# U-SPCC-47 — The measured noise floor, and which E1 clauses survive it

Read-only analysis plus documentation. No code, row, fixture or prereg-prediction edit.
0 endpoint requests, 0 model calls.

## 0. What was measured

`U-SPCC-45` compared two runs of the **same** arm on **byte-identical** prompts:

| | A | B |
|---|---|---|
| file | `experiments/ptr-engine/measure/rows-e1-spcc-2026-11-10.jsonl` | `experiments/ptr-engine/measure/rows-e1-final-2026-11-10.jsonl` (spcc rows) |
| commit | `e18a587` | `e4692f8` |
| value / contract | 20/48 · 19/48 | 22/48 · 21/48 |

`prompt_sha256` and `prompt_tokens` equal at all 100 turns; `fixture_sha256` identical
(`f0a636fea0f82b152e8d23f0f51a9fb0f38479eabd40290e73bd98ebd3e620c3`). Answers differ at
**6/100 turns**: T5, T41, T52, T57, T60, T80. **2 of the 6 are scored checkpoints** — T57
`cp.TX-03.f06.d5` (A `NONE`, B `NUM 3501`) and T60 `cp.TX-03.f06.d8` (A `NONE`, B `NUM
3503`) — and those two are the **entire** 20/48→22/48 value delta and the entire
19/48→21/48 contract delta.

Mechanism: `cached_tokens` differ at **26/100 turns** on identical prompts (79,808 vs
81,024 total; 22 of 26 higher in B). `git log e18a587..e4692f8` touches only
`run_longrun.py`; no hunk is in `Planner` (`run_longrun.py:1474`) or any prompt-construction
code; the `run_cell` hunks are the `CapRefusal`/`BudgetExhausted` exits and neither fired
(`error=None`, `cap_refused_mid_turn=None` on all 200 rows).

## 1. Per-distance buckets, recomputed from the rows

Scored with `longrun/score_longrun.py:score_answer_contract_rows` (the authoritative path:
`value_ok = (exp_int is not None and vv is not None and vv == exp_int)`,
`contract_ok = (ak == "NUM" and value_ok)` at `score_longrun.py:1232-1234`). 8 checkpoints
per bucket, 48 per arm.

| distance | `spcc` value · contract | `masking-no-fetch` | `bounded-context-fetch` | gap `spcc`−masking (value · contract) | vs ±2 band |
|---|---|---|---|---|---|
| d2 | 7/8 · 6/8 | 8/8 · 8/8 | 5/8 · 5/8 | −1 · **−2** | **inside** (exactly 2) |
| d5 | 4/8 · 4/8 | 0/8 · 0/8 | 0/8 · 0/8 | **+4** · **+4** | outside |
| d6 | 5/8 · 5/8 | 0/8 · 0/8 | 0/8 · 0/8 | **+5** · **+5** | outside |
| d8 | 4/8 · 4/8 | 0/8 · 0/8 | 0/8 · 0/8 | **+4** · **+4** | outside |
| d20 | 2/8 · 2/8 | 0/8 · 0/8 | 0/8 · 0/8 | **+2** · **+2** | **at the edge** (exactly 2) |
| d32 | 0/8 · 0/8 | 0/8 · 0/8 | 0/8 · 0/8 | 0 · 0 | inside (no effect) |
| **total** | **22/48 · 21/48** | **8/48 · 8/48** | **5/48 · 5/48** | **+14** · **+13** | outside |

Gap `spcc`−fetch: d2 +2 value / +1 contract; d5 +4; d6 +5; d8 +4; d20 +2; d32 0.

The `d2` value gap is −1 and the `d2` contract gap is −2; the contract gap is the one
`U-SPCC-44` reported as "6/8 vs 8/8". The single value/contract divergence is T70
`cp.TX-03.f08.d2`, answered `ANSWER: TEXT 3700` — right value, wrong kind, so it counts for
value and not for contract.

## 2. Clause-by-clause survival

E1's preregistered prediction: *"`spcc` scores ≥ fetch on single-fact and > masking
everywhere; billed tokens ≤ masking."*

| clause | observed | vs the ±2/48 band | verdict |
|---|---|---|---|
| `spcc` ≥ fetch on single-fact | fetch arm never fetched (43/48 checkpoints stranded, `tools_mode: off`) | — | **unadjudicable** (unchanged) |
| `spcc` > masking **everywhere** | `d2` 6/8 vs 8/8 (contract); `d32` 0/8 vs 0/8 | the only failing bucket is `d2` at −2, **exactly the measured flip magnitude** | **not adjudicable** — inside the band, not a clean falsification |
| billed ≤ masking | 9,066 vs 9,730 (billed over the 48 answer turns) | 664-token gap vs **1,216-token** cache-driven variation between two runs of the same arm on identical prompts | **not adjudicable** — inside the band |
| `spcc` > masking on the aggregate | 22/48 vs 8/48 | 14 checkpoints = **7× the band** | **survives** |
| falsifier: "not strictly above masking on any class" | `d5` 4>0, `d6` 5>0, `d8` 4>0, `d20` 2>0 | gaps of 4–5, outside the band | **did not fire** (unchanged) |

Stated without softening: the "everywhere" clause is **not** a clean falsification and the
billing clause is **not** a clean hold. Both are inside the noise band. The aggregate
advantage is real and large. The falsifier stays silent.

## 3. Power and request cost

Measured flip rates: per-turn **6/100 = 0.06**; per-scored-checkpoint **2/48 = 0.041667**.

For a two-arm difference over 48 checkpoints, `Var(D) = 48·p` under iid flips, so
`sd(D) = sqrt(48p)`. A 2-checkpoint gap is:

- at `p = 2/48`: `sd = 1.414` checkpoints → **1.41 sd**, two-sided p ≈ 0.157
- at `p = 0.06`: `sd = 1.697` checkpoints → **1.18 sd**, two-sided p ≈ 0.239

Neither is significant. For 80 % power at two-sided α = 0.05 (`z = 1.96 + 0.84 = 2.80`),
`sd_R = sd/sqrt(R)`:

| reps | sd (p=2/48) | z | power | cost (3 arms × 100 turns) |
|---|---|---|---|---|
| 1 | 1.414 | 1.41 | 0.29 | 300 |
| 2 | 1.000 | 2.00 | 0.52 | 600 |
| 3 | 0.817 | 2.45 | 0.69 | 900 |
| **4** | **0.707** | **2.83** | **0.81** | **1,200** |
| 5 | 0.632 | 3.16 | 0.89 | 1,500 |
| **6** | **0.577** | **3.46** | **0.93** | **1,800** |

At the conservative turn-level rate `p = 0.06`, 80 % power needs **6 reps** (z = 2.89,
power 0.82) = **1,800 requests**; 5 reps gives only 0.75.

**Answer: 4 reps (iid checkpoint rate) to 6 reps (turn-level rate), costing 1,200–1,800
requests for three arms × 100 turns.**

**Does it fit?** Yes. Live ledger headroom, recomputed with
`request_ledger.build_report(paths, 12094, 0, 0)` over all `measure/rows-*.jsonl`:

```
{'cap': 12094, 'spent': 8412, 'spent_deduplicated': 8382, 'remaining': 3682,
 'remaining_raw': 3682, 'remaining_deduplicated': 3712, 'within_budget': True}
```

1,200–1,800 ≤ 3,682 (raw) and ≤ 3,712 (deduplicated). **It fits, with 1,882–2,482 requests
to spare.** The 4,013 figure quoted in the ticket is **stale**: it was the headroom at
`U-SPCC-39` (`orchestration/units/U-SPCC-39.md:63`), before the E1 cell spent 331. Against
4,013 it also fits, with 2,213–2,813 to spare.

The cost is 2.4–3.6× E1's preregistered 200–500 request ceiling. That is the open decision.

## 4. Open decision (operator)

Whether E1's ceiling (200–500 requests) and its `reps=1` shape are amended to admit a
powered design. The arithmetic says a powered E1 fits the ledger; the prereg says it does
not fit the ceiling. **Not decided here.** The prereg's prediction, falsifier, controls and
ceiling are unedited; the deviation note added under E1 is additions-only
(`git diff --numstat` → `35 0`).

## 5. Writes

- `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` — one 7-column row
  (column histogram 15×10 / 7×3 / 17×7 → 15×10 / 7×3 / **18×7**)
- `docs/STATE.md` — §"Measured noise floor"
- `journal/2026-11-10.md` — §"U-SPCC-47"
- `orchestration/STATUS.md` — §"U-SPCC-47"
- `experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md` — `### Deviation note —
  2026-11-10, measured noise floor` under E1, additions only
- `orchestration/units/U-SPCC-47.md`, `orchestration/handoffs/U-SPCC-47.json`

No row file, fixture, `ptr_engine/layers.py`, `longrun/arm_cd.py`, `longrun/claim_mode.py`
or `longrun/cell.py` was touched.
