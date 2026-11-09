# CONTRACTDRIFT

## Summary
Fixed instrument defect investigation and added two-level scoring (contract vs value).

- Contract-line drift verdict: **not reproduced** — harness adds `CHECKPOINT_CONTRACT_LINE` on every checkpoint turn (`run_longrun.py:2827`, `:3084`), including ARM-D fetch follow-ups (`_followup_msgs` built from `info["prompt"]`). r2 collapse attributed to endpoint sampling nondeterminism.
- Fix: `checkpoint_prompt` made idempotent (no double-append on tool-follow-up re-assembly).
- Test: `experiments/ptr-engine/longrun/tests/test_contract_presence.py` (4 tests, all green).
- Two-level scoring added to `score_longrun.py` (`score_answer_contract_rows`, `mirror_answer_contract`).
- Re-scored four row files: masking 12/48 both levels; fetch r1 28/48 both; fetch r2 contract 1/48, value 36/48 (35 kind-mismatch-but-value-correct).
- Boundary: masking correct only at d=2 (inside unmasked window); d=8/20/32 outside.

## Write paths
experiments/ptr-engine/longrun/score_longrun.py, experiments/ptr-engine/longrun/run_longrun.py, experiments/ptr-engine/longrun/tests/test_contract_presence.py, experiments/ptr-engine/research-seed-concepts/RESULTS-TX02-CELL1.md, orchestration/units/CONTRACTDRIFT.md, orchestration/handoffs/CONTRACTDRIFT.json