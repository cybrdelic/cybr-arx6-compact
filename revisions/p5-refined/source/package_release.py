"""Package only a completed, verified proof release; refuse missing renders."""
from pathlib import Path
import hashlib,json,zipfile,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proofs=json.loads((ROOT/'reports/proof-render-verification.json').read_text())
 geom=json.loads((ROOT/'reports/geometry-verification.json').read_text())
 envelope=json.loads((ROOT/'reports/envelope-screen.json').read_text())
 tests=json.loads((ROOT/'reports/numerical-tests.json').read_text())
 if not geom['all_modified_parts_valid'] or not envelope['all_below_0p01_mm3'] or not tests['passed']:raise RuntimeError('Release checks did not pass')
 for name,rec in proofs.items():
  p=ROOT/'renders'/f'ARX6-P5-Refined-{name}-1080p.png';master=ROOT/'renders'/f'ARX6-P5-Refined-{name}-4K.png'
  if sha(p)!=rec['png_sha256'] or sha(master)!=rec['master_sha256']:raise RuntimeError('Rendered image changed')
  if rec['native_geometry_sha256']!=sha(ROOT/'assets/refined-native.bin'):raise RuntimeError('Render/CAD cache mismatch')
  if rec['render_source_sha256']!=sha(ROOT/'source/pathtrace.cpp'):raise RuntimeError('Render source changed')
  with Image.open(p) as im:
   if im.size!=(1920,1080):raise RuntimeError('Wrong output dimensions')
  with Image.open(master) as im:
   if im.size!=(3840,2160):raise RuntimeError('Wrong master dimensions')
 archive=ROOT.parent/'ARX6-P5-Refined-Source-and-CAD.zip';members={}
 for folder in ['source','assets','cad','reports','renders']:
  for p in (ROOT/folder).rglob('*'):
   if not p.is_file() or '__pycache__' in p.parts:continue
   if p.suffix.lower() in ['.f32','.pyc','.log','.pid','.ttf','.otf','.woff','.woff2']:continue
   if folder=='source' and (p.suffix not in ['.py','.cpp','.h'] or p.name in ['test_fillets.py','probe_edges.py','upgrade_tracer.py','test_tracer.cpp']):continue
   if folder=='reports' and p.name.startswith('preview-'):continue
   members['ARX6-P5-Refined/'+p.relative_to(ROOT).as_posix()]=p
 for name in ['README.md','requirements.txt']:members['ARX6-P5-Refined/'+name]=ROOT/name
 manifest={n:sha(p) for n,p in sorted(members.items())}
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for n,p in sorted(members.items()):z.write(p,n)
  z.writestr('MANIFEST-SHA256.json',json.dumps(manifest,indent=2)+'\n')
 with zipfile.ZipFile(archive) as z:
  if z.testzip():raise RuntimeError('ZIP integrity error')
  for n,h in manifest.items():
   if hashlib.sha256(z.read(n)).hexdigest()!=h:raise RuntimeError('Archive hash mismatch: '+n)
 verification=dict(archive=archive.name,archive_sha256=sha(archive),archive_size_bytes=archive.stat().st_size,verified_archive_members=len(manifest),modified_part_instances=geom['modified_parts_checked'],all_modified_step_parts_valid=geom['all_modified_parts_valid'],no_new_part_volume_outside_original=envelope['all_below_0p01_mm3'],inherited_multisolid_instances=geom['inherited_multisolid_instances'],proofs=proofs,dynamics_rerun=False,new_video_rendered=False,font_files_distributed=False)
 (ROOT.parent/'ARX6-P5-Refined-Verification.json').write_text(json.dumps(verification,indent=2))
 print(archive,archive.stat().st_size,flush=True)
if __name__=='__main__':main()
