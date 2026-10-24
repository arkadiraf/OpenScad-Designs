// WALL CLIMBER TREE - a tree that grows out of the wall, for sprawling and climbing plants.
// Two parts that slide together:
//   ROOTS - the wall side: a buttressed burl where the trunk leaves the wall, and roots that crawl
//           over the wall in every direction, meandering and forking. It prints flat on its back.
//   TREE  - the front half of the burl, the trunk and the crown. The trunk carries on as a leader;
//           two limbs part from it just above the burl, and the crown splits 3 -> 7 -> 13, sprawling
//           in all directions, its branches ending at different lengths, up to 150 mm above the
//           first parting. It prints standing, as it hangs.
// Iteration 3: roots and crown both drawn at random (root_seed; the layout script's seed), and
// the branches swirl round their own line and round each other, growing together where they meet.
// Iteration 5: the step round the base of the leader is gone (the burl follows the trunk's real,
// thinning radius and never crosses it), forks get a fillet in their parent (fork copies), and the
// branches zigzag and tangle (see the layout script).
// Iteration 4: smoother forks (each leaves close along its parent and peels off slowly), forks
// clearly thinner than what they leave, and a wider, sprawlier crown (see the layout script).
// Both halves of the burl come from one surface, cut by the plane y = split_y, so their outlines
// match. The tree slides down a dovetail into the roots until its foot sits on a shelf of the burl;
// one 6 mm screw then goes through the tree's lower keel and the roots into the wall, so the tree
// clamps the roots against the wall.
//
// The base follows the Wild Chaotic Tree (art/Tree Vase/Wild Chaotic Tree; guide §17): the burl is
// one skin, a smooth maximum of the trunk's section, a buttress ridge running out along every root,
// and a copy of each root's base, so the roots come out of a fillet. Trunk, burl and the roots'
// bases all wear one bark fixed in space round the trunk axis (wbark), so their fissures line up
// across every join; the roots blend into their own bark past their buttress, the trunk once it
// bends up into the crown.
//
// The crown is searched by Wall_Climber_Tree_layout.py and read from Wall_Climber_Tree_layout.scad
// (climb >= 45 deg everywhere, so it prints standing; clearance between branches; height).
//
// Axes: the wall is the plane y = 0 (the tree is in y > 0), +z is up, x runs along the wall.
// All dimensions in mm. OpenSCAD trigonometry uses DEGREES.

include <Wall_Climber_Tree_layout.scad>

/* [1 - Trunk and split] */
trunk_z = 37;           // where the trunk's axis meets the wall
trunk_climb = 50;       // deg, the trunk leaves the wall climbing this steeply
split_y = 12;           // the plane between the two parts, from the wall

/* [2 - Screw and slide] */
screw_d = 6;            // screw diameter
head_d = 12;            // screw head diameter (the counterbore is 0.5 mm wider)
under_head = 6;         // tree wood under the screw head
foot_z = 31;            // the tree's foot (the shelf it sits on)
screw_up = 9;           // screw above the foot
rail_len = 26;          // dovetail tongue length above the foot
rail_w = 10;            // tongue width at the tree's back
rail_w2 = 14;           // tongue width at its face (the dovetail)
rail_h = 3.5;           // tongue height
fit = 0.25;             // clearance per side in the slide

/* [3 - Burl] */
trunk_r = 11;           // trunk radius (the layout is made for it)
flare = 4;              // extra radius of the burl against the wall, between the buttresses
flare_h = 20;           // how far out the flare reaches
lobe = 24;              // the keel under the trunk that carries the screw
lobe_w = 60;            // its angular half-width, deg: wider than the counterbore
burl_h = 34;            // where the trunk takes over from the burl skin
buttress = 20;          // how far the buttresses reach out over the wall beyond the burl
buttress_h = 30;        // how far out from the wall they start (the burl's full depth)

/* [4 - Roots] */
root_count = 9;
root_reach = 98;        // how far the longest roots run from the trunk's foot
root_r0 = 7.6;          // root radius where it leaves the burl (1.35 x it must stay under split_y)
root_r1 = 2.0;          // at the tips
root_meander = 6.5;     // how far the roots snake from side to side (mm)
root_sweep = 20;        // how far a root tip swings off its straight line (mm)
side_roots = 0.7;       // share of the roots that fork a side root
root_seed = 2;          // another number gives another root system

/* [5 - Bark] */
bark_depth = 1.0;       // fissure depth on the trunk (mm); thinner members get less
plate_w = 6.2;          // bark plate width (mm)
plate_len = 12.4;       // bark plate length (mm)

/* [6 - View] */
part = "assembly";      // [assembly, tree, roots, exploded, none]
quality = 1;            // [0:Draft, 1:Normal, 2:Fine]
// No bark and coarse sampling, for finding the shape: the same paths, radii and joins, only the
// surface is dropped (seconds instead of minutes)
sketch = false;
face_az = -135;         // turn about z for the views; -135 shows the front in the isometric view

/* [Hidden] */
$fn = quality == 0 ? 32 : 64;
spp = sketch ? 2 : quality == 0 ? 4 : quality == 1 ? 7 : 10;          // surface samples per bark plate
step = sketch ? 2.5 : quality == 0 ? 1.8 : quality == 1 ? 1.0 : 0.7;   // ring spacing along roots (mm)
skin_S = sketch ? 144 : quality == 0 ? 216 : 432;                      // samples round a burl ring
tex = sketch ? 0 : 1;                                                  // bark on (1) or off (0)
big = 500;
hole_r = screw_d/2+0.2;
bore_r = head_d/2+0.25;
screw_z = foot_z+screw_up;
a0 = trunk_climb;
E0 = [0, 0, trunk_z];
A0 = [0, cos(a0), sin(a0)];               // the trunk's direction leaving the wall
B1 = [1, 0, 0];                           // a frame round the trunk axis, for the bark
B2 = cross(A0, B1);
dzh = tan(a0);                            // the trunk's centre rises this much per mm out
trunk_plates = round(2*PI*trunk_r/plate_w);
total_h = layout_top;

assert(layout_check == [trunk_z, trunk_climb, burl_h, trunk_r],
       "Wall_Climber_Tree_layout.scad was made for another trunk: re-run Wall_Climber_Tree_layout.py");
assert(1.35*root_r0 < split_y, "Roots taller than split_y would be cut by the split");

// ---------------------------------------------------------------- library
function lerp(a,b,t) = a+(b-a)*t;
function unit(v) = v/max(norm(v),1e-6);
function frac(x) = x-floor(x);
function wrap(a) = a-360*round(a/360);        // angle difference into -180..180
function smooth(e0,e1,x) = let(t=max(0,min(1,(x-e0)/(e1-e0)))) t*t*(3-2*t);
function sum(v,i=0) = i>=len(v) ? 0 : v[i]+sum(v,i+1);
function sum_points(P,i=0) = i>=len(P) ? [0,0,0] : P[i]+sum_points(P,i+1);
function smax(a,b,k) = let(h=max(0,min(1,0.5+0.5*(a-b)/k))) lerp(b,a,h)+k*h*(1-h);
function smax_all(v,k,i=0) = i>=len(v)-1 ? v[len(v)-1] : smax(v[i],smax_all(v,k,i+1),k);
// deterministic pseudo-random in [0, 1): reproducible, and keeps parts off exact angles
function rnd(a,b=0,c=0) = let(x=sin(a*127.1+b*311.7+c*74.7)*43758.5453) x-floor(x);
function tangents(P) = [for(i=[0:len(P)-1])
    unit(i==0 ? P[1]-P[0] : i==len(P)-1 ? P[i]-P[i-1] : P[i+1]-P[i-1])];
function normal0(t) = unit(cross(t,abs(t[2]) < 0.9 ? [0,0,1] : [1,0,0]));
function transport(T,i,n) = i>=len(T) ? [] :
    let(v=unit(n-(n*T[i])*T[i])) concat([v],transport(T,i+1,v));
function arclen(P,i=0,acc=[0]) = i>=len(P)-1 ? acc :
    arclen(P,i+1,concat(acc,[acc[i]+norm(P[i+1]-P[i])]));
function climb(v) = atan2(v[2],norm([v[0],v[1]]));     // degrees above horizontal
function min_climb(P) = min([for(i=[1:len(P)-1]) climb(P[i]-P[i-1])]);
function curve(f,len_mm) = [for(k=[0:max(8,ceil(len_mm/step))]) f(k/max(8,ceil(len_mm/step)))];

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

// ---------------------------------------------------------------- bark (from Wild Chaotic Tree)
function n2(x,y) = (sin(263*x+131*y+11)+sin(-97*x+211*y+47)+sin(59*x-173*y+83))/3;
// Bark height in 0..1 (1 = top of a plate, 0 = bottom of a fissure) at plate coordinates U (around;
// a fissure on every whole number) and V (along). The fissures meander and drift over several
// plates, each column breaks into plates of its own length, and some plates split lengthwise.
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

// The bark of the trunk, fixed in space round the trunk axis (E0 along A0): fissures run along the
// trunk, round the burl by angle and out along the roots (V falls with the distance beyond the
// trunk). The burl skin, the trunk and the roots' bases all wear it, so their fissures line up.
// Out on the burl's bulge (well beyond the trunk) V changes fast and the cross cracks alias into
// dashes, so they fade there and the fissures carry the texture. They fade only from 6 mm out:
// where the burl hands over to the trunk (within a few mm of it) both must wear the same bark, or
// the trunk's cracks notch the burl's smoother surface along the crossing (scallops).
function wbark(p) = let(d=p-E0, s=d*A0, q=d-s*A0, r=norm(q), a=atan2(q*B2,q*B1))
    bark(trunk_plates*a/360,(s-max(0,r-trunk_r))/plate_len,1-0.8*smooth(6,14,r-trunk_r));
// The direction straight away from the trunk axis: the trunk's own surface normal.
function off_axis(p) = let(d=p-E0, q=d-(d*A0)*A0) unit(q);

function knot_h(d,kr) = let(q=d/kr)
    kr/4*(0.9*exp(-1.3*q*q)-0.8*exp(-5*q*q)+0.2*cos(360*d/1.1)*exp(-q*q));
function knot_calm(d,kr) = smooth(0.7*kr,1.5*kr,d);

// A tube along path P (radii R) wearing bark, R the outer bark. knots: [[t, direction, size]].
// wmix: a function of the smooth surface point, 0 where the tube wears the trunk's bark (wbark, at
// the trunk's depth) and 1 where it wears its own; it blends between them.
// kids: the forks that leave this tube, [[path, radii], ...]. Where a fork crosses one of this
// tube's rings, the ring takes a copy of the fork's cross-section there (a circle, sunk fork_in
// into the fork) through a smooth maximum (fork_k), so the crotch fills with a fillet instead of
// the V-groove two crossing tubes leave (after the Wild Chaotic Tree's limb circles, guide �16.1).
// The copy sinks away as the fork's centre crosses this tube's surface (gone half a fork radius
// past it; fading later left flat fins on the parent), and the fork's own surface takes over.
fork_in = 0.3;
fork_k = 3.5;
function kid_circle(Pi,Ti,Ni,Bi,Ri,kid) = let(C=kid[0], Rc=kid[1], n=min(len(C)-1,90),
        dd=[for(j=[0:n]) abs((C[j]-Pi)*Ti)], j0=search(min(dd),dd)[0])
    dd[j0]>2*step ? undef : let(o=C[j0]-Pi, on=o*Ni, ob=o*Bi, dist=norm([on,ob]),
        rc=Rc[j0]-fork_in-Rc[j0]*smooth(Ri-0.5*Rc[j0],Ri+0.5*Rc[j0],dist))
    rc<=0.2 ? undef : [dist,atan2(ob,on),rc];
function circ_far(a,c) = let(d=wrap(a-c[1]), h=c[2]*c[2]-pow(c[0]*sin(d),2))
    h<=0 ? 0 : c[0]*cos(d)+sqrt(h);
module bark_tube(P,R,depth,seed=0,knots=[],wmix=undef,kids=[]) {
    T=tangents(P); N=transport(T,0,normal0(T[0])); L=arclen(P);
    Rmax=max(R); n=max(5,round(2*PI*Rmax/plate_w)); S=n*spp;
    K=[for(k=knots) let(i=round(k[0]*(len(P)-1)), B=cross(T[i],N[i]))
        [L[i],atan2(k[1]*B,k[1]*N[i]),k[2]]];
    loft([for(i=[0:len(P)-1]) let(B=cross(T[i],N[i]),
            CC=[for(kid=kids) let(c=kid_circle(P[i],T[i],N[i],B,R[i],kid)) if(!is_undef(c)) c])
        [for(j=[0:S-1]) let(a=360*j/S,
            ds=[for(k=K) norm([wrap(a-k[1])*PI/180*R[i],L[i]-k[0]])],
            calm=len(K)==0 ? 1 : min([for(m=[0:len(K)-1]) knot_calm(ds[m],K[m][2])]),
            bump=len(K)==0 ? 0 : sum([for(m=[0:len(K)-1]) knot_h(ds[m],K[m][2])]),
            u=cos(a)*N[i]+sin(a)*B,
            Ra=len(CC)==0 ? R[i] : smax_all(concat([R[i]],[for(c=CC) circ_far(a,c)]),fork_k),
            q0=P[i]+Ra*u, m=is_undef(wmix) ? 1 : wmix(q0),
            own=bark(n*j/S+seed,L[i]/plate_len+0.37*seed),
            f=tex*(lerp(bark_depth,depth*R[i]/Rmax,m)*calm*(1-(m>=1 ? own : lerp(wbark(q0),own,m)))-bump))
            q0-f*u]]);
}

// ---------------------------------------------------------------- the burl's shape
function ell_hit(th,e,r=trunk_r) = let(a=r, b=r/cos(a0), ux=cos(th), uz=sin(th),
                             A=ux*ux/(a*a)+uz*uz/(b*b), B=-2*uz*e/(b*b), C=e*e/(b*b)-1)
    (-B+sqrt(B*B-4*A*C))/(2*A);
// The rings stay centred on E0, where every root starts, until past the roots' tops (hold_h);
// only then do they follow the trunk out. Distance from the ring centre to the trunk's section in a
// wall plane is an exact ray-ellipse hit (the section is an ellipse e above the ring centre).
hold_h = split_y;
// Past hold_h the ring centres glide onto the trunk axis over 10 mm (a fixed offset left them
// outside the trunk's section once the trunk thins where the limbs part).
function ring_e(h) = h<=hold_h ? h*dzh : hold_h*dzh*(1-smooth(hold_h,hold_h+10,h));
function ring_dz(h) = max(h,0)*dzh-ring_e(max(h,0));
function ring_c(h) = E0+[0,h,ring_dz(h)];
function lobe_ang(th) = exp(-pow(wrap(th+90)/lobe_w,2));
function lobe_h(h) = (0.45+0.55*smooth(0,12,h))*(1-smooth(18,burl_h,h));
function flare_at(h) = h<=0 ? flare : h>=flare_h ? 0 : flare*pow(1-h/flare_h,2.2);
// The burl lies 0.05 mm outside the trunk over its whole length and ends there, so the two
// surfaces run parallel and never cross: a crossing is a crease whatever its angle. Tried first:
// 0.4 mm proud, then sunk under the trunk over its last 14 mm (iteration 4: a 0.4 mm step round
// the base of the leader); 0.6 mm inside wherever it did not flare (a crease where the keel
// dipped under the trunk). The burl's end leaves a 0.05 mm rim, half a layer.
burl_in = -0.05;
// The trunk's real radius along its straight part (from the layout): it thins where the limbs
// part, inside the burl. A burl that kept the full trunk_r ended 1.7 mm proud of the thinned trunk:
// the step round the base of the leader. Each ring cuts the trunk obliquely, so the radius is read
// at the point's own axial position, found in two passes.
trunk_R_tab = let(L=arclen(layout_P[0])) [for(i=[0:len(L)-1]) [L[i]-4,layout_R[0][i]]];
function trunk_rad(s) = lookup(s,trunk_R_tab);
function trunk_hit(th,h) = let(hh=max(h,0), e=hh*dzh-ring_dz(hh), c=ring_c(hh), u=[cos(th),0,sin(th)],
        r0=ell_hit(th,e,trunk_rad(hh/cos(a0))), r1=ell_hit(th,e,trunk_rad((c+r0*u-E0)*A0)))
    ell_hit(th,e,trunk_rad((c+r1*u-E0)*A0));
function core(th,h) = trunk_hit(th,h)+flare_at(h)
                      +lobe*lobe_ang(th)*lobe_h(h)-burl_in;

// ---------------------------------------------------------------- roots (after Wild Chaotic Tree)
// Each root starts inside the burl and lies on the wall (its centreline 0.35 r out, so the wall
// takes a third of it). Out to its foot contour, just past its buttress, it runs straight out
// under the buttress at full radius and the burl carries a copy of it (root_band): the smooth
// maximum turns that into a fillet between root, buttress and burl. Beyond the foot it tapers and
// snakes on over the wall with a one-sided sweep and a side-to-side meander, ramped in over 60 % of
// the free root so it bends wider than it is thick.
// Random draws for the roots, shifted by root_seed: another seed, another root system.
function rr(i,k) = rnd(i+31.7*root_seed,k,root_seed);
// Angles from random gaps (0.45..1.45 of an even share each), turned by a random start, so the roots
// bunch and part irregularly instead of fanning evenly.
root_gaps = [for(k=[0:root_count-1]) 0.45+rr(k,12)];
root_gap_sum = sum(root_gaps);
function root_angle(i) = 360*rr(0,13)+360*(i==0 ? 0 : sum([for(k=[0:i-1]) root_gaps[k]]))/root_gap_sum;
function root_rad0(i) = root_r0*(0.82+0.18*rr(i,9));
function butt_reach(i) = buttress*(0.75+0.35*rr(i,2));
function root_foot(i) = core(root_angle(i),0)+butt_reach(i)+4;
function root_s0(i) = 3;                                     // starts inside the burl
// roots that head down the wall run shorter, so the roots part stays compact
function root_end(i) = root_foot(i)+(root_reach-12)*(0.6+0.4*rr(i,3))*lerp(1,0.7,max(0,-sin(root_angle(i))));
function root_tG(i) = (root_foot(i)-root_s0(i))/(root_end(i)-root_s0(i));
function root_u(i,t) = max(0,(t-root_tG(i))/(1-root_tG(i)));       // 0 up to the foot, 1 at the tip
function root_radius(i,t) = root_r1+(root_rad0(i)-root_r1)*pow(1-root_u(i,t),1.25);
function root_rho(i,t) = lerp(root_s0(i),root_end(i),t);
function root_off(i,t) = let(u=root_u(i,t)) root_sweep*(2*rr(i,4)-1)*u*u
    + root_meander*(0.6+0.8*rr(i,14))*smooth(0,0.6,u)*sin(360*(root_rho(i,t)-root_foot(i))/(54+34*rr(i,5))+360*rr(i,6));
function on_wall(rho,a,r) = E0+[rho*cos(a),0.35*r,rho*sin(a)];
function root_point(i,t) = let(rho=root_rho(i,t))
    on_wall(rho,root_angle(i)+root_off(i,t)/rho*180/PI,root_radius(i,t));
// Side roots fork off partway, head out to one side and turn outward again; each starts inside
// its root at 62 % of its thickness.
function has_side(i) = rr(i,7)<side_roots;
function side_t(i) = lerp(root_tG(i),1,0.2+0.25*rr(i,8));
function side_radius(i,t) = lerp(0.62*root_radius(i,side_t(i)),0.9*root_r1,pow(t,0.8));
function side_root_point(i,t) = let(t0=side_t(i), p=root_point(i,t0), q=root_point(i,t0+0.02),
    dir=atan2(q[2]-p[2],q[0]-p[0]), side=rr(i,10)<0.5 ? -1 : 1, Ls=36+16*rr(i,11),
    P1=[p[0],p[2]]+0.5*Ls*[cos(dir+side*42),sin(dir+side*42)],
    P2=[p[0],p[2]]+Ls*[cos(dir+side*26),sin(dir+side*26)],
    xz=(1-t)*(1-t)*[p[0],p[2]]+2*t*(1-t)*P1+t*t*P2)
    [xz[0],0.35*side_radius(i,t),xz[1]];
// Every root and side root ends in a rounded tip (a sphere of its end radius).
module roots() for(i=[0:root_count-1]) let(L=root_end(i)-root_s0(i)) {
    bark_tube(curve(function(t) root_point(i,t),L),curve(function(t) root_radius(i,t),L),
        0.75*bark_depth,seed=3.1*i+1,
        wmix=function(p) smooth(core(root_angle(i),0)+2,root_foot(i)+10,norm([p[0]-E0[0],p[2]-E0[2]])));
    translate(root_point(i,1)) sphere(root_radius(i,1),$fn=16);
    if(has_side(i)) {
        bark_tube(curve(function(t) side_root_point(i,t),50),curve(function(t) side_radius(i,t),50),
            0.6*bark_depth,seed=4.3*i+2);
        translate(side_root_point(i,1)) sphere(side_radius(i,1),$fn=16);
    }
}

// ---------------------------------------------------------------- the burl skin
// Buttresses: a ridge along every root, growing out of the burl from buttress_h and flaring ever
// faster towards the wall, narrowing as it goes (26 -> 9 deg), and ending on its root's base.
function butt(th,h) = h>=buttress_h ? 0 : let(f=(buttress_h-max(h,0))/buttress_h, w=lerp(30,11,f))
    sum([for(i=[0:root_count-1]) butt_reach(i)*pow(f,1.8)*exp(-pow(wrap(th-root_angle(i))/w,2))]);
// The copy of a root's base in the skin: the root seen from the ring centre (E0: every root starts
// there, and roots end below hold_h), its far side along each ray, deeper inside the root than its
// bark and the ring step, sinking 4 mm more over the last 10 mm before the foot contour so the
// fillet fades out before the copy ends. Bisection, because the copy narrows as it sinks.
band_in = bark_depth+0.3+0.6;
function band_r(i,s) = root_rad0(i)-band_in-4*smooth(root_foot(i)-10,root_foot(i),s);
function band_ok(i,c,sn,h,f) = let(r=band_r(i,f*c), q=r*r-pow(h-0.35*root_rad0(i),2))
    q>0 && f*sn<=sqrt(q) && f*c<=root_foot(i);
function band_bis(i,c,sn,h,lo,hi,n) = n==0 ? lo : let(m=(lo+hi)/2)
    band_ok(i,c,sn,h,m) ? band_bis(i,c,sn,h,m,hi,n-1) : band_bis(i,c,sn,h,lo,m,n-1);
function root_band(i,th,h) = let(d=wrap(th-root_angle(i)), c=cos(d), sn=abs(sin(d)), f0=4)
    h>hold_h || c<=0.5 || !band_ok(i,c,sn,max(h,0),f0) ? 0 : band_bis(i,c,sn,max(h,0),f0,root_foot(i)/c,10);
function skin_smooth(th,h) = smax_all(concat([core(th,h)+butt(th,h)],
                                      [for(i=[0:root_count-1]) root_band(i,th,h)]),8);
// Rings every 0.4 mm over the roots' bases, 0.8 mm beyond.
skin_hs = sketch ? concat([-1],[for(h=[0:1:hold_h]) h],[for(h=[hold_h+2:2:burl_h]) h],[burl_h])
                 : concat([-1],[for(h=[0:0.4:hold_h]) h],[for(h=[hold_h+0.6:0.6:burl_h]) h],[burl_h]);
// The bark is cut in along the ring (in the wall plane) where the roots join, and along the
// trunk's own normal (away from its axis) from past the roots' tops, so that where the burl dips
// under the trunk the two surfaces carry the same bark cut the same way: no seam, no scallops.
module skin() loft([for(h=skin_hs) let(c=ring_c(h), w=smooth(hold_h,hold_h+8,h))
    [for(j=[skin_S-1:-1:0]) let(th=360*j/skin_S, u=[cos(th),0,sin(th)], r=skin_smooth(th,h),
                                p=c+r*u, n=unit(lerp(u,off_axis(p),w)))
        p-tex*bark_depth*(1-wbark(p))*n]]);

// ---------------------------------------------------------------- trunk and crown
// From Wall_Climber_Tree_layout.scad: member 0 is the trunk (straight along A0 through the burl,
// then on as the leader), 1-2 the limbs that part from it, 3-6 the forks. The trunk wears the
// trunk's bark until it bends up out of the burl, then its own.
function axial(p) = (p-E0)*A0;
function kids_of(m) = [for(k=[0:len(layout_P)-1]) if(layout_parent[k]==m) [layout_P[k],layout_R[k]]];
module trunk() bark_tube(layout_P[0],layout_R[0],bark_depth,0,
    [[0.62,[-0.5,0.3,0.8],4.5]],
    function(p) smooth(layout_straight-12,layout_straight+14,axial(p)),kids_of(0));
module branches() for(m=[1:len(layout_P)-1]) let(P=layout_P[m], R=layout_R[m], e=P[len(P)-1]) {
    // knots face up and out: a swollen rim facing down would be a ledge
    bark_tube(P,R,bark_depth*0.85,1.7*m+0.4,[[0.45+0.1*rnd(m,3),[0.4*sign(e[0]),0.3,0.85],3.4]],
              undef,kids_of(m));
    translate(e) sphere(R[len(R)-1],$fn=24);            // as wide as the tube's end: no flat ring
}
module crown() { trunk(); branches(); translate(layout_P[0][len(layout_P[0])-1])
    sphere(layout_R[0][len(layout_R[0])-1],$fn=24); }

// ---------------------------------------------------------------- slide, shelf and screw
// A dovetail tongue on the tree's back (wider at the wall), from its foot up: it adds to the foot
// the tree prints on. The groove in the roots is the tongue grown by `fit`, closed at the shelf
// and open upwards; above the split outline the roots' burl lies lower than the groove.
module dovetail(c,z0,z1) translate([0,0,z0]) linear_extrude(z1-z0) polygon([
    [-rail_w/2-c,split_y+1],[rail_w/2+c,split_y+1],
    [rail_w2/2+c,split_y-rail_h-c],[-rail_w2/2-c,split_y-rail_h-c]]);
module rail() dovetail(0,foot_z,foot_z+rail_len);
module groove() dovetail(fit,foot_z-fit,big/2);
// A teardrop (point up, 45 deg) along y, so the hole and the counterbore print in the standing
// tree. The keel under the trunk is wider than the counterbore all the way down (lobe_w), so the
// counterbore is a tunnel with walls to the foot (guide §23.2).
module teardrop_y(r,y0,y1) translate([0,y1,screw_z]) rotate([90,0,0]) linear_extrude(y1-y0)
    union() { circle(r); rotate(45) square(r); }
module screw_hole() teardrop_y(hole_r,-1,split_y+under_head+0.01);
module screw_cut() {
    screw_hole();
    teardrop_y(bore_r,split_y+under_head,big/4);
}
module front_of_split() translate([-big/2,split_y,-big/2]) cube(big);
module tree_zone() intersection() { front_of_split(); translate([-big/2,-big/2,foot_z]) cube(big); }

module tree_part() difference() {
    union() {
        intersection() { union() { skin(); crown(); } tree_zone(); }
        rail();
    }
    screw_cut();
}
module roots_part() difference() {
    union() {
        difference() { skin(); tree_zone(); }
        roots();
    }
    translate([-big/2,-big,-big/2]) cube(big);      // the wall
    groove();
    screw_hole();
}

// ---------------------------------------------------------------- checks and summary
function bottom(h) = ring_c(h)[2]-skin_smooth(-90,h);     // the burl's underside, under the trunk
foot_depth = max([for(h=[split_y:0.5:burl_h]) if(bottom(h)<=foot_z) h])-split_y;
root_lo = min([for(i=[0:root_count-1]) for(t=[0:0.05:1]) root_point(i,t)[2]-root_radius(i,t)]);
root_w = [min([for(i=[0:root_count-1]) for(t=[0:0.05:1]) root_point(i,t)[0]]),
          max([for(i=[0:root_count-1]) for(t=[0:0.05:1]) root_point(i,t)[0]])];
echo(str("Wall climber tree: first parting at ", round(layout_part_z), " mm, tips below ", round(layout_top),
         " mm; crown climbs at least ", round(min([for(P=layout_P) min_climb([for(p=P) if(p[2]>trunk_z+2) p])])),
         " deg; roots from x ", round(root_w[0]), " to ", round(root_w[1]), ", lowest edge z ", round(root_lo*10)/10));
echo(str("  foot ", foot_depth, " mm deep from the split; burl under the screw head ",
         round(bottom(split_y+under_head)*10)/10, " (must be <= ", screw_z-bore_r, ")"));

// Both print in Cocoa Brown; the exploded view shows the roots lighter to tell the parts apart.
module assembly(gap=0) {
    color("#6F5034") translate([0,gap,gap/2]) tree_part();
    color(gap>0 ? "#9D7A54" : "#6F5034") roots_part();
}
if (part == "assembly") rotate([0,0,face_az]) assembly();
if (part == "exploded") rotate([0,0,face_az]) assembly(40);
if (part == "tree") color("#6F5034") render() translate([0,0,-foot_z]) tree_part();   // prints standing
if (part == "roots") color("#6F5034") render() rotate([90,0,0]) roots_part();         // prints on its back
