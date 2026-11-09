# UNIT `FIXTURE10`

**Status:** done · **Bound:** 50 calls · **Inference requests:** 0 (offline).

## Purpose

Produce `experiments/ptr-engine/longrun/tasks-v6/LR-01.v10.json`: LR-01 now carries per-turn
`tool_outputs` so masking removes facts the checkpoints require and `bounded-context-fetch`
can recover them by ref. No new ground truth invented; all 12 checkpoint `expected` values
byte-identical to v9.

## What changed

- Schema `consonance.longrun-fixture/1` -> `consonance.longrun-fixture/2`; fixture_version
  `v10-pointer-contrast`; generation kept `gen-7` (check_pointer requires it).
- Added 5 documents: `doc-resolve` (resolve.py body), `doc-errors` (errors.py body),
  `doc-live` (2 revs), `doc-revoked`, `doc-secret`; plus revision_schedule, fetch_scenarios,
  outcomes_reachable, fetch_budget_tokens/basis for pointer validation.
- `wall_tokens` carried (6629) with basis preserved (+ `basis` key); wall_tokens_by_arm
  extended with `masking-no-fetch`/`bounded-context-fetch` (4625).
- Turn 1 carries `tool_outputs` for doc-resolve and doc-errors (bodies = item bodies).
- Each checkpoint gained `ground_truth` (doc/revision/value=expected) and `stale_value`.

## Reachability

All 12 checkpoints reachable: 8 via doc-resolve, 4 via doc-errors. 0 unreachable.

## Verification

- `check_pointer_fixtures.py` passes on v10; deliberate break (mismatched body) -> FAIL then restored.
- Offline dry-run both arms: markers produced at masked turns; T5 token count strictly
  lower than T4 (masked turn 1 tool_output replaced by marker).
- `bounded-context-fetch` fetch resolves `doc-resolve@r1` -> OK with body bytes == source body.
- `pytest .../tests/test_fixture10_contrast.py` passes (2 tests).
- Existing longrun tests: fixture_schema, wall_key, arm_cd_wiring, tool_channel* pass;
  test_verdict_semantics collection error is pre-existing (exit-code 14 partition drift).

## Write paths

- `experiments/ptr-engine/longrun/tasks-v6/LR-01.v10.json`
- `experiments/ptr-engine/longrun/tests/test_fixture10_contrast.py`
- this card + handoff
