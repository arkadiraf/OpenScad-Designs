"""Glass fit and seat check for Chalice Tree, on the exported mesh (STL or 3MF).

    python Chalice_Tree_seat_check.py Chalice_Tree.stl [--lift 85 --glass-d 80 --foot-z 17.5 --foot-R 50 --foot 2]

mesh_check.py measures a glass that stands on the wood as a straight cylinder with a rounded foot.
This glass curves in over its bottom 17.5 mm, so the wood legitimately fills the space a straight
glass would take there. This script measures against the real profile instead:

  - closest material to the glass: signed distance from every vertex to the glass envelope
    (negative = inside the glass). With clearance 0 the fit is tight, so the pressed faces sit at
    0 and nothing may be deeper than the -0.01 mm tolerance.
  - the seat: faces within 0.25 mm (one layer) of the glass below the top of the curve, split into
    pads under the bottom and pads on the curved foot, their area, and the largest angular gap
    between them (< 180 deg, or the glass could tip off).
"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from mesh_check import load, surface   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('mesh')
ap.add_argument('--lift', type=float, default=85)
ap.add_argument('--glass-d', type=float, default=80)
ap.add_argument('--foot-z', type=float, default=17.5)
ap.add_argument('--foot-R', type=float, default=50)
ap.add_argument('--foot', type=float, default=2, help='rounding of the bottom edge')
ap.add_argument('--clearance', type=float, default=0)
a = ap.parse_args()
gr = a.glass_d / 2 + a.clearance
C = np.array([a.glass_d / 2 - a.foot_R, a.lift + a.foot_z])
Rf = a.foot_R + a.clearance
e = a.foot + a.clearance


def sdf(r, z):
    x = np.where(z >= C[1], r - (gr - e), np.hypot(r - C[0], z - C[1]) - (Rf - e))
    y = a.lift + e - z
    return np.where((x > 0) & (y > 0), np.hypot(x, y), np.maximum(x, y)) - e


ok = True
for name, V, F in load(a.mesh):
    r = np.hypot(V[:, 0], V[:, 1]); d = sdf(r, V[:, 2])
    k = np.argmin(d)
    print(f'{name}: closest material to the glass {d[k]:+.3f} mm at z {V[k, 2]:.1f}, r {r[k]:.1f}')
    if d[k] < -0.01:
        ok = False
    T, area, nz, vol = surface(V, F)
    c = T.mean(axis=1); rc = np.hypot(c[:, 0], c[:, 1]); dc = sdf(rc, c[:, 2])
    pad = (np.abs(dc) < 0.25) & (c[:, 2] < a.lift + a.foot_z)
    bottom = pad & (c[:, 2] < a.lift + 0.3)
    phi = np.degrees(np.arctan2(c[pad, 1], c[pad, 0])) % 360
    s = np.sort(np.unique(np.round(phi)))
    gap = np.max(np.diff(np.concatenate([s, [s[0] + 360]]))) if len(s) else 360
    print(f'  seat: {area[pad].sum() / 100:.1f} cm2 of pads on the glass below {a.foot_z} mm '
          f'({area[bottom].sum() / 100:.2f} cm2 of it under the bottom edge), '
          f'largest gap between pads {gap:.0f} deg')
    if gap >= 180:
        ok = False
print('RESULT:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
