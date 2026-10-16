// Continuous outer shell and rear cavity; measured front reliefs retained locally.
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
module native_housing() {
    difference() {
        intersection() {
            native_housing_outer();
            translate([-model_body_width-100,-8,-model_body_height])
                cube([model_body_width+200,model_body_depth,2*model_body_height]);
        }
        // Front lock/hinge relief data retains its measured local tolerances.
        for(layer=profile_11) if(layer[0]<14)
            along_y(layer[0],min(layer[1],14)-layer[0])
                for(loop=layer[2]) if(loop[0]%2==1)
                    loop_sketch(11,loop,(layer[0]+min(layer[1],14))/2);
        along_y(14-eps,model_body_depth-8-bottom_thickness-14+eps)
            native_housing_outline(wall_thickness);
    }
    if(hinge_gusset_size>0) for(s=[-1,1]) scale([1,1,s])
        along_x(4,10) polygon([[4.2,model_body_height/2-1.6],
            [4.2,model_body_height/2-1.6-hinge_gusset_size],[14,model_body_height/2-1.6]]);
}
