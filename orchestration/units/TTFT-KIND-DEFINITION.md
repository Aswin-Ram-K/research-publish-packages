# Unit `TTFT-KIND-DEFINITION`

**One purpose:** decide, in writing and in code, which row kind defines per-turn TTFT, and measure what the decision changes in the published record.
**Mode:** offline, read-only over row files; **zero inference requests**. **Bound:** 26 tool calls (used 23 including handoff).
**Tag:** `automated` — no human answerer, no `ask_user_question`; conservative defaults recorded in the handoff.

## Why

`TURN-ROW-ATTRIBUTION` (PASS `f17663d1`) settled the row model: a turn with k follow-ups makes k+1 sends and has k+1 rows — `kind="turn-initial"` (`send_index=0`), k `kind="tool-followup"`, and the last follow-up as `kind="turn"`. So a tools-on cell has two candidate latency rows per turn, answering different questions. Without a stated definition, `analyze_stats.py` computed over **every row**, which both quoted the last follow-up and counted follow-up sends as extra turns (G8 published a p95 at n=70 on a 48-turn cell).

## Decision

> per-turn TTFT = the TTFT of the turn's own initial request: `kind="turn-initial"` when present, else the legacy `kind="turn"` row with `definition_fallback: true`; `kind="tool-followup"` is never a turn row.

Rationale, implementation, caller table, legacy policy and the both-definition tables: [`docs/TTFT-DEFINITION.md`](../../docs/TTFT-DEFINITION.md).
Measured impact artefact: [`experiments/ptr-engine/measure/TTFT-DEFINITION-IMPACT.json`](../../experiments/ptr-engine/measure/TTFT-DEFINITION-IMPACT.json).

## Write paths (exactly these)

`experiments/ptr-engine/longrun/analyze_stats.py` · `experiments/ptr-engine/longrun/tests/test_ttft_definition.py` · `docs/TTFT-DEFINITION.md` · `experiments/ptr-engine/measure/TTFT-DEFINITION-IMPACT.json` · `orchestration/units/TTFT-KIND-DEFINITION.md` · `orchestration/handoffs/TTFT-KIND-DEFINITION.json` · `orchestration/journals/TTFT-KIND-DEFINITION.jsonl` · `/tmp/**`.

Not touched: any rows file, any fixture, `run_longrun.py`, `client.py`, `grade_v5.py`, `docs/LATENCY-REPORT.md`, `measure/LATENCY-REPORT.json`, `PARM-1`. The n≥60 floor, the bootstrap (`RESAMPLES=10000`, `SEED=20261020`) and the disputed dedupe rule are untouched.

## Acceptance

- one selector `turn_latency_rows()` used by the arm p50/p95 path, the quantile-comparison values and the paired path;
- legacy cells resolve and every figure from them carries `definition_fallback` with a `mirrored_turns` count;
- tools-off cells bit-identical (verified against the published p50 for G1/G3/G4/G5/G6/G10);
- G7/G8/G9 reported under both definitions, side by side, with n and interval-or-refusal;
- tests discriminate both directions, and red→green is recorded without editing a file on disk;
- verdict row recorded before the handoff.
