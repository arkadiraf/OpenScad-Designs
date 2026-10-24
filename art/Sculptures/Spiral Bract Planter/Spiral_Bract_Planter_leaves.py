#!/usr/bin/env python3
"""Leaf workshop for the Spiral Bract Planter (iteration 2: solid bracts that bend open, with a thin
edge lip).

Every leaf on the planter is generated here from a seed: where it sits on the golden-angle spiral,
its outline (shoulder, tip, base, lopsidedness, hook), its dome (height, cross-section, tip
thickness, midrib spine), its lip thickness, how it bends open (flare, where it starts, how the flare
curves, cup or trough across, twist, tip curl) and its veins (count, slope, depth; off by default).
The .scad only draws what this script writes into it, between `// BEGIN LEAVES` and `// END LEAVES`.

What iteration 1 taught: a leaf is solid from the pot wall out to its face, so overlapping leaves
simply merge, and the leaf whose face is higher shows - which is always the lower leaf where its tip
crosses the next one's base, because a leaf fades to nothing at its base and peaks near its tip.
No air under the leaves means no pockets, nothing passing through anything, nothing floating.
Iteration 2 adds the bend (`lift`) on top of that dome, and hollows only a lip along the upper free
edges, EDGE_T thick at the edge, so the leaves read thin where you see their edges.

The `budget` step scales each leaf's bend down until none of its surfaces hangs past MAX_OVERHANG
degrees from vertical.

The shape functions mirror Spiral_Bract_leaf.scad and the envelope in Spiral_Bract_Planter.scad:
change them together.

usage:
  python Spiral_Bract_Planter_leaves.py layout [--seed 7] [--write]   # print / write the leaf table
  python Spiral_Bract_Planter_leaves.py check  [--seed 7]             # overhang of every leaf
  python Spiral_Bract_Planter_leaves.py sheet  [--seed 7] [--out sheet.png]  # every leaf, face + side
  python Spiral_Bract_Planter_leaves.py map    [--seed 7] [--out map.png]    # the planter unrolled
  python Spiral_Bract_Planter_leaves.py leaf 12 [--seed 7]                   # one leaf's genes

Every command takes `--body saucer` to work on the matching saucer (Spiral_Bract_Saucer.scad)
instead: the same leaves on a flared tray, rising into a ring of petals round the planter's foot.

The built tables: `layout --seed 7 --write` and `layout --body saucer --seed 3 --write`.
"""
import argparse, math, os, re
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- body envelope and pot: keep in step with the .scad [Body] and [Pot] blocks
R0, RB, RT = 66.0, 89.0, 72.0      # mm: radius at the bed, at the belly, at the rim
ZB, ZT = 78.0, 165.0               # mm: belly height, rim height
WALL = 4.0                         # mm, pot wall
EDGE_T = 2.5                       # mm, leaf thickness at its free edges
TEXTURE = True                     # veins on the leaves (keep in step with `texture` in the .scad)
GOLDEN = 180.0 * (3 - math.sqrt(5))  # 137.508 deg

# ---- layout knobs
SPACING = 0.037      # rise per leaf, as a share of the local radius (sets the leaf count)
L_REF = 74.0         # mm, leaf length at the belly
ASPECT = (0.34, 0.46)  # half-width / length
START = -0.50        # first base height, as a share of its length (below the bed)
CROWN = 0.55         # extra length of the top leaves
TOP = ZT + 38        # mm, highest crown tip
MAX_OVERHANG = 48.0  # deg from vertical, for any free surface of a leaf (house limit 60)

# ---- the saucer: keep in step with Spiral_Bract_Saucer.scad
BODY = 'planter'     # which body the commands work on: planter or saucer (--body)
S_RF = 79.0          # mm, inner floor radius: the planter's foot is 74.5 at the bed, 82 at 20 mm up
S_WALL = 3.0         # mm, wall under the leaves
S_FLOOR = 3.0        # mm
S_ZT = 20.0          # mm, rim height
S_TAN = math.tan(math.radians(20))   # wall flare, 20 deg from vertical
S_L_REF = 42.0       # mm, leaf length
S_SPACING = 0.0088   # rise per leaf, as a share of the radius
S_TOP = S_ZT + 18    # mm, highest petal tip

GENES = ['phi', 'z', 'L', 'W', 'tilt', 'sh', 'basep', 'tipp', 'asym', 'sway',
         'H', 'p', 'tipf', 'ridge', 'Tm', 'F', 't0', 'k', 'C', 'tw', 'curl', 'nv', 'vc', 'vd']


def ss(a, b, x):
    s = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return s * s * (3 - 2 * s)


def R(z):
    z = np.asarray(z, float)
    if BODY == 'saucer':
        return S_RF + S_WALL + (z - S_FLOOR) * S_TAN
    lo = R0 + (RB - R0) * (1 - np.cos(np.pi * np.clip(z, 0, ZB) / ZB)) / 2
    hi = RT + (RB - RT) * (1 + np.cos(np.pi * (np.clip(z, ZB, ZT) - ZB) / (ZT - ZB))) / 2
    return np.where(z <= ZB, lo, hi)


def dR(z):
    z = np.asarray(z, float)
    if BODY == 'saucer':
        return np.full_like(z, S_TAN)
    lo = (RB - R0) * np.pi / (2 * ZB) * np.sin(np.pi * np.clip(z, 0, ZB) / ZB)
    hi = -(RB - RT) * np.pi / (2 * (ZT - ZB)) * np.sin(np.pi * (np.clip(z, ZB, ZT) - ZB) / (ZT - ZB))
    return np.where((z <= 0) | (z >= ZT), 0.0, np.where(z <= ZB, lo, hi))


def under_shift(z):
    """Near the rim the leaves' solid underside reaches into the wall, to 0.6 mm short of the
    inside, so the crown stands on the rim; the faces stay put and the cavity cuts no leaf."""
    if BODY == 'saucer':
        return -(S_WALL - 1.4) * ss(S_ZT - 6, S_ZT, z)
    return -(WALL - 1.4) * ss(ZT - 15, ZT, z)


def leaf_z(g, u, t):
    x, y = leaf_xy(g, u, t)
    return g['z'] - x * math.sin(math.radians(g['tilt'])) + y * math.cos(math.radians(g['tilt']))


def rim():
    return S_ZT if BODY == 'saucer' else ZT


def top():
    return S_TOP if BODY == 'saucer' else TOP


def scad_path():
    return os.path.join(HERE, 'Spiral_Bract_Saucer.scad' if BODY == 'saucer' else 'Spiral_Bract_Planter.scad')


# ---------------------------------------------------------------- one leaf (vectorised over u, t)
def leaf_w(g, t, side):
    sh = g['sh']
    f = np.where(t <= sh, np.sin(np.pi / 2 * np.clip(t / sh, 0, 1)) ** g['basep'],
                 np.clip(np.cos(np.pi / 2 * np.clip((t - sh) / (1 - sh), 0, 1)), 0, 1) ** g['tipp'])
    return g['W'] * f * (1 + side * g['asym'])


def leaf_xc(g, t):
    return g['sway'] * g['W'] * t * t


def leaf_xy(g, u, t):
    w = leaf_w(g, t, np.where(u >= 0, 1, -1))
    return leaf_xc(g, t) + u * w, t * g['L']


def along(g, t):
    pk = min(g['sh'] + 0.1, 0.72)
    return np.where(t <= pk, np.sin(np.pi / 2 * np.clip(t / pk, 0, 1)) ** 1.3,
                    g['tipf'] + (1 - g['tipf']) * np.cos(np.pi / 2 * np.clip((t - pk) / (1 - pk), 0, 1)))


def dome(g, u, t):
    """Iteration 1's bract: a dome fading to nothing at the base and lower edges, a midrib spine,
    and an EDGE_T step along the upper edges, where they face up."""
    a = along(g, t)
    au = np.minimum(1, np.abs(u))
    return (g['H'] * a * (1 - au ** g['p'])
            + g['ridge'] * g['H'] * 0.35 * a * np.clip(1 - au / 0.4, 0, 1) ** 2
            + EDGE_T * ss(g['sh'] + 0.04, g['sh'] + 0.24, t))


def lift(g, u, t):
    """How the leaf bends open, mm outward: flare, cup / trough, twist and tip curl. Zero below t0,
    which is above the shoulder, so the lower edges stay on the body."""
    t0 = g['t0']
    s = ss(t0 - 0.05, t0 + 0.15, t)
    gg = np.clip((t - t0) / (1 - t0), 0, 1) ** g['k']
    return (g['F'] * gg + s * (g['C'] * (1 - u * u) + g['tw'] * u * ss(t0, 1, t))
            + g['curl'] * ss(0.72, 1, t) ** 2)


def thick(g, u, t):
    """Lip thickness: EDGE_T at the edge, Tm further in."""
    return EDGE_T + (g['Tm'] - EDGE_T) * (1 - u * u)


def relief(g, u, t):
    """Texture, mm: lateral veins running up and out to the edges."""
    x, y = leaf_xy(g, u, t)
    au = np.abs(u)
    ph = g['nv'] * (y - g['vc'] * np.abs(x - leaf_xc(g, t))) / g['L']
    veins = g['vd'] * ((1 + np.cos(2 * np.pi * ph)) / 2) ** 2
    fade = (1 - ss(0.72, 0.97, au)) * ss(0.06, 0.22, t) * (1 - ss(0.86, 1, t))
    return veins * fade * along(g, t)


def offsets(g, u, t, texture=None):
    """(outer, inner) offsets along the envelope normal, before the rim shift. Solid down into the
    pot wall, except a lip along the upper free edges: within 2-10 mm of the edge, where the leaf has
    bent open, the underside follows the face at the lip thickness, so the edge is EDGE_T thick."""
    texture = TEXTURE if texture is None else texture
    face = dome(g, u, t) + lift(g, u, t)
    outer = face + (relief(g, u, t) if texture else 0)
    w = leaf_w(g, t, np.where(u >= 0, 1, -1))
    dist = np.minimum((1 - np.abs(u)) * w, (1 - t) * g['L'] * 0.6)
    lip = ((1 - ss(2, 10, dist)) * ss(g['t0'] - 0.05, g['t0'] + 0.15, t)
           * ss(EDGE_T + 0.5, EDGE_T + 2.5, face))
    inner = (-0.8 + lip * np.maximum(0, face - thick(g, u, t) + 0.8)
             + (1 - lip) * under_shift(leaf_z(g, u, t)))
    return outer, inner


def to_3d(g, u, t, off):
    x, y = leaf_xy(g, u, t)
    c, s = math.cos(math.radians(g['tilt'])), math.sin(math.radians(g['tilt']))
    a, b = x * c + y * s, -x * s + y * c
    z = g['z'] + b
    r = R(z)
    phi = np.radians(g['phi']) + a / r
    d = dR(z)
    nn = np.sqrt(1 + d * d)
    return np.stack([r * np.cos(phi) + off * np.cos(phi) / nn,
                     r * np.sin(phi) + off * np.sin(phi) / nn,
                     z - off * d / nn], axis=-1)


def overhang(g, n_t=60, n_u=31):
    """Worst angle from vertical (deg) of a downward-facing free surface of the leaf, above z = 10.
    The face always counts; the underside only where the lip stands clear of the body."""
    t = np.linspace(0.02, 0.98, n_t)[:, None] * np.ones((1, n_u))
    u = np.ones((n_t, 1)) * np.linspace(-0.97, 0.97, n_u)[None, :]
    out, inn = offsets(g, u, t, texture=False)
    worst = 0.0
    for off, sign, free in ((out, 1, np.ones_like(out, bool)), (inn, -1, inn > 0.3)):
        P = to_3d(g, u, t, off)
        Pu = np.gradient(P, axis=1); Pt = np.gradient(P, axis=0)
        n = np.cross(Pu, Pt) * sign            # outward of the solid
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
        ang = np.degrees(np.arcsin(np.clip(-n[..., 2], 0, 1)))
        ok = free & (P[..., 2] > 10) & (np.abs(u) < 0.95)
        if ok.any():
            worst = max(worst, float(ang[ok].max()))
    return worst


def fit_budget(g):
    """Scale the bend genes down until the leaf stays inside MAX_OVERHANG. Returns the scale."""
    k = 1.0
    base = {key: g[key] for key in ('F', 'C', 'tw', 'curl')}
    for _ in range(30):
        if overhang(g) <= MAX_OVERHANG:
            return k
        k *= 0.88
        for key, v in base.items():
            g[key] = v * k
    return k


# ---------------------------------------------------------------- layout
def make_leaf(u, n, z, L, W, sh, crown, F, k=1.0):
    """One leaf's genes; `u(a, b)` draws from the seeded generator. `k` scales the bends and the
    height jitter (the saucer's short leaves); the dome always scales with the leaf length."""
    g = dict(
        phi=(n * GOLDEN + u(-4, 4)) % 360,
        z=z + u(-0.8, 0.8) * k,
        L=L, W=W,
        tilt=u(4, 12),           # every leaf leans the same way round: the spiral swirls
        sh=sh,
        basep=u(0.55, 0.95),     # base: <1 rounded
        tipp=u(0.85, 1.45),      # tip: 1 ogive, >1 drawn-out point
        asym=u(-0.12, 0.12),
        sway=u(-0.16, 0.16),
        H=L / L_REF * u(6.0, 9.5),   # dome height, mm
        p=u(1.6, 3.0),           # cross-section: low = pointed dome, high = flat pillow
        tipf=u(0.15, 0.35),      # dome left at the tip
        ridge=u(0.0, 1.0),       # midrib spine
        Tm=u(3.2, 4.2),          # lip thickness away from the edge, mm
        F=F,
        t0=min(0.8, sh + u(0.05, 0.3)),    # bends open above its shoulder
        k=u(1.2, 2.6),           # 1: straight flare, >1: curls out late
        C=k * u(-1.5, 3.0),      # + cupped (centre out), - trough (edges out), mm
        tw=k * u(-3.0, 3.0),     # one edge lifts more than the other, mm
        curl=u(-0.3, 0.5) * F,   # tip flicks out (+) or hooks back (-)
        nv=u(6.0, 10.0),         # lateral veins along the leaf
        vc=u(0.7, 1.4),          # vein slope: higher = veins point further up
        vd=u(0.3, 0.5),          # vein height, mm
    )
    if crown > 0.3:
        # crown leaves stand on the rim: nothing may bend back into the opening
        g['C'] = abs(g['C']); g['curl'] = abs(g['curl']); g['tw'] *= 0.35
    return g


def layout(seed, budget=True):
    return layout_saucer(seed, budget) if BODY == 'saucer' else layout_planter(seed, budget)


def layout_saucer(seed, budget=True):
    """A ring of short leaves up the flared tray wall; the top ones grow into petals over the rim."""
    rng = np.random.default_rng(seed)
    leaves, n, z = [], 0, None
    while True:
        u = lambda a, b: float(rng.uniform(a, b))
        asp = u(0.36, 0.48)
        sh = u(0.38, 0.54)
        zc = 0.0 if z is None else z
        crown = float(ss(S_ZT - 14, S_ZT - 6, zc))
        L = S_L_REF * (1 + 0.5 * crown) * u(0.9, 1.1)
        if z is None:
            z = -0.45 * L
        L = min(L, S_TOP - z)
        sh = min(sh, (S_ZT - 2 - z) / L)
        if sh * L < 8 or sh < 0.22:
            break
        g = make_leaf(u, n, z, L, L * asp, sh, crown, u(1.0, 3.0) + 5.0 * crown, L / L_REF)
        if budget:
            g['bend'] = fit_budget(g)
        leaves.append(g)
        z += S_SPACING * float(R(max(z, 0) + 0.4 * L))
        n += 1
    return leaves


def layout_planter(seed, budget=True):
    rng = np.random.default_rng(seed)
    leaves, n, z = [], 0, None
    while True:
        u = lambda a, b: float(rng.uniform(a, b))
        asp = u(*ASPECT)
        sh = u(0.38, 0.54)
        zc = 0.0 if z is None else z
        asp += 0.08 * (1 - float(ss(0, 45, zc)))    # wider at the foot, where the body is narrow
        crown = float(ss(ZT - 70, ZT - 20, zc))
        L = L_REF * (float(R(zc + 30)) / RB) * (1 + CROWN * crown) * u(0.92, 1.08)
        if z is None:
            z = START * L
        L = min(L, TOP - z)          # the crown stops at TOP
        # The shoulder must sit on the body: above the rim a leaf stands free, and edges below
        # its shoulder would hang. Crown leaves pull their shoulder down and grow a longer point.
        sh = min(sh, (ZT - 4 - z) / L)
        if sh * L < 14 or sh < 0.22:
            break
        F = u(1.5, 6.0) + 10.0 * crown           # flare at the tip, mm: opens like a flower
        g = make_leaf(u, n, z, L, L * asp, sh, crown, F)
        if budget:
            g['bend'] = fit_budget(g)
        leaves.append(g)
        z += SPACING * float(R(z + 0.4 * L))
        n += 1
    return leaves


def fmt(v):
    return f'{v:.3f}'.rstrip('0').rstrip('.')


def table_text(leaves, seed):
    body = ' --body saucer' if BODY == 'saucer' else ''
    lines = [f'// BEGIN LEAVES  (written by Spiral_Bract_Planter_leaves.py layout{body} --seed {seed} --write;'
             f' {len(leaves)} leaves)',
             '// ' + ', '.join(GENES),
             'leaves = [']
    for i, g in enumerate(leaves):
        vals = ', '.join(fmt(g[k]) for k in GENES)
        lines.append(f'    [{vals}],' if i < len(leaves) - 1 else f'    [{vals}]')
    lines += ['];', '// END LEAVES']
    return '\n'.join(lines)


def write_table(leaves, seed):
    SCAD = scad_path()
    src = open(SCAD, encoding='utf-8').read()
    new, k = re.subn(r'// BEGIN LEAVES.*?// END LEAVES', lambda m: table_text(leaves, seed), src, flags=re.S)
    if k != 1:
        raise SystemExit('markers // BEGIN LEAVES ... // END LEAVES not found once in the .scad')
    open(SCAD, 'w', encoding='utf-8', newline='\n').write(new)
    print(f'wrote {len(leaves)} leaves into {os.path.basename(SCAD)}')


# ---------------------------------------------------------------- pictures
GREEN = np.array([63, 142, 67], float) / 255


def shade(hmap, mask, px):
    """Lambert shading of a height map (mm), light from the upper left."""
    gy, gx = np.gradient(hmap, px)
    n = np.dstack([-gx, gy, np.ones_like(hmap)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    light = np.array([-0.5, 0.6, 0.62]); light /= np.linalg.norm(light)
    k = np.clip(n @ light, 0, 1) * 0.75 + 0.25
    img = np.ones(hmap.shape + (3,))
    img[mask] = (GREEN * k[..., None])[mask]
    return (img * 255).astype(np.uint8)


def splat(xy, h, px, x0, y0, Wd, Hd, zbuf, idbuf, leaf_id=0):
    c = ((xy[..., 0] - x0) / px).astype(int).ravel()
    r = (Hd - 1 - (xy[..., 1] - y0) / px).astype(int).ravel()
    h = h.ravel()
    ok = (c >= 0) & (c < Wd) & (r >= 0) & (r < Hd)
    for cc, rr, hh in zip(c[ok], r[ok], h[ok]):
        if hh > zbuf[rr, cc]:
            zbuf[rr, cc] = hh; idbuf[rr, cc] = leaf_id


def grid(g, px):
    n_t = int(g['L'] / px * 1.6); n_u = int(2 * g['W'] / px * 1.6)
    t = np.linspace(0, 1, n_t)[:, None] * np.ones((1, n_u))
    u = np.ones((n_t, 1)) * np.linspace(-1, 1, n_u)[None, :]
    return u, t


def leaf_tile(g, px=0.3):
    """Face view (flat outline, shaded by the face height) and the midrib profile from the side."""
    u, t = grid(g, px)
    x, y = leaf_xy(g, u, t)
    out, _ = offsets(g, u, t)
    x0, x1 = float(x.min()) - 2, float(x.max()) + 2
    Wd, Hd = int((x1 - x0) / px) + 1, int((g['L'] + 4) / px) + 1
    zb = np.full((Hd, Wd), -1e9); ib = np.full((Hd, Wd), -1)
    splat(np.stack([x, y], -1), out, px, x0, -2, Wd, Hd, zb, ib)
    mask = ib >= 0
    face = shade(np.where(mask, zb, 0), mask, px)
    # side view: the face and underside along the midrib (u = 0) and along one edge lip (u = 0.92)
    tt = np.linspace(0, 1, 200)
    side = Image.new('RGB', (int(34 / px), Hd), 'white')
    d = ImageDraw.Draw(side)
    for uu, col in ((0.92, (150, 200, 150)), (0.0, (63, 142, 67))):
        o, i_ = offsets(g, np.full_like(tt, uu), tt)
        poly = [(int((4 + oo) / px), int(Hd - 1 - (yy + 2) / px)) for oo, yy in zip(o, tt * g['L'])]
        poly += [(int((4 + ii) / px), int(Hd - 1 - (yy + 2) / px))
                 for ii, yy in zip(i_[::-1], (tt * g['L'])[::-1])]
        d.polygon(poly, fill=col)
    d.line([(int(4 / px), 0), (int(4 / px), Hd)], fill=(180, 180, 180))
    tile = Image.new('RGB', (face.shape[1] + side.width + 6, Hd), 'white')
    tile.paste(Image.fromarray(face), (0, 0)); tile.paste(side, (face.shape[1] + 6, 0))
    return tile


def sheet(leaves, out, cols=8):
    tiles = [leaf_tile(g) for g in leaves]
    cw = max(t.width for t in tiles) + 16
    ch = max(t.height for t in tiles) + 30
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new('RGB', (cw * cols, ch * rows), 'white')
    d = ImageDraw.Draw(img)
    for i, t in enumerate(tiles):
        cx, cy = (i % cols) * cw, (i // cols) * ch
        img.paste(t, (cx + 8, cy + 4 + (ch - 30 - t.height)))
        g = leaves[i]
        d.text((cx + 6, cy + ch - 24),
               f"#{i} z{g['z']:.0f} {g['L']:.0f}x{2 * g['W']:.0f} flare {g['F']:.1f} bend x{g.get('bend', 1):.2f}",
               fill='black')
    img.save(out)
    print(f'sheet: {len(leaves)} leaves -> {out}')


def body_map(leaves, out, px=0.5):
    """The planter unrolled at the belly radius: arc length x height, front-most leaf wins.
    Prints how much of the pot below the rim no leaf covers."""
    rb = float(R(rim() / 2))
    circ = 2 * math.pi * rb
    Wd, Hd = int(circ / px), int((top() + 4) / px)
    zbuf = np.full((Hd, Wd), -1e9); ids = np.full((Hd, Wd), -1)
    for i, g in enumerate(leaves):
        u, t = grid(g, px)
        out_, _ = offsets(g, u, t)
        P = to_3d(g, u, t, out_)
        phi = np.degrees(np.arctan2(P[..., 1], P[..., 0])) % 360
        r = np.hypot(P[..., 0], P[..., 1])
        xy = np.stack([phi / 360 * circ, P[..., 2]], -1)
        keep = P[..., 2] >= 0
        splat(xy[keep], (r - R(P[..., 2]))[keep], px, 0, 0, Wd, Hd, zbuf, ids, i)
    mask = ids >= 0
    img = shade(np.where(mask, zbuf, zbuf[mask].min() if mask.any() else 0), mask, px)
    seam = np.zeros_like(mask)
    seam[1:, :] |= ids[1:, :] != ids[:-1, :]; seam[:, 1:] |= ids[:, 1:] != ids[:, :-1]
    img[seam & mask] = (img[seam & mask] * 0.45).astype(np.uint8)
    rim_row = Hd - 1 - int(rim() / px)
    body = mask[rim_row:, :]
    img[rim_row:, :][~body] = [230, 80, 80]          # bare pot in red
    img[rim_row, :] = [200, 60, 60]
    Image.fromarray(img).save(out)
    print(f'map: {len(leaves)} leaves, {100 * body.mean():.1f} % of the pot below the rim covered -> {out}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['layout', 'check', 'sheet', 'map', 'leaf'])
    ap.add_argument('index', nargs='?', type=int)
    ap.add_argument('--seed', type=int)
    ap.add_argument('--body', choices=['planter', 'saucer'], default='planter')
    ap.add_argument('--write', action='store_true', help='layout: write the table into the .scad')
    ap.add_argument('--out', help='PNG path for sheet / map')
    a = ap.parse_args()
    global BODY
    BODY = a.body
    if a.seed is None:
        a.seed = 3 if BODY == 'saucer' else 7
    leaves = layout(a.seed)
    stem = 'Spiral_Bract_Saucer' if BODY == 'saucer' else 'Spiral_Bract_Planter'
    if a.cmd == 'layout':
        if a.write:
            write_table(leaves, a.seed)
        else:
            print(table_text(leaves, a.seed))
    elif a.cmd == 'check':
        for i, g in enumerate(leaves):
            print(f"#{i:2d} z {g['z']:6.1f}  flare {g['F']:5.1f} mm  bend x{g['bend']:.2f}  "
                  f"worst {overhang(g):4.1f} deg")
        cut = sum(g['bend'] < 1 for g in leaves)
        print(f'{cut} of {len(leaves)} leaves had their bend scaled to stay under {MAX_OVERHANG} deg')
    elif a.cmd == 'sheet':
        sheet(leaves, a.out or os.path.join(HERE, stem + '_leaf_sheet.png'))
    elif a.cmd == 'map':
        body_map(leaves, a.out or os.path.join(HERE, stem + '_map.png'))
    elif a.cmd == 'leaf':
        g = leaves[a.index]
        for k in GENES + ['bend']:
            print(f'{k:6s} {g[k]:9.3f}')
        print(f'worst overhang {overhang(g):.1f} deg')


if __name__ == '__main__':
    main()
