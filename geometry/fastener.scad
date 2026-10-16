// Selector pin: two measured stem fits and a R0.2 round on the head rim.
// A single revolved head profile replaces 65 artificial Z intervals.
module native_fastener() {
    translate([55,10,0]) {
        translate([0,0,2]) cylinder(h=2+eps,r=1.518686);
        translate([0,0,4]) cylinder(h=2+eps,r=1.556194);
        rotate_extrude(convexity=4) polygon(concat([[0,6]],
            [for(a=[-90:11.25:0]) [3.4+0.2*cos(a),6.2+0.2*sin(a)]],
            [for(a=[0:11.25:90]) [3.4+0.2*cos(a),7.8+0.2*sin(a)]],[[0,8]]));
    }
}
