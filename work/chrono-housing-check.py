"""Chrono constrained poses, then delivered-STL contact checks in two runtimes.

Generate: <PyChrono python> work/chrono-housing-check.py poses
Inspect: <project python> work/chrono-housing-check.py inspect --previous-manifest <backup.json>
Source: https://api.projectchrono.org/10.0.0/motors.html
Prescribed kinematics only; no calibrated PETG force/friction/thermal model.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'work/thick-housing'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate():
    import pychrono as ch

    preset = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']['200 - scale 1']
    assert [float(preset['body_'+axis]) for axis in ['width', 'depth', 'height']] == [200]*3
    assert float(preset['size_scale']) == 1
    results = {}
    for name, steps, slope in [('door', 360, math.pi/2), ('slider', 120, -.008)]:
        system = ch.ChSystemNSC()
        ground, body = ch.ChBody(), ch.ChBody()
        ground.SetFixed(True)
        system.Add(ground)
        system.Add(body)
        # Body REF begins at the CAD origin, so its solved frame transforms
        # the original CAD coordinates without a separate COM translation.
        if name == 'door':
            motor = ch.ChLinkMotorRotationAngle()
            frame = ch.ChFramed(ch.ChVector3d(.020, -.0005, 0), ch.ChQuaterniond(1, 0, 0, 0))
            motor.Initialize(body, ground, frame)
            motor.SetAngleFunction(ch.ChFunctionRamp(0, slope))
        else:
            motor = ch.ChLinkMotorLinearPosition()
            # Chrono10 linear motor moves along its localZ; map localZ to CADX.
            motor.Initialize(body, ground, ch.ChFramed(ch.ChVector3d(0, 0, 0),
                                                      ch.QuatFromAngleY(math.pi/2)))
            motor.SetMotionFunction(ch.ChFunctionRamp(0, slope))
        system.AddLink(motor)
        records = []
        max_error = 0.
        for step in range(steps+1):
            if step:
                status = system.DoStepKinematics(1/steps)
                assert status in [ch.ExitFlag_SUCCESS, ch.ExitFlag_ABSTOL_RESIDUAL,
                                  ch.ExitFlag_RELTOL_UPDATE, ch.ExitFlag_ABSTOL_UPDATE], (name, step, status)
            rotation = body.GetRotMat()
            axes = [rotation.GetAxisX(), rotation.GetAxisY(), rotation.GetAxisZ()]
            pos = body.GetPos()
            matrix = [[getattr(axes[col], axis) for col in range(3)]+[getattr(pos, axis)*1000]
                      for axis in ['x', 'y', 'z']]+[[0, 0, 0, 1]]
            t = step/steps
            if name == 'door':
                a = t*slope
                c, s = math.cos(a), math.sin(a)
                expected = [[c, -s, 0, 20-20*c-.5*s],
                            [s, c, 0, -.5-20*s+.5*c], [0, 0, 1, 0], [0, 0, 0, 1]]
            else:
                expected = [[1, 0, 0, -8*t], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
            # Rotation error is dimensionless; translation error is in mm.
            error = max(abs(matrix[i][j]-expected[i][j]) for i in range(4) for j in range(4))
            max_error = max(max_error, error)
            records.append(dict(time_s=t, position=90*t if name == 'door' else -8*t,
                                transform_mm=matrix))
        assert max_error < 1e-5, (name, max_error)
        results[name] = dict(poses=records, max_matrix_error=max_error)
        print(name, len(records), 'poses; max matrix error', max_error, flush=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT/'chrono-poses.json').write_text(json.dumps(dict(
        script_sha256=digest(Path(__file__)), preset_sha256=digest(ROOT/'mini-vault.json'),
        main_source_sha256=digest(ROOT/'mini-vault.scad'),
        engine='PyChrono 10.0.0', units='solver meters/radians/seconds; output transforms mm',
        solver='DoStepKinematics, no collision forces or material properties',
        motors=results), indent=2))


def inspect(previous_manifest):
    import numpy as np
    import trimesh

    sys.path.insert(0, str(ROOT))
    from analyze import NAMES
    from exporter import source_hashes
    spec = importlib.util.spec_from_file_location('motion', ROOT/'work/final-print-check.py')
    motion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(motion)
    poses_path = OUTPUT/'chrono-poses.json'
    poses = json.loads(poses_path.read_text())
    assert poses['script_sha256'] == digest(Path(__file__))
    assert poses['preset_sha256'] == digest(ROOT/'mini-vault.json')
    assert poses['main_source_sha256'] == digest(ROOT/'mini-vault.scad')
    manifest_path = ROOT/'exports/mini-vault-200-scale-1-print.verification.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['source_hashes'] == source_hashes()
    meshes = {}
    for name in NAMES:
        path = ROOT/f'work/rendered-parts/scale-100-200/{name}.stl'
        assert digest(path) == manifest['parts'][name]['source_sha256'], name
        meshes[name] = trimesh.load_mesh(path)
    bodies = {n: motion.solid(m) for n, m in motion.checks.place(meshes, 1).items()}
    control_path = OUTPUT/'control-1.8.stl'
    original_check = json.loads((OUTPUT/'verification.json').read_text())
    assert original_check['current_manifest_sha256'] == digest(manifest_path)
    previous = json.loads(previous_manifest.read_text())
    assert digest(previous_manifest) == original_check['previous_manifest_sha256']
    assert json.loads(control_path.with_suffix('.export.json').read_text())['source_hashes'] == source_hashes()
    assert digest(control_path) == previous['parts']['housing']['source_sha256']
    control = motion.solid(trimesh.load_mesh(control_path))
    records = {'door': [], 'slider': []}
    for name in ['door', 'slider']:
        moving = ([n for n in NAMES if n not in ['housing', 'hinge_leaf_top', 'hinge_leaf_bottom']]
                  if name == 'door' else ['latch', 'link'])
        fixed = [n for n in NAMES if n not in moving]
        for pose in poses['motors'][name]['poses']:
            contacts = []
            transform = np.array(pose['transform_mm'])[:3]
            for part in moving:
                moved = bodies[part].transform(transform)
                for other in fixed:
                    contact = motion.overlap_record(moved ^ bodies[other])
                    if contact['raw_mm3'] > .001:
                        previous = motion.overlap_record(moved ^ (control if other == 'housing' else bodies[other]))
                        contacts.append(dict(part=part, other=other, control=previous, candidate=contact))
            records[name].append(dict(position=pose['position'], contacts=contacts))
        print(name, len(records[name]), 'Chrono poses inspected against STL', flush=True)
    increased = [dict(group=group, position=row['position'], part=r['part'], other=r['other'])
                 for group, rows in records.items() for row in rows for r in row['contacts']
                 if r['candidate']['non_sliver_mm3'] > r['control']['non_sliver_mm3']+.001]
    door_contacts = [(row['position'], r) for row in records['door'] for r in row['contacts']
                     if r['other'] == 'housing' and r['candidate']['non_sliver_mm3'] > .001]
    worst = max(door_contacts, key=lambda pair: pair[1]['candidate']['non_sliver_mm3'])
    assert not any(r['candidate']['non_sliver_mm3'] > .001
                   for row in records['slider'] for r in row['contacts'])
    ring_samples = []
    for shift in [0, -.5]:
        contact = motion.overlap_record(bodies['retaining_ring'].translate([0, shift, 0]) ^ bodies['shaft'])
        ring_samples.append(dict(shift_Y_mm=shift, **contact))
    result = dict(script_sha256=digest(Path(__file__)), chrono_poses_sha256=digest(poses_path),
                  manifest_sha256=digest(manifest_path), control_stl_sha256=digest(control_path),
                  previous_manifest_sha256=digest(previous_manifest),
                  source_hashes=source_hashes(), contacts=records, increased_contacts=increased,
                  worst_door_housing=dict(angle_degrees=worst[0], **worst[1]), ring_seating=ring_samples,
                  physical_fit='not_run', collision_force_simulation='not_run', thermal_warp='not_run',
                  limitation='Chrono constrained poses; Manifold STL intersection, no Chrono contact-force solve. Discrete poses and uncalibrated print tolerances cannot certify no jamming.')
    (OUTPUT/'chrono-contact-verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(increased=increased, worst_door_angle=worst[0],
                          worst_door_mm3=worst[1]['candidate']['non_sliver_mm3'],
                          ring_overlaps_mm3=[r['raw_mm3'] for r in ring_samples]), indent=2))
    assert not increased


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['poses', 'inspect'])
    parser.add_argument('--previous-manifest', type=Path)
    arguments = parser.parse_args()
    if arguments.mode == 'inspect' and arguments.previous_manifest is None:
        parser.error('inspect requires --previous-manifest from before the wall change')
    generate() if arguments.mode == 'poses' else inspect(arguments.previous_manifest)
