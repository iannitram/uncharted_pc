# Uncharted PC roadmap — 2026-10-24

This plan supersedes the inherited Bloodborne roadmap, preserved in [history](../history/ROADMAP_bloodborne_2026-09_ru.md). It targets fork `iannitram/uncharted_pc`. Current review baseline: main snapshot `68c8cf9a6563d653ed17ce72d758aaa5f33a7a76`; the fork's separate linux branch has reported working builds and must be reconciled before implementation. Dates below are proposed work windows from project kickoff, not delivery commitments. Owners are roles to assign.

## Window 1: correctness and reproducible builds (weeks 1–2)

Runtime maintainer: resolve save integrity findings [#48–53](https://github.com/iannitram/uncharted_pc/issues/48), existing #34–39, and AJM process termination #56. Renderer maintainer: triage #31–33/#37 and reproduce the current-header build failure #60. Release maintainer: establish dependency-pinned Windows/Linux CI #59. No release passes with unreported skipped runtime tests.

Deliverables: synthetic regression suite, build manifests, error propagation for saves, successful native compilation and explicit remaining failures. Exit: no known silent-save-success failures; build and test logs repeat on clean workers.

## Window 2: Windows and Linux release candidates (weeks 3–5)

| Platform | Deliverables | Dependencies | Release acceptance |
|---|---|---|---|
| Windows x86-64, Windows 10/11 | CLANG64 build recipe; staged portable ZIP; debug symbols; checksums; dependency/license manifest; update rollback and save preservation checks; direct-game Steam shortcut | #39, #54, #59, #60, #65 | U1/U2/U3 boot, save/load, executable switch, restart and controller checks; cold/warm shader runs; AMD/NVIDIA hardware smoke and 30-minute soaks; clean machine DLL check |
| Linux x86-64, SteamOS/Arch first | Reconcile linux branch without overwriting its fixes; shared Uncharted runner; reproducible build docs; portable archive/AppImage; desktop/Steam integration and symbols | #54, #59; existing #20/#41/#42 and linux branch comparison | U1/U2/U3 boot/save/load/switch/restart; RADV and NVIDIA checks; Steam Game Mode input; 20 W Phoenix handheld 30/60 Hz power and frame-time evidence; clean-system package launch |
| macOS Intel and Apple Silicon (research only) | Separate feasibility reports, unsupported-host diagnostics, synthetic ABI/TLS/mapping/fault probes, Vulkan/MoltenVK feature inventory | #55; CPU execution strategy before packaging | Architecture-specific go/no-go with reproducible smoke tests on physical Macs; no playable binary promised |

Linux branch achievements described in fork #23 are historical reports, not measured results of this checkout. Compare each existing fix before selecting commits. Windows packages remain Windows-specific; Linux artifacts must not ship DLL-centric launch paths.

## Window 3: campaign stability and power (weeks 6–8)

QA lead and renderer/runtime owners: reproduce and resolve U2 streaming (#61), chapter 21 progression (#62), U3 geometry (#63) and cutscene stalls (#64). Accept validated plain ELF inputs (#66). Review upstream idle-worker work through existing #41, retaining memory/fence ordering. Do not integrate unreviewed guest-byte patches from issue attachments.

Deliverables: per-game/per-revision chapter checklist, 30-minute streaming and save/load soaks, GPU/driver compatibility table, CPU/power and frame-time benchmarks. 60 Hz is the primary correctness target; 30 Hz is a handheld option. Above 60 FPS is not a fork objective (fork #23). Separate high-rate bug reports from supported-rate regressions.

## Window 4: quality and macOS decision (weeks 9–12, conditional)

Performance owner: shader preload (#16), bounded save matching (#57), shared preparation cache (#58), and measured draw/copy thread tuning. Product work reuses existing issues: graphics profiles #10, Xbox prompts #11, persistent trophies #12, aspect ratio #14, automated QA #15, FSR4 #18 and stereo #19. These follow correctness and require platform compatibility checks.

macOS owner: if window 2 proves a viable runtime, scope an Intel experimental build and/or Apple Silicon execution prototype separately. Deliver an experimental signed/notarized app bundle only after runtime and GPU acceptance; publish unsupported-feature limits. If feasibility fails, publish the blockers and defer playable macOS delivery rather than label a Windows/Wine bundle native.

## Release evidence required

Each candidate records commit, compiler/dependencies, OS/CPU/GPU/driver, game revision identifier (no game files), settings, cold/warm cache state, expected skips, logs and known limitations. Publish artifact checksums and third-party notices, preserve user saves/config, and test upgrade failure recovery. QA evidence includes p50/p95/p99 frame times, RSS/VRAM trend, device-lost/assertion counts and power for handhelds. Source code fixes are proposed in [the review register](../review-2026-10-24/BUG_REPORT.md).

## Mac compatibility bundle experiment

In window 2, also test the Windows release through a macOS-compatible Wine runtime and MoltenVK on physical Macs. Proton itself targets Linux. Apple Silicon needs a validated x86-64 translation path. Deliver a configuration, Vulkan feature inventory and go/no-go report; if successful, scope an experimental compatibility app in window 4 after redistribution and packaging checks. See [the feasibility assessment](../review-2026-10-24/MAC_COMPATIBILITY.md).
