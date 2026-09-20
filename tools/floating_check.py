#!/usr/bin/env python3
"""Find regions of a mesh that start in mid-air, and say where they are.

Bambu Studio refuses a plate with "object ... has floating regions" but does not say where. This
finds them: every surface point lower than all its neighbours (the lowest point of a region) with
nothing under it, tested by casting a ray straight down through the mesh.

Use it on designs made of tubes (the tree holders): there it agrees with Bambu Studio, 0 on every
design the slicer accepted and 1 on the one it refused (a fork's end cap lifted off its parent by
its own arch). It over-reports on thin blades, e.g. the 75 folded leaves of the Braided Tree: a
leaf's lowest edge is carried by the twig beside it in the same layer, which only a per-layer island
test sees. The slicer stays the authority (build_design.py slices every build); this says where.

usage:
  python floating_check.py model.3mf [--gap 0.25] [--top 25]

Exit code 0 when nothing hangs, 1 otherwise.
"""
import argparse, sys
import numpy as np

from mesh_check import load


def local_minima(V, F, above):
    """Vertices no higher than every neighbour, above `above`."""
    low = np.full(len(V), True)
    for a, b in ((0, 1), (1, 2), (2, 0)):
        i, j = F[:, a], F[:, b]
        np.logical_and.at(low, i, V[i, 2] <= V[j, 2])
        np.logical_and.at(low, j, V[j, 2] <= V[i, 2])
    return np.where(low & (V[:, 2] > above))[0]


def near_below(p, grid, cell, gap, reach):
    """Is there any surface point within `cell` sideways and between gap and reach below p?
    A leaf edge or a fork underside resting against another part is carried by it, and the
    slicer treats the two as one island."""
    cx, cy = int(p[0] // cell), int(p[1] // cell)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for q in grid.get((cx + dx, cy + dy), ()):
                if gap < p[2] - q[2] < reach and (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 <= cell * cell:
                    return True
    return False


def supported(p, T, box, gap):
    """Does a ray straight down from p hit a triangle more than `gap` below it?"""
    x0, x1, y0, y1, zmin = box
    m = (x0 <= p[0]) & (x1 >= p[0]) & (y0 <= p[1]) & (y1 >= p[1]) & (zmin < p[2] - gap)
    if not m.any():
        return False
    a, b, c = T[m, 0], T[m, 1], T[m, 2]
    v0, v1, v2 = c[:, :2] - a[:, :2], b[:, :2] - a[:, :2], p[:2] - a[:, :2]
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
    d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    ok = np.abs(den) > 1e-12
    safe = np.where(ok, den, 1)
    u = np.where(ok, (d11 * d20 - d01 * d21) / safe, -1)
    v = np.where(ok, (d00 * d21 - d01 * d20) / safe, -1)
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
    if not hit.any():
        return False
    w = 1 - u[hit] - v[hit]
    z = w * a[hit, 2] + v[hit] * b[hit, 2] + u[hit] * c[hit, 2]
    return bool((z < p[2] - gap).any())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mesh')
    ap.add_argument('--gap', type=float, default=0.25, help='a region counts as hanging when the nearest '
                    'material below it is more than this far down (mm, about one layer)')
    ap.add_argument('--reach', type=float, default=0.5, help='material this far sideways and below still '
                    'carries a region (mm, about one extrusion width)')
    ap.add_argument('--top', type=int, default=25, help='how many to list')
    a = ap.parse_args()

    parts = load(a.mesh)
    # a part may rest on another, so both tests see every part
    T = np.concatenate([V[F] for _, V, F in parts])
    box = (T[:, :, 0].min(1), T[:, :, 0].max(1), T[:, :, 1].min(1), T[:, :, 1].max(1), T[:, :, 2].min(1))
    grid = {}
    for _, V, _ in parts:
        for q in V:
            grid.setdefault((int(q[0] // a.reach), int(q[1] // a.reach)), []).append(q)
    bad_all = 0
    for name, V, F in parts:
        cand = local_minima(V, F, a.gap + 0.35)
        bad = [V[i] for i in cand
               if not near_below(V[i], grid, a.reach, a.gap, 4) and not supported(V[i], T, box, a.gap)]
        bad.sort(key=lambda q: q[2])
        print(f"--- {name}: {len(cand)} points lower than all their neighbours, {len(bad)} of them in mid-air")
        for p in bad[:a.top]:
            print(f"    z {p[2]:7.2f}  r {np.hypot(p[0], p[1]):6.1f}  phi {np.degrees(np.arctan2(p[1], p[0])) % 360:6.1f}")
        bad_all += len(bad)
    print(f"  {'PASS' if bad_all == 0 else 'FAIL'}: {bad_all} regions start in mid-air")
    sys.exit(0 if bad_all == 0 else 1)


if __name__ == '__main__':
    main()
