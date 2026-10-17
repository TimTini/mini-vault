"""Read back both print kits independently of the export process."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from exporter import source_hashes

spec = importlib.util.spec_from_file_location('motion', ROOT/'work/final-print-check.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)

results = {}
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--preset',choices=['all','150 - scale 1','200 - scale 1','220 - scale 1.5'],default='all')
selected=parser.parse_args().preset
for preset,key,folder in [('150 - scale 1','150-scale-1','scale-100-150'),('200 - scale 1','200-scale-1','scale-100-200'),('220 - scale 1.5','220-scale-1.5','scale-150-220')]:
    if selected!='all' and selected!=preset:
        continue
    path = ROOT/f'exports/mini-vault-{key}-print.stl'
    manifest = json.loads(path.with_suffix('.verification.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['sha256']
    assert manifest['source_hashes'] == source_hashes()
    pieces = trimesh.load_mesh(path).split(only_watertight=False)
    assert len(pieces) == 22 and all(p.is_volume for p in pieces)
    records = {}
    for name, record in manifest['parts'].items():
        source_path = ROOT/f'work/rendered-parts/{folder}/{name}.stl'
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == record['source_sha256']
        source = trimesh.load_mesh(source_path)
        transform = np.asarray(record['print_transform'])
        np.testing.assert_allclose(transform[:3,:3].T @ transform[:3,:3], np.eye(3), atol=1e-12)
        assert abs(np.linalg.det(transform[:3,:3])-1) < 1e-12
        expected = source.copy()
        expected.apply_transform(transform)
        matches = [p for p in pieces if np.allclose(p.bounds,expected.bounds,atol=1e-7)]
        assert len(matches) == 1, name
        np.testing.assert_allclose(motion.canonical_triangles(matches[0]),motion.canonical_triangles(expected),atol=1e-7)
        individual_path = ROOT/f'exports/{folder}/{name}.stl'
        individual = trimesh.load_mesh(individual_path)
        expected.apply_translation(-expected.bounds[0])
        np.testing.assert_allclose(motion.canonical_triangles(individual),motion.canonical_triangles(expected),atol=1e-7)
        assert individual.is_volume and len(individual.split()) == 1
        assert abs(individual.volume-source.volume) < .001
        np.testing.assert_allclose(individual.bounds[0],0,atol=1e-7)
        unsupported = (individual.face_normals[:,2]<-.999) & (individual.triangles_center[:,2]>.05)
        area = float(individual.area_faces[unsupported].sum())
        if name == 'latch':
            # Preserve the original T-slot roof on the right of the backer.
            # Only the newly supported shifted-neck region must reach the bed.
            factor = float(manifest['parameters']['size_scale'])
            clip_x = -41.5*factor-source.bounds[0,0]
            neck = unsupported & (individual.triangles_center[:,0] < clip_x-.001)
            assert float(individual.area_faces[neck].sum()) < .001
        records[name] = dict(sha256=hashlib.sha256(individual_path.read_bytes()).hexdigest(),
                             bounds_mm=individual.bounds.tolist(), horizontal_underside_above_bed_mm2=area)
    for i,left in enumerate(pieces):
        for right in pieces[i+1:]:
            assert any(left.bounds[1,a] <= right.bounds[0,a]-9.999999 or right.bounds[1,a] <= left.bounds[0,a]-9.999999 for a in (0,1))
    results[key] = dict(sha256=manifest['sha256'],components=22,closed=True,
                        rigid_transforms_match_triangles=True,individual_parts=records)
    print(key, '22 closed components, exact triangles, 22 print parts and latch bed support verified', flush=True)
suffix='' if selected=='all' else '-'+next(iter(results))
(ROOT/'work'/f'print-delivery{suffix}-verification.json').write_text(json.dumps(results,indent=2))
