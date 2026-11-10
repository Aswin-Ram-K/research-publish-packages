# U-SPCC-40 — G3's `n` carries the arm term; the ceiling is enforced on actual sends

## Defect

G3's `n` and the request ceiling it is compared against were denominated in different
quantities:

- `experiments/ptr-engine/longrun/cell.py:1259` — `facts["n"] = int(t["value"]) * int(r["value"])`,
  i.e. `turns × reps`, with **no arm term**.
- `experiments/ptr-engine/longrun/cell.py:1296` — `if ok and not (lo <= facts["n"] <= hi)`
  compared that `n` to `PREREG-SPCC`'s `request_ceiling` of 200–500, which is denominated
  in **requests**.
- `experiments/ptr-engine/longrun/cell.py:1130` — G1 does it correctly:
  `turns_total = facts["turns"] * facts["arms"] * facts["reps"]`.
- `experiments/ptr-engine/longrun/run_longrun.py:3105` prices per arm
  (`cell_total = turns + extra`) and `:3113` sums into `would_send_total`.

Measured consequence: a three-arm, two-rep, 100-turn cell was **admitted** at `n = 200`
while sending **600** — 100 above the preregistration's own ceiling. The only three-arm
shape that fits the ceiling (one rep, 300 requests) was **refused** for being under the
floor at `n = 100`. E1 as preregistered was unsatisfiable.

`validate_g3` never received an arm count, so it could not see the other arms.

## Change

1. `cell.validate_g3(..., arms=None)` — new trailing parameter. `n` is now
   `turns × arms × reps`; `arms=None` means 1, so every pre-existing single-arm caller
   is bit-identical. `facts["arms"]` and `facts["n_basis"]` record the term.
2. `cell.eval_gate_prereg` passes `arms=getattr(args, "arms", None)`; the verdict carries
   `arms` and `n_basis`.
3. `run_longrun.prereg_gate_args` supplies the real arm count from `cfg.arms` via
   `cell._arms_count` (one rule, no second copy) — never a default of 1.
4. The refusal text names the **baseline** explicitly: `computed baseline n=600
   (turns x arms x reps) over 48 checkpoint(s)`, and the consequence says the brake stops
   the run at 500 actual sends.

## The baseline is not the send count

`run_longrun.py:500-501` states fetch rounds can be unbounded and each fetch follow-up is
an additional model call. A three-arm cell with `--fetch-rounds-per-turn` above zero sends
more than `turns × arms × reps`, so a cell admitted at a baseline of 300 could still
exceed 500 in practice.

Therefore the ceiling is enforced in two places, with two different numbers:

- **Baseline `n`** (the gate): a floor test and a first ceiling test. Below 200 the cell
  cannot support the claim whatever it fetches; above 500 it is already over before a
  single follow-up.
- **Actual sends** (the brake): `RequestCapGate.acquire` gained an optional `ceiling` and
  a run-scoped `run_counter`, so the ceiling is a **run** budget (the scope PREREG-SPCC
  states it in) spent once across all arms, not once per arm. `enforce_prereg_gate` arms
  it from the admitted verdict's `thresholds.request_ceiling`; `build_cap_gate` passes it
  through. The global cap and the run allocation keep their existing semantics — the
  brake only ever gains a limit.

`PREREG-SPCC.json`'s ceiling is unchanged. No bypass was added. No other gate was
weakened.

## Evidence

Red (pre-change code, `git show HEAD:` restored): the three-arm two-rep case is admitted.

```
FAILED ...::test_three_arms_two_reps_is_refused_at_600
E  AssertionError: True is not false : {... 'n': 200, 'claim': 'E1', ...}
6 failed, 1 passed in 2.21s
```

Green (this change):

```
.......                                                                  [100%]
7 passed in 3.39s
```

Required suite:

```
42 passed in 8.19s
```

`python3 tools/doc_check.py` → `OK docs clean`, exit 0.

## Shapes

| shape | baseline `n` | gate | actual sends |
|---|---:|---|---|
| 3 arms × 1 rep × 100 turns | 300 | admitted | 300 (runner prices 3 × 100) |
| 3 arms × 2 reps × 100 turns | 600 | **refused** (ceiling 500) | — |
| 1 arm × 2 reps × 100 turns | 200 | admitted | 200 |
| 1 arm × 1 rep × 100 turns | 100 | **refused** (floor 200) | — |

H1 is unchanged: with no arm count supplied `n = turns × reps` exactly as before, and the
threshold is still PARM-1's 60 (`n=59` refused, `n=60` admitted).

Fetch-heavy brake proof: three arms, one rep, 100 turns, `--fetch-rounds-per-turn 10`,
`--fetch-rounds-per-arm 200`. Baseline 300 is admitted; the run would send far more; the
brake stops it at **500 actual sends** with
`CAP REFUSED ... over the prereg request ceiling: ... prereg_ceiling=500 run_sends=500`.

## Observation (pre-existing, not introduced here)

A refusal that lands **mid-turn** leaves the follow-up rows already bought in that turn
unwritten, so the exit reconciliation reports `delta=-4` and the cell exits **9** rather
than 4. The run still stops at the ceiling and the ledger is not trusted afterwards, so
the behaviour is safe; the exit code is the pre-existing mid-turn accounting path, not a
consequence of this unit.
