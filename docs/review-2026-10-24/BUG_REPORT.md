# Bug report and issue register

Reviewed 2026-10-24 at main snapshot `68c8cf9a6563d653ed17ce72d758aaa5f33a7a76`. P1 = high impact/release gate; P2 = planned work. Measured = synthetic local reproduction; read = static review; upstream reports remain unverified here. Fixes are proposed, not implemented.

| ID | Priority | Finding | Evidence | Issue |
|---|---|---|---|---|
| S01 | P1 | Read-only save mounts permit writes | read | [issue](https://github.com/iannitram/uncharted_pc/issues/48) |
| S02 | P2 | Malformed save mount names alias a live slot | measured | [issue](https://github.com/iannitram/uncharted_pc/issues/49) |
| S03 | P2 | Save search lists regular files as save directories | measured | [issue](https://github.com/iannitram/uncharted_pc/issues/50) |
| S04 | P1 | Save deletion returns success when files remain | measured | [issue](https://github.com/iannitram/uncharted_pc/issues/51) |
| S05 | P2 | Concurrent save searches race on global sort settings | read | [issue](https://github.com/iannitram/uncharted_pc/issues/52) |
| S06 | P2 | Save search dereferences unchecked realloc failures | read | [issue](https://github.com/iannitram/uncharted_pc/issues/53) |
| P01 | P1 | Unify Uncharted launch and executable switching across Windows and Linux | read | [issue](https://github.com/iannitram/uncharted_pc/issues/54) |
| P02 | P1 | Gate macOS delivery on host runtime and Apple Silicon feasibility | read | [issue](https://github.com/iannitram/uncharted_pc/issues/55) |
| A01 | P1 | MP3 and AAC AJM instance requests terminate the entire process | read + upstream report | [issue](https://github.com/iannitram/uncharted_pc/issues/56) |
| O01 | P2 | Replace recursive save wildcard matching with bounded matching | read; unbenchmarked | [issue](https://github.com/iannitram/uncharted_pc/issues/57) |
| O02 | P2 | Measure and reduce repeated game preparation in Uncharted runner | read; unbenchmarked | [issue](https://github.com/iannitram/uncharted_pc/issues/58) |
| D01 | P2 | Add reproducible platform CI and release verification | read | [issue](https://github.com/iannitram/uncharted_pc/issues/59) |
| B01 | P1 | GPU build fails with Vulkan-Headers 1.4.365 | measured | [issue](https://github.com/iannitram/uncharted_pc/issues/60) |
| U01 | P1 | Investigate U2 streaming assertion reported upstream | upstream report; not reproduced here | [issue](https://github.com/iannitram/uncharted_pc/issues/61) |
| U02 | P1 | Track U2 chapter 21 progression blocker and physics glitches | upstream report; not reproduced here | [issue](https://github.com/iannitram/uncharted_pc/issues/62) |
| U03 | P1 | Track U3 missing geometry and view-blocking graphics corruption | upstream report; not reproduced here | [issue](https://github.com/iannitram/uncharted_pc/issues/63) |
| U04 | P2 | Investigate U3 video freezes while audio advances | upstream report; not reproduced here | [issue](https://github.com/iannitram/uncharted_pc/issues/64) |
| U05 | P2 | Fix Steam shortcut process association for Windows launcher | upstream report; not reproduced here | [issue](https://github.com/iannitram/uncharted_pc/issues/65) |
| U06 | P2 | Accept validated decrypted ELF inputs or explain required SELF format | read + upstream report | [issue](https://github.com/iannitram/uncharted_pc/issues/66) |

## S01: Read-only save mounts permit writes

Location: src/runtime_savedata.c:153-185; src/runtime_file.c:202-215. Evidence: read.

MODE_RDONLY is printed but never stored or passed to runtime_file_mount. The file layer protects app0/hostapp only, so saves mounted read-only remain writable.

**Proposed fix:** Store access mode on each mount and enforce it for open/truncate/rename/unlink and metadata writes; return the guest read-only error.

**Acceptance:** Mount an existing synthetic save MODE_RDONLY; verify all write APIs fail and hashes stay unchanged while reads succeed.

## S02: Malformed save mount names alias a live slot

Location: src/runtime_savedata.c:196-206. Evidence: measured.

slot_of uses atoi after the prefix: /savedataX resolves to slot 0. Umount clears slot 0 but unmounts the malformed string, leaving the real file mount behind.

**Proposed fix:** Parse bounded, NUL-terminated decimal text; require a canonical exact /savedataN match before changing state.

**Acceptance:** Run reproduce_savedata.c; add malformed, trailing-text, missing-digit and unterminated input cases.

## S03: Save search lists regular files as save directories

Location: src/runtime_savedata.c:303-321. Evidence: measured.

save_search accepts every suitably named directory entry without checking its file type. A stray.txt fixture increases hits from 1 to 2.

**Proposed fix:** Check directory type with stat/fstatat and define a deliberate symlink policy before collecting entries.

**Acceptance:** Run reproduce_savedata.c; include a directory, ordinary file, dangling link and metadata sibling.

## S04: Save deletion returns success when files remain

Location: src/runtime_savedata.c:139-145,253-267. Evidence: measured.

remove_tree discards nftw/removal errors; save_delete unconditionally returns zero. A protected synthetic save retains its child after successful return.

**Proposed fix:** Return and propagate deletion errors, preserve failure details, and serialize deletion against mounts; avoid reporting a removed save until both data and metadata operations have succeeded.

**Acceptance:** Run reproduce_savedata.c as an unprivileged user; add full permission and mounted-save lifecycle cases.

## S05: Concurrent save searches race on global sort settings

Location: src/runtime_savedata.c:294-325. Evidence: read.

sort_key and sort_order are globals read by qsort's comparator without a lock. Concurrent searches overwrite ordering and introduce a C data race.

**Proposed fix:** Make comparator state per invocation using a portable context sort, or serialize setting state and sorting with a dedicated mutex.

**Acceptance:** Run concurrent searches with different keys/directions under ThreadSanitizer and verify each independently.

## S06: Save search dereferences unchecked realloc failures

Location: src/runtime_savedata.c:315-319. Evidence: read.

entries=realloc(...) overwrites the only pointer; allocation failure loses the old allocation and immediately dereferences NULL.

**Proposed fix:** Use a temporary pointer, check allocation and capacity overflow, free the prior buffer and return ERR_INTERNAL on failure.

**Acceptance:** Inject allocation failures at the first and later growth operations; require a guest error and no leaks.

## P01: Unify Uncharted launch and executable switching across Windows and Linux

Location: run.py:25-49,105; run.sh:39-60. Evidence: read.

run.py assumes ctypes.windll and bb-probe.exe; run.sh retains the Bloodborne preparation/patch path, ignores BB_EXE, and has no Uncharted LoadExec loop. Linux output is bb-probe, so the documented Python command in fork discussions does not work on this snapshot.

**Proposed fix:** Introduce a shared platform-neutral runner selecting native filenames, platform-specific wait/console hooks and restart quoting. Route Linux through the same Uncharted per-executable preparation and LoadExec logic; compare with the existing linux branch before duplicating work.

**Acceptance:** Use synthetic subprocess mocks on both platforms to cover U1/U2/U3, restart, exit 101, paths with spaces and user-directory preservation.

## P02: Gate macOS delivery on host runtime and Apple Silicon feasibility

Location: src/probe.c:11; src/runtime_thread.c:18-26,88; src/runtime_memory.c; gpu/CMakeLists.txt:68-70. Evidence: read.

Direct x86-64 guest execution, Linux arch_prctl/GS, memfd and signal context dependencies have no Darwin backend. Apple Silicon additionally needs an execution/translation strategy. MoltenVK alone cannot supply these CPU/runtime requirements.

**Proposed fix:** Add a clear unsupported-platform configure diagnostic now. Produce separate Intel and ARM feasibility spikes for TLS, fixed mappings, exception handling and Vulkan features before promising playable builds.

**Acceptance:** Acceptance: documented go/no-go per architecture plus a synthetic guest thread/TLS/memory/fault smoke test; no macOS playable claim until real hardware validation.

## A01: MP3 and AAC AJM instance requests terminate the entire process

Location: src/runtime_ajm.c:425. Evidence: read + upstream report.

instance_create exits(21) for codec!=1 rather than returning an AJM error. Upstream #588 reports this exact MP3 stop on Linux. ATRAC9 is supported; MP3/AAC are not.

**Proposed fix:** Return an explicit unsupported-codec AJM result immediately; add MP3/AAC decoding through an appropriately licensed decoder with correct gapless, partial input, output format and batch semantics.

**Acceptance:** Request codecs 0/2 using synthetic data: no process exit; later validate decode sample counts and reset/gapless behavior against known fixtures.

## O01: Replace recursive save wildcard matching with bounded matching

Location: src/runtime_savedata.c:289-293. Evidence: read; unbenchmarked.

like recursively tries every suffix for each percent wildcard. Repeated percent/literal patterns can make save enumeration exponential and deeply recursive.

**Proposed fix:** Use an iterative wildcard algorithm or dynamic programming with bounded pattern length and preserved SQL-LIKE percent/underscore semantics.

**Acceptance:** Compare results with simple fixtures and benchmark adversarial patterns of increasing length; establish bounded time and stack use.

## O02: Measure and reduce repeated game preparation in Uncharted runner

Location: run.py:65-74; scripts/content_profile.py; run.sh:54-59. Evidence: read; unbenchmarked.

The Windows preparation cache uses timestamps and repeatedly stats inputs; Linux always prepares/links in the legacy path. There is no shared cache key binding executable identity, module set and preparation version.

**Proposed fix:** After unifying the runner, use an atomic per-game/per-executable manifest keyed by source identity and script/schema version; reuse prepared files only after validation, and invalidate on module additions/removals.

**Acceptance:** Measure cold and warm launch time and metadata I/O; verify changed source, removed module, interrupted build and same-name games never reuse incorrect artifacts.

## D01: Add reproducible platform CI and release verification

Location: build.sh; tests/; packaging/windows/package.sh; missing .github/workflows. Evidence: read.

This snapshot has no GitHub Actions workflow; many tests skip unless native test executables exist. A green Python run alone leaves runtime/GPU behavior untested.

**Proposed fix:** Add Windows CLANG64 and Linux dependency-pinned build/test jobs that compile all required harnesses before discovery, fail on unexpected skips, and smoke-test staged packages. Add macOS feasibility-only checks until supported.

**Acceptance:** CI publishes dependency versions, explicit expected skip list, build/test logs, package manifest, checksums and software-only Vulkan smoke results; hardware playthrough gates remain separate.

## B01: GPU build fails with Vulkan-Headers 1.4.365

Location: gpu/shadps4/video_core/renderer_vulkan/vk_frame_generation.cpp:349. Evidence: measured.

ninja -C out/gpu -j2 bbgpu fails with ambiguous vk::Extent2D assignment using GCC and Vulkan-Headers 365. See build.log. Earlier environment setup also failed with older headers missing eMesaKosmickrisp (historical setup evidence, not today's build).

**Proposed fix:** Use explicit vk::Extent2D{width,height} construction at the failing assignment; specify and test minimum/current Vulkan-Headers versions in CMake and CI.

**Acceptance:** A clean configured Linux build succeeds with documented minimum and current headers; frame-generation extent values remain correct.

## U01: Investigate U2 streaming assertion reported upstream

Location: src/runtime_memory.c; gpu/shadps4/video_core/buffer_cache/; src/probe.c. Evidence: upstream report; not reproduced here.

Open upstream Supermedo/uncharted_pc#479 (also #401/#384/#383) reports iSubMesh < m_numSubMeshInstances. README acknowledges the streaming crash. No causal link to any specific cache bug is proven.

**Proposed fix:** Reproduce at 60 Hz using a legally supplied local dump; bisect memory/cache changes, add bounded resource lifetime and EOP timing diagnostics, then fix the proven ownership or synchronization violation rather than suppressing the assertion.

**Acceptance:** Affected scene and 30-minute streaming soak pass with cold/warm shader caches; compare save/load and regional revisions.

## U02: Track U2 chapter 21 progression blocker and physics glitches

Location: src/probe.c game patches; src/runtime_time.c; src/runtime_pad.c. Evidence: upstream report; not reproduced here.

Open upstream #558/#415/#394 report a truck taking no damage; #448/#590 report ground clipping. These may have different causes and need independent reproductions.

**Proposed fix:** At 60 Hz first, separate projectile/input behavior from timestep and collision problems; bisect game timing patches and restore validated timing for affected revisions. Keep separate failing assertions for truck progression and collision.

**Acceptance:** Replay chapter 21 from a local save and verify truck damage, progression and stable collisions at supported 30/60 Hz.

## U03: Track U3 missing geometry and view-blocking graphics corruption

Location: gpu/shadps4/video_core/texture_cache/; gpu/shadps4/shader_recompiler/. Evidence: upstream report; not reproduced here.

Open upstream #601/#603/#356/#376 report missing objects and corrupt geometry. Existing fork #31/#37 cover specific code defects but are not demonstrated root causes of these reports.

**Proposed fix:** Capture a bounded renderer trace on affected hardware, compare with AA off, validate cache barriers and shader IR, and apply existing cache/recompiler fixes one at a time with visual verification.

**Acceptance:** Affected U3 early chapters render climbable geometry consistently across AMD/NVIDIA; attach diagnostic text and reference observations, not game assets.

## U04: Investigate U3 video freezes while audio advances

Location: gpu/shadps4/core/libraries/videodec/videodec2_impl.cpp; video presentation/scheduler. Evidence: upstream report; not reproduced here.

Open upstream #510 reports frozen video with continuing audio, including recurrence at 60 FPS.

**Proposed fix:** Instrument decode return codes, packet/frame progress and presentation timestamps; test decoder flush/drain and reset paths; fix the demonstrated stall while preserving audio/video synchronization.

**Acceptance:** Multiple affected cutscenes complete at 60 Hz after pause/resume and scene changes; decode errors return explicit guest errors.

## U05: Fix Steam shortcut process association for Windows launcher

Location: launcher/uncharted_launcher.py; packaging/windows/ launcher stub; launcher/bbport_steam.py. Evidence: upstream report; not reproduced here.

Open upstream #362 reports Steam Input selecting desktop bindings when shortcuts target Play Uncharted.exe, while a direct bb-probe.exe shortcut works. Fork #20 is related Linux device routing, not the same Windows launch path.

**Proposed fix:** Generate a prepared direct-game shortcut with validated arguments/environment, or retain correct Steam association through launcher process lifetime; document preparation invalidation after updates.

**Acceptance:** Test Steam Controller and Xbox controller through Game Mode and Desktop Mode shortcuts, with fresh preparation and after an update.

## U06: Accept validated decrypted ELF inputs or explain required SELF format

Location: scripts/prepare.py:26-32; scripts/link_modules.py. Evidence: read + upstream report.

Open upstream #498 supplies the error expected PS4 SELF for already decrypted plain ELF input. parse_self explicitly rejects the ELF magic.

**Proposed fix:** Add a validated ELF64 x86-64 input path sharing all segment/bounds checks with SELF extraction, including module-linking callers; alternatively document the supported dump format clearly without asking users to share binaries.

**Acceptance:** Synthetic plain ELF and equivalent SELF yield consistent images; reject malformed program headers, filesz/memsz overflow, wrong architecture and truncated segments.

## Existing issues: proposed fixes and acceptance

- [#31](https://github.com/iannitram/uncharted_pc/issues/31): Guard copying the old cached image during ExpandImage with validated GPU-data ownership (HasGpuValidData or this fork's equivalent). Preserve freshly refreshed guest data when the old cache is CPU-dirty. Regression: write new guest bytes, expand, and confirm the stale cached pixels cannot overwrite them.
- [#32](https://github.com/iannitram/uncharted_pc/issues/32): Check coroutine handle validity before done()/resume() in both CE and DE waits. Express counter comparisons without unsigned underflow. Validate WAIT_ON_CE_COUNTER before any CE submission and normal paired CE/DE traffic.
- [#33](https://github.com/iannitram/uncharted_pc/issues/33): Reset asc_next_offs_dw[vqid] when successfully mapping/reusing the compute queue, together with its read pointer, under the queue lifecycle synchronization. Validate destroy/remap with a different ring and a nonzero old offset.
- [#34](https://github.com/iannitram/uncharted_pc/issues/34): Advance the backing offset for every backing-bearing VMA kind when splitting, including KIND_FLEX. Make split insertion failure transactional. Validate partial mprotect/unmap and GPU writeback to each page; separately verify live backing pages are never reused.
- [#35](https://github.com/iannitram/uncharted_pc/issues/35): Use a persistent Asio work guard and stop-aware run loop, or consume the pending request count under the same mutex before draining and recheck it before sleeping. Never clear newly posted requests after run(). Regression: post precisely between run/restart/sleep and require bounded completion.
- [#36](https://github.com/iannitram/uncharted_pc/issues/36): Check runtime_file_mount's return value before publishing the save slot/result; roll back slot reservation and return ERR_MOUNT_FULL on exhaustion. Test all free mount slots with startup mounts present and then unmount/remount.
- [#37](https://github.com/iannitram/uncharted_pc/issues/37): Port the upstream opcode operand-count correction and barrier lowering together after verifying this fork's enum/IR semantics. Validate both WBINVL1 opcodes followed by a known instruction and check emitted barrier scopes.
- [#38](https://github.com/iannitram/uncharted_pc/issues/38): Return errors from write_param, fwrite, fflush and fclose. Persist via a same-directory temporary file and atomic replacement so failure leaves previous metadata intact. Also propagate buffered I/O close failures in save_icon and memory_io. Validate /dev/full and protected directories without touching real saves.
- [#39](https://github.com/iannitram/uncharted_pc/issues/39): Provide positioned I/O with a handle/offset strategy that does not mutate the shared sequential file pointer, or serialize every sequential and positioned operation on the same underlying file description. Locking only positioned() is insufficient. Validate interleaved reads/writes and duplicated descriptors on Windows.
- [#41](https://github.com/iannitram/uncharted_pc/issues/41): Optimization follow-up: preserve the existing idle-worker patch decision and validate its lifecycle/synchronization preconditions before integration. Benchmark at 20 W, 30/60 Hz, with idle CPU, package power, frame-time p50/p95/p99 and streaming correctness; upstream #518's performance numbers are reporter measurements, not measurements of this checkout.
- [#16](https://github.com/iannitram/uncharted_pc/issues/16): Optimization follow-up: cache keys must include game revision, translated shader version, GPU/driver identity and relevant feature flags. Warm only validated compatible pipeline/shader entries; expose cancellable progress. Measure cold/warm frame-time p99, cache size and invalidation behavior before claiming reduced stutter.
