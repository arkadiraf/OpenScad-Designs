#!/usr/bin/env python3
"""How high each member's end cap reaches, from a design's part="paths" echo.

A member is swept as a tube and closed with a flat cap square to its path, so the cap's top edge
sits `r * cos(climb)` ABOVE the last point of the centreline. A design that holds its paths below
a height limit can still break it by that much, and the thicker the tips the more it is: blunting
the Grand Chaotic Tree's tips (2.75 mm to 2.7-4.8 mm) lifted its top by 0.85 mm and left 0.15 mm
under the limit.

This reads the same echo `member_clearance.py` does and reports the tallest caps, so the margin
can be checked in a second instead of after a render.

usage:
  openscad.com -o paths.echo -D 'part="paths"' design.scad
  python cap_height.py paths.echo [--limit 320] [--top 6]
Exit code 1 when a cap reaches above --limit.
"""
import argparse, json, re, sys
import numpy as np


def caps(path):
    """(cap top, name, path end, tip radius, climb) for every member, tallest first."""
    txt = open(path, encoding='utf-8', errors='replace').read()
    out = []
    for name, _parent, pts, rad in re.findall(r'ECHO: "PATH;([^;]*);([^;]*);(\[.*?\]\]);(\[[^\]]*\])"', txt):
        P = np.array(json.loads(pts))
        R = np.array(json.loads(rad))
        if len(P) < 2:
            continue
        d = P[-1] - P[-2]
        climb = np.degrees(np.arctan2(d[2], np.hypot(d[0], d[1])))
        out.append((P[-1, 2] + R[-1] * np.cos(np.radians(climb)), name, P[-1, 2], R[-1], climb))
    return sorted(out, reverse=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('echo', help='OpenSCAD output of part="paths" (the file written with -o, or its log)')
    ap.add_argument('--limit', type=float, help='height limit to check against, e.g. total_h')
    ap.add_argument('--top', type=int, default=6, help='members to list')
    a = ap.parse_args()

    rows = caps(a.echo)
    if not rows:
        sys.exit('no PATH lines found - render the design with part="paths"')
    for top, name, z, r, climb in rows[:a.top]:
        print(f'{name:<14} path ends z {z:6.1f}, tip r {r:4.1f}, climb {climb:4.1f} deg -> cap top z {top:6.1f}')
    top, name = rows[0][0], rows[0][1]
    if a.limit is None:
        print(f'highest cap {top:.2f} mm ({name})')
        return
    over = top - a.limit
    print(f'{"FAIL" if over > 0 else "PASS"}: highest cap {top:.2f} mm ({name}), '
          f'{abs(over):.2f} mm {"above" if over > 0 else "under"} the {a.limit:g} mm limit')
    sys.exit(1 if over > 0 else 0)


if __name__ == '__main__':
    main()
