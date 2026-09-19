#!/usr/bin/env python3
"""Clearance and merge check between the members (branches, forks, stubs) of a design.

The design echoes one line per member when rendered with part="paths":
    ECHO: "PATH;<name>;<parent name or empty>;[[x, y, z], ...];[r, r, ...]"
(the centreline points and the tube radius at each). For every pair of members this finds
the smallest gap between their surfaces (centreline distance minus both radii) and, where
they overlap, the overlap as a share of the thinner member's thickness at that spot.

Skipped, because they are meant to be joined: a member and its own parent near the junction
(a stub until it clears the parent tube, a fork or sub-branch for its first 40 mm), and
everything below --floor + 5 mm (inside the trunk bowl).

usage:
  openscad.com -o paths.echo -D 'part="paths"' design.scad
  python member_clearance.py paths.echo [--floor 60] [--limit 0.30] [--top 14]
Exit code 1 when any pair overlaps more than --limit.
"""
import argparse, json, re, sys
import numpy as np


def load(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    M = {}
    for name, parent, pts, rad in re.findall(r'ECHO: "PATH;([^;]*);([^;]*);(\[.*?\]\]);(\[[^\]]*\])"', txt):
        P = np.array(json.loads(pts)); R = np.array(json.loads(rad))
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        M[name] = dict(P=P, R=R, L=L, parent=parent)
    return M


def seg_dist(P, A, B):
    """Distance from each point P[i] to each segment A[k]-B[k], and the segment parameter."""
    d = B - A
    dd = np.maximum((d * d).sum(1), 1e-12)
    t = np.clip(((P[:, None, :] - A[None]) * d[None]).sum(2) / dd[None], 0, 1)
    Q = A[None] + t[..., None] * d[None]
    return np.linalg.norm(P[:, None, :] - Q, axis=2), t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('echo', help='OpenSCAD output of part="paths" (the file written with -o, or its log)')
    ap.add_argument('--floor', type=float, default=60, help='glass floor height: members are checked from 5 mm above it')
    ap.add_argument('--limit', type=float, default=0.30, help='largest allowed overlap, share of the thinner thickness')
    ap.add_argument('--top', type=int, default=14, help='pairs to list')
    a = ap.parse_args()
    M = load(a.echo)
    if not M:
        sys.exit('no PATH lines found - render the design with part="paths"')

    def mask(name, other):
        m = M[name]
        keep = m['P'][:, 2] >= a.floor + 5
        if m['parent'] == other:
            if name.startswith('twig'):
                keep &= np.linalg.norm(m['P'] - m['P'][0], axis=1) > M[other]['R'].max() + m['R'][0] + 3
            else:
                keep &= m['L'] > 40
        return keep

    names, rows = list(M), []
    for i, na in enumerate(names):
        for nb in names[i + 1:]:
            ka, kb = mask(na, nb), mask(nb, na)
            if ka.sum() == 0 or kb.sum() < 2:
                continue
            A, B = M[na], M[nb]
            PA, RA = A['P'][ka], A['R'][ka]
            idx = np.where(kb)[0]
            idx = idx[idx < len(B['P']) - 1]
            D, T = seg_dist(PA, B['P'][idx], B['P'][idx + 1])
            RB = B['R'][idx][None] * (1 - T) + B['R'][idx + 1][None] * T
            G = D - RA[:, None] - RB
            F = np.maximum(0, -G) / (2 * np.minimum(RA[:, None], RB))
            k = np.unravel_index(np.argmax(F - 1e-3 * G), G.shape)
            rows.append((F[k], G[k], na, nb, PA[k[0]]))
    rows.sort(key=lambda r: (-r[0], r[1]))
    print(f'{len(M)} members, {len(rows)} pairs checked; limit {100 * a.limit:.0f} % overlap of the thinner member')
    for f, g, na, nb, p in rows[:a.top]:
        flag = f'OVER {100 * a.limit:.0f} %' if f > a.limit else ('merged' if g < 0 else '')
        print(f'  overlap {100 * f:4.0f} %  gap {g:6.2f} mm  {na:<14} {nb:<14} at z {p[2]:6.1f} '
              f'r {np.hypot(p[0], p[1]):5.1f} phi {np.degrees(np.arctan2(p[1], p[0])) % 360:5.1f}  {flag}')
    bad = [r for r in rows if r[0] > a.limit]
    print('RESULT:', 'FAIL' if bad else 'PASS', f'(worst overlap {100 * max(r[0] for r in rows):.0f} %)')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
