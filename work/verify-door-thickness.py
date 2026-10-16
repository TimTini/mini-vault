"""Compare the 200/2.4 mm door kit with its backed-up 2 mm door kit.

Generate current Chrono poses first with chrono-housing-check.py poses.
Run in project Python: verify-door-thickness.py --backup <door-change backup>.
Rigid geometry only, no physical PETG fit or thermal claims.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyze import NAMES
from exporter import source_hashes

spec = importlib.util.spec_from_file_location('motion', ROOT/'work/final-print-check.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', type=Path, required=True)
    args = parser.parse_args()
    parameters = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']['200 - scale 1']
    assert float(parameters['door_plate_thickness']) == 2.4
    manifest_path = ROOT/'exports/mini-vault-200-scale-1-print.verification.json'
    manifest = json.loads(manifest_path.read_text())
    old_manifest_path = args.backup/'mini-vault-200-scale-1-print.verification.json'
    old_manifest = json.loads(old_manifest_path.read_text())
    assert manifest['parameters'] == parameters
    assert manifest['source_hashes'] == source_hashes()
    assert {k: v for k, v in manifest['source_hashes'].items() if k != 'mini-vault.scad'} == {
        k: v for k, v in old_manifest['source_hashes'].items() if k != 'mini-vault.scad'}
    assert old_manifest['parameters'] == dict(parameters, door_plate_thickness='2')
    meshes, control = {}, {}
    changed = ['door', 'shaft', 'dial']
    for name in NAMES:
        path = ROOT/f'work/rendered-parts/scale-100-200/{name}.stl'
        assert motion.digest(path) == manifest['parts'][name]['source_sha256'], name
        meshes[name] = trimesh.load_mesh(path)
        assert meshes[name].is_volume and len(meshes[name].split()) == 1, name
        if name in changed:
            path = args.backup/f'{name}.stl'
            assert motion.digest(path) == old_manifest['parts'][name]['source_sha256'], name
            control[name] = trimesh.load_mesh(path)
        else:
            assert manifest['parts'][name]['source_sha256'] == old_manifest['parts'][name]['source_sha256'], name
            control[name] = meshes[name]
    bodies = [{n: motion.solid(m) for n, m in motion.checks.place(parts, 1).items()}
              for parts in [control, meshes]]
    checks = motion.checks.checks
    raw_before, sig_before = checks.intersections(motion.checks.place(control, 1))
    raw_after, sig_after = checks.intersections(motion.checks.place(meshes, 1))
    increases = [dict(group='static', pair=k, old_mm3=sig_before.get(k, 0), new_mm3=v)
                 for k, v in sig_after.items() if v > sig_before.get(k, 0)+.001]
    poses_path = ROOT/'work/thick-housing/chrono-poses.json'
    poses = json.loads(poses_path.read_text())
    assert poses['preset_sha256'] == motion.digest(ROOT/'mini-vault.json')
    assert poses['main_source_sha256'] == motion.digest(ROOT/'mini-vault.scad')
    assert poses['script_sha256'] == motion.digest(ROOT/'work/chrono-housing-check.py')
    records = []

    def compare(group, pose, moving_names, fixed_names, transform):
        for name in moving_names:
            for other in fixed_names:
                values = [motion.overlap_record(case[name].transform(transform) ^ case[other])
                          for case in bodies]
                if max(r['raw_mm3'] for r in values) > .001:
                    row = dict(group=group, pose=pose, pair=name+'/'+other, control=values[0], candidate=values[1])
                    records.append(row)
                    if values[1]['non_sliver_mm3'] > values[0]['non_sliver_mm3']+.001:
                        increases.append(row)

    for group in ['door', 'slider']:
        moving = ([n for n in NAMES if n not in ['housing', 'hinge_leaf_top', 'hinge_leaf_bottom']]
                  if group == 'door' else ['latch', 'link'])
        fixed = [n for n in NAMES if n not in moving]
        for pose in poses['motors'][group]['poses']:
            compare(group, pose['position'], moving, fixed, np.array(pose['transform_mm'])[:3])
        print(group, len(poses['motors'][group]['poses']), 'Chrono poses compared', flush=True)
    for angle in range(0, 360, 2):
        transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0, 1, 0])[:3]
        compare('shaft', angle, ['shaft', 'dial', 'knob'],
                ['door', 'housing', 'collar_1', 'collar_2', 'collar_3', 'disk_1', 'disk_2', 'disk_3'], transform)
    # Disk gate intentionally engages link: compare disk clearance to the newly
    # thickened door and unchanged stationary supports, excluding driving pins.
    for angle in range(0, 360, 2):
        transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0, 1, 0], [-.028609, 0, 0])[:3]
        compare('disks', angle, ['disk_1', 'disk_2', 'disk_3'],
                ['door', 'housing', 'shaft', 'collar_1', 'collar_2', 'collar_3'], transform)
    door = meshes['door']
    origin = [-80, -20, 70]
    hits, _, _ = door.ray.intersects_location([origin], [[0, 1, 0]], multiple_hits=True)
    planes = sorted(float(p[1]) for p in hits)
    assert len(planes) == 2 and abs(planes[0]+7.4) < .005 and abs(planes[1]+5) < .005, planes
    gaps = {}
    for label, parts in [('control', control), ('candidate', meshes)]:
        dial_gap = float(parts['door'].bounds[0, 1]-parts['dial'].bounds[1, 1])
        bore = min(parts['door'].section([0, 1, 0], [0, -6, 0]).discrete, key=lambda p: np.ptp(p[:, 0]))
        stem = parts['shaft'].section([0, 1, 0], [0, 0, 0]).discrete[0]
        gaps[label] = dict(dial_door_axial_mm=dial_gap,
                           shaft_door_radial_mm=float((np.ptp(bore[:, 0])-np.ptp(stem[:, 0]))/2))
    assert abs(gaps['candidate']['dial_door_axial_mm']-.2) < .005
    assert abs(gaps['candidate']['shaft_door_radial_mm']-.1) < .005
    result = dict(parameters=parameters, source_hashes=source_hashes(),
                  script_sha256=motion.digest(Path(__file__)), manifest_sha256=motion.digest(manifest_path),
                  previous_manifest_sha256=motion.digest(old_manifest_path), chrono_poses_sha256=motion.digest(poses_path),
                  changed_parts=changed, unchanged_parts=19, door_skin_planes_Y_mm=planes, gaps_mm=gaps,
                  static_control_mm3=raw_before, static_candidate_mm3=raw_after,
                  increased_contacts=increases, motion_contacts=records,
                  physical_fit='not_run', thermal_warp='not_run', slicer='not_run',
                  limitation='Sampled rigid motion; intentional mounting contacts retained; numerical sliver cutoff .006 mm is not a print tolerance.')
    target = ROOT/'work/door-thickness-verification.json'
    target.write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(door_skin_planes=planes, gaps=gaps, increased_count=len(increases)), indent=2), flush=True)
    assert not increases, 'See report for increased contacts'


if __name__ == '__main__':
    main()
