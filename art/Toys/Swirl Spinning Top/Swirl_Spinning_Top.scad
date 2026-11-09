// Swirl Spinning Top - a small spinning top whose body is two spiral ribbons.
//
// Two upright ribbons start at the hub and wind out, getting squarer as they go, until each one
// runs into half of a rounded-square frame. That makes a two-armed swirl, balanced for spinning.
// The ribbons' lower edges follow a cone down to the point, so from the side the body is a funnel
// of ribbons. A slender stem rises from the hub to be twirled between finger and thumb.
//
// Printing: the body's top is one flat plane (frame, ribbon tops and hub). So the body prints upside
// down on that plane with no supports at all: every ribbon is a vertical wall growing up from the bed,
// and the cone of lower edges becomes their free top. The stem prints standing on its flared base.
// A short pin joins them through holes in the hub and in the stem base (press fit, or a drop of glue).
//
// Axes: +z is up as the top spins, the point is at z = 0, the body's flat top is at z = body_h.

/* [Output] */
// assembly: the top as it spins. plate: the three parts as they print. body/stem/pin: one part, laid out for printing
part = "assembly"; // [assembly, plate, body, stem, pin, none]

/* [Size] */
total_h = 50;       // mm, point to stem tip
frame_w = 42;       // mm, outer width of the rounded-square frame
body_h = 23;        // mm, point to the body's flat top

/* [Swirl] */
arms = 2;           // number of spiral ribbons (2 is balanced and reads best)
turns = 1.25;       // how far each ribbon winds from the hub to the frame
handed = 1;         // [1:anticlockwise out, -1:clockwise out]
squareness = 4;     // superellipse exponent of the frame (2 = circle)
wind_bias = 1.5;    // >1 packs the inner turns tighter and makes each ribbon meet the frame in a wedge
ribbon_t = 2.4;     // mm, ribbon wall thickness (six 0.4 mm lines)
frame_t = 2.6;      // mm, frame wall thickness
frame_h = 4.5;      // mm, frame band height
hub_r = 5.5;        // mm, hub radius at the top
tip_r = 1.4;        // mm, radius of the rounded point

/* [Stem] */
stem_base_r = 6.5;  // mm, flare where the stem meets the body
stem_r = 2.6;       // mm, shaft radius just above the flare
stem_top_r = 2.0;   // mm, shaft radius at the rounded tip
flare = 4;          // mm, how quickly the flare narrows into the shaft

/* [Joint] */
pin_d = 4;          // mm
pin_depth = 6;      // mm, how far the pin goes into the body and into the stem
fit = 0.12;         // mm, radial clearance of the holes (0.1 press fit, 0.2 for glue)

/* [Hidden] */
N = 150;                            // stations per ribbon
R = frame_w / 2 - frame_t / 2;      // frame centreline half-width
stem_h = total_h - body_h;
r_start = 2.2;                      // ribbon starts inside the hub
z_tip = tip_r;
frame_bot = body_h - frame_h;
cone_k = (frame_bot - z_tip) / R;   // rise of the ribbons' lower edges per mm outwards
eps = 0.01;

function lerp(a, b, t) = a + (b - a) * t;
function sq_r(n, a) = 1 / pow(pow(abs(cos(a)), n) + pow(abs(sin(a)), n), 1 / n);
function unit(v) = v / norm(v);

// Ribbon centreline: radius grows from the hub to the frame while the shape morphs
// from a circle (inner turns) to the frame's superellipse (where it joins the frame).
function arm_pt(k, s) =
    let(a = handed * 360 * turns * s + 360 * k / arms + 45,
        n = lerp(2, squareness, s * s),
        r = lerp(r_start, R * sq_r(n, a), pow(s, wind_bias)))
    [r * cos(a), r * sin(a)];
function frame_pt(a) = R * sq_r(squareness, a) * [cos(a), sin(a)];

// Section of a wall: flat top (the print bed), rounded lower edge.
function section(t, zb, zt) =
    let(h = t / 2)
    concat([[-h, zt], [h, zt]],
           [for (a = [0 : -30 : -180]) [h * cos(a), zb + h + h * sin(a)]]);

// Loft a wall section along a 2D path; zb_of(r) gives the lower edge at radius r.
module wall(pts, t, zb_list, zt, closed = false) {
    n = len(pts);
    M = len(section(t, 0, 10));
    verts = [for (i = [0 : n - 1])
        let(p = pts[i],
            d = closed ? pts[(i + 1) % n] - pts[(i - 1 + n) % n]
                       : pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)],
            nn = unit([-d[1], d[0]]),
            sec = section(t, zb_list[i], zt))
        for (q = sec) [p[0] + q[0] * nn[0], p[1] + q[0] * nn[1], q[1]]];
    segs = closed ? n : n - 1;
    sides = [for (i = [0 : segs - 1]) for (j = [0 : M - 1])
        [i * M + j, ((i + 1) % n) * M + j, ((i + 1) % n) * M + (j + 1) % M, i * M + (j + 1) % M]];
    caps = closed ? [] : [[for (j = [0 : M - 1]) j],
                          [for (j = [M - 1 : -1 : 0]) (n - 1) * M + j]];
    polyhedron(verts, concat(sides, caps), convexity = 6);
}

module arm(k) {
    pts = [for (i = [0 : N]) arm_pt(k, i / N)];
    zb = [for (p = pts) min(z_tip + cone_k * norm(p), body_h - ribbon_t - 0.6)];
    wall(pts, ribbon_t, zb, body_h);
}

module frame() {
    pts = [for (i = [0 : 239]) frame_pt(i * 360 / 240)];
    wall(pts, frame_t, [for (p = pts) frame_bot], body_h, closed = true);
}

// Hub: a cone to the rounded point, with the same slope as the ribbons' lower edges.
module hub() {
    hull() {
        translate([0, 0, z_tip]) sphere(r = tip_r, $fn = 32);
        translate([0, 0, z_tip + cone_k * hub_r]) cylinder(r = hub_r, h = body_h - z_tip - cone_k * hub_r, $fn = 48);
    }
}

module pin_hole() { translate([0, 0, -eps]) cylinder(r = pin_d / 2 + fit, h = pin_depth + 0.4 + eps, $fn = 32); }

// Body in spinning orientation (flat top at z = body_h).
module body() {
    difference() {
        union() { hub(); frame(); for (k = [0 : arms - 1]) arm(k); }
        translate([0, 0, body_h]) mirror([0, 0, 1]) pin_hole();
    }
}

// Stem standing on its base (z = 0), rising stem_h.
function stem_r_at(h) = lerp(stem_r, stem_top_r, h / stem_h) + (stem_base_r - stem_r) * exp(-h / flare);
module stem() {
    top = stem_h - stem_top_r;
    prof = concat([[0, 0]],
                  [for (h = [0 : 0.5 : top]) [stem_r_at(h), h]],
                  [for (a = [0 : 10 : 90]) [stem_top_r * cos(a), top + stem_top_r * sin(a)]]);
    difference() {
        rotate_extrude($fn = 64) polygon(prof);
        pin_hole();
    }
}

module pin() {
    c = 0.5;
    L = 2 * pin_depth;
    rotate_extrude($fn = 32) polygon([[0, 0], [pin_d / 2 - c, 0], [pin_d / 2, c], [pin_d / 2, L - c], [pin_d / 2 - c, L], [0, L]]);
}

module body_print() { translate([0, 0, body_h]) mirror([0, 0, 1]) body(); }
module stem_print() { translate([frame_w / 2 + stem_base_r + 6, 4, 0]) stem(); }
module pin_print() { translate([frame_w / 2 + stem_base_r + 6, -stem_base_r - 6, 0]) pin(); }

echo(str("Swirl Spinning Top: ", total_h, " mm tall, frame ", frame_w, " mm, body ", body_h,
         " mm, ", arms, " ribbons x ", turns, " turns, ribbon lower edges rise ",
         round(atan(cone_k)), " deg, stem ", stem_h, " mm, pin d ", pin_d, " x ", 2 * pin_depth, " mm"));

color("#FF9016") {
    if (part == "assembly") { body(); translate([0, 0, body_h]) stem(); }
    if (part == "plate") { body_print(); stem_print(); pin_print(); }
    if (part == "body") body_print();
    if (part == "stem") stem_print();
    if (part == "pin") pin_print();
}
