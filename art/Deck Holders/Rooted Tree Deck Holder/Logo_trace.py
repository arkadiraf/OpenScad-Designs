#!/usr/bin/env python3
"""Build Logo.svg, the plaque logo of the Rooted Tree Deck Holder, from the supplied artwork.

The logo is three discs (the white parts of the artwork); they print in black on the white wall.
- Discs 2 and 3 are traced from the full logo (Logo_source.png, white on dark), and clipped to
  ideal circles so their rims come out round.
- Disc 1 is an ideal circle with the emblem cut out of it. The emblem comes from the separate,
  sharper emblem artwork (Emblem_source.png, black on white), scaled into the place it has in the
  full logo, and thickened so its strokes survive a 0.4 mm nozzle at plaque size.

usage:  python Logo_trace.py Logo_source.png Emblem_source.png Logo.svg [--plaque-w 37]
Needs Pillow, numpy and the potrace command.
"""
import argparse, os, subprocess, tempfile
import numpy as np
from PIL import Image, ImageFilter

# Measured on Logo_source.png (pixels): disc centres, radius, and the emblem's box in disc 1.
CY, R = 252, 169
CX = [189, 549, 911]
EMB = (119, 167, 259, 339)            # x0, y0, x1, y1
K = 4                                   # upsampling for a smooth trace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('logo'); ap.add_argument('emblem'); ap.add_argument('out')
    ap.add_argument('--plaque-w', type=float, default=37, help='printed logo width, mm')
    ap.add_argument('--grow', type=float, default=0.1, help='emblem stroke growth per side, mm')
    a = ap.parse_args()

    x0, x1 = CX[0] - R - 4, CX[2] + R + 4
    y0, y1 = CY - R - 4, CY + R + 4
    W, H = (x1 - x0) * K, (y1 - y0) * K
    mm_per_px = a.plaque_w / ((x1 - x0) * K)

    src = Image.open(a.logo).convert('L')
    big = np.array(src.crop((x0, y0, x1, y1)).resize((W, H), Image.LANCZOS)) > 128
    yy, xx = np.mgrid[0:H, 0:W]

    def disc(i):
        return (xx - (CX[i] - x0) * K) ** 2 + (yy - (CY - y0) * K) ** 2 < (R * K) ** 2

    ink = np.zeros((H, W), bool)
    for i in (1, 2):
        ink |= big & disc(i)

    # disc 1: circle minus the emblem
    em = Image.open(a.emblem).convert('L')
    e = np.array(em) < 128
    ys, xs = np.nonzero(e)
    em = em.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    ew, eh = (EMB[2] - EMB[0]) * K, (EMB[3] - EMB[1]) * K
    em = em.resize((ew, eh), Image.LANCZOS).point(lambda v: 255 if v < 128 else 0)   # emblem = 255
    grow = max(1, round(a.grow / mm_per_px))
    em = em.filter(ImageFilter.MaxFilter(2 * grow + 1))
    cut = np.zeros((H, W), bool)
    ox, oy = (EMB[0] - x0) * K, (EMB[1] - y0) * K
    cut[oy:oy + eh, ox:ox + ew] = np.array(em) > 128
    ink |= disc(0) & ~cut

    with tempfile.TemporaryDirectory() as d:
        pbm = os.path.join(d, 'logo.pbm')
        Image.fromarray(np.where(ink, 0, 255).astype(np.uint8)).convert('1').save(pbm)
        subprocess.run(['potrace', '-s', '--flat', '-t', '8', '-a', '1.0', '-O', '0.4', '-o', a.out, pbm],
                       check=True)
    print(f'wrote {a.out}: {W} x {H} px, {mm_per_px * 1000:.1f} um/px at {a.plaque_w} mm, '
          f'emblem grown {grow} px ({grow * mm_per_px:.2f} mm) per side')


if __name__ == '__main__':
    main()
