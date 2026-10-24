#!/usr/bin/env python3
"""Leaf workshop for the Spiral Bract Planter.

Every bract (leaf) on the planter is generated here from a seed: where it sits on the golden-angle
spiral, and its own shape genes (shoulder, tip, base, lopsidedness, hook, bulge, cross-section,
spine, edge step, flare, tilt). The .scad only draws what this script writes into it, between the
`// BEGIN LEAVES` and `// END LEAVES` markers, so a new seed gives a new planter.

The leaf shape functions below mirror `leaf_w`, `leaf_xc`, `leaf_h` and `R` in the .scad: the two
change together.

usage:
  python Spiral_Bract_Planter_leaves.py layout [--seed 7] [--write]   # print / write the leaf table
  python Spiral_Bract_Planter_leaves.py sheet  [--seed 7] [--out sheet.png]  # every leaf, flat, shaded
  python Spiral_Bract_Planter_leaves.py map    [--seed 7] [--out map.png]    # the planter unrolled
  python Spiral_Bract_Planter_leaves.py leaf 12 [--seed 7]                   # one leaf's genes

The built table: `layout --seed 7 --write` (the default seed).
"""
import argparse, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SCAD = os.path.join(HERE, 'Spiral_Bract_Planter.scad')  # this archived copy rewrites the archived .scad

# ---- body envelope: keep in step with the .scad [Body] block
R0, RB, RT = 66.0, 89.0, 72.0      # mm: radius at the bed, at the belly, at the rim
ZB, ZT = 78.0, 165.0               # mm: belly height, rim height
GOLDEN = 180.0 * (3 - math.sqrt(5))  # 137.508 deg

# ---- layout knobs
SPACING = 0.0405     # rise per leaf, as a share of the local radius (sets the leaf count)
L_REF = 74.0         # mm, leaf length at the belly
ASPECT = (0.34, 0.46)  # half-width / length
START = -0.42        # first base height, as a share of its length (below the bed)
CROWN = 0.55         # extra length of the top leaves
TOP = ZT + 38          # mm, highest crown tip


def R(z):
    """Envelope radius: cosine flanks, zero slope at the bed, the belly and the rim; vertical above."""
    if z <= 0:
        return R0
    if z <= ZB:
        return R0 + (RB - R0) * (1 - math.cos(math.pi * z / ZB)) / 2
    if z <= ZT:
        return RT + (RB - RT) * (1 + math.cos(math.pi * (z - ZB) / (ZT - ZB))) / 2
    return RT


def smoothstep(a, b, x):
    s = min(1.0, max(0.0, (x - a) / (b - a)))
    return s * s * (3 - 2 * s)


# ---- gene vector, same order as the .scad table
GENES = ['phi', 'z', 'L', 'W', 'tilt', 'sh', 'basep', 'tipp', 'asym', 'sway',
         'H', 'p', 'ridge', 'edge', 'lean', 'tipf']


def leaf_w(g, t, side):
    """Half-width on one side (+1 right, -1 left) at t (0 base .. 1 tip)."""
    if t <= g['sh']:
        f = math.sin(math.pi / 2 * t / g['sh']) ** g['basep']
    else:
        f = max(0.0, math.cos(math.pi / 2 * (t - g['sh']) / (1 - g['sh']))) ** g['tipp']
    return g['W'] * f * (1 + side * g['asym'])


def leaf_xc(g, t):
    """Midrib offset: the tip hooks sideways."""
    return g['sway'] * g['W'] * t * t


def along(g, t):
    pk = min(g['sh'] + 0.1, 0.72)
    if t <= pk:
        return math.sin(math.pi / 2 * t / pk) ** 1.3
    return g['tipf'] + (1 - g['tipf']) * math.cos(math.pi / 2 * (t - pk) / (1 - pk))


def leaf_h(g, u, t):
    """Height above the envelope at (u across -1..1, t along 0..1), mm."""
    a = along(g, t)
    au = min(1.0, abs(u))
    return (g['H'] * a * (1 - au ** g['p'])
            + g['ridge'] * g['H'] * 0.35 * a * max(0.0, 1 - au / 0.4) ** 2
            + g['edge'] * smoothstep(g['sh'] + 0.04, g['sh'] + 0.24, t)
            + g['lean'] * smoothstep(0.45, 1.0, t) ** 2)


def leaf_xy(g, u, t):
    """Point in the flat leaf plane (x across, y along), mm."""
    w = leaf_w(g, t, 1 if u >= 0 else -1)
    return leaf_xc(g, t) + u * w, t * g['L']


def on_body(g, x, y):
    """Leaf-plane point -> (phi deg, z mm) on the envelope, after the leaf's tilt."""
    c, s = math.cos(math.radians(g['tilt'])), math.sin(math.radians(g['tilt']))
    a, b = x * c + y * s, -x * s + y * c
    z = g['z'] + b
    return g['phi'] + math.degrees(a / R(z)), z


# ---------------------------------------------------------------- layout
def layout(seed):
    rng = np.random.default_rng(seed)
    leaves, n, z = [], 0, None
    while True:
        u = lambda a, b: float(rng.uniform(a, b))
        asp = u(*ASPECT)
        sh = u(0.38, 0.54)
        # the leaf length follows the local radius, so the spiral keeps its look up the body,
        # and the leaves finishing the crown grow longer
        zc = 0.0 if z is None else z
        crown = smoothstep(ZT - 70, ZT - 20, zc)
        L = L_REF * (R(zc + 30) / RB) * (1 + CROWN * crown) * u(0.92, 1.08)
        if z is None:
            z = START * L
        L = min(L, TOP - z)          # the crown stops at TOP
        # The shoulder must sit on the body: above the rim a leaf is a free blade, and edges below
        # its shoulder would hang. Crown leaves pull their shoulder down and grow a longer point.
        sh = min(sh, (ZT - 4 - z) / L)
        if sh * L < 14 or sh < 0.22:
            break
        g = dict(
            phi=(n * GOLDEN + u(-4, 4)) % 360,
            z=z + u(-0.8, 0.8),
            L=L, W=L * asp,
            tilt=u(4, 12),           # every leaf leans the same way round: the spiral swirls
            sh=sh,
            basep=u(0.55, 0.95),     # base: <1 rounded
            tipp=u(0.85, 1.45),      # tip: 1 ogive, >1 drawn-out point
            asym=u(-0.12, 0.12),
            sway=u(-0.16, 0.16),
            H=(L / L_REF) * u(6.5, 10.5),
            p=u(1.6, 3.0),           # cross-section: low = pointed dome, high = flat pillow
            ridge=u(0.0, 1.0),
            edge=u(1.2, 2.4),
            lean=u(0.0, 2.5) + 4.0 * crown,
            tipf=u(0.15, 0.35),
        )
        leaves.append(g)
        z += SPACING * R(z + 0.4 * L)
        n += 1
    return leaves


def table_text(leaves, seed):
    lines = [f'// BEGIN LEAVES  (written by Spiral_Bract_Planter_leaves.py layout --seed {seed} --write;'
             f' {len(leaves)} leaves)',
             '// ' + ', '.join(GENES),
             'leaves = [']
    for i, g in enumerate(leaves):
        vals = ', '.join(f'{g[k]:.3f}'.rstrip('0').rstrip('.') for k in GENES)
        lines.append(f'    [{vals}],' if i < len(leaves) - 1 else f'    [{vals}]')
    lines += ['];', '// END LEAVES']
    return '\n'.join(lines)


def write_table(leaves, seed):
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


def leaf_raster(g, px=0.25):
    """Flat leaf (untilted) as a height map: returns image array and extent."""
    xs = [leaf_xy(g, u, t)[0] for t in np.linspace(0, 1, 60) for u in (-1, 1)]
    x0, x1 = min(xs) - 2, max(xs) + 2
    W, H = int((x1 - x0) / px) + 1, int((g['L'] + 4) / px) + 1
    hmap = np.zeros((H, W)); mask = np.zeros((H, W), bool)
    for r in range(H):
        y = g['L'] + 2 - r * px
        t = y / g['L']
        if not 0 <= t <= 1:
            continue
        xc = leaf_xc(g, t)
        wl, wr = leaf_w(g, t, -1), leaf_w(g, t, 1)
        for c in range(W):
            x = x0 + c * px
            d = x - xc
            if -wl <= d <= wr and (wl > 0 or wr > 0):
                uu = d / wr if d >= 0 else d / wl
                hmap[r, c] = leaf_h(g, uu, t); mask[r, c] = True
    return hmap, mask


def sheet(leaves, out, cols=10):
    px = 0.35
    tiles = []
    for i, g in enumerate(leaves):
        h, m = leaf_raster(g, px)
        tiles.append(Image.fromarray(shade(h, m, px)))
    cw = max(t.width for t in tiles) + 20
    ch = max(t.height for t in tiles) + 34
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new('RGB', (cw * cols, ch * rows), 'white')
    d = ImageDraw.Draw(img)
    for i, t in enumerate(tiles):
        cx, cy = (i % cols) * cw, (i // cols) * ch
        img.paste(t, (cx + (cw - t.width) // 2, cy + 4 + (ch - 34 - t.height)))
        g = leaves[i]
        d.text((cx + 6, cy + ch - 26), f"#{i}  z{g['z']:.0f}  {g['L']:.0f}x{2 * g['W']:.0f}", fill='black')
    img.save(out)
    print(f'sheet: {len(leaves)} leaves -> {out}')


def body_map(leaves, out, px=0.5):
    """The planter unrolled at the belly radius: arc length x height, front-most leaf wins."""
    circ = 2 * math.pi * RB
    Wd, Hd = int(circ / px), int((ZT + 50) / px)
    zbuf = np.full((Hd, Wd), -1e9); ids = np.full((Hd, Wd), -1)
    for i, g in enumerate(leaves):
        for t in np.linspace(0, 1, int(g['L'] / px * 1.5)):
            for u in np.linspace(-1, 1, int(2 * g['W'] / px * 1.5)):
                x, y = leaf_xy(g, u, t)
                phi, z = on_body(g, x, y)
                if z < 0:
                    continue
                c = int((phi % 360) / 360 * Wd) % Wd
                r = Hd - 1 - int(z / px)
                if r < 0:
                    continue
                h = leaf_h(g, u, t) + R(z) - RB      # outward distance at this height
                if h > zbuf[r, c]:
                    zbuf[r, c] = h; ids[r, c] = i
    mask = ids >= 0
    img = shade(np.where(mask, zbuf, zbuf[mask].min() if mask.any() else 0), mask, px)
    # dark seams where the front leaf changes
    seam = np.zeros_like(mask)
    seam[1:, :] |= ids[1:, :] != ids[:-1, :]; seam[:, 1:] |= ids[:, 1:] != ids[:, :-1]
    img[seam & mask] = (img[seam & mask] * 0.45).astype(np.uint8)
    rim = Hd - 1 - int(ZT / px)
    img[rim, :] = [200, 60, 60]
    Image.fromarray(img).save(out)
    print(f'map: {len(leaves)} leaves, {100 * mask[rim:, :].mean():.1f} % of the body covered -> {out}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['layout', 'sheet', 'map', 'leaf'])
    ap.add_argument('index', nargs='?', type=int)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--write', action='store_true', help='layout: write the table into the .scad')
    ap.add_argument('--out', help='PNG path for sheet / map')
    a = ap.parse_args()
    leaves = layout(a.seed)
    if a.cmd == 'layout':
        if a.write:
            write_table(leaves, a.seed)
        else:
            print(table_text(leaves, a.seed))
    elif a.cmd == 'sheet':
        sheet(leaves, a.out or os.path.join(HERE, 'Spiral_Bract_Planter_leaf_sheet.png'))
    elif a.cmd == 'map':
        body_map(leaves, a.out or os.path.join(HERE, 'Spiral_Bract_Planter_map.png'))
    elif a.cmd == 'leaf':
        g = leaves[a.index]
        for k in GENES:
            print(f'{k:6s} {g[k]:9.3f}')


if __name__ == '__main__':
    main()
