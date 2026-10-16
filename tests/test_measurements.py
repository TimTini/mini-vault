import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MeasurementContract(unittest.TestCase):
    def test_reference_contract(self):
        self.assertTrue((ROOT / 'analyze.py').exists(), 'missing reference analyzer')
        spec = importlib.util.spec_from_file_location('analyze', ROOT / 'analyze.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.inspect_reference(ROOT / 'reference/MINI-VAULT.stl')
        self.assertEqual(result['sha256'], 'c851ba43c400c378f7867406aabe91f46b6700cfa4c6eae54b21f1a133ed0a94')
        self.assertEqual(len(result['parts']), 22)
        self.assertEqual(result['units'], 'mm')
        self.assertEqual(result['parts'][11]['size'], [142.0, 100.0, 84.0])
        self.assertEqual(module.measure_parts([None]*22)['wall_thickness'],1.8)
        for ids in ((4, 20, 21), (17, 18, 19)):
            ys = sorted(result['parts'][i]['bounds'][0][1] for i in ids)
            self.assertAlmostEqual(ys[1] - ys[0], 5)
            self.assertAlmostEqual(ys[2] - ys[1], 5)


if __name__ == '__main__':
    unittest.main()
