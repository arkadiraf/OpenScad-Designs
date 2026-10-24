// Spiral Bract leaf library - shared by the planter and its saucer (include<>, not use<>).
//
// A leaf (bract) is solid from inside the body's wall out to its face, over its own outline
// (u across -1..1, t from base 0 to tip 1). The face is iteration 1's dome - fading to nothing at the
// base and lower edges, a midrib spine, an edge step along the upper edges - plus `lift`, how the leaf
// bends open: flare, cup or trough, twist, tip curl. Only a lip along the upper free edges is
// hollow, `edge_t` thick at the edge, so the leaves read thin where their edges show. Being solid,
// overlapping leaves merge, and the lower leaf, higher where its tip crosses the next leaf's base,
// shows in front - no air under the leaves, nothing passing through anything.
// Mirrors Spiral_Bract_Planter_leaves.py: change the two together.
//
// The including file defines: R(z), dR(z) (the envelope radius and its slope), under_shift(z)
// (how much deeper the solid underside goes near a rim, 0 elsewhere), edge_t, texture, GM (rows) and GN (columns).
//
// g = [phi, z, L, W, tilt, sh, basep, tipp, asym, sway, H, p, tipf, ridge, Tm, F, t0, k, C, tw, curl, nv, vc, vd]
//      0    1  2  3  4     5   6      7     8     9     10 11 12    13     14  15 16  17 18 19  20    21  22  23

function ss(a, b, x) = let(s = min(1, max(0, (x - a) / (b - a)))) s * s * (3 - 2 * s);

function leaf_w(g, t, side) =
    let(sh = g[5],
        f = t <= sh ? pow(sin(90 * min(1, t / sh)), g[6])
                    : pow(max(0, cos(90 * min(1, (t - sh) / (1 - sh)))), g[7]))
    g[3] * f * (1 + side * g[8]);
function leaf_xc(g, t) = g[9] * g[3] * t * t;

function along(g, t) =
    let(pk = min(g[5] + 0.1, 0.72))
    t <= pk ? pow(sin(90 * min(1, t / pk)), 1.3)
            : g[12] + (1 - g[12]) * cos(90 * min(1, (t - pk) / (1 - pk)));
// iteration 1's bract: dome, midrib spine, edge step above the shoulder
function dome(g, u, t) =
    let(a = along(g, t), au = min(1, abs(u)), H = g[10])
    H * a * (1 - pow(au, g[11]))
    + g[13] * H * 0.35 * a * pow(max(0, 1 - au / 0.4), 2)
    + edge_t * ss(g[5] + 0.04, g[5] + 0.24, t);
// how the leaf bends open: zero below t0 (above the shoulder), so the lower edges stay on the body
function lift(g, u, t) =
    let(t0 = g[16], s = ss(t0 - 0.05, t0 + 0.15, t),
        gg = pow(min(1, max(0, (t - t0) / (1 - t0))), g[17]))
    g[15] * gg + s * (g[18] * (1 - u * u) + g[19] * u * ss(t0, 1, t)) + g[20] * pow(ss(0.72, 1, t), 2);
// lip thickness: edge_t at the edge, Tm further in
function thick(g, u, t) = edge_t + (g[14] - edge_t) * (1 - u * u);
// texture: lateral veins running up and out to the edges
function relief(g, u, t) =
    let(xc = leaf_xc(g, t), x = xc + u * leaf_w(g, t, u >= 0 ? 1 : -1), y = t * g[2], au = abs(u),
        ph = g[21] * (y - g[22] * abs(x - xc)) / g[2],
        veins = g[23] * pow((1 + cos(360 * ph)) / 2, 2),
        fade = (1 - ss(0.72, 0.97, au)) * ss(0.06, 0.22, t) * (1 - ss(0.86, 1, t)))
    veins * fade * along(g, t);

// height of a leaf-plane point
function leaf_z(g, u, t) =
    let(x = leaf_xc(g, t) + u * leaf_w(g, t, u >= 0 ? 1 : -1)) g[1] - x * sin(g[4]) + t * g[2] * cos(g[4]);

// [outer, inner] offsets along the envelope normal: solid down into the wall, except a lip along the
// upper free edges (within 2-10 mm of the edge, where the leaf has bent open), edge_t thick at the edge.
// Near a rim the solid underside reaches deeper (under_shift), so the crown stands on the rim; the face
// stays where it is, and the underside stops short of the cavity, so the cavity never cuts a leaf.
function offsets(g, u, t) =
    let(face = dome(g, u, t) + lift(g, u, t),
        dist = min((1 - abs(u)) * leaf_w(g, t, u >= 0 ? 1 : -1), (1 - t) * g[2] * 0.6),
        lip = (1 - ss(2, 10, dist)) * ss(g[16] - 0.05, g[16] + 0.15, t) * ss(edge_t + 0.5, edge_t + 2.5, face))
    [face + (texture ? relief(g, u, t) : 0),
     -0.8 + lip * max(0, face - thick(g, u, t) + 0.8) + (1 - lip) * under_shift(leaf_z(g, u, t))];

// leaf-plane (u, t) -> 3D point at `off` mm along the envelope normal
function leaf_pt(g, u, t, off) =
    let(xc = leaf_xc(g, t), x = xc + u * leaf_w(g, t, u >= 0 ? 1 : -1), y = t * g[2],
        a = x * cos(g[4]) + y * sin(g[4]), b = -x * sin(g[4]) + y * cos(g[4]),
        z = g[1] + b, r = R(z), phi = g[0] + a / r * 180 / PI, d = dR(z))
    [r * cos(phi), r * sin(phi), z] + off * [cos(phi), sin(phi), -d] / sqrt(1 + d * d);

module leaf(g) {
    M = GM; N = GN;
    rows = M - 1;                          // t = 1/M .. (M-1)/M; the base and the tip are apexes
    S = N + 1;
    uv = [for (i = [1:M - 1]) for (j = [0:N]) [2 * j / N - 1, i / M]];
    off = [for (p = uv) offsets(g, p[0], p[1])];
    outer = [for (k = [0:len(uv) - 1]) leaf_pt(g, uv[k][0], uv[k][1], off[k][0])];
    inner = [for (k = [0:len(uv) - 1]) leaf_pt(g, uv[k][0], uv[k][1], off[k][1])];
    nO = rows * S;
    OB = 2 * nO; OT = OB + 1; IB = OB + 2; IT = OB + 3;
    ob = offsets(g, 0, 0); ot = offsets(g, 0, 1);
    pts = concat(outer, inner, [leaf_pt(g, 0, 0, ob[0]), leaf_pt(g, 0, 1, ot[0]),
                                leaf_pt(g, 0, 0, ob[1]), leaf_pt(g, 0, 1, ot[1])]);
    o = function(i, j) i * S + j;
    q = function(i, j) nO + i * S + j;
    faces = concat(
        [for (i = [0:rows - 2]) for (j = [0:N - 1]) [o(i, j), o(i + 1, j), o(i + 1, j + 1), o(i, j + 1)]],
        [for (j = [0:N - 1]) [OB, o(0, j), o(0, j + 1)]],
        [for (j = [0:N - 1]) [OT, o(rows - 1, j + 1), o(rows - 1, j)]],
        [for (i = [0:rows - 2]) for (j = [0:N - 1]) [q(i, j), q(i, j + 1), q(i + 1, j + 1), q(i + 1, j)]],
        [for (j = [0:N - 1]) [IB, q(0, j + 1), q(0, j)]],
        [for (j = [0:N - 1]) [IT, q(rows - 1, j), q(rows - 1, j + 1)]],
        // side walls round the outline: base, up the right edge, tip, down the left edge
        let(loop = concat([[OB, IB]], [for (i = [0:rows - 1]) [o(i, N), q(i, N)]], [[OT, IT]],
                          [for (i = [rows - 1:-1:0]) [o(i, 0), q(i, 0)]]),
            L = len(loop))
        [for (k = [0:L - 1]) let(a = loop[k], b = loop[(k + 1) % L]) [a[0], b[0], b[1], a[1]]]
    );
    polyhedron(points = pts, faces = faces, convexity = 6);
}
