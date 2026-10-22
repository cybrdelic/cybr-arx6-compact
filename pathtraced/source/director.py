"""Twelve-second path-traced edit: two-second reveal and full ten-second cycle."""
from frames import *
FPS=24;DURATION=12;COUNT=FPS*DURATION

def director(frame):
 film=frame/FPS
 t=2.15+.3*(film/2) if film<2 else min(9.999,film-2)
 R,pos=pose(t);yaw=math.degrees(math.atan2(R[1,2,0],R[1,0,0]));aperture=.0011
 if film<2:
  shot='Reveal';target=np.array([.16,.235,0]);eye=orbit(target,1.24-.035*film/2,9-yaw+8*film/2,19);fov=32
 elif t<.5:
  shot='Approach';target=np.array([.16,.235,0]);eye=orbit(target,1.24,13-yaw,20);fov=33
 elif t<2.3:
  shot='Contact and lift';tcp=pos[6]+R[6]@np.array([0,.172,0]);target=tcp+np.array([0,.028,0]);eye=target+np.array([.285,.19,.36]);fov=32;aperture=.00075
 elif t<6:
  shot='Transfer and placement';target=np.array([.16,.235,0]);eye=orbit(target,1.24,13-yaw,20);fov=33
 elif t<7:
  shot='Compact joint detail';target=pos[3]+R[2]@np.array([0,-.018,.025]);eye=target+np.array([.24,.27,.44]);fov=34;aperture=.0008
 else:
  shot='Return and release';target=np.array([.16,.235,0]);eye=orbit(target,1.24,13-yaw,20);fov=33
 return dict(t=t,eye=eye,target=target,fov=fov,aperture=aperture),shot

if __name__=='__main__':
 import sys
 dest=ROOT/'assets/frame_inputs';dest.mkdir(exist_ok=True)
 report=[]
 for i in range(COUNT):
  kwargs,shot=director(i);j=write(dest/f'{i:05d}.bin',index=i,w=1920,h=1080,spp=16,depth=6,**kwargs);j['shot']=shot;report.append(j)
 (ROOT/'reports/timeline.json').write_text(json.dumps(report,indent=2))
 for i in [72,204]:
  k,shot=director(i);write(ROOT/'assets'/f'camera-test-{i}.bin',index=i,w=960,h=540,spp=16,**k)
 print('Prepared',len(report),'native 1080p frames',[(x['index'],x['shot']) for x in report if x['index'] in [0,48,60,104,192,216]])
