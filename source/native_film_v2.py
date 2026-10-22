"""P5 native CAD cinematic capture. No image synthesis or frame interpolation.
The geometry is tessellated from the supplied 278-part CSG source; rigid motion
comes from assets/capture.json. VTK uses GLSL PBR shading rather than the
single-pass constructive ray tracer. Every delivered frame is rendered anew.
"""
from pathlib import Path
import os,time,json,math,subprocess,argparse,hashlib
import numpy as np
import vtk
vtk.vtkObject.GlobalWarningDisplayOff()
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from PIL import Image
from geometry import ROOT,Scene,BODIES

def normalize(x):
 x=np.array(x,float);return x/np.linalg.norm(x)

def environment():
 w,h=1024,512
 phi=np.linspace(-math.pi,math.pi,w,endpoint=False)[None,:];theta=np.linspace(0,math.pi,h)[:,None]
 dirs=np.stack(np.broadcast_arrays(np.sin(theta)*np.sin(phi),np.cos(theta),np.sin(theta)*np.cos(phi)),axis=-1)
 data=np.empty((h,w,3),np.float32)
 data[:]=(.006,.009,.015)
 data+=np.maximum(dirs[:,:,1,None],0)**1.8*np.array([.018,.020,.026])
 horizon=np.exp(-((dirs[:,:,1]+0.08)/0.22)**2)
 back=np.clip((dirs[:,:,2]+0.15)*0.5+0.5,0,1)
 data+=horizon[:,:,None]*back[:,:,None]*np.array([.010,.013,.018])
 for direction,width,height,radiance,gain in [
  ([-1.05,1.9,.95],.18,.30,[10.8,10.2,9.1],1.0),
  ([1.35,1.15,.35],.12,.42,[2.6,3.4,4.8],0.75),
  ([-.10,.55,-1.25],.26,.18,[1.6,1.9,2.4],0.55),
  ([0.0,-1.0,0.0],.65,.65,[.10,.10,.12],0.20),
 ]:
  z=normalize(direction);x=normalize(np.cross(z,[0,1,0]) if abs(z[1])<0.98 else np.cross(z,[1,0,0]));y=np.cross(x,z)
  ax=np.arctan2(dirs@x,dirs@z);ay=np.arctan2(dirs@y,dirs@z)
  dist=np.maximum(np.abs(ax)/width,np.abs(ay)/height)
  box=np.clip((1.0-dist)/.12,0,1);box=box*box*(3-2*box);box*=((dirs@z)>0)
  data+=box[:,:,None]*np.array(radiance)*gain
 data=np.clip(data,0,None)
 image=vtk.vtkImageData();image.SetDimensions(w,h,1)
 image.GetPointData().SetScalars(numpy_to_vtk(np.ascontiguousarray(data[::-1].reshape(-1,3)),deep=True,array_type=vtk.VTK_FLOAT))
 texture=vtk.vtkTexture();texture.SetInputData(image);texture.SetColorModeToDirectScalars();texture.InterpolateOn();texture.MipmapOn()
 return texture

class Renderer:
 def __init__(self,w,h,quality=1):
  self.w,self.h=w,h;self.scene=Scene();self.parts=self.scene.parts
  self.window=vtk.vtkEGLRenderWindow();self.window.SetOffScreenRendering(1);self.window.SetSize(w,h);self.window.SetMultiSamples(0)
  self.ren=vtk.vtkRenderer();self.window.AddRenderer(self.ren);r=self.ren
  r.SetBackground(.004,.006,.010);r.SetBackground2(.010,.014,.022);r.GradientBackgroundOn();r.SetAutomaticLightCreation(False)
  r.UseImageBasedLightingOn();self.env=environment();r.SetEnvironmentTexture(self.env,False);r.UseSphericalHarmonicsOn();r.SetEnvironmentUp(0,1,0);r.SetEnvironmentRight(1,0,0)
  r.UseFXAAOff();r.UseSSAOOn();r.SetSSAORadius(6.);r.SetSSAOBias(.30);r.SetSSAOKernelSize(24 if quality else 12);r.SSAOBlurOn()
  self.actors=[];self.transforms=[];self.poly=[]
  material={
   'paint':((.80,.80,.78),.00,.16,.62),
   'darkmetal':((.022,.025,.030),.78,.18,.0),
   'metal':((.72,.73,.75),1.,.17,.0),
   'steel':((.60,.62,.65),1.,.16,.0),
   'brass':((.70,.46,.20),1.,.18,.0),
   'pcb':((.018,.10,.055),.08,.38,.0),
   'rubber':((.010,.012,.014),0.,.52,.0),
   'polymer':((.018,.020,.024),0.,.40,.0),
  }
  total=0
  for p in self.parts:
   f=ROOT/'assets/meshes'/f"{p['id']:03d}.npz"
   if not f.exists():raise FileNotFoundError(f)
   d=np.load(f);v=d['vertices'];faces=d['faces'];total+=len(faces)
   points=vtk.vtkPoints();points.SetData(numpy_to_vtk(v,deep=True))
   cells=vtk.vtkCellArray();flat=np.c_[np.full(len(faces),3,dtype=np.int64),faces].ravel().astype(np.int64)
   cells.SetCells(len(faces),numpy_to_vtkIdTypeArray(flat,deep=True));poly=vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(cells)
   clean=vtk.vtkCleanPolyData();clean.SetInputData(poly);clean.SetTolerance(1e-7)
   normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(clean.GetOutputPort());normals.SetFeatureAngle(35);normals.SplittingOn();normals.ConsistencyOn();normals.ComputePointNormalsOn();normals.Update()
   mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(normals.GetOutput());mapper.ScalarVisibilityOff()
   actor=vtk.vtkActor();actor.SetMapper(mapper);prop=actor.GetProperty();prop.SetInterpolationToPBR();color,metal,rough,coat=material[p['finish']]
   prop.SetColor(*color);prop.SetMetallic(metal);prop.SetRoughness(rough);prop.SetCoatStrength(coat);prop.SetCoatRoughness(.21);prop.SetCoatIOR(1.48)
   r.AddActor(actor);self.actors.append(actor);self.transforms.append(vtk.vtkMatrix4x4());self.poly.append(normals)
  print('native triangles',total,flush=True)
  # The studio ground is presentation scenery, not part of the mechanical model.
  ground=vtk.vtkPlaneSource();ground.SetOrigin(-10000,-.2,-10000);ground.SetPoint1(-10000,-.2,10000);ground.SetPoint2(10000,-.2,-10000);ground.Update()
  gm=vtk.vtkPolyDataMapper();gm.SetInputData(ground.GetOutput());ga=vtk.vtkActor();ga.SetMapper(gm);prop=ga.GetProperty();prop.SetInterpolationToPBR();prop.SetColor(.018,.022,.029);prop.SetMetallic(.05);prop.SetRoughness(.26);prop.SetCoatStrength(.06);r.AddActor(ga);self.ground=ga
  # Direct lights give real cast shadows in addition to the studio reflection map.
  self.lights=[]
  for position,color,intensity,cone in [((-880,1180,760),(1.00,.96,.90),3.0,34),((860,760,280),(.68,.80,1.00),1.05,28),((-120,520,-1040),(.85,.92,1.0),0.70,40)]:
   light=vtk.vtkLight();light.SetLightTypeToSceneLight();light.SetPosition(*position);light.SetFocalPoint(150,220,0);light.SetColor(*color);light.SetIntensity(intensity);light.SetPositional(True);light.SetConeAngle(cone);light.SetExponent(12);light.SetAttenuationValues(1,0,0);r.AddLight(light);self.lights.append(light)
  r.UseShadowsOn()
  shadow=vtk.vtkShadowMapPass();shadow.GetShadowMapBakerPass().SetResolution(2048)
  passes=vtk.vtkRenderPassCollection();passes.AddItem(shadow.GetShadowMapBakerPass());passes.AddItem(shadow)
  seq=vtk.vtkSequencePass();seq.SetPasses(passes);camPass=vtk.vtkCameraPass();camPass.SetDelegatePass(seq)
  ssao=vtk.vtkSSAOPass();ssao.SetDelegatePass(camPass);ssao.SetRadius(4.2);ssao.SetBias(.50);ssao.SetKernelSize(32);ssao.BlurOn()
  tone=vtk.vtkToneMappingPass();tone.SetToneMappingType(vtk.vtkToneMappingPass.GenericFilmic);tone.SetGenericFilmicDefaultPresets();tone.SetExposure(1.00);tone.SetUseACES(True);tone.SetDelegatePass(ssao)
  dof=vtk.vtkDepthOfFieldPass();dof.SetAutomaticFocalDistance(False);dof.SetDelegatePass(ssao);tone.SetDelegatePass(ssao)
  r.SetPass(tone);self.passes=[shadow,passes,seq,camPass,ssao,dof,tone]
  camera=r.GetActiveCamera();camera.SetViewUp(0,1,0);camera.SetClippingRange(1,10000)
  self.cap=vtk.vtkWindowToImageFilter();self.cap.SetInput(self.window);self.cap.SetInputBufferTypeToRGB();self.cap.ReadFrontBufferOff();self.cap.ShouldRerenderOff()
  self.total_triangles=total
  self._disassembly_cache={}
 def _disassembly_phase(self,p):
  # Heuristic inspection staging, NOT a collision-checked physical teardown.
  name=p['name']; role=p['role']; group=p['group']
  def chain_rank():
   if group=='fixtures': return 0.0
   if group=='gripper': return 0.4
   if group=='J6': return 1.2
   if group=='J5': return 2.0
   if group=='J4': return 3.0
   if group=='CB3': return 3.8
   if group=='J3': return 4.2
   if group=='structure':
    if name.startswith('fore_') or name.startswith('wrist_') or name=='wrist_idle_bearing' or name=='wrist_idle_trunnion': return 3.4
    if name.startswith('upper_'): return 5.2
    if name.startswith('base_') or name.startswith('turret_'): return 7.6
    return 5.0
   if group=='CB2': return 5.8
   if group=='J2': return 6.2
   if group=='J1': return 7.2
   if group=='base': return 8.2
   return 6.0
  def local_rank():
   t=(name+' '+role).lower()
   if 'workpiece' in t or 'nest_' in t: return 0.00
   if 'screw' in t or 'bolt' in t or 'nut' in t or 'clamp' in t: return 0.00
   if 'cover' in t or 'panel' in t or 'cap' in t: return 0.12
   if 'encoder' in t or 'board' in t or 'magnet' in t: return 0.22
   if 'brake' in t: return 0.30
   if 'spring' in t or 'reaction pin' in t or 'reaction arbor' in t: return 0.36
   if 'motor' in t or 'rotor' in t or 'stator' in t or 'bearing' in t or 'bushing' in t: return 0.46
   if 'reducer' in t or 'bulkhead' in t or 'carrier' in t: return 0.58
   if 'guide rod' in t or 'jaw' in t or 'rack' in t or 'finger pad' in t or 'carriage' in t or 'bridge' in t or 'mount neck' in t: return 0.68
   if 'adapter' in t or 'frame' in t or 'yoke' in t or 'weldment' in t or 'case' in t or 'shell' in t: return 0.80
   return 0.55
  start=0.05+0.085*chain_rank()+0.11*local_rank()
  duration=0.12 if group not in {'J1','J2','J3','J4','J5','J6'} else 0.10
  return min(start,0.95), min(start+duration,1.0)

 def _inspection_factor(self,p,progress):
  if progress<=0: return 0.0
  key=p['id']
  if key not in self._disassembly_cache:
   self._disassembly_cache[key]=self._disassembly_phase(p)
  start,end=self._disassembly_cache[key]
  if progress<=start: return 0.0
  if progress>=end: return 1.0
  return smooth((progress-start)/max(end-start,1e-6))

 def update(self,t,explode=0,visibility=None):
  mats,pos=self.scene.pose(t);self.scene.mats=mats;self.scene.pos=pos
  progress=float(np.clip(explode,0,1))
  for i,(actor,p) in enumerate(zip(self.actors,self.parts)):
   b=BODIES.index('fixed_hardware' if p['body']=='fixed' else p['body']);R=mats[b]
   local=np.array(p['explode_mm'],float)
   if np.linalg.norm(local)<1e-9:
    n=(p['name']+' '+p['role']).lower()
    if 'bearing' in n or 'bushing' in n: local=np.array([0.0,26.0,0.0])
    elif 'workpiece' in n: local=np.array([0.0,55.0,0.0])
    else: local=np.array([0.0,34.0,0.0])
   factor=self._inspection_factor(p,progress)
   o=pos[b]+R@(local*factor)
   A=self.transforms[i]
   for j in range(3):
    for k in range(3):A.SetElement(j,k,float(R[j,k]))
    A.SetElement(j,3,float(o[j]))
   actor.SetUserMatrix(A);actor.SetVisibility(visibility is None or p['id'] in visibility)
 def render(self,t,eye,target,angle=31,explode=0,visibility=None):
  self.update(t,explode,visibility)
  self.ground.SetPosition(0,-230*explode,0)
  c=self.ren.GetActiveCamera();c.SetPosition(*eye);c.SetFocalPoint(*target);c.SetViewAngle(angle);c.SetClippingRange(2,50000);c.SetFocalDistance(float(np.linalg.norm(np.array(eye)-target)));c.SetFocalDisk(4.0 if np.linalg.norm(np.array(eye)-target)<600 else 1.8)
  self.window.Render();self.cap.Modified();self.cap.Update()
  out=vtk_to_numpy(self.cap.GetOutput().GetPointData().GetScalars()).reshape(self.h,self.w,3)
  return np.ascontiguousarray(out[::-1])
 def close(self):self.window.Finalize()

def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def orbit(target,distance,azimuth,elevation):
 a=np.deg2rad(azimuth);e=np.deg2rad(elevation)
 return np.array(target)+distance*np.array([math.cos(e)*math.sin(a),math.sin(e),math.cos(e)*math.cos(a)])

# A real edited sequence: a complete continuous transfer followed by detail coverage.
SHOTS=[
 dict(name='Reveal',duration=3.0),
 dict(name='Pick transfer return',duration=10.0),
 dict(name='Precision grip',duration=4.0),
 dict(name='Compact elbow',duration=3.0),
 dict(name='Exploded architecture',duration=5.0),
 dict(name='Reassembly hero',duration=3.0),
]

def shot_state(index,local,renderer):
 u=local/SHOTS[index]['duration'];s=smooth(u)
 if index==0:
  t=1.6+.7*u;target=np.array([150,225,0]);m,_=renderer.scene.pose(t);yaw=math.degrees(math.atan2(m[1,2,0],m[1,0,0]));eye=orbit(target,1120-50*s,12-yaw+5*s,20+2*s);angle=33;explode=0
 elif index==1:
  t=min(local,9.999);target=np.array([155,215,0]);m,_=renderer.scene.pose(t);yaw=math.degrees(math.atan2(m[1,2,0],m[1,0,0]));eye=orbit(target,1150,12-yaw,20+2*math.sin(math.pi*u));angle=33;explode=0
 elif index==2:
  t=.50+1.48*u;m,p=renderer.scene.pose(t);i=BODIES.index('tool');tcp=p[i]+m[i]@np.array([0,172,0]);target=tcp+np.array([0,35,0]);eye=target+np.array([305+25*s,105,330-35*s]);angle=31;explode=0
 elif index==3:
  t=1.7+1.1*u;m,p=renderer.scene.pose(t);i=BODIES.index('fore');target=p[i]+np.array([0,0,38]);eye=orbit(target,430,35-15*u,10+8*u);angle=32;explode=0
 elif index==4:
  t=2.5;explode=smooth(u);target=np.array([165,225,0]);eye=orbit(target,1040+160*s,-28+24*u,15+2*s);angle=32
 else:
  t=2.5;explode=1-smooth(u);target=np.array([145-22*s,218-8*s,-5+8*s]);eye=orbit(target,1180-150*s,-6-2*s,17+3*s);angle=31
 return t,eye,target,angle,explode

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--width',type=int,default=1920);ap.add_argument('--height',type=int,default=1080);ap.add_argument('--still',action='store_true');ap.add_argument('--shot',type=int,default=-1);ap.add_argument('--fps',type=int,default=24);args=ap.parse_args()
 start=time.time();r=Renderer(args.width,args.height);print('setup seconds',time.time()-start,flush=True)
 if args.still:
  for i in range(6):
   state=shot_state(i,SHOTS[i]['duration']*.5,r);a=r.render(*state);Image.fromarray(a).save(ROOT/f'native-test-{i}.png');print('still',i,'elapsed',round(time.time()-start,2),flush=True)
  r.close();return
 todo=range(len(SHOTS)) if args.shot<0 else [args.shot]
 for idx in todo:
  shot=SHOTS[idx];frames=round(shot['duration']*args.fps);output=ROOT/'shots'/f'{idx+1:02d}-{shot["name"].replace(" ","-")}.mp4'
  cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{args.width}x{args.height}','-r',str(args.fps),'-i','-','-an','-c:v','libx264','-threads','2','-preset','medium','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE);report=[]
  for f in range(frames):
   local=f/args.fps;state=shot_state(idx,local,r);a=r.render(*state);proc.stdin.write(a.tobytes());report.append({'frame':f,'film_time':local,'simulation_time':state[0],'eye':state[1].tolist(),'target':state[2].tolist(),'explode':float(state[4]),'rgb_sha256':hashlib.sha256(a.tobytes()).hexdigest()})
   if f%(args.fps)==0:print('SHOT',idx+1,'frame',f,'/',frames,'elapsed',round(time.time()-start,1),flush=True)
  proc.stdin.close();code=proc.wait()
  if code:raise RuntimeError('FFmpeg failed '+str(code))
  (ROOT/'reports'/f'shot-{idx+1:02d}.json').write_text(json.dumps({'shot':shot,'resolution':[args.width,args.height],'fps':args.fps,'frames':report,'triangles':r.total_triangles},indent=2))
  print('COMPLETED',output,output.stat().st_size,flush=True)
 r.close()
if __name__=='__main__':main()
