"""Compare old/new delivered components and isolate the corrected shallow marker."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('check',ROOT/'work/final-print-check.py')
check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
results={}
for key,folder,factor in [('200-scale-1','scale-100-200',1),('220-scale-1.5','scale-150-220',1.5)]:
    oldpath=ROOT/f'work/backup/door-marker-20261016/mini-vault-{key}-print.stl'
    metadata=json.loads(oldpath.with_suffix('.verification.json').read_text())
    assert hashlib.sha256(oldpath.read_bytes()).hexdigest()==metadata['sha256']
    parts=trimesh.load_mesh(oldpath).split(only_watertight=False)
    unchanged=[]
    for name,record in metadata['parts'].items():
        source=trimesh.load_mesh(ROOT/f'work/rendered-parts/{folder}/{name}.stl')
        previous=[p for p in parts if np.allclose(p.bounds,record['bounds_mm'],atol=1e-7)]
        assert len(previous)==1
        old=previous[0].copy();old.apply_transform(np.linalg.inv(record['print_transform']))
        if name!='door':
            np.testing.assert_allclose(check.canonical_triangles(source),check.canonical_triangles(old),atol=1e-7)
            unchanged.append(name)
            continue
        added=check.solid(source)-check.solid(old)
        removed=check.solid(old)-check.solid(source)
        assert abs(removed.volume())<.001
        components=check.overlap_record(added)['components']
        significant=[c for c in components if c['volume_mm3']>.001]
        print(key,'added',added.volume(),'removed',removed.volume(),'significant',significant,flush=True)
        assert len(significant)==1
        bounds=np.array(significant[0]['bounds_mm'])
        assert abs(bounds[:,0]).max()<.51*factor
        assert bounds[0,2]>27.4*factor
        assert bounds[0,1]>-7.001*factor and bounds[1,1]<-6.79*factor
        contours=source.section([0,1,0],[0,-6.9*factor,0]).discrete
        marker=[p for p in contours if np.ptp(p[:,0])<2*factor and p[:,2].min()>20*factor]
        assert len(marker)==1
        np.testing.assert_allclose(np.ptp(marker[0],axis=0)[[0,2]],[factor,4*factor],atol=.005)
        results[key]=dict(marker_width_height_mm=np.ptp(marker[0],axis=0)[[0,2]].tolist(),
                          added_mm3=added.volume(),removed_mm3=removed.volume(),changed_region_bounds_mm=bounds.tolist())
    assert len(unchanged)==21
    results[key]['unchanged_other_parts']=unchanged
    print(key,results[key],flush=True)
(ROOT/'work/door-marker-fix-verification.json').write_text(json.dumps(results,indent=2))
