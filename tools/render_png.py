#!/usr/bin/env python3
"""Render a .scad file to a trimmed PNG with OpenSCAD's preview renderer.

Views: iso (true isometric, orthographic), front, back, top, persp (3/4 perspective).
The flat background is trimmed to the model plus a margin.

usage:
  python render_png.py design.scad out.png [--view iso] [--size 2000] [-D show_glass=false ...]

OpenSCAD is taken from $OPENSCAD, else the newest install, else `openscad`; builds that have the
Manifold backend are asked for it, which is far faster than CGAL ($OPENSCAD_BACKEND overrides).
"""
import argparse, functools, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageChops

VIEWS = {   # rot x, rot y, rot z, projection
    'iso':   (54.7356, 0, 45, 'ortho'),
    'front': (90, 0, 0, 'ortho'),
    'back':  (90, 0, 180, 'ortho'),
    'top':   (0, 0, 0, 'ortho'),
    'persp': (70, 0, 30, 'perspective'),
}


def openscad_exe():
    """Newest install first: the nightly renders with Manifold, minutes faster per part."""
    for p in (os.environ.get('OPENSCAD'),
              r'C:\Program Files\OpenSCAD (Nightly)\openscad.com',
              r'C:\Program Files\OpenSCAD\openscad.com',
              shutil.which('openscad')):
        if p and os.path.exists(p):
            return p
    raise SystemExit('OpenSCAD not found: set $OPENSCAD')


@functools.lru_cache(maxsize=None)
def _backend(exe):
    """The backend flag this binary accepts, if any. 2021.01 errors out on an unknown option."""
    want = os.environ.get('OPENSCAD_BACKEND', 'Manifold')
    if want.lower() == 'none':
        return ()
    try:
        h = subprocess.run([exe, '--help'], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ()
    return ('--backend', want) if '--backend' in h.stdout + h.stderr else ()


def openscad_cmd():
    """The command to run OpenSCAD with: the binary, plus a backend flag where it is supported."""
    exe = openscad_exe()
    return [exe, *_backend(exe)]


def render(scad, out_png, view='iso', size=2000, defines=(), margin=60, scheme='Tomorrow'):
    rx, ry, rz, proj = VIEWS[view]
    raw = tempfile.mktemp(suffix='.png')
    cmd = [*openscad_cmd(), '-o', raw, f'--imgsize={size},{size}', f'--projection={proj}',
           f'--camera=0,0,0,{rx},{ry},{rz},500', '--viewall', '--autocenter', f'--colorscheme={scheme}']
    for d in defines:
        cmd += ['-D', d]
    r = subprocess.run(cmd + [scad], capture_output=True, text=True)
    log = r.stdout + r.stderr
    if r.returncode or 'ERROR' in log:
        raise SystemExit(f'OpenSCAD failed:\n{log}')
    im = Image.open(raw).convert('RGB')
    os.remove(raw)
    bg = Image.new('RGB', im.size, im.getpixel((0, 0)))
    b = ImageChops.difference(im, bg).getbbox()
    im = im.crop((max(0, b[0] - margin), max(0, b[1] - margin),
                  min(im.width, b[2] + margin), min(im.height, b[3] + margin)))
    im.save(out_png)
    return im.size, [l for l in log.splitlines() if l.startswith(('ECHO', 'WARNING'))]


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scad'); ap.add_argument('png')
    ap.add_argument('--view', default='iso', choices=VIEWS)
    ap.add_argument('--size', type=int, default=2000)
    ap.add_argument('-D', dest='defines', action='append', default=[], help='OpenSCAD variable override, e.g. show_glass=false')
    a = ap.parse_args()
    size, notes = render(a.scad, a.png, a.view, a.size, a.defines)
    print('\n'.join(notes))
    print(f'wrote {a.png} {size[0]}x{size[1]}')
