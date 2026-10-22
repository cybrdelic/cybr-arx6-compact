# ARX / 6 — P6-B print-first redesign checkpoint

## Corrected requirement

Print every component that can credibly be redesigned for the intended job, including the primary structure. Do not define PETG as covers-only and do not retain an entire aluminum frame merely because the previous CAD used aluminum. Transparent PETG is the target for rigid printed parts. Printable flexible pads/seats use TPU rather than pretending rigid PETG has rubber properties.

This package is a **complete manufacturing-disposition audit plus the first structural/gear test articles**, not a finished whole-robot conversion. Targets are not certifications. It does not contain a new motion film, a fully integrated printed robot assembly, or a new whole-arm dynamics/FEA/thermal validation.

## Delivered now

- All **398 existing P6-A part records** reviewed individually in `reports/part-register.json` and the searchable HTML review.
- **136 existing records** assigned to printing or print-oriented redesign, including hybrid interfaces and replacement transmission architectures. The 12 CSD records represent the case/output envelopes of six purchased reducers; they are NOT 12 newly designed printable gears. Repeated TPU seats are counted as instances. The target count is not a count of completed STL files or a printable percentage by mass.
- **Four real structural CAD/STL test articles**: the two halves of the upper frame, its internal lap coupler, and the reinforced forearm frame.
- **Two real printed-gear tooth trials**: a module-1.2, 20-tooth pinion and a matching-module rack. They are not integrated gripper replacements.
- Source, STEP/BREP, millimetre-unit STL, body-local mass properties, a 36-case uniform-beam tradeoff screen, and file/geometry verification.

## What becomes printed

The target includes the base, upper/forearm links, turret/wrist yokes, structural actuator cases, reducer/carrier structures, custom bearing carriers, output adapters, motor-support structures, gripper bridge and jaws, racks/pinion, cable-management parts, sensor mounts, inspection covers, spring enclosures and workpiece nests. A part carrying load is a reason to redesign its section and connections, not to exclude it from printing.

Printed reduction gears are in scope. Existing precision harmonic units are not silently declared unprintable, but replacing them requires actual tooth geometry, a new reduction topology if needed, ratio/efficiency/backlash analysis, bearing arrangement and load/life testing. Printing a solid catalog envelope would not implement a gearbox. The original CSD ratings are not transferred to a printed replacement.

## Metal and bought-in exceptions

Small metal screws/nuts, preload sleeves/washers, rolling elements, concentrated wear shafts/pins, winding/magnet/PCB parts, friction/electromagnetic brake internals and the current steel springs remain functional hardware. These are item-specific exceptions, not a hidden full metal skeleton. A printed carrier may still use a local bearing sleeve, metal shaft, captive nut, or heat-transfer plate. Customized rotor and spring hubs are themselves in the printed/hybrid redesign scope.

Compression limiters and inserts are not cosmetic: they provide localized paths for bolt tightening loads. Their dimensions must be matched to the new printed host. See source [3]. No new bolt tightening torque is released.

## Structural prototypes actually built

The refined P5 upper and forearm BREP solids are preserved under `inputs/`. Their tube spans are reinforced from **2.5 mm to 6 mm nominal wall thickness** while keeping the existing external link envelope. These are real Boolean additions to load-bearing geometry, not render thickness or an aluminum skeleton hidden by a shell.

The 357 mm-long upper frame is split at parent Y=148 mm, with a 0.30 mm joint gap. An 80 mm-long internal PETG coupler has 0.20 mm nominal side clearance, rounded outer corners, and four crossed sleeve/bolt bores. Proposed M4 bolts and metal compression sleeves are listed in the report. The bolt/sleeve hardware is **not yet modeled in the new STEP assembly**. Load-transfer slip, fastener bearing, creep and fatigue remain unqualified.

The first coupler geometry interfered with the socket's inner corner fillets; its outer corners were rounded to 1.4 mm and the final three-piece CAD intersection test reports zero overlap. An inherited elbow-collar tangent topology produced a nonmanifold STL despite BREP validity. A local radius change from 36.5 to 36.65 mm over Z=18.8..22.2 mm removes that pinch. This is an actual clearance change requiring fit review, not an invisible mesh repair.

The cover attachment holes now have through clearances and inward captive-nut pockets instead of assuming the old tapped aluminum threads remain in plastic. Revised cover screw lengths are candidate values; full cap/washer/seat integration is not complete. Original actuator-end flange geometry is retained as a starting interface and is **not yet strengthened/qualified for printed loading**.

### Print-file dimensions

| Test article | Bounding size, mm |
|---|---:|
| Upper frame, proximal | 66 x 180.85 x 47 |
| Upper frame, distal | 88 x 175.85 x 48 |
| Internal lap coupler | 47.6 x 80 x 31.6 |
| Reinforced forearm | 79 x 169 x 72 |
| Gear tooth trial | 26.4 x 26.4 x 12 |
| Rack tooth trial | 60.32 x 7.2 x 12 |

Files use millimetres. Structural STL orientation puts the beam length in the XY plane. Every STL lies inside the nominal Bambu A1 build cube, with a separate 246 mm planning-envelope check for the structural parts. This is **not** proof that supports, plate exclusions, adhesion, bridges or the chosen slicer profile are correct. No G-code is provided. Manufacturer machine reference [1].

## Gear redesign consequence

The current gripper uses module 0.3 with 20 teeth. The trial uses module 1.2 and 20 teeth: pitch radius grows from 3 to 12 mm. At the same output-shaft torque, ideal rack force falls to one quarter. Keeping the same rack force requires four times the pinion torque, normally implying coordinated reduction/motor/control changes. Geometry, jaw passages and bridge dimensions must change as well.

The trial pinion has a 4.1 mm bore for a 4 mm test mandrel, not the current motor shaft. The flanks are sampled involutes; root transitions are simple radial segments, not a cutter-generated trochoid. No mesh/contact-ratio, root-strength, backlash, wear or lifetime test has been executed. The purpose is to establish a genuinely printable tooth trial instead of calling the metal tooth set print-ready.

## Engineering screen and limits

`source/screen_print_first.py` executes 36 uniform-beam surrogate cases covering two rectangular link sections, two wall thicknesses, three assumed stiffness sets and three transverse loads. Bending and shear terms are explicit. Nominal PETG assumptions are E=1.5 GPa and G=0.28 GPa; the lower-stiffness sensitivity uses E=0.8 GPa and G=0.22 GPa. These are assumptions, not measurements of the user's filament or print. The reference aluminum stiffness is also a declared comparison input.

For the same PETG modulus, the nominal section second moment increases approximately 1.91x for the upper span and 2.01x for the forearm span. The 6 mm-wall, 25 N nominal-PETG surrogate predicts 0.442 mm and 0.176 mm deflection respectively. These are **not actual robot TCP deflections**: the uniform surrogates omit real end flanges, holes, bolted splice, bearing/contact compliance and the coupled robot geometry. They do not establish payload or accuracy. At higher loads/lower stiffness, chosen comparison thresholds fail; those results are retained.

Compliance-factor studies (1x, 2x, 4x, 8x) show sensitivity only. There is no fitted time-temperature creep curve and no predicted service life. Supplier typical coupon properties explicitly are not application design allowables [2].

The 25/40 unfavorable thermal cases in P6-A are not erased by printing more structure. Printed motor cases require redesigned heat rejection and a new duty-cycle thermal model. The supplied link/gear test pieces do not solve that problem.

## Verification executed

All six test STL files are watertight, consistently wound, single-component meshes with positive volume. The associated six STEP test parts reimport as valid single solids. The nominal upper-frame three-piece assembly has zero pairwise overlap. The 398-record inventory has unique IDs and no unclassified record. Source inputs are hashed, and a ZIP manifest checks all included bytes.

These are geometric and code checks, not physical printing, whole-arm collision clearance, nonlinear joint mechanics, thermal qualification, motor sizing, fatigue, electronics safety or real-world assembly validation. Do not put the structural test articles into a powered or spring-loaded arm on the strength of these file checks.

## Reproduce

Python 3 with the packages in `requirements.txt`:

```sh
python source/audit_print_first.py
python source/build_structural_prototypes.py
python source/build_printed_gear_trials.py
python source/screen_print_first.py
python source/verify_delivery.py
python source/build_review.py
```

The source inputs are bundled. Original P6-A and P5 files are not overwritten. No image-generation outputs or font files are included.

## Sources

[1] Bambu Lab A1 official technical specifications, nominal 256 x 256 x 256 mm build volume. `https://bambulab.com/en/a1/tech-specs`

[2] Polymaker PolyLite PETG technical data and its explicit typical-values/application disclaimer. `https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/petg-pet/polylite-tm-petg`

[3] SPIROL, compression-limiter and insert load-path guidance. `https://www.spirol.com/resources/white-papers/how-to-properly-mate-compression-limiters-and-threaded-inserts-in-plastic-assemblies/`

[4] Harmonic Drive CSD-17-100-2UH manufacturer data. This describes the purchased original, not a printed substitute. `https://www.harmonicdrive.net/products/gear-units/gear-units/csd-2uh/csd-17-100-2uh`
