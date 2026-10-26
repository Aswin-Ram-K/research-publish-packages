# The append-cost law: how much of a re-sent prefix re-bills as a function of where the append lands

**Unit:** MISS-LAW · **Evidence:** `experiments/miss-law/rows.jsonl` (764 rows, one row per request,
fsynced per row: 753 at the aggregation run plus 11 position-control rows) · `law_fit.json` · **Sweep:** `run.py`, `grid2.py`, `agg.py`

**Answer in one line.** For a prefix-cached chat server with cache block size `B`, appending `L`
tokens to a prefix of `P1` tokens re-bills

```
R = uncached = (P1 mod B) + L              (SGLang, B = 64)        <- the tail of the history + what you appended
R = uncached = (P1 mod B) + B + L          (vLLM,    B = 1056)     <- ... plus one whole block
```

plus one discontinuity that is worth more than the formula: **if `P1 mod B ∈ {0, 1}` the server
reports no cache at all and the entire prefix is billed** (`R = P1 + L`). That is not a tail cost,
it is an avalanche — ~8,000 tokens in this grid, against a formula that otherwise predicts 2.

The prediction asked for in the brief — that this explains the 2-fetch vs 6-fetch sign flip —
**does not hold**. Section 6 shows why, with the arithmetic.

---

## 1. Servers and instruments

| id | model | endpoint | flavour | max_model_len | block size measured |
|---|---|---|---|---|---|
| `sglang` | `occamy-1.0` | `http://192.168.2.168:8012/v1` | SGLang, `page_size=1`, `enable_cache_report=True`, `chunked_prefill_size=8192`, `max_total_num_tokens=1,514,599` | 131,072 | **B = 64** |
| `vllm` | `qwen3.5-9b` | `http://192.168.2.168:8014/v1` | vLLM 0.27.1, prefix caching on, `cache_config_info` advertises `block_size="1056"` | 32,768 | **B = 1056** (advertised value, measured) |

Both answered a 1-token request before any measurement began. Both serve the same tokenizer family
(`" the"` is token id 279 on both), which is what makes the exact-token payload possible.

- **SGLang instrument:** `usage.prompt_tokens_details.cached_tokens`. On a cold request the whole
  `prompt_tokens_details` object is `null`. **`null` is not zero** — it is "the server reported no
  hit". Rows keep `cached_reported=false`, and only then is the value treated as 0 for arithmetic.
- **vLLM instrument:** this build returns `prompt_tokens_details: null` on **every** request, hit or
  miss (a 3.77 s → 0.61 s repeat proves caching happens; the field stays null), so per-request
  reporting is blind here. Cached tokens are read as the delta of the server counter
  `vllm:prompt_tokens_cached_total` across each serial request. These deltas are attributable only
  because this unit is the sole writer and requests are strictly serialized. `vllm:prefix_cache_hits_total`
  turns out to be another **token** counter (not a block counter) on this build, so the two agree
  trivially — the vLLM numbers below rest on a single server-side quantity and want independent
  re-derivation.

`B` was **measured, not assumed**:

- SGLang: `cached_tokens` stayed at exactly 8000 for all 64 consecutive primed lengths
  `P1 = 8000 … 8063`. A 32-token block would have stepped to 8032 by `P1 = 8032`; a 128-token block
  would require 8000 ≡ 0 (mod 128), which it is not. Separately, the discovery sweep produced
  `cached ∈ {448, 1344, 2240, 3136, 4032, 4928, 5824, 6720}` — odd multiples of 64, so a 56-token
  block is excluded by 448 ≡ 0 (mod 56) failing on 1344. Only 64 divides all of them.
- vLLM: `cached_tokens` sat at 5280 for `P1 = 7000 … 7330` and stepped to 6336 at `P1 = 7396`,
  i.e. the step lands on `7 × 1056 = 7392`, matching the advertised `block_size = 1056`.
- Lesson recorded: **gcd of the reported cached values is a bad estimator** — it overshoots
  (448 for SGLang) and is ambiguous across divisors. The plateau width and the step position are
  what pin `B`.

## 2. Exact request shape (reproducible)

```
round 1 (prime):   [system: NONCE + "\n\n" + FILLER + "\n\n" + QUESTION,
                    user:   "Reply with the single word OK."]
round 2 (measure): same two messages +
                    [assistant: "OK.", user: " the" * n]
```

- `FILLER` is whole sentences from a fixed pool, padded with `" the"` to an **exact** token count
  (`/tokenize` verified on both servers). `P1 = F + 53` exactly, so a target `P1` sets `F = P1 − 53`.
- `" the"*n` is exactly `n` payload tokens. `L = P2 − P1` additionally carries the template's
  **framing tokens** (12 of them): `L = n + 12`. Every number below uses the measured `L`, never `n`.
- `NONCE` is a permutation of ten one-token words → **constant 10 tokens**, so `P1` (and therefore
  `P1 mod B`) is identical across reps while the prefix is still unique, hence cold. Each rep is an
  independent prime→append cycle.
- The prefix cache hashes the rendered token stream only; the divergence between the two rounds is
  the assistant header, 2 tokens before `P1` (verified by tokenizing both message lists: identical
  through index 8050, then the generation header vs `OK.`).

## 3. Measured grid — SGLang, B = 64

Fixed `P1 = 8000` block, payload `n = 1` (`L = 13`), 3 reps per cell. `P1` was stepped by exactly one
token across a whole block so that every residue `P1 mod 64` is covered.

| `P1 mod 64` | primed `P1` | `L` | `cached` | `uncached` | `(P1 mod B) + L` | reps |
|---:|---:|---:|---:|---:|---:|---:|
| **0** | 8000 | 13 | **null** | **8013** | 13 | 3/3 miss |
| **1** | 8001 | 13 | **null** | **8014** | 14 | 3/3 miss |
| 2 | 8002 | 13 | 8000 | 15 | 15 | 3 |
| 3 | 8003 | 13 | 8000 | 16 | 16 | 3 |
| 4 | 8004 | 13 | 8000 | 17 | 17 | 3 |
| 5 | 8005 | 13 | 8000 | 18 | 18 | 3 |
| … | … | 13 | 8000 | `r + 13` | `r + 13` | 3 |
| 62 | 8062 | 13 | 8000 | 75 | 75 | 3 |
| 63 | 8063 | 13 | 8000 | 76 | 76 | 3 |

`residue 2 … 63`: **residual `measured − predicted = 0` in 186/186 rows** (`62 residues × 3 reps`).
`residue 0, 1`: complete miss in **6/6 rows**.

Payload size does not interact with the residue (2 reps each, `P1` fixed, predicted `(P1 mod 64) + L`):

| `P1` | `P1 mod 64` | `n` | `L` | `cached` | `uncached` | predicted |
|---:|---:|---:|---:|---:|---:|---:|
| 8005 | 5 | 16 | 28 | 8000 | 33 | 33 |
| 8005 | 5 | 32 | 44 | 8000 | 49 | 49 |
| 8005 | 5 | 64 | 76 | 8000 | 81 | 81 |
| 8005 | 5 | 128 | 140 | 8000 | 145 | 145 |
| 8037 | 37 | 128 | 140 | 8000 | 177 | 177 |
| 8063 | 63 | 128 | 140 | 8000 | 203 | 203 |
| 8064 | **0** | 64 | 76 | **null** | **8140** | 76 |
| 8064 | **0** | 128 | 140 | **null** | **8204** | 140 |
| 8065 | **1** | 16 | 28 | **null** | **8093** | 29 |

**The avalanche is not a rounding artefact.** At `P1 mod 64 ∈ {0,1}` even an *identical repeat*
reports no hit (`P1 = 8064`, repeated verbatim → `cached = null`), so the cache entry is genuinely
absent, not merely rounded down. It is also **residue-based, not positional**: every `P1` with
residue 0 or 1 missed at every absolute position tried — `2048, 2049` (block #32), `4096, 4097`
(#64), `6144, 6145` (#96), `7681` (#120), `7936, 7937` (#124), `8000, 8001` (#125) — 11/11 misses
spanning four separate block indices. **Mechanism not established**; it is reported as measured.

Consequence worth naming: `P1 − 64` keeps the residue, so the earlier "recovery at `L − 64`"
observation is **not reproduced** here — 7936 (residue 0) misses exactly like 8000.

## 4. Measured grid — vLLM, B = 1056

18 primed lengths spread across one block, `n = 1` (`L = 13`), 3 reps. `cached` never exceeded
`(floor(P1/1056) − 1) · 1056`, i.e. this server leaves **one entire block** of the shared prefix
unbilled-as-cached, on top of the unaligned tail:

| `P1` | `P1 mod 1056` | `cached` | `uncached` | `(P1 mod B) + B + L` |
|---:|---:|---:|---:|---:|
| 7000 | 664 | 5280 | 1733 | 664 + 1056 + 13 = 1733 |
| 7396 | 4 | 6336 | 1073 | 4 + 1056 + 13 = 1073 |
| 7462 | 70 | 6336 | 1139 | 1139 |
| 7990 | 598 | 6336 | 1667 | 1667 |
| 8054 | 662 | 6336 | 1731 | 1731 |

Residual `measured − ((P1 mod B) + B + L)` is **exactly `+1056` for every row** (i.e. the
`+B` model is the fit, not `+0`); the `+0` model is short by 1056 everywhere. Payload variants agree
(`P1 = 7000`, `r = 664`): `n = 64 → 1796`, `n = 512 → 2244`, `n = 1056 → 2788`, each exactly
`664 + 1056 + L`. No avalanche residue was found on vLLM in the 18 residues sampled.

So the two servers do **not** share a quantisation: an append on SGLang costs `≤ 64 + L`; on vLLM it
costs `≤ 2112 + L` — one block plus the tail, ~33× more overhead for the same append.

## 5. Controls

| control | request | result | reads |
|---|---|---|---|
| **WARM** (identical repeat) | 8053-token prompt sent twice, same nonce | `cached = 8000` of 8053 → **99.3 %** | instrument reads **high** when it should ✔ |
| **COLD** (prefix broken mid-history) | 8053 prompt, then the same prompt with one word of the filler changed | `cached = null` (→ 0) on **both** requests | instrument reads **~0** when it should ✔ |
| COLD, structural | 8 fresh-nonce discovery prefixes | `cached = null` on 8/8 | ✔ |

`/flush_cache` was never called and neither server was restarted.

## 6. Validation against the measured crossover — the prediction fails, and here is the arithmetic

The brief's numbers are `+44.8 %` at 2 fetches (3 rounds) and `−95.6 %` at 6 fetches (7 rounds) on a
30,000-char corpus. In `experiments/agentic-lazy/crossover/RESULTS.md` those two cells are
`occamy-1.0`, 12 items/30 k, **cold** = `+44.9 %`, and `occamy-1.0`, 30 items/30 k, **cold** =
`−95.6 %`. "Cold" there means *a fresh nonce on every request, so no prefix can be reused*, and
`uncached` is a **run total** (summed over that run's requests), which is why longer runs lose.

**6.1 The law reproduces both numbers — degenerately.** In a cold cell `cached = 0` on every
request, so the law collapses to `R = P`. From the shipped rows, the 2-fetch cell bills
`C0 = 6490` against `L1 = 658 + 1192 + 1747 = 3597` → **+44.6 %** (published +44.9 %, quoted
+44.8 % — the quoted pair reproduces). For the 6-fetch cell the `n = 30 / 30 k` rows are **not on
disk**; the published aggregates are `C0 = 7065`, `L1 = 13 822` → **−95.7 %**, matching the quoted
−95.6 %. No block-boundary term is exercised in either cell — its value there is identically 0.

**6.2 The boundary term cannot explain the flip.** The law's own contribution per append is
`P1 mod B ≤ 63` tokens (mean 32). Over the six appends that separate the two cells the *maximum*
boundary-attributable cost is `6 × 63 = 378` tokens (mean 192), while the quoted swing is
`13 822 − 3 578 = 10 244` uncached tokens. **Boundaries account for ≤ 3.7 % of the swing.**

**6.3 In the warm regime the law holds, and the flip does not occur.** Applied to the crossover's own
shipped warm rows, the law predicts `cached = floor(P/64) · 64` in **57 of 60** rows exactly
(the 3 exceptions are round-1 rows whose prime was not resident in the shared warm prefix). Those
rows bill `C0 = 12` and `L1 = 1, 27, 47` — i.e. `P mod 64` — giving a billed saving of **−525 %**, and
a 7-round warm run extrapolates to ≈ **−1,700 %**. Warm, L1 loses at *both* fetch counts, so the
sign flip is absent.

**Conclusion, stated plainly:** the sign flip between 2 and 6 fetches is produced by the **cold arm**
— the fresh-nonce regime where nothing may be cached and billed tokens grow with the number of
rounds — not by appends landing off the block boundary. The round-trip cost is **not** the mechanism.
Two further reasons to treat the quoted pair as describing fetch count alone: both cells are cold
(so the cache is deliberately disabled), and the 2-fetch cell has 12 items while the 6-fetch cell has
30, so fetch count moves together with index size and task length.

## 7. What a client should do

The engine should treat a fetch payload as **an append whose cost is set by an alignment residue, not
by its own size**, and quantise accordingly. Concretely, for the primed prefix length `P1` and block
size `B`: (i) **never let `P1` land at `P1 mod B ∈ {0,1}`** — pad the history by 2 tokens (`1` if the
residue is 1) *before* appending, which converts an avalanche that re-bills the whole prefix into a
2-token tail; this single rule is worth ~8,000 billed tokens per append on the SGLang endpoint and is
the only place in this law where a 2-token intervention buys four orders of magnitude;
(ii) otherwise accept `P1 mod B` as an unavoidable per-append tax and **batch fetches** — `K` separate
appends pay `Σ (P1_i mod B) ≈ K·B/2` while one batched append pays a single residue, so merging two
fetches saves ~32 tokens on SGLang and ~1,584 on vLLM (`B/2 + B`) for identical payload; (iii) **size
playloads by body tokens, not by append count** — since the overhead is independent of payload size,
one 4,000-token fetch beats eight 500-token fetches by roughly `7 × B/2` tokens, and on vLLM (where
`B = 1056` and the tax is a block and a half) lazy loading should only be chosen when the bodies
*actually needed* are a small fraction of the corpus, not merely small in absolute terms.

## 8. What this law does not say

- It is a law about **one append onto an already-primed prefix**. Multi-append runs were not swept
  end to end; §6.3 extrapolates.
- The SGLang avalanche at residue 0/1 is measured but **not explained**; do not generalise it to
  other builds without re-measuring.
- vLLM's numbers rest on one server-side counter (both cache counters on this build count tokens), so
  the `+ B` term deserves independent re-derivation.
- The 3-rep cells are deterministic (identical values), so reps here bound transcription error, not
  sampling variance.

## Scope and withdrawals (2026-10-26)

- **Adjudications.** The record's C1 (SGLang avalanche magnitude) and C3 (QUALITY-ARM's token column is
  not a bill) both sit in `experiments/ptr-engine/RECORD.md` — C1 at `RECORD.md:114`, C3 at `RECORD.md:118`.
  Read them before quoting any number in this file: C3 records the instrument defect at
  `quality/runner.py:490`/`:495` (`L = prompt_tokens + FRAMING`, the whole prefix passed off as the append).
- **Withdrawn elsewhere, not restated here.** The "5.2× overstatement" reading of ENGINE-R1's `397`
  (this file, §3 cell C / `LAW.md:85`) is withdrawn as a general claim: `RECORD.md:114` (C1) records it first
  withdrawn and then **UNDECIDABLE** — `397` is not a general law of that endpoint, and the rows fit both
  residue-0 readings. Do not cite this file for a 5.2× ratio. Any billed-token identity
  (`sum(prompt_tokens) + 12·(R−1)`) is refuted by the rows (`RECORD.md:118`, C3; `RECORD.md:134`, C10 —
  C rep2 residual +17,193): this law prices one append, it does not telescope a conversation into a bill.
- **Scope, restated.** The formula above is a law about **one warm append onto an already-primed prefix**;
  multi-append runs are outside it and were not swept end to end (§8, `LAW.md:205-206`).
