# Compact P5 cinematic revision map

This repository preserves one compact-arm design and two historical cinematic edits. It does not introduce another geometry framework. Shared constructive geometry, body masses, captured dynamics, all 278 cached meshes, reconstructed capture programs, pinned requirements and bundled MuJoCo runtime are byte-identical between the two source packages.

## Latest restored short cut

- Original `source/native_film.py` maps to `source/native_film_v2.py`, byte-for-byte. It implements the revised lighting/materials and staged inspection offsets.
- Original `source/render_delivery.py` maps to `source/render_delivery_v2.py`. Only entrypoint/import names and output locations were changed: frames go to `frames-v2/`, clips to `clips-v2/`, reports to `reports/v2/`, and the movie to the repository root rather than its parent. Its renderer-hash lookup follows the renamed renderer.
- Original `source/complete_pending.py` maps to `source/complete_pending_v2.py`, with matching entrypoint/output-directory substitutions only.
- Three original v2 reports are preserved under `reports/v2/`. Their hashes and claims describe the supplied render, not a run performed for publication.
- The original package README is retained beside this file. Its unversioned command names refer to the original package layout; use the versioned commands in the root README here.
- The standalone renderer download matched the archive renderer byte-for-byte.

The unversioned `source/native_film.py` and six-shot finalizer remain the v1 28-second pipeline. The v2 renderer still contains the old six-shot convenience CLI, so use `complete_pending_v2.py` or `render_delivery_v2.py` for the actual 15-second delivery. Do not use its direct main entrypoint to reproduce the short cut.

## Preserved media

`media/ARX6-P5-Cinematic-v1.mp4` is the original 28-second, 672-frame movie. `media/ARX6-P5-Cinematic-v2.mp4` is the later 15-second, 360-frame restored short cut. The latter's own provenance says it was freshly rebuilt from retained source and recorded edits, not recovery of original encoded v2 bytes. Publication review did not render either movie.

Both videos use the same reconstructed ten-second MuJoCo capture. V2 includes only its first four seconds; the component inspection and reassembly segments are heuristic display offsets, not a physical teardown simulation. No full electromechanical validation, new joint limits, new actuator models, manufacturing tolerances or hardware tests were added in v2.
