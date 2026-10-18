# Motion vectors: follow-up after the 2026-09-26 video

_Translated from Russian; original: [ru/motion_vectors.md](ru/motion_vectors.md)._

Source material: `video_2026-09-26_04-19-53.mp4`, FSR 3.1 Performance,
render 960×540 → output 1920×1080, and `out/dev/t71.log`.
This describes the current working-tree changes, not a confirmation of in-game quality.

A shared pass for all G-buffer draws turned out to be too expensive: Performance ran at about
49 FPS with it and 77–78 FPS without it. Object vectors are now enabled by default only
for shaders with a pose/bone buffer (640–16384 bytes, excluding the shared scene buffer of
864 bytes; 16-byte stride). In a trial run with a narrower 1024-byte threshold
this reduced the number of processed draws to about 140 per frame, eliminated history
overflow and gave about 81–87 FPS. The remaining draws keep the cheap camera vectors.
`BB_OBJECT_MOTION=0` disables the whole feature, `BB_OBJECT_MOTION_ALL=1` restores the shared
pass for A/B. The auxiliary target's alpha channel stores depth: if a later regular
draw covered the object, its vector is not used. The quality of the character and weapon in motion
after this selection still needs to be checked visually.

## Findings

- At the end of the source log, over 600 frames: 257400 G-buffer draws, 256200 declared
  as moving, only 30000 received previous positions (~11.7% of all draws).
  This is draw coverage, not a percentage of pixels. The old counter did not distinguish
  the reason for each miss.
- History reserved the size of the entire vertex buffer multiplied by the instance count
  **including firstInstance**. For submeshes of shared buffers these are excess
  positions; the budget was 2097152 positions per frame.
- History had no separate barrier between vertex shader writes/reads;
  reusing the host-parameter ring did not wait for the GPU.
- Disabled writes of all vertices were directed to a single scratch element.
- `CameraMotion::OnDisplayPass` reset Depth() before computing the jitter phases:
  Performance got 8 phases instead of 32. Reconstructing position from depth
  also did not account for the viewport offset.

## Changes

- The history range is determined by the min/max of the actual indices, accounting for baseVertex
  and primitive restart. FirstInstance is subtracted in the shader instead of consuming memory.
- All eligible direct G-buffer draws are saved, starting from their first appearance.
  The constant-change heuristic was removed: it considered almost all draws moving
  and missed the start of motion. Reading is only possible on a match with the previous frame.
- The key includes all vertex stream descriptions, the shader, the address and content hash of the
  indices, the vertex range, instances and the ordinal among identical draws.
  A topology change or a skipped frame resets the corresponding history.
- Budget is 4194304 positions/frame; the two arrays together take 128 MiB instead of 64 MiB.
  When memory runs out, camera vectors remain. The log separately shows saves,
  matches, missing history, out-of-memory and invalid ranges.
- Added vertex-to-vertex barriers, a GPU wait before reusing
  host parameters, coherent host memory and independent tracking of the motion image layout.
  Re-reading the image does not clear the flag that vectors are present.
- Disabled accesses are bypassed by branching. For repeated invocations of the same
  indexed vertex, atomic writes of the position components are used.
  Positions behind the camera and NaN/infinite vectors are not used.
- Performance gets 32 jitter phases after the FSR context is created. Camera vectors
  are reconstructed from unjittered coordinates; object vectors were already obtained
  from clip positions before the viewport offset.

## Checks

Build and CPU tests:

```bash
cd native_probe
nix-shell shell.nix --run 'bash build.sh && ninja -C out/gpu motion-history-test motion-shader-test && out/gpu/motion-history-test && out/gpu/motion-shader-test out/motion-shaders'
```

`test_motion_history.cpp` checks u16/u32 ranges, restart, negative baseVertex,
firstInstance, repeated draws, topology changes, a skipped frame, budget exhaustion,
overflow and the phase count. A run with AddressSanitizer/UBSan also passed.

`test_motion_shaders.cpp` uses the real SPIR-V backend and creates VS/PS with
and without vectors. All four results passed `spirv-val --target-env vulkan1.3`.
Reproducing this requires `spirv-val` from SPIRV-Tools:

```bash
for shader in out/motion-shaders/*.spv; do
    spirv-val --target-env vulkan1.3 "$shader" || exit
done
```

Build/test logs: `out/dev/motion-validation.log`. The verification environment has no access
to `/dev/dri`: quality on the RX 7800 XT, FPS and coverage percentage after the changes
have not been checked yet. Successful SPIR-V validation does not prove the image is correct.

## Next in-game run

From `game_files`:

```bash
BB_FRAME_STATS=1 BB_TOGGLE_FILE=out/dev/motion-toggles bash native_probe/run.sh 2>&1 | tee native_probe/out/dev/motion-run.log
```

Bit 29 in the temporary toggle file disables only history writes. For a correct
performance comparison, run the game with and without `BB_OBJECT_MOTION=0`:
pipeline selection and the extra target are set at process start.
After toggling, give FSR a few frames to refresh its history.
Compare the same scene: character/weapon while running, camera rotation, combat, still camera.
After ~600 frames check `Object motion:`: `with history`, `capacity skips`, `unmatched`.

Remaining limitations: identical meshes are matched by draw order, which
can change when objects are culled; a change of address of dynamic vertex buffers
loses the match. Indirect draws, tessellation/geometry shaders, MSAA and passes
outside the G-buffer stay on camera vectors. Transparency/particles, blurry UI and moving
scaling to the renderer level are not solved by this change. The cost of scanning
indices and of the atomic writes needs to be measured in a real run.

## September 29: weapons and small skeletons (ghosting of the whirling saw)

Video `video_2026-09-29_23-08-26.mp4`: the character stands still, the saw disc spins and leaves
a trail. A `BB_MOTION_SELECT_LOG=1` log showed the cause: the vertex shader's second buffer is
a bone palette of 48 bytes per bone (3x4), and for weapons/props it is 96–384 bytes (2–8 bones).
The "from 640 bytes" rule did not include such draws, so the disc got only camera vectors,
i.e. it was stationary as far as FSR was concerned.

Changes:

- `Motion::ClassifyBuffer` (`motion_history.h`): 864 — scene, ≥640 — character skeleton,
  96..639 and a multiple of 48 — small skeleton. Pipelines with any skeleton get the variant
  with vectors.
- There are about a thousand small skeletons per frame, most of them static parts of the map.
  So they are gated: the palette hash is compared with the previous frame by a cheap
  key (`History::Moving`) before scanning indices. If it matches, the camera vector is exact
  and nothing is written. If it changed, positions are saved and from the next frame on the object
  vector is used. Hashing with the 416-byte buffer does not work: it changes along with the camera
  for almost everything (verified: history overflow and FPS dropping to ~40).
- Menu: "Show motion vectors (debug)". Red/green — |x|/|y|, blue —
  the pixel received an object vector. `BB_MOTION_SELECT_LOG=1` prints the G-buffer shaders
  with their buffer sizes and the decision.

Measurement `out/motion-gated.log`: ~225 saved draws and ~600 "static" per frame,
no overflow, 58–80 FPS in gameplay scenes. That the trail on the saw is gone
still needs to be confirmed visually.
