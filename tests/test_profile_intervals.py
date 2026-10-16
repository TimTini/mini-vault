import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class ProfileIntervals(unittest.TestCase):
    def test_housing_has_no_missing_axial_interval(self):
        text=(ROOT/'profiles/housing.scad').read_text()
        layers=json.loads(text.split('profile_11 = ',1)[1].rstrip(';\n'))
        gaps=[b[0]-a[1] for a,b in zip(layers[:-1],layers[1:])]
        self.assertLessEqual(max(gaps),1e-7,'missing profile interval creates internal caps')
        self.assertGreaterEqual(min(layer[1]-layer[0] for layer in layers),0.0005-1e-9,
                                'sub-micrometre layers collapse at STL float precision')


if __name__=='__main__':
    unittest.main()
