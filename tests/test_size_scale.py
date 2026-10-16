import hashlib
import json
import unittest

import trimesh

from exporter import ROOT, source_hashes


class SizeScale(unittest.TestCase):
    def test_scaled_preset_keeps_measured_fit_gaps_and_current_exports(self):
        preset = json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']
        self.assertEqual(preset['Default']['size_scale'], '1')
        target = preset['220 - scale 1.5']
        self.assertEqual(target['size_scale'], '1.5')
        self.assertEqual([target['body_'+a] for a in ['width', 'depth', 'height']], ['220']*3)
        report = json.loads((ROOT/'work/size-scale-verification.json').read_text())
        self.assertEqual(report['source_hashes'], source_hashes())
        self.assertEqual(report['preset_hash'], hashlib.sha256((ROOT/'mini-vault.json').read_bytes()).hexdigest())
        self.assertEqual(report['increased_contacts_mm3'], {})
        self.assertEqual(len(report['parts']), 22)
        for name, record in report['parts'].items():
            path = ROOT/'work/rendered-parts/scale-150-220'/f'{name}.stl'
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record['sha256'])
            self.assertEqual(record['components'], 1)
        for key, gap in [('door_shaft_radial_gap_mm', .1), ('hinge_radial_gap_mm', .1),
                         ('dial_panel_axial_gap_mm', .2), ('disk_collar_radial_gap_mm', .2)]:
            self.assertAlmostEqual(report['measurements'][key], gap, delta=.005)

    def test_print_stls_match_current_source_and_keep_parts_separate(self):
        for stem in ['mini-vault-200-scale-1-print','mini-vault-220-scale-1.5-print']:
            path = ROOT/'exports'/f'{stem}.stl'
            metadata = json.loads(path.with_suffix('.verification.json').read_text())
            self.assertEqual(metadata['source_hashes'], source_hashes())
            self.assertEqual(metadata['components'],22)
            parts = trimesh.load_mesh(path).split(only_watertight=False)
            self.assertEqual(len(parts),22)
            self.assertTrue(all(p.is_volume for p in parts))


if __name__ == '__main__':
    unittest.main()
