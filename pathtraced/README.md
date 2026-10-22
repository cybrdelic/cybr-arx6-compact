# Compact P5: native Monte Carlo film

The later **12-second, 1920×1080, 24 fps, 288-frame** CPU path-traced film uses the same compact-arm constructive design, mass records and reconstructed ten-second contact capture as the VTK films in the parent directory. It is a separate rendering pipeline, not a new mechanical model, validation result, or disassembly demonstration. A two-second moving reveal precedes the ten-second action with camera cuts.

## Renderer architecture

- `source/pathtrace.cpp`: standalone C++17/OpenMP renderer with per-mesh and instance BVHs, actual CAD triangles, diffuse and GGX/Smith–Schlick shading, finite rectangular emitters, next-event light sampling and power-heuristic multiple importance sampling. Russian roulette terminates later paths. Maximum depth is six surface interactions.
- `source/frames.py` and `director.py`: deterministic camera/pose inputs, linear translation and SO(3) rotational interpolation of the 120 Hz capture. All 288 retained inputs use 16 camera samples on robot pixels and 8 on floor/background. Inspection explosion is zero throughout this edit.
- `source/denoise.py`: geometry-guided four-scale à-trous denoising, filmic tone mapping and sRGB encoding. This is not a generative image model.
- `source/produce.py`: resumable full-frame rendering with source, input and image hashes. `finalize.py` checks completed frames, encodes and fully decodes the movie, and builds a source package.
- `source/export_native.py`: optional regeneration of the derived triangle cache from the parent's included native meshes; not needed for a fresh checkout.
- `source/pathtrace_all_lights.reference.cpp`: retained earlier all-light-sampling reference. `test_tracer.cpp` and `reports/` are historical evidence, not tests rerun during publication.

There are 278 parts and 778,022 retained triangles. Normal processing removes 24 degenerate coil triangles from the parent 778,046-triangle cache; it does not decimate valid geometry. Selected housing finish overrides are display-only. Design, mass and contact-capture bytes exactly match the parent inputs.

This is a finite-sample, depth-limited, denoised RGB rendering study. It is not an infinite-bounce reference, spectral or volumetric transport, glass/transmission validation, calibrated supplier finish, measured product photograph, or new hardware qualification. The original electrical/thermal and full self-collision limitations remain those of the reconstructed compact capture.

## Fresh checkout: restore before rendering

The 56,022,040-byte `assets/native.bin` is a **derived data cache, not an executable**. It is stored as deterministic gzip split into two exact byte parts to fit the publication transport limit. From the repository root:

```bash
python3 pathtraced/tools/restore_native_cache.py
```

The standard-library helper verifies every part, the gzip stream and the restored cache, then creates the expected path. It is idempotent and refuses conflicting files. No external or private assets are needed. Raw-cache SHA-256: `7c2db656ec1fe131df8a8761558458871440f5bad7b2ded5ba4081c77c0be29c`.

Rendering needs a C++17 compiler with OpenMP, Python packages listed here, and FFmpeg/ffprobe. Run in a working checkout because historical reports are replaced by fresh output:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r pathtraced/requirements.txt
python3 pathtraced/tools/restore_native_cache.py
mkdir -p pathtraced/frames pathtraced/previews pathtraced/reports pathtraced/assets/frame_inputs
g++ -O3 -march=native -fopenmp -std=c++17 -ffast-math pathtraced/source/pathtrace.cpp -o pathtraced/source/pathtrace
python3 pathtraced/source/director.py
python3 pathtraced/source/produce.py
python3 pathtraced/source/finalize.py
```

**Checkpoint warning:** `produce.py` accepts an existing frame when its PNG hash matches its saved record. It does not establish that the frame matches the current source or input hashes. After any source, camera, geometry or sampling changes, use a fresh output workspace with no reused rendered frames. A fresh checkout includes no completed frame sequence.

The pipeline requests four native render threads and creates a large linear proof frame as well as the image sequence. Budget additional disk and RAM; performance depends on the host. Compiler flags include fast-math, so cross-machine bitwise image identity is not promised. `finalize.py` writes its delivery MP4, poster and source ZIP in the repository root. That ZIP is the historical renderer delivery format, not this reviewed publication layout: it includes the locally built executable and raw cache, omits the added transport tools/docs, and contains fresh run logs. Review it separately before sharing. No renderer, simulation, compiled archive executable, or archived test was executed during publication review. The included compiled executable was deliberately omitted; build the provided C++ source locally.

## Preserved evidence and packaging

`reports/` and `assets/frame_inputs/` retain the supplied production records and exact camera/pose input bytes. All 288 decoded movie frames match the archived per-frame hashes and are distinct. The media is source-derived, not regenerated for this repository.

Only historical native-log output paths were made relative, and the optional `export_native.py` input-root default was made portable. All rendering, simulation and geometric mathematics are unchanged. `docs/ORIGINAL-MANIFEST-SHA256.json` identifies the original archive bytes, including the omitted compiled binary and unpacked cache, so it is a historical manifest, not a checksum list for this transport layout. `docs/ORIGINAL_README.md` preserves the original delivery notes.

No new project license is granted by publication. The parent dependency/license notes apply; this renderer also depends on the external compiler/OpenMP runtime, NumPy, SciPy, Pillow, Numba and FFmpeg, without vendoring them. The supplied requirements file installs VTK, although only optional cache regeneration needs it; the CPU renderer itself does not use VTK. No third-party font, image model, HDR image or texture library is bundled in this rendering addition.

## Portable build

From the repository root, run `python pathtraced/tools/build_native.py --check --smoke`. See [PORTABILITY.md](../PORTABILITY.md) for Windows/MSVC, Linux/GCC and macOS/Clang setup, optional serial operation, and verification scope. Existing Linux commands above remain historical reproduction details.
