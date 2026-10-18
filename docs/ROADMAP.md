# Roadmap: Uncharted: The Nathan Drake Collection, native on Linux (SteamOS)

Status as of 2026-10-17. This replaces the Bloodborne roadmap, which is kept in
`history/ROADMAP_bloodborne_2026-09_ru.md` (Russian, unchanged).

## Goal

Run Uncharted 1, 2 and 3 from the PS4 collection natively on Linux, on two machines
running SteamOS: a Strix Halo machine (main test and debug box) and a Legion Go
(handheld performance target). The emulation is not rewritten.

Ground rules:

- **Our `linux` branch builds on spacepepperoni's Linux fork** (`spacepepperoni/uncharted_Linux`,
  merged 2026-10-17 at c06843d, Ian's decision). That fork already builds and runs the collection
  on Linux and the Steam Deck and keeps merging SuperMedo's releases. We merge it (and through
  it SuperMedo) instead of redoing its work. Our own work stays on `linux`.
- Nothing goes to SuperMedo or spacepepperoni without Ian saying so, one change at a time.
- No game files, dumps or keys in the repository. Each machine uses its own dump of the
  collection (CUSA02343 / CUSA02320).
- Every claim in a report says whether it was measured or only read from the code.
- Their GitHub workflows came with the merge: `sync-upstream.yml` (every 6 hours, force-pushes an
  `upstream` branch and merges into `main`) and `build.yml` (releases on pushes to `main`). They only
  run from the default branch, so they are inert on `linux`. **Do not merge `linux` into our fork's
  `main` without deciding about them first.**

## Where things stand (2026-10-17)

What spacepepperoni's fork already does (read from their commits and README, **not measured on our
machines**):

- **Builds on Linux.** `build.sh` Linux branch, libavcodec for MP3 audio, CI builds an AppImage.
- **Launches on Linux.** `run.py` is cross-platform now (`WINDOWS = sys.platform == 'win32'`), and
  `launcher/uncharted_linux.py` (1,280 lines) is a Linux launcher: game choice, per-game Add to
  Steam, a Saves folder per game, an update check against both repos, crash reports to SuperMedo's
  issue tracker. `packaging/linux/package.sh` builds the tarball, `install.sh` is a one-line
  installer, and the AppImage updates itself.
- **Steam Deck mode**, chosen automatically on SteamOS (their README: 25-30 FPS on a Deck).
- **Linux game fixes:** the games' code callbacks installed on Linux (Uncharted 2 camera NaN, mouse
  look), PS4 FPU state for guest threads, a NaN guard on colour outputs (Uncharted 2 black squares),
  constant-ring polling (Uncharted 3 stretching), AMD GPU hang markers.
- **Ported fixes** from sibling shadPS4 and bbport forks: texture cache, VRAM pressure, frame limiter,
  SRT walker, swapchain.
- Their reported status: Uncharted 1 in-game, seems stable; Uncharted 2 in-game, physics glitches;
  Uncharted 3 crashes often.

Still true from our 2026-10-16 code review: `run.sh` is the old Bloodborne launcher (`../CUSA03173`);
`src/runtime_fiber.c`'s Linux stack-bounds handling is a deliberate no-op; bbport is ahead of the fork
point with commits we have not looked at.

## Phases

### First goal: code maps (Ian, 2026-10-17)
Before anything else, map the code so every later session starts from a short, checked guide
instead of re-reading 900 files. The index is [`maps/overview.md`](maps/overview.md) (updated
2026-10-17 for the merged Linux fork; read from the code, nothing run). Next, the module maps it
lists, each in `docs/maps/`: loader, executable preparation, the OS-facing runtime, the game-facing
runtime, the GPU shim and our changes inside the vendored shadPS4 code, and launch, build and
packaging (Linux launcher included).
- Rules: every claim is checked against the code and marked read or measured; vendored code
  (`gpu/shadps4/`, `gpu/third_party/`) is mapped only by its `bbport:` changes; statements taken
  from the Bloodborne-era docs say "inherited from Bloodborne, not verified for Uncharted".
- The local Qwen model may draft module maps from a brief that carries the facts from the
  overview; Claude reviews every draft before it lands (on 2026-10-17, 7 of 41 Qwen maps and
  translations for the Craft apps were rejected and most others needed corrections).
- Done when the module maps exist and each has been checked against the code.

### Phase 0: baseline on our machines (Strix Halo, then Legion Go)
- Build this branch on the Strix Halo (`bash build.sh`, in the craft-build container if the host
  lacks the libraries) and also try their released AppImage. Install the dump.
- Play each game about 15 minutes. Record per game: boots, menu, in-game, frame rate, visible
  problems, saved log. Compare with their reported status above.
- Done when all three games have a measured row on the Strix Halo, and the build steps for this
  machine are written down.

### Phase 1: done upstream (spacepepperoni)
Linux build, Linux launcher, relaunch on exit code 101, saves, AppImage, Steam shortcuts. Our part:
keep merging their `main` (and check it builds) before starting new work, so we never redo theirs.

### Phase 2: all three games playable
- Uncharted 3 first (theirs crashes often), then Uncharted 2's physics glitches, then the README's
  known problems (Uncharted 2 streaming crash `iSubMesh < m_numSubMeshInstances`, Uncharted 3
  London bar crash, flashing shapes on some characters). Check their open issues and branches
  (`up/*`) before starting, so we do not duplicate a fix in progress.
- Done when each game plays 30 minutes without a crash on the Strix Halo, measured.

### Phase 3: 60 FPS on the Strix Halo
- Measure per game, find the bottleneck, tune. Done when each game holds 60 FPS in a defined test
  route.
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

### Phase 4: the Legion Go
- Their Steam Deck mode is the starting point (also AMD, also SteamOS). Measure on the Legion Go,
  tune Deck mode or add a Legion Go profile.
- Done when the AppImage runs on the Legion Go at a playable frame rate and a clean install is
  documented.

## Documentation

- Done: this roadmap; the old Russian one archived; the overview code map (`maps/overview.md`).
- To do: translate every remaining Russian document in `docs/` to English (16 of the 19 files
  are mostly or partly Russian; only `parallel_gpu.md` and `original-readme/` are English),
  marking Bloodborne-only statements as "inherited from Bloodborne, not verified for
  Uncharted". Suitable as homework for the local Qwen model, then reviewed.
- Done upstream: install instructions for Linux and the Steam Deck (their README: AppImage,
  one-line installer). To do: notes for our two machines once Phase 0 has measured them.

## Open items

- Which of bbport's 8 newer commits to take.
- Settled: the Linux launcher exists (`launcher/uncharted_linux.py`, spacepepperoni).
- Whether to send anything of ours to spacepepperoni, and how (Ian's call, one change at a time).
- `run.sh` is still Bloodborne's; drop it or point it at Uncharted once Phase 0 shows which
  launch path we use.
