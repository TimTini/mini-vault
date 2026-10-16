door_marker_loop = [1,0,[[0.0,24.0],[-0.098,24.01],[-0.191,24.038],[-0.278,24.084],[-0.354,24.146],[-0.416,24.222],[-0.462,24.309],[-0.49,24.402],[-0.5,24.5],[-0.5,27.5],[-0.495,27.573],[-0.471,27.668],[-0.441,27.736],[-0.402,27.798],[-0.336,27.87],[-0.257,27.929],[-0.168,27.971],[-0.073,27.995],[0.0,28.0],[0.098,27.99],[0.191,27.962],[0.278,27.916],[0.354,27.854],[0.416,27.778],[0.462,27.691],[0.49,27.598],[0.5,27.5],[0.5,24.5],[0.495,24.427],[0.471,24.332],[0.441,24.264],[0.402,24.202],[0.336,24.13],[0.257,24.071],[0.168,24.029],[0.073,24.005]]];
// Continuous panel. Rear functional reliefs preserve measured local data.
module native_door() {
    difference() {
        if(size_scale==1) along_y(-5-door_plate_thickness,door_plate_thickness) door_panel_outline();
        else {
            // The .4 mm internal leading chamfer clears the frame during opening.
            front=-5-door_plate_thickness;
            hull() {
                along_y(front,.001) door_panel_outline(.4);
                along_y(front+.4,.001) door_panel_outline();
            }
            along_y(front+.4,door_plate_thickness-.4) door_panel_outline();
        }
        along_y(-5-door_plate_thickness-eps,door_plate_thickness+2*eps) {
            circle(r=shaft_stem_diameter/2+fit_gap(.1));
            translate([-50-(model_body_width-142),0]) hull() for(x=[-8,8])
                translate([x,0]) circle(r=3+fit_gap(.2));
        }
        along_y(-5-door_plate_thickness-eps,.2*door_plate_thickness/2+eps)
            // Dial marker stays with the lock; body height only stretches the panel.
            polygon(door_marker_loop[2]);
    }
    measured_part(0,[for(layer=profile_0) if(layer[0]>=-5) layer]);
}
