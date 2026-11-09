# UNIT `TRANCHE-CANARY` — pre-tranche canary

**Status:** done · **mode:** offline (zero requests, zero sockets) · **bound:** 24 tool calls

## Why

`TRANCH1-DRYRUN-2` passed 10/10 cells offline; the live tranche's cell 1 died at T27/48 with
T3 and T27 each burning the full 4,096-token completion ceiling (`length`, then
`runaway_turn`), exit 6: 28 requests spent, 0 usable cells. That failure is model behaviour
on the chosen prompts at the chosen channel — invisible to a dry run. The recorded cell
proves the signal is early: the first cap-length completion is at T3.

## What was built

1. `experiments/ptr-engine/tools/tranche_canary.py` — classify the first N turn rows of one
   arm's cell 1 (N default 5) into `shape_ok` (0) · `shape_degenerate` (1) · `shape_unknown`
   (2) · could-not-run (3). Replay mode reads rows (zero requests); live mode runs a cell-1
   launch command, rewriting only the `--turns` window and refusing `--reps != 1`.
2. Replay proof over the 27 recorded rows, zero requests: N=5 → `shape_degenerate` naming T3
   (`completion_tokens 4096`, `max_tokens 4096`); N=2 → `shape_unknown` (T1–T2 clean, no
   parseable answer, cap at T3 outside the window) — the pair shows why N is not 2.
3. `docs/TRANCHE-CANARY.md` — launch order `gates dry-run · canary (N=5 per arm) · tranche`,
   cost arithmetic (4 × 5 = 20 requests vs ≈720 tranche, ≈2.8 %), exit-code mapping and the
   explicit statement that the canary spends real requests and is charged to the ledger.
4. `tests/test_tranche_canary.py` — 13 tests: ok (incl. a 171 s slow-but-untruncated turn),
   degenerate (synthetic `completion_tokens == max_tokens`, and a `turn_wall_cap` variant),
   unknown (short window / no traffic / no parseable answer), could-not-run (missing rows,
   `--turns 0`, `--launch` without `--live`, `--reps 3`), the recorded-cell replay, and the
   stop-reason vocabulary guard.

## Verdict-function contract (one sentence)

`shape_ok` when no turn in the window hit the completion ceiling, no stop reason is
`runaway_turn`/`turn_wall_cap`, and the arm's own contract produced a parseable answer;
`shape_degenerate` when a cap-length completion appears in the window (turn, token counts
and wall time named); else `shape_unknown`, never rounded to ok.

## Constraints observed

- No edit to `cell.py`, `run_longrun.py`, `PARM-1*`, the fixture, graders, analyser,
  `REQUEST-LEDGER.json`, any row file or published number. The 27 stopped-cell rows were
  read only.
- Exit codes imported from `longrun/exit_codes.py`; no new code invented. One documented
  departure from argparse: usage errors exit 3, not 2, because 2 is `shape_unknown`.
- Assumption recorded: the card's write path `measure/TRANCHE-CANARY.json` resolves to
  `experiments/ptr-engine/measure/TRANCHE-CANARY.json` (the experiment's measure root; no
  workspace-root `measure/` exists).

## Evidence

- `python -m pytest tests/test_tranche_canary.py -q` → `13 passed in 0.02s` (verdict PASS,
  sha `f17663d1`).
- Replay N=5 → exit 1, `shape_degenerate`, evidence `turn 3, completion_tokens 4096,
  max_tokens 4096, wall_ms 114838.846, stop_reason length`.
- Replay N=2 → exit 2, `shape_unknown`, `turns_observed 2`, zero requests.
