import os
import subprocess
import unittest

import trimesh

from audit import check_baseline
from exporter import ROOT


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class NativeLinkCover(unittest.TestCase):
    def test_continuous_bevels_preserve_reference_and_reduce_direct_faces(self):
        for index, name in [(13, 'link'), (16, 'latch_cover')]:
            with self.subTest(part=name):
                path = ROOT/'work/native-link-cover'/f'{name}.stl'
                path.parent.mkdir(parents=True, exist_ok=True)
                result = subprocess.run([os.environ['MINI_VAULT_OPENSCAD'], '--backend', 'Manifold',
                                         '--hardwarnings', '--export-format', 'binstl', '-o', str(path),
                                         '-D', f'part="{name}"', str(ROOT/'mini-vault.scad')],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                mesh = trimesh.load_mesh(path)
                self.assertTrue(mesh.is_volume)
                self.assertEqual(len(mesh.split()), 1)
                self.assertLess(len(mesh.faces), 2000)
                report = check_baseline(index, path)
                self.assertEqual(report['status'], 'passed', report)


if __name__ == '__main__':
    unittest.main()
