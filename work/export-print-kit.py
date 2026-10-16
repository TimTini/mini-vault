"""Render a saved print preset and orient its 22 parts into one separated STL."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyze import NAMES
from exporter import render_part, source_hashes


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preset', choices=['200 - scale 1','220 - scale 1.5'], required=True)
    parser.add_argument('--openscad', default=os.environ.get('MINI_VAULT_OPENSCAD','openscad'))
    args = parser.parse_args()
    preset = args.preset
    key, source_folder = {'200 - scale 1':('200-scale-1','scale-100-200'),
                          '220 - scale 1.5':('220-scale-1.5','scale-150-220')}[preset]
    presets_path = ROOT/'mini-vault.json'
    parameters = json.loads(presets_path.read_text())['parameterSets'][preset]
    numeric = {k:float(v) for k,v in parameters.items()}
    provenance = source_hashes()
    preset_hash = digest(presets_path)
    directory = ROOT/'work/rendered-parts'/source_folder
    output = ROOT/'exports'/f'mini-vault-{key}-print.stl'
    if output.exists():
        raise FileExistsError(output)

    def render(name):
        path = render_part(name, numeric, directory/f'{name}.stl',
            args.openscad)
        mesh = trimesh.load_mesh(path)
        assert mesh.is_volume and len(mesh.split()) == 1, name
        metadata = json.loads(path.with_suffix('.export.json').read_text())
        assert metadata['source_hashes'] == provenance
        if name == 'housing':
            indexed = trimesh.load_mesh(metadata['source'], process=False)
            size = [numeric['body_'+a] for a in ['width','depth','height']]
            np.testing.assert_allclose(indexed.extents, size, atol=.001, rtol=0)
            np.testing.assert_allclose(mesh.extents, size, atol=.02, rtol=0)
        print(name, 'one closed part', flush=True)
        return name, dict(sha256=digest(path), faces=len(mesh.faces),
                         bounds_mm=mesh.bounds.tolist(), volume_mm3=float(mesh.volume), components=1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        parts = dict(pool.map(render, NAMES))
    assert source_hashes() == provenance and digest(presets_path) == preset_hash
    report_path = ROOT/'work'/f'preset-{key}-export.json'
    report = dict(preset=preset, parameters=parameters, source_hashes=provenance,
                  preset_hash=preset_hash, verifier_sha256=digest(Path(__file__)), parts=parts,
                  physical_fit='not_run', mechanism_motion='verified_separately')
    report_path.write_text(json.dumps(report, indent=2))
    spec = importlib.util.spec_from_file_location('prepare_print', ROOT/'prepare-scale-print.py')
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    prepare.export_separated(output, report_path, directory, preset,
                             parts_output=ROOT/'exports'/source_folder)


if __name__ == '__main__':
    main()
