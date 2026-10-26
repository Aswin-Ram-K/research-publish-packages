# CLAIM-SENSITIVITY.md — do the 13 BLOCKED claims actually move?

**Verdict: 13 claims re-measured three ways offline — SURVIVES 1 / MOVES 12 / UNDECIDABLE 0.**
No number in `CLAIMS.md` is edited here; this file states only whether each published figure is stable under the rows the calibrated detector flags. Zero live requests, no endpoint, no GX10, no model lock.

## Rule, stated before the numbers

- **Repair (primary estimator).** The detector's model is *stale* credit: the fired row records the previous turn's cache state, so its gap is inflated by ~one quantum. Copying the previous credit row's `cached_tokens` is therefore a **tautological no-op** — the fired row already holds that value (verified: every repair-by-copy changed nothing). The determinate repair uses the invariant `uncached = prompt_tokens − cached` with the detector's own baseline: `cached_true = prompt_tokens − baseline_gap_p25(arm)`. `prompt_tokens` is never touched, so prompt aggregates cannot move (confirmed on C23: prompt means identical to 4 dp).
- **Exclusion** drops flagged rows. It is reported for every claim but is a *sample* change, not an estimate of the same quantity (dropping turns changes turn-window means), so it cannot by itself decide a verdict.
- **Verdict.** SURVIVES if every published component stays within **±1 %** of its published point value under repair (none of these 13 carries a published CI); MOVES if any leaves; UNDECIDABLE if the repair is not determinate. Repair is determinate for all 13, so none is UNDECIDABLE.
- `gcd_cached` is excluded from the verdict: a base-gap repair is not quantised, so `gcd → 1` there is a repair artefact, not evidence about the cell.

## The 13 rows

| id | published | excluded | repaired | verdict |
|---|---|---|---|---|
| C17 | arm R mean uncached/turn = 1279.3000 | 1155.9697 | 1118.5250 (**-12.57 %**) | MOVES |
| C18 | arm F mean uncached/turn = 1177.0000 | 1151.3684 | 1124.2000 (**-4.49 %**) | MOVES |
| C19 | arm A mean uncached/turn = 752.4250 | 733.9744 | 728.2750 (**-3.21 %**) | MOVES |
| C20 | arm C mean uncached/turn = 763.0750 | 728.6316 | 716.1250 (**-6.15 %**) | MOVES |
| C21 | A/R ratio = 1.7002 | 1.3326 | 1.5359 (**-9.67 %**) | MOVES |
| C22 | break share of R excess = 0.0785 | 0.1549 | 0.1006 (**+28.15 %**) | MOVES |
| C23 | arm R mean uncached, turns 19-34 = 1659.9375 | 1538.4000 | 1314.7500 (**-20.80 %**) | MOVES |
| C24 | R / break-only counterfactual = 1.0680 | 1.0239 | 1.0389 (**-2.72 %**) | MOVES |
| C44 | E/F mean gross break cost = 1.0385 | 1.0385 | 1.0385 (**+0.00 %**) | SURVIVES |
| C46 | S1 mean uncached/turn = 740.4000 | 727.3000 | 720.4000 (**-2.70 %**) | MOVES |
| C47 | mean uncached/turn = 739.2000 | 715.9000 | 705.7000 (**-4.53 %**) | MOVES |
| C50 | V1 mean uncached/turn = 2230.8000 | 2135.4000 | 2104.2000 (**-5.68 %**) | MOVES |
| C51 | vLLM/SGLang ratio = 3.0740 | 3.0320 | 3.0180 (**-1.82 %**) | MOVES |

## Worst-case shift

Biggest relative move under the primary (repaired) estimator: **C22 — break share of R excess, 0.0785 → 0.1006, +28.15 %**. Biggest headline move on a claim statistic: **C23 arm R mean uncached 1,659.9375 → 1,314.75 (−20.80 %)**; C21's A/R falls 1.700 → 1.536 (margin over the 1.5× test nearly gone) and R/F collapses 1.0869 → 0.9950 (parity).

## What SURVIVES, and why it is not luck

**C44** is the only claim that cannot move: all six G1 break events sit on **cold-miss rows (`cached_tokens = 0`)**, which the detector never flags (`break_rows_flagged = 0`), and the published quantity is `uncached − (prompt % 64)`. Fired rows exist on F (13/132) but none of them is a break row, so both means, the E/F ratio and the 2/6-within-10 % count are bit-identical under all three recomputes. `REMEASURE-G1-BREAK` is therefore not needed for C44 as published.

## What MOVES — direction only, no number edited

| claim | published | corrected direction (repaired) | card that would re-run it live |
|---|---|---|---|
| C17 | 1279.3000 | arm R mean uncached/turn **1,279.3 → 1,118.5 (−12.57 %)**, hit .7373 → .7703 (+4.5 %): R was *over*-credited, so A/R shrinks | `REMEASURE-U15` |
| C18 | 1177.0000 | arm F mean uncached/turn **1,177.0 → 1,124.2 (−4.49 %)**, hit .7627 → .7733 | `REMEASURE-U15` |
| C19 | 752.4250 | arm A mean uncached/turn **752.4 → 728.3 (−3.21 %)**, hit .9270 → .9293 | `REMEASURE-U15` |
| C20 | 763.0750 | arm C mean uncached/turn **763.1 → 716.1 (−6.15 %)**, hit .9243 → .9290 | `REMEASURE-U15` |
| C21 | 1.7002 | **A/R 1.7002 → 1.5359 (−9.66 %)** — still above the 1.5× test but with ~2 % margin instead of 13 %; **R/F 1.0869 → 0.9950** (R and F at parity, not "within 8.7 %"); gap 8.69 % → −0.50 % | `REMEASURE-U15` |
| C22 | 0.0785 | break share **.0785 → .1006** (+28.2 %), steady .9215 → .8994: break cost is ~10 %, not 7.8 % | `REMEASURE-U15` |
| C23 | 1659.9375 | R **1,659.94 → 1,314.75 (−20.8 %)** on an unchanged 5,811.94 prompt; C 754.94 → 699.56; F 1,678.94 → 1,546.94; A unchanged | `REMEASURE-U15` |
| C24 | 1.0680 | counterfactual R **32,143 → 30,265 (−5.84 %)**, R/cf-A **1.0680 → 1.0389** | `REMEASURE-U15` |
| C46 | 740.4000 | S1 unc/turn **740.4 → 720.4 (−2.70 %)**, 32k 729.2 → 710.22, 64k 746.01 → 725.51, hit .974202 → .974899; S2 752.6 → 745.1 (−1.00 %) | `REMEASURE-WIN-SGL` |
| C47 | 739.2000 | unc/turn **739.2 → 705.7 (−4.53 %)**, 32k 725.74 → 697.3, 64k 746.01 → 709.85, hit .974242 → .975412 | `REMEASURE-G3-S0` |
| C50 | 2230.8000 | V1 unc/turn **2,230.8 → 2,104.2 (−5.68 %)**, hit .869037 → .876468; V2 2,246.0 → 2,162.8 (−3.70 %) | `REMEASURE-WIN-VLLM-V1` |
| C51 | 3.0740 | ratio **3.074× → 3.018× (−1.82 %)**; S0 32k 725.74 → 697.3, V1 2,230.8 → 2,104.2 — vLLM is still ~3× SGLang, so the qualitative cross-stack claim holds while every published figure shifts | `REMEASURE-G3-S0 + REMEASURE-WIN-VLLM-V1` |

All 12 MOVES are **in the same direction**: the flagged credit *over*-states `cached_tokens`, so published `hit` is too low and published `uncached` is too high. The correction is therefore conservative for the paper's "cache is not free" reading and *un*-conservative for U15's 1.700× headline, which loses ~10 %.

## As-published reproduction

All 13 recompute to the published values from `rows.jsonl` (mismatch list empty for all 13). One cosmetic note: `recompute.py` rounds `break_share` to 4 dp (0.0785) while `CLAIMS.md` prints 6 dp (0.078454) — same number, not a discrepancy.

## Method and bounds

- Detector: `tools/audit/cached_dedupe.py`, whole-file per-arm grouping — reproduces the handoff's fire counts exactly: U15 R 7/40, F 2/40, C 2/40, A 1/40 · G1 F 13/132, E 1/132 · G3 A 8/222, C 7/222, H 7/222, R 7/222 · WIN-SGL A 6/444, R 5/444, C 4/444, H 4/444 · WIN-VLLM A/C/H/R 14/142 each.
- Recompute: `papers/context-cache/recompute.py` functions called unchanged, with only `rows()` monkey-patched to serve the variant row lists, so every formula is the published one. C44 is recomputed from rows with its `analysis.json` definition (`cost_gross = uncached − (prompt % 64)`).
- Baseline gaps used for repair: U15 A 506.0/C 478.5/F 608.0/R 942.0, WIN-SGL A 479.8/C 485.0/H 482.0/R 481.0, G3 A 476.0/C 476.0/H 477.0/R 477.0, WIN-VLLM A 1984.0/C 1982.0/H 1983.0/R 1960.0.
- 0 live requests; no GX10, no endpoint, no model lock. Writes confined to this file, `state/logs/claim-sensitivity.json`, `orchestration/handoffs/CLAIM-SENSITIVITY.json`, `orchestration/units/CLAIM-SENSITIVITY.md`; `CLAIMS.md`, `MANUSCRIPT.md`, `EVIDENCE.md`, `RUN.json`, `recompute.py`, `CLAIM-HEALTH.md` and all tests untouched.
