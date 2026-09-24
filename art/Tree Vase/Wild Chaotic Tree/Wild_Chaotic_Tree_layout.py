"""Layout search that produced the branch tables in Wild_Chaotic_Tree.scad.

    python Wild_Chaotic_Tree_layout.py 71 2500

The tree is a 3 -> 7 -> 13 hierarchy: 3 limbs out of the trunk (rows 0-2), 4 forks off the limbs
(rows 3-6) and 6 more off 6 of those 7 (rows 7-12). This draws random trees, scores each one, and
prints the best as JSON to paste into `limb_table` and `fork_table`.

**Seed 71 over 2500 trees is the layout in the .scad**, the best of 8 seeds tried: largest empty
sector 97 deg, seat 126 deg, 10 meetings. Every other seed gives a different tree.

Sizes scale with the glass (SC = 80/96), and the fork heights with the glass height (130/170),
because a turn rate is degrees per glass height rather than per mm: the same number turns faster
per mm on a shorter glass (guide 17).

It mirrors the .scad's own geometry, so the two must be changed together:
  limbs  phi = a0 + turn(z, lift) + amp*sin(360(z-lift)/lam + ph)
  forks  phi = phi(parent, z0) + turn(z, z0) + amp*(sin(360(z-z0)/lam + ph) - sin(ph))
  radius = scale * R(z), a fork taking `share` of its parent while the parent thins by
           sqrt(1 - share^2) so the two cross-sections add up, tapering to tip_r at the end.

Where it has drifted from the design on purpose: this file still tapers to a fixed `tip_r` over
the last 35 mm, and `spare` is the 2.5 mm that was in the .scad when the search ran. The design has
since taken the blunt tips of guide 16.1 (tip_share / tip_taper / tip_curve) and `tip_spare` 3.5.
Both are left alone so this file still reproduces the tables above; the Grand tree's copy of this
search has the blunt-tip model, because its layout was searched with it.
"""
import numpy as np, sys, json

SC = 80 / 96                        # sizes scale with the glass diameter
HS = 130 / 170                      # fork heights scale with the glass height
lift, glass_h, W, total_h, spare = 83.0, 130.0, 42.0, 267.0, 2.5
z_b0 = 0.5 * lift
glass_top = lift + glass_h
bore_r, press, br, tip_r = 41.0, 0.2, 10.0, 2.2
arch_zone = lift + 20
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
        Rad[i] = Rad[i] + (tip_r - Rad[i]) * sm(m['end'] - 35, m['end'], Z)
    return rows, P, Rad


def score(limbs, forks, verbose=False):
    rows, P, Rad = model(limbs, forks)
    n = len(rows)
    worst, prof = 0, []
    for z in range(int(lift + 46), int(glass_top + 17), 5):
        k = int(z - z_b0)
        a = np.sort([P[i, k] % 360 for i in range(n) if not np.isnan(P[i, k]) and z >= rows[i]['z0'] + 8])
        g = np.max(np.diff(np.concatenate([a, [a[0] + 360]])))
        worst = max(worst, g); prof.append(round(g))
    pen = 0
    # a steady seat: the three limbs under the glass must not leave a gap wider than 150 deg
    k = int(lift - z_b0)
    a = np.sort(P[:3, k] % 360)
    seat = np.max(np.diff(np.concatenate([a, [a[0] + 360]])))
    if seat > 150: pen += 3 * (seat - 150)
    meets = []
    hug = bore_r + (1 - press) * Rad
    for i in range(n):
        for j in range(i):
            d = np.abs((P[i] - P[j] + 180) % 360 - 180) * np.pi / 180 * np.maximum(hug[i], hug[j])
            reach = Rad[i] + Rad[j]
            valid = ~np.isnan(d)
            if rows[i]['parent'] == j:
                valid &= Z > rows[i]['z0'] + 40
            if (valid & (Z < arch_zone) & (Z > lift - 25) & (d < reach)).any():
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
            if set(A[:2]) & set(B[:2]) and abs(A[2] - B[2]) < 20:
                pen += 25
    for i, r in enumerate(rows):    # a fork next to a meeting on its parent
        if r['parent'] >= 0 and any(r['parent'] in M_[:2] and abs(M_[2] - r['z0']) < 17 for M_ in meets):
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
            r1 = rng.choice([-1, 1]) * rng.uniform(45, 90)
            zc, r2 = (round(rng.uniform(69, 107)), round(-np.sign(r1) * rng.uniform(40, 80))) if j == rev else (0, 0)
            limbs.append([round(a0[j]), round(r1), zc, r2, [1.32, 1.26, 1.36][j], [0, 10, 5][j],
                          round(rng.uniform(20, 25)), round(rng.uniform(4, 8)), round(rng.uniform(100, 150)),
                          round(rng.uniform(0, 360)), 2])
        forks, last = [], {}
        par2 = [0, 1, 2, int(rng.integers(0, 3))]           # level 2: 3 -> 7
        rng.shuffle(par2)
        for p in par2:
            for _ in range(20):
                fk = rng.uniform(11, 47)
                if all(abs(fk - z) >= 20 for z in last.get(p, [])):
                    break
            last.setdefault(p, []).append(fk)
            r1 = -cur_dir(limbs, forks, int(p), lift + fk) * rng.uniform(55, 95)
            if rng.uniform() < 0.25:
                r1 = -r1
            forks.append([int(p), round(fk), round(r1), 0, 0, round(rng.uniform(0.64, 0.74), 2), round(rng.uniform(3, 15)),
                          round(rng.uniform(20, 25)), round(rng.uniform(4, 8)), round(rng.uniform(92, 142)),
                          round(rng.uniform(0, 360)), 1])
        par3 = list(rng.choice(7, 6, replace=False))         # level 3: 7 -> 13
        for p in par3:
            p = int(p)
            lo = max([47] + [z + 23 for z in last.get(p, [])] + ([forks[p - 3][1] + 23] if p >= 3 else []))
            fk = rng.uniform(lo, max(lo + 4, 111))
            last.setdefault(p, []).append(fk)
            r1 = -cur_dir(limbs, forks, p, lift + fk) * rng.uniform(45, 90)
            if rng.uniform() < 0.3:
                r1 = -r1
            revz = round(fk + rng.uniform(33, 58)) if rng.uniform() < 0.25 and fk < 84 else 0
            forks.append([p, round(fk), round(r1), revz, round(-np.sign(r1) * rng.uniform(40, 70)) if revz else 0,
                          round(rng.uniform(0.58, 0.70), 2), round(rng.uniform(3, 22)), round(rng.uniform(18, 25)),
                          round(rng.uniform(3, 7)), round(rng.uniform(75, 125)), round(rng.uniform(0, 360)),
                          int(rng.integers(0, 2))])
        sc, worst, m = score(limbs, forks)
        if best is None or sc < best[0]:
            best = (sc, limbs, forks, worst, m)
    print('best score', round(best[0], 1), 'worst gap', round(best[3]), 'meetings', best[4])
    score(best[1], best[2], verbose=True)
    print(json.dumps(dict(limbs=best[1], forks=best[2])))
