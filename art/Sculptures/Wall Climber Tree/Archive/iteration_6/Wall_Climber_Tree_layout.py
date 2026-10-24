"""Crown layout for Wall_Climber_Tree.scad (iteration 6): searches the branch paths and writes them
to Wall_Climber_Tree_layout.scad, which the design includes.

    python Wall_Climber_Tree_layout.py 61 120      <- the layout in the .scad (best of seeds 61-66)

Iteration 6 (on top of iteration 5):
  stronger zigzag one bend every 22..38 mm (was 30..50), up to 5, each swing taking 50 % of the
                  climb budget (was 35 %, cap 22 mm); the swirl drops to 12 % (was 25 %).
  more sprawl     longer members (limbs 165..210 mm), tips spanning >= 215 mm along the wall (230
                  was out of reach under the 45 deg climb: the widest of 15 trees spanned 226) and
                  reaching up to 160 mm out from it; the score weights the spread x 4 (was x 3).
  more tangle     merges up to 35 % of the thinner branch over up to 24 mm (was 30 %, 18 mm).
  thicker down    fork shares 68/66/64 % (was 64/62/60), tips at 60 % of a member's start radius,
                  so the branches off the limbs are still thick enough to split again; a fork is
                  still never thicker than its parent minus 1 mm.
  forks capped    at their parent's final (thinned) radius minus INSET: sized from the parent
                  before it thinned, a fork could be thicker than the leader where it left it.
  strict split    3 -> 7 -> 13 exactly: the trunk splits into 3 (the leader and two limbs), the 3
                  into 7 (two forks off the leader, one off each limb), and 6 different branches of
                  the 7 fork once each into 13 (iteration 5 let a thick branch fork twice instead).

Iteration 5 (on top of iteration 4):
  zigzag          a member is no longer a smooth Bezier: it runs through 1..4 bend points (one per
                  30..50 mm) that swing alternately to either side of its line, in a plane of its
                  own, joined by a Hermite spline (member_path). The swing takes 35 % of the climb
                  budget (the swirl, still on top, 25 %), so it still climbs >= 45 deg.
  entangle        of the fork candidates that pass, the choice adds ENTANGLE (20 mm) for each
                  branch the fork meets (up to 2) to the spread of its tip: crowns now have 5..7
                  meetings, where the spread alone gave 0..2.
  the leader      leaves the trunk's straight part exactly along it (exact=True): the tilted fork
                  start of iteration 4 kinked the leader by ~20 deg there, a crease ring.

Iteration 4 (on top of iteration 3's swirl and meetings):
  smoother forks  a fork leaves close along its parent (within ~20 deg, tilted a little up and
                  towards its tip) and peels away over ~20 % of its length, so the crotch is long
                  and narrow, and it starts thinner than its parent minus INSET, so it stays
                  hidden inside while they run together. (A collar, starting as thick as the parent
                  allows and narrowing over 22 mm, poked out of the parent within millimetres of its
                  tilted start: sleeves, floating regions, 0.57 % overhang. Dropped.) It arrives
                  along the line to its tip (arriving
                  steeper forced a shallow middle). Leaving steeper than its chord makes a fork dip
                  below the chord further on (its mean climb is the chord's), so the chord climbs
                  are steeper than in iteration 3.
  thinner forks   a fork takes 60..64 % of its parent's radius (was 66..80 %), never more than the
                  parent minus 1 mm; the main stem stays the thickest member.
  more sprawl     longer members, each fork heading wherever, among the candidates that pass, its
                  tip lands furthest from the others; tips spanning >= 200 mm along the wall (was
                  150); the score weighting the spread higher and the meetings lower.
  growing         forks leave a member only past its own joint (its first half); level 3 takes a
                  second pass so a thick member can fork twice; WHY counts every rejection.

Iteration 3 made the branches swirl and entangle: every member spirals round its own line
(0.6..1.6 turns, its radius sized from the climb it can spare, up to 14 mm), a fork turns the
opposite way to its parent, so the two wind round each other, and members may meet and grow
together where they cross, sinking into each other by at most MERGE_MAX of the thinner one's
thickness and over at most MEET_LEN mm (a long fused run would read as one thick branch).

    python Wall_Climber_Tree_layout.py [seed] [tries]

The tree is 3 -> 7 -> 13, sprawling in all directions:
  level 1  the trunk leaves the wall (straight through the burl, along A0) and carries on as the
           leader; two limbs part from it just above the burl, at different heights   -> 3
  level 2  4 forks: two off the leader, one off each limb                              -> 7
  level 3  6 more forks off those 7 (one each where they are thick enough, a second
           where not)                                                                 -> 13
A fork leaves its parent part-way up and heads off at a random azimuth (sideways along the wall,
out from it, or back towards it where there is room) and a random climb (52..76 deg); its length
shrinks with its level, so the branches end at different lengths and heights. Nothing ends higher
than `CROWN_H` above the first parting.

Each member is a cubic Bezier from a point a few mm back inside its parent (along the parent's
tangent) to its tip, leaving close along the parent and arriving along the line to the tip (see
above), plus two waves of wander scaled by the climb the member can spare (a wave
of amplitude a and length l turns it by up to atan(2 pi a / l)). Radii: a fork takes `SHARE[level]`
of its parent's radius there, the parent thins over -5..+25 mm of the fork,
and every member tapers to a blunt tip.

Hard checks (a draw is rejected otherwise): climb >= 45 deg along every member (the tree prints
standing); where members meet, a merge of at most MERGE_MAX over at most MEET_LEN mm (a child is
not checked against its parent over its first half, at least SKIP_CHILD mm: that is the joint;
nor siblings forking close together over their first 30 mm); nothing nearer the wall than MIN_Y; no tip cap above the top; tips spanning
MIN_SPAN along the wall. Score: the smallest 3D distance between two tips, plus the volume they
spread over (x 3), plus 3 for each meeting (up to 10).

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
STEP = 1.0                          # sample spacing along members (mm)
ENTANGLE = 20.0                     # how much a fork prefers to meet other branches (mm of spread)
MERGE_MAX = 0.35                    # members may sink into each other by this share of the thinner
MEET_LEN = 24                       # ... over at most this length of either (mm)
MIN_SPAN = 215                      # the tips must span at least this along the wall (mm)
MAX_X = 150                         # ... but stay within this of the trunk (the print bed)
MIN_Y = 13.0                        # no crown surface nearer the wall past a member's first 15 mm
MAX_Y = 160.0                       # how far out from the wall a tip may reach
MIN_CLIMB = 45.0
TIP_MIN, TIP_SHARE = 2.2, 0.60
R_MIN = 1.8                         # no fork starts thinner than this (it would be a twig)
INSET = 1.0                         # a fork starts this much thinner than its parent (its bark)
SHARE = {1: 0.68, 2: 0.66, 3: 0.64}               # radius share of a fork, by level
LENGTH = {1: (165, 210), 2: (95, 145), 3: (50, 95)}  # fork length range, by level (mm)
CLIMB_RANGE = {1: (52, 66), 2: (58, 74), 3: (60, 78)}   # chord climb by level: limbs sprawl most;
# a fork leaving steeper than its chord (along its parent) dips below the chord further on (its mean
# climb is the chord's), so smooth forks need steeper chords than iteration 3's
SKIP_CHILD = 45                     # a fork is not checked against its parent over its first half,
                                    # at least this long: it peels off slowly, and that is the joint
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


def hermite(Q, M):
    """Cubic Hermite spline through points Q with tangents M, sampled about STEP mm apart."""
    out = [Q[0]]
    for k in range(len(Q) - 1):
        n = max(4, int(math.ceil(np.linalg.norm(Q[k + 1] - Q[k]) * 1.15 / STEP)))
        s = np.linspace(0, 1, n + 1)[1:, None]
        h00, h10, h01, h11 = 2*s**3 - 3*s**2 + 1, s**3 - 2*s**2 + s, -2*s**3 + 3*s**2, s**3 - s**2
        out.extend(h00 * Q[k] + h10 * M[k] + h01 * Q[k + 1] + h11 * M[k + 1])
    return np.array(out)


def member_path(A, d_par, E, zz, sw, exact=False):
    """A zigzag from A to E: through 1..4 bend points that swing alternately to either side of the
    line A-E, in a plane of the member's own (zz = (bend spacing, share, plane angle)), joined by a
    Hermite spline; plus a swirl round the line (sw = (share, turns, phase, hand)), faded in over
    the first 25 %. It leaves along d_par exactly (exact: the trunk going on as the leader, no kink)
    or close along it, tilted a little up and towards the tip (a fork: a narrow crotch, and climb
    to spare where the parent has flattened). The swing and the swirl are sized from the climb the
    member can spare: the chord leaves sin a - cos a of sideways speed per mm before the member
    drops under 45 deg; the zigzag takes 35 % of it, the swirl 25 %."""
    ch = E - A
    L = np.linalg.norm(ch)
    cu = ch / L
    d0 = unit(d_par) if exact else unit(d_par + 0.3 * cu + np.array([0, 0, 0.3]))
    side = np.cross([0.0, 0.0, 1.0], cu)
    e1 = unit(side) if np.linalg.norm(side) > 1e-6 else np.array([1.0, 0, 0])   # sideways
    e2 = unit(np.cross(cu, e1))                                                  # the other way
    chord_climb = math.degrees(math.atan2(ch[2], math.hypot(ch[0], ch[1])))
    ca = math.radians(chord_climb)
    budget = max(0.0, math.sin(ca) - math.cos(ca))
    spacing, zshare, zang = zz
    nz = int(np.clip(round(L / spacing), 1, 5))
    Ls = L / (nz + 1)
    amp = min(22.0, zshare * 0.50 * budget * Ls / 2)    # two swings of amp per bend spacing
    ez = math.cos(zang) * e1 + math.sin(zang) * e2
    Q = [A] + [A + (k / (nz + 1)) * ch + (-1) ** k * amp * ez for k in range(1, nz + 1)] + [E]
    M = [d0 * np.linalg.norm(Q[1] - Q[0])] +         [(Q[k + 1] - Q[k - 1]) / 2 for k in range(1, len(Q) - 1)] + [Q[-1] - Q[-2]]
    P = hermite(Q, M)
    s = arclen(P)
    t = s / s[-1]
    share, turns, ph, hand = sw
    ra = min(8.0, share * 0.12 * budget * L / (2 * np.pi * turns))
    phi = ph + hand * 2 * np.pi * turns * t
    swirl = ra * sm(0.0, 0.25, t)[:, None] * ((np.cos(phi) - np.cos(ph))[:, None] * e1
                                              + (np.sin(phi) - np.sin(ph))[:, None] * e2)
    return P + swirl


def climb_min(P, z_from=-1e9):
    d = np.diff(P, axis=0)
    c = np.degrees(np.arctan2(d[:, 2], np.hypot(d[:, 0], d[:, 1])))
    keep = P[1:, 2] > z_from
    return c[keep].min() if keep.any() else 90.0


def wav(rng):
    """Zigzag: bend spacing (mm), share of the climb budget, plane angle round the member's line."""
    return (rng.uniform(22, 38), rng.uniform(0.75, 1.0), rng.uniform(0, 2 * np.pi))


def swirl(rng, hand):
    return (rng.uniform(0.6, 1.0), rng.uniform(0.6, 1.6), rng.uniform(0, 6.3), hand)


def heading(rng, A, base_az, spread, level, top):
    """A tip for a fork from A: azimuth near base_az (deg, 0 = +x along the wall, 90 = out from the
    wall), a random climb, a length for its level; kept off the wall and under the top."""
    for _ in range(60):
        az = base_az + rng.uniform(-spread, spread)
        cl = rng.uniform(*CLIMB_RANGE[level])
        L = rng.uniform(*LENGTH[level])
        d = np.array([math.cos(math.radians(cl)) * math.cos(math.radians(az)),
                      math.cos(math.radians(cl)) * math.sin(math.radians(az)),
                      math.sin(math.radians(cl))])
        E = A + L * d
        if E[1] < 25:                                    # heading into the wall: mirror it out
            d[1] = -d[1]
            E = A + L * d
        if E[2] > top - 4:                               # too high: shorten to fit
            E = A + (top - 4 - A[2]) / d[2] * d
        if 25 <= E[1] <= MAX_Y and abs(E[0]) <= MAX_X and \
                np.linalg.norm(E - A) > (20 if level == 3 else min(30, 0.6 * LENGTH[level][0])):
            return E                                     # a fork high up may end short
    return None


def draw(rng):
    """One random crown: dict of members {parent, level, fork_s, P} or None."""
    s1 = rng.uniform(34, 40)
    s2 = s1 + rng.uniform(8, 14)
    z_part = E0[2] + s1 * A0[2]
    top = z_part + CROWN_H
    M = []
    # leader: on from the straight trunk, out from the wall, slightly to one side
    S1 = E0 + S_STRAIGHT * A0
    n0 = int(S_STRAIGHT + 4)
    straight = E0[None] + np.linspace(-4, S_STRAIGHT, n0 + 1)[:, None] * A0[None]
    hand0 = rng.choice([-1, 1])
    for _ in range(25):
        lead_tip = heading(rng, S1, 90, 60, 1, top)
        if lead_tip is None:
            continue
        lead_tip[2] = max(lead_tip[2], top - rng.uniform(4, 30))
        sw0 = swirl(rng, hand0)
        sw0 = (0.5 * sw0[0],) + sw0[1:]                # half the swirl: it would curl into its forks
        P0 = np.vstack([straight, member_path(S1, A0, lead_tip, wav(rng), sw0, exact=True)[1:]])
        if climb_min(P0, E0[2] + 2) >= MIN_CLIMB:
            break
    else:
        return None
    M.append(dict(parent=-1, level=1, fork_s=0.0, P=P0, hand=hand0))
    M[0]['r'] = base_radius(M[0], M)

    def fork(parent, s, base_az, spread, level):
        """Grow one fork. Candidates come from base_az +- spread; of those that climb, stay off the
        wall and meet the members already there acceptably, the one whose tip lands furthest from
        every tip so far is kept (that spreads the crown by itself). All 13 drawn at once almost
        never pass together."""
        Pp = M[parent]['P']
        Lp = arclen(Pp)
        back = 5 + 1.5 * rng.uniform()
        A, d = at(Pp, Lp, s - back)
        tips = np.array([m['P'][-1] for m in M])
        best, best_d = None, -1.0
        hand = -M[parent]['hand']                        # wind round the parent the other way
        for _ in range(90):
            E = heading(rng, A, base_az, spread, level, top)
            if E is None:
                WHY['L%d no tip' % level] += 1
                continue
            mem = dict(parent=parent, level=level, fork_s=s, hand=hand,
                       P=member_path(A, d, E, wav(rng), swirl(rng, hand)))
            mem['r'] = base_radius(mem, M)
            if mem['r'] is None:
                WHY['L%d parent too thin' % level] += 1
                return False
            P, r = mem['P'], mem['r']
            if climb_min(P, E0[2] + 2) < MIN_CLIMB:
                WHY['L%d climb' % level] += 1
                continue
            far = arclen(P) > 15
            if (P[far, 1] - r[far]).min() < MIN_Y:
                WHY['L%d wall' % level] += 1
                continue
            cs = [contact(M + [mem], k, len(M), margin=0.05) for k in range(len(M))]
            if not all(meet_ok(c) for c in cs):
                WHY['L%d meeting' % level] += 1
                continue
            # spread, plus ENTANGLE for each branch it meets (up to 2): a fork that crosses another
            # and grows into it ties the crown together
            meets = sum(1 for c in cs if c[0] < 0.3)
            dist = np.linalg.norm(tips - P[-1], axis=1).min() + ENTANGLE * min(meets, 2)
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
    # level 2: two off the leader, one off each limb, each heading away from its parent's line
    L0 = arclen(M[0]['P'])[-1]
    # forks leave a member past its own joint (its first half, where it still runs along its
    # parent), and the leader's two forks lie well apart, or they run into each other
    f3 = rng.uniform(0.36, 0.46)
    for parent, frac in ((0, f3), (0, f3 + rng.uniform(0.20, 0.28)),
                         (1, rng.uniform(0.50, 0.68)), (2, rng.uniform(0.50, 0.68))):
        Lp = arclen(M[parent]['P'])[-1]
        if not (fork(parent, frac * Lp, 90, 110, 2) or  # any way off the wall; the freest wins
                fork(parent, min(0.9, frac + 0.12) * Lp, 90, 110, 2)):
            return None
    # level 3: a strict 7 -> 13: six different branches fork once each (tried in a random order;
    # one that is too thin, or finds no way, at 50..75 % along gets a second try at 35..50 %)
    placed = 0
    for parent in rng.permutation(7):
        if placed == 6:
            break
        Lp = arclen(M[int(parent)]['P'])[-1]
        ok = fork(int(parent), rng.uniform(0.50, 0.75) * Lp, 90, 110, 3) or              fork(int(parent), rng.uniform(0.35, 0.50) * Lp, 90, 110, 3)
        placed += ok
    if placed < 6:
        return None
    return dict(M=M, z_part=z_part, top=top)


def base_radius(mem, M):
    """A member's radius before its own forks thin it: a share of its parent's radius at the fork,
    tapering to a blunt tip, swelling from 60 % over its first 6 mm (inside the parent)."""
    P = mem['P']
    L = arclen(P)
    if mem['parent'] < 0:
        u = np.clip((L - S_STRAIGHT) / (L[-1] - S_STRAIGHT), 0, 1)
        r1 = max(TIP_MIN, TIP_SHARE * R_T)
        return np.where(L <= S_STRAIGHT, R_T, r1 + (R_T - r1) * (1 - u ** 1.6))
    p = M[mem['parent']]
    Lp = arclen(p['P'])
    i = min(np.searchsorted(Lp, mem['fork_s']), len(Lp) - 1)
    r0 = min(SHARE[mem['level']] * p['r'][i], p['r'][i] - INSET)
    if r0 < R_MIN:
        return None                                      # the parent is too thin to fork here
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
    # A fork was sized from its parent before the parent thinned for its own forks (the leader
    # loses ~46 % over four), so it could come out thicker than the parent where it leaves it: its
    # start then poked out below the junction with nothing under it, a region starting in mid-air.
    # Cap every fork at the parent's final radius there minus INSET, parents first (members are in
    # the order they were grown), so the cap carries down to the forks' own forks.
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
    return dict(climbs=climbs, clearance=worst, tip_gap=dmin, meetings=meetings, merge=merge,
                score=dmin + 4.0 * spread + 5.0 * min(meetings, 10),
                lengths=[arclen(m['P'])[-1] for m in M])


def write_scad(c, R, info, seed, tries, out):
    M = c['M']

    def arr(P):
        return '[' + ','.join('[%.2f,%.2f,%.2f]' % tuple(p) for p in P) + ']'

    def arr1(r):
        return '[' + ','.join('%.2f' % x for x in r) + ']'

    lines = ['// Written by Wall_Climber_Tree_layout.py %d %d -- do not edit; re-run the script.' % (seed, tries),
             '// 3 -> 7 -> 13, swirled. Climb >= %.1f deg, %d meetings (merge <= %.0f %%), tips >= %.1f mm apart.'
             % (min(info['climbs']), info['meetings'], 100 * info['merge'], info['tip_gap']),
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
            continue
        ok += 1
        if best is None or info['score'] > best[2]['score']:
            best = (c, R, info)
    return best, ok


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 61
    tries = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    best, ok = search(seed, tries)
    if best is None:
        sys.exit('no crown passed the checks; try more tries or another seed')
    c, R, info = best
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Wall_Climber_Tree_layout.scad')
    write_scad(c, R, info, seed, tries, out)
    T = np.array([m['P'][-1] for m in c['M']])
    print('seed %d: %d of %d crowns passed; best: tips %.1f mm apart, %d meetings (merge <= %.0f %%), climb >= %.1f deg'
          % (seed, ok, tries, info['tip_gap'], info['meetings'], 100 * info['merge'], min(info['climbs'])))
    print('first parting at z %.1f, top %.1f; tips span x %.0f..%.0f, y %.0f..%.0f, z %.0f..%.0f'
          % (c['z_part'], c['top'], T[:, 0].min(), T[:, 0].max(), T[:, 1].min(), T[:, 1].max(),
             T[:, 2].min(), T[:, 2].max()))
    print('member lengths (mm):', ' '.join('%.0f' % l for l in info['lengths']))
    print('wrote', out)


if __name__ == '__main__':
    main()
