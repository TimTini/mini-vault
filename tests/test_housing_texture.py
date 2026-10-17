"""Capsule grooves are cut into the 3 mm shell without enlarging its envelope."""
import json
import os
import unittest

import numpy as np
import trimesh

from exporter import ROOT, render_part


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class HousingTexture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters = dict(body_width=200, body_depth=200, body_height=200,
                              wall_thickness=3, housing_texture=1)
        cls.path = render_part('housing', cls.parameters, ROOT/'work/housing-texture/test-on.stl',
                               os.environ['MINI_VAULT_OPENSCAD'])
        cls.mesh = trimesh.load_mesh(cls.path)

    def hits(self, origin, direction, axis):
        points, _, _ = self.mesh.ray.intersects_location([origin], [direction], multiple_hits=True)
        return sorted(points[:, axis])

    def test_four_walls_leave_two_point_four_mm_under_grooves(self):
        # The 200 shell spans X=-158..42 and Z=-100..100; groove centres at U=0.
        for origin, direction, axis, expected in [
            ([-58,100,0], [1,0,0], 0, [39,41.4]),
            ([-58,100,0], [-1,0,0], 0, [-157.4,-155]),
            ([-58,100,0], [0,0,1], 2, [97,99.4]),
            ([-58,100,0], [0,0,-1], 2, [-99.4,-97]),
        ]:
            np.testing.assert_allclose(self.hits(origin,direction,axis), expected, atol=.01)
        # Half-pitch lands remain at the original outer wall.
        for origin, direction, axis, expected in [
            ([-58,100,16], [1,0,0], 0, [39,42]),
            ([-58,100,16], [-1,0,0], 0, [-158,-155]),
            ([-42,100,0], [0,0,1], 2, [97,100]),
            ([-42,100,0], [0,0,-1], 2, [-100,-97]),
        ]:
            np.testing.assert_allclose(self.hits(origin,direction,axis), expected, atol=.01)

    def test_mounting_band_back_and_topology(self):
        np.testing.assert_allclose(self.mesh.extents,[200,200,200],atol=.02)
        np.testing.assert_allclose(self.hits([0,12,0],[1,0,0],0),[40.2,42],atol=.01)
        np.testing.assert_allclose(self.hits([-42,100,0],[0,1,0],1),[190,192],atol=.01)
        self.assertTrue(self.mesh.is_volume)
        self.assertEqual(len(self.mesh.split()),1)
        self.assertEqual(int((trimesh.load_mesh(self.path,process=False).area_faces==0).sum()),0)
        metadata=json.loads(self.path.with_suffix('.export.json').read_text())
        self.assertLess(metadata['indexed_faces'],50000)

    def test_disabled_option_keeps_plain_envelope(self):
        path=render_part('housing',dict(self.parameters,housing_texture=0),
                         ROOT/'work/housing-texture/test-off.stl',os.environ['MINI_VAULT_OPENSCAD'])
        np.testing.assert_allclose(trimesh.load_mesh(path).extents,[200,200,200],atol=.02)

    def test_front_groove_cutoff_and_rear_margin(self):
        # Front is Y=-8: the first groove tip is Y=25, 33 mm from the mouth.
        # The groove tips remain behind the protected front band.
        for y,outer in [(16.9,42),(24.9,42),(25.3,41.7),(26,41.4),
                        (175.7,41.7),(175.9,41.9),(177,42),(184.1,42)]:
            with self.subTest(y=y):
                np.testing.assert_allclose(self.hits([0,y,0],[1,0,0],0),[39,outer],atol=.01)

    def test_groove_edges_slope_45_degrees_on_all_four_walls(self):
        # Each .2 mm step toward the unchanged mouth edge raises the floor .2 mm.
        for u,depth in [(9.3,.6),(9.5,.5),(9.7,.3),(9.9,.1),(10.1,0)]:
            for origin,direction,axis,expected in [
                ([-58,100,u],[1,0,0],0,[39,42-depth]),
                ([-58,100,u],[-1,0,0],0,[-158+depth,-155]),
                ([-58+u,100,0],[0,0,1],2,[97,100-depth]),
                ([-58+u,100,0],[0,0,-1],2,[-100+depth,-97]),
            ]:
                with self.subTest(offset=u,direction=direction):
                    np.testing.assert_allclose(self.hits(origin,direction,axis),expected,atol=.01)

    def test_depth_stays_in_final_mm_when_scaled(self):
        path=render_part('housing',dict(self.parameters,size_scale=1.5,body_width=220,
            body_height=220,body_depth=220,housing_texture_depth=.9,housing_texture_width=24,
            housing_texture_pitch=36),ROOT/'work/housing-texture/test-scaled.stl',
            os.environ['MINI_VAULT_OPENSCAD'])
        mesh=trimesh.load_mesh(path)
        self.assertTrue(mesh.is_volume)
        np.testing.assert_allclose(mesh.extents,[220,220,220],atol=.02)
        points,_,_=mesh.ray.intersects_location([[0,100,0]],[[1,0,0]],multiple_hits=True)
        np.testing.assert_allclose(sorted(points[:,0]),[58.5,62.1],atol=.01)
        points,_,_=mesh.ray.intersects_location([[0,100,11.55]],[[1,0,0]],multiple_hits=True)
        np.testing.assert_allclose(sorted(points[:,0]),[58.5,62.55],atol=.01)

    def test_shallow_body_rejects_overlapping_capsule_ends(self):
        with self.assertRaisesRegex(RuntimeError,'protected mouth and rear margins'):
            render_part('housing',dict(self.parameters,body_depth=50),
                ROOT/'work/housing-texture/test-invalid.stl',os.environ['MINI_VAULT_OPENSCAD'])

    def test_minimum_remaining_wall_boundary(self):
        path=render_part('housing',dict(self.parameters,wall_thickness=2.4),
            ROOT/'work/housing-texture/test-min-wall.stl',os.environ['MINI_VAULT_OPENSCAD'])
        self.assertTrue(trimesh.load_mesh(path).is_volume)
        with self.assertRaisesRegex(RuntimeError,'at least 1.8 mm of wall'):
            render_part('housing',dict(self.parameters,wall_thickness=2.3),
                ROOT/'work/housing-texture/test-thin-wall.stl',os.environ['MINI_VAULT_OPENSCAD'])


if __name__=='__main__':
    unittest.main()
