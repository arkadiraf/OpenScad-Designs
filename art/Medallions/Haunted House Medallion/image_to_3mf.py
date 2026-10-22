#!/usr/bin/env python3
"""Turn a flat colour illustration (PNG with transparency) into a multi-colour medallion 3MF.

The picture is snapped to a small palette of Bambu PLA Basic colours, each colour is traced into
polygons and extruded:

  * Transparent pixels are empty; the white disc behind the house is part of the medallion
    (--cut-white cuts it away instead, keeping the ghost)
  * Black base  - the whole silhouette, z = 0 .. base_h (the back of the medallion is black)
  * Top layer   - z = base_h .. thickness, split into one part per colour; black outlines included

Only the top layers change colour, which keeps purge waste low. Each part is a separate mesh in
one object, so Bambu Studio / Orca can assign any filament to any part.

usage:
  python image_to_3mf.py source.png out.3mf [--width 75] [--thickness 3] [--top 0.6] [--cut-white [--keep-white 125,45]]
then:
  python tools/bambu_3mf.py out.3mf --printer H2C
"""
import argparse, os, subprocess, sys, tempfile, zipfile

import cv2
import numpy as np
from manifold3d import CrossSection, FillRule, Manifold
from PIL import Image
from scipy import ndimage
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools')

# name, palette RGB seen in the picture, Bambu PLA Basic hex for the part
PALETTE = [
    ('Black',  (0, 0, 0),       '#000000'),
    ('Orange', (240, 110, 20),  '#FF6A13'),
    ('White',  (240, 240, 240), '#FFFFFF'),
    ('Purple', (100, 70, 170),  '#5E43B7'),
    ('Green',  (20, 175, 80),   '#00AE42'),
    ('Yellow', (245, 230, 20),  '#F4EE2A'),
]


def classify(img, up):
    """Label map (-1 = empty) at `up` x the source resolution."""
    rgba = np.asarray(img.convert('RGBA')).astype(np.float32)
    a = rgba[..., 3:4] / 255.0
    rgb = rgba[..., :3] * a + 255.0 * (1 - a)         # flatten on white for edge pixels
    h, w = a.shape[:2]
    big = cv2.resize(rgb, (w * up, h * up), interpolation=cv2.INTER_CUBIC)
    alpha = cv2.resize(a[..., 0], (w * up, h * up), interpolation=cv2.INTER_LINEAR)
    pal = np.array([p[1] for p in PALETTE], np.float32)
    d = ((big[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
    lab = d.argmin(-1).astype(np.int32)
    lab[alpha < 0.5] = -1
    return lab


def clean(lab, min_px):
    """Drop colour specks smaller than min_px and refill them from the nearest colour."""
    lab = lab.copy()
    for k in range(len(PALETTE)):
        comp, n = ndimage.label(lab == k)
        if n == 0:
            continue
        sizes = ndimage.sum(np.ones_like(comp), comp, range(1, n + 1))
        small = np.isin(comp, np.nonzero(sizes < min_px)[0] + 1)
        lab[small] = -2
    # anti-aliased outline edges read as thin colour fringes; colour strips thinner than
    # ~0.2 mm can't print as their own lines anyway, so they join the black outline
    r = 3
    disk = np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
    for k in range(1, len(PALETTE)):
        m = lab == k
        lab[m & ~ndimage.binary_opening(m, structure=disk)] = 0
    hole = lab == -2
    if hole.any():
        idx = ndimage.distance_transform_edt(lab < 0, return_distances=False, return_indices=True)
        filled = lab[idx[0], idx[1]]
        lab[hole] = filled[hole]
    return lab


def remove_background(lab, keep, scale, up, cut_white):
    """With cut_white, the white behind the house is treated as background and cut out: white
    patches larger than a cobweb cell (or long slivers along the frame) go, except those under a
    `keep` seed (the ghost). Then only the piece holding the most material stays; loose bits
    would fall off the print."""
    white = [k for k, p in enumerate(PALETTE) if p[0] == 'White'][0]
    comp, n = ndimage.label(lab == white)
    keep_ids = {comp[y * up, x * up] for x, y in keep} - {0}
    for i, sl in enumerate(ndimage.find_objects(comp), 1):
        if not cut_white or i in keep_ids:
            continue
        area = (comp[sl] == i).sum() * scale ** 2
        span = max(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) * scale
        if area > 1.2 or span > 3.0:
            lab[comp == i] = -1
    body, n = ndimage.label(lab >= 0, structure=np.ones((3, 3)))
    sizes = ndimage.sum(np.ones_like(body), body, range(1, n + 1))
    main = sizes.argmax() + 1
    print(f'dropped {n - 1} loose pieces, {(sizes.sum() - sizes.max()) * scale ** 2:.1f} mm2')
    lab[(body != main) & (lab >= 0)] = -1
    return lab


def trace(mask, scale, h, simplify):
    """Binary mask -> shapely geometry in mm (y up, origin bottom-left)."""
    m = (mask.astype(np.uint8)) * 255
    contours, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    geom = Polygon()
    polys = []
    for c in contours:
        if len(c) < 3:
            continue
        pts = [((x + 0.5) * scale, (h - y - 0.5) * scale) for x, y in c[:, 0, :]]
        p = Polygon(pts).buffer(0)
        if not p.is_empty:
            polys.append(p)
    for p in polys:                                    # nesting resolved by even-odd
        geom = geom.symmetric_difference(p)
    return geom.simplify(simplify).buffer(0)


def to_cross_section(geom):
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    loops = []
    for p in polys:
        if p.is_empty:
            continue
        loops.append(list(p.exterior.coords)[:-1])
        loops += [list(r.coords)[:-1] for r in p.interiors]
    return CrossSection(loops, FillRule.EvenOdd)


def write_mesh_3mf(path, man):
    mesh = man.to_mesh()
    v, t = mesh.vert_properties[:, :3], mesh.tri_verts
    verts = ''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v)
    tris = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t)
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources><object id="1" type="model"><mesh><vertices>{verts}</vertices>'
             f'<triangles>{tris}</triangles></mesh></object></resources>'
             '<build><item objectid="1"/></build></model>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('3D/3dmodel.model', model)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--name', default='Haunted House Medallion')
    ap.add_argument('--width', type=float, default=75.0, help='overall width, mm')
    ap.add_argument('--thickness', type=float, default=3.0, help='total thickness, mm')
    ap.add_argument('--top', type=float, default=0.6, help='colour layer thickness, mm')
    ap.add_argument('--up', type=int, default=4, help='upsampling before tracing')
    ap.add_argument('--min-feature', type=float, default=0.35, help='smallest colour patch side, mm')
    ap.add_argument('--cut-white', action='store_true', help='cut the white backdrop out (open fretwork)')
    ap.add_argument('--keep-white', default='125,45', help='x,y;x,y source pixels of white parts to keep')
    ap.add_argument('--preview', help='write the cleaned label map as a PNG here')
    a = ap.parse_args()

    img = Image.open(a.src)
    lab = classify(img, a.up)
    ys, xs = np.nonzero(lab >= 0)
    lab = lab[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = lab.shape
    scale = a.width / w                                 # mm per (upsampled) pixel
    lab = clean(lab, (a.min_feature / scale) ** 2)
    keep = [tuple(int(v) for v in q.split(',')) for q in a.keep_white.split(';') if q]
    keep = [(x - xs.min() // a.up, y - ys.min() // a.up) for x, y in keep]
    lab = remove_background(lab, keep, scale, a.up, a.cut_white)
    print(f'size {a.width:.1f} x {h * scale:.1f} mm, {scale * a.up:.3f} mm per source pixel')

    if a.preview:
        pal = np.array([p[1] for p in PALETTE] + [(255, 255, 255)], np.uint8)
        Image.fromarray(pal[lab]).save(a.preview)

    simp = scale * 0.4
    sil = trace(lab >= 0, scale, h, simp)
    base_h = a.thickness - a.top

    geoms, used = {}, Polygon()
    for k, (name, _, _) in enumerate(PALETTE):
        if name == 'Black':
            continue
        g = trace(lab == k, scale, h, simp).intersection(sil).difference(used)
        g = g.buffer(-1e-3).buffer(1e-3)                # drop zero-width slivers
        if g.area > 0:
            geoms[name] = g
            used = used.union(g)
    geoms['Black'] = sil.difference(used)

    parts = []
    tmp = tempfile.mkdtemp()
    for name, _, hexcol in PALETTE:
        if name not in geoms:
            continue
        top = Manifold.extrude(to_cross_section(geoms[name]), a.top).translate((0, 0, base_h))
        man = top
        if name == 'Black':
            man = Manifold.extrude(to_cross_section(sil), base_h) + top
        if man.is_empty():
            continue
        p = os.path.join(tmp, f'{name}.3mf')
        write_mesh_3mf(p, man)
        print(f'{name:7s} top area {geoms[name].area:8.1f} mm2  volume {man.volume():8.1f} mm3')
        parts.append(f'{name}={p}={hexcol}')

    subprocess.run([sys.executable, os.path.join(TOOLS, 'merge_3mf.py'), a.out, a.name] + parts,
                   check=True)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
