# UNIT `H1-CONDITIONING`

**Purpose.** Pre-register the reading of H1 **before** the grid exists: state, from the fixture's own
numbers, how the four arms' treatment onsets condition the frozen 48-turn p95, define the three readings
as callable row-selectors, and freeze the decision rule so the reading cannot be chosen after the
intervals appear. OFFLINE: zero inference requests, zero rows.

**Bound.** ≤22 tool calls, **0 requests**. **Status:** done (see handoff).

**Write paths (exactly).** `docs/H1-CONDITIONING.md`,
`experiments/ptr-engine/measure/H1-CONDITIONING.json`,
`experiments/ptr-engine/longrun/tests/test_h1_conditioning.py`,
`orchestration/units/H1-CONDITIONING.md`, `orchestration/handoffs/H1-CONDITIONING.json`,
`orchestration/journals/H1-CONDITIONING.jsonl`.

**Inputs (read-only).** `experiments/ptr-engine/measure/FIXTURE-TREATMENTS.json` (`ee91383c`),
`experiments/ptr-engine/longrun/analyze_stats.py` (imported, never copied: `min_n_for`, `rank_span`,
`quantile_ci`, `MIN_N`, `TAIL_MIN`), `docs/PARM-1-ERRATA.md` (the additive-errata pattern),
`docs/PREREG-ARM-RUN.md` (PARM-1's frozen H1 — **not edited**).

**Deliverables.** `docs/H1-CONDITIONING.md` (dilution arithmetic, three readings with n and selectors,
decision rule, PARM-1 errata **proposal** — not applied, guard, scope); `H1-CONDITIONING.json`
(machine-readable arithmetic + reading table); `test_h1_conditioning.py` (selector derivability, the
n≥60 claim guard, fire-turn verification against a synthetic 48-turn sample, one mutant red→green).

**Kill condition.** If the fire turns in the fixture cannot be reproduced from a row sample using only
row fields, STOP and report which arm's marker is unobservable — the readings would then not be
derivable from rows at all. — Not triggered: all four markers are row-observable (`evicted`,
`digest_at`, `lease`, `prefix_sha256`).
