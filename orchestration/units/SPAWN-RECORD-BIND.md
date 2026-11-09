# UNIT SPAWN-RECORD-BIND

**Purpose.** Close the three record defects D2/D3/D4 that `V-SPAWN-ATTACK-2` found in
`experiments/ptr-engine/longrun/spawn_record.py`, without touching `cell.py` (pinned by
`TRANCH1-DRYRUN`, `07bd683a`). Offline: 0 requests. D5 is recorded, never fixed here.

**Bound.** ≤24 tool calls, 0 requests. Write paths: `spawn_record.py`,
`experiments/ptr-engine/longrun/tests/test_spawn_classification.py`, `docs/GATE-CHAIN.md` (§11 append), this card, the
handoff, the journal, `/tmp/srb/**`.

**Objective (from the card).**
1. D2 — `validate_refusal` must require coverage of `{2,3,4,8,12}` (or an explicit
   `--required-exits` override) and name the missing exits.
2. D3 — parse with a duplicate-key-rejecting hook and refuse by name, so key order can
   never rewrite a declaration.
3. D4 — the record must declare `instrumentation {primitive, covers, excludes}` and the
   validator must reject a record that omits it; narrow the doc claim to exactly what was
   measured; add a syscall-level oracle `--observed-from-syscall`.
4. Acceptance — 10+ passed (existing ten kept), one new test per defect, a red→green per
   guard, own verdict row, `cell.py` sha before/after.

**Result.** done. 18 passed. `cell.py` sha `b549e45e…` before and after.
