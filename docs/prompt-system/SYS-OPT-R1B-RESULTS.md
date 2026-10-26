# SYS-OPT round 1 (V1) — results

**Card:** `SYS-OPT-R1B` (`ad0c4cf8`) · **Version:** **V1** · **Executed:** `2026-10-24T12:00Z–12:30Z`
**Rule:** `docs/prompt-system/VERSIONS.md` §§0–11 (pre-registered) + Amendment A1 + **Amendment A2**
(this round's headline rule, change traceability, quality set and dense V0 re-pin).
**V1's single change:** `pointer_block.quote_tokens 0 → 40` (lever 1). Nothing else changed.

## What ran

| | |
|---|---|
| substrate | MoE `occamy-1.0` SGLang `:8012` (**O1**); dense `qwen3.5-9b` vLLM `:8014` (**O4**) |
| census | 2 models × 3 arms (P0, P1, P3) × 71 turns = **426 rows**; P2 withdrawn (A1.2) |
| prompt | **one artefact**: 213 (arm, turn) pairs rendered once and sent to both models; `prompt_byte_identity` **213/213, 0 mismatches** |
| integrity | 0 nulls, 0 non-200, `requests_sent == 1` and `corrections == 0` on **426/426** rows |
| quality | 40 probes/model (20 questions × P0/P1 form) against the frozen grader; V0 before = 20 P1-form probes/model at `quote_tokens=0`, same salt, same questions |
| requests | **525** (round) + **40** (V0 before-probe) = **565**; tool calls **33** |
| restores proven | `:8012` 200 `occamy-1.0` `max_model_len 131072`; `:8014` 200 `qwen3.5-9b` `max_model_len 32768`; no container started/stopped/restarted |

## Round 1 — per model, per arm (71 turns each)

| model | arm | n | mean unc/turn | bootstrap CI95 | hit (per-turn) |
|---|---|---|---|---|---|
| MoE | P0 (reference) | 71 | 593.549 | [549.254, 634.676] | 0.9046 |
| MoE | **P1 (headline)** | 71 | **652.831** | **[628.972, 671.690]** | **0.7622** |
| MoE | P3 (mid-edit control) | 71 | 630.831 | [563.930, 722.127] | 0.7897 |
| dense | P0 (reference) | 71 | 1896.986 | [1805.254, 1982.930] | 0.7254 |
| dense | **P1 (headline)** | 71 | **1893.169** | **[1776.606, 2004.141]** | **0.4028** |
| dense | P3 (mid-edit control) | 71 | 1916.690 | [1780.042, 2058.437] | 0.4023 |

Bootstrap: 10,000 resamples of the 71 turn indices, seed `20251024`, percentile interval. P0 and P3 are
**references**; only P1 is decisive (A2.1).

### Δ against V0 (paired by turn)

| model | V0 pin | V0 unc/turn | V0 hit | Δunc/turn P1−V0 | CI95 | hit gain | cost improves? |
|---|---|---|---|---|---|---|---|
| MoE | O1/P1, `cells/R2-PROMPT/O1/rows.jsonl` | 522.718 | 0.6950 | **+130.113** | **[+121.718, +138.394]** | **+6.72 pp** | **no — costs more** |
| dense | O4/P1, `cells/R2-PROMPT/O4/rows.jsonl` | 1664.352 | 0.1808 | **+228.817** | **[+140.310, +319.183]** | **+22.20 pp** | **no — costs more** |

**Instrument drift, measured by the untouched reference arm.** P0's bytes are identical to the pinned
P0 run, so its gap is drift, not treatment: MoE **+63.155** (P0 593.549 vs pin 530.394, +11.9 %),
dense **+13.127** (1896.986 vs 1883.859, +0.7 %). Drift-corrected Δunc/turn is therefore MoE **+66.958**
and dense **+215.690** — still a cost rise on both models, above the +45 falsification ceiling.
The hit gain is real but does not buy anything: the index grew, so a larger share of a larger prompt is
cached while the uncached tokens per turn also grew.

## Quality — frozen 20 questions, P0 and P1 form (before vs after)

| model | form | V0 (quote_tokens=0) | V1 (quote_tokens=40) | change |
|---|---|---|---|---|
| MoE | P1 (the form the change acts on) | **20/20 wrong (100 %)** | **20/20 wrong (100 %)** | **0 pp** |
| MoE | P0 | 20/20 wrong | 20/20 wrong | 0 pp |
| dense | P1 | **19/20 wrong (95 %)** | **18/20 wrong (90 %)** | **−5 pp** |
| dense | P0 | 20/20 wrong | 20/20 wrong | 0 pp |

Component rates explain it, and they are the useful part:

- **MoE:** P1 `span_ok` **0/20 → 0/20**, `sha8_ok` 20/20 → 20/20. The MoE **ignored** the new quote
  column and kept answering `length + sha8`; its V1 P1 answers are the V0 answers verbatim.
- **dense:** P1 `span_ok` **0/20 → 20/20**, `sha8_ok` **20/20 → 2/20**. The dense model **did** start
  quoting the span head — and stopped stating the `sha8`. The answer form moved to match P0's, at the
  cost of the hash the same question asks for.

**Recorded limitation of the frozen quality set** (kept frozen; fixed only for round 2, before it runs):
the question asks for *both* a span quote and the `sha8`, but the **P0 form has no index and therefore no
`sha8` to state** — that form is unanswerable by construction and scores 0/20 for every version. The
before/after comparison above is therefore read on the **P1 form**, where both quantities are available.

## A2's prediction — falsified on both models

| | predicted | measured | outcome |
|---|---|---|---|
| P1-form mismatch fall | ≥ 20 pp on both models | MoE **0 pp**, dense **−5 pp** | **fails the < 10 pp falsification floor on both** |
| Δunc/turn | no worse than +45 | MoE **+130.1** (+67.0 drift-corrected), dense **+228.8** (+215.7) | **fails on both** |

Per A2.2's pre-registered falsification the change is **reverted**: `quote_tokens` returns to 0 and the
lever may not be retried without a new measured finding (§8). Recorded, not dropped.

## Verdict line

**V1 = `no_signal`** — it improves on **neither** model: on both, the Δunc CI excludes zero but the mean
is **positive** (costs more), so the §2 cost condition fails even though the hit gain clears 2.0 pp.
Not adopted, not added to the release chain.

**CEILING DECLARED AT ROUND 1** (VERSIONS.md §4: `no_signal` declares the ceiling). Search stops; the
best version is **V0** (none was adopted); `closed_at_ceiling: true`, `ceiling_round: 1` are the closing
card's values to write into `state/sys-opt-verdict.json` — **this unit did not write that file** (card
step 7). No spare round was spent chasing noise, and no round 2 may run on this lineage without a
`DECISIONS` entry naming a measured lever and the remaining headroom.

**The paired release to ship is therefore V0's**: one prompt artefact (pointer index + append-only
newest delta, `pad_to:"none"`, `quote_tokens:0`) with per-model serving configs
**MoE = O1** (SGLang `:8012`, `f2efaaac…`) and **dense = O4** (vLLM `:8014`, `163a5db6…`).
