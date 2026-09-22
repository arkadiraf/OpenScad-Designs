"""Layout search for Leaning_Chaotic_Tree.scad - WORK IN PROGRESS.

    python Leaning_Chaotic_Tree_layout.py <seed> <trees>

**No seed reproduces the tables in the .scad yet.** Those are a hand-made placeholder, put in to
look at the growth while the geometry was changing under it; see Leaning_Chaotic_Tree_notes.md.
When a searched layout is adopted, record its seed and count here as the other designs do
(guide 3.1).

A 3 -> 7 -> 13 hierarchy: 3 limbs out of the trunk (rows 0-2), 4 forks off the limbs (rows 3-6)
and 6 more off 6 of those 7 (rows 7-12). It draws random trees, scores each, and prints the best
as JSON for `limb_table` and `fork_table`. The search itself is the Grand tree's; what is this
tree's own:

  - The tube leans across the tree, and the cage is only a cage above cage_z0: meetings are
    scored from 60 mm up, and the no-contact rule only between 45 mm and there, because below
    that the limbs are leaving the trunk together and are meant to be close.
  - Branches are spread round the crown radius they have reached, not round a fixed bore.
  - There is no seat: the tube rests on the roots, not on the limbs.
  - Fork heights fit a 100 mm tree (a fork must start below where it ends - check it).
  - The turn rates are deliberately small (12-80 degrees over the tube's length), because the
    brief is for branches that grow up and bend only where the tube is in the way.

Last run (6 seeds x 4000): only 1-4 meetings. That is the open question - straightness costs
the merges that tie the cage together; the rates probably need to come part of the way back up.
"""
import numpy as np, sys, json, math

lift, glass_h, W, total_h, spare = 2.5, 100.0, 32.0, 100.0, 1.5
z_b0 = 1.5
glass_top = lift + glass_h * math.cos(math.radians(25))
bore_r, press, br = 8.25, 0.2, 3.0
crown_r, rho0 = 24.0, 6 * 16 / 96.0
scf = 16 / 96.0        # fixed lengths were set for a 96 mm glass
tip_share, tip_min, tip_taper, tip_curve = 0.55, 7.5, 240.0, 2.5
arch_zone = 60.0        # cage_z0: no arches below it
Z = np.arange(z_b0, total_h, 1.0)


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def R(z):
    return br * np.interp(z, [z_b0, lift, glass_top, total_h], [1.1, 1.0, 0.85, 0.65])


def ismooth(u):
    u = np.asarray(u, float)
    return np.where(u <= 0, 0, np.where(u < 1, u ** 3 - u ** 4 / 2, u - 0.5))


def turn(z, zref, r1, zc, r2):
    rev = (lambda x: 0 * x) if zc == 0 else (lambda x: (r2 - r1) * W * ismooth((x - (zc - W / 2)) / W))
    return (r1 * (z - zref) + rev(z) - rev(np.float64(zref))) / glass_h


def model(limbs, forks):
    """Angles and radii of every member at every height in Z (nan outside its range)."""
    rows = [dict(parent=-1, z0=z_b0, **dict(zip('a0 r1 zc r2 scale drop lean amp lam ph tw'.split(), l))) for l in limbs]
    rows += [dict(z0=lift + f[1], **dict(zip('parent fk r1 zc r2 share drop lean amp lam ph tw'.split(), f))) for f in forks]
    n = len(rows)
    P = np.full((n, len(Z)), np.nan)
    for i, m in enumerate(rows):
        zc = 0 if m['zc'] == 0 else lift + m['zc']
        if m['parent'] < 0:
            p = m['a0'] + turn(Z, lift, m['r1'], zc, m['r2']) + m['amp'] * np.sin(np.radians(360 * (Z - lift) / m['lam'] + m['ph']))
        else:
            base = np.interp(m['z0'], Z, P[m['parent']])
            p = base + turn(Z, m['z0'], m['r1'], zc, m['r2']) + m['amp'] * (np.sin(np.radians(360 * (Z - m['z0']) / m['lam'] + m['ph'])) - np.sin(np.radians(m['ph'])))
        m['end'] = total_h - spare - m['drop']
        P[i] = np.where((Z >= m['z0']) & (Z <= m['end']), p, np.nan)
    # effective scales, in member order (a parent is always earlier)
    S = np.zeros((n, len(Z)))
    for i, m in enumerate(rows):
        if m['parent'] < 0:
            s = np.full(len(Z), m['scale'], float)
        else:
            s = np.full(len(Z), m['share'] * np.interp(m['z0'], Z, S[m['parent']]))
        S[i] = s
        for k in range(i):    # nothing: children come later and thin their parent below
            pass
        # thinning by this member's own children
        for k, c in enumerate(rows):
            if c['parent'] == i:
                f = np.sqrt(1 - c['share'] ** 2)
                S[i] *= 1 + (f - 1) * sm(c['z0'] - 6, c['z0'] + 10, Z)
    Rad = S * R(Z)[None]
    for i, m in enumerate(rows):
        # blunt tip: a share of this member's own thickness at the rim, reached along a curve over
        # its last tip_taper mm, so it stays wide and only rounds off near the end
        tip = max(tip_min * scf, tip_share * np.interp(glass_top, Z, S[i]) * R(glass_top))
        t = np.clip((Z - (m['end'] - tip_taper * scf)) / (tip_taper * scf), 0, 1)
        Rad[i] = Rad[i] + (tip - Rad[i]) * t ** tip_curve
    return rows, P, Rad


def score(limbs, forks, verbose=False):
    rows, P, Rad = model(limbs, forks)
    n = len(rows)
    worst, prof = 0, []
    for z in range(int(arch_zone), int(total_h - 4), 3):
        k = int(z - z_b0)
        a = np.sort([P[i, k] % 360 for i in range(n) if not np.isnan(P[i, k]) and z >= rows[i]['z0'] + 8])
        g = np.max(np.diff(np.concatenate([a, [a[0] + 360]])))
        worst = max(worst, g); prof.append(round(g))
    pen = 0
    # a steady seat: the three limbs under the glass should stand like a tripod. A gap of 180 deg
    # would tip the glass off; press for an even spread instead of just staying legal
    k = int(lift - z_b0)
    a = np.sort(P[:3, k] % 360)
    seat = np.max(np.diff(np.concatenate([a, [a[0] + 360]])))
    seat = seat  # no seat: the tube rests on the roots, not on the limbs
    meets = []
    hug = np.stack([rho0 + (crown_r + r['lean'] - rho0) * sm(r['z0'], r['end'], Z)
                    for r in rows])
    for i in range(n):
        for j in range(i):
            d = np.abs((P[i] - P[j] + 180) % 360 - 180) * np.pi / 180 * np.maximum(hug[i], hug[j])
            reach = Rad[i] + Rad[j]
            valid = ~np.isnan(d)
            if rows[i]['parent'] == j:
                valid &= Z > rows[i]['z0'] + 22
            if (valid & (Z < arch_zone) & (Z > 45) & (d < reach)).any():
                pen += 200
            zone = valid & (Z >= arch_zone)
            dd = np.where(zone, d, np.inf)
            for q in range(1, len(Z) - 1):
                if zone[q] and dd[q] <= dd[q - 1] and dd[q] < dd[q + 1] and dd[q] < reach[q]:
                    meets.append((i, j, Z[q]))
    m = len(meets)
    if m < 8: pen += 15 * (8 - m)
    if m > 16: pen += 15 * (m - 16)
    for a_ in range(m):
        for b in range(a_):
            A, B = meets[a_], meets[b]
            if set(A[:2]) & set(B[:2]) and abs(A[2] - B[2]) < 25:
                pen += 25
    for i, r in enumerate(rows):    # a fork next to a meeting on its parent
        if r['parent'] >= 0 and any(r['parent'] in M_[:2] and abs(M_[2] - r['z0']) < 10 for M_ in meets):
            pen += 25
    if verbose:
        print('worst gap', round(worst), 'seat gap', round(seat), 'profile', prof)
        print('meetings', m, [(i, j, int(z)) for i, j, z in meets], 'penalty', pen)
        for i, r in enumerate(rows):
            print(i, 'parent', r['parent'], 'z0', r['z0'], 'r at lift/rim', np.round(np.interp([lift + 5, glass_top], Z, Rad[i]), 1))
    return worst + pen, worst, m


def cur_dir(limbs, forks, par, z):
    rows, P, _ = model(limbs, forks)
    q = int(z - z_b0)
    return np.sign(P[par, q + 1] - P[par, q - 1]) or 1


if __name__ == '__main__':
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
    best = None
    for it in range(int(sys.argv[2]) if len(sys.argv) > 2 else 2000):
        base = rng.uniform(0, 360)
        gaps = rng.uniform(95, 145, 3); gaps *= 360 / gaps.sum()
        a0 = (base + np.concatenate([[0], np.cumsum(gaps[:-1])])) % 360
        limbs = []
        rev = rng.integers(0, 3)
        for j in range(3):
            r1 = rng.choice([-1, 1]) * rng.uniform(12, 65)
            zc, r2 = (round(rng.uniform(30, 65)), round(-np.sign(r1) * rng.uniform(10, 55))) if j == rev else (0, 0)
            limbs.append([round(a0[j]), round(r1), zc, r2, [1.32, 1.26, 1.36][j], [0, 7, 4][j],
                          round(rng.uniform(-6, 8)), round(rng.uniform(1, 3)), round(rng.uniform(60, 110)),
                          round(rng.uniform(0, 360)), 2])
        forks, last = [], {}
        par2 = [0, 1, 2, int(rng.integers(0, 3))]           # level 2: 3 -> 7
        rng.shuffle(par2)
        for p in par2:
            for _ in range(20):
                fk = rng.uniform(14, 44)
                if all(abs(fk - z) >= 14 for z in last.get(p, [])):
                    break
            last.setdefault(p, []).append(fk)
            r1 = -cur_dir(limbs, forks, int(p), lift + fk) * rng.uniform(15, 80)
            if rng.uniform() < 0.25:
                r1 = -r1
            forks.append([int(p), round(fk), round(r1), 0, 0, round(rng.uniform(0.70, 0.80), 2), round(rng.uniform(1, 7)),
                          round(rng.uniform(-6, 8)), round(rng.uniform(1, 3)), round(rng.uniform(55, 105)),
                          round(rng.uniform(0, 360)), 1])
        par3 = list(rng.choice(7, 6, replace=False))         # level 3: 7 -> 13
        for p in par3:
            p = int(p)
            lo = max([40] + [z + 15 for z in last.get(p, [])] + ([forks[p - 3][1] + 15] if p >= 3 else []))
            fk = rng.uniform(lo, max(lo + 4, 74))
            last.setdefault(p, []).append(fk)
            r1 = -cur_dir(limbs, forks, p, lift + fk) * rng.uniform(12, 70)
            if rng.uniform() < 0.3:
                r1 = -r1
            revz = round(fk + rng.uniform(18, 32)) if rng.uniform() < 0.25 and fk < 55 else 0
            forks.append([p, round(fk), round(r1), revz, round(-np.sign(r1) * rng.uniform(10, 50)) if revz else 0,
                          round(rng.uniform(0.68, 0.78), 2), round(rng.uniform(1, 10)), round(rng.uniform(-6, 8)),
                          round(rng.uniform(1, 3)), round(rng.uniform(50, 95)), round(rng.uniform(0, 360)),
                          int(rng.integers(0, 2))])
        sc, worst, m = score(limbs, forks)
        if best is None or sc < best[0]:
            best = (sc, limbs, forks, worst, m)
    print('best score', round(best[0], 1), 'worst gap', round(best[3]), 'meetings', best[4])
    score(best[1], best[2], verbose=True)
    print(json.dumps(dict(limbs=best[1], forks=best[2])))
