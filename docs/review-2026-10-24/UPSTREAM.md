# Upstream unresolved-issue assessment

Checked 2026-10-24 using the connected GitHub issue search. Source: `Supermedo/uncharted_pc`, query `repo:Supermedo/uncharted_pc is:issue is:open`, maximum 100 results. The saved snapshot contains 100 returned titles/URLs. This is a bounded issue sample, not a complete export; no claim is made about omitted older issues or all discussion comments. Open status alone does not prove a bug still reproduces on the fork. The search even returns a title marked FIXED (#596), so avoid treating every result as a new confirmed defect.

| Unresolved upstream work | Fork disposition | Proposed action |
|---|---|---|
| #588 MP3 AJM abort | New #56 | Return codec errors, implement validated MP3/AAC decode; current source confirms exit path |
| #479/#401/#384/#383 streaming assertion | New #61 | Reproduce revision-specific resource lifetime failure; fix demonstrated cause, retain assertion |
| #558/#415/#394 convoy progression; #448/#590 collision | New #62 | Separate reproductions at supported 60 Hz; audit timing/patch behavior |
| #601/#603/#356/#376 missing geometry/corruption | New #63 | Capture cache/shader diagnostics and isolate affected changes; existing #31/#37 are candidates, not proven causes |
| #510 cutscene freeze with ongoing audio | New #64 | Trace decoder/presentation progress and flush/reset semantics |
| #362 Windows shortcut Steam Input association | New #65 | Prepared direct-game shortcut or process-association fix; validate controller layouts |
| #498 plain ELF rejected | New #66 | Shared validated ELF path or precise supported-format documentation |
| #497 flexible-map split | Existing #34 | Backing-offset fix and partial mapping/writeback regression |
| #496 mount exhaustion | Existing #36 | Atomic mount reservation/rollback and capacity tests |
| #518/#447/#306 scheduling/CPU pressure | Existing #41/#17 | Review idle-worker changes and verify power/frame-time behavior; source of report measurements is upstream reporter |
| #351 FSR noise on Phoenix | Existing #8 and fork #23's reported fix | Verify linux-branch protected-memory fix before integration; retain conservative defaults outside validated devices |
| #589 Xbox prompts; #332 trophies; #556/#440 ultrawide | Existing #11/#12/#14 | Keep existing roadmap and verify per-game/platform rendering behavior |
| #326 internal vs output resolution | Existing #10 | Per-device profiles and correct UI/scene separation |
| General crashes (#600/#591/#593/#560 and others) | Retained in snapshot, no invented root cause | Request reproducible scene/build/settings metadata in normal maintainer triage; group only when signatures establish the same defect |

Spam/moderation, playthrough confirmations and feature discussion are not code defects. No attachments, scripts or executable fixes from issue bodies were executed. Existing fork #40 lists shadPS4 correctness port candidates; verify licenses, source compatibility and tests before porting. This review did not revalidate every cited upstream commit or PR head. Existing #41/#42 track PR #346/#405 decisions; their current merge status was not independently refreshed, so the roadmap does not claim them merged or integrated.

Fork #23 records Linux hardware results and project priorities; these are historical reports, not measurements of this main checkout. The snapshot and newly filed tracking issues preserve provenance so implementation can test each report rather than assume branch equivalence.
