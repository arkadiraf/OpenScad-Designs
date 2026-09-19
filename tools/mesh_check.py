#!/usr/bin/env python3
"""Printability checks for an exported mesh (3MF or STL).

Implements the acceptance tests of POT_DESIGNER_AGENT.md / WOVEN_DESIGNER_AGENT.md
for meshes exported from OpenSCAD:

  * topology       boundary / non-manifold edges (must be 0 / 0), shell count
  * overhang       area share of printed surface past 60 deg and 45 deg from vertical,
                   split into height bands (bottom 1 cm, body, top 3 cm)
  * bed contact    area lying on z = 0
  * bore           (vase holders) smallest distance from the Z axis above the glass floor
  * volume / mass  PLA at 100 % solid (1.24 g/cm3)

A 3MF may hold several mesh objects (a multi-part file from merge_3mf.py, or a Bambu Studio
project from bambu_3mf.py): each part is checked on its own, then the overhang/volume totals are
reported for all parts. Regions that start in mid-air (Bambu Studio: "floating regions") are left to
the slicer itself: bambu_3mf.py --slice.
Topology uses the file's own vertex indices for 3MF (exact); STL is welded at 1e-6 mm.

usage:
  python mesh_check.py model.3mf [--bore-r 41 --floor-h 9] [--max-overhang 0.5] [--locate]

Exit code 0 when every hard check passes, 1 otherwise.
"""
import argparse, re, struct, sys, zipfile
import numpy as np

PLA = 1.24          # g / cm3
SIN60 = np.sin(np.radians(60))
SIN45 = np.sqrt(0.5)


# ------------------------------------------------------------------ loading
def load(path):
    """Return a list of (name, V[n,3], F[m,3]) meshes."""
    if path.lower().endswith('.3mf'):
        # Meshes sit in 3D/3dmodel.model (core spec, merge_3mf.py) or in 3D/Objects/*.model
        # (Bambu Studio project, bambu_3mf.py). Coordinates are read as stored, before any build
        # transform, so the bore stays on the Z axis.
        z = zipfile.ZipFile(path)
        out = []
        for entry in sorted(n for n in z.namelist() if n.startswith('3D/') and n.endswith('.model')):
            xml = z.read(entry).decode()
            for m in re.finditer(r'<object id="(\d+)"([^>]*)>\s*<mesh>(.*?)</mesh>', xml, re.S):
                name = re.search(r'name="([^"]*)"', m.group(2))
                body = m.group(3)
                V = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', body), dtype=float)
                F = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', body), dtype=np.int64)
                out.append((name.group(1) if name else 'object ' + m.group(1), V, F))
        return out
    data = open(path, 'rb').read()
    if data[:5] == b'solid' and b'facet' in data[:400]:
        T = np.array([l.split()[1:4] for l in data.decode().splitlines() if l.strip().startswith('vertex')],
                     dtype=float).reshape(-1, 3, 3)
    else:
        n = struct.unpack('<I', data[80:84])[0]
        rec = np.frombuffer(data[84:84 + n * 50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
        T = rec['v'].reshape(-1, 3, 3).astype(float)
    q = np.round(T.reshape(-1, 3) / 1e-6).astype(np.int64)
    uq, inv = np.unique(q, axis=0, return_inverse=True)
    return [('stl', uq * 1e-6, inv.reshape(-1, 3))]


# ------------------------------------------------------------------ checks
def topology(V, F):
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    e.sort(axis=1)
    ue, cnt = np.unique(e, axis=0, return_counts=True)
    # shells: union-find over vertices of each triangle
    parent = np.arange(len(V))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b, c in F:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = ra
    shells = len({find(i) for i in np.unique(F)})
    # near-duplicate vertices (distinct indices closer than 1e-4 mm): informational
    q = np.round(V / 1e-4).astype(np.int64)
    dup = len(V) - len(np.unique(q, axis=0))
    return ue, cnt, shells, dup


def surface(V, F):
    T = V[F]
    cr = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    a2 = np.linalg.norm(cr, axis=1)
    ok = a2 > 1e-12
    nz = np.zeros(len(F)); nz[ok] = cr[ok, 2] / a2[ok]
    area = a2 / 2
    vol = np.einsum('ij,ij->i', T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6 / 1000
    return T, area, nz, vol


def report(name, V, F, args, locate):
    print(f"--- {name}: {len(V)} vertices, {len(F)} triangles")
    ue, cnt, shells, dup = topology(V, F)
    nb, nn = int((cnt == 1).sum()), int((cnt > 2).sum())
    print(f"  edges        boundary {nb}   non-manifold {nn}   shells {shells}   near-duplicate vertices {dup}")
    if locate:
        for (a, b), c in zip(ue[cnt != 2], cnt[cnt != 2]):
            m = (V[a] + V[b]) / 2
            print(f"    edge x{c} at r {np.hypot(m[0], m[1]):.2f} phi {np.degrees(np.arctan2(m[1], m[0])) % 360:.1f}"
                  f" z {m[2]:.2f} len {np.linalg.norm(V[a] - V[b]):.4f}")
    T, area, nz, vol = surface(V, F)
    lo, hi = V[:, 2].min(), V[:, 2].max()
    print(f"  bbox         x {V[:,0].min():.1f}..{V[:,0].max():.1f}  y {V[:,1].min():.1f}..{V[:,1].max():.1f}"
          f"  z {lo:.2f}..{hi:.2f} mm")
    print(f"  volume       {vol:.1f} cm3 -> {vol * PLA:.0f} g PLA at 100 % solid")
    ok = nb == 0 and nn == 0 and vol > 0
    if vol <= 0:
        print("  FAIL: negative volume - faces are wound inside out")
    return ok, (T, area, nz, vol)


def overhang(T, area, nz, top_z, max_over):
    zmin = T[:, :, 2].min(axis=1)
    bed = T[:, :, 2].max(axis=1) < 0.01
    total = area[~bed].sum()
    print(f"  bed contact  {area[bed].sum() / 100:.1f} cm2")
    body_pct = 0.0
    for lim, lab in [(SIN60, '60'), (SIN45, '45')]:
        over = (~bed) & (nz < -lim)
        bands = []
        for z0, z1, bl in [(-1, 10, 'bottom 1 cm'), (10, top_z - 30, 'body'), (top_z - 30, top_z + 1, 'top 3 cm')]:
            p = 100 * area[over & (zmin >= z0) & (zmin < z1)].sum() / total
            bands.append(f"{bl} {p:.2f}%")
            if lab == '60' and bl != 'bottom 1 cm':
                body_pct += p
        print(f"  past {lab} deg  {100 * area[over].sum() / total:.2f}%   ({', '.join(bands)})"
              f"   above 1 mm {100 * area[over & (zmin > 1)].sum() / total:.2f}%")
    passed = body_pct < max_over
    print(f"  {'PASS' if passed else 'FAIL'}: past 60 deg above the bottom 1 cm = {body_pct:.2f}% (limit {max_over}%)")
    return passed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mesh')
    ap.add_argument('--bore-r', type=float, help='glass bore radius (mm): nothing may come closer to the Z axis')
    ap.add_argument('--floor-h', type=float, default=0.0, help='glass floor height (mm); bore check starts above it')
    ap.add_argument('--max-overhang', type=float, default=0.5, help='%% of surface past 60 deg allowed above 1 cm')
    ap.add_argument('--locate', action='store_true', help='print the position of every bad edge')
    args = ap.parse_args()

    meshes = load(args.mesh)
    all_ok = True
    parts = []
    for name, V, F in meshes:
        ok, s = report(name, V, F, args, args.locate)
        all_ok &= ok
        parts.append((V, s))

    Vall = np.concatenate([V for V, _ in parts])
    T = np.concatenate([s[0] for _, s in parts]); area = np.concatenate([s[1] for _, s in parts])
    nz = np.concatenate([s[2] for _, s in parts]); vol = sum(s[3] for _, s in parts)
    print(f"--- all parts ({len(meshes)})")
    print(f"  size         {Vall[:,0].max() - Vall[:,0].min():.1f} x {Vall[:,1].max() - Vall[:,1].min():.1f}"
          f" x {Vall[:,2].max():.1f} mm, bottom at z = {Vall[:,2].min():.3f}")
    print(f"  volume       {vol:.1f} cm3 -> {vol * PLA:.0f} g PLA at 100 % solid (~{vol * PLA * 0.3:.0f} g at typical infill)")
    if abs(Vall[:, 2].min()) > 0.01:
        print("  FAIL: model does not sit on z = 0"); all_ok = False
    all_ok &= overhang(T, area, nz, Vall[:, 2].max(), args.max_overhang)
    if args.bore_r is not None:
        sel = Vall[:, 2] > args.floor_h + 0.01
        rmin = np.hypot(Vall[sel, 0], Vall[sel, 1]).min()
        good = rmin >= args.bore_r - 0.01
        print(f"  {'PASS' if good else 'FAIL'}: closest material to the axis above the floor {rmin:.2f} mm"
              f" (bore {args.bore_r:.2f} mm)")
        all_ok &= good
    print("RESULT:", "PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
