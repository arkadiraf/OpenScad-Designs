# OpenScad-Designs
AI Driven 3d Designs

Sculptural, math-driven designs for 3D printing, written in OpenSCAD with Claude Code. Each design
is sized from a real object (here, the glass vase it holds). It is checked for printability and
ships ready to print:

- a `.scad` source you can resize in OpenSCAD's Customizer
- a multi-colour `.3mf` that opens in Bambu Studio as a finished project
- an isometric render

## Gallery

### Math Driven Pots and Vases

Tree-shaped holders for a plain glass vase. The glass drops into a straight bore and stands on a
stump floor, and you can see the tree's growth rings through the glass bottom.

<table>
  <tr>
    <td align="center" width="50%">
      <a href="art/Math%20Driven%20Pots%20and%20Vases/Braided%20Tree%20Vase%20Holder/">
        <img src="art/Math%20Driven%20Pots%20and%20Vases/Braided%20Tree%20Vase%20Holder/Braided_Tree_Vase_Holder.png" alt="Braided Tree Vase Holder" width="360">
      </a>
      <br><b>Braided Tree Vase Holder</b>
    </td>
    <td align="center" width="50%">
      <a href="art/Math%20Driven%20Pots%20and%20Vases/Embracing%20Tree/">
        <img src="art/Math%20Driven%20Pots%20and%20Vases/Embracing%20Tree/Embracing_Tree.png" alt="Embracing Tree" width="340">
      </a>
      <br><b>Embracing Tree</b>
    </td>
  </tr>
  <tr>
    <td valign="top">
      A money-tree trunk of ten stems woven over and under around the glass, rising at 46°. Roots
      spread over the bed, and a crown of forked branches carries 75 folded leaves around the rim.
    </td>
    <td valign="top">
      A single tree stands behind the glass. Its trunk hugs the glass and forks into two limbs that
      wrap around it, with a tall central leader. Each twig ends in a bright new shoot flanked by
      two mature leaves.
    </td>
  </tr>
</table>

| | Braided Tree Vase Holder | Embracing Tree |
|---|---|---|
| Glass | 80 × 130 mm (82 mm bore, floor 9 mm) | 80 × 130 mm (82 mm bore, floor 8 mm) |
| Size | 153.5 × 150.6 × 177.6 mm | 153.8 × 150.6 × 179.4 mm |
| Colours (Bambu PLA Basic) | Cocoa Brown `#6F5034`, Mistletoe Green `#3F8E43` | Cocoa Brown `#6F5034`, Mistletoe Green `#3F8E43`, Bright Green `#BECF00` |
| Print on the H2C, 35 % infill | 7 h 56 min, 188 g | 6 h 08 min, 91 g |
| Files | [scad](art/Math%20Driven%20Pots%20and%20Vases/Braided%20Tree%20Vase%20Holder/Braided_Tree_Vase_Holder.scad) · [3mf](art/Math%20Driven%20Pots%20and%20Vases/Braided%20Tree%20Vase%20Holder/Braided_Tree_Vase_Holder.3mf) | [scad](art/Math%20Driven%20Pots%20and%20Vases/Embracing%20Tree/Embracing_Tree.scad) · [3mf](art/Math%20Driven%20Pots%20and%20Vases/Embracing%20Tree/Embracing_Tree.3mf) |

The images are renders, not photos.

## Printing

- Each `.3mf` is a **Bambu Studio project** for the Bambu Lab H2C: 0.4 mm nozzle, 0.20mm Standard
  process, 35 % sparse infill. Every colour part is already assigned its own PLA Basic filament,
  with purge volumes. Open it and slice.
- Print upright without supports. Both holders pass the house rules: no more than 0.5 % of the
  surface past 60° above the first centimetre, and nothing that starts in mid-air.
- For another Bambu printer: `python tools/bambu_3mf.py <file>.3mf --printer X1C`
  (`--list-printers` shows all ten).
- For a different glass, change `glass_d` and `glass_h` in the Customizer, then rebuild (below).
  Every dimension is derived from the glass.

## How the designs are made

[OPENSCAD_DESIGNER_AGENT.md](OPENSCAD_DESIGNER_AGENT.md) is the design guide. It covers the house
print rules, the OpenSCAD techniques, the geometry traps found along the way, and the
reference figures for each design. The scripts in [`tools/`](tools/) do the packaging and checking:

| Script | What it does |
|---|---|
| `build_design.py` | Exports every colour part, merges them, writes the Bambu project, renders the image, and runs the mesh checks and a Bambu Studio slice |
| `mesh_check.py` | Printability checks: watertight parts, overhang, bore clearance, bed contact, volume |
| `bambu_3mf.py` | Turns a 3MF into a Bambu Studio project, or re-targets it to another printer; `--slice` asks Bambu Studio for its verdict |
| `merge_3mf.py`, `render_png.py` | Multi-part 3MF merge; preview renders |

```bash
python tools/build_design.py "art/Math Driven Pots and Vases/Embracing Tree/Embracing_Tree.scad" \
    --name "Embracing Tree" --out "art/Math Driven Pots and Vases/Embracing Tree" \
    --part wood=#6F5034 --part leaves_dark=#3F8E43 --part leaves_light=#BECF00 \
    --check-args "--bore-r 41 --floor-h 8"
```

This needs OpenSCAD 2021.01+ and Python 3 with `numpy` and `Pillow`. Bambu Studio is optional; if
it's installed, the build also slice-checks the result.

## License

[GPL-3.0](LICENSE)
