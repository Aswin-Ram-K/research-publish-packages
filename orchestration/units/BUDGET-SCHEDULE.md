# UNIT `BUDGET-SCHEDULE` — priced plan for the 3,219 remaining requests

**Card:** `21254578-7b0e-4150-9c8f-3f89d31abdd8` · **Tag:** `[automated]` (no human, no questions, zero inference).
**Bound:** ≤28 tool calls, 0 requests. **Actual:** 13 tool calls, 0 requests, 0 network, 0 `git`, 0 artefact edits.
**Runs after:** `REQUEST-LEDGER` (`a2c4508e`, done) + `PROJECTION-CALIBRATION` (`c0c7d1c8`, done).

## Objective

Turn the measured budget into a priced plan: price full PARM-1, an H1-only run, and the historical
config-C reconnaissance shape in **requests and wall hours**; state H1/H2/H3 evaluability and the
discordant-pair arithmetic for each; recommend one with a harness-checkable stop rule; name what the quota
cannot fund. Consume artefacts — invent no number that can be read, and do not re-open PARM-1's thresholds.

## Inputs (read-only, unedited)

- `experiments/ptr-engine/measure/REQUEST-LEDGER.json` — `budget.cap` 4,320 · `budget.spent` 1,101 ·
  `budget.remaining` **3,219** · `total.requests` 1,101.
- Corpus kind histogram (`rows-*.jsonl`, 14 files): `turn` 801, `tool-followup` 68, unmarked 232 →
  **per-turn request factor 1.374532** (1,101 ÷ 801).
- `experiments/ptr-engine/measure/PROJECTION.json` — s/turn off p50 2.9 / p90 38.1 / mean 27.5 (n=960);
  on-auto p50 218.2 / p90 682.7 / mean 190.9 (n=9); s/completion-token 0.0338 / 0.0288 / 0.0349;
  policy wall 60 s; abort cap 180 s (not a per-turn wall).
- `docs/PREREG-ARM-RUN.md` (PARM-1) — H1 n ≥ 60 (lines 36–37), turns/arm = 48 (line 137), reps ≥ 2 at N=48
  (lines 142–144), thinking off (line 151), H3 2/12 = 16.7 pp (line 99), McNemar licence at b+c ≥ 6 (line 108),
  decidable < 8/12 ⇒ unadjudicable (line 113), 12 v6 checkpoint ids vs 3 v2 ids on disk (lines 156–163).

## Result

| schedule | turns | requests | wall off (mean / p90) | wall @60 s | remaining after | H1 | H2 | H3 |
|---|---|---|---|---|---|---|---|---|
| A — 4×60×3 | 720 | 990 | 5.50 / 7.62 h | 12.0 h | 2,229 | evaluable* | evaluable | evaluable |
| **A\* — 4×48×3** | 576 | **792** | **4.40 / 6.10 h** | 9.6 h | **2,427** | **evaluable** | **evaluable** | **evaluable** |
| B — 4×60×1 | 240 | 330 | 1.83 / 2.54 h | 4.0 h | 2,889 | knife-edge | evaluable | margin only |
| C — 4×48×1 | 192 | 264 | 1.47 / 2.03 h | 3.2 h | 2,955 | not evaluable (n=48) | evaluable | not evaluable |

\*A is only evaluable if the fixture is extended to 60 turns and PARM-1 is re-frozen — which this card forbids.
**Recommended: A\***, with the five stop predicates in the measure artefact (cap check per cell; 180 s turn
abort; ATTACK / V-GATE-CHAIN defect; after-rep-1 H3 veto saving 528 requests; decidable < 8/12).

**Discordant pairs:** A 36, A\* 36, B 12, C 3. b+c ≥ 6 is reachable for A and A\*, needs a 50 % flip rate at
B, and is **unreachable at C (≤3)**.

**Cannot fund:** a 20-rep/arm power grid (5,278 req), a fifth 3-rep grid (3,960), a paired quantile test at any
price (absent from `analyze_stats.py`), between-rep variance at 1 rep, thinking-on H1 (30.5 h mean / 109.2 h p90).

**Finding that reframes the card:** the quota is **not** binding — A\* costs 24.6 % of what remains. Wall time,
the frozen 48-turn grid, and the missing paired quantile test are the constraints.

## Deviation

The card's 60-turn shapes (A, B) contradict PARM-1 line 137 (`Turns per arm: 48`, fixture `N = 48`). Both
readings were priced; the 48-turn × 3-rep reading is recommended because the card forbids re-opening PARM-1.
The operator decision is recorded with its default (A\*; no re-freeze).

## Writes

`experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` · `experiments/ptr-engine/measure/budget-schedule.json` ·
`orchestration/units/BUDGET-SCHEDULE.md` · `orchestration/handoffs/BUDGET-SCHEDULE.json` ·
`orchestration/journals/BUDGET-SCHEDULE.jsonl`. Nothing else touched.
