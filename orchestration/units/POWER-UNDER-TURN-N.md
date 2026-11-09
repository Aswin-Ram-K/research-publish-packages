# UNIT `POWER-UNDER-TURN-N`

**Card** `a0277b58-e5ff-4313-b315-ab26099bf86d`, execution `8af67fa7-f72b-4693-884f-031ee16a7f27`
**Tags** `automated` · `verdict` · **OFFLINE: zero requests, no network, no live cell**
**One purpose** re-derive the power verdict with the **turn** denominator the analyser actually uses, and
say plainly whether the 1,016-request grid can adjudicate H1.

## Why

`P95-POWER-FROM-ROWS` (PASS `f17663d1`) concluded `A* sufficient` from **request rows**. Four settled
cards changed the denominator: `ANALYSIS-CONSUMER-FIX` / `TTFT-KIND-DEFINITION` (per-turn TTFT = the turn's
own initial request, `n` = turns), `TURN-CENSUS-60` (max 48 turns/cell/arm, zero cells ≥ 60),
`LATENCY-REDERIVE-TRUNCATED` (n = 47/47/48 turns, not 68/70/72). A power claim whose `n` is not the
analyser's `n` is about a different measurement.

## Tasks and what each produced

1. Re-derive per-grid turn series with `analyze_stats.turn_latency_rows()` + `min_n_for(0.95)`; report arms,
   `n_turns` after dedup and after dropping `stop_reason ∈ {length, runaway_turn}`, turn-based p50/p95 with
   `quantile_ci` intervals or the **verbatim refusal**. → `cells_turn_n` in the artefact; §3 of the page.
2. Paired resampling at n ∈ {24,47,48,60,96,144} by **run-block** draws, request-n and turn-n side by side,
   disjointness fractions; block count and degeneracy stated. → `power` block; §4.
3. Three answers in order, each with its number. → `answers.a/b/c`; §5.
4. Verdict in the three allowed words. → **`grid_underpowered`**, `verdict_forcing_numbers`.
5. Price of the alternative at 1.374532, with the `PARM-1:150-152` four-arm constraint. → `price`; §6.
6. No analyser/threshold/`PARM-1`/grid-card/ledger/published-page edit; no live cell re-run.

## Declared write paths (exactly)

- `experiments/ptr-engine/measure/POWER-UNDER-TURN-N.json`
- `docs/POWER-UNDER-TURN-N.md`
- `experiments/ptr-engine/tests/test_power_under_turn_n.py`
- `orchestration/units/POWER-UNDER-TURN-N.md`
- `orchestration/handoffs/POWER-UNDER-TURN-N.json`
- `orchestration/journals/POWER-UNDER-TURN-N.jsonl`

No other path was written. Rows files are read-only and their sha256 recorded in the artefact.

## Hard bound

≤ 45 tool calls, ≤ 6 write paths, 0 inference requests, stop if `turn_latency_rows` cannot be imported or
if a required number is absent (then `not_derivable`, never a substitute). Bound used: 18 tool calls.

## Deliverable

Artefact + page + guard, verdict row `grid_underpowered` recorded before the handoff.
