"""Check the eight unnumbered ticks against the actual rendered relief."""
import os
import unittest

import numpy as np
import trimesh

from exporter import ROOT, render_part


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class DialTicks(unittest.TestCase):
    def test_unnumbered_ticks_reach_number_row_without_changing_other_ticks(self):
        path = render_part('dial', {'door_plate_thickness': 2.4},
                           ROOT/'work/dial-ticks/candidate.stl', os.environ['MINI_VAULT_OPENSCAD'])
        mesh = trimesh.load_mesh(path)
        self.assertTrue(mesh.is_volume)
        self.assertEqual(len(mesh.split()), 1)
        # Probe normal to the face: raised marks start at Y=-14;
        # the unchanged body surface is Y=-13.6.
        def front(radius, angle):
            a = np.deg2rad(angle)
            hits, _, _ = mesh.ray.intersects_location(
                [[radius*np.cos(a), -20, radius*np.sin(a)]], [[0, 1, 0]], multiple_hits=True)
            return float(hits[:, 1].min())

        for angle in np.arange(22.5, 360, 45):
            with self.subTest(angle=angle):
                self.assertAlmostEqual(front(18.4, angle), -14, delta=.005)
                self.assertAlmostEqual(front(18.6, angle), -13.6, delta=.005)
                self.assertAlmostEqual(front(8.8, angle), -13.6, delta=.005)
                # Width stays 1 mm, including near the new outer tip.
                self.assertAlmostEqual(front(18, angle+np.rad2deg(np.arctan(.6/18))), -13.6, delta=.005)
        for angle in range(0, 360, 45):
            self.assertAlmostEqual(front(11, angle), -14, delta=.005)
            self.assertAlmostEqual(front(12.5, angle), -13.6, delta=.005)
        np.testing.assert_allclose(mesh.extents, [42, 6.4, 41.988094], atol=.01)


if __name__ == '__main__':
    unittest.main()
