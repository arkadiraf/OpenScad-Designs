"""Trace the TAU Engineering ECE logo (three discs) into OpenSCAD polygons for the Card Box lid.

Source: TAU_ECE_Logo_source.png, a phone screenshot of TAUEnginneringECELogo_HEB_N...png
(white discs with dark marks on a dark background, 1080 x 2424 px).

Everything white in the logo band is traced (outer disc edges plus the dark marks as holes),
along pixel boundaries after 4x upsampling, then simplified (Douglas-Peucker). The output,
Card_Box_Logo.scad, is in units of the disc radius, centred on the middle disc, y up:
`ece_logo()` is the white area, `ece_logo_w` / `ece_logo_h` its size.
The right disc touches the screenshot edge, so it is clipped to its fitted circle.

usage:  python Card_Box_logo_trace.py [TAU_ECE_Logo_source.png] [Card_Box_Logo.scad]
"""
import sys, os
import numpy as np
from PIL import Image

UP = 4
TOL = 1.2
HERE = os.path.dirname(os.path.abspath(__file__))


def trace(mask):
    h, w = mask.shape
    m = np.zeros((h + 2, w + 2), bool); m[1:-1, 1:-1] = mask
    out = {}
    ii, jj = np.where(m)
    for i, j in zip(ii, jj):
        if not m[i - 1, j]: out.setdefault((j + 1, i), []).append((j, i))
        if not m[i, j - 1]: out.setdefault((j, i), []).append((j, i + 1))
        if not m[i + 1, j]: out.setdefault((j, i + 1), []).append((j + 1, i + 1))
        if not m[i, j + 1]: out.setdefault((j + 1, i + 1), []).append((j + 1, i))
    loops = []
    while out:
        start = next(iter(out)); loop = [start]; p = start
        while True:
            q = out[p].pop()
            if not out[p]:
                del out[p]
            if q == start:
                break
            loop.append(q); p = q
            if p not in out:
                break
        loops.append(np.array(loop, float) - 1)
    return loops


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a; L = np.hypot(*ab)
    d = np.hypot(*(pts - a).T) if L == 0 else \
        np.abs(ab[0] * (pts[:, 1] - a[1]) - ab[1] * (pts[:, 0] - a[0])) / L
    k = int(np.argmax(d))
    if d[k] <= tol:
        return np.array([a, b])
    return np.vstack([dp(pts[:k + 1], tol)[:-1], dp(pts[k:], tol)])


def simplify_closed(loop, tol):
    far = int(np.argmax(np.hypot(*(loop - loop[0]).T)))
    ring = np.vstack([loop, loop[:1]])
    return np.vstack([dp(ring[:far + 1], tol)[:-1], dp(ring[far:], tol)[:-1]])


def area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def runs(v):
    out, s = [], None
    for i, b in enumerate(v):
        if b and s is None: s = i
        if not b and s is not None: out.append((s, i - 1)); s = None
    if s is not None: out.append((s, len(v) - 1))
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'TAU_ECE_Logo_source.png')
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'Card_Box_Logo.scad')
    lum = np.array(Image.open(src).convert('L')).astype(float)
    h, w = lum.shape
    white = lum > 128
    white[:int(0.17 * h)] = False; white[int(0.95 * h):] = False     # status bar, header, nav bar
    rows = np.where(white.any(axis=1))[0]
    y0, y1 = rows[0], rows[-1] + 1
    cy = (y0 + y1) / 2; R = (y1 - y0) / 2
    cols = runs(white[y0:y1].any(axis=0))
    assert len(cols) == 3, cols
    c1 = cols[0][0] + R; c3 = cols[2][0] + R                      # left edges are uncut
    centres = [c1, (c1 + c3) / 2, c3]
    x0 = max(0, int(c1 - R) - 2); x1 = w
    crop = Image.fromarray(lum[y0 - 2:y1 + 2, x0:x1].astype(np.uint8))
    big = np.array(crop.resize((crop.width * UP, crop.height * UP), Image.BICUBIC)).astype(float)
    hh, ww = big.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    px = (xx + 0.5) / UP + x0; py = (yy + 0.5) / UP + y0 - 2
    inside = np.zeros_like(big, bool)
    for c in centres:
        inside |= np.hypot(px - c, py - cy) < R
    # white inside the fitted discs (the right disc is clipped by the image edge)
    mask = (big > 128) & inside
    loops = [simplify_closed(l, TOL) for l in trace(mask)]
    loops = [l for l in loops if abs(area(l)) > (0.6 * UP) ** 2]
    cx = centres[1]
    polys = [np.column_stack(((l[:, 0] / UP + x0 - cx) / R, -(l[:, 1] / UP + y0 - 2 - cy) / R)) for l in loops]
    pts, paths = [], []
    for p in polys:
        paths.append(list(range(len(pts), len(pts) + len(p)))); pts += p.tolist()
    allp = np.vstack(polys)
    lw = allp[:, 0].max() - allp[:, 0].min(); lh = allp[:, 1].max() - allp[:, 1].min()
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write('// TAU Engineering ECE logo: the white area of the three discs (marks are holes),\n')
        f.write('// traced from TAU_ECE_Logo_source.png by Card_Box_logo_trace.py. Do not edit by hand.\n')
        f.write(f'// Disc radius {R:.1f} px; units here are disc radii, centred on the middle disc, y up.\n')
        f.write(f'ece_logo_w = {lw:.5f};\nece_logo_h = {lh:.5f};\n')
        f.write('ece_logo_points = [\n' + ',\n'.join(f'[{x:.5f},{y:.5f}]' for x, y in pts) + '];\n')
        f.write('ece_logo_paths = [\n' + ',\n'.join(str(p) for p in paths) + '];\n')
        f.write('module ece_logo() polygon(ece_logo_points, ece_logo_paths);\n')
    print(f'discs at x {[round(float(c), 1) for c in centres]}, y {cy:.1f}, r {R:.1f} px; '
          f'{len(polys)} loops, {len(pts)} points, {lw:.3f} x {lh:.3f} radii -> {dst}')


if __name__ == '__main__':
    main()
