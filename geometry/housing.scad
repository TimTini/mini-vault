// Continuous feature CSG. Dimensions recovered from the reference mesh in mm;
// see docs/HOUSING-FEATURES.md for datums, fits and independent verification.
module native_housing_outline(inset=0) {
    w=model_body_width-2*inset; h=model_body_height-2*inset; r=body_corner_radius-inset;
    translate([42-model_body_width/2,0]) hull() for(sx=[-1,1],sz=[-1,1])
        translate([sx*(w/2-r),sz*(h/2-r)]) circle(r=r);
}
module native_housing_outer() {
    along_y(-7.5,model_body_depth-1) native_housing_outline();
    for(end=[0,1],j=[0:7]) {
        a=j*90/8; b=(j+1)*90/8;
        hull() for(t=[a,b])
            let(y=end==0 ? -7.5-.5*sin(t) : model_body_depth-8.5+.5*sin(t),
                inset=.5-.5*cos(t))
                along_y(y-.005,.01) native_housing_outline(inset);
    }
}

// Corner centres move with the panel spans; the mounting lip keeps its 10.2 radius.
module housing_mouth_outline(radius=10.2,left=-80,right=30) {
    hull() for(x=[left,right],z=[-30,30])
        translate(body_point([x,z])) circle(r=radius);
}

module housing_mouth_opening() {
    along_y(-7.5,21.5+eps) housing_mouth_outline();
    // R0.5 inner edge round. Analytic quarter-circle loft, rather than measured slices.
    for(j=[0:7]) hull() for(a=[j*90/8,(j+1)*90/8])
        along_y(-7.5-.5*sin(a)-eps,2*eps)
            housing_mouth_outline(10.7-.5*cos(a));
    // Right door-swing relief: symmetric cubic fit, 0.9 mm maximum at Y=-0.5.
    // Its rounded XZ section retains the measured R10.2 corner.
    hull() for(j=[-16:16]) let(t=abs(j)/16)
        along_y(-.5+6.5*j/16-eps,2*eps)
            housing_mouth_outline(right=30+.9*(1-1.5*t*t+.5*t*t*t));
    // Left internal lead-in: a 45-degree conical/planar transition, Y=3..11.
    hull() for(y=[3,11]) along_y(y-eps,2*eps)
        housing_mouth_outline(radius=y-.8,left=-88);
    along_y(11,3+eps) housing_mouth_outline(left=-88);
}

module housing_lock_pockets() {
    // Two blind rectangular pockets, with R1 entry corners on the upper pocket.
    along_y(-5.2,5.4) {
        polygon([for(p=[[-98.2,-24.2],[-90.2,-24.2],[-90.2,-15.8],[-98.2,-15.8]]) body_point(p)]);
        polygon([for(p=[[-98.2,15.8],[-90.2,15.8],[-90.2,24.2],[-98.2,24.2]]) body_point(p)]);
    }
    // R1 concave blend around the upper pocket's mouth, including its front/rear edges.
    for(j=[0:15]) hull() for(a=[j*90/16,(j+1)*90/16])
        along_x(-91.2-(model_body_width-142)+sin(a)-eps,2*eps)
            translate([-5.2,15.8]) offset(delta=1-cos(a)) square([5.4,8.4]);
}

module housing_lock_stop() {
    // Trapezoidal central stop; the rear face retreats at 45 degrees to Y=-1.
    intersection() {
        along_y(-5,4) polygon([for(p=[[-90.2,-9],[-88.2,-7],[-88.2,7],[-90.2,9]]) body_point(p)]);
        translate([-(model_body_width-142),0,-10]) linear_extrude(20)
            polygon([[-91,-5],[-88.2,-5],[-88.2,-3],[-90.2,-1],[-91,-1]]);
    }
}

module housing_hinge_guides() {
    for(s=[-1,1]) scale([1,1,s]) translate([0,0,(model_body_height-84)/2])
        difference() {
            along_x(3.5,12) polygon([[-5,36.2],[4,36.2],[8,40.2],[8,41],[-5,41]]);
            translate([5.5,-3,38.1]) cube([10+eps,5,4]);
        }
}

module housing_capsule_cutter(span) {
    depth=housing_texture_depth/size_scale;
    width=housing_texture_width/size_scale;
    pitch=housing_texture_pitch/size_scale;
    front=max(14+.01,25/size_scale-8);
    rear=model_body_depth-8-8/size_scale;
    count=floor((span-48/size_scale-width)/pitch)+1;
    for(i=[0:count-1]) translate([(i-(count-1)/2)*pitch,0,-depth])
        linear_extrude(depth+.01) hull() for(y=[front+8/size_scale+width/2,rear-8/size_scale-width/2])
            translate([0,y]) circle(d=width);
}

module housing_capsule_grooves() {
    // Subtract from four sidewalls; the functional mouth and rear stay plain.
    for(s=[-1,1]) {
        translate([42-model_body_width/2,0,s*model_body_height/2]) scale([1,1,s])
            housing_capsule_cutter(model_body_width);
        multmatrix([[0,0,s,s==1 ? 42 : 42-model_body_width],
                    [0,1,0,0],[1,0,0,0],[0,0,0,1]])
            housing_capsule_cutter(model_body_height);
    }
}

module native_housing() {
    union() {
      difference() {
        intersection() {
            native_housing_outer();
            translate([-model_body_width-100,-8,-model_body_height])
                cube([model_body_width+200,model_body_depth,2*model_body_height]);
        }
        housing_mouth_opening();
        housing_lock_pockets();
        along_y(14-eps,model_body_depth-8-bottom_thickness-14+eps)
            native_housing_outline(wall_thickness);
        if(housing_texture==1) housing_capsule_grooves();
      }
      housing_lock_stop();
      housing_hinge_guides();
    }
    if(hinge_gusset_size>0) for(s=[-1,1]) scale([1,1,s])
        along_x(4,10) polygon([[4.2,model_body_height/2-1.6],
            [4.2,model_body_height/2-1.6-hinge_gusset_size],[14,model_body_height/2-1.6]]);
}
