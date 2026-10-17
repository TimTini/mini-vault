"""The door rear must remain editable feature CSG and export nondegenerate triangles."""
import json
import os
import unittest

import numpy as np
import trimesh
from exporter import ROOT, render_part


class DoorFeatureSource(unittest.TestCase):
    def test_measured_stack_is_reference_only(self):
        self.assertFalse('include <profiles/door.scad>' in (ROOT/'mini-vault.scad').read_text())
        self.assertFalse('profile_0' in (ROOT/'geometry/door.scad').read_text())


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class DoorFeatureMesh(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = render_part('door', {}, ROOT/'work/door-feature-rebuild/test-default.stl',
                               os.environ['MINI_VAULT_OPENSCAD'])

    def test_direct_mesh_budget(self):
        report = json.loads(self.path.with_suffix('.export.json').read_text())
        self.assertLess(report['indexed_faces'], 30000)

    def test_no_degenerate_export_triangles(self):
        mesh = trimesh.load_mesh(self.path, process=False)
        self.assertEqual(int((mesh.area_faces == 0).sum()), 0)
        indexed = trimesh.load_mesh(json.loads(self.path.with_suffix('.export.json').read_text())['source'],
                                    process=False)
        self.assertEqual(int((indexed.area_faces == 0).sum()), 0)
        self.assertTrue(trimesh.load_mesh(self.path).is_volume)

    def test_saved_presets_and_mechanism_interfaces(self):
        cases = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']
        cases['mechanism'] = dict(shaft_stem_diameter=5.1, disk_pitch=5.5)
        cases['combined'] = dict(cases['220 - scale 1.5'], link_web_thickness=2.4,
                                 hinge_socket_root_thickness=2.6)
        for index, (name, values) in enumerate(cases.items()):
            with self.subTest(preset=name):
                parameters = {k: float(v) for k, v in values.items()}
                scale = parameters.get('size_scale', 1)
                path = render_part('door', parameters, ROOT/f'work/door-feature-tests/preset-{index}.stl',
                                   os.environ['MINI_VAULT_OPENSCAD'])
                metadata = json.loads(path.with_suffix('.export.json').read_text())
                mesh = trimesh.load_mesh(path)
                self.assertLess(metadata['indexed_faces'], 30000)
                self.assertTrue(mesh.is_volume)
                self.assertEqual(len(mesh.split()), 1)
                for source in [path, metadata['source']]:
                    raw = trimesh.load_mesh(source, process=False)
                    self.assertEqual(int((raw.area_faces == 0).sum()), 0)
                contours = mesh.section([0, 1, 0], [0, -4.5*scale, 0]).discrete
                bore = min((p for p in contours if np.linalg.norm((p.min(0)+p.max(0))[[0, 2]]) < .01),
                           key=lambda p: np.ptp(p[:, 0]))
                expected = parameters.get('shaft_stem_diameter', 5)*scale + .2
                self.assertAlmostEqual(float(np.ptp(bore[:, 0])), expected, delta=.005)
                self.assertAlmostEqual(mesh.bounds[1, 1],
                    (13+2*(parameters.get('disk_pitch', 5)-5))*scale, delta=.005)
                points, _, _ = mesh.ray.intersects_location([[-34*scale, -3*scale, 0]],
                                                           [[0, 0, 1]], multiple_hits=True)
                inner = min(p[2] for p in points if p[2] > 0)
                web = parameters.get('link_web_thickness', 1.6)
                self.assertAlmostEqual(inner, (4+(web-1.6)/2)*scale+.2, delta=.01)


if __name__ == '__main__':
    unittest.main()
