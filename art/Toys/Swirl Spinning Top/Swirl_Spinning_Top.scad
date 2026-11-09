// Swirl Spinning Top - a small spinning top whose body is four spiral ribbons.
//
// Four ribbons start at the corners of a rounded-square frame and wind in towards the axis, rounder
// as they go. They alternate: two climb as they wind in and become fins running up the stem, and two
// drop and become fins running down the spike to the point. Seen from the side each ribbon is a
// smooth spline: it leaves the frame level and bends steadily into its fin. The frame is a thin flat
// ring a third of the way up. Near the axis each ribbon grows taller, into a fin on the core.
//
// Printing: one piece, standing on its point, with supports (tree supports, plus a brim for the
// point). The frame and the undersides of the ribbons hang over the bed and need them.
//
// Axes: +z is up as the top spins, the point is at z = 0.

/* [Output] */
// top: the whole top, one piece, standing on its point as it prints
part = "top"; // [top, none]

/* [Size] */
total_h = 50;       // mm, point to stem tip
frame_w = 36;       // mm, outer width of the rounded-square frame
frame_z = 17;       // mm, height of the frame's middle above the point (about a third of total_h)

/* [Swirl] */
arms = 4;           // [2:2:8] ribbons, alternately climbing to the stem and dropping to the point
turns = 0.8;        // how far each ribbon winds from the frame to the axis
handed = 1;         // [1:anticlockwise out, -1:clockwise out]
squareness = 4;     // superellipse exponent of the frame (2 = circle)
wind_bias = 1.0;    // >1 keeps the ribbons near the frame longer and packs the inner turns tighter
straighten = 2;      // >1 stops the winding near the axis, so the fins run straight along the core
ribbon_t = 2.4;     // mm, ribbon wall thickness (six 0.4 mm lines)
band_h = 3.2;       // mm, ribbon height where it leaves the frame
fin_h = 6;          // mm, extra ribbon height where it becomes a fin on the core
fin_top = 46;       // mm, where the climbing fins end on the stem
fin_bot = 4;        // mm, where the dropping fins end on the spike
curve = 0.25;       // [0:0.05:1] spline shape: small = level near the frame then a sharp bend into the fin, 1 = an even slope

/* [Frame] */
frame_t = 2.6;      // mm, frame wall thickness
frame_h = 3.5;      // mm, frame band height

/* [Core] */
core_r = 2.3;       // mm, radius of the stem and spike away from the waist
core_cap = 8;       // mm, the core follows the ribbons in towards the axis, but never wider than this
stem_top_r = 1.8;   // mm, radius of the rounded stem tip
tip_r = 1.4;        // mm, radius of the rounded point
tip_flat = 0.4;     // mm trimmed off the point: a small flat to stand on the bed while printing

/* [Hidden] */
N = 160;                            // stations per ribbon
R = frame_w / 2 - frame_t / 2;      // frame centreline half-width
r_end = 2.0;                        // ribbons end inside the core
frame_top = frame_z + frame_h / 2;
frame_bot = frame_z - frame_h / 2;

function lerp(a, b, t) = a + (b - a) * t;
function sq_r(n, a) = 1 / pow(pow(abs(cos(a)), n) + pow(abs(sin(a)), n), 1 / n);
function unit(v) = v / norm(v);

// Ribbon centreline in plan: from the frame (s = 1, at a corner) in to the axis (s = 0), the shape
// morphing from the frame's superellipse to a circle.
function arm_pt(k, s) =
    let(a = handed * 360 * turns * (pow(s, straighten) - 1) + 360 * k / arms + 45,
        n = lerp(2, squareness, s * s),
        r = lerp(r_end, R * sq_r(n, a), pow(s, wind_bias)))
    [r * cos(a), r * sin(a)];
function frame_pt(a) = R * sq_r(squareness, a) * [cos(a), sin(a)];

// Side profile of a ribbon: a cubic Bezier spline along the ribbon, 0 at the frame and 1 at the end
// of the fin. It leaves the frame level (control points 0, 0) and bends smoothly into the fin.
function spline(u) = let(c = curve) 3 * u * u * (1 - u) * c + u * u * u + 3 * u * (1 - u) * (1 - u) * 0;

// Section of a wall, rounded top and bottom edges.
function section(t, zb, zt) =
    let(h = t / 2)
    concat([for (a = [180 : -30 : 0]) [h * cos(a), zt - h + h * sin(a)]],
           [for (a = [0 : -30 : -180]) [h * cos(a), zb + h + h * sin(a)]]);

// Loft a wall section along a 2D path, with lower and upper edge heights per point.
module wall(pts, t, zb_list, zt_list, closed = false) {
    n = len(pts);
    M = len(section(t, 0, 10));
    verts = [for (i = [0 : n - 1])
        let(p = pts[i],
            d = closed ? pts[(i + 1) % n] - pts[(i - 1 + n) % n]
                       : pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)],
            nn = unit([-d[1], d[0]]),
            sec = section(t, zb_list[i], zt_list[i]))
        for (q = sec) [p[0] + q[0] * nn[0], p[1] + q[0] * nn[1], q[1]]];
    segs = closed ? n : n - 1;
    sides = [for (i = [0 : segs - 1]) for (j = [0 : M - 1])
        [i * M + j, ((i + 1) % n) * M + j, ((i + 1) % n) * M + (j + 1) % M, i * M + (j + 1) % M]];
    caps = closed ? [] : [[for (j = [0 : M - 1]) j],
                          [for (j = [M - 1 : -1 : 0]) (n - 1) * M + j]];
    polyhedron(verts, concat(sides, caps), convexity = 6);
}

// Even k climbs to the stem, odd k drops to the point. Each leaves the frame from its top or bottom
// edge, so where the two kinds lie side by side near the frame they are at different heights.
function rib_h(s) = band_h + fin_h * spline(1 - s);
function rib_z(up, s) = let(g = spline(1 - s), h = rib_h(s))
    up ? lerp(frame_top, fin_top - h / 2, g) : lerp(frame_bot, fin_bot + h / 2, g);
function rib_r(s) = lerp(r_end, R, pow(s, wind_bias));   // roughly; the plan shape is ignored

module arm(k) {
    up = k % 2 == 0;
    pts = [for (i = [0 : N]) arm_pt(k, i / N)];
    h = [for (i = [0 : N]) rib_h(i / N)];
    zc = [for (i = [0 : N]) rib_z(up, i / N)];
    wall(pts, ribbon_t, [for (i = [0 : N]) zc[i] - h[i] / 2], [for (i = [0 : N]) zc[i] + h[i] / 2]);
}

module frame() {
    pts = [for (i = [0 : 239]) frame_pt(i * 360 / 240)];
    wall(pts, frame_t, [for (p = pts) frame_bot], [for (p = pts) frame_top], closed = true);
}

// Core: stem above the waist, spike below, rounded at both ends. Each flares to follow its ribbons:
// at height z it reaches out to the ribbons whose inner edge (lower for climbing ones, upper for
// dropping ones) is at that height, so they sit on it as fins; eased off to at most core_cap.
function env_r(z) = let(up = z > frame_z,
    ss = [for (i = [0 : 200]) let(s = i / 200) if (up ? rib_z(true, s) - rib_h(s) / 2 >= z : rib_z(false, s) + rib_h(s) / 2 <= z) s])
    len(ss) == 0 ? 0 : rib_r(max(ss));
function ease(x, c) = x / pow(1 + pow(x / c, 4), 1 / 4);   // ~x when small, never above c
function core_r_at(z) = max(
    z < frame_z ? lerp(tip_r, core_r, (z - tip_r) / (frame_z - tip_r))
                : lerp(core_r, stem_top_r, (z - frame_z) / (total_h - stem_top_r - frame_z)),
    ease(env_r(z), core_cap));
module core() {
    top = total_h - stem_top_r;
    prof = concat([[0, tip_r]], [for (z = [tip_r : 0.5 : top]) [core_r_at(z), z]], [[core_r_at(top), top], [0, top]]);
    rotate_extrude($fn = 48) polygon(prof);
    translate([0, 0, tip_r]) sphere(r = tip_r, $fn = 32);
    translate([0, 0, top]) sphere(r = stem_top_r, $fn = 32);
}

module body() { core(); frame(); for (k = [0 : arms - 1]) arm(k); }

echo(str("Swirl Spinning Top: ", total_h, " mm tall, frame ", frame_w, " mm at z ", frame_z, " mm, ",
         arms, " ribbons x ", turns, " turns, fins up to z ", fin_top, " and down to z ", fin_bot, " mm"));

color("#FF9016") if (part == "top")
    translate([0, 0, -tip_flat]) difference() {
        body();
        translate([0, 0, tip_flat - 50]) cube(100, center = true);
    }
