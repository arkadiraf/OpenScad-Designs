# Rooted Tree Deck Holder

An upright holder for a deck of playing cards, **70 × 25 × 100 mm** (W × D × H), slotted at the back
so you can push the deck up with a finger and draw it, and closed by a **sliding lid** that snaps
shut. It is a plain card box
with square corners and a light 1.5 mm fillet. Laid out after the reference print:
- A tree stands to one side of the front. Its three-strand braided trunk leans out and its crown
  spreads over the whole upper face.
- The roots grow out of the trunk strands and run to both sides. They cross over the plaque, frame
  it, and wrap over both corners onto the sides.
- The plaque carries the faculty's three-disc logo, with no words.

| Front | Isometric |
|---|---|
| <img src="Rooted_Tree_Deck_Holder_Front.png" width="300"> | <img src="Rooted_Tree_Deck_Holder.png" width="260"> |

The images are renders, not photos.

## Sizes

| | mm |
|---|---|
| Outer box | 70 × 25 × 100, corners filleted 1.5 (the relief adds up to 2.8 at the front and 1.5 on the sides) |
| Cavity | 65.2 × 20.2 × 98, for 63.5 × 88.9 mm poker cards and a deck up to 19 mm thick (about 60 cards) |
| Deck top below the rim | 9.1 |
| Back slot | 34 wide, from 28 mm above the bed to the top |
| Walls / floor | 2.4 / 2 |
| Lid | 67.8 × 23.4 × 2, its top 1.6 below the rim |
| Logo | 37 × 12, inlaid 0.6 and standing 0.4 proud |

## Printing

- Stands on its floor, no supports. Bambu Lab H2C project, 0.20 mm Standard, 35 % infill.
- Three parts, each on its own filament: **Box** Jade White `#FFFFFF`, **Relief** Brown `#9D432C`,
  **Logo** Black `#000000`. Brown is the nearest PLA Basic colour to copper; for the look in the
  reference photo, swap filament 2 to a silk copper in Bambu Studio.
- Every tree member is sunk into the wall by a share of its radius that depends on its direction,
  so no underside is steeper than 58° from vertical. Mesh check: 0 open / non-manifold edges on
  all parts, the relief is one shell, 0.46 % of the surface past 60° above the first centimetre
  (house limit 0.5 %).
- About 52 g at 100 % solid (roughly 16 g at typical infill). Not yet sliced with Bambu Studio:
  the build ran where Bambu Studio is not installed, so check the slice preview before printing.
- The emblem in the first disc is small (about 6 mm tall). `Logo_trace.py` thickens its strokes
  by 0.1 mm a side so they hold at a 0.4 mm nozzle; expect the finest slits to close up.

## The sliding lid

| The lid, as printed | |
|---|---|
| <img src="Rooted_Tree_Deck_Holder_Lid.png" width="300"> | The lid slides in from the back. It runs in a groove round the inside of the side and front walls, 1.2 mm below the rim, and enters through the back wall, which is cut away above the groove floor. The groove ceiling slopes at 45°, so the box still prints without supports, and the lid's top edges are bevelled to match. |

- **Lock.** Near the back of each side, a slot frees an 11 mm spring arm along the lid's edge. A
  small rounded bump on the arm's free end stands 0.5 mm proud of the edge. When the lid is shut
  it snaps into a matching dimple in the groove. Pull the lid back by its grip grooves to release it.
- **Fit, checked on the real geometry.** Shut, the lid and box do not touch (0 mm³). 3 mm open,
  only the two bumps press 0.5 mm into the walls, and the arms flex inward into their slots.
  Fully open, the lid runs free.
- **Printing.** The lid is a separate package, `Rooted_Tree_Deck_Holder_Lid.3mf` (Jade White,
  about 4 g solid, 1 g at typical infill). It prints flat, top up. The 0.2 mm clearance suits a
  0.4 mm nozzle; if your lid is tight, raise `lid_clear` to 0.25–0.3 and rebuild both packages.
- `lid = false` removes the grooves and the lid, for the open-top box.

## How the joints work

<img src="Rooted_Tree_Deck_Holder_Trunk.png" width="300" alt="Close-up of the braided trunk, where the strands run on into the limbs">

- **Strands into limbs.** Each trunk strand and the first limb it feeds are one tube: no joint at all.
- **Forks.** A child starts just inside its parent, 4 % wider than the parent's end and at the same
  depth, then narrows to its own radius over 1.6 radii. The parent runs on a little past the fork,
  tapering inside its children, so no end cap shows.
- **Roots.** The roots start inside their strand, keep just behind its braided depth while they
  are inside it, and swell out of it. The strand and core ends dive into the wall.
- **Bark.** Every ring is laid out from the wall's outward normal, and the bark twist is a function
  of the position on the wall. A parent and a child therefore have the same ring vertices and the
  same ridges where they overlap, with no sawtooth seam. The bark fades out on tips that sink into
  the wall.

## How the corners work

The paths are written on a guide surface with 8 mm corners (`path_r`), so their coordinates keep
their meaning whatever the real fillet is. Round a corner each tube rides a radius of its own: the
largest of its rings' sink depth plus 1.15 × radius. Then no tube bends tighter than itself, and it
stays proud of the squarer real corner. The root tables were laid out for a 50 mm deep box; on a
shallower one their run along a side eases in (m·tanh(t/m), 1:1 at the corner), so the roots fan
out over the side there is instead of running off its back edge. Rings are added where a member crosses a corner, and the
sink is smoothed along each member, so no chord or sink jump cuts a tube under the edge or kinks it.

## Customizer

| Variable | What it does |
|---|---|
| `card_w`, `card_h`, `deck_t`, `side_clear` | The deck; the box is sized from these (the defaults give 70 × 25) |
| `box_h`, `wall`, `floor_t`, `corner_r` | Box height, walls, the fillet on the vertical edges |
| `slot_w`, `slot_bottom` | The back slot |
| `trunk_side` | -1 tree on the left and plaque on the right (default), 1 mirrored |
| `seed` | Grows a different crown and different rootlets |
| `crown_depth`, `limb_len`, `limb_r`, `root_r`, `spread` | Tree size and density |
| `plaque_content` | `logo` (the default, no words), `text`, or `logo_and_text` |
| `logo_file`, `logo_w` | The logo (`Logo.svg`) and its width |
| `line_en1` … `line_he2`, `text_size`, `plaque_layout` | Optional plaque text (English and Hebrew), stacked or side by side |
| `lid`, `lid_t`, `lid_groove_d`, `lid_lip`, `lid_clear` | The sliding lid and its groove |
| `detent_h`, `detent_arm` | The lock: bump height and spring arm length |
| `part` | `assembly` to look at; `box`, `relief`, `logo` are the three colour parts; `lid` the lid as printed |
| `view`, `lid_open` | What the assembly shows (`lid`: the lid alone) and how far the lid is drawn open |

Any change needs the parts exported again:

```bash
python tools/build_design.py "art/Deck Holders/Rooted Tree Deck Holder/Rooted_Tree_Deck_Holder.scad" \
    --name "Rooted Tree Deck Holder" --out "art/Deck Holders/Rooted Tree Deck Holder" \
    --part box=#FFFFFF --part relief=#9D432C --part logo=#000000
python tools/build_design.py "art/Deck Holders/Rooted Tree Deck Holder/Rooted_Tree_Deck_Holder.scad" \
    --name "Rooted Tree Deck Holder Lid" --out "art/Deck Holders/Rooted Tree Deck Holder" \
    --define 'view="lid"' --part lid=#FFFFFF
```

## The logo

`Logo.svg` is built from the supplied artwork by `Logo_trace.py` (needs potrace):

```bash
python Logo_trace.py Logo_source.png Emblem_source.png Logo.svg --plaque-w 37
```

- Discs 2 and 3 are traced from `Logo_source.png` (the full logo, white on dark) and clipped to
  ideal circles.
- Disc 1 is an ideal circle with the emblem cut out. The emblem comes from the sharper
  `Emblem_source.png` and is thickened for print.
- If you change `logo_w`, re-run the script with the same `--plaque-w`.
