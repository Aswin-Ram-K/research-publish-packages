# UNIT RUNNER-ROUNDS-48 — pool settable, launch numbers fixed

**Status:** partial — tasks 1-3 landed and 4(a)/(b) are green; 4(c) did NOT reproduce
(`--budget 67` does not refuse the cell dry-run on this tree: 0 of 3 gates).
**Gate:** `orchestration/handoffs/HARNESS-REPIN.json` present, `evidence.harness_sha256`
= `1f7c67914e5b76680616f08c16708635060a81ab3932c20806e597a5343f3285` (status partial, pin written).

## Edits
1. `experiments/ptr-engine/longrun/run_longrun.py:230` `TOOL_FETCH_ROUNDS_PER_ARM = 48`
   (was 24), comment naming this card + v5/v6 evidence.
2. `experiments/ptr-engine/longrun/run_longrun.py:2857` new `--fetch-rounds-per-arm`
   (default `TOOL_FETCH_ROUNDS_PER_ARM`, metavar N); resolver `fetch_rounds_per_arm(cfg)`
   at `:276-293`; validation in `main()` `:2887-2892` refuses `0` / negative with exit 2.
   Wired into every former constant use: `projected_requests` `:463`, the cap test in
   `fetch_rounds` `:961`, manifest `:1459`/`:1469`, dry-run print `:2132`, `followup_pool`
   `:2249`, resume print `:2266`, per-turn print `:2631`, final print `:2637`.
3. `experiments/ptr-engine/tools/run_a_star.py:181` `--budget 67` -> `108`; `:44`
   `FETCH_ALLOWANCE = 48` (was 24); defaults `:196` and `:280` 67 -> 108.
4. `experiments/ptr-engine/longrun/tests/test_tool_channel2.py` — the only test that
   encoded the old provisioning (assertion_d, lines 233-270): 24 -> 48 with
   `RUNNER-ROUNDS-48` comments.

## Evidence
- (a) `python3 tests/test_tool_channel2.py` (from workspace root) — assertion (d) passed:
  `-> used=48/48; T2 tool_calls error=fetch_budget_exhausted` (that assertion was reached
  and passed; the run then fails later at assertion_e, see finding F2).
- (b) `run_longrun.py --fetch-rounds-per-arm 0` -> exit 2,
  `--fetch-rounds-per-arm must be a positive integer (got 0); 0 and negative values are refused`;
  `-1` -> exit 2, same message with `(got -1)`.
- (c) NOT REPRODUCED. Both dry runs exit 0 with `0 of 3 gate(s) would refuse`; the cell's
  stage-3b projection is `projected_requests=48` for both 67 and 108, and G1 is priced
  from the ledger cap (`limit=4,320`), not from `--budget`.

## Findings
- F1: `--budget` is not the gate that refuses at 67 on this `cell.py`; the BUDGET-48-WIRE
  claim "gate requires 80/82 -> REFUSES at exit 3 stage 3/7" did not hold in dry run.
- F2: `tests/test_tool_channel2.py` assertion_e fails: tools-off stdout drifted from
  `manifests/v4tools2-baseline-pre.py` because the baseline predates the TREATMENTS block
  (61 B per prompt, diff at prompt lines T1/T2/T3). Pre-existing, not this edit.
- F3: `tests/test_tool_channel.py` assertion_f fails with `rounds == 3`: the call passes
  `rounds_used=0` with `per_turn_cap=None`, so the per-turn cap (3) stops it. Identical
  call shape at HEAD -> pre-existing, not this edit.

## Bound
22 stated; 27 used (cell.py investigation for 4(c) overran).
