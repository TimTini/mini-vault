"""Production housing envelopes, sections and retained default reference fidelity."""
import os
import unittest
import numpy as np
import trimesh
from exporter import ROOT, render_part
from audit import check_baseline

@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class NativeHousing(unittest.TestCase):
    def test_default_and_minimum_shell_preserve_interfaces(self):
        for depth in [100,28.5]:
            path=render_part('housing',dict(body_depth=depth),ROOT/f'work/native-housing/production-{depth}.stl',os.environ['MINI_VAULT_OPENSCAD'])
            mesh=trimesh.load_mesh(path)
            self.assertTrue(mesh.is_volume)
            self.assertEqual(len(mesh.split()),1)
            np.testing.assert_allclose(mesh.extents,[142,depth,84],atol=.02)
            if depth==100:
                report=check_baseline(11,path)
                self.assertEqual(report['status'],'passed',report)
    def test_main_wall_and_front_lip_have_separate_dimensions(self):
        path=render_part('housing',dict(wall_thickness=2.4),ROOT/'work/native-housing/production-wall.stl',os.environ['MINI_VAULT_OPENSCAD'])
        mesh=trimesh.load_mesh(path)
        for y,expected in [(12,1.8),(40,2.4)]:
            contours=sorted(mesh.section([0,1,0],[0,y,0]).discrete,key=lambda p:np.ptp(p[:,0]))
            self.assertAlmostEqual(contours[-1][:,0].max()-contours[0][:,0].max(),expected,delta=.02)
