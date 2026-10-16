"""Check rendered default assembly pins against baseline mating geometry."""
import hashlib
import json
import math
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]


def solid(mesh):
    result = mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                 np.asarray(mesh.faces, dtype=np.uint64)))
    assert result.status() == mf.Error.NoError
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline = {p.stem: trimesh.load_mesh(p) for p in (ROOT / 'exports/baseline').glob('*.stl')
                if not p.stem.startswith('fastener')}
    others = {name: solid(mesh) for name, mesh in baseline.items()}
    records = []
    pins = []
    for index, (part, hole) in enumerate(zip([2, 3, 5], [7, 3, 12])):
        path = ROOT / 'work' / f'assembly-pin-{part}.off'
        mesh = trimesh.load_mesh(path, process=False)
        assert mesh.is_volume
        angle = math.radians(22.5 * (hole - 7))
        center = np.array([-.028609 + 13.5 * math.cos(angle), 13.5 * math.sin(angle)])
        front = -2 + index * 5
        # Author video 0:25/0:35: the round head is on the rear disk face.
        head_section = mesh.section([0, 1, 0], [0, front + 3, 0])
        head = head_section.discrete[0][:, [0, 2]]
        head_radius = float(np.linalg.norm(head - center, axis=1).max())
        assert head_radius > 3.3, 'pin head must face the rear/interior, as in author video'
        np.testing.assert_allclose(mesh.bounds[:, 1], [front - 2, front + 4], atol=.001)
        section = mesh.section([0, 1, 0], [0, front + .5, 0])
        shank = section.discrete[0][:, [0, 2]]
        axis_error = float(np.linalg.norm((shank.min(axis=0) + shank.max(axis=0)) / 2 - center))
        assert axis_error < .001
        disk = baseline[f'disk_{index + 1}'].section([0, 1, 0], [0, front + .5, 0])
        contours = [line[:, [0, 2]] for line in disk.discrete]
        mating = min(contours, key=lambda line: np.linalg.norm(line.mean(axis=0) - center))
        clearance = float(np.linalg.norm(mating - center, axis=1).min()
                          - np.linalg.norm(shank - center, axis=1).max())
        assert clearance > .025
        pin = solid(mesh)
        overlaps = {name: float((pin ^ body).volume()) for name, body in others.items()}
        assert max(overlaps.values()) < .0001, overlaps
        for previous in pins:
            assert abs((pin ^ previous).volume()) < .0001
        pins.append(pin)
        records.append(dict(part=part, hole=hole, front_y=front, axis_error_mm=axis_error,
                            head_radius_on_rear_mm=head_radius,
                            sampled_radial_clearance_mm=clearance, is_volume=True,
                            intersection_mm3=overlaps, off_sha256=sha(path)))
    report = dict(scope='default pin_holes=[7,3,12], baseline dimensions only',
                  source_sha256=sha(ROOT / 'mini-vault.scad'), pins=records,
                  baseline_hashes={p.name: sha(p) for p in (ROOT / 'exports/baseline').glob('*.stl')},
                  orientation_reference='https://www.youtube.com/watch?v=2BFG1QkyP0Q&t=35s',
                  physical_fit='not_run', motion='not_run', self_intersections='not_run')
    (ROOT / 'work/assembly-placement-verification.json').write_text(json.dumps(report, indent=2))
    print('3 pins: axis, head seat, radial clearance and pair intersections passed')


if __name__ == '__main__':
    main()
