"""Compose Variants_Overview.png: the Wild Chalice Tree and its five branch-layout variants side
by side, from each one's own isometric PNG.

    python Variants_Overview.py

Re-run it whenever a variant is re-rendered (make_variants.py --png). All six are the same tree
around the same glass (same height, same roots), so every render is drawn at one common height.
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'Variants_Overview.png')
BG, INK, SOFT, ACCENT = (248, 248, 248), (40, 40, 40), (105, 105, 105), (111, 80, 52)
F = 'C:/Windows/Fonts/'
font = lambda name, size: ImageFont.truetype(F + name, size)
TITLE, NAME, BODY = font('segoeuib.ttf', 40), font('segoeuib.ttf', 25), font('segoeui.ttf', 18)

V = json.load(open(os.path.join(HERE, 'variants.json')))
tiles = [('Original', os.path.join(HERE, '..', 'Wild_Chalice_Tree.png'), 'layout seed 139 · wander 4')]
for n, v in V.items():
    tiles.append((n.replace('_', ' '), os.path.join(HERE, n, f'Wild_Chalice_Tree_{n}.png'),
                  f'layout seed {v["seed"]} · wander {v["wander"]}'))

TILE_H, COLS, CW, PAD = 760, 3, 560, 30
imgs = []
for name, path, sub in tiles:
    im = Image.open(path).convert('RGB')
    im = im.resize((round(im.width * TILE_H / im.height), TILE_H), Image.LANCZOS)
    if im.width > CW:                                   # keep it inside its column
        im = im.resize((CW, round(im.height * CW / im.width)), Image.LANCZOS)
    imgs.append(im)
rows = (len(tiles) + COLS - 1) // COLS
TOP, CAP = 140, 90
W = COLS * CW + (COLS + 1) * PAD
H = TOP + rows * (TILE_H + CAP + PAD)
canvas = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(canvas)
d.text((PAD, 34), 'Wild Chalice Tree: five branch layouts', font=TITLE, fill=INK)
d.text((PAD, 90), 'The same 80 × 130 mm glass, trunk and roots; only the 3 → 7 → 13 branch layout and its '
                  'wander differ. Isometric renders, not photos.', font=BODY, fill=SOFT)
for k, ((name, _, sub), im) in enumerate(zip(tiles, imgs)):
    r, c = divmod(k, COLS)
    x0 = PAD + c * (CW + PAD); y0 = TOP + r * (TILE_H + CAP + PAD)
    canvas.paste(im, (x0 + (CW - im.width) // 2, y0 + TILE_H - im.height))
    cx = x0 + CW / 2
    for text, f, fill, dy in ((name, NAME, INK, 12), (sub, BODY, ACCENT, 48)):
        d.text((cx - d.textlength(text, font=f) / 2, y0 + TILE_H + dy), text, font=f, fill=fill)
canvas.save(OUT, optimize=True)
print('wrote', OUT, canvas.size)
