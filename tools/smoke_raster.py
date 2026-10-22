"""Render one real compact-arm frame through the platform VTK backend."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
from native_film import Renderer, shot_state
from PIL import Image
import numpy as np

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'.build/raster-smoke.png')
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    renderer=Renderer(160,90,quality=0)
    try:
        state=shot_state(0,1.0,renderer)
        image=renderer.render(*state)
        assert image.shape==(90,160,3) and image.max()>image.min()
        Image.fromarray(image).save(a.output)
        print(json.dumps({'backend':renderer.window.GetClassName(),'triangles':renderer.total_triangles,
                          'resolution':[160,90],'output':str(a.output),
                          'scope':'One actual PBR robot frame, not a complete cinematic film'}))
    finally:renderer.close()
if __name__=='__main__':main()
