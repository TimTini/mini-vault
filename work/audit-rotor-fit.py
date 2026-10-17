"""Read-only audit of current rotor axial stack and mixed old/new components."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyze import NAMES
from exporter import source_hashes

spec = importlib.util.spec_from_file_location('motion', ROOT/'work/final-print-check.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest_path = ROOT/'exports/mini-vault-200-scale-1-print.verification.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['source_hashes'] == source_hashes()
    current = {}
    hashes = {}
    for name in NAMES:
        path = ROOT/f'work/rendered-parts/scale-100-200/{name}.stl'
        hashes[name] = digest(path)
        assert hashes[name] == manifest['parts'][name]['source_sha256'], name
        current[name] = trimesh.load_mesh(path)
    backup = ROOT/'work/backup/door-thickness-20261017-011018'
    old_manifest = json.loads((backup/'mini-vault-200-scale-1-print.verification.json').read_text())
    old = {}
    for name in ['door', 'shaft', 'dial']:
        path = backup/f'{name}.stl'
        assert digest(path) == old_manifest['parts'][name]['source_sha256']
        old[name] = trimesh.load_mesh(path)
    cases = {'old_2mm': dict(current, **old), 'current_2p4mm': current,
             'new_door_old_shaft_and_dial': dict(current, shaft=old['shaft'], dial=old['dial'])}
    results = {}
    fixed = ['door', 'collar_1', 'collar_2', 'collar_3', 'disk_1', 'disk_2', 'disk_3', 'retaining_ring']
    for label, meshes in cases.items():
        planes = {}
        for name in ['door', 'shaft', 'knob']:
            hits, _, _ = meshes[name].ray.intersects_location([[0, -20, 3]], [[0, 1, 0]], multiple_hits=True)
            planes[name] = sorted(set(float(p[1]) for p in hits))
        solids = {n: motion.solid(meshes[n]) for n in fixed+['shaft', 'dial', 'knob']}
        peaks = {}
        for angle in range(0, 360, 2):
            transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0, 1, 0])[:3]
            for name in ['shaft', 'dial', 'knob']:
                body = solids[name].transform(transform)
                for other in fixed:
                    record = motion.overlap_record(body ^ solids[other])
                    key = name+'/'+other
                    if key not in peaks or record['raw_mm3'] > peaks[key]['raw_mm3']:
                        peaks[key] = dict(angle=angle, **record)
        results[label] = dict(bounds_Y_mm={n: meshes[n].bounds[:, 1].tolist() for n in ['door','shaft','dial','knob','retaining_ring']},
                             thrust_probe_XZ_mm=[0, 3], thrust_probe_Y_planes_mm=planes,
                             shaft_shoulder_door_gap_mm=planes['door'][0]-planes['shaft'][-1],
                             door_knob_gap_mm=planes['knob'][0]-planes['door'][-1],
                             dial_door_gap_mm=float(meshes['door'].bounds[0,1]-meshes['dial'].bounds[1,1]),
                             peak_overlaps=peaks)
        print(label, 'gap', results[label]['dial_door_gap_mm'], flush=True)
        for key, value in peaks.items():
            if value['raw_mm3'] > .001:
                print(key, value['angle'], round(value['raw_mm3'], 6), round(value['non_sliver_mm3'], 6), flush=True)
    projects = {}
    ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    for path in sorted((ROOT/'exports').glob('*.3mf')):
        shafts = []
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if not member.endswith('.model'):
                    continue
                model = ET.fromstring(archive.read(member))
                for obj in model.findall('.//m:object', ns):
                    vertices = obj.findall('./m:mesh/m:vertices/m:vertex', ns)
                    if not vertices:
                        continue
                    points = np.array([[float(v.get(axis)) for axis in ['x', 'y', 'z']] for v in vertices])
                    extents = np.ptp(points, axis=0)
                    if np.allclose(extents[:2], [14, 14], atol=.02) and 30 < extents[2] < 33:
                        shafts.append(dict(member=member, object_id=obj.get('id'), mesh_length_mm=float(extents[2])))
        projects[path.name] = dict(sha256=digest(path), shaft_meshes=shafts)
    assert manifest['source_hashes'] == source_hashes()
    for name, expected in hashes.items():
        assert digest(ROOT/f'work/rendered-parts/scale-100-200/{name}.stl') == expected
    report = dict(source_hashes=source_hashes(), source_STL_sha256=hashes, slicer_project_mesh_inventory=projects,
                  manifest_sha256=digest(manifest_path), script_sha256=digest(Path(__file__)),
                  angle_step_degrees=2, cases=results, physical_fit='not_run',
                  limitation='Rigid nominal meshes; overlap does not measure friction or printed tolerances. Old case retains current non-door support geometry.')
    (ROOT/'work/rotor-fit-audit.json').write_text(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
