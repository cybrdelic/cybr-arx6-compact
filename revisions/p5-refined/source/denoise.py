"""Geometry-guided a-trous Monte Carlo denoising. No trained/generated imagery."""
from pathlib import Path
import numpy as np
from numba import njit,prange,set_num_threads
from PIL import Image
set_num_threads(4)
@njit(parallel=True,cache=True)
def atrous(src,norm,depth,part,step):
 h,w,c=src.shape;dst=np.empty_like(src)
 offsets=np.array([-2,-1,0,1,2]);kernel=np.array([1.,4.,6.,4.,1.])
 for y in prange(h):
  for x in range(w):
   a0=src[y,x,0];a1=src[y,x,1];a2=src[y,x,2]
   lum0=.2126*a0+.7152*a1+.0722*a2
   v0=v1=v2=0.;ws=0.;pid=part[y,x];z=depth[y,x]
   for ky in range(5):
    yy=min(h-1,max(0,y+offsets[ky]*step))
    for kx in range(5):
     xx=min(w-1,max(0,x+offsets[kx]*step))
     if part[yy,xx]!=pid:continue
     ncos=norm[y,x,0]*norm[yy,xx,0]+norm[y,x,1]*norm[yy,xx,1]+norm[y,x,2]*norm[yy,xx,2]
     nw=max(0.,ncos)**32 if pid!=-1 else 1.
     if nw<.001:continue
     dz=abs(depth[yy,xx]-z);zw=np.exp(-dz/(.006+z*.018*step)) if z<1e10 else 1.
     b0=src[yy,xx,0];b1=src[yy,xx,1];b2=src[yy,xx,2]
     lum=.2126*b0+.7152*b1+.0722*b2
     # Relative luminance guide preserves broad physical reflection boundaries.
     dw=abs(lum-lum0)/(.035+.60*max(lum0,lum))
     cw=np.exp(-dw*dw*.5)
     weight=kernel[ky]*kernel[kx]*nw*zw*cw
     v0+=weight*b0;v1+=weight*b1;v2+=weight*b2;ws+=weight
   dst[y,x,0]=v0/max(ws,1e-12);dst[y,x,1]=v1/max(ws,1e-12);dst[y,x,2]=v2/max(ws,1e-12)
 return dst

def load(path):
 with open(path,'rb')as f:
  w,h,c,s=np.fromfile(f,'<i4',4);a=np.fromfile(f,'<f4').reshape(h,w,c)
 return a,int(s)

def filter_frame(a,steps=(1,2,4,8)):
 col=np.maximum(0,np.nan_to_num(a[:,:,:3],nan=0,posinf=0)).copy()
 n=np.ascontiguousarray(a[:,:,3:6]);d=np.ascontiguousarray(a[:,:,6]);p=np.ascontiguousarray(a[:,:,7])
 for step in steps: col=atrous(col,n,d,p,step)
 return col

def display_rgb(x,exposure=1):
 x=np.clip(x*exposure,0,1e5)
 x=np.clip((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0,1)
 x=np.where(x<=.0031308,12.92*x,1.055*x**(1/2.4)-.055)
 return np.clip(x*255+.5,0,255).astype('uint8')

if __name__=='__main__':
 import sys,time
 start=time.time();a,s=load(sys.argv[1]);im=filter_frame(a);Image.fromarray(display_rgb(im)).save(sys.argv[2]);print('denoised',s,'spp',time.time()-start)
