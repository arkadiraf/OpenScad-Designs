"""Grand Chaotic Tree Catalogue: unique, print-verified Grand Chaotic Trees, end to end.

    python catalogue.py all [N]       # run (or resume) every stage until N designs pass (default 25)
    python catalogue.py layouts       # 1. branch-layout search over LAYOUT_SEEDS
    python catalogue.py branches [N]  # 2. wander seed per layout, until N layouts pass
    python catalogue.py roots         # 3. root system (root_count, root_seed) per design
    python catalogue.py build         # 4. .scad + 3MF (Bambu H2C) + PNG + mesh checks + Bambu slice
    python catalogue.py check         # 5. glass clearance and seat (from the build's mesh check), shells
    python catalogue.py image         # 6. Catalogue.png, a 5 x 5 grid, and the results table

Every stage records what it found in catalogue.json and skips work already done, so a stopped run
resumes where it left off. Each design is Grand_Chaotic_Tree_template.scad with five things filled
in: limb_table and fork_table (a 3 -> 7 -> 13 branch layout from Grand_Chaotic_Tree_layout.py),
wander_seed (how every branch wanders), root_seed and root_count (the whole root system).
README.md explains the criteria: the Grand Chaotic Tree's own (a 100 x 200 mm glass standing on the
limbs 80 mm up with 1 mm clearance, a 320 mm limit, a 310 mm root spread), with the catalogue
method of ../Wild Chalice Tree Catalogue (this file started as a copy of its catalogue.py).
"""
import json, os, re, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
TOOLS = os.path.join(REPO, 'tools')
sys.path.insert(0, TOOLS)
from render_png import openscad_cmd   # noqa: E402
from member_clearance import load     # noqa: E402
from mesh_check import load as load_mesh   # noqa: E402

TEMPLATE = os.path.join(HERE, 'Grand_Chaotic_Tree_template.scad')
LAYOUT = os.path.join(HERE, 'Grand_Chaotic_Tree_layout.py')
PREFIX, CODE = 'Grand_Chaotic', 'GCT'      # files Grand_Chaotic_GCT_NN.*
TOTAL_H, ROOT_SPREAD, LIFT = 320, 310, 80
MESH_CHECK = '--bore-r 51 --floor-h 80 --foot-r 3'   # the 1 mm clearance, and the pads the glass stands on
STATE = os.path.join(HERE, 'catalogue.json')
SEARCH = os.path.join(HERE, 'search')
DESIGNS = os.path.join(HERE, 'Designs')
LAYOUT_SEEDS = list(range(5001, 5061))     # 60 layout searches
LAYOUT_TREES = 4000                        # random trees per layout seed
WANDER_SEEDS = range(1, 25)                # the original's wander seed was the best of 48
ROOT_SEEDS = 12                            # root seeds tried per design, from its own range
ROOT_BASE = 5000                           # design k tries ROOT_BASE + 100k + 1 ...
WOOD = '#6F5034'                           # Bambu PLA Basic Cocoa Brown
WORKERS = 14                               # OpenSCAD path evaluations at once (16 cores here)
BUILDS = 5                                 # full builds at once


# ------------------------------------------------------------------ state and .scad writing
def state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {'layouts': {}, 'branches': {}, 'designs': {}}


def save(st):
    json.dump(st, open(STATE + '.tmp', 'w'), indent=1)
    os.replace(STATE + '.tmp', STATE)


def fmt_rows(rows):
    return '[\n' + ',\n'.join('    [' + ', '.join(f'{v:>5}' if isinstance(v, float) else f'{v:>4}' for v in r) + ']'
                              for r in rows) + ']'


def sub1(pattern, repl, s, flags=0):
    s2, n = re.subn(pattern, lambda m: repl, s, count=1, flags=flags)
    assert n == 1, f'pattern not found: {pattern}'
    return s2


def write_scad(path, title, lay, wander, root_seed=1, root_count=9):
    raw = open(TEMPLATE, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    s = raw.replace('\r\n', '\n')
    s = sub1(r'limb_table = \[.*?\]\];', 'limb_table = ' + fmt_rows(lay['limbs']) + ';', s, flags=re.S)
    s = sub1(r'fork_table = \[.*?\]\];', 'fork_table = ' + fmt_rows(lay['forks']) + ';', s, flags=re.S)
    s = sub1(r'wander_seed = \d+;', f'wander_seed = {wander};', s)
    s = sub1(r'root_seed = \d+;', f'root_seed = {root_seed};', s)
    s = sub1(r'root_count = \d+;', f'root_count = {root_count};', s)
    # the template still describes the original's layout (seed 43): replace that paragraph
    s = sub1(r'// The layout came from a search over random 3 -> 7 -> 13 trees for the smallest\n.*?'
             r'// turns back halfway up\.\n',
             f'// The layout came from a search over random 3 -> 7 -> 13 trees for the smallest empty\n'
             f'// sector around the glass, a tripod seat and no stacked arches:\n'
             f'// Layout: Grand_Chaotic_Tree_layout.py {lay["seed"]} {LAYOUT_TREES} (largest empty sector '
             f'{lay["gap"]} deg, seat {lay["seat"]} deg)\n', s, flags=re.S)
    s = sub1(r'// GRAND CHAOTIC TREE, CATALOGUE TEMPLATE[^\n]*\n(//[^\n]*\n){3}',
             f'// GRAND CHAOTIC TREE {title} - a catalogue design (Grand Chaotic Tree Catalogue/catalogue.py):\n'
             f'// branch layout {lay["seed"]}, wander seed {wander}, root seed {root_seed}, {root_count} roots.\n', s)
    s = sub1(r'echo\(str\("Grand Chaotic Tree TEMPLATE \| ', f'echo(str("Grand Chaotic Tree {title} | ', s)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
    return path


def paths_echo(scad, defines):
    fd, echo = tempfile.mkstemp(suffix='.echo'); os.close(fd)
    subprocess.run([*openscad_cmd(), '-o', echo, '-D', 'part="paths"', *[x for d in defines for x in ('-D', d)], scad],
                   capture_output=True, text=True)
    return echo


def tightest_bend(P, R, k=4):
    """Smallest circumradius through centreline points k apart, over the tube radius there."""
    if len(P) < 2 * k + 1:
        return 99.0
    a, b, c = P[:-2 * k], P[k:-k], P[2 * k:]
    ab, bc, ca = (np.linalg.norm(x, axis=1) for x in (b - a, c - b, a - c))
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
    return float(np.min(ab * bc * ca / np.maximum(4 * area, 1e-9) / R[k:-k]))


# ------------------------------------------------------------------ 1. layouts
def stage_layouts(st):
    os.makedirs(os.path.join(SEARCH, 'layouts'), exist_ok=True)
    todo = [s for s in LAYOUT_SEEDS if str(s) not in st['layouts']]

    def run(seed):
        out = subprocess.run([sys.executable, LAYOUT, str(seed),
                              str(LAYOUT_TREES)], capture_output=True, text=True).stdout
        open(os.path.join(SEARCH, 'layouts', f'seed_{seed}.txt'), 'w').write(out)
        lines = out.splitlines()
        g = re.search(r'worst gap (\d+) seat gap (\d+)', lines[1])
        return seed, dict(seed=seed, score=float(lines[0].split()[2]), gap=int(g[1]), seat=int(g[2]),
                          **json.loads(lines[-1]))
    with ThreadPoolExecutor(15) as ex:
        for seed, lay in ex.map(run, todo):
            st['layouts'][str(seed)] = lay
            print(f'layout {seed}: score {lay["score"]}, largest empty sector {lay["gap"]} deg')
    save(st)


# ------------------------------------------------------------------ 2. branches
def eval_branches(scad, seed):
    echo = paths_echo(scad, [f'wander_seed={seed}'])
    try:
        txt = open(echo, encoding='utf-8', errors='replace').read()
        summ = re.search(r'meeting points \[branch, under, z, arch\]: (\[.*?\]\]|\[\]) \| climb >= (-?\d+)', txt)
        meets = json.loads(summ[1]); climb = int(summ[2])
        cl = subprocess.run([sys.executable, os.path.join(TOOLS, 'member_clearance.py'), echo, '--floor', str(LIFT),
                             '--top', '1'], capture_output=True, text=True).stdout
        worst = int(re.search(r'worst overlap (\d+) %', cl)[1])
        caps = subprocess.run([sys.executable, os.path.join(TOOLS, 'cap_height.py'), echo, '--limit', str(TOTAL_H)],
                              capture_output=True, text=True).returncode == 0
        bend = min(tightest_bend(m['P'], m['R']) for n, m in load(echo).items() if n.startswith('b'))
    finally:
        os.remove(echo)
    arch = max([m[3] for m in meets] + [0])
    ok = worst <= 30 and climb >= 30 and caps and bend >= 1.25
    score = (0 if ok else 1000) + worst + 0.5 * arch + 3 * max(0, 33 - climb) + 20 * max(0, 1.4 - bend)
    return dict(wander=seed, ok=ok, score=round(score, 1), worst=worst, climb=climb, arch=arch,
                meets=len(meets), bend=round(bend, 2))


def stage_branches(st, want):
    order = sorted(st['layouts'].values(), key=lambda l: l['score'])
    while sum(b['ok'] for b in st['branches'].values()) < want:
        batch = [l for l in order if str(l['seed']) not in st['branches']][:6]
        if not batch:
            print('out of layouts: add seeds to LAYOUT_SEEDS'); break
        scads = {l['seed']: write_scad(os.path.join(SEARCH, 'cand', f'L{l["seed"]}.scad'), f'L{l["seed"]}', l, 4)
                 for l in batch}
        jobs = [(l['seed'], w) for l in batch for w in WANDER_SEEDS]
        with ThreadPoolExecutor(WORKERS) as ex:
            res = list(ex.map(lambda j: (j[0], eval_branches(scads[j[0]], j[1])), jobs))
        for l in batch:
            r = sorted([x for s, x in res if s == l['seed']], key=lambda x: x['score'])[0]
            st['branches'][str(l['seed'])] = r
            print(f'layout {l["seed"]}: {"PASS" if r["ok"] else "fail"} wander {r["wander"]} (merge {r["worst"]} %, '
                  f'climb {r["climb"]} deg, bend {r["bend"]}x)')
        save(st)
        print(f'{sum(b["ok"] for b in st["branches"].values())} layouts pass so far')


# ------------------------------------------------------------------ 3. roots
def eval_roots(scad, seed):
    echo = paths_echo(scad, [f'root_seed={seed}'])
    try:
        M = {n: m for n, m in load(echo).items() if 'root' in n}
    finally:
        os.remove(echo)
    bend = min(tightest_bend(m['P'], m['R']) for m in M.values())
    reach = max(float(np.max(np.hypot(m['P'][:, 0], m['P'][:, 1]) + m['R'])) for m in M.values())
    tips = np.sort([np.degrees(np.arctan2(m['P'][-1, 1], m['P'][-1, 0])) % 360 for n, m in M.items()
                    if n.startswith('root')])
    gap = float(np.max(np.diff(np.concatenate([tips, [tips[0] + 360]]))))
    side = sum(n.startswith('twigroot') for n in M)
    ok = bend >= 1.25 and reach <= ROOT_SPREAD / 2 + 2
    score = (0 if ok else 1000) + gap + 20 * max(0, 1.5 - bend) + 15 * max(0, 3 - side)
    return dict(root_seed=seed, ok=ok, score=round(score, 1), root_bend=round(bend, 2), reach=round(reach, 1),
                tip_gap=round(gap), side_roots=side)


def design_ids(st):
    passing = sorted([s for s, b in st['branches'].items() if b['ok']], key=lambda s: st['branches'][s]['score'])
    return passing


def stage_roots(st, want):
    for k, lseed in enumerate(design_ids(st)[:want], 1):
        name = f'{CODE}_{k:02d}'
        d = st['designs'].get(name)
        if d and d['layout'] == int(lseed) and d.get('root_seed', 0) > ROOT_BASE:
            continue
        lay, br = st['layouts'][lseed], st['branches'][lseed]
        count = [8, 9, 10, 11][(k * 3) % 4]                      # 8-11 roots, spread over the catalogue
        scad = write_scad(os.path.join(SEARCH, 'cand', f'{name}.scad'), name, lay, br['wander'], 1, count)
        # a range of its own: no shared root systems, here or with the earlier rounds (Wander used 101-512)
        seeds = range(ROOT_BASE + 100 * k + 1, ROOT_BASE + 100 * k + 1 + ROOT_SEEDS)
        with ThreadPoolExecutor(WORKERS) as ex:
            res = sorted(ex.map(lambda s: eval_roots(scad, s), seeds), key=lambda r: r['score'])
        r = res[0]
        st['designs'][name] = dict(name=name, layout=int(lseed), wander=br['wander'], root_count=count,
                                   branch=br, roots=r, root_seed=r['root_seed'])
        print(f'{name}: layout {lseed}, wander {br["wander"]}, {count} roots, root seed {r["root_seed"]} '
              f'({"PASS" if r["ok"] else "fail"}, bend {r["root_bend"]}x, {r["side_roots"]} side roots)')
        save(st)


# ------------------------------------------------------------------ 4. build
def design_scad(name):
    return os.path.join(DESIGNS, name, f'{PREFIX}_{name}.scad')


def build_one(st, name):
    d = st['designs'][name]
    scad = write_scad(design_scad(name), name.replace('_', ' '), st['layouts'][str(d['layout'])], d['wander'],
                      d['root_seed'], d['root_count'])
    log = os.path.join(DESIGNS, name, 'build.log')
    t = time.time()
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'build_design.py'), scad,
                        '--name', f'{PREFIX.replace("_", " ")} {name}', '--out', os.path.dirname(scad),
                        '--part', f'wood={WOOD}', '--check-args', MESH_CHECK], capture_output=True, text=True)
    txt = r.stdout + r.stderr
    open(log, 'w', encoding='utf-8').write(txt)
    g = lambda p: (re.search(p, txt) or [None, None])[1]
    return dict(build_ok='BUILD: PASS' in txt, mesh_ok='RESULT: PASS' in txt, slice_ok='PASS: slicer check' in txt,
                size=g(r'size\s+([\d.]+ x [\d.]+ x [\d.]+) mm'), print_time=(g(r'print time (\S+ \S+ \S+)') or '').rstrip(','),
                grams=float(g(r'\(total (\d+) g\)') or 0), overhang60=g(r'past 60 deg above the bottom 1 cm = ([\d.]+%)'),
                minutes=round((time.time() - t) / 60, 1))


def stage_build(st):
    todo = [n for n, d in sorted(st['designs'].items()) if not d.get('build', {}).get('build_ok')]
    with ThreadPoolExecutor(BUILDS) as ex:
        for n, b in zip(todo, ex.map(lambda n: build_one(st, n), todo)):
            st['designs'][n]['build'] = b
            save(st)
            print(f'{n}: build {"PASS" if b["build_ok"] else "FAIL"}, slice {"PASS" if b["slice_ok"] else "FAIL"}, '
                  f'{b["size"]} mm, {b["print_time"]}, {b["grams"]:.0f} g ({b["minutes"]} min)')


# ------------------------------------------------------------------ 5. check
def shells(path):
    """Connected pieces of the mesh with their signed volumes, largest first."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    out = []
    for _, V, F in load_mesh(path):
        e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]]])
        _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(V), len(V))),
                                      directed=False)
        fl = lab[F[:, 0]]
        for r in np.unique(fl):
            T = V[F[fl == r]]
            out.append(float(np.einsum('ij,ij->i', T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6))
    return sorted(out, reverse=True)


def check_one(name):
    m3f = os.path.join(DESIGNS, name, f'{PREFIX}_{name}.3mf')
    # the glass here has a straight side, so mesh_check.py --foot-r (run by the build, MESH_CHECK)
    # measures it exactly: nothing inside the glass or its 1 mm clearance, and the pads it stands on
    log = open(os.path.join(DESIGNS, name, 'build.log'), encoding='utf-8').read()
    vols = shells(m3f)
    g = re.search(r'seat\s+([\d.]+) cm2 of pads .*largest gap between them (\d+) deg', log)
    c = re.search(r'(PASS|FAIL): closest material to the glass (-?[\d.]+) mm', log)
    steady = re.search(r'(PASS|FAIL): the glass stands steady', log)
    # one solid body; any other shell must be an internal void (negative volume) left where merged
    # branches overlap, which the slicer fills, or a degenerate sliver of no volume at all (the Wild
    # Chalice catalogue's WCT_10 has a flat 4-vertex one); a loose piece has real volume
    solid = len([v for v in vols if v > 0.01]) == 1
    return dict(seat_ok=bool(g and c and steady and c[1] == 'PASS' and steady[1] == 'PASS'),
                seat_cm2=float(g[1]) if g else 0, seat_gap=int(g[2]) if g else 360, glass_clear=float(c[2]) if c else -99,
                solid_ok=solid, voids=len(vols) - 1, void_mm3=round(-sum(v for v in vols if v < 0), 4), solid_mm3=[round(v, 4) for v in vols])


def stage_check(st):
    todo = [n for n, d in sorted(st['designs'].items()) if d.get('build', {}).get('build_ok') and 'check' not in d]
    with ThreadPoolExecutor(6) as ex:
        for n, c in zip(todo, ex.map(check_one, todo)):
            st['designs'][n]['check'] = c
            save(st)
            print(f'{n}: seat {"PASS" if c["seat_ok"] else "FAIL"} {c["seat_cm2"]} cm2 gap {c["seat_gap"]} deg, '
                  f'{"one solid" if c["solid_ok"] else "LOOSE PIECES"}, {c["voids"]} internal voids')


def verified(d):
    b, c = d.get('build', {}), d.get('check', {})
    return bool(b.get('build_ok') and b.get('slice_ok') and c.get('seat_ok') and c.get('solid_ok'))


# ------------------------------------------------------------------ 6. image and table
def stage_image(st):
    from PIL import Image, ImageDraw, ImageFont
    F = 'C:/Windows/Fonts/'
    font = lambda n, s: ImageFont.truetype(F + n, s)
    TITLE, NAME, BODY = font('segoeuib.ttf', 46), font('segoeuib.ttf', 24), font('segoeui.ttf', 17)
    BG, INK, SOFT, ACCENT = (248, 248, 248), (40, 40, 40), (105, 105, 105), (111, 80, 52)
    names = [n for n, d in sorted(st['designs'].items()) if verified(d)][:25]
    COLS, CW, TH, CAP, PAD, TOP = 5, 380, 600, 72, 24, 150
    rows = (len(names) + COLS - 1) // COLS
    W = COLS * CW + (COLS + 1) * PAD
    canvas = Image.new('RGB', (W, TOP + rows * (TH + CAP + PAD) + 10), BG)
    d = ImageDraw.Draw(canvas)
    d.text((PAD, 36), f'Grand Chaotic Tree Catalogue: {len(names)} unique trees', font=TITLE, fill=INK)
    d.text((PAD, 100), 'One 100 × 200 mm glass, standing 80 mm up on three limbs. Every tree has its own branch layout, branch wander '
                       'and root system, and every one is sliced and print-checked. Renders, not photos.',
           font=BODY, fill=SOFT)
    for k, n in enumerate(names):
        e = st['designs'][n]
        im = Image.open(os.path.join(DESIGNS, n, f'{PREFIX}_{n}.png')).convert('RGB')
        s = min(TH / im.height, CW / im.width)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        r, c = divmod(k, COLS)
        x0, y0 = PAD + c * (CW + PAD), TOP + r * (TH + CAP + PAD)
        canvas.paste(im, (x0 + (CW - im.width) // 2, y0 + TH - im.height))
        cx = x0 + CW / 2
        for text, f, fill, dy in ((n.replace('_', ' '), NAME, INK, 8),
                                  (f'layout {e["layout"]} · wander {e["wander"]} · roots {e["root_seed"]} '
                                   f'({e["root_count"]})', BODY, ACCENT, 40)):
            d.text((cx - d.textlength(text, font=f) / 2, y0 + TH + dy), text, font=f, fill=fill)
    canvas.save(os.path.join(HERE, 'Catalogue.png'), optimize=True)
    print('wrote Catalogue.png', canvas.size)
    # results table
    L = ['| Design | Layout | Wander | Roots | Size (mm) | Branch merge | Climb | Seat | H2C slice (35 %) | Checks |',
         '|---|---|---|---|---|---|---|---|---|---|']
    for n, e in sorted(st['designs'].items()):
        b, c, br = e.get('build', {}), e.get('check', {}), e['branch']
        L.append(f'| {n} | {e["layout"]} | {e["wander"]} | {e["root_seed"]} ({e["root_count"]}) | {b.get("size", "-")} | '
                 f'{br["worst"]} % | {br["climb"]}° | {c.get("seat_cm2", "-")} cm², {c.get("seat_gap", "-")}° | '
                 f'{b.get("print_time", "-").rstrip(",")}, {b.get("grams", 0):.0f} g | '
                 f'{"PASS" if verified(e) else "**FAIL**"}{" (" + str(c["voids"]) + " voids)" if c.get("voids") else ""} |')
    open(os.path.join(HERE, 'catalogue_results.md'), 'w', encoding='utf-8').write(
        '# Catalogue results\n\nWritten by `catalogue.py image` from `catalogue.json`.\n\n' + '\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    sys.stdout.reconfigure(line_buffering=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    st = state()
    if cmd in ('all', 'layouts'):
        stage_layouts(st)
    if cmd in ('all', 'branches'):
        stage_branches(st, want)
    if cmd in ('all', 'roots'):
        stage_roots(st, want)
    if cmd in ('all', 'build'):
        stage_build(st)
    if cmd in ('all', 'check'):
        stage_check(st)
    if cmd in ('all', 'image'):
        stage_image(st)
