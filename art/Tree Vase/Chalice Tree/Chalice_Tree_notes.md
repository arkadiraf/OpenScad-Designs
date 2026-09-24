# Chalice Tree: requirements, decisions and checks

A small vase glass cupped 85 mm up in a 3 → 7 → 13 tree, sized for a Flashforge Adventurer 5 Pro
(220 × 220 × 220 mm) and exported as STL. The three limbs rise out of a buttressed trunk in one
smooth cup and meet the glass on its curved foot, so the glass sits down into the branches instead
of standing on limbs bent flat under it.

Files:

| File | What it is |
|---|---|
| `Chalice_Tree.scad` | the design. `sketch = true` by default (no bark, for fast iterations) |
| `Chalice_Tree_layout.py` | the 3 → 7 → 13 layout search; `python Chalice_Tree_layout.py 58 4000` reproduces the tables |
| `Chalice_Tree_seat_check.py` | glass fit and seat check against the real curved-foot profile (mesh_check.py assumes a straight glass) |
| `Chalice_Tree.stl` | the print (bark on), binary STL, for the Flashforge |
| `Chalice_Tree.3mf` | the same mesh as a Bambu Studio project (H2C, Cocoa Brown PLA Basic, 35 % infill) |
| `Chalice_Tree.png` | isometric render of the `.scad` with bark (a render, not a photo) |

## Requirements, and how each was read

| Requirement | As built |
|---|---|
| Glass 8 cm across, 13 cm tall | `glass_d` 80, `glass_h` 130 |
| "A slight curved base of small radius 5 cm starting curve at 17.5 cm from base" | **Read as: the side curves in over the bottom 17.5 mm along a 50 mm radius** (17.5 cm cannot be right on a 13 cm glass). `glass_foot_z` 17.5, `glass_foot_R` 50: the side is straight down to 17.5 mm, then follows a 50 mm arc tangent to it, which brings the bottom in to 73.7 mm across; its edge is rounded 2 mm (`glass_foot`). If the real glass differs, change those three in the Customizer: everything else is derived |
| 0 clearance, tight fit | `clearance` 0. The wood is pressed flat onto the glass itself; nothing reaches inside it |
| No 90° bend of the tree; the glass sits on the branch profile | The limbs no longer pass flat under the glass bottom and turn up round its corner (the Wild / Grand trees). They rise in a cup, turning at most ~45° from upright, and settle onto the **curved foot**; the glass sits into them. Each limb is pressed along the whole curve (0.5–17.5 mm above the glass bottom), with a small pad under the bottom edge |
| Glass leaning on the branches at about 8.5 cm | `lift` 85: the glass bottom 85 mm above the bed; rim at 215 mm |
| Height 215 mm total | `total_h` 215: the tallest end cap is at 213.1 mm; the tips finish level with the rim |
| Roots spreading 200 mm | `root_spread` 200: the print measures 172 × 196 mm |
| Printer: Flashforge Adventurer 5 Pro, 220 × 220 × 220, STL | asserts in the `.scad` stop a height over 220 or roots wider than 210. STL instead of the Bambu 3MF project |
| Iterate without texture | `sketch = true` (guide §3 step 4): same paths, no bark or knots |
| Same 3 → 7 → 13 branching | a fresh layout search for this glass and height (below) |
| A new, unique design | new layout seed, new wander seed, and the cup-shaped rise onto the curved foot |

## Decisions

- **Based on the Wild Chaotic Tree's code** (same 80 × 130 glass family): its seamless trunk /
  buttress / root skin, blunt tips, arches and bark carry over unchanged.
- **The glass as an obstacle with a curved foot.** `env_sdf` is the real profile in (r, z): the
  straight side, the 50 mm foot arc, the bottom plane, the edge rounded. The distance to leave it
  along the push direction (`env_exit`) is found by bisection, because the arc makes the closed
  form of the earlier trees wrong; the glass is convex, so the ray leaves it once.
- **The hug line follows the foot.** A branch pressed against the glass has its centreline at
  `hug_prof(z) + 0.8 r`, and `hug_prof` follows the curved foot too. Below the glass bottom it
  carries on along the **tangent** of the arc. Clamping the curve there left a kink at z = 85, and
  then at the clamp point. That kink bent the limbs to 0.3× their radius, which folds a tube.
- **Limbs blend into that line** (`lerp(rho0, m_rho_g(z), ease)`) instead of easing to a fixed
  radius and then switching. The limb therefore arrives already following the curve, with no
  knee. The tightest limb bend is now 1.33× its radius (limb 2, where it settles onto the glass).
- **Tips end at the rim, so there is no "lean out above the rim".** The table's lean column is now
  how far each tip opens out from the glass over its last `tip_open` (40) mm, and the sideways
  flick uses the same span. The old formulas divided by the room above the rim, which is negative
  here.
- **Fewer meetings than the tall trees.** The branches have ~126 mm above the glass bottom, against
  ~180 on the Wild tree, so the search aims for 6–14 meetings instead of 8–16.

## Layout and wander

- `Chalice_Tree_layout.py 58 4000`: best of 8 seeds × 4000 trees. Largest empty sector 93°, seat
  130°. It was chosen over seed 11 (lower search score) because in the `.scad` seed 11 needs a 28 mm
  arch and seed 41 a 60 mm one, while seed 58's arches stay ≤ 16 mm with climb ≥ 39°.
- `wander_seed` 8, the best of 32 scanned: 7 meetings, arches ≤ 9.6 mm, climb ≥ 40°, tightest bend
  1.33× the tube radius. Seeds 7, 13, 21 and 24 each throw a 49–85 mm arch.

## Measured (sketch STL, OpenSCAD 2021.01 / CGAL, 3 min 46 s)

| Check | Result |
|---|---|
| Size | 172.1 × 196.3 × 213.1 mm, on z = 0; fits the 220 mm cube |
| Topology | 118 342 triangles, **0 / 0** edges, **1 shell** |
| Past 60° | **0.00 %** above the bottom 1 cm; past 45° 0.16 % (report only) |
| Glass | closest material **−0.000 mm** (the tight fit touches, nothing inside); **seat 10.4 cm²** of pads on the curved foot, 2.4 cm² of it under the bottom edge; largest gap between pads 99° |
| Branches | merges 10–26 % (limit 30 %); top of every end cap ≤ 213.1 mm (limit 215) |
| Mid-air | `floating_check.py --reach 0.35`: **0** regions |
| Bed contact | 75.2 cm² |
| Volume | 330.5 cm³ (410 g if solid) |

The textured STL figures are in the section below once it has been built.

## Measured (textured, OpenSCAD 2026.09.18 nightly / Manifold, 38 s)

`sketch=false`, `part="wood"`; the STL and the 3MF were exported from the same file (2026-09-24).

| Check | Result |
|---|---|
| Size | 172.1 × 196.3 × 213.1 mm, on z = 0; fits the 220 mm cube |
| Topology | 380 014 triangles, **0 / 0** edges, **1 shell** (4 near-duplicate vertices: checker note only) |
| Past 60° | **0.00 %** above the bottom 1 cm (0.08 % overall); past 45° 0.80 % |
| Glass | closest material **+0.000 mm** at z 87.5 (touches, nothing inside); **seat 9.7 cm²** of pads, 2.38 cm² under the bottom edge; largest gap 98° |
| Mid-air | `floating_check.py --reach 0.35`: **0** regions |
| Bed contact | 72.1 cm² |
| Volume | 318.6 cm³ (395 g if solid) |
| Bambu Studio slice (H2C, 0.20mm Standard, 35 % infill) | **no warnings** (no floating regions); **7 h 05 min**, **197 g** |

## Known and open

- **Sketch shows a ring where the trunk hands over to the limbs** (about 30 mm up). It comes from
  the sketch faceting (18-sided limbs against the finely sampled trunk skin); with bark on, the
  join is seamless. Ignore it while sketching.
- The fit is **zero clearance** as asked. The print will not be exact, and a glass that is a
  little large will sit higher on the limbs rather than jam. If it sits too high, set `clearance`
  to 0.2–0.3 and re-export.
- Sliced clean in Bambu Studio (H2C). Not yet sliced in Orca-Flashforge for the Adventurer 5 Pro: check the print time there.

## How to work on it (Windows, OpenSCAD nightly)

```powershell
# fast look, the same shapes without bark (sketch is the default in the file)
python tools/render_png.py "art/Tree Vase/Chalice Tree/Chalice_Tree.scad" sketch.png --view persp --size 900
# centrelines for the path checks (seconds)
& "C:\Program Files\OpenSCAD (Nightly)\openscad.com" -o paths.echo -D 'part=\"paths\"' "art/Tree Vase/Chalice Tree/Chalice_Tree.scad"
python tools/member_clearance.py paths.echo --floor 50 --limit 0.30
python tools/cap_height.py paths.echo --limit 215
# the print: bark on, one body, STL
& "C:\Program Files\OpenSCAD (Nightly)\openscad.com" --backend Manifold --export-format binstl -o Chalice_Tree.stl -D 'part=\"wood\"' -D sketch=false "art/Tree Vase/Chalice Tree/Chalice_Tree.scad"
python tools/mesh_check.py Chalice_Tree.stl
python "art/Tree Vase/Chalice Tree/Chalice_Tree_seat_check.py" Chalice_Tree.stl
python tools/floating_check.py Chalice_Tree.stl --reach 0.35
```

`--floor 50` on `member_clearance.py` skips everything below 55 mm: the three limbs start together
inside the trunk, and limbs 1 and 2 go on as one stem until limb 2 parts at 31 mm, so they are
still separating at 45 mm. That is a fork, meant to overlap, but the tool only exempts a
parent and its own child, so it would report the limbs as a 61–100 % overlap.
