#!/usr/bin/env python3
"""Where the overhang is: mesh_check.py says how much surface is past 60 deg, this says where.

For every part of a 3MF (or an STL), the surface past the limit above the bottom band is summed
into x/z bins and the largest bins are listed, as a share of the whole model's surface (the same
denominator for every part, so the numbers add up across parts).

usage:
  python overhang_map.py model.3mf [--limit 60] [--above 10] [--bin-x 20] [--bin-z 10] [--top 12]
"""
import argparse, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mesh_check import load, surface      # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mesh')
    ap.add_argument('--limit', type=float, default=60, help='degrees from vertical (default 60)')
    ap.add_argument('--above', type=float, default=10, help='ignore faces starting below this z (default 10 mm)')
    ap.add_argument('--bin-x', type=float, default=20)
    ap.add_argument('--bin-z', type=float, default=10)
    ap.add_argument('--top', type=int, default=12, help='bins listed per part')
    a = ap.parse_args()
    sin_lim = np.sin(np.radians(a.limit))
    meshes = load(a.mesh)
    total = sum(surface(V, F)[1].sum() for _, V, F in meshes)
    for name, V, F in meshes:
        T, area, nz, _ = surface(V, F)
        over = (nz < -sin_lim) & (T[:, :, 2].min(axis=1) >= a.above)
        if not over.any():
            print(f"{name}: 0.00%")
            continue
        c = T[over].mean(axis=1)
        print(f"{name}: {100 * area[over].sum() / total:.2f}% of the model's surface")
        bins = {}
        for x, z, ar in zip(np.floor(c[:, 0] / a.bin_x) * a.bin_x, np.floor(c[:, 2] / a.bin_z) * a.bin_z, area[over]):
            bins[(x, z)] = bins.get((x, z), 0) + ar
        for (x, z), ar in sorted(bins.items(), key=lambda k: -k[1])[:a.top]:
            print(f"   x {x:+6.0f}..{x + a.bin_x:+5.0f}  z {z:5.0f}..{z + a.bin_z:4.0f}   {100 * ar / total:.3f}%")


if __name__ == '__main__':
    main()
