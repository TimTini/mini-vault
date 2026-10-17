// MINI-VAULT reconstruction. Dimensions are mm; mechanical relationships INFERRED.
// Measured section sketches preserve complex features without importing the STL.
// Individual selectors/source_layout keep STL coordinates; assembly places loose pins.

/* [Display] */
part = "assembly"; // [assembly,exploded,source_layout,housing,door,hinge_socket_top,hinge_socket_bottom,hinge_leaf_top,hinge_leaf_bottom,fastener_1,fastener_2,fastener_3,disk_1,disk_2,disk_3,collar_1,collar_2,collar_3,latch,shaft,dial,retaining_ring,knob,link,latch_cover]
show_reference = false;
explode_distance = 12;
// Inferred selector-pin placement; 15 measured holes, 22.5 degrees apart.
// Hole 7 is at +X; the missing sixteenth position is the lock notch at -X.
pin_holes = [7,3,12];

/* [Size] */
// Final housing dimensions stay in mm; fit gaps retain their nominal mm value.
size_scale = 1; // .1

/* [Housing] */
body_width = 142;
body_depth = 100;
body_height = 84;
wall_thickness = 1.8;
// Step .1: an integer default is an integer spinbox, so preset 2.4 would be stored as 2.
bottom_thickness = 2; // .1
body_corner_radius = 12;
door_corner_radius = 10;

/* [Local reinforcement] */
// Load-bearing sections only. Step .1 so preset 2.8 is not rounded to 3.
door_plate_thickness = 2; // .1
door_rib_height = 0;
hinge_socket_root_thickness = 1.8;
hinge_gusset_size = 0;
link_web_thickness = 1.6;
// Step .1 so preset 0.8 is not rounded to 1.
latch_pocket_inset = 0; // .1

/* [Lock disks] */
disk_diameter = 35;
disk_thickness = 2;
disk_pitch = 5;
disk_hole_diameter = 3.2;
disk_hole_pitch_radius = 13.5;
disk_bore_diameter = 9.6;

/* [Shaft and hinges] */
shaft_stem_diameter = 5;
hinge_hole_diameter = 4.2;

/* [Resolution] */
curve_segments = 128;

/* [Hidden] */
model_body_width=body_width/size_scale;
model_body_depth=body_depth/size_scale;
model_body_height=body_height/size_scale;
// Internal coordinates are scaled once at the output; nominal gaps are divided here.
function fit_gap(mm) = mm/size_scale;
function fit_add(mm) = mm-fit_gap(mm);
assert(size_scale>=1 && size_scale<=1.5,"size_scale: 1..1.5");

$fn = curve_segments;
eps = 0.00001; // Boolean epsilon only, not mechanical clearance.
disk_center_x = -0.028609;
include <geometry/door-rear.scad>
include <geometry/door.scad>
include <profiles/hinge_socket_top.scad>
include <geometry/fastener.scad>
include <profiles/disk_1.scad>
include <profiles/hinge_leaf_top.scad>
include <geometry/latch.scad>
include <geometry/rotating.scad>
include <profiles/retaining_ring.scad>
include <geometry/housing.scad>
include <profiles/knob.scad>
include <geometry/link-cover.scad>
include <geometry/collar.scad>

names = ["door","hinge_socket_top","fastener_1","fastener_2","disk_1",
    "fastener_3","hinge_leaf_top","latch","shaft","dial","retaining_ring",
    "housing","knob","link","hinge_leaf_bottom","hinge_socket_bottom",
    "latch_cover","collar_1","collar_2","collar_3","disk_2","disk_3"];

assert(model_body_width >= 142 && model_body_width <= 220, "model_body_width: design domain 142..220 mm");
assert(model_body_height >= 84 && model_body_height <= 220, "model_body_height: design domain 84..220 mm");
// Minimum rear inner plane Y18.5 clears the baseline shaft end Y18 by 0.5 mm.
assert(model_body_depth >= 28.5 && model_body_depth <= 220, "model_body_depth: design domain 28.5..220 mm");
assert(door_plate_thickness>=2 && door_plate_thickness<=2.8,
    "door_plate_thickness: 2..2.8 mm");
assert(hinge_socket_root_thickness>=1.8 && hinge_socket_root_thickness<=2.6,
    "hinge_socket_root_thickness: 1.8..2.6 mm");
assert(link_web_thickness>=1.6 && link_web_thickness<=2.4, "link_web_thickness: 1.6..2.4 mm");
assert(latch_pocket_inset>=0 && latch_pocket_inset<=0.8, "latch_pocket_inset: 0..0.8 mm");
assert(door_rib_height>=0 && door_rib_height<=4 && (door_rib_height==0 || model_body_height>=160),
    "door ribs: height 0..4 mm; enabled only with model_body_height>=160");
assert(hinge_gusset_size>=0 && hinge_gusset_size<=4, "hinge_gusset_size: 0..4 mm");
assert(wall_thickness >= 1.8 && wall_thickness <= 3, "wall_thickness: design domain 1.8..3 mm");
assert(bottom_thickness >= 2 && bottom_thickness <= 4, "bottom_thickness: design domain 2..4 mm");
assert(body_corner_radius>=12 && body_corner_radius<=14 &&
    door_corner_radius>=10 && door_corner_radius<=12,"Corner-radius design domains: body 12..14, door 10..12 mm");
assert(disk_diameter >= 34 && disk_diameter <= 36, "disk_diameter: design domain 34..36 mm");
assert(disk_thickness >= 1.8 && disk_thickness <= 2.2, "disk_thickness: design domain 1.8..2.2 mm");
assert(disk_pitch >= 5 && disk_pitch <= 6 && disk_pitch > disk_thickness+3-eps,
    "disk_pitch must accommodate each disk and its 3 mm collar");
assert(disk_hole_diameter > 0 && disk_bore_diameter > 0 &&
    disk_hole_pitch_radius+disk_hole_diameter/2 < disk_diameter/2 &&
    disk_hole_pitch_radius-disk_hole_diameter/2 > disk_bore_diameter/2,
    "Disk holes must remain inside the rim and clear of the bore");
assert(disk_bore_diameter>=9.6 && disk_bore_diameter<=10,"Disk bore must accommodate the measured collar stem");
assert(shaft_stem_diameter >= 4.8 && shaft_stem_diameter <= 5.2, "shaft stem domain 4.8..5.2 mm");
assert(hinge_hole_diameter >= 4.1 && hinge_hole_diameter <= 4.3, "hinge hole domain 4.1..4.3 mm");
assert(curve_segments >= 64 && curve_segments <= 512, "curve_segments: 64..512");
assert(len(pin_holes)==3 && len([for(h=pin_holes) if(h>=0 && h<=14 && floor(h)==h) 1])==3,
    "pin_holes: three integer selector holes in 0..14");
assert(part=="assembly" || part=="exploded" || part=="source_layout" || len([for(n=names) if(n==part) 1])==1,
    str("Unknown part selector: ",part));

// Preserve corner radii, local lock dimensions and the right-side datum.
// Enlarge empty panel spans. Keep the central lock, gate tip and guides rigid.
function width_shift(x) = x<=-74 ? model_body_width-142 :
    x>=-64 ? 0 : (model_body_width-142)*(-64-x)/10;
// Latch grip sits at X -53..-39. Follow the left door edge up to X -39.
// The hook from X -34 stays with the link; the short span between them stretches.
function latch_width_shift(x) = x<=-39 ? model_body_width-142 :
    x>=-34 ? 0 : (model_body_width-142)*(-34-x)/5;
function latch_body_point(p) = [p[0]-latch_width_shift(p[0]), p[1]+height_shift(p[1])];
function height_shift(z) = abs(z)<=26 ? 0 :
    sign(z)*(model_body_height-84)/2*min(1,(abs(z)-26)/3);
function link_web_weight(x) = x<-39.5 || x>=-18 ? 0 : x<=-20 ? 1 : (-18-x)/2;
// Split edges at every deformation datum, so both sides of a ligament follow
// the same piecewise map even when the measured polygon has long straight edges.
function split_profile_edges(points,axis,datums) = [for(i=[0:len(points)-1])
    let(a=points[i],b=points[(i+1)%len(points)],d=b[axis]-a[axis])
    each concat([a],[for(x=d>=0 ? datums : [for(j=[len(datums)-1:-1:0]) datums[j]])
        if(abs(d)>eps && x>min(a[axis],b[axis]) && x<max(a[axis],b[axis])) a+(b-a)*(x-a[axis])/d])];
function door_mount_point(p,y) =
    let(receiver=y>=-5 && p[0]>=1 && p[0]<=15.6 && abs(p[1])>=29.99 && abs(p[1])<=36.01,
        q0=receiver && (hinge_socket_root_thickness>1.8 || size_scale>1) ?
            [min(p[0],size_scale>1 ? 15-fit_gap(.2) : 14.8),p[1]] : p,
        q=receiver && abs(p[1])>=33.8 && abs(p[1])<=34.2 ?
            q0-[0,sign(p[1])*fit_add(abs(p[1])-33.8)] : q0)
    // Move the lower receiver cheek with the thicker socket tongue, keeping
    // the upper cheek, barrel and neighboring housing/leaf unchanged.
    y>=-5 && p[0]>=1 && p[0]<=15.6 && abs(p[1])>=29.99 && abs(p[1])<=32.01 ?
        q-[0,sign(p[1])*(hinge_socket_root_thickness-1.8)] :
    y>=-5 && p[0]>=-46.1 && p[0]<=-17.9 && abs(p[1])>=0.9 && abs(p[1])<=5.3 ?
        let(v=p-[-34,0],r=norm(v),
            clearance_shift=abs(r-4.2)<.025 ? v/r*fit_add(.2) :
                abs(abs(p[1])-1)<.02 ? [0,sign(p[1])*fit_add(.2)] : [0,0])
        q+[0,sign(p[1])*(link_web_thickness-1.6)/2*link_web_weight(p[0])]-clearance_shift : q;
function latch_guide_point(p) = p[0]>=-39.5 && abs(p[1])>=0.99 &&
    (abs(p[1])<=1.01 || abs(p[1])>=3.99 || p[0]>=-34) ?
        p+[0,sign(p[1])*(link_web_thickness-1.6)/2] : p;
function structural(id) = id==0 || id==1 || id==6 || id==7 || id==11 || id==13 || id==16;
function body_point(p) = [p[0]-width_shift(p[0]),p[1]+height_shift(p[1])];
function depth_y(y) = y<=15 ? y : y>=90 ?
    92+(model_body_depth-100)-(92-y)*bottom_thickness/2 :
    15+(y-15)*(75+model_body_depth-100-(bottom_thickness-2))/75;
function axial_y(id,y) = id==11 ? depth_y(y) : id==4 ?
    -2+(y+2)*disk_thickness/2 : id==8 ? y<=-7 ? y : y<=13 ?
    -7+(y+7)*(20+2*(disk_pitch-5))/20 : y+2*(disk_pitch-5) :
    id==10 ? y+2*(disk_pitch-5) : id==0 && y>5 ?
    y+2*(disk_pitch-5)*(y-5)/8 : y;
function transformed_point(id,p,y) = id==4 ?
    [disk_center_x+(p[0]-disk_center_x)*disk_diameter/35,
     (p[1]-(p[0]<-9 && abs(p[1])<=3 ? sign(p[1])*fit_add(.2) : 0))*disk_diameter/35] :
    id==8 && y>=-7 ? p*shaft_stem_diameter/5 :
    id==10 && norm(p)<3 ? p*shaft_stem_diameter/5 :
    (id==1 || id==6) ? [p[0]-width_shift(p[0]),p[1]] :
    id==0 && y>=-5 && norm(p)>eps && norm(p)<5 ? p*(1+(shaft_stem_diameter-5)/(2*norm(p))) :
    id==13 ? p+[0,abs(p[1])<=0.801 ? sign(p[1])*(link_web_thickness-1.6)/2*link_web_weight(p[0]) : 0] :
    id==0 ? body_point(door_mount_point(p,y)) :
    id==7 ? latch_body_point(latch_guide_point(p)) :
    id==16 ? body_point(p) :
    structural(id) ? body_point(p) : p;
function corner_point(id,p,y,depth) =
    let(delta=id==0 ? door_corner_radius-10 : id==11 && (depth==0 || y>=14) ? body_corner_radius-12 : 0,
        left=id==0 ? -80 : -88,
        cx=p[0]<=left ? left : p[0]>=30 ? 30 : p[0],
        cz=p[1]<=-30 ? -30 : p[1]>=30 ? 30 : p[1],
        v=p-[cx,cz],r=norm(v),
        corner=(p[0]<=left || p[0]>=30) && abs(p[1])>=30 && r>0)
    corner && delta!=0 ? p+[cx==left ? delta : -delta,cz>0 ? -delta : delta]+v*delta/r : p;

// Axis permutation is explicit: sketch (X,Z), extrusion Y for most parts.
module along_y(y,h) {
    translate([0,y,0])
        multmatrix([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
            linear_extrude(height=h,convexity=20) children();
}

module loop_sketch(id,loop,y) {
    data=loop[2];
    if(loop[1]==2) {
        center=[data[0],data[1]];
        sizable=id==0 || id==11;
        cavity=id==11 && loop[0]%2==1 && y>=14;
        wall_delta=cavity ? wall_thickness-1.8 : 0;
        w=data[2]+(sizable ? model_body_width-142 : 0)-2*wall_delta;
        h=data[3]+(sizable ? model_body_height-84 : 0)-2*wall_delta;
        corner_delta=id==0 ? door_corner_radius-10 : id==11 && (loop[0]==0 || cavity) ? body_corner_radius-12 : 0;
        r=data[4]+corner_delta-wall_delta;
        translate([center[0]-(sizable ? (model_body_width-142)/2 : 0),center[1]])
            hull() for(sx=[-1,1],sy=[-1,1]) translate([sx*(w/2-r),sy*(h/2-r)]) circle(r=r);
    } else if(loop[1]==1) {
        center=[data[0],data[1]];
        radius=data[2];
        disk_hole=id==4 && loop[0]%2==1;
        bore=disk_hole && norm(center-[disk_center_x,0])<0.1;
        new_center=disk_hole ? bore ? center :
            [disk_center_x,0]+(center-[disk_center_x,0])*disk_hole_pitch_radius/13.5 :
            transformed_point(id,center,y);
        new_radius=disk_hole ? bore ? disk_bore_diameter/2-fit_add(.2) : disk_hole_diameter/2-fit_add((3.2-3.112388)/2) :
            id==4 ? radius*disk_diameter/35 :
            id==8 && y>=-7 ? radius*shaft_stem_diameter/5 :
            id==12 && loop[0]%2==1 ? radius*shaft_stem_diameter/5 :
            id==0 && y>=-5 && norm(center)<0.1 && radius<5 ? radius+(shaft_stem_diameter-5)/2-fit_add(.1) :
            id==1 && loop[0]%2==1 && abs(radius-2.6)<0.02 ? 2.5+fit_gap(.1) :
            id==1 && loop[0]%2==1 && abs(radius-2.1)<0.02 ? hinge_hole_diameter/2 : radius;
        translate(new_center) circle(r=new_radius);
    } else {
        xs=[for(p=data) p[0]];
        zs=[for(p=data) abs(p[1])];
        // Door opening the latch grip passes through. Move the whole opening with the left edge.
        latch_slot=id==0 && loop[0]%2==1 && min(xs)<-50 && max(xs)<-20 && max(zs)<6;
        if(latch_slot) offset(delta=-fit_add(.2))
            polygon([for(p=data) [p[0]-(model_body_width-142), p[1]]]);
        else {
        wide=model_body_width==142 || !structural(id) || id==13 ? data :
            id==7 ? split_profile_edges(data,0,[-39,-34]) :
            split_profile_edges(data,0,[-74,-64]);
        tall=structural(id) && id!=13 && id!=1 && id!=6 && model_body_height!=84 ?
            split_profile_edges(wide,1,[-29,-26,26,29]) : wide;
        vertices=(id==13 || id==0 || id==7) && link_web_thickness!=1.6 ?
            split_profile_edges(tall,0,[-39.5,-20,-18]) : tall;
        points=[for(p=vertices) let(q=id==12 && loop[0]%2==1 ? p*shaft_stem_diameter/5 : p)
            transformed_point(id,corner_point(id,q,y,loop[0]),y)];
        // Only the main cavity wall changes. Front lip/hinge clearance stays measured.
        main_cavity=id==11 && loop[0]%2==1 && y>=14;
        if(id==7 && loop[0]%2==1 && latch_pocket_inset>0)
            offset(delta=-latch_pocket_inset) polygon(points);
        else if(main_cavity) offset(delta=-(wall_thickness-1.8)) polygon(points);
        else polygon(points);
        }
    }
}

module measured_sketch(id,loops,y) {
    // Nested contours use even/odd depth, including islands inside holes.
    for(outer=loops) if(outer[0]%2==0)
        difference() {
            loop_sketch(id,outer,y);
            for(hole=loops) if(hole[0]==outer[0]+1) loop_sketch(id,hole,y);
        }
}

module measured_part(id,layers,axis=1) {
    union() for(layer=layers)
    for(span=id==11 && layer[0]<14 && layer[1]>14 ?
        [[layer[0],14],[14,layer[1]]] : [[layer[0],layer[1]]]) {
        a=span[0]; b=span[1]; y=(a+b)/2;
        // Thicken outward: the latch slides against the original Y=-5 back face.
        plate=id==0 && b<=-5;
        lo=plate ? -5+(a+5)*door_plate_thickness/2 : axis==1 ?
            axial_y(id,a)-((id==9 || (id==8 && a<=-7)) ? door_plate_thickness-2 : 0) :
            id==1 && a==32 ? a-(hinge_socket_root_thickness-1.8) : a;
        hi=plate ? -5+(b+5)*door_plate_thickness/2 : axis==1 ?
            axial_y(id,b)-((id==9 || (id==8 && b<=-7)) ? door_plate_thickness-2 : 0) : b;
        if(axis==1) along_y(lo,hi-lo) measured_sketch(id,layer[2],y);
        else translate([0,0,lo+((id==1 || id==6) ? height_shift(lo) : 0)-((id==6 && a>=36.2) ? fit_add(.2) : 0)])
            linear_extrude(height=hi-lo+((id==6 && a==32) ? -fit_add(.2) : 0)) {
                // Hinge sketches lie in XY; housing Z movement is applied to their placement.
                if(id==1 || id==6) measured_sketch(id,layer[2],0);
                else measured_sketch(id,layer[2],y);
            }
    }
}

module along_x(x,h) {
    multmatrix([[0,0,1,x],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
        linear_extrude(height=h) children();
}

module door_rib(a,b) {
    back=-5;
    module bar(radius) { hull() { translate(a) circle(r=radius); translate(b) circle(r=radius); } }
    // A wider, tapered foot joins the panel; the narrow upper web saves volume.
    hull() {
        along_y(back-eps,eps*2) bar(1.6);
        along_y(back+min(1,door_rib_height),eps*2) bar(1);
    }
    if(door_rib_height>1) along_y(back+1,door_rib_height-1) bar(1);
}

module housing() { render(convexity=20) native_housing(); }
module door_panel_outline(inset=0) {
    w=model_body_width-12; h=model_body_height-4; r=door_corner_radius;
    offset(delta=-inset+fit_add(.2)) translate([40-w/2,0])
        hull() for(sx=[-1,1],sz=[-1,1])
            translate([sx*(w/2-r),sz*(h/2-r)]) circle(r=r);
}
module door() {
    if(door_plate_thickness==2) native_door();
    else intersection() {
        native_door();
        // Inset the added skin at its root, then chamfer the entire outline.
        // Extending the old edge forward increases its hinge-corner contact.
        union() {
            translate([-model_body_width-100,-7,-model_body_height])
                cube([model_body_width+200,100,2*model_body_height]);
            hull() {
                along_y(-7,eps) door_panel_outline(door_plate_thickness-2);
                along_y(-5-door_plate_thickness,eps) door_panel_outline(2*(door_plate_thickness-2));
            }
        }
    }
    if(door_rib_height>0) {
        left=40-(model_body_width-12)+6;
        top=(model_body_height-4)/2-6;
        for(s=[-1,1]) {
            // Leave the hinge receiver clear at X=1..25 on the outer ribs.
            door_rib([left,s*top],[-2,s*top]);
            door_rib([left,s*(26+(model_body_height-84)/4)],[34,s*(26+(model_body_height-84)/4)]);
        }
        door_rib([34,-top],[34,top]);
    }
    if(hinge_gusset_size>0) for(s=[-1,1]) scale([1,1,s])
        let(z=30+height_shift(30)-(hinge_socket_root_thickness-1.8),back=-5)
            along_x(4,10) polygon([[back-.1,z-hinge_gusset_size],[back-.1,z+.1],[3.5,z+.1]]);
}
module hinge_socket() { measured_part(1,profile_1,2); }
module hinge_leaf() { measured_part(6,profile_6,2); }
module fastener() { native_fastener(); }
module disk() { measured_part(4,profile_4); }
module collar() { native_collar(); }
module latch() { native_latch(); }
module shaft() { native_shaft(); }
module dial() { translate([0,fit_add(.2),0]) native_dial(); }
module retaining_ring() { measured_part(10,profile_10); }
module knob() { measured_part(12,profile_12); }
module link() { native_link(); }
module latch_cover() { native_latch_cover(); }

module instance(i) {
    if(i==0) door();
    else if(i==11) housing();
    else if(i==1) hinge_socket();
    else if(i==15) mirror([0,0,1]) hinge_socket();
    else if(i==6) hinge_leaf();
    else if(i==14) mirror([0,0,1]) hinge_leaf();
    else if(i==2 || i==3 || i==5)
        translate([0,i==2 ? 0 : i==3 ? 9.4 : 18.3,0]) fastener();
    else if(i==4 || i==20 || i==21)
        translate([0,(i==4 ? 0 : i==20 ? 1 : 2)*disk_pitch,0]) disk();
    else if(i>=17 && i<=19) translate([0,(i-17)*disk_pitch,0]) collar();
    else if(i==7) latch();
    else if(i==8) shaft();
    else if(i==9) dial();
    else if(i==10) retaining_ring();
    else if(i==12) translate([0,2*(disk_pitch-5),0]) knob();
    else if(i==13) link();
    else if(i==16) latch_cover();
}

// Source fastener axis (55,10,Z), head underside Z6, tip Z2.
// Author assembly video 2BFG1QkyP0Q at 0:25/0:35: heads face the interior.
// +Z maps to +Y; head underside seats on the REAR disk face.
// Hole positions are measured; selected holes are an example configuration.
module assembled_instance(i) {
    if(i==2 || i==3 || i==5) {
        index=i==2 ? 0 : i==3 ? 1 : 2;
        angle=22.5*(pin_holes[index]-7);
        translate([disk_center_x+disk_hole_pitch_radius*cos(angle),
                   -2+disk_thickness+index*disk_pitch, disk_hole_pitch_radius*sin(angle)])
            rotate([-90,0,0]) translate([-55,-10,-6]) fastener();
    } else instance(i);
}

module assembly(exploded=false,source_layout=false) {
    // Keep every part; translucent housing exposes the assembled mechanism.
    for(i=[0:21]) color(i==11 ? [0.7,0.75,0.85,0.4] :
        i==0 ? [0.5,0.75,0.9] :
        !source_layout && !exploded ? [0.9,0.7,0.35] : [0.9,0.65+(i%3)*0.1,0.35])
        translate(exploded ? [0,(i==11 ? 8 : i==0 ? -4 : i/2)*explode_distance,0] : [0,0,0])
            if(source_layout) instance(i); else assembled_instance(i);
}

scale([size_scale,size_scale,size_scale]) {
if(part=="assembly") assembly();
else if(part=="exploded") assembly(true);
else if(part=="source_layout") assembly(source_layout=true);
else for(i=[0:21]) if(part==names[i]) instance(i);
}

if(show_reference) %import("reference/MINI-VAULT.stl",convexity=20);
