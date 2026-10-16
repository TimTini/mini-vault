import os
import unittest
import numpy as np
import trimesh
from exporter import ROOT,render_part


class WallParameters(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'),'set MINI_VAULT_OPENSCAD for render regression')
    def test_front_lip_stays_measured_when_main_wall_changes(self):
        path=render_part('housing',dict(wall_thickness=2.4),ROOT/'work/regression-wall.stl',
                         os.environ['MINI_VAULT_OPENSCAD'])
        mesh=trimesh.load_mesh(path)
        for y,expected in [(12,1.8),(20,2.4)]:
            with self.subTest(y=y):
                loops=sorted(mesh.section([0,1,0],[0,y,0]).discrete,key=lambda p:np.ptp(p[:,0]))
                self.assertAlmostEqual(float(loops[-1][:,0].max()-loops[0][:,0].max()),expected,delta=0.02)


if __name__=='__main__':
    unittest.main()
