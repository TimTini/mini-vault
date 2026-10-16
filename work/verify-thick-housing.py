"""Check the saved 200/2.4 mm shell against an explicit 200/1.8 mm control.

Run export-print-kit.py for the 200 preset first, then this script with
--openscad and --previous-manifest pointing to the backed-up print manifest.
Rigid sampled geometry only; not a physical PETG fit or thermal simulation.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyze import NAMES
from exporter import render_part, source_hashes

spec = importlib.util.spec_from_file_location('motion', ROOT/'work/final-print-check.py')
motion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)
solid = motion.solid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--openscad', required=True)
    parser.add_argument('--previous-manifest', type=Path, required=True)
    args = parser.parse_args()
    parameters = {k: float(v) for k, v in json.loads((ROOT/'mini-vault.json').read_text())
                  ['parameterSets']['200 - scale 1'].items()}
    assert parameters['wall_thickness'] == 2.4 and parameters['bottom_thickness'] == 2
    provenance = source_hashes()
    directory = ROOT/'work/rendered-parts/scale-100-200'
    manifest_path = ROOT/'exports/mini-vault-200-scale-1-print.verification.json'
    manifest = json.loads(manifest_path.read_text())
    previous = json.loads(args.previous_manifest.read_text())
    assert {k: float(v) for k, v in manifest['parameters'].items()} == parameters
    assert manifest['source_hashes'] == provenance
    meshes = {}
    for name in NAMES:
        path = directory/f'{name}.stl'
        assert motion.digest(path) == manifest['parts'][name]['source_sha256'], name
        assert json.loads(path.with_suffix('.export.json').read_text())['source_hashes'] == provenance
        mesh = trimesh.load_mesh(path)
        assert mesh.is_volume and len(mesh.split()) == 1, name
        if name != 'housing':
            assert motion.digest(path) == previous['parts'][name]['source_sha256'], name
        meshes[name] = mesh
    control_path = render_part('housing', dict(parameters, wall_thickness=1.8),
                              ROOT/'work/thick-housing/control-1.8.stl', args.openscad)
    control = trimesh.load_mesh(control_path)
    assert motion.digest(control_path) == previous['parts']['housing']['source_sha256']
    housing = meshes['housing']
    np.testing.assert_allclose(housing.extents, [200, 200, 200], atol=.02)
    sections = {}
    for y, expected in [(12, 1.8), (20, 2.4), (100, 2.4), (180, 2.4)]:
        loops = sorted(housing.section([0, 1, 0], [0, y, 0]).discrete, key=lambda p: np.ptp(p[:, 0]))
        measured = float(loops[-1][:, 0].max()-loops[0][:, 0].max())
        assert abs(measured-expected) < .02, (y, measured)
        sections[str(y)] = measured
    # Use indexed OpenSCAD geometry for the material delta. Independent STL
    # simplification can move curved skins by up to the exporter tolerance.
    indexed = []
    indexed_inputs = []
    for path in [directory/'housing.export.json', control_path.with_suffix('.export.json')]:
        indexed_path = Path(json.loads(path.read_text())['source'])
        indexed_inputs.append(dict(path=str(indexed_path), sha256=motion.digest(indexed_path)))
        indexed.append(trimesh.load_mesh(indexed_path, process=False))
    new_body, old_body = map(solid, indexed)
    new_print, old_print = solid(housing), solid(control)
    added = new_body-old_body
    removed = abs(float((old_body-new_body).volume()))
    assert removed < .001, removed
    # The changed material must stay behind the functional front region, and
    # before the unchanged 2 mm rear plate (outer rear plane Y=192).
    front_added = abs(float(added.trim_by_plane([0, -1, 0], -(14-.006)).volume()))
    rear_added = abs(float(added.trim_by_plane([0, 1, 0], 190+.006).volume()))
    assert front_added < .001 and rear_added < .001, (front_added, rear_added)
    posed = motion.checks.place(meshes, 1)
    bodies = {n: solid(m) for n, m in posed.items()}
    checks = motion.checks.checks
    before_meshes = dict(posed, housing=control)
    raw_before, significant_before = checks.intersections(before_meshes)
    raw_after, significant_after = checks.intersections(posed)
    increased = {k: v for k, v in significant_after.items() if v > significant_before.get(k, 0)+.001}
    print('Static 231 pairs; increased contacts:', increased, flush=True)
    moving_names = [n for n in NAMES if n not in ['housing', 'hinge_leaf_top', 'hinge_leaf_bottom']]
    door_group = mf.Manifold.batch_boolean([bodies[n] for n in moving_names], mf.OpType.Add)
    sweeps = {'door': [], 'slider': [], 'disks': [], 'shaft': []}

    def record(group, pose, moving):
        delta = motion.overlap_record(moving ^ added)
        sweeps[group].append(dict(pose=pose, added_material_contact=delta,
                                 control_contact=motion.overlap_record(moving ^ old_print),
                                 candidate_contact=motion.overlap_record(moving ^ new_print)))

    for angle in np.arange(0, 90.001, .5):
        transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0, 0, 1], [20, -.5, 0])
        record('door', float(angle), door_group.transform(transform[:3]))
    print('Door: 181 poses checked', flush=True)
    slider_contacts = []
    for shift in np.linspace(-8, 0, 61):
        for name in ['latch', 'link']:
            moved = bodies[name].translate([float(shift), 0, 0])
            record('slider', dict(part=name, shift_mm=float(shift)), moved)
            for other in NAMES:
                if other not in ['latch', 'link', 'housing']:
                    contact = motion.overlap_record(moved ^ bodies[other])
                    if contact['raw_mm3'] > .001:
                        slider_contacts.append(dict(part=name, other=other, shift_mm=float(shift), **contact))
    print('Slider: 61 positions, both parts checked against all stationary parts', flush=True)
    for index in range(1, 4):
        rotor = bodies[f'disk_{index}']+bodies[f'fastener_{index}']
        for angle in range(0, 360, 2):
            transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0, 1, 0], [-.028609, 0, 0])
            record('disks', dict(disk=index, angle=angle), rotor.transform(transform[:3]))
    rotor = mf.Manifold.batch_boolean([bodies[n] for n in ['shaft', 'dial', 'knob', 'retaining_ring']], mf.OpType.Add)
    for angle in range(0, 360, 2):
        transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0, 1, 0])
        record('shaft', angle, rotor.transform(transform[:3]))
    worst_added = max(r['added_material_contact']['raw_mm3'] for rows in sweeps.values() for r in rows)
    worst_door = max(sweeps['door'], key=lambda r: r['candidate_contact']['non_sliver_mm3'])
    increased_motion = [dict(group=group, pose=r['pose']) for group, rows in sweeps.items() for r in rows
                        if r['candidate_contact']['non_sliver_mm3'] > r['control_contact']['non_sliver_mm3']+.001]
    result = dict(parameters=parameters, source_hashes=provenance,
                  preset_sha256=motion.digest(ROOT/'mini-vault.json'),
                  verifier_sha256=motion.digest(Path(__file__)),
                  previous_manifest_sha256=motion.digest(args.previous_manifest),
                  current_manifest_sha256=motion.digest(manifest_path),
                  unchanged_other_parts=21, control_matches_previous_housing=True,
                  indexed_inputs=indexed_inputs,
                  geometry_basis=dict(material_delta='indexed OpenSCAD OFF before simplification',
                                      static_and_motion_contacts='delivered STL',
                                      added_material_contacts='moving STL against indexed OFF delta'),
                  outer_dimensions_mm=housing.extents.tolist(), right_wall_sections_mm=sections,
                  added_mm3=float(added.volume()), removed_mm3=removed,
                  front_added_mm3=front_added, rear_added_mm3=rear_added,
                  control_contacts_mm3=raw_before, candidate_contacts_mm3=raw_after,
                  candidate_non_sliver_contacts_mm3=significant_after,
                  increased_non_sliver_contacts_mm3=increased, increased_motion_contacts=increased_motion,
                  sweeps=sweeps, slider_other_contacts=slider_contacts,
                  worst_added_contact_mm3=worst_added, worst_door=worst_door,
                  physical_fit='not_run', thermal_warp='not_run', slicer='not_run',
                  limitation='Discrete rigid poses; rotation checks target housing only; static pairs cover all parts. Sliver cutoff 0.006 mm is numerical, not a print tolerance.')
    assert source_hashes() == provenance
    (ROOT/'work/thick-housing/verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(worst_added_contact_mm3=worst_added,
                          worst_door_angle=worst_door['pose'],
                          worst_door_contact_mm3=worst_door['candidate_contact']['non_sliver_mm3'],
                          static_contacts=significant_after, slider_contacts=len(slider_contacts)), indent=2), flush=True)
    assert not increased and not increased_motion and worst_added < .001
    assert not any(r['non_sliver_mm3'] > .001 for r in slider_contacts)


if __name__ == '__main__':
    main()
