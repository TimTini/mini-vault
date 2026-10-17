"""Compare continuous rear-door CSG with a hash-verified measured-layer snapshot.

Run with project Python and --openscad. Writes only --output, never delivered kits.
The snapshot is local evidence; see docs/DOOR-FEATURES.md for reproduction scope.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from exporter import render_part, export_indexed, source_hashes
from audit import compare_part, section_error, check_baseline
from analyze import NAMES


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solid(mesh):
    body = mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                np.asarray(mesh.faces, dtype=np.uint64)))
    assert body.status() == mf.Error.NoError
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--openscad', required=True)
    parser.add_argument('--backup', type=Path, default=ROOT/'work/backup/door-feature-20261017')
    parser.add_argument('--output', type=Path, default=ROOT/'work/door-feature-rebuild')
    parser.add_argument('--motion-only', action='store_true')
    parser.add_argument('--inspect-existing', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    snapshot = json.loads((args.backup/'snapshot.json').read_text())
    for name, expected in snapshot.items():
        assert digest(args.backup/name) == expected, name
    hashes = source_hashes()
    script_hash = digest(Path(__file__))
    preset_hash = digest(ROOT/'mini-vault.json')
    helpers = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in
               [ROOT/'work'/n for n in ['final-print-check.py', 'verify-size-scale.py', 'verify-local-220.py']]}
    presets = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']
    cases = {n: {k: float(v) for k, v in p.items()} for n, p in presets.items()}
    cases.update(minimum={'body_depth': 28.5}, rounded={'door_corner_radius': 11},
                 mechanism={'shaft_stem_diameter': 5.1, 'disk_pitch': 5.5},
                 combined=dict(cases['220 - scale 1.5'], link_web_thickness=2.4,
                               hinge_socket_root_thickness=2.6))
    previous = None
    if args.inspect_existing:
        previous = json.loads((args.output/'geometry-verification.json').read_text())
        assert previous['source_hashes'] == hashes
        assert previous['mini_vault_json_sha256'] == preset_hash
        assert previous['control_snapshot_sha256'] == digest(args.backup/'snapshot.json')
        assert previous['script_sha256'] == script_hash
    report = dict(source_hashes=hashes, script_sha256=script_hash, mini_vault_json_sha256=preset_hash,
                  control_snapshot_sha256=digest(args.backup/'snapshot.json'), cases={},
                  physical='not_run', slicer='not_run', independent_self_intersection='not_run')
    if not args.motion_only:
        for index, (name, parameters) in enumerate(cases.items()):
            folder = args.output/f'case-{index}'
            folder.mkdir(exist_ok=True)
            candidate_path = folder/'candidate.stl'
            if previous is None:
                command = [args.openscad, '--backend', 'Manifold', '--hardwarnings',
                           '--export-format', 'off', '-o', str(folder/'control.off'), '-D', 'part="door"']
                for k, v in parameters.items():
                    command += ['-D', k+'='+json.dumps(v)]
                command.append(str(args.backup/'mini-vault.scad'))
                start = time.perf_counter()
                process = subprocess.run(command, capture_output=True, text=True)
                (folder/'control.log').write_text(process.stdout+process.stderr)
                assert process.returncode == 0, process.stderr
                old_seconds = time.perf_counter()-start
                before = export_indexed(folder/'control.off', folder/'control.stl')
                start = time.perf_counter()
                render_part('door', parameters, candidate_path, args.openscad)
                new_seconds = time.perf_counter()-start
            else:
                old = previous['cases'][name]
                assert old['parameters'] == parameters
                for item in ['control', 'candidate']:
                    assert digest(folder/(item+'.stl')) == old[item]['sha256']
                before = export_indexed(folder/'control.off', folder/'control-recheck.stl')
                assert digest(folder/'control-recheck.stl') == old['control']['sha256']
                old_seconds = old['control']['render_seconds']
                new_seconds = old['candidate']['render_and_export_seconds']
            after = json.loads(candidate_path.with_suffix('.export.json').read_text())
            assert after['source_hashes'] == hashes
            scale = parameters.get('size_scale', 1)
            control, candidate = [trimesh.load_mesh(folder/(n+'.stl')) for n in ['control', 'candidate']]
            indexed_control = trimesh.load_mesh(folder/'control.off', process=False)
            indexed_candidate = trimesh.load_mesh(after['source'], process=False)
            if previous is not None:
                export_indexed(after['source'], folder/'candidate-recheck.stl')
                assert digest(folder/'candidate-recheck.stl') == digest(candidate_path)
            result = compare_part(folder/'control.stl', candidate_path, 6700+index)
            values = [-6.9, -6.1, -4.9, -4.5, -4.02, -3.98, -3.5, -3, -2.1, -1.9,
                      -1, -.02, .02, .2, .5, .9, 1.1, 1.98, 2.02, 2.5, 3.05, 3.2, 3.5,
                      3.98, 4.02, 4.5, 4.9, 5.1, 10, 12.9]
            result['sections'] = [section_error(indexed_control, indexed_candidate, 1, y*scale) for y in values]
            # The old simplified STL bridges the Y0 discontinuity; keep its diagnostics
            # but compare the actual indexed source at that seam at the same .1 mm gate.
            result['stl_sections'] = [section_error(control, candidate, 1, y*scale) for y in values if abs(y) > .05]
            result['stl_seam_diagnostics'] = [section_error(control, candidate, 1, y*scale) for y in [-.02,.02]]
            result['parameters'] = parameters
            result['control'] = dict(faces=before['indexed_faces'], stl_faces=before['stl_faces'],
                indexed_sha256=digest(folder/'control.off'), sha256=digest(folder/'control.stl'),
                render_seconds=old_seconds, zero_area_faces=int((indexed_control.area_faces == 0).sum()))
            result['candidate'] = dict(faces=after['indexed_faces'], stl_faces=after['stl_faces'],
                indexed_sha256=digest(Path(after['source'])), sha256=digest(candidate_path),
                render_and_export_seconds=new_seconds, indexed_zero_area=int((indexed_candidate.area_faces == 0).sum()),
                stl_zero_area=int((trimesh.load_mesh(candidate_path, process=False).area_faces == 0).sum()))
            result['complexity_passed'] = after['indexed_faces'] < 30000
            if any(s['status'] == 'failed' for s in result['sections'] + result['stl_sections']):
                result['status'] = 'failed'
            if result['candidate']['indexed_zero_area'] or result['candidate']['stl_zero_area']:
                result['status'] = 'failed'
            assert candidate.is_volume and len(candidate.split()) == 1
            report['cases'][name] = result
            (args.output/'geometry-verification.json').write_text(json.dumps(report, indent=2))
            print(name, result['status'], before['indexed_faces'], '->', after['indexed_faces'],
                  'zeros', result['candidate']['indexed_zero_area'], result['candidate']['stl_zero_area'], flush=True)
        report['reference_default'] = check_baseline(0, args.output/'case-0/candidate.stl')
        (args.output/'geometry-verification.json').write_text(json.dumps(report, indent=2))
        assert report['reference_default']['status'] == 'passed'
        assert all(r['status'] == 'passed' and r['complexity_passed'] for r in report['cases'].values())

    spec = importlib.util.spec_from_file_location('motion', ROOT/'work/final-print-check.py')
    motion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(motion)
    geometry = json.loads((args.output/'geometry-verification.json').read_text())
    assert geometry['source_hashes'] == hashes and geometry['mini_vault_json_sha256'] == preset_hash
    contacts = {}
    for case, scale, key, source_folder in [('200 - scale 1', 1, '200-scale-1', 'scale-100-200'),
                                           ('220 - scale 1.5', 1.5, '220-scale-1.5', 'scale-150-220')]:
        index = list(cases).index(case)
        folder = args.output/f'case-{index}'
        manifest_path = args.backup/'exports'/f'mini-vault-{key}-print.verification.json'
        manifest = json.loads(manifest_path.read_text())
        assert manifest['parameters'] == presets[case] and geometry['cases'][case]['parameters'] == cases[case]
        assert geometry['cases'][case]['status'] == 'passed'
        mesh_hashes = {n: digest(folder/(n+'.stl')) for n in ['control', 'candidate']}
        for n, expected in mesh_hashes.items():
            assert expected == geometry['cases'][case][n]['sha256']
        meshes = {}
        for name in NAMES:
            if name == 'door':
                continue
            path = ROOT/'work/rendered-parts'/source_folder/(name+'.stl')
            assert digest(path) == manifest['parts'][name]['source_sha256'], name
            meshes[name] = trimesh.load_mesh(path)
        bodies = {n: solid(m) for n, m in motion.checks.place(meshes, scale).items()}
        doors = [solid(trimesh.load_mesh(folder/(n+'.stl'))) for n in ['control', 'candidate']]
        records, increases = [], []

        def compare(group, position, part, door_transform=None):
            values = [motion.overlap_record((door.transform(door_transform) if door_transform is not None else door) ^ part)
                      for door in doors]
            row = dict(group=group, position=position, control=values[0], candidate=values[1])
            records.append(row)
            if values[1]['non_sliver_mm3'] > values[0]['non_sliver_mm3'] + .001:
                increases.append(row)

        for name in bodies:
            compare('static/'+name, 0, bodies[name])
        fixed = ['housing', 'hinge_leaf_top', 'hinge_leaf_bottom']
        for angle in np.linspace(0, 90, 361):
            transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0,0,1], [20*scale,-.5*scale,0])[:3]
            for name in fixed:
                compare('door/'+name, float(angle), bodies[name], transform)
        for distance in np.linspace(0, -8*scale, 121):
            transform = np.eye(4)[:3]; transform[0,3] = distance
            for name in ['latch', 'link']:
                moved = bodies[name].transform(transform)
                values = [motion.overlap_record(door ^ moved) for door in doors]
                row = dict(group='slider/'+name, position=float(distance), control=values[0], candidate=values[1])
                records.append(row)
                if values[1]['non_sliver_mm3'] > values[0]['non_sliver_mm3'] + .001:
                    increases.append(row)
        for angle in range(0, 360, 2):
            for group, names, center in [('shaft', ['shaft','dial','knob'], [0,0,0]),
                                         ('disks', ['disk_1','disk_2','disk_3','fastener_1','fastener_2','fastener_3'], [-.028609*scale,0,0])]:
                transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0,1,0], center)[:3]
                for name in names:
                    compare(group+'/'+name, angle, bodies[name].transform(transform))
        contacts[case] = dict(records=records, increased_contacts=increases, unchanged_other_parts=21,
                              manifest_sha256=digest(manifest_path), door_sha256=mesh_hashes)
        for n, expected in mesh_hashes.items():
            assert digest(folder/(n+'.stl')) == expected
        (args.output/'motion-verification.json').write_text(json.dumps(dict(source_hashes=hashes, cases=contacts,
            script_sha256=script_hash, motion_helper_sha256=helpers, mini_vault_json_sha256=preset_hash,
            geometry_report_sha256=digest(args.output/'geometry-verification.json'),
            method='Rigid sampled door/slider/shaft/disk poses and mesh Booleans; no contact-force solver.',
            physical='not_run', slicer='not_run'), indent=2))
        print(case, 'motion records', len(records), 'increases', len(increases), flush=True)
    assert source_hashes() == hashes and digest(ROOT/'mini-vault.json') == preset_hash
    assert digest(Path(__file__)) == script_hash
    for name, expected in helpers.items():
        assert digest(ROOT/name) == expected
    assert all(not c['increased_contacts'] for c in contacts.values()), 'Inspect increased contact report'


if __name__ == '__main__':
    main()
