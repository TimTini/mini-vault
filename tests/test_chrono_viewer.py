"""Replay tests require only stdlib; no graphics device or CAD exports."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('chrono_viewer', ROOT/'work/chrono-viewer.py')


class ChronoViewer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path(SPEC.origin).exists():
            cls.viewer = None
            return
        cls.viewer = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(cls.viewer)

    def setUp(self):
        if self.viewer is None and self._testMethodName != 'test_viewer_exists':
            self.skipTest('Viewer implementation missing')

    def test_viewer_exists(self):
        self.assertIsNotNone(self.viewer, 'Chrono pose replay viewer has not been implemented')

    def test_pause_scrub_mode_switch_and_play_from_end(self):
        playback = self.viewer.Playback({'door': 361, 'slider': 121})
        playback.toggle()
        playback.advance(3)
        self.assertEqual(playback.index, 180)
        playback.seek(73)
        self.assertFalse(playback.playing)
        playback.advance(10)
        self.assertEqual(playback.index, 73)
        playback.select('slider')
        self.assertEqual(playback.index, 0)
        playback.toggle()
        playback.advance(6)
        self.assertEqual(playback.index, 120)
        self.assertFalse(playback.playing)
        playback.toggle()
        self.assertEqual(playback.index, 0)
        playback.advance(3)
        self.assertEqual(playback.index, 60)
        with self.assertRaises(ValueError):
            playback.seek(121)

    def test_motion_composition_and_pin_seating(self):
        v = self.viewer
        identity = v.base_matrix('door')
        self.assertEqual(v.pose_matrix('slider', 'door', identity), identity)
        shift = copy.deepcopy(identity)
        shift[0][3] = -8
        self.assertEqual(v.pose_matrix('slider', 'latch', shift)[0][3], -8)
        self.assertEqual(v.pose_matrix('slider', 'housing', shift), identity)
        pin = v.base_matrix('fastener_1')
        # Pin head underside from the exported source seats on disk 1 rear face.
        point = [55, 10, 6, 1]
        placed = [sum(pin[i][j]*point[j] for j in range(4)) for i in range(4)]
        for actual, expected in zip(placed, [13.471391, 0, 0, 1]):
            self.assertAlmostEqual(actual, expected, places=6)
        rotated = [[0, -1, 0, 19.5], [1, 0, 0, -20.5], [0, 0, 1, 0], [0, 0, 0, 1]]
        self.assertEqual(v.pose_matrix('door', 'hinge_leaf_top', rotated), identity)
        self.assertEqual(v.pose_matrix('door', 'door', rotated), rotated)

    def test_inputs_reject_stale_mesh_source_and_bad_pose(self):
        v = self.viewer
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def write(relative, value):
                path = root/relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value)
                return hashlib.sha256(path.read_bytes()).hexdigest()
            source_hash = write('mini-vault.scad', 'cube(1);')
            script_hash = write('work/chrono-housing-check.py', '# fixture')
            parameters = {'body_width': '200', 'body_depth': '200', 'body_height': '200', 'size_scale': '1'}
            preset_hash = write('mini-vault.json', json.dumps({'parameterSets': {'200 - scale 1': parameters}}))
            names = ['door', 'hinge_socket_top', 'fastener_1', 'fastener_2', 'disk_1',
                     'fastener_3', 'hinge_leaf_top', 'latch', 'shaft', 'dial', 'retaining_ring',
                     'housing', 'knob', 'link', 'hinge_leaf_bottom', 'hinge_socket_bottom',
                     'latch_cover', 'collar_1', 'collar_2', 'collar_3', 'disk_2', 'disk_3']
            parts = {name: {'source_sha256': write(f'work/rendered-parts/scale-100-200/{name}.stl', name)}
                     for name in names}
            write('exports/mini-vault-200-scale-1-print.verification.json', json.dumps({
                'parameters': parameters, 'source_hashes': {'mini-vault.scad': source_hash}, 'parts': parts}))
            motors = {}
            for mode, count, end in [('door', 361, 90), ('slider', 121, -8)]:
                rows = []
                for i in range(count):
                    position = end*i/(count-1)
                    if mode == 'door':
                        c, s = math.cos(math.radians(position)), math.sin(math.radians(position))
                        matrix = [[c, -s, 0, 20-20*c-.5*s], [s, c, 0, -.5-20*s+.5*c],
                                  [0, 0, 1, 0], [0, 0, 0, 1]]
                    else:
                        matrix = v.base_matrix('door')
                        matrix[0][3] = position
                    rows.append({'position': position, 'transform_mm': matrix})
                motors[mode] = {'poses': rows}
            poses = {'main_source_sha256': source_hash, 'preset_sha256': preset_hash,
                     'script_sha256': script_hash, 'motors': motors}
            pose_path = 'work/thick-housing/chrono-poses.json'
            write(pose_path, json.dumps(poses))
            loaded, meshes = v.load_inputs(root)
            self.assertEqual(len(loaded['door']), 361)
            self.assertEqual(len(meshes), 22)
            manifest_path = root/'exports/mini-vault-200-scale-1-print.verification.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['parts']['unexpected'] = manifest['parts'].pop('disk_1')
            write('work/rendered-parts/scale-100-200/unexpected.stl', 'disk_1')
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, '22-part'):
                v.load_inputs(root)
            manifest['parts']['disk_1'] = manifest['parts'].pop('unexpected')
            manifest_path.write_text(json.dumps(manifest))
            write('work/rendered-parts/scale-100-200/latch.stl', 'changed')
            with self.assertRaisesRegex(ValueError, 'latch.stl'):
                v.load_inputs(root)
            write('work/rendered-parts/scale-100-200/latch.stl', 'latch')
            write('mini-vault.scad', 'cube(2);')
            with self.assertRaisesRegex(ValueError, 'mini-vault.scad'):
                v.load_inputs(root)
            write('mini-vault.scad', 'cube(1);')
            poses['motors']['slider']['poses'][10]['transform_mm'][0][0] = float('nan')
            write(pose_path, json.dumps(poses))
            with self.assertRaisesRegex(ValueError, 'slider.*10'):
                v.load_inputs(root)
            poses['motors']['slider']['poses'][10]['transform_mm'][0][0] = 1
            poses['motors']['slider']['poses'][10]['transform_mm'][0][3] = 999
            write(pose_path, json.dumps(poses))
            with self.assertRaisesRegex(ValueError, 'slider.*10'):
                v.load_inputs(root)


if __name__ == '__main__':
    unittest.main()
