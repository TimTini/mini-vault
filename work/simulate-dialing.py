"""Quasistatic rigid pin pickup measured from current meshes; no friction model."""
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
spec=importlib.util.spec_from_file_location('scalecheck',ROOT/'work/verify-size-scale.py')
checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)

def rotated(body,angle):
    t=trimesh.transformations.rotation_matrix(-np.deg2rad(angle),[0,1,0])
    return body.transform(t[:3])

def volume(a,b,angle):
    return abs(float((rotated(a,angle)^b).volume()))

def bounds(a,b):
    # Locate both edges of the forbidden overlap band about the aligned pins.
    angles=np.arange(-180,180.001,2.)
    occupied=[float(t) for t in angles if volume(a,b,t)>1e-6]
    assert occupied and max(occupied)-min(occupied)<120,occupied
    edges=[]
    for direction in [-1,1]:
        lo,hi=0.,80.
        assert volume(a,b,0)>1e-6 and volume(a,b,direction*hi)<1e-6
        for _ in range(32):
            mid=(lo+hi)/2
            if volume(a,b,direction*mid)>1e-6: lo=mid
            else: hi=mid
        edges.append(direction*hi)
    return edges

def run(folder,factor):
    directory=ROOT/folder
    names=['knob','disk_1','disk_2','disk_3','fastener_1','fastener_2','fastener_3','link']
    meshes={n:trimesh.load_mesh(directory/f'{n}.stl') for n in names}
    for n in names:
        assert json.loads((directory/f'{n}.export.json').read_text())['source_hashes']==source_hashes()
    placed=checks.place(meshes,factor)
    bodies={n:checks.checks.solid(m) for n,m in placed.items()}
    # Driver -> rear disk3 -> middle disk2 -> front disk1.
    pairs=[('knob','fastener_3'),('fastener_3','fastener_2'),('fastener_2','fastener_1')]
    contacts=[]
    for a,b in pairs:
        # Align each pair's pin center in XZ before measuring the collision band.
        h={'fastener_1':7,'fastener_2':3,'fastener_3':12}
        bearing=lambda n:90. if n=='knob' else 22.5*(h[n]-7)
        offset=bearing(b)-bearing(a)
        aligned=rotated(bodies[a],offset)
        edge=bounds(aligned,bodies[b])
        contacts.append(dict(driver=a,follower=b,alignment_rotation_degrees=offset,
                             forbidden_relative_angle_degrees=[offset+e for e in edge],
                             edge_offset_degrees=edge,
                             overlap_inside_mm3=volume(aligned,bodies[b],edge[1]-.1),
                             overlap_outside_mm3=volume(aligned,bodies[b],edge[1]+.1)))
        print(factor,a,b,contacts[-1],flush=True)
    low=np.array([p['forbidden_relative_angle_degrees'][0] for p in contacts])
    high=np.array([p['forbidden_relative_angle_degrees'][1] for p in contacts])
    span=360-(high-low)
    # Free relative phase lives in [high,low+360]; clamp only when a pin picks up.
    def simulate(stops,seed,step=.5):
        rng=np.random.default_rng(seed)
        q=[0.]
        for i in range(3): q.append(q[-1]-high[i]-rng.uniform(1,span[i]-1))
        trace=[]
        def move(target):
            nonlocal q
            for dial in np.linspace(q[0],target,int(abs(target-q[0])/step)+2)[1:]:
                old=q.copy();q[0]=float(dial)
                for i in range(3):
                    gap=(old[i]-old[i+1]-high[i])%360
                    proposed=gap+q[i]-old[i]
                    if proposed>span[i]: q[i+1]=old[i+1]+proposed-span[i]
                    elif proposed<0: q[i+1]=old[i+1]+proposed
        # Clear four full turns, then stop at first target CCW.
        first=stops[0]%360+5*360
        move(first);trace.append(q.copy())
        # Two pickup gaps before disk2 can move on the reversed leg.
        distance=(q[0]-stops[1])%360
        while distance<span[0]+span[1]-.000001: distance+=360
        move(q[0]-distance);trace.append(q.copy())
        # One pickup gap before disk3 can move on final CCW leg.
        distance=(stops[2]-q[0])%360
        while distance<span[0]-.000001: distance+=360
        move(q[0]+distance);trace.append(q.copy())
        errors=[float((v+180)%360-180) for v in q[1:]]
        # A gate must clear the returned link at every sampled slider position.
        gate=[]
        for j,name in enumerate(['disk_3','disk_2','disk_1']):
            disk=rotated(bodies[name],q[j+1])
            overlaps=[]
            for x in np.linspace(-8*factor,0,41):
                overlaps.append(abs(float((disk^bodies['link'].translate([float(x),0,0])).volume())))
            gate.append(dict(disk=name,maximum_link_overlap_mm3=max(overlaps)))
        pair_contacts=[]
        for state in trace:
            for i,(a,b) in enumerate(pairs):
                pair_contacts.append(abs(float((rotated(bodies[a],state[i])^rotated(bodies[b],state[i+1])).volume())))
        assert max(pair_contacts)<.00001,pair_contacts
        return dict(seed=seed,step_degrees=step,stop_angles_degrees=[float(v%360) for v in stops],
                    disk_angles_degrees_rear_to_front=errors,stages_rear_to_front=trace,
                    gate_checks=gate,maximum_stop_pin_overlap_mm3=max(pair_contacts))
    exact=np.array([sum(low),sum(high[:2]),low[0]])%360
    rounded=np.round(exact/22.5)*22.5
    trials=[simulate(exact,seed,step) for seed in range(5) for step in [.25,1.]]
    assert all(max(abs(v) for v in t['disk_angles_degrees_rear_to_front'])<1e-6 for t in trials)
    exact_trial=trials[0]
    rounded_trial=simulate(rounded,0)
    assert max(g['maximum_link_overlap_mm3'] for g in exact_trial['gate_checks'])<.001
    # Negative control: an additional five degrees on the final stop blocks disk3.
    wrong=simulate(rounded+np.array([0,0,5.]),0)
    assert wrong['gate_checks'][0]['maximum_link_overlap_mm3']>1
    print('stops',factor,exact/22.5,'rounded',rounded/22.5,
          'gate',rounded_trial['gate_checks'],flush=True)
    return dict(source_hashes=source_hashes(),scale=factor,contacts=contacts,
                convention='Front view, CCW positive; pointer assumed at +Z (top), 16=0. Disk order rear3, middle2, front1.',
                exact_dial_numbers=(exact/22.5).tolist(),rounded_dial_numbers=(rounded/22.5).tolist(),
                exact_trials=trials,rounded_trial=rounded_trial,negative_control=wrong,
                assumptions=['Disks remain stationary until picked up; no frictional drag',
                             'Rigid contact, 1e-6 mm3 Boolean threshold',
                             'Dial/shaft/knob keys preserve current source angular phase',
                             'Top pointer is a stated convention, not a verified marking on the physical door'],
                input_sha256={n:hashlib.sha256((directory/f'{n}.stl').read_bytes()).hexdigest() for n in names})

if __name__=='__main__':
    result=[run('work/rendered-parts/scale-100-200',1),run('work/rendered-parts/scale-150-220',1.5)]
    (ROOT/'work/dialing-contact-verification.json').write_text(json.dumps(result,indent=2))
