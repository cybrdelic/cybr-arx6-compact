"""Verify all native renders, encode them, decode the movie, then package source."""
from pathlib import Path
import subprocess,json,hashlib,zipfile,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent
FPS=24;EXPECTED=288

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def command(args,timeout=180):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError(p.stderr[-6000:])
 return p.stdout

def main():
 manifest_path=ROOT/'reports/render-manifest.json'
 if not manifest_path.is_file():raise RuntimeError('Native capture has not finished.')
 manifest=json.loads(manifest_path.read_text());timeline=json.loads((ROOT/'reports/timeline.json').read_text())
 if len(timeline)!=EXPECTED:raise RuntimeError('Unexpected timeline length')
 rec=[]
 for i in range(EXPECTED):
  p=ROOT/'frames'/f'{i:05d}.png';r=ROOT/'reports'/f'frame-{i:05d}.json'
  if not p.is_file() or not r.is_file():raise RuntimeError(f'Missing capture frame {i}')
  d=json.loads(r.read_text())
  if sha(p)!=d['png_sha256']:raise RuntimeError(f'Changed frame {i}')
  with Image.open(p) as im:
   if im.size!=(1920,1080):raise RuntimeError(f'Wrong resolution: {i}')
  rec.append(d)
 chapters=[];previous=None
 for i,x in enumerate(timeline):
  if x['shot']!=previous:
   if chapters:chapters[-1]['end']=i
   chapters.append({'start':i,'end':EXPECTED,'title':x['shot']});previous=x['shot']
 meta=[';FFMETADATA1','title=ARX / 6 — P5 native path-traced action']
 for c in chapters:meta+=['[CHAPTER]','TIMEBASE=1/24',f'START={c["start"]}',f'END={c["end"]}',f'title={c["title"]}']
 mf=ROOT/'reports/chapters.ffmetadata';mf.write_text('\n'.join(meta)+'\n')
 movie=OUT/'ARX6-P5-Pathtraced-Action-1080p.mp4'
 command(['ffmpeg','-y','-v','error','-framerate','24','-i',str(ROOT/'frames/%05d.png'),'-i',str(mf),'-map','0:v:0','-map_metadata','1','-map_chapters','1','-frames:v',str(EXPECTED),'-vf','scale=out_color_matrix=bt709:out_range=tv','-c:v','libx264','-preset','slow','-crf','16','-threads','4','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-movflags','+faststart',str(movie)],timeout=180)
 info=json.loads(command(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]));stream=next(s for s in info['streams'] if s['codec_type']=='video')
 dec=command(['ffmpeg','-v','error','-i',str(movie),'-map','0:v:0','-f','framemd5','-'])
 hashes=[row.rsplit(',',1)[-1].strip() for row in dec.splitlines() if row and not row.startswith('#')]
 if len(hashes)!=EXPECTED:raise RuntimeError('Incomplete final decode')
 if [stream['width'],stream['height']]!=[1920,1080] or stream['avg_frame_rate']!='24/1':raise RuntimeError('Wrong final format')
 (ROOT/'reports/decoded-frames.framemd5').write_text(dec)
 poster=OUT/'ARX6-P5-Pathtraced-Frame.png';shutil.copy2(ROOT/'frames/00036.png',poster)
 # Independent encode/decode comparison, to catch color-range mistakes.
 decoded=ROOT/'previews/decoded-frame-36.png'
 command(['ffmpeg','-y','-v','error','-i',str(movie),'-vf','select=eq(n\\,36)','-frames:v','1',str(decoded)])
 aa=np.array(Image.open(ROOT/'frames/00036.png')).astype('float32');bb=np.array(Image.open(decoded)).astype('float32')
 report={'file':movie.name,'size_bytes':movie.stat().st_size,'sha256':sha(movie),'renderer':'Custom native CPU Monte Carlo path tracer, not VTK/Eevee/raster PBR, and not Blender Cycles','resolution':[stream['width'],stream['height']],'frame_rate':stream['avg_frame_rate'],'duration_s':float(info['format']['duration']),'native_frames_rendered':len(rec),'decoded_frames':len(hashes),'distinct_decoded_frames':len(set(hashes)),'full_decode_passed':True,'maximum_surface_interactions':6,'sampling':'16 camera paths per robot pixel; 8 per floor/background pixel, with four-emitter MIS','denoising':'Geometry-guided a-trous spatial filter; no generative image model','thin_lens_depth_of_field':True,'geometry_parts':manifest['geometry']['parts'],'native_triangles':manifest['geometry']['triangles'],'canonical_geometry_sha256':manifest['geometry']['geometry_sha256'],'capture_sha256':manifest['capture_sha256'],'simulation_scope':'Same P5-based contact capture as the preceding cinematic source; not a new engineering validation','content':'Two-second moving reveal followed by the full ten-second operating recording, with gripper and elbow detail camera cuts','disassembly_included':False,'audio':False,'frame_interpolation':False,'image_generation':False,'color_encode_decode_mean_abs_8bit_error':float(np.abs(aa-bb).mean()),'source_render_manifest_sha256':sha(manifest_path),'chapters':chapters}
 vp=OUT/'ARX6-P5-Pathtraced-Verification.json';vp.write_text(json.dumps(report,indent=2));shutil.copy2(vp,ROOT/'reports/video-verification.json')
 archive=OUT/'ARX6-P5-Pathtraced-Source.zip';members={}
 for folder in ['source','assets','reports']:
  for p in (ROOT/folder).rglob('*'):
   if not p.is_file() or any(x in p.parts for x in ['__pycache__']) or p.suffix in {'.lock','.pid','.log'}:continue
   if p.name in {'denoise_fast.py','test_tracer'}:continue
   members['ARX6-P5-Pathtraced/'+p.relative_to(ROOT).as_posix()]=p
 members['ARX6-P5-Pathtraced/README.md']=ROOT/'README.md'
 members['ARX6-P5-Pathtraced/requirements.txt']=ROOT/'requirements.txt'
 # Include actual sample renders, not synthetic promotional imagery.
 for name in ['direct-only.png','six-bounce.png']:
  p=ROOT/'previews'/name
  if p.exists():members['ARX6-P5-Pathtraced/previews/'+name]=p
 members['ARX6-P5-Pathtraced/preview.png']=poster
 hashes_zip={k:sha(p) for k,p in sorted(members.items())}
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
  for name,p in sorted(members.items()):z.write(p,name)
  z.writestr('MANIFEST-SHA256.json',json.dumps(hashes_zip,indent=2))
 with zipfile.ZipFile(archive) as z:
  if z.testzip():raise RuntimeError('ZIP CRC failed')
  for name,h in hashes_zip.items():
   if hashlib.sha256(z.read(name)).hexdigest()!=h:raise RuntimeError('ZIP hash failed: '+name)
 (OUT/'ARX6-P5-Pathtraced-Source-Verification.json').write_text(json.dumps({'file':archive.name,'sha256':sha(archive),'members_verified':len(hashes_zip),'crc_passed':True,'font_files_distributed':False},indent=2))
 print(json.dumps(report,indent=2));print('DELIVERED',movie,archive,poster,flush=True)
if __name__=='__main__':main()
