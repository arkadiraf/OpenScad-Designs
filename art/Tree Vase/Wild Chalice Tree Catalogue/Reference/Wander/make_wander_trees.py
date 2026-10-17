"""Wild Chalice Wander Trees: the Wild Chalice Tree (same 80 x 130 mm glass with its base curving
in to a 50 mm bottom, cupped 85 mm up with zero clearance, same height) where the roots wander as
well as the branches, so every tree is unique from the ground up.

    python make_wander_trees.py            # write every tree's .scad from trees.json

Each tree is ../Wild_Chalice_Tree.scad with:
  - its own 3 -> 7 -> 13 branch layout (`limb_table`, `fork_table`) from
        python ../Wild_Chalice_Tree_layout.py SEED 4000
    and its own branch wander (`wander_seed`, picked by ../Various/wander_search.py's scoring,
    re-run here by wander_search.py)
  - a root system of its own: `root_seed` re-draws every root's angle, length, one-sided sweep,
    meander (phase, wavelength and now also amplitude, 0.7-1.3x root_meander), side roots and
    buttress reach, and the trunk knots; `root_count` varies between trees.
Everything else (glass, seat, trunk, bark, printing rules) is the original's.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'Wild_Chalice_Tree.scad')
TREES = json.load(open(os.path.join(HERE, 'trees.json')))


def fmt_rows(rows):
    return '[\n' + ',\n'.join('    [' + ', '.join(f'{v:>5}' if isinstance(v, float) else f'{v:>4}' for v in r) + ']'
                              for r in rows) + ']'


def sub1(pattern, repl, s, flags=0):
    s2, n = re.subn(pattern, repl, s, count=1, flags=flags)
    assert n == 1, f'pattern not found: {pattern}'
    return s2


def root_wander(s):
    """Seed the root system: every root rnd(i, k) becomes rr(i, k) = rnd(i + 19 root_seed, k)."""
    s = sub1(r'(side_roots = [^\n]*\n)',
             r'\1root_seed = 1;          // another number grows a different root system: angles, lengths,\n'
             r'                        // sweep, meander, side roots, buttresses and trunk knots\n', s)
    s = sub1(r'(function root_angle\(i\) = )360\*i/root_count\+20\*\(rnd\(i,1\)-0\.5\);',
             r'function rr(i,k) = rnd(i+19*root_seed,k);     // per-root random, drawn anew for every root_seed\n'
             r'\g<1>360*i/root_count+26*(rr(i,1)-0.5);', s)
    for fn in ('butt_reach', 'root_end', 'root_off', 'has_side', 'side_t', 'side_root_point'):
        m = re.search(rf'function {fn}\(.*?;\n(?=\S|\n)', s, flags=re.S)
        assert m, fn
        s = s[:m.start()] + m.group(0).replace('rnd(i,', 'rr(i,') + s[m.end():]
    s = sub1(r'\+ root_meander\*smooth', '+ root_meander*(0.7+0.6*rr(i,10))*smooth', s)
    s = sub1(r'trunk_knots = \[\[.*?\]\];',
             'trunk_knots = [for(k=[0:3]) [15+15*rr(k,11),90*k+60*rr(k,12),3.7+1.3*rr(k,13)]];', s)
    s = sub1(r'seed=3\.1\*i\+1,', 'seed=3.1*i+1+0.37*root_seed,', s)
    s = sub1(r'seed=4\.3\*i\+2\)', 'seed=4.3*i+2+0.37*root_seed)', s)
    return s


def write_scad(name, t):
    raw = open(SRC, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'      # keep the source's line endings
    s = root_wander(raw.replace('\r\n', '\n'))
    s = sub1(r'limb_table = \[.*?\]\];', 'limb_table = ' + fmt_rows(t['limbs']) + ';', s, flags=re.S)
    s = sub1(r'fork_table = \[.*?\]\];', 'fork_table = ' + fmt_rows(t['forks']) + ';', s, flags=re.S)
    s = sub1(r'wander_seed = \d+;', f'wander_seed = {t["wander"]};', s)
    s = sub1(r'root_seed = 1;', f'root_seed = {t["root_seed"]};', s)
    s = sub1(r'root_count = \d+;', f'root_count = {t["root_count"]};', s)
    s = sub1(r'// Layout: Wild_Chalice_Tree_layout\.py [^\n]*',
             f'// Layout: Wild_Chalice_Tree_layout.py {t["seed"]} 4000 (largest empty sector {t["gap"]} deg, '
             f'seat {t["seat"]} deg)', s)
    s = sub1(r"// WILD CHALICE TREE - the Chalice Tree's seat with the Wild Chaotic Tree's crown\.",
             f'// WILD CHALICE TREE, {name.replace("_", " ")} - the Wild Chalice Tree with branches AND roots\n'
             f'// that wander: layout seed {t["seed"]}, wander seed {t["wander"]}, root seed {t["root_seed"]}, '
             f'{t["root_count"]} roots.', s)
    s = sub1(r'echo\(str\("Wild Chalice Tree \| ', f'echo(str("Wild Chalice {name} | ', s)
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f'Wild_Chalice_{name}.scad')
    open(out, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
    return out


if __name__ == '__main__':
    for name, t in TREES.items():
        print('wrote', write_scad(name, t))
