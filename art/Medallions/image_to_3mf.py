#!/usr/bin/env python3
"""Turn a flat colour illustration (PNG with transparency, or a JPG on a white / paper background)
into a double-sided multi-colour medallion 3MF, ready to slice in Bambu Studio.

Each medallion lives in its own folder with a medallion.json (see README.md):

  source      the drawing, in the folder
  size        longest side of the medallion, mm
  palette     [[part name, [r, g, b] as seen in the drawing, Bambu PLA Basic hex], ...]
              The first entry is the core colour: it fills the middle layer and swallows the
              outlines and every colour strip too thin to print on its own. Several entries may
              share a part name (e.g. dark-brown and black outlines both print Black).
  holes       [[x, y], ...] source pixels inside the hang hole (and any other enclosed opening)
  optional    thickness (3.0), core (1.8), top (colour on the top face only, this thick),
              min_feature (0.35 mm), cut_white + keep_white (cut the white backdrop away)

The picture is snapped to the palette, each colour is traced into polygons and extruded:

  * default: colour on both faces, z = 0 .. f and thickness - f .. thickness, and a solid core of
    the first palette colour between, f = (thickness - core) / 2. 3.0 mm with a 1.8 mm core gives
    0.6 mm (3 layers) of colour per face. The back shows the picture mirrored
  * "top": T: a core-colour base under the whole silhouette and only the top T in colour
  * "core": 0 runs every colour the full thickness

Background: transparent pixels, or near-white pixels connected to the image border or to a
`holes` seed, are empty. Only the largest connected piece is kept (loose bits would fall off).

Each colour is a separate part of one object; the 3MF is converted to a Bambu Studio project
(tools/bambu_3mf.py: H2C, PLA Basic, 35 % infill) and, with --slice, sliced to check it.

usage:
  python image_to_3mf.py "Taco Fiesta Medallion" [more folders ...] [--slice] [--printer H2C]
  python image_to_3mf.py --all --slice
writes <Folder_Name>.3mf (the Bambu Studio project) and <Folder_Name>.png, a
top view of the colour map as it will print.
"""
import argparse, json, os, subprocess, sys, tempfile, zipfile

import cv2
import numpy as np
from manifold3d import CrossSection, FillRule, Manifold
from PIL import Image
from scipy import ndimage
from shapely.geometry import MultiPolygon, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', 'tools')
sys.path.insert(0, TOOLS)
from bambu_3mf import convert, slice_check   # noqa: E402

PX_PER_MM = 40          # resolution the drawing is resampled to before tracing
OPEN_R = 0.1            # colour strips narrower than 2 x this (mm) join the core colour
SIMPLIFY = 0.02         # outline simplification, mm


def load(path, holes):
    """RGB (float) and object mask at the source resolution."""
    img = Image.open(path)
    if img.mode in ('RGBA', 'LA', 'P'):
        rgba = np.asarray(img.convert('RGBA')).astype(np.float32)
        a = rgba[..., 3:4] / 255.0
        rgb = rgba[..., :3] * a + 255.0 * (1 - a)     # flatten on white for edge pixels
        return rgb, a[..., 0] >= 0.5
    else:
        rgb = cv2.medianBlur(np.asarray(img.convert('RGB')), 3).astype(np.float32)
        mask = np.ones(rgb.shape[:2], bool)
    # near-white paper connected to the border, or to a hole seed, is background
    light = (rgb.min(-1) > 200) & (np.ptp(rgb, -1) < 40)
    comp, _ = ndimage.label(light)
    edge = np.concatenate([comp[0], comp[-1], comp[:, 0], comp[:, -1]])
    seeds = [comp[y, x] for x, y in holes]
    for x, y in holes:
        if comp[y, x] == 0:
            print(f'  warning: hole seed {x},{y} is not on a light pixel')
    bg = np.isin(comp, list((set(edge) | set(seeds)) - {0}))
    return rgb, mask & ~bg


def classify(rgb, mask, palette, size):
    """Label map (-1 = empty) at PX_PER_MM, cropped to the medallion; returns (lab, mm per px)."""
    ys, xs = np.nonzero(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb, mask = rgb[y0:y1, x0:x1], mask[y0:y1, x0:x1].astype(np.float32)
    h, w = mask.shape
    k = size * PX_PER_MM / max(h, w)
    W, H = round(w * k), round(h * k)
    big = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_CUBIC)
    alpha = cv2.resize(mask, (W, H), interpolation=cv2.INTER_LINEAR)
    best = np.full((H, W), np.inf, np.float32)
    lab = np.zeros((H, W), np.int32)
    for i, (_, col, _) in enumerate(palette):
        d = ((big - np.float32(col)) ** 2).sum(-1)
        lab[d < best] = i
        np.minimum(best, d, out=best)
    lab[alpha < 0.5] = -1
    return lab, size / max(W, H), (x0, y0, k)


def drop_specks(lab, n, min_px):
    """Refill colour specks smaller than min_px from the nearest other colour."""
    lab = lab.copy()
    for k in range(n):
        comp, m = ndimage.label(lab == k)
        if m == 0:
            continue
        sizes = ndimage.sum(np.ones_like(comp), comp, range(1, m + 1))
        lab[np.isin(comp, np.nonzero(sizes < min_px)[0] + 1)] = -2
    hole = lab == -2
    if hole.any():
        idx = ndimage.distance_transform_edt(lab < 0, return_distances=False, return_indices=True)
        filled = lab[idx[0], idx[1]]
        lab[hole] = filled[hole]
    return lab


def clean(lab, n, min_px, open_r_px):
    """Drop colour specks smaller than min_px and fold colour strips thinner than 2 x open_r_px
    into the core colour (label 0). Specks go again afterwards: a thin strip ending in a blob
    (a blended star tip) leaves the blob behind."""
    lab = drop_specks(lab, n, min_px)
    r = open_r_px
    disk = np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
    for k in range(1, n):
        m = lab == k
        lab[m & ~ndimage.binary_opening(m, structure=disk)] = 0
    return drop_specks(lab, n, min_px)


def remove_background(lab, white, keep, scale, cut_white):
    """With cut_white, the white backdrop is cut out: white patches larger than ~1 mm2 (or long
    slivers) go, except those under a `keep` seed. Then only the piece holding the most material
    stays; loose bits would fall off the print."""
    if cut_white:
        comp, _ = ndimage.label(lab == white)
        keep_ids = {comp[y, x] for x, y in keep} - {0}
        for i, sl in enumerate(ndimage.find_objects(comp), 1):
            if i in keep_ids:
                continue
            area = (comp[sl] == i).sum() * scale ** 2
            span = max(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) * scale
            if area > 1.2 or span > 3.0:
                lab[comp == i] = -1
    body, n = ndimage.label(lab >= 0, structure=np.ones((3, 3)))
    sizes = ndimage.sum(np.ones_like(body), body, range(1, n + 1))
    main = sizes.argmax() + 1
    print(f'  dropped {n - 1} loose pieces, {(sizes.sum() - sizes.max()) * scale ** 2:.1f} mm2')
    lab[(body != main) & (lab >= 0)] = -1
    return lab


def hole_report(lab, scale):
    """Enclosed openings (hang hole) and their size."""
    comp, n = ndimage.label(lab < 0)
    border = set(np.concatenate([comp[0], comp[-1], comp[:, 0], comp[:, -1]]))
    for i, sl in enumerate(ndimage.find_objects(comp), 1):
        if i in border:
            continue
        hh, ww = (sl[0].stop - sl[0].start) * scale, (sl[1].stop - sl[1].start) * scale
        print(f'  opening {ww:.1f} x {hh:.1f} mm at {sl[1].start * scale:.0f}, {sl[0].start * scale:.0f} mm')


def trace(mask, scale, h):
    """Binary mask -> shapely geometry in mm (y up, origin bottom-left)."""
    m = mask.astype(np.uint8) * 255
    contours, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    geom = Polygon()
    for c in contours:
        if len(c) < 3:
            continue
        p = Polygon([((x + 0.5) * scale, (h - y - 0.5) * scale) for x, y in c[:, 0, :]]).buffer(0)
        if not p.is_empty:
            geom = geom.symmetric_difference(p)        # nesting resolved by even-odd
    return geom.simplify(SIMPLIFY).buffer(0)


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


def build(folder, printer, do_slice):
    cfg = json.load(open(os.path.join(folder, 'medallion.json'), encoding='utf-8'))
    name = os.path.basename(os.path.normpath(folder))
    stem = os.path.join(folder, name.replace(' ', '_'))
    print(f'== {name}')
    palette = cfg['palette']
    parts = list(dict.fromkeys(p[0] for p in palette))          # part names, core first
    part_of = np.array([parts.index(p[0]) for p in palette])
    hexes = {p[0]: p[2] for p in palette}

    rgb, mask = load(os.path.join(folder, cfg['source']), cfg.get('holes', []))
    lab, scale, (x0, y0, k) = classify(rgb, mask, palette, cfg['size'])
    lab = np.where(lab >= 0, part_of[np.maximum(lab, 0)], -1)
    h, w = lab.shape
    lab = clean(lab, len(parts), (cfg.get('min_feature', 0.35) / scale) ** 2, round(OPEN_R / scale))
    white = [i for i, p in enumerate(parts) if hexes[p].upper() == '#FFFFFF']
    keep = [(round((x - x0) * k), round((y - y0) * k)) for x, y in cfg.get('keep_white', [])]
    lab = remove_background(lab, white[0] if white else -9, keep, scale, cfg.get('cut_white', False))
    print(f'  size {w * scale:.1f} x {h * scale:.1f} mm')
    hole_report(lab, scale)

    pal = np.array([[int(hexes[p][i:i + 2], 16) for i in (1, 3, 5)] for p in parts] + [[255, 255, 255]], np.uint8)
    Image.fromarray(pal[lab]).save(stem + '.png')

    sil = trace(lab >= 0, scale, h)
    t = cfg.get('thickness', 3.0)
    if cfg.get('top') is not None:                     # (z0, z1) slabs
        faces, core = [(t - min(cfg['top'], t), t)], [(0, t - min(cfg['top'], t))]
    elif cfg.get('core', 1.8) > 0:
        f = (t - min(cfg.get('core', 1.8), t)) / 2
        faces, core = [(0, f), (t - f, t)], [(f, t - f)]
    else:
        faces, core = [(0, t)], []
    faces = [z for z in faces if z[1] > z[0]]
    core = [z for z in core if z[1] > z[0]]

    geoms, used = {}, Polygon()
    for i, p in enumerate(parts[1:], 1):
        g = trace(lab == i, scale, h).intersection(sil).difference(used)
        g = g.buffer(-1e-3).buffer(1e-3)                # drop zero-width slivers
        if g.area > 0:
            geoms[p] = g
            used = used.union(g)
    geoms[parts[0]] = sil.difference(used)

    specs = []
    tmp = tempfile.mkdtemp()
    for i, p in enumerate(parts):
        if p not in geoms:
            continue
        slabs = [(geoms[p], z) for z in faces] + ([(sil, z) for z in core] if i == 0 else [])
        man = Manifold()
        for g, (z0, z1) in slabs:
            man += Manifold.extrude(to_cross_section(g), z1 - z0).translate((0, 0, z0))
        if man.is_empty():
            continue
        path = os.path.join(tmp, f'{i}.3mf')
        write_mesh_3mf(path, man)
        print(f'  {p:17s} {hexes[p]}  face area {geoms[p].area:7.1f} mm2  volume {man.volume():7.1f} mm3')
        specs.append(f'{p}={path}={hexes[p]}')

    out = stem + '.3mf'
    subprocess.run([sys.executable, os.path.join(TOOLS, 'merge_3mf.py'), out, name] + specs, check=True)
    convert(out, printer_id=printer)
    print('  wrote', out)
    if do_slice:
        ok, lines = slice_check(out)
        print('\n'.join('  ' + l for l in lines))
        return ok is not False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('folders', nargs='*', help='medallion folders (each with a medallion.json)')
    ap.add_argument('--all', action='store_true', help='every folder next to this script with a medallion.json')
    ap.add_argument('--printer', default='H2C')
    ap.add_argument('--slice', action='store_true', help='slice with Bambu Studio and report warnings')
    a = ap.parse_args()
    folders = a.folders
    if a.all:
        folders = sorted(os.path.join(HERE, d) for d in os.listdir(HERE)
                         if os.path.isfile(os.path.join(HERE, d, 'medallion.json')))
    if not folders:
        ap.error('no medallion folders given')
    ok = all([build(f, a.printer, a.slice) for f in folders])
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
