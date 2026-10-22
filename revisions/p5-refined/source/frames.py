from pathlib import Path
import numpy as np,json,struct,math
from scipy.spatial.transform import Rotation,Slerp
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'assets/capture.json').read_text())
BODIES=DATA['bodyNames'];STATES=np.array(DATA['bodies']);PARTS=json.loads((ROOT/'assets/design.json').read_text())['parts']
BODY=[BODIES.index('fixed_hardware' if p['body']=='fixed' else p['body']) for p in PARTS]
def pose(t):
 a=np.clip(t*120,0,len(STATES)-1);i=int(a);j=min(i+1,len(STATES)-1);f=a-i
 pos=(1-f)*STATES[i,:,:3]+f*STATES[j,:,:3]
 mats=[]
 for k in range(10):
  if i==j:m=STATES[i,k,3:].reshape(3,3)
  else:m=Slerp([0,1],Rotation.from_matrix(np.stack([STATES[i,k,3:].reshape(3,3),STATES[j,k,3:].reshape(3,3)])))([f]).as_matrix()[0]
  mats.append(m)
 return np.array(mats),pos

def orbit(target,distance,azimuth,elevation):
 a,e=np.deg2rad([azimuth,elevation]);return np.array(target)+distance*np.array([np.cos(e)*np.sin(a),np.sin(e),np.cos(e)*np.cos(a)])

def write(path,t=2.5,index=0,w=960,h=540,spp=16,depth=6,eye=None,target=None,fov=32,aperture=0,explode=0):
 R,pos=pose(t)
 if target is None:target=np.array([.16,.24,0])
 if eye is None:
  yaw=math.degrees(math.atan2(R[1,2,0],R[1,0,0]));eye=orbit(target,1.20,12-yaw,19)
 if explode:
  R=R[BODY];pos=pos[BODY];offset=np.array([p['explode_mm'] for p in PARTS])*explode*.001;pos+=np.einsum('nij,nj->ni',R,offset)
 rows=np.concatenate([R,pos[:,:,None]],axis=2).astype('<f4')
 with open(path,'wb') as f:
  f.write(struct.pack('<7i',index,w,h,spp,depth,int(explode!=0),len(R)))
  f.write(struct.pack('<9f',*eye,*target,fov,aperture,1.))
  f.write(rows.tobytes())
 return {'index':index,'time':t,'eye':list(map(float,eye)),'target':list(map(float,target)),'fov':fov,'aperture':aperture,'spp':spp,'max_depth':depth,'width':w,'height':h,'explode':explode}
if __name__=='__main__':
 print(write(ROOT/'assets/test.bin',w=768,h=432,spp=16))
