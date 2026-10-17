"""Wild Chalice Tree variants: the same tree and glass (80 x 130 mm, base curving in to a 50 mm
bottom, cupped 85 mm up with zero clearance), each with its own searched branch layout.

    python make_variants.py            # write every variant's .scad from VARIANTS
    python make_variants.py --png      # and render its isometric PNG (nightly OpenSCAD)

Each variant is ../Wild_Chalice_Tree.scad with `limb_table`, `fork_table` and `wander_seed`
replaced; nothing else changes. The tables come from ../Wild_Chalice_Tree_layout.py:

    python ../Wild_Chalice_Tree_layout.py SEED 4000

(12 seeds tried x 4000 trees). `wander` is the wander seed picked for each layout by
wander_search.py. Seeds 733 and 1129 scored well in the search but no wander seed (1-24) kept
them under a 30 % merge with a 30 deg climb, so 1301 and 307 replaced them (617, 401, 1031, 523
and 1213 were also tried with wander seeds 1-16).
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'Wild_Chalice_Tree.scad')
TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'tools')

# name: (layout seed, wander seed, largest empty sector, seat, layout JSON)
VARIANTS = json.load(open(os.path.join(HERE, 'variants.json')))


def fmt_rows(rows):
    out = []
    for r in rows:
        out.append('    [' + ', '.join(f'{v:>4}' if not isinstance(v, float) else f'{v:>5}' for v in r) + ']')
    return '[\n' + ',\n'.join(out) + ']'


def write_scad(name, v):
    raw = open(SRC, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'      # keep the source's line endings
    s = raw.replace('\r\n', '\n')
    s = re.sub(r'limb_table = \[.*?\]\];', 'limb_table = ' + fmt_rows(v['limbs']) + ';', s, count=1, flags=re.S)
    s = re.sub(r'fork_table = \[.*?\]\];', 'fork_table = ' + fmt_rows(v['forks']) + ';', s, count=1, flags=re.S)
    s = re.sub(r'wander_seed = \d+;', f'wander_seed = {v["wander"]};', s, count=1)
    s = re.sub(r'// Layout: Wild_Chalice_Tree_layout\.py .*',
               f'// Layout: Wild_Chalice_Tree_layout.py {v["seed"]} 4000 (largest empty sector '
               f'{v["gap"]} deg, seat {v["seat"]} deg)', s, count=1)
    s = s.replace('// WILD CHALICE TREE - the Chalice Tree\'s seat with the Wild Chaotic Tree\'s crown.',
                  f'// WILD CHALICE TREE, {name.replace("_", " ")} - the Wild Chalice Tree with another '
                  f'branch layout\n// (layout seed {v["seed"]}, wander seed {v["wander"]}).', 1)
    s = s.replace('echo(str("Wild Chalice Tree | ', f'echo(str("Wild Chalice Tree {name} | ', 1)
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f'Wild_Chalice_Tree_{name}.scad')
    open(out, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
    return out


if __name__ == '__main__':
    for name, v in VARIANTS.items():
        scad = write_scad(name, v)
        print('wrote', scad)
        if '--png' in sys.argv:
            png = scad[:-5] + '.png'
            subprocess.run([sys.executable, os.path.join(TOOLS, 'render_png.py'), scad, png,
                            '--view', 'iso', '--size', '1600', '-D', 'sketch=false'], check=True)
            print('rendered', png)
