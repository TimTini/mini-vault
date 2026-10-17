"""Split existing raised dial marks into a second material; preserve source solid."""
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile
import manifold3d as mf
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from exporter import source_hashes

def solid(mesh):
    s=mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices,dtype=np.float64),np.asarray(mesh.faces,dtype=np.uint64)))
    assert s.status()==mf.Error.NoError
    return s

def mesh(body):
    d=body.to_mesh64()
    m=trimesh.Trimesh(d.vert_properties[:,:3],d.tri_verts,process=False)
    assert m.is_volume
    return m

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    source=ROOT/'work/rendered-parts/scale-100-200/dial.stl'
    sources=source_hashes()
    preset_path=ROOT/'mini-vault.json'
    preset=json.loads(preset_path.read_text())['parameterSets']['200 - scale 1']
    manifest_path=ROOT/'exports/mini-vault-200-scale-1-print.verification.json'
    manifest=json.loads(manifest_path.read_text())
    assert manifest['parameters']==preset and float(preset['size_scale'])==1
    assert manifest['source_hashes']==sources
    assert manifest['parts']['dial']['source_sha256']==digest(source)
    metadata=json.loads(source.with_suffix('.export.json').read_text())
    assert metadata['source_hashes']==sources
    original=trimesh.load_mesh(source);body=solid(original)
    # The raised layer is .4 mm; its absolute Y changes with door thickness.
    # Snap to the actual STL plane so float32 rounding cannot add a thin body skin.
    expected=original.bounds[0,1]+.4
    planes=np.unique(original.vertices[:,1])
    split_y=float(planes[np.argmin(abs(planes-expected))])
    assert abs(split_y-expected)<1e-5
    # Inset the color seam 1e-6 mm into the relief, avoiding a coplanar body film.
    # Both parts still partition the exact original solid without a physical gap.
    split_y-=.000001
    marks=body.trim_by_plane([0,-1,0],-split_y)
    base=body.trim_by_plane([0,1,0],split_y)
    assert marks.volume()>0 and base.volume()>0
    assert abs((marks^base).volume())<1e-8
    merged=marks+base
    assert abs((merged-body).volume())<1e-7 and abs((body-merged).volume())<1e-7
    parts=[mesh(base),mesh(marks)]
    transform=np.eye(4);transform[:3,:3]=[[1,0,0],[0,0,1],[0,-1,0]]
    posed=original.copy();posed.apply_transform(transform);transform[:3,3]=-posed.bounds[0]
    for p in parts:p.apply_transform(transform)
    core='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    ET.register_namespace('',core)
    tag=lambda n:f'{{{core}}}{n}'
    model=ET.Element(tag('model'),unit='millimeter')
    ET.SubElement(model,tag('metadata'),name='Application').text='MINI-VAULT colored dial'
    ET.SubElement(model,tag('metadata'),name='BambuStudio:3mfVersion').text='1'
    resources=ET.SubElement(model,tag('resources'))
    materials=ET.SubElement(resources,tag('basematerials'),id='10')
    for name,color in [('Body black','#101010FF'),('Numbers and ticks white','#FFFFFFFF')]:
        ET.SubElement(materials,tag('base'),name=name,displaycolor=color)
    names=['Dial body - black','Numbers and ticks - white']
    for i,p in enumerate(parts):
        obj=ET.SubElement(resources,tag('object'),id=str(i+1),type='model',name=names[i],pid='10',pindex=str(i))
        data=ET.SubElement(obj,tag('mesh'));verts=ET.SubElement(data,tag('vertices'));tris=ET.SubElement(data,tag('triangles'))
        for v in p.vertices:ET.SubElement(verts,tag('vertex'),**dict(zip('xyz',[format(float(x),'.15g') for x in v])))
        for f in p.faces:ET.SubElement(tris,tag('triangle'),v1=str(f[0]),v2=str(f[1]),v3=str(f[2]))
    assembly=ET.SubElement(resources,tag('object'),id='3',type='model',name='MINI-VAULT 200 scale1 colored dial')
    components=ET.SubElement(assembly,tag('components'))
    for i in [1,2]:ET.SubElement(components,tag('component'),objectid=str(i))
    ET.SubElement(ET.SubElement(model,tag('build')),tag('item'),objectid='3')
    config=ET.Element('config');obj=ET.SubElement(config,'object',id='3')
    ET.SubElement(obj,'metadata',key='name',value='MINI-VAULT 200 scale1 colored dial')
    ET.SubElement(obj,'metadata',key='extruder',value='1')
    for i,name in enumerate(names):
        part=ET.SubElement(obj,'part',id=str(i+1),subtype='normal_part')
        ET.SubElement(part,'metadata',key='name',value=name)
        ET.SubElement(part,'metadata',key='extruder',value=str(i+1))
    content=b'<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="application/xml"/></Types>'
    rels=b'<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    output=ROOT/'exports/mini-vault-200-scale-1-dial-black-white.3mf'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content);z.writestr('_rels/.rels',rels)
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/model_settings.config',ET.tostring(config,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/project_settings.config',json.dumps({'filament_colour':['#101010','#FFFFFF']}))
    # Fresh XML/mesh reload verifies both material volumes and the assembled union.
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        xml=ET.fromstring(z.read('3D/3dmodel.model'));checked=[]
        for obj in xml.findall(f'{tag("resources")}/{tag("object")}'):
            data=obj.find(tag('mesh'))
            if data is None:continue
            vs=[[float(v.attrib[a]) for a in 'xyz'] for v in data.find(tag('vertices'))]
            fs=[[int(f.attrib[a]) for a in ['v1','v2','v3']] for f in data.find(tag('triangles'))]
            checked.append(solid(trimesh.Trimesh(vs,fs,process=False)))
        assert len(checked)==2
        target=mesh(body);target.apply_transform(transform)
        joined=checked[0]+checked[1];expected=solid(target)
        assert abs((joined-expected).volume())<1e-7 and abs((expected-joined).volume())<1e-7
    assert source_hashes()==sources and manifest['parts']['dial']['source_sha256']==digest(source)
    assert json.loads(preset_path.read_text())['parameterSets']['200 - scale 1']==preset
    report=dict(output=str(output),sha256=digest(output),source_sha256=digest(source),source_hashes=sources,
                parameters=preset,preset_sha256=digest(preset_path),source_manifest_sha256=digest(manifest_path),
                exporter_sha256=digest(Path(__file__)),split_plane_source_y_mm=split_y,
                parts=[dict(name=n,filament=i+1,color=['#101010','#FFFFFF'][i],volume_mm3=float(p.volume),components=len(p.split()),bounds_mm=p.bounds.tolist()) for i,(n,p) in enumerate(zip(names,parts))],
                union_matches_source=True,overlap_mm3=abs((checked[0]^checked[1]).volume()),marks_thickness_mm=float(parts[1].extents[2]),
                slicer='pending',physical='not_run')
    output.with_suffix('.verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
