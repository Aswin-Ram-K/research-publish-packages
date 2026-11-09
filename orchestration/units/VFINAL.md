# VFINAL — Final gate: go/no-go for request spend on TX-SUP, TX-AGG, TX-HOP, TX-ABS

## Scope
Final verifier. Read-only on fixtures/tests/runner/scorer. Single unit, no subagents.
Workspace root: `/home/zer0null/research extractor`. Runner: `.venv/bin/python -m pytest` from `experiments/ptr-engine/longrun`.

## Literal test counts (default run)
Command: `/home/zer0null/research extractor/.venv/bin/python -m pytest tests/test_tx_sup.py tests/test_tx_agg.py tests/test_tx_hop.py tests/test_tx_abs.py`
Result: `55 passed in 0.13s` (per-file below).

Per-file:
- `test_tx_sup.py`: `21 passed in 0.09s`
- `test_tx_agg.py`: `5 passed in 0.02s`
- `test_tx_hop.py`: `18 passed in 0.09s`
- `test_tx_abs.py`: `11 passed in 0.04s`

## Literal default checker run
Command: `.venv/bin/python check_pointer_fixtures.py tasks-v7/TX-SUP.v1.json tasks-v7/TX-AGG.v1.json tasks-v7/TX-HOP.v1.json tasks-v7/TX-ABS.v1.json`

Status lines:
- `tasks-v7/TX-SUP.v1.json: OK`
- `tasks-v7/TX-AGG.v1.json: FAIL` (48 errors, all `fact value ... not found in introduction turn ... tool output` = reachability)
- `tasks-v7/TX-HOP.v1.json: OK`
- `tasks-v7/TX-ABS.v1.json: FAIL` (duplicate expected 'NONE' x12 + kind/type mismatch x12 + reachability x12 per absent cp)

Outcomes all four per file: True for all. Checkpoints=48, N as reported.

## Disabled checks for TX-ABS
TX-ABS tests invoke `CPF.validate(fx, disabled={"duplicate_expected", "gradability", "reachability"})`.
- `duplicate_expected`: inherent to kind (NONE repeated for 12 absent checkpoints by design; test_tx_abs_checker_fails_duplicate_expected_disabled_toggle proves default fires).
- `gradability`: inherent to kind for absent cps (answer kind NONE vs expected type TEXT); verified answerable cps (36/36) are gradable, so no defect hidden.
- `reachability`: inherent to kind (absent subject absent from all bodies; cannot be "found" in intro turn).

AGG uses `disabled={"reachability"}` only; inherent (aggregate not literally in any single body). Verified AGG passes with only reachability disabled (0 errors).

## Fixture × check table

| Fixture | Structure (48 cps, 12/bucket, 48 unique turns, runner identity) | Distinct expected | Extrapolability | Shortcut status | Kind invariant | Default checker | Verdict |
|---|---|---|---|---|---|---|---|
| TX-SUP | OK (48, {2:12,6:12,20:12,32:12}, 48 unique turns, runner identity OK) | 48/48 | no const-diff triple across revisions (test passes) | stale present in initial rev not final; no arithmetic progression | stale!=current (48/48), current=latest revision (48/48) | OK | GO |
| TX-AGG | OK (48, buckets 12 each, 48 unique turns, runner identity OK) | 48/48 | no const first-diff triple; sums not derivable from group index (checked: group sums diffs not constant) | body count constant 2 per group (12/12 intro turns) | 4 aggregates per group (all/first2/last2/alt) recompute match 48/48 | FAIL reachability (inherent) | GO |
| TX-HOP | OK (48, buckets 12 each, 48 unique turns, runner identity OK) | 48/48 | no const diff in keyed tables (test passes) | JOIN required 48/48; BUT target row position perfectly predictable by chain%4 (chain 1->pos0, 2->pos1, 3->pos2, 0->pos3) | key in A body, expected not in A, expected+key+alt1 in B body (48/48) | OK | NO-GO |
| TX-ABS | OK (48, buckets 12 each, 48 unique turns, runner identity OK) | 37 (36 NUM + NONE) | answerable values distinct (36/36); absent values NONE | absent subjects (VAL_D..O) absent from all bodies/items/sp (12/12); answerable values in exactly one body (36/36); shape VAL_[A-Z] same as answerable | 12 absent (3/bucket) + 36 answerable (9/bucket) | FAIL duplicate/gradability/reachability (all inherent) | GO |

## Row-position analysis (TX-HOP residual)
Distribution: `{0: 12, 1: 12, 2: 12, 3: 12}` (uniform, as FixHopRow reported).
Predictability test: position is a perfect function of chain index mod 4:
`{1: {0:12}, 2: {1:12}, 3: {2:12}, 0: {3:12}}`.
`turn % 4` is NOT a perfect predictor (6/6 split), but chain index is, and chain is recoverable from the entity key / cp id. Therefore the "join required" property is weakened: a model can pick row `(chain mod 4)` without reading the key column. Shortcut NOT closed. FixHopRow's claim of closure is wrong.

## Test-count reconciliation
Earlier reported counts: SUP 21, AGG 17, HOP 18, ABS 11 (last reported; VHARDEN per-file agreed).
Current counts: SUP 21, AGG 5, HOP 18, ABS 11.
- SUP: no change (21).
- HOP: no change (18).
- ABS: no change (11) [note: HARDENABS reported 9; FixAbsToken/VHARDEN-era tests brought to 11].
- AGG: 17 -> 5, loss of 12 tests. The removed tests included extrapolability guards (`test_tx_agg_no_arithmetic_member_series`, `test_tx_agg_no_constant_group_offset`, `test_tx_agg_no_linear_function_of_group_index`) and checker red-greens. Coverage retained: `test_no_constant_first_diff_triple`, `test_expected_not_derivable_from_group_index`, `test_body_count_constant_per_group`, `test_no_expected_value_in_single_body`, `test_guard_red_green`. Verified AGG fixture exhibits no constant-diff or constant-offset pattern (group sums diffs not constant). Coverage is reduced but no defect evidenced; however the extrapolability guard is weaker (only checks i*1000 and i, not arbitrary constant offsets). Recommend restoring the 12 tests or at least the constant-offset guard.

## Disabled-by-default guards
No `pytest.skip`, `xfail`, or `skipif` in any of the four test files.
Disabled checks appear only as explicit `CPF.validate(..., disabled={...})` arguments in test assertions (red-green toggles) and in TX-ABS/TX-AGG default test calls. No silent bypass.

## Contradiction resolutions
1. HardenAgg (17 passed) vs FixAggBodies (5 passed): FixAggBodies rewrote test_tx_agg.py, dropping 12 tests. The fixture itself improved (body count constant 2, aggregates verified). HardenAgg's count is stale; FixAggBodies is the current authoritative count. Regression in test coverage is real (12 tests lost) but not a fixture defect.
2. FixAbsToken default-vs-disabled: disabled set = {duplicate_expected, gradability, reachability}; all three inherent to absent kind (verified answerable gradability 36/36 passes). No defect hidden.
3. FixHopRow row positions {0:12,1:12,2:12,3:12}: uniform but perfectly predictable by chain%4. FixHopRow's "closed" claim is incorrect; shortcut persists.

## Verdicts
- TX-SUP: GO
- TX-AGG: GO (coverage gap noted; recommend restore tests)
- TX-HOP: NO-GO (row position predictable by chain mod 4; vary row order independently of chain, then re-run VFINAL)
- TX-ABS: GO
