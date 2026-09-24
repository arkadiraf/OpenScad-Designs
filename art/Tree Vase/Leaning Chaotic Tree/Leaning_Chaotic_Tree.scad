// LEANING CHAOTIC TREE - a holder for a single flower in a 16 x 100 mm science
// tube, which leans out of the tree instead of standing in it. The round-bottomed
// tube rests low among the roots and tilts by `tilt` degrees, and the tree grows
// up around it: a trunk that comes down in buttresses splits into 3 limbs at
// three different heights, the limbs into 7 branches and those into 13, each fork
// turning its own way around the tube; some reverse partway up. The wood starts
// thick and only the ends come down to 2.5 mm, so the tree reads as a tree and
// not as wire. There is no floor and nothing is cut away for the tube: the wood
// grows against it like a tree round an obstacle, pressed flat where it touches,
// bark and all. The tube lies across the tree rather than in it: its round end
// rests on the roots out to one side, its mouth ends out on the other, and its
// middle passes over the centre, so the limbs meet it at their own heights -
// one under it, the other two at its sides. It slides in and out along its own
// axis, so nothing may stand in that line. Wherever two branches meet, the later one
// arches out over the other and the two grow together: it sinks in by arch_merge
// of the thinner one's thickness (10 % planned, 30 % at most), which also ties
// the cage together for printing. The trunk, its buttresses and the bases of the
// roots are one skin; the limbs and roots take over from it along defined
// contours where the surfaces cross almost parallel, wearing the same bark
// pattern on both sides, so the joins do not show. Every path is
// unique and nothing is symmetrical. Bark, knots and pruned twig stubs are
// modelled on every member.
// Step 1 is the tube; every holder dimension is derived from it.
// All dimensions in mm. OpenSCAD trigonometry uses DEGREES.

/* [1 - Real science tube] */
tube_d = 16;            // outer diameter of the glass tube
tube_h = 100;           // length of the tube
tube_wall = 1;          // preview only
tube_bottom = 8;        // preview only: where the bore starts above the round bottom
tube_foot = 8;          // radius of the rounded end; 8 = a round-bottomed test tube
show_tube = true;

/* [2 - Fit, lean and height] */
clearance = 0.25;       // radial gap around the tube: 0.5 mm on the diameter, so a 16 mm tube
                        // goes into a 16.5 mm bore
tilt = 25;              // degrees the tube leans from upright. Its end lands (tube_h/2)*sin(tilt)
                        // off centre and its mouth as far the other way, so the lean is what sets
                        // how far out it rests and how much room the trunk has beside it
tilt_az = 11;           // which way its mouth leans, degrees round the tree. Its end comes down
                        // on the opposite side, and this aims it along a root so it rests on one
                        // instead of dropping between two
lift = 2.5;             // the lowest point of the tube: resting on a root, out where they have
                        // thinned to about this height
total_h = 100;          // overall height, branch tips included: the tips finish level with the
                        // tube's mouth, so the flower has the height to itself

/* [3 - Trunk and roots] */
trunk_waist = 9;        // trunk radius at its narrowest
root_collar = 2.2;      // slight flare of the trunk between the buttresses
buttress = 13;          // how far the buttresses reach out over the ground beyond the trunk
buttress_h = 12;        // how high up the trunk the buttresses start (below the fork, so the
                        // two flares do not add up into a shelf)
grain_twist = 20;       // spiral grain: degrees the trunk turns from the ground to the tube
root_count = 9;
root_spread = 75;       // diameter the roots reach over the ground
root_r0 = 3.2;          // root radius where it starts, inside the trunk: thick enough to carry
                        // the end of the tube where it rests on them
root_r1 = 0.9;          // root radius at the tip
root_meander = 2.4;     // how far the roots snake from side to side (mm)
root_sweep = 6.5;       // how far a root tip swings off its straight line (mm)
side_roots = 0.6;       // share of the roots that fork a side root

/* [4 - Branches] */
press = 0.2;            // share of a branch's thickness pressed flat against the tube
branch_r = 3;           // radius of a scale-1 branch at the tube bottom (limbs are thicker):
                        // the limbs come out about 8 mm across and taper from there
tip_share = 0.55;       // how thick a branch ends: this share of its own thickness at the rim, so
                        // a tip is blunt wood and not a needle
tip_min = 7.5;          // but never thinner than this (x sc = 1.25 mm): every branch ends at
                        // about 2.5 mm across, which is where the taper is aimed
tip_taper = 240;        // over how long a branch narrows to its tip (x sc = 40 mm; these branches
                        // are long and fine, so the taper is a big share of one)
tip_curve = 2.5;        // how the narrowing is spread: 1 straight, higher stays wide and rounds off late
wander = 0.25;          // irregular wander of every branch (0 = straight): these grow up, and
                        // only the tube bends them
sprawl = 0.35;          // branches leaning out and tips flung sideways (0 = none)
wander_seed = 2;        // another number gives every branch a different wander
arch_merge = 0.10;      // where two branches meet, the one on top sinks into the other by this
                        // share of the thinner one's thickness (planned 0.10, 0.30 at most)
arch_w = 8;             // half-width of an arch, measured along the height (mm)
cage_z0 = 35;           // branches only arch over each other above this height: below it the
                        // limbs are still leaving the trunk together and are meant to be close
reverse_w = 32;         // height over which a branch reverses its turn (mm)
// The layout came from a search over random 3 -> 7 -> 13 trees (seed 127 of 12
// tried, 9000 each): the smallest empty sector around the tube at every height
// (131 deg - with 13 fine branches on a 16 mm tube the cage is open by design,
// and the tube is meant to show), a cradle that holds the round end (the three
// limbs 124 deg apart at most) and no stacked arches.
// Limbs, out of the trunk: [angle at the tube bottom (deg), turn rate as degrees
//  per tube height (+ counter-clockwise seen from above), reversal height above
//  the tube bottom (mm; 0 none), turn rate after it, radius scale, tip below the
//  top (mm), lean out above the rim (mm), meander amplitude (deg), meander
//  wavelength (mm), meander phase (deg), twig stubs (0..2)]
limb_table = [
    [    5,   28,    0,    0, 1.32,    0,    2,    2,   85,   40,    2],
    [  125,  -34,    0,    0, 1.26,    5,   -3,    2,   95,  210,    2],
    [  245,   22,   55,  -30, 1.36,    2,    5,    2,   75,  300,    2]];
// How each limb rises out of the trunk, so they part at different heights:
// [parting height (mm), where it reaches the side of the tube (mm), share of
//  the rise spent speeding up, share spent
//  slowing down]. Limb 0 parts first; limbs 1 and 2 go on together as one
// forked stem, and limb 2 parts last.
limb_rise = [[6, 45, 0.4, 0.4], [9, 52, 0.4, 0.4], [13, 58, 0.4, 0.4]];
// Forks, each off an earlier member (limbs are 0-2, then the forks in this
// order from 3); the first four make the 7 branches, the last six the 13. A fork
// takes `share` of its parent's thickness and the parent thins so that their two
// cross-sections add up to the one before the fork:
// [parent, fork height above the tube bottom (mm), turn rate (deg per tube
//  height), reversal height above the tube bottom (mm; 0 none), turn rate after
//  it, share, tip below the top (mm), lean out above the rim (mm), meander
//  amplitude (deg), meander wavelength (mm), meander phase (deg), twig stubs]
fork_table = [
    [    0,   18,  -30,    0,    0, 0.76,    3,    4,    2,   80,  150,    1],
    [    1,   24,   26,    0,    0, 0.74,    7,   -2,    2,   70,   20,    1],
    [    2,   30,  -24,    0,    0, 0.75,    4,    6,    2,   90,  260,    1],
    [    0,   36,   32,    0,    0, 0.72,    9,   -4,    2,   65,  100,    1],
    [    3,   52,   24,    0,    0, 0.74,    5,    3,    2,   85,  330,    0],
    [    1,   56,  -28,    0,    0, 0.72,    8,    0,    2,   75,   60,    1],
    [    4,   60,   30,    0,    0, 0.73,    3,    5,    2,   80,  190,    0],
    [    2,   64,  -22,    0,    0, 0.71,    6,   -5,    2,   70,  240,    1],
    [    5,   68,   26,    0,    0,  0.7,    4,    2,    2,   90,   10,    0],
    [    6,   72,  -26,    0,    0, 0.72,    8,   -2,    2,   85,  130,    1]];

/* [5 - Bark] */
bark_depth = 0.3;       // fissure depth on the trunk (mm); thinner members get less
plate_w = 2.2;          // bark plate width (mm)
plate_len = 4.4;        // bark plate length (mm)

/* [6 - View] */
part = "assembly";      // [assembly, wood, tube, paths, none]
show_guides = false;    // preview only: the ground, the root spread and the total_h limit
quality = 1;            // [0:Draft, 1:Normal, 2:Fine]
sketch = false;         // plain tubes, no bark or knots: the same shapes, rendered in seconds,
                        // for finding the geometry before the surface is worth looking at

/* [Hidden] */
$fn = quality == 0 ? 48 : 96;
spp = quality == 0 ? 5 : quality == 1 ? 8 : 12;          // surface samples per bark plate
step = quality == 0 ? 2 : quality == 1 ? 1 : 0.7;        // ring spacing along members (mm)
tube_r = tube_d/2;
bore_r = tube_r+clearance;
tube_top = lift+tube_h*cos(tilt);   // world height of the tube's mouth, once it leans
sc = tube_d/96;         // the fixed lengths below were set for a 96 mm tube; scaled to this one
trunk_plates = 16;      // bark plates around the trunk
tip_spare = 1.5;        // tips end this far below total_h: a leaning tip's end cap reaches past its
                        // path end by its own radius, and a blunt tip carries a wider cap

assert(tube_d > 2*tube_wall && tube_h > tube_bottom, "Invalid tube dimensions");
assert(lift >= 1.5, "The tube must clear the plate: its round end dips a little below lift when it leans");
assert(total_h > tube_top+30*sc, "Leave room for the branches above the mouth");

// ---------------------------------------------------------------- library
function lerp(a,b,t) = a+(b-a)*t;
function polar(r,a,z) = [r*cos(a),r*sin(a),z];

// The tube leans, so the cage wraps a tilted line rather than the z axis.
//  - axis_off(z) is how far that line is from the tree's axis at height z: negative under the
//    tube's midpoint, where its end rests on the roots, and positive above it, where its mouth
//    leans out the other way. The two axes cross at z_cross, halfway along the tube.
//  - tilt_k(a) converts between the two ways of measuring the gap: a horizontal offset of d in
//    direction a clears the tilted line by only d*tilt_k(a), so a wanted gap is divided by it.
z_cross = lift+tube_h/2*cos(tilt);              // the tube's middle, over the centre of the tree
function axis_off(z) = (z-z_cross)*tan(tilt);   // its axis, one side at the foot and the other at the mouth
function axis_xy(z) = axis_off(z)*[cos(tilt_az),sin(tilt_az)];
function tilt_k(a) = sqrt(1-pow(sin(tilt)*cos(a-tilt_az),2));
U = [sin(tilt)*cos(tilt_az),sin(tilt)*sin(tilt_az),cos(tilt)];      // up the tube
E0 = [cos(tilt)*cos(tilt_az),cos(tilt)*sin(tilt_az),-sin(tilt)];    // across it, for points on the axis
tube_foot_p = [axis_off(lift)*cos(tilt_az),axis_off(lift)*sin(tilt_az),lift];   // its round end
function unit(v) = v/max(norm(v),1e-6);
function frac(x) = x-floor(x);
function wrap(a) = a-360*round(a/360);        // angle difference into -180..180
function smooth(e0,e1,x) = let(t=max(0,min(1,(x-e0)/(e1-e0)))) t*t*(3-2*t);
function sum(v,i=0) = i>=len(v) ? 0 : v[i]+sum(v,i+1);
function sum_points(P,i=0) = i>=len(P) ? [0,0,0] : P[i]+sum_points(P,i+1);
// deterministic pseudo-random in [0, 1): reproducible, and keeps parts off exact angles
function rnd(a,b=0,c=0) = let(x=sin(a*127.1+b*311.7+c*74.7)*43758.5453) x-floor(x);
function tangents(P) = [for(i=[0:len(P)-1])
    unit(i==0 ? P[1]-P[0] : i==len(P)-1 ? P[i]-P[i-1] : P[i+1]-P[i-1])];
function normal0(t) = unit(cross(t,abs(t[2]) < 0.9 ? [0,0,1] : [1,0,0]));
function transport(T,i,n) = i>=len(T) ? [] :
    let(v=unit(n-(n*T[i])*T[i])) concat([v],transport(T,i+1,v));
function arclen(P,i=0,acc=[0]) = i>=len(P)-1 ? acc :
    arclen(P,i+1,concat(acc,[acc[i]+norm(P[i+1]-P[i])]));

// Solid loft through rings (each counter-clockwise seen from the direction of
// travel); the ends are fanned to their centroids.
module loft(rings) {
    N=len(rings); S=len(rings[0]);
    polyhedron(points=concat([for(r=rings) each r],
        [sum_points(rings[0])/S,sum_points(rings[N-1])/S]), faces=concat(
        [for(j=[0:S-1]) [N*S,j,(j+1)%S]],
        [for(i=[0:N-2]) for(j=[0:S-1])
            let(k=(j+1)%S, a=i*S+j, b=(i+1)*S+j, c=(i+1)*S+k, d=i*S+k)
            each [[a,b,c],[a,c,d]]],
        [for(j=[0:S-1]) [N*S+1,(N-1)*S+(j+1)%S,(N-1)*S+j]]), convexity=12);
}

// ---------------------------------------------------------------- bark
// Smooth pseudo-noise in -1..1 from three crossed sine waves.
function n2(x,y) = (sin(263*x+131*y+11)+sin(-97*x+211*y+47)+sin(59*x-173*y+83))/3;
// Bark height in 0..1 (1 = top of a plate, 0 = bottom of a fissure) at plate
// coordinates U (around; a fissure on every whole number) and V (along).
// The fissures meander at plate scale and drift over several plates, so
// neighbouring furrows converge and part like real furrowed bark. Each column is broken into plates of its own
// length by shallower, tilted cross cracks, so the cracks never line up, and
// some plates are split lengthwise by a shallow secondary groove. cw (0..1)
// scales the cross cracks.
function bark(U,V,cw=1) = let(
    u = U+0.5*n2(0.9*U,0.2*V)+0.45*n2(0.35*U+5,0.07*V),
    d = abs(u-round(u)),                                   // 0 on a fissure
    col = floor(u),
    h = frac(sin(col*78.233)*43758.5453),                  // per-column random
    v = V*(0.75+0.5*h)+h+0.35*(frac(u)-0.5)*(h-0.5)+0.12*n2(0.7*U+3,0.5*V),
    dv = abs(v-round(v)),                                  // 0 on a cross crack
    sp = abs(frac(u)-0.5),                                 // 0 along the plate middle
    ridge = smooth(0.04,0.24,d),
    crack = 1-cw*0.5*(1-smooth(0.05,0.2,dv)),
    split = h>0.6 ? 0.62+0.38*smooth(0.02,0.1,sp) : 1)
    min(ridge*(0.85+0.15*sin(180*frac(u))),crack,split);

// The bark of the trunk, fixed in space around the trunk axis: fissures run up
// the trunk (round it by angle, with the spiral grain), and down the flare and out
// along the roots (V falls with the distance beyond the trunk). Every surface near
// a join wears this, so where two surfaces meet their fissures line up.
function wbark(p) = let(r=norm([p[0],p[1]]), a=atan2(p[1],p[0]))
    bark(trunk_plates*(a-twist_at(min(p[2],crotch_z)))/360,(p[2]-max(0,r-trunk_waist))/plate_len);

// A knot at surface distance d (mm) from its centre, size kr: a swollen rim
// around a sunken eye, ringed like end grain. Returns a radius change in mm.
function knot_h(d,kr) = let(q=d/kr)
    kr/4*(0.9*exp(-1.3*q*q)-0.8*exp(-5*q*q)+0.2*cos(360*d/1.1)*exp(-q*q));
// How much bark remains near knots (the fissures fade around them).
function knot_calm(d,kr) = smooth(0.7*kr,1.5*kr,d);

// A tube along path P (radii R) wearing bark: plates sized from plate_w and
// plate_len, fissures cut up to `depth` into the radius (less where the tube is
// thinner), so R is the outer bark. seed shifts the pattern between members.
// knots: [[t, direction, size]] with t = 0..1 along the tube and direction a
// world vector the knot faces (it is placed where the ring points that way).
// tube = true: the smooth tube is pressed flat onto the tube where it would
// grow into it (press_tube), and the bark there, squashed to 40 % of its depth,
// is cut into the flat face, away from the tube. wmix: a function of the smooth
// surface point, 0 where the tube wears the trunk's bark (wbark, at the trunk's
// depth) and 1 where it wears its own; tubes that leave the trunk blend from one to
// the other past their handover contour.
module bark_tube(P,R,depth,seed=0,knots=[],tube=false,wmix=undef) {
    T=tangents(P); N=transport(T,0,normal0(T[0])); L=arclen(P);
    Rmax=max(R); n=sketch ? 6 : max(5,round(2*PI*Rmax/plate_w)); S=sketch ? n*3 : n*spp;
    K=[for(k=knots) let(i=round(k[0]*(len(P)-1)), B=cross(T[i],N[i]))
        [L[i],atan2(k[1]*B,k[1]*N[i]),k[2]]];
    loft([for(i=[0:len(P)-1]) let(B=cross(T[i],N[i]))
        [for(j=[0:S-1]) let(a=360*j/S,
            ds=[for(k=K) norm([wrap(a-k[1])*PI/180*R[i],L[i]-k[0]])],
            calm=sketch || len(K)==0 ? 1 : min([for(m=[0:len(K)-1]) knot_calm(ds[m],K[m][2])]),
            bump=sketch || len(K)==0 ? 0 : sum([for(m=[0:len(K)-1]) knot_h(ds[m],K[m][2])]),
            u=cos(a)*N[i]+sin(a)*B,
            q0=P[i]+R[i]*u, m=is_undef(wmix) ? 1 : wmix(q0),
            own=sketch ? 0 : bark(n*j/S+seed,L[i]/plate_len+0.37*seed),
            f=sketch ? 0 : lerp(bark_depth,depth*R[i]/Rmax,m)*calm*(1-(m>=1 ? own : lerp(wbark(q0),own,m)))-bump,
            q=tube ? press_tube(q0) : [q0,99,u],
            w=1-smooth(press_k,2*press_k,q[1]))
            q[0]+lerp(f,0.4*max(f,0),w)*unit(lerp(-u,q[2],w))]]);
}
// Points along a curve f(t), t = 0..1, spaced about `step` mm apart.
function curve(f,len_mm) = [for(k=[0:max(8,ceil(len_mm/step))]) f(k/max(8,ceil(len_mm/step)))];

// STEP 1: the tube, leaning out of the roots on its own axis.
module science_tube() {
    translate(tube_foot_p) rotate([0,0,tilt_az]) rotate([0,tilt,0]) difference() {
        rotate_extrude() polygon(concat([[0,0],[tube_r-tube_foot,0]],
            [for(a=[-90:6:0]) [tube_r-tube_foot+tube_foot*cos(a),tube_foot+tube_foot*sin(a)]],
            [[tube_r,tube_h],[0,tube_h]]));
        translate([0,0,tube_bottom]) cylinder(r=tube_r-tube_wall,h=tube_h);
    }
}

// The tube and its clearance as an obstacle: a cylinder of radius bore_r from
// lift up, its foot rounded like the tube's. Wood that would grow into it is
// pushed out onto its surface along a smooth direction field (the same shape
// with a much rounder foot, so the push never flips where a limb wraps round
// the foot); within press_k of it the push fades out smoothly.
// Measured in the tube's own frame: q across its axis, u along it from its round end. That is
// the same pair of coordinates the standing designs called (r, z), so the shapes below are
// unchanged - only what feeds them is. u also runs on past the tube's mouth, because the tube
// slides in and out along this line and nothing may stand in it.
env_e = tube_foot+clearance;        // rounding of the obstacle's end; with a round-bottomed tube
                                    // this equals bore_r and the end is a full hemisphere
env_eg = max(env_e,12*sc);          // rounding of the direction field: never sharper than the tube
press_k = 2.5*sc;                   // width of the smooth transition (mm)
function env_sdf(q,u) = let(x=q-(bore_r-env_e), y=env_e-u)
    x>0 && y>0 ? norm([x,y])-env_e : max(x,y)-env_e;
function env_dir(q,u) = let(x=q-(bore_r-env_eg), y=env_eg-u)         // [outward, along the tube]
    x>0 && y>0 ? [x,-y]/norm([x,y]) : x>y ? [1,0] : [0,-1];
// From a point inside, the distance along g to the obstacle's surface.
function env_exit(q,u,g) = let(
    ts = g[0]>1e-6 ? (bore_r-q)/g[0] : 1e9,
    tb = g[1]< -1e-6 ? u/(-g[1]) : 1e9,
    t0 = min(ts,tb))
    q+t0*g[0]>bore_r-env_e && u+t0*g[1]<env_e
        ? let(v=[q,u]-[bore_r-env_e,env_e], b=v*g) -b+sqrt(max(0,b*b-(v*v-env_e*env_e)))
        : t0;
// A point pushed out of the tube: [new point, its distance to the tube before
// the push (negative inside), the push direction].
function press_tube(p) = let(
    d3=p-tube_foot_p, u=d3*U, w=d3-u*U, q=norm(w),
    e=q>1e-6 ? w/q : E0, g=env_dir(q,u), d=env_sdf(q,u),
    s=d>=0 ? d : -env_exit(q,u,g), g3=g[0]*e+g[1]*U)
    [p+(smax(s,0,press_k)-s)*g3,s,g3];

// ---------------------------------------------------------------- STEP 2: trunk and branches
// The branches are laid out first: the three limbs start together inside the
// trunk, rise, part one after another, pass under the foot of the tube and
// climb onto its side. The trunk is then one surface (radius as a function of
// angle and height): a thick column that turns three-lobed as the first limb
// parts and narrows smoothly into the limbs, ending inside them at the crotch.
// Below, it comes down in buttresses that spread over the ground and run out as
// roots.
waist_z = 4;            // height of the trunk's narrowest point
branch_z0 = 1.5;        // where the limbs start, deep inside the trunk
turn_rate = grain_twist/lift;   // spiral grain, degrees per mm of height
function twist_at(z) = turn_rate*z;
function smax(a,b,k=3) = let(h=max(0,min(1,0.5+0.5*(a-b)/k))) lerp(b,a,h)+k*h*(1-h);

nm = len(limb_table); ns = len(fork_table); nmem = nm+ns;
function branch_radius(z) = branch_r*lookup(z,[[branch_z0,1.1],[lift,1],[tube_top,0.85],[total_h,0.65]]);
// Sideways offset from the tube's axis for a member of radius r pressed against it at angle a.
// The wanted perpendicular gap is divided by tilt_k, because a horizontal step away from a
// leaning line does not clear it by its full length.
function hug_off(r,a) = (bore_r+(1-press)*r)/tilt_k(a);
function room_up(top) = top-tube_top+10*sc;      // how much a tip has above the tube's mouth
function lean(z,top,amount) = let(rm=room_up(top)) rm<=0.01 ? 0
    : amount*min(1,rm/(70*sc))*pow(max(0,z-(tube_top-10*sc))/rm,1.5);
branch_rho0 = 6*sc;     // the limbs start this far off the axis, deep inside the trunk;
                        // it has to stay well under a limb radius or the trunk cannot end inside them
// Parting and out under the tube: a limb leaves the trunk upright, leans out at
// a steady rate and reaches the side of the tube upright again. The speed rises
// and falls linearly (limb_rise), which keeps every bend at least 1.25 times the
// limb's radius while the tube still presses a pad into it.
function trap(u,a,d) = let(m=1/(1-a/2-d/2))
    u<=0 ? 0 : u>=1 ? 1 : u<a ? m*u*u/(2*a) : u<1-d ? m*(u-a/2) : 1-m*(1-u)*(1-u)/(2*d);
function part_z(j) = limb_rise[j][0];
function hug_z(j) = limb_rise[j][1];
function ease_out(j,z) = trap((z-part_z(j))/(hug_z(j)-part_z(j)),limb_rise[j][2],limb_rise[j][3]);

// Turning: a rate r1 (degrees per tube height) that changes smoothly to r2
// around height zc (the integral of a smoothstep), zero at zref.
function ismooth(u) = u<=0 ? 0 : u<1 ? u*u*u-u*u*u*u/2 : u-0.5;
function rev(x,r1,zc,r2) = zc==0 ? 0 : (r2-r1)*reverse_w*ismooth((x-(zc-reverse_w/2))/reverse_w);
function turn(z,zref,r1,zc,r2) = (r1*(z-zref)+rev(z,r1,zc,r2)-rev(zref,r1,zc,r2))/tube_h;

// All members as one list, limbs first: [parent (-1 = trunk), start height,
// angle at the tube bottom, r1, reversal height (absolute, 0 none), r2, scale
// (limbs) or share (forks), end height, lean, meander amplitude, wavelength,
// phase, twig stubs].
members = concat(
    [for(j=[0:nm-1]) let(T=limb_table[j]) [-1,branch_z0,T[0],T[1],T[2]==0 ? 0 : lift+T[2],T[3],
        T[4],total_h-tip_spare-T[5],T[6],T[7],T[8],T[9],T[10]]],
    [for(s=[0:ns-1]) let(T=fork_table[s]) [T[0],lift+T[1],0,T[2],T[3]==0 ? 0 : lift+T[3],T[4],
        T[5],total_h-tip_spare-T[6],T[7],T[8],T[9],T[10],T[11]]]);
function Mb(i) = members[i];
function is_main(i) = Mb(i)[0]<0;
function m_z0(i) = Mb(i)[1];
function m_end(i) = Mb(i)[7];
kids = [for(i=[0:nmem-1]) [for(k=[0:nmem-1]) if(Mb(k)[0]==i) k]];
function prod(v,i=0) = i>=len(v) ? 1 : v[i]*prod(v,i+1);
// A member thins at each of its forks, from 8 mm below to 25 mm above it (a
// quicker change would kink the centreline, which follows the radius).
function thin(i,z) = prod([for(k=kids[i]) 1+(sqrt(1-Mb(k)[6]*Mb(k)[6])-1)*smooth(m_z0(k)-10*sc,m_z0(k)+30*sc,z)]);
function scale_at(i,z) = (is_main(i) ? Mb(i)[6] : Mb(i)[6]*scale_at(Mb(i)[0],m_z0(i)))*thin(i,z);
bscale = [for(i=[0:nmem-1]) is_main(i) ? Mb(i)[6] : Mb(i)[6]*scale_at(Mb(i)[0],m_z0(i))];
// Member radius: its share of the tree's thickness, narrowing to a blunt tip over its
// last tip_taper mm. The tip is a share of this member's own thickness at the rim, so
// thick branches end as thick wood and thin ones stay in proportion; the narrowing runs
// along a curve (tip_curve), so a branch keeps its thickness most of the way and only
// rounds off near the end instead of running out into a point.
function rim_r(i) = bscale[i]*thin(i,tube_top)*branch_radius(tube_top);
function tip_rad(i) = max(tip_min*sc,tip_share*rim_r(i));
function m_r(i,z) = lerp(bscale[i]*thin(i,z)*branch_radius(z),tip_rad(i),
    pow(max(0,min(1,(z-(m_end(i)-tip_taper*sc))/(tip_taper*sc))),tip_curve));
// Natural irregularity, different for every member (from rnd), on top of the
// table's turn and meander. It fades in over 50 mm from where the member leaves
// the trunk's seat or its parent, so forks still start on their parent.
//  - wander_t: sideways along the tube (mm), three waves of unrelated lengths;
//    the shortest is gentle, so a bend never gets tighter than about 8 mm.
//  - wander_r: lifting off the tube by up to 3-7.5 mm in places, then back.
//  - flick: the last part above the rim swings 3-8 mm to one side (less on
//    tips with under 58 mm of room, so they keep climbing steeply enough to
//    print; the lean shrinks the same way).
function wr(i,k,c=0) = rnd(i+17*wander_seed,k,c);
function wave(i,k,z,l0,l1) = sin(360*z/lerp(l0,l1,wr(i,k,1))+360*wr(i,k,2));
function w_fade(i,z) = let(z0=is_main(i) ? hug_z(i) : m_z0(i)) smooth(z0,z0+60*sc,z);
function wander_t(i,z) = wander*sc*w_fade(i,z)*(7*wave(i,31,z,110*sc,160*sc)+3*wave(i,32,z,55*sc,80*sc)
    +1.1*wave(i,33,z,34*sc,45*sc));
function wander_r(i,z) = sprawl*sc*w_fade(i,z)*lerp(4,9,wr(i,34))
    *pow(max(0,0.6*wave(i,35,z,140*sc,200*sc)+0.4*wave(i,36,z,70*sc,100*sc)),2);
function tip_room(i) = max(0,min(1,room_up(m_end(i))/(70*sc)));
function flick(i,z) = sprawl*sc*tip_room(i)*(4+6*wr(i,37))*(wr(i,38)<0.5 ? -1 : 1)
    *pow(max(0,z-(tube_top-10*sc))/max(0.01,room_up(m_end(i))),2);
function side_mm(i,z) = (wander_t(i,z)+flick(i,z))*180/PI/(bore_r+8*sc);   // as degrees
function m_phi(i,z) = is_main(i)
    ? Mb(i)[2]+turn(z,lift,Mb(i)[3],Mb(i)[4],Mb(i)[5])+Mb(i)[9]*sin(360*(z-lift)/Mb(i)[10]+Mb(i)[11])+side_mm(i,z)
    : let(z0=m_z0(i)) m_phi(Mb(i)[0],z0)+turn(z,z0,Mb(i)[3],Mb(i)[4],Mb(i)[5])
        +Mb(i)[9]*(sin(360*(z-z0)/Mb(i)[10]+Mb(i)[11])-sin(Mb(i)[11]))+side_mm(i,z);

// Trunk radius, one skin for the trunk, its buttresses and the bases of the roots
// and limbs. Near the ground it is a smooth maximum (fillet 10 mm) of the core
// column swollen by the buttresses and a copy of each root's base (root_band), so
// the roots meet the trunk in a fillet. Above, a
// smooth maximum of that and each limb's cross-section (the far side of the
// limb's circle seen from the axis), so the column turns three-lobed and the
// valleys deepen into the crotch.
//  - The core narrows by at most fade_rate mm per mm of height from where the
//    limbs start, so no exposed part of the trunk narrows fast enough to print as
//    a shelf; it is gone inside the lobes long before the crotch.
//  - Handover contour to the limbs, hand_z(a): below it the limb circles are
//    0.3 mm fuller than the limbs, so the trunk skin covers them; over the 7 mm
//    above it they sink 1.3 mm inside, so the limbs take over along a contour where
//    the two surfaces cross almost parallel. The contour wanders 7 mm round the
//    trunk. The fillet between the lobes narrows to nothing at the crotch, where
//    the loft ends inside the limbs.
fade_rate = 0.35;       // mm of trunk radius lost per mm of height: it has to be gone before
                        // the leaning tube arrives over the trunk, at about 25 mm
function trunk_core(z) = z<=waist_z ? trunk_waist+root_collar*pow((waist_z-z)/waist_z,2) : trunk_waist;
function soft_ramp(u,w) = u<=0 ? 0 : u<w ? u*u/(2*w) : u-w/2;
function core_r(z) = max(0,trunk_core(z)-fade_rate*soft_ramp(z-fade_z0,6*sc));
// The trunk is centred on the world axis, so it needs each limb's circle in world terms, not in
// the tube's leaning frame.
function limb_world(j,z) = let(q=m_xy(j,z)) [norm(q),atan2(q[1],q[0])];
function limb_circles(z) = z<branch_z0 ? [] : [for(j=[0:nm-1]) let(w=limb_world(j,z)) [w[0],w[1],m_r(j,z)]];
function hand_z(a) = crotch_z-sc*(4+8*(0.5+0.3*sin(3*a+40)+0.2*sin(7*a+110)));
function limb_off(a,z) = let(h=hand_z(a)) sc*lerp(0.4,-1.6,smooth(h,h+8*sc,z));
function circ_far(a,c) = let(d=wrap(a-c[1]), h=c[2]*c[2]-pow(c[0]*sin(d),2)) h<=0 ? 0 : c[0]*cos(d)+sqrt(h);
function smax_all(v,k,i=0) = i>=len(v)-1 ? v[len(v)-1] : smax(v[i],smax_all(v,k,i+1),k);
function trunk_r(a,z,C,b=0) = let(o=limb_off(a,z),
    k=0.05+9*sc*smooth(branch_z0,lobe_z0,z)*(1-smooth(lobe_z0,crotch_z,z)),
    base=smax_all(concat([core_r(z)+b],[for(i=[0:root_count-1]) root_band(i,a,z)]),12*sc))
    len(C)==0 ? base : smax_all(concat([base],[for(c=C) circ_far(a,[c[0],c[1],c[2]+o])]),k);
function root_angle(i) = 360*i/root_count+20*(rnd(i,1)-0.5);
function lobe(da,w) = exp(-pow(da/w,2));
// Buttresses: a ridge for every root, growing out of the trunk from buttress_h
// down and flaring ever faster towards the ground, like a real root flare. Each
// narrows as it goes and ends on the base of its root (root_band), with the trunk
// standing between them.
function butt_reach(i) = buttress*(0.75+0.35*rnd(i,2));
function butt(a,z) = z>=buttress_h ? 0 : let(f=(buttress_h-z)/buttress_h, w=lerp(26,9,f))
    sum([for(i=[0:root_count-1]) butt_reach(i)*pow(f,2.3)*lobe(wrap(a-root_angle(i)-0.3*twist_at(z)),w)]);
// The buttresses swell the core, so they fade out where the limbs take over.
function trunk_rho(a,z,C) = trunk_r(a,z,C,butt(a,z));

// Knots on the trunk column: [height, angle, size].
trunk_knots = [[22,70,5],[29,205,4.2],[16,300,3.7],[26,128,3.7]];
// Rings every 0.4 mm up to 12 mm (the round tops of the root bases) and twice the
// usual samples around (the sides of the root bases), then the usual spacing.
module trunk() {
    zl=12*sc; n1=ceil(zl/0.4); n2=ceil((crotch_z-zl)/step); S=2*trunk_plates*spp;
    loft([for(z=concat([for(k=[0:n1]) zl*k/n1],[for(k=[1:n2]) zl+(crotch_z-zl)*k/n2]))
        let(C=limb_circles(z))
        [for(j=[0:S-1]) let(a=360*j/S, rc=trunk_rho(a,z,C),
            ds=[for(q=trunk_knots) norm([wrap(a-q[1])*PI/180*rc,z-q[0]])],
            calm=min([for(m=[0:len(trunk_knots)-1]) knot_calm(ds[m],trunk_knots[m][2])]),
            bump=sum([for(m=[0:len(trunk_knots)-1]) knot_h(ds[m],trunk_knots[m][2])]),
            rho=rc-bark_depth*calm*(1-wbark([rc*cos(a),rc*sin(a),z]))+bump)
            [rho*cos(a),rho*sin(a),z]]]);
}

// Each root starts inside the trunk foot and lies on the ground (the centreline
// is 0.3 r up, so the bed cut takes 35 % of the root height), tapering all the
// way to its tip. Out to its foot contour, root_foot(i), it runs straight out
// under its buttress and the trunk skin carries a copy of it (root_band) just
// inside it, which the skin's smooth maximum turns into a fillet between the
// root and the trunk and buttress; the root comes out of that fillet at a
// shallow angle. Beyond the foot it snakes on over the ground to the root
// spread, with a one-sided sweep and a side-to-side meander gentle enough that
// its bend stays wider than the root.
root_tip = root_spread/2-root_r1-1-0.15*root_sweep;   // centreline radius of the longest tip (its sweep adds a little)
function root_s(i) = trunk_core(0)-10*sc;           // where it starts, inside the trunk
function root_end(i) = root_tip*(0.8+0.2*rnd(i,2));
function root_foot(i) = trunk_core(0)+butt_reach(i)+4*sc;   // just past the foot of its buttress
function root_tG(i) = (root_foot(i)-root_s(i))/(root_end(i)-root_s(i));
function root_u(i,t) = max(0,(t-root_tG(i))/(1-root_tG(i)));       // 0 up to the foot, 1 at the tip
function root_radius(i,t) = root_r1+(root_r0-root_r1)*pow(1-t,1.25);
function root_rho(i,t) = lerp(root_s(i),root_end(i),t);
function root_off(i,t) = let(u=root_u(i,t)) root_sweep*(2*rnd(i,3)-1)*u*u
    + root_meander*smooth(0,0.6,u)*sin(360*(root_rho(i,t)-root_foot(i))/((72+24*rnd(i,4))*sc)+360*rnd(i,5));
function root_point(i,t) = let(rho=root_rho(i,t))
    polar(rho,root_angle(i)+root_off(i,t)/rho*180/PI,0.3*root_radius(i,t));
// The copy of a root's base in the trunk skin: the lying, tapering cylinder
// seen from the axis (its far side along each ray, from its half-width at height
// z), inside the root by more than its bark is deep; over the last 8 mm before
// the foot contour it sinks a further 3.3 mm, so the fillet fades out before the
// copy ends.
band_in = bark_depth+0.3*sc;    // how far the copy sits inside the root: deeper than its bark
function band_r(i,rho) = root_radius(i,max(0,min(1,(rho-root_s(i))/(root_end(i)-root_s(i)))))-band_in
    -4*sc*smooth(root_foot(i)-10*sc,root_foot(i),rho);
function band_w(r,z) = let(q=r*r-pow(z-0.3*(r+band_in),2)) q>0 ? sqrt(q) : -1;
// The far side along a ray at angle a: the largest distance f at which the ray,
// f sin(d) off the root's axis, is still within the copy's half-width there
// (bisection: the copy tapers, so the half-width shrinks outward).
function band_ok(i,c,s,z,f) = let(w=band_w(band_r(i,f*c),z)) w>=0 && f*s<=w;
function band_bis(i,c,s,z,lo,hi,n) = n==0 ? lo : let(m=(lo+hi)/2)
    band_ok(i,c,s,z,m) ? band_bis(i,c,s,z,m,hi,n-1) : band_bis(i,c,s,z,lo,m,n-1);
function root_band(i,a,z) = let(d=wrap(a-root_angle(i)), c=cos(d), s=abs(sin(d)), f0=0.5*trunk_core(0))
    c<=0.7 || !band_ok(i,c,s,z,f0) ? 0 : band_bis(i,c,s,z,f0,root_foot(i)/c,9);
// Side roots fork off partway, head out to one side and turn outward again.
function has_side(i) = rnd(i,6)<side_roots;
function side_t(i) = lerp(root_tG(i),1,0.2+0.2*rnd(i,7));
function side_radius(i,t) = lerp(0.62*root_radius(i,side_t(i)),0.9*root_r1,pow(t,0.8));
function side_root_point(i,t) = let(t0=side_t(i), p=root_point(i,t0), q=root_point(i,t0+0.02),
    dir=atan2(q[1]-p[1],q[0]-p[0]), side=rnd(i,8)<0.5 ? -1 : 1, Ls=(30+12*rnd(i,9))*sc,
    P1=[p[0],p[1]]+0.5*Ls*[cos(dir+side*42),sin(dir+side*42)],
    P2=[p[0],p[1]]+Ls*[cos(dir+side*26),sin(dir+side*26)],
    xy=(1-t)*(1-t)*[p[0],p[1]]+2*t*(1-t)*P1+t*t*P2,
    r=side_radius(i,t), zs=0.3*r+(p[2]-0.3*side_radius(i,0))*pow(1-t,2))
    [xy[0],xy[1],zs];
root_len = root_tip+root_r0;
module roots() {
    for(i=[0:root_count-1]) {
        bark_tube(curve(function(t) root_point(i,t),root_len),curve(function(t) root_radius(i,t),root_len),
            0.7*bark_depth,seed=3.1*i+1,wmix=function(p) smooth(trunk_core(0)+5*sc,root_foot(i)+10*sc,norm([p[0],p[1]])));
        if(has_side(i))
            bark_tube(curve(function(t) side_root_point(i,t),45*sc),curve(function(t) side_radius(i,t),45*sc),
                0.55*bark_depth,seed=4.3*i+2);
    }
}

// ---------------------------------------------------------------- STEP 3: branches meet
// Centreline radius without arches: a limb parts from the others, passes under
// the foot of the tube (which presses its top flat: the tube stands on the
// three limbs) and onto its side, hugs it and leans out above the rim; a fork
// leaves its parent's centreline and settles on the tube within 15 mm.
function m_rho0(i,z,acc) = is_main(i)
    ? m_rho_g(i,z)
    : m_rho_g(i,z);
function bumps(C,z) = sum([for(c=C) c[2]*exp(-pow((z-c[1])/arch_w,2))]);
// A fork's own arches fade in over its first 21 mm, so it starts exactly on its
// parent's centreline and its end cap stays buried in it. Without this an arch
// just above a fork lifts the fork off its parent and its cap hangs in mid-air,
// which the slicer reports as a floating region. arch_h divides by the same ramp,
// so the arch still clears what it crosses.
function bump_ramp(i,z) = is_main(i) ? 1 : smooth(m_z0(i),m_z0(i)+25*sc,z);
function m_rho(i,z,acc) = m_rho0(i,z,acc)+(i<len(acc) ? bumps(acc[i],z)*bump_ramp(i,z) : 0);
// Where branch i meets an earlier branch m it arches out over it, just enough to
// sink in by arch_merge of the thinner one's thickness, then returns to the
// tube: [m, height, arch height]. A meeting is any closest approach (along the
// tube) nearer than the two radii, whether the paths cross or only touch. The
// arch height covers the need anywhere within 12 mm of the meeting. Branches
// are resolved in order, so an arch over a branch that itself arches lands on
// its arched position.
// Centreline radius on the tube, lifting off it in places and leaning out
// above the rim (arches left out).
function m_rho_g(i,z) = hug_off(m_r(i,z),m_phi(i,z))+lean(z,m_end(i),Mb(i)[8])+wander_r(i,z);
function sep(i,m,z) = abs(wrap(m_phi(i,z)-m_phi(m,z)))*PI/360*(m_rho_g(i,z)+m_rho_g(m,z));   // apart along the tube (mm)
// Leaning tips need more radial room: the gap between two tubes that lean out
// by slope s is their radial offset divided by sqrt(1 + s^2).
function lean_slope(i,z) = (m_rho_g(i,z+1)-m_rho_g(i,z-1))/2;
function need(i,m,z,acc) = let(rm=m_r(m,z), ri=m_r(i,z), reach=rm+ri-2*arch_merge*min(rm,ri), d=sep(i,m,z),
    s=(lean_slope(i,z)+lean_slope(m,z))/2)
    d>=reach ? 0 : max(0,m_rho(m,z,acc)+sqrt(reach*reach-d*d)*sqrt(1+s*s)-m_rho0(i,z,acc));
function arch_h(i,m,zc,zs,ze,acc) = max([for(k=[-7:7]) let(dz=2*sc*k, z=zc+dz)
    if(z>=zs && z<=ze) need(i,m,z,acc)/(exp(-pow(dz/arch_w,2))*max(0.25,bump_ramp(i,z)))]);
function crossings(i,acc) = [for(m=[0:1:i-1])
    let(zs=max(m_z0(i)+5,cage_z0,m_z0(m)+5,m==Mb(i)[0] ? m_z0(i)+48*sc : 0), ze=min(m_end(i),m_end(m)))
    for(z=[zs:1:ze])
        let(s0=z>zs ? sep(i,m,z-1) : 1e9, s1=sep(i,m,z), s2=z<ze ? sep(i,m,z+1) : 1e9)
        if(s1<=s0 && s1<s2 && s1<m_r(i,z)+m_r(m,z)) [m,z,arch_h(i,m,z,zs,ze,acc)]];
function build(i,acc=[]) = i>=nmem ? acc : build(i+1,concat(acc,[crossings(i,acc)]));
cross = build(0);
function rho(i,z) = m_rho(i,z,cross);
// Where each limb leaves the trunk: a small circle round the tree's axis, so the three start
// together inside the trunk and part as they reach out.
function start_xy(j) = branch_rho0*[cos(120*j),sin(120*j)];
// Where a member is heading: its place against the tube, as in the Wild tree.
function aim_xy(i,z) = let(a=m_phi(i,z)) axis_xy(z)+rho(i,z)*[cos(a),sin(a)];
// Where it actually is. A limb eases out of the trunk over its rise, a fork leaves its parent
// wherever the parent actually is - both in x and y, because an angle round the tube's axis is
// singular where that axis passes through the trunk, and a limb would whip round with it.
function m_xy(i,z) = is_main(i)
    ? lerp(start_xy(i),aim_xy(i,z),ease_out(i,z))
    : let(z0=m_z0(i)) lerp(m_xy(Mb(i)[0],z0),aim_xy(i,z),smooth(z0,z0+18*sc,z));
// The trunk ends where the first limb to part no longer contains the axis (with
// 2.9 mm to spare), and turns three-lobed over the 10 mm below.
crotch_z = [for(z=[branch_z0:0.5:lift+22]) if(min([for(j=[0:nm-1]) m_r(j,z)-3.5*sc-limb_world(j,z)[0]])<0) z][0]-0.5;
lobe_z0 = crotch_z-12*sc;
fade_z0 = branch_z0;            // where the core starts to narrow
function m_t(i,z) = (z-m_z0(i))/(m_end(i)-m_z0(i));
function m_point(i,t) = let(z=lerp(m_z0(i),m_end(i),t), q=m_xy(i,z)) [q[0],q[1],z];
function m_path(i) = curve(function(t) m_point(i,t),m_end(i)-m_z0(i)+80);

// Heights to keep knots and twigs away from: arches over or under the branch
// and its forks.
function busy(i) = concat([for(c=cross[i]) c[1]],
    [for(k=[0:nmem-1]) for(c=cross[k]) if(c[0]==i) c[1]],
    [for(k=[0:nmem-1]) if(Mb(k)[0]==i) m_z0(k)]);
function is_free(z,busy,d=26*sc) = min(concat([999],[for(b=busy) abs(z-b)]))>=d;
// Up to n free heights, at least 25 mm apart, from a jittered ladder.
function spaced(f,n,d=30*sc,i=0,acc=[]) = len(acc)>=n || i>=len(f) ? acc :
    spaced(f,n,d,i+1,len(acc)==0 || f[i]-acc[len(acc)-1]>=d ? concat(acc,[f[i]]) : acc);
function pick(z0,z1,busy,n,seed,ok=function(z) true) = z1<=z0 ? [] : spaced([for(k=[0:10]) let(z=z0+(z1-z0)*(k+0.5*rnd(seed,k,12))/10)
    if(z>=z0 && z<z1 && is_free(z,busy) && ok(z)) z],n);
// Room for a twig stub on member i at height z: every other member at least
// 12 mm clear of both around its first 17 mm, no arch or fork within 33 mm, and
// member i not swinging out into it.
function twig_ok(i,z) = twig_r0(i,z)>=twig_min && rho(i,z+22*sc)-rho(i,z)<=3*sc && is_free(z,busy(i),40*sc) && min(concat([99],[for(m=[0:nmem-1])
    if(m!=i && m_z0(m)<z+16*sc && m_end(m)>z+16*sc) sep(i,m,z+12*sc)-m_r(i,z)-m_r(m,z+12*sc)]))>=14*sc;
function outward(p,turn=0) = let(o=axis_xy(p[2]), a=atan2(p[1]-o[1],p[0]-o[0])+turn) [cos(a),sin(a),0];

// Short pruned twig stubs from a centreline point p of a branch heading T:
// they leave it at an angle, away from the tube and to the side the branch is
// not moving to, and climb at least 45 degrees, so they part from it clearly.
function twig_dir(p,T,seed) = let(o=outward(p), t=[-o[1],o[0],0], u=unit(T),
    sd=t*(u*t>0 ? -0.35 : 0.35), d=u+0.9*o+sd, h=norm([d[0],d[1]])) unit([d[0],d[1],max(d[2],h)]);
function twig_point(p,T,seed,t) = let(len=(15+5*rnd(seed,14))*sc)
    p+0.95*len*t*twig_dir(p,T,seed)+[0,0,1.5*sc*t*t];
function twig_r0(i,z) = 0.62*m_r(i,z);        // a stub is a share of the branch it leaves
twig_min = 2.7*sc;                            // and not worth placing below this radius
function twig_radius(t,r0) = r0*lerp(1,0.74,t);
function m_heading(i,z) = m_point(i,m_t(i,z+1))-m_point(i,m_t(i,z-1));
module twig(p,T,seed,r0) {
    bark_tube(curve(function(t) twig_point(p,T,seed,t),20*sc),curve(function(t) twig_radius(t,r0),20*sc),
        0.35*bark_depth,seed=seed,tube=true);
}
function knot_zs(i) = pick(is_main(i) ? lift+25*sc : m_z0(i)+18*sc,tube_top-15*sc,busy(i),is_main(i) ? 3 : 1,i+20);
function twig_zs(i) = pick(is_main(i) ? lift+32*sc : m_z0(i)+22*sc,tube_top-15*sc,busy(i),Mb(i)[12],i+40,
    function(z) twig_ok(i,z));

// Branch i with its knots and twig stubs, all clear of arches.
module member(i) {
    P=m_path(i);
    bark_tube(P,[for(p=P) m_r(i,p[2])],(is_main(i) ? 0.8 : 0.7)*bark_depth,seed=7.3*i+2,tube=true,
        wmix=is_main(i) ? function(p) smooth(crotch_z,crotch_z+20*sc,p[2]) : undef,
        knots=[for(z=knot_zs(i)) [m_t(i,z),outward(m_point(i,m_t(i,z)),40*(rnd(i,z,21)-0.5)),
            m_r(i,z)*(0.3+0.12*rnd(i,z,22))]]);
    for(z=twig_zs(i)) twig(m_point(i,m_t(i,z)),m_heading(i,z),i*7+z,twig_r0(i,z));
}
module branches() { for(i=[0:nmem-1]) member(i); }

// Flat cut at the build plate.
module bed_cut() {
    difference() { children(); translate([-300,-300,-100]) cube([600,600,100]); }
}
// Nothing is cut for the tube: the branches are pressed against it (press_tube).
module wood() {
    trunk();
    branches();
    bed_cut() roots();
}

// Preview-only guides: the ground, the root spread and the height limit.
module guides() {
    %color([0.5,0.5,0.5,0.15]) translate([0,0,-0.5]) cylinder(r=root_spread/2+10,h=0.5);
    %color([1,0.3,0.2,0.4]) difference() {
        cylinder(r=root_spread/2,h=0.6); translate([0,0,-1]) cylinder(r=root_spread/2-1,h=3);
    }
    %color([1,0.3,0.2,0.4]) translate([0,0,total_h]) difference() {
        cylinder(r=100*sc,h=0.4); translate([0,0,-1]) cylinder(r=100*sc-1,h=2);
    }
}

// Smallest climb angle along a path (for the overhang budget).
function rise(P) = min([for(i=[0:len(P)-2]) let(d=P[i+1]-P[i]) atan2(d[2],norm([d[0],d[1]]))]);
function above(P,z0) = [for(p=P) if(p[2]>=z0) p];
echo(str("Leaning Chaotic Tree | tube ",tube_d," x ",tube_h," mm | bore d ",2*bore_r,
    " mm | tube leans ",tilt," deg towards ",tilt_az," deg, its end at [",
    round(tube_foot_p[0]*100)/100,", ",round(tube_foot_p[1]*100)/100,", ",lift,
    "], mouth at ",round(tube_top*10)/10," mm | total height ",total_h,
    " mm | crotch at ",crotch_z,
    " mm | roots ",root_count," over ",root_spread," mm | branches ",nm," -> ",nm+4," -> ",nmem,
    " (",len([for(i=[0:nmem-1]) if(Mb(i)[4]>0) i])," reverse) | radius at the rim ",
    [for(i=[0:nmem-1]) round(m_r(i,tube_top)*10)/10]," | ",
    len([for(i=[0:nmem-1]) each cross[i]])," meeting points [branch, under, z, arch]: ",
    [for(i=[0:nmem-1]) for(c=cross[i]) [i,c[0],round(c[1]),round(c[2]*10)/10]],
    " | climb >= ",round(min([for(i=[0:nmem-1]) rise(above(m_path(i),lift/2))]))," deg"));

// Debug: every member's centreline and radii, for an outside clearance check.
if(part=="paths") {
    for(i=[0:nmem-1]) let(P=m_path(i))
        echo(str("PATH;b",i,";",is_main(i) ? "" : str("b",Mb(i)[0]),";",P,";",[for(p=P) m_r(i,p[2])]));
    for(i=[0:nmem-1]) for(z=twig_zs(i))
        let(p=m_point(i,m_t(i,z)), T=m_heading(i,z), P=curve(function(t) twig_point(p,T,i*7+z,t),20*sc))
        echo(str("PATH;twig",i,"_",round(z),";b",i,";",P,";",
            curve(function(t) twig_radius(t,twig_r0(i,z)),20*sc)));
    for(i=[0:root_count-1]) {
        echo(str("PATH;root",i,";;",curve(function(t) root_point(i,t),root_len),";",
            curve(function(t) root_radius(i,t),root_len)));
        if(has_side(i)) echo(str("PATH;twigroot",i,";root",i,";",curve(function(t) side_root_point(i,t),45*sc),";",
            curve(function(t) side_radius(i,t),45*sc)));
    }
}

wood_color = "#6F5034";     // Bambu PLA Basic Cocoa Brown
if(part=="assembly") {
    if($preview && show_guides) guides();
    if(show_tube) %color([0.7,0.87,0.95,0.35]) translate([0,0,lift]) science_tube();
    color(wood_color) wood();
}
if(part=="wood") wood();
if(part=="tube") color([0.7,0.87,0.95,0.35]) science_tube();
