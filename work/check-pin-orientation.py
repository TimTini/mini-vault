"""Check current source-axis pin meshes against exterior/interior assembly datums."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from exporter import source_hashes

def check():
    records=[]
    for scale,folder in [(1,'scale-100-200'),(1.5,'scale-150-220')]:
        for i,hole in enumerate([0,1,6]):
            path=ROOT/'work/rendered-parts'/folder/f'fastener_{i+1}.stl'
            meta=json.loads(path.with_suffix('.export.json').read_text())
            assert meta['source_hashes']==source_hashes()
            mesh=trimesh.load_mesh(path)
            mesh.apply_translation(-scale*np.array([55,10+[0,9.4,18.3][i],6]))
            mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]))
            a=np.deg2rad((hole-7)*22.5)
            axis=scale*np.array([-.028609+13.5*np.cos(a),13.5*np.sin(a)])
            rear=i*5*scale
            mesh.apply_translation([axis[0],rear,axis[1]])
            def radius(y):
                section=mesh.section(plane_normal=[0,1,0],plane_origin=[0,y,0])
                assert section is not None
                points=np.concatenate(section.discrete)[:,[0,2]]
                return float(np.linalg.norm(points-axis,axis=1).max())
            small_y=rear-3*scale
            big_y=rear+scale
            small=radius(small_y);big=radius(big_y)
            assert small<1.6*scale and big>3.3*scale
            assert small_y<rear-2*scale<big_y
            # At each disk, scene Z = -(SCAD Y - rear)/scale - 2.
            assert -(small_y-rear)/scale-2>0
            assert -(big_y-rear)/scale-2<-2
            records.append(dict(scale=scale,disk=i+1,hole=hole,
                                small_end_towards_exterior_y_mm=small_y,small_radius_mm=small,
                                large_head_towards_interior_y_mm=big_y,head_radius_mm=big,
                                mesh_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    result=dict(scope='current pin meshes, SCAD assembled transform and scene axis comparison; no friction/motion assertion',
                source_hashes=source_hashes(),orientation='small end towards external dial; large head towards box interior',pins=records)
    (ROOT/'work/pin-orientation-verification.json').write_text(json.dumps(result,indent=2))
    print('6 current mesh sections: small ends face exterior, large heads face interior; SCAD/scene axes consistent.')

if __name__=='__main__':check()
