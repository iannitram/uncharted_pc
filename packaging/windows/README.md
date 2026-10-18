# NDC Native on Windows: building

The port builds and runs natively on 64-bit Windows 10 (1903+) / 11. Players: see
`README-Package.txt` (it ships in the package as README.txt). CI builds it on every pull request
(`.github/workflows/ci.yml`).

## Build

Install [MSYS2](https://www.msys2.org) (`winget install MSYS2.MSYS2`), open the
**MSYS2 CLANG64** shell and install the toolchain and libraries (the counterpart of
`shell.nix`):

```bash
pacman -S --needed git patch \
  mingw-w64-clang-x86_64-{toolchain,cmake,ninja,pkgconf,python} \
  mingw-w64-clang-x86_64-{vulkan-headers,vulkan-loader,vulkan-memory-allocator,glslang} \
  mingw-w64-clang-x86_64-{sdl3,fmt,boost,robin-map,xxhash,ffmpeg,zydis} \
  mingw-w64-clang-x86_64-{spirv-tools,spirv-headers,spirv-cross}
```

magic_enum, miniz and xbyak (not packaged by MSYS2) are submodules under `gpu/third_party/`.
Then, in the repository:

```bash
git submodule update --init --recursive
bash build.sh                      # out/bb-probe.exe, out/bb-gpu-capabilities.exe, out/bb-play.exe
BB_GAME_DIR=F:/path/to/CUSA02343 BB_EXE=u2 python run.py
python launcher/uncharted_launcher.py
bash packaging/windows/package.sh  # dist/ndc-native-windows/ and .zip
```

`run.py` prepares the chosen executable (`BB_EXE` = `u1`, `u2`, `u3`) and starts `bb-probe.exe`;
when the game switches executables (the collection menu starting U2 or U3), it prepares and
starts that one. From a source tree it adds `C:\msys64\clang64\bin` (or `$MSYS2_ROOT`) to
`PATH` for the DLLs.

The package freezes the launcher with PyInstaller (a private venv in `out/pyenv`, from a
python.org Python) into `NDC Native.exe`, which also runs `run.py` (`--run`), the preparation
scripts (`--script`) and the game without the window (`--play`): players need no Python.
`Play NDC Native.exe` (`packaging/windows/play.c`) runs `NDC Native.exe --play` from its folder
and waits for it, for shortcuts and Steam. The package's `licenses` folder is assembled by
`package.sh` (see `THIRD-PARTY-NOTICES.txt`), with `SOURCE.txt` naming the commit and library
versions.

FSR 4: `bash tools/fetch_fsr4_assets.sh` fetches the v07 INT8 assets into `fsr4_shaders/`, which
the package ships when present.

DLSS (optional): `DLSS_SDK_ROOT=<checkout of github.com/NVIDIA/DLSS> bash
packaging/windows/build_dlss.sh` builds `bbport_dlss.dll` (`gpu/dlss_bridge`, the only code that
uses the NVIDIA SDK, compiled with MSVC 2022) and copies it with `nvngx_dlss.dll` next to
`out/bb-probe.exe`; `package.sh` ships both when present, with NVIDIA's licence. The renderer
loads the bridge at run time (`vk_dlss.cpp`). `BB_DLSS=0` turns it off.

The icon (`launcher/uncharted.ico`/`.png`, original artwork) is drawn by
`packaging/windows/make_uncharted_icon.py` and built into the executables.

## What is different from Linux

| Linux | Windows |
|---|---|
| `mov rax, fs:[0]` rewritten to `gs:[0]`, GS base set with `arch_prctl` | GS is the TEB and cannot move. The loader rewrites the displacement to `gs:[0x1480 + 8*slot]` (the TEB's `TlsSlots[slot]`, same 9-byte instruction) and each guest thread keeps its TCB in that TLS slot. The slot is claimed first thing in `main` (Vulkan drivers take many). |
| One memfd for direct + flexible memory, `mmap(MAP_FIXED)` views | A pagefile-backed section; the PS4 range 64 GiB–1 TiB is reserved as one placeholder and views replace placeholders (`VirtualAlloc2`/`MapViewOfFile3`, as in shadPS4). Partial unmaps split views and restore page protections (GPU tracking). |
| `-no-pie`, heap below 1 TiB | `--disable-high-entropy-va`: heaps and thread stacks stay low and out of the PS4 range. |
| SIGSEGV handler, `sigsetjmp` recovery | Vectored exception handler; `bb_setjmp`/`bb_longjmp` (`src/compat_win.c`) restore all Win64 callee-saved registers without SEH unwinding (guest frames have no unwind data; clang's `__builtin_longjmp` restores a wrong frame pointer on Win64). |
| Guest thread stacks from `runtime_low_map` | Windows allocates them, fully committed (`pthread_attr_setstacksize`): guest code has no stack probes and would skip the guard page. The main thread stack is 16 MiB committed. |
| glibc `nanosleep`, monotonic condition variables | High-resolution waitable timers (`compat_sleep_ns`; winpthreads' sleep rounds to 15.6 ms); semaphore deadlines use `CLOCK_REALTIME` (winpthreads rejects monotonic condition variables). |
| `libbbgpu.so` | `libbbgpu.a`, linked into `bb-probe.exe` by CMake (`gpu/CMakeLists.txt`), with a manifest for UTF-8 paths and long paths. |
| In-game restart: `sh -c "$BB_RESTART_COMMAND"` | `run.py` puts its command line in `BB_RESTART_COMMAND`; the new launch waits for the old process (`--after PID`). The launcher keeps the game in a job object. |
| Mod overlay with symlinks | Symlinks when allowed (Developer Mode), else junctions for folders and hard links for files. |

Diagnostics added on the way: `BB_FRAME_DUMP_TRIGGER=<file>` writes the guest display buffer
and the presented image of the next frame to `BB_DUMP_DIR` (raw 32-bit pixels), which also
works for menus and movies.

Not ported: the watchdog/`--timeout` thread dumps (Linux signals), userfaultfd tracking
(`BB_UFFD`), MangoHud and PGO (GCC flags). The C test programs run on Linux in CI
(`tools/ci_linux.sh`).
