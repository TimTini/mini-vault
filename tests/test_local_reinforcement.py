import os
import hashlib
import json
import re
import unittest

import numpy as np
import trimesh
import manifold3d as mf

from exporter import ROOT, render_part


@unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
class LocalReinforcement(unittest.TestCase):
    def test_enlarged_latch_keeps_two_pockets_and_thicker_ligaments(self):
        path = render_part('latch', dict(body_width=220, body_depth=220, body_height=220,
                                        latch_pocket_inset=.8),
                           ROOT/'work/local-regression/latch-pockets.stl', os.environ['MINI_VAULT_OPENSCAD'])
        mesh = trimesh.load_mesh(path)
        contours = [p[:, [0, 2]] for p in mesh.section([0, 1, 0], [0, -2, 0]).discrete]
        self.assertEqual(len(contours), 3, 'two internal relief pockets must remain closed')
        areas = [abs((p[:-1, 0]*p[1:, 1]-p[:-1, 1]*p[1:, 0]).sum()) for p in contours]
        outer = contours.pop(int(np.argmax(areas)))
        a = outer[:-1]
        v = np.diff(outer, axis=0)
        for pocket in contours:
            d = pocket[:, None, :]-a
            t = np.clip((d*v).sum(axis=2)/np.maximum((v*v).sum(axis=1), 1e-20), 0, 1)
            distance = float(np.linalg.norm(d-t[:, :, None]*v, axis=2).min())
            self.assertGreaterEqual(distance, 2.79, '2 mm ligament plus 0.8 mm inset')

    def test_large_profile_report_matches_current_geometry(self):
        report = json.loads((ROOT/'work/local-220-verification.json').read_text())
        for file, expected in (report['source_hashes'] | report['extra_hashes']).items():
            self.assertEqual(hashlib.sha256((ROOT/file).read_bytes()).hexdigest(), expected, file)
        self.assertEqual(len(report['parts']), 22)
        self.assertEqual(report['increased_intersections_mm3'], {})
        self.assertTrue(all(not p['increased_mm3'] for p in report['hinge_angle_samples']))
        self.assertAlmostEqual(report['measurements']['socket_root_Z'], 2.6, delta=.01)
        self.assertAlmostEqual(report['measurements']['link_Z_at_X-16'], 1.6, delta=.01)
        for name, part in report['parts'].items():
            path = ROOT/f'exports/local-220/{name}.stl'
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), part['sha256'], name)

    def test_link_web_thickens_but_gate_tip_stays_measured(self):
        path = render_part('link', dict(link_web_thickness=2.4),
                           ROOT/'work/local-regression/link.stl', os.environ['MINI_VAULT_OPENSCAD'])
        mesh = trimesh.load_mesh(path)
        for x, expected in [(-30, 2.4), (-16, 1.6), (-40, 5)]:
            loops = mesh.section([1, 0, 0], [x, 0, 0]).discrete
            self.assertAlmostEqual(float(np.ptp(np.concatenate(loops)[:, 2])), expected, delta=.01)
        self.assertTrue(mesh.is_volume)
        path = render_part('latch', dict(link_web_thickness=2.4),
                           ROOT/'work/local-regression/latch-unit.stl', os.environ['MINI_VAULT_OPENSCAD'])
        latch = trimesh.load_mesh(path)
        bodies = [mf.Manifold(mf.Mesh64(m.vertices.astype(np.float64), m.faces.astype(np.uint64)))
                  for m in [mesh, latch]]
        self.assertLess(abs(float((bodies[0] ^ bodies[1]).volume())), .001,
                        'thicker link must still fit its latch slot')


class PresetCustomizerTypes(unittest.TestCase):
    def test_decimal_preset_values_keep_a_decimal_spinbox(self):
        preset = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']['220 - local reinforcement']
        source = (ROOT/'mini-vault.scad').read_text()
        for name, raw in preset.items():
            if '.' not in raw:
                continue
            match = re.search(rf'^{re.escape(name)} = ([0-9.]+);\s*(//.*)?$', source, re.M)
            self.assertIsNotNone(match, name)
            default, hint = match.group(1), match.group(2) or ''
            # 2 and 2.0 are integer spinboxes. A preset such as 2.8 is then rounded to 3.
            written_as_decimal = '.' in default and not re.fullmatch(r'\d+\.0+', default)
            step_allows_decimal = re.search(r'//\s*\.\d+', hint) is not None
            self.assertTrue(written_as_decimal or step_allows_decimal, name)


if __name__ == '__main__':
    unittest.main()
