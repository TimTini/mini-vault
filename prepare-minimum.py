"""Build the shallow print-test without scaling the baseline mechanism."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import trimesh
from exporter import ROOT, render_part, source_hashes
from scipy.spatial import cKDTree
from analyze import NAMES


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--openscad',required=True)
    args=parser.parse_args()
    root=ROOT/'print-tests/minimum'
    assembly=root/'assembly';printing=root/'stl'
    assembly.mkdir(parents=True,exist_ok=True);printing.mkdir(exist_ok=True)
    params=json.loads((root/'parameters.json').read_text())
    render_part('housing',params,assembly/'housing.stl',args.openscad)
    records=[];meshes=[]
    for name in NAMES:
        source=ROOT/'exports/baseline'/f'{name}.stl'
        output=assembly/f'{name}.stl'
        if name!='housing':
            shutil.copyfile(source,output)
            assert sha(source)==sha(output)
        mesh=trimesh.load_mesh(output)
        assert mesh.is_volume and len(mesh.split(only_watertight=False))==1,name
        transform=np.eye(4)
        if name=='housing':
            transform[:3,:3]=[[1,0,0],[0,0,1],[0,-1,0]]
        elif not name.startswith(('fastener','hinge_')):
            transform[:3,:3]=[[1,0,0],[0,0,-1],[0,1,0]]
        posed=mesh.copy();posed.apply_transform(transform)
        translation=-posed.bounds[0]
        posed.apply_translation(translation);transform[:3,3]=translation
        print_path=printing/f'{name}.stl';posed.export(print_path)
        checked=trimesh.load_mesh(print_path)
        assert checked.is_volume and abs(checked.bounds[0,2])<1e-5
        assert abs(checked.volume-mesh.volume)<max(0.01,mesh.volume*1e-5)
        records.append(dict(name=name,assembly_sha256=sha(output),baseline_sha256=sha(source),
                            mechanism_unchanged=name!='housing',print_sha256=sha(print_path),
                            print_transform=transform.tolist(),size=checked.extents.tolist(),
                            volume_mm3=float(checked.volume),is_volume=True,components=1))
        meshes.append((name,checked))
    # Shelf layout is for convenience, not a promise about a particular printer.
    x=y=row_height=0.0;layout=[];placements=[]
    for name,mesh in sorted(meshes,key=lambda item:-item[1].extents[1]):
        w,h,_=mesh.extents
        if x and x+w>250:
            x=0;y+=row_height+5;row_height=0
        placed=mesh.copy();placed.apply_translation([x,y,0]);layout.append(placed)
        placements.append(dict(name=name,offset=[x,y,0]));x+=w+5;row_height=max(row_height,h)
    for i,a in enumerate(layout):
        for b in layout[i+1:]:
            overlap=np.minimum(a.bounds[1,:2],b.bounds[1,:2])-np.maximum(a.bounds[0,:2],b.bounds[0,:2])
            assert not (overlap>1e-5).all(),'overlapping print placements'
    combined=trimesh.util.concatenate(layout)
    layout_source=ROOT/'work/minimum-layout.off'
    combined.export(layout_source)
    # ASCII preserves double coordinates for the translated shelf layout. Binary
    # float32 at XY~250 collapsed mechanical slivers even after simplification.
    combined.export(root/'layout.stl',file_type='stl_ascii')
    final_layout=trimesh.load_mesh(root/'layout.stl')
    assert final_layout.is_volume and len(final_layout.split(only_watertight=False))==22
    vertex_error=max(float(cKDTree(dst).query(src)[0].max()) for src,dst in
                     [(combined.vertices,final_layout.vertices),(final_layout.vertices,combined.vertices)])
    assert vertex_error<1e-6,'layout coordinate precision lost'
    assert abs(final_layout.volume-combined.volume)<0.01
    layout_export=dict(format='ASCII STL',vertex_distance_max_mm=vertex_error,
                       volume_error_mm3=abs(final_layout.volume-combined.volume))
    housing=trimesh.load_mesh(assembly/'housing.stl')
    shaft=trimesh.load_mesh(assembly/'shaft.stl')
    np.testing.assert_allclose(housing.extents,[142,28.5,84],atol=0.02)
    assert not housing.contains([[0,18.49,0]]).any()
    assert housing.contains([[0,18.51,0]]).all()
    gap=18.5-float(shaft.bounds[1,1]);assert abs(gap-.5)<.01
    baseline=trimesh.load_mesh(ROOT/'exports/baseline/housing.stl')
    hashes=source_hashes()
    hashes['prepare-minimum.py']=sha(Path(__file__))
    hashes['print-tests/minimum/parameters.json']=sha(root/'parameters.json')
    report=dict(parameters=params,source_hashes=hashes,parts=records,
                housing_size=housing.extents.tolist(),shaft_rear_clearance_nominal=gap,
                layout_size=final_layout.extents.tolist(),layout_components=22,placements=placements,
                housing_volume_reduction_percent=100*(1-housing.volume/baseline.volume),
                layout_sha256=sha(root/'layout.stl'),layout_export=layout_export,
                physical_fit='not_run',slicer='not_run',
                motion='not_run',minimum_scope='depth at 0.5 mm nominal rear clearance; XY/mechanism preserved')
    (root/'verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ['parts','placements','source_hashes']},indent=2))


if __name__=='__main__':
    main()
