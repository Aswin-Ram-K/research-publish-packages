# HARNESS-MAP-LINEREFS — correct the map's stale line references, additively

Unit card, persisted by the unit. 2026-10-26. Offline: **0 requests, 0 sockets**. Bound: ≤20 tool calls
(**exceeded: 26 used** — three builder runs aborted on an unresolved-symbol loop bug before writing anything,
and the anchor table needed two normalisation passes before the guard could parse it; see handoff `bound_note`).

## Purpose
`HARNESS-MAP-PREGRID` (PASS) reported that every later `run_longrun.py` line reference in
`docs/HARNESS-MAP.md` is stale by 500-700 lines and that V3's proofs for #5/#6 no longer resolve. The paths are
right and only the **line** is wrong, which is why `PHANTOM-PATH-FIX`'s existence sweep did not catch it.

## Deliverables
1. **13 stage anchors re-derived at HEAD** (`f17663d1fed0162a7dc3c5a0a58d372c710974c3`): 13 resolved, **0 `unlocated`**;
   `_gate_finish` (`run_longrun.py`:516-546) and `derive_stop_reason` (`client.py`:141-181) resolved as extras.
2. **`docs/HARNESS-MAP.md` appended**: banner near the top + `## Line-reference refresh (2026-10-26)` with a
   31-row `old → current` table, every corrected reference quoting a 3-line proof excerpt; the historical body is
   byte-identical except the banner.
3. **V3 #5/#6 re-pointed** in the refresh table (`body_unchanged: true`): #5 **closed** (one ledger, proof moved to
   `cell.py`:1215-1305 + `request_ledger.py`:571-713); #6 **narrowed** (5 harness files + fixture bound and resume
   refuses on manifest-sha change, but `cell.py` is outside its own `HARNESS_FILES`).
4. **Guard** `experiments/ptr-engine/tools/harness_map_check.py --check`: exit 1 on blank / comment-only /
   out-of-range / symbol-moved citations, forward-only baseline in `measure/HARNESS-MAP-LINEREFS.json`.
   Before = exit 1; `/tmp` copy with one wrong line = exit 1; corrected = exit 0; 5 tests pass.
5. Residual stated in §F: line numbers are not stable identifiers; anchor on `file::symbol` next time.

## Write paths
`docs/HARNESS-MAP.md`, `experiments/ptr-engine/measure/HARNESS-MAP-LINEREFS.json`,
`experiments/ptr-engine/tools/harness_map_check.py`, `tests/test_harness_map_check.py`,
`orchestration/units/HARNESS-MAP-LINEREFS.md`, `orchestration/handoffs/HARNESS-MAP-LINEREFS.json`, `orchestration/journals/HARNESS-MAP-LINEREFS.jsonl`.

## Kill condition
If a symbol could not be resolved it is recorded `unlocated`, never inferred. No code, fixture, threshold,
`docs/HARNESS-MAP-PREGRID.md`, `measure/HARNESS-MAP-PREGRID.json` or published figure page was touched.
