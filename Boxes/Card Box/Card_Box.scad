// Card Box - a two-piece box for a deck of playing cards.
// Base tray with thumb notches on the long sides, and a lid that slips over a
// thin lip at the top of the base, flush with the base's outer wall when closed.
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
lip_h  = 12;     // [5:1:30] height of the lip the lid slides over, mm
lid_wall = 1.2;  // [0.8:0.4:2] lid skirt thickness, mm
fit    = 0.2;    // [0:0.05:0.5] radial clearance between lip and lid, mm

/* [Thumb notches] */
notch_w = 24;    // [0:1:50] width of the notch on each long side (0 = none)
notch_d = 16;    // [0:1:40] depth of the notch below the rim

/* [Output] */
part = "assembly"; // [assembly, base, lid, closed, none]

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
assert(notch_d < inner_d - 2, "notch deeper than the box");

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
        // thumb notches: U shape cut from the rim on both long sides
        if (notch_w > 0 && notch_d > 0)
            for (s = [-1, 1])
                translate([0, s*outer_w/2, base_h - notch_d + notch_w/2])
                    rotate([90, 0, 0]) hull() {
                        cylinder(r = notch_w/2, h = 2*wall + 2, center = true);
                        translate([0, notch_d, 0])
                            cube([notch_w, eps, 2*wall + 2], center = true);
                    }
    }
}

// Step 3: the lid, modelled top-down on the bed (open side up)
module lid() {
    difference() {
        rbox(outer_l, outer_w, lid_h, corner_r);
        translate([0, 0, floor_t])
            rbox(outer_l - 2*lid_wall, outer_w - 2*lid_wall, lid_h,
                 corner_r - lid_wall);
    }
}

echo(str("Card Box: inside ", inner_l, " x ", inner_w, " x ", inner_d,
         " mm; outside ", outer_l, " x ", outer_w, " x ",
         base_h + floor_t, " mm closed; base ", base_h, " mm, lid ", lid_h,
         " mm; lip ", lip_t, " mm thick x ", lip_h, " mm"));

if (part == "base" || part == "assembly")
    color("#C12E1F") base();
if (part == "lid" || part == "assembly")
    color("#C12E1F") translate([0, outer_w + gap, 0]) lid();
if (part == "closed") {
    color("#C12E1F") base();
    color("#C12E1F", 0.6)
        translate([0, 0, base_h + floor_t]) mirror([0, 0, 1]) lid();
}
