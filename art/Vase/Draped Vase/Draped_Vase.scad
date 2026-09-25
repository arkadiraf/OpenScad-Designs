// DRAPED VASE - a holder for a straight glass vase (100 x 200 mm), after a glossy
// blue vase that looks like heavy cloth draped round a column: soft vertical folds
// that meander and twist as they rise, grooves between them, and a few shallow
// hollows pressed into the surface.
// The outer surface is one closed-form radius R(phi, z) round the glass, sampled
// into rings and lofted as one polyhedron; the glass bore is subtracted from it.
// Because R is single-valued there are no undercuts, and every fold rises far
// steeper than the 60 degree overhang limit: it prints without supports.
// sketch = true samples coarsely: use it while the shape is being found.
// Step 1 is the glass; every holder dimension is derived from it.
// All dimensions in mm. OpenSCAD trigonometry uses DEGREES.

/* [Output] */
part = "assembly"; // [assembly, body, glass, none]
// Coarse sampling, for finding the shape
sketch = false;
show_glass = true;

/* [1 - Real glass vase] */
glass_d = 100;          // outer diameter of the glass
glass_h = 200;          // height of the glass
glass_wall = 3;         // preview only
glass_bottom = 6;       // preview only
glass_foot = 3;         // rounding of the glass bottom edge (preview only)

/* [2 - Fit] */
clearance = 1;          // radial gap round the glass (bore radius = glass_d / 2 + clearance)
floor_h = 8;            // glass floor above the bed (house rule: >= 7.5)
rim_above = 10;         // how far the holder rim stands above the glass rim (hides the glass)

/* [3 - Body] */
r_mean = 59;            // outer radius at mid height, before the folds
belly = 5;              // extra radius low down (the body swells a little below the middle)
belly_z = 0.35;         // where the swelling peaks, as a share of the height
top_in = 3;             // narrower at the top by this much
min_wall = 5;           // thinnest wall outside the bore, in the deepest groove
rim_round = 6;          // rounding of the top outer edge
rim_min = 2.4;          // narrowest flat rim left at the top
rim_calm = 0.8;         // share of the fold depth left at the rim

/* [4 - Folds] */
seed = 3;               // a different seed gives a differently draped vase
folds = 9;              // large folds round the vase (ridges and grooves alternate)
fold_depth = 12;        // how far a large fold stands out (grooves as deep, down to min_wall)
fold_w = 21;            // half-width of a ridge, degrees (grooves are narrower)
meander = 20;           // how far a fold snakes from side to side, degrees
waves = 1.05;           // snaking waves over the height
twist = 18;             // how far the folds turn from bottom to top, degrees
small_folds = 9;        // thin creases between the large folds
small_depth = 2.5;
small_w = 5;            // degrees
hollows = 6;            // shallow pressed-in hollows
hollow_depth = 11;
hollow_size = 25;       // mm, radius of a hollow

/* [5 - S-folds] */
// Local folds, each with its own start and end: the centreline swings once
// left and once right (an S), the fold swells in the middle and fades out at
// both ends, and a shadow groove runs along one side of it, as in cloth.
s_folds = 12;
s_depth = 11;           // how far an S-fold stands out at its middle
s_width = 10;           // mm, half-width of the ridge
s_groove = 0.8;         // depth of the shadow groove, as a share of the ridge
s_swing = 16;           // mm, how far the S swings to each side
s_len_min = 0.5;        // shortest S-fold, as a share of the height
s_len_max = 0.95;       // longest

/* [Hidden] */
bore_r = glass_d / 2 + clearance;
H = floor_h + glass_h + rim_above;          // height of the holder
N_body = sketch ? 80 : 240;                    // rings below the rim rounding
N_rim = sketch ? 4 : 10;                       // rings in the rim rounding
M = sketch ? 120 : 360;                        // points per ring
$fn = sketch ? 96 : 240;

// ---------------------------------------------------------------- library
function frac(x) = x - floor(x);
function rnd(a, b = 0, c = 0) = frac(sin(a * 127.1 + b * 311.7 + c * 74.7 + seed * 19.3) * 43758.5453);
function vsum(v) = len(v) == 0 ? 0 : v * [for (x = v) 1];
function adiff(a, b) = let(d = a - b) d - 360 * round(d / 360);         // -180..180
function smax(a, b, k) = (a + b + sqrt((a - b) * (a - b) + k * k)) / 2;  // smooth max
function gauss(x) = exp(-x * x);

// Closed solid through rings; each ring counter-clockwise seen from above.
module loft(rings) {
    n = len(rings); S = len(rings[0]);
    pts  = [for (ring = rings) each ring];
    side = [for (i = [0:n - 2]) for (j = [0:S - 1])
            let(j2 = (j + 1) % S, a = i * S + j, b = (i + 1) * S + j, c = (i + 1) * S + j2, d = i * S + j2)
            each [[a, b, c], [a, c, d]]];
    caps = [[for (j = [0:S - 1]) j], [for (j = [S - 1:-1:0]) (n - 1) * S + j]];
    polyhedron(points = pts, faces = concat(side, caps), convexity = 10);
}

// ---------------------------------------------------------------- step 1: the glass
module glass_vase() {
    color([0.75, 0.88, 1, 0.35]) translate([0, 0, floor_h]) difference() {
        hull() {
            translate([0, 0, glass_foot]) rotate_extrude() translate([glass_d / 2 - glass_foot, 0]) circle(glass_foot);
            translate([0, 0, glass_foot]) cylinder(d = glass_d, h = glass_h - glass_foot);
        }
        translate([0, 0, glass_bottom]) cylinder(d = glass_d - 2 * glass_wall, h = glass_h);
    }
}

// ---------------------------------------------------------------- step 2: the drape
// The silhouette before the folds: a slight swelling low down, narrower at the top.
function base_r(t) = r_mean + belly * pow(sin(180 * min(1, t / (2 * belly_z))), 2) * (t < 2 * belly_z ? 1 : 0)
                     + belly * 0.35 * sin(180 * t) - top_in * t * t;

// Large folds at height t: [centre angle, signed depth, half-width]. Ridges and
// grooves alternate; each snakes with its own waves and swells and thins as it rises.
function fold_set(t) = [for (k = [0:folds - 1]) let(
        ridge = k % 2 == 0,
        phi0 = 360 * k / folds + 18 * (rnd(k, 1) - 0.5),
        // a sway shared by neighbouring folds (so they flow side by side, like cloth)
        // plus a smaller one of their own
        c = phi0 + twist * t
            + meander * (0.85 + 0.3 * rnd(k, 2)) * sin(360 * waves * t + 360 * rnd(0, 4) + 50 * k / folds)
            + meander * 0.12 * sin(360 * waves * (1.6 + 0.8 * rnd(k, 3)) * t + 360 * rnd(k, 5)),
        a = fold_depth * (ridge ? 1 : -1)
            * (0.45 + 0.35 * sin(360 * (0.6 + 0.7 * rnd(k, 6)) * t + 360 * rnd(k, 7))
                   + 0.2 * sin(360 * (1.8 + 0.8 * rnd(k, 10)) * t + 360 * rnd(k, 17))),
        w = fold_w * (ridge ? 1 : 0.45) * (0.7 + 0.6 * rnd(k, 8)) * (0.85 + 0.25 * sin(360 * t * 0.8 + 360 * rnd(k, 9))))
    [c, a, w]];

function crease_set(t) = [for (k = [0:small_folds - 1]) let(
        c = 360 * (k + 0.5) / small_folds + 25 * (rnd(k, 11) - 0.5) + twist * 1.2 * t
            + meander * 0.9 * sin(360 * waves * t + 360 * rnd(0, 4) + 50 * (k + 0.5) / small_folds)
            + meander * 0.1 * sin(360 * waves * 1.7 * t + 360 * rnd(k, 12)),
        a = small_depth * (rnd(k, 13) < 0.5 ? 1 : -1)
            * max(0, sin(180 * (t - 0.1 * rnd(k, 14)) / (0.7 + 0.3 * rnd(k, 15)))),
        w = small_w * (0.7 + 0.6 * rnd(k, 16)))
    [c, a, w]];

// S-folds at height z: [centre angle, depth, half-width (deg), groove side];
// depth 0 outside a fold's own height range.
s_table = [for (k = [0:s_folds - 1]) let(
        L = H * (s_len_min + (s_len_max - s_len_min) * rnd(k, 31)),
        zc = H * (0.12 + 0.76 * frac(k * 0.618 + 0.25 * rnd(k, 32))),   // spread evenly up the height
        z0 = zc - L / 2)
    [360 * (k + 0.6 * rnd(k, 33)) / s_folds,      // where it stands round the vase
     z0, L,
     s_depth * (0.65 + 0.35 * rnd(k, 34)),
     (rnd(k, 35) < 0.5 ? 1 : -1),                  // which way the S turns
     (rnd(k, 36) < 0.5 ? 1 : -1),                  // which side the groove is on
     0.8 + 0.4 * rnd(k, 37)]];                     // width factor
deg_per_mm = 180 / (PI * r_mean);
function s_set(z) = [for (f = s_table) let(s = (z - f[1]) / f[2])
    if (s > 0 && s < 1)
        [f[0] + f[4] * s_swing * deg_per_mm * sin(360 * s) + 8 * (s - 0.5),
         f[3] * pow(sin(180 * s), 2), s_width * f[6] * deg_per_mm, f[5]]];
function s_profile(d, p) = p[1] * (gauss(d / p[2]) - s_groove * gauss((d - p[3] * 1.5 * p[2]) / (0.75 * p[2])));

// Hollows: [angle, height, depth]
hollow_set = [for (k = [0:hollows - 1])
    [360 * (k + rnd(k, 21)) / hollows, H * (0.2 + 0.62 * rnd(k, 22)), hollow_depth * (0.6 + 0.4 * rnd(k, 23))]];

// The folds calm down towards the rim, so the opening stays round-ish.
function rim_fade(t) = 1 - (1 - rim_calm) * pow(max(0, (t - 0.8) / 0.2), 1.5);

function drape_r(phi, z, F, C, SF) = let(
        t = z / H,
        f = rim_fade(t) * vsum([for (p = F) p[1] * gauss(adiff(phi, p[0]) / p[2])]),
        c = vsum([for (p = C) p[1] * gauss(adiff(phi, p[0]) / p[2])])
            + vsum([for (p = SF) s_profile(adiff(phi, p[0]), p)]),
        h = vsum([for (p = hollow_set) let(dx = adiff(phi, p[0]) * PI / 180 * r_mean, dz = z - p[1])
                  -p[2] * gauss(sqrt(dx * dx + dz * dz) / hollow_size)]))
    smax(base_r(t) + f + c + h, bore_r + min_wall, 6);   // deep grooves bottom out softly

// Heights of the rings: even up the body, then a quarter circle round the rim.
z_list = concat([for (i = [0:N_body]) (H - rim_round) * i / N_body],
                [for (k = [1:N_rim]) H - rim_round + rim_round * sin(90 * k / N_rim)]);
rim_k = concat([for (i = [0:N_body]) 0], [for (k = [1:N_rim]) 1 - cos(90 * k / N_rim)]);

module drape_outer() {
    loft([for (i = [0:len(z_list) - 1]) let(z = z_list[i], t = z / H, F = fold_set(t), C = crease_set(t), SF = s_set(z))
          [for (j = [0:M - 1]) let(phi = 360 * j / M + 0.37, r0 = drape_r(phi, z, F, C, SF),
                                   r = r0 - min(rim_round, r0 - bore_r - rim_min) * rim_k[i])
               [r * cos(phi), r * sin(phi), z]]]);
}

module body() {
    difference() {
        drape_outer();
        translate([0, 0, floor_h]) cylinder(r = bore_r, h = H);   // open through the top
    }
}

// ---------------------------------------------------------------- summary
echo(str("Draped vase holder: glass ", glass_d, " x ", glass_h, " mm, bore d ", 2 * bore_r,
         " mm, floor ", floor_h, " mm, holder ", H, " mm tall, its rim ", rim_above,
         " mm above the glass, outer r ~", r_mean, " +- ", fold_depth, " mm"));

// ---------------------------------------------------------------- part selector
if (part == "assembly") {
    color("#0056B8") body();
    if (show_glass) glass_vase();
}
if (part == "body") body();
if (part == "glass") glass_vase();
