"""Read the actual exported 3MF, including the raised-only color split."""
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
import zipfile

import trimesh

from exporter import ROOT,source_hashes


OUTPUT=ROOT/'exports/mini-vault-200-scale-1-dial-black-white.3mf'
NS={'c':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}


@unittest.skipUnless(OUTPUT.exists(),'requires local colored dial export')
class ColoredDial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(OUTPUT) as archive:
            cls.model=ET.fromstring(archive.read('3D/3dmodel.model'))
            cls.config=ET.fromstring(archive.read('Metadata/model_settings.config'))
        cls.meshes=[]
        for data in cls.model.findall('c:resources/c:object/c:mesh',NS):
            vertices=[[float(v.get(a)) for a in 'xyz'] for v in data.find('c:vertices',NS)]
            faces=[[int(t.get(a)) for a in ['v1','v2','v3']] for t in data.find('c:triangles',NS)]
            cls.meshes.append(trimesh.Trimesh(vertices,faces,process=False))

    def test_marks_are_only_point_two_mm_relief(self):
        self.assertEqual(len(self.meshes),2)
        self.assertAlmostEqual(self.meshes[1].extents[2],.2,delta=.00001)
        # Digits and all 16 ticks remain separate islands, including long ticks.
        self.assertEqual(len(self.meshes[1].split()),28)
        for mesh in self.meshes:
            self.assertTrue(mesh.is_volume)

    def test_one_assembly_two_assignable_parts(self):
        self.assertEqual(len(self.model.findall('c:build/c:item',NS)),1)
        self.assertEqual(len(self.model.findall('c:resources/c:object/c:components/c:component',NS)),2)
        parts=self.config.findall('object/part')
        self.assertEqual(len(parts),2)
        self.assertEqual([p.find("metadata[@key='extruder']").get('value') for p in parts],['1','2'])

    def test_export_is_bound_to_current_200_source(self):
        report=json.loads(OUTPUT.with_suffix('.verification.json').read_text())
        self.assertEqual(report['source_hashes'],source_hashes())
        self.assertEqual(report['sha256'],hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
        for field,path in [('preset_sha256','mini-vault.json'),
                           ('source_manifest_sha256','exports/mini-vault-200-scale-1-print.verification.json'),
                           ('exporter_sha256','work/export-colored-dial.py')]:
            self.assertEqual(report[field],hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
        self.assertEqual(report['parameters'],json.loads((ROOT/'mini-vault.json').read_text())['parameterSets']['200 - scale 1'])
        self.assertTrue(report['union_matches_source'])
        self.assertLess(report['overlap_mm3'],1e-7)


if __name__=='__main__':
    unittest.main()
