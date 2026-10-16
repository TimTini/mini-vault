"""Full baseline geometry acceptance, not source-text assertions."""
import unittest
import json
import hashlib
from pathlib import Path

from exporter import source_hashes

ROOT=Path(__file__).resolve().parents[1]


class GeometryContract(unittest.TestCase):
    def test_baseline_geometry_acceptance(self):
        # Reports come from actual renders and mesh/section measurements in audit.py.
        path=ROOT/'work/audit-all-baseline.json'
        self.assertTrue(path.exists(),'missing full baseline report')
        report=json.loads(path.read_text())
        self.assertIn('source_hashes',report,'report lacks profile dependency provenance')
        self.assertTrue({'analyze.py','profile_builder.py'}.issubset(report['source_hashes']),
                        'audit helper dependencies are missing from provenance')
        expected_sources=source_hashes()
        self.assertEqual(set(report['source_hashes']),set(expected_sources),
                         'report source dependency keyset is stale')
        reference=ROOT/'reference/MINI-VAULT.stl'
        self.assertEqual(report.get('reference_hash'),hashlib.sha256(reference.read_bytes()).hexdigest(),
                         'reference geometry changed after audit')
        for file,expected in report['source_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/file).read_bytes()).hexdigest(),expected,
                             f'stale source: {file}')
        parts=report['parts']
        self.assertEqual(len(parts),22)
        for part in parts:
            with self.subTest(part=part['name']):
                self.assertEqual(part['status'],'passed')
                self.assertTrue(part['is_volume'])
                self.assertLessEqual(part['bounds_error'],0.1)
                self.assertLessEqual(max(part['surface']['p95']),0.1)
                self.assertLessEqual(max(part['surface']['maximum']),0.25)
                output=ROOT/'exports/baseline'/f"{part['name']}.stl"
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(),part['output_hash'],
                                 'output changed after audit')


if __name__=='__main__':
    unittest.main()
