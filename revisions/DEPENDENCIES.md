# Dependencies and rights boundaries

The source artifacts contain no new project-wide LICENSE or independent redistribution grant. Publication does not extend third-party licenses to project code, supplier models or older helpers. Preserve existing notices and verify rights before redistribution under another license or commercial use.

P5 Refined pins CadQuery 2.8.0, NumPy 2.3.5, SciPy 1.17.0, VTK 9.6.2, Numba 0.65.1 and Pillow 12.3.0 in its original requirements. Rendering additionally uses a C++17 compiler and OpenMP. Its custom renderer is not PBRT; the README cites PBRT concepts. No compiled renderer, fonts, image-generation assets or third-party texture pack is included in this revision addition.

P6-B separately pins NumPy 2.3.5, CadQuery 2.8.0 and trimesh 4.11.1. [Trimesh's upstream license is MIT](https://github.com/mikedh/trimesh/blob/main/LICENSE.md); it does not license this project. Resolve actual transitive OCP/OpenCascade and other package versions and retain their notices when creating a deployment environment. The requirements are source-delivered pins, not a newly installed or tested lockfile.

The P5 baseline's bundled MuJoCo runtime and its notices remain in their original repository locations. The additive source review did not install dependencies, run archived code or qualify mechanical hardware. Follow the [root baseline README](../README.md) for that separate edition.

P6-A source is unavailable. Its source-reported module names and historical test results cannot establish an independently runnable environment. P6-B's replacement-property input does not substitute for the missing P6-A algorithms.
