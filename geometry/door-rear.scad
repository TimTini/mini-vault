// Rear door features recovered from the reference; dimensions before size_scale.
// Curves are analytic feature profiles, not measured section stacks.
function door_circle_point(c,r,a) = let(t=(a%360+360)%360) c+r*[cos(t),sin(t)];
function door_arc(c,r,a,b) = let(step=360/curve_segments,
    first=floor(min(a,b)/step)+1,last=ceil(max(a,b)/step)-1,
    indices=first<=last ? (b>a ? [first:last] : [last:-1:first]) : [])
    concat([door_circle_point(c,r,a)],[for(i=indices) door_circle_point(c,r,i*step)]);
function door_circle(r,c=[0,0]) = door_arc(c,r,0,360);
function door_capsule(left,right,r) = concat(door_arc([right,0],r,90,-90),[[right,-r]],
    door_arc([left,0],r,270,90),[[left,r]]);
function door_rear_points(points,y) =
    let(wide=model_body_width==142 ? points : split_profile_edges(points,0,[-74,-64]),
        tall=model_body_height==84 ? wide : split_profile_edges(wide,1,[-29,-26,26,29]),
        vertices=link_web_thickness==1.6 ? tall : split_profile_edges(tall,0,[-39.5,-20,-18]))
    [for(p=vertices) transformed_point(0,p,y)];
module door_rear_sketch(points,y=-3) { polygon(door_rear_points(points,y)); }

module door_rotor_carrier() {
    difference() {
        along_y(-5,3) circle(r=8);
        along_y(-5-eps,1+eps) polygon(door_circle(shaft_stem_diameter/2+fit_gap(.1)));
        // Bayonet entry: circular bore with opposed quarter-sector windows.
        ri=2.6; ro=4.6; ai=asin(1/ri); ao=asin(1/ro);
        entry=concat(door_arc([0,0],ri,-90,-ai),[[sqrt(ri*ri-1),-1]],
            door_arc([0,0],ro,-ao,0),[[ro,0]],door_arc([0,0],ri,0,180-ai),
            [[-sqrt(ri*ri-1),1]],door_arc([0,0],ro,180-ao,180),[[-ro,0]],
            door_arc([0,0],ri,180,270));
        along_y(-4,2+eps) door_rear_sketch(entry);
    }
    // The original contract radially offsets all vertices within R5 when D changes.
    // It does not uniformly scale these sectors or their straight slot edges.
    outer=4.6; inner=2.6; a=asin(1/outer); b=asin(1/inner);
    sector=concat(door_arc([0,0],outer,a,180-a),[[-sqrt(outer*outer-1),1]],
        door_arc([0,0],inner,180-b,b),[[sqrt(inner*inner-1),1]]);
    for(s=[-1,1]) along_y(-2,axial_y(0,13)+2)
        door_rear_sketch([for(p=sector) [p[0],s*p[1]]]);
}

function door_fork_outline() = let(a=asin(2/5.2),b=asin(1/5.2)) concat([[-66,5.2]],
    door_arc([-34,0],5.2,90,a),[[-29.2,2],[-18,2],[-18,1]],
    door_arc([-34,0],5.2,b,-b),[[-34+sqrt(5.2*5.2-1),-1],[-18,-1],[-18,-2]],
    door_arc([-34,0],5.2,-a,-90),[[-34,-5.2]],door_arc([-66,0],5.2,270,90));
function door_upper_rail_outer(left=-46) = let(a=asin(2/5.2)) concat([[left,5.2]],
    door_arc([-34,0],5.2,90,a),[[-29.2,2],[-18,2],[-18,1],[left,1]]);
function door_upper_tail() = let(top=2.001,a=asin(top/5.2)) concat(
    door_arc([-34,0],5.2,90,a),[[-34+sqrt(5.2*5.2-top*top),top],[-18,top],[-18,1],[-34,1]]);

module door_latch_fork() {
    along_y(-5,1) difference() {
        door_rear_sketch(door_fork_outline());
        // The grip opening follows the left edge as a rigid profile, as before.
        translate([-(model_body_width-142),0]) offset(delta=-fit_add(.2))
            polygon(door_capsule(-66,-34,4.2));
    }
}

function door_rail_cap_profile() = concat([[0,0],[5,0],[5,2]],
    door_arc([1,3],1,-90,-180),[[0,3]]);
module door_rail_tail_cap() {
    // R1 convex top edge: Y=0..1, Z=3..2. Beyond Y1 the top stays at Z2.
    shift=(link_web_thickness-1.6)/2;
    module compensated_section(a) {
        y=1-cos(a); z=3-sin(a);
        inner=-34+sqrt(4.2*4.2-z*z)*(1-fit_add(.2)/4.2);
        inner_z=z*(1-fit_add(.2)/4.2);
        outer=-34+sqrt(5.2*5.2-z*z);
        slope=(z-inner_z)/(outer-inner);
        along_y(y-.005,.01)
            polygon([[-48,0],[-16,0],[-16,z+slope*(-16-outer)],[-48,z+slope*(-48-outer)]]);
    }
    module cap() {
        if(fit_add(.2)>0) {
            // Apply radial compensation after the cap trim, as in the reference.
            // The inner top corner moves inward/down; the outer corner stays fixed.
            for(j=[0:31]) hull() { compensated_section(j*90/32); compensated_section((j+1)*90/32); }
            z=2; inner=-34+sqrt(4.2*4.2-z*z)*(1-fit_add(.2)/4.2);
            outer=-34+sqrt(5.2*5.2-z*z); slope=(z*fit_add(.2)/4.2)/(outer-inner);
            along_y(1,4) polygon([[-48,0],[-16,0],[-16,z+slope*(-16-outer)],[-48,z+slope*(-48-outer)]]);
        }
        else along_x(-48,32) polygon(door_rail_cap_profile());
    }
    if(shift==0) cap();
    else {
        intersection() {
            translate([0,0,shift]) cap();
            translate([-48,-.01,0]) cube([28,5.02,8]);
        }
        intersection() {
            multmatrix([[1,0,0,0],[0,1,0,0],[-shift/2,0,1,-9*shift],[0,0,0,1]]) cap();
            translate([-20,-.01,0]) cube([2,5.02,8]);
        }
        intersection() { cap(); translate([-18,-.01,0]) cube([2,5.02,8]); }
    }
}
module door_rail_end_hole() {
    // R1.9 concave round on the R4.2 internal arc; centre (R,Y)=(6.1,3.1).
    cutoff=acos((6.1-4.225)/1.9);
    angles=fit_add(.2)==0 ? [for(j=[0:16]) j*90/16] :
        concat([for(j=[0:16]) if(j*90/16<cutoff) j*90/16],[cutoff,cutoff],
               [for(j=[0:16]) if(j*90/16>cutoff) j*90/16]);
    before=len([for(a=angles) if(a<cutoff) 1]);
    // One cutter owns the complete inner surface; no tangent overlap of two bores.
    // One-micron overlap removes exact tangent cutter seams; below the .01 mm fit gate.
    join=.001;
    profile=concat([[0,-4],[4.2-fit_add(.2)+join,-4]], [for(i=[0:len(angles)-1]) let(a=angles[i],r=4.2+join+1.9*(1-cos(a)))
        [r-(a<cutoff || (a==cutoff && i==before) ? fit_add(.2) : 0),3.1+1.9*sin(a)]],[[0,5]]);
    translate([-34,0,(link_web_thickness-1.6)/2])
        multmatrix([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
            rotate_extrude(convexity=10) polygon(profile);
}
module door_rail_front_left_bar() {
    // Apply the thickness map after the R2 end trim: these operations do not commute.
    along_y(-4,2.005) door_rear_sketch([[-46,4.2],[-39.5,4.2],[-39.5,5.2],[-46,5.2]]);
    intersection() {
        for(j=[0:15]) hull() for(a=[j*90/16,(j+1)*90/16])
            let(y=-2+2*sin(a),left=-44-2*cos(a))
                along_y(y-.005,.01) door_rear_sketch(
                    [[left,4.2],[-39.5,4.2],[-39.5,5.2],[left,5.2]],y);
        translate([-48,-2,0]) cube([10,2,8]);
    }
}
module door_latch_rails() {
    for(s=[-1,1]) scale([1,1,s]) {
      difference() {
        union() {
            difference() {
                along_y(-4,4) door_rear_sketch(door_upper_rail_outer(link_web_thickness==1.6 ? -46 : -39.5));
                // R2 left end: straight up to Y=-2, retreating to X=-44 at Y=0.
                translate([-44,-2,0]) linear_extrude(8) difference() {
                    translate([-2,0]) square([2,2]);
                    circle(r=2);
                }
            }
            intersection() {
                along_y(0,5) door_rear_sketch(door_upper_tail());
                door_rail_tail_cap();
                // R2 outer end: X=-18 until Y3, then rounds to X=-20 at Y5.
                union() {
                    translate([-50,0,0]) cube([32,3,8]);
                    translate([-50,3,0]) cube([30,2,8]);
                    translate([-20,3,0]) cylinder(h=8,r=2);
                }
            }
        }
        door_rail_end_hole();
        along_y(-4,4) door_rear_sketch([[-48,0],[-34,0],[-34,4.2],[-46,4.2],[-48,4.2]]);
      }
      if(link_web_thickness!=1.6) door_rail_front_left_bar();
    }
}

module door_hinge_receivers() {
    for(s=[-1,1]) {
        // Compact C-section around the socket tongue, then the solid back cheek.
        front=[[1.5,30],[15.5,30],[15.5,31.95],[5.5,31.95],
               [5.5,34.05],[15.5,34.05],[15.5,36],[1.5,36]];
        back=[[1.5,30],[15.5,30],[15.5,36],[1.5,36]];
        difference() {
            union() {
                along_y(-5,7) door_rear_sketch([for(p=front) [p[0],s*p[1]]]);
                along_y(2,2) door_rear_sketch([for(p=back) [p[0],s*p[1]]]);
            }
            // R2 on both axial ends of the left edge; Z spans follow housing height.
            translate([0,0,-model_body_height]) linear_extrude(2*model_body_height) union() {
                intersection() {
                    translate([1.5,-3]) circle(r=2);
                    translate([-2,-5]) square([8,2]);
                }
                translate([-2,-3]) square([5.5,5]);
                translate([-2,2]) difference() {
                    square([7.5,2]);
                    translate([7.5,0]) circle(r=2);
                }
            }
        }
    }
}

module door_cover_supports() {
    for(s=[-1,1]) {
        for(bounds=[[-90,-74,24.2,26]]) difference() {
            along_y(-5,5) door_rear_sketch([for(p=[[bounds[0],bounds[2]],[bounds[1],bounds[2]],
                [bounds[1],bounds[3]],[bounds[0],bounds[3]]]) [p[0],s*p[1]]]);
            translate([-(model_body_width-142),0,-30]) linear_extrude(60)
                polygon([[-100,-2],[-90,-2],[-88,0],[-100,0]]);
        }
        along_y(0,2) door_rear_sketch([for(p=[[-85,24.2],[-79,24.2],[-79,26],[-85,26]]) [p[0],s*p[1]]]);
        // Base, 45-degree lead-in and retaining tab share one continuous prism.
        scale([1,1,s]) translate([-(model_body_width-142),0,14]) linear_extrude(1.8)
            polygon([[-90,-5],[-82,-5],[-82,0],[-84,0],[-84,2],[-86,2],[-88,0],[-90,-2]]);
        // Rotated 10x2 base and 4x2 retaining tab; measured 35-degree datum.
        along_y(-5,5) door_rear_sketch([for(p=[[-62.287,18.604],[-54.096,12.868],
            [-52.949,14.506],[-61.14,20.242]]) [p[0],s*p[1]]]);
        along_y(0,2) door_rear_sketch([for(p=[[-59.83,16.883],[-56.553,14.589],
            [-55.406,16.227],[-58.683,18.521]]) [p[0],s*p[1]]]);
    }
}
module native_door_rear() {
    door_rotor_carrier();
    door_latch_fork();
    door_latch_rails();
    door_hinge_receivers();
    door_cover_supports();
}
