# To do

## Grand Chaotic Tree: seams where the trunk meets the limbs and roots

Folder: `art/Math Driven Pots and Vases/Grand Chaotic Tree/`. The design passes its build, but the
seams between the parts it is built from show.

**What shows.** The Bambu Studio slice preview shows a patch of top-surface fill (diagonal lines)
on the side of the trunk at the fork. Around it the surface prints as wall lines. So the surface
there faces up and is nearly level: a shelf. In the gallery render there is also a band of bark
cross-cracks where the limbs leave the trunk.

**Where it is.** Measured on the packaged 3MF (2026-09-19): 13.2 cm² of up-facing faces flatter
than 37° from level, 12–98 mm up and within 70 mm of the axis. It sits almost all round the trunk,
20–35 mm up and 20–35 mm from the axis. The largest patches:

| Height | Angle | Area | Distance from the axis |
|---|---|---|---|
| 30–35 mm | 60–80° | 80 mm² | 20–30 mm |
| 30–35 mm | 180–200° | 66 mm² | 21–31 mm |
| 25–30 mm | 280–300° | 64 mm² | 25–35 mm |
| 30–35 mm | 320–340° | 64 mm² | 21–30 mm |
| 20–25 mm | 0–20° | 53 mm² | 14–35 mm |

The 0–20° patch is where root 0 starts inside the trunk. So is the model's one real sealed pocket
(60 mm³ at 21 mm from the axis, 24 mm up).

**Why.** The trunk hands over to the limbs between about 25 and 44 mm (`branch_z0` to
`crotch_z`). Over that span the trunk core fades out (`core_r`, 29 → 41.5 mm), and the valleys
between the three limb lobes deepen faster than the height rises, which leaves near-level shelves
between the limb tubes. The trunk loft, the limb tubes and the root tubes are separate solids with
their own bark, so where one surfaces from another there is a crease and a change of texture.

**Solved in the Wild Chaotic Tree (built and sliced 2026-09-20); port it back.** `Wild Chaotic Tree/Wild_Chaotic_Tree.scad`
removes these seams with defined handover contours:
- **One skin.** The trunk skin includes a copy of each root's base (`root_band`), sitting just
  inside the root. A 10 mm smooth maximum turns it into a fillet between root, buttress and trunk.
- **Roots.** Each root stays straight out to its foot contour and comes out of the fillet at a
  shallow angle.
- **Limbs.** The limbs start deep inside the trunk. Along a wandering contour (`hand_z`) the skin
  goes from 0.3 mm outside them to 1.3 mm inside over 7 mm.
- **Shared bark.** Near the joins the tubes wear the same bark pattern as the skin (`wbark`, fixed
  in space around the trunk axis).
- **Result.** Exposed trunk narrows by at most 1.44 mm per mm in the handover (was 3.4).

The steps below were the plan for the Grand Chaotic Tree.

**Fix plan.**
1. Limit how fast the trunk narrows. Its radius should shrink by no more than about 1 mm per mm of
   height (a surface no flatter than 45°) anywhere in the handover. Either fade the core over a
   longer span that starts lower, or build the valley radius from a slope-limited function of height
   rather than `smax(core, lobes)` with a fading core.
2. Start the roots lower and further inside the trunk foot. This removes the shelf and the sealed
   pocket at 0–20°. The whole root start, cap included, should sit inside the trunk below the
   buttress crest.
3. Blend the textures. Fade the limbs' bark cross-cracks in over their first centimetres out of the
   trunk, so the band where they leave it disappears.
4. Check before rebuilding. Measure up-facing faces flatter than 37° in the handover region (the
   figure above) and aim for well under 1 cm². Component-render the trunk and the limbs together and
   list the shells (only the body and near-zero merge pockets). Then rebuild with `build_design.py`
   (`--check-args "--bore-r 49 --floor-h 100 --foot-r 3"`) and look at the slice preview around the
   fork.
5. Worth adding to `tools/mesh_check.py`: report "shelves", meaning up-facing faces flatter than a
   given angle above the bottom 1 cm, so this is caught at build time.
