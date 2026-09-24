// EMBRACING TREE - vase holder grown around a real glass. All dimensions in mm.
// One rear trunk rises from a growth-ring root plate and splits into two limbs
// that wrap around the glass and a tall central leader. Every tip carries a leaf
// cluster: a bright new shoot flanked by two mature leaves.
// Step 1 is the glass; every holder dimension below is derived from it.
// F5 shows the glass reference. F6 and the exported parts contain only the tree.
// OpenSCAD trigonometry uses DEGREES; the browser designers use radians.

/* [1 - Real glass vase] */
glass_d = 80;           // outer diameter of the glass
glass_h = 130;          // height of the glass
glass_wall = 2.5;       // preview only
glass_bottom = 5;       // preview only
show_glass = true;

/* [2 - Fit and root plate] */
clearance = 1;          // RADIAL: 80 mm glass -> 82 mm bore
base_h = 8;             // glass floor above the build plate (>= 7.5)
seat_h = 5;             // collar around the glass foot, above the floor
seat_wall = 2.8;
member_gap = 1.5;       // bore to the innermost trunk / limb bark
ring_count = 5;         // growth rings in the floor, seen through the glass bottom
ring_groove = 0.6;      // groove depth

/* [3 - Tree silhouette] */
trunk_r = 12;           // trunk radius at the bed
trunk_angle = 135;      // where the trunk stands (deg); 135 = behind the glass in the iso view
fork_h = 56;            // height of the three-way fork
embrace_angle = 112;    // how far each limb wraps around the glass (deg)
limb_r = 7;             // limb radius at the fork
twig_r = 3.2;
bark_depth = 0.07;      // bark rib height, fraction of the radius

/* [4 - Roots] */
root_count = 6;         // surface roots around the plate (the trunk adds three)
root_reach = 29;        // how far the roots run out over the bed
root_r0 = 5.5;          // where a root rises onto the plate rim
root_r1 = 2;            // at the tip
root_bend = 16;         // max sideways bend (deg)

/* [5 - Leaves and PLA palette] */
leaf_length = 26;
leaf_width = 12;
leaf_thickness = 2.4;   // >= 2.4 mm: six 0.4 mm lines
leaf_tilt = 27;         // side leaves of a cluster, deg from vertical (<= 30)
wood_color = "#6F5034";       // Bambu PLA Basic Cocoa Brown
mature_color = "#3F8E43";     // Bambu PLA Basic Mistletoe Green
new_growth_color = "#BECF00"; // Bambu PLA Basic Bright Green

/* [6 - View and export] */
part = "assembly"; // [assembly, holder, wood, leaves_dark, leaves_light, glass, fit_test, none]
quality = 1;       // [0:Draft, 1:Normal, 2:Fine]

/* [Hidden] */
$fn = quality == 0 ? 48 : 96;
steps = quality == 0 ? 20 : quality == 1 ? 36 : 54;   // rings per tube
sides = quality == 0 ? 12 : quality == 1 ? 24 : 36;   // samples per ring (6 bark ribs)
glass_r = glass_d / 2;
bore_r = glass_r + clearance;
glass_top = base_h + glass_h;
trunk_z0 = -2;          // the trunk foot starts below the bed; the bed cut flattens it
trunk_root_r0 = 6.5;    // flare roots at the trunk foot
trunk_root_z0 = 10;     // where they leave the trunk
root_z0 = base_h+seat_h-root_r0*(1+bark_depth)-0.5;   // surface roots start under the collar top
leaf_jitter = 6;        // deterministic variation of leaf facing and tilt (deg)
leaf_fold = 0.25;       // edge rise of the folded leaf per mm of half-width
shoot_ahead = leaf_fold*leaf_width/2+0.3;   // shoot in front of the mature pair (leaf_cluster)
leaf_sink = 3;          // leaves start this far back inside their tube, along its axis
// Tube radius at a tip that holds a whole cluster (three leaves spread over the shoot offset).
leaf_hold_r = (shoot_ahead+0.3+leaf_thickness)/2/(1-bark_depth)+0.3;

assert(glass_d > 2 * glass_wall && glass_h > glass_bottom, "Invalid glass dimensions");
assert(clearance >= 0.5 && base_h >= 7.5 && seat_wall >= 2, "Check glass fit/base thickness");
assert(member_gap >= 1, "Members must stay >= 1 mm outside the bore");
assert(fork_h > base_h + 20 && fork_h < glass_top - 45, "Fork must sit below the crown");
assert(root_z0 > 0.3 * root_r0, "Roots need room under the collar top: raise seat_h or thin root_r0");
assert(leaf_thickness >= 2.4 && leaf_width < leaf_length, "Keep leaves printable");
assert(leaf_tilt <= 30, "Steeper side leaves print with a shelf under the blade");
assert(twig_r >= leaf_hold_r, "Twigs are too thin to hold a leaf cluster");

function lerp(a,b,t) = a + (b-a)*t;
function polar(r,a,z) = [r*cos(a), r*sin(a), z];
function unit(v) = v / max(norm(v), 0.000001);
function tangents(P) = [for (i=[0:len(P)-1])
    unit(i==0 ? P[1]-P[0] : i==len(P)-1 ? P[i]-P[i-1] : P[i+1]-P[i-1])];
function normal0(t) = unit(cross(t, abs(t[2]) < 0.9 ? [0,0,1] : [1,0,0]));
function transport(T,i,n) = i>=len(T) ? [] :
    let(v=unit(n-(n*T[i])*T[i])) concat([v],transport(T,i+1,v));
function sum_points(P,i=0) = i>=len(P) ? [0,0,0] : P[i]+sum_points(P,i+1);
function path(f) = [for(j=[0:steps]) f(j/steps)];
function tip_dir(f) = unit(f(1)-f(1-1/steps));   // direction of a path at its end
// deterministic pseudo-random in [0, 1): reproducible, and keeps parts off exact angles
function rnd(a,b=0,c=0) = let(x=sin(a*127.1+b*311.7+c*74.7)*43758.5453) x-floor(x);
function jit(a,b,c) = (rnd(a,b,c)-0.5)*leaf_jitter;
// smallest climb angle along a path, and smallest bark-to-bore gap of a tube
function rise(P) = min([for(i=[0:len(P)-2]) let(d=P[i+1]-P[i]) atan2(d[2],norm([d[0],d[1]]))]);
function gap(P,R) = min([for(i=[0:len(P)-1]) if(P[i][2] > base_h)
    norm([P[i][0],P[i][1]]) - R[i]*(1+bark_depth)]) - bore_r;

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

// Parallel-transport tube; six shallow harmonic ribs form the bark.
// phase rotates the ring samples: tubes that meet must not share vertices.
module wood_tube(P,R,phase=0) {
    T=tangents(P); N=transport(T,0,normal0(T[0]));
    loft([for(i=[0:len(P)-1]) let(B=cross(T[i],N[i]))
        [for(j=[0:sides-1]) let(a=360*j/sides+phase,
            r=R[i]*(1+bark_depth*cos(6*a+18*i/(len(P)-1))))
            P[i]+r*(cos(a)*N[i]+sin(a)*B)]]);
}

// STEP 1: an 80 x 130 mm open glass cylinder, rounded at the bottom outside.
module glass_vase() {
    difference() {
        rotate_extrude() polygon(concat([[0,0],[glass_r-2,0]],
            [for(a=[-90:6:0]) [glass_r-2+2*cos(a),2+2*sin(a)]],
            [[glass_r,glass_h],[0,glass_h]]));
        translate([0,0,glass_bottom]) cylinder(r=glass_r-glass_wall,h=glass_h);
    }
}

// STEP 2: a rear trunk hugs the glass: its inner bark stays member_gap outside
// the bore all the way up, while it sways a little and thins towards the fork.
function trunk_radius(t) = lerp(trunk_r,limb_r+1,pow(t,0.7));
function trunk_rho(t) = bore_r+member_gap+trunk_radius(t)*(1+bark_depth);
function trunk_point(t) = polar(trunk_rho(t),trunk_angle+5*sin(180*t),lerp(trunk_z0,fork_h,t));
tree_r = trunk_rho(1);  // radius of the fork

// At the fork two opposite limbs wrap around the glass (s = -1, +1) while the
// stem carries on as a tall rear leader (s = 0), leaning the way the trunk
// leaned. Unequal tip heights keep the two limbs from mirroring each other.
function limb_top(s) = glass_top+(s==0 ? 17 : s<0 ? 2 : 9);
function limb_point(s,t) = polar(tree_r+(s==0 ? 9 : 7)*t*t,
    trunk_angle+s*embrace_angle*t-(s==0 ? 8*sin(180*t) : 0),
    lerp(fork_h,limb_top(s),t));
function limb_radius(s,t) = lerp(s==0 ? limb_r+1 : limb_r,leaf_hold_r,t);
// trunk + leader as one path, so the stem has no seam at the fork
stem_P = concat(path(function(t) trunk_point(t)), [for(j=[1:steps]) limb_point(0,j/steps)]);
stem_R = concat(path(function(t) trunk_radius(t)), [for(j=[1:steps]) limb_radius(0,j/steps)]);

// Offshoots emerge at two different heights and climb steeply. On the limbs
// they lean back towards the trunk, so no leaf cluster crowds its own limb or
// the limb tip; the leader sends one to each side.
function twig_start(k) = k==0 ? 0.48 : 0.76;
function twig_dir(s,k) = s==0 ? (k==0 ? 1 : -1) : -s;
function twig_point(s,k,t) = let(u=twig_start(k),p=limb_point(s,u),
    a=atan2(p[1],p[0]), direction=twig_dir(s,k))
    polar(norm([p[0],p[1]])+8*pow(t,1.2), a+direction*21*t,
        p[2]+(k==0 ? 28 : 25)*t);
function twig_radius(t) = lerp(twig_r,leaf_hold_r,t);

// Roots lie on the bed: the centreline sits 0.3 r up, so the bed cut takes
// 35 % of the root height and leaves a flat >= 95 % of its width. Bends are
// gentle and one-sided (a bend tighter than the root radius breaks CGAL).
function root_radius(t,r0) = root_r1+(r0-root_r1)*pow(1-t,1.6);   // flared base
// Surface roots start inside the collar (the bore trims their inner end into
// its wall), arch over the plate rim and run out between the trunk roots.
function plate_root_angle(i) = trunk_angle+360*(i+1)/(root_count+1)+10*(rnd(i,1)-0.5);
function plate_root_point(i,t) = let(L=root_reach*(0.85+0.3*rnd(i,2)),
    bend=(rnd(i,3)-0.5)*2*root_bend)
    polar(lerp(bore_r+0.5,bore_r+seat_wall+L,t), plate_root_angle(i)+bend*t*t,
        0.3*root_radius(t,root_r0)+(root_z0-0.3*root_r0)*pow(1-t,2.5));
// Three flare roots leave the trunk foot and settle onto the bed.
function trunk_root_point(s,t) = let(L=root_reach*(s==0 ? 0.8 : 1),
    bend=(rnd(s,4)-0.5)*root_bend)
    polar(trunk_rho(0)+L*t, trunk_angle+s*30*t+bend*t*t,
        0.3*root_radius(t,trunk_root_r0)+(trunk_root_z0-0.3*trunk_root_r0)*pow(1-t,2.5));

// Scalloped plate, always wider than the collar so the collar never overhangs.
function plate_r(a) = bore_r+seat_wall+3.5+2.2*cos(5*a)+1.0*sin(3*a);

module root_plate() {
    difference() {
        linear_extrude(height=base_h) polygon([for(a=[0:3:357]) plate_r(a)*[cos(a),sin(a)]]);
        // Off-centre growth rings stay visible through the glass floor
        // (inside the root ends, which fill the floor edge up to the collar).
        for(k=[1:ring_count]) let(f=k/ring_count, rr=(bore_r-8)*pow(f,0.85))
            translate([1.4*f,0.7*f,base_h-ring_groove]) difference() {
                cylinder(r=rr+0.5,h=ring_groove+1);
                translate([0,0,-1]) cylinder(r=rr-0.5,h=ring_groove+3);
            }
    }
}
// The collar locates the glass foot; its inner lip is left for the bore to cut.
module collar() {
    translate([0,0,base_h-0.2]) difference() {
        cylinder(r=bore_r+seat_wall,h=seat_h+0.2,$fn=180);
        translate([0,0,-0.1]) cylinder(r=bore_r-0.5,h=seat_h+0.4,$fn=180);
    }
}
module stem() { wood_tube(stem_P,stem_R); }
module roots() {
    for(i=[0:root_count-1]) wood_tube(path(function(t) plate_root_point(i,t)),
        path(function(t) root_radius(t,root_r0)),i%2*180/sides);
    for(s=[-1:1]) wood_tube(path(function(t) trunk_root_point(s,t)),
        path(function(t) root_radius(t,trunk_root_r0)),(s+1)*120/sides);
}
// The knot covers the start caps of the two limbs inside the stem.
module fork_knot() { translate(trunk_point(1)) sphere(r=limb_r+1,$fn=32); }
module branches() {
    for(s=[-1,1]) wood_tube(path(function(t) limb_point(s,t)),
        path(function(t) limb_radius(s,t)),(s+1)*60/sides);
    for(s=[-1:1]) for(k=[0:1]) wood_tube(path(function(t) twig_point(s,k,t)),
        path(function(t) twig_radius(t)),90/sides);
}
// Everything the leaves grow from.
module leaf_hosts() { stem(); branches(); }

// Straight bore for the glass and a flat cut at the build plate. The plate is
// left out: it lies entirely between the bed and the glass floor, and trimming
// it would put coplanar faces into the preview.
module trim() {
    difference() {
        union() children();
        translate([0,0,base_h]) cylinder(r=bore_r,h=glass_h+180,$fn=180);
        translate([-300,-300,-100]) cube([600,600,100]);
    }
}
module wood() {
    root_plate();
    trim() { collar(); stem(); roots(); fork_knot(); branches(); }
}

// Leaf: pointed lens, width ~ sin(pi*t)^0.9, with a gentle fold along the
// midrib (the V reads as a leaf from above). One lofted solid per leaf.
module leaf_blade(scale_leaf=1) {
    L=leaf_length*scale_leaf; W=leaf_width*scale_leaf; h=leaf_thickness/2;
    loft([for(i=[0:16]) let(t=i/16,w=0.45+(W/2-0.45)*pow(sin(180*t),0.9),f=w*leaf_fold)
        [[-w,L*t,f+h],[0,L*t,h],[w,L*t,f+h],
         [w,L*t,f-h],[0,L*t,-h],[-w,L*t,f-h]]]);
}

// The blade stands upright facing outward, its axis tilted from vertical
// along the glass, and grows from its lowest point b.
module leaf_at(b,a,tilt=0,size=1) {
    n=[cos(a),sin(a),0];
    v=cos(tilt)*[0,0,1]+sin(tilt)*[-sin(a),cos(a),0];
    u=cross(v,n);
    multmatrix([[u[0],v[0],n[0],b[0]], [u[1],v[1],n[1],b[1]],
        [u[2],v[2],n[2],b[2]], [0,0,0,1]]) leaf_blade(size);
}

// A bright new shoot flanked by two mature leaves. The shoot stands further
// out than the mature pair by more than the largest fold height, so where they
// overlap no mature leaf shows in front of the shoot: cutting the shoot out of
// them leaves no slivers. Unequal offsets keep the pair from mirroring.
// Every leaf starts leaf_sink mm back inside the tube that ends at p (heading
// d), with the cluster centred on the tube axis. So each leaf's lowest corner
// is embedded in wood: a corner below the tube would start in mid-air (what
// Bambu Studio reports as "floating regions").
module leaf_cluster(p,d,id,tone,size=1) {
    a=atan2(p[1],p[0])+jit(id,1,0);
    n=[cos(a),sin(a),0];
    b=p-leaf_sink*d;
    shoot=(shoot_ahead+0.3)/2;
    if(tone=="light" || tone=="all") leaf_at(b+shoot*n,a,jit(id,2,0),size);
    if(tone=="dark" || tone=="all") for(sign=[-1,1])
        leaf_at(b+(shoot-shoot_ahead-(sign<0 ? 0 : 0.3))*n,a+jit(id,3,sign),
            sign*leaf_tilt+jit(id,4,sign)/2,size*0.88);
}
module leaves_raw(tone="all") {
    for(s=[-1:1]) {
        leaf_cluster(limb_point(s,1),tip_dir(function(t) limb_point(s,t)),3*s,tone,1.05);
        for(k=[0:1]) leaf_cluster(twig_point(s,k,1),tip_dir(function(t) twig_point(s,k,t)),
            3*s+k+1,tone,k==0 ? 0.85 : 0.95);
    }
}
// Colour parts must not overlap: each leaf tone gives way to the wood it grows
// from, and the mature leaves give way to the new shoot.
module leaves_light() { difference() { leaves_raw("light"); leaf_hosts(); } }
module leaves_dark() {
    difference() { leaves_raw("dark"); leaf_hosts(); leaves_raw("light"); }
}

module fit_test() {
    difference() {
        cylinder(r=bore_r+seat_wall,h=seat_h,$fn=180);
        translate([0,0,-0.1]) cylinder(r=bore_r,h=seat_h+0.2,$fn=180);
    }
}

limb_P = [for(s=[-1,1]) path(function(t) limb_point(s,t))];
twig_P = [for(s=[-1:1]) for(k=[0:1]) path(function(t) twig_point(s,k,t))];
echo(str("Embracing Tree | glass ",glass_d," x ",glass_h," mm | bore d ",2*bore_r,
    " mm | glass floor ",base_h," mm | fork at z ",fork_h," r ",round(tree_r*10)/10,
    " | stem gap ",round(gap(stem_P,stem_R)*10)/10,
    " mm, limb gap ",round(min([for(s=[-1,1]) gap(limb_P[(s+1)/2],path(function(t) limb_radius(s,t)))])*10)/10,
    " mm | limbs rise >= ",round(min([for(P=limb_P) rise(P)]))," deg, twigs >= ",
    round(min([for(P=twig_P) rise(P)]))," deg | ",9*3," leaves | crown top ~",
    round(limb_top(0)+leaf_length*1.05-2)," mm | tips r ",round(leaf_hold_r*10)/10," mm | 3 PLA colors"));

// Export wood / leaves_dark / leaves_light at the SAME origin and merge them
// into one multipart object (tools/build_design.py). Print upright.
if(part=="assembly") {
    if(show_glass && $preview)
        %color([0.7,0.87,0.95,0.22]) translate([0,0,base_h]) glass_vase();
    color(wood_color) wood();
    color(mature_color) leaves_raw("dark");       // leaves never reach the bore or the bed
    color(new_growth_color) leaves_raw("light");
}
if(part=="glass") color([0.7,0.87,0.95,0.35]) glass_vase();
if(part=="holder") { wood(); leaves_raw(); }
if(part=="wood") wood();
if(part=="leaves_dark") leaves_dark();
if(part=="leaves_light") leaves_light();
if(part=="fit_test") fit_test();
