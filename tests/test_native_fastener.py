import os
from pathlib import Path
import subprocess
import unittest

import numpy as np
import trimesh

from exporter import ROOT


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class NativeFastener(unittest.TestCase):
    def test_direct_export_is_compact_and_preserves_pin_interfaces(self):
        path = ROOT/'work/native-fastener/regression.stl'
        path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([os.environ['MINI_VAULT_OPENSCAD'], '--backend', 'Manifold',
                                 '--hardwarnings', '--export-format', 'binstl', '-o', str(path),
                                 '-D', 'part="fastener_1"', str(ROOT/'mini-vault.scad')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        raw = trimesh.load_mesh(path, process=False)
        mesh = trimesh.load_mesh(path)
        self.assertLess(len(raw.faces), 8000, 'native fillet revolution replaces artificial Z slices')
        self.assertTrue(mesh.is_volume)
        np.testing.assert_allclose(mesh.bounds, [[51.4, 6.4, 2], [58.6, 13.6, 8]], atol=.005)
        for z, diameter in [(3, 3.037372), (5, 3.112388), (7, 7.2)]:
            contour = np.concatenate(mesh.section([0, 0, 1], [0, 0, z]).discrete)
            self.assertAlmostEqual(float(np.ptp(contour[:, 0])), diameter, delta=.005)


if __name__ == '__main__':
    unittest.main()
