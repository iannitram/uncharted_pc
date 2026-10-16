# Research

Background research behind the [roadmap](../docs/ROADMAP.md), collected on 2026-10-16, the day
after the first Uncharted releases (0.3 to 0.3.3). Every report links its sources inline and
marks claims it could not verify. The upstream issue tracker, prices and versions change fast,
so read the numbers as "as of 2026-10-16".

| Report | What it covers | Start with |
|---|---|---|
| [codebase-architecture.md](codebase-architecture.md) | How the port works (launcher → `run.py` → preparation scripts → `bb-probe` → C runtime → GPU library), what is Uncharted and what is left over from Bloodborne, build and tests, technical debt, a prioritised improvement list | [Key takeaways](codebase-architecture.md#key-takeaways), [Improvement candidates](codebase-architecture.md#improvement-candidates) |
| [uncharted-collection-technical.md](uncharted-collection-technical.md) | The PS4 collection itself: Bluepoint's remaster, versions and title IDs, Naughty Dog's fiber job system and three-frame pipeline, Uncharted on shadPS4, lessons from the official PC ports, and each known problem mapped to research | [Known problems mapped to research](uncharted-collection-technical.md#known-problems-mapped-to-research) |
| [graphics-upscaling-and-performance.md](graphics-upscaling-and-performance.md) | FSR 3.1/4, DLSS, XeSS on Vulkan; frame pacing and latency; shader compilation stutter; VRAM pressure on 4 GB cards; Intel iGPU drivers; NaN and flicker bugs in shader translation | [Key takeaways](graphics-upscaling-and-performance.md#key-takeaways-for-uncharted_pc) |
| [similar-projects.md](similar-projects.md) | The upstream ports (uncharted_pc, the Bloodborne ports) and their issue trackers, shadPS4, other PS4 emulators, static recompilation projects, other single-game PS4 ports, and what to reuse from each | [What to reuse](similar-projects.md#what-to-reuse-summary-matrix) |
| [legal-licensing-distribution.md](legal-licensing-distribution.md) | Licence compatibility of everything in the release zip (DLSS, FFmpeg, FSR 4 assets), Sony's and other publishers' enforcement history, risk factors, updater security, Steam | [Recommended actions](legal-licensing-distribution.md#recommended-actions) |
| [porting-candidates.md](porting-candidates.md) | The worklist of fixes from SuperMedo's Bloodborne port (same engine code, 1.7 to 1.8.2) and from shadPS4, with whether each applies cleanly here | [Engine fixes](porting-candidates.md#engine-fixes-from-the-bloodborne-port) |

## The findings that shaped the roadmap

1. **Most user reports fall into a few crash groups:**
   - the `m_gfxEopTick` assertion;
   - guest faults at `0xd9c59b`;
   - the U2 `iSubMesh` streaming assertion;
   - out of video memory on 2–4 GB cards;
   - Intel iGPU driver faults.

   Each has a concrete lead
   ([similar-projects](similar-projects.md#upstream-uncharted_pc),
   [known problems](uncharted-collection-technical.md#known-problems-mapped-to-research)).
2. **Fixes for several of them already exist in the sibling Bloodborne port**, which shares this
   engine code ([porting-candidates](porting-candidates.md)). Examples are the out-of-memory
   fallbacks, red-zone protection and the DLSS device-failure retry.
3. **The U3 green/black flashes are probably NaN handling in shader translation.** Upstream
   shadPS4 has fixed it
   ([graphics](graphics-upscaling-and-performance.md#shader-translation-flicker-and-nan-bugs)).
4. **The release zip has licence gaps:**
   - FFmpeg is GPL-3.0 and ships without licence texts;
   - the NVIDIA DLSS files conflict with the GPL;
   - the updater runs unverified downloads and points at the upstream repository, not this fork.

   See [legal](legal-licensing-distribution.md#recommended-actions).
5. **The codebase is young and was only built on Windows:** no CI, many Bloodborne leftovers,
   about 200 environment variables, game-specific constants spread across files
   ([architecture](codebase-architecture.md#technical-debt-and-risks)). The Linux build and the
   test suite have since been fixed on this branch, and CI now runs them.

## Method

Five research passes ran in parallel: the local code, the upstream repositories and issue
trackers, shadPS4, the game and engine, graphics technology, and licensing. Some sites (Reddit,
Wikipedia, Digital Foundry, gnu.org) could not be reached directly. Claims that rest only on
search snippets or forum reposts are marked as such in each report.
