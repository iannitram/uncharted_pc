# Graphics, Upscaling and Performance Research for uncharted_pc

Research snapshot taken **2026-10-16**. It combines public sources (linked inline) with a read of this
repository (`gpu/shadps4/…`, `docs/upscaler.md`, `docs/motion_vectors.md`, `docs/parallel_gpu.md`,
`docs/CHANGES_2026-10-0*.md`, `README.md`). Vendor SDKs, drivers and community tools change month to
month, so read every version number as "as of 2026-10-16". **[Unverified]** marks claims that rest only
on secondary press or search snippets. **[Speculative]** marks my own inferences. **[Code reading]**
marks conclusions drawn from this repository's source that have not been confirmed on the hardware in
question. Licensing is covered only briefly here. The full analysis is in
[legal-licensing-distribution.md](legal-licensing-distribution.md).

## Key takeaways for uncharted_pc

- **The U3 green/black one-frame flashes are probably NaN-semantics bugs, and upstream shadPS4 fixed a
  batch of them on 2026-10-04.** The fork in `gpu/shadps4` translates GCN's *unordered* "not" compares
  (`V_CMP_NGE/NGT/NLE/NLT/NEQ_F32`) to *ordered* SPIR-V compares, so they return the wrong answer when an
  input is NaN. A NaN guard that works on PS4 then lets NaN through. Upstream
  [PR #5257](https://github.com/shadps4-emu/shadPS4/pull/5257) fixes these compares, the `MIN3/MAX3/MED3`
  NaN rules and `DX10_CLAMP` saturation. Porting it is the cheapest experiment to try first. See
  [Shader translation flicker and NaN bugs](#shader-translation-flicker-and-nan-bugs).
- **The 4 GB crashes look like a hard `ASSERT` on allocation failure.** **[Code reading]** Every image
  and buffer is created with `VMA_ALLOCATION_CREATE_WITHIN_BUDGET_BIT`, and any failure is a fatal
  `ASSERT_MSG`. The VMA allocator is also created **without** `VMA_ALLOCATOR_CREATE_EXT_MEMORY_BUDGET_BIT`,
  so VMA does not read the driver's budget. It assumes 80 % of the heap and counts only its own
  allocations. Before tuning garbage-collector thresholds, add memory priority, an evict-and-retry path
  and lower-cost settings for 4 GB cards. See [VRAM pressure on 4 GB GPUs](#vram-pressure-on-4-gb-gpus).
- **AMD still has no official FSR 4 on Vulkan.** The FSR SDK 2.3.0 "Redstone" README lists "Vulkan is
  currently not supported in SDK", and the developer request
  ([FidelityFX-SDK #194](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/issues/194), opened
  2026-08-23) has had no AMD reply. AMD shipped official FSR 4.1 INT8 for RDNA 3 on 2026-06-22, but only
  for DX12. The port's bit-exact Vulkan replay of 4.1.1 is ahead of everything public except
  OptiScaler's DX12-interop bridge. Redstone ML frame generation and Ray Regeneration are DX12-only and
  RDNA 4-only.
- **DLSS on Vulkan is fully supported through NGX, including frame generation, but the in-engine
  features come with Vulkan caveats.** The DLSS SDK 310.x includes frame generation up to 6x
  ([310.6.0](https://github.com/NVIDIA/DLSS/releases)). Streamline's DLSS-G guide says that on Vulkan,
  **VSync with FG is D3D12-only** and **Dynamic MFG is D3D12-only**. Streamline also requires Reflex for
  DLSS-G. DLSS 4.5 presets M/L are expensive on RTX 20/30 cards, so keep K for Quality and DLAA there.
- **The project has no latency reduction or present-timing support, and that matters most with frame
  generation.** `VK_NV_low_latency2` (NVIDIA) and `VK_AMD_anti_lag` (AMD Windows drivers, and Mesa 26.3
  RADV) are both usable directly from Vulkan. The default present mode is **Mailbox**. Mailbox can
  silently drop frames that were generated to be shown. Use FIFO (with VRR) or Immediate when FG is on.
- **There is no official XeFG/XeLL for Vulkan.** XeSS-SR has had Vulkan since SDK 2.0.1. XeFG and XeLL
  are DX12-only ([intel/xess #60](https://github.com/intel/xess/issues/60) is open with no commitment).
  XeSS-SR on Vulkan is the only Intel feature worth adding, and its license (binary-only, no reverse
  engineering) is stricter than MIT.
- **The project already has shadPS4's pipeline cache (SPIR-V + keys, preloaded at boot).** It does not
  persist `VkPipelineCache` data, and it has no async or graphics-pipeline-library fallback. A driver
  disk cache on NVIDIA/AMD hides most of the second-run cost. First-run hitches need prewarming, or a
  DXVK-style `VK_EXT_graphics_pipeline_library` fast-link path.

## AMD FSR 3.1, FSR 4 and Redstone on Vulkan

### Official status (Oct 2026)

- **SDK version and API support.** The FidelityFX/FSR SDK on GitHub is now titled "AMD FSR™ SDK 2.3.0 –
  'Redstone'". It lists ML upscaler 4.1.1, ML frame generation 4.0.1 and Ray Regeneration 1.2.0, and its
  *Known issues* table says **"Vulkan is currently not supported in SDK"**, even though the intro still
  mentions "DirectX 12 or Vulkan applications"
  ([FidelityFX-SDK README](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK)). The prebuilt
  signed binaries are all `amd_fidelityfx_*_dx12.dll` (see the file list in
  [`docs/license.md`](https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/main/docs/license.md)).
- **No AMD response to the Vulkan request.** Issue
  [#194 "No Vulkan, Linux, or RHI compatibility"](https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/issues/194)
  was opened 2026-08-23. It has no AMD reply, labels or milestone. The
  [OptiScaler FSR4 wiki](https://github.com/optiscaler/OptiScaler/wiki/fsr4-compatibility-list) (edited
  2026-07-22) says FSR 4 "doesn't officially support Vulkan or DX11 yet".
- **FSR 3.1 on Vulkan.** FSR 3.1 is the last AMD upscaler and frame generator with an official Vulkan
  backend. Vulkan support arrived with FidelityFX SDK 1.1 / FSR 3.1 in July 2024
  ([GamingOnLinux](https://www.gamingonlinux.com/2024/07/amd-releases-fidelityfx-sdk-110-with-fsr-31-and-vulkan-support/)),
  and SDK 1.1.4 fixed the Vulkan frame-interpolation swapchain and pacing
  ([GPUOpen 1.1.4 notes](https://gpuopen.com/manuals/fsr_sdk/whats-new/version_1_1_4/)). The 1.x source
  is MIT.
- **FSR 4 on RDNA 3 (official, DX12 only).** AMD shipped **FSR 4.1 INT8** for Radeon RX 7000 desktop GPUs
  in Adrenalin **26.6.2 on 2026-06-22**, ahead of the July date it had announced. Coverage says it reached
  300+ games through the driver override, and AMD claims no quality loss compared with RDNA 4
  ([Tom's Hardware](https://www.tomshardware.com/pc-components/gpu-drivers/amd-brings-official-fsr-4-1-support-to-rx-7000-series-gpus-int8-model-now-available-in-300-games-rdna-3-apus-also-getting-fsr-4-1-soon),
  [KitGuru](https://www.kitguru.net/gaming/joao-silva/amd-expands-fsr-4-1-support-to-radeon-rx-7000-series-gpus/)).
  AMD says RDNA 3 APUs follow "by the end of 2026"
  ([TechPowerUp](https://www.techpowerup.com/353477/amd-confirms-fsr-4-is-coming-to-apus-by-the-end-of-2026)),
  and RDNA 2 support is expected in **early 2027** (OptiScaler wiki, above). One forum claims 26.6.2
  already enabled 780M/890M APUs **[Unverified]**
  ([egpu.io](https://egpu.io/forums/pc-gaming/amd-releases-fsr-4-for-rdna-3-cards-rdna-3-5-apus/)).
- **Redstone (ML frame generation, Ray Regeneration, Radiance Caching).** These are **RDNA 4-only**.
  Ray Regeneration launched first, in Call of Duty: Black Ops 7. ML frame generation replaces FSR 3's
  analytical interpolation and can be swapped in by the driver for games that integrate FSR 3.1
  ([Hardware Busters](https://hwbusters.com/news/amd-fsr-redstone-debuts/),
  [Guru3D](https://www.guru3d.com/review/amd-fsr-redstone-quick-deepdive-review/)). No Vulkan path is
  documented for any Redstone component. The DLL notes in `docs/upscaler.md` confirm that
  `amdxcffx64.dll` contains the FP8 FSR 4 passes and `mlfi_*` ML frame interpolation, and no INT8 ML FG.
  **[Speculative]** ML FG is unlikely to run well on RDNA 2/3 or NVIDIA even if it were captured the way
  4.1.1 was. It is FP8/WMMA-oriented and much heavier than upscaling.

### The INT8 model and community use

- **August 2025 source leak.** On about 2025-08-20, AMD's FidelityFX SDK 2.0 push briefly published FSR 4
  source under MIT, including an **INT8** (DP4a) path, and then removed it
  ([igor'sLAB](https://www.igorslab.de/en/amd-fsr-4-leak-how-a-botched-github-push-reshuffles-the-cards/),
  [Guru3D](https://www.guru3d.com/story/amd-accidentally-opensources-fsr-4-code-on-github)). Within weeks,
  community DLLs built from it were running on RDNA 3, RDNA 2 and NVIDIA. RDNA 3 took roughly 3x the time
  of FSR 3.1 (≈1.9 ms vs 0.6 ms), and RDNA 2 was slower still, with no WMMA
  ([igor'sLAB](https://www.igorslab.de/en/amd-fsr-4-leak-also-allows-use-on-older-gpus/)).
- **OptiScaler.** OptiScaler is GPL-3.0. Its 0.9 builds added **"FSR4 VK w/Dx12"**, which runs FSR 4 in
  Vulkan games through a DX12 interop bridge, not natively
  ([igor'sLAB](https://www.igorslab.de/optiscaler-aktiviert-fsr-4-unter-vulkan-bevor-amd-selbst-liefert/),
  [ProfesionalReview, 2026-02-24](https://www.profesionalreview.com/2026/02/24/optiscaler-fsr-4-juegos-api-vulkan/)).
  On Linux this needs Proton 11+ and the latest vkd3d, and RADV can be much slower than AMDVLK
  ([OptiScaler wiki](https://github.com/optiscaler/OptiScaler/wiki/fsr4-compatibility-list)). An INT8
  "4.0.2b" build in March 2026 cut ghosting and RDNA 2 cost
  ([itc.ua](https://itc.ua/news/novaya-versyya-optiscaler-optymyzyruet-fsr-4-dlya-staryh-vydeokart-amd-na-rdna-2/)).
  The OptiScaler Client 1.0.7 (2026-09-15) **stopped injecting INT8 on RDNA 3**, because the driver now
  ships 4.1 there ([PCGH](https://www.pcgameshardware.de/FidelityFX-Super-Resolution-Software-277617/News/OptiScaler-Client-1-0-7-FSR-4-DLL-Swap-MFG-1553923/)).
  On Vulkan, OptiScaler offers FSR 2/3.1, XeSS 2.x, DLSS and bridged FSR 4. Its **frame generation
  (OptiFG) is DX12-only** ([OptiScaler README](https://github.com/optiscaler/OptiScaler)).
- **FireBurn/FSR-Vulkan** (MIT, about 71 commits, 1 star at time of reading) is a standalone native-Vulkan
  library ([repo](https://github.com/FireBurn/FSR-Vulkan)). It provides the FSR 3 upscaler (3.1.x bridge),
  "FSR 3.1.6 analytical optical flow + frame interpolation", an experimental **source-v07 INT8/DOT4 FSR 4
  provider** that needs an external shader and model bundle, and Ray Regeneration and Radiance Caching
  *validation contracts only* (no denoising). Its README says plainly that it is "not AMD FSR 4.1.1",
  provides no official AMD providers, and must not be relabeled as such. Q2RTX is its reference
  integration. With a single maintainer and one star, it is effectively a vendored dependency, and the
  port's patches in `gpu/patches/fsr-vulkan` will need manual rebasing.

### Licensing in brief

The FSR 3.1 source and FSR-Vulkan are MIT. The v07 assets from FireBurn/Q2RTX rest on the contested MIT
grant from the 2025 leak. The current SDK `docs/license.md` lists the `signedbin\amd_fidelityfx_*_dx12.dll`
files under the MIT-style block. Everything not listed falls under the default "binary only, no reverse
engineering" license (checked in this session: lines 1–7 and 581–586 of that file). Details and caveats
are in
[legal-licensing-distribution.md → FSR sections](legal-licensing-distribution.md#fsr-411-assets-extracted-from-amds-dll).

### Implications for this project

1. **Keep the in-house FSR 4.1.1 replay.** AMD is unlikely to ship a Vulkan FSR 4 soon (#194 has no reply,
   and the SDK says Vulkan is unsupported). The bit-exact `fsr411` core is currently the only native-Vulkan
   4.1.1 implementation known. Keep `verify.sh` in CI with a pinned DLL hash. AMD updates the model through
   the driver and the DLL, and the cbuffer and tensor tables will change.
2. **Expect FSR 4 on RDNA 2 and NVIDIA to stay costly.** The INT8 model is DP4a-bound off RDNA 3+. Present
   FSR 4 as a quality option rather than a performance option on RX 6000 and GTX/RTX cards, and default
   those cards to FSR 3.1 or DLSS.
3. **Do not plan for Redstone ML FG or Ray Regeneration on Vulkan.** Keep FSR 3.1-style interpolation
   (FSR-Vulkan 3.1.6) as the cross-vendor FG.
4. **Pin and mirror FireBurn/FSR-Vulkan**, since it is a single-maintainer dependency. If FSR 3.1.x or the
   v07 provider needs fixes, consider upstreaming them so the patch stack stays small.
5. The 1080-tier race in v07 pass 11 (fixed locally in `tools/fsr4_pass11_guard.pl`) and the
   nondeterministic right edge at non-multiple-of-64 widths in AMD's own 4.1.1 DLL are worth reporting to
   AMD and FireBurn. Both are real bugs in AMD's shaders.

## NVIDIA DLSS on Vulkan and licensing

### Streamline vs NGX direct

- **NGX (the DLSS SDK) supports Vulkan for Super Resolution, Ray Reconstruction and, since 310.6, frame
  generation up to 6x.** Releases in the last two years
  ([NVIDIA/DLSS releases](https://github.com/NVIDIA/DLSS/releases)): 310.1.0 (Jan 2025, transformer
  beta), 310.3.0 (Jun 2025, transformer out of beta), 310.5.0 (6 Jan 2026, **SR presets L and M**),
  310.6.0 (21 Apr 2026, **FG 5x/6x** and UI recomposition), 310.9.1 (8 Sep 2026, RR transformer preset F),
  and **310.9.16 on 16 Oct 2026** ("bug fixes and stability"). The port's bridge (`bbport_dlss.dll`,
  `nvngx_dlssg.dll`) follows the NGX-direct route.
- **Streamline** ([NVIDIA-RTX/Streamline](https://github.com/NVIDIA-RTX/Streamline), v2.14.16) is the
  route NVIDIA recommends for DLSS-G. The core is MIT ([license.txt](https://raw.githubusercontent.com/NVIDIA-RTX/Streamline/main/license.txt)),
  but the **DLSS-G plugin is prebuilt only**, and shipping requires "production" signed builds.
  Streamline intercepts the swapchain (manual hooking is possible) and manages Reflex. Its
  [DLSS-G programming guide](https://github.com/NVIDIA-RTX/Streamline/blob/main/docs/ProgrammingGuideDLSS_G.md)
  lists these Vulkan specifics:
  - Optical flow runs in interop mode by default. Native Vulkan optical flow needs driver ≥ 527.64
    (Windows) and Vulkan 1.1+ (1.3 recommended).
  - On Vulkan, `eBlockNoClientQueues` is required when the client waits on the inputs-processing fence.
  - **VSync with frame generation: D3D12 only.** **Dynamic MFG: D3D12 only** (driver ≥ 595.41).
  - **Reflex is required** (`sl.reflex`). A non-Streamline Reflex integration "cannot be used" with DLSS-G
    through Streamline.
  - MFG goes up to 6x (5 generated frames). Query `numFramesToGenerateMax` instead of hard-coding RTX 50
    limits.
  - HUD-less color and UI color+alpha inputs must match the backbuffer size exactly. Automatic menu
    detection needs UI color+alpha.
- **Shipping evidence.** Vulkan titles ship DLSS 4 MFG today: DOOM: The Dark Ages, and Indiana Jones and
  the Great Circle, both on idTech/Vulkan
  ([NVIDIA](https://www.nvidia.com/en-us/geforce/news/doom-the-dark-ages-path-tracing-dlss-ray-reconstruction-update/)).
  A DSOGaming test of DLSS 4.5 features found camera stutter in Indiana Jones despite 240+ fps, and could
  not enable 6x/Dynamic MFG in DOOM, which is consistent with Dynamic MFG being D3D12-only
  ([DSOGaming](https://www.dsogaming.com/?p=193746)) **[Unverified single review]**.
- **Driver-level fallback.** NVIDIA **Smooth Motion** now covers Vulkan apps on RTX 50, and on RTX 40 in
  later NVIDIA App and driver releases
  ([Khronos news](https://www.khronos.org/news/permalink/nvidia-adds-vulkan-support-to-smooth-motion-frame-generation-a-boost-for-many-games-and-emulators),
  [DSOGaming](https://www.dsogaming.com/news/smooth-motion-is-finally-available-to-nvidia-rtx-40-series-gpus)).
  Users can turn it on without any port integration. It interpolates the final image including the HUD.

### DLSS 4 / 4.5 models and MFG requirements

- **DLSS 4.5 SR** (CES 2026) uses a second-generation transformer with ~5x the compute of DLSS 4's model.
  It runs on all RTX cards, but RTX 20/30 have no FP8
  ([VideoCardz](https://videocardz.com/newz/nvidia-dlss-4-5-to-feature-2nd-gen-transformer-model-and-dynamic-6x-frame-generation)).
  Early tests show a **20–24 % loss on RTX 30/20** and up to 15 % on an RTX 4060 Ti when moving from preset
  K to L/M
  ([TechSpot](https://www.techspot.com/news/110835-dlss-45-improved-visuals-come-20-performance-cost.html)).
  The SDK defaults are K for DLAA/Quality/Balanced, M for Performance and L for Ultra Performance (310.5.0
  notes, via search **[Unverified wording]**).
- **Frame generation.** Single-frame DLSS FG works on RTX 40/50, and RTX 40 also gets the newer FG model.
  **MFG 3x/4x and the DLSS 4.5 6x / Dynamic modes are RTX 50-only.** Dynamic MFG launched on 2026-03-31
  through the NVIDIA App beta
  ([tbreak](https://tbreak.com/nvidia-dlss-4-5-march-31-launch-games/)), and it is D3D12-only per the
  Streamline guide.

### License terms relevant to a GPL project

- DLSS is distributed under the **NVIDIA RTX SDKs License (14 Mar 2024)**
  ([LICENSE.txt](https://github.com/NVIDIA/DLSS/blob/main/LICENSE.txt)). The SDK may be redistributed in
  object form inside an application that "adds material functionality". Apps must **attribute NVIDIA**
  (splash, about box or credits) and run only on NVIDIA GPUs. **§4(a)** bans reverse engineering, and
  **§4(e)** says "You may not use the SDK in any manner that would cause it to become subject to an open
  source software license". Advance notice to NVIDIA is required before *commercial* release. Developers
  have asked whether `nvngx_dlss.dll` itself may be swapped or updated, and NVIDIA has not answered
  ([NVIDIA forum](https://forums.developer.nvidia.com/t/updating-unity-dlss-nvngx-dlss-dll-file-licensing/329558)).
- The GPL-side conflict (a GPL-2.0+ program loading a proprietary DLL that it ships itself) is analysed
  in [legal-licensing-distribution.md → GPL and the NVIDIA DLSS SDK](legal-licensing-distribution.md#gpl-and-the-nvidia-dlss-sdk).
  The short version: make DLSS an optional, user-installed component.

### Implications for this project

1. **Stay on NGX direct** for SR and FG. It avoids Streamline's swapchain interception, which would
   clash with the port's own presenter and FSR 3 FG. The cost is the Reflex coupling: implement
   `VK_NV_low_latency2` directly (see [Frame pacing](#frame-pacing-presentation-modes-and-latency-reduction))
   so DLSS FG has a latency-reduction partner.
2. **Expose the preset**, defaulting to K for DLAA/Quality and M/L only for Performance and Ultra
   Performance on RTX 40/50. Older cards lose 20 %+ with L/M.
3. **Do not offer Dynamic MFG or VSync+FG on Vulkan.** Neither is supported. Document VRR (G-SYNC) as the
   way to get smooth FG output.
4. Keep the "NVIDIA, GeForce RTX and DLSS are trademarks…" credit, and add the required NVIDIA
   attribution to the launcher's about page. Consider moving the DLSS DLLs to an optional download (see
   the legal doc).

## Intel XeSS, XeFG and XeLL on Vulkan

- **XeSS-SR on Vulkan exists.** SDK 2.0.1 (17 Mar 2025) added **XeSS-SR for Vulkan 1.1** and DX11.
  2.1.0/2.1.1 improved Vulkan validation and fixed Vulkan crashes. **XeSS 3.0.0** (9 Mar 2026) added 3x/4x
  multi-frame generation on Arc, and **3.0.2** (24 Jul 2026) updated XeLL to 1.3.2.10
  ([intel/xess releases](https://github.com/intel/xess/releases),
  [VideoCardz](https://videocardz.com/newz/intel-xess-sdk-3-0-2-released-brings-updates-to-xe-low-latency)).
  XeSS-SR runs on any GPU with DP4a (SM 6.4 equivalent) and uses XMX on Arc.
- **XeFG and XeLL are DX12-only.** XeFG works on Arc and, since 2.1.0, on non-Intel GPUs with SM 6.4.
  XeLL on non-Intel GPUs only works together with XeFG ([intel/xess](https://github.com/intel/xess)). The
  request "Vulkan support for XeFG and XeLL" ([#60](https://github.com/intel/xess/issues/60), opened
  2026-03-09) got only "Thanks for expressing interest!" from an Intel account on 2026-05-18, and is
  still open.
- **License.** The Intel Simplified Software License (Oct 2022 version) allows redistribution **in
  binary form without modification**, with notice. It forbids reverse engineering, decompilation and
  modification ([LICENSE.txt](https://raw.githubusercontent.com/intel/xess/main/LICENSE.txt)). The SDK is
  closed-source, Windows DLLs only.
- **OptiScaler as a route.** OptiScaler can output XeSS 2.x on Vulkan, but only by *replacing* an upscaler
  the game already calls (DLSS/FSR/XeSS inputs). Its Vulkan frame generation does not exist (OptiFG is
  DX12-only). It also offers Fakenvapi (Reflex → Anti-Lag 2 / LatencyFlex / XeLL)
  ([OptiScaler](https://github.com/optiscaler/OptiScaler)). For a native Windows Vulkan port, OptiScaler
  adds little except for users who want to swap the DLSS path for something else.
- The port's own roadmap (`docs/ROADMAP.md`, 29 Sep) noted that `libxess.dll` exports
  `xessVKCreateContext`/`xessVKExecute`. On Windows the earlier Linux PE-loading problem does not apply,
  so the DLL can simply be `LoadLibrary`'d.

### Implications for this project

1. **XeSS-SR (Vulkan) is cheap to add** through the existing upscaler interface (same color, depth,
   motion, jitter inputs) and gives Intel Arc/iGPU users an XMX path. It is optional at best, because
   FSR 3.1/TAA already cover those GPUs. The license allows shipping `libxess.dll` unmodified with its
   notice, but it is proprietary like DLSS, so treat it as a user-installed component.
2. **Skip XeFG and XeLL** until Intel ships Vulkan. Revisit #60 periodically.

## Frame pacing, presentation modes and latency reduction

### Present modes with frame generation

- The swapchain defaults to **Mailbox** (`BB_PRESENT_MODE`, `vk_swapchain.cpp`), with FIFO as the
  fallback. Mailbox replaces a queued image when a newer one arrives before vblank. On a fixed-refresh
  display where the output rate is above the refresh rate, generated frames get **discarded**, so you pay
  for FG and see judder. **[Speculative, from Mailbox semantics]**
- AMD's guidance for its FG swapchain is to use VSync with a game-side limiter at **half the refresh
  rate**, or VSync off with tearing for the highest displayed rate. It also recommends normal-priority
  queues and short command lists running alongside interpolation, so that the paced presents land on time
  ([FidelityFX frame interpolation swapchain](https://gpuopen.com/manuals/fidelityfx_sdk2/techniques/frame-interpolation-swap-chain/)).
  Its present thread waits a calculated delta before presenting each generated frame and then the real
  one, using a moving average of frame times. The port's own presenter does the same thing ("spaced over
  the measured interval").
- **DLSS-G on Vulkan does not support VSync+FG** (see above). With G-SYNC/FreeSync, the usual setup is
  FIFO (or the driver-level VSync override) plus VRR, with a frame cap slightly below refresh.
- **Pacing extensions.** `VK_KHR_present_id2` and `VK_KHR_present_wait2` (ratified 2025, surface-queryable)
  let the app wait for a specific present to complete
  ([refpage](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_present_wait2.html)).
  **`VK_EXT_present_timing`** shipped in Vulkan 1.4.335 (Nov 2025) after five years of work. It adds
  present-time feedback and **target present times**
  ([Phoronix](https://www.phoronix.com/news/Vulkan-1.4.335-Released)). The NVIDIA beta driver supported
  it at launch, and Mesa 26.1 wired it up for ANV/RADV/NVK/PanVK/Turnip
  ([Phoronix](https://www.phoronix.com/news/Mesa-Merges-Present-Timing)). Windows AMD/Intel status is
  unknown **[Unverified]**.
- **Windows windowed mode.** NVIDIA's "Vulkan/OpenGL present method → Prefer layered on DXGI swapchain"
  routes Vulkan presents through DXGI, which improves borderless/windowed VRR and stutter. Results vary
  by setup ([NVIDIA forum](https://forums.developer.nvidia.com/t/use-of-dxgi-swapchain-vulkan-opengl-present-method/329070),
  [Khronos forum](https://community.khronos.org/t/vulkan-present-mode-preferred-native-vs-layered-on-dxgi-swapchain/112055)).

### Latency reduction on Vulkan

- **NVIDIA Reflex → `VK_NV_low_latency2`.** Call `vkSetLatencySleepModeNV` for the swapchain, then
  `vkLatencySleepNV` before sampling input, with optional latency markers
  ([Khronos refpage](https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VK_NV_low_latency2.html)).
  DXVK 2.6+ and vkd3d-proton 2.12+ use it. DXVK's docs warn it "may reduce performance or lead to less
  consistent frame pacing" in some games ([dxvk.conf](https://sources.debian.org/src/dxvk/2.7.1-3/dxvk.conf)).
- **AMD Anti-Lag 2 → `VK_AMD_anti_lag`** (introduced in Vulkan 1.3.291, July 2024). AMD's Windows driver
  added Anti-Lag 2 on Vulkan in 24.9.1 (Counter-Strike 2 was the first title)
  ([AMD 24.9.1 notes](https://community.amd.com/t5/pc-drivers-software/amd-software-adrenalin-edition-24-9-1-release-notes/m-p/714647/highlight/true)),
  and it covers RX 5000 and newer. **Mesa 26.3** (stable around November 2026) merges native RADV support
  ([Phoronix, 2026-10-08](https://phoronix.com/news/Mesa-26.3-RADV-VK_AMD_anti_lag)).
- **Cross-vendor.** The MIT
  [low_latency_layer](https://phoronix.com/news/low-latency-layer) (May 2026) implements both extensions on
  AMD/Intel under Linux. Intel XeLL has no Vulkan API (see the previous section).

### VRR

VRR needs no Vulkan API. It works with FIFO/Immediate in exclusive or independent-flip fullscreen, and
in DXGI-layered windowed mode on NVIDIA. The port's pacing for generated frames should hold a steady
cadence *below* the refresh rate, so that VRR stays in range, rather than racing above it.

### Implications for this project

1. **Pick the present mode from the frame-generation state.** With FG on, use FIFO + VRR (or Immediate,
   for tearing users). With FG off, keep Mailbox/FIFO. Show this in the overlay instead of leaving it to
   `BB_PRESENT_MODE`.
2. **Add `VK_NV_low_latency2` (NVIDIA) and `VK_AMD_anti_lag` (AMD).** The sleep point is the guest's flip
   / `sceVideoOutSubmitFlip` boundary, before the game samples input. Both are small, and they matter most
   when DLSS FG or FSR 3 FG adds a frame of latency.
3. **Adopt `VK_KHR_present_wait2`/`present_id2` where available** to measure actual present times
   (`vkWaitForPresent2KHR`) for the FG spacer, and keep the current CPU-timed spacer as the fallback.
   Track `VK_EXT_present_timing` for target-time presents once Windows drivers expose it.
4. **Cap the game at refresh ÷ multiplier, slightly lower** (for example 58 for 2x on 120 Hz), following
   AMD's guidance. The 120 Hz guest mode plus 2x FG only makes sense on 240 Hz panels.

## Shader compilation stutter in translation layers

### What the port has now

- **[Code reading]** `gpu/shadps4/video_core/cache_storage.*` and `vk_pipeline_serialization.cpp` are
  shadPS4's **pipeline cache** ("Initial implementation of pipeline cache", v0.13.0, Dec 2025 per the
  [shadPS4 releases](https://github.com/shadps4-emu/shadPS4/releases)). It stores shader metadata, SPIR-V
  binaries, pipeline keys and profiles per game serial, and at boot it preloads (creates)
  every known pipeline. It is on by default (`BB_PIPELINE_CACHE`), and `Clear()` rebuilds it when it is
  incompatible. shadPS4 v0.17.0 fixed "shader cache invalidation caused by struct padding in memcmp". Make
  sure that fix is in the fork, or the cache misses silently.
- **No `VkPipelineCache` persistence.** **[Code reading]** `createPipelineCacheUnique({})` starts empty
  every run and is never saved with `vkGetPipelineCacheData`. On NVIDIA and AMD Windows, the driver's
  implicit disk cache usually hides this. On Intel Windows and in fresh driver installs it does not.
- **Pipelines are compiled synchronously on the GPU thread** when the cache misses. The README's
  `m_gfxEopTick` crash came from exactly this ("shaders building on a first run").

### How other layers handle it

- **DXVK.** DXVK 2.0 (2022) moved to `VK_EXT_graphics_pipeline_library` (GPL). It compiles
  vertex/fragment libraries when the game *loads* its shaders and fast-links them at draw time, then
  builds optimized pipelines in the background. Its old state cache became "largely unused" and was
  later removed ([DXVK 2.0 notes](https://www.linuxcompatible.org/story/dxvk-20-released/),
  [DXVK README](https://github.com/doitsujin/dxvk)). Games that load shaders at draw time still stutter
  somewhat. Community forks (dxvk-gplasync) add **async** compilation: draws are skipped while a pipeline
  compiles, with a per-render-target threshold to limit visual damage
  ([dxvk-gplasync-lowlatency](https://github.com/Digger1955/dxvk-gplasync-lowlatency)).
- **vkd3d-proton.** It has an internal SPIR-V disk cache (2.7+) and uses `VK_EXT_shader_module_identifier`
  to cut the cache by more than 95 %, with Steam/Fossilize priming driver caches ahead of time
  ([linuxadictos](https://www.linuxadictos.com/en/vkd3d-proton-2-7-includes-improvements-for-vulkan-and-fixes-for-some-titles.html),
  [Phoronix](https://www.phoronix.com/news/ANV-Lands-Shader-Module-Ident)).
- **Yuzu, Ryujinx, Cemu.** Yuzu disabled its async shaders in 2021 because they were "prone to causing
  graphical issues"
  ([commit](https://git.openpunk.com/OpenPunk/yuzu/commit/8390286a89dd259f0ff44cc95fc20d017b58046f)).
  Ryujinx refused async, saying the glitches sometimes persist until a restart, and relied on a persistent
  per-game shader cache instead
  ([Ryujinx FAQ mirror](https://github-wiki-see.page/m/RavenStryker/EmulationSwRyu/wiki/FAQ-and-Troubleshooting))
  **[Unverified mirror]**. Cemu skips draws while compiling and compiles "essential" shaders synchronously.
- **`VK_EXT_shader_object`** removes pipelines altogether, and a Khronos layer emulates it where drivers
  lack it ([Khronos blog](https://www.khronos.org/blog/you-can-use-vulkan-without-pipelines-today)).
  Support across Windows drivers is uneven. **[Speculative]** For shadPS4's key structure (many dynamic
  states already), GPL with fast-link is the more practical first step.
- **Shipping caches.** `VK_EXT_pipeline_creation_cache_control` (core in 1.3) lets you create pipelines
  with `FAIL_ON_PIPELINE_COMPILE_REQUIRED` to check whether a pipeline is cached without blocking
  ([refpage](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_pipeline_creation_cache_control.html)).
  Shipping prebuilt SPIR-V caches is technically easy, because SPIR-V does not depend on the driver.
  Legally, it distributes translated game code, which is the same gray area the Switch emulators avoided
  (see the legal doc).

### Implications for this project

1. **Prewarm on first launch.** Ship a "pipeline key manifest" (keys and guest shader hashes only, no
   code) recorded from a full playthrough. On first launch, translate and compile matching shaders on a
   loading screen as the game encounters them, or in the background with a worker pool. **[Speculative]**
   This carries less legal risk than shipping SPIR-V, and it removes most first-run hitches.
2. **Persist `VkPipelineCache`** with header validation (vendorID, deviceID, `pipelineCacheUUID`), mainly
   for Intel and fresh drivers. It is cheap insurance.
3. **Add a GPL fast-link path** (vertex-input/pre-raster/fragment/output libraries) on drivers with
   `graphicsPipelineLibraryFastLinking`, with background optimized builds. This is DXVK's proven
   approach. Avoid draw-skipping async by default, given yuzu's and Ryujinx's experience, and keep it as an
   opt-in for low-end CPUs.
4. **Make waits robust.** The `m_gfxEopTick` fix (waiting on the frame) is right. Also bound the
   compile-time stall per frame and log `PipelineCreationFeedback` so the slow shaders are known.

## VRAM pressure on 4 GB GPUs

### What the code does today

**[Code reading]**

- **Budget.** `Instance::CollectPhysicalMemoryInfo` sums `heapBudget` over the device-local heaps *once
  at startup* on discrete GPUs, then subtracts min(⅛, 1 GB). `TextureCache` derives its thresholds from
  that sum. For a 4 GB card with about 3.5 GB of budget, that gives roughly trigger ≈ 0, pressure ≈ 1.5 GB
  and critical ≈ 3.0 GB of *process* device-local usage. Only integrated GPUs re-read
  `GetDeviceMemoryBudgetNow()` each pass (the Steam Deck fix of 2026-10-03). Discrete GPUs never follow
  the live budget, which drops when other apps (browser, overlays, OBS) take VRAM.
- **Eviction.** Only textures are evicted, at 10/20/40 per pass. Buffers (guest-memory backing, now
  sparse arenas), the 128 MiB object-motion history (`docs/motion_vectors.md`), FSR 3/4 histories and
  model scratch, FG images, DLSS internals and swapchain images are never evicted.
- **Allocation.** `image.cpp`, `buffer.cpp` and `vk_presenter.cpp` all use
  `VMA_ALLOCATION_CREATE_WITHIN_BUDGET_BIT`, and any failure hits `ASSERT_MSG("Failed allocating …")`.
  VMA's documentation: with this flag, "the allocation is not made if it would exceed the budget…VMA then
  tries…the next eligible Vulkan memory type. If all of them fail, the call then fails with
  `VK_ERROR_OUT_OF_DEVICE_MEMORY`". Because the allocator is created **without**
  `VMA_ALLOCATOR_CREATE_EXT_MEMORY_BUDGET_BIT` and never calls `vmaSetCurrentFrameIndex`, VMA uses its
  fallback "80 % heuristics" budget and counts only VMA's own allocations (checked in VMA 3.4
  `vk_mem_alloc.h`, [VMA repo](https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator)).
  Allocations made outside VMA (FSR-Vulkan, NGX, FG, swapchain) are invisible to that check.
- **Result [Speculative but consistent with the symptom "crash after a while"].** As the game streams
  new areas, usage creeps toward the 4 GB cliff. Texture GC cannot free enough, an image or buffer
  allocation fails, and the `ASSERT` ends the process. Any `VK_ERROR_DEVICE_LOST` after WDDM over-commit
  would be a second failure mode (VMA's docs list both). Check a GTX 1650 / RX 570 `last_run.log` for
  `Failed allocating image/buffer` versus `device lost` to tell them apart.

### How others handle it

- **Vulkan's model.** `VK_EXT_memory_budget` gives per-heap budget and usage that change with system
  load. Apps should poll it and respond by freeing memory, moving resources to host memory or dropping
  mip levels ([refpage](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_memory_budget.html)).
  `VK_EXT_memory_priority` and `VK_EXT_pageable_device_local_memory` tell the OS what to demote first.
  Render targets should get high priority
  ([Khronos slides](https://www.khronos.org/developers/linkto/making-use-of-new-vulkan-features)).
  VMA recommends the budget flag for *non-essential* resources (textures) and **not** for critical ones
  (render targets) (VMA "Staying within budget").
- **DXVK 2.5** (Nov 2024) rewrote memory management: it defragments, returns idle memory, and on dGPUs
  enforces the driver budget more strictly by evicting unused resources to system RAM, with a warning
  that stutter remains once VRAM is exceeded
  ([Phoronix](https://www.phoronix.com/news/DXVK-2.5-Released),
  [notes](https://www.linuxcompatible.org/story/dxvk-25-released/)).
- **Yuzu** capped integrated GPUs at 4 GB and later ran GC only at ⅞ full to avoid stutter. Low-VRAM
  users then saw more stutter near the limit
  ([SteamDeckHQ](https://steamdeckhq.com/news/yuzu-early-access-3604-steam-deck-improvements/),
  [Wccftech](https://wccftech.com/yuzu-switch-better-vram-fixing-stuttering/amp/)).
- **shadPS4 upstream** v0.19.0 (2 Oct 2026) "Fix sparse backing offsets, barriers, and memory budgeting"
  and v0.20.0 (14 Oct 2026) "buffer_cache: allocate sparse backing with device address support"
  ([releases](https://github.com/shadps4-emu/shadPS4/releases)). Its FAQ lists 2 GB VRAM as the minimum
  ([FAQ](https://shadps4.net/about/faq/)), which is optimistic for this game with upscaling.

### Implications for this project

1. **Never `ASSERT` on out-of-memory.** On failure: run aggressive texture GC, retry, and then retry
   without `WITHIN_BUDGET`, letting WDDM demote memory. Use `WITHIN_BUDGET` only for sampled textures,
   not for render targets, upscaler, FG or presenter resources.
2. **Enable the VMA budget flag** (`VMA_ALLOCATOR_CREATE_EXT_MEMORY_BUDGET_BIT` + `vmaSetCurrentFrameIndex`)
   and **re-read the live budget on discrete GPUs too**, not just iGPUs. Thresholds should be fractions of
   the *current* budget (the iGPU 70/85/95 % rule) plus a fixed reserve for non-VMA allocations.
3. **Enable `VK_EXT_memory_priority` / `VK_EXT_pageable_device_local_memory`**, with high priority for
   render targets and low for streaming textures.
4. **Add a "4 GB profile"**, selected automatically when device-local memory is ≤ 4.5 GB:
   - no frame generation and no FSR 4 (its model scratch and history are large);
   - TAA or FSR 3.1 only;
   - object-motion history budget halved (128 → 64 MiB);
   - single-buffered FG resources;
   - logging of budget headroom every N seconds.
5. Record a long route on a GTX 1650 with `BB_GC_BUDGET_MB=3000` on a big card first. `docs/CHANGES_2026-10-02.md`
   only tested a single location for 40 minutes.

## Intel Gen9 iGPU Vulkan driver issues

- **Driver status.** Intel moved 6th–10th gen (Gen9/Gen9.5: HD 520/530/620/630, UHD 6xx) to **legacy
  support in July 2022**: critical and security fixes only, quarterly at most
  ([Phoronix](https://www.phoronix.com/news/Intel-Gen9-To-Legacy-Model)). The newest legacy driver found is
  **31.0.101.2141 WHQL (2026-04-06)**
  ([release notes PDF](https://downloadmirror.intel.com/916846/ReleaseNotes_101.2141_WHQL.pdf)). Vulkan
  bugs on these chips will not be fixed by Intel.
- **Known patterns in other projects.**
  - DXVK 2.0+ crashed every game on an HD 620, and the reporter fell back to DXVK 1.10.3
    ([dxvk #3575](https://github.com/doitsujin/dxvk/issues/3575)).
  - RPCS3 calls Intel's proprietary Vulkan driver unsupported "due to their poor state". It lists
    `VK_ERROR_FRAGMENTATION` crashes, and it auto-disables MSAA because Intel iGPUs lack
    `shaderStorageImageMultisample`
    ([RPCS3 wiki](https://github.com/RPCS3/rpcs3/wiki/Graphics-Driver-Issues)).
  - Dolphin's HD 620 Vulkan crashes were closed as won't-fix
    ([Dolphin #10470](https://bugs.dolphin-emu.org/issues/10470)). An Intel crash was traced to an
    access violation in the **`igc64.dll` shader compiler**
    ([Intel forum](https://community.intel.com/t5/Graphics/Dolphin-Emulator-Vulkan-Crash/m-p/578429)).
  - Yuzu blacklisted **fp16 on the Intel Windows driver** because a game crashed Intel's SPIR-V compiler
    ([commit](https://git.openpunk.com/OpenPunk/yuzu/commit/ef6cc3aa1dcb9f8983177a0471dbd8061c88753c)).
- **This port already** disables `VK_EXT_vertex_input_dynamic_state` on Intel (the HD 630 black screen,
  issue #56) and skips `getToolProperties` ("Intel: causes crash on start") in `vk_instance.cpp`.
- **Gen9 iGPUs share system RAM.** Their "VRAM" budget is a slice of system memory, so the iGPU GC path
  (live budget, 70/85/95 %) applies, and the 8 GB RAM + page file requirement is tight for them.

### Implications for this project

1. **Find out which module crashes first.** `igc64.dll` means the shader compiler, so per-shader or
   per-feature blacklists help. `igvk64.dll` / `igdumdim64.dll` means the runtime, so feature toggles or
   giving up are the options. Ask HD 520 reporters for the Windows Event Viewer faulting-module line.
2. **Add an "Intel legacy" safe profile** keyed on `driverID == INTEL_PROPRIETARY_WINDOWS` with a Gen9
   device ID:
   - fp16/int16 off in the recompiler (yuzu precedent);
   - no `extendedDynamicState3`, `robustness2` nullDescriptor or sparse binding (the new sparse buffer
     arenas are a likely risk **[Speculative]**);
   - no FG and no FSR 4;
   - TAA/FSR 3.1 only, 720p internal.

   Make each item a `BB_*` toggle so testers can bisect.
3. **Set expectations.** Intel no longer fixes these drivers, and other emulators (RPCS3, Dolphin) treat
   them as unsupported. Document "HD 5xx/6xx: best effort, may crash in driver" in the README, as the
   README already partly does.

## Shader translation flicker and NaN bugs

### Concrete findings in this fork

**[Code reading]** These were compared against upstream shadPS4.

- **Unordered compares are translated as ordered.** In `frontend/translate/vector_alu.cpp`,
  `V_CMP_NGE_F32 → LT`, `NGT → LE`, `NLE → GT`, `NLT → GE` and `NEQ → LG` all go through the IR default
  `ordered = true` (`OpFOrd*`). On GCN, the N-forms are **true when either input is NaN** (`!(a >= b)`).
  The usual shader idiom `if (!(x >= 0)) x = 0;` or a `discard` guard therefore lets NaN through on PC
  and catches it on PS4. The same applies to `V_CMPX_*` (exec-mask) variants and the F64 forms.
  Upstream fixed this in **[shadPS4 PR #5257](https://github.com/shadps4-emu/shadPS4/pull/5257)
  "shader_recompiler: Improve NaN handling"** (merged 2026-10-04), which "applied unordered compares to
  the appropriate VALU compare instructions".
- **PR #5257 also covers the rest of GCN's NaN semantics.**
  - It implements the remaining `*_LEGACY` variants.
  - `MIN3/MAX3/MED3` follow DX10 NaN rules (`NMin/NMax`, MED3 with NaN behaves like MIN3), and it
    **drops the AMD trinary-minmax extension path**. This fork still emits `OpFMid3AMD` on AMD, which has
    different NaN behavior per vendor.
  - It honors the **`DX10_CLAMP` mode bit**: saturate becomes `NClamp`, so NaN → 0.
  - Downstream forks bumped their shader-cache version after it, because both the SPIR-V and the runtime
    info change.
- **Already present here:** `V_MIN/MAX_LEGACY_F32` NaN handling (upstream
  [#4310](https://github.com/shadps4-emu/shadPS4/pull/4310), April 2026: when an operand is NaN, the
  legacy forms return src1), `V_MUL/MAC/MAD_LEGACY` zero rules (bbport, which fixed U3 young Drake's
  glowing hair), `SignedZeroInfNanPreserve` when supported, and an opt-in `BB_SATURATE_NAN` for vertex
  shaders. That last one "made no change" on Sully's shirt, which fits the ordered-compare or MED3 cause
  rather than saturate alone. **[Speculative]**
- **CPU-side divergence can look like a shader bug.** `VRCPPS`/`VRSQRTPS` return *different
  approximations on Intel and AMD CPUs* ([rr write-up](https://robert.ocallahan.org/2021/09/rr-trace-portability-diverging-behavior.html)).
  Upstream [#5241](https://github.com/shadps4-emu/shadPS4/pull/5241) (merged 2026-10-06) patches them to
  reproduce AMD (Jaguar-like) results on Intel hosts using a compressed 17-entry XOR table. It fixed Dark
  Souls Remastered and **Bloodborne DLC "dark spots" lighting on Intel**. If the U3 flashes happen only
  on Intel CPUs, this is the lead. The skinning and cloth matrices for characters are often built on the
  CPU with SIMD reciprocals. **[Speculative]** A related PR on packed-reciprocal NaN and MXCSR handling
  ([#5325](https://github.com/shadps4-emu/shadPS4/pull/5325)) was closed without merging.
- Other recent upstream translation fixes worth comparing:
  - `V_CVT_PK_U8_F32` rounding, saturation and byte select
    ([#5194](https://github.com/shadps4-emu/shadPS4/pull/5194), merged 2026-10-01).
  - "Skip images and samplers behind untaken branches"
    ([#5218](https://github.com/shadps4-emu/shadPS4/pull/5218), still open). This relates to garbage
    descriptor reads.
  - v0.20.0's "texture_cache: initialize added depth-overlap subresources". Uninitialized subresources are
    a classic cause of one-frame black or garbage.

### Other known causes of one-frame garbage in GCN→SPIR-V translation

- **NaN/Inf semantics:** the compares, min/max, clamp and legacy multiplies covered above.
  `exp2(e*log2(0))` is the textbook case. **Denorm/FP16:** this fork maps `FpDenormMode` to the
  `DenormFlushToZero`/`DenormPreserve` execution modes when the driver supports independent float
  controls. Otherwise the mode is lost silently, so check the "denorm mode not supported" warnings in the
  logs for the GPU that flickers.
- **Image format reinterpretation:** a render target written as UNORM and sampled as UINT/SNORM, or
  BC/compressed aliasing via `eBlockTexelViewCompatible`. A wrong view format for one frame after a
  texture-cache rebind gives exactly one frame of green or black.
- **Uninitialized VGPR/SGPR or LDS reads:** GCN hardware returns stale register contents, while SPIR-V
  `OpUndef` lets the compiler pick anything. Vendor-dependent flicker is a hint.
- **Synchronization:** a missing barrier between a compute write and a vertex-stage read. The
  object-motion history needed exactly this (`docs/motion_vectors.md`). This kind of bug shows up on
  some vendors and frame timings only.

### Debugging tools

- **RenderDoc** for Vulkan frame capture, pixel history and shader debugging
  ([docs](https://renderdoc.org/docs)). The shim stubs out shadPS4's RenderDoc hooks (`bbgpu.cpp`:
  "not used by the port"), so re-enable the in-app API trigger for single-frame captures of the flash.
  Pixel history on a green pixel leads straight to the offending draw and its SPIR-V.
- **The port's own tools:** the frame analyzer (`BB_CAPTURE_TRIGGER`), FSR/present dumps (`BB_DUMP_*`,
  `BB_PRESENT_DUMP_TRIGGER`) and dumped IR. Capture frame N and N+1 and diff the per-draw constants.
- **Validation layers:** GPU-assisted validation for out-of-bounds and unbound descriptors, and
  **debugPrintf** with `isnan()` checks injected by the recompiler behind a flag. GPU-AV and debugPrintf
  are mutually exclusive
  ([Khronos layer docs](https://fuchsia.googlesource.com/third_party/Vulkan-ValidationLayers/+/83cf5dd76d877e06a646421ea0f99663a5c28c4c/docs/khronos_validation_layer.md),
  [debug_printf](https://chromium.googlesource.com/external/github.com/KhronosGroup/Vulkan-ValidationLayers/+/137d96bb8950e25874de7fe5dfa0d1502ea68340/docs/debug_printf.md)).
- **Crash tools for the U3 Cartagena device-lost:**
  - Radeon GPU Detective, which supports Vulkan since 1.1 and offers hardware crash analysis on RDNA 2+
    ([GPUOpen](https://gpuopen.com/learn/rgd-1-1-vulkan-support/));
  - NVIDIA Nsight Aftermath;
  - `VK_EXT_device_fault`, plus debug-utils markers and object names
    ([Vulkan tutorial](https://docs.vulkan.org/tutorial/latest/Building_a_Simple_Engine/Tooling/04_crash_minidump.html)).

### Implications for this project

1. **Port PR #5257 first** (unordered N-compares, NaN-correct MIN3/MAX3/MED3 without `FMid3AMD`, and
   `DX10_CLAMP` → NClamp). Bump the shader-cache version, then re-test Sully's shirt in Cartagena with
   `BB_SATURATE_NAN` unset. This is the highest-value, lowest-effort fix in this report.
2. **Find out whether the flashes depend on the CPU vendor.** If they appear only on Intel hosts, port
   #5241 (RCPPS/RSQRTPS emulation).
3. **Add a recompiler debug flag** that wraps every VALU result written to an export or a
   position/color output with `isnan → debugPrintf(shader hash, pc)`. A single run then names the
   offending GCN instruction.
4. **Rebase the shadPS4 fork regularly** (v0.19/v0.20 bring texture-cache initialization, sparse memory
   budgeting and NaN fixes). Each bbport change in `shader_recompiler` should carry a test in
   `taa-shader-test`-style SPIR-V harnesses.

## Sources

AMD / FSR
- AMD FSR SDK 2.3.0 "Redstone" README: https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK
- FidelityFX SDK license file: https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/main/docs/license.md
- FidelityFX-SDK issue #194: https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/issues/194
- FSR SDK 1.1.4 notes: https://gpuopen.com/manuals/fsr_sdk/whats-new/version_1_1_4/
- GamingOnLinux, SDK 1.1 + Vulkan: https://www.gamingonlinux.com/2024/07/amd-releases-fidelityfx-sdk-110-with-fsr-31-and-vulkan-support/
- Frame interpolation swapchain docs: https://gpuopen.com/manuals/fidelityfx_sdk2/techniques/frame-interpolation-swap-chain/
- Tom's Hardware, FSR 4.1 on RX 7000: https://www.tomshardware.com/pc-components/gpu-drivers/amd-brings-official-fsr-4-1-support-to-rx-7000-series-gpus-int8-model-now-available-in-300-games-rdna-3-apus-also-getting-fsr-4-1-soon
- KitGuru: https://www.kitguru.net/gaming/joao-silva/amd-expands-fsr-4-1-support-to-radeon-rx-7000-series-gpus/
- TechPowerUp, APUs by end of 2026: https://www.techpowerup.com/353477/amd-confirms-fsr-4-is-coming-to-apus-by-the-end-of-2026
- egpu.io forum (unverified APU claim): https://egpu.io/forums/pc-gaming/amd-releases-fsr-4-for-rdna-3-cards-rdna-3-5-apus/
- Hardware Busters, Redstone: https://hwbusters.com/news/amd-fsr-redstone-debuts/
- Guru3D, Redstone deep dive: https://www.guru3d.com/review/amd-fsr-redstone-quick-deepdive-review/
- igor'sLAB, leak: https://www.igorslab.de/en/amd-fsr-4-leak-how-a-botched-github-push-reshuffles-the-cards/ and https://www.igorslab.de/en/amd-fsr-4-leak-also-allows-use-on-older-gpus/
- Guru3D, leak: https://www.guru3d.com/story/amd-accidentally-opensources-fsr-4-code-on-github
- OptiScaler: https://github.com/optiscaler/OptiScaler ; FSR4 wiki: https://github.com/optiscaler/OptiScaler/wiki/fsr4-compatibility-list
- igor'sLAB, OptiScaler FSR 4 on Vulkan: https://www.igorslab.de/optiscaler-aktiviert-fsr-4-unter-vulkan-bevor-amd-selbst-liefert/
- ProfesionalReview, OptiScaler Vulkan: https://www.profesionalreview.com/2026/02/24/optiscaler-fsr-4-juegos-api-vulkan/
- itc.ua, INT8 4.0.2b: https://itc.ua/news/novaya-versyya-optiscaler-optymyzyruet-fsr-4-dlya-staryh-vydeokart-amd-na-rdna-2/
- PCGH, OptiScaler Client 1.0.7: https://www.pcgameshardware.de/FidelityFX-Super-Resolution-Software-277617/News/OptiScaler-Client-1-0-7-FSR-4-DLL-Swap-MFG-1553923/
- FireBurn/FSR-Vulkan: https://github.com/FireBurn/FSR-Vulkan

NVIDIA / DLSS
- DLSS SDK releases: https://github.com/NVIDIA/DLSS/releases ; license: https://github.com/NVIDIA/DLSS/blob/main/LICENSE.txt
- Streamline: https://github.com/NVIDIA-RTX/Streamline ; license: https://raw.githubusercontent.com/NVIDIA-RTX/Streamline/main/license.txt
- DLSS-G programming guide: https://github.com/NVIDIA-RTX/Streamline/blob/main/docs/ProgrammingGuideDLSS_G.md
- NVIDIA, DOOM: The Dark Ages DLSS 4 update: https://www.nvidia.com/en-us/geforce/news/doom-the-dark-ages-path-tracing-dlss-ray-reconstruction-update/
- DSOGaming DLSS 4.5 review: https://www.dsogaming.com/?p=193746
- VideoCardz, DLSS 4.5: https://videocardz.com/newz/nvidia-dlss-4-5-to-feature-2nd-gen-transformer-model-and-dynamic-6x-frame-generation
- TechSpot, DLSS 4.5 cost: https://www.techspot.com/news/110835-dlss-45-improved-visuals-come-20-performance-cost.html
- tbreak, Dynamic MFG launch: https://tbreak.com/nvidia-dlss-4-5-march-31-launch-games/
- NVIDIA forum, nvngx_dlss.dll licensing: https://forums.developer.nvidia.com/t/updating-unity-dlss-nvngx-dlss-dll-file-licensing/329558
- Khronos news, Smooth Motion on Vulkan: https://www.khronos.org/news/permalink/nvidia-adds-vulkan-support-to-smooth-motion-frame-generation-a-boost-for-many-games-and-emulators
- DSOGaming, Smooth Motion RTX 40: https://www.dsogaming.com/news/smooth-motion-is-finally-available-to-nvidia-rtx-40-series-gpus

Intel / XeSS
- intel/xess: https://github.com/intel/xess ; releases: https://github.com/intel/xess/releases ; issue #60: https://github.com/intel/xess/issues/60 ; license: https://raw.githubusercontent.com/intel/xess/main/LICENSE.txt
- VideoCardz, XeSS 3.0.2: https://videocardz.com/newz/intel-xess-sdk-3-0-2-released-brings-updates-to-xe-low-latency

Pacing and latency
- VK_NV_low_latency2: https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VK_NV_low_latency2.html
- VK_KHR_present_wait2: https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_present_wait2.html
- Phoronix, Vulkan 1.4.335 / present timing: https://www.phoronix.com/news/Vulkan-1.4.335-Released ; Mesa: https://www.phoronix.com/news/Mesa-Merges-Present-Timing
- Phoronix, RADV VK_AMD_anti_lag (Mesa 26.3): https://phoronix.com/news/Mesa-26.3-RADV-VK_AMD_anti_lag
- Phoronix, low_latency_layer: https://phoronix.com/news/low-latency-layer
- AMD Adrenalin 24.9.1 notes: https://community.amd.com/t5/pc-drivers-software/amd-software-adrenalin-edition-24-9-1-release-notes/m-p/714647/highlight/true
- dxvk.conf (2.7.1): https://sources.debian.org/src/dxvk/2.7.1-3/dxvk.conf
- NVIDIA forum, DXGI present method: https://forums.developer.nvidia.com/t/use-of-dxgi-swapchain-vulkan-opengl-present-method/329070 ; Khronos forum: https://community.khronos.org/t/vulkan-present-mode-preferred-native-vs-layered-on-dxgi-swapchain/112055

Shader compilation
- shadPS4 releases: https://github.com/shadps4-emu/shadPS4/releases
- DXVK 2.0 notes: https://www.linuxcompatible.org/story/dxvk-20-released/ ; DXVK: https://github.com/doitsujin/dxvk
- dxvk-gplasync-lowlatency: https://github.com/Digger1955/dxvk-gplasync-lowlatency
- vkd3d-proton 2.7: https://www.linuxadictos.com/en/vkd3d-proton-2-7-includes-improvements-for-vulkan-and-fixes-for-some-titles.html
- Phoronix, shader module identifier: https://www.phoronix.com/news/ANV-Lands-Shader-Module-Ident
- Yuzu async disable commit: https://git.openpunk.com/OpenPunk/yuzu/commit/8390286a89dd259f0ff44cc95fc20d017b58046f
- Ryujinx FAQ mirror: https://github-wiki-see.page/m/RavenStryker/EmulationSwRyu/wiki/FAQ-and-Troubleshooting
- Khronos, shader objects: https://www.khronos.org/blog/you-can-use-vulkan-without-pipelines-today
- VK_EXT_pipeline_creation_cache_control: https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_pipeline_creation_cache_control.html

VRAM
- VK_EXT_memory_budget: https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_memory_budget.html
- Khronos, "Making use of new Vulkan features": https://www.khronos.org/developers/linkto/making-use-of-new-vulkan-features
- VulkanMemoryAllocator (staying within budget, in `vk_mem_alloc.h`): https://github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator
- DXVK 2.5: https://www.phoronix.com/news/DXVK-2.5-Released ; https://www.linuxcompatible.org/story/dxvk-25-released/
- Yuzu GC: https://steamdeckhq.com/news/yuzu-early-access-3604-steam-deck-improvements/ ; https://wccftech.com/yuzu-switch-better-vram-fixing-stuttering/amp/
- shadPS4 FAQ: https://shadps4.net/about/faq/

Intel iGPU
- Phoronix, Gen9 to legacy: https://www.phoronix.com/news/Intel-Gen9-To-Legacy-Model
- Intel 101.2141 release notes: https://downloadmirror.intel.com/916846/ReleaseNotes_101.2141_WHQL.pdf
- DXVK #3575: https://github.com/doitsujin/dxvk/issues/3575
- RPCS3 driver issues wiki: https://github.com/RPCS3/rpcs3/wiki/Graphics-Driver-Issues
- Dolphin #10470: https://bugs.dolphin-emu.org/issues/10470 ; Intel forum: https://community.intel.com/t5/Graphics/Dolphin-Emulator-Vulkan-Crash/m-p/578429
- Yuzu Intel fp16 blacklist: https://git.openpunk.com/OpenPunk/yuzu/commit/ef6cc3aa1dcb9f8983177a0471dbd8061c88753c

Flicker and NaN debugging
- shadPS4 PR #5257: https://github.com/shadps4-emu/shadPS4/pull/5257 ; #4310: https://github.com/shadps4-emu/shadPS4/pull/4310 ; #5241: https://github.com/shadps4-emu/shadPS4/pull/5241 ; #5325: https://github.com/shadps4-emu/shadPS4/pull/5325 ; #5194: https://github.com/shadps4-emu/shadPS4/pull/5194 ; #5218: https://github.com/shadps4-emu/shadPS4/pull/5218
- rr, RCPPS divergence: https://robert.ocallahan.org/2021/09/rr-trace-portability-diverging-behavior.html
- RenderDoc docs: https://renderdoc.org/docs
- Radeon GPU Detective Vulkan: https://gpuopen.com/learn/rgd-1-1-vulkan-support/
- Vulkan crash minidump tutorial: https://docs.vulkan.org/tutorial/latest/Building_a_Simple_Engine/Tooling/04_crash_minidump.html
- Khronos validation layer docs: https://fuchsia.googlesource.com/third_party/Vulkan-ValidationLayers/+/83cf5dd76d877e06a646421ea0f99663a5c28c4c/docs/khronos_validation_layer.md ; debugPrintf: https://chromium.googlesource.com/external/github.com/KhronosGroup/Vulkan-ValidationLayers/+/137d96bb8950e25874de7fe5dfa0d1502ea68340/docs/debug_printf.md
