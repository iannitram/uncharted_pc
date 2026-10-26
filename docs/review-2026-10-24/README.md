# Uncharted PC code review — 2026-10-24

Repository: `iannitram/uncharted_pc`. Reviewed checkout: `68c8cf9a6563d653ed17ce72d758aaa5f33a7a76`, local branch `work`, matching the checked-out main snapshot. Origin is the fork; README identifies `Supermedo/uncharted_pc` as upstream. Review scope spans preparation/launch, host runtime, saves/files, GPU command/resource boundaries, shader translation, build/packaging, platform architecture and tests. This is a broad risk-based source review, not a line-by-line certification of the vendored renderer or dependencies.

## Assessment

Hold release acceptance on reproducible builds, save integrity and native test coverage. The current Linux GPU build fails against installed Vulkan-Headers 1.4.365. Save-data fixtures reproduce invalid mount-name aliasing, files listed as saves and deletion failures reported as success. Static review additionally finds read-only save mounts unenforced, global sort state races and unchecked allocation failure. Existing fork issues already track important memory, event and renderer ordering bugs; each now has a proposed fix/acceptance follow-up rather than a duplicate.

Windows is the advertised product. Linux runtime/build paths exist but this main snapshot's shell runner retains Bloodborne orchestration; a separate linux branch is described in fork #23 and must be compared before port work. macOS has CPU ABI/TLS/memory/exception and GPU feature prerequisites; Apple Silicon needs a separate guest execution strategy. A Vulkan translation layer alone is insufficient.

## Deliverables

- [Bug report](BUG_REPORT.md): 19 individual newly filed issues, evidence, fixes and acceptance; follow-ups on nine existing correctness issues and two performance issues.
- [Updated platform roadmap](ROADMAP-proposed.md): phased windows, Windows/Linux artifacts and release gates, Intel/Apple Silicon macOS feasibility deliverables. Previous inherited Bloodborne roadmap preserved in history.
- [Code map](CODE_MAP.md): execution flow and subsystem responsibilities.
- [Mac compatibility bundle feasibility](MAC_COMPATIBILITY.md): Wine/MoltenVK translation path and acceptance gates.
- [Optimization proposals](OPTIMIZATIONS.md): existing performance work plus bounded wildcard/preparation-cache proposals and benchmark method.
- [Upstream assessment](UPSTREAM.md), [open issue snapshot](upstream-open-snapshot.json), [machine-readable findings](findings.json).
- [Validation log](validation.log), [GPU build log](build.log), [reproduction output](reproduction.log), [synthetic reproduction source](reproduce_savedata.c).

## Validation and practical limits

Measured on this Linux x86-64 cloud workspace, not the fork owner's handheld/laptop: `/workspace/setup/check.sh` rebuilt and passed standalone file-mods, content, motion-history and UI-composition checks, then ran 82 Python tests: 57 passed, 25 skipped. Skips are meaningful limitations: native runtime/probe/GPU binaries are absent for several suites. See validation.log. No full-suite pass is claimed.

Measured build attempt: with `/workspace/setup/activate.sh` loaded, `ninja -C out/gpu -j2 bbgpu` exited unsuccessfully at `vk_frame_generation.cpp:349`, ambiguous `vk::Extent2D` brace assignment. Existing configured build cache and provided dependencies were used; this is not a successful clean configure/build or package validation. Build failure is #60. Logs retain compiler output and absolute workspace paths for reproducibility.

Synthetic save checks:

```sh
gcc -std=c11 -O0 -pthread -I. -Isrc docs/review-2026-10-24/reproduce_savedata.c -o /tmp/uncharted-review-savedata
/tmp/uncharted-review-savedata
```

Run as an unprivileged user. This harness includes the actual savedata implementation and stubs only file-mount bookkeeping/export lookup. It verifies the three observed defective outcomes against temporary, invented fixtures and cleans them up. It is a review reproduction, not the post-fix regression suite; its assertions intentionally expect current bad behavior and must be inverted after fixes. No game binaries, decrypted data, assets or private saves are used or added.

No Windows/macOS execution, hardware Vulkan gameplay, campaign completion, security audit, dependency vulnerability scan or performance benchmark was possible in this pass. All hardware acceptance and upstream gameplay reports are explicitly unverified here. Proposed fixes are not implemented. No upstream PR or issue was sent. Fork issues and follow-up comments were created through the connected GitHub tools as requested. Review documents are maintained in this repository folder; see Git history for publication.

## Issue publication register

- S01: https://github.com/iannitram/uncharted_pc/issues/48
- S02: https://github.com/iannitram/uncharted_pc/issues/49
- S03: https://github.com/iannitram/uncharted_pc/issues/50
- S04: https://github.com/iannitram/uncharted_pc/issues/51
- S05: https://github.com/iannitram/uncharted_pc/issues/52
- S06: https://github.com/iannitram/uncharted_pc/issues/53
- P01: https://github.com/iannitram/uncharted_pc/issues/54
- P02: https://github.com/iannitram/uncharted_pc/issues/55
- A01: https://github.com/iannitram/uncharted_pc/issues/56
- O01: https://github.com/iannitram/uncharted_pc/issues/57
- O02: https://github.com/iannitram/uncharted_pc/issues/58
- D01: https://github.com/iannitram/uncharted_pc/issues/59
- B01: https://github.com/iannitram/uncharted_pc/issues/60
- U01: https://github.com/iannitram/uncharted_pc/issues/61
- U02: https://github.com/iannitram/uncharted_pc/issues/62
- U03: https://github.com/iannitram/uncharted_pc/issues/63
- U04: https://github.com/iannitram/uncharted_pc/issues/64
- U05: https://github.com/iannitram/uncharted_pc/issues/65
- U06: https://github.com/iannitram/uncharted_pc/issues/66
