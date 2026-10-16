"""Keep indexed topology through export; remove numerical slivers before STL.

OpenSCAD's direct STL of these layered sketches loses topology when coincident
coordinates collapse. OFF retains face indices. Manifold simplify has a 0.005 mm
tolerance and the final STL is reimported and checked before acceptance.
"""
import argparse
import json
import subprocess
import hashlib
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import manifold3d
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parent


def source_hashes():
    files=[ROOT/'mini-vault.scad',ROOT/'exporter.py',ROOT/'audit.py',ROOT/'build.ps1',
           ROOT/'analyze.py',ROOT/'profile_builder.py']+sorted((ROOT/'profiles').glob('*.scad'))+sorted((ROOT/'geometry').glob('*.scad'))
    return {str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


@contextmanager
def exclusive_file(path):
    try:
        handle=path.open('x')
    except FileExistsError as error:
        raise RuntimeError(f'Output already in use: {path}') from error
    with handle:
        handle.write(str(os.getpid()))
    try:
        yield
    finally:
        path.unlink()


def export_indexed(source,output,tolerance=0.005):
    indexed=trimesh.load_mesh(source,process=False)
    if not indexed.is_volume:
        raise ValueError(f'Indexed OpenSCAD output is not a volume: {source}')
    solid=manifold3d.Manifold(manifold3d.Mesh64(np.asarray(indexed.vertices,dtype=np.float64),
                                            np.asarray(indexed.faces,dtype=np.uint64)))
    if solid.status()!=manifold3d.Error.NoError:
        raise ValueError(f'Manifold input error: {solid.status()}')
    data=solid.simplify(tolerance).to_mesh64()
    mesh=trimesh.Trimesh(data.vert_properties[:,:3],data.tri_verts,process=False)
    if not mesh.is_volume:
        raise ValueError('Simplified indexed mesh is not a volume')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.stl',prefix='.mesh-',dir=output.parent,delete=False) as handle:
        temporary=Path(handle.name)
    try:
        mesh.export(temporary)
        reimported=trimesh.load_mesh(temporary)
        if not reimported.is_volume:
            raise ValueError('STL quantization still breaks topology; output is rejected')
        os.replace(temporary,output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return dict(indexed_faces=len(indexed.faces),stl_faces=len(reimported.faces),
                simplification_tolerance=tolerance,indexed_is_volume=True,stl_is_volume=True,
                source=str(source),output=str(output))


def render_part(name,parameters,output,openscad):
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with exclusive_file(output.with_suffix(output.suffix+'.lock')):
        return render_owned_part(name,parameters,output,openscad)


def render_owned_part(name,parameters,output,openscad):
    hashes=source_hashes()
    identity=hashlib.sha256(str(output.resolve()).casefold().encode()).hexdigest()[:16]
    intermediate=ROOT/'work/mesh-intermediates'/identity/(output.stem+'.off')
    intermediate.parent.mkdir(parents=True,exist_ok=True)
    command=[openscad,'--backend','Manifold','--hardwarnings','--export-format','off',
             '-o',str(intermediate),'-D','part='+json.dumps(name)]
    for k,v in parameters.items():
        command += ['-D',k+'='+json.dumps(v)]
    command.append(str(ROOT/'mini-vault.scad'))
    result=subprocess.run(command,capture_output=True,text=True)
    diagnostic=result.stdout+result.stderr
    output.with_suffix('.log').write_text(diagnostic)
    output.with_suffix('.command.json').write_text(json.dumps(command,indent=2))
    if result.returncode or not intermediate.exists():
        first_error=next((line for line in diagnostic.splitlines() if 'ERROR' in line or 'WARNING' in line),diagnostic[-300:])
        raise RuntimeError(f'{name}: render failed ({result.returncode}): {first_error}')
    try:
        # Preserve near-tangent fillet sections of small mechanical parts. The
        # large housing/door need a larger numerical-sliver reduction threshold.
        # The assembled scaled mechanism has near-tangent keyed fits; .005
        # collapsed those contacts when serialized as float32 STL. The measured
        # .002 setting retains closed topology without loosening a fit surface.
        tolerance=0.002 if name=='assembly' else 0.005 if name in ['housing','door','exploded'] else 0.0001
        report=export_indexed(intermediate,output,tolerance)
    except ValueError as error:
        raise RuntimeError(f'{name}: export rejected: {error}') from error
    if source_hashes()!=hashes:
        raise RuntimeError(f'{name}: source changed while rendering; output is not verified')
    report['source_hashes']=hashes
    output.with_suffix('.export.json').write_text(json.dumps(report,indent=2))
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--openscad',required=True)
    parser.add_argument('--part',default='assembly')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--parameters',type=Path)
    args=parser.parse_args()
    parameters=json.loads(args.parameters.read_text(encoding='utf-8-sig')) if args.parameters else {}
    render_part(args.part,parameters,args.output,args.openscad)
    print(args.output)


if __name__=='__main__':
    main()
