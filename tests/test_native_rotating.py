import os
import subprocess
import unittest

import numpy as np
import trimesh

from exporter import ROOT


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class NativeRotating(unittest.TestCase):
    def test_rotating_features_export_without_axial_staircases(self):
        expected = {'shaft': [[-7, -13.2, -7], [7, 18, 7]],
                    'dial': [[-21, -13.6, -20.994047], [21, -7.2, 20.994047]]}
        for name in expected:
            with self.subTest(part=name):
                path = ROOT/'work/native-rotating'/f'{name}.stl'
                path.parent.mkdir(parents=True, exist_ok=True)
                result = subprocess.run([os.environ['MINI_VAULT_OPENSCAD'], '--backend', 'Manifold',
                                         '--hardwarnings', '--export-format', 'binstl', '-o', str(path),
                                         '-D', f'part="{name}"', str(ROOT/'mini-vault.scad')],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                mesh = trimesh.load_mesh(path)
                self.assertTrue(mesh.is_volume)
                self.assertEqual(len(mesh.split()), 1)
                self.assertLess(len(mesh.faces), 15000)
                np.testing.assert_allclose(mesh.bounds, expected[name], atol=.01)
                if name == 'shaft':
                    section = np.concatenate(mesh.section([0, 1, 0], [0, 0, 0]).discrete)
                    self.assertAlmostEqual(float(np.ptp(section[:, 0])), 5, delta=.005)
                else:
                    for y, radius in [(-9.1, 19.9), (-8, 18.8), (-7.3, 18.1)]:
                        section = np.concatenate(mesh.section([0, 1, 0], [0, y, 0]).discrete)
                        self.assertAlmostEqual(float(np.max(np.linalg.norm(section[:, [0, 2]], axis=1))),
                                               radius, delta=.01)


if __name__ == '__main__':
    unittest.main()
