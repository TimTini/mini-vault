"""Measure the saved 1.5/220 preset and retain actual assembly contacts."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyze import NAMES
from exporter import source_hashes

spec = importlib.util.spec_from_file_location('local_check', ROOT/'work/verify-local-220.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contours(mesh, axis, value):
    origin = np.zeros(3)
    origin[axis] = value
    return mesh.section(np.eye(3)[axis], origin).discrete


def place(meshes, scale):
    result = {n: m.copy() for n, m in meshes.items()}
    for i, hole in enumerate([7, 3, 12]):
        m = result[f'fastener_{i+1}']
        m.apply_translation(-scale*np.array([55, 10+[0, 9.4, 18.3][i], 6]))
        m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2, [1, 0, 0]))
        angle = np.deg2rad(22.5*(hole-7))
        m.apply_translation(scale*np.array([-.028609+13.5*np.cos(angle), i*5, 13.5*np.sin(angle)]))
    return result


def positive_z_hit(mesh, origin):
    points, _, _ = mesh.ray.intersects_location([origin], [[0, 0, 1]], multiple_hits=True)
    return float(min(p[2] for p in points if p[2] > origin[2]+1e-6))


def main():
    scale = 1.5
    directory = ROOT/'work/rendered-parts/scale-150-220'
    meshes = {n: trimesh.load_mesh(directory/f'{n}.stl') for n in NAMES}
    sources = source_hashes()
    # Verify every mesh was generated from this exact source state.
    for n, m in meshes.items():
        metadata = json.loads((directory/f'{n}.export.json').read_text())
        assert metadata['source_hashes'] == sources, f'stale render: {n}'
        assert m.is_volume and len(m.split()) == 1, (n, [(c.volume, len(c.faces)) for c in m.split()])
    measured = {}
    np.testing.assert_allclose(meshes['housing'].extents, [220]*3, atol=.02)
    measured['housing_extents_mm'] = meshes['housing'].extents.tolist()
    stem = contours(meshes['shaft'], 1, 0)[0]
    stem_d = float(np.ptp(stem[:, 0]))
    bore = min(contours(meshes['door'], 1, -9), key=lambda p: np.ptp(p[:, 0]))
    measured['shaft_diameter_mm'] = stem_d
    measured['door_shaft_radial_gap_mm'] = (float(np.ptp(bore[:, 0]))-stem_d)/2
    socket = min(contours(meshes['hinge_socket_top'], 2, 96), key=lambda p: np.ptp(p[:, 0]))
    journal = contours(meshes['hinge_leaf_top'], 2, 96)[0]
    measured['hinge_radial_gap_mm'] = (float(np.ptp(socket[:, 0]))-float(np.ptp(journal[:, 0])))/2
    measured['dial_panel_axial_gap_mm'] = float(meshes['door'].bounds[0, 1]-meshes['dial'].bounds[1, 1])
    pin_section = contours(meshes['fastener_1'], 2, 7.5)[0]
    pin_d = float(np.ptp(pin_section[:, 0]))
    disk_loops = contours(meshes['disk_1'], 1, -1.5)
    pin_hole = min(disk_loops, key=lambda p: abs(float(np.ptp(p[:, 0]))-4.756194))
    measured['pin_hole_diametral_gap_mm'] = float(np.ptp(pin_hole[:, 0]))-pin_d
    center_bore = min(disk_loops, key=lambda p: np.linalg.norm((p.min(0)+p.max(0))[[0, 2]]))
    tab = max(contours(meshes['collar_1'], 1, -1.5), key=lambda p: p[:, 0].max())
    measured['disk_collar_radial_gap_mm'] = float(np.ptp(center_bore[:, 0]))/2-float(tab[:, 0].max())
    hook = np.concatenate(contours(meshes['latch'], 0, -55))
    inner_z = np.unique(np.round(hook[:, 2], 4))
    measured['latch_slot_inner_planes_Z_mm'] = [float(z) for z in inner_z if abs(abs(z)-1.4)<.005]
    measured['link_gate_web_mm'] = float(np.ptp(np.concatenate(contours(meshes['link'], 0, -24))[:, 2]))
    measured['door_latch_radial_gap_mm'] = positive_z_hit(meshes['door'], [-51, -3, 0])-6
    measured['hinge_tongue_axial_gap_mm'] = positive_z_hit(meshes['door'], [15, 0, 97.71])-97.7
    for key, expected, tolerance in [
        ('shaft_diameter_mm', 7.5, .005), ('door_shaft_radial_gap_mm', .1, .005),
        ('hinge_radial_gap_mm', .1, .005), ('dial_panel_axial_gap_mm', .2, .005),
        ('pin_hole_diametral_gap_mm', .087612, .005), ('disk_collar_radial_gap_mm', .2, .005),
        ('link_gate_web_mm', 2.4, .005),
        ('door_latch_radial_gap_mm', .2, .01), ('hinge_tongue_axial_gap_mm', .25, .01),
    ]:
        assert abs(measured[key]-expected) <= tolerance, (key, measured[key], expected)
    assert any(abs(z-1.4)<.005 for z in inner_z) and any(abs(z+1.4)<.005 for z in inner_z), inner_z
    posed = place(meshes, scale)
    raw, significant = checks.intersections(posed)
    baseline = {n: trimesh.load_mesh(ROOT/'exports/baseline'/f'{n}.stl') for n in NAMES}
    original_raw, original_significant = checks.intersections(place(baseline, 1))
    increased = {pair: volume for pair, volume in significant.items()
                 if volume > original_significant.get(pair, 0)*scale**3+.05}
    angles = []
    for degrees in [0, 15, 30, 60, 90]:
        values = []
        for parts, factor in [(baseline, 1), (meshes, scale)]:
            door = parts['door'].copy()
            door.apply_transform(trimesh.transformations.rotation_matrix(
                np.deg2rad(degrees), [0, 0, 1], factor*np.array([20, -.5, 0])))
            value = abs(float((checks.solid(door) ^ checks.solid(parts['housing'])).volume()))
            values.append(value)
        angles.append(dict(angle_degrees=degrees, baseline_mm3=values[0], scaled_mm3=values[1]))
    report = dict(parameters=json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']['220 - scale 1.5'],
                  source_hashes=sources, preset_hash=digest(ROOT/'mini-vault.json'),
                  verifier_hash=digest(Path(__file__)), measurements=measured,
                  parts={n: dict(sha256=digest(directory/f'{n}.stl'), bounds_mm=m.bounds.tolist(),
                                 faces=len(m.faces), volume_mm3=float(m.volume), components=1)
                         for n, m in meshes.items()},
                  baseline_contacts_mm3=original_raw, candidate_contacts_mm3=raw,
                  baseline_non_sliver_contacts_mm3=original_significant,
                  candidate_non_sliver_contacts_mm3=significant, increased_contacts_mm3=increased,
                  hinge_angle_samples=angles, physical_fit='not_run', strength='not_run',
                  continuous_mechanism_motion='not_run')
    target = ROOT/'work/size-scale-verification.json'
    target.write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(measurements=measured, increased=increased, angles=angles), indent=2), flush=True)
    assert not increased, increased
    assert all(p['scaled_mm3'] <= p['baseline_mm3']*scale**3+.05 for p in angles), angles


if __name__ == '__main__':
    main()
