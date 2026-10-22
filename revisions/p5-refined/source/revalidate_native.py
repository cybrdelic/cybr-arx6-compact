"""Replace only changed BREP-derived triangles in native ray-tracing cache."""
from pathlib import Path
import struct,json,hashlib,time
import numpy as np
import cadquery as cq
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
vtk.vtkObject.GlobalWarningDisplayOff()
ROOT=Path(__file__).resolve().parents[1]
def smooth_normals(s):
 vertices,faces=s.tessellate(.012,.065)
 v=np.array([x.toTuple() for x in vertices],dtype='f8');faces=np.asarray(faces,dtype='i8')
 po=vtk.vtkPoints();po.SetData(numpy_to_vtk(v,deep=True));cells=vtk.vtkCellArray()
 cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*len(faces)+1,3,dtype='i8'),deep=True),numpy_to_vtkIdTypeArray(faces.ravel(),deep=True))
 poly=vtk.vtkPolyData();poly.SetPoints(po);poly.SetPolys(cells)
 cl=vtk.vtkCleanPolyData();cl.SetInputData(poly);cl.SetTolerance(1e-9)
 ns=vtk.vtkPolyDataNormals();ns.SetInputConnection(cl.GetOutputPort());ns.SetFeatureAngle(30);ns.SplittingOn();ns.ConsistencyOn();ns.ComputePointNormalsOn();ns.Update()
 p=ns.GetOutput();v=vtk_to_numpy(p.GetPoints().GetData())*.001;n=vtk_to_numpy(p.GetPointData().GetNormals());tri=vtk_to_numpy(p.GetPolys().GetConnectivityArray()).reshape(-1,3)
 rows=np.concatenate([v[tri[:,0]],v[tri[:,1]],v[tri[:,2]],n[tri[:,0]],n[tri[:,1]],n[tri[:,2]]],axis=1).astype('<f4')
 return rows
start=time.time();records=[]
with open(ROOT/'assets/native.bin','rb') as src,open(ROOT/'assets/revalidated-native.bin','wb') as dst:
 header=src.read(8);magic,count=struct.unpack('<II',header);assert magic==0x41525850;dst.write(header)
 for i in range(count):
  h=src.read(16);pid,body,mat,nt=struct.unpack('<IIII',h);raw=src.read(nt*72)
  path=ROOT/'cad'/f'{pid:03d}.brep'
  if path.exists():
   s=cq.Shape.importBrep(str(path));rows=smooth_normals(s)
   assert rows.shape[1]==18 and np.isfinite(rows).all()
   dst.write(struct.pack('<IIII',pid,body,mat,len(rows)));dst.write(rows.tobytes())
   records.append(dict(id=pid,original_triangles=nt,refined_triangles=len(rows),brep_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
  else:dst.write(h);dst.write(raw)
  if i%30==0:print('TESSELLATED',i,'seconds',round(time.time()-start,1),flush=True)
report=dict(part_instances=count,changed_instances=len(records),linear_deflection_mm=.012,angular_deflection_rad=.065,unchanged_parts_byte_preserved=True,parts=records,refined_native_sha256=hashlib.sha256((ROOT/'assets/revalidated-native.bin').read_bytes()).hexdigest())
(ROOT/'reports/revalidation-tessellation.json').write_text(json.dumps(report,indent=2));print('DONE',round(time.time()-start,1),flush=True)
