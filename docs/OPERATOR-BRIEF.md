# Operator brief — p95 TTFT and tokens-to-verified-success (issue 4)

**Unit** `OPERATOR-BRIEF-4` · **2026-10-26T18:10Z** · **requests spent: 0**, network: none. Every figure is
re-derived today from the path beside it; a figure I could not re-derive is named as omitted. Companion:
`experiments/ptr-engine/measure/OPERATOR-BRIEF.json`.

## 1. Verdict

**Overall: not adjudicable.** Settling it needs one grid holding **all four arms**, ≥60 usable timings per arm, and
the 12 declared checkpoint ids in its rows (`docs/PREREG-ARM-RUN.md:150-152`, `:36-37`).

## 2. The three hypotheses

| | gate as frozen | verdict cell |
|---|---|---|
| **H1** latency | disjoint 95 % intervals at n ≥ 60, C's hi < A's lo (`docs/PREREG-ARM-RUN.md:33-40`) | **undecidable** — pointer-stable p50 **166.96** ms (n=47) vs transcript-grow **482.24** ms (n=48), gap **315.29** ms (`experiments/ptr-engine/measure/P95-POWER.json` `.per_grid_summary[0].p50_gap_ms`); no p95 interval exists at this n. The pair's two other grids show 32.39 and 11.99 ms. |
| **H2** cache cost | ≤ **0.95** × cache-inclusive **and** < 1.00 × uncached, per completed turn (`docs/PREREG-ARM-RUN.md:65-72`) | **undecidable** — the uncached limb changes sign between grids, so no single admissible grid satisfies both limbs; no ratio is printed. |
| **H3** quality | lose no more than 2 of 12 checkpoints (**16.7** pp), veto at b+c ≥ 6, either arm < 8 of 12 decidable → no verdict (`docs/PREREG-ARM-RUN.md:95-114`) | **not evaluable at this n** — 12 ids exist, but 3 are NONE items, so a constant `ANSWER: NONE` earns 3 free (`docs/PARM-1-ERRATA.md`); the four-arm run does not exist. |

## 3. Quality

- **Frozen `checkpoint_accuracy`: 2 of 66 cells** (2 passes / 66 cells, 8 documents —
  `experiments/ptr-engine/measure/PROSE-VALUE-METRIC.json` `.population.n_frozen_pass`, `.n_cells`). It governs those
  8 `cell-*.grade-v5.json` documents generated at/after 15:56Z.
- **Value-aware beside it: 4 of 66** — the frozen rule missed **2**, and **4** asserted values are wrong
  (`.overall.frozen_nonpass_right`, `.frozen_nonpass_wrong`). Whether prose asserting a value counts is still open
  (`orchestration/handoffs/V-REASON-MIX.json`).
- Grid-wide: **3/25** = **12.0** % grade_v5 checkpoint grid; **5/43** det_verify, sha `12ccc74e…`, partial grid
  (`docs/QUALITY-ERAS.md` §5). Neither moves.

## 4. Cost

- **p50 ms (G4)** — `experiments/ptr-engine/measure/P95-POWER.json` `.sets`: lease-reopen **136.17** (n=34),
  pointer-stable **166.96** (n=47), transcript-compact **202.49** (n=48), transcript-grow **482.24** (n=48). No
  interval is printed: none was re-read today as one.
- **p95 comparisons between two arms: zero.** Every p95-bearing grid is single-arm, and the tools-grid p95 is
  withdrawn with no replacement (`experiments/ptr-engine/measure/WITHDRAWN.json` `WI-004`); n=48 is refused by the
  frozen floor, not caveated.
- **`tokens_to_verified_success`: 3 event / 20 censored** of 23 pairs; all events are pointer-stable at `cp.0.t12`
  (`experiments/ptr-engine/measure/TVS-CENSORED.json` `.counts`). A censoring statement for three arms, a number for
  one; no mean, median or imputation over a censored set.

## 5. The plan and its price

Tranche 1 = **PAIR-3+CTX-2**: 4 arms, pair at 3 reps, context at 2 reps = **480** turns / **660** requests, leaving
**2,559** of **3,219** (`experiments/ptr-engine/measure/price-replication.json` `.budget`).

- **Promote** to PAIR-6+CTX-2 only if pooled p95 intervals separate C-lower **and** all three reps' p50 gaps ≥ 100 ms
  (`.decision_rule.step_3_promote`).
- **Stop:** no 792 grid if those intervals overlap or any rep's p50 gap < 100 ms (`.step_4_stop_no_replication`).
- **Hard constraint:** `docs/PREREG-ARM-RUN.md:150-152` requires all four arms in the same grid, so a pair-only grid is
  **not an admissible H1 verdict** — hence the context arms, bought at 2 reps.

## 6. Blockers

- **Gate chain fails**: `orchestration/handoffs/V-GATE-CHAIN-3.json` — six operands bypass the projection gate.
  Unblock: one class-shaped operand validation, then a fresh verifier.
- **Spawn rule, verifier in flight**: `orchestration/handoffs/V-SPAWN-DECLARE.json` partial — a refusal record must
  declare every spawn the oracle saw (`experiments/ptr-engine/measure/PREFLIGHT-SPAWN-DECLARE.json`).
- **The tree moved**: `cell.py` no longer matches its pin
  (`experiments/ptr-engine/measure/TREE-FREEZE.json` `.card_pin_recheck.files[0].matches_card_pin` false), and
  `V-TREE-FREEZE.json` is partial (classify BEFORE). Unblock: fix D1, re-freeze.
- **Fixture v8 re-freeze: done** — `V-FIXTURE-V8.json`; `experiments/ptr-engine/measure/V8-DRYRUN-REFREEZE.json` sha
  `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641`.
- **Quality register**: `orchestration/handoffs/GRADE-V5-REPAIR.json` partial (`graded_n` counts non-answers);
  `V-REASON-MIX.json` partial.

## 7. Superseded — do not cite

| withdrawn | replacement |
|---|---|
| "≈466 requests" | 1,101 used / 3,219 left (`experiments/ptr-engine/measure/REQUEST-LEDGER.json` `.budget`) |
| 1,071 requests, 3,249 left | 1,101 / 3,219; the 30-row deduction is **not applied** (unsound; same file `.deduction`) |
| `55/64 wilson95 0.8594` | withdrawn: 3/3 for that run, wrong denominator (`experiments/ptr-engine/measure/WITHDRAWN.json` `WI-003`) |
| `p95 318.14 n=68` | **withdrawn, no replacement** (`experiments/ptr-engine/measure/WITHDRAWN.json` `WI-004`) |
| "5/43 mixes grader eras" | withdrawn charge; 5/43 reproduces under det_verify sha `12ccc74e…` (`WI-005`) |
| `217k` prompt | turn 48 = 2,197 tokens; corpus max 51,216 (`WI-006`) |
| "384 requests" | 660 for tranche 1 (`experiments/ptr-engine/measure/price-replication.json` `.budget`) |

## 8. What would change my mind

1. One four-arm grid with disjoint pooled p95 intervals and all three p50 gaps > 100 ms → H1 `has evidence`.
2. Two further grids reproducing the **315.29** ms gap (`experiments/ptr-engine/measure/P95-POWER.json`
   `.per_grid_summary`), not one grid's luck.
3. Pointer-stable ≥ 8 of 12 decidable and losing > 2 checkpoints → H3 veto kills the latency win
   (`docs/PREREG-ARM-RUN.md:110-114`).
