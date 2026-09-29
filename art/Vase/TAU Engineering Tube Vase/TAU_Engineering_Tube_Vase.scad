// TAU ENGINEERING TUBE VASE - a compact holder for a 16 x 150 mm science test tube,
// used as a single-stem bud vase. Dedicated to the Tel Aviv University Faculty of
// Engineering, and built from the three marks of the TAU logo:
//   - the base is the thick rounded triangle of the middle mark (a Reuleaux triangle),
//   - the body is the right-hand mark: three overlapping circles, each one a thin
//     ring whose centre orbits the tube as it rises, so the three rings twist round
//     each other like the orbits of an atom and narrow into a neck,
//   - the left-hand mark, the round emblem (flame, crown and the letters AT), is inlaid
//     in white under the base: an exact trace of the logo (TAU_Emblem.scad, made by
//     TAU_Emblem_trace.py), mirrored so it reads right when the vase is turned over,
//   - the top is a round collar; its centre is the tube.
// Tight fit: the bore is the tube plus a small radial clearance. Each ring's inner arc
// reaches a little into the bore, so the bore cuts three long grip strips on them, and
// the tube is held at three lines all the way up, plus the collar at the top.
// The tube's round bottom sits in a matching spherical seat.
// Printable without supports: the rings are vertical walls that lean at most ~25 deg,
// the collar sits on a 45 deg cone, and the logo is part of the first layers on the bed
// (black holder, white logo: the colour changes only for those few layers).
// Step 1 is the test tube; every holder dimension is derived from it.
// All dimensions in mm. OpenSCAD trigonometry uses DEGREES.

/* [0 - Weight: wall and base thickness] */
// Presets: standard 2.0 / 4, medium 1.5 / 4, light 1.0 / 2.5
// Wall thickness of each ring (0.4 mm nozzle: 1.0 = 2 lines, 1.5 = 3-4, 2.0 = 5)
orbit_w = 2.0;          // [1.0:0.1:3.0]
// Thickness of the base (at least logo_depth + 1)
base_h = 4;             // [2.5:0.5:6]

/* [Output] */
part = "assembly"; // [assembly, holder, logo, tube, none]
// Coarse sampling, for finding the shape
sketch = false;
show_tube = true;
// Preview colours only; the 3MF is always black with a white logo
preview_colors = "black"; // [black, blue]
// Batch plate: copies in a grid, all the same way round (1 x 1 = a single vase).
// Bambu H2C (330 x 320 bed): 4 x 4 at 84 x 80 mm fills the plate evenly (5 across does not fit)
// Bambu X2D (256 x 256 bed): 3 x 3 at 90 x 90 mm (4 across does not fit)
plate_cols = 1;         // [1:6]
plate_rows = 1;         // [1:6]
plate_pitch = [84, 80]; // centre-to-centre spacing, x and y

/* [1 - Test tube] */
tube_d = 16;            // outer diameter of the tube
tube_h = 150;           // overall length of the tube, round bottom included
tube_wall = 1;          // preview only
tube_lip = 1;           // flared rim at the top (preview only)

/* [2 - Fit] */
clearance = 0.2;        // radial gap round the tube (bore radius = tube_d / 2 + clearance)
floor_h = 2.5;          // material under the tip of the tube
holder_h = 75;          // overall height of the holder (<= 100)
lead_in = 0.8;          // entry chamfer at the top of the bore

/* [3 - Orbits (the three rings)] */
orbits = 3;             // number of rings (the logo has 3)
orbit_grip = 0.5;       // how far each ring's inner arc reaches into the bore (cut flat there; at most 0.3 x orbit_w)
orbit_e_bot = 8;        // ring centre off the axis at the bed (sets the width of the belly)
orbit_e_waist = 3.5;    // ... at the waist
orbit_e_top = 5.5;      // ... at the top; 5.5 gives the logo's proportions (offset / radius ~ 0.38)
belly = 0.18;           // top of the belly, as a fraction of the holder
waist = 0.62;           // height of the waist, as a fraction of the holder
twist = 150;            // how far the rings turn round the tube from bottom to top

/* [4 - Base (Reuleaux triangle)] */
base_w = 66;            // width of the Reuleaux triangle (constant in every direction)
base_round = 3;         // rounding of its three corners
base_chamfer = 1.2;     // top edge chamfer

/* [5 - Collar] */
collar_h = 7;           // height of the straight part of the collar
collar_t = 2.2;         // wall thickness outside the bore

/* [6 - Logo under the base (the left-hand mark)] */
// false = plain black underside, no logo inlay (single colour)
with_logo = true;
logo_r = 24;           // radius of the logo circle (the base's inscribed radius is ~0.42 base_w)
logo_depth = 1;         // inlay thickness (5 layers at 0.2 mm, so the white stays white)
// A white outline round the circle; the logo's disc is black like the holder, so
// without it only the emblem shows
logo_outline = 0.8;     // width, 0 = none

/* [Hidden] */
include <TAU_Emblem.scad>                               // tau_emblem(), in units of the disc radius
bore_r = tube_d / 2 + clearance;
seat_z = floor_h + bore_r;                              // centre of the round seat
// Thin walls grip less, so the bore leaves at least 70 % of the wall at the grip strips
grip = min(orbit_grip, 0.3 * orbit_w);
c0 = bore_r + orbit_w / 2 - grip;                       // ring centreline at its inner arc
assert(base_h >= logo_depth + 1, "base_h must be at least logo_depth + 1");
assert(orbit_w >= 0.8, "orbit_w below two 0.4 mm lines");
hub_r = bore_r + 2;                                     // solid hub round the seat
corner_r = base_w / sqrt(3);                            // Reuleaux vertex distance
front = -45;                                            // faces the iso camera (sec. 9 of the guide)
t_base = base_h / holder_h;
// The rings' centres point between the base corners at the base top, so the
// base shows three clean corners.
orbit_phase = front + 180 / orbits - twist * ease(t_base) + 0.7;
steps = sketch ? 24 : 60;                               // rings along the height
ring_fn = sketch ? 36 : 96;                             // points round each ring
$fn = sketch ? 36 : 96;

function lerp(a, b, t) = a + (b - a) * t;
function smooth(t) = t * t * (3 - 2 * t);
// Twist eased at both ends so the rings stand straight on the base and under the collar
function ease(t) = smooth(t);
// Ring centre off the axis: belly low down, smooth waist, flared mouth
function orbit_e(t) = t <= belly ? orbit_e_bot
                    : t <= waist ? lerp(orbit_e_bot, orbit_e_waist, smooth((t - belly) / (waist - belly)))
                    : lerp(orbit_e_waist, orbit_e_top, smooth((t - waist) / (1 - waist)));
function orbit_theta(k, t) = orbit_phase + 360 * k / orbits + twist * ease(t);
function orbit_center(k, t) = let(e = orbit_e(t), a = orbit_theta(k, t)) [e * cos(a), e * sin(a)];
function orbit_R(t) = c0 + orbit_e(t);                  // inner arc stays at c0 all the way up
function outer_r(z) = let(t = min(1, max(0, z / holder_h))) orbit_R(t) + orbit_e(t) + orbit_w / 2;


// Closed solid through rings of points; each ring counter-clockwise seen from above.
module loft(rings) {
    n = len(rings); S = len(rings[0]);
    pts  = [for (ring = rings) each ring];
    side = [for (i = [0:n - 2]) for (j = [0:S - 1])
            let(j2 = (j + 1) % S, a = i * S + j, b = (i + 1) * S + j, c = (i + 1) * S + j2, d = i * S + j2)
            each [[a, b, c], [a, c, d]]];
    caps = [[for (j = [0:S - 1]) j], [for (j = [S - 1:-1:0]) (n - 1) * S + j]];
    polyhedron(points = pts, faces = concat(side, caps), convexity = 10);
}

// A disc of radius R(t) + dr whose centre follows orbit k, from z0 to z1
module orbit_disc(k, dr, z0, z1) {
    loft([for (i = [0:steps]) let(z = lerp(z0, z1, i / steps),
                                  t = min(1, max(0, z / holder_h)),
                                  c = orbit_center(k, t), r = orbit_R(t) + dr)
          [for (j = [0:ring_fn - 1]) let(a = 360 * j / ring_fn)
               [c[0] + r * cos(a), c[1] + r * sin(a), z]]]);
}

// ---------------------------------------------------------------- Step 1: the tube
module tube() {
    r = tube_d / 2;
    color("LightCyan", 0.35) translate([0, 0, floor_h + clearance]) difference() {
        union() {
            translate([0, 0, r]) sphere(r);
            translate([0, 0, r]) cylinder(r = r, h = tube_h - r);
            translate([0, 0, tube_h - tube_lip]) cylinder(r = r + tube_lip, h = tube_lip);
        }
        translate([0, 0, r]) sphere(r - tube_wall);
        translate([0, 0, r]) cylinder(r = r - tube_wall, h = tube_h);
    }
}

// ---------------------------------------------------------------- Step 2: the holder
module reuleaux() {
    offset(r = base_round) offset(delta = -base_round)
        intersection_for (k = [0:2]) let(a = front + 120 * k)
            translate(corner_r * [cos(a), sin(a)]) circle(r = base_w, $fn = 360);
}

module base() {
    hull() {
        linear_extrude(base_h - base_chamfer) reuleaux();
        translate([0, 0, base_h - 0.01]) linear_extrude(0.01) offset(delta = -base_chamfer) reuleaux();
    }
}

// The right-hand mark: three rings, lofted as band = outer disc - inner disc
module orbits() {
    for (k = [0:orbits - 1]) difference() {
        orbit_disc(k,  orbit_w / 2, 0, holder_h);
        orbit_disc(k, -orbit_w / 2, -1, holder_h + 1);
    }
}

// Solid hub round the round seat, with a 45 deg top
module hub() {
    rotate_extrude() polygon([[0, 0], [hub_r, 0], [hub_r, seat_z], [bore_r - 0.5, seat_z + hub_r - bore_r + 0.5],
                              [0, seat_z + hub_r - bore_r + 0.5]]);
}

// Collar at the top, on a 45 deg cone; inner lip at bore_r - 0.5 is cut away by the bore
module collar() {
    ro = bore_r + collar_t;
    zb = holder_h - collar_h - collar_t;
    rotate_extrude() polygon([[bore_r - 0.5, zb], [bore_r, zb], [ro, zb + collar_t],
                              [ro, holder_h - 0.8], [ro - 0.8, holder_h], [bore_r - 0.5, holder_h]]);
}

module bore() {
    translate([0, 0, seat_z]) sphere(bore_r);
    translate([0, 0, seat_z]) cylinder(r = bore_r, h = holder_h);
    translate([0, 0, holder_h - lead_in]) cylinder(r1 = bore_r, r2 = bore_r + lead_in + 0.01, h = lead_in + 0.01);
}

// The left-hand mark under the base: the traced emblem plus an optional outline ring,
// mirrored in x because it is seen from below. Flush with the bed, logo_depth thick.
module logo() {
    linear_extrude(logo_depth) mirror([1, 0]) rotate(front + 180) {    // top of the emblem to the front corner
        scale(logo_r) tau_emblem();
        if (logo_outline > 0) difference() {
            circle(r = logo_r, $fn = 180);
            circle(r = logo_r - logo_outline, $fn = 180);
        }
    }
}

module holder() {
    difference() {
        union() {
            base();
            hub();
            orbits();
            collar();
        }
        bore();
        if (with_logo) logo();
    }
}

// ---------------------------------------------------------------- summary
lean = max([for (i = [0:steps - 1]) let(t0 = i / steps, t1 = (i + 1) / steps,
            d = norm(orbit_center(0, t1) - orbit_center(0, t0)) + abs(orbit_R(t1) - orbit_R(t0)))
            atan(d / (holder_h / steps))]);
echo(str("TAU tube vase: tube ", tube_d, " x ", tube_h, " mm, bore d ", 2 * bore_r,
         " mm, tip at z ", floor_h + clearance, ", tube inserted ", holder_h - floor_h - clearance,
         " mm (", round(100 * (holder_h - floor_h) / tube_h), "% of its length), holder ", holder_h,
         " mm tall, base ", base_w, " mm, belly d ", 2 * (c0 + 2 * orbit_e_bot + orbit_w / 2),
         " mm, waist d ", 2 * (c0 + 2 * orbit_e_waist + orbit_w / 2),
         " mm, mouth d ", 2 * (c0 + 2 * orbit_e_top + orbit_w / 2), " mm, ring wall lean max ",
         round(lean * 10) / 10, " deg, logo d ", 2 * logo_r, " under the base, ring walls ", orbit_w,
         " mm (grip ", grip, "), base ", base_h, " mm"));

// ---------------------------------------------------------------- output
// Copies of the children on the batch grid, centred on the origin
module plate() {
    for (i = [0:plate_cols - 1], j = [0:plate_rows - 1])
        translate([(i - (plate_cols - 1) / 2) * plate_pitch[0], (j - (plate_rows - 1) / 2) * plate_pitch[1], 0])
            children();
}

if (part == "assembly") plate() {
    // Bambu PLA Basic Black (lifted, so the preview shades), or Bambu PLA Basic Blue
    color(preview_colors == "blue" ? "#0A2989" : "#1E1E1E") holder();
    if (with_logo) color("#FFFFFF") logo();            // Bambu PLA Basic Jade White
    if (show_tube) tube();
}
if (part == "holder") plate() holder();
if (part == "logo" && with_logo) plate() logo();
if (part == "tube") tube();
