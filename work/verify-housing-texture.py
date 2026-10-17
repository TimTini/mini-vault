"""Compare 200 housing contacts to an explicit hash-verified pre-texture snapshot."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analyze import NAMES
from exporter import render_part,source_hashes


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup',type=Path,required=True)
    parser.add_argument('--openscad')
    parser.add_argument('--delivered',action='store_true',help='Check the actual exported 200 housing without rendering a separate candidate')
    args=parser.parse_args()
    if not args.delivered and not args.openscad:
        parser.error('--openscad is required when rendering a candidate')
    snapshot=json.loads((args.backup/'snapshot.json').read_text())
    for name,expected in snapshot.items():
        assert digest(args.backup/name)==expected,name
    sources=source_hashes()
    preset_hash=digest(ROOT/'mini-vault.json')
    script_hash=digest(Path(__file__))
    parameters={k:float(v) for k,v in json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']['200 - scale 1'].items()}
    assert parameters['wall_thickness']==3 and parameters['housing_texture']==1
    folder=ROOT/'work/housing-texture'
    directory=ROOT/'work/rendered-parts/scale-100-200'
    if args.delivered:
        path=directory/'housing.stl'
        manifest=json.loads((ROOT/'exports/mini-vault-200-scale-1-print.verification.json').read_text())
        assert {k:float(v) for k,v in manifest['parameters'].items()}==parameters
        assert manifest['source_hashes']==sources
        assert manifest['parts']['housing']['source_sha256']==digest(path)
        assert json.loads(path.with_suffix('.export.json').read_text())['source_hashes']==sources
    else:
        path=render_part('housing',parameters,folder/'candidate.stl',args.openscad)
    spec=importlib.util.spec_from_file_location('motion',ROOT/'work/final-print-check.py')
    motion=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(motion)
    helpers={n:digest(ROOT/'work'/n) for n in ['final-print-check.py','verify-size-scale.py','verify-local-220.py']}
    old_path=args.backup/'work/rendered-parts/scale-100-200/housing.stl'
    housing=[motion.solid(trimesh.load_mesh(p)) for p in [old_path,path]]
    other={}
    meshes={}
    for name in NAMES:
        if name=='housing':
            continue
        p=directory/(name+'.stl')
        key=p.relative_to(ROOT).as_posix()
        assert digest(p)==snapshot[key],name
        other[name]=digest(p)
        meshes[name]=trimesh.load_mesh(p)
    bodies={n:motion.solid(m) for n,m in motion.checks.place(meshes,1).items()}
    rows=[]
    increases=[]

    def compare(group,position,body):
        values=[motion.overlap_record(body^h) for h in housing]
        row=dict(group=group,position=position,control=values[0],candidate=values[1])
        rows.append(row)
        if values[1]['non_sliver_mm3']>values[0]['non_sliver_mm3']+.001:
            increases.append(row)

    for n,body in bodies.items():
        compare('static/'+n,0,body)
    for angle in np.linspace(0,90,361):
        transform=trimesh.transformations.rotation_matrix(np.deg2rad(angle),[0,0,1],[20,-.5,0])[:3]
        compare('door',float(angle),bodies['door'].transform(transform))
    for shift in np.linspace(0,-8,121):
        transform=np.eye(4)[:3]
        transform[0,3]=shift
        for n in ['latch','link']:
            compare('slider/'+n,float(shift),bodies[n].transform(transform))
    for angle in range(0,360,2):
        for names,center in [(['shaft','dial','knob'],[0,0,0]),
                             (['disk_1','disk_2','disk_3','fastener_1','fastener_2','fastener_3'],[-.028609,0,0])]:
            transform=trimesh.transformations.rotation_matrix(np.deg2rad(angle),[0,1,0],center)[:3]
            for n in names:
                compare('rotation/'+n,angle,bodies[n].transform(transform))
    assert len(rows)==2244
    assert source_hashes()==sources and digest(ROOT/'mini-vault.json')==preset_hash
    assert digest(Path(__file__))==script_hash
    for n,expected in other.items():
        assert digest(directory/(n+'.stl'))==expected
    for n,expected in helpers.items():
        assert digest(ROOT/'work'/n)==expected
    report=dict(parameters=parameters,source_hashes=sources,preset_sha256=preset_hash,
                housing_source='delivered' if args.delivered else 'rerendered',
                housing_path=path.relative_to(ROOT).as_posix(),
                verifier_sha256=script_hash,helper_sha256=helpers,
                backup_snapshot_sha256=digest(args.backup/'snapshot.json'),
                control_housing_sha256=digest(old_path),candidate_housing_sha256=digest(path),
                unchanged_other_parts_sha256=other,records=rows,increased_contacts=increases,
                physical='not_run',thermal='not_run',slicer='not_run',
                method='Pairwise rigid sampled contacts; existing sliver classifier, .001 mm3 increase gate.')
    (folder/'contact-verification.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('200:',len(rows),'pairwise records;',len(increases),'increased contacts',flush=True)
    assert not increases,'Inspect contact-verification.json'


if __name__=='__main__':
    main()
