# ARX / 6 — P5 refined geometry, aluminum, and antialiasing proofs

This package is a proof-stage refinement of the actual compact 278-part P5
model. It is not a new robot design or generated look-alike imagery. The two
still images are native Monte Carlo path-traced views of the revised CAD.
There is no new action-film export in this package.

## View

`renders/ARX6-P5-Refined-hero-1080p.png` and
`renders/ARX6-P5-Refined-closeup-1080p.png` are the delivery proofs.
The corresponding `-4K.png` files are the native-resolution masters.

Both views use the archived operating state at 2.5 seconds. The close-up
shows the elbow cartridge, forearm service panel, fasteners, and upper arm.
It intentionally crops the rest of the robot rather than rescaling parts.

## Real geometry changes

The archived constructive source is retained at `assets/design.json`.
`source/refine_cad.py` builds selected native OpenCascade solids, cleans
redundant Boolean edges, and adds real fillets/chamfers. It also cuts hexagonal
recesses in previously cylindrical screw heads. These are prototype geometric
details, not certification of a particular purchased fastener standard.

123 part instances receive modeled changes. They include 0.8 mm longitudinal
fillets on the upper-arm, forearm, and wrist rails; 1.2 mm service-panel corner
radii; 0.18 mm panel perimeter breaks; 0.35 mm service-cover edge radii;
0.6 mm outer housing-lip radii; and 2 mm baseplate corner radii. The per-part
report records the actually successful values, selected edges, rejected
attempts, volume, centroid, and full inertia. It is not a blanket smoothing
modifier on the old render mesh. The remaining instances are retained.

`cad/` contains the 123 revised STEP parts and native BREP equivalents.
`cad/ARX6-P5-Refined-operating-pose.step` includes all 278 named model instances
at the proof pose. The geometry verification report distinguishes instances
from solids. Inherited multi-solid reference-coil instances are preserved and
identified rather than silently merged or declared a single solid.

An initial envelope screen caught chamfers that filled small interior corners.
Those additions were removed by retaining the original solid envelope; the
final screen records zero added volume for every modified part. The earlier
failed screen remains in `reports/envelope-before-preservation.json`.

The modified STEP exports are reimported and checked for validity and solid
count. Their BREP tessellations use 0.012 mm linear and 0.065 rad angular
inputs, with crease-aware normals. These tessellation inputs are not a
machining tolerance. Unmodified native triangle records are copied unchanged.
The supplied renderer does not use a normal-only bevel to substitute for CAD.

## Materials

White enamel is replaced by satin aluminum with a directional anisotropic
microfacet response. Exposed aluminum adapters use a more visibly brushed
response. Dark housings use a coated-metal appearance, service caps have a
turned/anodized-metal response, and steel, brass, polymer, and rubber remain
differentiated.

Procedural textures modulate roughness, reflectance, and shading normals in
rigid-body coordinates. They include fine directional machining grain, turned
cap rings, restrained bead-blast variation, and subtle coating microtexture.
Fine patterns are attenuated with an approximate ray-footprint filter. This
is not full ray-differential filtering, measured optical data, real dirt, or
a simulation of a manufacturing process. Surface bump changes shading only;
the separate fillets and chamfers change the native geometric boundary.

The metallic shader uses anisotropic GGX visible-normal sampling and Smith
masking, with Schlick Fresnel. Four rectangular lights, next-event estimation,
power-heuristic multiple-importance sampling, and up to eight surface
interactions retain geometric indirect lighting, glossy reflections, and
soft shadows. There is no raster renderer, shadow-map pass, screen-space AO,
image-generation input, or frame interpolation in these proofs.

## Antialiasing and reconstruction

Each proof is traced at **3840 x 2160 with 64 camera paths at every native
pixel**, in an 8 x 8 stratification. Thin silhouettes no longer inherit a
lower sampling budget merely because the center ray misses the robot.
The thin-lens camera has a small aperture. The 1080p result uses four native
pixels per output pixel, nominally 256 camera paths before reconstruction.

Three geometry-guided a-trous passes operate at native resolution. A Lanczos
filter then downsamples the linear radiance to 1920 x 1080 before filmic tone
mapping and sRGB encoding. This is not upscaling, a sharpening trick, or a
post-render blur used in place of geometric sample coverage. The denoiser
and finite sample/bounce counts remain approximation limits. Temporal
stability has not been verified by a new film in this proof-stage delivery.

## Mechanical scope

The revised per-part volume, centroid, and inertia are measured from BREP.
`assets/refined-mass-properties.json` propagates their mass-property deltas
into the archived rigid-body values, using the densities declared in the
refinement script (2700 kg/m^3 aluminum, 7850 kg/m^3 steel, etc.). Purchased
mass overrides and inherited internal-mass assumptions remain unchanged.
This is an updated mass model, **not a rerun of the controller, motor-duty,
contact, clearance, spring-life, or safety validation suite**. The new
geometry has not been released for manufacture or hardware use.

An exact-BREP outside-volume screen, when present, tests whether changed
parts add appreciable material outside their old boundaries. It is not a
strength calculation, fit qualification, tool-access check, or continuous
assembly swept-volume audit. Earlier P5 qualification limitations remain.

## Reproduce

Python 3, CadQuery/OpenCascade, NumPy, SciPy, VTK, Numba, Pillow, and a C++17
compiler with OpenMP are required. The included binary geometry caches allow
rendering without rebuilding the CAD. No font files are needed or distributed.

```sh
python source/refine_cad.py
python source/export_refined_native.py
python source/verify_geometry.py
python source/check_envelopes.py
g++ -O3 -march=native -fopenmp -std=c++17 source/pathtrace.cpp -o source/pathtrace
g++ -O2 -fopenmp -std=c++17 source/test_refined.cpp -o source/test_refined
source/test_refined
python source/render_proofs.py
```

`render_proofs.py` reuses completed proof images when their report exists;
remove the corresponding output image/report to intentionally rerender after
changes. To intentionally regenerate CAD after editing refinement rules, remove
the `reports/cad-NNN.json` per-part checkpoints first. The frame reports contain the exact renderer and geometry hashes,
native logs, sampling histograms, resolutions, and PNG hashes. The archive's
SHA-256 manifest checks packaged bytes, not physical safety.

## Technical references

The sampling, reconstruction, and texture-filtering concepts follow the
standard approaches described by *Physically Based Rendering*, fourth
edition, chapters 8 and 10. The implementation here is the project's custom
renderer, not PBRT, Cycles, or a claim of equivalent image quality.

- PBRT, Stratified Sampler: https://pbr-book.org/4ed/Sampling_and_Reconstruction/Stratified_Sampler
- PBRT, Image Reconstruction: https://pbr-book.org/4ed/Sampling_and_Reconstruction/Image_Reconstruction
- PBRT, Texture Sampling and Antialiasing: https://pbr-book.org/4ed/Textures_and_Materials/Texture_Sampling_and_Antialiasing
- CadQuery class reference: https://cadquery.readthedocs.io/en/latest/classreference.html
