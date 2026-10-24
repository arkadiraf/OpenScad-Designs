// Kitten Planter - a sitting kitten whose head is a plant pot, open on top between the ears.
//
// The kitten is built from ellipsoids joined by hulls: haunches and chest make the seated body,
// the head is pulled down into a neck cone (so the cheeks and chin slope at >= 45 deg and print
// without supports), front legs stand straight down to the paws and the tail curls round the
// front on the bed. Head and body are one hollow shell (wall `wall` mm on the print): the inside is
// the same ellipsoids shrunk by the wall, so the pot is the whole kitten, open on top of the head.
// Under the rim a 45 deg funnel collar narrows the inside to the opening, which gives the ears a
// solid rim to stand on and leaves no flat ceiling inside. Legs, thighs, paws and tail are solid.
// Colours are flush patches cut through the surface: eyes, pupils, nose and inner ears, a white
// muzzle, bib, socks and tail tip.
//
// Axes while modelling: +x is where the kitten looks, +z is up. The finished kitten is turned by
// face_az so it looks at the viewer of the gallery's isometric render.

/* [Output] */
part = "assembly"; // [assembly, whole, inside, body, white, pink, eyes, pupils, none]
// Coarse spheres: for finding the shape
sketch = false;
// Overall height to the ear tips, mm
height = 200; // [100:5:260]
// Turn about z, deg (-45 faces the isometric viewer)
face_az = -45;

/* [Pot] */
// Wall thickness of head and body, mm on the print
wall = 3.5;         // [2:0.5:6]
// Floor thickness, mm on the print
floor_t = 3.5;      // [2:0.5:6]
open_rx = 27;       // opening half-length (front-back), model units (mm at 190 mm tall)
open_ry = 33;       // opening half-width (side to side)
rim_f = 0.5;        // rim height in the head, as a share of its half-height above the centre
// Drain hole diameter, mm on the print (0 = none: use it as a cachepot); stand it on a saucer
drain_d = 10;       // [0:1:20]

/* [Head] */
head_c = [10, 0, 128];  // mm, centre
head_s = [46, 58, 42];  // mm, semi-axes
neck_c = [6, 0, 90];    // mm, the point the head narrows into
neck_s = [36, 46, 18];  // mm
eye_y = 21;             // mm, from the midline
eye_dz = 3;             // mm, above the head centre
eye_s = [9, 9, 10.5];   // mm, eye patch
eye_tilt = 14;          // deg, outer corners up
pupil_s = [9, 4.2, 8];  // mm

/* [Ears] */
ear_az = 56;        // deg from the front, where the ears sit round the rim
ear_face = 28;      // deg from the front, where the ears look
ear_h = 32;         // mm, above the rim
ear_w = 15;         // mm, half-width at the base
ear_t = 5.5;         // mm, half-thickness at the base
ear_lean = 8;       // mm, tip offset outwards

/* [Body] */
haunch_c = [-6, 0, 26];
haunch_s = [50, 52, 40];
chest_c = [4, 0, 72];
chest_s = [32, 42, 38];
thigh_c = [-4, 36, 26];     // mirrored in y
thigh_s = [36, 20, 30];
leg_y = 15;                 // mm, front legs from the midline
tail_r0 = 7.5;              // mm, tail radius at the body
tail_r1 = 5.5;              // mm, at the tip

/* [Hidden] */
ear_top = head_c.z + head_s.z * rim_f - 3 + ear_h + 1.8;   // model units, unscaled
s = height / ear_top;
w = wall / s;               // the wall in model units
fl = floor_t / s;
$fn = sketch ? 32 : 96;
rim_z = head_c.z + head_s.z * rim_f;
big = 400;

// ---------------------------------------------------------------- library
function unit(v) = v / norm(v);
function tangents(P) = [for (i = [0:len(P) - 1])
    unit(i == 0 ? P[1] - P[0] : i == len(P) - 1 ? P[i] - P[i - 1] : P[i + 1] - P[i - 1])];
function first_normal(t) = unit(cross(t, abs(t[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0]));
function transport(T, i, prev) = i >= len(T) ? [] :
    let(n = unit(prev - (prev * T[i]) * T[i])) concat([n], transport(T, i + 1, n));

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

module sweep(P, R, sides = 32) {
    T = tangents(P);
    N = transport(T, 0, first_normal(T[0]));
    loft([for (i = [0:len(P) - 1]) let(B = cross(T[i], N[i]))
          [for (j = [0:sides - 1]) let(a = 360 * j / sides) P[i] + R[i] * (cos(a) * N[i] + sin(a) * B)]]);
}

module ell(c, sx, g = 0) translate(c) scale(sx + [g, g, g]) sphere(1);
// Radius of an ellipse with semi-axes a, b in direction t.
function ell_r(a, b, t) = 1 / sqrt(pow(cos(t) / a, 2) + pow(sin(t) / b, 2));
// Point on the front of the head at (y, z), pushed in by `inset`.
function face_pt(y, z, inset = 0) =
    [head_c.x + head_s.x * sqrt(max(0, 1 - pow(y / head_s.y, 2) - pow((z - head_c.z) / head_s.z, 2))) - inset, y, z];
// A prism along x through the face, for flush colour patches.
module through_x(p, r = 1.2) translate(p + [-14, 0, 0]) rotate([0, 90, 0]) cylinder(r = r, h = 24, $fn = 16);

// ---------------------------------------------------------------- the kitten
// g > 0 shrinks every ellipsoid by g: the inside of the shell.
module head(g = 0) hull() { ell(head_c, head_s, -g); ell(neck_c, neck_s, -g); }

module body(g = 0) hull() { ell(haunch_c, haunch_s, -g); ell(chest_c, chest_s, -g); }

module mirror_y() { children(); mirror([0, 1, 0]) children(); }

module front_legs() mirror_y() {
    hull() { translate([37, leg_y, 10]) sphere(10); translate([29, leg_y, 70]) sphere(12); }
}
paw_c = [44, leg_y + 0.5, 3];
foot_c = [28, 45, 3];
module front_paws(g = 0) mirror_y() ell(paw_c, [14, 10.5, 9], g);

module thighs() mirror_y() ell(thigh_c, thigh_s);
module hind_feet(g = 0) mirror_y() ell(foot_c, [15, 9, 7], g);
// White socks: the paws and feet, coming to a point up the leg, so the colour boundary slopes at
// about 45 deg instead of capping the paw with a flat dome.
module socks() mirror_y() {
    hull() { ell(paw_c, [14, 10.5, 9], 0.4); translate(paw_c + [-6, -0.5, 22]) sphere(1, $fn = 12); }
    hull() { ell(foot_c, [15, 9, 7], 0.4); translate(foot_c + [-2, -3, 18]) sphere(1, $fn = 12); }
}

// Tail: round the -y side from behind, ending in front of the right front paw, lying on the bed
// cut through 35 % of its height.
tail_n = 40;
tail_pts = [for (i = [0:tail_n]) let(t = i / tail_n, a = 175 + 160 * t,
                                      rr = 52 - 4 * t * t, r = tail_r0 + (tail_r1 - tail_r0) * t)
            [-6 + rr * cos(a), rr * sin(a), 0.3 * r]];
tail_rad = [for (i = [0:tail_n]) tail_r0 + (tail_r1 - tail_r0) * i / tail_n];
tail_tip = tail_pts[tail_n];
module tail() { sweep(tail_pts, tail_rad); translate(tail_tip) sphere(tail_r1); }

// Muzzle: two whisker pads and a chin point inside the neck, so the underside slopes back.
pad_z = head_c.z - 13;
module muzzle(g = 0) hull() {
    mirror_y() translate(face_pt(9, pad_z, 4)) scale([0.9, 1, 0.85]) sphere(10.5 + g);
    translate(face_pt(0, head_c.z - 32, 10)) sphere(3 + g);
}

// Ears sit on the rim between the opening and the edge of the head, looking forwards and out.
ear_rr = (ell_r(open_rx, open_ry, ear_az) + ell_r(head_s.x * sqrt(1 - rim_f * rim_f),
                                                  head_s.y * sqrt(1 - rim_f * rim_f), ear_az)) / 2;
ear_p = [head_c.x + ear_rr * cos(ear_az), ear_rr * sin(ear_az), rim_z - 3];
module ear_place() mirror_y() translate(ear_p) rotate([0, 0, ear_face]) children();
module ear() hull() {
    scale([ear_t, ear_w, 3]) sphere(1);
    translate([-1.5, ear_lean, ear_h]) sphere(1.8, $fn = 24);
}
module inner_ear() hull() {
    translate([3, 0, 9]) scale([3.2, ear_w * 0.62, 6]) sphere(1);
    translate([2, ear_lean * 0.85, ear_h * 0.78]) sphere(1, $fn = 16);
}

module kitten_raw() {
    intersection() {
        union() { head(); muzzle(); }
        translate([-big / 2, -big / 2, 0]) cube([big, big, rim_z]);
    }
    body(); thighs(); hind_feet(); front_legs(); front_paws(); tail();
    ear_place() ear();
}

// The pot: head and body shrunk by the wall, above the floor, inside a 45 deg funnel that opens
// to the elliptical mouth on the rim.
module disc(rx, ry, z) translate([head_c.x, 0, z]) scale([rx, ry, 1]) cylinder(r = 1, h = 0.01, $fn = $fn * 1.5);
module inside() {
    intersection() {
        union() { head(w); body(w); }
        hull() { disc(open_rx, open_ry, rim_z + 5); disc(open_rx + 150, open_ry + 150, rim_z - 145); }
        translate([-big / 2, -big / 2, fl]) cube(big);
    }
    if (drain_d > 0) translate([head_c.x, 0, -1]) cylinder(d = drain_d / s, h = fl + 2);
}

module kitten() difference() {
    kitten_raw();
    inside();
    translate([-big / 2, -big / 2, -big]) cube(big);
}

// ---------------------------------------------------------------- colour zones
// Each part is the kitten cut by its zone, minus every zone ahead of it in this list, so the
// parts never overlap. 0 highlights (white) > 1 pupils > 2 eyes > 3 nose and inner ears >
// 4 white fur > body.
eye_c = [for (sg = [1, -1]) face_pt(sg * eye_y, head_c.z + eye_dz, 1)];
module zone(k) {
    if (k == 0) for (sg = [1, -1]) translate(face_pt(sg * (eye_y - 2.2), head_c.z + eye_dz + 3.2, 0)) sphere(1.9, $fn = 24);
    if (k == 1) for (i = [0, 1]) translate(eye_c[i]) scale(pupil_s) sphere(1);
    if (k == 2) for (i = [0, 1]) let(sg = i == 0 ? 1 : -1)
        translate(eye_c[i]) rotate([sg * eye_tilt, 0, 0]) scale(eye_s) sphere(1);
    if (k == 3) {
        hull() {
            through_x(face_pt(4.5, pad_z + 9, 0));
            through_x(face_pt(-4.5, pad_z + 9, 0));
            through_x(face_pt(0, pad_z + 3.5, 0));
        }
        ear_place() inner_ear();
    }
    if (k == 4) {
        muzzle(0.4);
        ell([chest_c.x + chest_s.x, 0, 76], [11, 20, 30]);
        socks();
        translate(tail_tip) sphere(13);
    }
}
module zones_before(k) for (j = [0:k - 1]) zone(j);

module colour(k) render() difference() {
    intersection() { kitten(); zone(k); }
    if (k > 0) zones_before(k);
}
module body_part() render() difference() { kitten(); zones_before(5); }

// ---------------------------------------------------------------- summary
echo(str("Kitten planter: ", height, " mm to the ear tips (scale ", round(s * 1000) / 1000, "), rim at ",
         round(rim_z * s), " mm; opening ", round(2 * open_rx * s), " x ", round(2 * open_ry * s),
         " mm; wall ", wall, " mm, floor ", floor_t, " mm; drain ", drain_d > 0 ? str(drain_d, " mm") : "none"));

// ---------------------------------------------------------------- output
module out() rotate([0, 0, face_az]) scale(s) children();
if (part == "assembly") out() {
    color("#FF9016") body_part();
    color("#FFFFFF") { colour(0); colour(4); }
    color("#F55A74") colour(3);
    color("#BECF00") colour(2);
    color("#000000") colour(1);
}
if (part == "whole") out() kitten();
if (part == "inside") out() inside();
if (part == "body") out() body_part();
if (part == "white") out() { colour(0); colour(4); }
if (part == "pink") out() colour(3);
if (part == "eyes") out() colour(2);
if (part == "pupils") out() colour(1);
