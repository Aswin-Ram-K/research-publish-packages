# V-INSTRUMENTS — independent recomputation of the three spending/gating instruments

**Unit:** V-INSTRUMENTS (verifier; author of none of the three instruments)
**Bound:** ≤36 tool calls, zero inference requests. **Used: 22. Requests sent: 0.**
**Mode:** automated, offline. No network, no `git`, repository read-only; every throwaway script lived in `/tmp` or was piped to `python3 -`.
**Prerequisites settled:** `REQUEST-LEDGER` (a2c4508e), `PROJECTION-CALIBRATION` (c0c7d1c8), `RECORD-STOP-REASON` (3f5f1ee7).

## Objective

Recompute, from `experiments/ptr-engine/measure/rows-*.jsonl` alone, the three harness instruments that
now decide what the project may spend and what may start:

| instrument | decides | recorded figure |
|---|---|---|
| `tools/request_ledger.py` | quota spent, gate exit `4` | 1,101 requests / 232 assumed_billed / 3,219 remaining, cap 4,320 |
| `cell.eval_gate_projection` (G2) | whether a live cell may start (exit `8`) | 0.03 s/token; 60 s per-turn default; refused at `projected > --max-wall` |
| `client.STOP_REASONS` | why every future turn ended | 10 closed-vocabulary members |

## Independence ordering (the whole point of the unit)

For **each** instrument: (1) my own script computed the quantity from the raw rows; (2) I recorded the
number; (3) only then did I read `request_ledger.py`, `cell.py` / `project_wallclock.py`, `client.py` /
`run_longrun.py`; (4) reconcile. No implementation file was opened before the corresponding number was
written down.

## Method per instrument

**A.** My costing rule: a row is a *request* iff it reached the wire — i.e. it carries `prompt_tokens`
(so a usage payload came back) **or** an HTTP-status error (the server rejected it, but saw it). Two
rows fail both and are excluded. Then compared with the tool's rule and induced exit `0/3/4/5` on the
real corpus (and on a deliberately corrupt `/tmp` row file for `5`).

**B.** Recomputed per-mode turn walls myself (`wall_ms/1000` when present, else `latency_s`, error rows
dropped, linearly interpolated percentiles), the aggregate and per-row seconds/token, the residual
spread, and then drove the *real* gate function `cell.eval_gate_projection` through a
`types.SimpleNamespace` at the `--max-wall` boundary ±1 s and against every flag that can move the
multiplier.

**C.** Induced all ten members through `client.derive_stop_reason` with my own fake inputs (not their
tests), then through the row writer `run_longrun.stop_reason_for_row`, and attempted three deliberately
wrong labels.

## Findings

Full detail: [`docs/V-INSTRUMENTS.md`](../../docs/V-INSTRUMENTS.md). Verdict and evidence:
[`orchestration/handoffs/V-INSTRUMENTS.json`](../handoffs/V-INSTRUMENTS.json).

## Outcome

- **A — pass.** 1,099 vs 1,101 requests (Δ −2, 0.18 %). The two extra rows are pre-flight setup
  failures that never reached the wire; their rule's `assumed_billed` bucket cannot tell those from an
  unmarked row that did. Direction: inflates spend, never understates it.
- **B — partial.** Every recorded number reproduces to 4 dp (Δ 0), and the boundary is exact. But the
  default multiplier is a single pooled 60 s: `--projected-from` defaults to `None` and nothing passes
  it, so a thinking cell is admitted on a wall 3.6× below its own measured p50.
- **C — partial.** 10/10 inducible; `runaway_turn` has no producer, a tool call with no finish chunk is
  labelled `empty_response`, and 0 of 1,101 rows carry `stop_reason`, so the historical cap-exhausted
  rows are *not* yet groupable.
- **overall — partial.** No number is wrong in a direction that changes a decision already made; two
  instruments have a gap that would change a *future* decision.

## Rules honoured

- Wrote no source; modified no row, grade, settled document, or instrument.
- Only the four declared write paths were created.
- Shas confirmed at end (see handoff `shas_unchanged`).
