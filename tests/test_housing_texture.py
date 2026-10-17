"""Capsule relief adds material on four walls without cutting the base shell."""
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

    def test_four_walls_keep_three_mm_under_grooves(self):
        # The 200 shell spans X=-158..42 and Z=-100..100; groove centres at U=0.
        for origin, direction, axis, expected in [
            ([-58,100,0], [1,0,0], 0, [39,42]),
            ([-58,100,0], [-1,0,0], 0, [-158,-155]),
            ([-58,100,0], [0,0,1], 2, [97,100]),
            ([-58,100,0], [0,0,-1], 2, [-100,-97]),
        ]:
            np.testing.assert_allclose(self.hits(origin,direction,axis), expected, atol=.01)
        # Half-pitch lands add .6 mm on every side.
        for origin, direction, axis, expected in [
            ([-58,100,16], [1,0,0], 0, [39,42.6]),
            ([-58,100,16], [-1,0,0], 0, [-158.6,-155]),
            ([-42,100,0], [0,0,1], 2, [97,100.6]),
            ([-42,100,0], [0,0,-1], 2, [-100.6,-97]),
        ]:
            np.testing.assert_allclose(self.hits(origin,direction,axis), expected, atol=.01)

    def test_mounting_band_back_and_topology(self):
        np.testing.assert_allclose(self.mesh.extents,[201.2,200,201.2],atol=.02)
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
        # The relief panel starts at Y=17, preserving the specified 25 mm band.
        for y,outer in [(16.9,42),(24.9,42.6),(26,42),(175.9,42),(177,42.6),(184.1,42)]:
            with self.subTest(y=y):
                np.testing.assert_allclose(self.hits([0,y,0],[1,0,0],0),[39,outer],atol=.01)

    def test_relief_stays_in_final_mm_when_scaled(self):
        path=render_part('housing',dict(self.parameters,size_scale=1.5,body_width=220,
            body_height=220,body_depth=220,housing_texture_height=.9,housing_texture_width=24,
            housing_texture_pitch=36),ROOT/'work/housing-texture/test-scaled.stl',
            os.environ['MINI_VAULT_OPENSCAD'])
        mesh=trimesh.load_mesh(path)
        self.assertTrue(mesh.is_volume)
        np.testing.assert_allclose(mesh.extents,[221.8,220,221.8],atol=.02)

    def test_shallow_body_rejects_overlapping_capsule_ends(self):
        with self.assertRaisesRegex(RuntimeError,'protected mouth and rear margins'):
            render_part('housing',dict(self.parameters,body_depth=50),
                ROOT/'work/housing-texture/test-invalid.stl',os.environ['MINI_VAULT_OPENSCAD'])


if __name__=='__main__':
    unittest.main()
