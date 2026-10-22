"""True CAD edge treatments. Separate prototype review revision, millimetres.
The archived P5 source is never overwritten. Bearing bores are not deliberately
selected. Geometric validity is not a strength, fit, or safety qualification.
"""
from pathlib import Path
import json,hashlib,time,math
import numpy as np
import cadquery as cq
from cad_core import build,solid
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'assets/design.json').read_text())
DENSITY={'aluminum':2700e-9,'steel':7850e-9,'brass':8500e-9,'rubber':1100e-9,'polymer':1250e-9}

def properties(s,p):
 rho=DENSITY.get(p['material'],2700e-9);b=s.BoundingBox()
 return dict(volume_mm3=s.Volume(),mass_kg=s.Volume()*rho,com_mm=s.Center().toTuple(),inertia_kg_m2=(np.array(cq.Shape.matrixOfInertia(s))*rho*1e-6).tolist(),bounds_mm=[[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]])
def circles(e,min_r=0):
 try:return e.geomType()=='CIRCLE' and e.radius()>min_r
 except:return False

def refine(p):
 original=solid(build(p['shape'])).clean();s=original;ops=[];rejections=[]
 def apply(label,kind,radii,select):
  nonlocal s
  for rad in radii:
   es=[e for e in s.Edges() if select(e)]
   if not es:return
   try:
    r=s.fillet(rad,es) if kind=='fillet' else s.chamfer(rad,None,es)
    if not r.isValid() or len(r.Solids())!=1:raise ValueError('Invalid BREP')
    v=r.Volume()
    if v<=0 or v>s.Volume()*1.000001 or v<s.Volume()*.94:raise ValueError('Unexpected volume change')
    s=solid(r).clean();ops.append(dict(operation=kind,label=label,radius_or_width_mm=rad,selected_edges=len(es)));return
   except Exception as ex:rejections.append(dict(operation=label,radius=rad,error=type(ex).__name__))
 name=p['name'];pid=p['id'];bb=np.array(p['bounds_mm'])
 if 'service_panel' in name:
  thickness=float(np.min(bb[1]-bb[0]))
  apply('rounded panel corners','fillet',[1.2,.8,.4],lambda e:e.geomType()=='LINE' and abs(e.Length()-thickness)<.02)
  apply('panel perimeter edge break','chamfer',[.18,.12,.08],lambda e:e.geomType()=='LINE' and e.Length()>10)
 elif pid in [274,275]:
  minlen=150 if pid==274 else 60
  apply('long outer frame edges','fillet',[.8,.6,.4],lambda e:e.geomType()=='LINE' and e.Length()>minlen and abs(abs(e.Center().x)-30)<.02)
  apply('exposed frame-end perimeter','chamfer',[.35,.2,.12],lambda e:e.geomType()=='LINE' and e.Length()>45 and abs(e.Center().z)>(21.9 if pid==274 else 29.9))
 elif pid==272:
  apply('baseplate vertical corners','fillet',[2.,1.,.6],lambda e:e.geomType()=='LINE' and abs(abs(e.Center().x)-95)<.05 and abs(abs(e.Center().z)-95)<.05)
  apply('baseplate upper perimeter','chamfer',[.8,.5,.25],lambda e:e.geomType()=='LINE' and e.Length()>120 and e.Center().y>1)
 elif pid==277:
  apply('wrist long exterior rail radii','fillet',[.8,.5,.3],lambda e:e.geomType()=='LINE' and e.Length()>90 and abs(abs(e.Center().x)-40)<.03)
 elif pid==273:
  apply('turret mounting-plate outside corners','fillet',[1.,.6,.3],lambda e:e.geomType()=='LINE' and abs(e.Length()-6)<.02 and abs(abs(e.Center().x)-41)<.02 and (abs(e.Center().z+29)<.02 or abs(e.Center().z-33)<.02))
 elif pid==276:
  apply('yoke outside edge breaks','chamfer',[.4,.25,.15],lambda e:e.geomType()=='LINE' and e.Length()>35)
 elif 'structural_heat_spreader_case' in name:
  rr=max((e.radius() for e in s.Edges() if circles(e)),default=0)
  apply('outer flange lip','fillet',[.6,.4,.25],lambda e:circles(e) and abs(e.radius()-rr)<.01)
  apply('housing end cap outer lip','chamfer',[.35,.2,.12],lambda e:circles(e,25) and abs(e.radius()-(rr-4))<.01)
 elif 'rear_service_cover' in name or name.endswith('spring_cover'):
  rr=max((e.radius() for e in s.Edges() if circles(e)),default=0)
  apply('cover outside edge radius','fillet',[.35,.25,.15],lambda e:circles(e) and abs(e.radius()-rr)<.01)
 elif name.endswith('captured_spring_case'):
  rr=max((e.radius() for e in s.Edges() if circles(e)),default=0)
  apply('spring can external rims','fillet',[.5,.35,.2],lambda e:circles(e) and abs(e.radius()-rr)<.01)
 elif 'screw' in p['role'].lower() and ('cover_' in name or 'panel_screw' in name or 'output_bolt' in name):
  planes=[f for f in s.Faces() if f.geomType()=='PLANE']
  if planes:
   face=max(planes,key=lambda f:f.Area());center=face.Center();n=face.normalAt(center);radius=math.sqrt(face.Area()/math.pi)
   if radius>1.:
    wire=cq.Workplane(cq.Plane(origin=center+n*.02,normal=n)).polygon(6,2*radius*.56).val()
    cutter=cq.Solid.extrudeLinear(wire,[],n*(-radius*.52-.03));r=s.cut(cutter).clean()
    if r.isValid() and len(r.Solids())==1 and 0<r.Volume()<s.Volume():
     s=solid(r);ops.append(dict(operation='hex_socket_cut',circumradius_mm=radius*.56,depth_mm=radius*.52))
  rr=max((e.radius() for e in s.Edges() if circles(e)),default=0)
  apply('socket-head rim chamfer','chamfer',[.12,.08,.05],lambda e:circles(e) and abs(e.radius()-rr)<.01)
 else:apply('exposed bracket outer edge break','chamfer',[.25,.15,.08],lambda e:e.geomType()=='LINE' and e.Length()>18)
 if ops:
  outside=sum(x.Volume() for x in s.cut(original).Solids())
  if outside>.001:
   clipped=s.intersect(original).clean()
   if not clipped.isValid() or len(clipped.Solids())!=1:raise ValueError('Envelope preservation produced invalid solid')
   s=solid(clipped)
   ops.append(dict(operation='retain_original_envelope',removed_added_volume_mm3=outside,reason='Keep original internal openings; subtractive exterior refinement only'))
 before=properties(original,p);after=properties(s,p)
 rec=dict(id=pid,name=name,material=p['material'],operations=ops,rejected_attempts=rejections,original=before,refined=after,valid=s.isValid(),solid_count=len(s.Solids()),volume_change_percent=100*(after['volume_mm3']/before['volume_mm3']-1),mechanical_scope='Review geometry; contacts, fits, strength, dynamics not requalified')
 if ops:
  cq.exporters.export(s,str(ROOT/'cad'/f'{pid:03d}-{name}.step'))
  s.exportBrep(str(ROOT/'cad'/f'{pid:03d}.brep'));rec['step']=f'cad/{pid:03d}-{name}.step'
 return rec

def main():
 results=[];start=time.time()
 selected=[p for p in D['parts'] if p['finish']=='paint' or 'service_panel' in p['name'] or 'rear_service_cover' in p['name'] or p['name'].endswith('spring_cover') or ('screw' in p['role'].lower() and ('cover_' in p['name'] or 'panel_screw' in p['name'] or 'output_bolt' in p['name'])) or p['id'] in [235,241,250]]
 for p in selected:
  recfile=ROOT/'reports'/f'cad-{p["id"]:03d}.json'
  if recfile.exists():results.append(json.loads(recfile.read_text()));continue
  try:r=refine(p)
  except Exception as ex:
   r=dict(id=p['id'],name=p['name'],failed=True,error=repr(ex),operations=[])
   (ROOT/'cad'/f'{p["id"]:03d}.brep').unlink(missing_ok=True)
   (ROOT/'cad'/f'{p["id"]:03d}-{p["name"]}.step').unlink(missing_ok=True)
  recfile.write_text(json.dumps(r,indent=2));results.append(r)
  print('CAD',p['id'],p['name'],'operations',len(r['operations']),'valid',r.get('valid'),'elapsed',round(time.time()-start,1),flush=True)
 summary=dict(original_source_sha256=hashlib.sha256((ROOT/'assets/design.json').read_bytes()).hexdigest(),selected_parts=len(selected),modified_parts=sum(bool(r['operations']) for r in results),parts=results)
 (ROOT/'reports/cad-refinement.json').write_text(json.dumps(summary,indent=2));print('DONE',summary['modified_parts'],flush=True)
if __name__=='__main__':main()
