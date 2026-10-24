# Proposed optimizations

No performance improvement was measured in this review. Benchmark before enabling changes, at identical game revision, scene, resolution, driver, power and cold/warm shader state. Keep correctness fixes separate from throughput tuning.

| Proposal | Tracking | Implementation / guardrail | Evidence to collect |
|---|---|---|---|
| Idle workers sleep; host priority policy | Existing #41/#17; upstream #518 | Review upstream #346 and fiber/EOP interactions; use bounded adaptive spin then blocking; preserve responsiveness and avoid starvation. Reporter byte patches are not a patch source to apply blindly. | 20 W Phoenix 30/60 Hz, idle CPU, package power, frame-time p99, load times and long-run correctness |
| Shader/pipeline warming | Existing #16 | Versioned driver/device/game cache keys, cancellable warmup, bounded storage and robust invalidation. | Cold vs warm p95/p99 and compilation stalls; startup overhead and disk growth |
| Bounded save pattern matching | #57 | Replace recursive percent matching with iterative or DP matching, preserving underscore behavior. | Adversarial scaling, stack bounds and matching equivalence |
| Shared preparation cache | #58 | Manifest per game/executable/module set; atomic outputs and precise invalidation. | Warm/cold launch time, stat/I/O counts, removal/update/interruption tests |

Draw pipeline, staging copies and texture binding reuse already have substantial implementation/history. Do not add concurrency speculatively: first sample command processor, DrawRec, DrawPrep and copy workers with the existing frame statistics. If CPU overhead remains material after idle-worker work, compare bounded worker counts at 4/8/16 logical CPUs. Record fence order and memory barriers so higher throughput cannot resurrect frame-reuse or cache bugs. This is methodology for the existing performance work, not a measured additional defect.

Use LTO only after compiler support checks; existing CMake already performs them. Use PGO only with representative U1/U2/U3 scenes, matching compiler/profile format and explicit profile provenance. Current GCC-specific PGO options should remain disabled for unsupported compilers. Verify code size/startup and p99 as well as mean FPS; faster average FPS cannot excuse more stalls or save corruption.
