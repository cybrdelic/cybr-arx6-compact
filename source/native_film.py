"""P5 native CAD cinematic capture. No image synthesis or frame interpolation.
The geometry is tessellated from the supplied 278-part CSG source; rigid motion
comes from assets/capture.json. VTK uses GLSL PBR shading rather than the
single-pass constructive ray tracer. Every delivered frame is rendered anew.
"""
from pathlib import Path
import os,time,json,math,subprocess,argparse,hashlib
import numpy as np
import vtk
from render_backend import create_render_window
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from PIL import Image
from geometry import ROOT,Scene,BODIES

def normalize(x):
 x=np.array(x,float);return x/np.linalg.norm(x)

def environment():
 w,h=768,384
 phi=np.linspace(-math.pi,math.pi,w,endpoint=False)[None,:];theta=np.linspace(0,math.pi,h)[:,None]
 dirs=np.stack(np.broadcast_arrays(np.sin(theta)*np.sin(phi),np.cos(theta),np.sin(theta)*np.cos(phi)),axis=-1)
 data=np.empty((h,w,3),np.float32);data[:]=(.045,.050,.065)
 data+=np.maximum(dirs[:,:,1,None],0)*np.array([.07,.075,.085])
 for direction,width,height,radiance in [([-1,1.5,.8],.38,.52,[4.4,4.15,3.8]),([1.2,.7,.6],.25,.65,[1.6,1.85,2.2]),([0,.8,-1],.30,.55,[3.0,3.3,3.7])]:
  z=normalize(direction);x=normalize(np.cross(z,[0,1,0]));y=np.cross(x,z)
  ax=np.arctan2(dirs@x,dirs@z);ay=np.arctan2(dirs@y,dirs@z)
  dist=np.maximum(np.abs(ax)/width,np.abs(ay)/height)
  box=np.clip((1.04-dist)/.08,0,1);box=box*box*(3-2*box);box*=((dirs@z)>0)
  data+=box[:,:,None]*np.array(radiance)*.65
 # VTK panorama treats the first row as the lower image boundary.
 image=vtk.vtkImageData();image.SetDimensions(w,h,1)
 image.GetPointData().SetScalars(numpy_to_vtk(np.ascontiguousarray(data[::-1].reshape(-1,3)),deep=True,array_type=vtk.VTK_FLOAT))
 texture=vtk.vtkTexture();texture.SetInputData(image);texture.SetColorModeToDirectScalars();texture.InterpolateOn();texture.MipmapOn()
 return texture

class Renderer:
 def __init__(self,w,h,quality=1):
  self.w,self.h=w,h;self.scene=Scene();self.parts=self.scene.parts
  self.window=create_render_window(vtk);self.window.SetOffScreenRendering(1);self.window.SetSize(w,h);self.window.SetMultiSamples(0)
  self.ren=vtk.vtkRenderer();self.window.AddRenderer(self.ren);r=self.ren
  r.SetBackground(.012,.015,.021);r.SetBackground2(.033,.040,.050);r.GradientBackgroundOn();r.SetAutomaticLightCreation(False)
  r.UseImageBasedLightingOn();self.env=environment();r.SetEnvironmentTexture(self.env,False);r.UseSphericalHarmonicsOn();r.SetEnvironmentUp(0,1,0);r.SetEnvironmentRight(1,0,0)
  r.UseFXAAOff();r.UseSSAOOn();r.SetSSAORadius(9.);r.SetSSAOBias(.35);r.SetSSAOKernelSize(32 if quality else 16);r.SSAOBlurOn()
  self.actors=[];self.transforms=[];self.poly=[]
  material={
   'paint':((.70,.69,.64),.02,.26,.45),
   'darkmetal':((.028,.034,.041),.75,.26,.0),
   'metal':((.69,.71,.73),1.,.21,.0),
   'steel':((.51,.55,.59),1.,.20,.0),
   'brass':((.80,.49,.18),1.,.20,.0),
   'pcb':((.015,.09,.05),.1,.42,.0),
   'rubber':((.012,.014,.017),0.,.64,.0),
   'polymer':((.014,.016,.018),0.,.54,.0),
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
  gm=vtk.vtkPolyDataMapper();gm.SetInputData(ground.GetOutput());ga=vtk.vtkActor();ga.SetMapper(gm);prop=ga.GetProperty();prop.SetInterpolationToPBR();prop.SetColor(.037,.043,.052);prop.SetMetallic(.15);prop.SetRoughness(.32);r.AddActor(ga);self.ground=ga
  # Direct lights give real cast shadows in addition to the studio reflection map.
  self.lights=[]
  for position,color,intensity in [((-650,1050,600),(1,.94,.84),2.0),((750,650,350),(.80,.89,1),.65),((100,850,-850),(.84,.91,1),1.4)]:
   light=vtk.vtkLight();light.SetLightTypeToSceneLight();light.SetPosition(*position);light.SetFocalPoint(130,220,0);light.SetColor(*color);light.SetIntensity(intensity);light.SetPositional(True);light.SetConeAngle(55);light.SetExponent(2);light.SetAttenuationValues(1,0,0);r.AddLight(light);self.lights.append(light)
  r.UseShadowsOn()
  shadow=vtk.vtkShadowMapPass();shadow.GetShadowMapBakerPass().SetResolution(2048)
  passes=vtk.vtkRenderPassCollection();passes.AddItem(shadow.GetShadowMapBakerPass());passes.AddItem(shadow)
  seq=vtk.vtkSequencePass();seq.SetPasses(passes);camPass=vtk.vtkCameraPass();camPass.SetDelegatePass(seq)
  ssao=vtk.vtkSSAOPass();ssao.SetDelegatePass(camPass);ssao.SetRadius(7.);ssao.SetBias(1.0);ssao.SetKernelSize(64);ssao.BlurOn()
  tone=vtk.vtkToneMappingPass();tone.SetToneMappingType(vtk.vtkToneMappingPass.GenericFilmic);tone.SetGenericFilmicDefaultPresets();tone.SetExposure(.85);tone.SetUseACES(True);tone.SetDelegatePass(ssao)
  dof=vtk.vtkDepthOfFieldPass();dof.SetAutomaticFocalDistance(False);dof.SetDelegatePass(ssao);tone.SetDelegatePass(dof)
  r.SetPass(tone);self.passes=[shadow,passes,seq,camPass,ssao,dof,tone]
  camera=r.GetActiveCamera();camera.SetViewUp(0,1,0);camera.SetClippingRange(1,10000)
  self.cap=vtk.vtkWindowToImageFilter();self.cap.SetInput(self.window);self.cap.SetInputBufferTypeToRGB();self.cap.ReadFrontBufferOff();self.cap.ShouldRerenderOff()
  self.total_triangles=total
 def update(self,t,explode=0,visibility=None):
  mats,pos=self.scene.pose(t);self.scene.mats=mats;self.scene.pos=pos
  for i,(actor,p) in enumerate(zip(self.actors,self.parts)):
   b=BODIES.index('fixed_hardware' if p['body']=='fixed' else p['body']);R=mats[b];o=pos[b]+R@(np.array(p['explode_mm'])*explode)
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
  t=2.5;explode=.75*smooth(u/.68);target=np.array([190,235,10]);eye=orbit(target,1230+140*s,-12+16*u,18);angle=36
 else:
  t=2.5;explode=.75*(1-smooth(u/.67));target=np.array([190-35*s,235-10*s,10-10*s]);eye=orbit(target,1370-270*s,4-4*s,18+3*s);angle=36-3*s
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
