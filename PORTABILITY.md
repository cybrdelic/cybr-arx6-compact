# Portable setup and bounded verification

These entry points support Windows, Linux and macOS with Python 3.12, Node.js 22+, CMake 3.18+ and a C++17 compiler. Use Visual Studio Build Tools with its C++ workload on Windows, GCC/Clang on Linux, or Xcode Command Line Tools on macOS. OpenMP is optional; Apple Clang and other compilers without it use the same serial renderer. No global compiler configuration is changed by the build helper.

Create an isolated environment with `python -m venv .venv`. Activate with `.venv\Scripts\Activate.ps1` in PowerShell or `source .venv/bin/activate` in Bash/Zsh. Then run from the repository root:

```text
python -m pip install -r requirements.txt
python tools/restore_original_film.py
python pathtraced/tools/restore_native_cache.py
python -m unittest discover -s pathtraced/tests -v
python tools/smoke_cad.py
node source/capture.mjs
python source/inspect_capture.py
python pathtraced/tools/build_native.py --check --smoke
python tools/smoke_raster.py
```

`capture.mjs` writes a fresh reconstructed trajectory and `inspect_capture.py` writes its current review. Run these in a working copy; historical captures/reports should be preserved when comparing provenance. The CAD smoke evaluates representative actual Boolean and helical parts without replacing the packaged meshes. Full mesh regeneration remains `python source/build_meshes.py` after moving cached meshes aside.

The CPU build uses a short, checkout-specific temporary directory on Windows to avoid legacy CMake/MSBuild path-length limits. On other systems it uses `pathtraced/.build/native`. Override with `--build-dir`; use `ARX_PATHTRACER` to select an explicitly built executable for production. `--serial` disables OpenMP without changing the transport integrator. MSVC may warn that temporary build outputs can affect incremental builds; removing an expired cache simply requires rebuilding.

The production path tracer accepts one path per line with `--stream-lines`, so paths containing spaces work. The legacy whitespace-delimited `--stream` interface is retained. `produce.py` selects the portable build automatically and uses the line protocol. FFmpeg and ffprobe are required on PATH for film encoding/verification, but not for CAD, dynamics, or the bounded CPU frame.

The VTK film renderers select native WGL on Windows, native Cocoa on macOS, and EGL for headless Linux. `ARX_RENDER_BACKEND=native`, `egl`, or `osmesa` overrides this selection where that backend is available. The CPU tracer is available when no compatible GPU context exists. A context probe or one frame does not certify an entire cinematic film, driver, or physical device.

The three-OS CI workflow installs fresh dependencies, evaluates real CAD, regenerates and checks the reconstructed solve, restores verified data, builds with the host compiler, runs 128 intersection and 9,000 shading checks, and renders a bounded CPU frame. A workflow definition is not a passing CI run; consult Actions for each platform's current result.

Windows audit of published baseline `0003382bd6a2e96f3bed065003efec35001982f7` reproduced the contact solve and numerical renderer tests. The cache fix preserves exact digests and no-overwrite semantics, including filesystems where hard links are unsupported. This audit does not cover subsequently recovered refined geometry, any new film, or hardware qualification. See the root README for physical-model limitations.
