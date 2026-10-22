# ARX / 6 — P5 native path-traced action

This revision replaces the earlier rasterized VTK presentation with a native
C++ Monte Carlo path tracer. It is not a grade of the old MP4, not a recording
of an image-generation output, and not the former single-fragment CSG renderer.
It is a new renderer of the compact P5 mechanical model.

## Film and content

The release film is 1920 × 1080 at 24 fps. The twelve-second edit contains a
moving two-second reveal and the complete existing ten-second contact recording,
with gripper and compact-joint detail cuts. Camera cuts change the viewpoint,
not the source mechanical poses. No optical-flow video-frame interpolation is
used. There is no audio. This cut does not include a physical disassembly or
reassembly procedure. The earlier heuristic explosion was not a validated
service sequence and is not presented as one here.

## What is path traced

Every output frame starts from new camera rays through the scene. Rays intersect
the actual CAD-derived surface triangles using reusable two-level BVHs. The
integrator samples diffuse and rough specular scattering, traces secondary
paths, connects surface points to four rectangular area emitters, and combines
light/BSDF strategies using a power-heuristic MIS estimator. Paths may have up
to six surface interactions, with Russian roulette after the early bounces.
Glossy floor/object reflections and indirect illumination come from geometry
intersections, not a screen-space reflection or AO pass. Shadow maps are not
used. The camera has a small physical thin-lens aperture.

Materials use an isotropic GGX/Smith approximation, Schlick Fresnel and a
metallic/diffuse mixture. They are proposed display appearances, not measured
optical properties or a supplier finish certification. The finite bounce limit,
finite sampling and denoising are approximation limits; no claim of an exact
infinite-bounce or fully unbiased final image is made. There is no transmission,
volumetric transport, spectral rendering or simulated sensor response.

Six cartridge cases and the base (part IDs 2, 32, 66, 100, 132, 168, 272) receive
a dark display finish. This does not change CAD dimensions, masses, contacts,
actuator parameters or the physics recording. Other part finish assignments
come from the supplied canonical design.

## Sampling and reconstruction

Robot pixels use 16 camera-path samples; floor/background pixels use 8. The
exact per-frame sample histogram is recorded. High-frequency noise is reduced
by a four-stage geometry-guided a-trous spatial filter. It uses the renderer's
own surface normals, distance and part IDs; it is not a generative image model.
A fitted filmic curve is followed by sRGB encoding. This is not a calibrated
ACES color pipeline. The capture is native 1080p, not an enlarged lower-
resolution render. There is no temporal frame synthesis or duplicated-still
pan/zoom shortcut. A settled operating state can legitimately be visually still;
independent decoded-frame hashes are recorded rather than manufactured.

## Preserved model and motion

`assets/design.json` is the unchanged 278-part compact P5 constructive source,
SHA-256 `48b3dcf993f78a9e1f386c8458644bb5829d627c895b88e58e616ae14aa565a0`.
The native capture data contains 778,022 triangles. The input tessellations had
778,046; 24 degenerate coil triangles were removed by the normal-processing
stage. No mesh decimation, arbitrary part shrinking, substitute shell or
look-alike robot is used. Vertex positions are converted from millimetres to
metres; 35-degree crease-split normals are used for rendering.

`assets/capture.json` is unchanged from the prior cinematic source package.
It is the reconstructed P5-based computed-torque/contact recording, **not**
the original 28-scenario electromechanical validation and not measured hardware.
The independent workpiece and jaw/body poses are read from that capture, not
visually welded to the gripper. No mechanics were redesigned or requalified by
this rendering change. Previous supplier-interface, spring, safety and physical
qualification limitations remain.

## Source and reproducibility

`source/pathtrace.cpp` is the actual production light-transport implementation.
`source/frames.py` reads and interpolates the existing rigid-body poses on SO(3).
`source/director.py` defines the camera edit. `source/denoise.py` performs the
explicit spatial filter. `source/produce.py` checkpoints separately rendered
frames. `source/finalize.py` refuses incomplete captures, encodes the PNGs,
fully decodes the MP4, and checks the source archive's member hashes.

The included native surface file is enough to render without CADQuery or VTK.
`source/export_native.py` documents the initial export from the earlier
cinematic package. Its original input location is session-specific; point
`ORIGINAL` at an extracted `ARX6-P5-Cinematic` source package only when repeating
that optional tessellation/normal export. `assets/native.bin` is its verified
result. Never use the supplied CPU binary as a cross-platform executable;
recompile on the target computer. It was compiled for the capture host.

A Linux environment with a C++17 compiler, OpenMP, Python and FFmpeg is required.
There is no claim of real-time playback rendering on a phone or of a CUDA build.
The MP4 itself needs only a normal video player.

```sh
python -m pip install -r requirements.txt
g++ -O3 -march=native -fopenmp -std=c++17 -ffast-math \
  source/pathtrace.cpp -o source/pathtrace
python source/director.py
OPENBLAS_NUM_THREADS=1 python source/produce.py
python source/finalize.py
```

Frames can be resumed only for the **same** frozen source and input files.
To change materials, lights, geometry, camera or samples, start a separate
output workspace; do not mix old frame checkpoints with modified inputs.
The current capture checks that its source files do not change during its run.

## Evidence and limits

`reports/numerical-tests.json` compares BVH hits to an independent brute-force
intersection implementation and checks finite/nonnegative BSDF samples. These
are sampled software checks, not a proof of every configuration.
`reports/transport-ablation.json` compares one-interaction and six-interaction
renders at the same pose. `reports/render-manifest.json` records the actual
renderer settings, source hashes and execution time. `reports/frame-*.json`
contains each frame's physical timestamp, camera, ray count, sample histogram,
raw RGB hash and PNG checksum. `reports/video-verification.json` contains full
MP4 decode results, format, file hash and a PNG-to-video color comparison.

Background algorithm references: *Physically Based Rendering*, fourth edition,
sections 13.4 (path-tracing MIS and roulette) and 9.6 (microfacet roughness).
This package is not PBRT or Blender/Cycles and makes no equivalence claim to
those renderers.
