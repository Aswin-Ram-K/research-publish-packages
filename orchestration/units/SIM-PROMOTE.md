# SIM-PROMOTE — adopt the cost model that already exists and passes its tests

Card kind: `task board` · tag `automated` · permission `workspace-write`
Parent: `R2-OPT-SIM` (card, **no handoff on disk**) · supersedes the failed **`R2-OPT-SIM2`** card, which
produced `scratch/r2-opt-sim/{report2.json, cost_model2.py, cost_model.py, calibrate.py, selfcheck.py,
tests/test_r2_opt_sim.py}` (21 tests green) but **no report and no handoff**, and which is abandoned in three
other copies under `.tmp-sandbox/s3, s5, s6, s7, s8, s9`.

## OBJECTIVE

Third attempt at this work must not be a third rewrite. **Promote** the cost model that is already on disk
and already green: pin what it is, price its measured quality, fix only the defect a verifier would find first,
and put the deliverable where the card says it belongs. One deliverable: the report
`strategy/R2_OPT_SIM.md` + this unit's handoff.

## STATE AS FOUND (measured, not assumed)

| Fact | Value |
|---|---|
| `scratch/r2-opt-sim/cost_model.py` | 51,403 B, sha256 `4c5a…` (see handoff) — the *base* SIM model (`SCHEMA resextract/r2-opt-sim/model/1`) |
| `scratch/r2-opt-sim/calibrate.py` | 64,964 B — regenerates constants from rows |
| `scratch/r2-opt-sim/constants.json` | 33,857 B, sha256 `bce60b68…2d1b` — stamped `unit: R2-OPT-SIM` (NOT re-stamped by R2-OPT-SIM2) |
| `scratch/r2-opt-sim/report2.json` | 23,902 B — `SCHEMA resextract/r2-opt-sim2/report/1`, 9-candidate `mutable`-aware ranking, S4 tail-break analysis |
| `scratch/r2-opt-sim/cost_model2.py` | 45,576 B — **only** in `scratch/` and the abandoned sandboxes; imports nothing |
| `tests/test_r2_opt_sim.py` | 14,529 B, **21 passed in 0.06 s** (run before any write) |
| `strategy/R2_OPT_SIM.md` | **absent** — the parent card's deliverable was never written |
| `orchestration/handoffs/R2-OPT-SIM.json` | **absent** — no unit of this family ever reported |

## HARD BOUND

- **0 live requests, no `.occamy.lock`, no network, no git.** Everything derived from disk.
- Max 40 tool calls / 90 minutes. Stop and report `partial` if the regeneration check cannot finish.
- **No third cost model is written.** `cost_model.py` / `calibrate.py` / `constants.json` stay byte-identical;
  the only *code* change permitted is one added guard case in `selfcheck.py`.

## WRITE PATHS

- `orchestration/units/SIM-PROMOTE.md` (this card)
- `strategy/R2_OPT_SIM.md` (the report)
- `scratch/r2-opt-sim/selfcheck.json`, `scratch/r2-opt-sim/selfcheck.py` (guard case only)
- `tests/test_r2_opt_sim.py` (**additive** coupling assertion only)
- `orchestration/handoffs/SIM-PROMOTE.json`
- run artifacts under `.scratch/simpromote/**`

## DO NOT TOUCH

`experiments/context-cache/cells/**` (evidence) · `src/**` · `docs/PLAN.md` · `orchestration/STATUS.md` ·
other units' cards/handoffs · any target repo · systemd · DSH.

## DELIVERABLE SHAPE

Unit-shape handoff (`unit`, `status`, `artifacts`, `evidence`, `blocker`, `next_unit_hint`, `write_paths`)
plus `assumptions`; `evidence` = commands with actual output (test suite, regeneration rerun, model rerun,
guard red→green).
