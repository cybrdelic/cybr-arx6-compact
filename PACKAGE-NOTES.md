# ARX / 6 — compact P5 action film

This is a new camera edit of the original compact 278-part P5 geometry.
The production footage is native CAD geometry rendered with VTK PBR shading;
it is not generated imagery and it is not the earlier inspection slideshow.
It also is not the original single-pass constructive GLSL renderer. That
renderer could not produce this capture at usable speed in this CPU-only
runtime. The delivered production renderer tessellates the native CAD and
uses conventional GPU-style shading through software OpenGL.

## Six-shot edit

| Film time | Shot | Content |
| --- | --- | --- |
| 00:00–00:03 | Reveal | Moving camera around the assembled, moving compact arm |
| 00:03–00:13 | Pick / transfer / return | Uncut ten-second contact-driven cycle |
| 00:13–00:17 | Precision grip | Close approach, jaw closure, and lift |
| 00:17–00:20 | Compact elbow | Close-up of the actual compact cartridge geometry |
| 00:20–00:25 | Exploded architecture | Original per-component inspection offsets |
| 00:25–00:28 | Reassembly hero | Return to the compact assembled model |

All shots are native 1920 × 1080 at 24 frames per second. The video has no
audio. Frames are independently rendered from the geometry; no generated
look-alike images, optical-flow frame interpolation, or repeated still-image
pan/zoom sequence is used. Animation poses are sampled from a 120 Hz capture
using rotational interpolation, which is different from synthesizing new
video frames. Exploded positions are presentation transforms, not a physical
disassembly simulation. The studio floor lowers during explosion to show
parts with downward inspection offsets.

## Geometry provenance

`assets/design.json` is the unchanged original compact P5 constructive source:
SHA-256 `48b3dcf993f78a9e1f386c8458644bb5829d627c895b88e58e616ae14aa565a0`.
The 278 instances include repeated hardware and the five workpiece/fixture
solids. OpenCascade rebuilds the source constructions and supplies the
production triangles. `reports/native-mesh-build.json` records all 278 valid
solids, their volumes, and the 778,046 resulting triangles. The tessellation
uses 0.045 mm linear and 0.12 rad angular deflection inputs. These are
rendering settings, not manufacturing tolerances or an exhaustive surface
error certificate.

## Motion provenance and limitations

The original compact P5 nominal trajectory was not present with the recovered
inputs. A new capture was executed with the bundled MuJoCo WASM 3.16.0 runtime
using the compact geometry dimensions, original body mass/inertia tensors,
independent free puck, contact/friction, and opposing jaw coordinates.
The capture uses a computed-torque/PD arm controller and force-controlled
jaw drive. It is NOT a rerun of the earlier 28-scenario electromechanical
validation or the original electrical controller. It does not validate
motor current, thermal performance, functional safety, or hardware accuracy.
The capture XML includes contact proxies for nests, jaw pads, and the puck;
it does not reproduce a complete robot self-collision model. Arm joint
ranges in this capture are broad reconstruction bounds, not the mechanical
hardware's certified travel. The jaw working range remains 17.5–38.5 mm.

The puck is not welded or script-attached to the hand. Its motion comes from
contact and friction in the included capture, not a substituted visual path.
The closed-jaw command starts after the hand descends rather than closing
prematurely onto the puck top. Counterbalance torque is a torsion-spring
screening model; the displayed coil remains the original reference shape,
not a deforming flexible-body simulation. Catalog-envelope and unqualified
supplier-interface limitations remain those of P5.

## Reproduce

Requires Linux EGL/OpenGL (tested on Mesa software rendering), FFmpeg,
Python packages in `requirements.txt`, and Node.js. A discrete GPU or phone
performance guarantee is not implied.

```sh
python -m pip install -r requirements.txt
# Optional: regenerate the new contact capture. This does not run P5's old validation.
node source/capture.mjs
# Packaged meshes allow rendering without repeating CAD generation.
# To rebuild CAD tessellations, first remove assets/meshes/*.npz:
python source/build_meshes.py
OPENBLAS_NUM_THREADS=1 LP_NUM_THREADS=4 python source/native_film.py --width 1920 --height 1080 --fps 24
python source/finalize_film.py
```

Use `--shot 0` through `--shot 5` to render one shot. Use `--still --width 960
--height 540` for six camera tests. The geometry helper also contains an
experimental constructive ray-query compiler; that path is not used by
`native_film.py` or by the delivered video.

`reports/shot-*.json` records each production frame's camera, physical time,
inspection offset and raw RGB hash. The final verification records full
FFmpeg decoding, dimensions, frame counts, distinct decoded-frame hashes,
clip hashes, and the output MP4 checksum. The archive manifest verifies
packaged bytes, not physical-robot safety. No font files are distributed.
