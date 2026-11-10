# U-SPCC-32 — compaction honesty: state the drop, make epoch monotonic

**Status:** done. **Date:** 2026-11-10. **Predecessor:** `U-SPCC-31` (commit `ba064ba`).

## Why

Two defects in `experiments/ptr-engine/ptr_engine/layers.py` were measured against the real module.
Both are decisive: E1 (200–500 requests) cannot run until they are fixed, because the arm would evict
content it claims to retain and would stamp the wrong epoch on every row after a compaction.

**D1 — compaction discards content but claims a summary.** At `layers.py:226-231` the journal was
emptied and replaced by `[summary: N turns folded into epoch E]`, a marker asserting a summary that
does not exist. Measured: a fact `doc-fact-01 value 3001` written into the journal at turn 1 is present
in the prompt at turns 1–23 and absent from turn 24 onward; the turn-26 prompt contained the literal
line `[summary: 24 turns folded into epoch 1]` and no `3001`.

**D2 — epoch is not monotonic.** `st.epoch = epoch` at the end of `compile_prompt` overwrote the state
with the caller's argument, so the `max()` guard at `:222` protected nothing. Measured over 28 turns
with the caller always passing `epoch=0`: state epoch went 0 … 0, 1 at turn 24 (the compaction), then
back to **0** at turn 25 and stayed 0, while `compactions` stayed 1. `_Prompt.epoch` and `run.epoch`
reported the same wrong value.

## What changed

- `experiments/ptr-engine/ptr_engine/layers.py`
  - marker is now `[compacted: %d turns dropped at epoch %d]` — deterministic, still in L1, so the
    prefix invariant is unchanged;
  - after the compaction block, `epoch = st.epoch` unconditionally, and the trailing `st.epoch = epoch`
    write-back is removed, so the state is authoritative and a stale caller value can never regress it;
  - `compile_prompt` docstring now says the journal is DROPPED and only a marker is retained, and that
    `state.epoch` is authoritative.
  - `COMPACT_EVERY` unchanged; no model call added; compaction is still lossy.
- `experiments/ptr-engine/longrun/tests/test_layers_compaction.py` — new, drives the real module for 28
  turns with `epoch=0` every turn.
- `experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md` — dated deviation note under E1. The
  E1 prediction and falsifier are **unedited and binding**; the note records an instrument property
  discovered before the run and states the consequence as a prediction about the outcome.
- `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` — one row recording both defects
  with the measured turn numbers and the fix.

## Acceptance

- New test proves: fact present turns 1–23, absent 24+; turn-26 prompt carries the new marker and no
  `summary`; `st.epoch`/`_Prompt.epoch`/`run.epoch` equal and non-decreasing over 28 turns with
  `epoch=0`; `compactions` increments exactly once.
- Red→green recorded: red failed on the marker text and on `epoch regressed: [0,…,1,0,0,0,0]`; green
  is 4 passed.
- `test_layers_compaction.py` + `test_spcc_arm.py` + `test_arm_cd_wiring.py` → 14 passed.
- `python3 tools/doc_check.py` exits 0.
