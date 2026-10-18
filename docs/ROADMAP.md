# Roadmap

Revised 2026-10-16 for **Uncharted: The Nathan Drake Collection**, after 0.3.3. It replaces the
Bloodborne-era plan, which is kept, translated, in
[history/BLOODBORNE_ROADMAP_2026-09-30.md](history/BLOODBORNE_ROADMAP_2026-09-30.md) (Russian
original: [ru/ROADMAP.md](ru/ROADMAP.md)). The research behind each item is in
[`Research/`](../Research/README.md) and is linked where it applies.

## Goals

1. **Play all three games start to finish on Windows 10/11** from the user's own PS4 dump. No
   game data, keys or official art is ever shipped.
2. **Run well on common hardware**: 6 GB GPUs at 60 FPS, 4 GB GPUs without crashing, and
   higher frame rates, upscaling and frame generation where the hardware allows.
3. **Stay maintainable**: an English codebase and docs, CI on every change, game-specific data
   in one place, and a clear way to take fixes from the sibling Bloodborne port and from shadPS4.
4. **Distribute cleanly**: licence-complete release packages and a verified updater.
5. **Later: Linux and the Steam Deck** for Uncharted. The engine code already runs on Linux for
   Bloodborne.

## Where things stand

The port boots all three games, with saves, controller plus keyboard and mouse, TAA, FSR 3.1,
FSR 4 and DLSS, and FSR 3 or DLSS frame generation
([README](../README.md#features)). Upstream got about 150 issues in its first day; most are
crashes in a handful of groups
([similar-projects](../Research/similar-projects.md#upstream-uncharted_pc)).

### Done on this branch (2026-10-16)

- [x] All Russian documentation translated to English; originals kept in [`docs/ru/`](ru/).
- [x] In-game settings menu (Insert / L3+R3) in English. Its Bloodborne-only switches (model
      detail, effects, cheats) are hidden unless a patch image was applied (`BB_GAME_PATCHES`).
- [x] The Linux build works again: Win32-only code in the scheduler, missing includes, and
      miniupnpc and xbyak handled only on Windows in CMake. `shell.nix` now lists the online
      code's dependencies.
- [x] Tests fixed and all running: 82 Python tests (none skipped), the five C test programs and
      the seven C++ GPU tests, on lavapipe. `test_probe.py` also finds `bb-probe.exe` on Windows.
- [x] CI ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)): the Linux build and every
      test ([`tools/ci_linux.sh`](../tools/ci_linux.sh)), plus a Windows MSYS2 CLANG64 build.
      Both are green.
- [x] The Windows build works with today's MSYS2 again. Current clang and libc++ no longer
      include standard headers transitively, which broke FidelityFX, sirit and shadPS4
      (`gpu/shim/libcxx_compat.h`). A new warning also hit a dead variable in
      `runtime_services.c`.
- [x] Programs linked with the GPU library no longer abort at start on a Linux account
      without `~/.local/share`.
- [x] **Ported 2026-10-18** ([details](../Research/porting-candidates.md#status-2026-10-18)):
  - 35 commits from SuperMedo's Bloodborne port (1.7 to 1.9.1), covering:
    - VRAM exhaustion: allocating past the budget, a system-memory fallback for guest memory,
      a VRAM reserve, and a texture collector that evicts again;
    - device lost on pre-RDNA3 AMD cards;
    - SRT walker and scheduler crashes;
    - frame limiter pacing;
    - retrying device creation without DLSS when that fails;
    - atomic save writes;
    - a clear message on CPUs without AVX/BMI1/MOVBE/LZCNT;
    - red-zone trampolines (the mechanism; Uncharted's site list still needs the game files).
  - shadPS4's GCN NaN fix (PR #5257), the likely cause of the U3 green/black flashes. It needs
    checking in game, on Sully's shirt in Cartagena.
- [x] The last "Bloodborne" default names removed from the loader and GPU library.
- [x] [`Research/`](../Research/README.md): architecture, the game and engine, graphics,
      similar projects, licensing, porting worklist.

## Decisions for the maintainer

All five were decided on 2026-10-18 and are done on this branch:

1. **Port fixes from SuperMedo's Bloodborne port and shadPS4:** yes. See
   [porting-candidates.md](../Research/porting-candidates.md#status-2026-10-18).
2. **Update source:** this fork. The launcher checks `iannitram/uncharted_pc` releases and
   installs only a package whose SHA-256 matches the digest GitHub publishes
   (`launcher/update_check.py`). Releases therefore have to be published on this fork.
3. **DLSS and FSR 4:** both stay in the package. The zip now carries a complete `licenses`
   folder: every MSYS2 library and source component, the Python runtime, `SOURCE.txt` with the
   commit and versions, and a notice that NVIDIA's files are not GPL. The launcher credits NVIDIA
   and AMD.
4. **Name and font:** the product is "NDC Native" (`NDC Native.exe`, `Play NDC Native.exe`,
   `ndc-native-windows.zip`), described as a port for *Uncharted: The Nathan Drake Collection*.
   The launcher uses Segoe UI; the Cinzel font is gone.
5. **Bloodborne code:** deleted, and git history keeps it. That covers:
   - the Bloodborne launchers and their translations;
   - the community patches with `patches.py`, and `mods.py`;
   - `run.sh` and the AppImage/Nix packaging;
   - the effects and cheats in the in-game menu;
   - the shadNet online/PSN code (about 2 MB) and its protobuf, OpenSSL and miniupnpc
     dependencies.

   The red-zone tables are now per executable (`patches/redzone/<exe>.json`, none yet for
   Uncharted).

## 1. Stability: the crash groups

The order is by how many reports each group has and how good the lead is. Every item ends with a
log line or a test that shows it fixed.

| Problem | Lead | Next step |
|---|---|---|
| **Out of video memory on 2–4 GB cards** | Allocations made "within budget" end the process on failure, and the budget is read once. The games bind `0xffffffff`-sized buffers, about 2.7 GiB once clamped ([graphics](../Research/graphics-upscaling-and-performance.md#vram-pressure-on-4-gb-gpus), [technical](../Research/uncharted-collection-technical.md#known-problems-mapped-to-research)). The Bloodborne port has fixes: `44e7644` (allocate past the budget) and `96502c8` (fall back to system memory) | **Ported** with `5dc1f11` (VRAM log), `acfe3a8` (VMA uses `VK_EXT_memory_budget`) and `5f65e2d` (VRAM reserve). Still to do: evict and retry instead of asserting, and bound the huge descriptors. Add an automatic 4 GB profile: no frame generation, no FSR 4, smaller history buffers |
| **`m_gfxEopTick` assertion** (still reported on 0.3.3) | Naughty Dog's three-frame pipeline checks that the GPU finished a frame before reusing its slot ([technical](../Research/uncharted-collection-technical.md#frame-centric-pipelining-and-frameparams)). shadPS4 found a flip that is signalled before its end-of-pipe packet (PR #4882, #5140). The Bloodborne port's `76f5b5f` is in the same area | Check the flip/EOP order in `gnmdriver`/`videoout`. Log how often and how long the 0.3.2 wait spins, which tells shader-compile lag apart from a steady ordering bug |
| **Guest fault at `0xd9c59b`** (U2/U3 openings, U3 London bar) and the **U2 `iSubMesh` streaming assertion**, both on US 1.02 | Windows writes exception frames over the System V red zone, which corrupts guest leaf-function locals on page-protection faults. This is confirmed for this collection in shadPS4 (#5038, PR #4802). The Bloodborne port's `bc893e2` has trampolines for it ([porting](../Research/porting-candidates.md#mechanisms-that-need-data-for-uncharted)) | Symbolize `0xd9c59b`: is it a frameless leaf function? The trampoline mechanism is **ported**; generate red-zone sites for the three executables with `tools/redzone_sites.py`. Reproduce on 1.00 and on a non-US 1.02 |
| **Steam Deck `vk_scheduler` assertions, device lost** | `acdfdf0` (record chunk never null), `3a7cde8` (stable texture slots), `3d43d8f` and `4f30202` (object motion on pre-RDNA3 AMD) | **Ported**; needs confirming on a Steam Deck |
| **Intel iGPU crashes** | The HD 630 black screen is fixed in 0.3.3, but the HD 520 crashes inside Intel's driver ([graphics](../Research/graphics-upscaling-and-performance.md#intel-gen9-igpu-vulkan-driver-issues)) | Separate driver crashes from guest crashes in the log. Use conservative defaults on Gen9: no frame generation, no FSR 4 |
| **Old CPUs: `0xC000001D`** (upstream #144) | The game needs AVX, BMI1, MOVBE and LZCNT. The Bloodborne port's `1dd8471` checks this at start, and `e750af8` translates the instructions | **Check ported.** Translation needs a plan for each Uncharted executable |
| **DLSS driver failure stops the game** (upstream #148) | `3e3b760`: create the device again without DLSS's extensions | **Ported** |
| **Saves corrupted by a crash mid-write** | `f7ea858`: write to a copy, then rename | **Ported** |

Also for stability:

- [ ] **A crash triage table**: assert strings and guest offsets mapped to issues and versions,
      fed by `last_run.log`. Log the GPU and driver in every log (`c07f0ff`). Add a log
      sanitizer that strips personal paths, as the God of War III port does
      ([similar-projects](../Research/similar-projects.md#other-native-ps4-game-ports)).
- [ ] **A freeze reporter** that dumps guest thread stacks after 10 s without a frame
      (`tools/watch_freeze.py` is a start).
- [ ] **Version coverage.** Target 1.02 and keep fixes signature-based, not fixed-address.
      Patch databases only know 01.00 and 01.02, at different offsets
      ([technical](../Research/uncharted-collection-technical.md#which-version-to-target)).

## 2. Graphics correctness and performance

- [ ] **U3 one-frame green/black flashes.** shadPS4 PR #5257 fixes the NaN semantics of
      `V_CMP_N*`, `MIN3/MAX3/MED3` and saturate
      ([graphics](../Research/graphics-upscaling-and-performance.md#shader-translation-flicker-and-nan-bugs)).
      **Ported 2026-10-18**, and the shader cache version is bumped. Next, check Sully's shirt in
      Cartagena. If the flashes remain, capture the flash frame in RenderDoc and compare the cloth
      vertex buffers with the previous frame
      ([technical](../Research/uncharted-collection-technical.md#known-problems-mapped-to-research)).
- [ ] **First-run shader hitches.** Save the driver `VkPipelineCache` too, and prewarm from a
      recorded list of pipeline keys. Avoid async compilation that skips draws
      ([graphics](../Research/graphics-upscaling-and-performance.md#shader-compilation-stutter-in-translation-layers)).
- [ ] **Frame generation pacing.** Mailbox can drop generated frames, so use FIFO with VRR
      (or Immediate) when frame generation is on. Add Reflex (`VK_NV_low_latency2`) and
      Anti-Lag 2 (`VK_AMD_anti_lag`). DLSS frame generation on Vulkan needs Reflex
      ([graphics](../Research/graphics-upscaling-and-performance.md#frame-pacing-presentation-modes-and-latency-reduction)).
- [ ] **Above 120 FPS.** Cloth, animation constants and mouse scaling were tuned for 60 Hz
      ([technical](../Research/uncharted-collection-technical.md#frame-rate-dependent-logic-and-community-patches)).
      Prefer frame generation over a higher game rate. Watch for the mouse-sensitivity frame-rate
      bug that Legacy of Thieves had
      ([technical](../Research/uncharted-collection-technical.md#lessons-from-the-official-pc-ports)).
- [ ] **Upscalers.** AMD has no official FSR 4 on Vulkan; this port's 4.1.1 replay is the only
      native Vulkan version found. Keep its assets user-generated. XeSS exists for Vulkan only
      as upscaling, under a binary licence; XeFG and XeLL are DX12-only
      ([graphics](../Research/graphics-upscaling-and-performance.md#amd-fsr-31-fsr-4-and-redstone-on-vulkan)).

## 3. Distribution and compliance

Ordered by value for effort; details in
[legal → Recommended actions](../Research/legal-licensing-distribution.md#recommended-actions).

- [x] **A complete `licenses/` folder** in the zip, generated by `package.sh`, and **`SOURCE.txt`**
      with the commit, submodules and MSYS2 package versions (decision 3). Check the first real
      package for missing licences: `package.sh` reports any it could not find.
- [x] **DLSS and FSR 4 bundled with notices**: what is not GPL, NVIDIA and AMD credit in the
      launcher (decision 3).
- [x] **A verified updater**: this fork's releases, an exact asset name, and the SHA-256 that
      GitHub publishes for the asset (decision 2).
- [ ] **Signed releases**: minisign or Authenticode on top of the checksum, and immutable
      releases.
- [ ] **Release automation**: one `VERSION` file, and a tag-driven packaging job that uploads
      the zip and its checksums.
- [ ] **Community rules**: no piracy help in issues or Discord, no dump guides, no donations or
      early access. These were the factors that hurt Yuzu
      ([legal](../Research/legal-licensing-distribution.md#nintendo-v-yuzu-and-ryujinx-2024)).

## 4. Codebase health

From [architecture → Improvement candidates](../Research/codebase-architecture.md#improvement-candidates).

- [ ] **Tests for the path that ships**: `run.py` (executable mapping, prepare caching, the
      LoadExec loop between U1, U2 and U3, the restart command), `link_modules.py` and the
      launcher's environment. Run the native tests on Windows in CI too.
- [ ] **One game profile per title and version**: the shader hashes in `run.py`, the guest
      callback offsets in `runtime_pad.c`, the EOP patch, and the UI composition hashes. Log
      which entries matched.
- [ ] **A registry of environment variables.** There are about 200 `BB_*` variables. Generate
      `docs/ENVIRONMENT.md` from one table, and add a test that fails on unregistered names.
- [x] **Bloodborne code and the online stack removed** (decision 5).
- [ ] **Leftover start-up-patch paths.** `BB_RENDER_RES`, live resolution and the patch image
      (`--patches`) only served Bloodborne's `run.sh`. Remove them, or wire them to `run.py`.
- [ ] **Repeatable upstream sync**: complete `gpu/VENDOR.txt`, add a `tools/upstream_diff.sh`, and
      keep a log of every cherry-pick (porting worklist:
      [porting-candidates.md](../Research/porting-candidates.md)).
- [ ] **Docs**: rewrite `packaging/windows/README.md` for Uncharted, and move the Bloodborne
      logs into `docs/history/`.

## 5. Linux and Steam Deck for Uncharted

The engine builds and its tests pass on Linux (see above), but the Uncharted path is
Windows-only ([architecture](../Research/codebase-architecture.md#linux-status-for-uncharted)):

- [ ] `run.py` without `ctypes.windll`; executable switching (LoadExec, exit code 101) in the
      Linux runner.
- [ ] Loader gaps: thunk memory near the image, so `install_game_callbacks` (mouse camera, the U2
      NaN patch) also runs on Linux; `runtime_restart` through `BB_RESTART_COMMAND`.
- [ ] An Uncharted AppImage and a portable Tk launcher.

## Out of scope

- Shipping game files, keys, decryption, or official artwork.
- Patches or features for other games in this repository. The Bloodborne port lives in its own
  repositories.
