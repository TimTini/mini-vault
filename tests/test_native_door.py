"""Production door reference and rear interface preservation."""
import os
import unittest
import trimesh
from exporter import ROOT,render_part
from audit import check_baseline,section_error

@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class NativeDoor(unittest.TestCase):
    def test_marker_keeps_local_size_when_body_height_changes(self):
        for size,factor in [(200,1),(220,1.5)]:
            with self.subTest(size=size,factor=factor):
                path=render_part('door',dict(body_width=size,body_depth=size,body_height=size,size_scale=factor),
                    ROOT/f'work/native-door/marker-{size}.stl',os.environ['MINI_VAULT_OPENSCAD'])
                mesh=trimesh.load_mesh(path)
                contours=mesh.section([0,1,0],[0,-6.9*factor,0]).discrete
                marker=[p for p in contours if p[:,0].max()-p[:,0].min()<2*factor and p[:,2].min()>20*factor]
                self.assertEqual(len(marker),1)
                self.assertAlmostEqual(marker[0][:,2].min(),24*factor,delta=.005)
                self.assertAlmostEqual(marker[0][:,2].max(),28*factor,delta=.005)
                self.assertAlmostEqual(marker[0][:,0].max()-marker[0][:,0].min(),factor,delta=.005)

    def test_default_panel_and_rear_features_preserve_reference(self):
        path=render_part('door',{},ROOT/'work/native-door/production-final.stl',os.environ['MINI_VAULT_OPENSCAD'])
        mesh=trimesh.load_mesh(path)
        report=check_baseline(0,path)
        self.assertEqual(report['status'],'passed',report)
        reference=trimesh.load_mesh(ROOT/'work/reference-parts/door.stl')
        for y in [-6,-4.5,-3,-1,.5,2.5,3.5,4.5,10]:
            result=section_error(reference,mesh,1,y)
            self.assertEqual(result['status'],'passed',result)
