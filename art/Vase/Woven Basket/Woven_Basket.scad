// WOVEN BASKET - a holder for a straight glass vase (80 x 130 mm): a flat-reed
// basket woven round the glass. Flat vertical stakes stand in a round base; flat
// weavers go over one stake and under the next, each row the other way round, so
// every stake shows as a dash in every second row. A lashed rim closes the top and
// a two-strand rope runs round the foot.
// Zero clearance: the weavers' inner faces are pressed onto the glass, so the bore
// cuts small flats on them and the glass is held snug by the wall and the rim.
// Printable without supports: stakes are vertical, the weavers are pointed lenses in
// section (tips well under 60 deg from vertical), the rim sits in the top row on a
// V-shaped underside, and the rope's overhang is inside the bottom centimetre.
// Step 1 is the glass; every holder dimension is derived from it.
// All dimensions in mm. OpenSCAD trigonometry uses DEGREES.

/* [Output] */
part = "assembly"; // [assembly, frame, weave, accent, glass, none]
// Coarse sampling and no rim lashing, for finding the shape
sketch = false;
show_glass = true;

/* [1 - Real glass vase] */
glass_d = 80;           // outer diameter of the glass
glass_h = 130;          // height of the glass
glass_wall = 2.5;       // preview only
glass_bottom = 5;       // preview only
glass_foot = 3;         // rounding of the glass bottom edge (preview only)

/* [2 - Fit] */
clearance = 0;          // radial gap round the glass (bore radius = glass_d / 2 + clearance)
weave_press = 0.3;      // how far the weavers' inner faces reach into the bore (cut flat there)
floor_h = 8;            // glass floor above the bed (house rule: >= 7.5)
rim_above = 2;          // basket rim above the glass rim

/* [3 - Stakes] */
stakes = 16;            // vertical stakes round the basket (even, for a plain weave)
stake_w = 7;            // width of a flat stake
stake_t = 2.4;          // its thickness

/* [4 - Weavers] */
weave_h = 9;            // height of a flat weaver
weave_t = 3;            // its thickness in the middle
row_overlap = 1.6;      // rows overlap this much in height (about; the pitch fits the height)
stake_grip = 0.4;       // weavers pressed into the stakes, so the wall is one body
weave_square = 1.8;     // 0 = sine wave; higher = flatter where a weaver crosses a stake
lens_n = 2.2;           // weaver section: w = t/2 (1 - |u|^n); higher = fuller, blunter edges
// Rows in the accent colour, counted from 0 at the bottom; negative counts from the top
accent_rows = [2, 3, -4, -3];

/* [5 - Rim] */
rim_h = 13;             // height of the rim band
rim_out = 1;            // how far the rim stands out past the weave
rim_v = 40;             // half-angle of the rim's V underside, degrees from vertical (< 55)
lash_pitch = 6;         // spacing of the lashing wraps round the rim
lash_depth = 0.6;

/* [6 - Rope foot] */
rope_strand = 2.5;      // radius of each of the two strands
rope_offset = 2;        // strand centre off the rope axis
rope_pitch = 14;        // length of one full twist
rope_cut = 0.9;         // how much of the rope is cut off by the bed

/* [Hidden] */
bore_r = glass_d / 2 + clearance;
A = stake_t / 2 + weave_t / 2 - stake_grip;            // weaver swing in and out of the stakes
R = bore_r - weave_press + A + weave_t / 2;            // stake circle
r_in = R - A - weave_t / 2;                            // innermost weaver face
r_out = R + A + weave_t / 2;                           // outermost weaver face
top_z = floor_h + glass_h + rim_above;
// Weaver edges curl in towards the stake circle, so at a stake they end 0.3 mm
// inside it, and between stakes each row's bottom edge lies on the row below
// (a straight lens section leaves the edge bridging ~17 mm between midspans).
tip_pull = 1 - (stake_t / 2 - 0.3) / A;
phi0 = 180 / stakes + 0.7;                             // stake angles kept off exact multiples of 90

rim_ri = min(r_in, bore_r) - 0.5;                      // inner lip, cut away by the bore
rim_ro = r_out + rim_out;
rim_rm = (rim_ri + rim_ro) / 2;
rim_rr = (rim_ro - rim_ri) / 2;                        // round top
rim_zt = top_z - rim_h;                                // tip of the V
rim_vi = (rim_rm - rim_ri) / tan(rim_v);               // height of the V
lash_n = round(2 * PI * rim_rm / lash_pitch);          // whole number of wraps

z_c0 = floor_h - 1 + weave_h / 2;                      // first row: bottom edge 1 mm into the base
z_last = rim_zt + 1.5;                                 // last row: its centre just above the rim's tip
rows = round((z_last - z_c0) / (weave_h - row_overlap)) + 1;
pitch = (z_last - z_c0) / (rows - 1);
acc = [for (a = accent_rows) a < 0 ? rows + a : a];

rope_R = r_out + 0.5;                                  // rope axis
rope_z = rope_offset + rope_strand - rope_cut;
rope_tw = round(2 * PI * rope_R / rope_pitch);         // whole number of twists

M_w = sketch ? 128 : 320;                              // samples round a weaver
K_w = sketch ? 4 : 7;                                  // samples down each face of a weaver
M_r = sketch ? 160 : 12 * lash_n;                      // samples round the rim
M_f = sketch ? 240 : 720;                              // samples round the rope
S_f = sketch ? 8 : 16;

assert(stakes % 2 == 0, "stakes must be even for a plain weave");
assert(rim_v < 55, "rim V steeper than the overhang rule allows");
assert(rim_h >= rim_vi + rim_rr + 1, "rim_h too small for the V and the round top");
assert(stake_w < 2 * PI * R / stakes - 4, "stakes too wide for their spacing");

// ---------------------------------------------------------------- library
function unit(v) = v / norm(v);
function cyl(rho, phi, z) = [rho * cos(phi), rho * sin(phi), z];
function tanh(x) = let(e = exp(2 * x)) (e - 1) / (e + 1);
function has(v, x) = len([for (a = v) if (a == x) 1]) > 0;

// Closed ring of rings (a torus): each ring counter-clockwise seen from ahead,
// looking back down the path; the last ring joins the first, so there are no caps.
module ring_loft(rings) {
    n = len(rings); S = len(rings[0]);
    pts  = [for (ring = rings) each ring];
    side = [for (i = [0:n - 1]) for (j = [0:S - 1])
            let(i2 = (i + 1) % n, j2 = (j + 1) % S,
                a = i * S + j, b = i2 * S + j, c = i2 * S + j2, d = i * S + j2)
            each [[a, b, c], [a, c, d]]];
    polyhedron(points = pts, faces = side, convexity = 10);
}

// ---------------------------------------------------------------- step 1: the glass
module glass_vase() {
    color([0.75, 0.88, 1, 0.35]) translate([0, 0, floor_h]) difference() {
        hull() {
            translate([0, 0, glass_foot]) rotate_extrude($fn = 96) translate([glass_d / 2 - glass_foot, 0]) circle(glass_foot, $fn = 24);
            translate([0, 0, glass_foot]) cylinder(d = glass_d, h = glass_h - glass_foot, $fn = 96);
        }
        translate([0, 0, glass_bottom]) cylinder(d = glass_d - 2 * glass_wall, h = glass_h, $fn = 96);
    }
}

// ---------------------------------------------------------------- step 2: the basket
// Base: a plain disc under the glass floor; the rope covers its edge. A 45 deg
// plinth under the rope carries its outer strand, which would otherwise hang
// over the bed.
module base() {
    cylinder(r = rope_R + 0.5, h = floor_h, $fn = 180);
    cylinder(r1 = rope_R + rope_offset + 0.6 * rope_strand, r2 = rope_R, h = rope_z, $fn = 180);
}

// Stakes: flat, vertical, from inside the base to inside the rim.
module stakes() {
    for (k = [0:stakes - 1]) rotate(phi0 + 360 * k / stakes)
        translate([R, 0, floor_h - 1]) linear_extrude(rim_zt + 3 - floor_h + 1)
            hull() for (s = [-1, 1]) translate([0, s * (stake_w - stake_t) / 2]) circle(d = stake_t, $fn = 20);
}

// Weavers: row j is outside stake k when j + k is even. tanh flattens the wave
// where it crosses a stake, so a weaver lies on the stake's face instead of a point.
function wave(j, phi) = let(c = cos(stakes / 2 * (phi - phi0) + 180 * j))
    weave_square > 0 ? tanh(weave_square * c) / tanh(weave_square) : c;
function row_z(j) = z_c0 + j * pitch;
function row_pt(j, phi) = cyl(R + A * wave(j, phi), phi, row_z(j));
function lens_w(u) = max(0.15, weave_t / 2 * (1 - pow(abs(u), lens_n)));
// The blunt bottom edge is tilted 45 deg (inner side raised), so no weaver has a
// flat underside: 0.3 mm of flat along every row is ~1 % of the surface past 60 deg.
function lens_z(u, inner) = u * weave_h / 2 + (inner ? 0.3 * pow(max(0, -u), 12) : 0);

module weaver(j) {
    ring_loft([for (i = [0:M_w - 1]) let(
            phi = 360 * i / M_w + 0.13,
            P = row_pt(j, phi),
            T = unit(row_pt(j, phi + 0.5) - row_pt(j, phi - 0.5)),
            N = unit(cross(T, [0, 0, 1])),                          // outward, horizontal
            c = -A * wave(j, phi) * tip_pull)                       // edge curl
        concat([for (k = [0:K_w]) let(u = cos(180 * k / K_w)) P + (c * u * u + lens_w(u)) * N + [0, 0, lens_z(u, false)]],
               [for (k = [0:K_w]) let(u = -cos(180 * k / K_w)) P + (c * u * u - lens_w(u)) * N + [0, 0, lens_z(u, true)]])]);
}
module rows(accent) for (j = [0:rows - 1]) if (has(acc, j) == accent) weaver(j);

// Rim: a band with a V underside that sits in the top row, straight sides and a
// round top, wrapped with a lashing that spirals round its section.
function seg(a, b, n) = [for (i = [0:n - 1]) a + (b - a) * i / n];
rim_prof = concat(
    seg([rim_ro, top_z - rim_rr], [rim_ro, rim_zt + (rim_ro - rim_rm) / tan(rim_v)], sketch ? 2 : 4),
    seg([rim_ro, rim_zt + (rim_ro - rim_rm) / tan(rim_v)], [rim_rm, rim_zt], sketch ? 3 : 8),
    seg([rim_rm, rim_zt], [rim_ri, rim_zt + rim_vi], sketch ? 3 : 8),
    seg([rim_ri, rim_zt + rim_vi], [rim_ri, top_z - rim_rr], sketch ? 2 : 4),
    [for (i = [0:(sketch ? 7 : 16) - 1]) let(a = 180 - 180 * i / (sketch ? 7 : 16))
        [rim_rm + rim_rr * cos(a), top_z - rim_rr + rim_rr * sin(a)]]);
rim_c = [rim_rm, rim_zt + rim_h / 2];
rim_n = let(n = len(rim_prof)) [for (i = [0:n - 1]) let(
        t = rim_prof[(i + 1) % n] - rim_prof[(i + n - 1) % n], p = [t[1], -t[0]] / norm(t))
    p * (rim_prof[i] - rim_c) >= 0 ? p : -p];
function lash(phi, q) = sketch ? 0 : lash_depth * (0.5 + 0.5 * cos(lash_n * phi + 360 * q));

module rim() {
    n = len(rim_prof);
    ring_loft([for (i = [0:M_r - 1]) let(phi = 360 * i / M_r + 0.29)
        [for (k = [0:n - 1]) let(p = rim_prof[k] + lash(phi, k / n) * rim_n[k]) cyl(p[0], phi, p[1])]]);
}

// Rope foot: two strands twisted round a ring on the bed.
function strand_pt(s, phi) = let(psi = rope_tw * phi + 180 * s + 20)
    cyl(rope_R + rope_offset * cos(psi), phi, rope_z + rope_offset * sin(psi));
module strand(s) {
    ring_loft([for (i = [0:M_f - 1]) let(
            phi = 360 * i / M_f + 0.21, psi = rope_tw * phi + 180 * s + 20,
            P = strand_pt(s, phi),
            T = unit(strand_pt(s, phi + 0.2) - strand_pt(s, phi - 0.2)),
            u = [cos(psi) * cos(phi), cos(psi) * sin(phi), sin(psi)],
            N = unit(u - (u * T) * T), B = cross(T, N))
        [for (a = [0:S_f - 1]) let(b = 360 * a / S_f) P + rope_strand * (cos(b) * N + sin(b) * B)]]);
}
module rope() for (s = [0, 1]) strand(s);

// Subtract the bore (open through the top) and everything below the bed.
module trim() {
    difference() {
        children();
        translate([0, 0, floor_h]) cylinder(r = bore_r, h = top_z, $fn = 360);
        translate([0, 0, -50]) cylinder(r = 200, h = 50);
    }
}

module frame() trim() { base(); rope(); stakes(); rim(); }
module weave() trim() difference() { rows(false); stakes(); rim(); base(); }
module accent() trim() difference() { rows(true); stakes(); rim(); base(); rows(false); }

// ---------------------------------------------------------------- summary
echo(str("Woven basket: glass ", glass_d, " x ", glass_h, " mm, bore d ", 2 * bore_r,
         " mm (clearance ", clearance, ", weavers pressed ", weave_press, " mm), floor ", floor_h,
         " mm; ", stakes, " stakes at r ", round(R * 10) / 10, ", ", rows, " rows at pitch ",
         round(pitch * 100) / 100, " mm (overlap ", round((weave_h - pitch) * 100) / 100,
         "), weaver edge ", round(atan((weave_t * lens_n / 2 + 2 * A * tip_pull) / (weave_h / 2))), " deg from vertical; wall r ",
         round(r_in * 10) / 10, " - ", round(r_out * 10) / 10, ", rim to r ", rim_ro, " at z ", top_z,
         ", rope foot to r ", round((rope_R + rope_offset + rope_strand) * 10) / 10,
         ", accent rows ", acc));

// ---------------------------------------------------------------- part selector
if (part == "assembly") {
    color("#6F5034") frame();
    color("#E4BD68") weave();
    color("#9D2235") accent();
    if (show_glass) glass_vase();
}
if (part == "frame") frame();
if (part == "weave") weave();
if (part == "accent") accent();
if (part == "glass") glass_vase();
