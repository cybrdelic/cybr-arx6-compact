"""Checkpointed native 1080p path-traced capture; encodes only complete frames."""
from pathlib import Path
import os,sys,time,json,hashlib,subprocess,re
from PIL import Image
import numpy as np
from denoise import load,filter_frame,display_rgb
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
 lock=ROOT/'reports/render.lock'
 fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
 sources={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'source').iterdir() if p.is_file()}
 started=time.time();timeline=json.loads((ROOT/'reports/timeline.json').read_text());records=[]
 proc=None
 try:
  proc=subprocess.Popen([str(ROOT/'source/pathtrace'),str(ROOT/'assets/native.bin'),'--stream','unused','4'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=open(ROOT/'reports/native-stderr.log','w'),text=True,bufsize=1)
  first=proc.stdout.readline().strip();print(first,flush=True)
  for entry in timeline:
   i=entry['index'];out=ROOT/'frames'/f'{i:05d}.png';record=ROOT/'reports'/f'frame-{i:05d}.json'
   if out.exists() and record.exists():
    old=json.loads(record.read_text())
    if old.get('png_sha256')==digest(out):records.append(old);continue
   raw=ROOT/'frames'/f'{i:05d}.f32';inp=ROOT/'assets/frame_inputs'/f'{i:05d}.bin';begin=time.time()
   proc.stdin.write(f'{inp} {raw}\n');proc.stdin.flush()
   line=proc.stdout.readline().strip()
   if not line.startswith('FRAME '):raise RuntimeError(f'Native render failed: {line}; exit {proc.poll()}')
   a,spp=load(raw)
   if a.shape!=(1080,1920,12) or not np.isfinite(a[:,:,:3]).all():raise RuntimeError('Invalid rendered image')
   sample_values,sample_counts=np.unique(a[:,:,11],return_counts=True)
   col=filter_frame(a);im=display_rgb(col)
   tmp=out.with_suffix('.tmp.png');Image.fromarray(im).save(tmp,compress_level=2);os.replace(tmp,out)
   rec={**entry,'renderer':'ARX native CPU Monte Carlo path tracer / C++17','native_log':line,'primary_samples_histogram':{str(int(v)):int(n) for v,n in zip(sample_values,sample_counts)},'raw_rgb_sha256':hashlib.sha256(a[:,:,:3].copy().tobytes()).hexdigest(),'png_sha256':digest(out),'postprocess':'Four geometry-guided a-trous passes, followed by filmic tonemapping and sRGB encoding','seconds_total':time.time()-begin,'frame_input_sha256':digest(inp)}
   record.write_text(json.dumps(rec,indent=2));records.append(rec)
   # Keep one independent raw linear-light proof frame. All other raw buffers
   # can be regenerated; remove them to keep checkpoint storage bounded.
   if i==36:os.replace(raw,ROOT/'previews/pathtraced-linear-proof.f32')
   else:raw.unlink()
   print(f'COMPLETED {i+1}/{len(timeline)} {entry["shot"]} render_seconds={time.time()-begin:.2f} elapsed={time.time()-started:.1f}',flush=True)
  proc.stdin.close();status=proc.wait(timeout=20)
  if status:raise RuntimeError(f'Native renderer exit {status}')
  for name,h in sources.items():
   if digest(ROOT/name)!=h:raise RuntimeError('Source changed during capture: '+name)
  report={'renderer':'Native C++ Monte Carlo path tracer; no OpenGL/VTK rendering','frame_count':len(records),'resolution':[1920,1080],'fps':24,'duration_s':12,'max_surface_interactions':6,'samples_per_pixel':'16 on robot, 8 on floor/background; exact counts retained per frame','finite_area_emitters':4,'next_event_estimation':'Power/solid-angle light selection','mis':'power heuristic for emitter and GGX/diffuse sampling','rasterization':False,'screen_space_ao':False,'shadow_maps':False,'generative_images':False,'optical_flow_interpolation':False,'postprocess':'geometry-guided spatial denoising; filmic tone mapping','source_sha256':sources,'geometry':json.loads((ROOT/'reports/geometry.json').read_text()),'capture_sha256':digest(ROOT/'assets/capture.json'),'wall_seconds':time.time()-started}
  (ROOT/'reports/render-manifest.json').write_text(json.dumps(report,indent=2))
  print('ALL_FRAMES_COMPLETE',flush=True)
 finally:
  if proc and proc.poll() is None:proc.terminate()
  lock.unlink(missing_ok=True)
if __name__=='__main__':run()
