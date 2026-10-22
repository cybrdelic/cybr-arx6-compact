"""Resumable native 1080p restoration of the 15-second v2 cut.

Usage: python source/render_delivery_v2.py --worker SHOT START END
       python source/render_delivery_v2.py --finish
Staging is a presentation sequence, not a validated physical teardown.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT
CUT=[(0,72,'Reveal'),(1,96,'Action excerpt'),(4,120,'Staged inspection'),(5,72,'Reassembly view')]
FPS=24
W,H=1920,1080

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def cmd(args,timeout=120):
 p=subprocess.run(args,text=True,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stderr[-5000:])
 return p.stdout

def worker(shot,start,end):
 from PIL import Image
 from native_film_v2 import Renderer,shot_state
 folder=ROOT/'frames-v2'/f'shot{shot:02d}';folder.mkdir(parents=True,exist_ok=True)
 (ROOT/'reports/v2/v2').mkdir(exist_ok=True)
 t0=time.monotonic();r=Renderer(W,H);rows=[]
 for f in range(start,end):
  st=shot_state(shot,f/FPS,r)
  image=r.render(*st)
  path=folder/f'{f:05d}.png';tmp=path.with_suffix('.part.png')
  Image.fromarray(image).save(tmp,compress_level=1);tmp.replace(path)
  rows.append({'frame':f,'simulation_time_s':float(st[0]),'inspection_progress':float(st[4]),'eye_mm':st[1].tolist(),'target_mm':st[2].tolist(),'rgb_sha256':hashlib.sha256(image.tobytes()).hexdigest()})
 r.close()
 report={'shot':shot,'start':start,'end_exclusive':end,'resolution':[W,H],'fps':FPS,'wall_seconds':time.monotonic()-t0,'frames':rows}
 (ROOT/'reports/v2/v2'/f'batch-{shot:02d}-{start:05d}.json').write_text(json.dumps(report,indent=2))
 print(f'COMPLETE {shot=} {start=} {end=} seconds={report["wall_seconds"]:.2f}',flush=True)

def finish():
 (ROOT/'clips-v2').mkdir(exist_ok=True);(ROOT/'reports/v2/v2').mkdir(exist_ok=True)
 for shot,count,label in CUT:
  folder=ROOT/'frames-v2'/f'shot{shot:02d}'
  assert all((folder/f'{n:05d}.png').is_file() for n in range(count)), (shot,'incomplete frames')
  cmd(['ffmpeg','-y','-v','error','-framerate',str(FPS),'-i',str(folder/'%05d.png'),'-frames:v',str(count),'-an','-c:v','libx264','-threads','2','-preset','medium','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'clips-v2'/f'{shot:02d}.mp4')])
 concat=ROOT/'reports/v2/clips.ffconcat'
 concat.write_text('ffconcat version 1.0\n'+''.join(f"file '{ROOT/'clips-v2'/f'{s:02d}.mp4'}'\n" for s,_,_ in CUT))
 meta=ROOT/'reports/v2/chapters.ffmetadata';lines=[';FFMETADATA1','title=ARX / 6 - compact P5 v2 short cut'];t=0
 for _,count,label in CUT:
  end=t+count/FPS;lines+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(t*1000)}',f'END={round(end*1000)}',f'title={label}'];t=end
 meta.write_text('\n'.join(lines)+'\n')
 movie=OUT/'ARX6-P5-Cinematic-v2.mp4'
 cmd(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-i',str(meta),'-map','0:v:0','-map_metadata','1','-map_chapters','1','-c:v','copy','-movflags','+faststart',str(movie)])
 decoded=cmd(['ffmpeg','-v','error','-i',str(movie),'-map','0:v:0','-f','framemd5','-'])
 rows=[l for l in decoded.splitlines() if l and not l.startswith('#')];hashes=[l.rsplit(',',1)[-1].strip() for l in rows]
 assert len(hashes)==360 and len(set(hashes))==360,('decoded/unique',len(hashes),len(set(hashes)))
 info=json.loads(cmd(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]));v=next(s for s in info['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'],v['avg_frame_rate'])==(W,H,'24/1')
 report={'film':movie.name,'size_bytes':movie.stat().st_size,'sha256':sha(movie),'width':v['width'],'height':v['height'],'fps':v['avg_frame_rate'],'duration_seconds':float(info['format']['duration']),'decoded_frames':len(hashes),'distinct_decoded_frames':len(set(hashes)),'full_decode_passed':True,'shots':[{'source_shot':s,'frames':n,'label':label} for s,n,label in CUT],'design_sha256':sha(ROOT/'assets/design.json'),'capture_sha256':sha(ROOT/'assets/capture.json'),'renderer_sha256':sha(ROOT/'source/native_film_v2.py'),'provenance':'Rebuilt from retained cinematic source plus v2 edits recorded in the conversation; not recovered original encoded bytes.','rendering':'Native CAD tessellation, VTK PBR, image-based lighting, shadow maps, SSAO, filmic tone mapping; not original single-pass constructive GLSL.','depth_of_field':'Bypassed in the previously recorded v2 source.','inspection':'Heuristic component-role staging and offsets; not validated real-world disassembly.','motion':'Existing reconstructed contact capture; not a rerun of original 28-scenario validation.','audio':False,'generated_images_used':False,'video_frame_interpolation':False}
 (ROOT/'reports/v2/video-verification.json').write_text(json.dumps(report,indent=2))
 (ROOT/'reports/v2/decoded-frames.framemd5').write_text(decoded)
 print(json.dumps(report,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--worker',nargs=3,type=int);ap.add_argument('--finish',action='store_true');a=ap.parse_args()
 if a.worker:worker(*a.worker)
 elif a.finish:finish()
 else:ap.error('Choose --worker SHOT START END or --finish')
