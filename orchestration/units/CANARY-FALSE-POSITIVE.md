# UNIT CANARY-FALSE-POSITIVE

**Purpose.** Control the instrument that gates the tranche: run `experiments/ptr-engine/tools/tranche_canary.py`
against tools-on rows in both directions (false `shape_degenerate`, false `shape_ok`). Offline, zero requests.

**Bound.** 22 tool calls; journal first, handoff within 6 calls; verdict row before the handoff write.
Used: 11 tool calls. Zero requests, zero network.

**Write paths (exactly).** `docs/CANARY-FALSE-POSITIVE.md` ·
`experiments/ptr-engine/measure/CANARY-FALSE-POSITIVE.json` · `orchestration/units/CANARY-FALSE-POSITIVE.md` ·
`orchestration/handoffs/CANARY-FALSE-POSITIVE.json` · `orchestration/journals/CANARY-FALSE-POSITIVE.jsonl`

**Never touched.** `tranche_canary.py`, `run_longrun.py`, `cell.py`, `GRID-SHAPE.json`, the fixture, the
graders, any `rows-*` file, any published number. No row file was written.

**Result: `canary_blind`.**

1. Known-positive control FIRES at N=5 — era A `rows-cell-pointer-stable-20261026T182535Z.jsonl` (27 rows,
   sha `46afc892480ae1db`), turn 3, `completion_tokens=4096 max_tokens=4096 stop_reason=length wall_ms=114838.846`.
   Not a regression. (At N=2 it does not fire; N≥3 required.)
2. All three tools-on files (`rows-longrun-v4-tools-2026-10-26.jsonl`, `rows-longrun-v5-tools.jsonl`,
   `rows-longrun-v6-tools.jsonl`) are `shape_unknown` at N=5, trigger `stop_reason_outside_vocabulary` at turn 1.
   No false `shape_degenerate` at N=5; no `shape_ok` possible.
3. N ∈ {2,5,8,12}: verdict constant `shape_unknown` on every tools-on file — the schema decides, not the
   window. First cap-length completion per file: v5 T29, v4 T45, v6 none (max 3283/4096, 80.1 %).
4. `shape_unknown` count: 3 of 3 tools-on files (100 % of the tools-on corpus) at N=5, and also at N=2/8/12;
   v6 still unknown at N=48. Cause is schema drift: 0/144 era B turns carry `stop_reason` or `answer_turn`.
5. Threshold: cap-length completion (or `runaway_turn`/`turn_wall_cap`) within N turns. Not too strict in
   substance — its late fires at T29/T45 are genuine runaway tool fan-out (130/116 `read_file` calls,
   `failed_turn=true`, manifest `max_calls_per_turn: 2`) — but too coarse to separate a long answer from a
   runaway, and it never gets to say `ok` on era B rows.

**Recommendation (not applied).** Read `finish_reason` when `stop_reason` is absent; require corroboration
before `shape_degenerate`; use `answer_verified` as the era B answer contract; keep N=5 as a floor (N≥3 keeps
the era-A control live). Gate sentence: require `shape_ok` on the first 12 turns, `shape_degenerate ⇒ STOP`
**and `shape_unknown ⇒ STOP`**. The card's `any shape_degenerate ⇒ STOP` is necessary but not sufficient.

**Answer to "live tomorrow":** `shape_unknown exit=2` at turn 1 at every N, which would not be right — the
shape is readable, the reader is out of date.
