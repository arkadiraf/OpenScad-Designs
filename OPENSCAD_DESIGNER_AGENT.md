# OpenSCAD Designer Agent

Standalone operating guide for designing **3D-printable objects in OpenSCAD**. It covers sculptural
glass-insert vase holders in particular, from a brief to a verified, packaged design:
`.scad` source + multi-part `.3mf` + isometric `.png`.

The process was built and debugged while designing **Braided Tree Vase Holder** (2026-09-18/19; §12)
refined while finishing **Embracing Tree** (2026-09-19; §13), extended with procedural bark on
**Cradle Tree** (2026-09-19; §14), and with branches that meet and grow together on **Tangled** and
**Chaotic Cradle Tree** (2026-09-19; §15).
The print rules (§4) come from the house guides `POT_DESIGNER_AGENT.md` and `WOVEN_DESIGNER_AGENT.md`,
restated here so this guide can be followed on its own. Those two guides drive the browser apps
(`EquationDrivenPotDesigner.html`, `EquationDrivenWovenPots.html`). This one drives OpenSCAD.

Everything scripted lives in `tools/` next to this file:

| Script | What it does |
|---|---|
| `tools/build_design.py` | One command: copy the `.scad` into the design folder, export every colour part in parallel, merge them into one 3MF, turn it into a Bambu Studio project (H2C by default), render the isometric PNG, run the mesh checks and a Bambu Studio slice |
| `tools/mesh_check.py` | Printability checks on a 3MF/STL: open or non-manifold edges, shells, overhang by height band, bed contact, bore clearance, volume and mass. Reads core-spec 3MFs and Bambu Studio projects. Exit code 0 means pass |
| `tools/merge_3mf.py` | Merges single-mesh OpenSCAD 3MF exports into one object with named, coloured parts |
| `tools/bambu_3mf.py` | Rewrites a 3MF as a Bambu Studio project: printer, plate, one PLA Basic filament per part, purge volumes and infill (§9.1). Converts in place; re-targets its own output to another printer. `--slice` slices it with the installed Bambu Studio and reports its warnings, print time and filament |
| `tools/render_png.py` | Preview render to PNG from a preset view (iso, front, back, top, persp), background trimmed |
| `tools/member_clearance.py` | Gap or overlap between every pair of branches, from the centrelines a design echoes with `part="paths"`; fails above a merge limit (§15.1) |

---

## 0. The whole process in brief

```bash
# 1. design: edit the .scad; the user's OpenSCAD window auto-reloads it (§2)
# 2. look at it: quick preview render (seconds), read the PNG
python tools/render_png.py design.scad preview.png --view persp --size 900
# 3. test risky components alone with a full CGAL render (§6.1)
# 4. package + verify in one go (minutes, parts render in parallel)
python tools/build_design.py design.scad --name "Design Name" \
    --part bark=#6F5034 --part leaves=#3F8E43 --check-args "--bore-r 41 --floor-h 9"
# 5. if a check fails: locate it, fix the .scad, rebuild
python "tools/mesh_check.py" "Design Name/Design_Name.3mf" --bore-r 41 --floor-h 9 --locate
```

Do not call a design finished until step 4 prints `BUILD: PASS` (mesh checks and the Bambu Studio
slice) **and** you have looked at the PNG.

---

## 1. Environment

| Item | Value on this machine |
|---|---|
| OpenSCAD | **2021.01** at `C:\Program Files\OpenSCAD\`. Use `openscad.com` from scripts (a console binary that prints the log); `openscad.exe` is the GUI |
| Geometry kernel | CGAL only: exact, single-threaded and slow (minutes per part). There is no Manifold backend in 2021.01 (§7) |
| Python | 3.13 with `numpy` and `Pillow`. The tools need nothing else (no trimesh) |
| Shell | PowerShell 5.1 by default; Git Bash is also available |

The tools find OpenSCAD through `$OPENSCAD`, then the default install path, then `PATH`.

**Shell pitfalls that each cost a failed run:**

- **`-D` string values lose their quotes in PowerShell.** `-D 'part="bark"'` arrives as `part=bark`,
  which OpenSCAD reads as an unknown variable, so it renders nothing (`WARNING: Ignoring unknown
  variable 'bark'`). Write `-D 'part=\"bark\"'` in PowerShell and `-D 'part="bark"'` in bash. Better still,
  let the Python tools call OpenSCAD: they pass arguments as a list, with no quoting involved.
- **PowerShell `-replace` is case-insensitive.** Replacing a placeholder `SCR` also hits `scratchpad`.
  Don't template scripts with `-replace`; write the `.py` file directly.
- **Inline `python -c "..."` with nested quotes breaks the PowerShell parser.** Put anything longer than a
  line into a `.py` file.
- Python output in a background run is buffered until the process ends. An empty log mid-run is normal.

---

## 2. Working with the user's open OpenSCAD window

There is no API into the OpenSCAD GUI. **Share a file instead:**

1. Find what is open: `(Get-Process openscad).MainWindowTitle` gives, e.g., `claudeTest.scad - OpenSCAD`.
   The command line only names a file if it was opened that way.
2. Ask the user to turn on **Design → Automatic Reload and Preview**. After that, every save you make
   re-previews in their window.
3. You cannot see their window, so render your own PNGs (`tools/render_png.py`, or
   `openscad.com -o x.png --camera=...`) and read them. Keep them around 900 px; full-size renders
   waste context.
4. If the user may also be editing, ask them to save before you write, so neither of you overwrites the
   other.
5. Structure the file for the **Customizer panel**. `/* [Section] */` comments group variables, and
   `// [a, b, c]` after a string variable makes a dropdown. A good Customizer is most of the
   hand-off: the user can resize the glass or thin the leaves without reading code.
6. Put an `echo()` summary of the derived dimensions in the file. It appears in the user's console on
   every reload and in your CLI log (§5.8).

---

## 3. Design process

1. **Read the brief and the house rules (§4).** Look at earlier designs in the repo for style: the
   vase galleries use sculptural, organic, multi-colour bodies.
2. **Step 1: model the reference object first**, e.g. the glass the holder must fit. Give it
   variables (`glass_d`, `glass_h`) and preview-only detail (wall, rounded foot, translucent colour).
   Save it so the user sees it, and render it yourself.
3. **Step 2: derive every holder dimension from those variables.** Bore radius, floor height,
   stem radius, fork heights and crown height are all expressions in `glass_*`, never literals. Then
   changing the glass in the Customizer rebuilds a correct holder.
4. **Iterate in preview.** A preview takes about 2 s, a full render minutes. Render 2–3 angles
   (a front 3/4 view, a high view that looks into the opening, a view without the glass) after each
   change, and judge the look there. Also render:
   - **the `iso` view that `build_design.py` will use for the gallery PNG.** Turn the design about z so
     it reads there (§9: the side facing away from the viewer is φ = 135°).
   - **the `top` view, to check the crown layout.** Leaf clusters within ~10 mm of each other or of
     another limb read as one blob, and cutting the colour parts apart there leaves slivers (§6).
   - **close-ups of the joints** (forks, root-to-plate). Use `openscad.com --camera=eye,centre` with
     `--projection=perspective`. Seams and ledges don't show at full-model scale.
5. **Before the first full render, test the risky primitives alone** (§6.1). One bad tube invalidates
   a 15-minute render.
6. **Build and verify** (§9, §10), fix, rebuild. Only re-render parts whose geometry changed.
7. **Package and report** (§10, §11).

---

## 4. Print rules (house rules)

| Rule | Value | Where it comes from |
|---|---|---|
| Glass bore | straight cylinder, radius `glass_d/2 + 1 mm`, from the floor up through the top, **subtracted from everything** so the fit is guaranteed by CSG | Pot guide §1.1, woven §6b (`insertOffsetMm` 1) |
| Glass floor | **≥ 7.5 mm** above the build plate | Woven §8 |
| Members clear the bore | the innermost surface stays ≥ ~1 mm outside the bore, so no member is cut flat by it | Woven §6b (house style) |
| Overhang | printed surface past **60° from vertical < 0.5 %**, excluding the bottom 1 cm and bridged spans. 45° is report-only | Pot §5.1, woven §8 (user's Bambu setup) |
| Bed contact | members lying on the bed are **cut through 35 % of their height**: centreline at `0.3·r` above z = 0, which leaves a flat ≥ 95 % of the tube width | Woven §6b, §8 |
| Bottom 1 cm | some overhang is allowed there; the slicer can add "on build plate only" supports | Woven §8 |
| Topology | 0 boundary / 0 non-manifold edges on **every** part | Both guides |
| Sits on z = 0 | yes | Both guides |
| Colours | **Bambu Lab PLA Basic only**, hexes from the table below; pick a combination not already in the palette tables of the other two guides, or used by an OpenSCAD design so far (Braided: Cocoa Brown + Mistletoe Green; Embracing: Cocoa Brown + Mistletoe Green + Bright Green; Cradle, Tangled, Chaotic, Grand Chaotic and Wild Chaotic: Cocoa Brown alone) | Pot §12, user |
| Printer and infill | **Bambu Lab H2C** (0.4 mm nozzle, 0.20mm Standard process), **35 % sparse infill**, unless the user names another | user |

**Bambu Lab PLA Basic colours** (the same list is built into `tools/bambu_3mf.py`; keep the two in
step):

| Name | Hex | Name | Hex | Name | Hex |
|---|---|---|---|---|---|
| Jade White | `#FFFFFF` | Hot Pink | `#F5547C` | Cyan | `#0086D6` |
| Beige | `#F7E6DE` | Orange | `#FF6A13` | Blue | `#0A2989` |
| Gold | `#E4BD68` | Pumpkin Orange | `#FF9016` | Cobalt Blue | `#0056B8` |
| Silver | `#A6A9AA` | Sunflower Yellow | `#FEC600` | Purple | `#5E43B7` |
| Gray | `#8E9089` | Yellow | `#F4EE2A` | Indigo Purple | `#482960` |
| Bronze | `#847D48` | Bright Green | `#BECF00` | Blue Gray | `#5B6579` |
| Brown | `#9D432C` | Bambu Green | `#00AE42` | Light Gray | `#D1D3D5` |
| Cocoa Brown | `#6F5034` | Mistletoe Green | `#3F8E43` | Dark Gray | `#545454` |
| Maroon Red | `#9D2235` | Turquoise | `#00B1B7` | Black | `#000000` |
| Red | `#C12E1F` | Magenta | `#EC008C` | Pink | `#F55A74` |

**Geometry translations of the 60° rule:**

- A tube whose axis rises at angle α above horizontal has its underside tilted `90° − α` from vertical.
  Keep **α ≥ 30°** (≥ 45° for clean undersides). For a helix of radius ρ that climbs height H while turning
  θ radians: `α = atan(H / (ρ·θ))`.
- Spheres always have a bottom cap past 60° (about 6.7 % of their area). Use them only as joints whose
  underside is buried in other members.
- **Thin blades (leaves, fins) must stand upright**: the blade plane contains the vertical, and its
  long axis stays within ~25–30° of vertical. A pointed lens has ~37–45° half-angles at its tips, so a
  steeper tilt turns the lower edge into a shelf. Thickness ≥ 2.4 mm (six 0.4 mm lines).
  The exact condition: a lens edge with half-angle θ, on a blade tilted τ from vertical, overhangs where
  **θ + τ > 60°**. The half-angle shrinks away from the tips, so the shelf is confined to the lower tip.
  Measured on a 26 × 12 mm lens: at τ = 0 it is 0.4 % of the leaf area, all in the lowest 1 mm; at
  τ = 27° it is 2 %, all in the lowest 3 mm along the axis. A `sink` of ≥ 2.5 mm buries most of it in
  the twig.
- Branches that start at a fork and climb outward need their outward and sideways speed below their
  climb. Budget with exponents close to 1 on the outward terms (§5.4).

---

## 5. OpenSCAD techniques that work

The reference file `Braided Tree Vase Holder/Braided_Tree_Vase_Holder.scad` contains all of these in
working form. Copy from it.

### 5.1 File layout

```
header comment (what it is, "Step 1 is the glass ...")
/* [Glass vase] */ /* [Fit] */ /* [Trunk] */ ...   Customizer variables, with units and limits in comments
/* [Output] */ part = "assembly"; // [assembly, holder, bark, leaves]
Derived values          (all from the glass variables)
Library                 lerp, unit, tangents, transport, sweep, loft, cyl, rnd
Step 1: the glass       glass(), preview only
Step 2: the holder      paths as functions, then modules per component
trim()                  subtract the bore and everything below z = 0
echo summary
part selector           if (part == ...) blocks
```

`part` must select **disjoint colour bodies** (§5.7), plus an `assembly` view that shows the colours
and the glass together. Add `none` to the list, for component tests (§6.1).

Constants that are not for the user (fold factors, jitter, offsets) belong in a `/* [Hidden] */`
block with the derived values, not halfway down the file. Derive them from the Customizer variables
wherever a user change could break them, e.g. an offset that has to exceed a leaf's fold height
(§5.7).

### 5.2 Tubes along paths: `sweep()` on top of `loft()`

Model branches, stems and roots as **one polyhedron per tube**. Do not use `hull()` chains of spheres:
every hull is another CGAL union, and hundreds of them take hours in 2021.01.

```openscad
function unit(v) = v / norm(v);
function tangents(P) = [for (i = [0:len(P) - 1])
    unit(i == 0 ? P[1] - P[0] : i == len(P) - 1 ? P[i] - P[i - 1] : P[i + 1] - P[i - 1])];
function first_normal(t) = unit(cross(t, abs(t[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0]));
function transport(T, i, prev) = i >= len(T) ? [] :            // parallel-transport frames
    let(n = unit(prev - (prev * T[i]) * T[i])) concat([n], transport(T, i + 1, n));

module sweep(P, R, sides = 18, ridges = 6, depth = 0.10, phase = 0) {
    T = tangents(P);
    N = transport(T, 0, first_normal(T[0]));
    loft([for (i = [0:len(P) - 1]) let(B = cross(T[i], N[i]))
          [for (j = [0:sides - 1]) let(a = 360 * j / sides + phase,
                                        r = R[i] * (1 + depth * cos(ridges * a)))   // bark ridges
               P[i] + r * (cos(a) * N[i] + sin(a) * B)]]);
}

// Closed solid through rings; each ring counter-clockwise seen from the direction of travel.
module loft(rings) {
    n = len(rings); S = len(rings[0]);
    pts  = [for (ring = rings) each ring];
    side = [for (i = [0:n - 2]) for (j = [0:S - 1])
            let(j2 = (j + 1) % S, a = i * S + j, b = (i + 1) * S + j, c = (i + 1) * S + j2, d = i * S + j2)
            each [[a, b, c], [a, c, d]]];
    caps = [[for (j = [0:S - 1]) j], [for (j = [S - 1:-1:0]) (n - 1) * S + j]];
    polyhedron(points = pts, faces = concat(side, caps), convexity = 10);
}
```

- **Winding:** ring points run counter-clockwise when viewed from ahead, looking back down the path.
  The first cap takes the ring order as is and the last cap reverses it. Check it once: a single tube
  exported alone must report a **positive volume** in `mesh_check.py` (a negative volume means the
  winding is inside out).
- Taper and bark: `R` is a per-ring radius list, `ridges` / `depth` add longitudinal bark ridges.
  With `sides = 18` and `ridges = 6`, each ridge gets three samples.
- Hide open ends inside other bodies, or cap them with a small sphere of the end radius.

### 5.3 Paths in cylindrical coordinates

```openscad
function cyl(rho, phi, z) = [rho * cos(phi), rho * sin(phi), z];
```

Write every path around the glass as `rho(t), phi(t), z(t)`. Interpolating in Cartesian coordinates
cuts chords inside the circle, towards the bore. In cylindrical coordinates the clearance is simply
`rho − r_tube`.

### 5.4 Recipes from the reference design

**Braid (two helix families woven over and under).** `N` stems per direction, `rows` crossing
intervals between the lower fork row `z0` and the upper fork row `z1`:

```openscad
twist = rows * 180 / N;                                         // degrees each stem turns
function weave_b(t) = depth * sin(180 * t);                     // 0 at both fork rows
function stem_path(dir, i) = [for (s = [0:48]) let(t = s / 48)
    cyl(rs + dir * weave_b(t) * cos(rows * 180 * t),            // +-: opposite families swap over/under
        360 * i / N + dir * twist * t,
        z0 + (z1 - z0) * t)];
```

- Crossings fall where `rows·180·t` is a multiple of 180, so `cos` alternates ±1: a true plain weave.
- `depth` < tube radius, so the crossing stems fuse into one rigid body.
- Stems of opposite families meet at the fork rows (angles `360i/N` at z0 and `360i/N + twist` at z1).
  Hang roots below the lower forks and branches above the upper ones.
- Stem radius: `rs = bore_r + gap + max over t of (r(t) + weave_b(t)·|cos(rows·180·t)|)`. This computes
  the clearance instead of guessing it.
- The reference uses N = 5, rows = 3 around an 82 mm bore, which gives a 46° climb.

**Roots.** Drop from the fork, flatten onto the bed, taper with a flare:

```openscad
function root_r(t) = r1 + (r0 - r1) * pow(1 - t, 1.6);
z(t)   = 0.3 * root_r(t) + (z0 - 0.3 * r0) * pow(1 - t, 2.5);   // on the bed: 35 % cut
phi(t) = phi0 + side * spread * t + bend * t * t;                 // gentle one-sided bend only
```

**Branches.** From a fork, `rho = rs + out·t^1.3`, `phi = phi0 + s·spread·t`, `z` linear up to the
tip. Exponents near 1 spread the outward and sideways motion evenly, which keeps the climb angle above
30°.

**Folded leaf, as one lofted solid.** A pointed lens along +y with a shallow V cross-section, so it
reads as a leaf from above as well:

```openscad
function lens_w(y, L, W) = let(Rv = (L*L/4 + W*W/4) / W)
    max(0.3, sqrt(max(0, Rv*Rv - pow(y - L/2, 2))) - (Rv - W/2));   // 0.3 mm blunt tips
module leaf3d(L, W) {
    h = leaf_t / (2 * cos(fold)); k = tan(fold);
    loft([for (i = [0:16]) let(y = L * (1 - cos(180 * i / 16)) / 2, w = lens_w(y, L, W))
          [[-w, y, w*k + h], [0, y, h], [w, y, w*k + h],       // ring CCW seen from +y
           [ w, y, w*k - h], [0, y, -h], [-w, y, w*k - h]]]);
}
```

Place it with a `multmatrix` whose columns are `x = a × u`, the axis `a` (tilted from vertical towards
the tangent) and the outward normal `u`. The blade then stands upright and faces outward.

**Where a leaf starts decides whether it prints.** Start it **inside its branch, `sink` mm back along
the branch's own axis** (`base − sink·along − 0.6·a`), not `sink` mm straight down its own axis.
Straight down from the tip of a branch climbing at 50° lands 2.5 · cos 50° ≈ 1.6 mm off the axis,
at or past the surface of a thin branch. The leaf's lowest corner then hangs below the branch and
starts in mid-air: Bambu Studio calls it a floating region (the slicer check in `build_design.py`
fails on it), and the printer extrudes a blob into the air. Bambu Studio flagged both trees for
this; after the change, neither. Its bottom ring must fit inside the branch there too: half the leaf
thickness plus the fold, plus any offset between the leaves of a cluster (§5.7). The small extra
step down its own axis keeps leaves that share a base from sharing a vertex (§6).

**Recipes from Embracing Tree** (`Embracing Tree/Embracing_Tree.scad`, §13):

- **Compact tube definitions with function literals** (2021.01 supports them):
  `function path(f) = [for (j = [0:steps]) f(j / steps)];` and then
  `wood_tube(path(function(t) limb_point(s, t)), path(function(t) limb_radius(s, t)));`.
- **A member that hugs the glass at a constant gap:** `rho(t) = bore_r + gap + r(t)·(1 + bark_depth)`.
  A tapering trunk then leans in as it thins, and the clearance never has to be checked by hand.
- **A stem that carries on through a fork:** build trunk and leader as **one path**,
  `concat(trunk_path, leader_path minus its first point)`, with the radii concatenated the same way.
  Ending the trunk with a cap at the fork leaves a visible ledge where the thinner limbs start.
  Match the two tangents at the join: a direction kink bends the tube with radius ≈ step length /
  kink angle. A 26° kink over 2 mm steps is a 4.5 mm bend on an 8 mm stem, which self-intersects
  (§6). The side limbs start on the stem centreline. A knot sphere of the stem radius covers their
  start caps, which would otherwise poke through the valleys of the bark ridges.
- **Surface roots that arch over a stump plate:** start each root **inside the collar**
  (`rho = bore_r + 0.5`) with `z0 = floor + collar_h − r0·(1 + bark_depth) − 0.5`. Then drop it onto
  the bed with the root profile above. The bore trims the root's inner end into the collar wall,
  where it disappears. Keep the growth-ring grooves inside the roots' inner reach
  (`rings ≤ bore_r − 8`), or the roots fill them.
- **Twigs on a long limb lean back or straight up, never along the limb.** A twig that follows its
  parent limb's direction crowds the limb, or the leaf cluster at the limb tip.
- **Tips thick enough to hold their cluster.** Three leaves spread over the two-tone offset form a
  cluster about 4.5 mm deep. A 1.7 mm twig tip cannot hold it. Derive the tip radius:
  `leaf_hold_r = (shoot_ahead + 0.3 + leaf_thickness) / 2 / (1 − bark_depth) + 0.3` (2.7 mm).
  Taper the twigs and limbs to that radius, centre the cluster on the tube axis, and
  `assert(twig_r >= leaf_hold_r)`. Get the tube direction at the tip from the path:
  `function tip_dir(f) = unit(f(1) - f(1 - 1/steps));`.

### 5.5 Deterministic variation

```openscad
function rnd(a, b = 0, c = 0) = let(x = sin(a*127.1 + b*311.7 + c*74.7) * 43758.5453) x - floor(x);
function jit(a, b, c) = (rnd(a, b, c) - 0.5) * jitter;      // +-jitter/2 degrees
```

Vary sizes, bends and tilts with `rnd(index...)`. Renders stay reproducible, and small angle jitter
also keeps geometry off exact angles (§6).

### 5.6 Stable previews

A preview is OpenCSG, not CGAL. **Coplanar faces in a `difference()` z-fight**, for example a stump
top at `floor_h` against the bore cylinder's bottom at `floor_h`. The subtracted face then flickers in
the other body's colour: the reference stump showed up green. Only `trim()` bodies that can actually
reach the bore or the bed. In the assembly view the leaves are not trimmed.

- A plate that lies entirely between the bed and the glass floor never needs trimming: union it
  outside `trim()`.
- **Never nest a `difference()` inside a `difference()` for small cutters** such as growth-ring
  grooves built as cylinder minus cylinder. The preview normalises the CSG tree into products: six
  such rings cut from the Cradle Tree trunk gave 448 terms and 12 s per preview. Build each groove
  as one solid (`rotate_extrude() translate([r - w/2, 0]) square([w, h]);`) and the whole preview
  dropped from 24 s to 9 s.
- Preview-only helpers (ground disc, height limit ring) sit behind a `show_guides` toggle that
  defaults to **false**. The gallery PNG is a preview render too, and would include them.
- A collar around the glass foot should have an **inner lip** (inner radius `bore_r − 0.5`) that the
  bore cuts away. An inner wall at exactly `bore_r` coincides with the bore cylinder and flickers.

### 5.7 Colour parts

OpenSCAD 2021.01 writes **one mesh per 3MF, without colour**. So:

1. Give each colour its own `part` value.
2. Export each one separately (in parallel, §7).
3. Merge them with `tools/merge_3mf.py` into one object with named parts.

The parts **must not overlap**. Subtract only what a part actually touches, e.g.
`leaves = difference() { leaves(); branches(); }`. Don't use `bark − leaves`: subtracting from the
large body is far more expensive and gains nothing. Subtracting the whole wood body (plate, roots,
trunk) from the leaves, as the Embracing Tree draft did, also costs time for nothing. Write a
`leaf_hosts()` module with only the members the leaves grow from.

**Two colours inside one leaf cluster** (e.g. a bright shoot flanked by darker mature leaves):
`dark = dark_leaves − hosts − light_leaves`. The V-folded leaves cross each other, and wherever a
dark leaf's raised edge sits in front of the shoot, the subtraction leaves a **loose sliver**. Embracing
Tree had 10 of them, 0.07–1.3 mm³ each, plus one with zero volume. The fix is to stand the front tone
off the back tone along the outward normal by **more than the largest fold-height difference**:
`shoot_ahead = fold · leaf_width / 2 + 0.3` (the extra 0.3 absorbs the facing jitter). Then no dark
material is ever in front of the shoot. The cut leaves a connected back layer, and each leaf keeps its
own base in the twig. Keep every offset small enough that each leaf still overlaps the twig tip.

Rejected alternative: subtracting the shoot's outline extruded through the cluster (a prism). There
are no skins, but it cuts the mature leaves off their bases. They end up as crescents that touch
only the shoot along a thin seam, or nothing at all.

### 5.8 Customizer and summary

```openscad
echo(str("Tree vase holder: glass ", glass_d, " x ", glass_h, " mm, bore d ", 2 * bore_r,
         " mm, stems at r ", round(stem_rs * 10) / 10, " mm rising ", round(stem_rise), " deg ..."));
```

Print the numbers you would otherwise have to measure: bore, floor, member climb angles and overall
height.

---

## 6. CGAL traps

Each of these cost at least one full render cycle on the reference designs.

| Symptom | Cause | Fix |
|---|---|---|
| `ERROR: CGAL error in CGALUtils::applyUnion3D: assertion violation!` | A **self-intersecting tube**: a bend radius smaller than the tube radius. A sine wiggle of amplitude A (mm) and wavelength λ bends with radius `λ² / (4π²·A)`; 4 mm over 17 mm gave **1.8 mm** against a 6 mm root. A direction kink where two paths are concatenated does the same (§5.4) | Use gentle one-sided bends; keep the bend radius > tube radius everywhere; match tangents at path joins. Find the culprit with §6.1 |
| Bambu Studio warns "*object … has floating regions*"; the build's slicer check fails | A region whose lowest point has nothing under it, e.g. a leaf corner poking out below a thin twig because the leaf was sunk down its own axis | Start leaves inside the branch along its axis, and make tips thick enough for the cluster (§5.4) |
| A colour part has **more shells than expected**, some tiny (0.1–1 mm³, even 0) | Two overlapping decoration tones were cut apart with `front − back`, and **slivers** of the back tone were left in front of the front tone (§5.7) | Offset the front tone by more than the fold-height difference. Find slivers by listing each shell's volume and position (§8) |
| The render "finishes" but pieces are missing | OpenSCAD **keeps going after a CGAL error** and drops that union | Always scan the log for `ERROR`. `build_design.py` fails on it |
| 14 non-manifold edges where two tubes cross | **Mirror-image tubes** (the two helix families, the left/right branch pair) have ring samples at mirrored angles: ψ + 20°·j maps to 180° − ψ − 20°·j, so vertices **coincide exactly** | Give one of each mirror pair a `phase` of half a ring step (`180 / sides`). Any phases whose sum isn't a multiple of the step will do |
| Non-manifold edges at one fork only | That fork sits at **exactly 180°**. OpenSCAD's `sin`/`cos` are exact at multiples of 90°, so a zero-tilt leaf lines up exactly with the faces of the `$fn` tip sphere | Small deterministic angle jitter (§5.5) |
| Non-manifold edges along a leaf's midrib and at its tips | Leaf built as **two slabs rotated about the midrib**: both share the tip points and cross along the axis | Build it as one lofted polyhedron (§5.4) |
| Touching at a single point or edge | Several solids **start at the same point** (leaf clusters) | Offset each start along its own axis (`sink`) |
| The checker reports non-manifold edges but OpenSCAD said nothing | The checker **welded near-duplicate vertices** (CGAL output can hold distinct vertices 1e-5 mm apart) | Use topology by 3MF vertex index. `mesh_check.py` does this and lists near-duplicates separately. "len 0.000" edges are the giveaway |
| Negative volume | Face winding inside out | Reverse the ring order (§5.2) |

**A clean preview says nothing about the render.** PNG export and F5 use OpenCSG, which never runs
CGAL. Only a full render (F6, or `-o *.3mf|*.stl`) exposes these problems.

### 6.1 Testing one component with a full render

```powershell
# t_root.scad: include the design, render one primitive; part="none" silences the part selector
Set-Content -Encoding ascii t_root.scad "include <design.scad>`nsweep(root_path(0, 1, 5), root_radii);"
& "C:\Program Files\OpenSCAD\openscad.com" -o t_root.3mf -D 'part=\"none\"' t_root.scad
python tools/mesh_check.py t_root.3mf
```

Test one stem, one root, one branch, one leaf, two crossing stems, a fork, and one cluster of leaves.
Each takes seconds. Run them as parallel processes from a small Python script: write each test's
`include` file, call `openscad.com` with the arguments as a list (no quoting trouble, §1), then call
`mesh_check.py`. On Embracing Tree, ten tests (single tubes, all roots, the whole crown, the plate,
one trimmed leaf cluster) finished in 35 s together. Include the real colour parts too
(`leaves_dark();`): at 1 min each, they show sliver shells before a full build does.

**Read an isolated component's check selectively.** Only the edges, shell count and volume sign
count. `bottom at z` fails because the piece floats. The overhang bands are measured from the
piece's own top, so for anything under ~4 cm tall the "top 3 cm" band overlaps the bottom band, and
the percentage is meaningless. Judge overhang on the merged file only.

---

## 7. Render time and parallelism (2021.01, this machine)

| Render | Time |
|---|---|
| Preview / PNG | 1–3 s |
| Bark part: stump, 10 stems, 15 roots, 15 branches, knobs; 58 k triangles | **3 min 22 s – 4 min 04 s** |
| Leaves, one lofted polyhedron each (75 leaves), minus branches | **2 min 06 s** |
| Leaves built as two unioned slabs each | 5 min 44 s |
| Whole holder as one body | > 15 min, abandoned |
| Embracing Tree wood: plate with ring grooves, collar, stem, 9 roots, 2 limbs, 6 twigs; 36 k triangles | **2 min 06 s** |
| Embracing Tree leaf parts, 9 or 18 leaves minus hosts (and minus the shoots) | 39 s / 53 s |
| Component tests (one tube to the whole crown) | 1–40 s |
| Cradle Tree, one body: textured trunk, 5 branches with forks and stubs, 7 roots; 315 k triangles | **14 min 19 s** (one branch assembly alone 54 s) |
| Cradle Tree preview (Normal / Draft quality) | 16 s / 6 s |
| Tangled / Chaotic Cradle Tree, one body, 8–9 branches with merges; 337 k / 328 k triangles | **21 min 37 s / 21 min 20 s**, run side by side |
| Grand Chaotic Tree, one body: buttressed trunk, 13 branches pressed against the glass, 9 roots; 500 k triangles, 5 GB RAM | **23 min 28 s** |
| One pressed limb alone / all roots alone (component tests) | 20–30 s / 6 min 13 s |
| Wild Chaotic Tree, one body: the trunk skin carrying the root bases, 13 branches, 9 roots; 454 k triangles | **21 min 07 s**; its trunk alone 41 s, its roots 5 min 24 s |
| A pair of merging branches alone (component test) | 1.5–3 min |

- CGAL uses one core. **Export colour parts as separate processes in parallel** (`build_design.py`
  does this), instead of rendering one big union.
- Re-render only the parts whose geometry changed. For long renders, run them in the background and
  check `Get-Process openscad` (CPU seconds climbing means it's working).
- Fewer booleans matter more than fewer triangles. A single polyhedron is nearly free; each union or
  difference is not.
- Newer OpenSCAD development builds have the **Manifold** backend, which is 10–100× faster. Installing
  one is a download: ask the user first, and never do it silently.

---

## 8. Verification: `tools/mesh_check.py`

```bash
python tools/mesh_check.py "Design/Design.3mf" --bore-r 41 --floor-h 9 [--foot-r 3] [--max-overhang 0.5] [--locate]
```

It checks every part of the 3MF, then all parts together:

| Output | Meaning | Must be |
|---|---|---|
| `boundary`, `non-manifold` (per part) | open edges and edges shared by more than two faces, by 3MF vertex index | **0 / 0** |
| `shells` | connected pieces in a part | body part **1**; a decoration part may be many, as long as each piece sits on the body (the reference leaves are 42 clusters on the branches). **Know the number you expect** (e.g. one per leaf cluster) and treat any extra as slivers until proven otherwise |
| `near-duplicate vertices` | distinct vertices within 1e-4 mm | informational |
| `volume` | per part and total; mass at 100 % solid, and ~30 % of that at typical infill | positive |
| `bottom at z` | lowest point of all parts | **0.000**. A decoration part alone fails this; check the merged file |
| `past 60 deg` | % of printed surface, split into bottom 1 cm / body / top 3 cm, and "above 1 mm" | body + top **< 0.5 %** |
| `past 45 deg` | same split | report only |
| `closest material to the axis above the floor` | bore clearance | ≥ bore radius |
| `closest material to the glass`, `seat` (with `--foot-r`) | for a glass that stands on the wood with no floor (§16): distance to the glass envelope, a bore of `--bore-r` from `--floor-h` up with its foot rounded by `--foot-r`; then the pads the glass stands on (area, radial range, largest angular gap) | ≥ 0 (−0.01 tolerance); gap **< 180°** |
| `RESULT` | PASS or FAIL; exit code 0 / 1 | **PASS** |

`--locate` prints the position of every bad edge (`r`, `phi`, `z`, length). Match those to the design:
fork angles, branch spread, crossing rows. That is how every trap in §6 was found.

`mesh_check.py` counts shells but does not list them. To find slivers, keep the per-part exports
(`build_design.py --keep-exports`) and list each shell's triangle count, volume and centre (`r`,
`phi`, `z`). Use a union-find over the triangles' vertex indices, as in `topology()`, and
`surface()` for the volume. Real pieces are hundreds of mm³; slivers are ~1 mm³ or less.

Figures the checker doesn't print, but the hand-off needs:
- the clearance of the **members**. The bore line reports the collar wall, which sits exactly at the
  bore, so measure the closest material above the collar top.
- **where the bottom-1 cm overhang sits** (e.g. "all below 1.8 mm: bed-cut edges of the roots").

Both are a few lines on top of `load()` / `surface()`.

**Regions that start in mid-air: slice to find out, `tools/floating_check.py` to find where.**
Bambu Studio names no position, so the tool takes every surface point lower than all its neighbours
and asks whether anything is under it (a ray straight down) or just beside and below it (0.5 mm,
one extrusion width). On tube designs it matches the slicer exactly: 0 on the five it accepted, 1 on
the Wild Chaotic Tree it refused, which was a fork's end cap lifted off its parent by the fork's own
arch (§17.1). It over-reports on thin blades (120 on the Braided Tree's 75 leaves), because a leaf's
lowest edge is carried by the twig beside it in the same layer; only a per-layer island test sees
that, which is the slicer's job.

An earlier vertex test was tried and dropped: it looked for lowest points with nothing 0.15 mm below
them, but it could not match Bambu Studio on these trees.
- **Horizontal leaf bottoms.** A strict "all neighbours higher" test misses them: their vertices all
  sit at the same height.
- **Leaf edges touching wood.** Almost every other hit was a leaf edge that touches wood sideways,
  which the slicer merges into the wood's island.
- **Fork knob bottoms.** Its bottoms hang 5 mm up but join the roots within a layer; Bambu Studio
  accepts them.

`build_design.py` therefore slices the project with Bambu Studio (§9.1) and fails on its "floating
regions" warning. Bambu Studio flagged the leaf bases of both trees and accepted them after the fix
in §5.4.

For a multi-part file, the overhang of a part's cut faces (e.g. leaf bases where the branch was
subtracted) counts in the totals even though it is internal. The figure is therefore slightly
pessimistic, which is the safe side.

---

## 9. Packaging: `tools/build_design.py`

```bash
python tools/build_design.py <design>.scad --name "Design Name With Spaces" \
    --part bark=#6F5034 --part leaves=#3F8E43 \
    --check-args "--bore-r 41 --floor-h 9" [--out DIR] [--keep-exports]
```

It creates:

```
<scad folder>/<Design Name With Spaces>/
    Design_Name_With_Spaces.scad   copy of the source; the 3MF is exported from this copy
    Design_Name_With_Spaces.3mf    ONE object, one named part per --part, units mm, standing on z = 0
    Design_Name_With_Spaces.png    true isometric (orthographic, 35.26 deg elevation, 45 deg azimuth), trimmed
```

- The 3MF is a **Bambu Studio project for the H2C** (`--printer`, default H2C; `--infill`, default
  35). It is one object with named parts on plate 1, each part on its own Bambu PLA Basic filament,
  with purge volumes. See §9.1. `--printer none` keeps the plain core-spec 3MF that `merge_3mf.py`
  writes (`<components>` plus `basematerials` display colours). Any slicer loads that one, but Bambu
  Studio opens it as "geometry only", with every part on filament 1.
- The PNG is a **render**, not a photo. Say so in the hand-off. It shows the glass in place; the CLI
  preview draws the translucent glass nearly opaque.
- The house gallery layout for the browser apps is `3dModels/Vases/<Design Name>/`. Use it if you are
  working in the full repo; `--out` sets the folder.
- **If the `.scad` already lives in its package folder** (e.g. `art/.../Embracing Tree/Embracing_Tree.scad`),
  pass that folder as `--out`. Otherwise the default creates a nested `Embracing Tree/Embracing Tree/`.
  When the file name already matches `--name` (`Embracing_Tree.scad` for "Embracing Tree"), the source
  is used in place and nothing is copied.
- **Don't edit the `.scad` while a build runs.** The exports read the file when they start, but the
  PNG is rendered afterwards from the file on disk. An edit mid-build gives a package whose PNG, 3MF
  and `.scad` come from different versions. Batch cosmetic edits, then rebuild once for the final
  package.
- `--keep-exports` writes `<Name>_<part>.3mf` into the package folder, which is handy for per-part
  analysis (§8). Delete them before the hand-off.
- **Orientation in the `iso` view:** +y appears at the back right, and the direction pointing
  straight away from the viewer is **φ = 135°**. Place whatever should stand behind the glass there,
  e.g. Embracing Tree's `trunk_angle = 135`. A render from a camera of your own will not match the
  gallery PNG.
- The build overwrites any `<Name>.png` already in the folder, e.g. a draft preview. Back it up first
  if the user may want it.

### 9.1 Bambu Studio project: `tools/bambu_3mf.py`

```bash
python tools/bambu_3mf.py "Design/Design.3mf" [more.3mf ...] [--printer H2C] [--infill 35] [--exact-colors]
python tools/bambu_3mf.py "Design/Design.3mf" --out other.3mf --printer X1C
python tools/bambu_3mf.py --list-printers    # H2C H2D H2DP H2S X1C X1E P2S P1S A1 A1M
```

It writes the layout Bambu Studio saves itself:

| File | Holds |
|---|---|
| `3D/Objects/object_1.model` | the part meshes, coordinates exactly as exported, so `mesh_check.py` still finds the bore on the Z axis |
| `3D/3dmodel.model` | the object as components; the build item moves it to the middle of plate 1 and onto the bed |
| `Metadata/model_settings.config` | object and part names, the filament of each part, plate 1 |
| `Metadata/project_settings.config` | printer, process and filament preset **names**, filament colours, the purge matrix, 35 % infill |

- **Only preset names travel, never their values.** Bambu Studio rebuilds each system preset
  from its own profiles and keeps only the keys listed in `different_settings_to_system` (the infill
  densities). So the file never ships stale temperatures or G-code. The preset names were checked
  against Bambu Studio 02.05 (`resources/profiles/BBL`) for all 10 printers, including bed size,
  height and nozzle count.
- **Colours** snap to the nearest PLA Basic colour (CIEDE2000, table in §4). Parts that land on the
  same filament share a slot. `--exact-colors` keeps the hexes as they are.
- **Purge volumes** are computed as Bambu Studio's "Re-calculate" does, using its measured tables
  (identical to `resources/flush/*.txt` in 02.05) and its HSV formula. Without them, filaments 3+
  would change with no purge at all.
- **Converting again** is safe for the tool's own output (e.g. `--printer X1C`). A project saved by
  Bambu Studio itself is refused without `--force`, because converting it would drop the user's edits.
- **Verified:** the colour matching and every purge matrix (10 printers, the full palette and 40
  random colours) match the browser designers' JavaScript exporter exactly. That exporter was run
  under VS Code's Electron with `ELECTRON_RUN_AS_NODE=1`, since there is no Node on this machine.
  Bambu Studio's CLI sliced the Embracing Tree project on the H2C using all three filaments (plus
  the purge matrix from the file).
- **`--slice` (and step 4 of `build_design.py`)** slices the project with the installed Bambu Studio
  (`$BAMBU_STUDIO`, else `C:\Program Files\Bambu Studio\bambu-studio.exe`), in about 10 s. It
  reports print time, grams per colour and every slicing warning, and fails on any warning. It is
  skipped with a note when Bambu Studio isn't installed. How it works: the CLI needs complete presets.
  Without them it looks for `machine_full/` files that a desktop install doesn't have, and it
  crashes. So the tool follows each preset's `inherits` chain in
  `resources/profiles/BBL/{machine,process,filament}` and applies the project's own edits (the
  infill). It then passes the presets with `--load-settings` / `--load-filaments`, which override
  the project on the command line. The G-code header (`; filament_colour`,
  `; flush_volumes_matrix`, the `T0/T1/T2` counts) shows what the slicer actually used. The CLI log
  always contains a few `[error]` lines about `nozzle_volume_type` on dual-nozzle printers. They are
  CLI noise; ignore them.

---

## 10. Hand-off checklist

- [ ] `RESULT: PASS` from `mesh_check.py` on the packaged 3MF, with per-part 0/0 edges
- [ ] Shell count per part equals the number you expect (no slivers, §6)
- [ ] Overhang reported: body and top past 60°, the bottom 1 cm separately (say what it is, e.g.
      "root undersides below 6 mm"), and 45° for reference
- [ ] Bore clearance (collar and members separately), glass floor height and overall size reported
- [ ] Mass: the slicer's grams per colour and print time (from the build's Bambu Studio slice); the
      100 % solid figure only for reference (it alarms people)
- [ ] `BUILD: PASS`: the Bambu Studio slice has no warnings (no "floating regions"); print time and
      grams per colour reported
- [ ] Filament per part, with PLA Basic names from the table in §4; the 3MF is an H2C project unless
      the user asked for another printer
- [ ] Looked at the PNG yourself
- [ ] The `.scad` in the package is the one the 3MF was exported from (`build_design.py` guarantees this)
- [ ] Told the user which Customizer variables matter, and that changing them needs a rebuild

---

## 11. Checklist for a new design (not a tree)

1. Reference object first (the glass, a bottle, a pot), with variables.
2. Silhouette and structure from derived variables. Decide what touches the bed (35 % cut) and what
   holds the reference object (bore plus floor).
3. Members as `sweep()` tubes, blades as `loft()` sections, and revolved bodies as `rotate_extrude()`.
   Avoid `hull()` chains and large `minkowski()`.
4. Break every mirror symmetry and every exact-angle alignment between separate solids (§6).
5. Keep bend radii larger than tube radii, including at the joins of concatenated paths.
6. Any ledge (a collar, a rim) must stand on something wider below it everywhere. A scalloped plate
   under a round collar needs its **minimum** radius outside the collar.
7. Where two colours overlap, decide which one is in front and offset it clear of the other (§5.7).
8. Test one of each primitive with a full render (§6.1), then build (§9).

**Finishing someone else's draft** (Embracing Tree started as one): before anything else, audit it
against §4. Check it with numbers, not by eye: member clearance, collar vs plate radius, root
heights vs the floor, leaf thickness, and what each colour part subtracts. Keep the concept and the
parameter names the author chose. Change the structure only where a rule or a trap forces it.

---

## 12. Reference design: Braided Tree Vase Holder

Folder `Braided Tree Vase Holder/`. A braided money-tree trunk woven around a real glass: roots
spreading over the bed, a stump floor with off-centre growth rings seen through the glass bottom, and a
crown of forked branches with folded leaves around the rim.

| Parameter | Value |
|---|---|
| Glass | 80 × 130 mm (`glass_d`, `glass_h`), clearance 1 mm, so an **82 mm bore**; glass floor 9 mm |
| Trunk | 5 + 5 stems, 3 crossing intervals, radius 7 → 5 mm, weave depth 3 mm, stems at r 50.9 mm rising **46°**, forks at z 13 / 114 mm |
| Roots | 3 per lower fork, 26 mm reach, radius 6 → 2.5 mm, 35 % bed cut, bends up to ±10° |
| Crown | 3 branches per upper fork (22° spread, 14 mm lean-out), 3-leaf tip clusters and a mid-branch pair: 75 folded leaves, 24 × 8 × 2.4 mm, each starting inside its branch (4 mm back from the tip, 3 mm for the pairs) |
| Filaments | bark `#6F5034` Cocoa Brown, leaves `#3F8E43` Mistletoe Green (PLA Basic) |

**Measured on the packaged 3MF** (`build_design.py`, 2026-09-19; an H2C project):

| Check | Result |
|---|---|
| Size | 153.5 × 150.6 × 177.6 mm, standing on z = 0; crown about 3.9 cm above the glass rim |
| Bark | 58 340 triangles, 1 shell, **0 boundary / 0 non-manifold** edges, 249.8 cm³ |
| Leaves | 25 486 triangles, 32 shells (clusters and pairs on the branches), **0 / 0** edges, 12.8 cm³ |
| Past 60° | **0.02 %** above the bottom 1 cm (body 0.00 %, top 3 cm 0.02 %). Bottom 1 cm 0.83 %, all below 6 mm: root undersides where they flatten onto the bed |
| Past 45° | 1.30 % overall (body 0.13 %, top 0.17 %), report only |
| Bore | closest material 42.33 mm from the axis (bore 41.00 mm); leaves ≥ 53.21 mm |
| Bed contact | 89 cm² (stump plus 15 root flats) |
| Mass | 326 g at 100 % solid (bark 310 g, leaves 16 g) |
| Bambu Studio slice (H2C, 0.20mm Standard, 35 % infill) | **no warnings**; 7 h 56 min; **188 g** (bark 173.1 g, leaves 14.9 g) |
| Render | bark 3 min 22 s and leaves 2 min 06 s, in parallel (3 min 44 s / 2 min 35 s alongside another build) |
| Reproducibility | re-exporting the same `.scad` gives byte-identical meshes (SHA-256 of each part's `<mesh>` matched an independent earlier export; checked before the leaf change in step 5) |

Design history, i.e. what the traps in §6 looked like in practice:

1. First full render: `applyUnion3D` assertion. Root wiggle bend radius 1.8 mm against 6 mm roots;
   replaced by a gentle one-sided bend with a flared taper.
2. 14 non-manifold edges at the stem crossings and upper forks: mirror-image tubes with coincident ring
   samples. Fixed with a half-step `phase` on one family and on one branch of each side pair.
3. Non-manifold edges on the leaves: the two-slab fold and shared base points. Fixed with one lofted
   polyhedron per leaf, a per-leaf `sink`, and ±4° jitter (one fork sits at exactly 180°).
4. The last "4 non-manifold edges" were checker artefacts (vertex welding). Fixed by index-based
   topology in `mesh_check.py`.
5. Bambu export (2026-09-19): Bambu Studio's slice warned of *floating regions*. The leaves were sunk
   straight down their own axis from the branch tips, so their bottom corners hung below the
   branches. Starting them inside the branch along its axis (§5.4) cleared the warning. The bark is
   unchanged.

---

## 13. Second design: Embracing Tree

Folder `art/Math Driven Pots and Vases/Embracing Tree/`. A single tree stands behind the glass. Its
trunk hugs the glass and forks into two limbs that wrap around the sides, while the stem carries on
as a tall leader. Nine leaf clusters, each a bright new shoot flanked by two mature leaves, ring the
rim. Below, a scalloped stump plate with growth rings holds the glass in a collar, and surface
roots arch over its rim. It was finished from another author's draft.

| Parameter | Value |
|---|---|
| Glass | 80 × 130 mm, clearance 1 mm, so an **82 mm bore**; glass floor 8 mm; collar 5 mm tall, 2.8 mm wall |
| Trunk and leader | one tube, radius 12 → 8 mm at the fork (z 56) → 2.7 mm at z 155; kept 1.5 mm outside the bore (`member_gap`); stands at `trunk_angle` 135° |
| Limbs | 2, radius 7 → 2.7 mm, wrapping ±112° around the glass, tips 2 / 9 mm above the rim, climbing ≥ **36°**, 2.6 mm outside the bore |
| Twigs | 2 per limb and 2 on the leader, radius 3.2 → 2.7 mm (`leaf_hold_r`: thick enough to hold a cluster), climbing ≥ 45°, leaning back towards the trunk |
| Roots | 6 surface roots arching over the plate rim (5.5 → 2 mm) plus 3 flare roots at the trunk foot (6.5 → 2 mm); 35 % bed cut |
| Leaves | 27 folded leaves, 26 × 12 × 2.4 mm (clusters scaled 0.85–1.05); mature pair at ±27°, shoot 1.8 mm in front of them; each leaf starts 3 mm back inside its tip tube, with the cluster centred on the tube axis |
| Filaments | wood `#6F5034` Cocoa Brown, mature leaves `#3F8E43` Mistletoe Green, shoots `#BECF00` Bright Green (PLA Basic) |

**Measured on the packaged 3MF** (`build_design.py`, 2026-09-19; an H2C project):

| Check | Result |
|---|---|
| Size | 153.8 × 150.6 × 179.4 mm, standing on z = 0 |
| Wood | 36 264 triangles, 1 shell, **0 / 0** edges, 115.0 cm³ |
| Leaves_dark / Leaves_light | 7 144 / 2 734 triangles, **9 / 9 shells** (one per cluster), **0 / 0** edges, 5.5 / 4.0 cm³ |
| Past 60° | **0.07 %** above the bottom 1 cm (body 0.02 %, top 3 cm 0.05 %: leaf bases). Bottom 1 cm 0.30 %, all below 1.8 mm, from the bed-cut edges of the roots and trunk foot |
| Past 45° | 2.90 % (body 2.29 %), report only. Higher than Braided because the limbs climb at 36° |
| Bore | collar wall at exactly 41.00 mm; wood above the collar ≥ 42.69 mm; leaves ≥ 55.51 mm |
| Bed contact | 83 cm² |
| Bambu Studio slice (H2C, 0.20mm Standard, 35 % infill) | **no warnings**; 6 h 08 min; **91 g** (wood 79.6 g, mature leaves 6.6 g, shoots 4.8 g). The checker's "~30 % of solid" estimate (46 g) is half the real figure: thin members are mostly walls. Report the slicer's grams |
| Render | wood 2 min 06 s alone (2 min 23 s alongside another build), leaves about 1 min, in parallel |

Design history:

1. **Draft audit (§11).** The trunk came within 0.2 mm of the bore. The plate's scallops dipped to
   r 41.3 mm under a collar reaching r 43.8 mm, so the collar overhung the edge. The roots rose
   through the glass floor inside the bore. The leaves were 2.2 mm thick. Each leaf part subtracted
   the entire wood body. A `hull()` buttress also reached into the bore. All were fixed by
   derivation (§5.4), not by hand-tuned numbers.
2. **Component tests (§6.1).** All ten came out 0/0 on the first try. The §5/§6 practices (loft
   winding, phases, jitter, `sink`) carried over as written.
3. **First full build.** PASS, but the dark leaves came out as 19 shells for 9 clusters: 10 slivers
   from `dark − light` (§5.7). An outline-prism cut was tried and rejected. Offsetting the shoot in
   front gave 9 shells.
4. **Look.** A ledge at the fork, where the trunk's end cap was wider than the limbs, was fixed with
   a continuous stem (§5.4). Two clusters 6 mm apart and one crowding its own limb were fixed by
   leaning the twigs back. The tree was also turned to 135° so it stands behind the glass in the
   gallery view.
5. **Bambu export.** Bambu Studio's slice warned of *floating regions*. The leaves were sunk 2.5 mm
   straight down from 1.7 mm twig tips, so their bottom corners hung below the twigs, and the
   4.5 mm-deep clusters could not fit inside the tips anyway. The fix: tips at the derived
   `leaf_hold_r` (2.7 mm) and leaves starting 3 mm back inside the tube along its axis (§5.4). The
   slice then came out clean.

---

## 14. Third design: Cradle Tree

Folder `art/Math Driven Pots and Vases/Cradle Tree/`. The glass sits 6 cm up in the branches of a
rooted tree. A trunk with a narrow waist and root buttresses opens into a bowl whose floor, with
growth rings, carries the glass. Five branches grow out of the bowl as ridges. They spiral around
the glass (continuing the trunk's grain), lean out above the rim and fork. Every member wears
procedural bark, and the branches carry knots and pruned twig stubs. It was designed live: the user
watched each save in OpenSCAD with automatic reload.

| Parameter | Value |
|---|---|
| Glass | 80 × 130 mm, clearance 1 mm, so an **82 mm bore**; glass floor at `lift` = 60 mm; rim at 190 mm; `total_h` 250 mm |
| Trunk | a radial surface (§14.1): waist r 19 mm at z 21, root collar +12 mm, 7 buttresses, grain turning 40° up to the floor |
| Roots | 7, radius 8 → 2.4 mm, 46 mm reach, 35 % bed cut |
| Branches | 5, radius 8.5 mm at the floor → 5.5 at the rim → 2 at the tips; bark 1.5 mm outside the bore; turning 87° around the glass (climbing 59°), climbing ≥ 38° out of the trunk; each with a fork above the rim, 2 knots and 2 twig stubs (climbing about 50°) |
| Bark | plates 7 × 14 mm, fissures up to 1.2 mm deep (0.96 on branches), scaled down on thinner members |
| Filament | wood `#6F5034` Cocoa Brown (PLA Basic), one part |

**Measured on the packaged 3MF** (`build_design.py`, 2026-09-19; an H2C project):

| Check | Result |
|---|---|
| Size | 156.4 × 136.5 × 249.2 mm, standing on z = 0 |
| Wood | 314 988 triangles, 1 shell, **0 / 0** edges, 373.2 cm³ |
| Past 60° | **0.04 %** above the bottom 1 cm (top 3 cm 0.00 %). Bottom 1 cm 0.13 %, all below 5 mm: root and trunk-foot edges at the bed cut |
| Past 45° | 3.33 % (body 3.01 %: the bowl flare and the branches leaving it), report only |
| Glass | closest material 40.99 mm from the axis above the floor (bore 41.00 mm): **it lifts straight out of the top**. Glass-to-bark gap 2.5 mm along the glass, 3.4 mm at the rim; about 49 mm of open arc between branches at the rim for fingers |
| Bed contact | 58 cm² |
| Bambu Studio slice (H2C, 0.20mm Standard, 35 % infill) | **no warnings**; 7 h 52 min; **227 g** (463 g if solid) |
| Render | 14 min 19 s as one body; components 7–128 s each |

### 14.1 Techniques this design added

- **Trunk as a radial surface.** Loft horizontal rings, and give each vertex its radius from a
  function of angle and height: `rho(a, z) = core(z) · (1 + buttresses) − bark depth · (1 − bark) +
  knots`. It can't self-intersect. Buttresses are Gaussian lobes at each root's angle that fade out
  by the waist, and everything turns with the spiral grain (`twist_at(z)`). The bottom ring at z = 0
  is the bed contact, so no bed cut is needed.
- **Trunk wrapped round the branches.** Lay the branch paths out first. Then make the trunk core a
  smooth maximum (`smax`, k = 3 mm) of its own waist profile and each branch's centreline radius
  minus half the branch radius. The branches stand out as ridges with no pockets between. Letting
  branches loop out of a narrow trunk left visible gaps.
- **Procedural bark** (`bark(U, V)`, in plate units):
  - Fissures run on whole numbers of `U`, warped by a smooth three-sine noise at plate scale, so
    neighbouring furrows converge and part.
  - Each plate column gets its own random length and tilt for the cross-cracks, so the cracks never
    line up.
  - Random columns get a shallower split down the middle.
  - Profiles use `smoothstep` ramps at least a sample wide. Narrower cracks alias into a pixelated
    look, which showed on the flared bowl.
  - Sampling: 8 surface samples per plate (Normal) and rings about 0.9 mm apart.
  - Fissure depth scales with member radius, and plate count is fixed per tube, so thin members get
    fine, shallow bark.
- **Knots:** `knot_h(d, kr)` is a swollen rim, a sunken eye and cosine end-grain rings. The fissures
  fade within 1.5 `kr` (`knot_calm`). They are placed by a world direction (outward from the glass)
  rather than a frame angle, so they never eat into the glass gap.
- **Twigs:** long thin twigs read as thorns. Short blunt stubs (11–15 mm, r 3.4 → 2.5) read as
  pruned wood.
- **Height limits:** a tube's flat end cap is tilted with the path, so it reaches past the path's
  end point. End paths 1 mm below a hard limit (the first build measured 250.14 mm).
- **Design live with the user:** save after each step (glass, trunk and roots, branches, bark).
  Keep previews under about 15 s, and offer the Draft quality for live tweaking.

Design history:

1. Glass first, then trunk and roots, then branches, then bark. Each step was saved to the user's
   window.
2. The first branches looped out of a narrow trunk, leaving pockets, and the floor rim read as a
   table top. Fixed by wrapping the trunk round the branches and adding a bevelled lip that the bore
   cuts away.
3. The preview took 27 s. The nested-difference growth rings were to blame (§5.6), and fixing them
   brought it to 9 s. Knots and stubs took it to 16 s.
4. The bark first read as bricks, then as planed lumber. It became natural with plate-scale
   meander, per-column plate lengths, split plates and wider crack ramps.
5. Production: component tests were all 0/0 on the first try. The single-body build passed the
   mesh checks and the Bambu Studio slice. Only the tip height needed the 1 mm spare.

---

## 15. Branches that meet: Tangled and Chaotic Cradle Tree

Folders `art/Math Driven Pots and Vases/Tangled Cradle Tree/` and `.../Chaotic Cradle Tree/`. Both
are the Cradle Tree (§14) with its five symmetric branches replaced by a table of unique paths.
Trunk, roots, bark, knots, stubs and the growth-ring floor are unchanged.

- **Tangled:** 5 main branches wind the same way and never cross. 3 sub-branches fork off and wind
  back. Where a sub-branch meets a main branch, it arches out over it and returns to the glass.
- **Chaotic:** 5 main branches in mixed directions, 3 of which reverse partway up, plus 4
  sub-branches, 2 of them forks near the rim. Any two branches may meet. The later one arches over
  and they grow together.

The user's rules: branches may merge where they meet, planned at **10 %** of the thinner one's
thickness and never more than 30 % (25 % for Tangled). The merges tie the cage into a stronger print.

| | Tangled Cradle Tree | Chaotic Cradle Tree |
|---|---|---|
| Branches | 5 main + 3 sub; 1 main fork above the rim | 5 main (3 reverse) + 4 sub, 2 of them forks at the rim |
| Meetings | 6 arches, merge 6–21 % | 4 arches, merge 7–14 % (largest empty sector around the glass 69–99° at every height) |
| Size | 156.4 × 136.8 × 248.8 mm | 156.4 × 142.6 × 249.1 mm |
| Wood | 337 464 triangles, **0 / 0** edges, 1 shell, 380.9 cm³ | 327 802 triangles, **0 / 0** edges, 2 shells (the second a 4-triangle, zero-volume pocket inside a merge), 374.6 cm³ |
| Past 60° | **0.04 %** above the bottom 1 cm; bottom 1 cm 0.12 % | **0.04 %**; bottom 1 cm 0.12 % |
| Past 45° | 3.50 % (report only) | 3.65 % (report only) |
| Glass | lifts straight out: closest material 40.99 mm from the axis (bore 41.00) | same |
| Climb | ≥ 37° | ≥ 38° |
| Bambu Studio slice (H2C, 35 % infill) | no warnings; 8 h 32 min; 236 g | no warnings; 8 h 21 min; 232 g |
| Render | 21 min 37 s | 21 min 20 s |

### 15.1 Techniques

- **One table row per branch.** Rows hold the angle at the floor, turn rate(s), reversal height,
  radius scale, tip drop, lean, and meander amplitude, wavelength and phase. Sub-branches also name
  their parent and fork height. Build one `members` list, mains first, and write every function
  over the member index.
- **Reversing a turn smoothly.** Integrate a smoothstep between the two rates:
  `ismooth(u) = u<=0 ? 0 : u<1 ? u³ − u⁴/2 : u − 0.5`, and the angle offset is
  `(r2 − r1) · W · ismooth((z − (zc − W/2)) / W)` with W = 40 mm. The direction eases through
  vertical with a bend radius around 40 mm. Subtract the term's value at the reference height so a
  sub-branch starts exactly on its parent.
- **Meetings, not just crossings.** A meeting is any local minimum, along the height, of the
  distance apart along the glass (`|Δφ| · r`) that falls below the two radii. Checking only for
  sign changes in Δφ missed a fork running alongside a branch (24 %).
- **Arch height** at a meeting: the later branch moves out radially until the two centrelines are
  `r1 + r2 − 2 · merge · min(r1, r2)` apart, allowing for the distance apart along the glass at
  each height. Take the largest need within ±12 mm of the meeting, divided by the Gaussian falloff
  (half-width 20 mm). Sized only at the meeting point, one arch still merged 31 % a few mm before
  it, where the two were converging.
- **Resolve in order.** Build the meeting lists recursively (`build(i, acc)`). Branch i sees the
  final, arched radius of every earlier branch, so an arch over an arched branch lands correctly.
  Avoid stacking: a sub-branch forking 5 mm before an arch over its own parent needed an 18 mm
  hump. Move the fork away from existing meetings.
- **Forks are members too.** A separate "fork above the rim" routine sat outside the meeting
  system and ran into a neighbour (67 % overlap). Model forks as sub-branches that start near the
  rim.
- **Check with the real tube sizes:** render `part="paths"` (every member's centreline and radii
  as echo lines) and run `tools/member_clearance.py --limit 0.30`. It takes seconds, while the
  meshes take minutes. Then full-render each merging pair on its own (component tests, §6.1).
- **Coverage search.** Random directions bunched the branches into two bundles, leaving a 156°
  empty sector. A Python copy of the angle functions (checked to match OpenSCAD at every height)
  scored 24 000 random tables. The score was the largest empty sector at every height, penalised
  for contact below the arch zone, fewer than 6 or more than 12 meetings, and stacked meetings. The
  best table cut the sector to 100°. Keep the search per design; the angle model is its only
  dependency.

### 15.2 Traps found

| Symptom | Cause | Fix |
|---|---|---|
| A preview that never ends and 38 MB of `cross()` / `undefined` warnings | a knot and twig placement helper with an **inverted range**: forks near the rim start above `glass_top − 10`, so the candidate heights fell before the branch's start. The negative `t` indexed outside the path, which gave NaN geometry | `pick()` returns `[]` when `z1 <= z0` and keeps only heights inside `[z0, z1)` |
| Heights 250.24 and 250.49 mm against a 250 mm limit | a leaning tip's end cap reaches up to r · sin(lean) past its path end; a 1 mm spare was too little | `tip_spare = 2.5` |
| An extra shell of 4–14 triangles and zero volume | two bark textures meeting trap a sealed pocket inside the merge | harmless; the Bambu slice has no warnings |
| A pair test shows 2 shells but the members were meant to merge | the same pocket, not a gap: list the shells with their volumes before worrying | — |


---

## 16. Grand Chaotic Tree: a tree that grows around the glass

Folder `art/Math Driven Pots and Vases/Grand Chaotic Tree/`. A bigger glass (96 × 170 mm) held 10 cm
up in a big rooted tree, 32 cm tall. It keeps the Chaotic approach (unique paths, branches that
arch over each other and merge about 10 %), but the tree is built like a real one:

- **3 → 7 → 13.** The trunk splits into 3 limbs, the limbs into 7 branches and those into 13.
- **No floor and no cuts.** The wood grows against the glass like a tree around an obstacle.
- **The glass stands on the limbs.** The three limbs pass under its foot, which presses their tops flat.
- **A buttressed base.** The trunk comes down in buttresses that run out into roots across the ground.

The user steered it through drafts: a first split that looks like a real fork, and splits at
different heights; less straight, more random and sprawling branches; a buttressed base like a
reference photo instead of a flat foot.

| Parameter | Value |
|---|---|
| Glass | 96 × 170 mm, foot rounded 2 mm, clearance 1 mm (98 mm bore); it stands at `lift` = 100 mm; rim at 270 mm; `total_h` 320 mm (the H2C prints 325) |
| Trunk | waist r 28 mm, slight flare (+4 mm) between 9 buttresses that reach 27–40 mm out over the ground from 50 mm up; turns three-lobed as the first limb parts and ends inside the limbs at the crotch (43.5 mm) |
| Roots | 9 plus 6 side roots, r 10 → 2.8 mm, 25 cm spread; each starts inside the trunk and runs down under its buttress |
| Limbs | scale 1.26–1.36 (r ≈ 16 mm at the glass bottom); they part at 28, 38 and 46 mm; the glass presses about 45 % of a limb's thickness flat at its foot |
| Branches | radius 12 mm × scale; each fork takes 59–72 % of its parent's thickness and the parent thins so the two cross-sections add up; pressed 20 % flat against the glass side; tips taper to 2.6 mm |
| Wander | three waves of unrelated length sideways (7, 3, 1.1 mm), lifting 4–9 mm off the glass in places, tips flicking 5–12 mm sideways; `wander_seed` 17 of 24 tried |
| Bark | plates 8.5 × 17 mm, fissures up to 1.5 mm (1.2 on limbs), drifting over several plates; squashed to 40 % where pressed against the glass |

**Measured on the packaged 3MF** (`build_design.py`, 2026-09-19; an H2C project):

| Check | Result |
|---|---|
| Size | 220.5 × 226.7 × 319.5 mm, standing on z = 0 (limit 320 mm) |
| Wood | 499 976 triangles, **0 / 0** edges, 724.8 cm³; 4 shells: the body and 3 sealed pockets inside it (60 mm³ where a root starts inside the trunk foot, and two of ~0 mm³ in merges) |
| Past 60° | **0.25 %** above the bottom 1 cm (top 3 cm 0.00 %); bottom 1 cm 0.04 % |
| Past 45° | 1.85 % (report only) |
| Glass | nothing inside the glass or its 1 mm clearance (closest −0.00 mm, at the side 116 mm up); **seat 1.9 cm²** of pads within one layer of 100 mm, 38.5–46.7 mm from the axis, largest gap between them 100° |
| Branches | 6 meetings, merge 10–13 %; climb ≥ 35°; tightest bend 1.3 × the tube radius |
| Bed contact | 113.5 cm² |
| Bambu Studio slice (H2C, 0.20mm Standard, 35 % infill) | **no warnings**; 13 h 57 min; **430 g** |
| Render | 23 min 28 s as one body; components 20 s – 6 min |

### 16.1 Techniques

- **The glass as an obstacle, not a cut.** Push every smooth tube vertex out of the glass envelope
  (a bore cylinder from the floor height up, its foot rounded like the glass's). Then cut the bark
  into the flattened face, away from the glass. A boolean cut would leave flat facets. The push is
  a smooth maximum of the signed distance and 0 (k = 2.5 mm), so the flat face blends into the round
  tube.
  - **Direction and distance come from two shapes.** The push direction comes from the same
    envelope with a much rounder foot (12 mm). The distance is the exit along that direction
    through the true envelope (foot 3 mm). With the true shape's own normal, the direction flips at
    the foot corner and folds the tube.
  - **The press is fine up to about half the tube.** Keep the centreline outside the envelope.
- **A glass standing on branches.** Choose each limb's rise so the glass bottom presses its top
  flat under the foot. Check, per limb: the pad's radial band (38–46 mm), the deepest press, and
  that no vertex is left inside the envelope. `mesh_check.py --foot-r` checks the finished mesh, and
  the three pads must leave no gap of 180° or more.
- **A limb profile with bounded curvature.** Smoothstep ease-outs bend hardest right at the start:
  on a 16 mm limb the bend was tighter than the limb (0.94×), which folds the tube. A trapezoid
  speed profile works: speed rises linearly, holds, falls linearly (`trap(u, a, d)`). Its
  curvature is `2/a · Δρ/Δz²`, not `6 · Δρ/Δz²`. A grid search over start height, end height,
  acceleration and deceleration found profiles that keep bend ≥ 1.25× the radius, climb ≥ 37° and
  a 7–9 mm pad.
- **A fork that looks like a fork.** The trunk is a radial surface: a smooth maximum of a fading
  core and each limb's cross-section, i.e. the far side of the limb's circle seen from the axis.
  The fillet narrows to nothing at the crotch, where the loft ends 3 mm inside the limbs. This
  needs every limb to contain the axis at the crotch; compute `crotch_z` from that.
  - **Split heights.** Give each limb its own parting height: the first limb to part sets the
    crotch, and the others go on as one fused stem and part higher.
  - **Hide the trunk deeper than the limbs' bark.** The trunk must sink more than the limbs' fissure
    depth (3 mm against 1.2 mm), or its bark shows through their fissures as a ring.
  - **Buttresses go on the core.** Add them to the core, not the whole trunk, so they fade out
    where the limbs take over.
- **Buttresses.** Each is an angular Gaussian ridge on the trunk radius, `reach · f^2.3` with f
  rising from 0 at `buttress_h` to 1 at the ground. Its width narrows from 26° to 9° going down,
  so the flare speeds up towards the ground, like a real root flare. A flaring radial surface only
  ever faces up and out, so it never overhangs. The roots start inside the trunk and run down under
  their ridge's crest (`root_zc`), so they come out of the buttress at its foot.
- **Wander without breaking the layout.** Wander is added on top of the searched layout: sideways
  mm converted to degrees at the glass radius, and radial lift-off, with a 60 mm fade-in. Any wander
  changes the meetings, so treat its seed as a search dimension. `wander_seed` scores each seed on
  worst merge, climb, arch height, stacked meetings and tightest bend over the tube radius; 24
  seeds took about 1 minute each, 6 at a time.
- **Twigs that leave their own branch.** A twig placed by a world direction ran into its own branch
  where the branch swung out. Point each twig along its branch's heading plus outward, and to the
  side the branch is not moving to, climbing ≥ 45°. Place twigs only where no other member is
  within 14 mm, no arch or fork is within 40 mm, and the branch doesn't swing out over the twig's
  first 22 mm.

### 16.2 Traps found

| Symptom | Cause | Fix |
|---|---|---|
| Bend tighter than the limb (0.94×) at the start of its rise | smoothstep's curvature peaks at the ends | trapezoid speed profile |
| Bend of 11 mm on a 13 mm limb just above a fork | the centreline follows the radius (`hug_r`), and the fork thinned the parent over 16 mm | thin over 40 mm (10 below to 30 above the fork) |
| Tips climbing 22–25° | lean and sideways flick together on a short tip | scale both by the room above the rim (`min(1, L/55)`) |
| A ring of trunk bark round the limbs where the trunk ends | the trunk sat 0.6–1.4 mm inside the limbs, less than their 1.2 mm fissures; the buttresses, added to the whole trunk, fade slowly and pushed it further out | sink the trunk 3 mm inside, add the buttresses to the core only, vary the handover height with angle |
| A flat-topped "sleeve" at a root's start | the root started too high and too far out, its end cap outside the trunk | start 12 mm inside the trunk foot, lower |
| Only 0.1 cm² of pad at the glass height | full-depth bark on the pressed face left only the plate tops there | bark squashed to 40 % where pressed; count pad faces within one 0.25 mm layer |
| **Open:** the slice preview shows top-surface fill on the side of the trunk at the fork | near-level shelves (13 cm² flatter than 37°, 20–35 mm up) where the trunk core fades out faster than the height rises, plus a root start near the surface | not fixed in this design yet ([TODO.md](TODO.md)); the Wild Chaotic Tree fixes it (§17.1) |

---

## 17. Wild Chaotic Tree: seamless joins

Folder `art/Math Driven Pots and Vases/Wild Chaotic Tree/`. The Grand Chaotic Tree (§16) grown for
the 80 × 130 mm glass, with its own chaotic layout. It is the first design where the trunk,
buttresses, roots and limbs meet without visible seams, which fixes the open issue in §16.2 and
[TODO.md](TODO.md).

| Parameter | Value |
|---|---|
| Scale | every size × 80/96 = 0.833: Customizer values set directly, fixed lengths in the code multiplied by `sc = glass_d/96` |
| Glass | 80 × 130 mm, foot 2 mm, clearance 1 mm (82 mm bore); stands at `lift` = 83 mm; rim 213 mm; `total_h` 267 mm |
| Layout | new 3 → 7 → 13 search (`wild_search.py`, fork heights scaled by the glass height, 130/170): largest empty sector 97°, seat 126°; `wander_seed` 29 of 32 tried |
| Limbs | start at 7 mm, 5.8 mm off the axis, deep inside the trunk; part at 16, 24 and 32 mm; crotch 34 mm |
| Base | 9 buttresses (reach 22–33 mm, from 30 mm up, below the fork), 9 roots plus side roots over 208 mm |
| Calmer than the Grand tree | the shorter glass turns the same angle per glass height 9 % faster sideways, which pushed tips and arches below 30°; wander 0.85, and tip lean and flick at full size only with 58 mm of room above the rim |

**Measured on the packaged 3MF** (`build_design.py`, 2026-09-20; an H2C project):

| Check | Result |
|---|---|
| Size | 179.2 × 197.2 × 266.0 mm, standing on z = 0 |
| Wood | 453 576 triangles, **0 / 0** edges, 394.7 cm³; 6 shells: the body and 5 sealed pockets of ~0 mm³ in merges |
| Past 60° | **0.03 %** above the bottom 1 cm; bottom 1 cm 0.05 % |
| Past 45° | 1.33 % (report only) |
| Glass | nothing inside the glass or its 1 mm clearance; **seat 1.6 cm²** of pads within one layer of 83 mm, 32.1–38.4 mm from the axis, largest gap 98° |
| Branches | 9 meetings, merge 12–26 %; climb ≥ 38°; tightest bend 1.4 × the tube radius |
| Mid-air | `floating_check.py`: **0** regions (the first build had 1, §17.2) |
| Bed contact | 75.0 cm² |
| Bambu Studio slice (H2C, 0.20mm Standard, 35 % infill) | **no warnings**; 9 h 32 min; **249 g** |
| Render | 21 min 07 s as one body |

### 17.1 Techniques: defining the contours of interference

A seam shows wherever one separately built solid pokes through another. Two things show at the
crossing: the crease, because the surfaces meet at an angle, and the change of bark, because each
solid has its own texture. Both are fixed by deciding where each handover happens and designing the
two surfaces to match there.

- **One skin for trunk, buttresses and root bases.** The trunk's radial function is a smooth maximum
  (k = 10 mm) of the core, the buttresses and a copy of each root's base (`root_band`), i.e. the
  lying, tapering cylinder seen from the axis.
  - **Placement.** The copy sits inside the root by more than the root's bark depth, so it never shows
    through the fissures. It sinks 3.3 mm further over the last 8 mm before the foot contour
    (`root_foot`, just past the buttress's foot), so the fillet fades out before the copy ends.
  - **Result.** The skin shows only where the smooth maximum makes the fillet between root, buttress
    and trunk, and the root tube comes out of that fillet at a shallow angle.
  - **Straight to the contour.** The root is straight out to the foot contour, so the copy matches
    it; the sweep and meander start there, with the meander ramped over 60 % of the free root (a
    shorter ramp bent roots tighter than their radius).
  - **Exact far side.** The copy's far side along a ray is found by bisection (9 steps), because the
    root tapers. A fixed-point iteration overshot at grazing angles and left splinters.
- **The limb contour.** `hand_z(a)` wanders 7 mm round the trunk, 4–12 mm below the crotch. The
  limbs start deep inside the trunk (at 7 mm, 5.8 mm off the axis), so nothing of them shows below
  the contour.
  - **Crossing.** Below the contour the limb circles in the skin are 0.3 mm fuller than the limbs; over
    the 7 mm above it they sink 1.3 mm inside. So the skin covers the limbs, then hands over along a
    contour where the two surfaces are nearly parallel.
  - **What didn't work.** An inset that grows over the whole lobe zone left a ring. So did a handover
    wander that also shifted the core fade: that started the narrowing almost at the ground.
- **The same bark on both sides.** `wbark(p)` is the trunk's bark as a function of world position:
  - **Coordinates.** U is the angle round the trunk axis (with the spiral grain). V is
    (z − max(0, r − trunk_waist))/plate_len, so fissures run up the trunk, down the flare and out along
    the roots.
  - **Who wears it.** The skin always does. `bark_tube(..., wmix=function(p) ...)` blends a tube from
    `wbark` at the skin's depth into its own bark: limbs from the crotch to 17 mm above it, roots
    from the trunk to 8 mm past the foot contour.
  - **Result.** Where two surfaces cross near a join, their fissures coincide.
- **No shelves.** The core narrows at a fixed rate (0.7 mm/mm with a soft start) instead of a
  smoothstep. The buttresses stop below the fork (30 mm), so the two flares don't add up.
  - **Check.** Scan the exposed skin (outside every limb circle) for places that narrow faster than
    1 mm per mm of height. In the handover: 16 samples, steepest 1.44 (the Grand tree's patch was 3.4).
  - **Near the ground.** Between 10 and 18 mm the scan finds the root fillets, up to 2.1: that is the
    flare itself, like the tops of the roots.
- **Sampling.** The trunk loft needs twice the samples round (416) and rings every 0.4 mm up to
  10 mm for the root bases. A preview takes about 1.5 minutes at Normal quality; use Draft.

### 17.2 Traps found

| Symptom | Cause | Fix |
|---|---|---|
| Bambu Studio: "object ... has floating regions", and it names no position | a fork's flat end cap hanging outside its parent: the fork's **own arch**, sized for a meeting 15 mm higher, still lifted it 5.3 mm off its parent's centreline at its start | a fork's arches fade in over its first 21 mm (`bump_ramp`), and `arch_h` divides by the same ramp so the arch still clears. Check every fork: its start must sit on its parent's centreline, with its radius inside the parent's |
| Splinters along the roots at ground level | the skin's copy of a root is found by a fixed-point iteration, which oscillates where the root tapers and overshot at grazing angles | bisection (9 steps) |
| A blocky ledge where a root leaves the flare | the skin's copy ended abruptly, and the fillet bulge was cut off with it | the copy sinks a further 3.3 mm into the root over the last 8 mm, so the fillet fades out first |
| Chunky bits along the roots near the trunk | the copy sat 0.5 mm inside the root, less than the bark's 1.25 mm, so it showed through the fissures | the copy sits deeper than the bark (`band_in`) |
| Roots bending tighter than their own radius | the meander ramped in over 13 mm right after the foot contour | ramp it over 60 % of the free root |
| Tips climbing 25° on a design scaled down from a bigger one | a shorter glass turns the same angle per glass height faster sideways, so lean, flick, turn and wander add up to more | tip lean and flick scaled by the room above the rim, wander 0.85 |
