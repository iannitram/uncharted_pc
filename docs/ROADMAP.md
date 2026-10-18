# Roadmap: Uncharted: The Nathan Drake Collection, native on Linux (SteamOS)

Status as of 2026-10-16. This replaces the Bloodborne roadmap, which is kept in
`history/ROADMAP_bloodborne_2026-09_ru.md` (Russian, unchanged).

## Goal

Run Uncharted 1, 2 and 3 from the PS4 collection natively on Linux, on two machines
running SteamOS: a Strix Halo machine (main test and debug box) and a Legion Go
(handheld performance target). The existing Linux code path, inherited from the
Bloodborne port, is made to work for Uncharted. The emulation is not rewritten.

Ground rules:

- This stays a fork of `Supermedo/uncharted_pc` and keeps merging his changes. Linux work
  lives on the `linux` branch. Nothing goes back to SuperMedo without Ian saying so, one
  change at a time.
- No game files, dumps or keys in the repository. Each machine uses its own dump of the
  collection (CUSA02343 / CUSA02320).
- Every claim in a report says whether it was measured or only read from the code.

## What the code review found (2026-10-16, read from the code, nothing run on Linux yet)

- The tree descends from the Linux port of Bloodborne (`deadinside28/bloodborne_pc`, fork
  point 0afaaa2, 2026-10-04). SuperMedo's 26 Uncharted commits since then touch no Linux
  script. **Nothing suggests Linux was run on this tree after the fork.**
- `build.sh` still has a working-looking Linux branch (pkg-config for Vulkan and SDL3, CMake
  and Ninja, `libbbgpu.so`). `src/` is mostly branched for both platforms.
- `run.sh` is still the Bloodborne launcher (default game folder `../CUSA03173`). It has no
  choice of Uncharted 1, 2 or 3 and no relaunch when the collection menu starts another game
  (`sceSystemServiceLoadExec`, exit code 101). That logic lives only in `run.py`, which uses
  Windows-only calls. **Linux needs a `run.py` equivalent.**
- No Linux equivalents yet for: the Uncharted launcher (`uncharted_launcher.py`, Windows
  only), the DLSS bridge (NVIDIA only, not needed on AMD hardware), and a few diagnostics.
- One spot to test first: `src/runtime_fiber.c`, where the Linux stack-bounds handling is
  deliberately a no-op.
- bbport (the Bloodborne port) is 8 commits ahead of the fork point (settings menu, memory
  layer, DLSS in the AppImage, online play). Decide later which, if any, to take.

## Baseline: how stock shadPS4 does today

Public compatibility reports (shadPS4 compatibility list, read 2026-10-16, not our own
measurement): none of the collection's title ids is marked playable.

| Title id | OS | Reported status | Note |
|---|---|---|---|
| CUSA02320 | Windows | nothing (crashes) | issue #71, 2026-10-05 |
| CUSA02320 | Linux | ingame, graphics and cutscene problems | issue #147, 2026-07-30 |
| CUSA02343 | Windows | menus | issue #2645 |
| CUSA02344 | Windows | ingame, some sounds missing | issue #441, 2026-10-14 |
| CUSA02826 | Linux | menus; Uncharted 3 crashes on load | issue #477, 2026-10-14 |

Our own baseline (Phase 0 below) replaces this table with measurements.

## Phases

### First goal: code maps (Ian, 2026-10-17)
Before Phase 0, map the code so every later session starts from a short, checked guide
instead of re-reading 900 files. The index is [`maps/overview.md`](maps/overview.md)
(written 2026-10-17, read from the code, nothing run): what each part is, how a game starts,
and where Linux and Windows differ. Next, the six module maps it lists, each in
`docs/maps/`: loader, executable preparation, the OS-facing runtime (the Linux seams),
the game-facing runtime, the GPU shim and our changes inside the vendored shadPS4 code,
and launch plus build.
- Rules: every claim is checked against the code and marked read or measured; vendored code
  (`gpu/shadps4/`, `gpu/third_party/`) is mapped only by its `bbport:` changes; statements
  taken from the Bloodborne-era docs say "inherited from Bloodborne, not verified for Uncharted".
- The local Qwen model may draft module maps from a brief that carries the facts from the
  overview; Claude reviews every draft before it lands (on 2026-10-17, 7 of 41 Qwen maps and
  translations for the Craft apps were rejected and most others needed corrections).
- Done when the six module maps exist and each has been checked against the code.


### Phase 0: baseline with stock shadPS4 (Strix Halo)
- Install the latest shadPS4 release on the Strix Halo, install the dump, and play each
  game for about 15 minutes.
- Record per game: boots, reaches the menu, plays in-game, frame rate, visible problems,
  saved log. Fill in the table above. Done when all three games have a measured row.

### Phase 1: it builds on Linux
- Build the current tree on the Strix Halo (SteamOS, in a container or distrobox as needed).
  Fix compile and link errors. Also test-compile on Arch in a container on Hyperion first.
- Done when `bash build.sh` produces the loader and `libbbgpu.so` on Linux and the build
  steps are written down.

### Phase 2: Uncharted boots and shows the menu
- Write the Linux `run.py` (game choice, relaunch on exit code 101, saves, config).
- Done when the collection menu appears and each of the three games starts to its first
  scene, measured with logs, on the Strix Halo.

### Phase 3: all three games playable
- Work through the known problems in the README: Uncharted 2 streaming crash
  (`iSubMesh < m_numSubMeshInstances`), Uncharted 3 London bar crash, flashing shapes on
  some characters, and anything Linux-specific that turns up.
- Done when each game can be played for 30 minutes without a crash.

### Phase 4: 60 FPS on the Strix Halo
- Measure per game, find the bottleneck, tune. Done when each game holds 60 FPS in a
  defined test route.
- **First-launch shader preparation (Ian, 2026-10-16):** like God of War or The Last of Us
  Part I on Steam, show a one-time "preparing shaders" screen the first time a game starts,
  then play without compile stutter. Today shaders are translated and compiled while playing;
  the results are cached in `user/`, and the cache is thrown away when the graphics driver or
  card changes (log line "Pipeline cache isn't compatible with current system: rebuilding
  it"). Steps: (1) measure how bad the first-run stutter is per game; (2) record which
  shaders a full play route uses, keyed by shader hash; (3) at first launch, find those
  shaders in the player's own dump and compile them before the game starts, with a progress
  bar; (4) redo the step automatically after a driver change. Open question: whether the
  game's shaders can be found in the dump without running the game (not yet looked at). Do
  not ship translated or compiled shaders in the repository. Also check whether Steam's own
  shader pre-caching helps when this is added as a non-Steam shortcut (not known).

### Phase 5: handheld on the Legion Go and packaging
- AppImage first (the repo already has `packaging/appimage.sh`) plus a Steam shortcut; a
  proper Arch package later if wanted.
- Done when the AppImage runs on the Legion Go at a playable frame rate and a clean install
  is documented.

## Documentation

- Done: this roadmap; the old Russian one archived; the overview code map (`maps/overview.md`).
- To do: translate every remaining Russian document in `docs/` to English (16 of the 19 files
  are mostly or partly Russian; only `parallel_gpu.md` and `original-readme/` are English),
  marking Bloodborne-only statements as "inherited from Bloodborne, not verified for
  Uncharted". Suitable as homework for the local Qwen model, then reviewed.
- To do: a Linux and SteamOS install guide for Uncharted (none exists).

## Open items

- Which of bbport's 8 newer commits to take.
- Whether the Windows launcher gets a Linux counterpart or Linux stays command line plus
  Steam shortcut.
