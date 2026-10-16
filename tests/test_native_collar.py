import os
import subprocess
import unittest

import trimesh

from audit import check_baseline
from exporter import ROOT


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class NativeCollar(unittest.TestCase):
    def test_bayonet_ramp_preserves_reference_without_layer_stack(self):
        path = ROOT/'work/native-collar/collar_1.stl'
        path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([os.environ['MINI_VAULT_OPENSCAD'], '--backend', 'Manifold',
                                 '--hardwarnings', '--export-format', 'binstl', '-o', str(path),
                                 '-D', 'part="collar_1"', str(ROOT/'mini-vault.scad')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        mesh = trimesh.load_mesh(path)
        self.assertTrue(mesh.is_volume)
        self.assertEqual(len(mesh.split()), 1)
        self.assertLess(len(mesh.faces), 8000)
        report = check_baseline(17, path)
        self.assertEqual(report['status'], 'passed', report)


if __name__ == '__main__':
    unittest.main()
