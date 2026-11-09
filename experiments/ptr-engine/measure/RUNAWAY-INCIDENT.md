# RUNAWAY-INCIDENT — the queued-turn-5 evidence (LIVE-SMOKE-CELL, cancelled)

**Row file (evidence, never edited, never deleted):**
`experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T145758Z.jsonl`
Arm `pointer-stable`, 6 rows, manifest `longrun-2026-10-26T145758Z-pointer-stable-r1`.

## The five rows the card cites

| turn | ttft_ms | wall_ms | completion_tokens |
|---|---|---|---|
| 1 | 631.76 | 218,187 | — |
| 2 | 675.56 | 40,057 | — |
| 3 | 399.60 | 24,110 | 856 |
| 4 | 198.35 | 7,804 | 275 |
| **5** | **198.43** | **475,873** | **16,384** |

Turn 5 spent **7 m 56 s** and **16,384 completion tokens** — exactly `max_tokens=16384`, the
ceiling the runner was sending, with `thinking` on and nothing in the harness objecting.

## The row that makes the case a *second* runaway (not in the card's five)

| turn | ttft_ms | wall_ms | completion_tokens |
|---|---|---|---|
| 6 | 138.25 | 379,528 | 13,126 |

The cell was not stopped after turn 5; it went on to a second ~6 m 20 s, 13 k-token turn.
A `--runaway-turns 2` guard aborts on the second such turn instead of spending the budget.

## The measurement path is sound — these values say so

- `ttft_source = "first_delta"` on **every** row: TTFT was latched on the first streamed
  token, not derived from wall time.
- `first_token_kind = "reasoning"` on every row: the first token belonged to the reasoning
  channel, which is what the model actually emitted first.
- `cached_source = "prompt_tokens_details"` on rows 2–6 (row 1 is `null`: the first request
  of a cell has no cached prefix to report — absence, not zero).
- **No row has `ttft_ms == wall_ms`** (198.43 ms vs 475,873 ms on turn 5). The old defect
  that recorded the whole response as time-to-first-token is gone.
- `max_tokens = 16384` and `thinking = "auto"` on every row: the two defaults this card
  changes (now 4096 and `"off"`).

## What the defect was

*This cell was stopped by a human decision, not by the harness — which is the defect this
card removes.*

Nothing in the harness bounded a turn's wall clock or the number of runaway turns, and the
completion ceiling was a permissive 16,384 with thinking left on. A 48-turn cell at that
rate is hours of wall clock for 72 requests.
