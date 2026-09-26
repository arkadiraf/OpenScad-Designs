"""Trace the emblem of the TAU logo's left-hand circle into OpenSCAD polygons.

Source: https://upload.wikimedia.org/wikipedia/commons/1/16/Tel_Aviv_university_logo_-_Hebrew.png
(1478 x 801 px, black marks on a transparent background).

The left disc is found in the image, the white emblem inside it is upsampled 4x from the ink
(darkness over white, so the anti-aliased edges are kept), traced along pixel boundaries, and simplified
(Douglas-Peucker). The output, TAU_Emblem.scad, is in units of the disc radius, centred on the
disc, y up: `tau_emblem()` is the white emblem, `tau_disc_r = 1`.

usage:  python TAU_Emblem_trace.py logo.png [TAU_Emblem.scad]
"""
import sys, os
import numpy as np
from PIL import Image

UP = 4          # upsampling
TOL = 1.2       # simplification tolerance, upsampled px (0.3 original px)


def disc_of(alpha):
    """Centre and radius of the left disc: the first blob of dark columns in the top part."""
    dark = alpha > 128
    rows = np.where(dark.any(axis=1))[0]
    # the three marks sit above the text; the first all-empty row after them separates the two
    top = rows[0]
    r = top
    while dark[r].any():
        r += 1
    band = dark[top:r]
    cols = np.where(band.any(axis=0))[0]
    x0 = cols[0]; x1 = x0
    while band[:, x1 + 1].any():
        x1 += 1
    return (x0 + x1 + 1) / 2, (top + r) / 2, (x1 + 1 - x0) / 2, (x0, x1 + 1, top, r)


def trace(mask):
    """Directed pixel-boundary edges (image coords, y down), chained into loops."""
    h, w = mask.shape
    m = np.zeros((h + 2, w + 2), bool); m[1:-1, 1:-1] = mask
    out = {}
    # For each inside pixel (i, j) in padded coords, emit its edges that border outside,
    # oriented clockwise in image coords (= counter-clockwise with y up).
    ii, jj = np.where(m)
    for i, j in zip(ii, jj):
        if not m[i - 1, j]: out.setdefault((j + 1, i), []).append((j, i))          # top: right -> left
        if not m[i, j - 1]: out.setdefault((j, i), []).append((j, i + 1))          # left: top -> bottom
        if not m[i + 1, j]: out.setdefault((j, i + 1), []).append((j + 1, i + 1))  # bottom: left -> right
        if not m[i, j + 1]: out.setdefault((j + 1, i + 1), []).append((j + 1, i))  # right: bottom -> top
    loops = []
    while out:
        start = next(iter(out))
        loop = [start]; p = start
        while True:
            q = out[p].pop()
            if not out[p]:
                del out[p]
            if q == start:
                break
            loop.append(q); p = q
            if p not in out:
                break
        loops.append(np.array(loop, float) - 1)                 # undo the padding
    return loops


def dp(pts, tol):
    """Douglas-Peucker on an open polyline."""
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a; L = np.hypot(*ab)
    if L == 0:
        d = np.hypot(*(pts - a).T)
    else:
        d = np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / L
    k = int(np.argmax(d))
    if d[k] <= tol:
        return np.array([a, b])
    return np.vstack([dp(pts[:k + 1], tol)[:-1], dp(pts[k:], tol)])


def simplify_closed(loop, tol):
    # split at the point farthest from the first, simplify both halves
    far = int(np.argmax(np.hypot(*(loop - loop[0]).T)))
    ring = np.vstack([loop, loop[:1]])
    s = np.vstack([dp(ring[:far + 1], tol)[:-1], dp(ring[far:], tol)[:-1]])
    return s


def area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TAU_Emblem.scad')
    # ink = darkness composited on white (the emblem may be clear or opaque white)
    a = np.array(Image.open(src).convert('RGBA')).astype(float)
    lum = a[..., :3].mean(axis=2) * a[..., 3] / 255 + 255 * (1 - a[..., 3] / 255)
    alpha = (255 - lum).astype(np.uint8)
    cx, cy, R, (x0, x1, y0, y1) = disc_of(alpha)
    crop = Image.fromarray(alpha[y0:y1, x0:x1])
    big = np.array(crop.resize((crop.width * UP, crop.height * UP), Image.BICUBIC)).astype(float) / 255
    hh, ww = big.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    rr = np.hypot((xx + 0.5) / UP + x0 - cx, (yy + 0.5) / UP + y0 - cy)
    white = (big < 0.5) & (rr < 0.9 * R)                      # the emblem: clear pixels well inside the disc
    loops = [simplify_closed(l, TOL) for l in trace(white)]
    loops = [l for l in loops if abs(area(l)) > (0.4 * UP) ** 2]   # drop specks
    # to disc units, y up
    polys = [np.column_stack(((l[:, 0] / UP + x0 - cx) / R, -(l[:, 1] / UP + y0 - cy) / R)) for l in loops]
    pts = []; paths = []
    for p in polys:
        paths.append(list(range(len(pts), len(pts) + len(p))))
        pts += p.tolist()
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write('// TAU logo, left-hand circle: the white emblem (flame, crown, the letters AT),\n')
        f.write('// traced from the Wikimedia Commons PNG by TAU_Emblem_trace.py. Do not edit by hand.\n')
        f.write(f'// Disc: centre ({cx:.1f}, {cy:.1f}) px, radius {R:.1f} px; units here are disc radii, y up.\n')
        f.write('tau_disc_r = 1;\n')
        f.write('tau_emblem_points = [\n' + ',\n'.join(f'[{x:.5f},{y:.5f}]' for x, y in pts) + '];\n')
        f.write('tau_emblem_paths = [\n' + ',\n'.join(str(p) for p in paths) + '];\n')
        f.write('module tau_emblem() polygon(tau_emblem_points, tau_emblem_paths);\n')
    print(f'disc centre ({cx:.1f}, {cy:.1f}) r {R:.1f} px; {len(polys)} loops, {len(pts)} points -> {dst}')
    for p in polys:
        print(f'  loop {len(p):4d} pts  area {area(p):+.4f}  x {p[:,0].min():+.3f}..{p[:,0].max():+.3f}  y {p[:,1].min():+.3f}..{p[:,1].max():+.3f}')


if __name__ == '__main__':
    main()
