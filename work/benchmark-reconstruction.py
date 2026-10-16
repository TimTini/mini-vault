"""Count direct STL triangles at identical tessellation, without mesh simplify.

python work/benchmark-reconstruction.py --source mini-vault.scad --output work/native-benchmark/after
Part totals are the sum of separately exported selectors, before assembly Boolean.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analyze import NAMES


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--openscad', default='openscad')
    parser.add_argument('--parts', nargs='+', default=NAMES)
    parser.add_argument('--parameters', type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    files = [source]+sorted((source.parent/'profiles').glob('*.scad'))+sorted((source.parent/'geometry').glob('*.scad'))
    hashes = {str(p.relative_to(source.parent)): digest(p) for p in files}
    parameters = json.loads(args.parameters.read_text()) if args.parameters else {}

    def run(name):
        target = output/f'{name}.stl'
        command = [args.openscad, '--backend', 'Manifold', '--hardwarnings', '--export-format', 'binstl',
                   '-o', str(target), '-D', 'part='+json.dumps(name)]
        for key, value in parameters.items():
            command += ['-D', key+'='+json.dumps(value)]
        command.append(str(source))
        start = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True)
        seconds = time.perf_counter()-start
        diagnostic = result.stdout+result.stderr
        (output/f'{name}.log').write_text(diagnostic)
        assert result.returncode == 0 and 'ERROR:' not in diagnostic and 'WARNING:' not in diagnostic, diagnostic
        raw = trimesh.load_mesh(target, process=False)
        reloaded = trimesh.load_mesh(target)
        print(name, len(raw.faces), 'triangles', 'volume', reloaded.is_volume, flush=True)
        return dict(name=name, triangles=len(raw.faces), seconds=seconds, bytes=target.stat().st_size,
                    bounds=reloaded.bounds.tolist(), is_volume=bool(reloaded.is_volume),
                    components=len(reloaded.split(only_watertight=False)), sha256=digest(target))

    with ThreadPoolExecutor(max_workers=2) as pool:
        parts = list(pool.map(run, args.parts))
    assert hashes == {str(p.relative_to(source.parent)): digest(p) for p in files}
    report = dict(source=str(source), source_hashes=hashes, parameters=parameters, curve_segments=128,
                  backend='Manifold', format='binstl', simplification='not_applied',
                  counting='sum of separate part exports; assembly Boolean not applied',
                  total_triangles=sum(p['triangles'] for p in parts), parts=parts,
                  physical='not_run', self_intersections='not_run')
    (output/'report.json').write_text(json.dumps(report, indent=2))
    print('Total', report['total_triangles'], flush=True)


if __name__ == '__main__':
    main()
