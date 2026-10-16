"""Audit selected pin/neighbor pairs for both interpretations of reported8/4/12.

Fixed angular contact bands approximate the small driver/disk eccentricity.
Friction, elasticity and physical operating forces are outside this audit.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import trimesh
import manifold3d as mf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from exporter import source_hashes
spec=importlib.util.spec_from_file_location('review',ROOT/'work/final-print-check.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
solid=review.solid
DIR=ROOT/'work/rendered-parts/scale-100-200'
cx=-.028609

def rotate(body,angle,center=0):
    t=trimesh.transformations.rotation_matrix(-np.deg2rad(angle),[0,1,0],[center,0,0])
    return body.transform(t[:3])

def run(holes,code):
    names=['knob','shaft','dial','disk_1','disk_2','disk_3','fastener_1','fastener_2','fastener_3','link','collar_1','collar_2','collar_3','door']
    meshes={n:trimesh.load_mesh(DIR/f'{n}.stl') for n in names}
    for n in names:assert json.loads((DIR/f'{n}.export.json').read_text())['source_hashes']==source_hashes()
    for i,h in enumerate(holes):
        pin=meshes[f'fastener_{i+1}'];pin.apply_translation(-np.array([55,10+[0,9.4,18.3][i],6]))
        pin.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]))
        a=np.deg2rad((h-7)*22.5);pin.apply_translation([cx+13.5*np.cos(a),i*5,13.5*np.sin(a)])
    bodies={n:solid(m) for n,m in meshes.items()}
    pairs=[('knob','fastener_3'),('fastener_3','fastener_2'),('fastener_2','fastener_1')]
    center=lambda n:0 if n in ['knob','shaft','dial'] else cx
    bearing=lambda n:90 if n=='knob' else (holes[int(n[-1])-1]-7)*22.5
    bands=[]
    for a,b in pairs:
        offset=bearing(b)-bearing(a);aligned=rotate(bodies[a],offset,center(a));edges=[]
        for direction in [-1,1]:
            lo,hi=0.,50.
            assert (aligned^bodies[b]).volume()>1
            for _ in range(30):
                mid=(lo+hi)/2
                if abs((rotate(aligned,direction*mid,center(a))^bodies[b]).volume())>1e-6:lo=mid
                else:hi=mid
            edges.append(offset+direction*hi)
        bands.append(edges)
    low=np.array(bands)[:,0];high=np.array(bands)[:,1];span=360-(high-low)
    q=[0.]
    for i in range(3):q.append(q[-1]-high[i]-span[i]/2)
    phases=np.array(code)%16*22.5
    first=phases[0]-2160
    d=(phases[1]-first)%360
    while d<sum(span[:2])-1e-6:d+=360
    second=first+d
    d=(second-phases[2])%360
    while d<span[0]-1e-6:d+=360
    stops=[first,second,second-d]
    trace=[];worst={};transmitting={};sample_count=0
    for stop in stops:
        for dial in np.linspace(q[0],stop,int(abs(stop-q[0])/1)+2)[1:]:
            old=q.copy();q[0]=float(dial)
            for i in range(3):
                gap=(old[i]-old[i+1]-high[i])%360
                if gap>360-1e-7:gap=0
                proposed=gap+q[i]-old[i]
                if proposed>span[i]:q[i+1]=old[i+1]+proposed-span[i]
                elif proposed<0:q[i+1]=old[i+1]+proposed
            # Inspect trajectory every10degrees, not only the final stops.
            sample_count+=1
            if sample_count%10:continue
            moving={n:rotate(bodies[n],q[0] if n in ['shaft','dial','knob'] else q[4-int(n[-1])],center(n))
                    for n in ['shaft','dial','knob','disk_1','disk_2','disk_3','fastener_1','fastener_2','fastener_3']}
            # Non-adjacent pin bodies and complete neighboring disk bodies were excluded previously.
            checks=[]
            for i in range(1,4):
                for j in range(1,4):
                    if i!=j:checks.append((f'fastener_{i}',f'disk_{j}'))
            checks += [('knob','disk_3'),('fastener_1','fastener_3')]
            for a,b in checks:
                v=abs((moving[a]^moving[b]).volume())
                if v>worst.get(a+'/'+b,{}).get('volume_mm3',0):worst[a+'/'+b]=dict(volume_mm3=v,dial_degrees=q[0])
            for a,b in pairs:
                v=abs((moving[a]^moving[b]).volume())
                if v>transmitting.get(a+'/'+b,{}).get('volume_mm3',0):transmitting[a+'/'+b]=dict(volume_mm3=v,dial_degrees=q[0])
        trace.append(q.copy())
    gates=[]
    for i in range(1,4):
        disk=rotate(bodies[f'disk_{i}'],q[4-i],cx)
        values=[abs((disk^bodies['link'].translate([float(x),0,0])).volume()) for x in np.linspace(-8,0,41)]
        gates.append(dict(disk=i,angle_error_degrees=float((q[4-i]+180)%360-180),max_link_overlap_mm3=max(values)))
    # Plan the three stops at measured contact rather than rounding to dial ticks.
    precise_phases=np.array([sum(high),sum(low[:2]),high[0]])%360
    precise_stops=[float(precise_phases[0]-2160)]
    d=(precise_phases[1]-precise_stops[0])%360
    while d<sum(span[:2])-1e-6:d+=360
    precise_stops.append(float(precise_stops[0]+d))
    d=(precise_stops[1]-precise_phases[2])%360
    while d<span[0]-1e-6:d+=360
    precise_stops.append(float(precise_stops[1]-d))
    initial_q=[0.]
    for i in range(3):initial_q.append(initial_q[-1]-high[i]-span[i]/2)
    precise_q=initial_q
    for stop in precise_stops:
        for dial in np.linspace(precise_q[0],stop,int(abs(stop-precise_q[0]))+2)[1:]:
            old=precise_q.copy();precise_q[0]=float(dial)
            for i in range(3):
                gap=(old[i]-old[i+1]-high[i])%360
                if gap>360-1e-7:gap=0
                proposed=gap+precise_q[i]-old[i]
                if proposed>span[i]:precise_q[i+1]=old[i+1]+proposed-span[i]
                elif proposed<0:precise_q[i+1]=old[i+1]+proposed
    precise_gates=[]
    for i in range(1,4):
        disk=rotate(bodies[f'disk_{i}'],precise_q[4-i],cx)
        v=max(abs((disk^bodies['link'].translate([float(x),0,0])).volume()) for x in np.linspace(-8,0,41))
        precise_gates.append(dict(disk=i,angle_error_degrees=float((precise_q[4-i]+180)%360-180),max_link_overlap_mm3=v))
    assert max(abs(x['angle_error_degrees']) for x in precise_gates)<1e-6
    assert max(x['max_link_overlap_mm3'] for x in precise_gates)<.001
    stack=[]
    for i in range(1,4):
        disk=meshes[f'disk_{i}'];collar=meshes[f'collar_{i}']
        stack.append(dict(disk=i,disk_rear_y_mm=float(disk.bounds[1,1]),collar_flange_front_y_mm=float((i-1)*5),
                          nominal_axial_gap_mm=float((i-1)*5-disk.bounds[1,1])))
    result=dict(holes=holes,dial_code=code,contact_bands_degrees=bands,stops=stops,
                stages_dial_rear_middle_front=trace,gate_checks=gates,trajectory_steps=sample_count,
                neighbor_collision_maxima=worst,significant_neighbor_collisions={k:v for k,v in worst.items() if v['volume_mm3']>.001},
                transmitting_contact_maxima=transmitting,axial_stack=stack,
                corrected_contact_dial_numbers=(precise_phases/22.5).tolist(),corrected_gate_checks=precise_gates,
                original_second_leg_degrees=stops[1]-stops[0],corrected_second_leg_degrees=precise_stops[1]-precise_stops[0])
    print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
    result=dict(source_hashes=source_hashes(),scope='200scale1currentmesh; quasistatic contact; no friction/elastic simulation',
                results=[run([0,1,6],[8,4,12]),run([8,4,12],[16,7,2])])
    (ROOT/'work/physical-dialing-audit.json').write_text(json.dumps(result,indent=2))
