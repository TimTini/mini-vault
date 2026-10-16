// Bayonet collar: annular flange, two opposed tabs and one planar ramp per tab.
module collar_tab_section(radius, z_min, z_max) {
    intersection() {
        difference() { circle(r=radius); circle(r=2.5+fit_gap(.1)); }
        translate([0,z_min]) square([radius+1,z_max-z_min]);
    }
}
module native_collar() {
    along_y(0,3) difference() { circle(r=8); circle(r=4.8); }
    for(s=[-1,1]) scale([s,1,s]) {
        along_y(-3.8,1.8+eps) collar_tab_section(4.6,-.8,0);
        along_y(-2,2+eps) collar_tab_section(4.6,-.8,.8);
        difference() {
            // Extend into the flange so the tab and ring share positive volume.
            along_y(0,3) collar_tab_section(5,-.8,.8);
            // A 45 degree lead-in goes from Z=-.8 at Y=.2 to Z=0 at Y=1.
            along_x(-eps,5+eps)
                polygon([[.2,-2],[3.1,-2],[3.1,0],[1,0],[.2,-.8]]);
        }
    }
}
