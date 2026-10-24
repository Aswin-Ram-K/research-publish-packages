# UTRACE1 — pinned-trace re-verification

**Bound:** 25 tool calls. **Status:** COMPLETE (partial — see `unverified`). Reported `partial` because
`ba6128bf`, the gate-hit method, and the producing units of three stray copies were outside this unit's
budget.

## Purpose
UCONT1 found `traces/2026-09-28-duval-m0.jsonl` in read-only target `/home/zer0null/Duval` changed during
this batch. Re-verify every trace-dependent claim in the workspace against the **pinned** copy
sha256 `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb`, not the live path.

## Write paths
`strategy/TRACE_PIN_REVERIFICATION.md`, `orchestration/units/UTRACE1.md`,
`orchestration/handoffs/UTRACE1.json`, `scratch/utrace1/**`.

## Constraints honoured
No git command of any kind against `/home/zer0null/Duval` — its object store was inspected by python `zlib`
reads only. Nothing written into `state/`. No claim was edited; corrections are reported.

## Result
Pin **CONFIRMED**: 866,816 B, sha256 `431605e6…c4ecb`, 573 lines / 573 JSON records, 23 mirrors under `state/`.
Live path **moved again**: now 1,624,082 B / 1087 lines / sha256 `35687221…075d`, growing past UCONT1's
1,570,243 B. Every trace-dependent claim (T1 size 1,570,243; T2 "1031 gate hits"; T3 "1.5 MB corpus") is
`holds-only-on-live`; against the pin they read **866,816 B / 573 gated lines / 712 occurrences**.
`1031` is the *line count* of the 1,570,243 B blob, not a gate-hit count under the documented pattern set
(which gives 1205 occurrences). Two `contradicted` items (a stale working-tree row in
`docs/LIVE_TARGET_NOTES.md:50`; UCONT1's blob pair, since `e25ac80f` is 1,567,661 B not 866,816 B) and four
containment lines still in the stronger "target untouched" form.

Full detail: `strategy/TRACE_PIN_REVERIFICATION.md`.
