# Review of TAA and temporal upscaler inputs — 2026-10-01

_Translated from Russian; original: [ru/TEMPORAL_REVIEW_2026-10-01.md](ru/TEMPORAL_REVIEW_2026-10-01.md)._

## Project status

bbport is a specialized Linux runtime for the original x86-64 code of Bloodborne
CUSA03173 1.09, translating GPU commands to Vulkan based on shadPS4. It is an experimental
port: the loader, HLE of system calls, audio, input, saves, the in-game settings UI
and temporal upscaling are already implemented. This working copy contains the sources, a built
library, a game dump and a save. There is no project Git metadata, so the change history
and the cleanliness of the working tree cannot be verified.

A full playthrough, portability to other drivers and the Steam Deck are not confirmed by this
review. The documentation still lists limitations: synthetic occlusion queries,
incomplete predication, transparent effects without their own motion vectors, and races
in the FSR 4.1.1 model for some non-standard output sizes.

## Video and causes

The source recording `video_2026-10-01_21-21-02.mp4`: 94.89 s, 2560×1080, 60 FPS.
It switches between TAA, FSR 4.1.1, FSR 4 and FSR 3.1. Temporal instability is visible on architecture, thin outlines
and the moving weapon. The in-game motion blur is enabled in the menu;
its contribution must not be attributed to TAA. The file `video_fixed_taa.mp4` has the same duration
but a different frame size (2560×1082); this recording by itself does not confirm a renderer fix.
Frames and sequences for viewing are in `out/dev/temporal-review/`.

Bugs were found in the code, independently of any subjective assessment of the video:

1. **FP16 depth in TAA history.** The half-float step near 1 is approximately 0.000488.
   With near ≈ 0.05, distant surfaces become indistinguishable. The history validation threshold
   was smaller than this step, so history could be both wrongly rejected and blended
   with a different surface. History is now RGBA32F.
2. **Incomparable cameras.** The old check compared the previous frame's depth with the current
   frame's depth. Now the current point is transformed into the previous camera's space, and the comparison
   is made against the expected depth there. The tolerance scales with perspective depth.
3. **Zeroing of distant vectors.** `depth >= 0.99999` was treated as sky and got zero
   motion. For a projection with near ≈ 0.05, far 3000 this threshold affects geometry from roughly
   1875 units onward. Now only clear depth 1 is treated as the infinite background; the background gets
   the camera's rotational motion without translation. Distant geometry gets normal reprojection.
4. **FP16 depth in object motion.** RGBA16F lost the depth used to check whether
   a vector is occluded by a later draw. The buffer and the graphics pipeline format are now
   RGBA32F; the depth check no longer accepts a different distant surface with a wide
   fixed tolerance. The final vectors for FSR are still RG16F.
5. **Mixed-depth check at edges.** TAA interpolated history depth across
   different surfaces. Now the four bilinear taps are checked independently, color is gathered
   only from consistent taps; with partial coverage the history weight is reduced.
6. **Accumulation too weak in the distance.** The previous depth-adaptive weight reduction to 0.8/0.5
   was replaced with a weight of 0.98…0.85 depending on motion when history is valid (the lower
   weight is reached at 8 px/frame). A diagnostic run with a weight of 0.94 showed
   residual color oscillation between jitter phases even with accepted history. History RGB
   is clamped to the range of the current frame's neighbors.
7. **Depth jitter on slopes and thin details.** Depth is now shifted to the
   stable pixel position using a local one-sided gradient, with protection against
   surface discontinuities. For motion/depth the nearest surface in a 3×3 neighborhood is selected;
   color and the clipping range are taken around the original color pixel. This lets
   thin outlines keep their history when foreground/background alternate under jitter.
8. **Unstable history addressing at near-zero motion — the main cause of the
   observed TAA jitter/shimmer.** Previously the integer and fractional parts of the bilinear coordinate
   were computed after adding a large pixel index to a very small motion.
   On the GPU this produced inconsistent parts and selection of a neighboring texel. Now the
   motion itself is split first: `base = p + ivec2(floor(motion))`,
   `fraction = motion - floor(motion)`. A regression check at pixel x=2010
   with motion of about −0.00003 px reproduces the bug of the old formula:
   color 0.250000 instead of the expected 0.739985. The fixed formula passes the check.

Fixes 3–4 apply to the shared inputs of TAA/FSR 3.1/FSR 4/FSR 4.1.1. AMD's algorithms and
ML assets were not modified. The shader/pipeline ABI check and the diagnostic object
motion dump were updated together with the resource format.

## Checks and limitations

Built `bbgpu`, `taa-shader-test`, `camera-motion-test` via `shell.nix`.
On a Vulkan GPU, 18 cases of the production TAA shader passed: reset with NaN, unjitter, accumulation,
clipping, surface disocclusion, off-screen, NaN history, exact far depth,
rejection of a different far surface, camera translation, edge with partially valid history,
sky and the sky/geometry boundary, sloped depth with both jitter signs, thin outline,
reduced persistence under motion, and very small negative motion at a large coordinate.
6 checks of the production camera-motion shader passed:
distant geometry, sky rotation, no sky translation, jitter exclusion,
valid and stale object vector. Log: `out/dev/temporal-review/tests.log`.
Additional unjitter check: `out/dev/temporal-review/taa-final-tests.log`.
Reproduction of the old formula's regression and 18 successful checks of the new one:
`out/dev/temporal-review/regression-proof.log`.
Final in-game check: `out/dev/temporal-review/subpixel-validation.log`.
All 64 existing Python tests passed (`out/dev/temporal-review/python-tests.log`).

Live smoke test: a copy of the save was loaded in the Hunter's Dream. In a single process,
TAA → Off → FSR 3.1 → FSR 4 v07 → FSR 4.1.1 → TAA were checked, at 2560×1440 output,
six final frames per mode, with camera movement between switches.
FSR runs with a 1706×960 input; TAA with native 2560×1440. The AMD contexts were
confirmed by the log; there was no fallback to FSR 3.1. The process exited normally;
after pipeline compilation it held the 60 FPS cap. Logs and raw frames:
`out/dev/temporal-review/subpixel-validation.log`, `out/dev/temporal-review/far-refined/`.
In-game motion blur and AA are disabled in the test configuration.

With a static camera on the distant tower region (x=2010…2099, y=400…779),
the mean absolute RGB change across six TAA frames dropped from 1.892 to
0.299 on a 0…255 scale, roughly 6.3×. After switching back to TAA — 0.279.
In the final run, FSR 3.1: 0.328, FSR 4: 0.278, FSR 4.1.1: 0.364.
This is a result for the chosen scene, not a universal quality score: the FSR input resolution
differs from TAA, and the before/after here compares specifically the last fix to
history addressing. Data: `out/dev/temporal-review/far-refined/stability.json`;
previous run: `out/dev/temporal-review/final-validation.log`.

For diagnostics, `BB_TAA_DIAGNOSTICS=1` was added: the alpha of the TAA output contains the weight of the accepted
history instead of 1. It can be read in the `BB_DUMP_TRIGGER` raw RGBA16F dump. RGB is unchanged,
and the history alpha still contains depth. Normal mode keeps the output opaque.
Additional modes 2 and 3 output the current color or the clamped history;
the diagnostic history image allows comparing a direct read with reprojection.
These comparisons revealed the addressing bug even with accepted history and near-zero motion.

The sources and `out/gpu/libbbgpu.so` have been updated. Rebuilt
`dist/Bloodborne-bbport-x86_64.AppImage` (832 MiB); the packaged `--vulkan-info`
successfully detected the RX 7800 XT via RADV. Logs: `appimage-build.log` and
`appimage-vulkan.log` in `out/dev/temporal-review/`. The full in-game run above
was performed with the local library; a separate full in-game run of the AppImage was not performed.

These tests confirm the specific fixes but do not prove that all
flickering in the game is gone. Object motion from vertex history, transparency, animated
materials, LOD selection and sub-pixel geometry under heavy resolution reduction
still need to be checked in dedicated scenes.

The cost of full precision: the two TAA histories take 253 MiB instead of 127 MiB at 4K;
object motion — 127 MiB instead of 63 MiB at 4K render. This also increases memory
bandwidth usage. A possible next optimization is a separate R32F depth
while keeping color and motion in FP16, with the same correctness tests.

For regressions:

```sh
nix-shell shell.nix --run 'ninja -C out/gpu taa-shader-test camera-motion-test && out/gpu/taa-shader-test && out/gpu/camera-motion-test'
```

The approach of providing motion for all input pixels is consistent with the recommendations in
[AMD FSR 3.1 integration](https://gpuopen.com/presentations/2024/FidelityFX_Super_Resolution_3-1_Release-Overview_and_Integration.pdf).
