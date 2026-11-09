# Swirl Spinning Top

A small spinning top, 50 mm tall and 42 mm across. Its body is two spiral ribbons. Each one winds out
from the hub, getting squarer as it goes, and runs into half of a rounded-square frame. The ribbons'
lower edges taper down to the point in a cone. A slender stem rises from the hub for twirling.

![Swirl Spinning Top](Swirl_Spinning_Top.png)

*(A render, not a photo.)*

## Printing: three parts, no supports

`Swirl_Spinning_Top.3mf` is a Bambu Studio project (H2C, 0.20 mm Standard, 35 % infill) with all
three parts on plate 1, in Bambu PLA Basic **Pumpkin Orange**:

| Part | How it prints |
|---|---|
| Body | upside down on its flat top (frame, ribbon tops and hub). Every ribbon is a vertical wall growing from the bed, so nothing overhangs |
| Stem | standing on its flared base |
| Pin | 4 x 12 mm, standing |

Push the pin into the hub, then push the stem onto it. The holes have 0.12 mm clearance, which makes
a press fit. Use `fit = 0.2` and a drop of glue if your printer runs tight.

Mesh checks: every part closed, one shell each. Nothing on the body or the stem is past 60°. The only
overhang is the pin's 0.5 mm end chamfer and the small bridged hole ceilings. About 9 g at 100 % solid.
It has not been sliced with Bambu Studio yet: that check was skipped in the build environment.

## Customizer

- `total_h`, `frame_w`, `body_h`: overall size
- `turns`, `wind_bias`, `squareness`, `arms`, `handed`: the swirl
- `ribbon_t`, `frame_t`, `frame_h`: wall sizes. Keep them at 2.4 mm or more
- `fit`: how tight the pin is

Change any of them, then rebuild with:

```bash
python tools/build_design.py "art/Toys/Swirl Spinning Top/Swirl_Spinning_Top.scad" --name "Swirl Spinning Top" \
    --out "art/Toys/Swirl Spinning Top" --part body=#FF9016 --part stem=#FF9016 --part pin=#FF9016
```
