# UNIT ANALYSIS-CONSUMER-FIX

**Objective.** Give the analysis the two mechanisms it lacks: a `usable_for`
consumer end to end (manifest carrier, excluded by name, printed AND in the
output document) and a truncated-turn rule (`stop_reason=length` /
`truncated=true` out of p50 and p95, counted per arm, surviving n printed,
min_n_for(0.95)=60 untouched, not applied to request/ledger accounting).

**Hard bound.** 24 tool calls; journal first, handoff within 6 calls, verdict row
before the handoff write. Offline: zero requests, no `ask_user_question`.

**Frozen by the card (never edited).** `cell.py`, `run_longrun.py`,
`grade_v5.py`, `PARM-1*`, the fixture, any `rows-*` file, any historical grade,
any published number, `min_n_for(0.95)`, the McNemar floor, every frozen
threshold; `docs/LATENCY-REPORT.md` and `docs/OPERATOR-BRIEF.md` are listed for
regeneration, never rewritten.

**Write paths.** `experiments/ptr-engine/longrun/analyze_stats.py`,
`experiments/ptr-engine/longrun/tests/test_analysis_consumer.py`,
`docs/ANALYSIS-CONSUMER.md`, `orchestration/units/ANALYSIS-CONSUMER-FIX.md`,
`orchestration/handoffs/ANALYSIS-CONSUMER-FIX.json`,
`orchestration/journals/ANALYSIS-CONSUMER-FIX.jsonl`.
`experiments/ptr-engine/tools/tokens_to_verified.py` — identity check only
(untouched, sha256 d4cca36c…). `experiments/ptr-engine/longrun/analyze.py` does
not exist (`measure/ANALYSIS-PATH.json` records that); the instrument is
`analyze_stats.py`, which is what was edited.

**Assumption recorded.** `cell.py` is frozen, so the manifest WRITER cannot live
in the grid; it lives in `analyze_stats.py` as
`write_cell_manifest_usable_for` / `stamp_usable_for` (+ `--stamp-rows`), and
cell.py's next revision must call it per finished cell. Until then the grid's own
census (`measure/GRID-CELL-SANITY.json`) carries the stamp for today's cells —
the same values, so nothing is re-admitted or excluded on a weaker basis.

**Kill condition.** Stop and report `partial` if the real artefacts cannot be
read offline or if consumption would require editing a frozen file.
