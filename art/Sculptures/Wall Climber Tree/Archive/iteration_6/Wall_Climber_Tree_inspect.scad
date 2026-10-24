// Close-up inspection of a region of Wall_Climber_Tree.scad: cuts the region out with a box and
// shows one component or all of them, turned for the view. Use it in sketch mode (no bark) to find
// steps and creases at the joints; this is how iteration 5's step at the leader's base was found.
//
//   openscad.com -o front.png -D sketch=true -D view_az=180 --camera=0,0,0,55,0,0,300 --viewall
//                --autocenter --projection=p --imgsize=800,800 Wall_Climber_Tree_inspect.scad
// view_az: 180 front, 90 right, -90 left. which: 0 all, 1 burl only, 2 crown only, 3 trunk only.
include <Wall_Climber_Tree.scad>
part = "none";
box = [-40, 4, 40, 80, 70, 85];   // x0, y0, z0, dx, dy, dz (assembled position; default: the first parting)
view_az = 180;
which = 0;
rotate([0,0,view_az]) color("#8a6a48") render() intersection() {
    if (which == 0) union() { skin(); crown(); }
    else if (which == 1) skin();
    else if (which == 2) crown();
    else trunk();
    translate([box[0],box[1],box[2]]) cube([box[3],box[4],box[5]]);
}
