# Overview map: how this tree runs Uncharted

*Written by Claude on 2026-10-17 from reading the code on `linux` (based on `main` 68c8cf9). Nothing here was run on Linux. Each claim is "read", not "measured". Module maps for the parts below are the roadmap's first goal; this page is the index they hang off.*

## The idea in one paragraph

This is not an emulator. The game's own x86-64 code (from the PS4 executables in the player's dump) runs natively on the PC. A small runtime written in C replaces the PS4 system libraries the game calls, and the game's GPU command stream is translated to Vulkan by a renderer taken from shadPS4 and extended. The tree is SuperMedo's Uncharted port of **bbport**, deadinside28's native Linux port of Bloodborne, so most of the code, the comments and many docs still say Bloodborne (`bb`, `bbport`, `BB_*`).

## The pieces

| Piece | Where | What it is |
|---|---|---|
| Executable preparation | `scripts/prepare.py`, `scripts/link_modules.py`, `scripts/link_libc.py`, `scripts/patches.py`, `scripts/mods.py` | Python, run offline on the player's dump. `prepare.py` inspects an already-plaintext PS4 SELF (no decryption) and turns it into a flat memory image plus metadata. `link_modules.py` (the successor of `link_libc.py`, which it still imports for `encode_id`) links the PS4's own libc.prx and other modules in as native code. `patches.py` applies game patches (`patches/`); `mods.py` handles mods (`docs/MODS.md`). |
| Loader | `src/probe.c` (1,008 lines) | The process that maps the prepared image (segments, relocations), resolves the game's imports to the runtime, and jumps to the entry point. Builds as `out/bb-probe` (Linux) or `out/bb-probe.exe` (Windows). Its first line calls itself a "minimal x86-64 native loader experiment". |
| Import table | `src/import_names.inc` (933 lines) | The PS4 library functions the runtime knows by name. |
| PS4 runtime (the replaced system libraries) | `src/runtime*.c`, `src/runtime.h` | One file per area: `runtime_memory` (866), `runtime_pad` (852, controllers), `runtime_services` (696; also the "load another executable" exit, code 101), `runtime_ajm` (568, audio decode via LibAtrac9), `runtime_file` (541), `runtime_thread` (463), `runtime_savedata` (388), `runtime_fiber` (361), `runtime_kernel` (351), `runtime_audio` (305), plus `runtime_content`, mutex, rwlock, sema, time, rtc. `src/compat_win.c`/`.h` hold Windows shims; `src/vulkan_smoke.c` is linked into the loader too. |
| GPU library | `gpu/` → `libbbgpu.so` (Linux) or linked into the exe (Windows) | `gpu/shadps4/` is a vendored part of shadPS4 (commit b4e7ae7, see `gpu/VENDOR.txt`): `video_core` (Vulkan renderer), `shader_recompiler` (PS4 GCN shaders to SPIR-V), `common`, plus the gnmdriver/videoout libraries and Videodec2 for cutscenes. Local changes are marked `bbport:`. `gpu/shim/` is this project's glue: `bbgpu.cpp` (the C entry points `src/` calls, header `gpu/bbgpu.h`), `window.cpp`/`sdl_window.h` (SDL3 window), `bbport_overlay`, `bbport_settings`, `bbport_threads.h`, `bbport_copy`, `bb_win_compat.h`. `gpu/third_party/` is vendored libraries (sirit, half, imgui, FSR-Vulkan, xbyak and others). |
| Upscalers | `gpu/third_party/fsr-vulkan`, `gpu/patches/fsr-vulkan`, `tools/fsr4cap/` | FSR 3.1, FSR 4 and 4.1.1 (assets built on the player's machine from their own DLLs), DLSS on Windows through `tools/bridge_helper/`. Design notes: `docs/upscaler.md`, `docs/motion_vectors.md`, `docs/DEPTH_ADAPTIVE_TAA.md`. |
| Launchers | `run.py` (157 lines), `run.sh` (125), `launcher/` | `run.py` starts the loader, picks the game, and relaunches when the collection menu asks for another game (exit code 101). It uses Windows-only calls (`ctypes.windll.kernel32`, `CREATE_NO_WINDOW`). `run.sh` is the old Bloodborne Linux launcher (default folder `../CUSA03173`, no game choice, no relaunch). `launcher/uncharted_launcher.py` (1,618 lines) is the Windows GUI launcher; `bbport_launcher*.py` are Bloodborne's. |
| Build | `build.sh`, `gpu/CMakeLists.txt`, `shell.nix`, `msys2-env.sh` | `build.sh` branches on `uname -s`: MSYS2/MinGW builds everything with CMake + Ninja + clang; otherwise it needs pkg-config with vulkan and sdl3, cmake and ninja, builds `libbbgpu.so` with CMake, builds LibAtrac9, then compiles `src/probe.c` with the runtime files directly with `$CC` (`-Werror`). `bash build.sh --test` (Linux branch only) also builds and runs `tests/test_pad.c`, `test_runtime.c`, `test_file_mods.c`, `test_sema.c` and `test_content.c`. |
| Tests | `tests/` | The C tests above, `test_patches.py`, and GPU-side C++ tests (`test_taa_shader.cpp`, `test_scene_resolution.cpp`). |
| Packaging | `packaging/` | `packaging/windows/package.sh` (the zip SuperMedo ships) and `packaging/appimage.sh` (inherited from bbport). |

## How a game starts (read from the code)

1. The launcher (`run.py`, or the GUI) points at the player's dump and runs `prepare.py` then `link_modules.py` for the chosen executable (`run.py` `prepare()`, line 65).
2. It starts `bb-probe`, which maps the prepared image, binds imports to `src/runtime*.c`, and starts the game's code natively.
3. The game's GPU calls (gnmdriver, videoout) go through `gpu/shim/bbgpu.cpp` into shadPS4's `video_core`, which records Vulkan.
4. When the collection menu picks Uncharted 1, 2 or 3, the runtime exits with code 101 (`runtime_services.c`) and the launcher starts the chosen executable.

## Where Linux and Windows differ

Files with `_WIN32` / `windows.h` branches, by count (read with grep, 2026-10-17): `src/probe.c` 21, `src/runtime_file.c` 12, `runtime_thread.c` 7, `runtime_memory.c` 7, `runtime_kernel.c` 7, `runtime_fiber.c` 5, `runtime_services.c` 3, `gpu/shim/bbport_write_log.cpp` 3, `gpu/shim/bbport_threads.h` 3, `runtime_savedata.c` 2, `compat_win.c` 2, `gpu/shim/window.cpp` 2, `gpu/shim/bb_win_compat.h` 2, `gpu/shim/bbgpu.cpp` 2, and one each in `runtime_time`, `runtime_sema`, `runtime_rtc`, `runtime_pad`, `runtime.h`, `runtime.c`. These are the seams the Linux work touches. The Linux branches came from bbport and have not been run on this tree (see the roadmap's code review). `runtime_fiber.c`'s Linux stack-bounds handling is a deliberate no-op: test it first.

## What to ignore when mapping

- `gpu/shadps4/` and `gpu/third_party/` are vendored (688 of the 902 files). Map them only as "what this project changed", by searching for `bbport:` comments, not file by file.
- `launcher/covers/`, `launcher/fonts/`, icons: assets.
- `launcher/bbport_*`, `docs/history/`, much of `docs/` (largely Russian): inherited from Bloodborne. Mark any claim from them "inherited from Bloodborne, not verified for Uncharted".

## Module maps to write (the roadmap's first goal)

Each in `docs/maps/<name>.md`, listing files, entry points, how they connect, and gotchas, with every claim checked against the code:

1. `loader.md`: `src/probe.c`, `src/import_names.inc`, `src/runtime.c`/`runtime.h`.
2. `prepare.md`: `scripts/prepare.py`, `link_modules.py`, `link_libc.py`, `patches.py`, `mods.py`, and what lands in the prepared folder.
3. `runtime-os.md`: memory, file, thread, fiber, kernel, mutex, rwlock, sema, time, rtc (the OS-facing half; the Linux seams).
4. `runtime-game.md`: services (exit 101), savedata, content, pad, audio, ajm.
5. `gpu-shim.md`: `gpu/shim/` and every `bbport:` change inside `gpu/shadps4/`.
6. `launch-and-build.md`: `run.py`, `run.sh`, `build.sh`, `gpu/CMakeLists.txt`, `packaging/`, and what a Linux `run.py` needs.
