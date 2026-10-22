"""Finish missing v2 frames using at most two native render workers.

Use --wait-pids only to adopt already-running workers in this session.
The render inputs are preserved and completed frames are reused.
"""
from pathlib import Path
import argparse, os, subprocess, sys, time, json
ROOT=Path(__file__).resolve().parents[1]
CUT=[(0,72),(1,96),(4,120),(5,72)]

def alive(pid):
 try:
  p=Path(f'/proc/{pid}/stat')
  return p.exists() and p.read_text().split()[2]!='Z'
 except (FileNotFoundError,IndexError):return False

def main():
 (ROOT/'reports/v2').mkdir(parents=True,exist_ok=True)
 (ROOT/'frames-v2').mkdir(parents=True,exist_ok=True)
 p=argparse.ArgumentParser();p.add_argument('--wait-pids',nargs='*',type=int,default=[]);a=p.parse_args()
 env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',LP_NUM_THREADS='2',PYTHONWARNINGS='ignore',MESA_SHADER_CACHE_DIR=str(ROOT/'.mesa-cache'))
 pending=[]
 for shot,n in CUT:
  f=ROOT/'frames-v2'/f'shot{shot:02d}';start=0
  while (f/f'{start:05d}.png').is_file():start+=1
  if start<n and not (a.wait_pids and shot in (1,4)):pending.append((shot,start,n))
 active=[]
 while pending or active or any(alive(pid) for pid in a.wait_pids):
  occupied=sum(alive(pid) for pid in a.wait_pids)
  while pending and len(active)+occupied<2:
   shot,start,end=pending.pop(0)
   log=open(ROOT/'reports/v2'/f'completion-shot{shot}-{start}.log','wb')
   proc=subprocess.Popen([sys.executable,str(ROOT/'source/render_delivery_v2.py'),'--worker',str(shot),str(start),str(end)],env=env,stdout=log,stderr=subprocess.STDOUT)
   active.append((proc,shot,start,end,log))
   print(f'BEGIN shot={shot} frames={start}:{end}',flush=True)
  for item in active[:]:
   proc,shot,start,end,log=item
   code=proc.poll()
   if code is not None:
    log.close();active.remove(item)
    if code:raise RuntimeError(f'Render worker {shot} failed ({code})')
    print(f'FINISHED shot={shot}',flush=True)
  time.sleep(2)
 subprocess.run([sys.executable,str(ROOT/'source/render_delivery_v2.py'),'--finish'],check=True,env=env)
 print('ALL COMPLETE',flush=True)
if __name__=='__main__':main()
