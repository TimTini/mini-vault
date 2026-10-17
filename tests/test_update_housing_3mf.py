"""Preserve Bambu project settings while replacing a housing mesh."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh

from exporter import ROOT

spec = importlib.util.spec_from_file_location('update_3mf', ROOT/'work/update-housing-3mf.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class UpdateHousing3MF(unittest.TestCase):
    def test_replaces_mesh_preserving_placement_settings_and_face_properties(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            old = trimesh.creation.box(extents=[10,20,30])
            vertices = ''.join('<vertex x="%s" y="%s" z="%s"/>' % tuple(v) for v in old.vertices)
            triangles = ''.join('<triangle v1="%s" v2="%s" v3="%s" face_property="3"/>' % tuple(f) for f in old.faces)
            model = ('<model xmlns="'+update.CORE+'"><resources><object id="1"><mesh><vertices>'+vertices+'</vertices><triangles>'+triangles+'</triangles></mesh></object></resources></model>').encode()
            main = ('<model xmlns="'+update.CORE+'" xmlns:p="'+update.PRODUCTION+'"><resources><object id="2"><components><component objectid="1" p:path="/3D/Objects/housing.model" transform="1 0 0 0 1 0 0 0 1 50 60 70"/></components></object></resources></model>').encode()
            config = b'<config><object id="2"><metadata key="extruder" value="2"/><metadata face_count="12"/><part id="1"><metadata key="matrix" value="unchanged"/><mesh_stat face_count="12"/></part></object></config>'
            original = folder/'original.3mf'
            with zipfile.ZipFile(original,'w') as archive:
                for name,data in [('3D/3dmodel.model',main),('3D/Objects/housing.model',model),('Metadata/model_settings.config',config),('Metadata/project_settings.config',b'keep printer and filaments'),('Metadata/plate_1.png',b'keep thumbnail')]:
                    archive.writestr(name,data)
            source = old.subdivide()
            source.apply_translation(-source.bounds[0])
            stl = folder/'housing.stl'
            source.export(stl)
            output = folder/'updated.3mf'
            report = update.update_project(original,stl,output)
            self.assertEqual(report['changed_entries'], ['3D/Objects/housing.model','Metadata/model_settings.config'])
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(archive.read('3D/3dmodel.model'),main)
                self.assertEqual(archive.read('Metadata/project_settings.config'),b'keep printer and filaments')
                self.assertEqual(archive.read('Metadata/plate_1.png'),b'keep thumbnail')
                obj = ET.fromstring(archive.read('3D/Objects/housing.model')).find('.//m:object',update.NS)
                mesh = update.object_mesh(obj)
                np.testing.assert_allclose(mesh.bounds,old.bounds,atol=1e-6)
                self.assertTrue(mesh.is_volume)
                faces = obj.findall('.//m:triangle',update.NS)
                self.assertEqual(len(faces),48)
                self.assertTrue(all(f.get('face_property')=='3' for f in faces))
                cfg = ET.fromstring(archive.read('Metadata/model_settings.config'))
                self.assertEqual(cfg.find('.//mesh_stat').get('face_count'),'48')
                self.assertEqual(cfg.find(".//metadata[@key='extruder']").get('value'),'2')
            with self.assertRaises(FileExistsError):
                update.update_project(original,stl,output)


if __name__ == '__main__':
    unittest.main()
