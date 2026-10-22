"""Reproducible proof cameras; same recorded operating state, no new physics."""
from frames import *

def camera(name,w=3840,h=2160,spp=64):
 t=2.5;R,pos=pose(t);yaw=math.degrees(math.atan2(R[1,2,0],R[1,0,0]))
 if name=='hero':
  target=np.array([.145,.235,0]);eye=orbit(target,1.17,11-yaw,19.5);fov=33;aperture=.00045
 elif name=='closeup':
  target=pos[3]+R[2]@np.array([0,-.052,.018]);eye=target+np.array([.255,.15,.36]);fov=32;aperture=.00022
 else:raise ValueError(name)
 return write(ROOT/'assets'/f'{name}.bin',t=t,index=0 if name=='hero' else 1,w=w,h=h,spp=spp,depth=8,eye=eye,target=target,fov=fov,aperture=aperture)

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');args=ap.parse_args()
 report={n:camera(n,960 if args.preview else 3840,540 if args.preview else 2160,64) for n in ['hero','closeup']}
 (ROOT/'reports'/('preview-cameras.json' if args.preview else 'proof-cameras.json')).write_text(json.dumps(report,indent=2));print(report)
