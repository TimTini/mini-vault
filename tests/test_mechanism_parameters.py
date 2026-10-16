import os
import unittest
import numpy as np
import trimesh
from exporter import ROOT,render_part


class MechanismParameters(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'),'set MINI_VAULT_OPENSCAD for render regression')
    def test_knob_bore_follows_shaft(self):
        path=render_part('knob',dict(disk_pitch=5.5,shaft_stem_diameter=5.1),
                         ROOT/'work/regression-knob.stl',os.environ['MINI_VAULT_OPENSCAD'])
        mesh=trimesh.load_mesh(path)
        loops=mesh.section([0,1,0],[0,15,0]).discrete
        hole=min(loops,key=lambda p:np.ptp(p[:,0]))
        self.assertAlmostEqual(float(np.ptp(hole[:,0])),5.1,delta=0.01)


if __name__=='__main__':
    unittest.main()
