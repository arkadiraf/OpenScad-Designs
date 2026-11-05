// Card Box - a two-piece box for a deck of playing cards.
// Base tray and a lid that slips over a thin lip at the top of the base.
// Closed, the lid's top rests on the rim and its skirt meets the base wall
// flush, so the outside reads as one solid block. A small pull notch at the seam on each short end
// gives a fingertip something to open it with.
// The lid top carries the TAU Engineering ECE logo as a black inlay, flush with
// the white surface (it prints in the lid's first layers, top down on the bed).
// Logo outline: Card_Box_Logo.scad, traced by Card_Box_logo_trace.py.

include <Card_Box_Logo.scad>
// Step 1 is the cavity: inner 100 x 70 mm, 25 mm deep (base floor to base rim).
// Both pieces print open side up / lid top down on the bed, no supports.

/* [Cavity (inside dimensions)] */
inner_l = 100;   // [40:1:200] inside length, mm
inner_w = 70;    // [30:1:150] inside width, mm
inner_d = 25;    // [10:1:120] inside depth of the base, mm

/* [Walls] */
wall    = 2.4;   // [1.6:0.4:4] base wall thickness (six 0.4 mm lines)
floor_t = 1.6;   // [1.2:0.2:3] base floor and lid top thickness, mm
corner_r = 4;    // [1:0.5:10] outer corner radius, mm

/* [Lid] */
lip_h  = 8;      // [4:1:30] height of the lip the lid slides over, mm
lid_wall = 1.2;  // [0.8:0.4:2] lid skirt thickness, mm
fit    = 0.2;    // [0:0.05:0.5] radial clearance between lip and lid, mm

/* [Pull notch] */
pull_w = 18;     // [0:1:40] width of the pull notch at the seam, short ends (0 = none)
pull_h = 2.5;    // [1:0.5:5] height the notch cuts into the lid edge, mm
pull_depth = 1;  // [0.4:0.2:1.6] depth of the matching scoop in the base wall, mm
pull_drop = 3;   // [1:0.5:8] how far the base scoop reaches below the seam, mm

/* [Logo] */
logo_w = 90;      // [0:1:100] logo width on the lid top, mm (0 = no logo)
logo_depth = 0.6; // [0.2:0.2:1.2] inlay depth, mm (3 layers at 0.2)

/* [Output] */
part = "assembly"; // [assembly, base, lid, logo, closed, showcase, none]

/* [Hidden] */
$fn = 64;
eps = 0.01;
outer_l = inner_l + 2*wall;
outer_w = inner_w + 2*wall;
base_h  = floor_t + inner_d;
lip_t   = wall - lid_wall - fit;      // thickness left in the lip
lid_h   = floor_t + lip_h;
gap     = 10;                         // spacing between pieces on the plate
assert(lip_t >= 0.8, "wall too thin for lid_wall + fit: lip under 0.8 mm");
assert(logo_w <= outer_l - 2*lid_wall - 4, "logo wider than the lid top");
assert(logo_depth < floor_t - 0.6, "logo inlay too deep for the lid top");
white = "#FFFFFF";   // Bambu PLA Basic Jade White
black = "#000000";   // Bambu PLA Basic Black

// rounded rectangle, centred, outer size l x w, corner radius r
module rrect(l, w, r) {
    rr = max(min(r, l/2 - eps, w/2 - eps), eps);
    offset(r = rr) square([l - 2*rr, w - 2*rr], center = true);
}
module rbox(l, w, h, r) linear_extrude(h) rrect(l, w, r);

// Step 2: the base
module base() {
    difference() {
        union() {
            // full-thickness wall below the lip
            rbox(outer_l, outer_w, base_h - lip_h, corner_r);
            // thin lip (the lid skirt + fit takes the rest of the wall)
            rbox(outer_l - 2*(lid_wall + fit), outer_w - 2*(lid_wall + fit),
                 base_h, corner_r - lid_wall - fit);
        }
        // cavity
        translate([0, 0, floor_t])
            rbox(inner_l, inner_w, base_h, corner_r - wall);
        // pull scoops: shallow half-ellipse just below the seam, short ends
        if (pull_w > 0)
            for (s = [-1, 1])
                translate([s*outer_l/2, 0, base_h - lip_h])
                    scale([1, pull_w/2, pull_drop])
                        rotate([0, 90, 0])
                            cylinder(r = 1, h = 2*pull_depth, center = true);
    }
}

// Step 3: the lid, modelled top-down on the bed (open side up)
// Logo inlay in lid coordinates: z = 0 is the outside of the lid top. Mirrored in y,
// so it reads right once the lid is turned over (rotate 180 about x) onto the box.
module logo_shape() mirror([0, 1, 0]) scale(logo_w / ece_logo_w) ece_logo();
module logo_inlay() if (logo_w > 0) linear_extrude(logo_depth) logo_shape();
module logo_cutter() if (logo_w > 0)
    translate([0, 0, -1]) linear_extrude(logo_depth + 1) logo_shape();

module lid_shell() {
    difference() {
        rbox(outer_l, outer_w, lid_h, corner_r);
        translate([0, 0, floor_t])
            rbox(outer_l - 2*lid_wall, outer_w - 2*lid_wall, lid_h,
                 corner_r - lid_wall);
        // pull notches: half-ellipse cut into the skirt's open edge, short ends
        if (pull_w > 0)
            for (s = [-1, 1])
                translate([s*outer_l/2, 0, lid_h])
                    scale([1, pull_w/2, pull_h])
                        rotate([0, 90, 0])
                            cylinder(r = 1, h = 4*lid_wall, center = true);
    }
}

module lid() difference() { lid_shell(); logo_cutter(); }

echo(str("Card Box: inside ", inner_l, " x ", inner_w, " x ", inner_d,
         " mm; outside ", outer_l, " x ", outer_w, " x ",
         base_h + floor_t, " mm closed; base ", base_h, " mm, lid ", lid_h,
         " mm; lip ", lip_t, " mm thick x ", lip_h, " mm"));

// the closed box: the lid turned over onto the base
module closed_lid() translate([0, 0, base_h + floor_t]) rotate([180, 0, 0]) children();

if (part == "base" || part == "assembly")
    color(white) base();
if (part == "lid" || part == "assembly")
    color(white) translate([0, outer_w + gap, 0]) lid();
if (part == "logo" || part == "assembly")
    color(black) translate([0, outer_w + gap, 0]) logo_inlay();
if (part == "closed") {
    color(white) base();
    color("#F2F2F2") closed_lid() lid();
    color(black) closed_lid() logo_inlay();
}

// showcase (render only): closed box on the left; open base with its lid
// beside it, logo up, on the right
module closed_box() {
    color(white) base();
    color("#F2F2F2") closed_lid() lid();
    color(black) closed_lid() logo_inlay();
}
if (part == "showcase") {
    translate([-(outer_l/2 + gap), 0, 0]) closed_box();
    translate([outer_l/2 + gap, 0, 0]) color(white) base();
    translate([outer_l/2 + gap, -(outer_w + gap), -(base_h + floor_t - lid_h)]) {
        color("#F2F2F2") closed_lid() lid();
        color(black) closed_lid() logo_inlay();
    }
}
