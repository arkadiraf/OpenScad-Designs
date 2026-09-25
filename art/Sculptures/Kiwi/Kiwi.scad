// Kiwi - a furry kiwi probing the ground with its beak.
//
// Inspired by Hamid Naderi Yeganeh's kiwi drawn with equations: the body is an equation too.
// Body and head are ellipsoids, each pulled into a cone towards one point (the hull of the
// ellipsoid and that point, in closed form): the belly narrows into the legs and the face
// narrows into the beak. That is what lets it print without supports. Nothing hangs flat:
// every underside slopes down to a leg or to the beak, and the beak tip rests on the base.
// The fur is a displacement of that surface: shingled locks that flow back and down.
//
// Axes: +x is where the kiwi looks, +z is up, the base top is at z = base_h.

/* [Output] */
part = "assembly"; // [assembly, fur, beak, legs, eyes, base, none]
// Untextured and coarse: for finding the shape (fur off, fewer samples)
sketch = false;
// Overall size, % (100 = 140 mm tall)
size_pct = 100; // [40:5:150]

/* [Body] */
body_len = 118;     // mm, tail to chest
body_w = 80;        // mm
body_h = 84;        // mm, the round part only (the belly cone comes on top)
body_z = 108;       // mm, centre height above the bed
body_pitch = 0;     // deg, nose down
leg_x = 2;          // mm, where the legs meet the belly
leg_len = 36;       // mm, base top to the point of the belly cone

/* [Head and beak] */
head_len = 42;      // mm, along the beak axis
head_w = 34;        // mm
head_h = 38;        // mm
head_x = 66;        // mm, centre
head_z = 112;       // mm, centre
beak_angle = 60;    // deg below horizontal
face_taper = 2.1;   // cone point of the face, in head half-lengths from the centre
beak_r0 = 6.5;      // mm, radius at the face
beak_r1 = 1.6;      // mm, radius at the tip
beak_bend = 3.5;      // mm, how far it curves (kiwi beaks bend down a little)
eye_r = 2.8;        // mm

/* [Legs and feet] */
leg_spread = 15;    // mm, ankle from the midline
leg_r1 = 4.2;       // mm, tarsus radius at the ankle
scute_pitch = 2.6;  // mm, scales down the front of the leg
scute_depth = 0.35; // mm
toe_lift = 2.0;     // mm, toe tips rise off the base
claw_len = 7;       // mm

/* [Fur] */
fur_depth = 1.4;    // mm, height of a lock on the body
lock_w = 3.2;       // mm, width of a lock
lock_len = 24;      // mm, length of a lock
flow = 22;          // deg, how far the locks turn down the sides
cone_fur = 0.5;     // fur depth on the belly and face cones, as a share (their undersides must print)

/* [Base] */
base_h = 5;         // mm
base_margin = 16;   // mm, base past the tail and the beak tip
base_w = 104;       // mm

/* [Hidden] */
N_body = sketch ? 90 : 300;     // rings, tail to chest
M_body = sketch ? 96 : 360;     // points per ring
N_head = sketch ? 60 : 160;
M_head = sketch ? 72 : 240;

// ---------------------------------------------------------------- library
function unit(v) = v / norm(v);
function lerp(a, b, t) = a + (b - a) * t;
function frac(x) = x - floor(x);
function clamp01(x) = max(0, min(1, x));
function rnd(a, b = 0, c = 0) = frac(sin(a * 127.1 + b * 311.7 + c * 74.7) * 43758.5453);
function rot_y(v, t) = [v.x * cos(t) + v.z * sin(t), v.y, -v.x * sin(t) + v.z * cos(t)];

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

module sweep(P, R, sides = 24, ridges = 0, depth = 0, phase = 0) {
    T = tangents(P);
    N = transport(T, 0, first_normal(T[0]));
    loft([for (i = [0:len(P) - 1]) let(B = cross(T[i], N[i]))
          [for (j = [0:sides - 1]) let(a = 360 * j / sides + phase,
                                        r = R[i] * (1 + depth * cos(ridges * a)))
               P[i] + r * (cos(a) * N[i] + sin(a) * B)]]);
}

// ---------------------------------------------------------------- the equations
// An ellipsoid pulled into a cone towards one point. E = [centre, semi-axes, pitch, apex in
// unit space, fur scale, fur depth]. In unit space the ellipsoid is the unit sphere, and the hull
// of the sphere and the apex Q is the sphere plus the tangent cone from Q. Along a ray u from the
// centre the surface is at rho = 1, or where the ray leaves that cone.
function cone_rho(u, Q) = let(D = norm(Q), w = -Q / D, A = u * w)
    (-A <= 1 / D) ? 1 :
    let(c2 = 1 - 1 / (D * D), a2 = A * A - c2, b2 = 2 * A / D,
        ts = abs(a2) < 1e-9 ? [-1 / b2] :
             let(s = sqrt(max(0, b2 * b2 - 4 * a2))) [(-b2 - s) / (2 * a2), (-b2 + s) / (2 * a2)],
        ok = [for (t = ts) if (t > 0 && t * A + D >= -1e-6) t])
    max(1, len(ok) ? min(ok) : 1);

// pol: 0 at the back pole, 180 at the front pole (the local +x). a: 0 at +y, 90 on top.
function e_dir(pol, a) = [-cos(pol), sin(pol) * cos(a), sin(pol) * sin(a)];
function e_surf(E, pol, a) = let(u = e_dir(pol, a), r = cone_rho(u, E[3]))
    E[0] + rot_y([u.x * r * E[1].x, u.y * r * E[1].y, u.z * r * E[1].z], E[2]);
function apex_unit(C, S, pitch, P) = let(d = rot_y(P - C, -pitch)) [d.x / S.x, d.y / S.y, d.z / S.z];

// One lock of fur, 0..1. along: arc length from the back pole; arc: arc length down from the
// dorsal line. Locks are shingled: each rises slowly to its tip and drops more steeply behind it,
// the tips pointing downstream (back and down).
function fur01(along, arc, sc, seed) =
    let(l = -along * cos(flow) + arc * sin(flow),
        c0 = along * sin(flow) + arc * cos(flow),
        w = lock_w * sc, L = lock_len * sc,
        c = c0 + 0.35 * w * sin(360 * l / (2.3 * L) + 90 * sin(c0 * 7)),   // locks wave a little
        cc = c / w, ci = floor(cc), fc = cc - ci,
        ll = l / (L * (0.75 + 0.5 * rnd(ci, seed, 3))) + rnd(ci, seed), li = floor(ll), p = ll - li,
        ramp = p < 0.8 ? p / 0.8 : (1 - p) / 0.2,
        across = pow(sin(180 * fc), 0.8),
        amp = 0.45 + 0.55 * rnd(ci, li, seed))
    ramp * across * amp;

function from_top(a) = let(t = (a - 90) - 360 * floor((a - 90 + 180) / 360)) abs(t);

function e_point(E, pol, a, fur, fade) =
    let(p = e_surf(E, pol, a))
    !fur ? p :
    let(along = pol * PI / 180 * E[1].x,
        arc = from_top(a) * PI / 180 * (E[1].y + E[1].z) / 2 * sin(pol),
        on_cone = clamp01((cone_rho(e_dir(pol, a), E[3]) - 1) / 0.05),    // flatter fur on the cone
        h = E[5] * fade * lerp(1, cone_fur, on_cone) * fur01(along, arc, E[4], E[4] * 17))
    p + h * unit(p - E[0]);

function e_rings(E, N, M, fur, fade) =
    [for (i = [0:N]) let(pol = 1 + 178 * i / N)
        [for (j = [0:M - 1]) e_point(E, pol, 360 * j / M, fur, fade(pol))]];

// ---------------------------------------------------------------- derived
apex_b = [leg_x, 0, base_h + leg_len];                     // the belly cone's point
S_b = [body_len / 2, body_w / 2, body_h / 2];
C_b = [0, 0, body_z];
E_body = [C_b, S_b, body_pitch, apex_unit(C_b, S_b, body_pitch, apex_b), 1, fur_depth];

S_h = [head_len / 2, head_w / 2, head_h / 2];
C_h = [head_x, 0, head_z];
beak_dir = rot_y([1, 0, 0], beak_angle);
beak_up = rot_y([0, 0, 1], beak_angle);                     // perpendicular, up and forward
apex_h = C_h + face_taper * S_h.x * beak_dir;              // the face's point, inside the beak
E_head = [C_h, S_h, beak_angle, [face_taper, 0, 0], 0.5, fur_depth * 0.5];

beak_in = 14;                                              // beak starts this far inside the face
beak_start = apex_h - beak_in * beak_dir;
beak_tip = apex_h + (apex_h.z - (base_h - 0.6)) / sin(beak_angle) * beak_dir;
beak_L = norm(beak_tip - beak_start);

// Shaggier at the tail; short on the face, none where the face meets the beak.
function body_fade(pol) = 1 + 0.7 * clamp01(1 - pol / 45);
function head_fade(pol) = clamp01((160 - pol) / 35);

base_x0 = C_b.x - body_len / 2 - base_margin;
base_x1 = beak_tip.x + base_margin;

// ---------------------------------------------------------------- the kiwi
module fur_body() {
    loft(e_rings(E_body, N_body, M_body, !sketch, function(p) body_fade(p)));
    loft(e_rings(E_head, N_head, M_head, !sketch, function(p) head_fade(p)));
}

function beak_pt(t) =
    beak_start + t * beak_L * beak_dir + 4 * beak_bend * t * (1 - t) * beak_up;
module beak() {
    n = sketch ? 30 : 80;
    sweep([for (i = [0:n]) beak_pt(i / n)],
          [for (i = [0:n]) lerp(beak_r0, beak_r1, pow(i / n, 0.8))], sides = sketch ? 16 : 32);
    translate(beak_tip) sphere(r = beak_r1, $fn = 16);
}

module eyes() {
    for (s = [-1, 1]) {
        a = s > 0 ? 28 : 152;
        p = e_surf(E_head, 112, a);
        translate(p + 0.2 * unit(p - C_h)) sphere(r = eye_r, $fn = sketch ? 16 : 32);
    }
}

// A tube whose rings are measured from a reference direction: a = 0 faces `ref` (the front of a
// leg, the top of a toe), and f(t, a) adds to the radius, for scales and joints.
module tube_f(P, R, ref, sides, f, phase = 0) {
    T = tangents(P); n = len(P) - 1;
    loft([for (i = [0:n]) let(N = unit(ref - (ref * T[i]) * T[i]), B = cross(T[i], N))
          [for (j = [0:sides - 1]) let(a = 360 * j / sides + phase)
               P[i] + (R[i] + f(i / n, a)) * (cos(a) * N + sin(a) * B)]]);
}
function bez(a, b, c, t) = (1 - t) * (1 - t) * a + 2 * t * (1 - t) * b + t * t * c;
// Shingled scales, 0..1: each rises along the member and drops at its lower edge.
function shingle(u) = let(p = frac(u)) p < 0.75 ? p / 0.75 : (1 - p) / 0.25;

// The tarsus: from inside the belly cone, back past the heel, down and forward to the ankle.
// The heel stays in the fur. Oval (deeper front to back), transverse scutes down its front,
// small reticulate scales behind, and a knob at the ankle joint.
function leg_top(s)  = [leg_x, s * 1.5, apex_b.z + 12];
function leg_heel(s) = [leg_x - 4, s * 3, apex_b.z - 3];
function ankle(s)    = [leg_x + 7, s * leg_spread, base_h + 7];
function leg_pt(s, t) = bez(leg_top(s), leg_heel(s), ankle(s), t);
leg_L = norm(ankle(1) - leg_top(1)) * 1.05;
function leg_r(t) = lerp(8, leg_r1, pow(clamp01(t / 0.55), 0.8)) + 0.9 * exp(-pow((t - 0.93) / 0.06, 2));
function leg_skin(t, a) = let(r = leg_r(t), show = clamp01((t - 0.3) / 0.1))
    0.12 * r * cos(2 * a)
    + (sketch ? 0 : show * (scute_depth * pow(max(0, cos(a)), 0.6) * shingle(t * leg_L / scute_pitch)
                            + 0.2 * max(0, -cos(a)) * abs(sin(360 * t * leg_L / 2.4) * sin(9 * a))));

// The foot: a sole pad sunk into the base; three toes forward and the hallux back, lying on the
// base (centreline 0.3 r above it) and lifting a little at the tip, each with knuckles, scutes on
// top, and a claw that curves down onto the base.
toes = [[-24, 25, 3], [6, 30, 4], [34, 24, 4], [155, 10, 2]];   // [azimuth for s = +1, length, joints]
function toe_r(t) = lerp(3.3, 1.9, t);
function toe_start(s) = ankle(s) + [2, 0, -3.5];
function toe_dir(s, k) = let(az = s * toes[k][0]) [cos(az), sin(az), 0];
function toe_pt(s, k, t) = let(A = toe_start(s), L = toes[k][1], d = toe_dir(s, k))
    [A.x + L * t * d.x, A.y + L * t * d.y,
     base_h + 0.3 * toe_r(t) + (A.z - base_h - 0.3 * toe_r(0)) * pow(1 - t, 3) + toe_lift * pow(t, 3)];
function toe_skin(k, t, a) = let(u = t * toes[k][2])
    toe_r(t) * 0.14 * pow(cos(180 * u), 8) * clamp01(t * 6)                  // knuckles
    + (sketch ? 0 : 0.25 * pow(max(0, cos(a)), 0.6) * shingle(t * toes[k][1] / 2.2));
function claw_pt(s, k, t) = let(E = toe_pt(s, k, 1), d = toe_dir(s, k), c = claw_len * (toes[k][2] > 2 ? 1 : 0.6))
    E - 1.5 * d + d * c * t + [0, 0, -(E.z - (base_h - 0.4)) * pow(t, 1.6)];

module legs() {
    n = sketch ? 24 : 120; m = sketch ? 12 : 40;
    for (s = [-1, 1]) {
        tube_f([for (i = [0:n]) leg_pt(s, i / n)], [for (i = [0:n]) leg_r(i / n)], [1, 0, 0],
               sides = sketch ? 16 : 40, f = function(t, a) leg_skin(t, a), phase = s > 0 ? 0 : 4.5);
        translate(ankle(s)) sphere(r = leg_r(1), $fn = sketch ? 16 : 32);
        translate([ankle(s).x + 3, ankle(s).y, base_h]) scale([7, 6, 4]) sphere(r = 1, $fn = sketch ? 16 : 40);
        for (k = [0:len(toes) - 1])
            tube_f([for (i = [0:m]) toe_pt(s, k, i / m)], [for (i = [0:m]) toe_r(i / m)], [0, 0, 1],
                   sides = sketch ? 12 : 24, f = function(t, a) toe_skin(k, t, a), phase = k * 3 + (s > 0 ? 0 : 7));
        for (k = [0:len(toes) - 1])
            translate(toe_pt(s, k, 1)) sphere(r = toe_r(1), $fn = sketch ? 12 : 24);
    }
}

module claws() {
    for (s = [-1, 1], k = [0:len(toes) - 1]) {
        m = sketch ? 8 : 20;
        sweep([for (i = [0:m]) claw_pt(s, k, i / m)], [for (i = [0:m]) lerp(1.8, 0.35, i / m)],
              sides = sketch ? 8 : 16, phase = k * 5 + (s > 0 ? 0 : 3));
    }
}

// An oval plinth with a bevelled top edge.
module base() {
    m = sketch ? 64 : 160;
    cx = (base_x0 + base_x1) / 2; rx = (base_x1 - base_x0) / 2; ry = base_w / 2;
    loft([for (z = [[0, 0], [base_h - 1.5, 0], [base_h, 1.5]])
          [for (j = [0:m - 1]) let(a = 360 * j / m) [cx + (rx - z[1]) * cos(a), (ry - z[1]) * sin(a), z[0]]]]);
}

// ---------------------------------------------------------------- summary
echo(str("Kiwi: ", round(base_x1 - base_x0), " x ", base_w, " mm base, ",
         round(C_b.z + S_b.z + fur_depth), " mm tall at ", size_pct, " %; legs ", leg_len,
         " mm; beak ", round(beak_L - beak_in), " mm at ", beak_angle, " deg, tip at x = ",
         round(beak_tip.x), "; sketch = ", sketch));

// ---------------------------------------------------------------- part selector
scale(size_pct / 100) {
    if (part == "assembly") {
        color("#9D432C") fur_body();                          // Brown
        color("#F7E6DE") { beak(); claws(); }                 // Beige
        color("#545454") legs();                              // Dark Gray
        color("#000000") eyes();                              // Black
        color("#00AE42") base();                              // Bambu Green
    }
    if (part == "fur")  difference() { fur_body(); eyes(); }
    if (part == "beak") difference() { union() { beak(); claws(); } fur_body(); legs(); base(); }
    if (part == "legs") difference() { legs(); fur_body(); base(); }
    if (part == "eyes") eyes();
    if (part == "base") base();
}
