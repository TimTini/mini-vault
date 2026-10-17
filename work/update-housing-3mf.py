"""Replace one housing in a Bambu project while preserving its other entries."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import trimesh

CORE='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PRODUCTION='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
NS={'m':CORE}


def object_mesh(obj):
    vertices=[[float(v.get(a)) for a in 'xyz'] for v in obj.findall('./m:mesh/m:vertices/m:vertex',NS)]
    faces=[[int(t.get(a)) for a in ['v1','v2','v3']] for t in obj.findall('./m:mesh/m:triangles/m:triangle',NS)]
    return trimesh.Trimesh(vertices,faces,process=True)


def replace_block(data,tag,content):
    pattern=rb'(<'+tag.encode()+rb'\b[^>]*>).*?(</'+tag.encode()+rb'>)'
    assert len(re.findall(pattern,data,re.S))==1,tag
    return re.sub(pattern,lambda m:m[1]+content+m[2],data,flags=re.S)


def update_project(project,housing,output):
    project,housing,output=map(Path,[project,housing,output])
    report_path=output.with_suffix('.verification.json')
    if output.exists() or report_path.exists():
        raise FileExistsError(output)
    source=trimesh.load_mesh(housing)
    assert source.is_volume and len(source.split())==1
    with zipfile.ZipFile(project) as archive:
        assert archive.testzip() is None
        infos=archive.infolist()
        entries={info.filename:archive.read(info.filename) for info in infos}
        archive_comment=archive.comment
    assert not any(n.endswith(('.gcode','.gcode.md5')) for n in entries), 'Re-slice projects containing toolpaths before replacement'
    matches=[]
    for name,data in entries.items():
        if not name.endswith('.model'):
            continue
        model=ET.fromstring(data)
        for obj in model.findall('./m:resources/m:object',NS):
            if obj.find('m:mesh',NS) is None:
                continue
            mesh=object_mesh(obj)
            if np.allclose(mesh.extents,source.extents,atol=.03,rtol=0):
                matches.append((name,obj,mesh))
    assert len(matches)==1,'Expected exactly one housing with matching dimensions'
    member,obj,old=matches[0]
    assert old.is_volume
    old_triangles=obj.findall('./m:mesh/m:triangles/m:triangle',NS)
    assert len(old_triangles)==len(old.faces)
    for triangle in old_triangles:
        assert set(triangle.attrib)<= {'v1','v2','v3','face_property'}, 'Painted facets need an explicit remapping plan'
        assert triangle.get('face_property') in [None,'3'], 'Unsupported face classification'
    # Preserve the existing local minimum, so its bed placement stays unchanged.
    replacement=source.copy()
    translation=old.bounds[0]-replacement.bounds[0]
    replacement.apply_translation(translation)
    np.testing.assert_allclose(replacement.bounds,old.bounds,atol=.03,rtol=0)
    _,distances,nearest=old.nearest.on_surface(replacement.triangles_center)
    assert float(distances.max())<.45,'Existing housing differs beyond the groove bevel'
    vertices=''.join('<vertex x="%s" y="%s" z="%s"/>' % tuple(format(float(v),'.15g') for v in point) for point in replacement.vertices).encode()
    triangles=[]
    for face,index in zip(replacement.faces,nearest):
        prop=old_triangles[index].get('face_property')
        attribute='' if prop is None else ' face_property="'+prop+'"'
        triangles.append('<triangle v1="%d" v2="%d" v3="%d"%s/>' % (*face,attribute))
    # Byte-patch only mesh lists, retaining the original namespace declarations.
    model_data=replace_block(entries[member],'vertices',vertices)
    model_data=replace_block(model_data,'triangles',''.join(triangles).encode())
    main=ET.fromstring(entries['3D/3dmodel.model'])
    parents=[]
    for parent in main.findall('./m:resources/m:object',NS):
        for component in parent.findall('./m:components/m:component',NS):
            if component.get('objectid')==obj.get('id') and component.get('{'+PRODUCTION+'}path','').lstrip('/')==member:
                parents.append(parent.get('id'))
    assert len(parents)==1,'Expected one housing component reference'
    config=ET.fromstring(entries['Metadata/model_settings.config'])
    parent=config.find("object[@id='"+parents[0]+"']")
    assert parent is not None and len(parent.findall('part'))==1
    part=parent.find("part[@id='"+obj.get('id')+"']")
    assert part is not None
    count=str(len(replacement.faces))
    metadata=parent.find('metadata[@face_count]')
    statistics=part.find('mesh_stat')
    assert metadata is not None and statistics is not None
    metadata.set('face_count',count)
    statistics.set('face_count',count)
    changed={member:model_data,'Metadata/model_settings.config':ET.tostring(config,encoding='utf-8',xml_declaration=True)}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as handle, zipfile.ZipFile(handle,'w') as archive:
        archive.comment=archive_comment
        for info in infos:
            archive.writestr(info,changed.get(info.filename,entries[info.filename]))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None and archive.namelist()==[i.filename for i in infos]
        for name,data in entries.items():
            assert archive.read(name)==changed.get(name,data),name
        checked=ET.fromstring(archive.read(member)).find("./m:resources/m:object[@id='"+obj.get('id')+"']",NS)
        mesh=object_mesh(checked)
        assert mesh.is_volume and len(mesh.split())==1
        np.testing.assert_allclose(mesh.vertices,replacement.vertices,atol=1e-10,rtol=0)
        np.testing.assert_array_equal(mesh.faces,replacement.faces)
    report=dict(project_sha256=hashlib.sha256(project.read_bytes()).hexdigest(),
                housing_sha256=hashlib.sha256(housing.read_bytes()).hexdigest(),
                output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                changed_entries=list(changed),unchanged_entries=len(entries)-len(changed),
                housing_object_id=obj.get('id'),housing_parent_id=parents[0],
                faces=len(replacement.faces),translation_mm=translation.tolist(),
                max_nearest_old_surface_mm=float(distances.max()),
                face_property_mapping='Nearest old surface; only exterior-appearance classification supported',
                source_geometry_matches=True,placements_and_settings_preserved=True,
                thumbnails='Existing previews retained; re-slice in the slicer',slicer='not_run',physical='not_run')
    report_path.write_text(json.dumps(report,indent=2))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--housing',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=update_project(args.project,args.housing,args.output)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
