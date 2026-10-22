# ARX / 6 — compact P5, restored v2 short-cut renderer

This restores the v2 lighting and staged inspection code recorded in the
conversation to the retained, original P5 cinematic source. It does not recover
the original v2 MP4 bytes. A video produced by this project is a fresh render.

The compact P5 geometry and captured physical states are unchanged. The CAD
has 278 modeled instances. The mesh input is native CAD tessellation, not image
generation and not a single-pass constructive shader.

## Intended short cut

- 0–3 seconds: moving reveal.
- 3–7 seconds: the first four seconds of the recorded action cycle.
- 7–12 seconds: staggered component inspection offsets.
- 12–15 seconds: reverse offsets toward the assembled pose.

The short cut does not contain the entire ten-second pick/return cycle.

## Rendering

The restored v2 parameters use PBR materials, a procedural HDR studio environment,
three scene lights, 2048-pixel shadow maps, 32-sample screen-space ambient occlusion,
and filmic tone mapping. Native frames are 1920 × 1080 at 24 fps.
Depth of field was bypassed in the recorded v2 code; it is not claimed active.
The ambient-occlusion kernel is not the earlier proposed 96-sample setting.
No generated images or optical-flow frame interpolation are used.

## Inspection limitation

The component-role staging is heuristic. The code ranks component groups and
applies saved explosion offsets. It has NOT been validated against tool access,
fastener rotation/thread engagement, supported loads, spring unloading, press
fits, retained joints, cable disconnection, or collision-free extraction paths.
It therefore is not an exact real-life disassembly/reassembly procedure, despite
earlier wording in the conversation. The reference spring shape is not an
animated, validated spring deformation model.

## Motion provenance

The input capture is the previous reconstruction using compact P5 dimensions and
mass properties. It is not a rerun of the original 28-scenario electromechanical
validation and does not qualify the physical robot. The retained `capture.mjs`
and capture XML describe that reconstruction.

## Reproduce

Requires Python, NumPy, SciPy, Pillow, VTK, FFmpeg and Linux EGL/OpenGL.
The packaged meshes make CAD regeneration unnecessary for rendering.
Run `python source/complete_pending.py` to render missing frames with at most two workers, encode the cut, and verify it.
For manual batches, run `python source/render_delivery.py --worker SHOT START END`.
The requested frame ranges are shot 0: 0–72; shot 1: 0–96; shot 4: 0–120;
shot 5: 0–72, with END exclusive. Use batches of 20 frames or fewer.
Then run `python source/render_delivery.py --finish` to encode, concatenate,
and independently decode/check all 360 frames.

The original longer-cut scripts are retained but are not the v2 short-cut entrypoint.
