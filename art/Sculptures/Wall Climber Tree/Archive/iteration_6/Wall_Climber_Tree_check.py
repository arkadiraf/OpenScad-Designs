"""Checks for Wall_Climber_Tree.scad that the packaging (tools/build_design.py) does not make:
how the two parts fit and slide, and where a part would start in mid-air.

    python Wall_Climber_Tree_check.py [--draft] [--sketch] [--slide 0,10,20,35]

1. Fit: intersects the tree (in its assembled position, raised by each slide offset) with the
   roots. 0 mm3 everywhere means the parts only touch where they meet and the tree slides in from
   above without hitting anything.
2. Exports both parts as they print (part="tree" / "roots") and runs tools/floating_check.py on
   each. Bambu Studio's slice (in build_design.py) is the authority; this says where.
Exit code 1 if any check fails.
"""
import argparse, os, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE                                  # the repository: the first folder up with tools/
while not os.path.isdir(os.path.join(ROOT, 'tools')):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from render_png import openscad_cmd          # noqa: E402  (finds the nightly + Manifold)
from mesh_check import load                  # noqa: E402

SCAD = os.path.join(HERE, 'Wall_Climber_Tree.scad')


def run(args):
    r = subprocess.run([*openscad_cmd(), *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def volume(path):
    tot = 0.0
    for _, V, F in load(path):
        T = V[F]
        tot += np.einsum('ij,ij->i', T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6
    return tot


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--draft', action='store_true', help='quality=0 (faster, coarser)')
    ap.add_argument('--sketch', action='store_true', help='no bark (fastest; the shape only)')
    ap.add_argument('--slide', default='0,10,20,35', help='slide offsets to test (mm up)')
    a = ap.parse_args()
    q = (['-D', 'quality=0'] if a.draft else []) + (['-D', 'sketch=true'] if a.sketch else [])
    tmp = tempfile.mkdtemp(prefix='wct_')
    ok = True

    print('fit and slide:')
    procs = []
    for dz in [float(x) for x in a.slide.split(',')]:
        src = os.path.join(tmp, f'fit_{dz:g}.scad')
        open(src, 'w').write(f'include <{SCAD.replace(os.sep, "/")}>\npart = "none";\n'
                             f'intersection() {{ translate([0,0,{dz}]) tree_part(); roots_part(); }}\n')
        out = os.path.join(tmp, f'fit_{dz:g}.stl')
        procs.append((dz, out, subprocess.Popen([*openscad_cmd(), '-o', out, *q, src],
                                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
    for dz, out, p in procs:
        log = p.communicate()[0]
        if 'empty' in log.lower() or not os.path.exists(out) or os.path.getsize(out) == 0:
            print(f'  raised {dz:5.1f} mm: no contact')
            continue
        v = volume(out)
        bad = abs(v) > 0.5
        ok &= not bad
        print(f'  raised {dz:5.1f} mm: overlap {v:8.3f} mm3' + ('   FAIL' if bad else '   (touching faces only)'))

    print('floating regions (as printed):')
    for part in ('tree', 'roots'):
        out = os.path.join(tmp, part + '.3mf')
        code, log = run(['-o', out, *q, '-D', f'part="{part}"', SCAD])
        if code or 'ERROR' in log:
            print(f'  {part}: export failed'); ok = False; continue
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'floating_check.py'), out],
                           capture_output=True, text=True)
        last = [l for l in r.stdout.splitlines() if l.strip()]
        print(f'  {part}: ' + (last[-1].strip() if last else 'no output'))
        for l in last[1:-1]:
            print('     ' + l.strip())
        ok &= r.returncode == 0
    print('RESULT:', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
