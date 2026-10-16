"""Export actual door/shaft/collar meshes as an offline classic-script asset."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from exporter import source_hashes

data={}
evidence=[]
for scale,folder in [(1,'scale-100-200'),(1.5,'scale-150-220')]:
    parts={}
    for name in ['door','shaft','collar_1','collar_2','collar_3']:
        path=ROOT/'work/rendered-parts'/folder/f'{name}.stl'
        meta=json.loads(path.with_suffix('.export.json').read_text())
        assert meta['source_hashes']==source_hashes(),name
        mesh=trimesh.load_mesh(path)
        assert mesh.is_volume,name
        # Scene X=SCAD X, scene Y=SCAD Z, scene Z=-SCAD Y-2 at scale1.
        points=mesh.vertices[:,[0,2,1]]/scale
        points[:,2]=-points[:,2]-2
        points=np.round(points,6)
        restored=points[:,[0,2,1]].copy()
        restored[:,1]=-restored[:,1]-2
        np.testing.assert_allclose(restored*scale,mesh.vertices,atol=scale*.00000051,rtol=0)
        anchors={}
        if name=='door':
            # Independent mating datum: the door's inside skin is SCAD Y=-5s.
            skin=np.all(np.abs(mesh.triangles[:,:,1]+5*scale)<.00001,axis=1)
            assert mesh.area_faces[skin].sum()>1000*scale*scale
            np.testing.assert_allclose(points[mesh.faces[skin]][:,:,2],3,atol=.000001,rtol=0)
            anchors={'inside_skin_scene_z':3,'first_disk_front_scene_z':0,'skin_to_first_disk_front_gap_normalized_mm':3}
        elif name.startswith('collar_'):
            i=int(name[-1])-1
            flange=np.all(np.abs(mesh.triangles[:,:,1]-i*5*scale)<.00001,axis=1)
            assert mesh.area_faces[flange].sum()>10*scale*scale
            np.testing.assert_allclose(points[mesh.faces[flange]][:,:,2],-2-i*5,atol=.000001,rtol=0)
            anchors={'flange_seat_scene_z':-2-i*5,'disk_rear_scene_z':-2-i*5}
        # Coordinate conversion is a proper rotation, so triangle winding stays valid.
        parts[name]={'positions':points.ravel().tolist(),'indices':mesh.faces.ravel().tolist()}
        evidence.append(dict(scale=scale,part=name,triangles=len(mesh.faces),vertices=len(points),
                             input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                             scene_bounds=[points.min(axis=0).tolist(),points.max(axis=0).tolist()],anchors=anchors))
    data[str(scale)]={'parts':parts}
asset=ROOT/'simulator/context-meshes.js'
asset.write_text('/* Generated from current source-axis STL; work/export-simulator-context.py. */\nwindow.VaultContextMeshes='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf8')
report=dict(scope='exact current200/220door,shaft,collar context; normalized scale; no CAD/STL changes',
            source_hashes=source_hashes(),meshes=evidence,asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest())
(ROOT/'work/simulator-context-verification.json').write_text(json.dumps(report,indent=2))
print(f'Exported10current context meshes; reversible coordinate check passed; {asset.stat().st_size}bytes.')
