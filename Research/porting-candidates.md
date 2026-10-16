# Fixes to port from sibling projects

Snapshot of 2026-10-16. This fork's engine code (loader, C runtime, vendored shadPS4 renderer) is
shared with two projects that kept moving after the Uncharted port split off:

- **SuperMedo's Bloodborne port**, [`Supermedo/bloodborne_pc`](https://github.com/Supermedo/bloodborne_pc),
  branch `windows`. This repository's history forks from it at `e076119` ("Online play, Add to
  Steam (1.6)", 2026-10-08). The Uncharted 0.3 commit (`5c457e7`) was built on 1.6. The
  Bloodborne branch has gone on through 1.7 to 1.8.2 (150 commits). Its engine fixes address
  several of the crash groups reported against Uncharted
  ([similar-projects.md](similar-projects.md#upstream-uncharted_pc)).
- **shadPS4** ([`shadps4-emu/shadPS4`](https://github.com/shadps4-emu/shadPS4)). The vendored copy
  in `gpu/shadps4` has diverged a lot
  ([codebase-architecture.md](codebase-architecture.md#technical-debt-and-risks)).

**Nothing on this page has been ported.** An attempt to cherry-pick the Bloodborne commits in
this session was stopped by the session's safety policy: bringing code in from another
repository needs the maintainer's explicit go-ahead. The tables below are the worklist for when
that is given. The "Applies" column comes from a read-only `git apply --check` against this
branch:

- **clean**: the patch applies on its own.
- **conflicts**: the patch needs manual merging, often because it builds on an earlier commit in
  the list, or because Uncharted already changed the same lines.
- **has own fix**: Uncharted already fixes the same problem differently. Skip it.

To fetch the Bloodborne branch for porting:

```sh
git fetch https://github.com/Supermedo/bloodborne_pc.git windows:refs/remotes/bb/windows
git log --oneline HEAD..bb/windows
git cherry-pick -x <commit>   # one at a time, oldest first; rebuild and run tools/ci_linux.sh
```

## Engine fixes from the Bloodborne port

These are in shared code (`gpu/shadps4`, `gpu/shim`, `src/`). None of them depends on
Bloodborne's game data. The list is oldest first, which is also the order to port them in.

| Commit | Date | Change | Why it matters for Uncharted | Applies |
|---|---|---|---|---|
| `e3d9e21` | 10-08 | ProcessCommands drain race (null record chunk) | — | has own fix (`liverpool.cpp`) |
| `982bc34` | 10-09 | Copied GPU command buffers live until their submission retires | Use-after-free in command buffers with `BB_COPY_GPU_BUFFERS` | conflicts |
| `d41e3da` | 10-09 | Quiet audio on stereo devices | — | has own fix (`runtime_audio.c` fold) |
| `5c660f9` | 10-09 | In-game menu checkboxes and sliders keep their changes | The Insert menu's widgets | clean |
| `1b73589` | 10-10 | SRT walker: patch faulting loads under a lock, retry patched ones | Shader resource walker crashes | clean |
| `f4a8763` | 10-10 | SRT walker: cover walkers loaded from the pipeline cache | Crashes on the second run, once the cache exists | clean |
| `dd1686d` | 10-10 | Frame limiter never flips two frames closer than the period | Frame pacing at 120 FPS and above | clean |
| `5ad7b47` | 10-05 | Images the texture cache must keep no longer block evictions | VRAM growth (4 GB cards) | clean |
| `7e8bd6c` | 10-04 | Keep GPU-written images over stale guest memory | Corrupt or white textures | clean |
| `a6675ea` | 10-11 | Let the texture collector free textures again | VRAM growth (4 GB cards) | clean |
| `79c250c` | 10-11 | Skip draw steps that cannot change anything | CPU time on the GPU thread | conflicts |
| `f7ea858` | 10-12 | Write save files to a copy and replace them in one rename | Saves corrupted by a crash mid-write | conflicts |
| `635f638`, `99a4fa5` | 10-12 | Quit game button in the in-game menu | Convenience | conflicts |
| `22a7532` | 10-12 | Keep the menu within the screen | Last menu row unreachable at small sizes | conflicts |
| `1dd8471` | 10-12 | Stop with a clear message on CPUs without AVX/BMI1/MOVBE/LZCNT | Upstream issue #144 (`0xC000001D`) | conflicts |
| `188c1f6` | 10-12 | Skip draws whose pipeline the driver cannot create | Driver failures stop the game | clean |
| `479f2f5` | 10-12 | SRT walker: leave speculative walks to their recovery point | Shader resource walker crashes | clean |
| `136a72d` | 10-12 | Hash uploads only of images the GPU may write | CPU time in the texture cache | conflicts |
| `d646b1d` | 10-12 | Frame limiter: plan the next slot from the last one | Frame pacing | conflicts (needs `dd1686d`) |
| `acdfdf0` | 10-10 | Scheduler: `record_chunk` is never null | The Steam Deck `vk_scheduler` assertions (upstream #80) | clean |
| `3a7cde8` | 10-10 | Texture cache never moves images (stable SlotVector) | Dangling image references, random crashes | clean |
| `f33e761` | 10-10 | Never preload motion-vector pipelines | Start-up time, memory | clean |
| `3d43d8f` | 10-12 | Object motion: plain aligned store instead of atomics | Device lost on RDNA2 | clean |
| `cb31b38` | 10-12 | Precise readbacks read guest memory through the backing view | Readback correctness (shadPS4 needs precise readbacks for this collection) | clean |
| `5dc1f11` | 10-13 | Log the memory in use once a minute | Diagnosing the out-of-memory reports | conflicts |
| `44e7644` | 10-13 | VRAM full: allocate past the budget instead of stopping | **The 4 GB crash** ([graphics report](graphics-upscaling-and-performance.md#vram-pressure-on-4-gb-gpus)) | conflicts |
| `4f30202` | 10-13 | Object motion off on AMD GPUs before RDNA3 | Device lost on RX 6000 and older | clean |
| `2c4ddeb` | 10-14 | Skip draws whose vertex buffer table pointer is null | Guest faults in draws | clean |
| `c07f0ff` | 10-15 | GPU info in every log; a garbage PM4 header no longer stops the game | Triage of user logs; command processor crashes | clean |
| `3e3b760` | 10-15 | Five small fixes, including a retry without DLSS when the Vulkan device fails with DLSS's extensions | Upstream #148 (DLSS driver failure) | conflicts |
| `76f5b5f` | 10-16 | VideoOut: a flip IRQ ahead of its label no longer stops the game | Flip/EOP ordering, the same family as the `m_gfxEopTick` assertion ([technical report](uncharted-collection-technical.md#frame-centric-pipelining-and-frameparams)) | conflicts |
| `96502c8` | 10-16 | VRAM full on 4–8 GB cards: guest memory backing falls back to system memory | **The 4 GB crash**, upstream #181 | conflicts (needs `44e7644`) |

## Mechanisms that need data for Uncharted

These two ship a generic mechanism plus a table generated from Bloodborne's executable. The
mechanism can be ported. The table has to be regenerated from the Uncharted executables, which
needs the game files.

| Commit | Change | What Uncharted needs |
|---|---|---|
| `bc893e2` | **Red-zone trampolines.** On CPUs where Windows saves the compact XSAVE layout (Intel 12th gen and later), a write fault that Windows delivers below `rsp` overwrites the System V red zone of the guest leaf function. `link_modules.py` routes those functions' stores through trampolines that lower `rsp` first. `tools/redzone_sites.py` (capstone) finds the sites. | Run `tools/redzone_sites.py` on `eboot.bin`, `big2-ps4_Shipping.elf` and `big3-ps4_Shipping.elf` (each version). This is the strongest lead for the U2 streaming and U3 London bar crashes on 1.02 ([technical report](uncharted-collection-technical.md#known-problems-mapped-to-research)). It is the same issue as shadPS4 PR [#4802](https://github.com/shadps4-emu/shadPS4/pull/4802). |
| `e750af8`, `38e7588` | **Legacy CPU translation** of BMI1, LZCNT, TZCNT and MOVBE sites for Intel 3rd generation and older. | A translation plan per Uncharted executable. Port `1dd8471` (the clear error message) first. |

## shadPS4 changes to consider

From [graphics-upscaling-and-performance.md](graphics-upscaling-and-performance.md) and
[uncharted-collection-technical.md](uncharted-collection-technical.md). The vendored copy is older
than these, so each needs a manual port.

| Upstream | Change | Why |
|---|---|---|
| PR [#5257](https://github.com/shadps4-emu/shadPS4/pull/5257) (merged 2026-10-04) | NaN semantics. `V_CMP_N*` become unordered compares, `MIN3/MAX3/MED3` handle NaN like GCN, saturate honours `DX10_CLAMP`, plus the legacy MAC/MAD multiply. | Most likely cause of the U3 one-frame green/black flashes ([details](graphics-upscaling-and-performance.md#shader-translation-flicker-and-nan-bugs)). It needs `OpNClamp` added to the vendored sirit and a shader cache version bump. SuperMedo already tried the saturate part alone (`BB_SATURATE_NAN`, no change on U3's cloth); the compare part has not been tried. |
| PR [#4882](https://github.com/shadps4-emu/shadPS4/pull/4882) (closed), PR [#5140](https://github.com/shadps4-emu/shadPS4/pull/5140) (open) | Signal the flip only after the end-of-pipe packet that follows it; a submit lock that waits only for the graphics ring; bounded `0xffffffff` buffer descriptors. | The `m_gfxEopTick` assertion and oversized device-local buffers ([details](uncharted-collection-technical.md#uncharted-on-shadps4-and-other-emulators)). |
| PR [#5241](https://github.com/shadps4-emu/shadPS4/pull/5241) | `RCPPS`/`RSQRTPS` on Intel return AMD's results. | Intel-only differences on the CPU side. |

## Lower priority from the Bloodborne port

Not engine fixes for Uncharted, but worth knowing about: keyboard sprint kept through direction
changes (`4b930b1`); mods on exFAT/FAT32 and read-only game files (`bf0878b`, `ba34a3a`);
ultrawide output (`005dad1`, `25e5651`); the frame stats percentile line (`488076f`); and
`BB_CAMERA_LOG` (`19d171c`). The online, patch and launcher commits are Bloodborne-only.
