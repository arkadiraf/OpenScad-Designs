// CRADLE TREE - a vase holder where the glass sits up in the branches of a tree.
// A rooted trunk stands under the glass; at 5-7 cm above the ground it opens
// into branches that cradle the glass, hold it on all sides and reach past its rim.
// The whole piece stays within 25 cm. Bark, knots and growth rings are modelled
// as surface detail on every member.
// Step 1 is the glass; every holder dimension is derived from it.
// All dimensions in mm. OpenSCAD trigonometry uses DEGREES.

/* [1 - Real glass vase] */
glass_d = 80;           // outer diameter of the glass
glass_h = 130;          // height of the glass
glass_wall = 2.5;       // preview only
glass_bottom = 5;       // preview only
show_glass = true;

/* [2 - Fit and height] */
clearance = 1;          // radial gap around the glass: 80 mm glass -> 82 mm bore
lift = 60;              // glass floor above the ground (50..70)
total_h = 250;          // overall height, branch tips included

/* [3 - Trunk and roots] */
trunk_waist = 19;       // trunk radius at its narrowest
root_collar = 12;       // extra trunk radius at the ground
grain_twist = 40;       // spiral grain: degrees the trunk turns from the ground to the floor;
                        // the branches keep turning at the same rate around the glass
root_count = 7;
root_reach = 46;        // how far the roots run out beyond the trunk foot
root_r0 = 8;            // root radius where it leaves the trunk
root_r1 = 2.4;          // root radius at the tip

/* [4 - Branches] */
branch_count = 5;       // main branches around the glass
branch_gap = 1.5;       // gap between the glass bore and the inner bark of a branch
branch_r = 8.5;         // branch radius at the glass floor
branch_top_r = 5.5;     // at the glass rim
tip_r = 2;              // at the tips
branch_lean = 22;       // how far the branches lean out above the rim

/* [5 - Bark] */
bark_depth = 1.2;       // fissure depth on the trunk (mm); thinner members get less
plate_w = 7;            // bark plate width (mm)
plate_len = 14;         // bark plate length (mm)

/* [6 - View] */
part = "assembly";      // [assembly, wood, glass, none]
show_guides = false;    // preview only: the ground and the total_h limit
quality = 1;            // [0:Draft, 1:Normal, 2:Fine]

/* [Hidden] */
$fn = quality == 0 ? 48 : 96;
spp = quality == 0 ? 5 : quality == 1 ? 8 : 12;          // surface samples per bark plate
step = quality == 0 ? 1.6 : quality == 1 ? 0.9 : 0.6;    // ring spacing along members (mm)
glass_r = glass_d/2;
bore_r = glass_r+clearance;
glass_top = lift+glass_h;
trunk_plates = 22;      // bark plates around the trunk

assert(glass_d > 2*glass_wall && glass_h > glass_bottom, "Invalid glass dimensions");
assert(lift >= 7.5, "The glass floor must be at least 7.5 mm above the plate");
assert(total_h > glass_top+30, "Leave room for the branches above the rim");

// ---------------------------------------------------------------- library
function lerp(a,b,t) = a+(b-a)*t;
function polar(r,a,z) = [r*cos(a),r*sin(a),z];
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
// The fissures meander at plate scale, so neighbouring furrows converge and
// part like real furrowed bark. Each column is broken into plates of its own
// length by shallower, tilted cross cracks, so the cracks never line up, and
// some plates are split lengthwise by a shallow secondary groove.
function bark(U,V) = let(
    u = U+0.45*n2(0.9*U,0.22*V),
    d = abs(u-round(u)),                                   // 0 on a fissure
    col = floor(u),
    h = frac(sin(col*78.233)*43758.5453),                  // per-column random
    v = V*(0.75+0.5*h)+h+0.35*(frac(u)-0.5)*(h-0.5)+0.12*n2(0.7*U+3,0.5*V),
    dv = abs(v-round(v)),                                  // 0 on a cross crack
    sp = abs(frac(u)-0.5),                                 // 0 along the plate middle
    ridge = smooth(0.04,0.24,d),
    crack = 0.5+0.5*smooth(0.05,0.2,dv),
    split = h>0.6 ? 0.62+0.38*smooth(0.02,0.1,sp) : 1)
    min(ridge*(0.85+0.15*sin(180*frac(u))),crack,split);

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
module bark_tube(P,R,depth,seed=0,knots=[]) {
    T=tangents(P); N=transport(T,0,normal0(T[0])); L=arclen(P);
    Rmax=max(R); n=max(5,round(2*PI*Rmax/plate_w)); S=n*spp;
    K=[for(k=knots) let(i=round(k[0]*(len(P)-1)), B=cross(T[i],N[i]))
        [L[i],atan2(k[1]*B,k[1]*N[i]),k[2]]];
    loft([for(i=[0:len(P)-1]) let(B=cross(T[i],N[i]))
        [for(j=[0:S-1]) let(a=360*j/S,
            ds=[for(k=K) norm([wrap(a-k[1])*PI/180*R[i],L[i]-k[0]])],
            calm=len(K)==0 ? 1 : min([for(m=[0:len(K)-1]) knot_calm(ds[m],K[m][2])]),
            bump=len(K)==0 ? 0 : sum([for(m=[0:len(K)-1]) knot_h(ds[m],K[m][2])]),
            r=R[i]-depth*R[i]/Rmax*calm*(1-bark(n*j/S+seed,L[i]/plate_len+0.37*seed))+bump)
            P[i]+r*(cos(a)*N[i]+sin(a)*B)]]);
}
// Points along a curve f(t), t = 0..1, spaced about `step` mm apart.
function curve(f,len_mm) = [for(k=[0:max(8,ceil(len_mm/step))]) f(k/max(8,ceil(len_mm/step)))];

// STEP 1: the glass, standing on its floor at the lifted height.
module glass_vase() {
    difference() {
        rotate_extrude() polygon(concat([[0,0],[glass_r-2,0]],
            [for(a=[-90:6:0]) [glass_r-2+2*cos(a),2+2*sin(a)]],
            [[glass_r,glass_h],[0,glass_h]]));
        translate([0,0,glass_bottom]) cylinder(r=glass_r-glass_wall,h=glass_h);
    }
}

// ---------------------------------------------------------------- STEP 2: trunk and branches
// The branches are laid out first: each starts inside the trunk, follows the
// spiral grain up and out, and reaches the glass at the floor. The trunk is then
// one surface (radius as a function of angle and height) wrapped around the
// inner half of every branch, so the branches stand out of it as ridges with no
// pockets between. Below, the trunk narrows to a waist and flares again into a
// root collar with buttresses where the roots leave.
waist_z = 0.35*lift;    // height of the trunk's narrowest point
branch_z0 = 0.3*lift;   // where the branches start inside the trunk
hug_z = lift+6;         // from here up the branches hug the glass
turn_rate = grain_twist/lift;   // spiral grain, degrees per mm of height
function tt(z) = z/lift;
function twist_at(z) = turn_rate*z;
function smax(a,b,k=3) = let(h=max(0,min(1,0.5+0.5*(a-b)/k))) lerp(b,a,h)+k*h*(1-h);

function branch_angle(j) = 360*j/branch_count+18+8*(rnd(j,5)-0.5);
function branch_end(j) = total_h-1-8*rnd(j,6);   // 1 mm spare: a tilted tip cap reaches past its path end
function branch_radius(z) = lookup(z,[[branch_z0,branch_r*1.15],[lift,branch_r],
    [glass_top,branch_top_r],[total_h,tip_r]]);
function hug(z) = bore_r+branch_gap+branch_radius(z);
// Branch centreline radius: eases out of the trunk to the glass, hugs it, and
// above the rim leans outward.
branch_rho0 = 10;
function branch_rho(j,z) = let(u=min(1,max(0,(z-branch_z0)/(hug_z-branch_z0))),
    rise=max(0,z-(glass_top-8))/(branch_end(j)-glass_top+8))
    z<hug_z ? lerp(branch_rho0,hug(hug_z),sin(90*u))
            : hug(z)+branch_lean*(0.8+0.4*rnd(j,7))*pow(rise,1.5);
function branch_point(j,t) = let(z=lerp(branch_z0,branch_end(j),t))
    polar(branch_rho(j,z),branch_angle(j)+turn_rate*(z-lift),z);

// Trunk radius: waist and root collar below, wrapped round the branches above
// (a smooth maximum), and a bevel above the floor that the bore cuts away.
lip_h = 6;
function trunk_core(z) = let(
    base = z<=waist_z ? trunk_waist+root_collar*pow((waist_z-z)/waist_z,2) : trunk_waist,
    wrapr = branch_rho(0,min(z,lift))-0.5*branch_radius(min(z,lift)))
    z<=lift ? smax(base,wrapr) : smax(base,wrapr)-0.9*(z-lift);
floor_r = trunk_core(lift);
function root_angle(i) = 360*i/root_count+20*(rnd(i,1)-0.5);
function lobe(da,w) = exp(-pow(da/w,2));
function trunk_rho(a,z) = let(fade=max(0,1-z/(waist_z+10)))
    trunk_core(z)*(1+0.45*fade*fade*sum([for(i=[0:root_count-1])
        lobe(wrap(a-root_angle(i)-twist_at(z)),16)]));

// Knots on the visible part of the trunk: [height, angle, size].
trunk_knots = [[24,70,5],[33,200,4],[17,305,3.5]];
module trunk() {
    top=lift+lip_h; nz=ceil(top/step); S=trunk_plates*spp;
    loft([for(k=[0:nz]) let(z=top*k/nz, th=twist_at(z))
        [for(j=[0:S-1]) let(a=360*j/S, rc=trunk_rho(a,z),
            ds=[for(q=trunk_knots) norm([wrap(a-q[1])*PI/180*rc,z-q[0]])],
            calm=min([for(m=[0:len(trunk_knots)-1]) knot_calm(ds[m],trunk_knots[m][2])]),
            bump=sum([for(m=[0:len(trunk_knots)-1]) knot_h(ds[m],trunk_knots[m][2])]),
            rho=rc-bark_depth*calm*(1-bark(trunk_plates*(a-th)/360,z/plate_len))+bump)
            [rho*cos(a),rho*sin(a),z]]]);
}

// Roots leave the buttresses and settle onto the bed: the centreline ends 0.3 r
// up, so the bed cut takes 35 % of the root height. Gentle one-sided bends only.
root_z0 = 14;           // where the roots leave the trunk
function root_radius(t) = root_r1+(root_r0-root_r1)*pow(1-t,1.5);
function root_point(i,t) = let(rho0=0.45*trunk_core(root_z0),
    L=trunk_core(0)-rho0+root_reach*(0.8+0.4*rnd(i,2)),
    bend=(rnd(i,3)-0.5)*40)
    polar(rho0+L*t, root_angle(i)+twist_at(root_z0)*(1-t)+bend*t*t,
        0.3*root_radius(t)+(root_z0-0.3*root_r0)*pow(1-t,2.2));
module roots() {
    for(i=[0:root_count-1]) let(f=function(t) root_point(i,t))
        bark_tube(curve(f,trunk_core(0)+root_reach), curve(function(t) root_radius(t),trunk_core(0)+root_reach),
            0.7*bark_depth,seed=3.1*i+1);
}

// ---------------------------------------------------------------- STEP 3: branches
// A side branch forks off each main branch above the rim and spreads sideways.
function fork_z(j) = glass_top-18+10*rnd(j,8);
function fork_t(j) = (fork_z(j)-branch_z0)/(branch_end(j)-branch_z0);
function side_point(j,t) = let(p=branch_point(j,fork_t(j)), a=atan2(p[1],p[0]),
    side=rnd(j,9)<0.5 ? -1 : 1, zt=total_h-22-18*rnd(j,10))
    polar(norm([p[0],p[1]])+16*pow(t,1.3), a+side*(22+10*rnd(j,11))*t, lerp(p[2],zt,t));
function side_radius(j,t) = lerp(0.75*branch_radius(fork_z(j)),tip_r*0.9,t);
function branch_path(j) = curve(function(t) branch_point(j,t),branch_end(j)-branch_z0+60);
// t (0..1 along a main branch) of the point at height z.
function branch_t(j,z) = (z-branch_z0)/(branch_end(j)-branch_z0);
function outward(p,turn=0) = let(a=atan2(p[1],p[0])+turn) [cos(a),sin(a),0];

// Short pruned twig stubs leave the main branches between the floor and the
// rim, pointing away from the glass and climbing at about 50 degrees.
twigs_per_branch = 2;
function twig_z(j,k) = lift+30+(glass_h-45)*(k+0.3+0.4*rnd(j,k,12))/twigs_per_branch;
function twig_point(j,k,t) = let(p=branch_point(j,branch_t(j,twig_z(j,k))), a=atan2(p[1],p[0]),
    side=rnd(j,k,13)<0.5 ? -1 : 1, len=11+4*rnd(j,k,14))
    polar(norm([p[0],p[1]])+0.7*len*pow(t,1.1), a+side*8*t, p[2]+len*t);
function twig_radius(t) = lerp(3.4,2.5,t);

// Main branch j with its knots, its fork and its twig stubs.
module branch(j) {
    {
        P=branch_path(j);
        bark_tube(P,[for(p=P) branch_radius(p[2])],0.8*bark_depth,seed=7.3*j+2,
            knots=[for(k=[0:1]) let(z=lift+25+50*k+25*rnd(j,k,20))
                [branch_t(j,z),outward(branch_point(j,branch_t(j,z)),40*(rnd(j,k,21)-0.5)),3+1.5*rnd(j,k,22)]]);
        bark_tube(curve(function(t) side_point(j,t),70),curve(function(t) side_radius(j,t),70),
            0.5*bark_depth,seed=5.1*j+4);
        for(k=[0:twigs_per_branch-1])
            bark_tube(curve(function(t) twig_point(j,k,t),16),curve(function(t) twig_radius(t),16),
                0.35*bark_depth,seed=2.7*j+k+9);
    }
}
module branches() { for(j=[0:branch_count-1]) branch(j); }

// Growth rings in the floor, seen through the glass bottom: off-centre like a
// real cross-section. Each groove is one revolved solid (a nested difference
// would blow up the preview's CSG tree).
module growth_rings() {
    for(k=[1:6]) let(f=k/6, rr=(bore_r-5)*pow(f,0.85))
        translate([1.5*f,0.8*f,lift-0.7]) rotate_extrude($fn=120) translate([rr-0.5,0]) square([1,2]);
}
// Flat cut at the build plate; the straight bore for the glass.
module bed_cut() {
    difference() { children(); translate([-300,-300,-100]) cube([600,600,100]); }
}
module bore_cut() {
    difference() { children(); translate([0,0,lift]) cylinder(r=bore_r,h=total_h,$fn=180); }
}
// The branches stay branch_gap outside the bore by design; the bore still cuts
// them in the final render (so the fit is guaranteed), but not in the preview,
// where cutting large textured members is slow.
module wood() {
    bore_cut() difference() { trunk(); growth_rings(); }
    if($preview) branches(); else bore_cut() branches();
    bed_cut() roots();
}

// Preview-only guides: the ground and the 25 cm height limit.
module guides() {
    %color([0.5,0.5,0.5,0.15]) translate([0,0,-0.5]) cylinder(r=110,h=0.5);
    %color([1,0.3,0.2,0.4]) translate([0,0,total_h]) difference() {
        cylinder(r=85,h=0.4); translate([0,0,-1]) cylinder(r=84,h=2);
    }
}

echo(str("Cradle Tree | glass ",glass_d," x ",glass_h," mm | bore d ",2*bore_r,
    " mm | glass floor at ",lift," mm, rim at ",glass_top," mm | total height ",total_h,
    " mm | trunk waist d ",2*trunk_waist," mm, floor d ",round(2*floor_r)," mm | ",branch_count,
    " branches turn ",round(turn_rate*glass_h)," deg around the glass, climbing ",
    round(atan(1/(hug(lift)*turn_rate*PI/180)))," deg | branch climb out of the trunk >= ",
    round(min([for(z=[lift/2:1:hug_z]) let(p=branch_point(0,(z-branch_z0)/(branch_end(0)-branch_z0)),
        q=branch_point(0,(z+1-branch_z0)/(branch_end(0)-branch_z0))) atan2(q[2]-p[2],norm([q[0]-p[0],q[1]-p[1]]))]))," deg"));

wood_color = "#6F5034";     // Bambu PLA Basic Cocoa Brown
if(part=="assembly") {
    if($preview && show_guides) guides();
    if(show_glass) %color([0.7,0.87,0.95,0.35]) translate([0,0,lift]) glass_vase();
    color(wood_color) wood();
}
if(part=="wood") wood();
if(part=="glass") color([0.7,0.87,0.95,0.35]) glass_vase();
