# Actual source architecture and reuse boundaries

Use these modules and their data, not reconstructed screenshots or this prose in place of source. The [exact reference-film chain](FILM-TO-CODE.md) maps the original compact model, controller, constraints, capture, geometry exporter and renderer at the verified public commit.

## P5 Refined: actual constructive and BREP source

`p5-refined/assets/design.json` is the retained 278-part constructive model, including ownership, materials, cuts/unions and mechanism metadata. `assets/mass-properties.json` and `assets/capture.json` are inherited baseline data; the two still proofs sample archived time 2.5 seconds. Original high-level compact authoring/mass-generation scripts are not thereby recovered.

- `source/cad_core.py` evaluates constructive geometry and provides native solid/property operations.
- `source/refine_cad.py` adds actual fillets, chamfers and hex recesses to 123 selected instances, retaining per-part checkpoints and rejected attempts. This is not a normal-only bevel.
- `source/verify_geometry.py` checks STEP/native solid properties; `source/check_envelopes.py` compares changed solids against original envelopes. The earlier failed envelope report remains preserved.
- `source/export_refined_native.py` creates the refined native cache from changed BREP tessellations and retained original triangle records. `source/revalidate_native.py` independently checks rebuilt geometry against delivery data.
- `source/frames.py`, `source/proof_cameras.py` and `source/part_centers.h` provide the actual frame/camera/material-coordinate inputs.
- `source/pathtrace.cpp` is the actual metallic Monte Carlo renderer, with anisotropic material response and procedural shading. `source/denoise.py` performs geometry-guided reconstruction; `source/render_proofs.py` drives the two proof renders. `source/test_refined.cpp` is delivered test source, not an executed test claim from this review.
- `source/package_release.py` is original package-authoring code; it is not the Git publication transport helper.

The archive contains 278 instances and inherited multi-solid coils, not 278 guaranteed single solids. Its mass delta is about -4.91667 g. Geometry changes did not trigger a new whole-arm contact/dynamics qualification. Preserve that distinction when adapting the model to GEO.

## P6-A: precise implementation gap

The authentic posed STEP, engineering dossier, searchable review and proof images are available under `p6-a-petg`. The source ZIP identified in that README is not recovered. Source-reported builders, revised capture/controller, native exporter, FEM/thermal analysis and dielectric renderer cannot be recovered from its assembly STEP or image pixels. The HTML contains a report/table filter, not the missing implementation. Never label this evidence-only directory a complete runnable P6-A project.

## P6-B: actual print-first prototype code

Six original modules and their required inputs are under [p6b-print-first](p6b-print-first/README.md). They use revision-relative paths.

- `source/audit_print_first.py` combines 278 constructive records with P6-A replacement properties to audit 398 stable IDs. The 136 printing/redesign targets are not completed parts or a printed mass percentage.
- `source/build_structural_prototypes.py` imports original Refined BREP IDs 274/275, builds 6 mm reinforced spans, splits the upper frame with a 0.30 mm gap and creates an 80 mm lap coupler. It adds captive-nut pockets and sleeve clearances, retaining a documented 0.15 mm elbow-collar radius change. Proposed splice bolts/sleeves are specified, not modeled. Joint ends, fits, anisotropy, creep and powered loading remain unqualified.
- `source/build_printed_gear_trials.py` constructs sampled involute flanks for a module-1.2, 20-tooth pinion and matching rack. These are not the existing module-0.3 integrated gripper. Fourfold pitch radius requires fourfold ideal pinion torque for equal rack force. Roots are radial transitions, not generated trochoids; bridge, jaw, transmission and controller integration remain open.
- `source/screen_print_first.py` implements 36 uniform-beam bending/shear comparisons and uncalibrated compliance sensitivities. Twelve cases exceed the selected 0.5 mm comparison threshold. These are not whole-arm FEA, actual TCP error, dynamic qualification or lifetime predictions.
- `source/verify_delivery.py` checks topology, build bounds and saved part/intersection/screen data. It does not execute whole-arm dynamics or thermal validation. `source/build_review.py` renders the real disposition records as a searchable table.

`inputs/P5-design.json` exactly matches the retained constructive design. `inputs/P5-upper-frame.brep` and `P5-fore-frame.brep` exactly match Refined `cad/274.brep` and `cad/275.brep`. `inputs/P6A-design.json` contains replacement properties/masses, not serialized P6-A builders, controllers or renderers.

GEO can reuse the genuine CSG evaluator, part/body records, native BREP construction, constraints/controller and explicit engineering checks. A generalized mating/tolerance system, supplier internals, electrothermal qualification and collision-checked manufacturing/service paths are still additional engineering, not capabilities established by these artifacts.
