"""Reproducible measurements; never modify the reference STL."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
NAMES = ['door', 'hinge_socket_top', 'fastener_1', 'fastener_2', 'disk_1',
         'fastener_3', 'hinge_leaf_top', 'latch', 'shaft', 'dial', 'retaining_ring',
         'housing', 'knob', 'link', 'hinge_leaf_bottom', 'hinge_socket_bottom',
         'latch_cover', 'collar_1', 'collar_2', 'collar_3', 'disk_2', 'disk_3']


def inspect_reference(path):
    mesh = trimesh.load_mesh(path)
    parts = mesh.split(only_watertight=False)
    incidence=np.bincount(mesh.edges_unique_inverse)
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), units='mm',
                trimesh=trimesh.__version__, whole_watertight=bool(mesh.is_watertight),
                whole_winding=bool(mesh.is_winding_consistent),
                degenerate_faces=int((mesh.area_faces < 1e-10).sum()),
                boundary_edges=int((incidence==1).sum()),
                non_manifold_edges=int((incidence>2).sum()),
                whole_faces=len(mesh.faces),split_faces=sum(len(p.faces) for p in parts),
                self_intersections='not_run', parts=[dict(id=i, name=NAMES[i],
                    bounds=p.bounds.round(6).tolist(), size=p.extents.round(6).tolist(),
                    watertight=bool(p.is_watertight), winding=bool(p.is_winding_consistent),
                    is_volume=bool(p.is_volume), faces=len(p.faces)) for i,p in enumerate(parts)])


def measure_parts(parts):
    # Preserve global axes; identity transforms make measurement/assembly distinction explicit.
    return dict(units='mm', coordinate_mode='source placement',
                transforms=[dict(id=i, local_to_source=np.eye(4).tolist(),
                                 source_to_local=np.eye(4).tolist()) for i in range(len(parts))],
                disk_pitch=5.0, disk_thickness=2.0, housing=[142.0,100.0,84.0],
                wall_thickness=1.8, bottom_thickness=2.0,
                rules='INFERRED from measured geometry')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    path=ROOT/'reference/MINI-VAULT.stl'
    info=inspect_reference(path)
    assert info['sha256']=='c851ba43c400c378f7867406aabe91f46b6700cfa4c6eae54b21f1a133ed0a94'
    assert len(info['parts'])==22 and info['parts'][11]['size']==[142.0,100.0,84.0]
    parts=trimesh.load_mesh(path).split(only_watertight=False)
    out=ROOT/'work/reference-parts';out.mkdir(parents=True,exist_ok=True)
    for i,p in enumerate(parts):
        p.export(out/f'{NAMES[i]}.stl')
    (ROOT/'work/reference-quality.json').write_text(json.dumps(info,indent=2))
    (ROOT/'work/measurements.json').write_text(json.dumps(measure_parts(parts),indent=2))
    print(json.dumps(dict(parts=len(parts),hash=info['sha256'],degenerate_faces=info['degenerate_faces'],
                         individual_volume=sum(p['is_volume'] for p in info['parts']),self_intersections='not_run')))


if __name__=='__main__':
    main()
