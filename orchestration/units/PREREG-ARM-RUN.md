# PREREG-ARM-RUN — unit card (self-persisted)

**Purpose (one):** freeze the four-arm comparison before any v6 data exists — H1 (p95 TTFT), H2
(total prompt work per completed turn, primary), H3 (quality guard, 2 of 12 checkpoints), exact
endpoint sources, exclusion rules, the 8-cell decision matrix incl. "the thesis is dead", the
stopping rule, and a self-frozen `rule_sha256`.

**Bound:** ≤26 tool calls, zero inference requests, no network, no git. **Kill condition:** if the
12 checkpoint ids or arm names disagreed irreconcilably between fixture, config and rows, list the
disagreement and mark the affected axis unadjudicable instead of choosing silently. They did not
disagree irreconcilably: the ids agree (coverage doc ≡ `LR-01.v6.json`), but **existing rows carry
v2 ids** (`cp.t12/cp.t24/cp.t46`), so no existing row file can adjudicate H3 — recorded, not hidden.

**Write paths (only these):** `docs/PREREG-ARM-RUN.md`,
`experiments/ptr-engine/measure/PREREG-ARM-RUN.json`, `orchestration/units/PREREG-ARM-RUN.md`,
`orchestration/handoffs/PREREG-ARM-RUN.json`, `orchestration/journals/PREREG-ARM-RUN.jsonl`.

**Deliverable shape:** rule body delimited by `<!-- parm-rule:begin/end -->`; sha256 over that body
only, recorded outside it and in the JSON as `rule_sha256`; 4 arms × 48 turns/rep with reps
`PENDING: BUDGET-SCHEDULE`; H1 needs ≥60 usable timings per arm; exclusions E1–E4 only, an arm's bad
answer is never an exclusion; quality failure vetoes a latency win.

**Evidence commands:** read `analyze_stats.py`, `docs/CHECKPOINT-COVERAGE.md`, `RUN-C-V2` handoff +
row file, `LR-01.v6.json`; recompute rule digest (command in §8 of the doc).

**Result:** done — see `orchestration/handoffs/PREREG-ARM-RUN.json`.
