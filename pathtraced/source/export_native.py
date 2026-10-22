"""Export original CAD triangles with crease-split normals, without decimation."""
from pathlib import Path
import struct,json,hashlib
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT.parent
BODY=['fixed_hardware','turret','upper','fore','roll','bend','tool','jaw_left','jaw_right','puck']
FINISH={'paint':0,'darkmetal':1,'metal':2,'steel':3,'brass':4,'pcb':5,'rubber':6,'polymer':7}
parts=json.loads((ROOT/'assets/design.json').read_text())['parts']
vtk.vtkObject.GlobalWarningDisplayOff()
out=ROOT/'assets/native.bin';count=0;input_count=0
with out.open('wb') as f:
 f.write(struct.pack('<II',0x41525850,len(parts)))
 for part in parts:
  m=np.load(ORIGINAL/'assets/meshes'/f'{part["id"]:03}.npz')
  vertices=m['vertices'].astype('f8');faces=m['faces'].astype('i8')
  po=vtk.vtkPoints();po.SetData(numpy_to_vtk(vertices,deep=True))
  ca=vtk.vtkCellArray();ca.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*len(faces)+1,3,dtype='i8'),deep=True),numpy_to_vtkIdTypeArray(faces.ravel(),deep=True))
  poly=vtk.vtkPolyData();poly.SetPoints(po);poly.SetPolys(ca)
  cl=vtk.vtkCleanPolyData();cl.SetInputData(poly);cl.SetTolerance(1e-8)
  ns=vtk.vtkPolyDataNormals();ns.SetInputConnection(cl.GetOutputPort());ns.SetFeatureAngle(35);ns.SplittingOn();ns.ConsistencyOn();ns.ComputePointNormalsOn();ns.Update()
  p=ns.GetOutput();v=vtk_to_numpy(p.GetPoints().GetData())*.001;n=vtk_to_numpy(p.GetPointData().GetNormals());tri=vtk_to_numpy(p.GetPolys().GetConnectivityArray()).reshape(-1,3)
  input_count+=len(faces)
  if len(tri)!=len(faces):print('degenerate triangle cleanup',part['id'],len(faces)-len(tri))
  rows=np.concatenate([v[tri[:,0]],v[tri[:,1]],v[tri[:,2]],n[tri[:,0]],n[tri[:,1]],n[tri[:,2]]],axis=1).astype('<f4')
  body=BODY.index('fixed_hardware' if part['body']=='fixed' else part['body'])
  f.write(struct.pack('<IIII',part['id'],body,FINISH[part['finish']],len(rows)));f.write(rows.tobytes());count+=len(rows)
print('Exported',count,'triangles',out.stat().st_size,'bytes')
report={'geometry_sha256':hashlib.sha256((ROOT/'assets/design.json').read_bytes()).hexdigest(),'parts':len(parts),'triangles':count,'decimation':False,'input_triangles':input_count,'degenerate_triangle_cleanup':input_count-count,'source':'Canonical compact P5, same CAD tessellations as delivered cinematic package','native_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'normal_treatment':'35-degree split smoothing; vertex positions unchanged'}
(ROOT/'reports/geometry.json').write_text(json.dumps(report,indent=2))
