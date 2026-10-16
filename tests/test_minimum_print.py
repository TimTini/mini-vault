import os
import unittest
import numpy as np
import trimesh
from exporter import ROOT, render_part


class MinimumPrint(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
    def test_shallow_housing_preserves_front_and_clears_shaft(self):
        output=ROOT/'work/minimum-regression/housing.stl'
        render_part('housing',dict(body_depth=28.5),output,os.environ['MINI_VAULT_OPENSCAD'])
        mesh=trimesh.load_mesh(output)
        self.assertTrue(mesh.is_volume)
        np.testing.assert_allclose(mesh.extents,[142,28.5,84],atol=0.02)
        for y in [12,16]:
            loops=sorted(mesh.section([0,1,0],[0,y,0]).discrete,key=lambda p:np.ptp(p[:,0]))
            self.assertEqual(len(loops),2)
            self.assertAlmostEqual(loops[-1][:,0].max()-loops[0][:,0].max(),1.8,delta=0.02)
        self.assertFalse(mesh.contains([[0,18,0],[0,18.49,0]]).any())
        self.assertTrue(mesh.contains([[0,18.51,0],[0,20,0]]).all())


if __name__=='__main__':
    unittest.main()
