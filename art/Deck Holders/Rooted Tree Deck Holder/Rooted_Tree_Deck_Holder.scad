// Rooted Tree Deck Holder
// ---------------------------------------------------------------------------------------------
// An upright holder for a deck of playing cards, 70 x 50 x 100 mm (width x depth x height), open
// at the top and slotted at the back so the deck can be pushed up and drawn. A copper tree grows
// on the front in relief, laid out after the reference print: the tree stands to one side, its
// braided trunk leaning out and its crown spreading over the whole upper face, and its roots run
// across over a name plaque on the other side, frame it and wrap round the corners onto the sides.
//
// Step 1 is the deck: the cavity is sized from the card and the deck thickness, and the outer box
// is the cavity plus the walls. Every tree member is a tube swept along a path written on the
// box surface in (u, z) coordinates, u being the arc length round the box from the front centre,
// so a root that runs past the corner wraps round it.
//
// Prints standing on its floor, no supports. Relief tubes are sunk into the wall by a share of
// their radius that depends on their direction, so no underside is steeper than 58 deg from
// vertical (a tube rising at 32 deg or more can stand half proud; a level one is sunk by 53 %).
//
// Colour parts: box (white), relief (copper), text (black). The plaque text is inlaid into the
// wall and stands slightly proud. An emblem of your own (SVG/DXF) can be added with logo_file.

/* [Cards] */
card_w = 63.5;          // card width, mm (poker 63.5, bridge 57)
card_h = 88.9;          // card height, mm
deck_t = 44;            // deck thickness you want to hold, mm (about 0.3 mm per card, 0.6 sleeved)
side_clear = 1.25;      // clearance each side of the card, mm

/* [Box] */
box_h = 100;            // outer height, mm
wall = 2.0;             // wall thickness, mm
floor_t = 2.0;          // floor thickness, mm
corner_r = 8;           // radius of the vertical box edges, mm (roots wrap round these)
front_clear = 2.0;      // depth clearance in front of + behind the deck, mm (total)
slot_w = 34;            // width of the back slot, mm
slot_bottom = 28;       // height of the bottom of the back slot above the bed, mm

/* [Tree] */
trunk_side = -1;        // [-1:left, 1:right] side the tree stands on; the plaque takes the other
seed = 7;               // changes the crown and the rootlets
crown_depth = 5;        // levels of forking in the crown
limb_len = 17;          // length of the first limbs, mm
limb_r = 2.8;           // radius of the trunk strands and first limbs, mm
root_r = 3.0;           // radius of the main roots at the trunk, mm
spread = 30;            // angle between sibling branches, deg
bark_depth = 0.08;      // bark ridge depth, share of the radius
twist = 9;              // bark twist, degrees per ring

/* [Plaque] */
show_text = true;
plaque_layout = "stacked";   // [stacked, side_by_side]
line_en1 = "TEL AVIV";
line_en2 = "UNIVERSITY";
line_he1 = "אוניברסיטת";
line_he2 = "תל אביב";
text_size = 3.6;        // cap height-ish, mm
font_en = "Liberation Sans:style=Bold";
font_he = "DejaVu Sans:style=Bold";
logo_file = "";         // optional emblem (SVG or DXF), placed above the text
logo_w = 34;            // emblem width, mm
text_proud = 0.4;       // how far the text stands out of the wall, mm
text_inlay = 0.6;       // how deep it is inlaid, mm

/* [Output] */
part = "assembly";      // [assembly, box, relief, text, none, paths]
sketch = false;         // coarse tubes, no bark: for fast previews
show_deck = false;      // preview only: the deck in place

/* [Hidden] */
box_w = card_w + 2 * side_clear + 2 * wall;
box_d = deck_t + front_clear + 2 * wall;
rc = corner_r;
sides = sketch ? 8 : 15;
ridges = 5;
seg = sketch ? 4 : 2.2;                      // ring spacing along members, mm
K_OVER = pow(sin(58), 2);                   // overhang limit: steepest underside 58 deg

fa = box_w / 2 - rc;                        // half of the flat front
fq = rc * PI / 2;                           // corner arc length
fb = box_d - 2 * rc;                        // flat side length
u_side_end = fa + fq + fb;                  // where the side ends at the back corner

z_base = 40;                                // where the roots leave the trunk
strand_top = [55, 68, 61];                  // where each trunk strand turns into a limb
function trunk_u(z) = trunk_side * lerp(7, 12, clamp((z - z_base) / 28, 0, 1));   // leans outwards
strand_amp = 2.9;
strand_wave = 30;

plaque = trunk_side < 0 ? [[-11, 29], [5, 32]] : [[-29, 11], [5, 32]];   // [u], [z] under the roots

// ---------------------------------------------------------------- library
function unit(v) = v / norm(v);
function lerp(a, b, t) = a + (b - a) * t;
function clamp(x, a, b) = min(b, max(a, x));
function smooth(a, b, x) = let(t = clamp((x - a) / (b - a), 0, 1)) t * t * (3 - 2 * t);
function rnd(a, b = 0, c = 0) = let(x = sin(a * 127.1 + b * 311.7 + c * 74.7) * 43758.5453) x - floor(x);
function dir(a) = [sin(a), cos(a)];                    // 2D (u, z), a from vertical, + towards +u
function ang(v) = atan2(v[0], v[1]);
function tangents(P) = [for (i = [0:len(P) - 1])
    unit(i == 0 ? P[1] - P[0] : i == len(P) - 1 ? P[i] - P[i - 1] : P[i + 1] - P[i - 1])];
function first_normal(t) = unit(cross(t, abs(t[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0]));
function transport(T, i, prev) = i >= len(T) ? [] :
    let(n = unit(prev - (prev * T[i]) * T[i])) concat([n], transport(T, i + 1, n));

module loft(rings) {
    n = len(rings); S = len(rings[0]);
    pts  = [for (ring = rings) each ring];
    side = [for (i = [0:n - 2]) for (j = [0:S - 1])
            let(j2 = (j + 1) % S, a = i * S + j, b = (i + 1) * S + j, c = (i + 1) * S + j2, d = i * S + j2)
            each [[a, b, c], [a, c, d]]];
    caps = [[for (j = [0:S - 1]) j], [for (j = [S - 1:-1:0]) (n - 1) * S + j]];
    polyhedron(points = pts, faces = concat(side, caps), convexity = 10);
}

module sweep(P, R, phase = 0) {
    T = tangents(P);
    N = transport(T, 0, first_normal(T[0]));
    dep = sketch ? 0 : bark_depth;
    loft([for (i = [0:len(P) - 1]) let(B = cross(T[i], N[i]))
          [for (j = [0:sides - 1]) let(a = 360 * j / sides,
                                        r = R[i] * (1 + dep * cos(ridges * a + phase + twist * i)))
               P[i] + r * (cos(a) * N[i] + sin(a) * B)]]);
}

// ---------------------------------------------------------------- the box surface
// u = arc length from the front centre, + towards +x. Returns [[x, y], outward normal].
function surf(u) =
    let(s = u < 0 ? -1 : 1, v = abs(u),
        r = v <= fa ? [[v, -box_d / 2], [0, -1]]
          : v <= fa + fq ? let(t = (v - fa) / rc * 180 / PI)
                [[fa + rc * sin(t), -box_d / 2 + rc - rc * cos(t)], [sin(t), -cos(t)]]
          : [[box_w / 2, -box_d / 2 + rc + (v - fa - fq)], [1, 0]])
    [[s * r[0][0], r[0][1]], [s * r[1][0], r[1][1]]];

// sink share from the direction: cos^2 of the climb is u'^2 / |t|^2
function dir_sink(t) = let(c2 = t[0] * t[0] / max(1e-9, t * t)) c2 <= K_OVER ? 0 : sqrt(1 - K_OVER / c2);

// member = [points (u, z), radii, base sink shares]; to 3D tube centres
function member3d(m) = let(P = m[0], R = m[1], SB = m[2], T = tangents(P))
    [for (i = [0:len(P) - 1]) let(f = surf(P[i][0]), s = max(SB[i], dir_sink(T[i])), c = s * R[i])
        [f[0][0] - f[1][0] * c, f[0][1] - f[1][1] * c, P[i][1]]];

// ---------------------------------------------------------------- paths
function bez(p0, p1, p2, t) = (1 - t) * (1 - t) * p0 + 2 * (1 - t) * t * p1 + t * t * p2;
function bezd(p0, p1, p2, t) = 2 * (1 - t) * (p1 - p0) + 2 * t * (p2 - p1);

// Catmull-Rom through control points, k samples per span
function cr(C, k) = [for (i = [0:len(C) - 2]) for (j = [0:k - (i == len(C) - 2 ? 0 : 1)])
    let(t = j / k, p0 = C[max(0, i - 1)], p1 = C[i], p2 = C[i + 1], p3 = C[min(len(C) - 1, i + 2)])
    0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
           + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)];

function path_len(P) = len(P) < 2 ? 0 : [for (i = [1:len(P) - 1]) 1] * [for (i = [1:len(P) - 1]) norm(P[i] - P[i - 1])];

// How far a member may run from p in direction a before it leaves the region it lives in.
function fit_len(p, a, L, ulim, zlo, zhi) =
    let(d = dir(a),
        tu = d[0] > 1e-6 ? (ulim - p[0]) / d[0] : d[0] < -1e-6 ? (-ulim - p[0]) / d[0] : 1e9,
        tz = d[1] > 1e-6 ? (zhi - p[1]) / d[1] : d[1] < -1e-6 ? (zlo - p[1]) / d[1] : 1e9)
    min(L, 0.85 * min(tu, tz));

function in_plaque(p, m = 2) = p[0] > plaque[0][0] - m && p[0] < plaque[0][1] + m
                            && p[1] > plaque[1][0] - m && p[1] < plaque[1][1] + m;

// A bent member from p, leaving along a0 and heading for a1, with radius r -> r1.
// Ends are buried when bury is true (the tip sinks into the wall).
function limb(p, a0, a1, L, r, r1, k, s0 = 0.1, bury = true) =
    let(p1 = p + 0.42 * L * dir(a0), p2 = p + L * dir(a1),
        n = max(4, ceil(L / seg)),
        w = (rnd(k, 3) - 0.5) * min(1.4, L / 14),
        P = [for (i = [0:n]) let(t = i / n, b = bez(p, p1, p2, t), g = unit(bezd(p, p1, p2, t)))
                 b + [-g[1], g[0]] * w * sin(180 * t)],
        R = [for (i = [0:n]) lerp(r, r1, i / n)],
        S = [for (i = [0:n]) bury ? lerp(s0, 1.2, smooth(0.72, 1, i / n)) : s0])
    [P, R, S, ang(p2 - p1)];

// The crown: each member forks into 2 (sometimes 3) until depth runs out.
// A member that would run out of room turns towards the vertical instead (it grows into space).
function crown_fit(p, a1, L) = fit_len(p, a1, L, fa + 0.55 * fq, z_base + 12, box_h - 3);
function crown(p, a0, a1_, L, r, d, k) =
    let(a1 = crown_fit(p, a1_, L) >= 0.6 * L ? a1_ : 0.6 * a1_,
        Lf = crown_fit(p, a1, L))
    Lf < 3.5 ? [] :
    let(r1 = max(0.85, 0.74 * r),
        m0 = limb(p, a0, a1, Lf, r, r1, k, 0.1, false),
        e = m0[0][len(m0[0]) - 1], ea = m0[3],
        nch = d == 0 ? 0 : rnd(k, 5) < 0.45 ? 3 : 2,
        lean = (rnd(k, 9) - 0.5) * 12 - 0.2 * ea,                    // a slight pull upwards
        kids = [for (j = [0:1:nch - 1])
               let(ca = clamp(ea + lean + spread * (j - (nch - 1) / 2) * (nch == 3 ? 0.8 : 1)
                              + (rnd(k, j, 11) - 0.5) * 16, -100, 100))
               each crown(e, ea, ca, L * (0.66 + 0.16 * rnd(k, j, 13)), r1 * (nch == 3 ? 0.88 : 0.96),
                          d - 1, k * 3 + j + 1)],
        m = len(kids) == 0 ? limb(p, a0, a1, Lf, r, 0.4 * r, k, 0.1, true) : m0)   // a twig ends in the wall
    concat([[m[0], m[1], m[2]]], kids);

// Trunk strands: three tubes braided round the trunk axis.
function strand_u(i, z) = trunk_u(z) + strand_amp * sin(360 * (z - z_base) / strand_wave + 120 * i);
function strand(i) = let(z0 = z_base - 4, z1 = strand_top[i], n = ceil((z1 - z0) / seg))
    [[for (j = [0:n]) let(z = lerp(z0, z1, j / n)) [strand_u(i, z), z]],
     [for (j = [0:n]) limb_r],
     [for (j = [0:n]) let(z = lerp(z0, z1, j / n))       // in front where it crosses the middle
         0.32 + 0.24 * cos(360 * (z - z_base) / strand_wave + 120 * i + 90)]];

function strand_end(i) = [strand_u(i, strand_top[i]), strand_top[i]];

// Main roots: control points (u, z), hand laid round the plaque and over the corners.
// Written for a tree on the left; trunk_side = 1 mirrors them.
roots_left = [
    [[-7, 46], [-11, 40], [-19, 35], [-26, 26], [-28.5, 14], [-27, 3], [-26, -2]],                  // left, down to the bed
    [[-9, 45], [-19, 42], [-31, 40], [-43, 33], [-51, 20], [-54, 6], [-55, -2]],                    // left, onto the side
    [[-6, 45], [-9.5, 39], [-14, 32], [-15.5, 20], [-14, 8], [-9, 2.8], [3, 2.2], [17, 2.7], [28, 2], [33, -1]],  // round the plaque
    [[-5, 46], [1, 40], [13, 36.5], [25, 36], [32.5, 33], [35.5, 23], [34, 11], [31.5, 2], [30.5, -2]],  // over the plaque, right frame
    [[-4, 47], [5, 43], [19, 41], [33, 39.5], [45, 34], [53, 22], [57, 10], [59, -2]],              // over the plaque, onto the right side
    [[10, 40.5], [22, 39.5], [31, 38], [41, 31], [46, 20], [48, 8], [48.5, -2]],                    // a second over the plaque
];
root_rad = [0.85, 0.8, 0.85, 1.0, 1.0, 0.6];
main_roots = [for (r = roots_left) [for (p = r) [-trunk_side * p[0], p[1]]]];

function root_member(c, r) = let(P = cr(c, max(2, ceil(10 / seg))), n = len(P) - 1)
    [P, [for (i = [0:n]) r * lerp(1, 0.45, pow(i / n, 0.8))], [for (i = [0:n]) 0.15]];

// Rootlets: side shoots off the main roots, heading outwards and down.
function rootlets(m, k) = let(P = m[0], n = len(P) - 1)
    [for (q = [0:2]) let(i = floor(n * (0.25 + 0.25 * q + 0.1 * rnd(k, q))),
                         p = P[i], t = unit(P[min(n, i + 1)] - P[max(0, i - 1)]), ta = ang(t),
                         side = p[0] >= trunk_u(z_base) ? 1 : -1,
                         a1 = ta + (q == 1 ? -1 : 1) * side * (25 + 20 * rnd(k, q, 2)),
                         L = fit_len(p, a1, 12 + 8 * rnd(k, q, 3), u_side_end - 6, 1.5, box_h),
                         lm = limb(p, ta, a1, max(L, 0.1), 0.62 * m[1][i], 0.3 * m[1][i], k + q, 0.2, true),
                         e = lm[0][len(lm[0]) - 1])
         if (L >= 4 && !in_plaque(e) && !in_plaque(lm[0][floor(len(lm[0]) / 2)])) [lm[0], lm[1], lm[2]]];

// ---------------------------------------------------------------- all members
strands = [for (i = [0:2]) strand(i)];
core = let(n = ceil(34 / seg)) [[for (j = [0:n]) let(z = lerp(z_base - 3, 67, j / n)) [trunk_u(z) + 0.3 * sin(j * 40), z]],
                                [for (j = [0:n]) lerp(4.6, 3.0, j / n)], [for (j = [0:n]) 0.55]];
// first limbs: [start (u, z), leaving angle, heading, length share, radius share]
// The crown grows mostly over the open side: written for a tree on the left, mirrored by trunk_side.
limb_table = [[strand_end(0), 0, -72, 0.85, 1.0],
              [[trunk_u(51), 51], 20, 84, 1.6, 0.95],
              [strand_end(2), 0, 62, 1.4, 1.0],
              [[trunk_u(61), 61], -15, -32, 0.9, 0.95],
              [strand_end(1), 0, 6, 1.0, 0.95],
              [[trunk_u(65), 65], 15, 34, 1.15, 0.9]];
limbs = [for (i = [0:len(limb_table) - 1]) let(l = limb_table[i], m = -trunk_side)
    each crown(l[0], m * l[1], m * l[2], limb_len * l[3], limb_r * l[4], crown_depth - (i >= 3 ? 1 : 0), seed * 31 + i)];
roots = [for (i = [0:len(main_roots) - 1]) root_member(main_roots[i], root_r * root_rad[i])];
shoots = [for (i = [0:len(roots) - 1]) each rootlets(roots[i], seed * 17 + i * 5)];
members = concat(strands, [core], limbs, roots, shoots);

// ---------------------------------------------------------------- Step 1: the deck
module deck() {
    color([0.85, 0.85, 0.9]) translate([-card_w / 2, -deck_t / 2, floor_t]) cube([card_w, deck_t, card_h]);
}

// ---------------------------------------------------------------- Step 2: the box
module footprint(o = 0) { offset(r = rc + o) square([box_w - 2 * rc, box_d - 2 * rc], center = true); }
module outer() { linear_extrude(box_h) footprint(); }
module cavity() { translate([0, 0, floor_t]) linear_extrude(box_h) footprint(-wall); }
module back_slot() {
    translate([0, box_d / 2, 0]) rotate([-90, 0, 0])
        hull() {
            translate([0, -(slot_bottom + slot_w / 2), 0]) cylinder(d = slot_w, h = 4 * wall, center = true, $fn = 72);
            translate([-slot_w / 2, -box_h - 5, -2 * wall]) cube([slot_w, 1, 4 * wall]);
        }
}
module shell() { difference() { outer(); cavity(); back_slot(); } }

// ---------------------------------------------------------------- the plaque text
module he_text(t) { text(t, size = text_size, font = font_he, halign = "center", valign = "center",
                         direction = "rtl", language = "he", script = "hebrew"); }
module en_text(t) { text(t, size = text_size, font = font_en, halign = "center", valign = "center"); }
module plaque_2d() {
    cx = (plaque[0][0] + plaque[0][1]) / 2;
    has_logo = logo_file != "";
    pitch = text_size * 1.6;
    if (plaque_layout == "stacked") {
        // English over Hebrew, centred; with an emblem the text sits low and the emblem above it
        z0 = has_logo ? plaque[1][0] + 2 + 1.5 * pitch : (plaque[1][0] + plaque[1][1]) / 2;
        rows = [line_en1, line_en2, line_he1, line_he2];
        for (i = [0:3]) translate([cx, z0 + (1.5 - i) * pitch + (i < 2 ? 0.4 : -0.4)])
            if (i < 2) en_text(rows[i]); else he_text(rows[i]);
        if (has_logo) translate([cx, (plaque[1][1] + z0 + 2 * pitch) / 2])
            resize([logo_w, 0], auto = [true, true]) import(logo_file, center = true);
    } else {
        // as on the reference print: English left, Hebrew right, emblem above
        ty = has_logo ? plaque[1][0] + 7.5 : (plaque[1][0] + plaque[1][1]) / 2;
        w = (plaque[0][1] - plaque[0][0]) / 4;
        for (i = [0:1]) {
            translate([plaque[0][0] + w, ty + (0.5 - i) * pitch]) en_text([line_en1, line_en2][i]);
            translate([plaque[0][1] - w, ty + (0.5 - i) * pitch]) he_text([line_he1, line_he2][i]);
        }
        if (has_logo) translate([cx, (plaque[1][1] + ty + pitch) / 2])
            resize([logo_w, 0], auto = [true, true]) import(logo_file, center = true);
    }
}
module text_solid() {
    if (show_text) translate([0, -box_d / 2 + text_inlay, 0]) rotate([90, 0, 0])
        linear_extrude(text_inlay + text_proud) plaque_2d();
}

// ---------------------------------------------------------------- the relief
module tubes() { for (i = [0:len(members) - 1]) sweep(member3d(members[i]), members[i][1], phase = 37 * i); }
module relief() {
    difference() {
        tubes();
        outer();
        back_slot();
        translate([-box_w, -box_d, -10]) cube([2 * box_w, 2 * box_d, 10]);      // bed
        translate([-box_w, -box_d, box_h]) cube([2 * box_w, 2 * box_d, 10]);    // rim
    }
}

// ---------------------------------------------------------------- summary
echo(str("Deck holder: outer ", box_w, " x ", box_d, " x ", box_h, " mm; cavity ", box_w - 2 * wall, " x ",
         box_d - 2 * wall, " x ", box_h - floor_t, " mm for ", card_w, " x ", card_h, " mm cards, deck up to ",
         deck_t, " mm; the deck stands ", box_h - floor_t - card_h, " mm below the rim; back slot ", slot_w,
         " mm wide from z ", slot_bottom, "; ", len(members), " tree members (", len(limbs), " crown, ",
         len(roots) + len(shoots), " roots)"));

// ---------------------------------------------------------------- parts
if (part == "assembly") {
    color("#F4F4F0") difference() { shell(); text_solid(); }
    color("#B5651D") relief();
    color("#111111") text_solid();
    if (show_deck) deck();
} else if (part == "box") {
    difference() { shell(); text_solid(); }
} else if (part == "relief") {
    relief();
} else if (part == "text") {
    text_solid();
} else if (part == "paths") {
    for (m = members) echo(m[0]);
}
