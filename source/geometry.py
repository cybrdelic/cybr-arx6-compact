"""Compile the supplied, unchanged P5 constructive geometry into ray-query tables.
No robot mesh or generated image is used. Coordinates are millimetres.
"""
from pathlib import Path
import json, itertools, hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BODIES=['fixed_hardware','turret','upper','fore','roll','bend','tool','jaw_left','jaw_right','puck']
FINISH={'paint':0,'darkmetal':1,'metal':2,'steel':3,'brass':4,'pcb':5,'rubber':6,'polymer':6}

def convex(poly):
 a=np.asarray(poly);b=np.roll(a,-1,axis=0)-a;c=np.roll(b,-1,axis=0)
 cross=b[:,0]*c[:,1]-b[:,1]*c[:,0]
 return bool(np.all(cross>=-1e-8) or np.all(cross<=1e-8))

def compile_geometry():
 design=json.loads((ROOT/'assets/design.json').read_text());data=[];meta=[]
 def emit(rows):
  start=len(data);data.extend(rows);return start
 for part in design['parts']:
  prims=[];tape=[];slow=False
  def walk(node,T):
   nonlocal slow
   op=node['op'];args=node['args']
   if op=='transform':walk(node['children'][0],T@np.asarray(args).reshape(4,4));return
   if op in ('union','cut','intersection'):
    for c in node['children']:walk(c,T)
    tape.append({'union':-1,'cut':-2,'intersection':-3}[op]);return
   inv=np.linalg.inv(T);info=np.zeros(4);v=[0,0,0,0]
   if op=='box':v=[0,*args]
   elif op=='cylinder':v=[1,args[0],args[1],0]
   elif op=='polygon':
    poly=np.array(args[0],float);area=np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1))
    if area<0:poly=poly[::-1]
    off=emit([[x,y,0,0] for x,y in poly]);v=[2,args[1],len(poly),off];info[0]=int(convex(poly));slow|=not bool(info[0])
   elif op=='helix':v=[3,args[0],args[1],args[2]];info[0]=args[3];slow=True
   else:raise ValueError('Unsupported native primitive '+op)
   prims.append([v,*inv[:3].tolist(),info.tolist()]);tape.append(len(prims))
  walk(part['shape'],np.eye(4));start=len(data)
  for p in prims:emit(p)
  code=emit([[x,0,0,0] for x in tape]);meta.append([[code,len(tape),start,len(prims)],[FINISH[part['finish']],int(slow),0,0]])
 buf=np.asarray(data,dtype='f4');M=np.asarray(meta,dtype='f4');buf.tofile(ROOT/'assets/geometry.f32');M.tofile(ROOT/'assets/parts.f32')
 report={'source_sha256':hashlib.sha256((ROOT/'assets/design.json').read_bytes()).hexdigest(),'parts':len(meta),'static_float4_records':len(data),'max_primitives':int(M[:,0,3].max()),'slow_parts':[p['name'] for p,m in zip(design['parts'],meta) if m[1][1]],'geometry_policy':'Original P5 CSG is evaluated; no tessellated robot or input image is sampled.'}
 (ROOT/'reports/geometry-compile.json').write_text(json.dumps(report,indent=2));print(report)
 return design

class Scene:
 def __init__(self):
  self.design=json.loads((ROOT/'assets/design.json').read_text());self.parts=self.design['parts']
  self.trace=json.loads((ROOT/'assets/capture.json').read_text());self.frames=np.array(self.trace['frames']);self.states=np.array(self.trace['bodies'])
  self.corners=np.array([list(itertools.product(*zip(*p['bounds_mm']))) for p in self.parts]);self.body=np.array([BODIES.index('fixed_hardware' if p['body']=='fixed' else p['body']) for p in self.parts]);self.explode=np.array([p['explode_mm'] for p in self.parts]);
 def pose(self,t):
  idx=np.clip(t*120,0,len(self.frames)-1);i=int(idx);j=min(i+1,len(self.frames)-1);f=idx-i
  # Interpolate on SO(3), avoiding a changing scale in the robot parts.
  from scipy.spatial.transform import Rotation,Slerp
  a,b=self.states[i],self.states[j];pos=(a[:,:3]*(1-f)+b[:,:3]*f)*1000
  mats=[]
  for k in range(len(BODIES)):
   if i==j:m=a[k,3:].reshape(3,3)
   else:m=Slerp([0,1],Rotation.from_matrix(np.stack([a[k,3:].reshape(3,3),b[k,3:].reshape(3,3)])))([f]).as_matrix()[0]
   mats.append(m)
  return np.asarray(mats),pos
 def update(self,t,explode=0):
  mats,pos=self.pose(t);R=mats[self.body];O=pos[self.body];offset=self.explode*explode
  origin=O+np.einsum('nij,nj->ni',R,offset)
  inv=np.transpose(R,(0,2,1));rows=np.concatenate([inv,-np.einsum('nij,nj->ni',inv,origin)[...,None]],axis=2)
  c=np.einsum('nij,nkj->nki',R,self.corners)+origin[:,None,:];lo=c.min(1)-.04;hi=c.max(1)+.04
  self.world_bounds=(lo,hi);self.mats=mats;self.pos=pos
  nodes=[]
  def build(ids):
   n=len(nodes);nodes.extend([None,None]);L=lo[ids].min(0);H=hi[ids].max(0)
   if len(ids)==1:part=int(ids[0])
   else:
    axis=int(np.argmax(H-L));cent=(lo[ids,axis]+hi[ids,axis])/2;order=ids[np.argsort(cent,kind='stable')];h=len(ids)//2;build(order[:h]);build(order[h:]);part=-1
   nodes[n]=[*L,len(nodes)//2];nodes[n+1]=[*H,part]
  build(np.arange(len(self.parts)))
  return rows.astype('f4'),np.array(nodes,dtype='f4')
 def point(self,body,local):
  i=BODIES.index(body);return self.pos[i]+self.mats[i]@np.asarray(local)

if __name__=='__main__':compile_geometry()
