# Codebase architecture and state of the code

Snapshot of `HEAD` = `68c8cf9` ("0.3.3: Intel fix, video memory note"), 2026-10-16. Line numbers
refer to `HEAD` unless noted. While this was written, the lead had uncommitted edits in
`src/probe.c`, `gpu/shim/bbport_overlay.cpp` and `gpu/shim/bbport_settings.h` (translating the
overlay to English and hiding the Bloodborne effect switches unless patches were applied, via a new
`BB_GAME_PATCHES` variable). Those edits are noted where they matter.

## Key takeaways

- **Architecture in one line.** Python scripts turn a decrypted PS4 SELF and its bundled
  `libc.prx` and `libSceFios2.prx` into one relocatable image, `out/<game>/boot-linked.bin`.
  `bb-probe(.exe)` (`src/probe.c`) maps that image, binds its imports to C "HLE" contracts
  (`src/runtime_*.c`) or to native `libc` exports, patches a few game functions, and jumps into
  the original x86-64 code. Graphics go to a vendored, heavily modified shadPS4 video core
  (`gpu/`), linked as a static library on Windows and as `libbbgpu.so` on Linux.
- **The Uncharted product only runs on Windows.** It uses `launcher/uncharted_launcher.py`
  (Tkinter, frozen to `Uncharted.exe`), then `run.py`, then `bb-probe.exe`. `run.py` calls
  `ctypes.windll` without a platform check (`run.py:38-40`). `run.sh` and the AppImage are still
  the Bloodborne pipeline: they default to `CUSA03173`, apply Bloodborne patches, have no
  executable switching (LoadExec) and no Uncharted shader hashes. The Linux code paths in
  `src/` still exist, but nobody runs them for Uncharted.
- **A lot of Bloodborne code is left.** Roughly 4.6k lines of Bloodborne launchers and language
  files, `patches/Bloodborne.xml` with `scripts/patches.py`/`mods.py`, the AppImage and Nix
  packaging, and about 47k lines of shadNet online/NP code. The online code is compiled and linked
  into the Uncharted build (it pulls in protobuf, OpenSSL and miniupnpc), but only the Bloodborne
  launcher can enable it (`BB_ONLINE`). Until the lead's current edit, the in-game menu was titled
  "Bloodborne — настройки" and showed 20 Bloodborne effect and cheat switches that do nothing in
  Uncharted.
- **The vendored shadPS4 has diverged a lot.** Compared with upstream commit `b4e7ae7`,
  `gpu/shadps4/video_core` has 50 of 145 files modified (about 10k diff lines) and 37 new files
  (about 9.3k lines of upscaler, frame generation, motion and draw pipeline code).
  `shader_recompiler` has 26 modified files. `gpu/VENDOR.txt` lists only 9 cherry-picked upstream
  fixes and does not mention the vendored `network`, `np` or `shadnet` code. Merging upstream
  fixes is a manual job.
- **Configuration is spread over about 200 `BB_*` environment variables.** 178 distinct quoted
  names appear in C/C++, and there are 174 `getenv` call sites. The launcher passes user settings
  to `run.py` and the game as environment variables. There is no list of these variables.
- **Game-specific values are hard-coded in several places.** These include guest code offsets with
  byte signatures (`src/runtime_pad.c:484-491`), a search for an assertion string that rewrites a
  branch (`src/probe.c:630`), shader hashes in `run.py:96-98`, `ui_composition.h` and
  `vk_shader_hle.cpp`, and Bloodborne title IDs and memory addresses in `patches.py`.
- **Tests do not cover the Uncharted path.** The Python suite runs 82 tests and skips 28 when
  binaries are missing. It covers prepare, `link_libc`, patches, mods, `run.sh` and the probe
  limits. Nothing tests `run.py`, `link_modules.py`, the Uncharted launcher or the LoadExec loop.
  `build.sh --test` never runs on Windows because `build.sh:32` exits first. The C++ GPU tests are
  `EXCLUDE_FROM_ALL` CMake targets that no script runs. There is **no CI** (no `.github/`).
- **The project depends on one maintainer and is young.** The repository has 54 commits from
  2026-10-01 to 2026-10-16 (deadinside 28, Supermedo 26). All Uncharted work is Supermedo's and
  arrived as one large commit (`5c457e7`: 121 files, +11,216/−492) plus three point releases.
  Design knowledge is mostly in Russian dated logs in `docs/`, and the roadmap (`docs/ROADMAP.md`)
  is still Bloodborne's.

## Repository map

| Path | What it is | Size (approx.) | Origin |
|---|---|---|---|
| `run.py` | Windows game starter: prepare, link, content profile, start `bb-probe.exe`, LoadExec loop | 159 lines | Uncharted (rewritten from the Bloodborne Windows `run.py`) |
| `run.sh` | Linux game starter: mods, prepare, link, patches, live resolution, build, start | 125 lines | Bloodborne |
| `build.sh`, `msys2-env.sh`, `shell.nix` | Build entry (MSYS2 CLANG64 branch and Linux/Nix branch) | 105 lines | Shared |
| `src/` | Loader (`probe.c`) and C HLE runtime (`runtime_*.c`), Windows compatibility layer | about 8.0k lines of C | Shared, with Uncharted additions |
| `scripts/` | SELF parsing and linking (`prepare`, `link_libc`, `link_modules`, `content_profile`), Bloodborne `patches` and `mods` | about 1.4k lines | Shared, except `patches.py`/`mods.py` (Bloodborne) |
| `gpu/shadps4/` | Vendored shadPS4: `video_core`, `shader_recompiler`, `common`, `core/libraries/{gnmdriver,videoout,kernel,avplayer,videodec,network,np,system}`, `shadnet` | about 152k lines of C++ | shadPS4 `b4e7ae7` plus bbport changes |
| `gpu/shim/` | Glue: `bbgpu.cpp` (C API), overlay, settings, window, parallel copy, write log, shadPS4 `core/` and `common/` stand-ins | about 2.6k lines plus stubs | Shared |
| `gpu/bbnet/`, `gpu/shadps4/shadnet`, `core/libraries/{network,np}` | shadNet co-op (from shadp2p) | about 47k lines | Bloodborne (online play, 1.6) |
| `gpu/dlss_bridge/` | `bbport_dlss.dll`, built with MSVC, the only code that uses the NVIDIA SDK | small | IFreemz, adapted |
| `gpu/third_party/` | Submodules and vendored code: fsr-vulkan (35 MB), imgui, xbyak, sirit, magic_enum, miniz, gcn, half, httplib, wepoll, fonts | 59 MB | Third party |
| `launcher/` | `uncharted_*.py` (Windows Tkinter), `bbport_*.py` (Bloodborne GTK4 and Windows) | 2.5k Uncharted lines, 4.6k Bloodborne lines | Mixed |
| `packaging/windows/` | `package.sh`, `build_dlss.sh`, `play.c` ("Play Uncharted.exe"), `.rc` files, readmes | | Mixed |
| `packaging/{appimage.sh,default.nix,bbport-entry.c}` | Linux AppImage | | Bloodborne |
| `patches/Bloodborne.xml` | GoldHEN/shadPS4 patches for Bloodborne 1.09 (60 entries) | | Bloodborne |
| `tools/` | Diagnostics, game drivers and FSR 4 asset tooling | | Mixed |
| `tests/` | Python `unittest` suites, plus C and C++ test programs | | Mostly Bloodborne or shared |
| `docs/` | Dated development logs and notes, being translated from Russian (`docs/ru/` keeps the originals) | | Mostly Bloodborne |

## Boot flow

### 1. Launcher to `run.py`

`Uncharted.exe` is `launcher/uncharted_launcher.py` frozen by PyInstaller. It has several roles:
`--play` runs without a window, `--run` runs `run.py`, and `--script` runs a preparation script.
`game_environment()` (`uncharted_launcher.py:290`) turns the saved settings into environment
variables, for example:

- `BB_GAME_DIR`, `BB_EXE`, `BB_USER_DIR`, `BB_LANGUAGE`, `BB_USER_NAME`
- `BB_FULLSCREEN`, `BB_PRESENT_MODE`, `BB_VBLANK_HZ`, `BB_WINDOW_SIZE`
- `BB_FSR1`, `BB_RCAS`, `BB_RCAS_ATTENUATION`, `BB_UPSCALER`, `BB_FSR_SHARPNESS`
- `BB_FRAME_GEN`, `BB_FRAME_GEN_MULTIPLIER`, `BB_INPUT_CONFIG`

It then starts `run.py`.

### 2. `run.py` (Windows only)

`run.py` does the following:

- Resolves `BB_EXE` (`u1` is `eboot.bin`, `u2` is `big2-ps4_Shipping.elf`, `u3` is
  `big3-ps4_Shipping.elf`).
- Sets defaults: `BB_CONFIG`, `BB_INPUT_CONFIG`, `BB_GPU_USER_DIR` and `BB_VBLANK_HZ=60`. It also
  sets the three Uncharted shader hashes (`run.py:96-98`): `BB_VELOCITY_PS=f4b18264`,
  `BB_UPSCALE_BEFORE_CS=aec539f0` and `BB_HUDLESS_PS=484cdbf5`.
- Runs `prepare()` (`run.py:65`). This runs `scripts/prepare.py` and then `scripts/link_modules.py`
  for the chosen executable, into `out/<exe stem>/`. The result is cached by modification time
  against the executable, `scripts/*.py` and `sce_module/*.prx`.
- Runs `scripts/content_profile.py` (`run.py:130`), which writes `content.bin` (`BBCONT01`: SKU
  and user parameters for AppContent).
- Starts `bb-probe.exe boot-linked.bin --content-profile … --app0 <game> --user <dir>`.
- Handles LoadExec. When the guest calls `sceSystemServiceLoadExec`, `runtime_services.c:101-116`
  writes `BB_LOADEXEC_FILE` and exits with code 101. `run.py` then prepares the requested
  executable and restarts with `--guest-argv`. This is how the U1 collection menu switches to U2
  or U3.
- Supports restarts. `BB_RESTART_COMMAND` (`run.py:133`) re-runs `run.py --after <pid>`. The
  in-game "Apply and restart" uses it through `runtime_restart()` (`probe.c:662`).

`run.py` does **not** run `patches.py` or `mods.py`. The package does not ship them either
(`package.sh`: "Bloodborne's patch and mod tools stay out").

### 3. Preparation scripts (`scripts/`)

- **`prepare.py`** parses a plaintext SELF/ELF (no decryption): segments, the dynamic table,
  relocations and import NIDs. It writes `boot.bin`, an analysis JSON, and `sfo()` for
  `param.sfo`.
- **`link_libc.py`** links the game's `libc.prx` (BBPROBE3/4 formats). `link_modules.py` imports
  `encode_id` from it.
- **`link_modules.py`** places the executable and the default modules `libc.prx` and
  `libSceFios2.prx` one after another in a single image, with one shared import table. Exports are
  matched by (NID, library, module). It writes **BBPROBE5** plus `link.json`. It also rewrites
  `mov rax, fs:[0]` (`FS_LOAD`) for the TCB, and maps library codes to the spelling the runtime
  was first written for (`RUNTIME_SPELLING`, `link_modules.py:27`, keyed to Bloodborne CUSA03173).
  That spelling is shared plumbing, not dead code.
- **`content_profile.py`** writes the content profile described in step 2.

### 4. Loader (`src/probe.c`, about 1,000 lines)

1. On Windows, `runtime_memory_reserve()` reserves the PS4 user range, and
   `runtime_thread_tcb_offset()` claims a TEB TLS slot before any driver DLL loads (`probe.c:702`).
2. It parses arguments, the content profile and `param.sfo`: the save-data ID, the title, and
   `bbnet_configure`.
3. It installs a vectored exception handler (`probe.c:189`). The handler first passes GPU page
   tracking faults to `bbgpu_handle_fault`, then handles speculative-read recovery
   (`runtime_fault_recover` and `bb_longjmp`), then prints a fatal report with an rbp stack walk.
4. It reads and validates `boot-linked.bin` (BBPROBE1..5): segments, import names, relocations
   (kind 0 = image-relative, 1 = function import, 2 = data import), the module table, native
   bindings and TLS. The image is mapped low with `runtime_image_map` (`runtime_memory.c:706`):
   at 0x400000 where possible and always below 2 GiB, because Uncharted's `TGenericOffsetPtr`
   requires it.
5. It initializes the GPU with `bbgpu_init` (`probe.c:902`), using the title, serial, SDK
   version and attributes.
6. **Imports.** Each import gets a 32-byte trap stub that stops with
   "STOP: first unsupported PS4 import" (`unresolved()`, `probe.c:121`), and data imports get
   no-access pages. Then each relocation resolves through `runtime_resolve(name)` (`runtime.c`).
   That function tries each `runtime_*_resolve` module in turn and finally `bbgpu_resolve`. If
   none matches and a native binding exists, the native export from `libc.prx`/`Fios2` is used.
   There are no automatic success stubs: an unknown function stops the game.
7. **Patches and hooks**, in order:
   - `apply_patches` (`probe.c:362`, BBPATCH2 from `patches.py`). Only `run.sh` (Bloodborne)
     passes `--patches`.
   - `install_guest_hooks` (`probe.c:487`), the diagnostic call counters behind `BB_GUEST_HOOKS`.
   - `install_game_callbacks` (`probe.c:570`), the Uncharted mouse camera hooks and the U2 NaN
     fix.
   - `patch_eop_tick_wait` (`probe.c:630`).
   - On Windows, `patch_tcb_loads` (`probe.c:227`) rewrites `gs:[0]` to the TEB TLS slot.
8. It sets page protections, sets up module TLS and the main TLS, attaches the main thread, sets
   the guest FPU state, runs each module initializer (`libc` first), and then enters the guest
   entry point with `/app0/eboot.bin` plus the guest argv.

## C runtime modules

Each module exports a `runtime_<x>_resolve(name)` that maps scoped NIDs, or symbol names through
`import_names.inc` (933 lines), to host functions.

| File | Lines | Implements |
|---|---|---|
| `runtime.c` | 264 | libc process contracts (atexit, cxa guards, `__tls_get_addr`, procparam, heap API), the resolve chain, the NID-to-symbol table |
| `runtime_kernel.c` | 351 | libkernel/POSIX: clocks, sleep, errno mapping (FreeBSD values), pthread once and keys, signals, sysctl |
| `runtime_memory.c` | 866 | Direct and flexible memory, reservations, protection, queries. On Windows the PS4 range is a placeholder replaced by section views (`VirtualAlloc2`/`MapViewOfFile3`). Image placement below 2 GiB (Uncharted). |
| `runtime_thread.c` | 463 | Guest threads on pthreads, FreeBSD variant II TCB/TLS, the Windows TEB-slot TCB, thread IDs (U3 job workers) |
| `runtime_mutex.c`, `runtime_rwlock.c`, `runtime_sema.c` | 263, 162, 185 | PS4 mutexes, rwlocks, kernel semaphores (FIFO) |
| `runtime_fiber.c` | 361 | libSceFiber (fibers that move between threads; the Naughty Dog job system) |
| `runtime_file.c` | 541 | Guest mount points (`/app0`, `/temp0`, `/download0`, `/data`, `/savedata*`) on host directories, descriptors, getdents |
| `runtime_savedata.c` | 388 | libSceSaveData on host directories, plus the **Bloodborne "sound hack"** limited to Bloodborne title IDs (`:73-105`) |
| `runtime_services.c` | 696 | System services for an offline single user: UserService, NetCtl (unplugged), common dialogs, the IME dialog, PlayGo, `LoadExec` (exit 101), and dispatch of network/NP calls to the shadNet code when `BB_ONLINE=1` (`:672-686`) |
| `runtime_content.c` | 91 | AppContent from the content profile; system module load counts |
| `runtime_pad.c` | 852 | libScePad on SDL3 gamepad, keyboard and mouse (`input.ini` bindings), and the **Uncharted guest callbacks** (mouse follow camera for U1/U2/U3, U1 pad and stick hooks, U2 focus NaN fix; `:245-491`) |
| `runtime_audio.c` | 305 | libSceAudioOut on SDL3 streams with hardware-like pacing |
| `runtime_ajm.c` | 568 | libSceAjm: ATRAC9 through LibAtrac9; whole-buffer decode behaviour for Uncharted (`:334-341`) |
| `runtime_rtc.c`, `runtime_time.c` | 155, 29 | Calendar ticks, timeval |
| `compat_win.c/.h` | 244 | `bb_setjmp`/`bb_longjmp` and POSIX shims for MinGW |
| `vulkan_smoke.c` | 62 | `--vulkan-only` smoke test (app name still "Bloodborne native probe") |

The GPU side resolves its own HLE symbols (GnmDriver, VideoOut, AvPlayer, Videodec2, and
network/NP when online) through `bbgpu_resolve` in `gpu/shim/bbgpu.cpp`.

## GPU library

`gpu/CMakeLists.txt` builds `bbgpu` from the following parts:

- **Vendored shadPS4** (`gpu/shadps4`, from commit `b4e7ae7`, see `gpu/VENDOR.txt`):
  `video_core` (Liverpool PM4 processing, buffer and texture caches, page manager, the Vulkan
  renderer), `shader_recompiler` (GCN to SPIR-V through sirit), `common`, and
  `core/libraries/{gnmdriver,videoout,kernel/equeue,avplayer,videodec}`. Videodec2, used for the
  Uncharted cutscenes, came from IFreemz/shadPS4-Bloodborne-DLSS-FSR. Local edits are marked
  `bbport:`: 295 markers in 92 files.
- **`gpu/shim/`**:
  - `bbgpu.cpp`: the C API (`gpu/bbgpu.h`): init, resolve, fault handling, guest-write dump, text
    input, mouse, camera yaw.
  - `window.cpp`: the SDL3 window and the event and mouse thread.
  - `bbport_overlay.cpp`: the ImGui in-game menu, opened with Insert or L3+R3, drawn by
    `vk_presenter.cpp:161,859-890`.
  - `bbport_settings.{h,cpp}`: run-time settings in `bbport.ini`, with environment overrides.
  - `bbport_toggles.h`: run-time optimization kill switches through `BB_TOGGLE_FILE`, and
    `BbStats` counters for `BB_FRAME_STATS`.
  - `bbport_copy.cpp`: parallel guest-memory copies.
  - `bbport_write_log.cpp`: a ring of the GPU's writes to guest memory, dumped on a fault
    (`BB_WRITE_LOG`).
  - `bbport_threads.h`: helper thread sizing.
  - `core/` and `common/`: minimal stand-ins for shadPS4's emulator core (`memory.h`,
    `address_space.h`, `signals.h`, `emulator_settings.h`, …), including `core/bloodborne_re.h`
    for co-op.
- **bbport renderer additions** (new files in `gpu/shadps4/video_core/renderer_vulkan/`, about
  9.3k lines in total with the host shaders):
  - `vk_temporal_upscaler.{h,cpp}` (about 2.4k lines): FSR 3.1, FSR 4 and FSR 4.1.1, TAA and DLSS
    on the HDR scene before the game's post-processing. It is placed by shader-hash triggers
    (`BB_UPSCALE_BEFORE_CS`, `BB_HUDLESS_PS`, `BB_UI_TRIGGER_VS`, `vk_temporal_upscaler.cpp:179-186`).
  - `vk_frame_generation.*` (about 840 lines, new in `5c457e7`): FSR 3 frame interpolation or
    DLSS-G. It uses the frame without UI and puts the UI back on top with `frame_gen_ui.comp`.
  - `vk_camera_motion.*`: camera motion vectors. For Uncharted they are rebuilt from the motion
    blur velocity pass constants (`BB_VELOCITY_PS`, `vk_rasterizer.cpp:1605`).
  - `vk_object_motion.*` and `motion_history.h`: object motion vectors (Bloodborne-era).
  - `vk_dlss.*`: loads `bbport_dlss.dll` at run time. `vk_fsr4.*` and `fsr411/`: FSR 4 INT8.
  - `vk_scene_resolution.*` and `scene_resolution.h`: reduced raster targets for live resolution
    changes.
  - `vk_draw_prep.*`, `vk_draw_pipe.h`, `vk_bind_helper.h`, `vk_constant_ring.h`: the parallel
    draw pipeline (`docs/parallel_gpu.md`).
  - `vk_frame_capture.*`, `vk_gpu_profiler.*`: diagnostics.
  - `ui_composition.h`: Scaleform UI detection by hard-coded shader hashes.
  - New host shaders: `taa.comp`, `camera_motion.comp`, `upscale_*.comp`, `frame_gen_*.comp`,
    `buffer_multi_copy.comp` and others.
- **The heaviest edits to upstream files** (diff lines): `vk_rasterizer.cpp` (about 3.3k),
  `vk_presenter.cpp` (about 980), `buffer_cache.cpp` (about 940), `liverpool.cpp` (about 810),
  `vk_scheduler.{h,cpp}` (about 1k), `vk_pipeline_cache.cpp`, `vk_shader_hle.cpp`,
  `vk_runtime.cpp`, `page_manager.cpp`.
- **`bbnet`**: a static library of shadNet, network and NP code with protobuf, OpenSSL, zlib and
  miniupnpc (Windows). It is always linked into `bbgpu` (`CMakeLists.txt:178-206`).
- **`gpu/dlss_bridge`**: built separately with MSVC by `packaging/windows/build_dlss.sh`.
- **Optimization settings.** LTO is on by default on Linux and off on Windows. PGO is used on
  Linux when there are `.gcda` files in `pgo/`. FSR-Vulkan gets local patches from
  `gpu/patches/fsr-vulkan/*.patch`, which `build.sh` applies to the submodule working tree.

## Launchers

| File | Platform and toolkit | Game | Used by the Uncharted release? |
|---|---|---|---|
| `launcher/uncharted_launcher.py`, `uncharted_widgets.py`, `uncharted_art.py`, `uncharted_fonts.py` | Windows, Tkinter, frozen to `Uncharted.exe` | Uncharted | **Yes** |
| `launcher/bbport_steam.py` | Steam `shortcuts.vdf` writer | Shared; its self-test strings still say Bloodborne (`:138-140`) | **Yes** (imported at `uncharted_launcher.py:1458`) |
| `launcher/bbport_launcher_win.py` | Windows, Tkinter | Bloodborne (`Bloodborne.exe`, online play, mods, patches) | No |
| `launcher/bbport_launcher.py`, `bb-launcher.sh`, `install-desktop.sh`, `io.github.bbport.Launcher.desktop.in`, `launcher/shell.nix` | Linux, GTK4/libadwaita | Bloodborne | No |
| `launcher/bbport_i18n.py`, `bbport_lang.py`, `bbport_lang_more.py`, `bbport_assets.py`, `bbport_vulkan.py` | Translation tables (Russian text as key), FSR 4 asset check, Vulkan ICD discovery for the AppImage | Bloodborne | No |
| `launcher/bloodborne.ico/png` | Icons | Bloodborne | No |

The Uncharted launcher handles the game folder, the choice of U1/U2/U3, display, AA, frame
generation, controls (written to `input.ini`), Add to Steam, shortcuts and a self-updater (GitHub
releases API, `uncharted_launcher.py:41,1533-1575`). Its version is hard-coded as
`VERSION = '0.3.3'` (`:40`). The UI text goes through a no-op `_()` (`:144`), so translation is
planned but not implemented.

## Packaging

- **`packaging/windows/package.sh`** (MSYS2 CLANG64, after `build.sh`):
  - Freezes the launcher with PyInstaller in a private venv (`out/pyenv`, needs a python.org
    Python) and strips `bb-probe.exe`.
  - Copies the CLANG64 DLLs found by `ldd`, the four preparation scripts, `run.py`, FSR 4 assets
    when present, and the DLSS DLLs when present.
  - Collects licenses, zips the result into `dist/uncharted-windows.zip`, and refreshes
    `dist/uncharted-windows/`, keeping saves and settings.
- **`packaging/windows/build_dlss.sh`** builds `bbport_dlss.dll` with Visual Studio 2022 against
  the `DLSS_SDK_ROOT` checkout, and copies `nvngx_dlss.dll` and `nvngx_dlssg.dll`.
- **`packaging/windows/play.c`** is "Play Uncharted.exe", which runs `Uncharted.exe --play`.
  `make_uncharted_icon.py` and `README-Uncharted.txt` are the Uncharted assets.
  `make_icon.py`, `README-Windows.txt` and `README.md` still describe the **Bloodborne** Windows
  build (`Bloodborne.exe`, `bbport_launcher_win.py`, `CUSA03173`).
- **`packaging/appimage.sh`, `default.nix`, `bbport-entry.c`** build
  `dist/Bloodborne-bbport-x86_64.AppImage` with the GTK launcher and `run.sh`. They are Bloodborne
  only.

## Tools

- **Uncharted-era drivers:**
  - `tools/try.py`: run one Uncharted game in the loader.
  - `tools/missing.py`: list imports that are not implemented, per Uncharted executable.
  - `tools/drive.py`: scripted input and screenshots.
  - `tools/watch_freeze.py`, `tools/stacks.{py,c}`: thread stacks of a running process (Windows
    dbghelp).
  - `tools/shot.ps1`: screenshot of the game window.
- **Shared diagnostics:** `got_import.py`, `import_names.py` (updates `src/import_names.inc`),
  `ab.sh` (A/B tests of `BB_TOGGLE_FILE` bits), `gpu_capabilities.c` (`bb-gpu-capabilities`, used
  for live-resolution auto-detection), `bridge_helper/`.
- **Bloodborne/Linux-era scripts:** `press.sh`, `restart.sh` and `soak.sh` call `run.sh`.
- **FSR 4 assets:** `fetch_fsr4_assets.sh`, `fsr4_optimize.sh`, `fsr4_verify.sh`, the
  `fsr4_*.pl` filters and `Fsr4SpirvCrossFixes.pm`. `fsr4cap/` captures FSR 4.1.1 under
  vkd3d-proton and replays it.

## Uncharted-specific vs Bloodborne leftovers

**Uncharted-specific (in use):**

- `run.py`; `launcher/uncharted_*.py`; `packaging/windows/{package.sh,play.c,make_uncharted_icon.py,README-Uncharted.txt}`.
- The guest callbacks in `src/runtime_pad.c:245-491`, `patch_eop_tick_wait` (`probe.c:630`) and
  low image placement (`runtime_memory.c:706`).
- U3 thread IDs (`runtime_thread.c:156`) and the AJM behaviour (`runtime_ajm.c:334`).
- Videodec2, `vk_frame_generation.*`, the velocity-pass camera path in
  `vk_camera_motion.cpp`/`vk_rasterizer.cpp:1605`, and the U2 scalar-copy shader HLE
  (`vk_shader_hle.cpp:246-247`).
- The `tools/` drivers listed above.

**Shared (game-agnostic or reused):** the loader, the link scripts, most runtime modules, the
shadPS4 core, the upscalers (FSR 3/4, TAA, DLSS), the parallel GPU pipeline, overlay
infrastructure, the settings model and `bbport_steam.py`.

**Bloodborne leftovers still in the tree:**

| Item | Where | Effect on the Uncharted build |
|---|---|---|
| Bloodborne patches (60 entries) and compiler (FPS presets, effect and cheat names, hard-coded scene and UI size addresses, `BLOODBORNE_IDS`) | `patches/Bloodborne.xml`, `scripts/patches.py:16-60,96-99,211` | Not run, not packaged. Dead for Uncharted. |
| Loose-file mod merger (Bloodborne `dvdroot_ps4` folder names) | `scripts/mods.py` | Not run, not packaged |
| 20 effect, cheat and tweak switches (Russian labels) | `gpu/shim/bbport_settings.h:30-51` (`Effects[]`) | **Compiled in and shown** in the in-game menu, with "Apply and restart", but nothing applies them in Uncharted. The lead's uncommitted edit hides them unless `BB_GAME_PATCHES=1`. |
| Menu title "Bloodborne — настройки" and the hint naming `patches/Bloodborne.xml` and Nexus mod #253 | `gpu/shim/bbport_overlay.cpp:165,397-401` | **Visible to Uncharted players** at `HEAD`; being fixed now |
| Live-resolution/startup-patch model (`live_resolution`, `output_res`, `model_lod`, `BB_RENDER_RES` patch path) | `bbport_settings.h`, `vk_temporal_upscaler.cpp:189-200`, `run.sh` | Partly dead: the patch path needs `patches.py` |
| shadNet online co-op (about 47k lines; `core/bloodborne_re.h`) | `gpu/bbnet`, `gpu/shadps4/{shadnet,core/libraries/network,core/libraries/np}`, `runtime_services.c:672` | **Compiled and linked**, adding protobuf, OpenSSL, zlib and miniupnpc build dependencies. Only `bbport_launcher_win.py:370` sets `BB_ONLINE`, so it never runs in Uncharted. |
| Sound-hack save edit | `src/runtime_savedata.c:73-105` | Inert (limited to Bloodborne title IDs) |
| Fallback title "Bloodborne" | `src/probe.c:892` (working tree), `gpu/shim/bbgpu.cpp:226`, `src/vulkan_smoke.c:10` | Cosmetic (used only without `param.sfo`) |
| GTK and Windows Bloodborne launchers, language tables, icons | `launcher/bbport_*` (except `bbport_steam.py`), `bb-launcher.sh`, `install-desktop.sh`, `*.desktop.in`, `launcher/shell.nix`, `bloodborne.*` | Not packaged |
| Linux starter, AppImage and Nix packaging | `run.sh` (defaults to `../CUSA03173`), `packaging/appimage.sh`, `default.nix`, `bbport-entry.c`; `runtime_restart()` on Linux runs `bash run.sh` (`probe.c:684`) | Not Uncharted-capable (see [Linux status](#linux-status-for-uncharted)) |
| Bloodborne build documentation | `packaging/windows/README.md`, `README-Windows.txt`, `make_icon.py`, `docs/ROADMAP.md`, `docs/DEVELOPMENT_LOG*.md`, `docs/history/*`, `docs/original-readme/` | Misleading for a new maintainer |
| Scaleform movie shader hashes (added in Bloodborne 0.2) | `gpu/shadps4/video_core/renderer_vulkan/ui_composition.h:28-29` | Probably Bloodborne-only; only matters for reduced-scene UI composition |
| Tests that target Bloodborne | `tests/test_patches.py`, `test_mods.py`, `test_run_settings.py` (`run.sh`), `test_packaged_vulkan.py` (AppImage) | They keep leftovers covered while the shipped path stays untested |

## Hard-coded game-specific hacks

- **`install_game_callbacks`** (`probe.c:570`, table at `runtime_pad.c:484-491`) has six entries:

  | Entry | Offset |
  |---|---|
  | U1 follow camera | `0xaecf0` |
  | U1 pad update | `0x117200` |
  | U1 joypad sticks | `0x11784e` |
  | U2 follow camera | `0x171fe0` |
  | U3 follow camera | `0x121b90` |
  | U2 camera focus NaN reset (in-place patch) | `0x33ba13` |

  Each entry is guarded by an exact byte signature, so a different game version silently gets no
  hook. Camera object field offsets (`+0x1310` and others for U1/U2/U3) and arc constants are
  hard-coded (`runtime_pad.c:245-280`). The thunks need memory within 2 GiB of the image.
  `near_image_memory` is Windows-only (`probe.c:566` returns NULL elsewhere). On Linux,
  `install_game_callbacks` also **returns early** (`probe.c:585`) at the first callback that needs
  a thunk. That skips the later table entries, including the U2 NaN patch, which needs no thunk.
- **`patch_eop_tick_wait`** (`probe.c:630-660`) searches the image for the assertion text
  `GetRenderFrameParams(frameToFreeInstancesFor)->m_gfxEopTick`. It then finds the `lea rdi` that
  references it, then a `cmp qword [reg+disp32],0; jne` within 64 bytes before that. It rewrites
  the branch into a `pause` loop. This works across versions as long as the instruction pattern
  holds, and it is applied to every executable, including non-Uncharted ones.
- **Shader hashes:**
  - `run.py:96-98` (velocity, upscale-before and HUD-less passes).
  - `vk_shader_hle.cpp:23,246-247`: copy shaders `0xfefebf9f`, `0x2d215c3b` and `0x6a6422a9`
    (U2).
  - `ui_composition.h:28-29` (Scaleform).
  - `BB_UI_TRIGGER_VS` (optional).
- **Bloodborne addresses** in `patches.py:96-99` (`SCENE_WIDTH` and others) and all of
  `Bloodborne.xml`, for app version 01.09.
- **Runtime NID spelling** is keyed to Bloodborne CUSA03173 library codes
  (`link_modules.py:22-27`, `runtime.c:191`).
- **Known Uncharted 1.02 (CUSA02320) crashes** listed in `README.md` suggest the hooks and HLE
  were tuned mostly on one dump (U1 `CUSA02343` 1.00 per `runtime_pad.c:245`).

## Build

**Windows (the shipped target)**, from an MSYS2 **CLANG64** shell:

1. Install the packages listed in `packaging/windows/README.md`: toolchain, cmake, ninja, pkgconf,
   python, Vulkan headers and loader, VMA, glslang, SDL3, fmt, boost, robin-map, xxhash, ffmpeg,
   zydis, SPIRV tools, headers and cross, protobuf, openssl, zlib, miniupnpc, nlohmann-json.
2. Run `bash build.sh`. On MINGW/MSYS it sources `msys2-env.sh` and initializes submodules (it
   checks for fsr-vulkan, imgui and xbyak). It applies the FSR-Vulkan patches, configures CMake
   (`RelWithDebInfo`, PGO off, `BB_LTO` default OFF) and builds `bb-probe`,
   `bb-gpu-capabilities` and `bb-play` in `out/gpu`, then copies them to `out/` (`build.sh:7-33`).
   On Windows `bb-probe.exe` is a CMake target that links the static `bbgpu`, the runtime and
   `atrac9` (`gpu/CMakeLists.txt:241-262`).
3. Optionally build DLSS with `DLSS_SDK_ROOT=… bash packaging/windows/build_dlss.sh` (needs MSVC
   2022).
4. Package with `bash packaging/windows/package.sh` (needs a python.org Python, or `WINPYTHON`).
5. Run from source with `BB_GAME_DIR=… BB_EXE=u1 python run.py`, or with
   `python launcher/uncharted_launcher.py`.

**Linux**, with `bash build.sh` on the Nix path:

- CMake builds `libbbgpu.so` (LTO on, and PGO from `pgo/` when present). `$CC` then compiles
  `src/probe.c` and `src/runtime*.c` into `out/bb-probe` with `-Werror -no-pie`, and builds
  `out/bb-gpu-capabilities` (`build.sh:35-92`).
- `shell.nix` does **not** list protobuf, OpenSSL, zlib or nlohmann_json. `gpu/CMakeLists.txt`
  requires them on every platform since online play was added (`e076119`), so the Nix build
  environment is probably broken. This could not be verified here because Vulkan and SDL3 are
  not installed in this environment.

## Tests and CI

- **Python** (`python3 -m unittest discover -s tests -p 'test_*.py'`): **82 tests, 28 skipped**,
  run in about 14 s in this environment. The skips are 14 for `'build native probe first'`
  (`test_probe.py` looks for `out/bb-probe` with no `.exe`, so these always skip on Windows) and
  14 for `'run bash build.sh --test first'` (`test_runtime`, `test_sema`, `test_content`).

  | Suite | Tests | Covers |
  |---|---|---|
  | `test_prepare` | 6 | SELF parsing |
  | `test_link_libc` | 7 | Cross-module identity and TLS (synthetic) |
  | `test_content` | 5 | Content profile and runtime |
  | `test_probe` | 14 | Loader limits on tiny synthetic images |
  | `test_runtime` | 7 | Wrapper around the C runtime test |
  | `test_sema` | 4 | Semaphores |
  | `test_patches` | 11 | Bloodborne |
  | `test_mods` | 13 | Bloodborne |
  | `test_run_settings` | 5 | `run.sh` (Bloodborne) |
  | `test_packaged_vulkan` | 7 | AppImage |
  | `test_upscaler_assets` | 3 | Uses `bbport_assets` |

- **C tests**: `tests/test_pad.c`, `test_runtime.c`, `test_file_mods.c`, `test_sema.c` and
  `test_content.c` are built and run by `build.sh --test`, **only on Linux**. The Windows branch
  `exit 0`s at `build.sh:32`, before the `--test` block at `:94`.
- **C++ GPU tests**: `test_motion_history`, `test_motion_shaders`, `test_ui_composition`,
  `test_scene_resolution`, `test_taa_shader`, `test_camera_motion` and `test_upscaler_support`
  are CMake targets marked `EXCLUDE_FROM_ALL` (`gpu/CMakeLists.txt:266-304`). Only the docs
  describe running them by hand with `ninja -C out/gpu …`.
- **Not covered at all:**
  - `run.py`: executable selection, caching, the LoadExec loop, the restart command.
  - `link_modules.py`: BBPROBE5 and multiple modules.
  - The Uncharted launcher, including `game_environment` and the updater.
  - `package.sh`.
  - The guest callbacks and `patch_eop_tick_wait` signature matching.
  - Videodec2, frame generation, DLSS.
  - Any end-to-end boot. This needs game files, so it can only be a manual or local smoke test.
- **CI:** none. There is no `.github/` directory; the only workflows in the tree belong to the
  `gpu/third_party/fsr-vulkan` submodule.

## Linux status for Uncharted

**Short answer: Uncharted cannot be run on Linux with the shipped tooling.**

- **`run.sh`** is the Bloodborne pipeline:
  - It defaults to `../CUSA03173` and always runs `mods.py`, which assumes Bloodborne folders.
  - It calls `prepare.py` and `link_modules.py` without `--exe`, so it always links `eboot.bin`
    (the U1 menu).
  - It always compiles `patches.py`. The version check skips the Bloodborne patches on a
    non-01.09 game, but `--fps uncap` sets `BB_VBLANK_HZ=0`.
  - It does not set `BB_VELOCITY_PS`, `BB_UPSCALE_BEFORE_CS` or `BB_HUDLESS_PS`, so there are no
    motion vectors and no upscaler placement for Uncharted.
  - It has no LoadExec loop, so choosing U2 or U3 in the collection menu exits with code 101.
  - It sets no `BB_LOADEXEC_FILE`, so `sceSystemServiceLoadExec` stops with exit code 21
    (`runtime_services.c:111`).
- **`run.py`** calls `ctypes.windll` unconditionally in `no_console()` (`run.py:38-40`), and
  `wait_for` is Windows-only, so it crashes on Linux.
- **Loader:** `near_image_memory` returns NULL on Linux (`probe.c:566`), so there is no mouse
  camera, and because of the early return the U2 NaN patch is skipped too (see
  [Hard-coded game-specific hacks](#hard-coded-game-specific-hacks)). `runtime_restart` runs
  `bash run.sh` (`probe.c:684`) instead of `BB_RESTART_COMMAND`.
- **Build:** `shell.nix` is missing the bbnet dependencies (see [Build](#build)). No Uncharted
  build has been confirmed on Linux since `5c457e7`.
- **Features:** DLSS is Windows-only by design (an MSVC DLL). FSR 3, FSR 4 and frame generation
  are Vulkan code and should compile on Linux, but are untested there.
- **Launcher and AppImage:** `uncharted_launcher.py` uses `windll`, `%APPDATA%`, Windows Steam
  paths and PyInstaller roles (13 Windows-specific references). The AppImage bundles the Bloodborne
  GTK launcher and `run.sh`.

**What Linux support would take** (L overall):

1. Make `run.py` cross-platform (guard `windll` and `CREATE_NO_WINDOW`, find `bb-probe` without
   `.exe`, `os.waitpid`-style `--after`), and make `run.sh` a thin wrapper around it, or keep
   `run.sh` only for Bloodborne.
2. Implement `near_image_memory` with `mmap` hints within ±2 GiB of the image, and remove the
   early `return` in `install_game_callbacks`.
3. Make `runtime_restart` use `BB_RESTART_COMMAND` on all platforms.
4. Fix `shell.nix`, or add a CMake option that leaves out `bbnet`.
5. Port the Uncharted launcher (Tkinter runs on Linux; path, Steam and console handling need
   abstraction), or build a minimal CLI.
6. Build an AppImage or Flatpak that bundles `run.py` and the Uncharted launcher.
7. Validate guest behaviour (memory placement, fibers, Videodec2 FFmpeg) on Linux with real
   dumps.

## Technical debt and risks

1. **Vendored shadPS4 fork.** About 152k lines of C++ under `gpu/shadps4`, compared with upstream
   `b4e7ae7`:

   | Directory | Files | Identical | Modified | New |
   |---|---|---|---|---|
   | `video_core` | 145 | 58 | 50 (about 10k diff lines) | 37 (about 9.3k lines) |
   | `shader_recompiler` | 122 | 95 | 26 (about 670 diff lines) | 1 |
   | `common` | 81 | 78 | 3 | 0 |

   The core hot paths (`vk_rasterizer.cpp`, `buffer_cache.cpp`, `liverpool.cpp`, `vk_scheduler`,
   `page_manager.cpp`) carry the largest changes, so upstream merges into them will conflict.
   `VENDOR.txt` records the base commit and 9 backported recompiler fixes, but not the vendored
   `core/libraries/{network,np,system}`, `shadnet` or `common/discord_rpc_handler`. **Merge
   strategy:** treat `shader_recompiler` as the cheapest place to merge (mostly identical files;
   cherry-pick upstream recompiler fixes as is already done). Keep a script that diffs
   `gpu/shadps4` against the recorded upstream commit, so the `bbport:` delta stays reviewable.
   Upstream `video_core` refactors are probably not worth merging wholesale; take fixes one by
   one.
2. **Environment-variable sprawl.** About 200 distinct `BB_*` names: 178 quoted in C/C++ with
   174 `getenv` sites, 77 in Python, 27 in shell scripts. They mix user settings (upscaler,
   frame generation, window), plumbing (`BB_LOADEXEC_FILE`, `BB_RESTART_COMMAND`), per-game data
   (shader hashes) and over 100 diagnostic switches. There is no registry, no validation and no
   documentation, settings are read at scattered times, and typos fail silently.
3. **Hard-coded offsets and hashes** (see [Hard-coded game-specific hacks](#hard-coded-game-specific-hacks)).
   They are version-fragile. The 1.02 (CUSA02320) crashes listed in `README.md` suggest that
   support for each version is incomplete.
4. **Bloodborne baggage** (see [Uncharted-specific vs Bloodborne leftovers](#uncharted-specific-vs-bloodborne-leftovers)).
   About 47k lines of online code and four extra build dependencies are linked for no Uncharted
   feature. A Bloodborne menu was shown to players. Leftover tests keep dead code green.
5. **No CI and limited automated testing.** A Windows build break or a packaging regression is
   only found by hand.
6. **Documentation gaps.** No current Uncharted architecture, roadmap or contributor guide exists
   (this file is the first). `packaging/windows/README.md` describes the Bloodborne package.
   Knowledge is in dated logs (`docs/CHANGES_*`, `docs/history/*`), being translated from
   Russian. The `README.md` "Building" section is two lines long.
7. **Single maintainer and bus factor.** Uncharted work landed as one large drop (`5c457e7`,
   121 files) plus fixes, all by one author. The repository history is 16 days long. Bloodborne
   knowledge is with deadinside28.
8. **Internationalization.** Cyrillic text outside `docs/`, counted in lines:

   | File | Lines | Status |
   |---|---|---|
   | `launcher/bbport_launcher_win.py` | 204 | Bloodborne leftover |
   | `bbport_i18n.py` | 116 | Bloodborne leftover |
   | `bbport_launcher.py` | 107 | Bloodborne leftover |
   | `gpu/shim/bbport_overlay.cpp` | 95 at `HEAD` | Being translated |
   | `bbport_lang_more.py` | 43 | Bloodborne leftover |
   | `gpu/shim/bbport_settings.h` | 20 | Being translated |

   The Uncharted launcher is English with a placeholder `_()`. The overlay font is the embedded
   DejaVu (`BB_FONT_PATH`).
9. **Platform coupling.** Some code paths exist for Linux but receive no testing. Windows-specific
   build quirks: static `bbgpu`, `--disable-high-entropy-va`, a 16 MiB committed stack, LTO off,
   and DLSS that needs MSVC alongside MSYS2.
10. **Release process.** The version is only in `uncharted_launcher.py:40` and commit messages.
    Releases are built by hand on the maintainer's machine. FSR 4 assets come from a separate
    download script, and FSR 4.1.1 assets cannot be redistributed.

## Improvement candidates

Effort: S is under a day, M is one to three days, L is a week or more.

| # | Priority | Change | Files | Effort |
|---|---|---|---|---|
| 1 | P0 | Finish the game-aware overlay (in progress): English strings, generic title, hide Bloodborne effects, cheats and LOD unless patches apply (`BB_GAME_PATCHES`), drop the Nexus #253 hint | `gpu/shim/bbport_overlay.cpp`, `gpu/shim/bbport_settings.h`, `src/probe.c` | S |
| 2 | P0 | Add CI: an Ubuntu job for the Python tests, and a Windows `msys2/setup-msys2` CLANG64 job that runs `bash build.sh` and the Python tests (cache pacman and ccache). Later, build the package as an artifact | new `.github/workflows/ci.yml` | M |
| 3 | P1 | Run the native tests on Windows: let `build.sh --test` build and run the C tests and the `EXCLUDE_FROM_ALL` GPU tests through CMake/ctest; teach `tests/test_probe.py` about `bb-probe.exe` | `build.sh:7-33,94-105`, `gpu/CMakeLists.txt:241-304`, `tests/test_probe.py:9` | M |
| 4 | P1 | Test the shipped path: `run.py` with stand-in scripts and probe (as `test_run_settings.py` does for `run.sh`), covering executable mapping, prepare caching, the LoadExec loop and the restart command; synthetic tests for `link_modules.py` BBPROBE5; `uncharted_launcher.game_environment` | new `tests/test_run_py.py`, `tests/test_link_modules.py`, `tests/test_uncharted_launcher.py` | M |
| 5 | P1 | Add one per-title "game profile" (title IDs and executables to shader hashes, callback table, EOP patch on/off, UI hashes) in place of `run.py` `setdefault`s and scattered constants; log which profile entries matched at start | `run.py:96-98`, `src/runtime_pad.c:484-491`, `src/probe.c:570-660`, `gpu/.../ui_composition.h`, `vk_shader_hle.cpp` | M |
| 6 | P1 | Build an environment-variable registry: one table (name, scope user/plumbing/debug, default, reader) generated into `docs/ENVIRONMENT.md`, with a unit test that greps the sources for unregistered `BB_*` names; move user settings into `bbport.ini` | new `docs/ENVIRONMENT.md`, `tests/test_env_registry.py`; `gpu/shim/bbport_settings.cpp`, `launcher/uncharted_launcher.py:290-330` | M |
| 7 | P1 | Isolate Bloodborne: move `launcher/bbport_*` (keep `bbport_steam.py`), `patches/`, `scripts/{patches,mods}.py`, `run.sh`, `packaging/{appimage.sh,default.nix,bbport-entry.c}`, `tools/{press,restart,soak}.sh` and their tests into `legacy/bloodborne/`, or delete them (the history keeps them) | as listed | S–M |
| 8 | P1 | Add a CMake option `BB_ONLINE` (default OFF for Uncharted) that leaves out `bbnet`, shadNet and NP and their protobuf, OpenSSL and miniupnpc dependencies; stub `bbnet_configure` and the network resolve | `gpu/CMakeLists.txt:160-206`, `src/runtime_services.c:672-690`, `gpu/shim/bbgpu.cpp` | M |
| 9 | P2 | Fix Linux loader gaps: `near_image_memory` with `mmap` hints, no early `return` in `install_game_callbacks`, `runtime_restart` through `BB_RESTART_COMMAND` | `src/probe.c:553-590,662-688` | S |
| 10 | P2 | Linux Uncharted support: cross-platform `run.py`, fixed `shell.nix`, an Uncharted AppImage, launcher portability (see [Linux status](#linux-status-for-uncharted)) | `run.py`, `shell.nix`, `packaging/*`, `launcher/uncharted_launcher.py` | L |
| 11 | P2 | Make upstream sync repeatable: complete `VENDOR.txt` (network, np, system, shadnet, discord), add `tools/upstream_diff.sh` (fetch the base commit and report modified and new files), keep a log of cherry-picks | `gpu/VENDOR.txt`, new `tools/upstream_diff.sh` | S, then M for each merge round |
| 12 | P2 | Update the docs: rewrite `packaging/windows/README.md` for Uncharted, write an Uncharted `docs/ROADMAP.md`, move Bloodborne roadmaps and logs to `docs/history/bloodborne/`, expand the README "Building" section | `packaging/windows/README.md`, `docs/ROADMAP.md`, `README.md` | S |
| 13 | P2 | Clean up the remaining "Bloodborne" defaults: fallback title and app names | `src/probe.c:892`, `gpu/shim/bbgpu.cpp:226`, `src/vulkan_smoke.c:10`, `launcher/bbport_steam.py:138-140` | S |
| 14 | P3 | Internationalization: choose English as the source, wire the Uncharted launcher's `_()` to a real catalog, and provide overlay strings through a table | `launcher/uncharted_launcher.py:144`, `gpu/shim/bbport_overlay.cpp` | M |
| 15 | P3 | Strengthen version handling: per-version signature tables for the guest callbacks, and investigate the CUSA02320 1.02 crashes listed in `README.md` | `src/runtime_pad.c`, `tools/missing.py`, `tools/try.py` | M–L |
| 16 | P3 | Release automation: one source for the version (for example `VERSION` read by the launcher and the package), and a tag-driven packaging job (DLSS needs an MSVC runner) | `launcher/uncharted_launcher.py:40`, `packaging/windows/package.sh` | M |

## Method and caveats

- **Static reading only.** Findings come from reading the tree at `68c8cf9`, from read-only `git`
  commands, and from running the Python test suite. No game binary was run and no native build was
  attempted: Vulkan and SDL3 are not installed in this environment.
- **How the upstream divergence was measured.** The numbers come from comparing `gpu/shadps4/*`
  with a shallow fetch of `shadps4-emu/shadPS4@b4e7ae7` (`src/`), counting identical, modified and
  new files plus `diff` line counts.
- **How the environment-variable counts were made.** Counts are distinct `"BB_…"` string
  literals in C/C++, quoted names in Python, and `$BB_…` references in shell scripts. CMake
  options such as `BB_LTO` and `BB_PGO` are excluded; a few counted names may not be environment
  variables.
- **Files that changed during the review.** `docs/` and three source files (`src/probe.c`,
  `gpu/shim/bbport_overlay.cpp`, `gpu/shim/bbport_settings.h`) were being edited by others while
  this was written. Line numbers in those files may shift.
