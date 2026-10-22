"""Render the two real path-traced proofs and reconstruct 1080p in linear light."""
from pathlib import Path
import hashlib,json,subprocess,time,sys,os
import numpy as np
from PIL import Image
from proof_cameras import camera
from denoise import load,filter_frame,display_rgb
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 report={};start=time.time()
 for name in ['hero','closeup']:
  meta=camera(name,3840,2160,64);raw=ROOT/'renders'/f'{name}.f32'
  output=ROOT/'renders'/f'ARX6-P5-Refined-{name}-1080p.png'
  rec=ROOT/'reports'/f'{name}-render.json'
  if output.exists() and rec.exists():report[name]=json.loads(rec.read_text());continue
  cmd=[str(ROOT/'source/pathtrace'),str(ROOT/'assets/refined-native.bin'),str(ROOT/'assets'/f'{name}.bin'),str(raw),'4']
  t=time.time();p=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=900)
  (ROOT/'reports'/f'{name}-native.log').write_text(p.stdout+p.stderr)
  print('TRACED',name,round(time.time()-t,2),p.stdout,flush=True)
  a,spp=load(raw)
  if a.shape!=(2160,3840,12) or not np.isfinite(a[:,:,:3]).all():raise ValueError('Invalid native proof')
  counts,qty=np.unique(a[:,:,11],return_counts=True)
  if not np.all(counts==64):raise ValueError('Some pixels did not receive 64 paths')
  linear=filter_frame(a,steps=(1,2,4))
  master=ROOT/'renders'/f'ARX6-P5-Refined-{name}-4K.png'
  Image.fromarray(display_rgb(linear)).save(master)
  smaller=np.stack([np.asarray(Image.fromarray(linear[:,:,c]).resize((1920,1080),Image.Resampling.LANCZOS)) for c in range(3)],axis=2)
  Image.fromarray(display_rgb(np.maximum(smaller,0))).save(output)
  data=dict(camera=meta,native_resolution=[3840,2160],delivery_resolution=[1920,1080],uniform_camera_paths_per_native_pixel=64,nominal_camera_paths_per_output_pixel=256,maximum_surface_interactions=8,
   sampling='8x8 spatial stratification at 2x linear resolution; thin-lens rays',texture_sampling='band-limited procedural roughness and bump in rigid-body coordinates; approximate scalar footprint, not full ray differentials',
   transport='anisotropic GGX VNDF with Smith masking, emitter NEE, power-heuristic MIS, diffuse/glossy secondary paths',
   denoising='Three geometry-guided spatial a-trous passes at native 4K',reconstruction='Lanczos downsample in linear radiance, followed by filmic mapping and sRGB encoding',
   native_log=p.stdout,seconds=time.time()-t,paths_histogram={str(int(k)):int(v) for k,v in zip(counts,qty)},
   png_sha256=sha(output),master_sha256=sha(master),native_geometry_sha256=sha(ROOT/'assets/refined-native.bin'),render_source_sha256=sha(ROOT/'source/pathtrace.cpp'),geometry_generated_images=False,rasterization=False)
  rec.write_text(json.dumps(data,indent=2));report[name]=data
  print('FINISHED',name,'elapsed',round(time.time()-start,1),flush=True)
  # Raw proof retained for reproducibility; it is not an encoded or upscaled image.
  del a,linear,smaller
 (ROOT/'reports/proof-render-verification.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
