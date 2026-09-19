// Tree Vase Holder
// A braided tree built around a real glass vase: roots on the bed, a
// growth-ring stump under the glass, braided stems woven over/under around
// it, and a crown of branches and leaves above the rim.
// Step 1 is the glass; everything after it is sized from the glass.
// All dimensions in mm.

/* [Glass vase] */
glass_d       = 80;     // outer diameter of the glass
glass_h       = 130;    // height of the glass
glass_wall    = 2.5;    // preview only
glass_floor   = 6;      // preview only
glass_edge_r  = 4;      // preview only: rounding of the glass bottom edge

/* [Fit] */
clearance     = 1;      // printed gap around the glass (insertOffsetMm)
floor_h       = 9;      // glass floor height above the build plate (>= 7.5)

/* [Braided trunk] */
strands       = 5;      // stems per spiral direction (twice this in total)
weave_rows    = 3;      // crossing intervals between the root row and the crown row
stem_r0       = 7;      // stem radius at the roots
stem_r1       = 5;      // stem radius at the crown
weave_depth   = 3;      // over/under offset at crossings (< stem radius, so crossings fuse)
stem_gap      = 1;      // gap between the bore and the innermost stem surface
crown_drop    = 25;     // crown row (upper fork points) this far below the glass rim

/* [Roots] */
root_len      = 26;     // how far the roots reach out on the bed
root_spread   = 24;     // side-root angle (deg)
root_r0       = 6;
root_r1       = 2.5;
root_bend     = 10;     // max sideways bend of a root (deg)

/* [Branches and leaves] */
branch_rise   = 16;     // centre branch tip height above the glass rim
branch_out    = 14;     // outward lean of the branch tips
branch_spread = 22;     // side-branch angle (deg)
branch_r0     = 4.5;
branch_r1     = 2.2;
leaf_len      = 24;
leaf_w        = 8;
leaf_t        = 2.4;
leaf_tilt     = 24;     // side leaves of a cluster, degrees from vertical
leaf_fold     = 25;     // fold along the midrib (deg per half)
mid_leaf_at   = 0.55;   // position of the leaf pair along each branch (0..1)
leaf_jitter   = 8;      // random variation of leaf tilt and facing (deg, > 0)

/* [Stump] */
ring_count    = 6;      // growth rings on the floor, seen through the glass bottom
ring_groove   = 0.8;    // groove depth

/* [Bark] */
tube_sides    = 18;
bark_ridges   = 6;
bark_depth    = 0.10;   // ridge height as a fraction of the tube radius

/* [Output] */
part          = "assembly";   // [assembly, holder, bark, leaves]
show_glass    = true;
bark_color    = "#6F5034";    // Bambu PLA Basic Cocoa Brown
leaf_color    = "#3F8E43";    // Bambu PLA Basic Mistletoe Green
$fn           = 96;

// ---------------------------------------------------------------
// Derived
glass_r   = glass_d / 2;
bore_r    = glass_r + clearance;
glass_z0  = floor_h;
glass_top = glass_z0 + glass_h;

trunk_z0  = floor_h + 4;              // root row: lower fork points
trunk_z1  = glass_top - crown_drop;   // crown row: upper fork points
trunk_h   = trunk_z1 - trunk_z0;
twist     = weave_rows * 180 / strands;   // total twist of one stem (deg)

function lerp(a, b, t) = a + (b - a) * t;
function stem_r(t)   = lerp(stem_r0, stem_r1, t);
function weave_b(t)  = weave_depth * sin(180 * t);   // 0 at both fork rows

// stem centreline radius: innermost stem surface stays stem_gap outside the bore
stem_rs = bore_r + stem_gap
        + max([for (i = [0:200]) let(t = i / 200)
               stem_r(t) + weave_b(t) * abs(cos(weave_rows * 180 * t))]);

// ---------------------------------------------------------------
// Tube sweep: circle (with bark ridges) swept along a path,
// parallel-transport frames, capped ends.
function unit(v) = v / norm(v);
function tangents(P) = [for (i = [0:len(P) - 1])
    unit(i == 0 ? P[1] - P[0] : i == len(P) - 1 ? P[i] - P[i - 1] : P[i + 1] - P[i - 1])];
function first_normal(t) = unit(cross(t, abs(t[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0]));
function transport(T, i, prev) = i >= len(T) ? [] :
    let(n = unit(prev - (prev * T[i]) * T[i])) concat([n], transport(T, i + 1, n));

// phase: rotates the ring samples. Mirror-image tubes (the two stem families,
// the left/right branches) need phases that differ by half a step, or their
// vertices coincide where they meet and CGAL leaves non-manifold edges.
module sweep(P, R, sides = tube_sides, ridges = bark_ridges, depth = bark_depth, phase = 0) {
    T = tangents(P);
    N = transport(T, 0, first_normal(T[0]));
    loft([for (i = [0:len(P) - 1]) let(B = cross(T[i], N[i]))
          [for (j = [0:sides - 1]) let(a = 360 * j / sides + phase, r = R[i] * (1 + depth * cos(ridges * a)))
               P[i] + r * (cos(a) * N[i] + sin(a) * B)]]);
}

// Closed solid through a list of rings (each ring counter-clockwise seen
// from the direction of travel), capped at both ends.
module loft(rings) {
    n = len(rings);
    S = len(rings[0]);
    pts = [for (ring = rings) each ring];
    side = [for (i = [0:n - 2]) for (j = [0:S - 1])
            let(j2 = (j + 1) % S, a = i * S + j, b = (i + 1) * S + j,
                c = (i + 1) * S + j2, d = i * S + j2)
            each [[a, b, c], [a, c, d]]];
    caps = [[for (j = [0:S - 1]) j],
            [for (j = [S - 1:-1:0]) (n - 1) * S + j]];
    polyhedron(points = pts, faces = concat(side, caps), convexity = 10);
}

function cyl(rho, phi, z) = [rho * cos(phi), rho * sin(phi), z];

// ---------------------------------------------------------------
// Step 1: the glass
module glass_solid(r, h, er) {
    hull() {
        translate([0, 0, er]) rotate_extrude() translate([r - er, 0]) circle(er);
        translate([0, 0, er]) cylinder(r = r, h = h - er);
    }
}

module glass() {
    difference() {
        glass_solid(glass_r, glass_h, glass_edge_r);
        translate([0, 0, glass_floor])
            glass_solid(glass_r - glass_wall, glass_h, max(0.5, glass_edge_r - glass_wall));
    }
}

// ---------------------------------------------------------------
// Step 2: the tree

// Braided stems. dir = +1 / -1 spiral direction. The over/under offset
// flips sign between the two families, so every crossing alternates.
stem_n = 48;
function stem_path(dir, i) = [for (s = [0:stem_n]) let(t = s / stem_n)
    cyl(stem_rs + dir * weave_b(t) * cos(weave_rows * 180 * t),
        360 * i / strands + dir * twist * t,
        trunk_z0 + trunk_h * t)];
stem_radii = [for (s = [0:stem_n]) stem_r(s / stem_n)];

function root_angle(i)  = 360 * i / strands;               // lower fork points
function crown_angle(i) = 360 * i / strands + twist;       // upper fork points

// Roots: drop from the lower fork and run out along the bed. On the bed the
// centreline sits 0.3 r up, so the bed cut takes 35% of the root's height.
// Bends stay gentle: a bend tighter than the root radius folds the tube
// through itself and breaks the CGAL union.
root_n = 24;
function root_r(t) = root_r1 + (root_r0 - root_r1) * pow(1 - t, 1.6);   // flared base
function root_path(phi0, s, bend) = let(L = root_len * (s == 0 ? 1 : 0.85))
    [for (k = [0:root_n]) let(t = k / root_n)
     cyl(stem_rs + L * t,
         phi0 + s * root_spread * t + bend * t * t,
         0.3 * root_r(t) + (trunk_z0 - 0.3 * root_r0) * pow(1 - t, 2.5))];
root_radii = [for (k = [0:root_n]) root_r(k / root_n)];

// deterministic pseudo-random in [0, 1), and a +-leaf_jitter/2 degree offset
function rnd(a, b = 0, c = 0) = let(x = sin(a * 127.1 + b * 311.7 + c * 74.7) * 43758.5453) x - floor(x);
function jit(a, b, c) = (rnd(a, b, c) - 0.5) * leaf_jitter;

// Branches: rise from the upper fork, fan sideways and lean out over the rim.
branch_n = 24;
function branch_tip_z(s) = glass_top + branch_rise - (s == 0 ? 0 : 7);
function branch_path(phi1, s) = let(zt = branch_tip_z(s), out = branch_out * (s == 0 ? 0.7 : 1))
    [for (k = [0:branch_n]) let(t = k / branch_n)
     cyl(stem_rs + out * pow(t, 1.3), phi1 + s * branch_spread * t, lerp(trunk_z1, zt, t))];
branch_radii = [for (k = [0:branch_n]) lerp(branch_r0, branch_r1, k / branch_n)];

// Leaf: pointed lens, blade standing upright and facing outward.
// Leaf: pointed lens along +y, folded along the midrib into a shallow V (so it
// reads as a leaf from above too), lofted as one solid. The blade contains the
// near-vertical leaf axis, so it stands upright and prints without supports.
leaf_n = 16;
function lens_w(y, L, W) = let(Rv = (L * L / 4 + W * W / 4) / W)
    max(0.3, sqrt(max(0, Rv * Rv - pow(y - L / 2, 2))) - (Rv - W / 2));

module leaf3d(L, W) {
    h = leaf_t / (2 * cos(leaf_fold));   // keeps the true blade thickness at leaf_t
    k = tan(leaf_fold);
    loft([for (i = [0:leaf_n]) let(y = L * (1 - cos(180 * i / leaf_n)) / 2, w = lens_w(y, L, W))
          [[-w, y, w * k + h], [0, y, h], [w, y, w * k + h],
           [ w, y, w * k - h], [0, y, -h], [-w, y, w * k - h]]]);
}

// base: a point on the branch centreline, along: the branch direction there.
// The leaf starts inside the branch, sink mm back along the branch and 0.6 mm
// down its own axis. So its lowest corner is embedded in wood (a corner below
// the branch would start in mid-air: Bambu Studio's "floating regions"), and
// leaves sharing a base never share a vertex.
module leaf_at(base, along, phi, tilt, size = 1, sink = 3) {
    u = [cos(phi), sin(phi), 0];                                // blade normal (outward)
    a = cos(tilt) * [0, 0, 1] + sin(tilt) * [-sin(phi), cos(phi), 0];   // leaf axis
    x = cross(a, u);
    p = base - sink * along - 0.6 * a;
    multmatrix([[x[0], a[0], u[0], p[0]],
                [x[1], a[1], u[1], p[1]],
                [x[2], a[2], u[2], p[2]],
                [0, 0, 0, 1]])
        leaf3d(leaf_len * size, leaf_w * size);
}

module stump() {
    difference() {
        cylinder(r = stem_rs - 2, h = floor_h, $fn = 120);
        // off-centre growth rings, like a real cross-section
        for (k = [1:ring_count]) let(f = k / ring_count, rr = (bore_r - 3) * pow(f, 0.85))
            translate([1.5 * f, 0.8 * f, floor_h - ring_groove])
                difference() {
                    cylinder(r = rr + 0.5, h = ring_groove + 1);
                    translate([0, 0, -1]) cylinder(r = rr - 0.5, h = ring_groove + 3);
                }
    }
}

module bark() {
    stump();
    for (i = [0:strands - 1]) {
        sweep(stem_path(+1, i), stem_radii);
        sweep(stem_path(-1, i), stem_radii, phase = 180 / tube_sides);
        // lower fork: knob plus three roots
        translate(cyl(stem_rs, root_angle(i), trunk_z0)) sphere(r = stem_r0 * 1.15, $fn = 24);
        for (s = [-1, 0, 1]) {
            P = root_path(root_angle(i), s, (rnd(i, s) - 0.5) * 2 * root_bend);
            sweep(P, root_radii);
            translate(P[root_n]) sphere(r = root_r1, $fn = 12);
        }
    }
    branches();
}

// upper forks: knob plus three branches each
module branches() {
    for (i = [0:strands - 1]) {
        translate(cyl(stem_rs, crown_angle(i), trunk_z1)) sphere(r = stem_r1 * 1.05, $fn = 24);
        for (s = [-1, 0, 1]) {
            P = branch_path(crown_angle(i), s);
            sweep(P, branch_radii, phase = s < 0 ? 180 / tube_sides : 0);
            translate(P[branch_n]) sphere(r = branch_r1, $fn = 12);
        }
    }
}

module leaves() {
    for (i = [0:strands - 1]) for (s = [-1, 0, 1]) {
        P   = branch_path(crown_angle(i), s);
        phi = crown_angle(i) + s * branch_spread;
        // cluster at the tip
        // jitter also keeps leaves off exact angles (a leaf at exactly 180 deg
        // lines up with the branch-tip sphere and CGAL leaves non-manifold edges)
        for (l = [-1, 0, 1])
            leaf_at(P[branch_n], unit(P[branch_n] - P[branch_n - 1]), phi + jit(i, s, l + 10),
                    l * leaf_tilt + s * 8 + jit(i, s, l + 20),
                    (l == 0 ? 1.05 : 0.85) * (0.9 + 0.2 * rnd(i, s, l)), sink = 4);
        // a pair part-way along the branch
        m = round(branch_n * mid_leaf_at);
        phi_m = crown_angle(i) + s * branch_spread * mid_leaf_at;
        for (l = [-1, 1])
            leaf_at(P[m], unit(P[m + 1] - P[m - 1]), phi_m + jit(i, s, l + 30), l * leaf_tilt * 1.2 + jit(i, s, l + 40),
                    0.7 * (0.9 + 0.2 * rnd(i, s, l + 5)));
    }
}

// Straight bore for the glass, and a flat cut at the build plate.
module trim() {
    difference() {
        children();
        translate([0, 0, floor_h]) cylinder(r = bore_r, h = 400, $fn = 180);
        translate([-500, -500, -100]) cube([1000, 1000, 100]);
    }
}

// ---------------------------------------------------------------
stem_rise = atan(trunk_h / (stem_rs * twist * PI / 180));
echo(str("Tree vase holder: glass ", glass_d, " x ", glass_h, " mm, bore d ", 2 * bore_r,
         " mm, glass floor ", floor_h, " mm, stems at r ", round(stem_rs * 10) / 10,
         " mm rising ", round(stem_rise), " deg, forks at z ", trunk_z0, " / ", trunk_z1,
         ", crown top ~", round(glass_top + branch_rise + leaf_len * 1.05 - 4), " mm"));

// Two-colour print: export "bark" and "leaves" separately and load them into
// the slicer as one object with two parts. They share one coordinate frame and
// do not overlap (leaves only touch the branches, which are cut out of them).
if (part == "assembly") {
    if (show_glass) color([0.75, 0.9, 1.0, 0.35]) translate([0, 0, glass_z0]) glass();
    color(bark_color) trim() bark();
    color(leaf_color) leaves();   // leaves never reach the bore or the bed
}
if (part == "holder") trim() { bark(); leaves(); }
if (part == "bark")   trim() bark();
if (part == "leaves") trim() difference() { leaves(); branches(); }
