"""Verify the current 150 mm preset and its delivered print geometry."""
import hashlib
import json
import unittest

import numpy as np
import trimesh

from exporter import ROOT, source_hashes


class Print150(unittest.TestCase):
    def test_preset_retains_current_wall_door_and_texture(self):
        presets = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']
        expected = dict(presets['200 - scale 1'], body_width='150', body_depth='150', body_height='150')
        self.assertEqual(presets['150 - scale 1'], expected)

    @unittest.skipUnless((ROOT/'exports/mini-vault-150-scale-1-print.stl').exists(), 'requires 150 export')
    def test_delivered_wall_floor_door_and_unscaled_mechanism(self):
        directory = ROOT/'work/rendered-parts/scale-100-150'
        housing = trimesh.load_mesh(directory/'housing.stl')
        np.testing.assert_allclose(housing.extents, [150]*3, atol=.02)
        for direction, axis, expected in [([1,0,0],0,[39,41.4]),
                                           ([-1,0,0],0,[-107.4,-105]),
                                           ([0,0,1],2,[72,74.4]),
                                           ([0,0,-1],2,[-74.4,-72]),
                                           ([0,1,0],1,[140,142])]:
            hits, _, _ = housing.ray.intersects_location([[-33,80,0]], [direction], multiple_hits=True)
            np.testing.assert_allclose(sorted(hits[:,axis]), expected, atol=.01)
        door = trimesh.load_mesh(directory/'door.stl')
        for origin,direction,axis,expected in [
            ([-33,80,9.7],[1,0,0],0,[39,41.7]),
            ([-33,80,9.7],[-1,0,0],0,[-107.7,-105]),
            ([-23.3,80,0],[0,0,1],2,[72,74.7]),
            ([-23.3,80,0],[0,0,-1],2,[-74.7,-72]),
        ]:
            hits, _, _ = housing.ray.intersects_location([origin], [direction], multiple_hits=True)
            np.testing.assert_allclose(sorted(hits[:,axis]), expected, atol=.01)
        hits, _, _ = door.ray.intersects_location([[-70,-20,50]], [[0,1,0]], multiple_hits=True)
        np.testing.assert_allclose(sorted(hits[:,1]), [-7.4,-5], atol=.005)
        for name in ['shaft','dial','knob','retaining_ring','disk_1','disk_2','disk_3']:
            current = trimesh.load_mesh(directory/f'{name}.stl')
            control = trimesh.load_mesh(ROOT/f'work/rendered-parts/scale-100-200/{name}.stl')
            self.assertTrue(current.is_volume)
            np.testing.assert_allclose(current.bounds, control.bounds, atol=.005)
            self.assertAlmostEqual(current.volume, control.volume, delta=.005)

    @unittest.skipUnless((ROOT/'exports/mini-vault-150-scale-1-dial-black-white.3mf').exists(), 'requires colored 150 export')
    def test_colored_dial_is_bound_to_150_and_current_relief(self):
        output = ROOT/'exports/mini-vault-150-scale-1-dial-black-white.3mf'
        report = json.loads(output.with_suffix('.verification.json').read_text())
        self.assertEqual(report['sha256'], hashlib.sha256(output.read_bytes()).hexdigest())
        self.assertEqual(report['source_hashes'], source_hashes())
        self.assertEqual(report['parameters'], json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']['150 - scale 1'])
        self.assertTrue(report['union_matches_source'])
        self.assertEqual(len(report['parts']), 2)
        self.assertEqual([p['components'] for p in report['parts']], [1,28])
        self.assertAlmostEqual(report['marks_thickness_mm'], .4, delta=.00001)


if __name__ == '__main__':
    unittest.main()
