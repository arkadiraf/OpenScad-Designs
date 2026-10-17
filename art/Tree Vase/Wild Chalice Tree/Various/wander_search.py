"""Pick a wander seed for each variant's layout (guide 16.1: any wander changes the meetings,
so the seed is a search dimension).

    python wander_search.py [FIRST LAST [NAME ...]]   # seeds FIRST..LAST (default 1..24), every variant or NAMEs

Each seed is evaluated from the part="paths" echo (nightly OpenSCAD, a few seconds each, 8 at a
time) and scored on: worst merge between members (member_clearance.py, must stay <= 30 %),
smallest climb (>= 30 deg), highest arch, tallest end cap (<= total_h) and the tightest bend of
any centreline as a multiple of its radius (>= 1.25). Prints a table and the best seed per
variant; copy those into variants.json as "wander".
"""
import json, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'tools')
sys.path.insert(0, TOOLS)
from render_png import openscad_cmd   # noqa: E402
from member_clearance import load     # noqa: E402

VARIANTS = json.load(open(os.path.join(HERE, 'variants.json')))


def tightest_bend(P, R, k=4):
    """Smallest circumradius through points k apart, divided by the tube radius there."""
    a, b, c = P[:-2 * k], P[k:-k], P[2 * k:]
    ab, bc, ca = (np.linalg.norm(x, axis=1) for x in (b - a, c - b, a - c))
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    rc = ab * bc * ca / np.maximum(4 * area, 1e-9)
    return float(np.min(rc / R[k:-k]))


def evaluate(name, seed):
    scad = os.path.join(HERE, name, f'Wild_Chalice_Tree_{name}.scad')
    echo = os.path.join(tempfile.gettempdir(), f'wcv_{name}_{seed}.echo')
    subprocess.run([*openscad_cmd(), '-o', echo, '-D', 'part="paths"', '-D', f'wander_seed={seed}', scad],
                   capture_output=True, text=True)
    txt = open(echo, encoding='utf-8', errors='replace').read()
    summ = re.search(r'meeting points \[branch, under, z, arch\]: (\[.*?\]\]|\[\]) \| climb >= (-?\d+)', txt)
    meets = json.loads(summ[1]); climb = int(summ[2])
    cl = subprocess.run([sys.executable, os.path.join(TOOLS, 'member_clearance.py'), echo, '--floor', '65',
                         '--top', '1'], capture_output=True, text=True).stdout
    worst = int(re.search(r'worst overlap (\d+) %', cl)[1])
    M = load(echo)
    caps = subprocess.run([sys.executable, os.path.join(TOOLS, 'cap_height.py'), echo, '--limit', '269'],
                          capture_output=True, text=True)
    bend = min(tightest_bend(m['P'], m['R']) for n, m in M.items() if n.startswith('b'))
    os.remove(echo)
    arch = max([m[3] for m in meets] + [0])
    ok = worst <= 30 and climb >= 30 and caps.returncode == 0 and bend >= 1.25
    score = (0 if ok else 1000) + worst + 0.5 * arch + 3 * max(0, 33 - climb) + 20 * max(0, 1.4 - bend)
    return dict(name=name, seed=seed, ok=ok, score=round(score, 1), worst=worst, climb=climb,
                arch=arch, meets=len(meets), bend=round(bend, 2), caps=caps.returncode == 0)


if __name__ == '__main__':
    lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 24)
    only = sys.argv[3:]                 # optional variant names
    names = [n for n in VARIANTS if not only or n in only]
    jobs = [(n, s) for n in names for s in range(lo, hi + 1)]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda j: evaluate(*j), jobs))
    for n in names:
        rows = sorted([r for r in res if r['name'] == n], key=lambda r: r['score'])
        print(f'== {n}')
        for r in rows[:5]:
            print('  ', r)
        print(f'BEST {n} wander_seed {rows[0]["seed"]}')
