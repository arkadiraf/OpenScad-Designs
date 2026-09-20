#!/usr/bin/env python3
"""Package an OpenSCAD design: folder + .scad + multi-part 3MF + isometric PNG,
then run the printability checks on the 3MF that was written.

The .scad must have a `part` variable that selects what to render, e.g.
    part = "assembly";   // [assembly, holder, bark, leaves]
Every --part given here is exported by OpenSCAD with -D part="<name>" (all parts
in parallel: CGAL is single-threaded), and the exports are merged into one 3MF
object with one named part per colour. That 3MF is then written as a Bambu Studio project
(bambu_3mf.py): printer, plate 1, one Bambu PLA Basic filament per part, purge volumes and sparse
infill, ready to slice. --printer none keeps the plain core-spec 3MF instead. The PNG is rendered
from part="assembly". The checks are mesh_check.py, then (for a Bambu project, when Bambu Studio is
installed) a slice with Bambu Studio itself, which fails the build on any slicing warning such as
"floating regions".

usage:
  python build_design.py design.scad --name "Braided Tree Vase Holder" \
      --part bark=#6F5034 --part leaves=#3F8E43 \
      [--out DIR] [--check-args "--bore-r 41 --floor-h 9"] [--keep-exports] \
      [--printer H2C|H2D|X1C|...|none] [--infill 35]

Output (default DIR = <scad folder>/<name>):
  DIR/<Name_With_Underscores>.scad   copy of the source (the exports are made from this copy)
  DIR/<Name_With_Underscores>.3mf    one object, one part per --part (a Bambu Studio project)
  DIR/<Name_With_Underscores>.png    isometric render of the assembly
"""
import argparse, os, shlex, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from merge_3mf import merge                     # noqa: E402
from bambu_3mf import convert, slice_check, DEFAULT_PRINTER, DEFAULT_INFILL   # noqa: E402
from render_png import render, openscad_cmd     # noqa: E402


def export_part(scad, part, out_3mf):
    t = time.time()
    r = subprocess.run([*openscad_cmd(), '-o', out_3mf, '-D', f'part="{part}"', scad],
                       capture_output=True, text=True)
    log = r.stdout + r.stderr
    notes = [l.strip() for l in log.splitlines()
             if any(k in l for k in ('ERROR', 'WARNING', 'Volumes', 'rendering time'))]
    failed = r.returncode != 0 or 'ERROR' in log or not os.path.exists(out_3mf)
    return part, time.time() - t, notes, failed


def main():
    sys.stdout.reconfigure(line_buffering=True)   # keep our lines in order with mesh_check's output
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scad')
    ap.add_argument('--name', required=True, help='design name with spaces, e.g. "Braided Tree Vase Holder"')
    ap.add_argument('--part', action='append', required=True, help='part=#RRGGBB (value of the scad `part` variable)')
    ap.add_argument('--out', help='output folder (default: next to the scad, named after --name)')
    ap.add_argument('--check-args', default='', help='extra arguments for mesh_check.py')
    ap.add_argument('--keep-exports', action='store_true', help='keep the per-part 3MF files in the output folder')
    ap.add_argument('--printer', default=DEFAULT_PRINTER,
                    help=f'Bambu printer for the project (default {DEFAULT_PRINTER}); "none" keeps a plain 3MF')
    ap.add_argument('--infill', type=float, default=DEFAULT_INFILL, help=f'sparse infill %% (default {DEFAULT_INFILL})')
    a = ap.parse_args()

    stem = a.name.replace(' ', '_')
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.scad)), a.name)
    os.makedirs(out, exist_ok=True)
    scad = os.path.join(out, stem + '.scad')
    if os.path.abspath(a.scad) != os.path.abspath(scad):
        shutil.copyfile(a.scad, scad)
    print(f'[1/4] source      {scad}')

    parts = [p.split('=', 1) for p in a.part]
    tmp = tempfile.mkdtemp(prefix='scad_parts_')
    kernel = 'Manifold' if '--backend' in openscad_cmd() else 'CGAL; minutes each'
    print(f'[2/4] exporting   {", ".join(p for p, _ in parts)} in parallel ({kernel})...')
    with ThreadPoolExecutor(len(parts)) as ex:
        jobs = [ex.submit(export_part, scad, p, os.path.join(tmp, p + '.3mf')) for p, _ in parts]
        results = [j.result() for j in jobs]
    bad = False
    for part, secs, notes, failed in results:
        print(f'      {part:<10} {secs:6.0f} s  {"FAILED" if failed else "ok"}  ' + ' | '.join(notes))
        bad |= failed
    if bad:
        raise SystemExit('export failed - fix the errors above (see the agent guide, "CGAL errors")')

    out_3mf = os.path.join(out, stem + '.3mf')
    merge(out_3mf, a.name, [(p.capitalize(), os.path.join(tmp, p + '.3mf'), c) for p, c in parts])
    if a.keep_exports:
        for p, _ in parts:
            shutil.copyfile(os.path.join(tmp, p + '.3mf'), os.path.join(out, f'{stem}_{p}.3mf'))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f'[3/4] merged      {out_3mf}')
    if a.printer.lower() != 'none':
        for line in convert(out_3mf, printer_id=a.printer, infill=a.infill):
            print('      ' + line)

    png = os.path.join(out, stem + '.png')
    size, notes = render(scad, png, 'iso')
    print(f'      rendered    {png} ({size[0]}x{size[1]})  ' + ' | '.join(notes))

    print('[4/4] checks')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'mesh_check.py'), out_3mf] + shlex.split(a.check_args))
    failed = r.returncode != 0
    if a.printer.lower() != 'none':
        # The slicer's own verdict: catches regions that start in mid-air ("floating regions"),
        # which the mesh checks cannot judge reliably.
        ok, lines = slice_check(out_3mf)
        print('\n'.join(lines))
        failed |= ok is False
    print('BUILD:', 'FAIL' if failed else 'PASS')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
