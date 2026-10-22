"""Exact BREP outside-volume screen on modified parts, not an assembly motion test."""
from pathlib import Path
import json,time
import cadquery as cq
from cad_core import build
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'assets/design.json').read_text());R=json.loads((ROOT/'reports/cad-refinement.json').read_text());records=[];start=time.time()
for rec in R['parts']:
 if not rec['operations']:continue
 p=D['parts'][rec['id']];old=build(p['shape']).clean();new=cq.Shape.importBrep(str(ROOT/'cad'/f'{p["id"]:03d}.brep'))
 try:
  outside=new.cut(old);vol=sum(x.Volume() for x in outside.Solids());passed=vol<.01
  records.append(dict(id=p['id'],name=p['name'],outside_original_volume_mm3=vol,below_0p01_mm3=passed))
 except Exception as ex:records.append(dict(id=p['id'],name=p['name'],failed=True,error=type(ex).__name__))
 if p['id']%20==0:print('ENVELOPE',p['id'],'seconds',round(time.time()-start,1),flush=True)
report=dict(parts_checked=len(records),all_below_0p01_mm3=all(r.get('below_0p01_mm3',False) for r in records),parts=records,scope='Material outside the original part BREP; not continuous swept clearance, strength, or tolerance validation')
(ROOT/'reports/envelope-screen.json').write_text(json.dumps(report,indent=2));print('DONE',report['all_below_0p01_mm3'],flush=True)
