"""The housing mouth is continuous feature CSG, independent of measured layers."""
import os
import unittest
import json
import numpy as np
import trimesh
from exporter import ROOT, render_part


class HousingFeatureSource(unittest.TestCase):
    def test_measured_housing_layers_are_reference_only(self):
        main = (ROOT/'mini-vault.scad').read_text()
        housing = (ROOT/'geometry/housing.scad').read_text()
        self.assertNotIn('include <profiles/housing.scad>', main)
        self.assertNotIn('profile_11', housing)


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class HousingFeatureMesh(unittest.TestCase):
    def test_direct_geometry_budget_at_original_resolution(self):
        path = render_part('housing', {}, ROOT/'work/housing-feature-rebuild/test-default.stl',
                           os.environ['MINI_VAULT_OPENSCAD'])
        report = json.loads(path.with_suffix('.export.json').read_text())
        self.assertLess(report['indexed_faces'], 20000)

    def test_saved_presets_preserve_mounting_dimensions(self):
        presets = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']
        for index, (name, values) in enumerate(presets.items()):
            with self.subTest(preset=name):
                parameters = {k: float(v) for k, v in values.items()}
                scale = parameters['size_scale']
                path = render_part('housing', parameters,
                                   ROOT/f'work/housing-feature-rebuild/test-preset-{index}.stl',
                                   os.environ['MINI_VAULT_OPENSCAD'])
                mesh = trimesh.load_mesh(path)
                self.assertTrue(mesh.is_volume)
                self.assertEqual(len(mesh.split()), 1)
                relief=2*parameters.get('housing_texture_height',.6) if parameters.get('housing_texture',0)==1 else 0
                np.testing.assert_allclose(mesh.extents,
                    [parameters['body_width']+relief, parameters['body_depth'], parameters['body_height']+relief], atol=.02)

                def hits(origin, direction, axis):
                    points, _, _ = mesh.ray.intersects_location([np.array(origin)*scale], [direction],
                                                               multiple_hits=True)
                    return sorted(points[:, axis]/scale)

                front = hits([0,12,0], [1,0,0], 0)
                rear = hits([0,40 if parameters.get('housing_texture',0)==1 else 20,0], [1,0,0], 0)
                np.testing.assert_allclose(front, [40.2,42], atol=.01)
                np.testing.assert_allclose(rear, [42-parameters['wall_thickness'],42], atol=.01)
                height_shift = (parameters['body_height']/scale-84)/2
                guide = hits([10,0,0], [0,0,1], 2)
                np.testing.assert_allclose(guide, np.array([36.2,38.1,40.2,42])+height_shift, atol=.01)
                lock = hits([-parameters['body_width']/scale,-3,20], [1,0,0], 0)
                self.assertAlmostEqual(lock[1]-lock[0], 1.8, delta=.01)


if __name__ == '__main__':
    unittest.main()
