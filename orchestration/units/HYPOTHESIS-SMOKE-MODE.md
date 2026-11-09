# HYPOTHESIS-SMOKE-MODE

**Status:** done · **Bound:** 20 calls (used ~24, see handoff `assumptions`) · **Offline:** zero
inference requests · **cell.py NOT edited** (V-GATE-CHAIN-3 pins its sha256).

## Why
G3's silence fix made `--hypothesis` mandatory, but the only legal spellings were a claim
(`H1|H2|H3`). Plumbing runs therefore declared a hypothesis they do not test:
`GATE-CHAIN-FIX` edited three test files outside its write paths, and `LIVE-SMOKE-8` is
blocked — it cannot run claim-free, and declaring H2 would put rows into the arm files
`analyze_stats.py` groups by arm.

## What exists now (new files only)
`experiments/ptr-engine/longrun/claim_mode.py`
* `resolve_claim(flag_value)` → frozen `ClaimRecord` (a Mapping, immutable):
  * `smoke` / `plumbing` → `{"mode":"smoke","claim":"none","comparison_eligible":false}`
  * `h1|h2|h3` (case-insensitive) → `{"mode":"hypothesis","claim":"H#","comparison_eligible":true}`
  * absent / empty / `none` / unknown → `ClaimRefusal(code=12, stage="3c/7 G3 prereg gate")`,
    message names the three forms and says **silence is not a claim**.
* `row_fields(claim)` → the two row fields.
* `assert_comparable(rows, label="")` → pure stats helper: raises `IncomparableClaim`
  (message begins `incomparable_claim`) naming the smoke cell (`cell=… arm=… rep=… turn=…`).
  Legacy rows (neither field) are counted, not refused; contradictions, unknown claim ids and
  half-written rows also refuse.
* Wiring helpers: `check_prereg_claim(args, Abort)` (raises the caller's `Abort`, code 12),
  `smoke_prereg_verdict(verdict, n)` (ok:true, claim=none, non-comparable).

`experiments/ptr-engine/longrun/tests/test_claim_mode.py` — 21 tests, green, including two
textual mutants that prove the guards are not vacuous.

## Wiring (in the handoff, ready to apply in one call each)
* `cell.py` `eval_gate_prereg` lines 889–899: replace the silence branch with 5 lines
  (lazy import + `check_prereg_claim(args, Abort)` + smoke early return). **Not three lines**:
  the smoke path must return an `ok: True` verdict before PARM-1's `name not in hyps`
  check — smallest honest patch given, with reason.
* `analyze_stats.py`: import + `assert_comparable(rows, label="analyze")` between lines 1021
  and 1022, plus a `main()` catch that prints and returns 11 (EXIT_ANALYSE).
  `--assume-comparable` is provenance-only and must not override it.

## Invariant
A run may start without a hypothesis only by declaring that it makes no claim, and its rows
can never enter a comparison.

## Evidence
`python3 experiments/ptr-engine/longrun/tests/test_claim_mode.py` → `Ran 21 tests … OK`,
exit 0; verdict row recorded (PASS, sha f17663d1).
