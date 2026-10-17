"""Read-only acceptance of feature CSG against the snapshotted layered builder.

Run with project Python, --openscad <executable>. Outputs stay under --output.
No delivered mesh is replaced by this verifier. Physical fit is not tested.
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
    result = mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                  np.asarray(mesh.faces, dtype=np.uint64)))
    assert result.status() == mf.Error.NoError
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--openscad', required=True)
    parser.add_argument('--backup', type=Path, default=ROOT/'work/backup/housing-feature-20261017')
    parser.add_argument('--output', type=Path, default=ROOT/'work/housing-feature-rebuild')
    parser.add_argument('--motion-only', action='store_true')
    parser.add_argument('--inspect-existing', action='store_true',
                        help='Recheck the hash-bound render matrix without rendering again')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    snapshot = json.loads((args.backup/'snapshot.json').read_text())
    for name, expected in snapshot.items():
        assert digest(args.backup/name) == expected, name
    hashes = source_hashes()
    preset_hash = digest(ROOT/'mini-vault.json')
    script_hash = digest(Path(__file__))
    motion_helpers = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in
                      [ROOT/'work'/n for n in ['final-print-check.py', 'verify-size-scale.py',
                                               'verify-local-220.py']]}
    old_metadata = json.loads((args.backup/'work/rendered-parts/scale-100-200/housing.export.json').read_text())
    for name, expected in old_metadata['source_hashes'].items():
        path = args.backup/name if (args.backup/name).exists() else ROOT/name
        assert digest(path) == expected, 'Changed control dependency: '+name
    previous = None
    if args.inspect_existing:
        previous = json.loads((args.output/'geometry-verification.json').read_text())
        assert previous['source_hashes'] == hashes
        assert previous['control_snapshot_sha256'] == digest(args.backup/'snapshot.json')
    presets = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']
    cases = {name: {k: float(v) for k, v in p.items()} for name, p in presets.items()}
    cases.update(minimum={'body_depth': 28.5}, rounded={'body_corner_radius': 13},
                 maximum={'body_width': 220, 'body_height': 220, 'body_depth': 220,
                          'wall_thickness': 3, 'bottom_thickness': 4, 'body_corner_radius': 14})
    report = dict(source_hashes=hashes, script_sha256=digest(Path(__file__)),
                  mini_vault_json_sha256=preset_hash,
                  control_snapshot_sha256=digest(args.backup/'snapshot.json'), cases={},
                  physical='not_run', slicer='not_run', independent_self_intersection='not_run')
    if not args.motion_only:
        for index, (name, params) in enumerate(cases.items()):
            folder = args.output/f'case-{index}'
            folder.mkdir(exist_ok=True)
            command = [args.openscad, '--backend', 'Manifold', '--hardwarnings',
                       '--export-format', 'off', '-o', str(folder/'control.off'),
                       '-D', 'part="housing"']
            for k, v in params.items():
                command += ['-D', k+'='+json.dumps(v)]
            command.append(str(args.backup/'mini-vault.scad'))
            path = folder/'candidate.stl'
            if previous is None:
                start = time.perf_counter()
                p = subprocess.run(command, capture_output=True, text=True)
                (folder/'control.log').write_text(p.stdout+p.stderr)
                assert p.returncode == 0, p.stderr
                control_seconds = time.perf_counter()-start
                before = export_indexed(folder/'control.off', folder/'control.stl')
                start = time.perf_counter()
                render_part('housing', params, path, args.openscad)
                candidate_seconds = time.perf_counter()-start
            else:
                old = previous['cases'][name]
                assert old['parameters'] == params
                assert digest(folder/'control.stl') == old['control']['sha256']
                assert digest(path) == old['candidate']['sha256']
                # Bind the indexed seam probe to the previously accepted input STL.
                before = export_indexed(folder/'control.off', folder/'control-recheck.stl')
                assert digest(folder/'control-recheck.stl') == old['control']['sha256']
                control_seconds = old['control']['render_seconds']
                candidate_seconds = old['candidate']['render_and_export_seconds']
            after = json.loads(path.with_suffix('.export.json').read_text())
            assert after['source_hashes'] == hashes
            scale = params.get('size_scale', 1)
            control, candidate = [trimesh.load_mesh(folder/(n+'.stl')) for n in ['control', 'candidate']]
            result = compare_part(folder/'control.stl', path, 5700+index)
            assert candidate.is_volume and len(candidate.split()) == 1
            values = [-7.976, -7.8, -7.5, -6.2, -5.7, -5.3063, -5.1, -4.8,
                      -3.1, -2.9, -2, -1.2, -.5, .18, .22, .6871, 1.9, 2.1,
                      3, 4.1, 6, 7.9, 8.1, 10.5, 11.1, 13.9, 14.1, 20]
            result['sections'] = [section_error(control, candidate, 1, y*scale) for y in values]
            # Within .005 mm of a discontinuous pocket end, the old simplified
            # STL smears an 8 mm step. Compare the indexed CSG there separately.
            indexed_control = trimesh.load_mesh(folder/'control.off', process=False)
            indexed_candidate = trimesh.load_mesh(after['source'], process=False)
            if previous is not None:
                export_indexed(after['source'], folder/'candidate-recheck.stl')
                assert digest(folder/'candidate-recheck.stl') == digest(path)
            result['indexed_seam_sections'] = [section_error(indexed_control, indexed_candidate, 1, y*scale)
                                               for y in [-5.201, .201]]
            result['control'] = dict(faces=before['indexed_faces'], stl_faces=before['stl_faces'],
                                     indexed_sha256=digest(folder/'control.off'),
                                     sha256=digest(folder/'control.stl'), render_seconds=control_seconds)
            result['candidate'] = dict(faces=after['indexed_faces'], stl_faces=after['stl_faces'],
                                       indexed_sha256=digest(Path(after['source'])),
                                       sha256=digest(path), render_and_export_seconds=candidate_seconds)
            result['parameters'] = params
            if any(s['status']=='failed' for s in result['sections']+result['indexed_seam_sections']):
                result['status'] = 'failed'
            result['complexity_passed'] = after['indexed_faces'] < 20000
            report['cases'][name] = result
            (args.output/'geometry-verification.json').write_text(json.dumps(report, indent=2))
            print(name, result['status'], before['indexed_faces'], '->', after['indexed_faces'], flush=True)
        report['reference_default'] = check_baseline(11, args.output/'case-0/candidate.stl')
        (args.output/'geometry-verification.json').write_text(json.dumps(report, indent=2))
        assert report['reference_default']['status'] == 'passed'
        assert all(r['status']=='passed' and r['complexity_passed'] for r in report['cases'].values())

    # Only housing changes. Every moving part is bound to the current delivered manifest.
    spec = importlib.util.spec_from_file_location('motion', ROOT/'work/final-print-check.py')
    motion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(motion)
    contacts = {}
    geometry = json.loads((args.output/'geometry-verification.json').read_text())
    assert geometry['source_hashes'] == hashes
    for case, scale in [('200 - scale 1', 1), ('220 - scale 1.5', 1.5)]:
        index = list(cases).index(case)
        folder = args.output/f'case-{index}'
        source_dir = ROOT/('work/rendered-parts/scale-100-200' if scale==1 else 'work/rendered-parts/scale-150-220')
        manifest_path = args.backup/('exports/mini-vault-200-scale-1-print.verification.json' if scale==1
                                    else 'exports/mini-vault-220-scale-1.5-print.verification.json')
        manifest = json.loads(manifest_path.read_text())
        assert manifest['parameters'] == presets[case]
        assert geometry['cases'][case]['parameters'] == cases[case]
        assert geometry['cases'][case]['status'] == 'passed'
        for n in ['control', 'candidate']:
            assert digest(folder/(n+'.stl')) == geometry['cases'][case][n]['sha256']
        meshes = {}
        for name in NAMES:
            path = source_dir/(name+'.stl')
            if name != 'housing':
                assert digest(path) == manifest['parts'][name]['source_sha256'], name
                meshes[name] = trimesh.load_mesh(path)
        placed = motion.checks.place(meshes, scale)
        bodies = {n: solid(m) for n, m in placed.items()}
        housing = [solid(trimesh.load_mesh(folder/(n+'.stl'))) for n in ['control', 'candidate']]
        housing_hashes = {n: digest(folder/(n+'.stl')) for n in ['control', 'candidate']}
        records, increases = [], []
        unions = {}

        def compare(group, position, moving, transform=None):
            key = tuple(moving)
            if key not in unions:
                unions[key] = mf.Manifold.batch_boolean([bodies[n] for n in moving], mf.OpType.Add)
            body = unions[key]
            if transform is not None:
                body = body.transform(transform)
            values = [motion.overlap_record(body ^ h) for h in housing]
            row = dict(group=group, position=position, control=values[0], candidate=values[1])
            records.append(row)
            if values[1]['non_sliver_mm3'] > values[0]['non_sliver_mm3'] + .001:
                increases.append(row)

        for name in bodies:
            compare('static/'+name, 0, [name])
        moving = [n for n in bodies if n not in ['hinge_leaf_top', 'hinge_leaf_bottom']]
        for angle in np.linspace(0, 90, 361):
            transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0,0,1],
                                                                  [20*scale,-.5*scale,0])[:3]
            compare('door', float(angle), moving, transform)
        for distance in np.linspace(0, -8*scale, 121):
            transform = np.eye(4)[:3]; transform[0,3] = distance
            compare('slider', float(distance), ['latch','link'], transform)
        contacts[case] = dict(records=records, increased_contacts=increases,
                              unchanged_other_parts=21, manifest_sha256=digest(manifest_path),
                              housing_sha256=housing_hashes)
        for n, expected in housing_hashes.items():
            assert digest(folder/(n+'.stl')) == expected
        (args.output/'motion-verification.json').write_text(json.dumps(dict(source_hashes=hashes, cases=contacts,
            script_sha256=script_hash, motion_helper_sha256=motion_helpers,
            mini_vault_json_sha256=preset_hash,
            geometry_report_sha256=digest(args.output/'geometry-verification.json'),
            method='Analytic rigid transforms, door 0..90 by .25deg; slider 121 positions. Mesh Boolean contacts; no force solver.',
            physical='not_run', slicer='not_run'), indent=2))
        print(case, 'motion increases', len(increases), flush=True)
    assert source_hashes() == hashes
    assert digest(ROOT/'mini-vault.json') == preset_hash
    assert digest(Path(__file__)) == script_hash
    for name, expected in motion_helpers.items():
        assert digest(ROOT/name) == expected
    assert all(not c['increased_contacts'] for c in contacts.values()), 'Increased contact: inspect motion report'


if __name__ == '__main__':
    main()
