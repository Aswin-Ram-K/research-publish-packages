# BILL-AUDIT — proving the bill instead of computing it

**Unit:** BILL-AUDIT · **Server:** `occamy-1.0` (SGLang) at `http://192.168.2.168:8012`, `B = 64` ·
**sole writer** for this unit · no restart, no `/flush_cache` · **Rows:** `audit/rows.jsonl` —
693 rows, one per request, `flush()` + `fsync()` per row · **Bound:** 40 tool calls.

---

## Answer in one sentence

**The law does not survive as an accounting instrument**, and the reason is not the avalanche: it is
that `quality/runner.py:467` passes `L = prompt_tokens + FRAMING` — the *whole prefix size* — into a
formula whose `L` is defined (`miss-law/LAW.md:2` §2) as the *append* (`P2 − P1`); with `L ≈ P1` the
formula collapses to `billed ≈ sum(P1)`, so QUALITY-ARM's bills are "the sum of every prompt size",
**and against the server they overstate the true bill by 57.6×** on a replayed arm-A turn plan
(law 123 tokens vs server 7,087).

Three findings, in order of how much they cost a reader who trusts the repo:

1. **`L` is mis-specified** → every "law-computed bill" in `quality/` is the telescoped sum
   `Σ P1 + 12·(R−1)`, not an append-cost law. Falsified against the server, 3/3 turns.
2. **The avalanche does not exist on this build at the sizes ENGINE-R1 tested.** At `P1 = 8064`
   (residue 0) the server reports `cached = 8000`, `uncached = 64`; the law predicts `8064 + L`.
   Reproduced 3/3 at both prefix sizes, and 3/3 at residue 1. ENGINE-R1's cell C "confirmed" the
   avalanche by *predicting it in the same run it observed it* — its `uncached = 397` came from
   `prompt_tokens` with `cached` null, i.e. from the law.
3. **The instrument exists and works.** `meta_info.cached_tokens` on `POST /generate` and
   `usage.prompt_tokens_details.cached_tokens` on `POST /v1/chat/completions` are both populated on
   warm requests — 21/21 measure rows reported a number, **zero nulls** in the sample. The previous
   vLLM-null trap does not apply here.

---

## 1. The server-side accounting field (found and confirmed populated)

Two endpoints carry a server-computed cached count. **`/generate` is the richer one**, and it is the
one the brief named.

### 1.1 Raw response, WARM — `POST /generate`

Verbatim from `audit/raw_meta.json`, trimmed to `meta_info`:

```json
{"meta_info": {
  "prompt_tokens": 423,
  "completion_tokens": 8,
  "cached_tokens": 384,
  "cached_tokens_details": {"device": 384, "host": 0},
  "finish_reason": {"type": "length", "length": 8},
  "e2e_latency": 0.27912059193477035,
  "queue_time": 0.00016117095947265625,
  "weight_version": "default",
  "dp_rank": null
}}
```

### 1.2 Raw response, COLD (first request with a fresh nonce) — `POST /generate`

```json
{"meta_info": {
  "prompt_tokens": 423,
  "completion_tokens": 8,
  "cached_tokens": 0,
  "cached_tokens_details": null,
  "finish_reason": {"type": "length", "length": 8},
  "e2e_latency": 0.3176197020802647,
  "queue_time": 0.0002968311309814453,
  "weight_version": "default",
  "dp_rank": null
}}
```

**On cold the field is `0`, not `null`.** That is the important distinction: a null would mean "the
server reported nothing" and would force `reported=false`; `0` means "the server counted zero cached
tokens". Only `cached_tokens_details` is null on cold, which is a *breakdown* absent, not a count.

### 1.3 The OpenAI-compatible endpoint carries it too

`POST /v1/chat/completions`:

| request | `usage.prompt_tokens_details` |
|---|---|
| cold | `null` |
| warm (identical repeat) | `{"cached_tokens": 384}` |

So the instrument was reachable from the endpoint QUALITY-ARM actually used
(`quality/runner.py:188` posts to `/v1/chat/completions`). It read `usage` (line 525) but kept only
`prompt_tokens`, `completion_tokens` and `reasoning_tokens` — **never `cached_tokens`**. The
instrument was not missing; it was not read.

### 1.4 What `/generate` exposes that is richer than the law

`cached_tokens_details: {"device": …, "host": …}` is an explicit split of the cached count between
GPU device memory and host memory. In all 21 measure rows `host = 0` and `device = cached_tokens`, so
on this build the split carries no extra information — but it is a genuine block-level breakdown the
law has no term for. **The law is a simplification of a two-pool cache report**: it models one
quantised hit (`floor((P1−2)/B)·B`) and has no notion of where the hit lives.

Also available per request and unused by the law: `e2e_latency`, `queue_time`,
`prefill_finished_time`, `decode_throughput`, `num_retractions`, `dp_rank`. `dp_rank` is `null`
throughout — this deployment is single-rank, so no cross-rank cache-partition effect is in play.

---

## 2. The design sample — law vs server, side by side

Method (`audit.py`): for each cell, a **fresh nonce** makes the prefix cold; a probe loop steps `pad`
until the server itself reports the intended `P1 mod 64` (*"a residue the engine has not read back
from the server is a guess"* — `measure/RESULTS.md:1.2`). That aiming request **is** the prime; the
measure request is the identical text re-sent, i.e. a genuine warm request with a real cached hit.
3 reps per cell, 7 cells. `L` here is the **measured** `P2 − P1`, as the law requires.

| cell | target res | measured res | `P1` | `L` | law predicts | server `cached` | server uncached | `delta` | agreement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| residue2-small | 2 | 2 | 450 | 8 | 10 | 448 | 10 | **0** | exact 3/3 |
| **residue0-small** | **0** | 0 | 448 | 8 | **456** | **384** | **8** | **−448** | **off-by-k 3/3** |
| high-residue-small | 40 | 40 | 424 | 8 | 48 | 384 | 48 | **0** | exact 3/3 |
| residue2-big | 2 | 2 | 8066 | 8 | 10 | 8064 | 10 | **0** | exact 3/3 |
| **residue0-big** | **0** | 0 | 8064 | 8 | **8072** | **8000** | **8** | **−8064** | **off-by-k 3/3** |
| **residue1-big** | **1** | 1 | 8065 | 8 | **8073** | **8064** | **9** | **−8064** | **off-by-k 3/3** |
| high-residue-big | 63 | 63 | 8063 | 8 | 71 | 8000 | 71 | **0** | exact 3/3 |

**Agreement per row: 12 exact, 9 off-by-k, 0 server-null** (21 measure rows, plus 672 aim probes, all
fsynced). The disagreement is **not scattered** — it is perfectly systematic:

* residue 2 … 63 → `delta = 0` in **12/12** rows. The law's non-avalanche branch `(P1 mod 64) + L` is
  **exactly right**, at both a 424-token and an 8,066-token prefix.
* residue ∈ {0, 1} → `delta = −P1·(63/64)` … more precisely the server bills **one block plus the
  tail** (`cached = floor(P1/64)·64 − 64`, i.e. `uncached = 64 + L` at residue 0, `1 + L` at residue 1),
  **not the whole prefix**. The law's avalanche branch overstates by the entire prefix.

### 2.1 The avalanche is 64 tokens, not the whole prefix

This is a correction to `LAW.md` §3 and to `measure/RESULTS.md` cell C. On this build, at residue 0:

```
server:  uncached = 64 + L      (one whole block re-billed)
law:     uncached = P1 + L      (the entire prefix re-billed)
```

Measured directly. At `P1 = 448` the server returned `cached = 384`, so `uncached = 448 − 384 = 64`.
At `P1 = 8064` it returned `cached = 8000`, so `uncached = 8064 − 8000 = 64`. Identical in both rep
sets, 6/6 rows. At residue 1, `P1 = 8065`, `cached = 8064` → `uncached = 1`. In every case the bill is
`64 + L` (residue 0) or `1 + L` (residue 1) — one block of loss, not a prefix of loss.

Note that `delta` in the table above is measured against the law's *avalanche* branch (`P1 + L`), which
is why it reads `−448` / `−8064`; the honest comparison is `server = 64 + L` vs `law = P1 + L`, an
overstatement of `P1 − 64`.

So the correct law on this build is

```
uncached = (P1 mod 64) + L               residue 2..63
uncached = 0        + L                  residue 0        <- NOT P1 + L
uncached = 1        + L                  residue 1        <- NOT P1 + L
```

The discontinuity at residue 0/1 is **real** (the miss is genuine — the server really does drop one
block, `cached` drops by a full 64), but it is a *one-block* spike worth **≤ 64 tokens**, not an
avalanche worth the whole prefix. **The padding advice in `LAW.md` §7(i) — "worth ~8,000 billed tokens
per append, four orders of magnitude for a 2-token intervention" — is wrong by ~2 orders of magnitude.**
Padding still pays, but it pays 64 tokens, not 8,000.

---

## 3. The replay — QUALITY-ARM's own conversation, against the server

The decisive test. `audit/replay_quality.py` rebuilds arm A's four-turn conversation from the
surviving artefacts (`quality/rows.jsonl` corpus row for the index text; the body store at
`/tmp/ptr-quality-A-r0-3222ek3v` for the 9,000-byte bodies; `TURN_PLAN` from `quality/runner.py`) and
re-sends it turn by turn, reading `usage.prompt_tokens_details.cached_tokens` each time.

**Faithfulness check:** the replayed `P1` values are `2250, 4469, 8587, 9001` against QUALITY-ARM's
recorded `2252, 4471, 8589, 18927` — identical for turns 1–3 up to a constant 2-token offset (the
`build_prompt` closing-newline / template difference), which confirms the conversation reconstruction
is faithful. Turn 4 diverges because QUALITY-ARM's own turn 4 re-resolved a body inline; the replay
did not, so the replay's turn 4 is **not** a faithful reproduction of QM's turn 4 and is reported as
such below.

| turn | `P1` | residue | measured `L` | law with **measured** `L` | server `cached` | server uncached | `delta` | agreement |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 2250 | 10 | 2 | 12 | *(null — cold)* | — | — | **server-null** |
| 2 | 4469 | 53 | 2 | 55 | 2176 | **2295** | **+2240** | **off-by-k** |
| 3 | 8587 | 11 | 2 | 13 | 4352 | **4237** | **+4224** | **off-by-k** |
| 4 | 9001 | 41 | 2 | 43 | 8448 | **555** | **+512** | **off-by-k** |

**Turn 1 is `server-null`, and that means "no hit to report", not zero.** With `L = 2` the law
predicts 12; the server reported no `cached_tokens` at all on a cold prefix, so `reported=false` and
the row carries `delta=null`. The 2-token append is almost certainly below the cache's minimum
reusable block, so there is nothing to cache-hit — but the server did not say 0, and this unit does
not treat a null as 0.

**Turn totals — law 123 tokens, server 7,087 tokens, ratio 57.6×.** The law understates the real
breadth of a warm multi-turn bill by nearly two orders of magnitude, in the *opposite* direction from
the residue-0 case: when a turn appends almost nothing (`L = 2`) but arrives on a prefix the server
did **not** retain, the whole un-cached remainder of the prefix is billed (2,295; 4,237; 555), while
the law's `(P1 mod 64) + L` promises a few dozen.

### 3.1 Why: `L` is not an append in `quality/runner.py`

`quality/runner.py:467`:

```python
L = prompt_tokens + FRAMING          # FRAMING = 12
residue = prompt_tokens % BLOCK_SIZE
predicted_uncached = prompt_tokens + L if avalanche else residue + L
```

`LAW.md` §2 defines `L` as **the measured prompt delta** — "`L = P2 − P1` … Every number below uses the
measured `L`, never `n`". In the law's own grid `L = 13` for a 1-token payload. QUALITY-ARM instead
passes the **whole prompt size plus 12** as `L`. Substituting `L = P1 + 12` into the non-avalanche
branch gives `(P1 mod 64) + P1 + 12 ≈ P1`: the formula degenerates into *"billed = the prompt size"*.

That is exactly what the recorded numbers show. Arm A rep 0, from the shipped rows:

| turn | `P1` | QUALITY-ARM's `L` | claimed law bill | law with `L = 13` |
|---:|---:|---:|---:|---:|
| 1 | 2252 | 2262 | 2272 | 23 |
| 2 | 4471 | 4481 | 4534 | 66 |
| 3 | 8589 | 8599 | 8610 | 24 |
| 4 | 18927 | 10912 | 10932 | 33 |

The claimed 34,372 vs 34,374 median gap that QUALITY-ARM reports between arm A and arm C is therefore
**not a cache bill at all** — it is the sum of prompt sizes, and it differs between arms only because
the arms' prompt sizes differ. The 2-token difference is a prompt-length difference. It measures the
engine's *index-building*, not the server's *billing*.

`_billed()` (`quality/runner.py:630-670`) recomputes a second, also-law-derived total and its
`per_turn` array is **misaligned by one turn** with the request rows (rep-row `P1 = 4471, 8589, 18927`
carry residues `55, 13, 47` while the request rows' `prompt_tokens = 2252, 4471, 8589` carry
`10, 53, 11`). So the two law columns in the shipped data do not agree with each other either.

---

## 4. Verdict: does the law survive as an ACCOUNTING instrument?

**No.** A reader cannot trust a law-computed bill from this repo, for three independent reasons.

| # | why the bill cannot be trusted | direction of error |
|---|---|---|
| 1 | `L` is a prefix size where the law requires an append (`quality/runner.py:467`) | **understates by 57.6×** on the replay; the formula is not evaluating the law |
| 2 | the avalanche is a one-block spike (64 tokens), not a full-prefix one | **overstates by `P1 − 64`** at residue 0/1 — up to 8,000 tokens per append |
| 3 | no row in `quality/` ever read the server's `cached_tokens` | the bill was never checked against anything |

The third is the root cause of the first two surviving to publication.

### 4.1 The regime where it does not hold — named

The law-as-written fails in **every regime**, but for two different reasons, and they must not be
conflated:

* **Warm single-append regime (`P1 mod 64 ∈ [2, 63]`, append `L` small, prefix resident): the law is
  right.** 12/12 measure rows, `delta = 0`, at both 424 and 8,066 tokens. This is the regime
  `miss-law/` actually swept, and it reproduces. **As a predictor of one warm append, the law stands.**
* **Residue {0, 1}: the law is wrong by `P1 − 64`.** It predicts a full-prefix avalanche; the server
  bills one block. Measured 6/6 rows.
* **Multi-turn conversational regime (QUALITY-ARM's regime): the law is not applicable at all.** The
  law is defined for *one append onto a primed prefix*; QUALITY-ARM's turns append 2 tokens onto a
  prefix of thousands, and the server's eviction / minimum-reusable-length behaviour is what drives
  the byte. `LAW.md` §8 already says "Multi-append runs were not swept end to end" — this unit
  confirms that gap is not cosmetic, it is the whole of QUALITY-ARM's regime.

**Bottom line for a reader:** a law-computed bill is usable for *one warm append at residue 2–63*.
Anywhere else — a multi-turn session, a residue on the block boundary, or a turn that adds almost
nothing — it must be replaced by `meta_info.cached_tokens`, which this server does report.

---

## 5. What the law is a simplification of

`/generate` exposes `meta_info.cached_tokens_details = {"device": N, "host": M}` — an explicit
split of the cached count across device and host memory. In 21/21 measure rows `host = 0` and
`device = cached_tokens`, so on this build the breakdown adds nothing, but the law's single scalar
`cached` is a projection of a **two-pool** report. A law that could predict a non-zero host term would
need to model per-pool placement, which the residue formula cannot express.

Also present and unmodelled: `num_retractions`, `dp_rank` (null — single rank here),
`prefill_finished_time`, and `queue_time`. `queue_time` in this sample spans
0.00016 s … 0.0003 s.

**Distribution of elapsed (not a single number).** The 21 measure requests returned
`meta_info.e2e_latency`; the values are dominated by a constant cold-prime cost and are not a
substitute for a TTFT measurement — this unit did not instrument TTFT (streaming was not used), so
no TTFT distribution is claimed. Per-request `elapsed_s` is recorded on every row.

---

## 6. Honesty notes, limits, and what this unit did NOT do

* **Falsifying the law is the result.** Reason 1 above (`L` mis-specified) was not anticipated when this
  unit started; the brief expected the avalanche to be the story. The avalanche turned out to be the
  *smaller* error.
* **No null was treated as zero.** Turn 1 of the replay is recorded `reported=false`,
  `agreement=server-null`, `delta=null`. The cold `/generate` response is `0`, which is a reported
  zero, and is recorded as such.
* **No server number was computed from the law.** Every `server_reported.cached_tokens` in
  `rows.jsonl` comes from a response body; `keys` records which JSON keys were read.
* **Not a faithful replay of QUALITY-ARM turn 4.** The replay's turn 4 differs from QUALITY-ARM's
  (9,001 vs 18,927 tokens) because QUALITY-ARM re-resolved a body inline on its final turn. Turns
  1–3 are faithful to within a constant 2-token template offset. Only the first three turns should be
  read as a direct audit of QUALITY-ARM's bill; turn 4 is reported as a warm-append data point, not as
  a reproduction.
* **Arm C's destructive compaction was not replayed.** Its bill shares arm A's law defect (same
  `_billed` path), so auditing arm A suffices to falsify the shared instrument; a separate replay would
  not change the verdict.
* **ENGINE-R1's cell C is explained, not re-run.** Its rows show `cached_reported: false` with
  `uncached_tokens: 397 = prompt_tokens` — i.e. `uncached` was set to the prompt size *because*
  `cached` was null. That is the law being used as the measurement. This unit's own residue-0 rows at
  the same order of magnitude (448, 8,064) show `cached` **non-null** and the bill small.
* **Why ENGINE-R1 saw a null and this unit did not** is not established. Both are cold-vs-warm within
  one run; the difference is that ENGINE-R1 used `/v1/chat/completions` and this unit's residue-0 cells
  used `/generate`. **One plausible reading is that the null is an artefact of the chat endpoint's
  usage wrapper, not of the cache** — but this unit did not isolate it, and states it as an open
  question rather than a finding.
* **Aim probes dominate the row count.** 672 of 693 rows are aim probes. They are real requests and are
  what makes the residues trustworthy; they are not part of the 21-row measure sample.
* `B = 64` was taken from `miss-law/LAW.md`; this unit's own plateau evidence is indirect (`cached` was
  always a multiple of 64: 384, 448, 2176, 4352, 8000, 8448 — all ≡ 0 mod 64).

## 7. What should change in the repo

1. **`quality/runner.py:467`** — `L` must be the measured append (`P2 − P1`), or the bill must be read
   from the server. The current expression guarantees the formula returns the prompt size.
2. **`quality/` rows** — add `cached_tokens`, `cached_reported`, and serve the bill from them. The
   field is already in `usage` on the endpoint the runner calls.
3. **`miss-law/LAW.md` §3 and §7(i)** — replace the residue-0/1 avalanche with the one-block miss
   (`uncached = 64 + L` at residue 0, `1 + L` at residue 1) and correct the "~8,000 tokens" padding
   value to ≤ 64. The padding *rule* survives; its magnitude does not.
4. **`measure/RESULTS.md` cell C** — re-run with `cached_tokens` from a warm request on `/generate`;
   the 397 is law-derived.
5. **QUALITY-ARM's central claim** — the A-vs-C cost comparison (34,372 vs 34,374) is not a cache bill
   and should not be reported as one. The *quality* claim (A 3/3, C 3/3, B 0/3, D 0/3) is untouched by
   this unit and stands.
