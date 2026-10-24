"""Wall Climber Tree Catalogue: unique, print-verified Wall Climber Trees, end to end.

    python catalogue.py all             # run (or resume) every stage
    python catalogue.py layouts         # 1. a crown per design (Wall_Climber_Tree_layout.py, its own seed)
    python catalogue.py roots           # 2. a root system per design (root seed, count, meander)
    python catalogue.py build           # 3. .scad + tree and roots 3MFs (Bambu H2C) + PNGs + mesh checks + slices
    python catalogue.py check           # 4. fit and slide, floating regions (Wall_Climber_Tree_check.py)
    python catalogue.py image           # 5. Catalogue.png, a 5 x 5 grid, and the results table
    python catalogue.py angled          # 6. each design from the main design's angled-left view
    python catalogue.py brochure        # 7. Catalogue_Brochure.pdf (and its pages as PNGs in Brochure/)

Every design is the main design (../Wall_Climber_Tree.scad, iteration 7) with its own crown and
its own roots:
  crown   Wall_Climber_Tree_layout.py SEED TRIES --bend F, written next to the design as
          Wall_Climber_WCT_NN_layout.scad. Three bend tiers (TIERS): x1.0 as the main design, x1.5,
          and x2.2, where the main branches bend and twist hardest.
  roots   root_seed (its own, 100 + k), root_count 8..11 spread over the catalogue, and in the
          x2.2 tier more meander and sweep, so the roots bend more too.
Every stage records what it found in catalogue.json and skips work already done, so a stopped run
resumes where it left off.
"""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.dirname(HERE)
REPO = MAIN
while not os.path.isdir(os.path.join(REPO, 'tools')):
    REPO = os.path.dirname(REPO)
TOOLS = os.path.join(REPO, 'tools')

TEMPLATE = os.path.join(MAIN, 'Wall_Climber_Tree.scad')
LAYOUT = os.path.join(MAIN, 'Wall_Climber_Tree_layout.py')
CHECK = os.path.join(MAIN, 'Wall_Climber_Tree_check.py')
PREFIX, CODE = 'Wall_Climber', 'WCT'        # files Wall_Climber_WCT_NN.*
STATE = os.path.join(HERE, 'catalogue.json')
DESIGNS = os.path.join(HERE, 'Designs')
N = 25
# (first design, last design, bend factor, root meander mm, root sweep mm)
TIERS = [(1, 9, 1.0, 6.5, 20), (10, 17, 1.5, 7.0, 23), (18, 25, 2.2, 8.0, 26)]
LAYOUT_TRIES = 60                           # grown crowns per seed (about 60 % pass)
SEED_BASE = 7000                            # design k searches seed 7000 + 10 k (+1, +2 if none passes)
WOOD = '#6F5034'                            # Bambu PLA Basic Cocoa Brown
BUILDS = 5                                  # full builds at once (16 cores here)


def tier(k):
    return next(t for t in TIERS if t[0] <= k <= t[1])


def name_of(k):
    return f'{CODE}_{k:02d}'


def ddir(name):
    return os.path.join(DESIGNS, name)


def scad_of(name):
    return os.path.join(ddir(name), f'{PREFIX}_{name}.scad')


def state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {'designs': {}}


def save(st):
    json.dump(st, open(STATE + '.tmp', 'w'), indent=1)
    os.replace(STATE + '.tmp', STATE)


# ------------------------------------------------------------------ 1. layouts
def search_layout(k):
    name = name_of(k)
    bend = tier(k)[2]
    out = os.path.join(ddir(name), f'{PREFIX}_{name}_layout.scad')
    os.makedirs(ddir(name), exist_ok=True)
    for seed in (SEED_BASE + 10 * k, SEED_BASE + 10 * k + 1, SEED_BASE + 10 * k + 2):
        r = subprocess.run([sys.executable, LAYOUT, str(seed), str(LAYOUT_TRIES), out, '--bend', str(bend)],
                           capture_output=True, text=True)
        txt = r.stdout
        if r.returncode == 0 and 'wrote' in txt:
            g = lambda p: re.search(p, txt)
            a = g(r'(\d+) of (\d+) crowns passed; best: score ([\d.]+), tips ([\d.]+) mm apart, (\d+) meetings '
                  r'\(merge <= (\d+) %\), climb >= ([\d.]+)')
            b = g(r'main branches turn (\d+) deg on average; (\d+) mm head back')
            s = g(r'tips span x (-?\d+)\.\.(-?\d+), y (-?\d+)\.\.(-?\d+), z (-?\d+)\.\.(-?\d+)')
            return name, dict(seed=seed, bend_f=bend, passed=f'{a[1]}/{a[2]}', score=float(a[3]),
                              tip_gap=float(a[4]), meetings=int(a[5]), merge=int(a[6]), climb=float(a[7]),
                              turn=int(b[1]), wallward=int(b[2]), span_x=int(s[2]) - int(s[1]),
                              tips_z=f'{s[5]}..{s[6]}')
    return name, None


def stage_layouts(st):
    todo = [k for k in range(1, N + 1) if 'layout' not in st['designs'].get(name_of(k), {})]
    with ThreadPoolExecutor(12) as ex:
        for name, lay in ex.map(search_layout, todo):
            if lay is None:
                print(f'{name}: no crown passed on three seeds'); continue
            st['designs'].setdefault(name, {'name': name})['layout'] = lay
            save(st)
            print(f'{name}: seed {lay["seed"]} bend x{lay["bend_f"]}: turn {lay["turn"]} deg, '
                  f'{lay["wallward"]} mm back to the wall, span {lay["span_x"]} mm, {lay["meetings"]} meetings')


# ------------------------------------------------------------------ 2. roots
def stage_roots(st):
    for k in range(1, N + 1):
        d = st['designs'].get(name_of(k))
        if not d or 'roots' in d:
            continue
        _, _, _, meander, sweep = tier(k)
        # root seeds of their own (the main design uses 2), 8-11 roots spread over the catalogue
        d['roots'] = dict(root_seed=100 + k, root_count=[9, 10, 8, 11][k % 4], root_meander=meander, root_sweep=sweep)
    save(st)


# ------------------------------------------------------------------ 3. build
def sub1(pattern, repl, s):
    s2, n = re.subn(pattern, lambda m: repl, s, count=1)
    assert n == 1, f'pattern not found: {pattern}'
    return s2


def write_scad(d):
    name, lay, ro = d['name'], d['layout'], d['roots']
    raw = open(TEMPLATE, 'rb').read().decode('cp1252')
    nl = '\r\n' if '\r\n' in raw else '\n'
    s = raw.replace('\r\n', '\n')
    s = sub1(r'include <Wall_Climber_Tree_layout\.scad>', f'include <{PREFIX}_{name}_layout.scad>', s)
    for key in ('root_seed', 'root_count', 'root_meander', 'root_sweep'):
        s = sub1(rf'\n{key} = [\d.]+;', f'\n{key} = {ro[key]};', s)
    head = (f'// WALL CLIMBER TREE {name.replace("_", " ")} - a catalogue design (Wall Climber Tree/Catalogue/catalogue.py):\n'
            f'// crown: Wall_Climber_Tree_layout.py {lay["seed"]} {LAYOUT_TRIES} --bend {lay["bend_f"]:g}; roots: seed '
            f'{ro["root_seed"]}, {ro["root_count"]} roots, meander {ro["root_meander"]} mm, sweep {ro["root_sweep"]} mm.\n'
            f'// Otherwise the main design (iteration 7), described below.\n//\n')
    open(scad_of(name), 'wb').write((head + s).replace('\n', nl).encode('cp1252'))


def package(scad, name, part, extra=()):
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'build_design.py'), scad, '--name', name,
                        '--out', os.path.dirname(scad), '--part', f'{part}={WOOD}', *extra],
                       capture_output=True, text=True)
    txt = r.stdout + r.stderr
    g = lambda p: (re.search(p, txt) or [None, None])[1]
    return txt, dict(build_ok='BUILD: PASS' in txt, mesh_ok='RESULT: PASS' in txt, slice_ok='PASS: slicer check' in txt,
                     edges=g(r'edges\s+(boundary \d+\s+non-manifold \d+\s+shells \d+)'),
                     size=g(r'size\s+([\d.]+ x [\d.]+ x [\d.]+) mm'),
                     print_time=(g(r'print time (\S+ \S+ \S+)') or '').rstrip(','),
                     grams=float(g(r'\(total (\d+) g\)') or 0),
                     overhang60=g(r'past 60 deg above the bottom 1 cm = ([\d.]+%)'))


def build_one(st, name):
    d = st['designs'][name]
    write_scad(d)
    scad = scad_of(name)
    t = time.time()
    with ThreadPoolExecutor(2) as ex:
        ft = ex.submit(package, scad, f'Wall Climber {name}', 'tree')
        fr = ex.submit(package, scad, f'Wall Climber {name} Roots', 'roots', ('--define', 'part="roots"'))
        (lt, bt), (lr, br) = ft.result(), fr.result()
    open(os.path.join(ddir(name), 'build.log'), 'w', encoding='utf-8').write(
        '==== tree\n' + lt + '\n==== roots\n' + lr)
    return dict(tree=bt, roots=br, minutes=round((time.time() - t) / 60, 1))


def m3fs(name):
    return [os.path.join(ddir(name), f'{PREFIX}_{name}{s}.3mf') for s in ('', '_Roots')]


def stage_build(st):
    # also every design whose 3MFs are missing: they are not committed (.gitignore)
    todo = [n for n, d in sorted(st['designs'].items()) if 'roots' in d and
            (not (d.get('build', {}).get('tree', {}).get('build_ok') and d['build']['roots'].get('build_ok'))
             or not all(os.path.exists(p) for p in m3fs(n)))]
    with ThreadPoolExecutor(BUILDS) as ex:
        for n, b in zip(todo, ex.map(lambda n: build_one(st, n), todo)):
            st['designs'][n]['build'] = b
            st['designs'][n].pop('check', None)
            save(st)
            print(f'{n}: tree {"PASS" if b["tree"]["build_ok"] else "FAIL"} ({b["tree"]["size"]} mm, '
                  f'{b["tree"]["print_time"]}, {b["tree"]["grams"]:.0f} g, past 60 {b["tree"]["overhang60"]}), '
                  f'roots {"PASS" if b["roots"]["build_ok"] else "FAIL"} ({b["roots"]["print_time"]}, '
                  f'{b["roots"]["grams"]:.0f} g)  [{b["minutes"]} min]')


# ------------------------------------------------------------------ 4. check
def check_one(name):
    r = subprocess.run([sys.executable, CHECK, '--scad', scad_of(name), '--slide', '0,20,35'],
                       capture_output=True, text=True)
    txt = r.stdout + r.stderr
    open(os.path.join(ddir(name), 'check.log'), 'w', encoding='utf-8').write(txt)
    over = [float(x) for x in re.findall(r'overlap\s+(-?[\d.]+) mm3', txt)]
    fl = re.findall(r'(tree|roots): (PASS|FAIL): (\d+) regions', txt)
    return dict(ok='RESULT: PASS' in txt, fit_mm3=max(over) if over else None,
                floating={p: int(c) for p, _, c in fl})


def stage_check(st):
    todo = [n for n, d in sorted(st['designs'].items()) if 'build' in d and 'check' not in d]
    with ThreadPoolExecutor(4) as ex:
        for n, c in zip(todo, ex.map(check_one, todo)):
            st['designs'][n]['check'] = c
            save(st)
            print(f'{n}: {"PASS" if c["ok"] else "FAIL"} fit {c["fit_mm3"]} mm3, floating {c["floating"]}')


def verified(d):
    b, c = d.get('build', {}), d.get('check', {})
    return bool(b.get('tree', {}).get('build_ok') and b.get('roots', {}).get('build_ok') and c.get('ok'))


# ------------------------------------------------------------------ 5. image and table
def stage_image(st):
    from PIL import Image, ImageDraw, ImageFont, ImageChops
    F = 'C:/Windows/Fonts/'
    font = lambda n, s: ImageFont.truetype(F + n, s)
    TITLE, NAME, BODY = font('segoeuib.ttf', 46), font('segoeuib.ttf', 24), font('segoeui.ttf', 17)
    BG, INK, SOFT, ACCENT = (248, 248, 248), (40, 40, 40), (105, 105, 105), (111, 80, 52)
    names = sorted(st['designs'])
    COLS, CW, TH, CAP, PAD, TOP = 5, 420, 360, 72, 24, 150
    rows = (len(names) + COLS - 1) // COLS
    W = COLS * CW + (COLS + 1) * PAD
    canvas = Image.new('RGB', (W, TOP + rows * (TH + CAP + PAD) + 10), BG)
    d = ImageDraw.Draw(canvas)
    nv = sum(verified(st['designs'][n]) for n in names)
    d.text((PAD, 36), f'Wall Climber Tree Catalogue: {len(names)} unique trees', font=TITLE, fill=INK)
    d.text((PAD, 100), f'Every tree has its own grown crown and its own roots; rows 2-5 bend harder (x1.5 from WCT 10, '
                       f'x2.2 from WCT 18). {nv} of {len(names)} sliced and print-checked. Renders, not photos.',
           font=BODY, fill=SOFT)
    for k, n in enumerate(names):
        e = st['designs'][n]
        p = os.path.join(ddir(n), f'{PREFIX}_{n}.png')
        r, c = divmod(k, COLS)
        x0, y0 = PAD + c * (CW + PAD), TOP + r * (TH + CAP + PAD)
        if os.path.exists(p):
            im = Image.open(p).convert('RGB')
            im = im.crop(ImageChops.difference(im, Image.new('RGB', im.size, im.getpixel((0, 0)))).getbbox())
            s = min(TH / im.height, CW / im.width)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            canvas.paste(im, (x0 + (CW - im.width) // 2, y0 + TH - im.height))
        cx = x0 + CW / 2
        lay, ro = e['layout'], e['roots']
        for text, f, fill, dy in ((n.replace('_', ' ') + ('' if verified(e) else '  (FAIL)'), NAME, INK, 8),
                                  (f'crown {lay["seed"]} · bend ×{lay["bend_f"]:g} · roots {ro["root_seed"]} '
                                   f'({ro["root_count"]})', BODY, ACCENT, 40)):
            d.text((cx - d.textlength(text, font=f) / 2, y0 + TH + dy), text, font=f, fill=fill)
    canvas.save(os.path.join(HERE, 'Catalogue.png'), optimize=True)
    print('wrote Catalogue.png', canvas.size)
    L = ['| Design | Crown seed | Bend | Turn (avg) | Back to wall | Tip span | Climb | Meetings | Roots | '
         'Tree (mm) | Tree slice | Past 60° | Roots slice | Checks |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for n in names:
        e = st['designs'][n]
        lay, ro, b = e['layout'], e['roots'], e.get('build', {})
        t, rt = b.get('tree', {}), b.get('roots', {})
        L.append(f'| {n} | {lay["seed"]} | ×{lay["bend_f"]:g} | {lay["turn"]}° | {lay["wallward"]} mm | '
                 f'{lay["span_x"]} mm | ≥ {lay["climb"]}° | {lay["meetings"]} (≤ {lay["merge"]} %) | '
                 f'{ro["root_seed"]} ({ro["root_count"]}) | {t.get("size", "-")} | {t.get("print_time", "-")}, '
                 f'{t.get("grams", 0):.0f} g | {t.get("overhang60", "-")} | {rt.get("print_time", "-")}, '
                 f'{rt.get("grams", 0):.0f} g | {"PASS" if verified(e) else "**FAIL**"} |')
    open(os.path.join(HERE, 'catalogue_results.md'), 'w', encoding='utf-8').write(
        '# Catalogue results\n\nWritten by `catalogue.py image` from `catalogue.json`. Turn: how far the main '
        'branches (leader, limbs and their forks) turn over their length, on average. Back to wall: the length '
        'of main branch heading back towards the wall. Checks: both builds and slices, the fit and slide, and '
        'no floating regions.\n\n' + '\n'.join(L) + '\n')
    print('\n'.join(L))


# ------------------------------------------------------------------ 6. angled views
# The view of ../Wall_Climber_Tree_Angled_Left.png: 35 deg left of the front, 20 deg from above,
# the whole assembly with its bark, unturned (face_az = 0).
ANGLED = ['--camera=0,0,0,70,0,145,500', '--viewall', '--autocenter', '--projection=p', '--imgsize=1600,1400',
          '--colorscheme=Tomorrow', '-D', 'face_az=0']


def angled_png(name):
    return os.path.join(ddir(name), f'{PREFIX}_{name}_Angled.png')


def render_angled(scad, out):
    sys.path.insert(0, TOOLS)
    from render_png import openscad_cmd
    from PIL import Image, ImageChops
    subprocess.run([*openscad_cmd(), '-o', out, *ANGLED, scad], capture_output=True, text=True)
    im = Image.open(out).convert('RGB')
    x0, y0, x1, y1 = ImageChops.difference(im, Image.new('RGB', im.size, im.getpixel((0, 0)))).getbbox()
    im.crop((max(0, x0 - 30), max(0, y0 - 30), min(im.width, x1 + 30), min(im.height, y1 + 30))).save(out)
    return out


def stage_angled(st):
    todo = [n for n in sorted(st['designs']) if 'build' in st['designs'][n] and
            (not os.path.exists(angled_png(n)) or os.path.getmtime(angled_png(n)) < os.path.getmtime(scad_of(n)))]
    with ThreadPoolExecutor(6) as ex:
        for out in ex.map(lambda n: render_angled(scad_of(n), angled_png(n)), todo):
            print('rendered', os.path.relpath(out, HERE))


# ------------------------------------------------------------------ 7. brochure
TIER_NAME = {1.0: ('Grown', 'bends like the main design'), 1.5: ('Swaying', 'bends half as hard again'),
             2.2: ('Wild', 'bends and twists hardest')}


def stage_brochure(st):
    """Catalogue_Brochure.pdf: a cover with the main design, an index of all 25, two designs a page
    with their angled view and numbers, and a page on printing and hanging them."""
    from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
    F = 'C:/Windows/Fonts/'
    font = lambda n, s: ImageFont.truetype(F + n, s)
    W, H, M = 1754, 2480, 130                                # A4 portrait at 212 dpi
    PAPER, INK, SOFT, BARK, RULE = (250, 246, 239), (46, 36, 28), (120, 104, 90), (111, 80, 52), (222, 210, 196)
    SERIF, SERIF_I, SANS, SANS_B = 'georgia.ttf', 'georgiai.ttf', 'segoeui.ttf', 'segoeuib.ttf'

    def cutout(path):
        """The render on the paper: its flat background made transparent."""
        im = Image.open(path).convert('RGB')
        bg = Image.new('RGB', im.size, im.getpixel((0, 0)))
        mask = ImageChops.difference(im, bg).convert('L').point(lambda v: 255 if v > 10 else v * 25)
        mask = mask.filter(ImageFilter.GaussianBlur(0.6))
        im.putalpha(mask)
        return im.crop(mask.getbbox())

    def fit(im, w, h):
        s = min(w / im.width, h / im.height)
        return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)

    def page():
        p = Image.new('RGB', (W, H), PAPER)
        return p, ImageDraw.Draw(p)

    def footer(d, n):
        d.line((M, H - 110, W - M, H - 110), fill=RULE, width=2)
        d.text((M, H - 92), 'Wall Climber Tree · Catalogue', font=font(SANS, 26), fill=SOFT)
        t = str(n)
        d.text((W - M - d.textlength(t, font=font(SANS, 26)), H - 92), t, font=font(SANS, 26), fill=SOFT)

    def para(d, xy, text, f, fill, width, gap=1.45):
        x, y = xy
        line = ''
        for w in text.split():
            if d.textlength(line + ' ' + w if line else w, font=f) > width:
                d.text((x, y), line, font=f, fill=fill)
                y += f.size * gap
                line = w
            else:
                line = line + ' ' + w if line else w
        if line:
            d.text((x, y), line, font=f, fill=fill)
            y += f.size * gap
        return y

    names = sorted(st['designs'])
    pages = []

    # cover
    p, d = page()
    d.text((M, 150), 'WALL CLIMBER TREE', font=font(SANS_B, 40), fill=BARK)
    d.text((M, 205), 'A catalogue of 25 grown trees', font=font(SERIF, 96), fill=INK)
    para(d, (M, 340), 'Trees that grow out of the wall, for climbing and sprawling plants. Every tree is grown '
         'branch by branch, bending and twisting as it goes, and every one is printed without supports.',
         font(SERIF_I, 38), SOFT, W - 2 * M)
    hero = fit(cutout(os.path.join(MAIN, 'Wall_Climber_Tree_Angled_Left.png')), W - 2 * M, 1500)
    p.paste(hero, ((W - hero.width) // 2, 520 + (1500 - hero.height) // 2), hero)
    d.text((M, 2090), 'The main design', font=font(SANS_B, 30), fill=INK)
    para(d, (M, 2135), 'Iteration 7: the tree the catalogue grows from. 285 × 142 × 183 mm, '
         'Cocoa Brown PLA. The 25 designs that follow each have their own crown and their own roots.',
         font(SANS, 28), SOFT, W - 2 * M)
    footer(d, 1)
    pages.append(p)

    # index: all 25, 5 x 5
    p, d = page()
    d.text((M, 150), 'The collection', font=font(SERIF, 80), fill=INK)
    y = para(d, (M, 260), 'Three families, by how hard the branches bend. All share the same burl, slide '
             'and screw; crowns and roots are grown anew for each.', font(SANS, 30), SOFT, W - 2 * M)
    tx = M
    for f, (title, sub) in TIER_NAME.items():
        ks = [n for n in names if st['designs'][n]['layout']['bend_f'] == f]
        d.text((tx, y + 20), f'{title} · {ks[0][-2:]}–{ks[-1][-2:]}', font=font(SANS_B, 28), fill=BARK)
        d.text((tx, y + 58), sub, font=font(SANS, 24), fill=SOFT)
        tx += (W - 2 * M) // 3
    gy, cw, ch = int(y + 140), (W - 2 * M) // 5, 370
    for k, n in enumerate(names):
        r, c = divmod(k, 5)
        x0, y0 = M + c * cw, gy + r * (ch + 10)
        th = fit(cutout(angled_png(n)), cw - 16, ch - 60)
        p.paste(th, (x0 + (cw - th.width) // 2, y0 + ch - 60 - th.height), th)
        t = n.replace('_', ' ')
        d.text((x0 + (cw - d.textlength(t, font=font(SANS_B, 26))) / 2, y0 + ch - 48), t,
               font=font(SANS_B, 26), fill=INK)
    footer(d, 2)
    pages.append(p)

    # two designs a page
    def spec_block(d, x, y, n):
        e = st['designs'][n]
        lay, ro, b = e['layout'], e['roots'], e['build']
        t, rt = b['tree'], b['roots']
        title, sub = TIER_NAME[lay['bend_f']]
        hm = lambda s: s.rsplit(' ', 1)[0]                   # '3h 38m 39s' -> '3h 38m'
        d.text((x, y), n.replace('_', ' '), font=font(SERIF, 76), fill=INK)
        d.text((x, y + 100), f'{title} · ×{lay["bend_f"]:g} bend', font=font(SANS_B, 30), fill=BARK)
        rows = [('Branches turn', f'{lay["turn"]}° on average'),
                ('Back to the wall', f'{lay["wallward"]} mm of branch'),
                ('Tips span', f'{lay["span_x"]} mm along the wall'),
                ('Roots', f'{ro["root_count"]}, meander {ro["root_meander"]:g} mm'),
                ('Tree', t['size'].replace(' x ', ' × ') + ' mm'),
                ('Print, tree', f'{hm(t["print_time"])}, {t["grams"]:.0f} g'),
                ('Print, roots', f'{hm(rt["print_time"])}, {rt["grams"]:.0f} g'),
                ('Seeds', f'crown {lay["seed"]} · roots {ro["root_seed"]}')]
        yy = y + 175
        for k, v in rows:
            d.text((x, yy), k, font=font(SANS, 24), fill=SOFT)
            d.text((x, yy + 30), v, font=font(SANS_B, 28), fill=INK)
            yy += 82
        ok = verified(e)
        d.text((x, yy + 10), 'Print-checked' if ok else 'Not verified', font=font(SANS_B, 26),
               fill=(70, 110, 60) if ok else (160, 50, 40))

    for i in range(0, len(names), 2):
        p, d = page()
        pair = names[i:i + 2]
        for j, n in enumerate(pair):
            y0 = M + j * 1120
            img = fit(cutout(angled_png(n)), 1080, 1040)
            p.paste(img, (M + (1080 - img.width) // 2, y0 + (1040 - img.height) // 2), img)
            spec_block(d, M + 1140, y0 + 40, n)
            if j == 0 and len(pair) == 2:
                d.line((M, y0 + 1080, W - M, y0 + 1080), fill=RULE, width=2)
        footer(d, len(pages) + 1)
        pages.append(p)

    # printing and hanging
    p, d = page()
    d.text((M, 150), 'Printing and hanging', font=font(SERIF, 80), fill=INK)
    ex = fit(cutout(os.path.join(MAIN, 'Wall_Climber_Tree_Exploded.png')), W - 2 * M, 900)
    p.paste(ex, ((W - ex.width) // 2, 300), ex)
    y = 300 + ex.height + 60
    for head, body in (
            ('Two parts', 'The roots print flat on their back. The tree prints standing, just as it hangs, with no '
                          'supports: every branch climbs at least 32°, inside the 60° overhang limit. Use a brim; '
                          'the tree stands on a 4 cm² foot.'),
            ('Material', 'Bambu PLA Basic, Cocoa Brown #6F5034. Bambu Lab H2C, 0.4 mm nozzle, 0.20 mm Standard, '
                         '35 % sparse infill. The widest trees need the full bed.'),
            ('Hanging', '1. Hold the roots against the wall. 2. Slide the tree down the dovetail until its foot '
                        "sits on the burl's shelf. 3. Drive one 6 mm screw (6 × 50 mm or longer, with a wall plug) "
                        'through the knot hole under the trunk: the tree clamps the roots to the wall.'),
            ('Every design is checked', 'Both parts: one closed solid, overhang under 0.5 % of the surface, no '
                                        'region starting in mid-air, a clean Bambu Studio slice, and a slide that '
                                        'fits with 0 mm³ of overlap all the way in.')):
        d.text((M, y), head, font=font(SANS_B, 32), fill=BARK)
        y = para(d, (M, y + 50), body, font(SANS, 29), INK, W - 2 * M) + 30
    footer(d, len(pages) + 1)
    pages.append(p)

    Image.init()                                             # registers JPEG, which the PDF writer uses
    out = os.path.join(HERE, 'Catalogue_Brochure.pdf')
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=212, quality=88)
    os.makedirs(os.path.join(HERE, 'Brochure'), exist_ok=True)
    for k, pg in enumerate(pages, 1):
        pg.resize((W // 2, H // 2), Image.LANCZOS).save(os.path.join(HERE, 'Brochure', f'page_{k:02d}.png'),
                                                       optimize=True)
    print('wrote', out, len(pages), 'pages')


if __name__ == '__main__':
    sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    st = state()
    if cmd in ('all', 'layouts'):
        stage_layouts(st)
    if cmd in ('all', 'roots'):
        stage_roots(st)
    if cmd in ('all', 'build'):
        stage_build(st)
    if cmd in ('all', 'check'):
        stage_check(st)
    if cmd in ('all', 'image'):
        stage_image(st)
    if cmd in ('all', 'angled'):
        stage_angled(st)
    if cmd in ('all', 'brochure'):
        stage_brochure(st)
