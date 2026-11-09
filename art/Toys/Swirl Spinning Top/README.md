# Swirl Spinning Top

A small spinning top, 50 mm tall and 36 mm across, printed in one piece. From the side it is a
double trumpet with a thin rounded-square frame round its waist. Four ribbons start at the corners
of the frame and wind in towards the axis. They alternate: two climb and become fins running up the
stem, and two drop and become fins running down the spike to the point.

![Swirl Spinning Top](Swirl_Spinning_Top.png)

*(A render, not a photo.)*

## Printing: one piece, with supports

`Swirl_Spinning_Top.3mf` is a Bambu Studio project: H2C, 0.20 mm Standard, 35 % infill, Bambu PLA
Basic **Pumpkin Orange**. The top stands upright on its point. The point has a 0.4 mm flat
(`tip_flat`) to stand on. Turn on:

- **supports**: tree supports, auto. The frame and the lower edges of the ribbons hang in the air
  (about 9 % of the surface is past 60°).
- **a brim**, so the small flat at the point stays on the bed.

Mesh checks: closed, one shell. About 5 g at 100 % solid. It has not been sliced with Bambu Studio
yet: that check was skipped in the build environment.

## Customizer

- `total_h`, `frame_w`, `frame_z`: overall size and the height of the waist
- `arms`, `turns`, `wind_bias`, `straighten`, `squareness`, `handed`: the swirl in plan
- `fin_top`, `fin_bot`, `soften`, `band_h`, `fin_h`: the side profile, meaning how high the fins run up
  the stem, how low they run down the spike, and how early the trumpets climb
- `core_r`, `core_flare`, `flare_len`: the stem and spike
- `ribbon_t`, `frame_t`, `frame_h`: wall sizes. Keep them at 2.4 mm or more

Change any of them, then rebuild with:

```bash
python tools/build_design.py "art/Toys/Swirl Spinning Top/Swirl_Spinning_Top.scad" --name "Swirl Spinning Top" \
    --out "art/Toys/Swirl Spinning Top" --part top=#FF9016 --check-args "--max-overhang 100"
```
