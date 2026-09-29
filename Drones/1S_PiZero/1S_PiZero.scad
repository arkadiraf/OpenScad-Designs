// 1S Pi Zero drone: a single-18650 quad on a 1.6 mm PCB frame.
//
// The frame is a printed circuit board and the middle of a stack:
//   top      Pi Zero 2 W, on four M2.5 posts of the battery harness
//            the 18650 cell, lying on the PCB; its tabs are soldered to pads at both ends
//   PCB      motors on top at the arm ends; charging/protection and power on the board
//   bottom   the four DYS XSD 7A ESCs, soldered on pin headers under the arms
//            the Crazyflie Bolt on M3 standoffs, with the Flow deck v2 plugged in under it
//            the landing gear, screwed through the frame with the harness
// The frame feeds the Pi over a 1x4 header (5V, GND, TX, RX) and the Bolt over its own pads.
//
// Printed parts: the battery harness (a cover of three hoops that lifts straight off the
// soldered cell, open between them and along the top for airflow, carrying the Pi posts and two
// bosses at the front), the camera harness (a 45-degree pad that
// the camera head's adhesive back sticks to, screwed to those bosses) and the landing gear (an open frame around the
// Bolt, with four legs).
//
// Step 1 is the bought parts, simplified to their envelopes; every size is a Customizer
// variable. Step 2 is the frame and the printed parts, all derived from them.
//
// Axes: x forward (camera side), y left, z up; z = 0 is the underside of the PCB.
//
// Parts: pcb (3D board), pcb_outline (2D, export as DXF for the board house), cradle, cam_mount,
// gear (printed, in flight position), print (the printed parts laid out for the bed), and
// cradle_print / cam_mount_print / gear_print (each one alone in its print orientation).

/* [Battery: 18650] */
bat_d   = 18.4;   // [17:0.1:19] cell diameter
bat_len = 65.2;   // [60:0.1:70] cell length
tab_pad = 3;      // [1:0.5:6] length of the solder pad beyond each end of the cell

/* [Motors and props] */
wheelbase   = 140;  // [100:1:180] motor-to-motor diagonal; 140 keeps the props clear of the Pi and camera
// RCINPOWER GTS V3 1203 drawing: bell 15.76, body 9.9 incl. a 1.4 mm cross-shaped base,
// shaft 1.5 mm protruding 4.8, base holes 4 x M2 in a cross, 9 mm apart across.
motor_base_d = 12;   // [8:0.1:18] span of the cross-shaped base
motor_base_t = 1.4;  // [0.5:0.1:3]
motor_bell_d = 15.76; // [12:0.01:18]
motor_h      = 9.9;  // [6:0.1:18] base to top of bell
motor_shaft  = 4.8;  // [2:0.1:8] shaft above the bell
motor_hole_pcd = 9;  // [6:0.1:12] the M2 holes sit on a circle of this diameter, 90 deg apart
motor_hole_d  = 2.2; // [1.4:0.1:3]
motor_shaft_hole = 4.0; // [0:0.5:7] clearance for the shaft end and its clip under the motor
prop_d      = 63.5; // [50:0.5:80] 2520 = 2.5 inch

/* [ESC: DYS XSD 7A, under the arms] */
// The ESC rests on the plastic of two standard 2.54 mm headers soldered into the frame. The pins
// run down past its two short edges and are soldered to its end pads: 4 at the inner end
// (power, ground, signal), 3 at the motor end (the phases).
esc_l = 16.2;  // [10:0.1:25] DYS: 16.2 x 11 x 4 mm
esc_w = 11;    // [5:0.5:14]
esc_t = 4;     // [1:0.5:6] board + parts
esc_board_t = 1.0;   // [0.6:0.1:1.6] the ESC's own PCB
esc_pins_in  = 4;    // [2:1:6] pins at the inner end
esc_pins_out = 3;    // [2:1:6] pins at the motor end
pitch        = 2.54;
header_h     = 2.5;  // [1:0.1:4] standard header plastic
pin_gap      = 0.3;  // [0:0.1:1] ESC edge to the pin face
esc_radius = 47;     // [30:0.5:60] distance of the ESC centre from the frame centre

/* [Flight controller: Crazyflie Bolt, under the frame] */
// Bolt 1.1 drawing: 36 x 35.4 mm, 3.1 mm holes on 30.5 x 30.5, FRONT arrow along +x, deck
// connectors P6 / P11 (1x10 each) running along x, 17 mm apart.
fc_size   = [36, 35.4]; // board x (front) and y
fc_holes  = 30.5; // [20:0.5:32] M3 square mounting pattern
fc_hole_d = 2.7;  // [2:0.1:3.5] frame hole for the M2.5 screws (Bolt's own: 3.1)
fc_standoff = 5;  // [3:0.5:12]
fc_deck_rows = 17; // [10:0.1:25] deck connector rows, centre to centre

/* [Flow deck v2, under the Bolt] */
flow_deck = true;
deck_l = 28;   // [15:0.5:35] along the connector rows (x)
deck_w = 21;   // [15:0.5:30] across them (y)
deck_gap = 8;  // [4:0.5:15] Bolt to deck, the deck connector height

/* [PCB frame] */
pcb_t     = 1.6;  // [0.8:0.1:2]
center_l  = 80;   // [60:1:100] centre plate length (x)
center_w  = 44;   // [40:1:60] centre plate width (y)
arm_w     = 12;   // [6:0.5:16] at least the ESC width
motor_pad_r = 9;  // [6:0.5:14]
corner_r  = 4;    // [0:0.5:10]
arm_fillet = 3;   // [0:0.5:8] where the arms meet the centre plate; small, to stay out of the prop wash

/* [Pi Zero 2 W, on top] */
pi_l = 65;   // [60:0.5:70]
pi_w = 30;   // [25:0.5:35]
pi_hole_x = 58;  // [50:0.5:62]
pi_hole_y = 23;  // [18:0.5:28]
pi_t = 1.4;
pi_gap = 2.0;   // [1:0.5:6] between the harness top and the Pi's underside

/* [Camera: Waveshare RPi Zero v1.3, flex strip with adhesive back] */
cam_w      = 9;   // [6:0.5:14] width of the camera head (and of the flex there)
cam_head_l = 11;  // [6:0.5:20] length of the head along the flex, the part glued down
cam_lens   = 8;   // [5:0.5:10] lens housing, square
cam_lens_h = 5;   // [2:0.5:8] lens housing height above the flex
cam_flex_len = 60; // [30:1:120] flex from the head to the Pi connector (display only)
cam_flex_up = true; // the flex leaves the head at the top edge of the pad (false: bottom edge)
cam_tilt = 45;    // [0:5:90] degrees below the horizon
cam_reach = 16;   // [4:0.5:30] distance of the camera centre in front of the harness block; puts the
                  // lens in front of the prop guard's front bridge
boss_z = 9;       // [6:0.5:22] height of the camera harness screws (the front blocks end 3 mm above);
                  // low, so the harness passes under the guard's front beam

/* [Harness] */
wall      = 2.0;  // [1.2:0.2:4] hoop and plate thickness
hoop_w    = 5;    // [3:0.5:10] width of each hoop over the cell
rail_w    = 6;    // [4:0.5:8]
rail_h    = 2;    // [1.5:0.5:4]

/* [Landing gear] */
gear_t    = 2;    // [1.5:0.5:4]
gear_bar  = 3;    // [2:0.5:6] width of the frame bars
leg_r     = 2.2;  // [1.5:0.1:4]
foot_x    = 42;   // [30:1:60]
foot_y    = 34;   // [20:1:50]
ground_clear = 10; // [4:1:30] under the Flow deck

/* [Prop guard (optional)] */
// One printed frame under the PCB: a pad under each motor, held by the motor screws (which get
// longer), three spokes out of the prop wash of the frame, and a band close round each prop on
// posts. Printed upright with no supports: posts and bridges stand on the bed, and the band
// comes down onto each post in 45-degree arches.
prop_guard  = true;
guard_gap   = 1.5;   // [0.5:0.25:5] prop tip to the band
guard_wall  = 1.2;   // [0.8:0.2:2.4] band and bridge thickness (3 lines)
guard_t     = 1.6;   // [1:0.2:3] pad and spoke thickness, under the frame
guard_below = 2.5;   // [1:0.5:6] band below the prop plane
guard_above = 4.5;   // [2:0.5:10] band above the prop plane
guard_posts = 12;    // [6:1:24] posts per ring, where they clear the frame
guard_cover = 270;   // [180:15:360] degrees of each prop the band covers; the gap faces the frame centre
guard_beam  = 2.5;   // [1.5:0.5:5] depth of the front bridge's top beam, over the camera
spoke_w     = 2.5;   // [1.5:0.5:5]

/* [Connectors: JST] */
// Power over JST PH (2.0 mm, 2 pins, through-hole, vertical); UART over JST GH (1.25 mm, 3 pins:
// TX, RX, GND; SMD, side entry, so it leaves no holes in the outline). The Pi's pair is on the
// top next to its GPIO end; the Bolt's pair is on the underside behind it.
ph_pitch = 2.0;
ph_hole  = 0.8;   // [0.6:0.05:1.2] drill for the PH pins
ph_body  = [4.5, 6.0];   // [depth, height] of a B2B-PH-K-S header; width = (n - 1) x pitch + 4
gh_pitch = 1.25;
gh_body  = [4.25, 4.25]; // [depth, height] of an SMxxB-GHS-TB header; width = (n - 1) x pitch + 4.25 (tabs)

/* [Hardware] */
// Every screw that goes into a printed part goes into a brass heat-set insert, since the cover
// comes off whenever the cell or the Pi is serviced. The Bolt hangs on nylon screws, spacers and
// nuts (light, and they keep metal away from its IMU). Screw lengths are picked below from the
// stack each one clamps.
ins_m2  = [3.6, 3.0, 3.2];   // M2 insert: outside diameter, length, hole to melt it into
ins_m25 = [4.0, 4.0, 3.6];   // M2.5 insert, in the top of each Pi post
motor_thread = 2.0;          // [1:0.5:4] usable thread depth in the motor base
show_hardware = true;

/* [Output] */
part = "assembly"; // [assembly, pcb, pcb_outline, cradle, cam_mount, gear, guard, print, cradle_print, cam_mount_print, gear_print, guard_print, none]
show_props = true;
show_electronics = true;

/* [Hidden] */
echo_dims = false;   // set by 1S_PiZero_verify.py
slice_z   = 5;       // height of part="cradle_slice", for the same script
echo_bom  = false;   // set by 1S_PiZero_bom.py
clash     = "pcb";   // body tested by part="guard_clash"
$fn = 40;
eps = 0.01;
L        = wheelbase / (2 * sqrt(2));          // motor x and y
motors   = [[L, L], [L, -L], [-L, -L], [-L, L]];
bat_r    = bat_d / 2;
fit_r    = bat_r + 0.25;                        // cell clearance inside the hoops
z_bc     = pcb_t + bat_r;                       // cell axis: the cell lies on the PCB
hoop_x   = [-pi_hole_x / 2, 0, pi_hole_x / 2];  // the outer hoops carry the Pi posts
rail_in  = fit_r;                                // rails outside the cell, so the cover lifts off
// M2 through cover, PCB and gear: just outside the rails, so the front ones clear the camera
// blocks and a driver reaches them past the Pi's edge
// ... and at x = +-24, clear of the prop guard's rings, which pass over the frame's corners
crad_hole = [24, rail_in + rail_w + 2.05];
rail_end = bat_len / 2 + 5;                      // rails run past the cell ends, under the gables
hoop_top = z_bc + fit_r + 1 + wall;              // flat top of the hoops
z_pi_bot = hoop_top + pi_gap;
z_pi_top = z_pi_bot + pi_t;
post_top = z_pi_bot;                             // the Pi sits on the printed posts, screwed into inserts
post_y   = pi_hole_y / 2;
block_t  = 4;                                    // camera harness block
prop_z   = pcb_t + motor_h + 0.5;                // prop hub on the shaft, just above the bell
z_fc     = -fc_standoff - 1.6;                   // Bolt board bottom
z_deck   = z_fc - deck_gap - 1;                  // deck board bottom
z_sensor = z_deck - 2;                           // lowest point of the deck
z_foot   = (flow_deck ? z_sensor : z_fc - 2) - ground_clear;
gear_x   = rail_end;                             // gear frame outer half-length
gear_y   = center_w / 2 - 0.5;

// Frame connectors: [name, side, type, pins, [x, y], rotation, signals]
connectors = [
    ["J1 Pi power", "top",    "PH", 2, [-6, center_w / 2 - 3],    0,  "5V, GND"],
    ["J2 Pi UART",  "top",    "GH", 3, [5, center_w / 2 - 2.5],   0,  "TX, RX, GND"],
    ["J3 Bolt power", "bottom", "PH", 2, [-25, 7],               90, "VBAT, GND"],
    ["J4 Bolt UART",  "bottom", "GH", 3, [-25, -7],              90, "TX, RX, GND"]
];

// Camera placement: centre in front of the block, lens along cam_n.
cam_c = [rail_end + block_t + cam_reach, 0, boss_z - 5];

// --------------------------------------------------------------------------------------------
// Library

module rrect(size, r) {
    offset(r) square([size[0] - 2 * r, size[1] - 2 * r], center = true);
}
module rbox(size, r, h) linear_extrude(h) rrect(size, r);
module rod(a, b, r) hull() { translate(a) sphere(r, $fn = 16); translate(b) sphere(r, $fn = 16); }
function arm_dir(m) = m / norm(m);
function perp(u) = [-u[1], u[0]];

// Two header rows just past the ESC's short edges: esc_pins_in at the inner end, esc_pins_out
// at the motor end. esc_row(m, s) is the centre of a row (s = -1 inner, +1 outer).
row_off = esc_l / 2 + pin_gap + 0.32;                // ESC centre to a row's pin centres
function esc_row(m, s) = (esc_radius + s * row_off) * arm_dir(m);
function row_n(s) = s < 0 ? esc_pins_in : esc_pins_out;
function esc_pins(m) = let(p = perp(arm_dir(m)))
    [for (s = [-1, 1]) for (k = [0:row_n(s) - 1]) esc_row(m, s) + (k - (row_n(s) - 1) / 2) * pitch * p];

// JST connectors: pin positions in plan, and a simplified body on the frame's top or underside.
function conn_pitch(c) = c[2] == "PH" ? ph_pitch : gh_pitch;
function conn_size(c) = c[2] == "PH" ? [(c[3] - 1) * ph_pitch + 4, ph_body[0], ph_body[1]]
                                     : [(c[3] - 1) * gh_pitch + 4.25, gh_body[0], gh_body[1]];
function conn_pins(c) = [for (k = [0:c[3] - 1]) let(u = (k - (c[3] - 1) / 2) * conn_pitch(c))
    c[4] + u * [cos(c[5]), sin(c[5])]];
module connector(c) let(s = conn_size(c), top = c[1] == "top")
    translate(concat(c[4], top ? pcb_t : -s[2])) rotate(c[5])
        color(c[2] == "PH" ? "WhiteSmoke" : "Wheat") translate([-s[0] / 2, -s[1] / 2, 0]) cube(s);

// Closest distance in plan from any prop disc edge to a point (negative: under the disc).
function prop_clear(p) = min([for (m = motors) norm(m - p)]) - prop_d / 2;

// --------------------------------------------------------------------------------------------
// Step 1: bought parts, simplified

module battery() {
    color("SteelBlue") translate([0, 0, z_bc]) rotate([0, 90, 0]) cylinder(d = bat_d, h = bat_len, center = true);
    color("Silver") for (s = [-1, 1])                                   // nickel tabs down to the pads
        translate([s * (bat_len / 2 + 0.2) - 0.2, -4, pcb_t]) cube([0.4, 8, bat_r]);
}

module motor(m) translate([m[0], m[1], pcb_t]) {
    color("DimGray") for (a = [0, 90]) rotate(a + atan2(m[1], m[0]) + 45)
        translate([-motor_base_d / 2, -2, 0]) cube([motor_base_d, 4, motor_base_t]);    // cross base
    color("Silver") translate([0, 0, motor_base_t]) cylinder(d = motor_bell_d, h = motor_h - motor_base_t);
    color("Silver") cylinder(d = 1.5, h = motor_h + motor_shaft);
}

module prop(m) translate([m[0], m[1], prop_z]) {
    color("Black") cylinder(d = 6, h = 5);
    %cylinder(d = prop_d, h = 1);
}

// Hanging under the arm: header plastic against the PCB, the ESC board on the plastic with its
// parts facing down, the pins passing its edges and soldered to its end pads.
module esc(m) let(u = arm_dir(m), a = atan2(u[1], u[0]), zb = -header_h - esc_board_t) {
    translate(concat(esc_radius * u, 0)) rotate(a) {
        color("RoyalBlue") translate([-esc_l / 2, -esc_w / 2, zb]) cube([esc_l, esc_w, esc_board_t]);
        color("Black") translate([-esc_l / 2 + 2.5, -esc_w / 2 + 1.5, zb - (esc_t - esc_board_t)])
            cube([esc_l - 5, esc_w - 3, esc_t - esc_board_t]);           // FETs and MCU
    }
    for (s = [-1, 1]) translate(concat(esc_row(m, s), -header_h)) rotate(a) color("Black")
        translate([-pitch / 2, -row_n(s) * pitch / 2, 0]) cube([pitch, row_n(s) * pitch, header_h]);
    for (p = esc_pins(m)) translate(concat(p, zb - 1.5)) color("Gold")
        translate([-0.32, -0.32, 0]) cube([0.64, 0.64, -zb + 1.5 + pcb_t + 1.5]);
}

module flight_controller() {                     // its screws, spacers and nuts are in hardware()
    translate([0, 0, z_fc]) {
        color("MediumPurple") difference() {
            rbox(fc_size, 2, 1.6);
            for (i = [-1, 1], j = [-1, 1]) translate([i * fc_holes / 2, j * fc_holes / 2, -1])
                cylinder(d = 3.1, h = 4, $fn = 20);
        }
        color("Black") translate([-5, -5, 1.6]) cube([10, 10, 1.2]);   // MCU; UP faces the frame
        color("White") for (i = [-1, 1], j = [-1, 1])                   // motor connectors P7-P10
            translate([i * (fc_size[0] / 2 - 3) - 3, j * 9 - 2.5, 1.6]) cube([6, 5, 3]);
    }
}

// Plugged into the Bolt's deck connectors P6 / P11 (1x10 along x, fc_deck_rows apart).
module flow_deck_board() {
    for (j = [-1, 1]) color("Black")
        translate([-12.7, j * fc_deck_rows / 2 - 1.25, z_deck + 1]) cube([25.4, 2.5, deck_gap]);
    translate([0, 0, z_deck]) {
        color("DarkSlateGray") translate([-deck_l / 2, -deck_w / 2, 0]) cube([deck_l, deck_w, 1]);
        color("Black") translate([-2.5, -2.5, -2]) cube([5, 5, 2]);     // PMW3901 + VL53L1x, facing down
        color("Black") translate([4, -2, -1.5]) cube([3, 4, 1.5]);
    }
}

module pi_zero() translate([0, 0, z_pi_bot]) {
    color("ForestGreen") difference() {
        rbox([pi_l, pi_w], 3, pi_t);
        for (i = [-1, 1], j = [-1, 1]) translate([i * pi_hole_x / 2, j * pi_hole_y / 2, -1])
            cylinder(d = 2.75, h = pi_t + 2);
    }
    translate([0, 0, pi_t]) {
        color("Silver") translate([-6, -6, 0]) cube([12, 12, 1.2]);                     // SoC
        color("Black") translate([pi_l / 2 - 4, -8.5, 0]) cube([4, 17, 1.2]);           // camera connector
        color("Silver") translate([-pi_l / 2 - 1, -6, -pi_t - 1.2]) cube([12, 12, 1.2]); // SD card, underside
        // mini HDMI at 12.4, micro USB at 41.4 and 54 mm from the left (SD) end
        color("Silver") translate([-pi_l / 2 + 12.4 - 5.6, -pi_w / 2 - 0.5, 0]) cube([11.2, 7.5, 3.3]);
        color("Silver") for (x = [41.4, 54]) translate([-pi_l / 2 + x - 3.8, -pi_w / 2 - 1, 0]) cube([7.6, 5.6, 2.6]);
        color("Goldenrod") translate([-25.4, pi_w / 2 - 3.5 - 2.54, -eps]) cube([50.8, 5.08, 0.1]);  // GPIO pads
    }
}

// Local frame of the camera head: flex in the xy plane, lens along +z, the flex leaves at +x.
// With cam_flex_up, +x is the pad's upper edge and the flex runs up and back over the harness
// to the Pi's camera connector; otherwise it leaves at the lower edge and loops up.
cam_flip = cam_flex_up ? 180 : 0;
module at_camera() translate(cam_c) rotate([0, 90 + cam_tilt, 0]) rotate(cam_flip) children();
function cam_local(p) = cam_c + [[cos(90 + cam_tilt), 0, sin(90 + cam_tilt)], [0, 1, 0],
                                 [-sin(90 + cam_tilt), 0, cos(90 + cam_tilt)]]
                              * [cos(cam_flip) * p[0], cos(cam_flip) * p[1], p[2]];

module strip(a, b, w) hull() { translate(a) cube([0.3, w, 0.3], center = true); translate(b) cube([0.3, w, 0.3], center = true); }

module camera() {
    at_camera() {
        color("Orange") translate([-cam_head_l / 2, -cam_w / 2, 0]) cube([cam_head_l, cam_w, 0.3]);
        color("Black") translate([-cam_lens / 2, -cam_lens / 2, 0.3]) cube([cam_lens, cam_lens, cam_lens_h - 1]);
        color("Black") translate([0, 0, cam_lens_h - 0.7]) cylinder(d = cam_lens * 0.75, h = 0.7);
    }
    // the flex, drawn as a loose run from the head to the Pi's camera connector
    exit = cam_local([cam_head_l / 2 + 4, 0, 0]);
    pi_c = [pi_l / 2 - 2, 0, z_pi_top + 0.6];
    top  = max(exit[2], pi_c[2]) + 3;
    color("Orange") {
        strip(cam_local([cam_head_l / 2, 0, 0]), exit, cam_w);
        strip(exit, [exit[0] - 3, 0, top], cam_w);
        strip([exit[0] - 3, 0, top], [pi_c[0] + 6, 0, top], cam_w);
        strip([pi_c[0] + 6, 0, top], pi_c, cam_w);
    }
}

// --------------------------------------------------------------------------------------------
// Step 2a: the PCB frame

module pcb_shape() difference() {
    // closing (grow, then shrink by the same radius) rounds only the inside corners: the arm roots
    offset(r = -arm_fillet) offset(r = arm_fillet) union() {
        rrect([center_l, center_w], corner_r);
        for (m = motors) hull() {
            translate(0.25 * m) circle(d = arm_w);
            translate(m) circle(r = motor_pad_r);
        }
    }
    for (m = motors) translate(m) {
        circle(d = motor_shaft_hole);
        for (a = [0:90:270]) rotate(a + atan2(m[1], m[0]) + 45)
            translate([motor_hole_pcd / 2, 0]) circle(d = motor_hole_d, $fn = 16);
    }
    for (m = motors) for (p = esc_pins(m)) translate(p) circle(d = 1.0, $fn = 12);
    for (i = [-1, 1], j = [-1, 1]) {
        translate([i * fc_holes / 2, j * fc_holes / 2]) circle(d = fc_hole_d, $fn = 20);
        translate([i * crad_hole[0], j * crad_hole[1]]) circle(d = 2.2, $fn = 16);
    }
    for (c = connectors) if (c[2] == "PH") for (p = conn_pins(c)) translate(p) circle(d = ph_hole, $fn = 12);
}

module pcb() {
    color("DarkGreen") linear_extrude(pcb_t) pcb_shape();
    for (c = connectors) connector(c);
    color("Gold") for (s = [-1, 1])                                     // BAT+ / BAT- tab pads
        translate([s * (bat_len / 2 + tab_pad / 2 - 0.5), 0, pcb_t]) cube([tab_pad, 10, 0.05], center = true);
}

// --------------------------------------------------------------------------------------------
// Step 2b: the battery harness, a cover over the soldered cell
//
// The cell is soldered to the frame, so the harness is a cover that lifts straight off it: below
// the cell's widest point its walls are vertical and the rails stand outside the cell, so nothing
// reaches under it. Four M2 screws through the rails hold it (and the landing gear) to the frame.

// Hoop section in (y, z - z_bc): straight walls up to the cell's equator, then a 45-degree roof,
// left open along the top, so it prints upright without a ceiling and vents the cell.
top_slot = 2 * (fit_r * sqrt(2) - (fit_r + 1));
module hoop_inner2d() union() {
    intersection() {
        hull() { circle(fit_r, $fn = 64); translate([0, fit_r * sqrt(2)]) square(0.01, center = true); }
        translate([-50, 0]) square([100, fit_r + 1]);
    }
    translate([-fit_r, -fit_r - 1]) square([2 * fit_r, fit_r + 1 + eps]);
}

module hoop() rotate([90, 0, 90]) linear_extrude(hoop_w, center = true) difference() {
    offset(r = wall) hoop_inner2d();
    hoop_inner2d();
    translate([-top_slot / 2, 0]) square([top_slot, 2 * fit_r]);
}

// Past each end of the cell a closed 45-degree gable ties the two sides together (the slotted
// hoops alone would leave them as separate pieces). It stands over the tab and its pad.
gable_t = 3;
gable_x = bat_len / 2 + 0.6 + gable_t / 2;
module gable_inner2d() polygon([[-fit_r, -fit_r - 1], [-fit_r, 0], [0, fit_r], [fit_r, 0], [fit_r, -fit_r - 1]]);
module gable() rotate([90, 0, 90]) linear_extrude(gable_t, center = true) difference() {
    offset(delta = wall) gable_inner2d();
    gable_inner2d();
}

module cradle() difference() {
    union() {
        for (x = hoop_x) translate([x, 0, z_bc]) hoop();
        for (s = [-1, 1]) translate([s * gable_x, 0, z_bc]) gable();
        for (j = [-1, 1]) {
            translate([-rail_end, j > 0 ? rail_in : -rail_in - rail_w, pcb_t]) cube([2 * rail_end, rail_w, rail_h]);
            for (i = [-1, 1]) translate([i * crad_hole[0], j * crad_hole[1], pcb_t])
                cylinder(d = 6, h = rail_h + 2);                         // screw bosses
            for (i = [-1, 1]) translate([i * pi_hole_x / 2, j * post_y, pcb_t])
                cylinder(d = ins_m25[0] + 2.6, h = post_top - pcb_t);   // Pi posts, an insert in each top
            // block for the camera harness screws, in front of the front post
            translate([pi_hole_x / 2, j > 0 ? post_y - 3 : -post_y - 3, pcb_t])
                cube([rail_end - pi_hole_x / 2, 6, boss_z + 3 - pcb_t]);
        }
    }
    translate([0, 0, z_bc]) rotate([90, 0, 90]) linear_extrude(bat_len + 1, center = true)
        hoop_inner2d();                                                 // the lift-off envelope of the cell
    translate([0, 0, pcb_t - 5]) cube([4 * rail_end, 4 * rail_end, 10], center = true);  // below the PCB top
    for (i = [-1, 1], j = [-1, 1]) {
        translate([i * crad_hole[0], j * crad_hole[1], 0]) cylinder(d = 2.3, h = 20, $fn = 16);   // M2 through
        translate([i * pi_hole_x / 2, j * post_y, post_top - ins_m25[1] - 0.5])
            cylinder(d = ins_m25[2], h = ins_m25[1] + 1, $fn = 20);     // M2.5 insert for the Pi
        translate([i * pi_hole_x / 2, j * post_y, post_top - ins_m25[1] - 2])
            cylinder(d = 2.6, h = 2, $fn = 16);                          // room for the screw tip
        translate([i * fc_holes / 2, j * fc_holes / 2, 0]) cylinder(d = 6.5, h = 10);            // Bolt screw heads
    }
    for (j = [-1, 1]) translate([rail_end + eps, j * post_y, boss_z]) rotate([0, -90, 0])
        cylinder(d = ins_m2[2], h = ins_m2[1] + 1.5, $fn = 20);        // M2 insert for the camera harness
}

// --------------------------------------------------------------------------------------------
// Step 2c: the camera harness

module cam_block() difference() {
    translate([rail_end, -(post_y + 3), boss_z - 3]) cube([block_t, 2 * (post_y + 3), 6]);
    for (j = [-1, 1]) translate([rail_end + block_t / 2, j * post_y, boss_z]) rotate([0, 90, 0])
        cylinder(d = 2.3, h = block_t + 2, center = true, $fn = 16);
}

// The pad the head's adhesive back sticks to, 1 mm wider than the head all round. Borders on
// both sides and at the lens end (opposite the flex; the bottom edge when cam_flex_up) locate
// the head; the flex end stays open.
cam_border_h = 1.5;
pad = [cam_head_l + 2, cam_w + 2];
module cam_plate() at_camera() {
    translate([-pad[0] / 2, -pad[1] / 2, -wall]) cube([pad[0], pad[1], wall]);
    translate([-pad[0] / 2, -pad[1] / 2, -eps]) cube([1, pad[1], cam_border_h]);          // lens end
    for (j = [-1, 1]) translate([-pad[0] / 2, j > 0 ? pad[1] / 2 - 1 : -pad[1] / 2, -eps])
        cube([pad[0], 1, cam_border_h]);                                                 // sides
}

module cam_mount() {
    cam_block();
    cam_plate();
    // two webs from the block to the back of the pad, inside the screw heads so a driver reaches them
    web_y = post_y - 3.8 / 2 - 0.8 - 2.5;          // outer edge clear of the head (3.8) by 0.8
    for (j = [-1, 1]) hull() {
        translate([rail_end + block_t - 1, j * (web_y + 1.25) - 1.25, boss_z - 3]) cube([1, 2.5, 6]);
        at_camera() translate([-pad[0] / 2, j * (pad[1] / 2 - 1) - 1, -wall]) cube([pad[0], 2, 0.5]);
    }
}

// --------------------------------------------------------------------------------------------
// Step 2d: the landing gear, an open frame under the PCB around the Bolt

function leg_top(i, j) = [i * (gear_x - 1.5), j * (gear_y - 1.5), -1.5];
function leg_foot(i, j) = [i * foot_x, j * foot_y, z_foot + leg_r];

module gear() difference() {
    union() {
        translate([0, 0, -gear_t]) linear_extrude(gear_t) difference() {
            rrect([2 * gear_x, 2 * gear_y], 3);
            rrect([2 * (gear_x - 2 * gear_bar), 2 * (gear_y - gear_bar)], 1.5);
        }
        for (i = [-1, 1], j = [-1, 1]) {
            translate([i * crad_hole[0], j * crad_hole[1], -ins_m2[1] - 1.5])
                cylinder(d = ins_m2[0] + 3, h = ins_m2[1] + 1.5 + eps);   // insert boss
            rod(leg_top(i, j), leg_foot(i, j), leg_r);
            translate([i * foot_x, j * foot_y, z_foot]) cylinder(r1 = 3.5, r2 = 0.9 * leg_r, h = 3);
        }
    }
    translate([0, 0, 5]) cube([200, 200, 10], center = true);            // flush with the PCB underside
    for (i = [-1, 1], j = [-1, 1]) translate([i * crad_hole[0], j * crad_hole[1], -ins_m2[1] - 0.5])
        cylinder(d = ins_m2[2], h = 5, $fn = 20);                       // M2 insert, pressed in from the top
}

// --------------------------------------------------------------------------------------------
// Step 2e: the prop guard (optional)

g_r0  = prop_d / 2 + guard_gap;                  // band inside
g_r1  = g_r0 + guard_wall;
g_rm  = (g_r0 + g_r1) / 2;
z_gbed = -guard_t;                               // pads, spokes, posts and bridges stand here
z_gb0 = prop_z - guard_below;                    // band bottom between the posts
z_gb1 = prop_z + guard_above;                    // band top
post_w = 2.5;                                    // along the band

function dist_seg(p, a, b) = let(d = b - a, t = max(0, min(1, ((p - a) * d) / (d * d)))) norm(p - (a + t * d));
function xy(p) = [p[0], p[1]];
// Anything a post or the band's lower part would hit: the PCB outline (plus a margin), the
// landing gear legs, the camera harness.
function over_frame(p, m) =
    (abs(p[0]) <= center_l / 2 + m && abs(p[1]) <= center_w / 2 + m)
    || min([for (mm = motors) dist_seg(p, 0.25 * mm, mm)]) <= arm_w / 2 + arm_fillet + m
    || min([for (mm = motors) norm(p - mm)]) <= motor_pad_r + m
    || min([for (i = [-1, 1], j = [-1, 1]) dist_seg(p, xy(leg_top(i, j)), xy(leg_foot(i, j)))]) <= leg_r + 3 + m
    || (p[0] >= rail_end - 1 && abs(p[1]) <= post_y + 3 + m);

function ring_pt(m, a, r) = m + r * [cos(a), sin(a)];
function outward(m) = atan2(m[1], m[0]);
// The band covers guard_cover degrees centred on the outward direction; its open side faces the
// frame centre, and its ends meet the bridges.
function arc_a0(m) = outward(m) - guard_cover / 2;
function arc_a1(m) = outward(m) + guard_cover / 2;
function in_arc(m, a) = adiff(a, outward(m)) <= guard_cover / 2 + 0.01;
// posts: every 360/guard_posts degrees from the outward direction, inside the arc and clear of
// the frame, plus one at each end of the arc; the three spoke ends (outward and +-60 degrees)
// are among them
function guard_post_angles(m) = concat(
    [for (k = [0:guard_posts - 1]) let(a = outward(m) + k * 360 / guard_posts)
        if (in_arc(m, a) && !over_frame(ring_pt(m, a, g_rm), 1.5)) a],
    [for (a = [arc_a0(m), arc_a1(m)]) if (!over_frame(ring_pt(m, a, g_rm), 1.5)) a]);
function adiff(a, b) = abs((a - b + 540) % 360 - 180);

// the band's lower edge at angle a: down to the bed on a post, rising at 45 degrees away from it,
// never lower than z_gb0 where it passes over the frame
function band_low(m, a, posts) = let(
        d = min([for (pa = posts) adiff(a, pa)]) * PI / 180 * g_rm,
        slope = d <= post_w / 2 ? z_gbed : z_gbed + (d - post_w / 2),
        keep = over_frame(ring_pt(m, a, g_rm), 1.5) ? z_gb0 : z_gbed)
    min(z_gb0, max(slope, keep));

module guard_band(m) let(posts = guard_post_angles(m), n = ceil(guard_cover / 2.5)) for (i = [0:n - 1]) {
    a0 = arc_a0(m) + guard_cover * i / n; a1 = arc_a0(m) + guard_cover * (i + 1) / n;
    hull() for (a = [a0, a1], r = [g_r0, g_r1], z = [band_low(m, a, posts), z_gb1])
        translate(concat(ring_pt(m, a, r), z)) cube(0.01, center = true);
}

module guard_pad(m) translate(concat(m, z_gbed)) difference() {
    cylinder(r = motor_pad_r, h = guard_t);
    translate([0, 0, -1]) cylinder(d = motor_shaft_hole, h = guard_t + 2);
    for (a = [0:90:270]) rotate(a + outward(m) + 45) translate([motor_hole_pcd / 2, 0, -1])
        cylinder(d = motor_hole_d, h = guard_t + 2, $fn = 16);
}

module guard_spokes(m) for (s = [-60, 0, 60]) hull() {
    translate(concat(ring_pt(m, outward(m) + s, motor_pad_r - 1), z_gbed)) cylinder(d = spoke_w, h = guard_t, $fn = 12);
    translate(concat(ring_pt(m, outward(m) + s, g_rm), z_gbed)) cylinder(d = spoke_w, h = guard_t, $fn = 12);
}

// Bridges tie the arc ends together on all four sides, so the guard is one closed outline. Each
// is a wall standing on the bed with a window: a pointed one (45-degree roof) on the sides and
// back; at the front a full-width opening under a top beam, which the camera harness passes
// under, with the lens out in front of it.
module guard_bridge(a, b, front = false) let(d = b - a, len = norm(d), ang = atan2(d[1], d[0]), w = len / 2 - 2.5)
    translate(concat(a, 0)) rotate(ang) rotate([90, 0, 0])
        linear_extrude(guard_wall, center = true) difference() {
            translate([0, z_gbed]) square([len, z_gb1 - z_gbed]);
            translate([len / 2, 0]) polygon(front
                ? [[-w, z_gbed - 1], [w, z_gbed - 1], [w, z_gb1 - guard_beam], [-w, z_gb1 - guard_beam]]
                : [[-w, z_gbed - 1], [w, z_gbed - 1], [w, z_gb1 - 2 - w], [0, z_gb1 - 2], [-w, z_gb1 - 2 - w]]);
        }

g_e = L - g_rm;                                          // where the arc ends cross the side lines
module prop_guard_frame() {
    for (m = motors) {
        guard_band(m);
        guard_pad(m);
        guard_spokes(m);
    }
    for (s = [-1, 1]) guard_bridge([-g_e - 0.5, s * L], [g_e + 0.5, s * L]);   // sides
    guard_bridge([-L, -g_e - 0.5], [-L, g_e + 0.5]);                            // back
    guard_bridge([L, -g_e - 0.5], [L, g_e + 0.5], front = true);                // front, over the camera
}

// The camera's view: a pyramid from the lens along its axis, 54 x 41 degrees (OV5647), 150 mm.
module cam_view() let(n = [cos(cam_tilt), 0, -sin(cam_tilt)], up = [sin(cam_tilt), 0, cos(cam_tilt)],
                      o = cam_local([0, 0, cam_lens_h]), D = 150, h = D * tan(27), v = D * tan(20.5))
    hull() {
        translate(o) cube(0.1, center = true);
        for (i = [-1, 1], j = [-1, 1]) translate(o + D * n + i * h * [0, 1, 0] + j * v * up) cube(0.1, center = true);
    }

// --------------------------------------------------------------------------------------------
// Step 2f: hardware
//
// Each screw is the longest standard length that still ends inside its insert (or nut), and at
// least 1.5 mm past the parts it clamps.

std_len = [3, 4, 5, 6, 8, 10, 12, 14, 16, 20];
function pick(lo, hi) = let(ok = [for (l = std_len) if (l >= lo && l <= hi) l])
    assert(len(ok) > 0, str("no standard screw between ", lo, " and ", hi, " mm")) ok[len(ok) - 1];

cover_head = pcb_t + rail_h + 2;                  // top of the cover's screw bosses
len_cover  = pick(cover_head + 1.5, cover_head + ins_m2[1] - 0.3);        // M2: cover + PCB + gear insert
len_pi     = pick(pi_t + 1.5, pi_t + ins_m25[1] - 0.3);                   // M2.5: Pi into its post insert
len_cam    = pick(block_t + 1.5, block_t + ins_m2[1] - 0.3);              // M2: camera harness into cover
len_motor  = pick(pcb_t + 1, pcb_t + motor_thread);                       // M2: from under the frame
len_motor_g = pick(guard_t + pcb_t + 1, guard_t + pcb_t + motor_thread);  // the same through the guard's pads
len_motor_used = prop_guard ? len_motor_g : len_motor;
len_fc     = pick(pcb_t + 1.5, pcb_t + fc_standoff / 2);                  // M2.5: frame / Bolt into its standoff

// Masses from the geometry: shank (x0.85 for the thread) + head (x0.8 for the socket).
STEEL = 7.85e-3; BRASS = 8.5e-3; NYLON = 1.14e-3;   // g/mm^3
function screw_g(d, l, dk, k, rho) = (PI * d * d / 4 * l * 0.85 + PI * dk * dk / 4 * k * 0.8) * rho;
function insert_g(ins, d) = PI * (ins[0] * ins[0] - d * d) / 4 * ins[1] * BRASS;
function nut_g(s, m, d, rho) = (0.866 * s * s - PI * d * d / 4) * m * rho;
function tube_g(od, id, l, rho) = PI * (od * od - id * id) / 4 * l * rho;
function standoff_g(l, male, rho) = (0.866 * 25 - PI * 2.5 * 2.5 / 4) * l * rho + PI * 2.5 * 2.5 / 4 * male * 0.85 * rho;
COPPER = 8.96e-3; PVC = 1.4e-3; PA66 = 1.14e-3;
// cable: n wires of copper area a (mm^2) and outside diameter od, length l, plus a plug at each end
function cable_g(n, a, od, l, plug) = n * l * (a * COPPER + (PI * od * od / 4 - a) * PVC) + 2 * plug;
function header_g(c) = let(s = conn_size(c)) s[0] * s[1] * s[2] * 0.4 * PA66 + c[3] * 0.64 * 0.64 * (s[2] + 3.4) * BRASS;
cable_len = 60;   // mm, each connector's lead

// [item, qty, g each, where]
hardware_list = [
    [str("M2 x ", len_cover, " socket head screw, steel"), 4, screw_g(2, len_cover, 3.8, 2, STEEL), "battery cover + PCB + landing gear"],
    ["M2 heat-set insert, brass", 4, insert_g(ins_m2, 2), "landing gear bosses"],
    [str("M2.5 x ", len_pi, " socket head screw, steel"), 4, screw_g(2.5, len_pi, 4.5, 2.5, STEEL), "Pi Zero into the cover posts"],
    ["M2.5 heat-set insert, brass", 4, insert_g(ins_m25, 2.5), "cover posts"],
    [str("M2 x ", len_cam, " socket head screw, steel"), 2, screw_g(2, len_cam, 3.8, 2, STEEL), "camera harness to the cover"],
    ["M2 heat-set insert, brass", 2, insert_g(ins_m2, 2), "cover front blocks"],
    [str("M2 x ", len_motor, " screw, steel (check against the motor's own)"), 16, screw_g(2, len_motor, 3.8, 1.5, STEEL), "motors, from under the frame (no guard)"],
    [str("M2.5 x ", fc_standoff, " standoff, female-female, nylon"), 4, standoff_g(fc_standoff, 0, NYLON), "Bolt under the frame"],
    [str("M2.5 x ", len_fc, " socket head screw, steel"), 8, screw_g(2.5, len_fc, 4.5, 2.5, STEEL), "Bolt standoffs, 4 from the frame, 4 from the Bolt"],
    ["Pin header 2.54 mm, per pin", esc_pins_in * 4 + esc_pins_out * 4,
        (0.64 * 0.64 * (header_h + esc_board_t + pcb_t + 4.5) * BRASS + pitch * pitch * header_h * 1.3e-3), "ESCs"],
    each [for (c = connectors) [str(c[0], ": JST ", c[2], " ", c[3], "-pin header (", c[6], ")"), 1, header_g(c),
                                c[1] == "top" ? "frame top" : "frame underside"]],
    each [for (c = connectors) [str(c[0], " lead, ", cable_len, " mm, ", c[3], " x ", c[2] == "PH" ? "26" : "28", " AWG"), 1,
                                c[2] == "PH" ? cable_g(c[3], 0.128, 0.9, cable_len, 0.08) : cable_g(c[3], 0.081, 0.7, cable_len, 0.04),
                                c[0][1] == "1" || c[0][1] == "2" ? "to the Pi's GPIO" : "to the Bolt"]]
];

module screw(d, l, dk, k, c = "DimGray") color(c) {             // head on z = 0, shank down -z
    cylinder(d = dk, h = k, $fn = 20);
    translate([0, 0, -l]) cylinder(d = d, h = l, $fn = 12);
}
module standoff(l, male) color("WhiteSmoke") {                  // hex body from z = 0 up, male stud down
    difference() { cylinder(d = 5 / cos(30), h = l, $fn = 6); if (male == 0) translate([0, 0, -1]) cylinder(d = 2.5, h = l + 2, $fn = 12); }
    if (male > 0) translate([0, 0, -male]) cylinder(d = 2.5, h = male, $fn = 12);
}
module insert(ins) color("Goldenrod") translate([0, 0, -ins[1]]) difference() {
    cylinder(d = ins[0], h = ins[1], $fn = 20);
    translate([0, 0, -1]) cylinder(d = ins[0] - 1.2, h = ins[1] + 2, $fn = 16);
}

module hardware() {
    for (i = [-1, 1], j = [-1, 1]) {
        translate([i * crad_hole[0], j * crad_hole[1], 0]) {
            translate([0, 0, cover_head]) screw(2, len_cover, 3.8, 2);
            insert(ins_m2);
        }
        translate([i * pi_hole_x / 2, j * post_y, 0]) {
            translate([0, 0, z_pi_top]) screw(2.5, len_pi, 4.5, 2.5);
            translate([0, 0, post_top]) insert(ins_m25);
        }
        translate([i * fc_holes / 2, j * fc_holes / 2, 0]) {
            translate([0, 0, pcb_t]) screw(2.5, len_fc, 4.5, 2.5);
            translate([0, 0, -fc_standoff]) standoff(fc_standoff, 0);
            translate([0, 0, z_fc]) rotate([180, 0, 0]) screw(2.5, len_fc, 4.5, 2.5);
        }
    }
    for (j = [-1, 1]) translate([0, j * post_y, boss_z]) {
        translate([rail_end + block_t, 0, 0]) rotate([0, 90, 0]) screw(2, len_cam, 3.8, 2);   // shank along -x
        translate([rail_end, 0, 0]) rotate([0, 90, 0]) insert(ins_m2);
    }
    for (m = motors, a = [0:90:270]) let(r = a + atan2(m[1], m[0]) + 45)
        translate([m[0] + cos(r) * motor_hole_pcd / 2, m[1] + sin(r) * motor_hole_pcd / 2, 0])
            translate([0, 0, prop_guard ? -guard_t : 0]) rotate([180, 0, 0]) screw(2, len_motor_used, 3.8, 1.5);
}

// --------------------------------------------------------------------------------------------
// Print layout: harness on its rails, cam mount on its block, gear upside down on its frame

module print_layout(which = "all") {
    if (which == "all" || which == "cradle") translate([0, 0, -pcb_t]) cradle();
    if (which == "all" || which == "cam_mount") translate([0, 50, -rail_end]) rotate([0, -90, 0]) cam_mount();
    if (which == "all" || which == "gear") translate([0, -75, 0]) rotate([180, 0, 0]) gear();
}

// --------------------------------------------------------------------------------------------
// Summary

prop_pi  = min([for (i = [-1, 1], j = [-1, 1]) prop_clear([i * pi_l / 2, j * pi_w / 2])]);
prop_cam = min([for (d = [-1, 1], j = [-1, 1]) prop_clear([cam_c[0] + d * (cam_head_l / 2 + 1) * sin(cam_tilt), j * (post_y + 3)])]);
echo(str("1S Pi Zero: wheelbase ", wheelbase, " mm, motors at +-", round(L * 10) / 10,
         ", prop gap to neighbour ", round((wheelbase / sqrt(2) - prop_d) * 10) / 10,
         " mm; in plan the prop tips clear the Pi by ", round(prop_pi * 10) / 10,
         " mm and the camera harness by ", round(prop_cam * 10) / 10, " mm"));
echo(str("  cell axis z ", z_bc, " (on the PCB), Pi board ", round(z_pi_bot * 10) / 10, "..", round(z_pi_top * 10) / 10,
         ", Bolt ", z_fc, ", Flow deck sensor ", z_sensor, ", feet at z ", round(z_foot * 10) / 10,
         ", overall height ", round((z_pi_top + 3 - z_foot) * 10) / 10, " mm; camera at ", cam_tilt, " deg"));
echo(str("  hardware: M2 x ", len_cover, " cover, M2.5 x ", len_pi, " Pi, M2 x ", len_cam, " camera, M2 x ",
         len_motor, " motors, M2.5 x ", len_fc, " Bolt on ", fc_standoff, " mm standoffs; weights in 1S_PiZero_BOM.md"));
if (echo_bom) for (h = hardware_list) echo(str("BOM|", h[0], "|", h[1], "|", h[2], "|", h[3]));
// With the optional prop guard, the motor screws get longer: listed as the difference.
guard_hw = [[str("M2 x ", len_motor_g, " motor screws instead of M2 x ", len_motor, " (difference)"), 16,
             screw_g(2, len_motor_g, 3.8, 1.5, STEEL) - screw_g(2, len_motor, 3.8, 1.5, STEEL), "through the guard's pads"]];
if (echo_bom) for (h = guard_hw) echo(str("BOMOPT|", h[0], "|", h[1], "|", h[2], "|", h[3]));
esc_seat = pitch / 2 - pin_gap - 0.32;                                   // ESC edge resting on the plastic
esc_gear = (esc_radius - row_off - pitch / 2 - esc_pins_in * pitch / 2) / sqrt(2) - gear_y;  // inner header to gear frame
echo(str("  ESC ", esc_l, " x ", esc_w, " on ", esc_pins_in, "+", esc_pins_out, " pin headers, rows ",
         round(2 * row_off * 100) / 100, " mm apart; each end rests ", round(esc_seat * 100) / 100,
         " mm on the plastic; inner header clears the landing gear by ", round(esc_gear * 10) / 10, " mm"));
assert(boss_z + 3 < post_top - 1, "camera blocks would cover the Pi post inserts: lower boss_z");
assert(esc_seat > 0.3, "ESC barely rests on the header plastic: reduce pin_gap");
assert(esc_gear > 0.5, "inner ESC header hits the landing gear: increase esc_radius");
assert(prop_pi > 0, "props overlap the Pi in plan: increase wheelbase");
assert(prop_cam > 0, "props overlap the camera harness in plan: increase wheelbase or reduce cam_reach");

// --------------------------------------------------------------------------------------------
// Part selector

if (part == "assembly") {
    color("DarkOrange") cradle();
    color("SlateGray") cam_mount();
    color("SlateGray") gear();
    if (prop_guard) color("DimGray") prop_guard_frame();
    pcb();
    if (show_hardware) hardware();
    for (m = motors) motor(m);
    if (show_props) for (m = motors) prop(m);
    if (show_electronics) {
        battery();
        for (m = motors) esc(m);
        flight_controller();
        if (flow_deck) flow_deck_board();
        pi_zero();
        camera();
    }
}
if (part == "pcb")         pcb();
if (part == "pcb_outline") pcb_shape();
if (part == "cradle")      cradle();
if (part == "cam_mount")   cam_mount();
if (part == "gear")        gear();
if (part == "guard")       prop_guard_frame();
// for the verify script: what the guard shares with one other body (must be empty)
if (part == "guard_clash") intersection() {
    prop_guard_frame();
    if (clash == "pcb") pcb();
    if (clash == "cradle") cradle();
    if (clash == "gear") gear();
    if (clash == "cam_mount") union() { cam_mount(); camera(); }
    if (clash == "motors") for (m = motors) motor(m);
    if (clash == "props") for (m = motors) translate(concat(m, prop_z - 0.5)) cylinder(d = prop_d, h = 3.5);
    if (clash == "escs") for (m = motors) esc(m);
    if (clash == "bolt") union() { flight_controller(); flow_deck_board(); }
    if (clash == "pi") pi_zero();
    if (clash == "cam_view") cam_view();
}
if (part == "guard_print") translate([0, 0, -z_gbed]) prop_guard_frame();   // upright, pads on the bed
if (part == "print")       print_layout();
if (part == "cradle_top") projection(cut = true) translate([0, 0, 1 - post_top]) cradle();  // for the verify script
if (part == "cradle_slice") projection(cut = true) translate([0, 0, -slice_z]) cradle();
if (echo_dims) for (d = [["pi_l", pi_l], ["pi_w", pi_w], ["pi_hole_x", pi_hole_x], ["pi_hole_y", pi_hole_y],
                         ["fc_l", fc_size[0]], ["fc_w", fc_size[1]], ["fc_deck_rows", fc_deck_rows],
                         ["motor_bell_d", motor_bell_d], ["motor_h", motor_h], ["motor_base_t", motor_base_t],
                         ["motor_shaft", motor_shaft], ["esc_l", esc_l], ["esc_w", esc_w], ["esc_t", esc_t],
                         ["bat_d", bat_d], ["bat_len", bat_len], ["cam_w", cam_w]])
    echo(str("DIM ", d[0], " ", d[1]));
if (part == "cradle_print")    print_layout("cradle");
if (part == "cam_mount_print") print_layout("cam_mount");
if (part == "gear_print")      print_layout("gear");
