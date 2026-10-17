"""Seed searches for the Wander trees, from the part="paths" echo (nightly OpenSCAD, 8 at a time).

    python tree_search.py branches NAME [FIRST LAST]      # wander seeds for NAME's branch layout
    python tree_search.py roots NAME [FIRST LAST]         # root seeds for NAME (its root_count)

branches: the same scoring as ../Various/wander_search.py - worst merge between members
  (member_clearance.py, <= 30 %), smallest climb (>= 30 deg), highest arch, end caps under
  total_h, tightest centreline bend >= 1.25x the member radius.
roots: the tightest bend of every root and side root over its radius (>= 1.25; a sine meander of
  amplitude A and wavelength L bends with radius L^2 / (4 pi^2 A)), and the footprint (root
  centreline + radius) inside root_spread / 2 + 2 mm, so the tree still fits the bed.
NAME must be in trees.json and written by make_wander_trees.py; the seed under test is passed
with -D, so the .scad is not touched.
"""
import json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'tools')
sys.path.insert(0, TOOLS)
from render_png import openscad_cmd   # noqa: E402
from member_clearance import load     # noqa: E402

ROOT_SPREAD = 208


def tightest_bend(P, R, k=4):
    """Smallest circumradius through points k apart, divided by the tube radius there."""
    if len(P) < 2 * k + 1:
        return 99.0
    a, b, c = P[:-2 * k], P[k:-k], P[2 * k:]
    ab, bc, ca = (np.linalg.norm(x, axis=1) for x in (b - a, c - b, a - c))
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    rc = ab * bc * ca / np.maximum(4 * area, 1e-9)
    return float(np.min(rc / R[k:-k]))


def paths(name, var, seed):
    scad = os.path.join(HERE, name, f'Wild_Chalice_{name}.scad')
    echo = os.path.join(tempfile.gettempdir(), f'wct_{name}_{var}_{seed}.echo')
    subprocess.run([*openscad_cmd(), '-o', echo, '-D', 'part="paths"', '-D', f'{var}={seed}', scad],
                   capture_output=True, text=True)
    return echo


def eval_branches(name, seed):
    echo = paths(name, 'wander_seed', seed)
    txt = open(echo, encoding='utf-8', errors='replace').read()
    summ = re.search(r'meeting points \[branch, under, z, arch\]: (\[.*?\]\]|\[\]) \| climb >= (-?\d+)', txt)
    meets = json.loads(summ[1]); climb = int(summ[2])
    cl = subprocess.run([sys.executable, os.path.join(TOOLS, 'member_clearance.py'), echo, '--floor', '65',
                         '--top', '1'], capture_output=True, text=True).stdout
    worst = int(re.search(r'worst overlap (\d+) %', cl)[1])
    caps = subprocess.run([sys.executable, os.path.join(TOOLS, 'cap_height.py'), echo, '--limit', '269'],
                          capture_output=True, text=True).returncode == 0
    bend = min(tightest_bend(m['P'], m['R']) for n, m in load(echo).items() if n.startswith('b'))
    os.remove(echo)
    arch = max([m[3] for m in meets] + [0])
    ok = worst <= 30 and climb >= 30 and caps and bend >= 1.25
    score = (0 if ok else 1000) + worst + 0.5 * arch + 3 * max(0, 33 - climb) + 20 * max(0, 1.4 - bend)
    return dict(seed=seed, ok=ok, score=round(score, 1), worst=worst, climb=climb, arch=arch,
                meets=len(meets), bend=round(bend, 2), caps=caps)


def eval_roots(name, seed):
    echo = paths(name, 'root_seed', seed)
    M = {n: m for n, m in load(echo).items() if 'root' in n}
    os.remove(echo)
    bend = min(tightest_bend(m['P'], m['R']) for m in M.values())
    reach = max(float(np.max(np.hypot(m['P'][:, 0], m['P'][:, 1]) + m['R'])) for m in M.values())
    # how evenly the main roots fan out: the largest angle between neighbouring root tips
    tips = np.sort([np.degrees(np.arctan2(m['P'][-1, 1], m['P'][-1, 0])) % 360
                    for n, m in M.items() if n.startswith('root')])
    gap = float(np.max(np.diff(np.concatenate([tips, [tips[0] + 360]]))))
    ok = bend >= 1.25 and reach <= ROOT_SPREAD / 2 + 2
    score = (0 if ok else 1000) + gap + 20 * max(0, 1.5 - bend)
    return dict(seed=seed, ok=ok, score=round(score, 1), bend=round(bend, 2), reach=round(reach, 1),
                tip_gap=round(gap), side_roots=sum(n.startswith('twigroot') for n in M))


if __name__ == '__main__':
    kind, name = sys.argv[1], sys.argv[2]
    lo, hi = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1, 16)
    f = eval_branches if kind == 'branches' else eval_roots
    with ThreadPoolExecutor(8) as ex:
        res = sorted(ex.map(lambda s: f(name, s), range(lo, hi + 1)), key=lambda r: r['score'])
    for r in res[:5]:
        print(name, kind, r)
    print(f'BEST {name} {kind} {res[0]["seed"]} ok={res[0]["ok"]}')
