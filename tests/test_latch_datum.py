import os
import subprocess
import unittest
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
OPENSCAD = Path(os.environ.get(
    "MINI_VAULT_OPENSCAD",
    "openscad",
))
FROZEN_MAIN = ROOT / "work" / "backup" / "before-native-20261016" / "mini-vault.scad"
PRODUCTION_MAIN = ROOT / "mini-vault.scad"
MAIN = Path(os.environ.get("MINI_VAULT_LATCH_MAIN", str(PRODUCTION_MAIN)))
NATIVE_WRAPPER = ROOT / "work" / "native-latch" / "native-latch-wrapper.scad"
OUT = ROOT / "work" / "native-latch"


class LatchDatumTest(unittest.TestCase):
    def render(self, source, name, defines):
        path = OUT / name
        args = [str(OPENSCAD), "--backend", "Manifold", "--hardwarnings", "-o", str(path)]
        for key, value in defines.items():
            args.extend(["-D", f'{key}="{value}"' if isinstance(value, str) else f"{key}={value}"])
        args.append(str(source))
        run = subprocess.run(args, capture_output=True, text=True, timeout=180)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(path.exists(), path)
        return trimesh.load_mesh(path, process=False)

    def test_native_grip_tracks_left_door_edge_and_fixed_link_tslot(self):
        link_path = ROOT / "work" / "reference-parts" / "link.stl"
        link = trimesh.load_mesh(link_path, process=False)
        link_tree = cKDTree(link.vertices)
        for width in (142, 170, 220):
            mesh = self.render(
                MAIN,
                f"native_w{width}_latch.stl",
                {"body_width": width, "part": "latch"},
            )
            delta = width - 142
            grip = mesh.vertices[(mesh.vertices[:, 1] >= -15.001) & (mesh.vertices[:, 1] < -10)]
            self.assertGreater(len(grip), 0)
            self.assertAlmostEqual(float(grip[:, 0].min()), -53 - delta, delta=0.1)
            self.assertAlmostEqual(float(grip[:, 0].max()), -39 - delta, delta=0.1)
            # Check the actual fixed hook section, rather than an accidental
            # nearest vertex elsewhere on the latch.  The link occupies
            # X=-41.3..-10, Y=-4..10, Z=+-2.5.
            hook = mesh.vertices[
                (mesh.vertices[:, 0] >= -41.51)
                & (mesh.vertices[:, 0] <= -39.49)
                & (mesh.vertices[:, 1] >= -4.01)
                & (mesh.vertices[:, 1] <= 0.01)
            ]
            self.assertGreater(len(hook), 0, f"fixed T-slot section missing at width={width}")
            overlap = np.minimum(hook.max(axis=0), link.bounds[1]) - np.maximum(
                hook.min(axis=0), link.bounds[0]
            )
            self.assertTrue(np.all(overlap >= -0.01), f"T-slot/link AABB gap at width={width}: {overlap}")
            self.assertLessEqual(
                float(link_tree.query(mesh.vertices, k=1, workers=-1)[0].min()),
                0.25,
                f"fixed link/T-slot lost at width={width}",
            )

    def test_frozen_user_mapping_records_old_fixed_link_gap(self):
        """The frozen artificial-layer mapping is the regression this module replaces."""
        link = trimesh.load_mesh(ROOT / "work" / "reference-parts" / "link.stl", process=False)
        legacy = self.render(FROZEN_MAIN, "frozen_w170_latch_regression.stl", {
            "body_width": 170, "part": "latch",
        })
        gap = float(cKDTree(link.vertices).query(legacy.vertices, k=1, workers=-1)[0].min())
        self.assertGreater(gap, 5.0)

    def test_web24_hook_slot_is_clear_against_regression_link(self):
        """The paired 2.4 mm link web gets a +/-1.4 mm hook clearance."""
        link_path = ROOT / "work" / "local-regression" / "link.stl"
        self.assertTrue(link_path.exists(), link_path)
        latch = self.render(
            MAIN,
            "native_w142_web24_latch.stl",
            {"body_width": 142, "link_web_thickness": 2.4, "part": "latch"},
        )
        link = trimesh.load_mesh(link_path, process=False)
        intersection = trimesh.boolean.intersection(
            [latch, link], engine="manifold", check_volume=False
        )
        volume = float(intersection.volume) if len(intersection.faces) else 0.0
        self.assertLessEqual(volume, 0.001, f"T-slot/link Boolean overlap={volume}")

        # At the fixed hook wall the actual section contains the widened
        # clearance planes.  Checking vertices here avoids treating a broad
        # outer arm vertex as proof that the slot was widened.
        hook_wall = latch.vertices[
            (np.abs(latch.vertices[:, 0] + 39.5) < 1e-3)
            & (latch.vertices[:, 1] >= -4.02)
            & (latch.vertices[:, 1] <= 0.01)
        ]
        z_values = np.unique(np.round(hook_wall[:, 2], 3))
        self.assertIn(-1.4, z_values)
        self.assertIn(1.4, z_values)

    def test_cover_catches_follow_door_support_datum_at_all_widths(self):
        catch_points = np.array([
            [-58.682671, 18.521221],
            [-55.406063, 16.226915],
        ])
        for width in (142, 170, 220):
            cover = self.render(MAIN, f"main_w{width}_latch_cover.stl", {
                "body_width": width, "part": "latch_cover",
            })
            door = self.render(MAIN, f"main_w{width}_door.stl", {
                "body_width": width, "part": "door",
            })
            delta = width - 142
            moved = catch_points.copy()
            # The cover is expected to use the door width datum: x<=-74 moves
            # fully, -74..-64 interpolates, x>=-64 stays fixed.
            moved[:, 0] -= np.where(
                catch_points[:, 0] <= -74,
                delta,
                np.where(catch_points[:, 0] >= -64, 0, delta * (-64 - catch_points[:, 0]) / 10),
            )
            y0_cover = cover.vertices[np.abs(cover.vertices[:, 1]) < 1e-5][:, [0, 2]]
            y0_door = door.vertices[np.abs(door.vertices[:, 1]) < 1e-5][:, [0, 2]]
            cover_distances = cKDTree(y0_cover).query(moved, k=1, workers=-1)[0]
            tree = cKDTree(y0_door)
            distances = tree.query(moved, k=1, workers=-1)[0]
            self.assertLessEqual(float(np.max(cover_distances)), 0.25, f"cover catch moved at width={width}")
            self.assertLessEqual(float(np.max(distances)), 0.25, f"cover catch drift at width={width}")


if __name__ == "__main__":
    unittest.main()
