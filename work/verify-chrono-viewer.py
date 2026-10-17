"""Finite GUI smoke of the saved-pose viewer; writes only work/chrono-viewer-smoke/."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('chrono_viewer', ROOT/'work/chrono-viewer.py')
viewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viewer)


def main():
    poses, meshes = viewer.load_inputs()
    app = viewer.Viewer(poses, meshes)
    output = ROOT/'work/chrono-viewer-smoke'
    output.mkdir(exist_ok=True)
    result = {'scope': 'Saved pose replay, native frame conversion and dispatched Tk controls; no CAD force solve',
              'viewer_sha256': hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest(),
              'poses_checked': {}, 'screenshots': []}
    try:
        # Check all saved poses through real Chrono bodies, including each pin's base frame.
        max_error = 0.
        for mode, rows in poses.items():
            app.playback.select(mode)
            for index, row in enumerate(rows):
                app.playback.seek(index)
                app.apply_pose()
                for name, body in app.bodies.items():
                    expected = viewer.pose_matrix(mode, name, row['transform_mm'])
                    rot = body.GetRotMat()
                    axes = [rot.GetAxisX(), rot.GetAxisY(), rot.GetAxisZ()]
                    pos = body.GetPos()
                    for i, axis in enumerate(['x', 'y', 'z']):
                        max_error = max(max_error, abs(getattr(pos, axis)*1000-expected[i][3]))
                        for j in range(3):
                            max_error = max(max_error, abs(getattr(axes[j], axis)-expected[i][j]))
            result['poses_checked'][mode] = len(rows)
        assert max_error < 1e-8, max_error
        result['native_frame_max_error_mm_or_dimensionless'] = max_error

        app.root.update()
        app.mode_buttons['door'].invoke()
        app.play_button.invoke()
        assert app.playback.playing
        app.play_button.invoke()
        assert not app.playback.playing
        app.scale.set(180)
        app.root.update()
        assert app.playback.index == 180 and not app.playback.playing
        assert '181/361' in app.label.get() and '45.00' in app.label.get()

        def capture(name):
            for _ in range(3):
                assert app.vis.Run(), '3D window closed during smoke'
                app.vis.BeginScene()
                app.vis.Render()
                app.vis.EndScene()
                app.root.update()
            path = output/name
            app.vis.WriteImageToFile(str(path))
            assert path.exists() and path.stat().st_size > 1000, path
            result['screenshots'].append(name)

        capture('door-45-deg.png')
        # Exercise Irrlicht's actual camera event receiver without desktop input.
        import pychrono.irrlicht as irr
        camera = app.vis.GetActiveCamera()
        def camera_position():
            pos = camera.getPosition()
            return [pos.X, pos.Y, pos.Z]
        before = camera_position()
        event = irr.SEvent()
        event.EventType = irr.EET_MOUSE_INPUT_EVENT
        event.MouseInput.Event = irr.EMIE_MOUSE_WHEEL
        event.MouseInput.Wheel = 1
        app.vis.GetDevice().postEventFromUser(event)
        capture('camera-zoom.png')
        after = camera_position()
        assert max(abs(a-b) for a, b in zip(before, after)) > 1e-5, (before, after)
        result['camera_wheel_zoom'] = 'passed via Irrlicht event dispatch'
        before = camera_position()
        for kind, x, y, buttons in [
            (irr.EMIE_LMOUSE_PRESSED_DOWN, 500, 350, irr.EMBSM_LEFT),
            (irr.EMIE_MOUSE_MOVED, 600, 400, irr.EMBSM_LEFT),
            (irr.EMIE_LMOUSE_LEFT_UP, 600, 400, 0),
        ]:
            event.MouseInput.Event = kind
            event.MouseInput.X, event.MouseInput.Y = x, y
            event.MouseInput.ButtonStates = buttons
            app.vis.GetDevice().postEventFromUser(event)
            assert app.vis.Run()
            app.vis.BeginScene()
            app.vis.Render()
            app.vis.EndScene()
        after = camera_position()
        assert max(abs(a-b) for a, b in zip(before, after)) > 1e-5, (before, after)
        result['camera_left_drag_orbit'] = 'passed via Irrlicht event dispatch'
        app.mode_buttons['slider'].invoke()
        assert app.playback.mode == 'slider' and app.playback.index == 0
        assert float(app.scale.cget('to')) == 120
        app.scale.set(120)
        app.root.update()
        assert app.playback.index == 120
        assert '121/121' in app.label.get() and '-8.00' in app.label.get()
        app.hide_housing.set(True)
        app.update_housing()
        capture('slider-minus-8-mm.png')
        app.hide_housing.set(False)
        app.update_housing()
        capture('slider-with-housing.png')
        app.step(-1)
        assert app.playback.index == 119
        result['controls'] = 'play/pause, scrub, mode switch, step, hide housing passed'
        result['status'] = 'passed'
    finally:
        app.close()
    (output/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
