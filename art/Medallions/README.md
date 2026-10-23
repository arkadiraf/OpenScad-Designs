# Medallions

Flat colour drawings turned into double-sided, multi-colour medallions for the Bambu Lab H2C
(Bambu PLA Basic, 35 % infill). One script, [image_to_3mf.py](image_to_3mf.py), does everything,
from the drawing to a sliced, checked Bambu Studio project.

## Layer stack

| z (mm)    | what                                                        |
|-----------|-------------------------------------------------------------|
| 2.4 – 3.0 | top face: the picture in colour (3 layers)                  |
| 0.6 – 2.4 | core: one solid colour under the whole silhouette           |
| 0.0 – 0.6 | bottom face: the picture in colour, so the back shows it mirrored |

The core is the first colour in the palette, usually the outline colour (black), so the rim reads
as one continuous outline. Colour strips thinner than 0.2 mm and specks smaller than
0.35 × 0.35 mm can't print as their own lines, so they merge into the core colour or the
colour next to them.

## Designs

| Folder | Size (mm) | Colours | Print time on the H2C |
|---|---|---|---|
| [Haunted House Medallion](Haunted%20House%20Medallion) | 75.0 × 67.2 | Black, Orange, Jade White, Purple, Bambu Green, Yellow | 1 h 10 m |
| [Vini Gift Alien Medallion](Vini%20Gift%20Alien%20Medallion) | 66.0 × 85.0 | Blue (core), Cobalt Blue, Sunflower Yellow, Orange, Purple, Bright Green, Jade White | 1 h 11 m |
| [Taco Fiesta Medallion](Taco%20Fiesta%20Medallion) | 58.0 × 75.0 | Black, Cobalt Blue, Sunflower Yellow, Red, Gold, Mistletoe Green, Beige, Jade White | 1 h 9 m |
| [Santa UFO Medallion](Santa%20UFO%20Medallion) | 58.2 × 75.0 | Black, Blue, Sunflower Yellow, Mistletoe Green, Red, Jade White | 53 m |
| [Christmas Spider Medallion](Christmas%20Spider%20Medallion) | 65.4 × 75.0 | Black, Gold, Bronze, Mistletoe Green, Red, Yellow, Jade White | 1 h 7 m |
| [Christmas Captain Bear Medallion](Christmas%20Captain%20Bear%20Medallion) | 66.2 × 75.0 | Black, Cobalt Blue, Red, Beige, Sunflower Yellow, Mistletoe Green, Jade White | 59 m |

Each one is 3.0 mm thick, weighs 8–13 g including purge, and has a hang hole of about 3 mm.

The Vini medallion is 85 mm tall instead of 75 mm so that its Hebrew lettering stays printable.
The back of every medallion is a mirror image, so on Vini the lettering reads backwards from
behind.

Each folder holds:

- `<Name>_source.jpg` / `.png`: the original drawing
- `medallion.json`: the build settings (below)
- `<Name>.png`: a top view of the colour map in the filament colours, so you can check it before
  printing
- `<Name>.3mf`: the Bambu Studio project, ready to slice and committed with the design

## Making a new medallion

1. **Add the drawing.** Create a folder named after the design, e.g. `Snowman Medallion/`, and put
   the drawing in it as `Snowman_Medallion_source.jpg`. The script accepts either:
   - a PNG with transparency, or
   - a JPG or PNG on a white or paper background. Near-white pixels connected to the image border
     count as background.

2. **Find the drawing's colours.** List the main colours, for example by sampling them in an image
   editor or by running k-means over the pixels (OpenCV `cv2.kmeans` with about 12 clusters, after
   dropping the near-white background). Pair each colour with the closest Bambu PLA Basic filament
   from the list in `tools/bambu_3mf.py`.

3. **Write `medallion.json`.** For example:

   ```json
   {
     "source": "Snowman_Medallion_source.jpg",
     "size": 75,
     "palette": [
       ["Black",       [5, 5, 5],       "#000000"],
       ["Black",       [40, 10, 2],     "#000000"],
       ["Cobalt Blue", [40, 87, 161],   "#0056B8"],
       ["Jade White",  [245, 245, 245], "#FFFFFF"]
     ],
     "holes": [[688, 719]]
   }
   ```

   | key | meaning |
   |---|---|
   | `source` | the drawing file in the folder |
   | `size` | longest side of the medallion, in mm |
   | `palette` | each entry is `[part name, [r, g, b] as it appears in the drawing, PLA Basic hex]`. **The first entry is the core colour.** Entries that share a part name print in the same filament; use this to map dark-brown or navy outline pixels to Black, for example. |
   | `holes` | `[x, y]` pixel coordinates in the source image, one inside the hang hole and one inside any other enclosed opening. Without a seed, the white inside the ring stays solid. |
   | `thickness` | total thickness, default 3.0 |
   | `core` | core thickness, default 1.8 (gives 0.6 mm faces). Set it to 0 to run every colour through the full thickness. |
   | `top` | puts colour on the top face only, this many mm thick; the rest is core colour. This needs less purging. |
   | `min_feature` | side of the smallest colour patch that is kept, default 0.35 mm |
   | `cut_white`, `keep_white` | cut the white backdrop out as open fretwork; `keep_white` lists `[x, y]` seeds for white parts to keep |

4. **Build and slice.** Run this from `art/Medallions`:

   ```bash
   python image_to_3mf.py "Snowman Medallion" --slice
   ```

   The script then:
   - traces each colour at 40 px/mm and extrudes the layer stack
   - writes one part per filament into a single object, then converts it to a Bambu Studio
     project (`tools/bambu_3mf.py`: H2C, PLA Basic, 35 % infill, purge matrix)
   - with `--slice`, slices it with the installed Bambu Studio and reports the print time, the
     filament per colour and any slicer warning. It exits with code 1 on a warning.

   It also prints the size, any enclosed openings (to check the hang hole) and the area of each
   colour.

5. **Check the result.** Look at `<Name>.png` for stray colour specks or wrongly mapped
   colours. If something is off, move a palette RGB closer to the colour that was missed, add an
   alias entry, or raise `min_feature`, then rebuild.

To rebuild every medallion:

```bash
python image_to_3mf.py --all --slice
```

`--printer` chooses another Bambu printer; see `python ../../tools/bambu_3mf.py --list-printers`.

The script needs `opencv-python`, `numpy`, `pillow`, `scipy`, `shapely` and `manifold3d`.
