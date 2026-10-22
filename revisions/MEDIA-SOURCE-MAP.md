# Reference media to actual generating sources

The references belong to different stages and must not be treated as one latest validated configuration.

## Exact film identity

Both supplied MP4 copies exactly match the existing `media/ARX6-P5-Pathtraced-Action-1080p.mp4`: 3,585,174 bytes, SHA-256 `c298178f407f1c47591dc6749d0ae6e10b4e65c10b9e972a92762577acd11a22`. Independent inspection confirms 1920×1080, 24 fps, 12 seconds and 288 frames. See [FILM-TO-CODE.md](FILM-TO-CODE.md) for actual modules, hidden parts and controller limits. No duplicate film was added.

## Refined metal close-up

The 2048×1152 reference strongly content-matches `p5-refined/renders/ARX6-P5-Refined-closeup-4K.png`, a 3840×2160 master. It is a resampled copy, not byte-identical. Independent resizing comparisons give about 0.048 mean absolute 8-bit channel difference with Pillow's Hamming filter; no exact original resizing algorithm is claimed.

The master SHA-256 `865d1a308444b5535f02c3747c32b7d09805c3ac528e913d7f1c35ed8a287c4f` matches `p5-refined/reports/proof-render-verification.json`. That report identifies actual `source/pathtrace.cpp` hash `3242ecb2f0e4735b02afe4209bdd0cd8bc471e444a794d87200eb72d328dc10f` and refined geometry hash `0cd8b69794c1dfd5c45a0ee7bda40bde0ec71e95013cc1f221dc8308218bb71d`. Real CAD/refinement, exporter, camera, renderer and denoiser sources are preserved. The historical report is not a newly rerun render.

## P6-A PETG hero

The other 2048×1152 reference strongly content-matches `p6-a-petg/ARX6-P6-PETG-hero-4K.png`, master SHA-256 `c36d152e555ab30232d2e4666116162a209a3140d13aca91be21410c437175c1`. It is also a resampled image, not a byte match, with about 0.048 mean channel difference under the same comparison. It depicts the earlier metal-core/ten-transparent-cover configuration, not P6-B prototypes.

The authentic P6-A dossier/STEP/verification remain available, but the implementation ZIP does not. Its builders, revised controller, FEM/thermal code, native exporter and dielectric renderer are not embedded in the images or review HTML. P6-B's property inventory does not restore those algorithms. No STEP-only or screenshot-derived substitute is presented as complete source.

## P6-B is a newer source checkpoint, not a new film

The 21:55 UTC delivery contains actual builders for six test articles and the complete audit inputs. It has no new full-arm proof or motion film. Keep its real implementation and its limitations separate from these older media.
