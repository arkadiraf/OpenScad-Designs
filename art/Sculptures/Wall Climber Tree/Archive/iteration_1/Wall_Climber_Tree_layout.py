"""Crown layout for Wall_Climber_Tree.scad: searches the branch paths and writes them to
Wall_Climber_Tree_layout.scad, which the design includes.

    python Wall_Climber_Tree_layout.py [seed] [tries]
    python Wall_Climber_Tree_layout.py 11 3000     <- the layout in the .scad (best of seeds 3, 7, 11, 19)

The tree is 3 -> 7: the trunk leaves the wall (straight through the burl, along A0) and carries on
as the leader; two limbs part from it just above the burl, at different heights. The leader forks
twice more and each limb once, so 7 tips (2 + 3 + 2). Every tip ends within `crown_h` (150 mm) above
the first parting, and the crown sprawls over the wall and out from it.

Each member is a cubic Bezier from a point a few mm back inside its parent (along the parent's
tangent) to its tip, leaving between the parent's direction and the line to the tip and arriving
steeper than that line. On top of it, two waves of unrelated length wander it sideways and towards /
away from the wall (faded in over its first 30 %, so it leaves its parent cleanly). Radii: a member
takes `share` of its parent's radius there, and the parent thins so the two cross-sections add up
(sqrt(1 - share^2), over -5..+25 mm of the fork); a child swells from 60 % over its first 6 mm,
inside its parent; every member tapers to a blunt tip of `tip_share` of its start radius.

Hard checks (a draw is rejected otherwise):
  climb >= 45 deg along every member (the tree prints standing; the bark needs the margin),
  surfaces of unrelated members >= `gap` apart (a child is not checked against its parent over its
  first 35 mm), nothing nearer the wall than `min_y`, no tip cap above total_h.
Score: the smallest distance between two tips, seen from the front (x, z), plus their spread.

The trunk numbers (E0, climb, burl_h, r_t) mirror the .scad; it asserts that they match.
"""
import json, math, os, sys
import numpy as np

# ---- mirrored from Wall_Climber_Tree.scad
E0 = np.array([0.0, 0.0, 37.0])     # where the trunk axis meets the wall
CLIMB = 50.0                        # trunk_climb
BURL_H = 34.0                       # burl_h
R_T = 11.0                          # trunk_r
A0 = np.array([0.0, math.cos(math.radians(CLIMB)), math.sin(math.radians(CLIMB))])

# ---- crown
CROWN_H = 150.0                     # tips end within this height above the first parting
STEP = 1.0                          # sample spacing along members (mm)
GAP = 2.5                           # clearance between unrelated members (mm)
MIN_Y = 13.0                        # no crown surface nearer the wall (the split is at 12), past
                                    # a member's first 15 mm (its start is inside its parent)
MIN_CLIMB = 45.0
TIP_MIN, TIP_SHARE = 2.8, 0.42
S_STRAIGHT = BURL_H / math.cos(math.radians(CLIMB)) + 6    # the trunk is straight through the burl


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def unit(v):
    return v / np.linalg.norm(v)


def arclen(P):
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])


def bez(A, B, C, D, t):
    t = t[:, None]
    return (1 - t) ** 3 * A + 3 * t * (1 - t) ** 2 * B + 3 * t * t * (1 - t) * C + t ** 3 * D


def at(P, L, s):
    """Point and unit tangent at arc length s along polyline P."""
    i = int(np.clip(np.searchsorted(L, s), 1, len(P) - 1))
    f = (s - L[i - 1]) / max(L[i] - L[i - 1], 1e-9)
    return P[i - 1] + f * (P[i] - P[i - 1]), unit(P[i] - P[i - 1])


def member_path(A, d_par, E, wav, rng_len=None):
    """Bezier from A (leaving between d_par and the chord) to E, plus wander."""
    ch = E - A
    L = np.linalg.norm(ch)
    cu = ch / L
    d0 = unit(d_par + 1.5 * cu)
    d1 = unit(cu + np.array([0, 0, 0.6]))
    n = max(12, int(math.ceil(L * 1.15 / STEP)))
    t = np.linspace(0, 1, n + 1)
    P = bez(A, A + 0.32 * L * d0, E - 0.30 * L * d1, E, t)
    e1 = unit(np.cross([0.0, 1.0, 0.0], cu))          # sideways along the wall
    e2 = unit(np.cross(cu, e1))                         # towards / away from the wall
    s = t * L
    # wander only as much as the member's climb can spare: a wave of amplitude a and length l
    # turns the direction by up to atan(2 pi a / l)
    chord_climb = math.degrees(math.atan2(ch[2], math.hypot(ch[0], ch[1])))
    k = float(np.clip((chord_climb - 52) / 22, 0.15, 1.0))
    f = k * sm(0.0, 0.3, t)[:, None]
    a1, l1, p1, a2, l2, p2, b1, m1, q1 = wav
    w1 = a1 * np.sin(2 * np.pi * s / l1 + p1) + a2 * np.sin(2 * np.pi * s / l2 + p2) \
        - (a1 * np.sin(p1) + a2 * np.sin(p2))           # 0 at the start
    w2 = b1 * (np.sin(2 * np.pi * s / m1 + q1) - np.sin(q1))
    return P + f * (w1[:, None] * e1 + w2[:, None] * e2)


def climb_min(P, z_from=-1e9):
    d = np.diff(P, axis=0)
    c = np.degrees(np.arctan2(d[:, 2], np.hypot(d[:, 0], d[:, 1])))
    keep = P[1:, 2] > z_from
    return c[keep].min() if keep.any() else 90.0


# Members: 0 leader (the trunk going on), 1 limb L, 2 limb R, 3-4 leader forks, 5 L fork, 6 R fork.
PARENT = [-1, 0, 0, 0, 0, 1, 2]


def draw(rng):
    """One random crown; returns its members or None."""
    # first parting just above the burl (s along the trunk), the second a little higher
    s1 = rng.uniform(36, 42)
    s2 = s1 + rng.uniform(9, 15)
    z_part = E0[2] + s1 * A0[2]
    top = z_part + CROWN_H
    # tips spread along the wall from left to right, at assorted heights and depths
    xs = np.linspace(-1, 1, 7) * rng.uniform(80, 105) + rng.uniform(-8, 8, 7)
    order = {1: 0, 5: 1, 3: 2, 0: 3, 4: 4, 6: 5, 2: 6}  # which slot each member's tip takes
    if rng.uniform() < 0.5:
        order = {1: 0, 5: 1, 4: 2, 0: 3, 3: 4, 6: 5, 2: 6}
    tips = {}
    for m, k in order.items():
        edge = abs(k - 3) / 3                           # outer tips end higher (their climb)
        z = top - 4 - rng.uniform(0, 1) * lerp(34, 6, edge)
        y = rng.uniform(30, 95)
        tips[m] = np.array([xs[k], y, z])
    # the leader: straight through the burl, then to its tip
    S1 = E0 + S_STRAIGHT * A0
    n0 = int(S_STRAIGHT + 4)
    straight = E0[None] + np.linspace(-4, S_STRAIGHT, n0 + 1)[:, None] * A0[None]
    wav = lambda: (rng.uniform(3, 7), rng.uniform(90, 140), rng.uniform(0, 6.3),
                   rng.uniform(0.4, 1.0), rng.uniform(40, 60), rng.uniform(0, 6.3),
                   rng.uniform(2, 6), rng.uniform(80, 130), rng.uniform(0, 6.3))
    lead = member_path(S1, A0, tips[0], wav())
    P0 = np.vstack([straight, lead[1:]])
    paths = {0: P0}
    starts = {0: (-1, 0.0)}
    fork_s = {1: s1, 2: s2}
    L0 = arclen(P0)
    fork_s[3] = rng.uniform(0.40, 0.55) * L0[-1]
    fork_s[4] = fork_s[3] + rng.uniform(0.12, 0.2) * L0[-1]
    for m in (1, 2, 3, 4, 5, 6):
        p = PARENT[m]
        Pp = paths[p]
        Lp = arclen(Pp)
        if m in (5, 6):
            fork_s[m] = rng.uniform(0.38, 0.55) * Lp[-1]
        back = 5 + 1.5 * rng.uniform()
        A, d = at(Pp, Lp, fork_s[m] - back)
        paths[m] = member_path(A, d, tips[m], wav())
        starts[m] = (p, fork_s[m])
    return dict(paths=paths, fork_s=fork_s, tips=tips, z_part=z_part, top=top)


def lerp(a, b, t):
    return a + (b - a) * t


SHARE = {1: 0.80, 2: 0.78, 3: 0.72, 4: 0.68, 5: 0.74, 6: 0.74}


def radii(c):
    """Radius along every member, with forks thinning their parents (cross-sections add up)."""
    paths, fork_s = c['paths'], c['fork_s']
    R = {}
    for m in range(7):
        P = paths[m]
        L = arclen(P)
        if m == 0:
            r0 = R_T
            u = np.clip((L - S_STRAIGHT) / (L[-1] - S_STRAIGHT), 0, 1)
            base = np.where(L <= S_STRAIGHT, r0, 0)
        else:
            p = PARENT[m]
            Lp = arclen(paths[p])
            i = min(np.searchsorted(Lp, fork_s[m]), len(Lp) - 1)
            r0 = SHARE[m] * R[p][i]
            u = L / L[-1]
        r1 = max(TIP_MIN, TIP_SHARE * r0)
        r = r1 + (r0 - r1) * (1 - u ** 1.6)
        if m == 0:
            r = np.where(L <= S_STRAIGHT, R_T, r)
        else:
            r = r * lerp(0.6, 1.0, sm(0, 6, L))          # swell inside the parent
        # this member thins after each of its own forks
        for k in range(7):
            if PARENT[k] == m:
                f = math.sqrt(1 - SHARE[k] ** 2) ** 0.5   # half the area rule: keeps limbs sturdy
                r = r * (1 + (f - 1) * sm(fork_s[k] - 5, fork_s[k] + 25, L))
        R[m] = r
    return R


def check(c, R):
    paths = c['paths']
    climbs = {m: climb_min(paths[m], E0[2] + 2) for m in range(7)}
    if min(climbs.values()) < MIN_CLIMB:
        return None
    for m in range(7):
        P = paths[m]
        far = arclen(P) > 15
        if m != 0 and (P[far, 1] - R[m][far]).min() < MIN_Y:
            return None
        if P[-1, 2] + R[m][-1] > c['top'] + 0.5:
            return None
    # clearances
    worst = 99.0
    for i in range(7):
        for j in range(i + 1, 7):
            Pi, Pj, Ri, Rj = paths[i], paths[j], R[i], R[j]
            Li, Lj = arclen(Pi), arclen(Pj)
            mi = np.ones(len(Pi), bool)
            mj = np.ones(len(Pj), bool)
            if PARENT[j] == i:
                mj = Lj > 35
            if PARENT[i] == j:
                mi = Li > 35
            if PARENT[i] == PARENT[j] and PARENT[i] >= 0:      # siblings: skip both starts
                mi, mj = Li > 30, Lj > 30
            if i == 0 and PARENT[j] == 0 or j == 0 and PARENT[i] == 0:
                pass
            A, B = Pi[mi], Pj[mj]
            if len(A) == 0 or len(B) == 0:
                continue
            D = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2) - Ri[mi][:, None] - Rj[mj][None, :]
            worst = min(worst, D.min())
            if D.min() < GAP:
                return None
    T = np.array([c['tips'][m][[0, 2]] for m in range(7)])
    dmin = min(np.linalg.norm(T[a] - T[b]) for a in range(7) for b in range(a + 1, 7))
    return dict(climbs=climbs, clearance=worst, tip_gap=dmin, score=dmin + 0.1 * np.ptp(T[:, 0]))


def write_scad(c, R, info, seed, tries, out):
    def arr(P):
        return '[' + ','.join('[%.2f,%.2f,%.2f]' % tuple(p) for p in P) + ']'

    def arr1(r):
        return '[' + ','.join('%.2f' % x for x in r) + ']'

    lines = ['// Written by Wall_Climber_Tree_layout.py %d %d -- do not edit; re-run the script.' % (seed, tries),
             '// Climb >= %.1f deg, clearance between members %.1f mm, tips >= %.1f mm apart.'
             % (min(info['climbs'].values()), info['clearance'], info['tip_gap']),
             'layout_check = [%.2f, %.2f, %.2f, %.2f];   // E0 z, climb, burl_h, trunk_r it was made for'
             % (E0[2], CLIMB, BURL_H, R_T),
             'layout_part_z = %.2f;   // the first parting' % c['z_part'],
             'layout_top = %.2f;      // tips end below this' % c['top'],
             'layout_straight = %.2f; // the trunk is straight (along A0) up to this arc length' % S_STRAIGHT,
             'layout_parent = %s;' % json.dumps(PARENT),
             'layout_fork_s = %s;' % json.dumps([round(c['fork_s'].get(m, 0), 2) for m in range(7)]),
             'layout_P = [']
    lines += ['  ' + arr(c['paths'][m]) + (',' if m < 6 else '') for m in range(7)]
    lines += ['];', 'layout_R = [']
    lines += ['  ' + arr1(R[m]) + (',' if m < 6 else '') for m in range(7)]
    lines += ['];']
    open(out, 'w').write('\n'.join(lines) + '\n')


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    tries = int(sys.argv[2]) if len(sys.argv) > 2 else 3000
    rng = np.random.default_rng(seed)
    best = None
    ok = 0
    for _ in range(tries):
        c = draw(rng)
        R = radii(c)
        info = check(c, R)
        if info is None:
            continue
        ok += 1
        if best is None or info['score'] > best[2]['score']:
            best = (c, R, info)
    if best is None:
        sys.exit('no crown passed the checks; try more tries or another seed')
    c, R, info = best
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Wall_Climber_Tree_layout.scad')
    write_scad(c, R, info, seed, tries, out)
    print('seed %d: %d of %d crowns passed; best: tips %.1f mm apart, clearance %.1f mm, climb >= %.1f deg'
          % (seed, ok, tries, info['tip_gap'], info['clearance'], min(info['climbs'].values())))
    print('first parting at z %.1f, top %.1f; tips (x, y, z):' % (c['z_part'], c['top']))
    for m in range(7):
        print('  %d  %s  climb >= %.1f' % (m, np.round(c['paths'][m][-1], 1), info['climbs'][m]))
    print('wrote', out)


if __name__ == '__main__':
    main()
