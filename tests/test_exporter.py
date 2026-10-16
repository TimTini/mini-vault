import importlib.util
import tempfile
import json
import unittest
from pathlib import Path

import trimesh

ROOT=Path(__file__).resolve().parents[1]


class ExportContract(unittest.TestCase):
    def test_indexed_export_survives_stl_precision(self):
        self.assertTrue((ROOT/'exporter.py').exists(),'missing indexed export pipeline')
        spec=importlib.util.spec_from_file_location('exporter',ROOT/'exporter.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        source=Path(json.loads((ROOT/'exports/baseline/housing.export.json').read_text())['source'])
        self.assertTrue(trimesh.load_mesh(source,process=False).is_volume)
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'housing.stl'
            result=module.export_indexed(source,output)
            self.assertTrue(trimesh.load_mesh(output).is_volume)
            self.assertEqual(result['simplification_tolerance'],0.005)


if __name__=='__main__':
    unittest.main()
