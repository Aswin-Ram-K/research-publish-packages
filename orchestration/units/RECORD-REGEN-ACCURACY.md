# UNIT RECORD-REGEN-ACCURACY

**Purpose.** Regenerate one stale record (`experiments/ptr-engine/measure/ACCURACY-RECOMPUTED.json`)
from its own embedded generator and prove that nothing but the two drifted fields moved.

**Input evidence.** `orchestration/handoffs/RECORD-DRIFT-TRIAGE.json` — verdict `record_stale`,
two differing paths: `/aggregate_records_checked[2]/source_sha256` (PUB `aa887d0a…`, REGEN `3d2da7bb…`)
and `/aggregate_records_checked[2]/mentions_3/25` (PUB `false`, REGEN `true`).

**Bound.** 18 tool calls; offline, zero requests; verdict row before handoff.
**Write paths (exactly).** the record (regenerated copy) · this card · `orchestration/handoffs/RECORD-REGEN-ACCURACY.json` · `orchestration/journals/RECORD-REGEN-ACCURACY.jsonl`
**Forbidden.** test, generator, OPERATOR-BRIEF.json, any grade/rows file, any latency/quality number, PARM-1*, WITHDRAWN.json.

**Procedure run.**
1. Reproduce command verbatim → `diff` showed exactly two hunks (lines 848, 850) = the two triaged paths.
2. Source proof: `sha256sum OPERATOR-BRIEF.json` = `3d2da7bb…` (the REGEN value); `:65` = `"grade_v5": {"value": "3/25", …}`.
3. Whole-file copy `/tmp/regen/ACCURACY-RECOMPUTED.json` → published path (no hand edits).
4. `pytest test_accuracy_recomputed.py -q` → 2 passed. Regenerated a second time: all three copies sha256 `dc3325b1…`, `cmp` identical.
5. Mutation check: `/tmp/mut` copy with `aggregate_records_checked[2]['mentions_3/25']` True→False → the byte-identity test FAILS.
6. No figure moved: `records`, `headline`, `doc_lines`, `discriminators`, `grade_v5_documents_checked` byte-equal before/after.

**Result.** done — record regenerated; delta support exactly the two triaged paths.
