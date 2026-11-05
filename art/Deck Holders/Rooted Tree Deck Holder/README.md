# Rooted Tree Deck Holder

An upright holder for a deck of playing cards, **70 × 50 × 100 mm** (W × D × H), open at the top and
slotted at the back so you can push the deck up with a finger and draw it. Laid out after the
reference print: a tree stands to one side of the front, its three-strand braided trunk leaning
out and its crown spreading over the whole upper face. Its roots run across over a name plaque on
the other side, frame it, and wrap round both corners onto the sides.

| Front | Isometric |
|---|---|
| <img src="Rooted_Tree_Deck_Holder_Front.png" width="300"> | <img src="Rooted_Tree_Deck_Holder.png" width="260"> |

The images are renders, not photos.

## Sizes

| | mm |
|---|---|
| Outer box | 70 × 50 × 100 (the relief adds up to 2.7 mm at the front and 1.6 mm on the sides) |
| Cavity | 66 × 46 × 98, for 63.5 × 88.9 mm poker cards and a deck up to 44 mm thick |
| Deck top below the rim | 9.1 |
| Back slot | 34 wide, from 28 mm above the bed to the top |
| Walls / floor | 2 / 2 |

## Printing

- Stands on its floor, no supports. Bambu Lab H2C project, 0.20 mm Standard, 35 % infill.
- Three parts, each on its own filament: **Box** Jade White `#FFFFFF`, **Relief** Brown `#9D432C`,
  **Text** Black `#000000`. Brown is the nearest PLA Basic colour to copper; for the look in the
  reference photo, swap filament 2 to a silk copper in Bambu Studio.
- Every tree member is sunk into the wall by a share of its radius that depends on its direction,
  so no underside is steeper than 58° from vertical. Mesh check: 0 open / non-manifold edges on
  all parts, the relief is one shell, 0.32 % of the surface past 60° above the first centimetre
  (house limit 0.5 %; most of it is the ceiling of the inlaid letters, which the black text fills).
- About 60 g at 100 % solid (roughly 18 g at typical infill). Not yet sliced with Bambu Studio:
  the build ran where Bambu Studio is not installed, so check the slice preview before printing.

## Customizer

| Variable | What it does |
|---|---|
| `card_w`, `card_h`, `deck_t`, `side_clear` | The deck; the box is sized from these (the defaults give 70 × 50) |
| `box_h`, `wall`, `floor_t`, `corner_r` | Box height, walls, corner radius the roots wrap round |
| `slot_w`, `slot_bottom` | The back slot |
| `seed` | Grows a different crown and different rootlets |
| `trunk_side` | -1 tree on the left and plaque on the right (default), 1 mirrored |
| `crown_depth`, `limb_len`, `limb_r`, `root_r`, `spread` | Tree size and density |
| `line_en1`, `line_en2`, `line_he1`, `line_he2`, `text_size` | Plaque text (English and Hebrew) |
| `plaque_layout` | `stacked` (English over Hebrew, the default) or `side_by_side` as on the reference print (set `text_size` to about 2.6 for that) |
| `logo_file`, `logo_w` | An emblem of your own (SVG or DXF), placed above the text |
| `part` | `assembly` to look at; `box`, `relief`, `text` are the three colour parts |

The plaque carries the university name as text. The official emblem is not drawn in the design; if
you have permission to use it, point `logo_file` at its SVG; it goes above the text, as on the
reference print, and the text moves down to make room.
Any change needs the parts exported again:

```bash
python tools/build_design.py "art/Deck Holders/Rooted Tree Deck Holder/Rooted_Tree_Deck_Holder.scad" \
    --name "Rooted Tree Deck Holder" --out "art/Deck Holders/Rooted Tree Deck Holder" \
    --part box=#FFFFFF --part relief=#9D432C --part text=#000000
```
