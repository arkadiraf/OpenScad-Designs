"""Seed search that chose the Slender Chaotic Tree: layout, branch wander and root system.

    python Slender_Chaotic_Tree_search.py layouts      # 1. layout search over LAYOUT_SEEDS (4000 trees each)
    python Slender_Chaotic_Tree_search.py branches     # 2. wander seeds 1-24 for the best layouts
    python Slender_Chaotic_Tree_search.py roots        # 3. root seeds for the best passing layout
    python Slender_Chaotic_Tree_search.py write        # 4. fill the winner into Slender_Chaotic_Tree.scad

The method and the pass criteria are the Grand Chaotic Tree Catalogue's (../Grand Chaotic Tree
Catalogue/catalogue.py, whose evaluators this imports), with this design's glass: merge <= 30 %,
climb >= 30 deg, end caps under total_h, centreline bends >= 1.25 x the tube radius, roots inside
the spread. Results go to search/search.json; the chosen seeds are written into the .scad.
"""
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'Grand Chaotic Tree Catalogue'))
import catalogue as C   # noqa: E402

SCAD = os.path.join(HERE, 'Slender_Chaotic_Tree.scad')
LAYOUT = os.path.join(HERE, 'Slender_Chaotic_Tree_layout.py')
SEARCH = os.path.join(HERE, 'search')
STATE = os.path.join(SEARCH, 'search.json')
LAYOUT_SEEDS = list(range(101, 113))
LAYOUT_TREES = 4000
BEST_LAYOUTS = 8                       # layouts given a wander search
C.TOTAL_H, C.ROOT_SPREAD, C.LIFT = 230, 205, 56


def state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {'layouts': {}, 'branches': {}, 'roots': {}}


def save(st):
    json.dump(st, open(STATE, 'w'), indent=1)


def write_scad(path, lay, wander, root_seed=1, root_count=9):
    raw = open(SCAD, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    s = raw.replace('\r\n', '\n')
    s = C.sub1(r'limb_table = \[.*?\]\];', 'limb_table = ' + C.fmt_rows(lay['limbs']) + ';', s, flags=re.S)
    s = C.sub1(r'fork_table = \[.*?\]\];', 'fork_table = ' + C.fmt_rows(lay['forks']) + ';', s, flags=re.S)
    s = C.sub1(r'wander_seed = \d+;', f'wander_seed = {wander};', s)
    s = C.sub1(r'root_seed = \d+;', f'root_seed = {root_seed};', s)
    s = C.sub1(r'root_count = \d+;', f'root_count = {root_count};', s)
    s = C.sub1(r'// The layout came from a search over random 3 -> 7 -> 13 trees for the smallest\n.*?'
               r'(?=// Limbs, out of the trunk)',
               '// The layout came from a search over random 3 -> 7 -> 13 trees for the smallest\n'
               '// empty sector around the glass at every height, a tripod seat and no stacked\n'
               f'// arches: Slender_Chaotic_Tree_layout.py {lay["seed"]} {LAYOUT_TREES} (largest empty sector\n'
               f'// {lay["gap"]} deg, seat {lay["seat"]} deg). Wander and root seeds from\n'
               '// Slender_Chaotic_Tree_search.py.\n', s, flags=re.S)
    open(path, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
    return path


def stage_layouts(st):
    os.makedirs(os.path.join(SEARCH, 'layouts'), exist_ok=True)

    def run(seed):
        f = os.path.join(SEARCH, 'layouts', f'seed_{seed}.txt')
        if not (os.path.exists(f) and open(f).read().strip().endswith('}')):
            out = subprocess.run([sys.executable, LAYOUT, str(seed), str(LAYOUT_TREES)],
                                 capture_output=True, text=True).stdout
            open(f, 'w').write(out)
        lines = open(f).read().splitlines()
        g = re.search(r'worst gap (\d+) seat gap (\d+)', lines[1])
        return seed, dict(seed=seed, score=float(lines[0].split()[2]), gap=int(g[1]), seat=int(g[2]),
                          **json.loads(lines[-1]))
    with ThreadPoolExecutor(12) as ex:
        for seed, lay in ex.map(run, LAYOUT_SEEDS):
            st['layouts'][str(seed)] = lay
            print(f'layout {seed}: score {lay["score"]}, largest empty sector {lay["gap"]} deg, seat {lay["seat"]} deg')
    save(st)


def stage_branches(st):
    order = sorted(st['layouts'].values(), key=lambda l: l['score'])[:BEST_LAYOUTS]
    batch = [l for l in order if str(l['seed']) not in st['branches']]
    os.makedirs(os.path.join(SEARCH, 'cand'), exist_ok=True)
    scads = {l['seed']: write_scad(os.path.join(SEARCH, 'cand', f'L{l["seed"]}.scad'), l, 1) for l in batch}
    jobs = [(l['seed'], w) for l in batch for w in C.WANDER_SEEDS]
    with ThreadPoolExecutor(C.WORKERS) as ex:
        res = list(ex.map(lambda j: (j[0], C.eval_branches(scads[j[0]], j[1])), jobs))
    for l in batch:
        r = sorted([x for s, x in res if s == l['seed']], key=lambda x: x['score'])[0]
        st['branches'][str(l['seed'])] = r
        print(f'layout {l["seed"]}: {"PASS" if r["ok"] else "fail"} wander {r["wander"]} (merge {r["worst"]} %, '
              f'climb {r["climb"]} deg, bend {r["bend"]}x, {r["meets"]} meetings, score {r["score"]})')
    save(st)


def best_branch(st):
    ok = [(b['score'], s) for s, b in st['branches'].items() if b['ok']]
    assert ok, 'no layout passed the wander search'
    return min(ok)[1]


def stage_roots(st):
    lseed = best_branch(st)
    br = st['branches'][lseed]
    scad = write_scad(os.path.join(SEARCH, 'cand', 'roots.scad'), st['layouts'][lseed], br['wander'])
    with ThreadPoolExecutor(12) as ex:
        res = sorted(ex.map(lambda s: C.eval_roots(scad, s), range(1, 13)), key=lambda r: r['score'])
    st['roots'] = dict(layout=int(lseed), **res[0])
    print(f'layout {lseed}, wander {br["wander"]}: root seed {res[0]["root_seed"]} '
          f'({"PASS" if res[0]["ok"] else "fail"}, bend {res[0]["root_bend"]}x, reach {res[0]["reach"]} mm)')
    save(st)


def stage_write(st):
    r = st['roots']
    lseed = str(r['layout'])
    write_scad(SCAD, st['layouts'][lseed], st['branches'][lseed]['wander'], r['root_seed'])
    print(f'wrote {SCAD}: layout {lseed}, wander {st["branches"][lseed]["wander"]}, root seed {r["root_seed"]}')


if __name__ == '__main__':
    sys.stdout.reconfigure(line_buffering=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    st = state()
    for name, fn in (('layouts', stage_layouts), ('branches', stage_branches), ('roots', stage_roots),
                     ('write', stage_write)):
        if cmd in ('all', name):
            fn(st)
