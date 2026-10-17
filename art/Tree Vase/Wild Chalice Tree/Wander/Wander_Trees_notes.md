# Wild Chalice Wander Trees

Five Wild Chalice Trees in which the roots wander as well as the branches, so each tree is unique
from the ground up. Same glass (80 × 130 mm, base curving in to a 50 mm bottom), same seat (cupped
85 mm up, zero clearance), same 269 mm height limit and print rules as `../Wild_Chalice_Tree.scad`.

| File | What it is |
|---|---|
| `make_wander_trees.py` | writes each tree's `.scad` from the original and `trees.json` |
| `trees.json` | per tree: branch layout (tables + search seed), `wander_seed`, `root_seed`, `root_count` |
| `tree_search.py` | `branches` / `roots` seed searches from the `part="paths"` echo |
| `Wander_Trees_Overview.py` / `.png` | the original plus the five, side by side |
| `Wander_N/` | `.scad`, `.png`, `build.log`, and the Bambu H2C `.3mf` (Cocoa Brown PLA Basic, 35 % infill) once built locally: 3MFs are not committed (`.gitignore`); the rebuild commands are below |

## What wanders

- **Branches:** a fresh 3 → 7 → 13 layout per tree (`../Wild_Chalice_Tree_layout.py SEED 4000`;
  14 new seeds searched, the passing ones used) and a `wander_seed` picked by `tree_search.py branches`.
- **Roots:** `root_seed` re-draws every per-root random (`rr(i,k) = rnd(i + 19·root_seed, k)`): angle
  (±13° jitter, was ±10°), length, one-sided sweep, meander phase, wavelength **and amplitude**
  (0.7–1.3 × `root_meander`, new), side roots and buttress reach; plus the trunk knots and the bark
  pattern. `root_count` varies from 8 to 11. Each tree's root seed came from its own range (101–112,
  201–212, ...) so no two trees share one.

## Trees and checks (nightly OpenSCAD / Manifold, Bambu Studio 02.05.00.66, 2026-10-17)

| Tree | Layout | Wander | Roots (seed, count) | Size (mm) | Worst merge | Climb | Seat (cm², largest gap) | H2C slice |
|---|---|---|---|---|---|---|---|---|
| Wander 1 | 3203 | 9 | 106, 8 | 198.3 × 178.8 × 267.7 | 15 % | 32° | 9.1, 103° | 9 h 12 min, 241 g |
| Wander 2 | 2111 | 14 | 207, 10 | 183.9 × 198.0 × 267.5 | 12 % | 30° | 9.6, 97° | 9 h 27 min, 251 g |
| Wander 3 | 3307 | 12 | 301, 9 | 188.7 × 164.8 × 267.3 | 22 % | 32° | 9.6, 92° | 9 h 17 min, 242 g |
| Wander 4 | 2531 | 4 | 403, 11 | 194.4 × 189.8 × 267.4 | 25 % | 32° | 9.6, 99° | 9 h 29 min, 251 g |
| Wander 5 | 3121 | 8 | 501, 10 | 176.0 × 181.6 × 267.5 | 22 % | 31° | 9.1, 90° | 9 h 27 min, 246 g |

Every tree: `build_design.py` **PASS** (0 boundary / 0 non-manifold edges, past 60° above the
bottom 1 cm ≤ 0.05 %), Bambu Studio slice **with no warnings**, `../Wild_Chalice_Tree_seat_check.py`
**PASS** (nothing inside the glass), tightest branch bend ≥ 1.36× and root bend ≥ 1.77× the radius.

**Shells:** Wander 3 is one shell. The others report 2–3: the extra shells are **internal voids**
(negative volume, 0.001–0.03 mm³, under 1.5 mm across) trapped where two merged branches overlap at
z 180–220 mm. Each tree is one solid body; the slicer fills the voids.

## Rebuild one

```bash
python make_wander_trees.py
python tools/build_design.py "art/Tree Vase/Wild Chalice Tree/Wander/Wander_1/Wild_Chalice_Wander_1.scad" --name "Wild Chalice Wander 1" --out "art/Tree Vase/Wild Chalice Tree/Wander/Wander_1" --part wood=#6F5034 --define sketch=false
python "art/Tree Vase/Wild Chalice Tree/Wild_Chalice_Tree_seat_check.py" "art/Tree Vase/Wild Chalice Tree/Wander/Wander_1/Wild_Chalice_Wander_1.3mf"
python "art/Tree Vase/Wild Chalice Tree/Wander/Wander_Trees_Overview.py"
```
