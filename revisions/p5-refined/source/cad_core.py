"""Evaluate the archived P5 constructive geometry; millimetres, no mesh substitutes."""
import json
from functools import lru_cache
import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

@lru_cache(maxsize=12000)
def _build(key):
    n=json.loads(key); a=n['args']; children=n['children']; op=n['op']
    if op=='box': return cq.Solid.makeBox(*[2*x for x in a],cq.Vector(*[-x for x in a]))
    if op=='cylinder': return cq.Solid.makeCylinder(a[0],2*a[1],cq.Vector(0,0,-a[1]))
    if op=='polygon':
        w=cq.Wire.makePolygon([cq.Vector(x,y,-a[1]) for x,y in a[0]],close=True)
        return cq.Solid.extrudeLinear(w,[],cq.Vector(0,0,2*a[1]))
    if op=='helix':
        r,wire,pitch,turns=a
        path=cq.Wire.makeHelix(pitch,pitch*turns,r)
        profile=cq.Workplane('XZ').center(r,0).circle(wire).val()
        return cq.Solid.sweep(profile,[],path,makeSolid=True,isFrenet=True)
    if op=='transform':
        t=gp_Trsf();t.SetValues(*np.array(a).reshape(4,4)[:3].ravel().tolist())
        return cq.Shape.cast(BRepBuilderAPI_Transform(build(children[0]).wrapped,t,True).Shape())
    if op=='union':return build(children[0]).fuse(build(children[1]))
    if op=='cut':return build(children[0]).cut(build(children[1]))
    if op=='intersection':return build(children[0]).intersect(build(children[1]))
    raise ValueError(op)

def build(node): return _build(json.dumps(node,separators=(',',':')))

def solid(shape):
    ss=shape.Solids()
    if len(ss)!=1:raise ValueError(f'Expected one solid, got {len(ss)}')
    return ss[0]
