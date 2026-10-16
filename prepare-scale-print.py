"""Orient verified parts on print faces and keep them separate in STL exports."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
import trimesh

from analyze import NAMES
from exporter import ROOT, source_hashes


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def orient_for_print(name, original):
    """Use a broad bed face; return a rigid transform without changing fit sizes."""
    transform = np.eye(4)
    if name in ['housing','latch','dial','knob'] or name.startswith('collar_'):
        transform[:3,:3] = [[1,0,0],[0,0,1],[0,-1,0]]
    elif name.startswith('fastener_'):
        transform[:3,:3] = [[1,0,0],[0,-1,0],[0,0,-1]]
    elif name.startswith('hinge_'):
        # Keep the journal axis upright and put the larger axial mounting face down.
        bottom, top = original.bounds[:,2]
        centers, normals = original.triangles_center[:,2], original.face_normals[:,2]
        lower_area = original.area_faces[(centers < bottom+.001) & (normals < -.999)].sum()
        upper_area = original.area_faces[(centers > top-.001) & (normals > .999)].sum()
        if upper_area > lower_area:
            transform[:3,:3] = [[1,0,0],[0,-1,0],[0,0,-1]]
    else:
        transform[:3,:3] = [[1,0,0],[0,0,-1],[0,1,0]]
    mesh = original.copy()
    mesh.apply_transform(transform)
    transform[:3,3] = -mesh.bounds[0]
    mesh.apply_translation(transform[:3,3])
    return mesh, transform


def export_separated(output, report_path=ROOT/'work/size-scale-verification.json',
                     sources=ROOT/'work/rendered-parts/scale-150-220', preset='220 - scale 1.5',
                     parts_output=None):
    """Keep disconnected part meshes in one STL, with 10 mm between XY bounds."""
    if output.exists():
        raise FileExistsError(output)
    report = json.loads(report_path.read_text())
    provenance = source_hashes()
    assert report['source_hashes'] == provenance, 'Part verification is stale'
    meshes, records = [], {}
    x, y, row_depth = 0., 0., 0.
    for name in NAMES:
        source = sources/f'{name}.stl'
        assert digest(source) == report['parts'][name]['sha256'], name
        mesh = trimesh.load_mesh(source)
        assert mesh.is_volume and len(mesh.split()) == 1, name
        original = mesh.copy()
        mesh, transform = orient_for_print(name, original)
        if parts_output is not None:
            parts_output.mkdir(parents=True, exist_ok=True)
            part_path = parts_output/f'{name}.stl'
            mesh.export(part_path, file_type='stl_ascii')
            part = trimesh.load_mesh(part_path)
            assert part.is_volume and len(part.split()) == 1, name
            np.testing.assert_allclose(part.vertices, mesh.vertices, atol=1e-7, rtol=0)
        width, depth, _ = mesh.extents
        if x and x + width > 480:
            x, y, row_depth = 0., y + row_depth + 10., 0.
        placement = np.array([x, y, 0.])
        mesh.apply_translation(placement)
        transform[:3,3] += placement
        np.testing.assert_allclose(sorted(mesh.extents), sorted(original.extents), atol=1e-7, rtol=0)
        records[name] = dict(source_sha256=digest(source),
                             print_transform=transform.tolist(),
                             bounds_mm=mesh.bounds.tolist(), faces=len(mesh.faces))
        meshes.append(mesh)
        x += width + 10.
        row_depth = max(row_depth, depth)
    for i, left in enumerate(meshes):
        for right in meshes[i+1:]:
            assert any(left.bounds[1, axis] <= right.bounds[0, axis] - 9.999999
                       or right.bounds[1, axis] <= left.bounds[0, axis] - 9.999999
                       for axis in (0, 1)), 'Part bounds overlap'
    combined = trimesh.util.concatenate(meshes)
    output.parent.mkdir(parents=True, exist_ok=True)
    combined.export(output, file_type='stl_ascii')
    checked = trimesh.load_mesh(output)
    parts = checked.split(only_watertight=False)
    assert len(parts) == 22 and all(p.is_volume for p in parts)
    np.testing.assert_allclose(checked.vertices, combined.vertices, atol=1e-7)
    assert len(checked.faces) == sum(len(m.faces) for m in meshes)
    assert abs(checked.volume - sum(m.volume for m in meshes)) < .001
    assert source_hashes() == provenance, 'Source changed while exporting'
    result = dict(preset=preset, parameters=report['parameters'], source_hashes=provenance,
                  sha256=digest(output), bytes=output.stat().st_size,
                  components=len(parts), all_components_closed=True,
                  bounds_mm=checked.bounds.tolist(), separation_mm=10,
                  preparation_script_sha256=digest(Path(__file__)),
                  transform='rigid per-part rotation and translation; each minimum Z = 0',
                  parts=records, slicer='not_run', physical='not_run')
    output.with_suffix('.verification.json').write_text(
        json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('parts', 'source_hashes')}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--single-stl', action='store_true',
                        help='Place 22 disconnected parts in one STL for slicer splitting')
    args = parser.parse_args()
    if args.single_stl:
        export_separated((args.output or ROOT/'exports/mini-vault-220-scale-1.5-print.stl').resolve(),
                         parts_output=ROOT/'exports/scale-150-220')
        return
    output = (args.output or ROOT/'exports/mini-vault-220-scale-1.5-print-parts').resolve()
    archive = output.parent / (output.name + '.zip')
    if output.exists() or archive.exists():
        raise FileExistsError(f'Choose a new output directory: {output}')
    report = json.loads((ROOT/'work/size-scale-verification.json').read_text())
    provenance = source_hashes()
    if report['source_hashes'] != provenance:
        raise RuntimeError('Part verification is stale; rebuild and verify the preset first')
    sources = ROOT/'work/rendered-parts/scale-150-220'
    for name in NAMES:
        if digest(sources/f'{name}.stl') != report['parts'][name]['sha256']:
            raise RuntimeError(f'Part changed after verification: {name}')
    output.mkdir(parents=True)
    records = {}
    for name in NAMES:
        original = trimesh.load_mesh(sources/f'{name}.stl')
        assert original.is_volume and len(original.split()) == 1, name
        mesh, transform = orient_for_print(name, original)
        path = output/f'{name}.stl'
        # ASCII retains double coordinates after the rigid print-pose transform.
        mesh.export(path, file_type='stl_ascii')
        checked = trimesh.load_mesh(path)
        assert checked.is_volume and len(checked.split()) == 1, name
        np.testing.assert_allclose(checked.bounds[0], [0, 0, 0], atol=1e-7)
        np.testing.assert_allclose(sorted(checked.extents), sorted(original.extents), atol=1e-7)
        np.testing.assert_allclose(checked.vertices, mesh.vertices, atol=1e-7)
        assert abs(checked.volume-original.volume) < .001, name
        records[name] = dict(sha256=digest(path), source_sha256=digest(sources/f'{name}.stl'),
                             print_transform=transform.tolist(), bounds_mm=checked.bounds.tolist(),
                             faces=len(checked.faces), is_volume=True, components=1,
                             volume_difference_mm3=float(checked.volume-original.volume))
        print(name, 'one closed part at Z0', flush=True)
    assert provenance == source_hashes(), 'Source changed while packaging'
    result = dict(preset='220 - scale 1.5', parameters=report['parameters'],
                  source_hashes=provenance, preparation_script_sha256=digest(Path(__file__)),
                  stl_format='ASCII', transform='rigid rotation and translation; each minimum XYZ = 0',
                  orientation='broad print face down; remaining supports require slicer review',
                  parts=records, slicer='not_run', physical='not_run')
    (output/'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (output/'README.txt').write_text(
        'MINI-VAULT — 22 STL riêng\n'
        'Preset: 220 - scale 1.5; vỏ 220 x 220 x 220 mm.\n'
        'Mỗi STL là một chi tiết riêng, đã xoay mặt in và đặt min XYZ về 0.\n'
        'Kích thước và khe lắp giữ nguyên sau phép xoay/tịnh tiến.\n'
        'Trong slicer, nhập dưới dạng nhiều đối tượng riêng, rồi Arrange.\n'
        'Khi có hộp thoại gộp nhiều file thành một đối tượng, chọn giữ đối tượng riêng.\n'
        'Chọn mặt đặt bàn, hướng in và support phù hợp cho từng chi tiết.\n'
        'verification.json ghi hash, phép tịnh tiến và kiểm tra 22 khối kín.\n', encoding='utf-8')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in sorted(output.iterdir()):
            package.write(path, path.name)
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        assert sum(n.endswith('.stl') for n in package.namelist()) == 22
        for name, record in records.items():
            assert hashlib.sha256(package.read(f'{name}.stl')).hexdigest() == record['sha256']
    print('Verified ZIP:', archive, 'bytes:', archive.stat().st_size,
          'SHA256:', digest(archive), flush=True)


if __name__ == '__main__':
    main()
