# METRICS-V2 — five-metric dashboard under the frozen rule

**Objective.** Implement the operator-approved metrics (TTFT tail incl. p99/max, cached-share
trend by third, tokens- and time-to-verified-success, failure-charged aggregation, per-depth
checkpoint accuracy, false-claim rate) plus a per-file VALIDITY block, documented before any
valid curve exists. The frozen decision rule is untouched and not re-derived.

**Status.** done. Analyser, METRICS.md, handoff, this card.
**Hard bound.** 22 tool calls / one pass; no requests; read-only on row files.
**Write paths.**
- `experiments/ptr-engine/longrun/analyze_longrun.py`
- `experiments/ptr-engine/longrun/METRICS.md`
- `orchestration/handoffs/METRICS-V2.json`
- `orchestration/units/METRICS-V2.md`

**Result.** Stage 1 file → `INVALID-INSTRUMENT` (no `answer_source`, no `max_tokens`, completion
capped at 128, 99/192 rows missing TTFT); **metrics withheld, not averaged**. Policy file →
`VALID` but `PARTIAL` (16 rows, turns 1–4/48): explicit n per arm (3–7), no checkpoint reached so
TTVS is `NOT_VERIFIED` with worst-case charge, depth accuracy `NOT_OBSERVED`, false claims 0.
Pooling across `max_tokens` refused (shown on the unlisted `-fix` file, 4096 vs 16384). Growing-file
and truncated-last-line input handled.

**Next.** Re-run after the policy file reaches turn 46; TTVS and depth accuracy become defined.
