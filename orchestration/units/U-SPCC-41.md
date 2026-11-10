# U-SPCC-41 — E1 three-arm cell: halted before spend on a row-loss blocker

## Status

**Blocked. Zero requests sent. No rows written. No cap, shape, arm or claim changed.**

The cell was not launched. The only work performed was read-only: the runner's CLI and
gate paths were read, and G3 was evaluated **offline** (pure function, no network) to
confirm the shape is admissible before any spend.

## Why halted

A blocker was raised against the run before the first request: the mid-turn refusal path
loses rows for paid follow-up calls. `U-SPCC-40` recorded the measurement — a fetch-heavy
cell stopped at the 500 ceiling exits with `delta=-4`, i.e. **four paid calls produced no
row**. The programme cap is enforced on row counts, so a lost row is undercounted spend,
and a later run can exceed the real cap while the ledger reports compliance.

A fetch-enabled three-arm cell is exactly the shape that triggers it, so the cell must not
run until the 500-stop path is proven to preserve every paid call's row.

## Admissibility (confirmed offline, zero requests)

`cell.eval_gate_prereg` called directly with the runner's own operands
(`hypothesis="E1"`, `turns=100`, `reps=1`, `arms=3`) against
`experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json` (`task_id=TX-03`, `N=100`,
48 checkpoints):

```
gate=G3  rule_id=PREREG-SPCC  hypothesis=E1  n=300  arms=3
n_basis="turns x arms x reps (baseline; fetch follow-ups are extra)"
ok=true  short="G3 n=300 in [200, 500]"
limit="n in [200, 500] and >= 48 checkpoint(s)"
thresholds.request_ceiling=[200, 500]
thresholds.checkpoints_in_fixture=48
artefact_sha256=3a01b3e4130dd6d4d2e9db2bbb0e16558847ebd65e46c1991a1696cd2eda7af8
```

The same call with `arms=1` returns `n=100`, `ok=false`,
`short="G3 n=100 outside [200, 500]"` — confirming the earlier single-arm
`rows-e1-spcc-2026-11-10.jsonl` cell was inadmissible, as recorded.

## Instrument finding: `--dry-run` does not print a G3 verdict

`run_longrun.main` returns from the `--dry-run` branch at
`experiments/ptr-engine/longrun/run_longrun.py:4204-4216` (`return run_dry(cfg, fixture, cells)`),
**before** `claim_mode.resolve_claim` and `enforce_prereg_gate` at
`experiments/ptr-engine/longrun/run_longrun.py:4218-4240`. So a dry run renders previews
and request counts but never adjudicates G3. Step 1 of the assignment ("run with
`--dry-run` and confirm the G3 verdict") cannot be satisfied by the dry-run path as it
stands; the verdict above was obtained by calling the gate's own function with the same
operands. This is a reporting gap, not a gate hole — the live path still refuses before
the first request.

## What was not done

- No `run_longrun.py` live invocation; `requests_spent = 0`.
- No rows file created at `experiments/ptr-engine/measure/rows-e1-three-arm-2026-11-10.jsonl`.
- No scoring, no pass-turn split, no verdict against E1's prediction — there is no data to
  adjudicate, and inventing one would be fabrication.
- No `FINDINGS-LEDGER.md` row: a ledger row records a result, and there is no result.
- No commit: nothing changed.

## Next

Re-issue this cell once the row-persistence fix lands and the 500-stop path is proven to
write a row for every paid call (reconciliation `delta == 0` at the stop). The shape is
already admitted: 3 arms × 1 rep × 100 turns, baseline `n = 300`, ceiling 500 on actual
sends.
