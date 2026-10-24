"""Crown layout for Wall_Climber_Tree.scad (iteration 7): searches the branch paths and writes them
to Wall_Climber_Tree_layout.scad, which the design includes.

    python Wall_Climber_Tree_layout.py 92 80           <- the layout in the .scad (best of seeds 91-98)
    python Wall_Climber_Tree_layout.py SEED TRIES [OUT] [--bend F]
                                                       <- --bend scales every curvature (the catalogue)

Iteration 7 (on top of iteration 6):
  grown, not aimed  a member is no longer a curve from its start to a chosen tip. It grows a
                    millimetre at a time from its start (grow): its heading turns by a curvature
                    whose plane rotates round the heading as it goes (a twist: a slow one bends it
                    in an arc, a fast one winds it into a loose helix), plus a gentle side-to-side
                    wiggle. Where it ends is wherever the growth took it.
  any direction     a fork only leans towards a drawn direction while it peels off its parent (its
                    first 25 %); after that it bends freely: sideways, out, up, or back towards
                    the wall. Main branches bend hardest (curvature 1/80..1/36 per mm), twigs least.
  60 deg printing   the climb limit drops from 45 to 30 deg (60 deg from vertical, the house rule);
                    growth is held at >= 33.5 deg (MIN_CLIMB + margin for the bark) and checked
                    >= 32. A heading that would dip below is lifted, keeping its azimuth, and a
                    pull upwards near it makes a branch arc up off it rather than ride it straight.
  the wall          a heading towards the wall is allowed while there is room: its pull towards
                    the wall shrinks with the distance left (1 per 20 mm), so a branch running at
                    the wall turns to run along it instead of crossing MIN_Y. The bed edge (MAX_X)
                    and the reach out (MAX_Y) steer the same way.
  bend score        crowns score for how far their main branches turn (total turning of the leader,
                    limbs and their forks) and for the length of branch heading back to the wall.

Iteration 6: stronger zigzag, a strict 3 -> 7 -> 13 split, forks capped at their parent's thinned
radius minus INSET, fork shares 68/66/64 %, tips at 60 % of a member's start radius. Iteration 5:
zigzag (replaced here by the wiggle), entangling forks (ENTANGLE), the leader leaving the trunk
exactly along it. Iteration 4: forks that leave close along their parent and peel away, thinner
forks, forks only past their parent's own joint, a fork's direction chosen by what is free, the WHY
counter. Iteration 3: meetings where members may grow into each other (MERGE_MAX over MEET_LEN).

The tree is 3 -> 7 -> 13:
  level 1  the trunk leaves the wall (straight through the burl, along A0) and carries on as the
           leader; two limbs part from it just above the burl, at different heights   -> 3
  level 2  4 forks: two off the leader, one off each limb                              -> 7
  level 3  6 different branches of those 7 fork once each                              -> 13
Nothing ends higher than `CROWN_H` above the first parting.

Radii: a fork takes `SHARE[level]` of its parent's radius there, the parent thins over -5..+25 mm
of the fork, and every member tapers to a blunt tip. The curvature is capped at 1 / (3.5 r) so the
tube's rings never fold over on the inside of a bend.

Hard checks (a draw is rejected otherwise): climb >= MIN_CLIMB along every member (the tree prints
standing); where members meet, a merge of at most MERGE_MAX over at most MEET_LEN mm (a child is
not checked against its parent over its first half, at least SKIP_CHILD mm: that is the joint; nor
siblings forking close together over their first 30 mm); nothing nearer the wall than MIN_Y; no tip
cap above the top; tips spanning MIN_SPAN along the wall. Score: the smallest distance between two
tips, plus the volume they spread over (x 4), plus 5 for each meeting (up to 10), plus the bend.

The trunk numbers (E0, climb, burl_h, r_t) mirror the .scad; it asserts that they match.
"""
import collections, json, math, os, sys
import numpy as np

# Why fork candidates were turned down, by level (python -c "...; print(L.WHY)" after a search).
WHY = collections.Counter()

# ---- mirrored from Wall_Climber_Tree.scad
E0 = np.array([0.0, 0.0, 37.0])     # where the trunk axis meets the wall
CLIMB = 50.0                        # trunk_climb
BURL_H = 34.0                       # burl_h
R_T = 11.0                          # trunk_r
A0 = np.array([0.0, math.cos(math.radians(CLIMB)), math.sin(math.radians(CLIMB))])

# ---- crown
CROWN_H = 150.0                     # tips end within this height above the first parting
STEP = 1.0                          # growth step and sample spacing along members (mm)
ENTANGLE = 20.0                     # how much a fork prefers to meet other branches (mm of spread)
MERGE_MAX = 0.35                    # members may sink into each other by this share of the thinner
MEET_LEN = 24                       # ... over at most this length of either (mm)
MIN_SPAN = 200                      # the tips must span at least this along the wall (mm):
                                    # 215 left only limbs running straight at the climb limit
MAX_X = 145                         # ... but the crown stays within this of the trunk (the bed)
MIN_Y = 13.0                        # no crown surface nearer the wall past a member's first 15 mm
MAX_Y = 150.0                       # how far out from the wall the crown may reach
MIN_CLIMB = 32.0                    # checked: 30 deg is the 60 deg overhang limit; 2 deg for bark
HOLD_CLIMB = 33.5                   # growth is held above this
TIP_MIN, TIP_SHARE = 2.2, 0.60
R_MIN = 1.8                         # no fork starts thinner than this (it would be a twig)
INSET = 1.0                         # a fork starts this much thinner than its parent (its bark)
SHARE = {1: 0.68, 2: 0.66, 3: 0.64}                  # radius share of a fork, by level
LENGTH = {1: (170, 225), 2: (100, 150), 3: (50, 95)}  # member length range, by level (mm)
LEAD_LEN = (175, 235)                                # the leader beyond the trunk's straight part
CLIMB_RANGE = {1: (38, 62), 2: (40, 70), 3: (42, 75)}  # climb of the direction a fork peels towards
BEND = {1: (1 / 80, 1 / 36), 2: (1 / 90, 1 / 42), 3: (1 / 140, 1 / 65)}   # curvature, by level
TWIST = {1: (0.2, 1.4), 2: (0.2, 1.2), 3: (0.0, 0.8)}   # turns of the bend plane over the member
BEND_F = 1.0                        # scales BEND (--bend; the catalogue's strong-bend designs)
WALL_PULL = 20.0                    # mm of room per unit of heading towards the wall (or bed edge)
SKIP_CHILD = 45                     # a fork is not checked against its parent over its first half,
                                    # at least this long: it peels off slowly, and that is the joint
S_STRAIGHT = BURL_H / math.cos(math.radians(CLIMB)) + 6    # the trunk is straight through the burl


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def smf(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def unit(v):
    return v / np.linalg.norm(v)


def arclen(P):
    return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])


def at(P, L, s):
    """Point and unit tangent at arc length s along polyline P."""
    i = int(np.clip(np.searchsorted(L, s), 1, len(P) - 1))
    f = (s - L[i - 1]) / max(L[i] - L[i - 1], 1e-9)
    return P[i - 1] + f * (P[i] - P[i - 1]), unit(P[i] - P[i - 1])


def genes(rng, level):
    """How a member grows: curvature (1/mm), turns of its bend plane over its length and which way,
    the bend plane's start angle, a slow swell of the curvature, and the wiggle (curvature,
    wavelength, phase)."""
    return dict(k=BEND_F * rng.uniform(*BEND[level]), turns=rng.uniform(*TWIST[level]) * rng.choice([-1, 1]),
                psi=rng.uniform(0, 2 * np.pi), swell=(rng.uniform(70, 160), rng.uniform(0, 2 * np.pi)),
                wig=(rng.uniform(0.012, 0.03), rng.uniform(45, 80), rng.uniform(0, 2 * np.pi)))


def grow(A, d0, L, r0, g, top, D=None, ramp=15.0):
    """Grow a member from A along d0 for L mm (or until it reaches the top), one STEP at a time.
    The heading turns by curvature g['k'] (swelling slowly between 40 and 100 %) in a plane that
    rotates g['turns'] times round the heading over L (parallel-transported frame: the rotation is
    the twist), plus a wiggle across it. The curvature ramps in over `ramp` mm, so the member
    leaves exactly along d0. D: a direction it is pulled towards over its first 25 % (a fork
    peeling off its parent). Then the heading is steered: towards the wall only as much as the room
    left allows (1 per WALL_PULL mm), likewise towards the bed edge and the reach out, and never
    below HOLD_CLIMB (lifted, keeping its azimuth); a pull upwards within 16 deg of that limit, so
    a branch arcs up off it instead of running straight along it.
    Plain floats: this runs some 10^5 steps per tree."""
    hx, hy, hz = (float(c) for c in unit(d0))
    # a normal to the heading, parallel-transported along
    nx, ny, nz = (0.0, 0.0, 1.0) if abs(hz) < 0.9 else (1.0, 0.0, 0.0)
    dt = nx * hx + ny * hy + nz * hz
    nx, ny, nz = nx - dt * hx, ny - dt * hy, nz - dt * hz
    nn = math.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / nn, ny / nn, nz / nn
    px, py, pz = (float(c) for c in A)
    kmax = 1.0 / (3.5 * r0)
    tw = 2 * math.pi * g['turns'] / L
    sl, sp = g['swell']
    kw, lw, pw = g['wig']
    hz_min = math.sin(math.radians(HOLD_CLIMB))
    peel = 0.25 * L
    out = [(px, py, pz)]
    s = 0.0
    while s < L and pz + r0 * 0.6 < top - 4:
        s += STEP
        bx, by, bz = ny * hz - nz * hy, nz * hx - nx * hz, nx * hy - ny * hx     # binormal h x n
        ramp_f = smf(0, ramp, s)
        psi = g['psi'] + tw * s
        k = g['k'] * (0.7 + 0.3 * math.sin(2 * math.pi * s / sl + sp))
        w = kw * math.sin(2 * math.pi * s / lw + pw)
        c1 = ramp_f * (k * math.cos(psi) - w * math.sin(psi))
        c2 = ramp_f * (k * math.sin(psi) + w * math.cos(psi))
        kk = math.hypot(c1, c2)
        if kk > kmax:
            c1, c2 = c1 * kmax / kk, c2 * kmax / kk
        vx, vy, vz = c1 * nx + c2 * bx, c1 * ny + c2 * by, c1 * nz + c2 * bz
        if D is not None and s < peel:                   # peel towards D
            f = 0.03 * (1 - s / peel) * ramp_f
            dd = D[0] * hx + D[1] * hy + D[2] * hz
            vx, vy, vz = vx + f * (D[0] - dd * hx), vy + f * (D[1] - dd * hy), vz + f * (D[2] - dd * hz)
        up = 0.012 * smf(HOLD_CLIMB + 16, HOLD_CLIMB + 1, math.degrees(math.asin(max(-1, min(1, hz)))))
        vz += up * (1 - hz * hz)
        hx, hy, hz = hx + vx * STEP, hy + vy * STEP, hz + vz * STEP
        hn = math.sqrt(hx * hx + hy * hy + hz * hz)
        hx, hy, hz = hx / hn, hy / hn, hz / hn
        # steering: the wall (y), the reach out (MAX_Y) and the bed edge (|x| <= MAX_X)
        hy = max(hy, -max(0.0, py - r0 - MIN_Y - 1.5) / WALL_PULL)
        hy = min(hy, max(0.0, MAX_Y - py) / WALL_PULL)
        hx = max(min(hx, max(0.0, MAX_X - px) / WALL_PULL), -max(0.0, MAX_X + px) / WALL_PULL)
        if hz < hz_min:
            hz = hz_min
        hh = math.hypot(hx, hy)
        want = math.sqrt(max(0.0, 1 - hz * hz))
        if hh > 1e-9:
            hx, hy = hx * want / hh, hy * want / hh
        else:
            hz = 1.0
        hn = math.sqrt(hx * hx + hy * hy + hz * hz)
        hx, hy, hz = hx / hn, hy / hn, hz / hn
        dt = nx * hx + ny * hy + nz * hz                 # transport the normal
        nx, ny, nz = nx - dt * hx, ny - dt * hy, nz - dt * hz
        nn = math.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / nn, ny / nn, nz / nn
        px, py, pz = px + hx * STEP, py + hy * STEP, pz + hz * STEP
        out.append((px, py, pz))
    return np.array(out)


def climb_min(P, z_from=-1e9):
    d = np.diff(P, axis=0)
    c = np.degrees(np.arctan2(d[:, 2], np.hypot(d[:, 0], d[:, 1])))
    keep = P[1:, 2] > z_from
    return c[keep].min() if keep.any() else 90.0


def turning(P, s_from=0.0):
    """Total turning of a path (deg) past arc length s_from."""
    T = np.diff(P, axis=0)
    T = T / np.linalg.norm(T, axis=1)[:, None]
    keep = arclen(P)[1:-1] > s_from
    a = np.degrees(np.arccos(np.clip((T[1:] * T[:-1]).sum(1), -1, 1)))
    return a[keep].sum()


def wallward(P, s_from=15.0):
    """Length (mm) of a path heading back towards the wall (more than 15 deg of its heading)."""
    d = np.diff(P, axis=0)
    keep = arclen(P)[1:] > s_from
    return float(((d[:, 1] < -0.26 * np.linalg.norm(d, axis=1)) & keep).sum() * STEP)


def direction(rng, base_az, spread, level):
    az = math.radians(base_az + rng.uniform(-spread, spread))
    cl = math.radians(rng.uniform(*CLIMB_RANGE[level]))
    return np.array([math.cos(cl) * math.cos(az), math.cos(cl) * math.sin(az), math.sin(cl)])


def draw(rng):
    """One random crown: dict of members {parent, level, fork_s, P} or None."""
    s1 = rng.uniform(34, 40)
    s2 = s1 + rng.uniform(8, 14)
    z_part = E0[2] + s1 * A0[2]
    top = z_part + CROWN_H
    M = []
    # leader: on from the straight trunk, exactly along it, then bending freely
    S1 = E0 + S_STRAIGHT * A0
    n0 = int(S_STRAIGHT + 4)
    straight = E0[None] + np.linspace(-4, S_STRAIGHT, n0 + 1)[:, None] * A0[None]
    hand0 = rng.choice([-1, 1])
    for _ in range(25):
        g = genes(rng, 1)
        P = grow(S1, A0, rng.uniform(*LEAD_LEN), R_T * 0.75, g, top, ramp=20.0)
        if arclen(P)[-1] < 120:
            continue
        P0 = np.vstack([straight, P[1:]])
        if climb_min(P0, E0[2] + 2) >= MIN_CLIMB:
            break
    else:
        return None
    M.append(dict(parent=-1, level=1, fork_s=0.0, P=P0, hand=hand0))
    M[0]['r'] = base_radius(M[0], M)

    def fork(parent, s, base_az, spread, level):
        """Grow one fork. Candidates peel towards base_az +- spread and then bend as they grow; of
        those that climb, stay off the wall and meet the members already there acceptably, the
        one whose tip lands furthest from every tip so far is kept (plus ENTANGLE per branch it
        meets, up to 2, and its own bend for the main branches)."""
        Pp = M[parent]['P']
        Lp = arclen(Pp)
        back = 5 + 1.5 * rng.uniform()
        A, d = at(Pp, Lp, s - back)
        tips = np.array([m['P'][-1] for m in M])
        best, best_d = None, -1.0
        stub = dict(parent=parent, level=level, fork_s=s, P=np.array([A, A + d]))
        r0 = fork_r0(stub, M)
        if r0 is None:
            WHY['L%d parent too thin' % level] += 1
            return False
        for _ in range(40):
            D = direction(rng, base_az, spread, level)
            d0 = unit(d + 0.35 * D + np.array([0, 0, 0.2]))
            L = rng.uniform(*LENGTH[level])
            P = grow(A, d0, L, r0, genes(rng, level), top, D=D)
            if arclen(P)[-1] < (20 if level == 3 else min(40, 0.5 * LENGTH[level][0])):
                WHY['L%d short' % level] += 1
                continue
            mem = dict(parent=parent, level=level, fork_s=s, P=P)
            mem['r'] = base_radius(mem, M)
            r = mem['r']
            if climb_min(P, E0[2] + 2) < MIN_CLIMB:
                WHY['L%d climb' % level] += 1
                continue
            far = arclen(P) > 15
            if (P[far, 1] - r[far]).min() < MIN_Y:
                WHY['L%d wall' % level] += 1
                continue
            if np.abs(P[:, 0]).max() > MAX_X:
                WHY['L%d bed' % level] += 1
                continue
            cs = [contact(M + [mem], k, len(M), margin=0.05) for k in range(len(M))]
            if not all(meet_ok(c) for c in cs):
                WHY['L%d meeting' % level] += 1
                continue
            meets = sum(1 for c in cs if c[0] < 0.3)
            dist = np.linalg.norm(tips - P[-1], axis=1).min() + ENTANGLE * min(meets, 2)
            if level <= 2:                               # the furthest tip is the straightest
                dist += (0.6 if level == 1 else 0.3) * turning(P, 20) + 0.3 * min(wallward(P), 60)
            if dist > best_d:
                best, best_d = mem, dist
        if best is None:
            WHY['L%d fork failed' % level] += 1
            return False
        M.append(best)
        return True

    # level 1: two limbs, one to each side (azimuth 180 = -x, 0 = +x), tilted out from the wall
    side = 1 if rng.uniform() < 0.5 else -1
    if not fork(0, s1, 90 + side * rng.uniform(55, 80), 20, 1):
        return None
    if not fork(0, s2, 90 - side * rng.uniform(55, 80), 20, 1):
        return None
    # level 2: two off the leader, one off each limb; forks leave a member past its own joint
    f3 = rng.uniform(0.36, 0.46)
    for parent, frac in ((0, f3), (0, f3 + rng.uniform(0.20, 0.28)),
                         (1, rng.uniform(0.45, 0.65)), (2, rng.uniform(0.45, 0.65))):
        Lp = arclen(M[parent]['P'])[-1]
        if not (fork(parent, frac * Lp, 90, 130, 2) or  # any way; the freest wins
                fork(parent, min(0.9, frac + 0.12) * Lp, 90, 130, 2)):
            return None
    # level 3: a strict 7 -> 13: six different branches fork once each
    placed = 0
    for parent in rng.permutation(7):
        if placed == 6:
            break
        Lp = arclen(M[int(parent)]['P'])[-1]
        ok = fork(int(parent), rng.uniform(0.50, 0.75) * Lp, 90, 130, 3) or \
            fork(int(parent), rng.uniform(0.35, 0.50) * Lp, 90, 130, 3)
        placed += ok
    if placed < 6:
        return None
    return dict(M=M, z_part=z_part, top=top)


def fork_r0(mem, M):
    p = M[mem['parent']]
    Lp = arclen(p['P'])
    i = min(np.searchsorted(Lp, mem['fork_s']), len(Lp) - 1)
    r0 = min(SHARE[mem['level']] * p['r'][i], p['r'][i] - INSET)
    return None if r0 < R_MIN else r0


def base_radius(mem, M):
    """A member's radius before its own forks thin it: a share of its parent's radius at the fork,
    tapering to a blunt tip."""
    P = mem['P']
    L = arclen(P)
    if mem['parent'] < 0:
        u = np.clip((L - S_STRAIGHT) / (L[-1] - S_STRAIGHT), 0, 1)
        r1 = max(TIP_MIN, TIP_SHARE * R_T)
        return np.where(L <= S_STRAIGHT, R_T, r1 + (R_T - r1) * (1 - u ** 1.6))
    r0 = fork_r0(mem, M)
    r1 = min(r0, max(TIP_MIN, TIP_SHARE * r0))
    u = L / L[-1]
    return r1 + (r0 - r1) * (1 - u ** 1.6)


def contact(M, i, j, R=None, margin=0.0):
    """How members i and j meet (skipping where they are joined by a fork): the smallest gap between
    their surfaces, the deepest overlap as a share of the thinner one's thickness there, and the
    length (mm, of the longer side) over which they overlap."""
    mi, mj = related_masks(M, i, j)
    A, B = M[i]['P'][mi], M[j]['P'][mj]
    if len(A) == 0 or len(B) == 0:
        return 99.0, 0.0, 0
    ri = (M[i]['r'] if R is None else R[i])[mi]
    rj = (M[j]['r'] if R is None else R[j])[mj]
    D = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2) - ri[:, None] - rj[None, :]
    thin = 2 * np.minimum(ri[:, None], rj[None, :])
    depth = (-D / thin).max() + margin
    over = D < 0
    return D.min(), max(0.0, depth), int(max(over.any(1).sum(), over.any(0).sum()))


def meet_ok(c):
    return c[1] <= MERGE_MAX and c[2] <= MEET_LEN


def self_ok(P, r):
    """A member that winds round may not run into itself: points more than 4 radii apart along it
    must stay a diameter apart in space."""
    L = arclen(P)
    D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    far = np.abs(L[:, None] - L[None, :]) > 4 * np.maximum(r[:, None], r[None, :]) + 6
    return not (far & (D < r[:, None] + r[None, :] + 1.0)).any()


def radii(c):
    """Radius along every member, with forks thinning their parents."""
    M = c['M']
    R = [mem['r'].copy() for mem in M]
    # parents thin after their forks (half the area rule, so limbs stay sturdy)
    for m, mem in enumerate(M):
        if mem['parent'] < 0:
            continue
        p = mem['parent']
        Lp = arclen(M[p]['P'])
        f = math.sqrt(1 - SHARE[mem['level']] ** 2) ** 0.5
        R[p] = R[p] * (1 + (f - 1) * sm(mem['fork_s'] - 5, mem['fork_s'] + 25, Lp))
    # cap every fork at the parent's final radius there minus INSET, parents first (iteration 6)
    for m, mem in enumerate(M):
        if mem['parent'] < 0:
            continue
        p = mem['parent']
        Lp = arclen(M[p]['P'])
        i = min(np.searchsorted(Lp, mem['fork_s']), len(Lp) - 1)
        cap = R[p][max(0, i - 8):i + 1].min() - INSET
        L = arclen(mem['P'])
        top = R[m][L < 25].max()
        if top > cap:
            R[m] = np.maximum(R[m] * cap / top, min(1.8, cap))
    return R


def related_masks(M, i, j):
    Li, Lj = arclen(M[i]['P']), arclen(M[j]['P'])
    mi, mj = np.ones(len(Li), bool), np.ones(len(Lj), bool)
    if M[j]['parent'] == i:
        mj = Lj > max(SKIP_CHILD, 0.5 * Lj[-1])
    if M[i]['parent'] == j:
        mi = Li > max(SKIP_CHILD, 0.5 * Li[-1])
    if M[i]['parent'] == M[j]['parent'] >= 0 and abs(M[i]['fork_s'] - M[j]['fork_s']) < 25:
        mi, mj = Li > 30, Lj > 30
    return mi, mj


def check(c, R):
    M = c['M']
    n = len(M)
    climbs = [climb_min(m['P'], E0[2] + 2) for m in M]
    if min(climbs) < MIN_CLIMB:
        return None
    for m in range(n):
        P = M[m]['P']
        far = arclen(P) > 15
        if m != 0 and (P[far, 1] - R[m][far]).min() < MIN_Y:
            return None
        if P[-1, 2] + R[m][-1] > c['top'] + 0.5:
            return None
        if not self_ok(P[arclen(P) > (S_STRAIGHT if m == 0 else 0)],
                       R[m][arclen(P) > (S_STRAIGHT if m == 0 else 0)]):
            return None
    C = [contact(M, i, j, R) for i in range(n) for j in range(i + 1, n)]
    if not all(meet_ok(c) for c in C):
        return None
    worst = min(c[0] for c in C)
    meetings = sum(1 for c in C if c[0] < 0.3)
    merge = max(c[1] for c in C)
    T = np.array([m['P'][-1] for m in M])
    if np.ptp(T[:, 0]) < MIN_SPAN:                       # rewarding meetings alone bunches the crown
        return None
    dmin = min(np.linalg.norm(T[a] - T[b]) for a in range(n) for b in range(a + 1, n))
    spread = np.ptp(T[:, 0]) * np.ptp(T[:, 1]) * np.ptp(T[:, 2]) ** 0.5 / 1e4
    main = [m for m in range(n) if M[m]['level'] <= 2]
    turns = [turning(M[m]['P'], S_STRAIGHT + 2 if m == 0 else 20) for m in range(n)]
    bend = float(np.mean([turns[m] for m in main]))
    wall = sum(wallward(M[m]['P']) for m in main)
    return dict(climbs=climbs, clearance=worst, tip_gap=dmin, meetings=meetings, merge=merge,
                turns=turns, bend=bend, wall=wall,
                score=dmin + 4.0 * spread + 5.0 * min(meetings, 10) + 0.4 * bend + 0.2 * min(wall, 80),
                lengths=[arclen(m['P'])[-1] for m in M])


def write_scad(c, R, info, seed, tries, out):
    M = c['M']

    def arr(P):
        return '[' + ','.join('[%.2f,%.2f,%.2f]' % tuple(p) for p in P) + ']'

    def arr1(r):
        return '[' + ','.join('%.2f' % x for x in r) + ']'

    lines = ['// Written by Wall_Climber_Tree_layout.py %d %d%s -- do not edit; re-run the script.'
             % (seed, tries, '' if BEND_F == 1 else ' --bend %g' % BEND_F),
             '// 3 -> 7 -> 13, grown. Climb >= %.1f deg, %d meetings (merge <= %.0f %%), tips >= %.1f mm apart,'
             % (min(info['climbs']), info['meetings'], 100 * info['merge'], info['tip_gap']),
             '// main branches turn %.0f deg on average, %.0f mm of them head back to the wall.'
             % (info['bend'], info['wall']),
             'layout_check = [%.2f, %.2f, %.2f, %.2f];   // E0 z, climb, burl_h, trunk_r it was made for'
             % (E0[2], CLIMB, BURL_H, R_T),
             'layout_part_z = %.2f;   // the first parting' % c['z_part'],
             'layout_top = %.2f;      // tips end below this' % c['top'],
             'layout_straight = %.2f; // the trunk is straight (along A0) up to this arc length' % S_STRAIGHT,
             'layout_parent = %s;' % json.dumps([m['parent'] for m in M]),
             'layout_level = %s;' % json.dumps([m['level'] for m in M]),
             'layout_fork_s = %s;' % json.dumps([round(m['fork_s'], 2) for m in M]),
             'layout_P = [']
    lines += ['  ' + arr(m['P']) + (',' if k < len(M) - 1 else '') for k, m in enumerate(M)]
    lines += ['];', 'layout_R = [']
    lines += ['  ' + arr1(r) + (',' if k < len(R) - 1 else '') for k, r in enumerate(R)]
    lines += ['];']
    open(out, 'w').write('\n'.join(lines) + '\n')


def search(seed, tries):
    rng = np.random.default_rng(seed)
    best, ok = None, 0
    for _ in range(tries):
        c = draw(rng)
        if c is None:
            continue
        R = radii(c)
        info = check(c, R)
        if info is None:
            WHY['tree check'] += 1
            continue
        ok += 1
        if best is None or info['score'] > best[2]['score']:
            best = (c, R, info)
    return best, ok


def main():
    global BEND_F
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('seed', type=int, nargs='?', default=92)
    ap.add_argument('tries', type=int, nargs='?', default=80)
    ap.add_argument('out', nargs='?',
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Wall_Climber_Tree_layout.scad'))
    ap.add_argument('--bend', type=float, default=1.0, help='scale every curvature by this')
    a = ap.parse_args()
    seed, tries, out, BEND_F = a.seed, a.tries, a.out, a.bend
    best, ok = search(seed, tries)
    if best is None:
        print(dict(WHY))
        sys.exit('no crown passed the checks; try more tries or another seed')
    c, R, info = best
    write_scad(c, R, info, seed, tries, out)
    T = np.array([m['P'][-1] for m in c['M']])
    print('seed %d: %d of %d crowns passed; best: score %.1f, tips %.1f mm apart, %d meetings (merge <= %.0f %%), climb >= %.1f deg'
          % (seed, ok, tries, info['score'], info['tip_gap'], info['meetings'], 100 * info['merge'], min(info['climbs'])))
    print('bend: main branches turn %.0f deg on average; %.0f mm head back to the wall' % (info['bend'], info['wall']))
    print('turning per member (deg):', ' '.join('%.0f' % t for t in info['turns']))
    print('first parting at z %.1f, top %.1f; tips span x %.0f..%.0f, y %.0f..%.0f, z %.0f..%.0f'
          % (c['z_part'], c['top'], T[:, 0].min(), T[:, 0].max(), T[:, 1].min(), T[:, 1].max(),
             T[:, 2].min(), T[:, 2].max()))
    print('member lengths (mm):', ' '.join('%.0f' % l for l in info['lengths']))
    print('WHY:', dict(WHY))
    print('wrote', out)


if __name__ == '__main__':
    main()
