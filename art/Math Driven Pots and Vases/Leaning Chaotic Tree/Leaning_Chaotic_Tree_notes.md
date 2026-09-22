# Leaning Chaotic Tree: requirements and what we learned

**Status: TO BE CONTINUED (paused 2026-09-22). Not buildable yet.** The geometry and the growth
model are in place; the branch layout is a hand-made placeholder, and the path checks fail (see
*Where it stands*).

- `Leaning_Chaotic_Tree.png` is a render of the `.scad` as it stands now, open problems included:
  the branches that loop out sideways, and the twig by the trunk.
- There is deliberately no `.3mf`. The only one was built from an abandoned early draft, failed the
  slicer, and went to the Recycle Bin; the first build that passes will make the next.

## Requirements

What the user asked for, in the order it came, with how each was read.

| Requirement | As built |
|---|---|
| A holder for a single flower in a science glass tube, 16 mm across and 100 mm long | `tube_d` 16, `tube_h` 100. Taken as round-bottomed (a test tube): `tube_foot` 8, a full hemisphere. That is the safe assumption. A flat-bottomed tube sits higher, with more clearance; if a round one were modelled as flat, it would clash. |
| A tree that engulfs it, in the same design language: 3 → 7 → 13, smooth joints, all the lessons so far | Started from the Wild Chaotic Tree: the same seamless joins, blunt tips, bark and arches |
| Held at an angle of 10–25°, the lower the better | `tilt` 25. The composition below forces it up (see *The tilt is not free*) |
| The branches sweep round it and need not cover all of it | The cage is open; the tube is meant to show |
| The tube is inserted along its own axis | The obstacle is open along the axis past the mouth, so nothing can stand in that line |
| The tube rests against the roots at its base | `lift` 2.5, and `tilt_az` 11, which brings the tube's end down onto root 5 (at 191°) rather than into the gap between two roots |
| Tight clearance: 0.5 mm on the diameter, so a 16.5 mm bore | `clearance` 0.25, radial. The other designs use 1 mm radial |
| Size: first 125 mm tall with roots 75 mm across, then "limit branches to 100 mm" | `total_h` 100, `root_spread` 75. The tips finish level with the tube's mouth (93 mm) |
| Branch thickness | First read as "no branch over 2.5 mm", which gave 1 mm twigs. **Corrected:** the trunk and limbs are thick and only the tips come down to 2.5 mm. So `branch_r` 3 (limbs about 8 mm), `trunk_waist` 9, and a tip floor of 2.5 mm (`tip_min` 7.5 × sc) |
| The roots start thicker | `root_r0` 3.2, `root_r1` 0.9 |
| **Composition:** the tube is offset to one side of the tree at the base and to the other side at the top, its middle roughly over the tree's centre; it leans across the tree, two limbs at its sides while it leans on the third | The tube's axis is a straight line that crosses the tree's axis at the tube's midpoint (`z_cross`). Its end is 21 mm off centre, its mouth 21 mm the other way |
| **Growth:** the branches grow up and bend much less; they grow straight where the tube is not in the way, and the tube bends them slightly, as a disturbance | `wander` 0.25, `sprawl` 0.35, and small turn rates in the layout search. See the open question below |
| Mimic the Wild Chaotic Tree's growth, which looked natural | The branch placement is the Wild tree's again (placed against the vessel). A free-crown model was tried and dropped (below) |
| Sketch without the bark first, until the geometry is right | `sketch = true` (below) |
| House rules | H2C, Bambu PLA Basic Cocoa Brown, 35 % infill. The user commits |

## Where it stands

`part="none"` on the current file gives:

- The tube leans 25° towards 11°. Its end is at [−20.7, −4.0, 2.5] and its mouth at 93.1 mm.
- The fork is at 19 mm, so there is a real trunk under the branches.
- Every tip radius is at the 1.3 mm floor.
- **Climb ≥ 5°**: needs ≥ 30° for the overhang budget.
- **53 meeting points**, with arches up to 21.6 mm (6 over 8 mm): the placeholder layout, with `cage_z0` at 35.
- **`member_clearance.py`: FAIL**, 148 % (a twig at 13 mm, inside limb b0; see open item 3).

Not yet built or sliced in this shape.

## Decisions, and why

**The tilted frame.** A branch still runs by world height z, so every rule about turning, climbing
and meeting is unchanged. What changes is where "the middle" is at that height, `axis_xy(z)`. A
horizontal offset from a leaning line also clears it by less than its length, so a wanted gap is
divided by `tilt_k(a)`. The tube as an obstacle (`press_tube`) uses the same formulas as the
upright designs' glass. The only difference is that they are measured in the tube's own frame:
*q* across its axis, *u* along it from its round end.

**The tilt is not free.** With the middle over the tree's centre, the tube's end sits
`(tube_h/2)·sin(tilt)` off centre, and the trunk has to fit in that gap. The clearance is
`|axis_off(z)|` minus the tube's radius at that height:

| Tilt | End off centre | Room for the trunk at 12 / 15 / 20 mm up |
|---|---|---|
| 15° | 12.9 mm | trunk and tube overlap |
| 18° | 15.5 mm | 4.3 / 3.3 / 1.7 mm |
| 20° | 17.1 mm | 5.6 / 4.5 / 2.7 mm |
| 22° | 18.7 mm | 6.8 / 5.6 / 3.6 mm |

So "lower is better" pulls against "thicker trunk". Either the lean goes up, or the trunk tapers
out early (`fade_rate` 0.35 makes it gone by about 25 mm). The tube can't be moved further out
without giving up having its middle over the centre.

**A limb starts in the trunk and eases out in x and y.** It heads for its place against the tube,
`m_rho`/`m_phi` exactly as in the Wild tree. The easing from the trunk to there is done in world
x/y (`m_xy`), because an angle round the tube's axis is singular where that axis passes through
the trunk. A fork leaves its parent wherever the parent actually is.

**Heights that used to hang off `lift` stand alone now.** On the earlier trees `lift` was also the
top of the trunk. Here it is only where the tube rests, so these are absolute:

- `waist_z` 4 and `branch_z0` 1.5;
- the limb partings and the heights where each limb reaches the tube (`limb_rise`: 6/9/13 → 45/52/58 mm);
- where arches may start: `cage_z0` replaces `lift + 24·sc`.

## What we learned

| Symptom | Cause | Fix / lesson |
|---|---|---|
| The fork collapsed to 0.5 mm | Limbs start `7·sc` off the axis. That was 40 % of a limb radius on the earlier trees, and more than a whole radius here | `branch_rho0` must stay well under a limb radius |
| Every branch sat at the tip floor, 1 mm twigs | A 2.5 mm cap on the limbs, then three levels of Da Vinci forking | The brief was misread: 2.5 mm is the tips, not the cap. Check the rim radii in the echo early |
| Climb 16° | The Wild tree's tip lean (22 mm) and the unscaled `+10` / `70` in `lean`, `tip_room` and `flick`, in a much shorter tree | Every length in those formulas × sc |
| Material 0.69 mm inside the tube | `outward()` measured from the tree's axis. Above about 42 mm the tube's axis is further out than the inner branches, so "outward" pointed into it and twigs and knots aimed at the tube | Measure outward from the tube's axis; press twigs too (`tube=true`) |
| Slicer "floating regions" while `floating_check.py` passed at its defaults | Fixed-size twig stubs (0.7 mm) on branches of 0.48 mm: the stub's base ring stood proud of its branch all round, a collar hanging in the air | Twig radius = 0.62 × its branch, skipped below `twig_min`. **`floating_check.py --reach 0.5` is too generous for members about 1 mm thick**; `--reach 0.35` / `0.2` found both collars |
| Still "floating regions" after that | Bisected: not twigs, side roots or knots. It persisted with only the three limbs, trunk and roots | **Open.** In the limb/trunk region, of a geometry that has since changed; re-check on the next build. Build `part="wood"` variants with features switched off and slice each (`bambu_3mf.py --slice`) |
| One limb thrown 13 mm sideways at the ground | The three limbs start together inside the trunk, and the arch system took them for branches overlapping; its guard was `lift + 24·sc`, the trunk top on the earlier trees | `cage_z0`: no arches below it |
| A limb whipping round, climb 8° | Its start was an angle round the tube's axis, which swings through a half turn where that axis crosses the trunk | Blend the start in x and y (`m_xy`) |
| Branches shot off to infinity, and looked wrong anyway | The free-crown model: branches aimed at a crown radius and dodged round the tube along the surface normal, divided by its horizontal length, which can cancel to almost nothing | Dropped. **The vessel-relative placement is what makes these trees grow naturally**: keep it and fix the start instead. If a dodge is ever needed, solve the horizontal move exactly (a quadratic, always well conditioned) |
| A render that never finished | After a revert, `start_xy` was undefined. OpenSCAD only *warns* ("Ignoring unknown function") and carries `undef` into every coordinate; the loft then grinds instead of failing | Run `part="none"` and read the warnings before any render |
| NaN coordinates | Tip lean divides by the room above the vessel's mouth, which is negative once the tips end below it | `room_up()` guard |
| Paths running downward | `total_h` was lowered under a layout searched for 125 mm, so some forks started above their own end | Check `lift + fork height < total_h − tip_spare − drop` whenever heights change |
| Very few meetings | The layout search with small turn rates (for straight growth) gave 1–4 meetings | Straightness costs the merges that tie the cage together for printing. **Open question** |

## Open items, in order

1. **Straight growth vs merges.** Ask the user which to favour, then re-run
   `Leaning_Chaotic_Tree_layout.py` with turn rates part of the way back up. Aim for 8–16 meetings,
   climb ≥ 30°, and every fork starting below its end. Adopt a searched layout, and record its seed
   and count in the script (guide §3.1).
2. **`cage_z0`** is 35 in the file. The meetings and arches only make sense above where the limbs
   have reached the tube (45–58 mm); 60 was intended.
3. **Twig and knot heights** still start at `lift + 32·sc` / `lift + 25·sc` (`twig_zs`, `knot_zs`).
   That puts a twig at 13 mm inside the trunk and fails `member_clearance.py` at 148 %. Start them
   above `crotch_z` for limbs.
4. Rescan `wander_seed` for the new layout.
5. Build, then check: mesh checks, `floating_check.py` at `--reach 0.35`, and the slice. Resolve the
   floating region. Only then turn off `sketch` and look at the bark. That first passing build is
   also what writes this folder's `.3mf` and replaces the `.png`.

## How to work on it

```bash
# fast look: the same shapes without bark or knots
python tools/render_png.py "art/Math Driven Pots and Vases/Leaning Chaotic Tree/Leaning_Chaotic_Tree.scad" sketch.png --view persp --size 900 -D sketch=true
```

```bash
# centrelines for the path checks (seconds, no geometry)
openscad.com -o paths.echo -D 'part="paths"' "art/Math Driven Pots and Vases/Leaning Chaotic Tree/Leaning_Chaotic_Tree.scad"
```

```bash
python tools/member_clearance.py paths.echo --floor 3
```

```bash
python tools/cap_height.py paths.echo --limit 100
```

```bash
# the build; mesh_check measures the bore along the leaning axis (take --foot-xy from the echo)
python tools/build_design.py "art/Math Driven Pots and Vases/Leaning Chaotic Tree/Leaning_Chaotic_Tree.scad" --name "Leaning Chaotic Tree" --out "art/Math Driven Pots and Vases/Leaning Chaotic Tree" --part wood=#6F5034 --check-args "--bore-r 8.25 --floor-h 2.5 --foot-r 8.25 --tilt 25 --tilt-az 11 --foot-xy -20.74,-4.03"
```

Sketch mode on this design: a preview in 15.7 s against 28.9 s, and 84 k triangles against 245 k.
Most of what is left is evaluating the paths, which sketch mode does not skip.
