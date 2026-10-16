"""Additional sampled-motion and delivered-mesh checks; no physical-fit claim."""
import hashlib
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
from exporter import source_hashes

spec = importlib.util.spec_from_file_location('scale_check', ROOT/'work/verify-size-scale.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
solid = checks.checks.solid


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_triangles(mesh):
    triangles = mesh.triangles
    order = np.lexsort((triangles[:,:,2], triangles[:,:,1], triangles[:,:,0]), axis=-1)
    flat = np.take_along_axis(triangles, order[:,:,None], axis=1).reshape((-1,9))
    return flat[np.lexsort(flat.T)]


def overlap_record(body):
    volume = abs(float(body.volume()))
    if volume < .00001:
        return dict(raw_mm3=volume, non_sliver_mm3=0., components=[])
    data = body.to_mesh64()
    mesh = trimesh.Trimesh(data.vert_properties[:, :3], data.tri_verts, process=False)
    parts = mesh.split(only_watertight=False)
    return dict(raw_mm3=volume,
                non_sliver_mm3=sum(abs(float(p.volume)) for p in parts if min(p.extents) > .006),
                components=[dict(volume_mm3=abs(float(p.volume)), bounds_mm=p.bounds.tolist(),
                                 extents_mm=p.extents.tolist()) for p in parts])


def main():
    sources = source_hashes()
    report = json.loads((ROOT/'work/size-scale-verification.json').read_text())
    assert report['source_hashes'] == sources
    original = {n: trimesh.load_mesh(ROOT/f'work/rendered-parts/scale-150-220/{n}.stl') for n in NAMES}
    for n in NAMES:
        assert digest(ROOT/f'work/rendered-parts/scale-150-220/{n}.stl') == report['parts'][n]['sha256']
    delivered = ROOT/'exports/mini-vault-220-scale-1.5-print.stl'
    manifest = json.loads(delivered.with_suffix('.verification.json').read_text())
    assert digest(delivered) == manifest['sha256']
    assert manifest['source_hashes'] == sources
    loaded = trimesh.load_mesh(delivered)
    pieces = loaded.split(only_watertight=False)
    assert len(pieces) == 22 and all(p.is_volume for p in pieces)
    for name, record in manifest['parts'].items():
        expected = original[name].copy()
        expected.apply_transform(record['print_transform'])
        matches = [p for p in pieces if np.allclose(p.bounds, expected.bounds, atol=1e-7)]
        assert len(matches) == 1, name
        piece = matches[0]
        assert len(piece.faces) == len(expected.faces)
        assert abs(piece.volume - expected.volume) < .001, name
        # Indexed components can reorder vertices. Sorted coordinates preserve
        # the exact mesh check independently of component ordering.
        a, b = piece.vertices, expected.vertices
        np.testing.assert_allclose(a[np.lexsort(a.T)], b[np.lexsort(b.T)], atol=1e-7)
        np.testing.assert_allclose(canonical_triangles(piece), canonical_triangles(expected), atol=1e-7)
    posed = checks.place(original, 1.5)
    fixed_names = ['housing', 'hinge_leaf_top', 'hinge_leaf_bottom']
    moving_names = [n for n in NAMES if n not in fixed_names]
    bodies = {n: solid(m) for n, m in posed.items()}
    fixed = mf.Manifold.batch_boolean([bodies[n] for n in fixed_names], mf.OpType.Add)
    moving = mf.Manifold.batch_boolean([bodies[n] for n in moving_names], mf.OpType.Add)
    assert fixed.status() == moving.status() == mf.Error.NoError
    angles = []
    for angle in np.arange(0., 90.001, .5):
        transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0,0,1], [30,-.75,0])
        contact = overlap_record(moving.transform(transform[:3]) ^ fixed)
        angles.append(dict(angle_degrees=float(angle), **contact))
        if int(angle*2) % 30 == 0:
            print('door', angle, 'raw', contact['raw_mm3'], 'non-sliver', contact['non_sliver_mm3'], flush=True)
    slider = []
    others = [n for n in NAMES if n not in ['latch','link']]
    for shift in np.arange(-12., .001, .2):
        contacts = {}
        for name in ['latch', 'link']:
            moved = bodies[name].translate([float(shift),0,0])
            for other in others:
                record = overlap_record(moved ^ bodies[other])
                if record['raw_mm3'] > .001:
                    contacts[name+'/'+other] = record
        slider.append(dict(shift_X_mm=float(shift), contacts=contacts))
    print('Slider 61 poses; worst non-sliver:',
          max((r['non_sliver_mm3'] for p in slider for r in p['contacts'].values()), default=0), flush=True)
    disk_rotation = []
    retracted = bodies['link'].translate([-12,0,0])
    stationary = ['door', 'housing', 'latch_cover', 'shaft', 'collar_1', 'collar_2', 'collar_3']
    for index in range(1,4):
        name = f'disk_{index}'
        rotor = bodies[name] + bodies[f'fastener_{index}']
        for angle in range(0,360,2):
            transform = trimesh.transformations.rotation_matrix(
                np.deg2rad(angle), [0,1,0], [-.0429135,0,0])
            moved = rotor.transform(transform[:3])
            contacts = {}
            for other in stationary:
                record = overlap_record(moved ^ bodies[other])
                if record['raw_mm3'] > .001:
                    contacts[name+'/'+other] = record
            record = overlap_record(moved ^ retracted)
            if record['raw_mm3'] > .001:
                contacts[name+'/retracted_link'] = record
            disk_rotation.append(dict(part=name, angle_degrees=angle, contacts=contacts))
        print(name, '180 rotation poses checked', flush=True)
    blocked_return = []
    for angle in [0, 5, 22.5, 45, 90, 180]:
        transform = trimesh.transformations.rotation_matrix(
            np.deg2rad(angle), [0,1,0], [-.0429135,0,0])
        disk = bodies['disk_1'].transform(transform[:3])
        blocked_return.append(dict(angle_degrees=angle,
            aligned_tip=overlap_record(bodies['link'] ^ disk),
            withdrawn_tip=overlap_record(retracted ^ disk)))
    locked_names = [n for n in moving_names if n not in ['latch','link']]
    locked = mf.Manifold.batch_boolean([bodies[n] for n in locked_names] +
        [bodies[n].translate([-12,0,0]) for n in ['latch','link']], mf.OpType.Add)
    locked_opening = []
    for angle in [0,.1,.25,.5,1,2,3,5]:
        transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0,0,1], [30,-.75,0])
        locked_opening.append(dict(angle_degrees=angle,
                                  **overlap_record(locked.transform(transform[:3]) ^ fixed)))
    ring_seating = []
    for offset in [0,-.75]:
        ring_seating.append(dict(shift_Y_mm=offset,
            **overlap_record(bodies['retaining_ring'].translate([0,offset,0]) ^ bodies['shaft'])))
    shaft_rotation = []
    rotor = mf.Manifold.batch_boolean([bodies[n] for n in ['shaft','knob','dial']] +
        [bodies['retaining_ring'].translate([0,-.75,0])], mf.OpType.Add)
    for angle in range(0,360,2):
        transform = trimesh.transformations.rotation_matrix(np.deg2rad(angle), [0,1,0])
        moved = rotor.transform(transform[:3])
        contacts = {}
        for other in ['door','housing','collar_1','collar_2','collar_3','disk_1','disk_2','disk_3']:
            record = overlap_record(moved ^ bodies[other])
            if record['raw_mm3'] > .001:
                contacts[other] = record
        shaft_rotation.append(dict(angle_degrees=angle, contacts=contacts))
    print('Shaft/dial/knob with seated ring: 180 rotation poses checked', flush=True)
    worst = max(angles, key=lambda p:p['non_sliver_mm3'])
    door = posed['door'].copy()
    door.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(worst['angle_degrees']), [0,0,1], [30,-.75,0]))
    depth_samples = []
    for component in overlap_record(solid(door) ^ bodies['housing'])['components']:
        bounds = np.array(component['bounds_mm'])
        values = []
        for left, right in [(door, posed['housing']), (posed['housing'], door)]:
            near = left.vertices[np.all((left.vertices >= bounds[0]-.02) &
                                       (left.vertices <= bounds[1]+.02), axis=1)]
            distances = right.nearest.signed_distance(near)
            values.append(float(max(distances, default=0)))
        depth_samples.append(dict(bounds_mm=bounds.tolist(),
                                  max_vertex_penetration_mm=values))
    result = dict(source_hashes=sources, verifier_sha256=digest(Path(__file__)),
                  delivered_stl_sha256=digest(delivered), delivered_components=22,
                  delivered_meshes_match_sources=True, measurements=report['measurements'],
                  hinge=dict(pivot_mm=[30,-.75,0], moving=moving_names, fixed=fixed_names,
                             sampling_degrees=.5, poses=angles),
                  slider=dict(sampling_mm=.2, range_X_mm=[-12,0], moving=['latch','link'],
                              fixed=others, poses=slider),
                  disk_rotation=dict(sampling_degrees=2, poses=disk_rotation,
                      exclusion='Adjacent driving pins and knob intentionally transfer torque; coupled dialing sequence not simulated'),
                  blocked_return=blocked_return, locked_opening=locked_opening,
                  ring_seating=ring_seating,
                  shaft_rotation=dict(sampling_degrees=2, poses=shaft_rotation,
                      exclusion='Driving-pin contacts and coupled code-dial sequence not simulated'),
                  worst_door_contact_depth=dict(angle_degrees=worst['angle_degrees'],
                      method='Signed distances at actual mesh vertices near overlap bounds; not a global maximum proof',
                      components=depth_samples),
                  physical_fit='not_run', slicer='not_run',
                  limitation='Sampled rigid geometry; no extrusion, material or elastic simulation')
    assert source_hashes() == sources
    (ROOT/'work/final-print-check.json').write_text(json.dumps(result, indent=2))
    worst = max(angles, key=lambda p:p['non_sliver_mm3'])
    print('Worst non-sliver door pose:', json.dumps(worst), flush=True)


if __name__ == '__main__':
    main()
