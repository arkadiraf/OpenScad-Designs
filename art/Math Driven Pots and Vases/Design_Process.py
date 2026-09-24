"""Compose Design_Process.png: the Design_Evolution.png row of renders (see Design_Evolution.py),
retitled, with photos of the printed Wild and Grand Chaotic Trees underneath. Before that, as there: the six holders for the 80 x 130 mm glass, in order, at true
relative scale, with what each one introduced and what changed between them. The Grand Chaotic
Tree is left out: it holds a bigger glass.

    python "Design_Process.py"

It reads each design's own gallery PNG from the folder beside it, so **re-run it whenever one of
those six is rebuilt** - otherwise the picture shows a design that no longer exists. The bbox in
the table below sets each tile's true scale; take it from the design's build output and keep it in
step, or that design will be drawn the wrong size next to the others."""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = ROOT + '/Design_Process.png'
BG = (248, 248, 248)
INK, SOFT, ACCENT = (40, 40, 40), (105, 105, 105), (111, 80, 52)          # accent: Cocoa Brown
F = 'C:/Windows/Fonts/'
font = lambda name, size: ImageFont.truetype(F + name, size)
TITLE, NAME, BODY, SMALL, STEP = font('segoeuib.ttf', 42), font('segoeuib.ttf', 25), font('segoeui.ttf', 18), \
    font('segoeui.ttf', 17), font('seguisb.ttf', 17)

# name, folder/file, bbox (x, y, z mm), what it introduced, colours, print on the H2C
D = [
    ('Braided Tree', 'Braided Tree Vase Holder/Braided_Tree_Vase_Holder', (153.5, 150.6, 177.6),
     'Ten stems woven over and under around the glass; 75 folded leaves.', '2 colours', '7 h 56 min · 188 g'),
    ('Embracing Tree', 'Embracing Tree/Embracing_Tree', (153.8, 150.6, 179.4),
     'One tree behind the glass; two limbs wrap around it; bright shoots among mature leaves.', '3 colours', '6 h 08 min · 91 g'),
    ('Cradle Tree', 'Cradle Tree/Cradle_Tree', (156.4, 136.5, 249.2),
     'Glass lifted 6 cm into the branches; spiral grain; procedural bark, knots and stubs.', '1 colour', '7 h 52 min · 227 g'),
    ('Tangled Cradle Tree', 'Tangled Cradle Tree/Tangled_Cradle_Tree', (156.4, 136.8, 248.8),
     'Sub-branches wind back and arch over the main branches; nothing crosses.', '1 colour', '8 h 32 min · 236 g'),
    ('Chaotic Cradle Tree', 'Chaotic Cradle Tree/Chaotic_Cradle_Tree', (156.4, 142.6, 249.1),
     'Every branch its own way, some reversing; where they meet they grow together.', '1 colour', '8 h 21 min · 232 g'),
    ('Wild Chaotic Tree', 'Wild Chaotic Tree/Wild_Chaotic_Tree', (179.2, 197.2, 266.1),
     'No floor: the glass stands on three limbs of a buttressed tree, and the joins do not show.',
     '1 colour', '9 h 32 min · 249 g'),
]
# the prints, photographed; each crop is a fraction box around the tree
P = [
    ('Wild Chaotic Tree/Wild_Chaotic_Tree_Print.jpg', 'Wild Chaotic Tree, printed',
     '80 × 130 mm glass · 179 × 197 × 266 mm · 9 h 32 min · 249 g', (0.17, 0.24, 0.83, 0.90)),
    ('Grand Chaotic Tree/Grand_Chaotic_Tree_Print.jpg', 'Grand Chaotic Tree, printed',
     '100 × 200 mm glass · 271 × 271 × 319 mm · 15 h 42 min · 481 g', (0.17, 0.24, 0.83, 0.90)),
]
PH = 820                                                            # photo height, px
photos = []
for f, *_, (a, b, c, e2) in P:
    im = ImageOps.exif_transpose(Image.open(f'{ROOT}/{f}')).convert('RGB')
    im = im.crop((round(a * im.width), round(b * im.height), round(c * im.width), round(e2 * im.height)))
    photos.append(im.resize((round(im.width * PH / im.height), PH), Image.LANCZOS))
# True relative scale: the renders are orthographic isometric (35.26 deg elevation), trimmed with
# a 60 px margin. Screen height of a model ~ z cos(e) + footprint sin(e) (footprint ~ round).
e = math.radians(35.26)
imgs, scales = [], []
for name, path, (x, y, z), *_ in D:
    im = Image.open(f'{ROOT}/{path}.png').convert('RGB')
    h_mm = z * math.cos(e) + max(x, y) * math.sin(e)
    imgs.append(im); scales.append((im.height - 120) / h_mm)       # px per mm in that render
PX_MM = 2.6                                                         # common scale
tiles = [im.resize((round(im.width * PX_MM / s), round(im.height * PX_MM / s)), Image.LANCZOS)
         for im, s in zip(imgs, scales)]

# COL is the width the captions wrap to; the trees are drawn wider than that, so the spacing has
# to come from the tiles. Take the pitch from the widest pair of neighbours and the margin from
# the outermost tile, leaving CLEAR px of daylight everywhere.
COL, CLEAR = 300, 26
GAP = max(0, max((tiles[i].width + tiles[i + 1].width) // 2 + CLEAR - COL for i in range(len(tiles) - 1)))
M = max(55, CLEAR + max(tiles[0].width, tiles[-1].width) // 2 - COL // 2)
W = 2 * M + len(D) * COL + (len(D) - 1) * GAP
img_h = max(t.height for t in tiles)
TOP = 150
PTOP = TOP + img_h + 215 + 70                                     # top of the photo band
H = PTOP + 70 + PH + 110
canvas = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(canvas)


def centred(text, cx, y, f, fill):
    d.text((cx - d.textlength(text, font=f) / 2, y), text, font=f, fill=fill)


def wrap(text, f, width):
    lines, cur = [], ''
    for word in text.split():
        t = (cur + ' ' + word).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur); cur = word
    return lines + [cur]


d.text((M, 40), 'OpenSCAD Design Process with Claude Opus', font=TITLE, fill=INK)
d.text((M, 96), 'Tree Vases: six tree vase holders for the same 80 × 130 mm glass, rendered from '
                'the OpenSCAD sources at one scale; below, the last of them and its bigger sibling, printed.', font=SMALL, fill=SOFT)
base = TOP + img_h                                                  # common ground line
for i, (t, (name, _, _, idea, colours, prt)) in enumerate(zip(tiles, D)):
    cx = M + i * (COL + GAP) + COL // 2
    canvas.paste(t, (cx - t.width // 2, base - t.height))
    y = base + 18
    centred(f'{i + 1}. {name}', cx, y, NAME, INK)
    y += 38
    for line in wrap(idea, BODY, COL - 10):
        centred(line, cx, y, BODY, INK); y += 24
    y += 6
    centred(f'{colours} · {prt}', cx, y, SMALL, ACCENT)
# arrows between the designs, on a clear patch: the trees are wider than their columns
for i in range(len(D) - 1):
    x0 = M + (i + 1) * COL + i * GAP + 8
    x1 = x0 + GAP - 16
    ya = base - 60
    d.rectangle([x0 - 6, ya - 14, x1 + 6, ya + 14], fill=BG)
    d.line([(x0, ya), (x1 - 11, ya)], fill=ACCENT, width=4)
    d.polygon([(x1, ya), (x1 - 16, ya - 9), (x1 - 16, ya + 9)], fill=ACCENT)
# nothing may run off the canvas or into the tree next to it
prev_right = None
for i, t in enumerate(tiles):
    cx = M + i * (COL + GAP) + COL // 2
    left = cx - t.width // 2
    right = left + t.width
    assert 0 <= left and right <= W, f'{D[i][0]} runs off the canvas: {left}..{right} of {W}'
    assert prev_right is None or left >= prev_right, f'{D[i][0]} overlaps {D[i - 1][0]}'
    prev_right = right

# the prints: a rule, a heading, then the photos side by side, centred
d.line([(M, PTOP), (W - M, PTOP)], fill=(215, 215, 215), width=2)
d.text((M, PTOP + 18), 'From render to print', font=NAME, fill=INK)
d.text((M + d.textlength('From render to print', font=NAME) + 18, PTOP + 25),
       'Photos of the printed holders, glass in place. Both single colour, printed on the Bambu Lab H2C.',
       font=SMALL, fill=SOFT)
PGAP = 140
x = (W - sum(p.width for p in photos) - PGAP * (len(photos) - 1)) // 2
py = PTOP + 70
for p, (_, cap, detail, _) in zip(photos, P):
    d.rectangle([x - 2, py - 2, x + p.width + 1, py + PH + 1], fill=(215, 215, 215))
    canvas.paste(p, (x, py))
    cx = x + p.width // 2
    centred(cap, cx, py + PH + 16, NAME, INK)
    centred(detail, cx, py + PH + 54, SMALL, ACCENT)
    x += p.width + PGAP

canvas.save(OUT, optimize=True)
print('wrote', OUT, canvas.size, f'(columns {COL} + {GAP} gap, {M} margin)')
print('render scales px/mm', [round(s, 2) for s in scales], 'tiles', [t.width for t in tiles])
