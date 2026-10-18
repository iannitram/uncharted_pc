# Similar Projects and Prior Art for uncharted_pc

Research snapshot taken **2026-10-16**. Star counts, issue counts and release lists change quickly
(the upstream project is one day old), so read every number as "as of 2026-10-16". Each claim
links to its source inline. **[Unverified]** marks claims that come only from secondary
aggregators or search snippets, and **[Speculative]** marks my own inferences.

## Key takeaways for uncharted_pc

- **Upstream is one day old and flooded with crash reports.** SuperMedo's
  [uncharted_pc](https://github.com/Supermedo/uncharted_pc) shipped v0.3 → v0.3.3 on 15 Oct 2026
  ([releases](https://github.com/Supermedo/uncharted_pc/releases)) and had about 976 stars and
  146 open issues out of 154 within roughly 36 hours
  ([repo](https://github.com/Supermedo/uncharted_pc), [issues](https://github.com/Supermedo/uncharted_pc/issues?q=is%3Aissue)).
  Most reports are crashes in a handful of clusters: `m_gfxEopTick` after cutscenes, guest fault at
  `0xd9c59b` (U2/U3 start, London bar), U2 streaming `iSubMesh` assertion, VRAM OOM on 2–4 GB cards,
  Intel iGPU driver faults, and Steam Deck `vk_scheduler` assertions. A crash-signature triage table
  that maps guest offsets and assert strings to issues would give the most value for the least work.
- **VRAM-pressure fixes already exist next door.** SuperMedo's Bloodborne 1.8.2 falls back to
  system memory instead of crashing with `ErrorOutOfDeviceMemory`, and stops texture thrash
  ([release notes](https://github.com/Supermedo/bloodborne_pc/releases)). bbport 0.5-pre3/pre4 added a
  shared VRAM budget and a fix for 4 GB cards collapsing
  ([bbport releases](https://github.com/deadinside28/bloodborne_pc/releases)). Issue
  [#181](https://github.com/Supermedo/uncharted_pc/issues/181) asks for exactly this fallback.
- **shadPS4 now reaches gameplay in the collection, and its tracker records which settings it needs.**
  The compat tracker moved CUSA02344 to *ingame* in Oct 2026, using **precise readbacks**
  ([#441](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/441)). The
  CUSA02343 and CUSA02320 entries record DMA, TDR and condvar/`NdJobWorkerThread` findings
  ([#2645](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/2645),
  [#147](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/147)). A rejected
  shadPS4 PR lists three Naughty Dog-specific GPU-sync fixes: flip signal timing, a submit lock that
  waits only for the graphics ring, and unbounded `0xffffffff` descriptors
  ([PR #4882](https://github.com/shadps4-emu/shadPS4/pull/4882)). Check each against our renderer.
- **A whole family of bbport-derived "native ports" exists to borrow from.** The God of War III, inFAMOUS SS, The Last
  Guardian, Gravity Rush 2 and CTR:NF ports all share the loader + `runtime_*.c` + shadPS4-video-core
  design ([shadps4 topic](https://github.com/topics/shadps4)). Two of them add QA tools we lack:
  `--check-imports`, launcher `--selftest` in CI, a freeze reporter, a log sanitizer and per-fix
  `ISS_*` toggles ([gow3_pc](https://github.com/FelipePrado0/gow3_pc), [iss_pc](https://github.com/HayatoG/iss_pc)).
  Some of them also do instruction rewriting for CPUs without AVX2/MOVBE/BMI1 (relevant to
  [#144](https://github.com/Supermedo/uncharted_pc/issues/144) `0xC000001D` and
  [#68](https://github.com/Supermedo/uncharted_pc/issues/68)).
- **Legal and community posture matters.** Ship no game data and keep official art out. Sony's 2025
  Bloodborne takedown was reportedly about the *trademark in the page*, not the code
  ([Push Square](https://www.pushsquare.com/news/2025/02/sonys-bloodborne-60fps-mod-dmca-takedown-was-about-the-name-not-the-patch-itself)).
  shadPS4 and Zelda64Recomp restrict or ban AI-generated contributions
  ([shadPS4 CONTRIBUTING](https://github.com/shadps4-emu/shadPS4/blob/main/CONTRIBUTING.md),
  [Zelda64Recomp](https://github.com/Zelda64Recomp/Zelda64Recomp)), and press has pointed out
  upstream's heavy AI co-authorship **[Unverified, search snippet only]**. So fixes from this fork
  are unlikely to be accepted upstream into shadPS4 as-is. Expect "this is just shadPS4" criticism
  ([#21](https://github.com/Supermedo/uncharted_pc/issues/21)) and document the architecture plainly.

## Upstream uncharted_pc

**Repo:** [Supermedo/uncharted_pc](https://github.com/Supermedo/uncharted_pc). The About text
reads "Uncharted: The Nathan Drake Collection running natively on Windows - by SuperMedo".
On 2026-10-16 it had 976 stars, 47 forks, 13 watchers and 168 commits on `main`, and showed no
topics.

### Releases

All four releases are dated 15 Oct (year not shown on the page; context places it in 2026)
([releases](https://github.com/Supermedo/uncharted_pc/releases)):

| Tag | Notes (summarised) |
|---|---|
| v0.3 | First public build. All three games, one launcher, 60/120 FPS, TAA/FSR/DLSS, frame generation. Fixes U3 Cartagena GPU-lost at high FPS. |
| v0.3.1 | Tried to fix `m_gfxEopTick` by limiting CPU run-ahead to one frame. The author could not reproduce it. |
| v0.3.2 | Turns off the 0.3.1 attempt; the game now *waits* for the GPU instead of asserting. |
| v0.3.3 | Intel HD 630 black screen fixed by disabling `VK_EXT_vertex_input_dynamic_state` on Intel (`BB_VERTEX_INPUT_DYNAMIC=1` turns it back on). Recommends 6 GB VRAM. U2 streaming and U3 London-bar crashes still open. |

### Issue tracker: common themes

Every issue (#4–#187) was opened 15–16 Oct 2026. 146 are open and 8 closed
([issue list](https://github.com/Supermedo/uncharted_pc/issues?q=is%3Aissue),
[closed](https://github.com/Supermedo/uncharted_pc/issues?q=is%3Aissue+is%3Aclosed)). No maintainer
replies were visible on the issues sampled. The clusters below come from issue titles plus the
few bodies that were read:

| Cluster | Example issues | Notes |
|---|---|---|
| Crash after or around cutscenes (U1 most often), `m_gfxEopTick` | [#5](https://github.com/Supermedo/uncharted_pc/issues/5), [#61](https://github.com/Supermedo/uncharted_pc/issues/61), [#67](https://github.com/Supermedo/uncharted_pc/issues/67) (Intel Arc, 0.3.3), [#153](https://github.com/Supermedo/uncharted_pc/issues/153), [#183](https://github.com/Supermedo/uncharted_pc/issues/183) | Still reported on 0.3.3, so the 0.3.2 wait is not enough everywhere. |
| Guest fault at `0xd9c59b` (U2 and U3 openings, U3 London bar) | [#58](https://github.com/Supermedo/uncharted_pc/issues/58), [#60](https://github.com/Supermedo/uncharted_pc/issues/60), [#71](https://github.com/Supermedo/uncharted_pc/issues/71) ("texture cache overflow"), [#124](https://github.com/Supermedo/uncharted_pc/issues/124) | Listed as a known issue in the README. #42 closed as a duplicate. |
| Other guest faults | `0x581aba` [#57](https://github.com/Supermedo/uncharted_pc/issues/57); `0x4944cb` [#25](https://github.com/Supermedo/uncharted_pc/issues/25); `0x4d27ba` [#17](https://github.com/Supermedo/uncharted_pc/issues/17); U1 U-boat exec at 0x0 [#134](https://github.com/Supermedo/uncharted_pc/issues/134) | Many U1 chapter-specific crashes: [#121](https://github.com/Supermedo/uncharted_pc/issues/121), [#135](https://github.com/Supermedo/uncharted_pc/issues/135), [#140](https://github.com/Supermedo/uncharted_pc/issues/140), [#175](https://github.com/Supermedo/uncharted_pc/issues/175). |
| U2 streaming / mesh assertion | [#9](https://github.com/Supermedo/uncharted_pc/issues/9), [#70](https://github.com/Supermedo/uncharted_pc/issues/70), [#187](https://github.com/Supermedo/uncharted_pc/issues/187) (train) | README: "`iSubMesh < m_numSubMeshInstances`, white textures first". |
| VRAM / low-memory GPUs | [#93](https://github.com/Supermedo/uncharted_pc/issues/93), [#103](https://github.com/Supermedo/uncharted_pc/issues/103) (both closed), [#145](https://github.com/Supermedo/uncharted_pc/issues/145), [#181](https://github.com/Supermedo/uncharted_pc/issues/181) | #181 (MX350, 2 GB) proposes: fix the `GarbageCollectImages()` deletion-counter accounting, fall back to another memory type in `BufferCache::EnsureResident()`, log `VK_EXT_memory_budget`, and check that the requested internal resolution and upscaler preset are actually applied. |
| Intel iGPU | [#14](https://github.com/Supermedo/uncharted_pc/issues/14) (Arc iGPU), [#15](https://github.com/Supermedo/uncharted_pc/issues/15) (HD 520, fault inside `igvk64.dll`), [#56](https://github.com/Supermedo/uncharted_pc/issues/56) (HD 630, fixed in 0.3.3) | |
| Steam Deck / Proton / AMD | [#80](https://github.com/Supermedo/uncharted_pc/issues/80) | U1/U2 hit `vk_scheduler.h:771 ReserveRecordData`; U3 hits `vk_scheduler.cpp:556 SubmitExecution` "Device lost during submit". |
| Old CPUs / instruction set | [#68](https://github.com/Supermedo/uncharted_pc/issues/68) (AVX2?), [#144](https://github.com/Supermedo/uncharted_pc/issues/144) (`0xC000001D` illegal instruction, i7-3770) | Sibling ports rewrite missing instructions (see [Other native PS4 game ports](#other-native-ps4-game-ports)). |
| DLSS dependency | [#148](https://github.com/Supermedo/uncharted_pc/issues/148): won't start on a GPU without DLSS even with DLSS off | SuperMedo's Bloodborne 1.7.8 added "fall back to running without DLSS if the NVIDIA driver fails" ([notes](https://github.com/Supermedo/bloodborne_pc/releases)). |
| Graphics glitches | blue textures U1 [#157](https://github.com/Supermedo/uncharted_pc/issues/157), [#171](https://github.com/Supermedo/uncharted_pc/issues/171); clipping [#182](https://github.com/Supermedo/uncharted_pc/issues/182); shadows flicker [#24](https://github.com/Supermedo/uncharted_pc/issues/24); U2 ADS blur [#173](https://github.com/Supermedo/uncharted_pc/issues/173); U3 white screen [#184](https://github.com/Supermedo/uncharted_pc/issues/184) | |
| Audio | MP3 decode crash in U3 [#155](https://github.com/Supermedo/uncharted_pc/issues/155); stutter [#74](https://github.com/Supermedo/uncharted_pc/issues/74); no 5.1 [#133](https://github.com/Supermedo/uncharted_pc/issues/133), [#178](https://github.com/Supermedo/uncharted_pc/issues/178) | |
| Feature requests | Linux [#59](https://github.com/Supermedo/uncharted_pc/issues/59), [#83](https://github.com/Supermedo/uncharted_pc/issues/83), [#179](https://github.com/Supermedo/uncharted_pc/issues/179); ultrawide [#8](https://github.com/Supermedo/uncharted_pc/issues/8); launcher-less shortcuts [#147](https://github.com/Supermedo/uncharted_pc/issues/147); ZArchive [#142](https://github.com/Supermedo/uncharted_pc/issues/142); single-game dumps [#185](https://github.com/Supermedo/uncharted_pc/issues/185); vibration toggle [#136](https://github.com/Supermedo/uncharted_pc/issues/136); KB prompts [#139](https://github.com/Supermedo/uncharted_pc/issues/139); HDR brightness [#65](https://github.com/Supermedo/uncharted_pc/issues/65) | |
| Launcher art | [#143](https://github.com/Supermedo/uncharted_pc/issues/143) asks to replace "AI generated" launcher images | The README says the default covers are original artwork. |

Region and version: several crashes are tagged CUSA02320 (US) v1.02. The README says the U2
streaming crash and the U3 London-bar crash were "both seen on the US version 1.02". The
Spanish-voice selection bug on EU CUSA02343 ([#73](https://github.com/Supermedo/uncharted_pc/issues/73))
was closed.

### Reception

- **The "is it really native?" debate**
  ([#21 "This is just ShadPS4"](https://github.com/Supermedo/uncharted_pc/issues/21)). A
  graphics-driver developer (K0bin) argues that it is "an emulator fork with slopped hacks to make
  one game faster". He points out that shadPS4 also runs PS4 x86 code natively. A user reports
  about 200 FPS vs about 77 FPS in shadPS4 (precise readbacks) in the same scene. No maintainer
  reply was visible.
- **Press.** The search engine surfaced coverage from VGTimes, iXBT.games (15 Oct 2026),
  TechNetBooks, a Brazilian site and Emulation King, plus a Portuguese YouTube video
  ([VGTimes](https://vgtimes.com/gaming-news/171227-uncharted-the-nathan-drake-collection-gets-an-unofficial-pc-port.html),
  [iXBT](https://ixbt.games/en/news/2026/10/15/sony-ne-smogla-a-fanaty-sami-vypustili-na-pk-trilogiiu-ps-ekskliuzivov-uncharted-the-nathan-drake-collection.html),
  [Emulation King](https://emulationking.com/sony/ps4/games/unchartedcollection/ports/unchartedpc/),
  [YouTube](https://www.youtube.com/watch?v=tDL38F2Qjc0)). **None of these sites were reachable
  from this environment (DNS failure)**, so their content is known only from search snippets. One
  snippet says Emulation King notes that "an AI coding tool is credited as co-author on 137 of the
  repository's 160 commits" **[Unverified]**.
- **Reddit and ResetEra** could not be reached (connection failure) and turned up nothing in
  search. **No reception data was gathered from them.**
- **Mindro.** The README thanks "Mindro for the shadPS4 Uncharted build". Issue
  [#4](https://github.com/Supermedo/uncharted_pc/issues/4) is from ManoharPadul ("mindro"), who says
  he is "building native port of uncharted" and asks people to contact him on Discord. No public
  repo was found.
- **Announced plans.** There is no public roadmap. The releases and README only list issues being
  "looked at" (U2 streaming, U3 London bar).

## Upstream Bloodborne ports (bbport and SuperMedo Windows)

### deadinside28/bloodborne_pc (bbport, Linux)

- On 2026-10-16: about 3.0k stars, 712 forks, 104 open issues, 25 open PRs and 150 commits
  ([repo](https://github.com/deadinside28/bloodborne_pc)). Latest stable is **0.51 (10 Oct)**;
  **0.6-pre1 (15 Oct)** is a pre-release
  ([releases](https://github.com/deadinside28/bloodborne_pc/releases)). Press coverage dates the
  first wide attention to about 4 Oct 2026
  ([iXBT](https://ixbt.games/en/news/2026/10/04/bloodborne-portirovali-a-pk-igra-zapuskaetsia-bez-emuliatora.html),
  reachable only via search snippet).
- **Architecture** ([README](https://github.com/deadinside28/bloodborne_pc)): the eboot is converted
  offline into a flat image with PS4 libc and libSceFios2 linked in as native code. A C loader maps
  it and jumps in, with no CPU emulation. `src/runtime_*.c` implements only the OS calls the game
  uses. The renderer is the shadPS4 video core and shader recompiler with about 200 marked changes.
  Two memory models exist: the old one is the default on NVIDIA/Intel, and the new one (game memory
  in system RAM, GPU reads it in place) is the default on AMD and became the default everywhere in
  0.6-pre1. The README describes it as "Wine + DXVK for a single game".
- **Release cadence** (Oct 2026, [releases](https://github.com/deadinside28/bloodborne_pc/releases)):
  - 0.4 (7 Oct): FSR 4.1.1 FP8 and an experimental memory model.
  - 0.5-pre1 to pre4 (8–9 Oct): VRAM budget shared between textures and copies, a fix for 4 GB
    cards collapsing, NVIDIA streaming stutter reduced, a portable GPU completion-label path, and
    detection of damaged extractions.
  - 0.5 (10 Oct): background pipeline compilation.
  - 0.51 (10 Oct): online play via a shadNet module, and an AppImage shrunk from 925 to 399 MB.
  - 0.6-pre1 (15 Oct): seamless co-op (BBSC) and any aspect ratio.
- **Roadmap** ([README](https://github.com/deadinside28/bloodborne_pc)): make the new memory model
  the default on NVIDIA and then remove the old one; create textures at load time; translate shaders
  ahead of time at install; more CPU parallelism (aimed at Steam Deck); async compute for the
  upscaler; XeSS/XeFG via a Wine helper; HDR; validating the Deck AppImage.
- **Issues** ([tracker](https://github.com/deadinside28/bloodborne_pc/issues)): regressions in
  0.6/new memory model (#203 Polaris, #200 VRAM grows across area loads until OOM on an RX 6750 XT,
  #204 slow on an RTX 4060 Laptop), AppImage/NVIDIA library linking (#205), and an NVIDIA Xid 109
  hang when DoF and motion blur are both on (#184). Issue #222 is an owner note asking that
  comments stay about this project, not forks.
- **Known gaps** ([README](https://github.com/deadinside28/bloodborne_pc)): `IT_SET_PREDICATION`
  is unimplemented, occlusion queries use synthetic counters, and only one machine (an RX 7800 XT
  on RADV) has been tested thoroughly.

### Supermedo/bloodborne_pc (Windows)

- On 2026-10-16: about 3.2k stars, 203 forks and 308 commits on the `windows` branch. The issue
  tab showed nothing when fetched signed-out ([repo](https://github.com/Supermedo/bloodborne_pc)).
  Latest release **1.8.2 (15 Oct)** ([releases](https://github.com/Supermedo/bloodborne_pc/releases)).
- **Fixes in recent releases that apply directly to Uncharted**
  ([releases](https://github.com/Supermedo/bloodborne_pc/releases)):
  - 1.8.2: use system memory when VRAM fills on 4–8 GB cards instead of `ErrorOutOfDeviceMemory`;
    stop discarding and reloading textures every few frames; fix the "Out of order flip IRQ" crash;
    fix read-only and USB/exFAT game folders.
  - 1.7.8: fall back to no DLSS if the NVIDIA driver fails.
  - 1.7.7: skip "Unimplemented PM4 type 0" instead of stopping; log GPU, VRAM and driver version.
  - 1.7.3: fix crash from an empty-pointer draw; fix `PermissionError` when antivirus locks files;
    warn when eboot.bin is modified.
  - 1.7.2: fix "Device lost during submit" on AMD RX 6000 and older by turning off object motion
    (`BB_OBJECT_MOTION=1` turns it back on).
- **README claims** ([repo](https://github.com/Supermedo/bloodborne_pc)): launcher in 13
  languages, one-click updates that keep saves and mods, a cheats page, online (beta) via The
  Hunter's Dream/shadNet, and best-effort translation on pre-Haswell Intel. Known problems listed:
  some AMD cards may crash when the world loads, and some rare instructions are not translated on
  old Intel CPUs.
- **Other forks:** [visy/bloodborne_pc_windows_port](https://github.com/visy/bloodborne_pc_windows_port)
  (seamless co-op) and [0xCydral/bloodborne_pc](https://github.com/0xCydral/bloodborne_pc)
  ([topic listing](https://github.com/topics/shadps4)).

**For uncharted_pc:** the 1.7.x–1.8.2 fixes and bbport's 0.5-pre memory/VRAM work should be
reviewed first and cherry-picked where they apply. Both projects share our code ancestry, so the
diffs should port with little change **[Speculative: not diffed]**.

## shadPS4

- **Status:** about 33.6k stars, 4,476 commits, GPL-2.0. Windows, Linux and macOS 26+ (no Intel
  Macs). The README still says it is "early in development". It is now core-only, and the README
  recommends the separate QtLauncher. Users supply firmware `.sprx` modules in `sys_modules`
  ([repo](https://github.com/shadps4-emu/shadPS4)).
- **2026 releases** ([releases](https://github.com/shadps4-emu/shadPS4/releases)):

| Version | Date | Highlights |
|---|---|---|
| v0.14.0 | 7 Feb | Global state class, key manager, CLI11 parser, new LLE modules (RTC, JPEG/PNG). |
| v0.15.0 | 17 Mar | kqueue/kevent support and guest signal handlers. |
| v0.16.0 | 1 Jun | New config system, OpenAL backend, camera, local multiplayer, Big Picture Mode. |
| v0.17.0 | 30 Jul | First shadNet, ZArchive support, sceMouse. |
| v0.18.0 | 18 Aug | AvPlayer as LLE, event-flag rewrite, **experimental Windows red-zone protection for Intel 12th-gen+**, `--mount`. |
| v0.19.0 | 2 Oct | Many GPU and shader-recompiler fixes, DLC as ZAR. |
| v0.20.0 | 14 Oct | shadNet 0.1.0, networking/P2P rework; online Bloodborne declared playable. |

  A nightly pre-release followed on 16 Oct. v0.13.0 (24 Dec 2025) had a "Bloodborne speedup
  fix", AJM fixes and an initial pipeline cache.
- **Architecture notes:** guest x86-64 runs natively on the host. The README credits Panda3DS for
  help with "natively executing the x64 code of PS4 binaries", and the shader recompiler is modelled
  on yuzu's Hades ([README](https://github.com/shadps4-emu/shadPS4)). So the CPU side is
  conceptually the same as bbport. The real differences are bbport's offline flat-image prep,
  per-game HLE written only for the calls each game makes, and game-specific renderer changes. This
  supports the point made in [#21](https://github.com/Supermedo/uncharted_pc/issues/21).
- **Bloodborne history:**
  - 2024: first in-game screenshots, then reaches Castle Cainhurst at single-digit FPS
    ([DSOGaming](https://www.dsogaming.com/pc-performance-analyses/first-screenshots-of-bloodborne-on-pc-via-the-shadps4-emulator/),
    [Notebookcheck](https://www.notebookcheck.net/Bloodborne-PC-emulation-achieves-major-milestone.877308.0.html)).
  - Dec 2025: reported "fully playable", with an online demo ahead of shadNet
    ([Wccftech](https://wccftech.com/bloodborne-pc-online-play-is-no-longer-a-dream-shadps4-developer-showcases-working-multiplayer-milestone/amp/)).
  - Oct 2026: official online play in v0.20.0.
  - Community add-ons such as DLSS/FSR (IFreemz), which uncharted_pc reuses, and seamless co-op
    (BBSC) ([topic](https://github.com/topics/shadps4)).
  - These articles were found via search and not re-fetched here.
- **Uncharted compatibility entries** ([search](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues?q=uncharted)):

| Entry | Serial | OS | Status | Key findings |
|---|---|---|---|---|
| [#441](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/441) | CUSA02344 | Windows | **ingame** (since 2 Oct 2026) | 2025: crash in `emit_spirv_context_get_set.cpp:169`. Oct 2026 (v0.19/v0.20): about an hour of play with **precise readbacks**, glitchy lighting in the U1 temple, missing gunshot audio. Labels include `experimental:red-zone-protection`. |
| [#2645](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/2645) | CUSA02343 | Windows | menus | v0.16: "Device lost waiting for frame", DMA gets it to the menu. v0.17: `buffer_cache.cpp:434 FindBuffer` assert after a cutscene. v0.19: invisible scene after the first cutscene unless readbacks are Precise; Relaxed is worse. Tip: base and update PARAM.SFO/PLAYGO must be in `sce_sys/`. Tip: TDR registry delay for device-lost under heavy load. |
| [#147](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/147) | CUSA02320 | Linux | ingame | Needs DMA. U3: write AV at 0x0 in `NdJobWorkerThread`, then `condvar.cpp` "Unreachable". U2: `condvar` crash in a cinematic; skipping it reaches the train at about 5 FPS. U1: AV after the intro cutscene. |
| [#71](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/71) | CUSA02320 | Windows | nothing | crashes |
| [#477](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/477) | CUSA02826 | Linux | menus | `UC:signals` |
| [#1000](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/1000), [#267](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/267) | CUSA02320, CUSA01399 | macOS | nothing | |
| [#1419](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/1419) | CUSA03331 (demo) | Windows | boots | |
| [#2689](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/2689), [#3110](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/3110) | CUSA03281 (U2 standalone), CUSA03280 (U1 standalone) | Windows | ingame / untriaged | Standalone remasters with the same engine. Useful for cross-checking. |

- **Uncharted-specific PRs:** [PR #4882](https://github.com/shadps4-emu/shadPS4/pull/4882)
  (sergek88, closed unmerged on 20 Aug 2026 under the AI-use rules) proposed three fixes:
  1. `sceGnmSubmitDone` waits up to 2 s for the **graphics ring only**, because Naughty Dog parks
     compute rings indefinitely.
  2. Fire the flip event after the frame's EOP fence write, at the end of the DCB.
  3. Skip GPU-modified marking for descriptors with `num_records = 0xffffffff` and sync only a
     16 MiB window.

  The author reported the intro going from about 35 min to about 41 s. The follow-up
  [PR #5140](https://github.com/shadps4-emu/shadPS4/pull/5140) ("Signal the flip after the whole
  flip DCB has executed") was still open in Sept 2026 (per the PR #4882 page). Items 2 and 3 look
  related to our `m_gfxEopTick` and VRAM/sync problems **[Speculative]**.
- **Contribution policy:** AI use must be disclosed, descriptions must be human-written, and
  contributors must be able to explain every decision
  ([CONTRIBUTING.md](https://github.com/shadps4-emu/shadPS4/blob/main/CONTRIBUTING.md)).

**For uncharted_pc:**
- Use the compat entries as an external regression list (scenes, asserts).
- Test whether the "precise readbacks" result corresponds to anything in our readback mode.
- Evaluate the three PR #4882 ideas against our EOP/flip path.
- Watch shadPS4's red-zone protection for Intel 12th-gen+ on Windows: native execution plus
  Windows exception handling can clobber the SysV red zone **[Speculative about relevance; worth
  checking against Intel-only crash reports]**.

## Other PS4 emulators and compatibility layers

| Project | Approach | State (Oct 2026) | Relevance |
|---|---|---|---|
| [fpPS4](https://github.com/red-prig/fpPS4) | Free Pascal/Lazarus compatibility layer; Vulkan; needs AVX2 | About 2.1k stars. "Early stages", large commercial games don't run. Core is being rewritten in the `kern` branch. Separate [compat tracker](https://github.com/red-prig/fpps4-game-compatibility/issues). | Low: different language, not running AAA games. |
| [Obliteration](https://github.com/obhq/obliteration) | Rust reimplementation of the PS4 kernel inside its own hypervisor (WHP/KVM/Hypervisor.framework); aims to run dumped system software (LLE). Started as a Kyty fork. | About 820 stars. **No games run yet**; sample log stops at a kernel panic during process creation. | Opposite end of the spectrum (full-system LLE); little to reuse. |
| [Kyty](https://github.com/InoriRus/Kyty) | HLE PS4/PS5 emulator, Windows, Vulkan | About 3.2k stars, 49 commits on `main`; "some simple games". No audio, MP4 or networking. | Low. |
| [GPCS4](https://github.com/Inori/GPCS4) | HLE; PM4 → Gnm reconstruction → Vulkan; GCN → SPIR-V; calls host libs for pure functions | About 2.0k stars. First commercial game (*We Are Doomed*) not playable; "for fun and research". | Historical. The "recover Gnm calls from PM4" idea is a useful mental model for debugging. |
| Spine | Closed-source, Linux-only, "Wine-like" layer that runs PS4 x86 directly. Last version 20220517; inactive ([Emulation General Wiki](https://emulation.gametechwiki.com/index.php/Spine), [GamingOnLinux](https://gamingonlinux.com/2021/09/ps4-emulator-spine-gets-a-new-demo-release)) | Mostly small 2D titles ran **[via search snippet]**. | The conceptual ancestor of "native execution + replacement OS libs" that bbport carries out per game. |
| [Bachata S4](https://github.com/JICA98/Bachata-S4) | shadPS4 core on Android ARM64 + FEX for x86-64 + Turnip/Vortek Vulkan | Nine games in the tracker (six ingame). | **Its compatibility-reporting scheme is worth copying:** one canonical issue per game, reports tied to release/device/driver, structured data in a separate repo. |

**How bbport-style ports differ:** shadPS4, Kyty, GPCS4 and fpPS4 are general HLE emulators that
already run guest x86 natively. Obliteration virtualises the real OS. Spine and the bbport family
specialise: per-game prep of the executable, a runtime that implements only the imports one game
needs, and renderer hacks that are acceptable because only one title must work. That
specialisation is why sibling ports can beat shadPS4 on speed. It is also why they inherit
shadPS4's GPU-translation bugs (the README notes the U3 green/black flashes "happen in shadPS4
too").

## Static recompilation and decompilation ports

| Project | What | Notes relevant here |
|---|---|---|
| [N64Recomp](https://github.com/N64Recomp/N64Recomp) → [Zelda64Recomp](https://github.com/Zelda64Recomp/Zelda64Recomp) | MIPS → C; N64ModernRuntime; RT64 renderer | About 8.3k / 7.4k stars. Users load their own US ROM in the in-game menu and assets are read at runtime. Mods are dropped onto the window or installed from a mod menu, with a mod template and docs; randomizer ships as a mod. GPL-3.0 game repo. **No generative AI allowed in contributions.** |
| [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) → [Unleashed Recompiled](https://github.com/hedge-dev/UnleashedRecomp) | Xbox 360 PPC → C++; no runtime included | About 6.6k / 5.2k stars. Unleashed's **installer accepts raw containers or folders and validates integrity**: it rejects compressed archives, mixed regions and modified files. Built-in mod loader (Hedge Mod Manager format), achievements, new D3D12/Vulkan renderer with async shader compilation. "Does not include any game assets." |
| [ps3recomp](https://github.com/sp00nznet/ps3recomp) | PS3 PPU/SPU → C; about 93 HLE modules written from documented behaviour, with RPCS3 as a *behavioural reference only* ("no RPCS3 GPL code in tree"); D3D12/Metal/Vulkan | MIT. **CI includes a regression gate that checks five ports against recorded goldens before shared-runtime changes land**, plus lavapipe Vulkan runs. Ports: Simpsons Arcade (in-game), Twisted Metal, GT5 Prologue and others ([search](https://github.com/search?q=ps3recomp&type=repositories)). |
| [U3-PS3Recomp](https://github.com/snozzy8z/U3-PS3Recomp) | **Uncharted 3 (PS3, BCES01175) static recomp** on ps3recomp | Four commits, four stars. Boot and loading screen render; **main menu not reached**, blocked on the SPU/SPURS asset-decode path. Same game as our U3, different platform and binary. |

**Lessons that transfer:**
1. **Asset/dump pipeline:** validate the dump up front. Check region, version, required files and
   modified eboot, as Unleashed does and as SuperMedo Bloodborne 1.7.3 started to with eboot
   warnings. Give a clear error instead of an in-game crash. The shadPS4 tip that base + update
   `PARAM.SFO`/`PLAYGO` must be in `sce_sys/`
   ([#2645](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/2645)) is the
   kind of check that belongs here. ZArchive input ([#142](https://github.com/Supermedo/uncharted_pc/issues/142))
   is already supported by shadPS4 v0.17.
2. **Mods:** a stable mod format and a mod loader that never touches game files (Zelda64Recomp,
   Unleashed). uncharted_pc already has `docs/MODS.md`; their manager-compatible formats are
   models to follow.
3. **Legal posture:** every successful project in this class ships code only, makes users supply
   their own dump, and avoids trademarked art. Sony's 2025 Bloodborne takedown targeted a page
   using the name, not the code
   ([Push Square](https://www.pushsquare.com/news/2025/02/sonys-bloodborne-60fps-mod-dmca-takedown-was-about-the-name-not-the-patch-itself),
   [PC Gamer](https://www.pcgamer.com/games/action/sony-bullies-bloodborne-60fps-mod-off-the-internet-with-dmca-takedown-as-it-continues-to-let-the-fromsoft-classic-gather-dust-on-ps4/)).
   ps3recomp's "behavioural reference, no copied GPL code" stance shows how to keep licences clean.
   Here we *are* GPL, inherited from shadPS4.
4. **Test methodology:** golden-output regression gates across ports (ps3recomp) map well onto
   scripted-pad replays (`BB_PAD_FILE`) with frame-hash or log-signature goldens per game and
   chapter **[Speculative design]**.
5. **Why recompilation is not needed here:** PS4 code is already x86-64, so a translator adds no
   speed. The recomp projects' value to us is their tooling and process, not their translation
   approach.

## Other native PS4 game ports

From the [GitHub `shadps4` topic](https://github.com/topics/shadps4) on 2026-10-16 (35 repos, the
first 20 inspected), a wave of bbport-derived single-game ports appeared in Oct 2026:

| Port | Game | Base | Useful bits |
|---|---|---|---|
| [FelipePrado0/gow3_pc](https://github.com/FelipePrado0/gow3_pc) (about 2.9k stars, 174 open issues) | God of War III Remastered (CUSA01623/01715) | SuperMedo's Windows bbport + shadPS4 video core with fixes from cuesta4's `eltutz` branch | **`--check-imports`** (checks all system imports without starting gameplay); Python `unittest` + C++ Ninja test targets on Windows/Linux; instruction rewriting for CPUs without MOVBE/BMI1/LZCNT; save import from shadPS4; automatic rule for MSAA black lines on AMD/Intel; ultrawide beta; Linux AppImage. |
| [HayatoG/iss_pc](https://github.com/HayatoG/iss_pc) | inFAMOUS Second Son (CUSA00223) | Shared core with HayatoG's [tlg_pc](https://github.com/HayatoG/tlg_pc) and [gr2_pc](https://github.com/HayatoG/gr2_pc), plus gow3_pc and bloodborne_pc | **Launcher `--selftest` run in GitHub Actions**; freeze reporter that dumps threads after 10 s without a frame; log `Config:` block plus a report tool that strips personal paths; 12 experimental fixes (BP01–BP12) taken from other ports, each with a switch and a "Recommended" profile; `ISS_*` diagnostic toggles; Windows red-zone protection; instruction rewriting. Known issue: Polaris crash on Windows; compare our RX 580 report [#81](https://github.com/Supermedo/uncharted_pc/issues/81). |
| [GetLostIn/CTR-NitroFueled-PC](https://github.com/GetLostIn/CTR-NitroFueled-PC) | Crash Team Racing: Nitro-Fueled (CUSA13795) | Windows fork of SacredFire (T3CHNOLOG1C's Linux port) on bbport; Windows layer from SuperMedo | Community patches compiled at startup; experimental background shader compilation. On Steam Deck it is limited by the GPU command thread (37–45 FPS). |
| [SotC-project/sotc-pc](https://github.com/SotC-project/sotc-pc), [SotC-project/i3-pc](https://github.com/SotC-project/i3-pc) | Shadow of the Colossus, inFAMOUS SS | Custom shadPS4 builds (game-tuned emulator, not bbport) | Shows the alternative "game-specific shadPS4 fork" route. |
| [Prathewsh/gravityrush_pc](https://github.com/Prathewsh/gravityrush_pc) | Gravity Rush Remastered / 2 | "Experimental native runtime" | |

Also: [IFreemz/shadPS4-Bloodborne-DLSS-FSR](https://github.com/IFreemz/shadPS4-Bloodborne-DLSS-FSR)
(source of our Videodec2 and DLSS bridge) and [Classmg22/BBSC](https://github.com/Classmg22/BBSC)
(seamless co-op). No other public Uncharted PS4 native port was found besides SuperMedo's.
Mindro's is announced but no repo was located.

**For uncharted_pc:** this ecosystem shares one code ancestry and moves daily. The cheapest wins
are:
- the CPU instruction-rewriting layer, which fixes `0xC000001D` on Ivy Bridge and other old CPUs;
- `--check-imports`;
- the freeze/thread-dump reporter and the privacy-scrubbed report tool, which would make the 150+
  issue reports far more actionable;
- per-fix toggles with a "Recommended" profile.

The GPL on all of them makes code reuse straightforward if attribution is kept
**[Speculative: licence compatibility should be confirmed per file]**.

## What to reuse: summary matrix

| Need in uncharted_pc | Best source | Type of reuse |
|---|---|---|
| VRAM OOM on 2–6 GB GPUs | SuperMedo Bloodborne 1.8.2; bbport 0.5-pre3/pre4; issue #181 analysis | Code cherry-pick |
| `m_gfxEopTick` / flip timing | shadPS4 PR #4882 and PR #5140 ideas; bbport "portable GPU completion-label path" (0.5-pre2) | Technique |
| Steam Deck / AMD device lost | SuperMedo Bloodborne 1.7.2 (object-motion off on RDNA2 and older) | Technique + toggle |
| DLSS-less start failure (#148) | SuperMedo Bloodborne 1.7.8 DLSS fallback | Code |
| Old CPUs (#144, #68) | gow3_pc / iss_pc instruction rewriting; SuperMedo Bloodborne "best-effort translation" | Code |
| Intel 12th-gen+ oddities | shadPS4 v0.18 red-zone protection | Technique |
| Bug report quality | iss_pc freeze reporter + path-scrubbing report tool; Bloodborne 1.7.7 GPU/driver logging | Code |
| Dump validation | Unleashed Recompiled installer; shadPS4 `sce_sys` tip; Bloodborne eboot-modified warning | Technique |
| Compat tracking | shadPS4 compat repo format; Bachata S4 canonical-issue + structured data repo | Process |
| Regression testing | ps3recomp golden gate; iss_pc `--selftest` in CI; gow3_pc `--check-imports` | Process |
| Mods | Zelda64Recomp mod menu/template; Unleashed mod loader | Design |

## Method and limitations

- Sources were fetched on 2026-10-16. GitHub web pages were reachable. **The GitHub REST API
  returned 403** and `gh` was not authorised for these repos, so issue data comes from the HTML
  issue lists (titles and dates), plus individual issue pages for #4, #21, #80 and #181.
- **These sites were unreachable (DNS/connection failure):** emulationking.com, vgtimes.com,
  ixbt.games, bloodbornepc.wiki, generationamiga.com, en.wikipedia.org, reddit.com,
  shadps4.net. Claims attributed to them come from search-engine snippets and are marked
  **[Unverified]** where it matters. ResetEra and YouTube comments were not reviewed.
- Star and issue counts were read from a model-summarised rendering of GitHub pages and may be
  slightly off.

## Sources

- Supermedo/uncharted_pc: [repo](https://github.com/Supermedo/uncharted_pc) · [releases](https://github.com/Supermedo/uncharted_pc/releases) · [issues](https://github.com/Supermedo/uncharted_pc/issues?q=is%3Aissue) · [closed](https://github.com/Supermedo/uncharted_pc/issues?q=is%3Aissue+is%3Aclosed) · [#4](https://github.com/Supermedo/uncharted_pc/issues/4) · [#21](https://github.com/Supermedo/uncharted_pc/issues/21) · [#80](https://github.com/Supermedo/uncharted_pc/issues/80) · [#181](https://github.com/Supermedo/uncharted_pc/issues/181)
- Supermedo/bloodborne_pc: [repo](https://github.com/Supermedo/bloodborne_pc) · [releases](https://github.com/Supermedo/bloodborne_pc/releases)
- deadinside28/bloodborne_pc: [repo](https://github.com/deadinside28/bloodborne_pc) · [releases](https://github.com/deadinside28/bloodborne_pc/releases) · [issues](https://github.com/deadinside28/bloodborne_pc/issues)
- shadPS4: [repo](https://github.com/shadps4-emu/shadPS4) · [releases](https://github.com/shadps4-emu/shadPS4/releases) · [CONTRIBUTING.md](https://github.com/shadps4-emu/shadPS4/blob/main/CONTRIBUTING.md) · [PR #4882](https://github.com/shadps4-emu/shadPS4/pull/4882) · [PR #5140](https://github.com/shadps4-emu/shadPS4/pull/5140)
- shadPS4 compatibility: [Uncharted search](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues?q=uncharted) · [#441](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/441) · [#2645](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/2645) · [#147](https://github.com/shadps4-compatibility/shadps4-game-compatibility/issues/147)
- Bloodborne on shadPS4 press: [DSOGaming](https://www.dsogaming.com/pc-performance-analyses/first-screenshots-of-bloodborne-on-pc-via-the-shadps4-emulator/) · [Notebookcheck](https://www.notebookcheck.net/Bloodborne-PC-emulation-achieves-major-milestone.877308.0.html) · [Wccftech](https://wccftech.com/bloodborne-pc-online-play-is-no-longer-a-dream-shadps4-developer-showcases-working-multiplayer-milestone/amp/)
- Other emulators: [fpPS4](https://github.com/red-prig/fpPS4) · [Obliteration](https://github.com/obhq/obliteration) · [Kyty](https://github.com/InoriRus/Kyty) · [GPCS4](https://github.com/Inori/GPCS4) · [Spine (Emulation General Wiki)](https://emulation.gametechwiki.com/index.php/Spine) · [Spine (GamingOnLinux)](https://gamingonlinux.com/2021/09/ps4-emulator-spine-gets-a-new-demo-release) · [Bachata S4](https://github.com/JICA98/Bachata-S4)
- Recompilation: [N64Recomp](https://github.com/N64Recomp/N64Recomp) · [Zelda64Recomp](https://github.com/Zelda64Recomp/Zelda64Recomp) · [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) · [UnleashedRecomp](https://github.com/hedge-dev/UnleashedRecomp) · [ps3recomp](https://github.com/sp00nznet/ps3recomp) · [U3-PS3Recomp](https://github.com/snozzy8z/U3-PS3Recomp) · [ps3recomp repo search](https://github.com/search?q=ps3recomp&type=repositories)
- Sibling native ports: [shadps4 topic](https://github.com/topics/shadps4) · [gow3_pc](https://github.com/FelipePrado0/gow3_pc) · [iss_pc](https://github.com/HayatoG/iss_pc) · [tlg_pc](https://github.com/HayatoG/tlg_pc) · [gr2_pc](https://github.com/HayatoG/gr2_pc) · [CTR-NitroFueled-PC](https://github.com/GetLostIn/CTR-NitroFueled-PC) · [sotc-pc](https://github.com/SotC-project/sotc-pc) · [visy/bloodborne_pc_windows_port](https://github.com/visy/bloodborne_pc_windows_port) · [IFreemz DLSS/FSR](https://github.com/IFreemz/shadPS4-Bloodborne-DLSS-FSR)
- Legal context: [Push Square](https://www.pushsquare.com/news/2025/02/sonys-bloodborne-60fps-mod-dmca-takedown-was-about-the-name-not-the-patch-itself) · [PC Gamer](https://www.pcgamer.com/games/action/sony-bullies-bloodborne-60fps-mod-off-the-internet-with-dmca-takedown-as-it-continues-to-let-the-fromsoft-classic-gather-dust-on-ps4/)
- Press on uncharted_pc (unreachable here; search snippets only): [VGTimes](https://vgtimes.com/gaming-news/171227-uncharted-the-nathan-drake-collection-gets-an-unofficial-pc-port.html) · [iXBT.games](https://ixbt.games/en/news/2026/10/15/sony-ne-smogla-a-fanaty-sami-vypustili-na-pk-trilogiiu-ps-ekskliuzivov-uncharted-the-nathan-drake-collection.html) · [Emulation King](https://emulationking.com/sony/ps4/games/unchartedcollection/ports/unchartedpc/) · [TechNetBooks](https://www.technetbooks.com/2026/10/uncharted-nathan-drake-collection.html) · [Gameplayscassi](https://gameplayscassi.com.br/noticias/uncharted-the-nathan-drake-collection-recebe-port-nativo-nao-oficial-para-pc/134272/) · [YouTube](https://www.youtube.com/watch?v=tDL38F2Qjc0) · [iXBT on bbport](https://ixbt.games/en/news/2026/10/04/bloodborne-portirovali-a-pk-igra-zapuskaetsia-bez-emuliatora.html)
