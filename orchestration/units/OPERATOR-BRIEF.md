# UNIT `OPERATOR-BRIEF`

**Persisted 2026-10-26.** Consolidated from settled cards `LATENCY-REPORT` (`9bf0d318`), `PUBLISHED-NUMBER-AUDIT` (`5c30dad8`), `REQUEST-LEDGER` (`a2c4508e`); rule source `PREREG-ARM-RUN` (`97788db8`). Offline: zero inference requests, no network, no `git`.

## Purpose

One page a human can read that answers where the operator's claim stands: *minimise p95 TTFT and tokens-to-verified-success over long runs at equal-or-better verified quality* (board #438 / FINAL-GOAL `a2b5ff2d`).

## Method

- Read the three source units' handoffs and the artefacts they published; recomputed nothing from prose where an artefact was readable.
- Headline cells taken from `experiments/ptr-engine/measure/LATENCY-REPORT.json` (`.cells`, grid `G4`), with `p95` refusals quoted verbatim.
- H2's uncached limb computed directly from `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` (and the v3/v4/baseline grids for the sign test), because `PREREG-ARM-RUN.json` records the cache-inclusive figure only.
- Quality denominators taken from `experiments/ptr-engine/measure/MATRIX-HONESTY.json` (`.accuracy`), not from any document.
- PARM-1 gate text taken from `experiments/ptr-engine/measure/PREREG-ARM-RUN.json` (`rule_sha256 21cb85…98ec8`).
- Spend taken from `experiments/ptr-engine/measure/REQUEST-LEDGER.json` (`.budget`, `.total`).
- Instrument causes taken from `experiments/ptr-engine/measure/ANSWER-DEGENERACY.md` §4.

## Result

`docs/OPERATOR-BRIEF.md` (2 pages) and its JSON twin `experiments/ptr-engine/measure/OPERATOR-BRIEF.json`. Overall verdict: **not adjudicable**; missing measurement named as one LR-01.v6 grid, 4 arms × 48 turns × ≥2 reps, 384 requests.

## Assumptions recorded

1. `board #757` was not readable from this unit's offline surface (board search returned no match; no card ids for that path are on disk). The brief therefore names the three gates from the settled artefacts' own `pending` / `next_unit_hint` fields and says so in place.
2. `BUDGET-SCHEDULE` (`21254578…`) has no handoff on disk, so its section is `PENDING` with what it will change, per the card.
3. "Prompt tokens per completed turn" = `prompt_tokens` summed over counted rows ÷ counted rows (48 per arm in `G4`); the analyser's `n_turn`, not `n_rows`, is the denominator for `G7`–`G9`.
4. `uncached` = `prompt_tokens - cached_tokens`, with `cached_tokens` present on all 48 rows of every RUN-C arm (0 missing), as PARM-1 `secondary_field` defines.

## Bound

≤22 tool calls, zero requests. Handoff written `partial` at call 4, then finalised.
