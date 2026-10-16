"""Render and independently compare output meshes against preserved components."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import trimesh
from analyze import ROOT,NAMES
from profile_builder import section,contour_distance
from scipy.optimize import linear_sum_assignment
from exporter import render_part,source_hashes,exclusive_file

GROUPS=dict(housing=[0,11],hinges=[1,2,3,5,6,14,15],
            lock=[4,7,8,9,10,12,13,16,17,18,19,20,21],all=list(range(22)))
CASES=dict(baseline={},wide=dict(body_width=170,body_height=100),
           deep=dict(body_depth=120),thick=dict(wall_thickness=2.4),
           rounded=dict(body_corner_radius=13,door_corner_radius=11),
           mechanism=dict(disk_pitch=5.5,shaft_stem_diameter=5.1))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_part(reference,actual,seed):
    ref=trimesh.load_mesh(reference);mesh=trimesh.load_mesh(actual)
    # Reproducible, area-weighted two-way sampling, not a Hausdorff bound.
    distances=[]
    for src,dst in ((ref,mesh),(mesh,ref)):
        points=trimesh.sample.sample_surface(src,5000,seed=seed)[0]
        distances.append(trimesh.proximity.closest_point(dst,points)[1])
    delta=np.abs(mesh.bounds-ref.bounds)
    sample=dict(median=[float(np.median(d)) for d in distances],
                p95=[float(np.percentile(d,95)) for d in distances],
                maximum=[float(d.max()) for d in distances],seed=seed,count_each=5000)
    return dict(bounds_error=float(delta.max()),surface=sample,
                watertight=bool(mesh.is_watertight),winding=bool(mesh.is_winding_consistent),
                is_volume=bool(mesh.is_volume),components=len(mesh.split(only_watertight=False)),
                volume=float(mesh.volume),reference_volume=float(ref.volume),
                status='passed' if delta.max()<=0.10 and max(sample['p95'])<=0.10 and
                max(sample['maximum'])<=0.25 and mesh.is_volume else 'failed')


def section_error(ref,mesh,axis,value):
    a=section(ref,axis,value);b=section(mesh,axis,value)
    if len(a)!=len(b):
        return dict(value=value,reference_loops=len(a),actual_loops=len(b),status='failed')
    if not a:
        return dict(value=value,status='not_applicable')
    ca=np.array([(p.min(axis=0)+p.max(axis=0))/2 for p in a]);cb=np.array([(p.min(axis=0)+p.max(axis=0))/2 for p in b])
    ea=np.array([np.ptp(p,axis=0) for p in a]);eb=np.array([np.ptp(p,axis=0) for p in b])
    rows,cols=linear_sum_assignment(np.linalg.norm(ca[:,None,:]-cb[None,:,:],axis=2)+np.linalg.norm(ea[:,None,:]-eb[None,:,:],axis=2))
    maximum=max(contour_distance(a[r],b[c]) for r,c in zip(rows,cols))
    return dict(value=value,loops=len(a),maximum=maximum,status='passed' if maximum<=0.10 else 'failed')


def check_baseline(i,path):
    result=compare_part(ROOT/'work/reference-parts'/f'{NAMES[i]}.stl',path,1200+i)
    axis=2 if i in [1,2,3,5,6,14,15] else 1
    ref=trimesh.load_mesh(ROOT/'work/reference-parts'/f'{NAMES[i]}.stl');mesh=trimesh.load_mesh(path)
    # Intervals bounded by dominant source planes cover steps, bores and repeating features.
    levels,counts=np.unique(np.round(ref.vertices[:,axis],4),return_counts=True)
    important=levels[counts>=max(4,int(counts.max()*0.15))]
    if len(important)>12:
        important=np.unique(np.r_[levels[0],important[np.linspace(0,len(important)-1,10,dtype=int)],levels[-1]])
    elif len(important)<2:
        important=ref.bounds[:,axis]
    values=(important[:-1]+important[1:])/2
    if i==11:
        values=np.unique(np.r_[values,20,50,89,91])
    result['sections']=[section_error(ref,mesh,axis,float(y)) for y in values]
    if any(s['status']=='failed' for s in result['sections']):
        result['status']='failed'
    return result


def check_variant(i,path,case):
    mesh=trimesh.load_mesh(path)
    baseline=trimesh.load_mesh(ROOT/'exports/baseline'/f'{NAMES[i]}.stl')
    result=dict(watertight=bool(mesh.is_watertight),winding=bool(mesh.is_winding_consistent),
                is_volume=bool(mesh.is_volume),bounds=mesh.bounds.tolist(),
                components=len(mesh.split(only_watertight=False)),status='passed' if mesh.is_volume else 'failed')
    if case in ['wide','deep','thick'] and i in GROUPS['lock'] and i not in [7,13,16]:
        invariant=float(np.abs(mesh.bounds-baseline.bounds).max())
        result['lock_bounds_invariant_error']=invariant
        if invariant>1e-4:
            result['status']='failed'
    if i==11:
        expected=np.array([170,100,100]) if case=='wide' else np.array([142,120,84]) if case=='deep' else np.array([142,100,84])
        result['housing_size_error']=float(np.abs(mesh.extents-expected).max())
        if result['housing_size_error']>0.1:
            result['status']='failed'
        mid=mesh.section([0,1,0],[0,40,0])
        loops=sorted(mid.discrete,key=lambda p:np.ptp(p[:,0]))
        wall=float(loops[-1][:,0].max()-loops[0][:,0].max())
        expected_wall=2.4 if case=='thick' else 1.8
        result['right_wall']=wall
        if abs(wall-expected_wall)>0.1:
            result['status']='failed'
        front=mesh.section([0,1,0],[0,12,0])
        front_loops=sorted(front.discrete,key=lambda p:np.ptp(p[:,0]))
        front_wall=float(front_loops[-1][:,0].max()-front_loops[0][:,0].max())
        result['front_lip_wall']=front_wall
        if abs(front_wall-1.8)>0.03:
            result['status']='failed'
    if case=='rounded' and i in [0,11]:
        plane=-6 if i==0 else 40
        loops=mesh.section([0,1,0],[0,plane,0]).discrete
        outer=max(loops,key=lambda p:np.ptp(p[:,0]))[:,[0,2]]
        lo=outer.min(axis=0);hi=outer.max(axis=0);side=min(hi-lo)
        arc=outer[(outer[:,0]<lo[0]+side*.25)&(outer[:,1]>hi[1]-side*.25)&
                  (outer[:,0]>lo[0]+.01)&(outer[:,1]<hi[1]-.01)]
        cx,cz,c=np.linalg.lstsq(np.c_[2*arc,np.ones(len(arc))],np.einsum('ij,ij->i',arc,arc),rcond=None)[0]
        radius=float(np.sqrt(c+cx*cx+cz*cz))
        result['corner_radius']=radius
        if abs(radius-(11 if i==0 else 13))>0.05:
            result['status']='failed'
    if case=='mechanism':
        expected=baseline.bounds.copy()
        if i in [4,20,21]:
            k={4:0,20:1,21:2}[i];expected[:,1]+=k*.5
        elif i in [17,18,19]:
            expected[:,1]+=(i-17)*.5
        elif i in [10,12]:
            expected[:,1]+=1
        if i in [4,20,21,17,18,19,10,12]:
            error=float(np.abs(mesh.bounds[:,1]-expected[:,1]).max())
            result['pitch_placement_error']=error
            if error>0.01:
                result['status']='failed'
        if i in [8,12]:
            plane=5 if i==8 else 15
            loops=mesh.section([0,1,0],[0,plane,0]).discrete
            loop=min(loops,key=lambda p:np.ptp(p[:,0]))
            diameter=float(np.ptp(loop[:,0]))
            result['stem_diameter' if i==8 else 'knob_bore_diameter']=diameter
            if abs(diameter-5.1)>0.01:
                result['status']='failed'
        if i==8:
            result['shaft_end_y']=float(mesh.bounds[1,1])
            if abs(mesh.bounds[1,1]-19)>0.01:
                result['status']='failed'
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--openscad',required=True)
    parser.add_argument('--group',choices=GROUPS,default='all')
    parser.add_argument('--case',choices=list(CASES)+['invalid'],default='baseline')
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args()
    case_directory=ROOT/'exports'/args.case
    case_directory.mkdir(parents=True,exist_ok=True)
    with exclusive_file(case_directory/'.audit.lock'):
        run_case(args)


def run_case(args):
    out=ROOT/'exports'/args.case;out.mkdir(parents=True,exist_ok=True)
    report=dict(case=args.case,group=args.group,source_hashes=source_hashes(),
                reference_hash=digest(ROOT/'reference/MINI-VAULT.stl'),parts=[],
                self_intersections='not_run',boolean_difference='not_run',physical='not_run',
                motion='not_run',source_placement_only=True)
    if args.case=='invalid':
        for index,parameters in enumerate([dict(body_width=-1),dict(wall_thickness=0),dict(wall_thickness=84),dict(part='unknown')]):
            rejected_output=out/f'invalid-{index+1}.stl'
            try:
                render_part('housing',parameters,rejected_output,args.openscad)
                status='failed'
            except RuntimeError:
                log=rejected_output.with_suffix('.log').read_text()
                status='rejected_input' if 'Assertion' in log else 'failed'
            report['parts'].append(dict(parameters=parameters,status=status,
                                       log=str(rejected_output.with_suffix('.log')),
                                       command=str(rejected_output.with_suffix('.command.json'))))
    else:
        def run(i):
            try:
                path=render_part(NAMES[i],CASES[args.case],out/f'{NAMES[i]}.stl',args.openscad)
            except RuntimeError as error:
                return dict(id=i,name=NAMES[i],status='failed',render_error=str(error))
            result=check_baseline(i,path) if args.case=='baseline' else check_variant(i,path,args.case)
            result.update(id=i,name=NAMES[i],output_hash=digest(path))
            print(NAMES[i],result['status'],round(result.get('bounds_error',0),4),flush=True)
            return result
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for result in pool.map(run,GROUPS[args.group]):
                report['parts'].append(result)
    target=ROOT/'work'/f'audit-{args.group}-{args.case}.json'
    if report['source_hashes']!=source_hashes():
        raise RuntimeError('Source changed during audit; mixed outputs are rejected')
    target.write_text(json.dumps(report,indent=2))
    failures=[p for p in report['parts'] if p['status'] not in ['passed','rejected_input']]
    print('report',target,'failures',len(failures),flush=True)
    raise SystemExit(bool(failures))


if __name__=='__main__':
    main()
