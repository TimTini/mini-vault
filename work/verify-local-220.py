"""Render the saved preset, measure load-bearing sections and check mating pairs.

python work/verify-local-220.py --openscad <openscad.com>
Uses the existing project Python environment. No printer or slicer actions.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solid(mesh):
    result = mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                 np.asarray(mesh.faces, dtype=np.uint64)))
    assert result.status() == mf.Error.NoError
    return result


def assembled(meshes):
    result = {name: mesh.copy() for name, mesh in meshes.items()}
    for index, hole in enumerate([7, 3, 12]):
        pin = result[f'fastener_{index+1}']
        pin.apply_translation(-np.array([55, 10+[0, 9.4, 18.3][index], 6]))
        pin.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [1, 0, 0]))
        angle = np.deg2rad(22.5*(hole-7))
        pin.apply_translation([-.028609+13.5*np.cos(angle), index*5, 13.5*np.sin(angle)])
    return result


def intersections(meshes):
    bodies = {name: solid(mesh) for name, mesh in meshes.items()}
    result = {}
    significant = {}
    for a, b in itertools.combinations(NAMES, 2):
        if np.all(np.minimum(meshes[a].bounds[1], meshes[b].bounds[1]) >
                  np.maximum(meshes[a].bounds[0], meshes[b].bounds[0])):
            overlap = bodies[a] ^ bodies[b]
            volume = abs(float(overlap.volume()))
            if volume > .001:
                result[f'{a}/{b}'] = volume
                data = overlap.to_mesh64()
                mesh = trimesh.Trimesh(data.vert_properties[:, :3], data.tri_verts, process=False)
                # Measured baseline front-face slivers have Y depth <=0.00467mm;
                # source and STL simplification resolution is 0.005mm here.
                # Preserve raw volumes; only classify separate components <=0.006mm
                # thick as numerical contact when testing for NEW interference.
                amount = sum(abs(float(c.volume)) for c in mesh.split(only_watertight=False)
                             if min(c.extents) > .006)
                if amount > .001:
                    significant[f'{a}/{b}'] = amount
    return result, significant


def measurements(meshes):
    np.testing.assert_allclose(meshes['housing'].extents, [220, 220, 220], atol=.02)
    records = {}
    for x, expected in [(-30, 2.4), (-16, 1.6), (-40, 5)]:
        contour = np.concatenate(meshes['link'].section([1, 0, 0], [x, 0, 0]).discrete)
        value = float(np.ptp(contour[:, 2]))
        assert abs(value-expected) < .01, (x, value, expected)
        records[f'link_Z_at_X{x}'] = value
    tongue = meshes['hinge_socket_top'].section([1, 0, 0], [10, 0, 0])
    root = float(np.ptp(np.concatenate(tongue.discrete)[:, 2]))
    assert abs(root-2.6) < .01, root
    records['socket_root_Z'] = root
    # Skin region is away from all ribs and mounts. The back face stays at Y=-5.
    door = meshes['door']
    assert door.contains([[-100, -7.79, 80], [-100, -5.01, 80]]).all()
    assert not door.contains([[-100, -7.81, 80], [-100, -4.99, 80]]).any()
    records['door_skin_probe_interval_mm'] = [2.78, 2.82]
    records['dial_to_door_front_gap_mm'] = float(door.bounds[0, 1]-meshes['dial'].bounds[1, 1])
    assert abs(records['dial_to_door_front_gap_mm']-.2) < .01
    contours = [p[:, [0, 2]] for p in meshes['latch'].section([0, 1, 0], [0, -2, 0]).discrete]
    assert len(contours) == 3, 'the two latch relief pockets must remain closed'
    areas = [abs((p[:-1, 0]*p[1:, 1]-p[:-1, 1]*p[1:, 0]).sum()) for p in contours]
    outer = contours.pop(int(np.argmax(areas)))
    a = outer[:-1]
    v = np.diff(outer, axis=0)
    ligaments = []
    for pocket in contours:
        d = pocket[:, None, :]-a
        t = np.clip((d*v).sum(axis=2)/np.maximum((v*v).sum(axis=1), 1e-20), 0, 1)
        ligaments.append(float(np.linalg.norm(d-t[:, :, None]*v, axis=2).min()))
    assert min(ligaments) >= 2.79, ligaments
    records['latch_pocket_sampled_min_ligament_mm'] = ligaments
    for y, expected in [(20, 2.4), (80, 2.4)]:
        loops = sorted(meshes['housing'].section([0, 1, 0], [0, y, 0]).discrete,
                       key=lambda p: np.ptp(p[:, 0]))
        wall = float(loops[-1][:, 0].max()-loops[0][:, 0].max())
        assert abs(wall-expected) < .02
        records[f'right_wall_Y{y}'] = wall
    # Keep the 2 mm gate open for the unchanged 1.6 mm fence tip.
    assert not meshes['disk_1'].contains([[-12, -1, .8], [-12, -1, -.8]]).any()
    return records


def hinge_samples(meshes, control):
    # Only the door/socket hinge path; latch unlocking/translation is excluded.
    fixed = ['housing', 'hinge_leaf_top', 'hinge_leaf_bottom']
    moving = ['door', 'hinge_socket_top', 'hinge_socket_bottom']
    records = []
    for degrees in [0, 15, 30, 60, 90]:
        transform = trimesh.transformations.rotation_matrix(np.deg2rad(degrees), [0, 0, 1], [20, -.5, 0])
        cases = []
        for parts in [control, meshes]:
            bodies = {n: solid(parts[n]) for n in fixed}
            overlaps = {}
            for name in moving:
                mesh = parts[name].copy()
                mesh.apply_transform(transform)
                body = solid(mesh)
                for other in fixed:
                    amount = abs(float((body ^ bodies[other]).volume()))
                    if amount > .01:
                        overlaps[name+'/'+other] = amount
            cases.append(overlaps)
        increased = {k: value for k, value in cases[1].items() if value > cases[0].get(k, 0)+.01}
        records.append(dict(angle_degrees=degrees, control_mm3=cases[0], candidate_mm3=cases[1],
                            increased_mm3=increased))
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--openscad', required=True)
    args = parser.parse_args()
    parameters = {k: float(v) for k, v in json.loads((ROOT/'mini-vault.json').read_text())
                  ['parameterSets']['220 - local reinforcement'].items()}
    provenance = source_hashes()
    extra = {file: digest(ROOT/file) for file in ['mini-vault.json', 'work/verify-local-220.py']}

    def render(name):
        path = render_part(name, parameters, ROOT/f'exports/local-220/{name}.stl', args.openscad)
        mesh = trimesh.load_mesh(path)
        assert mesh.is_volume and len(mesh.split()) == 1, name
        print(name, 'solid', flush=True)
        return name, mesh

    with ThreadPoolExecutor(max_workers=2) as pool:
        meshes = dict(pool.map(render, NAMES))
    measures = measurements(meshes)
    baseline = {name: trimesh.load_mesh(ROOT/f'exports/baseline/{name}.stl') for name in NAMES}
    invariant = ['fastener_1', 'fastener_2', 'fastener_3', 'disk_1', 'disk_2', 'disk_3',
                 'collar_1', 'collar_2', 'collar_3', 'knob', 'retaining_ring']
    for name in invariant:
        np.testing.assert_allclose(meshes[name].bounds, baseline[name].bounds, atol=.0001)
        assert abs(meshes[name].volume-baseline[name].volume) < .001, name
    np.testing.assert_allclose(meshes['dial'].extents, baseline['dial'].extents, atol=.0001)
    np.testing.assert_allclose(meshes['dial'].bounds, baseline['dial'].bounds-[0, .8, 0], atol=.0001)
    # Same envelope without local reinforcement isolates existing contact slivers
    # from the added material; retain the original-size baseline record as well.
    control = {name: mesh.copy() for name, mesh in baseline.items()}
    control_parameters = dict(body_width=220, body_height=220, body_depth=220,
                              wall_thickness=2.4, bottom_thickness=2.4)
    for name in ['door', 'housing', 'latch', 'latch_cover']:
        path = render_part(name, control_parameters, ROOT/f'exports/local-220-control/{name}.stl', args.openscad)
        control[name] = trimesh.load_mesh(path)
    for name in ['hinge_socket_top', 'hinge_leaf_top']:
        control[name].apply_translation([0, 0, 68])
    for name in ['hinge_socket_bottom', 'hinge_leaf_bottom']:
        control[name].apply_translation([0, 0, -68])
    original, _ = intersections(assembled(baseline))
    before, before_significant = intersections(assembled(control))
    after, after_significant = intersections(assembled(meshes))
    new = {pair: value for pair, value in after_significant.items()
           if value > before_significant.get(pair, 0)+.01}
    samples = hinge_samples(meshes, control)
    records = {name: dict(bounds_mm=mesh.bounds.tolist(), volume_mm3=float(mesh.volume),
                         sha256=digest(ROOT/f'exports/local-220/{name}.stl')) for name, mesh in meshes.items()}
    assert provenance == source_hashes()
    assert extra == {file: digest(ROOT/file) for file in extra}
    report = dict(parameters=parameters, source_hashes=provenance, extra_hashes=extra,
                  measurements=measures, unchanged_parts=invariant, parts=records,
                  baseline_intersections_mm3=original, unreinforced_220_intersections_mm3=before,
                  candidate_intersections_mm3=after,
                  contact_sliver_component_max_thickness_mm=.006,
                  control_non_sliver_intersections_mm3=before_significant,
                  candidate_non_sliver_intersections_mm3=after_significant,
                  increased_intersections_mm3=new, geometric_volume_cm3=sum(m.volume for m in meshes.values())/1000,
                  hinge_angle_samples=samples, physical_strength='not_run',
                  full_mechanism_motion='not_run', slicer_filament='not_run')
    (ROOT/'work/local-220-verification.json').write_text(json.dumps(report, indent=2))
    print('Increased intersections', new, flush=True)
    assert not new, new
    assert all(not p['increased_mm3'] for p in samples), samples
    print('22 solids; measured sections; 231 static pairs and five hinge angle comparisons passed', flush=True)


if __name__ == '__main__':
    main()
