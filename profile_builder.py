"""One-shot section measurements for complex contours, not STL triangle encoding.

Sections are polygon/circle sketches. Flat extrusions stay one interval; changing
profiles are subdivided until their boundary movement is below 0.04 mm.
"""
import json
import argparse
from pathlib import Path

import numpy as np
import trimesh
from scipy.optimize import linear_sum_assignment
from analyze import ROOT, NAMES

CANONICAL = [0,1,2,4,6,7,8,9,10,11,12,13,16,17]
AXIS = {1:2,2:2,6:2}


def rdp(points, tolerance=0.004):
    if len(points)<3:
        return points
    v=points[-1]-points[0]
    t=np.clip((points-points[0])@v/(v@v or 1),0,1)
    d=np.linalg.norm(points-(points[0]+t[:,None]*v),axis=1)
    k=int(d.argmax())
    if d[k]<=tolerance:
        return points[[0,-1]]
    return np.vstack([rdp(points[:k+1],tolerance)[:-1],rdp(points[k:],tolerance)])


def simplify_closed(points):
    p=points[:-1]
    k=int(np.linalg.norm(p-p[0],axis=1).argmax())
    return np.vstack([rdp(p[:k+1])[:-1],rdp(np.vstack([p[k:],p[:1]]))[:-1]])


def inside(point, polygon):
    a=polygon; b=np.roll(a,-1,axis=0)
    crossings=(a[:,1]>point[1])!=(b[:,1]>point[1])
    selected=np.where(crossings)[0]
    if not len(selected):
        return False
    aa=a[selected];bb=b[selected]
    xs=(bb[:,0]-aa[:,0])*(point[1]-aa[:,1])/(bb[:,1]-aa[:,1])+aa[:,0]
    return bool(np.count_nonzero(point[0]<xs)%2)


def contour_distance(a,b):
    # Distance to line segments avoids false changes from triangulation split points.
    best=0.0
    for p,q in ((a,b),(b,a)):
        v=np.roll(q,-1,axis=0)-q
        denom=np.einsum('ij,ij->i',v,v)
        for start in range(0,len(p),128):
            d=p[start:start+128,None,:]-q[None,:,:]
            t=np.clip(np.einsum('kij,ij->ki',d,v)/np.maximum(denom,1e-20),0,1)
            distances=np.linalg.norm(d-t[:,:,None]*v[None,:,:],axis=2).min(axis=1)
            best=max(best,float(distances.max()))
    return best


def section(mesh,axis,value):
    normal=np.eye(3)[axis];origin=normal*value
    s=mesh.section(plane_normal=normal,plane_origin=origin)
    if s is None:
        return []
    dims=[0,2] if axis==1 else [0,1]
    loops=[simplify_closed(c[:,dims]) for c in s.discrete if len(c)>3]
    return sorted(loops,key=lambda p:-abs(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))))


def descriptor(p,depth):
    # Recognize complete circles; concave notches and flat-sided bores remain polygons.
    center=(p.max(axis=0)+p.min(axis=0))/2
    radius=np.linalg.norm(p-center,axis=1)
    if len(p)>12 and np.ptp(radius)<0.002:
        return [depth,1,center.round(3).tolist()+[round(float(radius.mean()),3)]]
    size=np.ptp(p,axis=0)
    if min(size)>20:
        corner=p[(p[:,0]<p[:,0].min()+min(size)*0.25)&
                 (p[:,1]>p[:,1].max()-min(size)*0.25)&
                 (p[:,0]>p[:,0].min()+0.002)&(p[:,1]<p[:,1].max()-0.002)]
        if len(corner)>=6:
            cx,cy,c=np.linalg.lstsq(np.c_[2*corner,np.ones(len(corner))],
                                   np.einsum('ij,ij->i',corner,corner),rcond=None)[0]
            fitted=np.sqrt(max(0,c+cx*cx+cy*cy))
            q=np.abs(p-center)-(size/2-fitted)
            sd=np.linalg.norm(np.maximum(q,0),axis=1)+np.minimum(np.max(q,axis=1),0)-fitted
            if 0.1<fitted<min(size)/2 and np.max(np.abs(sd))<0.006:
                return [depth,2,center.round(3).tolist()+size.round(3).tolist()+[round(float(fitted),3)]]
    return [depth,0,p.round(3).tolist()]


def make_layers(mesh,axis):
    # Micrometre plane grid eliminates duplicate/jitter planes that collapse at STL
    # float precision. All consecutive intervals must be represented, without gaps.
    values=np.unique(np.round(mesh.vertices[:,axis],3))
    layers=[]
    previous_loops=None
    for lo,hi in zip(values[:-1],values[1:]):
        a=section(mesh,axis,lo+(hi-lo)*0.001)
        b=section(mesh,axis,hi-(hi-lo)*0.001)
        change=0.0
        if len(a)==len(b):
            # Equal-area symmetric loops can swap order across sections; match spatially.
            ca=np.array([(p.min(axis=0)+p.max(axis=0))/2 for p in a])
            cb=np.array([(p.min(axis=0)+p.max(axis=0))/2 for p in b])
            ea=np.array([np.ptp(p,axis=0) for p in a])
            eb=np.array([np.ptp(p,axis=0) for p in b])
            cost=(np.linalg.norm(ca[:,None,:]-cb[None,:,:],axis=2)+
                  np.linalg.norm(ea[:,None,:]-eb[None,:,:],axis=2)) if len(a) else []
            rows,cols=linear_sum_assignment(cost) if len(a) else ([],[])
            change=max((contour_distance(a[r],b[c]) for r,c in zip(rows,cols)),default=0)
        else:
            change=hi-lo
        count=max(1,int(np.ceil(change/0.04)))
        # The source planar coordinate intervals isolate topology changes.
        for x,y in zip(np.linspace(lo,hi,count+1)[:-1],np.linspace(lo,hi,count+1)[1:]):
            loops=section(mesh,axis,(x+y)/2)
            desc=[]
            for i,p in enumerate(loops):
                depth=sum(inside(p[0],other) for j,other in enumerate(loops) if i!=j)
                desc.append(descriptor(p,depth))
            if desc:
                entry=[round(float(x),6),round(float(y),6),desc]
                if layers and len(loops)==len(previous_loops):
                    ca=np.array([(p.min(axis=0)+p.max(axis=0))/2 for p in loops])
                    cb=np.array([(p.min(axis=0)+p.max(axis=0))/2 for p in previous_loops])
                    ea=np.array([np.ptp(p,axis=0) for p in loops]);eb=np.array([np.ptp(p,axis=0) for p in previous_loops])
                    rows,cols=linear_sum_assignment(np.linalg.norm(ca[:,None,:]-cb[None,:,:],axis=2)+np.linalg.norm(ea[:,None,:]-eb[None,:,:],axis=2))
                    movement=max(contour_distance(loops[r],previous_loops[c]) for r,c in zip(rows,cols))
                    # Reuse one sketch for numerically identical extrusion profiles.
                    if movement<0.006 and abs(layers[-1][1]-entry[0])<1e-5:
                        layers[-1][1]=entry[1]
                        continue
                if layers and layers[-1][2]==entry[2] and abs(layers[-1][1]-entry[0])<1e-5:
                    layers[-1][1]=entry[1]
                else:
                    layers.append(entry)
                    previous_loops=loops
    return layers


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--parts',nargs='+',type=int,default=CANONICAL)
    args=parser.parse_args()
    parts=trimesh.load_mesh(ROOT/'reference/MINI-VAULT.stl').split(only_watertight=False)
    report_path=ROOT/'work/profile-generation.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else []
    report=[r for r in report if r['component'] not in args.parts]
    target=ROOT/'profiles';target.mkdir(exist_ok=True)
    for i in args.parts:
        axis=AXIS.get(i,1)
        layers=make_layers(parts[i],axis)
        filename=target/f'{NAMES[i]}.scad'
        filename.write_text('// Measured section profiles, mm. Source component '+str(i)+'.\n'+
                            '// Boundary simplify tolerance 0.004 mm; layer movement <=0.04 mm.\n'+
                            f'profile_{i} = '+json.dumps(layers,separators=(',',':'))+';\n')
        report.append(dict(component=i,name=NAMES[i],axis=axis,layers=len(layers),bytes=filename.stat().st_size))
        print(i,NAMES[i],len(layers),flush=True)
    report_path.write_text(json.dumps(sorted(report,key=lambda r:r['component']),indent=2))


if __name__=='__main__':
    main()
