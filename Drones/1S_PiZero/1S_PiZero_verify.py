"""Check the 1S Pi Zero frame against the part drawings.

Exports the PCB outline and the printed harness from 1S_PiZero.scad and measures what was
actually drawn (hole centres and diameters, post positions), then compares it with the
datasheet figures:

    Crazyflie Bolt 1.1   36 x 35.4 mm, holes 3.1 mm on 30.5 x 30.5, deck rows 17 mm apart
    GTS V3 1203 motor    4 x M2 base holes, 9 mm apart across (a cross), bell 15.76
    DYS XSD 7A ESC       16.2 x 11 x 4 mm, 4 + 3 pins at 2.54 mm pitch
    Pi Zero 2 W          65 x 30 mm, M2.5 holes 3.5 mm in from each edge (58 x 23)
    Molicel P30B 18650   18.4 x 65.2 mm

    python Drones/1S_PiZero/1S_PiZero_verify.py
"""
import math
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from render_png import openscad_exe  # noqa: E402

SCAD = os.path.join(HERE, '1S_PiZero.scad')
TOL = 0.05
fails = []


def check(label, got, want, tol=TOL):
    ok = abs(got - want) <= tol
    print(f"  {'ok  ' if ok else 'FAIL'} {label:48s} {got:8.3f}  (drawing {want})")
    if not ok:
        fails.append(label)


def export(part, suffix):
    out = os.path.join(tempfile.gettempdir(), f'1s_pizero_verify_{part}.{suffix}')
    r = subprocess.run([openscad_exe(), '-o', out, '-D', f'part="{part}"', SCAD],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr)
    return out, r.stderr


def loops_from_svg(path):
    """Every closed subpath of the SVG as a list of (x, y); OpenSCAD writes y flipped."""
    d = ' '.join(re.findall(r'd="([^"]+)"', open(path).read()))
    loops = []
    for sub in re.split(r'[Mm]', d)[1:]:
        nums = [float(v) for v in re.findall(r'-?\d+\.?\d*(?:e-?\d+)?', sub)]
        loops.append([(nums[i], -nums[i + 1]) for i in range(0, len(nums) - 1, 2)])
    return loops


def circle(loop):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(loop, loop[1:] + loop[:1]):
        c = x0 * y1 - x1 * y0
        a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
    a /= 2
    return cx / (6 * a), cy / (6 * a), 2 * math.sqrt(abs(a) / math.pi)


def echo_values(stderr, *names):
    return {n: float(m.group(1)) for n in names
            for m in [re.search(rf'{n} = ([-\d.e]+)', stderr)] if m}


# ---- PCB: measure the holes that were drawn --------------------------------------------------
svg, _ = export('pcb_outline', 'svg')
holes = [circle(l) for l in loops_from_svg(svg) if len(l) >= 8]
holes = [h for h in holes if h[2] < 6]                      # drop the board outline

def near(x, y, r=0.6):
    hs = [h for h in holes if math.hypot(h[0] - x, h[1] - y) < r]
    return hs[0] if hs else None

print('Crazyflie Bolt 1.1 (frame holes for its M2.5 screws)')
bolt = [h for h in holes if abs(abs(h[0]) - 15.25) < 0.5 and abs(abs(h[1]) - 15.25) < 0.5]
check('number of Bolt holes', len(bolt), 4, 0)
if bolt:
    xs = sorted({round(h[0], 2) for h in bolt}); ys = sorted({round(h[1], 2) for h in bolt})
    check('hole spacing x', xs[-1] - xs[0], 30.5)
    check('hole spacing y', ys[-1] - ys[0], 30.5)
    check('frame hole dia (M2.5 clearance)', max(h[2] for h in bolt), 2.7, 0.1)

print('GTS V3 1203 motors (4 x M2, 9 mm apart across)')
L = 140 / (2 * math.sqrt(2))
for mx, my in [(L, L), (L, -L), (-L, -L), (-L, L)]:
    mh = [h for h in holes if 3.5 < math.hypot(h[0] - mx, h[1] - my) < 5.5]
    check(f'motor ({mx:+.1f},{my:+.1f}) hole count', len(mh), 4, 0)
    if len(mh) == 4:
        d = sorted(math.hypot(a[0] - b[0], a[1] - b[1]) for i, a in enumerate(mh) for b in mh[i + 1:])
        check('  opposite holes apart', d[-1], 9.0)
        check('  M2 hole dia', mh[0][2], 2.2, 0.1)

print('JST PH power connectors (2 pins, 2.0 mm pitch)')
ph = sorted((h for h in holes if 0.7 < h[2] < 0.9), key=lambda h: (h[1], h[0]))
check('PH pin holes (2 connectors x 2)', len(ph), 4, 0)
for k in range(0, len(ph) - 1, 2):
    check(f'  pitch at ({ph[k][0]:.1f}, {ph[k][1]:.1f})', math.hypot(ph[k + 1][0] - ph[k][0], ph[k + 1][1] - ph[k][1]), 2.0)

print('DYS XSD 7A headers (2.54 pitch, 4 inner + 3 motor side, 1.0 mm holes)')
pins = [h for h in holes if 0.9 < h[2] < 1.2]                        # ESC header holes (JST PH are 0.8)
arm = [(p, (p[0] + p[1]) / math.sqrt(2))                                  # distance along the arm
       for p in pins if p[0] > 0 and p[1] > 0 and abs(p[0] - p[1]) < 6]
rows = {}
for p, r in arm:
    rows.setdefault(round(r, 0), []).append(p)
rs = sorted(rows)
check('pin rows on one arm', len(rs), 2, 0)
if len(rs) == 2:
    check('pins at the inner end', len(rows[rs[0]]), 4, 0)
    check('pins at the motor end', len(rows[rs[1]]), 3, 0)
    inner = sorted(rows[rs[0]], key=lambda p: p[0] - p[1])
    check('pitch', math.hypot(inner[1][0] - inner[0][0], inner[1][1] - inner[0][1]), 2.54)
    ri = sum(p[0] + p[1] for p in rows[rs[0]]) / 4 / math.sqrt(2)
    ro = sum(p[0] + p[1] for p in rows[rs[1]]) / 3 / math.sqrt(2)
    # the ESC (16.2 long) must fit between the rows with the pins beside its edges
    check('row spacing - pin (0.64) - ESC length (16.2) = 2 x pin_gap', ro - ri - 0.64 - 16.2, 0.6)

# ---- harness and parts, from the design's own values -----------------------------------------
print('Part sizes (design values)')
subprocess.run([openscad_exe(), '-o', os.path.join(tempfile.gettempdir(), 'v.echo'), '-D', 'part="none"',
                    '-D', 'echo_dims=true', SCAD], capture_output=True, text=True)
vals = {}
for line in open(os.path.join(tempfile.gettempdir(), 'v.echo')).read().splitlines():
    m = re.match(r'ECHO: "DIM (\w+) ([-\d.e]+)"', line)
    if m:
        vals[m.group(1)] = float(m.group(2))
for key, want in [('pi_l', 65), ('pi_w', 30), ('pi_hole_x', 58), ('pi_hole_y', 23),
                  ('fc_l', 36), ('fc_w', 35.4), ('fc_deck_rows', 17),
                  ('motor_bell_d', 15.76), ('motor_h', 9.9), ('motor_base_t', 1.4), ('motor_shaft', 4.8),
                  ('esc_l', 16.2), ('esc_w', 11), ('esc_t', 4), ('bat_d', 18.4), ('bat_len', 65.2),
                  ('cam_w', 9)]:
    if key in vals:
        check(key, vals[key], want)
    else:
        print(f'  FAIL {key}: not echoed'); fails.append(key)

# Pi posts in the printed harness: measure them from the exported mesh top view
svg, _ = export('cradle_top', 'svg')
posts = [circle(l) for l in loops_from_svg(svg) if len(l) >= 8]
posts = [p for p in posts if 3.3 < p[2] < 3.9]              # the M2.5 insert holes at the post tops
check('Pi post insert holes found', len(posts), 4, 0)
if len(posts) == 4:
    xs = sorted(p[0] for p in posts); ys = sorted(p[1] for p in posts)
    check('Pi post spacing x', xs[-1] - xs[0], 58)
    check('Pi post spacing y', ys[-1] - ys[0], 23)

# The cover must lift straight off the soldered cell: below the cell's equator nothing may reach
# inside the cell's width (18.4 mm, plus the 0.25 mm fit).
print('Battery cover lifts off (slices between the PCB and the cell axis)')
fit_r = 18.4 / 2 + 0.25
z_axis = 1.6 + 18.4 / 2
for z in [1.8, 4, 7, 10, z_axis - 0.05]:
    out = os.path.join(tempfile.gettempdir(), '1s_pizero_slice.svg')
    subprocess.run([openscad_exe(), '-o', out, '-D', 'part="cradle_slice"', '-D', f'slice_z={z}', SCAD],
                   capture_output=True, text=True)
    # only along the cell (65.2 mm): past its ends the cover may close in over the tabs
    segs = [(a, b) for l in loops_from_svg(out) for a, b in zip(l, l[1:] + l[:1])]
    # sample each edge so a long edge crossing the cell zone is not missed between its end points
    closest = min(abs(a[1] + (b[1] - a[1]) * t / 20) for a, b in segs for t in range(21)
                  if abs(a[0] + (b[0] - a[0]) * t / 20) <= 65.2 / 2 + 0.25)
    ok = closest >= fit_r - 0.01
    print(f"  {'ok  ' if ok else 'FAIL'} z {z:5.2f}: closest material to the cell centreline {closest:.2f}"
          f" (must be >= {fit_r:.2f})")
    if not ok:
        fails.append(f'lift-off at z {z}')

# The optional prop guard must not touch anything: its intersection with each body is empty.
print('Prop guard clears every other part and the prop sweep')
for body in ['props', 'motors', 'pcb', 'escs', 'cradle', 'gear', 'cam_mount', 'bolt', 'pi', 'cam_view']:
    out = os.path.join(tempfile.gettempdir(), '1s_pizero_clash.stl')
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([openscad_exe(), '-o', out, '-D', 'part="guard_clash"', '-D', f'clash="{body}"',
                        '-D', 'prop_guard=true', SCAD], capture_output=True, text=True)
    empty = 'top level object is empty' in r.stderr.lower() or not os.path.exists(out)
    vol = 0.0
    if not empty:                                    # something was written: how much overlaps?
        import struct
        data = open(out, 'rb').read()
        if data[:5] == b'solid':
            tris = re.findall(r'vertex\s+(\S+)\s+(\S+)\s+(\S+)', data.decode(errors='replace'))
            v = [tuple(map(float, t)) for t in tris]
            for a, b, c in zip(v[0::3], v[1::3], v[2::3]):
                vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                        + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
        empty = abs(vol) < 0.01
    print(f"  {'ok  ' if empty else 'FAIL'} guard vs {body:10s} {'no overlap' if empty else f'overlap {abs(vol):.2f} mm3'}")
    if not empty:
        fails.append(f'guard vs {body}')

print(f"\n{'ALL MATCH' if not fails else 'MISMATCH: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
