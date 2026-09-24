# OpenScad-Designs
AI Driven 3d Designs

Sculptural, math-driven designs for 3D printing, written in OpenSCAD with Claude Code. Each design
is sized from a real object (here, the glass vase it holds). It is checked for printability and
ships ready to print:

- a `.scad` source you can resize in OpenSCAD's Customizer
- a multi-colour `.3mf` that opens in Bambu Studio as a finished project
- an isometric render

## Gallery

### Tree Vase

Tree-shaped holders for a plain glass vase. The glass drops straight in from the top. In the first
five it stands on a stump floor, and you can see the tree's growth rings through the glass bottom. In
the Wild and Grand Chaotic Trees and the Chalice Tree there is no floor at all: the wood grows
around the glass and it stands on the branches themselves.

[<img src="art/Tree%20Vase/Design_Evolution.png" alt="How the tree vase holders evolved: six designs at the same scale">](art/Tree%20Vase/Design_Evolution.png)

The six holders for the 80 × 130 mm glass, at the same scale, and what each one added. The Grand
Chaotic Tree is not in it: it holds a bigger glass. The picture is drawn from the designs' own
renders by [Design_Evolution.py](art/Tree%20Vase/Design_Evolution.py), which
is re-run whenever one of the six is rebuilt.

<table>
  <tr>
    <td align="center" width="33%">
      <a href="art/Tree%20Vase/Braided%20Tree%20Vase%20Holder/">
        <img src="art/Tree%20Vase/Braided%20Tree%20Vase%20Holder/Braided_Tree_Vase_Holder.png" alt="Braided Tree Vase Holder" width="260">
      </a>
      <br><b>Braided Tree Vase Holder</b>
    </td>
    <td align="center" width="33%">
      <a href="art/Tree%20Vase/Embracing%20Tree/">
        <img src="art/Tree%20Vase/Embracing%20Tree/Embracing_Tree.png" alt="Embracing Tree" width="245">
      </a>
      <br><b>Embracing Tree</b>
    </td>
    <td align="center" width="33%">
      <a href="art/Tree%20Vase/Cradle%20Tree/">
        <img src="art/Tree%20Vase/Cradle%20Tree/Cradle_Tree.png" alt="Cradle Tree" width="200">
      </a>
      <br><b>Cradle Tree</b>
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
    <td valign="top">
      The glass sits 6 cm up in the branches of a rooted tree. Five branches grow out of the trunk
      and spiral 87° around the glass, then fork above the rim. Every surface is furrowed bark with
      knots and pruned twig stubs.
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="art/Tree%20Vase/Tangled%20Cradle%20Tree/">
        <img src="art/Tree%20Vase/Tangled%20Cradle%20Tree/Tangled_Cradle_Tree.png" alt="Tangled Cradle Tree" width="200">
      </a>
      <br><b>Tangled Cradle Tree</b>
    </td>
    <td align="center" width="33%">
      <a href="art/Tree%20Vase/Chaotic%20Cradle%20Tree/">
        <img src="art/Tree%20Vase/Chaotic%20Cradle%20Tree/Chaotic_Cradle_Tree.png" alt="Chaotic Cradle Tree" width="215">
      </a>
      <br><b>Chaotic Cradle Tree</b>
    </td>
    <td align="center" width="33%">
      <a href="art/Tree%20Vase/Wild%20Chaotic%20Tree/">
        <img src="art/Tree%20Vase/Wild%20Chaotic%20Tree/Wild_Chaotic_Tree.png" alt="Wild Chaotic Tree" width="215">
      </a>
      <br><b>Wild Chaotic Tree</b>
    </td>
  </tr>
  <tr>
    <td valign="top">
      The Cradle Tree with sub-branches. Five main branches wind one way and never cross each other.
      Sub-branches fork off and wind back, and where one meets a main branch it arches out over it
      and grows into it.
    </td>
    <td valign="top">
      Every branch takes its own way: some turn against the grain, three reverse partway up, and
      sub-branches fork off in the other direction. Wherever two branches meet they grow together,
      which ties the whole cage into one strong print.
    </td>
    <td valign="top">
      A 27 cm tree for the 80 × 130 mm glass, with a wild layout of its own: the trunk splits into
      3 limbs, then 7 branches, then 13, and the glass stands on the three limbs with no floor under
      it. The first design where the trunk, its buttresses and the roots are one skin, so the roots
      and limbs grow out of it wearing the same bark and the joins do not show. Its branches now
      end as blunt cut wood, like the Grand tree's.
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="art/Tree%20Vase/Grand%20Chaotic%20Tree/">
        <img src="art/Tree%20Vase/Grand%20Chaotic%20Tree/Grand_Chaotic_Tree.png" alt="Grand Chaotic Tree" width="235">
      </a>
      <br><b>Grand Chaotic Tree</b>
    </td>
    <td align="center" width="33%">
      <a href="art/Tree%20Vase/Chalice%20Tree/">
        <img src="art/Tree%20Vase/Chalice%20Tree/Chalice_Tree.png" alt="Chalice Tree" width="190">
      </a>
      <br><b>Chalice Tree</b>
    </td>
  </tr>
  <tr>
    <td valign="top">
      A bigger glass, 100 × 200 mm, standing 8 cm up in a 32 cm tree whose roots sprawl
      into a 27 cm footprint. The trunk comes down in buttresses and splits into 3 limbs, then 7
      branches, then 13. Nothing is cut for the glass: the wood grows around it, pressed flat where
      it touches, and the glass stands on the three limbs. Joins without seams, like the Wild tree.
      The branches keep their thickness to the end and finish as blunt cut wood rather than
      running out into points.
    </td>
    <td valign="top">
      A 21.5 cm tree for the 80 × 130 mm glass, sized for a 220 mm printer. Instead of bending
      flat under the glass, the three limbs rise out of the trunk in one smooth cup, never more
      than about 45° from upright, and the glass's curved foot settles into them like an egg in a
      cup, 85 mm up. A tight fit with no clearance: the wood is pressed against the glass. The
      limbs fork into 7 branches and then 13, which end level with the rim.
    </td>
  </tr>
</table>

| Design | Glass (mm) | The glass sits at | Size (mm) | Colours (Bambu PLA Basic) | Print on the H2C, 35 % infill | Files |
|---|---|---|---|---|---|---|
| Braided Tree Vase Holder | 80 × 130 | 9 mm, on a floor | 153.5 × 150.6 × 177.6 | Cocoa Brown `#6F5034`, Mistletoe Green `#3F8E43` | 7 h 56 min, 188 g | [scad](art/Tree%20Vase/Braided%20Tree%20Vase%20Holder/Braided_Tree_Vase_Holder.scad) · [3mf](art/Tree%20Vase/Braided%20Tree%20Vase%20Holder/Braided_Tree_Vase_Holder.3mf) |
| Embracing Tree | 80 × 130 | 8 mm, on a floor | 153.8 × 150.6 × 179.4 | Cocoa Brown, Mistletoe Green, Bright Green `#BECF00` | 6 h 08 min, 91 g | [scad](art/Tree%20Vase/Embracing%20Tree/Embracing_Tree.scad) · [3mf](art/Tree%20Vase/Embracing%20Tree/Embracing_Tree.3mf) |
| Cradle Tree | 80 × 130 | 60 mm, on a floor | 156.4 × 136.5 × 249.2 | Cocoa Brown | 7 h 52 min, 227 g | [scad](art/Tree%20Vase/Cradle%20Tree/Cradle_Tree.scad) · [3mf](art/Tree%20Vase/Cradle%20Tree/Cradle_Tree.3mf) |
| Tangled Cradle Tree | 80 × 130 | 60 mm, on a floor | 156.4 × 136.8 × 248.8 | Cocoa Brown | 8 h 32 min, 236 g | [scad](art/Tree%20Vase/Tangled%20Cradle%20Tree/Tangled_Cradle_Tree.scad) · [3mf](art/Tree%20Vase/Tangled%20Cradle%20Tree/Tangled_Cradle_Tree.3mf) |
| Chaotic Cradle Tree | 80 × 130 | 60 mm, on a floor | 156.4 × 142.6 × 249.1 | Cocoa Brown | 8 h 21 min, 232 g | [scad](art/Tree%20Vase/Chaotic%20Cradle%20Tree/Chaotic_Cradle_Tree.scad) · [3mf](art/Tree%20Vase/Chaotic%20Cradle%20Tree/Chaotic_Cradle_Tree.3mf) |
| Wild Chaotic Tree | 80 × 130 | 83 mm, on 3 limbs | 179.2 × 197.2 × 266.1 | Cocoa Brown | 9 h 32 min, 249 g | [scad](art/Tree%20Vase/Wild%20Chaotic%20Tree/Wild_Chaotic_Tree.scad) · [3mf](art/Tree%20Vase/Wild%20Chaotic%20Tree/Wild_Chaotic_Tree.3mf) · [layout](art/Tree%20Vase/Wild%20Chaotic%20Tree/Wild_Chaotic_Tree_layout.py) |
| Grand Chaotic Tree | 100 × 200 | 80 mm, on 3 limbs | 270.9 × 271.2 × 318.5 | Cocoa Brown | 15 h 42 min, 481 g | [scad](art/Tree%20Vase/Grand%20Chaotic%20Tree/Grand_Chaotic_Tree.scad) · [3mf](art/Tree%20Vase/Grand%20Chaotic%20Tree/Grand_Chaotic_Tree.3mf) · [layout](art/Tree%20Vase/Grand%20Chaotic%20Tree/Grand_Chaotic_Tree_layout.py) |
| Chalice Tree | 80 × 130, curved foot | 85 mm, cupped in 3 limbs | 172.1 × 196.3 × 213.1 | Cocoa Brown | 7 h 05 min, 197 g | [scad](art/Tree%20Vase/Chalice%20Tree/Chalice_Tree.scad) · [3mf](art/Tree%20Vase/Chalice%20Tree/Chalice_Tree.3mf) · [layout](art/Tree%20Vase/Chalice%20Tree/Chalice_Tree_layout.py) · [notes](art/Tree%20Vase/Chalice%20Tree/Chalice_Tree_notes.md) |

Every one but the Chalice Tree leaves 1 mm of clearance around its glass, so the glass lifts
straight out of the top; the Chalice Tree is a tight fit by design (set `clearance` to 0.2-0.3 if
your glass sits too high). The images above are renders, not photos. The three trees that hold the
glass in their branches carry a **layout** script as well: the search that drew their 13 branches,
with the seed that reproduces the tables in the `.scad` (another seed grows a different tree).

### Printed

The Wild and Grand Chaotic Trees off the printer, glass in place, in one colour.
[Design_Process.png](art/Tree%20Vase/Design_Process.png) sets them under the renders they came from.

<table>
  <tr>
    <td align="center" width="50%">
      <a href="art/Tree%20Vase/Wild%20Chaotic%20Tree/Wild_Chaotic_Tree_Print.jpg">
        <img src="art/Tree%20Vase/Wild%20Chaotic%20Tree/Wild_Chaotic_Tree_Print.jpg" alt="The printed Wild Chaotic Tree holding its glass" width="330">
      </a>
      <br><b>Wild Chaotic Tree</b>: 80 × 130 mm glass, 26.6 cm tall
    </td>
    <td align="center" width="50%">
      <a href="art/Tree%20Vase/Grand%20Chaotic%20Tree/Grand_Chaotic_Tree_Print.jpg">
        <img src="art/Tree%20Vase/Grand%20Chaotic%20Tree/Grand_Chaotic_Tree_Print.jpg" alt="The printed Grand Chaotic Tree holding its glass" width="330">
      </a>
      <br><b>Grand Chaotic Tree</b>: 100 × 200 mm glass, 31.9 cm tall
    </td>
  </tr>
</table>

## Printing

- Each `.3mf` is a **Bambu Studio project** for the Bambu Lab H2C: 0.4 mm nozzle, 0.20mm Standard
  process, 35 % sparse infill. Every colour part is already assigned its own PLA Basic filament,
  with purge volumes. Open it and slice.
- Print upright without supports. All eight holders pass the house rules: no more than 0.5 % of the
  surface past 60° above the first centimetre, and nothing that starts in mid-air.
- Height: the Wild (266 mm) and Grand (318.5 mm) Chaotic Trees need an H2-series printer (H2C, H2D,
  H2D Pro or H2S). The other six are 250 mm or under and fit every printer in the list. The Chalice
  Tree (213 mm, roots within 200 mm) also fits a 220 mm cube such as the Flashforge Adventurer 5 Pro;
  export an STL for it with `-D sketch=false` (the command is in its notes).
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
| `mesh_check.py` | Printability checks: watertight parts, overhang, bore clearance (or, for a glass standing on branches, clearance to its rounded foot and the pads it stands on), bed contact, volume |
| `member_clearance.py` | How much branches overlap where they meet, from the centrelines in seconds, before any full render |
| `cap_height.py` | How high each branch reaches once its end cap is counted, from the same centrelines, against a height limit |
| `bambu_3mf.py` | Turns a 3MF into a Bambu Studio project, or re-targets it to another printer; `--slice` asks Bambu Studio for its verdict |
| `floating_check.py` | Finds regions that start in mid-air and says where they are (Bambu Studio only warns that they exist) |
| `merge_3mf.py`, `render_png.py` | Multi-part 3MF merge; preview renders |

```bash
python tools/build_design.py "art/Tree Vase/Embracing Tree/Embracing_Tree.scad" \
    --name "Embracing Tree" --out "art/Tree Vase/Embracing Tree" \
    --part wood=#6F5034 --part leaves_dark=#3F8E43 --part leaves_light=#BECF00 \
    --check-args "--bore-r 41 --floor-h 8"
```

For a design with no floor, the checker is given the glass's rounded foot instead of a plain bore,
and it reports the pads the glass stands on:

```bash
python tools/build_design.py "art/Tree Vase/Grand Chaotic Tree/Grand_Chaotic_Tree.scad" \
    --name "Grand Chaotic Tree" --out "art/Tree Vase/Grand Chaotic Tree" \
    --part wood=#6F5034 --check-args "--bore-r 51 --floor-h 80 --foot-r 3"
```

This needs OpenSCAD and Python 3 with `numpy` and `Pillow`. Bambu Studio is optional; if it's
installed, the build also slice-checks the result.

The tools use the newest OpenSCAD they find and ask it for the **Manifold** backend, which renders
these designs in about a minute where the old CGAL kernel took 20-30 of them. 2021.01 still works,
with CGAL, and is just slow. Set `$OPENSCAD` to choose a binary, or `OPENSCAD_BACKEND=none` to
leave the backend to OpenSCAD.

## License

[GPL-3.0](LICENSE)
