# Lazy loading vs. inlining — where does the billed-token crossover sit?

**Verdict: NEGATIVE.** Lazy loading (a compact index plus an on-demand `FETCH` tool) does
not beat inline loading on billed tokens anywhere in the 3 k–30 k character range once the
prefix is warm: the warm-prefix decision number is negative in 5 of 6 measured cells, and
the single positive one is a cell where the serving stack reports no cache statistics at
all.

This is a crossover **location** run, not a significance test: **1 rep per cell**. Nothing
here is a confidence interval, and no corpus, task or rep count was tuned to reach a number.

Status: **complete** — all 12 grid cells measured (24 runs, 65 request rows), no cell
dropped.

---

## 1. What was measured

| Axis | Values |
|---|---|
| Corpus size (sum of item body characters, exact and asserted) | **3,000** and **30,000** |
| Needed fraction | **2-of-12** at both sizes; **6-of-30** at 30 k only |
| Arms | **C0** = every item body inlined · **L1** = compact index + one text-emulated `FETCH <id>` tool |
| Cache state | **COLD** = fresh nonce on every request, so no prefix can be reused · **WARM** = steady prefix, no nonce; round 1 primes, later rounds are served from it |
| Models | `occamy-1.0` (SGLang, `:8012/v1`) · `qwen3.5-9b` (vLLM, `:8014/v1`) |
| Reps | **1** |
| Protocol | **text-emulated `FETCH <id>` / `ANSWER` on both models** (`protocol=text_emulated` on every L1 row), so the cross-model comparison carries no tool-calling confound |
| Runs | 24 (3 corpus cells × 2 arms × 2 cache states × 2 models) |

Corpora regenerate byte-for-byte from `SEED = 20261024` (`cx_corpus.py`). The harness
asserts per cell that the body total is **exactly** the target size, that every needed fact
sentence is in the C0 prompt, that **no** fact value or fact sentence appears in the L1
index, and that the task text never names an item id — `python3 cx_harness.py` →
`SELFCHECK PASS`.

Neither server was restarted and `/flush_cache` was never called. Cold isolation is by
per-request nonce alone, and `cached_tokens / prompt_tokens` proves the regime per row
rather than asserting it.

---

## 2. Per-cell results

`uncached = prompt − cached`. A **B** in the last column means the server returned
`prompt_tokens_details: null` — the cache instrument is **blind**, not a miss. In a blind
cell `uncached = prompt`, so it is an **upper bound** on billed tokens.

| model | items | corpus | cache | C0 prompt | C0 cached | **C0 uncached** | L1 prompt | L1 cached | **L1 uncached** | req (C0/L1) | fetches | fetched body chars | **saving_billed** | saving_prompt | C0 correct | L1 correct |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|
| occamy-1.0 | 12 | 3,000 | cold | 1,045 | 0 | 1,045 | 2,161 | 0 | 2,161 | 1/3 | 2 | 450 | **−106.8 %** | −117.5 % | 2/2 | 2/2 B |
| occamy-1.0 | 12 | 3,000 | warm | 1,025 | 64 | 961 | 2,104 | 1,920 | 184 | 1/3 | 2 | 450 | **+80.8 %** | −116.2 % | 2/2 | 2/2 |
| occamy-1.0 | 12 | 30,000 | cold | 6,488 | 0 | 6,488 | 3,578 | 0 | 3,578 | 1/3 | 2 | 4,953 | **+44.9 %** | +25.8 % | 2/2 | 2/2 B |
| occamy-1.0 | 12 | 30,000 | warm | 6,471 | 6,464 | 7 | 3,516 | 3,008 | 508 | 1/3 | 2 | 4,953 | **−7,157.1 %** | +26.5 % | 2/2 | 2/2 |
| occamy-1.0 | 30 | 30,000 | cold | 7,065 | 0 | 7,065 | 13,822 | 0 | 13,822 | 1/7 | 6 | 5,952 | **−95.6 %** | −116.7 % | 6/6 | 6/6 B |
| occamy-1.0 | 30 | 30,000 | warm | 7,046 | 7,040 | 6 | 15,812 | 14,400 | 1,412 | 1/8 | 7 | 5,952 | **−23,433.3 %** | −145.5 % | 6/6 | 6/6 |
| qwen3.5-9b | 12 | 3,000 | cold | 1,044 | 0 | 1,044 | 2,165 | 0 | 2,165 | 1/3 | 2 | 450 | **−107.4 %** | −118.1 % | 2/2 | 2/2 B |
| qwen3.5-9b | 12 | 3,000 | warm | 1,025 | 0 | 1,025 | 2,104 | 0 | 2,104 | 1/3 | 2 | 450 | **−105.3 %** | −116.2 % | 2/2 | 2/2 B |
| qwen3.5-9b | 12 | 30,000 | cold | 6,489 | 0 | 6,489 | 3,576 | 0 | 3,576 | 1/3 | 2 | 4,953 | **+44.9 %** | +25.8 % | 2/2 | **0/2** |
| qwen3.5-9b | 12 | 30,000 | warm | 6,471 | 0 | 6,471 | 3,516 | 0 | 3,516 | 1/3 | 2 | 4,953 | **+45.7 %** | +26.5 % | 2/2 | 2/2 B |
| qwen3.5-9b | 30 | 30,000 | cold | 7,065 | 0 | 7,065 | 13,724 | 0 | 13,724 | 1/7 | 6 | 5,952 | **−94.2 %** | −115.3 % | **0/6** | 6/6 B |
| qwen3.5-9b | 30 | 30,000 | warm | 7,046 | 0 | 7,046 | 13,599 | 0 | 13,599 | 1/7 | 6 | 5,952 | **−93.0 %** | −114.1 % | **0/6** | 6/6 B |

### The two numbers, and why only one of them decides

- **`saving_billed` = (C0_uncached − L1_uncached) / C0_uncached** — the decision number.
  A cached prefix token is not billed, so an L1 prompt that is 5× smaller but never cached
  can still cost more than a C0 prompt that is cached almost entirely.
- **`saving_prompt` = (C0_prompt − L1_prompt − fetched_body_tokens) / C0_prompt** — the
  contrast number. Fetched body tokens are `fetched_body_chars / 4`, a fixed 4 chars/token
  applied identically in every cell. It is the *generous* reading for L1: it credits the
  bodies L1 never fetched while ignoring that its cacheable share shrank.

The two columns have **opposite signs in 4 of the 12 cells**, and in every one of those
`saving_prompt` says L1 wins while `saving_billed` says it loses — most starkly at
30 k / 12 items / occamy / warm, where the prompt-level saving is **+26.5 %** and the billed
saving is **−7,157 %**. That gap is the whole point of the first arm, measured at both ends
of the range: saving prompt tokens is not the same as saving billed tokens.

---

## 3. The crossover point

**There is none in 3 k–30 k.**

Read the warm column — the production-relevant one, where a stable system prompt is re-used:

| model | items | 3,000 | 30,000 |
|---|---:|---:|---:|
| occamy-1.0 | 12 of 12 | **+80.8 %** (L1 wins) | **−7,157.1 %** (C0 wins) |
| qwen3.5-9b | 12 | −105.3 % (C0 wins) | +45.7 % (L1 wins, **cache-blind**) |
| occamy-1.0 | 30 | not measured (outside the card grid) | **−23,433.3 %** (C0 wins) |
| qwen3.5-9b | 30 | not measured (outside the card grid) | **−93.0 %** (C0 wins, **cache-blind**) |

**No corpus size in 3 k–30 k makes L1 stop losing to warm C0.**

Where C0's prefix is genuinely cached, growth makes C0 *better*, not worse. occamy warm
goes from `961` uncached out of `1,025` at 3 k to **`7` uncached out of `6,471`** at 30 k:
C0's billed cost collapses toward zero as the corpus grows, precisely because the whole
fan-out becomes one cache hit. L1 moves the other way — its turn count grew from 2 fetches
to 7, and because each fetched body is new text appended to the transcript and re-billed in
full until it too is cached, its billed cost grew from `184` to `1,412`.

**Growing the corpus does not rescue lazy loading. It is the regime that kills it.**

The single positive warm number at 30 k (qwen, +45.7 %) is **not** a crossover: qwen reports
`prompt_tokens_details: null` on **every** request, so its C0 prefix is never measured as
cached. That cell compares a cache-capable C0 against a blind instrument — it says "qwen's
stack does not report caching", not "L1 wins at 30 k". At occamy's measured 99.9 % warm C0
hit rate, qwen's 6,471-token C0 prompt would have billed ≈ 7 tokens, and L1 would have lost
by roughly the same overwhelming margin it loses everywhere else on a warm prefix.

The one cell where L1 genuinely wins is **3 k, warm, occamy (+80.8 %)**: C0 caches only
`64 / 1,025`, because a 3 k corpus plus system prompt is small enough that prefix-cache
block granularity leaves most of it uncached, while L1 — once its primed turns come back
cached — bills `184`. That is a small-corpus cache artifact, not a size at which the
technique pays, and it reverses at 30 k.

### Where the loss comes from

1. **C0's prefix is one cacheable object; L1's conversation is not.** C0 pays
   `prompt × (1 − hit)`. At 30 k occamy's warm hit rate is 99.9 % for C0 against 85.5 %
   (12 items) and 91.1 % (30 items) for L1: each fetched body is *new text* in the
   transcript and is re-billed in full on the next turn until it lands in the cache.
2. **Turn count multiplies the bill.** L1 costs `1 + fetches` requests — `3` for 2-of-12,
   `7–8` for 6-of-30 — and each round re-sends the growing transcript. At 30 k / 6-of-30
   that is 7–8 requests totalling ~15 k prompt tokens against C0's single ~7 k-token
   request, and under a warm prefix C0 bills almost none of its 7 k.

---

## 4. Correctness — reported, not hidden

**11 of 12 cells answered every required fact correctly on both arms.** The exceptions are
recorded as measured, not re-run to a better outcome:

| cell | failure | interpretation |
|---|---|---|
| qwen 12 / 30 k / L1 / cold | **0/2** facts, `max_rounds_exceeded` after 2 rounds | A real L1 protocol failure on this model at this size: qwen stopped before emitting its answer. |
| qwen 30 / 30 k / C0 / cold **and** warm | **0/6** facts on both | Both C0 runs failed the six-fact task, so this is a **model capability** limit, not an arm effect — qwen does not reliably emit six labelled fields at once. The L1 arm scored 6/6 in the same cells, so the billed comparison still stands. |

---

## 5. Threats to validity

1. **1 rep per cell, no error bars.** The large-effect cells (hundreds to thousands of
   percent) are far outside plausible rep variance. The small ones — the qwen 30 k cold/warm
   pair at +44.9 % / +45.7 % — are not distinguishable from noise and should not be quoted
   as point estimates without ≥3 reps.
2. **qwen's cache instrument is blind** (`prompt_tokens_details: null` on every request).
   Its `uncached` is an upper bound, and its billed column is not comparable to occamy's on
   equal terms. It is marked blind everywhere; it is never silently treated as "0 % hit".
3. **`saving_prompt` uses a fixed 4 chars/token** for fetched bodies. It is the contrast
   number; `saving_billed` uses only server-reported tokens.
4. **The warm regime assumes a stable system prompt.** That is the regime this technique is
   proposed for. A workload whose system prompt changes per request behaves like the COLD
   column, where L1 does win at 30 k / 2-of-12 (occamy +44.9 %, qwen +44.9 %) and loses at
   6-of-30 (both −94 % to −96 %).
5. **Concurrent session pressure.** A second session swept the same two endpoints for part
   of this run. Rows were partitioned into discrete runs by round structure and only rows
   belonging to a recorded completed run were kept (65 rows / 24 runs, verified
   collision-free); contemporaneous prompt-token figures differ by a few tokens between
   otherwise identical requests, consistent with that interleaving. It does not move any
   ratio materially, but it is why figures are reported to the token rather than to a tenth.

---

## 6. Verdict

> **NEGATIVE — lazy loading trades a smaller prompt for a larger bill, and growth makes it
> worse: wherever the prefix cache works, an inline corpus becomes a single cache hit while
> L1's extra fetch turns keep re-billing new text, so there is no corpus size in 3 k–30 k at
> which lazy loading beats a warm inline prompt.**

The technique optimises the number a reader can see — the prompt — rather than the number
that is charged: the uncached tokens. That gap is **+26.5 % on the prompt and −7,157 % on
the bill** in the same cell.

Restating the earlier partial finding: lazy loading pays **only** under a cold prefix, and
only at low needed fractions. The card's grid measures 2-of-12 and 6-of-30; the crossover is
governed by **needed fraction and warm-prefix capability**, not by corpus size.

---

## 7. Reproduce

```bash
cd experiments/agentic-lazy/crossover
python3 cx_corpus.py             # rebuild corpora (seed 20261024), exact sizes
python3 cx_harness.py            # SELFCHECK PASS: sizes, facts present, no fact in index
python3 run2/run_cx2.py --dry-run   # plan: 24 runs, no request sent
python3 run2/run_cx2.py             # the sweep; rows flushed + fsynced per request
python3 run2/analyze2.py            # the tables above; also writes cells.json
```

Evidence: `run2/rows.jsonl` (one JSON object per request, append+flush+fsync),
`run2/runs.json` (one summary per run), `run2/run2*.log` (per-run traces), `cells.json`
(aggregated table). The earlier partial sweep and its own RESULTS are preserved as
`RESULTS.firstattempt.md.bak`.
