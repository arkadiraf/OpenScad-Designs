# Wild Chalice Tree: requirements, decisions and checks

The Chalice Tree's seat with the Wild Chaotic Tree's crown and roots. The glass (80 × 130 mm, its
base curving in to a 50 mm bottom) is cupped 85 mm up in a 3 → 7 → 13 tree whose branches climb
past the rim and lean out 54 mm above it. Built for the Bambu Lab H2C (3MF project).

| File | What it is |
|---|---|
| `Wild_Chalice_Tree.scad` | the design. `sketch = true` by default (no bark, for fast iterations) |
| `Wild_Chalice_Tree_layout.py` | the 3 → 7 → 13 layout search; `python Wild_Chalice_Tree_layout.py 139 5000` reproduces the tables |
| `Wild_Chalice_Tree_seat_check.py` | glass fit and seat against the real curved base (`mesh_check.py` assumes a straight glass) |
| `Wild_Chalice_Tree.3mf` / `.png` | H2C project (Cocoa Brown PLA Basic, 35 % infill) and isometric render (a render, not a photo) |

## Requirements, and how each was read

| Requirement | As built |
|---|---|
| Chalice Tree extended to the size of the Wild Chaotic Tree's branches, reaching beyond the rim | `total_h` 269: rim at 215, tips up to 54 mm above it (the Wild tree's room); radius profile, lean out (18–25 mm) and flick are the Wild tree's |
| Keep the Chalice Tree's design clearance | `clearance` 0: the wood is pressed onto the glass itself, nothing inside it |
| Remove the band that supports the glass | no limb passes under the glass bottom (the Wild tree's limbs pass flat under it and wrap its foot). The glass rests on the limbs by its curved base only: 9.7 cm² of pads on the curve, 0.04 cm² under the bottom edge |
| Extend the roots as in the Wild Chaotic Tree | `root_spread` 208, the Wild tree's; the other root parameters were already identical |
| The real glass has a stronger curve at its base | curve starts 20 mm above the bottom and ends at a 50 mm bottom: `glass_foot_z` 20, `glass_base_d` 50; the arc radius (20.8 mm) is derived |
| Iterate with the nightly build | OpenSCAD 2026.09.23 nightly, Manifold backend |

## Decisions

- **The hug line is a true offset curve.** A pressed member's axis keeps `(1 − press)·r` off the
  glass, so on the foot it follows an arc of radius `R + d` about the same centre. The Chalice code
  shifted the foot arc sideways instead, which bends the centreline as tightly as the glass: harmless
  on the old 50 mm arc, 1.1× the limb radius on this 20.8 mm one. The offset arc gives ≥ 1.47×.
- **The cup stops at 45° (`cup_max`).** On a near-bowl base the arc runs almost flat at the bottom,
  and its tangent there dived the limbs into the axis (101 % overlaps). The hug line follows the
  arc only while it is within 45° of upright, then carries on down along that tangent, eased
  against the limbs' start radius (`hug_k`). That is also why nothing passes under the glass.
- **`limb_rise`** re-tuned for the deeper seat: the limbs part lower (12, 18, 23 mm) and settle onto
  the curve 11, 14 and 17 mm above the glass bottom.
- **Layout:** a fresh search with the Wild tree's crown ranges and the Chalice's seat rules (16 seeds;
  seed 139: largest empty sector 96°, seat 132°). `wander_seed` 4, the best of 24 on this layout:
  8 meetings, arches ≤ 14 mm, merges ≤ 12 %, climb ≥ 33°, tightest bend 1.48× the radius.

## Measured (textured, nightly / Manifold, 2026-10-05)

| Check | Result |
|---|---|
| Size | 179.2 × 197.2 × 266.9 mm, on z = 0 (limit 269) |
| Topology | 455 878 triangles, **0 / 0** edges, **1 shell** |
| Past 60° | **0.03 %** above the bottom 1 cm; bottom 1 cm 0.06 %; past 45° 2.12 % |
| Glass | closest material +0.001 mm (touches, nothing inside); seat 9.7 cm² on the curved base, largest gap between pads 92° |
| Mid-air | `floating_check.py --reach 0.35`: **0** regions |
| Bed contact | 75.0 cm² |
| Bambu Studio slice (H2C, 0.20mm Standard, 35 % infill) | **no warnings**; 9 h 16 min; **244 g** |
| Render | 50 s as one body |

## How to work on it

```bash
python tools/render_png.py "art/Tree Vase/Wild Chalice Tree/Wild_Chalice_Tree.scad" sketch.png --view persp --size 900
"C:/Program Files/OpenSCAD (Nightly)/openscad.com" -o paths.echo -D 'part="paths"' "art/Tree Vase/Wild Chalice Tree/Wild_Chalice_Tree.scad"
python tools/member_clearance.py paths.echo --floor 65 --limit 0.30
python tools/cap_height.py paths.echo --limit 269
python tools/build_design.py "art/Tree Vase/Wild Chalice Tree/Wild_Chalice_Tree.scad" --name "Wild Chalice Tree" --out "art/Tree Vase/Wild Chalice Tree" --part wood=#6F5034 --define sketch=false
python "art/Tree Vase/Wild Chalice Tree/Wild_Chalice_Tree_seat_check.py" "art/Tree Vase/Wild Chalice Tree/Wild_Chalice_Tree.3mf"
```

`--floor 65` on `member_clearance.py`: the limbs part as late as 23 mm and the crotch is at 53 mm, so
below ~65 mm they are still forks of each other, which the tool would report as overlaps.
Changing the glass in the Customizer needs a re-check of the bends and the wander seed.
