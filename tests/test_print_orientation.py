"""Regress print faces and the unsupported neck introduced by a wider latch."""
import importlib.util
import os
import unittest

import numpy as np
import trimesh

from exporter import ROOT, render_part


def bed_area(mesh):
    bottom = mesh.bounds[0,2]
    mask = (mesh.face_normals[:,2] < -.999) & (mesh.triangles_center[:,2] < bottom+.001)
    return float(mesh.area_faces[mask].sum())


class PrintOrientation(unittest.TestCase):
    def test_wide_parts_use_broad_print_faces_instead_of_assembly_axes(self):
        spec = importlib.util.spec_from_file_location('prepare_print', ROOT/'prepare-scale-print.py')
        prepare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prepare)
        for name, minimum_area in [('dial',700),('collar_1',100),('fastener_1',30)]:
            original = trimesh.load_mesh(ROOT/f'exports/baseline/{name}.stl')
            posed, transform = prepare.orient_for_print(name, original)
            self.assertGreater(bed_area(posed), minimum_area, name)
            self.assertAlmostEqual(posed.bounds[0,2], 0, delta=1e-7)
            self.assertAlmostEqual(posed.volume, original.volume, delta=.001)
            np.testing.assert_allclose(transform[:3,:3].T @ transform[:3,:3], np.eye(3), atol=1e-12)
            self.assertAlmostEqual(np.linalg.det(transform[:3,:3]),1)

    @unittest.skipUnless(os.environ.get('MINI_VAULT_OPENSCAD'), 'requires OpenSCAD')
    def test_enlarged_latch_neck_is_backed_to_the_print_bed(self):
        path = render_part('latch', dict(body_width=200, body_depth=200, body_height=200),
            ROOT/'work/print-orientation/regression-latch.stl', os.environ['MINI_VAULT_OPENSCAD'])
        mesh = trimesh.load_mesh(path)
        transform = np.eye(4)
        transform[:3,:3] = [[1,0,0],[0,0,1],[0,-1,0]]
        mesh.apply_transform(transform)
        mesh.apply_translation(-mesh.bounds[0])
        # The grip neck formerly had 188 mm2 of horizontal underside at Z=4.
        unsupported = (mesh.face_normals[:,2] < -.999) & (mesh.triangles_center[:,2] > .05)
        self.assertLess(float(mesh.area_faces[unsupported].sum()), .001)
        self.assertAlmostEqual(mesh.extents[2],15,delta=.001)


if __name__ == '__main__':
    unittest.main()
