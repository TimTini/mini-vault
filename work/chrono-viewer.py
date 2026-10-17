"""Replay saved MINI-VAULT 200 Chrono poses. No dynamics or contact-force solve.

Run with the separate PyChrono runtime; see README.md. Inputs stay read-only.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
FIXED_DOOR = {'housing', 'hinge_leaf_top', 'hinge_leaf_bottom'}
SLIDING = {'latch', 'link'}
PART_NAMES = {'door', 'hinge_socket_top', 'fastener_1', 'fastener_2', 'disk_1',
              'fastener_3', 'hinge_leaf_top', 'latch', 'shaft', 'dial', 'retaining_ring',
              'housing', 'knob', 'link', 'hinge_leaf_bottom', 'hinge_socket_bottom',
              'latch_cover', 'collar_1', 'collar_2', 'collar_3', 'disk_2', 'disk_3'}


def base_matrix(name):
    matrix = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    if name.startswith('fastener_'):
        index = int(name[-1])-1
        angle = math.radians(22.5*([7, 3, 12][index]-7))
        # Same seating as verify-size-scale.py:place(meshes, 1), in mm.
        matrix = [[1, 0, 0, -.028609+13.5*math.cos(angle)-55],
                  [0, 0, 1, index*5-6],
                  [0, -1, 0, 13.5*math.sin(angle)+10+[0, 9.4, 18.3][index]],
                  [0, 0, 0, 1]]
    return matrix


def pose_matrix(mode, name, motion):
    base = base_matrix(name)
    moving = name not in FIXED_DOOR if mode == 'door' else name in SLIDING
    if not moving:
        return base
    return [[sum(motion[i][k]*base[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def load_inputs(root=ROOT):
    def check_hash(relative, expected):
        path = root/relative
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Stale or changed input: {relative}')

    poses = json.loads((root/'work/thick-housing/chrono-poses.json').read_text())
    for key, relative in [('main_source_sha256', 'mini-vault.scad'),
                          ('preset_sha256', 'mini-vault.json'),
                          ('script_sha256', 'work/chrono-housing-check.py')]:
        check_hash(relative, poses[key])
    manifest = json.loads((root/'exports/mini-vault-200-scale-1-print.verification.json').read_text())
    preset = json.loads((root/'mini-vault.json').read_text())['parameterSets']['200 - scale 1']
    if manifest['parameters'] != preset:
        raise ValueError('Manifest does not match preset 200 - scale 1')
    if [float(preset['body_'+axis]) for axis in ['width', 'depth', 'height']] != [200]*3 or float(preset['size_scale']) != 1:
        raise ValueError('This replay supports only the saved 200 mm / scale 1 mechanism')
    for relative, expected in manifest['source_hashes'].items():
        check_hash(relative, expected)
    parts = manifest['parts']
    if set(parts) != PART_NAMES:
        raise ValueError('Expected the complete 22-part kit')
    meshes = {}
    for name, record in parts.items():
        relative = f'work/rendered-parts/scale-100-200/{name}.stl'
        check_hash(relative, record['source_sha256'])
        meshes[name] = root/relative
    records = {}
    for mode, count, end in [('door', 361, 90), ('slider', 121, -8)]:
        rows = poses['motors'][mode]['poses']
        if len(rows) != count:
            raise ValueError(f'Expected {count} {mode} poses')
        for index, row in enumerate(rows):
            m = row['transform_mm']
            valid = len(m) == 4 and all(len(r) == 4 for r in m)
            valid = valid and all(math.isfinite(x) for r in m for x in r)
            valid = valid and m[3] == [0, 0, 0, 1]
            valid = valid and abs(row['position']-end*index/(count-1)) < 1e-6
            if mode == 'door':
                c, s = math.cos(math.radians(row['position'])), math.sin(math.radians(row['position']))
                expected = [[c, -s, 0, 20-20*c-.5*s], [s, c, 0, -.5-20*s+.5*c],
                            [0, 0, 1, 0], [0, 0, 0, 1]]
            else:
                expected = base_matrix('door')
                expected[0][3] = row['position']
            valid = valid and max(abs(m[i][j]-expected[i][j]) for i in range(4) for j in range(4)) < 1e-5
            if not valid:
                raise ValueError(f'Invalid {mode} pose {index}')
        records[mode] = rows
    return records, meshes


class Playback:
    """Play each sequence once in six seconds; scrubbing always pauses."""
    def __init__(self, counts):
        self.counts = counts
        self.mode = 'door'
        self.index = 0
        self.playing = False
        self.fraction = 0.

    def select(self, mode):
        if mode not in self.counts:
            raise ValueError(f'Unknown motion: {mode}')
        self.mode = mode
        self.seek(0)

    def seek(self, index):
        if not 0 <= index < self.counts[self.mode]:
            raise ValueError(f'Pose index out of range: {index}')
        self.index = index
        self.fraction = 0.
        self.playing = False

    def toggle(self):
        if not self.playing and self.index == self.counts[self.mode]-1:
            self.seek(0)
        self.playing = not self.playing

    def advance(self, seconds):
        if self.playing:
            self.fraction += max(0, seconds)*(self.counts[self.mode]-1)/6
            step = int(self.fraction)
            self.fraction -= step
            self.index = min(self.index+step, self.counts[self.mode]-1)
            if self.index == self.counts[self.mode]-1:
                self.playing = False


class Viewer:
    def __init__(self, poses, meshes):
        import tkinter as tk
        from tkinter import ttk
        import pychrono as ch
        import pychrono.irrlicht as irr

        self.ch = ch
        self.poses = poses
        self.playback = Playback({mode: len(rows) for mode, rows in poses.items()})
        self.system = ch.ChSystemNSC()
        self.bodies = {}
        for name, path in meshes.items():
            mesh = ch.ChTriangleMeshConnected()
            if not mesh.LoadSTLMesh(str(path)):
                raise ValueError(f'Cannot load mesh: {path}')
            mesh.Transform(ch.ChVector3d(0, 0, 0), ch.ChMatrix33d(.001))
            shape = ch.ChVisualShapeTriangleMesh()
            shape.SetMesh(mesh)
            shape.SetBackfaceCull(False)
            color = ((.62, .69, .75) if name == 'housing' else
                     (.25, .62, .86) if name == 'door' else
                     (.9, .36, .18) if name in SLIDING else (.88, .7, .32))
            shape.SetColor(ch.ChColor(*color))
            if name == 'housing':
                shape.SetOpacity(.2)
            body = ch.ChBody()
            body.SetFixed(True)
            body.AddVisualShape(shape)
            self.system.Add(body)
            self.bodies[name] = body
        self.apply_pose()
        self.vis = irr.ChVisualSystemIrrlicht()
        self.vis.AttachSystem(self.system)
        self.vis.SetWindowSize(1040, 760)
        self.vis.SetWindowTitle('MINI-VAULT 200 | Saved Chrono pose replay')
        self.vis.SetCameraVertical(ch.CameraVerticalDir_Z)
        self.vis.SetBackgroundColor(ch.ChColor(.12, .14, .17))
        self.vis.Initialize()
        self.vis.AddCamera(ch.ChVector3d(-.28, -.34, .22), ch.ChVector3d(-.06, .02, 0))
        self.vis.AddTypicalLights()
        self.root = tk.Tk()
        self.root.title('MINI-VAULT | Điều khiển phát lại')
        self.root.geometry('530x340')
        self.root.minsize(530, 340)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        panel = ttk.Frame(self.root, padding=18)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='MINI-VAULT 200 — tư thế Chrono đã lưu',
                  font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        ttk.Label(panel, text='Phát lại động học · không tính lực kẹt/ma sát').pack(anchor='w', pady=(4, 12))
        modes = ttk.Frame(panel)
        modes.pack(fill='x')
        self.mode = tk.StringVar(value='door')
        self.mode_buttons = {}
        for mode, label in [('door', 'Cửa · 361 tư thế'), ('slider', 'Chốt trượt · 121 vị trí')]:
            button = ttk.Radiobutton(modes, text=label, value=mode, variable=self.mode, command=self.select_mode)
            button.pack(side='left', padx=(0, 20))
            self.mode_buttons[mode] = button
        self.position = tk.DoubleVar(value=0)
        self.scale = ttk.Scale(panel, from_=0, to=360, variable=self.position, command=self.scrub)
        self.scale.pack(fill='x', pady=(18, 4))
        self.label = tk.StringVar()
        ttk.Label(panel, textvariable=self.label).pack(anchor='w')
        actions = ttk.Frame(panel)
        actions.pack(fill='x', pady=12)
        self.play_button = ttk.Button(actions, text='Phát', command=self.toggle)
        self.play_button.pack(side='left')
        ttk.Button(actions, text='−1 tư thế', command=lambda: self.step(-1)).pack(side='left', padx=6)
        ttk.Button(actions, text='+1 tư thế', command=lambda: self.step(1)).pack(side='left')
        ttk.Button(actions, text='Về đầu', command=lambda: self.scrub(0)).pack(side='left', padx=6)
        self.hide_housing = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text='Ẩn vỏ để xem rõ cơ cấu bên trong', variable=self.hide_housing,
                        command=self.update_housing).pack(anchor='w')
        ttk.Label(panel, text='Giữ chuột trái để xoay; lăn bánh xe để zoom trong cửa sổ 3D.\n'
                  'Kéo thanh hoặc bấm ±1 sẽ tạm dừng. Mỗi lượt phát dài 6 giây.').pack(anchor='w', pady=(10, 0))
        self.closed = False
        self.failure = None
        self.last_time = time.monotonic()
        self.refresh()

    def apply_pose(self):
        ch = self.ch
        motion = self.poses[self.playback.mode][self.playback.index]['transform_mm']
        for name, body in self.bodies.items():
            matrix = pose_matrix(self.playback.mode, name, motion)
            rotation = ch.ChMatrix33d()
            for i in range(3):
                for j in range(3):
                    rotation[i, j] = matrix[i][j]
            body.SetPos(ch.ChVector3d(*(matrix[i][3]*.001 for i in range(3))))
            body.SetRot(rotation.GetQuaternion())

    def refresh(self):
        p = self.playback
        self.position.set(p.index)
        value = self.poses[p.mode][p.index]['position']
        unit = '°' if p.mode == 'door' else ' mm (X)'
        self.label.set(f'Tư thế {p.index+1}/{p.counts[p.mode]}   |   {value:.2f}{unit}')
        self.play_button.configure(text='Dừng' if p.playing else 'Phát')
        self.apply_pose()

    def select_mode(self):
        self.playback.select(self.mode.get())
        self.scale.configure(to=self.playback.counts[self.playback.mode]-1)
        sliding = self.playback.mode == 'slider'
        self.hide_housing.set(sliding)
        self.update_housing()
        camera = (-.22, .24, .15) if sliding else (-.28, -.34, .22)
        self.vis.SetCameraPosition(self.ch.ChVector3d(*camera))
        self.vis.SetCameraTarget(self.ch.ChVector3d(-.06, .02, 0))
        self.refresh()

    def scrub(self, value):
        self.playback.seek(int(round(float(value))))
        self.refresh()

    def step(self, amount):
        p = self.playback
        self.scrub(max(0, min(p.index+amount, p.counts[p.mode]-1)))

    def toggle(self):
        self.playback.toggle()
        self.last_time = time.monotonic()
        self.refresh()

    def update_housing(self):
        # Irrlicht binds a scene node once; changing ChVisualShape visibility
        # afterwards does not hide the already-bound node in this release.
        self.vis.UnbindItem(self.bodies['housing'])
        if not self.hide_housing.get():
            self.vis.BindItem(self.bodies['housing'])

    def tick(self):
        if self.closed:
            return
        try:
            if not self.vis.Run():
                self.close()
                return
            now = time.monotonic()
            self.playback.advance(now-self.last_time)
            self.last_time = now
            self.refresh()
            self.vis.BeginScene()
            self.vis.Render()
            self.vis.EndScene()
            self.root.after(16, self.tick)
        except Exception as error:
            self.failure = error
            self.close()

    def close(self):
        if not self.closed:
            self.closed = True
            self.vis.GetDevice().closeDevice()
            self.root.destroy()
            # Release the renderer before its attached system (also at shutdown).
            self.vis = None

    def run(self):
        self.tick()
        self.root.mainloop()
        if self.failure:
            raise RuntimeError('Viewer stopped after a rendering error') from self.failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate saved inputs without opening windows')
    args = parser.parse_args()
    try:
        poses, meshes = load_inputs()
        print(f'Validated {len(meshes)} meshes, 361 door poses, 121 slider poses.', flush=True)
        if not args.check:
            Viewer(poses, meshes).run()
    except (OSError, ValueError, KeyError, ImportError) as error:
        parser.exit(1, f'{error}\nSee README.md: Xem tu the PyChrono. No inputs were changed.\n')


if __name__ == '__main__':
    main()
