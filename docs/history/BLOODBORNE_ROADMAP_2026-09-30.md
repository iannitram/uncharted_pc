_Translated from the Russian original (Bloodborne era, state of 2026-09-26/30). Original: [docs/ru/ROADMAP.md](../ru/ROADMAP.md)._

# Native Bloodborne port: what's done and what's next

The main text reflects the state as of 2026-09-26; the first section below covers what changed by 09-30.
The most detailed snapshot: [CURRENT_STATUS_2026-09-29.md](CURRENT_STATUS_2026-09-29.md).
Report on the work of 09-30 – 10-01 (GPU pipeline, upscaler, crash, launcher, AppImage):
[SESSION_2026-09-30.md](SESSION_2026-09-30.md).
Details on individual topics:
[parallel_gpu.md](../parallel_gpu.md) (GPU multithreading, hitches during streaming),
[upscaler.md](../upscaler.md) (analysis of the game's frame, scene constants).

## Update 09-30

- Done after 09-26: FSR 4 INT8 (v07), object motion vectors, preset switching without a
  restart (reduced-size scene targets; D32S8 depth is copied by a shader), LTO and PGO,
  draw preparation scaling with the thread count (Steam Deck too).
- Issues from the "Known issues" section below: item 3 (restart on preset change) is
  solved; item 1 (object vectors) is implemented, FSR 4 still has ghosting on the character at
  Ultra Performance; item 2 (blurry UI) — the UI is drawn at 1920×1080.
- Limitation: reduced scene rendering (`SceneTargets::Eligible`) requires a 1920×1080 target,
  i.e. it only works with 1080p output.
- Parallelizing the GPU command thread (step 2 of [parallel_gpu.md](../parallel_gpu.md)): textures on
  a separate thread in parallel with buffers work correctly but give no speedup —
  each draw's data migrates between cores. The bottleneck is the GPU command thread: 91% on CPU,
  ~9% waiting for small guest memory copies before a fence. Next steps — a two-stage pipeline
  (the second thread owns the texture cache and draw recording, register copy from scanner deltas)
  or memoizing texture bindings across frames; see "What would scale" in parallel_gpu.md.
- **Two-stage draw pipeline** (`vk_draw_pipe.h`): the GPU command thread decodes PM4 and
  selects the pipeline; a second thread (`bb:DrawRec`) with its own copy of the registers binds resources
  and records the draw. +19% FPS on 16 threads, +18% on 8 (like the Steam Deck). Enabled by default
  with 8+ threads (`BB_DRAW_PIPE=0/1`). The bottleneck is now the second stage; details and plan are
  in parallel_gpu.md.
- Presets and GPU load: the scene is cheap on an RX 7800 XT, so the preset changes GPU time
  by only ~0.5 ms, while FSR 4 itself at 1080p output costs ~1.4 ms (FSR 4 Ultra Performance is more expensive than
  native rendering without an upscaler). Fixed: lighting passes stayed at 1920×1080 under
  any preset (the check looked at other targets' slots); reduced-size targets are now sampled
  directly, without resampling to native (the shader cache is rebuilt once). Next for
  Steam Deck — the guest memory copy of render target `3d5ebf4e` (see parallel_gpu.md).
- **Fixed a crash with the pipeline** (guest heap corruption, guest offset `0x263b8e7`, after
  13–17 minutes): the "GPU idle" interrupt was delivered before the EOP labels deferred to the Vulkan
  recording thread, and the game freed objects carrying those labels. Now the pipeline and deferred
  labels are waited on before it; 2 runs of 30 minutes without crashes (before the fix — 7 crashes out of 7).
- **1440p/2160p output resolution** ("Output resolution" menu, bbport.ini `output_res`, after
  a restart): the scene is rendered at the preset's resolution relative to the output, the upscaler (FSR 3 or FSR 4)
  completes the frame, and the UI is rasterized at the output resolution. Game effects (chromatic aberration,
  DoF, blur, SSAO, the game's anti-aliasing, dynamic shadows, SSR, intro movies, LOD) — same place.
- **Launcher** (`launcher/bb-launcher.sh`, GTK4/libadwaita) and **AppImage** for Steam Deck
  (`bash packaging/appimage.sh` → `dist/`; data in `~/.local/share/bbport`, `--play` —
  launch without the launcher window).
- Tools: `BB_PAD_FILE` (scripted gamepad input), `ab.sh` (A/B of
  `BB_TOGGLE_FILE` bits in a running game), and GPU thread idle time and stalls in `Frame stats`.

## How the port works

- The original eboot (CUSA03173 v01.09) runs directly on x86-64. The PS4 system libraries
  are replaced by our own HLE runtime in C (`runtime_*.c`, `probe.c`).
- Graphics: the shadPS4 video core and shader recompiler (GPL), built into `libbbgpu.so`
  (`gpu/`), with our own modifications. The shadPS4 emulator as a whole is not used.
- Game patches (FPS, resolution, etc.) — community XML (`patches/Bloodborne.xml`),
  compiled by `patches.py` and applied by the loader at startup.

## Done

### Performance and smoothness

| What | Result |
|---|---|
| Vulkan command recording on a separate thread, texture/buffer caches, rwlock instead of a mutex | 26 → 64 FPS in one scene |
| Draw call preparation on 4 threads (`bb:DrawPrep`), validation on the GPU thread | +11.5% |
| 256 KiB unprotect window when the game writes to memory (fewer page faults) | +22% |
| Texture descriptor cache, fast path for the same render targets | up to ~94 FPS outdoors |
| Guest memory copies on a thread pool, staging buffer pool | streaming hitches 60–170 ms → 40–50 ms |
| Waiting for copies before game-visible fences | UI flicker eliminated |
| "Readbacks Relaxed" mode | no "vertex explosions" (FaceGen) |
| 480 Hz vblank + frame limit up to min(monitor, 120), present immediately on flip | even frame pacing; running doesn't slow down above 120 FPS |

Everything can be toggled in-game via `BB_TOGGLE_FILE` (a bitmask) for A/B comparisons.
Statistics: `BB_FRAME_STATS=1`.

### Audio, input

- Audio output at the correct pace (previously there were clicks every 10.7 ms).
- Gamepad via SDL3, fallback keyboard layout.

### Frame analysis

- `BB_CAPTURE_TRIGGER=<file>` captures a single frame: passes, targets, shaders, textures,
  constants, blend modes.
- Reverse-engineered the structure of a Bloodborne frame (G-buffer, lighting, RGBA16F scene color, fog,
  post-processing, tonemapping, the game's anti-aliasing, UI) and the 864-byte scene constants
  (view and projection matrices).

### Temporal upscaler (FSR 3.1)

- **Camera motion vectors**: from scene depth and the current and previous frame's matrices
  (`vk_camera_motion.cpp`, `camera_motion.comp`). Verified by reprojecting the previous
  frame: static geometry matches.
- **Jitter**: subpixel offset of scene geometry via the viewport, Halton(2,3)
  sequence; number of phases 8·(output/render)². The UI and post-processing are not offset.
- **FSR 3.1** (FireBurn/FSR-Vulkan, native Vulkan, submodule `gpu/third_party/fsr-vulkan`):
  - *Native AA*: on the HDR scene color before post-processing, 1:1.
  - *Quality/Balanced/Performance/Ultra Performance presets* (x1.5/1.7/2/3): the game renders at
    reduced resolution (a resolution patch that `patches.py` derives from the community 720p
    patch), and FSR upscales the finished frame to 1920x1080 before the first UI pass.
    The UI and the output pass are redirected to full-size images, and the presenter
    displays them instead of the game's buffer.
- **Reactive mask** (snapshot of the scene before transparent draws, comparison before fog is
  applied): works, but causes shimmering on Bloodborne's haze — disabled by default.
- **In-game menu** (Dear ImGui, Insert or L3+R3): upscaler, preset, sharpness,
  jitter, mask, FPS counter. Settings in `bbport.ini`. Changing the preset — the
  "Apply and restart game" button.

## Known issues

State of the latest commit. The working tree has a pending move of the presets to reduced-size render
targets while keeping guest buffers, post-processing and UI at 1920×1080. Transitions
between presets and color/depth/stencil copies passed a Vulkan test on Lavapipe.
The RX 7800 XT does not support D32S8 blits, so the new path left the FSR input at 1920×1080
and lowered FPS. For such GPUs, startup now automatically picks the proven path with the game's
resolution patch and a 1920×1080 UI; changing the preset requires a restart again. On GPUs with the needed
support, switching without a restart remains. Items 2–3 below refer to the latest
commit, before these working-tree changes.

The general-purpose object motion vector pass was too expensive: Performance gave about
49 FPS with it and 77–78 FPS without it. Now the extra target and shaders are enabled only
for G-buffer draws with a pose/bone buffer; the rest use camera vectors.
In a trial run the selective path held about 81–87 FPS, with no skips due to history
capacity. Object vectors are enabled by default; `BB_OBJECT_MOTION=0` disables them, and
`BB_OBJECT_MOTION_ALL=1` restores the old general-purpose path for comparison. Selection by buffer
size is still heuristic: the quality of weapons and clothing in motion needs in-game verification.

1. **Moving objects "fall apart"** (weapon on the back, character, cloth, enemies): there are
   only camera motion vectors. The third-person camera follows the character, so
   camera vectors are wrong for it, and the upscaler takes history from the wrong place. This applies to
   any temporal upscaler (FSR 3/4, DLSS, XeSS).
2. **The UI is blurry in presets**: with the resolution patch the game thinks it is a 540p game and
   apparently prepares fonts and UI elements for that resolution. Menus
   (title, pause) don't go through the upscaler at all.
3. **Changing the preset requires a restart**: the resolution is set by a code patch at startup, and
   the game allocates its buffers once.

## Plan

### 1. Object motion vectors

Needed by all upscalers and by frame generation. The game doesn't compute them, so we compute them ourselves.

How:
- For each draw into the G-buffer (passes with 5+ targets) the recompiler produces a second variant
  of the vertex shader that outputs the position twice: with the current constants and with the previous
  frame's constants. The difference of the projections is the motion vector, written to an auxiliary
  RG16F target as an extra pixel shader output.
- Previous-frame constants: for each draw, remember the contents of the constant buffers
  (object matrix, skeleton bones) keyed by "shader + draw index in the pass" or by data
  address. Need to find out how the game stores skeleton matrices: in buffers that are overwritten
  every frame (then we copy the previous version) or in a ring buffer (then the previous frame's
  address is enough).
- Where an object isn't found (first frame, new object) — camera vectors, as now.
- Verification: a debug view of the vectors (`BB_DEBUG_MOTION`), reprojecting the previous frame
  with the full vectors, and visually — the saw on the back while running.

### 2. Renderer-level scaling (instead of the resolution patch)

The game runs at 1920x1080 (or at the monitor's resolution), and only the 3D scene passes are drawn at
reduced resolution. The UI and menus stay sharp, and the preset changes on the fly.

How:
- The texture cache allocates a reduced-size copy for scene targets (G-buffer, depth, lighting, scene color, effects);
  guest memory and the game's descriptors don't change.
- Viewport and scissor of passes into these targets are scaled (as already done for the UI,
  including passes with clipping disabled).
- Shaders that compute from pixel coordinates (`gl_FragCoord`, `texelFetch`,
  per-pixel compute shaders) receive a scale factor via the recompiler's push constants.
  Samples with normalized coordinates work unchanged.
- FSR goes in the same place as Native AA: scene color before post-processing (HDR, best
  quality); post-processing and UI run at full resolution.
- Risks: passes that read scene targets by pixel coordinates in post-processing, and
  guest memory reads of these targets (they must be forbidden or scaled back).

### 3. Other upscalers

All use the same inputs (color, depth, motion vectors, jitter, masks).

- **FSR 4 (INT8)**: FSR-Vulkan has an experimental FSR 4 v07 INT8 provider — add it
  as a menu option and compare with FSR 3.1 after step 1.
- **DLSS**: native Linux Vulkan SDK (NGX). Doesn't work on the RX 7800 XT, but is needed for
  NVIDIA users.
- **XeSS / XeFG and OptiScaler**: Intel ships them only as Windows DLLs. Options:
  an in-process Windows DLL (PE) loader, or running the whole build under Proton with
  OptiScaler, feeding it the inputs via the DLSS interface.
  Checked 09-29: libxess.dll (identical in DOOM: The Dark Ages, PRAGMATA, etc.) has a
  Vulkan path (`xessVKCreateContext`, `xessVKExecute`), but imports ~300 functions:
  MSVCP140 (iostream), VCRUNTIME140 (C++ exceptions), UCRT, kernel32, setupapi, dxgi.
  Decided to postpone; the most realistic path is a helper under Wine with shared Vulkan memory.

### 4. Frame generation

- FSR 3.1 Frame Generation (available in FSR-Vulkan): an intermediate frame between two finished ones,
  using the same motion vectors; the UI must be drawn on top separately (UI redirection already
  exists — it can be rendered into a separate layer).
- XeFG — after the Windows DLL question is resolved (see above).
- Requirement: frame delivery through the presenter (the queue and VRR already work).

### 5. Miscellaneous

- Steam Deck: portable build (patchelf, no Nix), testing presets at 1280x800.
- Further offloading of the GPU thread (step 2 of [parallel_gpu.md](../parallel_gpu.md)).
