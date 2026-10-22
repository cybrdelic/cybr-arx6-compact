# ARX compact P5: exact film-to-code provenance

## Scope and result

This report records read-only inspection performed on 22 October 2026. Project source, archived executables, renderers and simulations were not imported or executed. JSON, XML and binary inputs were inspected independently. Historical rendering and simulation reports are distinguished from checks performed during this inspection.

The newest film is the compact-cartridge P5 path-traced edition, not the separate belt-drive mechanism. Its actual source exposes more than the exterior: 278 named constructive parts, detailed cut/union trees, six 100:1 cartridge drives, two enclosed torsion counterbalances, part-to-body ownership, supplier-interface assumptions, body mass tensors, opposed-rack constraints, a computed-torque/PD controller and an independently simulated contact-driven puck.

The film remains a later visualization of retained geometry and a reconstructed contact capture. It is not the original compact electromechanical validation. Internal shaft motion, brake engagement, electrical dynamics and thermal behavior are not implemented by this film's rendering/capture pipeline.

## Verified public basis

- Repository: https://github.com/cybrdelic/cybr-arx6-compact
- Exact commit: https://github.com/cybrdelic/cybr-arx6-compact/tree/0003382bd6a2e96f3bed065003efec35001982f7
- The public recursive tree identified this revision without truncation. Independently calculated Git blob identities matched all 636 checked files covering the parent source tree, the entire pathtraced subtree, parent design/mass/capture inputs and newest MP4. There were no mismatches or missing inspected files.
- Both supplied newest video attachments were identified as byte-identical to the preserved public MP4. Its SHA-256 was independently rechecked during source inspection.

Keep the complete repository at this revision, including the parent and pathtraced directories. The report is a source map, not a substitute for the actual modules and data.

## Exact backward provenance chain

### 1. Film and encoder

The [preserved MP4](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/media/ARX6-P5-Pathtraced-Action-1080p.mp4) is 3,585,174 bytes, SHA-256 `c298178f407f1c47591dc6749d0ae6e10b4e65c10b9e972a92762577acd11a22`.

The [historical video verification](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/reports/video-verification.json) records 1920×1080, 24 fps, 12 seconds, 288 decoded and distinct frames, and no audio. It identifies render-manifest SHA-256 `230733681d794dd1ac690dc33faf9afcbcbe414962fa4f47ed91d36e970618dc`, matching the inspected manifest bytes.

[finalize.py](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/source/finalize.py), lines 21–57, checks all 288 PNG/report pairs, creates chapter metadata, encodes libx264 CRF 16/preset slow/yuv420p/BT.709, fully decodes the movie and records the output hash. This encoding pipeline was read, not rerun during inspection.

### 2. Frame production and renderer

[produce.py](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/source/produce.py), lines 12–44, invokes the native renderer with the geometry cache and each retained frame-input binary, denoises the output and records raw RGB, PNG and frame-input hashes. All 288 retained frame-input SHA-256 values independently matched their saved frame reports. Each binary header specifies its frame index, 1920×1080, 16 samples, depth 6, explosion disabled and ten body transforms.

The actual production light-transport implementation is [pathtrace.cpp](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/source/pathtrace.cpp):

- Lines 71–115: per-mesh BVH construction/intersection.
- Lines 137–184: immutable triangle loading, rigid instances and top-level BVH.
- Lines 187–227: diffuse/GGX/Smith-Schlick scattering, finite area-light sampling, multiple importance sampling, finite-depth secondary paths and Russian roulette.
- Lines 230–255: thin-lens camera samples, scene-linear RGB and geometry guides.

The source contains four rectangular emitters. Robot pixels use 16 camera paths, floor/background pixels eight. Part IDs 2, 32, 66, 100, 132, 168 and 272 receive a display-only dark finish. The retained `pathtrace_all_lights.reference.cpp` is an earlier reference, not the production implementation.

[denoise.py](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/source/denoise.py), lines 7–50, performs four spatial à-trous passes guided by normals, depth, part ID and luminance, followed by a fitted filmic curve and sRGB encoding. There is no image-generation, optical-flow, screen-space-shadow or AO input in this path. It is finite-sample, depth-limited, denoised RGB rendering, not spectral/volumetric transport or a calibrated supplier-finish model.

### 3. Camera edit and physical-pose replay

[director.py](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/source/director.py) defines a two-second reveal sampling physical capture time 2.15–2.45 seconds, then the ten-second action interval with approach, grip, transfer, compact-joint and return viewpoints.

[frames.py](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/source/frames.py) reads saved 120 Hz body transforms, linearly interpolates translation and uses SciPy SO(3) Slerp for rotations. It does not invoke a controller or solver during rendering. Camera cuts change the view, not the source mechanical poses. Explosion remains zero throughout this film; no physical disassembly is demonstrated.

### 4. Triangle cache and constructive geometry

[export_native.py](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/source/export_native.py) reads the parent's 278 `assets/meshes/NNN.npz` files, computes 35-degree split normals, converts millimetres to metres and writes part ID, body index, material and triangle positions/normals. It retains 778,022 triangles after normal processing removes 24 degenerate coil triangles from the 778,046-triangle parent cache. Valid geometry is not decimated.

The two published compressed cache parts were independently decompressed in memory. The result was exactly 56,022,040 bytes with SHA-256 `7c2db656ec1fe131df8a8761558458871440f5bad7b2ded5ba4081c77c0be29c`. Parsing verified the cache signature, 278 sequential part IDs, 778,022 triangles and a complete byte-length match. The [cache manifest](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/assets/native-cache-parts.json) and [restoration helper](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/pathtraced/tools/restore_native_cache.py) identify the required byte parts.

The actual constructive evaluator is [build_meshes.py](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/source/build_meshes.py), lines 10–37, paired with [design.json](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/assets/design.json). It uses CadQuery/OpenCascade for boxes, cylinders, polygon extrusions, swept helices, transforms, unions, cuts and intersections. Tessellation inputs are 0.045 mm linear and 0.12 rad angular deflection, not manufacturing tolerances.

[geometry.py](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/source/geometry.py) also contains an experimental CSG ray-query-table compiler and the raster editions' pose helper. That experimental compiler is not the production path-traced renderer.

### 5. Simulation inputs, constraints and controller

[capture.mjs](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/source/capture.mjs) reads [capture-model.xml](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/source/capture-model.xml), [capture-parameters.json](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/source/capture-parameters.json), [reference.mjs](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/source/reference.mjs) and the bundled MuJoCo WASM 3.16.0 runtime. Its reconstruction integrates ten seconds at 1/2400 second and samples at 120 Hz. The retained [capture.json](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/assets/capture.json) has 1,201 samples of qpos[15], qvel[14] and ten body rigid transforms.

The XML contains six hinge joints, two opposite-axis jaw sliders, a freejoint puck, joint-equality jaw synchronization and a fixed rack-pinion tendon. Its eight actual collision geoms are four nest pieces, two pads, puck and floor, not the 278 detailed visible parts. Pad/puck contact uses explicit friction 0.65. The puck is not welded or script-attached to the gripper.

The controller combines mass/bias inverse-dynamics terms with joint PD, limits joints 1–3 to ±55 Nm and 4–6 to ±12 Nm, limits jaw force to ±14 N and applies linear joint-2/3 torsion-spring torques. It does not integrate motor electrical dynamics, current limits, temperatures or brake state. The reference constructs two five-second pick/place halves with quintic phase interpolation and analytical arm/wrist inverse kinematics; derivatives use ±0.00025-second finite differences. The reference is a control target, not the puck's integrated trajectory.

The [mass-property records](https://github.com/cybrdelic/cybr-arx6-compact/blob/0003382bd6a2e96f3bed065003efec35001982f7/assets/mass-properties.json) provide mass, COM, inertia tensors and component membership. Independent comparison verified exact equality of mass/COM/MuJoCo inertia records for all eight moving mechanical bodies against the XML.

## Hidden mechanism represented by the constructive source

Each part record contains an ID, name, owning body, full constructive tree, material, group, functional role, mass override, finish, bounds, inspection offset, qualification status and optional spin metadata. The model comprises 202 cartridge-group parts across J1–J6, 30 structural parts, 21 gripper parts, eight base-hardware parts, 12 counterbalance parts and five workpiece/fixture solids.

Across the instances, the constructive trees contain 1,741 transforms, 1,290 cylinders, 857 cuts, 332 unions, 106 polygon extrusions, 72 boxes, three intersections and two helices.

- Each cartridge has separate reducer housing/output, structural heat-spreader case, rear service cover, bearing bulkhead/standoff, front/rear bearings, stator/rotor, stepped carrier, spring-applied brake stator and rotor/hub, encoder board/target, output adapter and fasteners. These are recoverable parts, not exterior labels.
- Six drive records specify parent/child bodies, axes, origins, interface dimensions, 100:1 reduction, motor IDs 734439/814370, CSD-17/14-100-2UH reducers and Servo Slim 50005/50004 brakes.
- The gripper includes a module-0.3, 20-tooth pinion, opposed racks, guide rods/bushings, pads, bridge, motor and cable-clamp components. Several status fields identify P5 rack-passage and motor-envelope clearance revisions.
- Both counterbalance modules contain cases, removable covers, reaction arbors, coils and fixed/moving reaction pins. Joint 2 uses 5 mm wire, 50 mm mean coil diameter, six active turns, stiffness 6.46015082530387 Nm/rad and free angle −0.65 rad. Joint 3 uses 4 mm wire, 40 mm mean diameter, six active turns, stiffness 3.3012251703041877 Nm/rad and free angle +0.55 rad.
- Structural geometry includes continuous fabricated load-path solids, cartridge mounting and output adapters, service panels, clamp hardware and a physical tool-to-gripper neck.

### Hidden metadata is not the same as implemented motion

Twenty-four part records carry 100:1 relative spin metadata for motor rotors, carriers, brake hubs and encoder targets. The film exporter does not serialize that field. Its frame writer supplies only ten rigid-body transforms, and the renderer groups the components by those bodies. Thus those internal components exist geometrically but do not rotate separately at shaft speed in this edition. The coils also keep their reference geometry instead of deforming; brake-role descriptions do not constitute an implemented brake-engagement simulation.

Supplier internals are deliberately sealed envelope representations. The source marks reducer internal CAD absent, motor windings not reverse engineered, rotor/reducer mass splits assumed, bearing life/load selection provisional, brake hubs needing supplier confirmation and encoder electronics unqualified. Interface geometry and functional metadata are present; complete supplier internal CAD and a general mating/tolerance solver are not.

## Original basis versus later additions

- Retained compact mechanical basis: design.json, mass-properties.json, part descriptions, six drive records and two spring records. Earlier gripper geometry is retained from P2 with noted P5 changes. The inspected compact tree does not contain the original high-level script that authored this JSON or regenerated its mass tensors.
- Later reconstruction: capture-model.xml, capture-parameters.json, reference.mjs, capture.mjs and capture.json. This supplies the cinematic editions' motion, not the missing original compact nominal/electromechanical run.
- Raster additions: build_meshes.py, the geometry.py pose helper, native_film.py and finalize_film.py. V2 adds native_film_v2.py, render_delivery_v2.py and complete_pending_v2.py. Its exploded/reverse-offset views are presentation staging, not collision-checked physical disassembly.
- Latest addition: the pathtraced pipeline. Its design, mass records and contact capture independently match the parent files byte for byte. It changes light transport, display finishes, camera edit and image reconstruction, not the mechanical model or qualification status.

## Reusable modules and required bases

For geometry work, retain the actual build_meshes.py evaluator and design.json, plus NumPy, CadQuery and OpenCascade. The evaluator has top-level build/write behavior and should be adapted into an explicit callable before importing it into another application. The frozen design is more informative than a mesh-only export because it retains construction, ownership and engineering metadata.

For dynamics work, retain mass-properties.json, capture-model.xml, capture-parameters.json, reference.mjs and capture.mjs with the exact bundled runtime/mujoco.js and runtime/mujoco.wasm. A new capture replaces the saved capture.json; it does not reproduce the unavailable original electromechanical validation.

For exact retained motion, use capture.json and frames.py. For the latest appearance, use director.py, pathtrace.cpp, denoise.py, produce.py and finalize.py, with the published frame inputs and restorable native cache. Optional triangle-cache regeneration additionally needs all 278 parent NPZ meshes and export_native.py. The C++ renderer needs a C++17 compiler/OpenMP; the pipeline also needs Python dependencies and FFmpeg/ffprobe.

This repository is a concrete mechanism case study and renderer, not by itself a complete general-purpose geometry/design framework. Reuse the actual modules with their required data, rather than reconstructing them from screenshots or this report.

## Availability and reproducibility limits

1. Film bytes, cached geometry, all frame inputs, replay/controller source and bundled MuJoCo runtime are present. No private asset is required merely to replay/rerender this edition. Restore the native cache from its two published byte parts before rendering.
2. The original compact nominal trajectory, electrical controller, 28-scenario electromechanical validation and upstream authoring/mass-generation scripts are not in the inspected compact tree. Recovering these remains a separate source-provenance question. Results from the incompatible belt-drive design must not be attributed to this compact mechanism.
3. Qualified supplier internal CAD, tolerance stackups, spring deformation/fatigue/preload procedures, real brake response, electrical/thermal qualification, complete self-collision and collision-free service extraction are absent or explicitly unqualified. Broad capture joint bounds are reconstruction bounds, not certified travel limits.
4. The original production PNG sequence and raw linear proof frame are not included in the reviewed public layout. Historical per-frame hashes and the encoded movie remain. Source-to-original-pixel identity was not independently reproduced; source, file bytes and data relationships were inspected. Saved numerical/transport reports are historical evidence, not tests rerun during this inspection.
5. The archived compiled renderer is intentionally omitted and must be rebuilt. Pathtracer Python dependencies are unpinned; compiler/FFmpeg/OpenMP versions are not fully locked. Native/fast-math compilation and encoding make cross-host bit-identical film reproduction unpromised.
6. produce.py accepts an existing PNG when its hash matches its old record; it does not validate that record against current source/input hashes. Changed inputs require a fresh output workspace. build_meshes.py likewise skips existing mesh caches, so an all-cache-hit call is not fresh geometry validation.
7. Published export_native.py has a portable input-root adjustment, explaining its difference from the historical render-manifest hash. Production renderer, frames, director, denoiser and producer hashes match that manifest. finalize.py matches the archive manifest rather than appearing in the earlier production source-hash map.
8. No project-wide license grant was present in the inspected tree. Public availability is not a blanket reuse/redistribution grant; dependencies retain their own notices.

## SHA-256 anchors

| Repository-relative file | SHA-256 |
| --- | --- |
| media/ARX6-P5-Pathtraced-Action-1080p.mp4 | c298178f407f1c47591dc6749d0ae6e10b4e65c10b9e972a92762577acd11a22 |
| assets/design.json | 48b3dcf993f78a9e1f386c8458644bb5829d627c895b88e58e616ae14aa565a0 |
| assets/mass-properties.json | 6919a163453a977e80b97eca815a69152804b9f131408f6909611155669f190e |
| assets/capture.json | ba938e6a1e0a829c52435a5ef165e7364bf8cb072a604bb18ff0577edf6f1b33 |
| source/build_meshes.py | 1b2e4f087634f8ff41ad450195a2a35ef3ef6445d1bc25efbad9c797f7fb2e50 |
| source/capture.mjs | 05745d4a46dc20e5dc2733ab1b34e44d1c3ec9b5aace2a7fe0ea6644b8ee02e5 |
| source/reference.mjs | 20da728baa7405f352d820ba873d7e2d8be7cbf42c3589aa9c83373419431895 |
| source/capture-model.xml | 15d293a0e6a25ab06f8526336d623cfc0dc2fecf928c0c624d3441ccd02e90fd |
| source/capture-parameters.json | 2272c35a842a0e56ca469a24e4cbb938053d10f7e0cc50bedfde9238e2ee1f7a |
| pathtraced/source/pathtrace.cpp | 94514f41bdd3468e9adb875ab3485d1ba68ebaefcd466750e67b403c09d09256 |
| pathtraced/source/frames.py | 67e920cd0511fbc5cf831e9e5ae555582d5edd2b5b3e0197ca651f516b365f11 |
| pathtraced/source/director.py | b95c9a4ac1716515ccad032836fcbc97029726bcfae4a1ebbc1d2159000ecc8a |
| pathtraced/source/denoise.py | 513c95430897a4dae7a360b9677732180688e9592f45c2175cf719c296d19a43 |
| pathtraced/source/produce.py | b48c2d24e80537503cd114ae2f90909cf6d4558ec9f610c682b8ccaeb7f8bef0 |
| pathtraced/source/finalize.py | 8b90320986872c960238d4efeb6243fe2ff323820a330ed85a75cc5aab8e466f |
| pathtraced/source/export_native.py, published portable version | 8dab69c7f5dcb0f6dd346be6fd1efd8b5e462bbaa8943b124c51846b0cf6189c |
| source/export_native.py, historical renderer archive version | 96227ea9b9d784955bd16aabd27634ace0a038890d21181a59663d39521715dd |
| pathtraced/assets/native.bin, restored derived cache | 7c2db656ec1fe131df8a8761558458871440f5bad7b2ded5ba4081c77c0be29c |
| pathtraced/reports/render-manifest.json | 230733681d794dd1ac690dc33faf9afcbcbe414962fa4f47ed91d36e970618dc |

