# LATENCY_DERIVE.md — what service latency these rows can and cannot support

**Unit:** LATENCY-DERIVE · **automated session, no answerer** · **0 live requests, no `.occamy.lock`,
0 writes outside this workspace** · read-only over `experiments/context-cache/cells/*/*.jsonl`.
**Computed:** 2026-10-23 · **Recompute:** `.venv/bin/python state/logs/lat_derive.py` (output saved at
`state/logs/lat_derive.out`).

The question is narrow: *from the rows already on disk, what service latency is computable?* This note
derives every number below in this pass and names, in §4, the metrics the rows **cannot** support — not
because they are hard, but because the matching design was never run.

---

## 0. The one-line answer

**Three latency quantities are computable, and only one of them is measured rather than assumed.**

| # | Quantity | Status | Headline |
|---|---|---|---|
| L1 | Cold-path TTFT vs prompt length | **computable, measured** | `207 ms @1k` → `7,529 ms @32.8k`; cold prefill ≈ **230 µs/token** |
| L2 | Warm-path TTFT (cache hit) | **computable, measured** | `85 ms @1k` → `232 ms @32.8k`; hit costs **4.4 µs/token** |
| L3 | End-to-end service latency `T(L)` | **only by assumption** | the decode term is **inferred**, never fitted: no cell varies decode length against a fixed prompt |
| — | TTFT **attribution** (prefill vs queueing) | **not computable** | 6.7–12.3 µs/token across cells on the same box — a 1.8× spread with no field to explain it |
| — | Real-service latency | **not computable** | 100 % serial, single stream; no concurrency, no inter-arrival, no generation length |

---

## 1. Coverage: the rows are timing-rich, and timing is structured

Every row-shaped file on disk carries absolute client-side timings — but **not** the same ones, and that
asymmetry is itself a finding (`§1` of `state/logs/lat_derive.out`):

| Field | Cells carrying it | Records |
|---|---|---|
| `ttft_ms` + `wall_ms` | 18 of 20 row files (G3, G3-LIMIT-V2, WIN-SGL, WIN-VLLM, DENSE-SGL, MOE-VLLM, LIVE-MEAS, U9, U10, U2, U3, U4, U6, E1–E4R, G1, U15, CROSS-HTTP, M1-M) | ~10,000 |
| `latency_ms` only (no `ttft`) | **M4, TUNED** — the two eviction-pressure cells | 600 |
| `ttft_ms` only (no `wall`) | G5 (fan-out), E3 replicate, U2 resolved, U4b | 268 |
| no per-row timing | M1-M diag rows | 8 |

So the two cells that carry the package's **capacity** and **eviction-policy** conclusions (M4, TUNED)
record only a single undifferentiated `latency_ms` — they cannot say whether time went to prefill or to
queueing, while the cells that can are the ones without eviction pressure. **No cell is both.**

`ttft_ms` is **content-token first-delta**, not first-byte: `experiments/context-cache/client.py:132`
stamps it on the first non-empty `delta.content`, and thinking is disabled throughout, so the field is
a clean decode-start bound. `wall_ms` closes at stream end (`client.py:136`).

---

## 2. What IS computable

### L1 — cold-path TTFT, measured directly

U9 is the only cell whose `completion_tokens == 1` on all 139 rows (`state/logs/lat_derive.out` §4), so
its `ttft_ms` is **pure prefill** with the decode term removed rather than assumed:

| prompt tokens | cold median TTFT | warm median TTFT | warm/cold |
|---:|---:|---:|---:|
| 1,024 | 207.4 ms | 85.5 ms | 0.412 |
| 2,048 | 348.1 ms | 87.2 ms | 0.251 |
| 4,096 | 692.9 ms | 105.2 ms | 0.152 |
| 8,192 | 1,421.9 ms | 130.2 ms | 0.092 |
| 16,384 | 3,054.9 ms | 139.2 ms | 0.046 |
| 32,768 | 7,529.0 ms | 231.6 ms | 0.031 |

OLS over the six lengths: **229.998 µs/token**, intercept **−263.9 ms**, r2 **0.9903**. The negative
intercept and the rising per-1024-token marginal (140.7 → 172.4 → 182.2 → 204.1 → 279.6 ms) say the
prefill term is **super-linear in L** — consistent with attention's L² component overtaking the linear
weight/activation pass somewhere above 2k tokens. **Caveat that must travel with the slope:** the six
lengths are fixed, so this is not a fit with six free parameters — it is a fit whose leverage is
mostly the far end, and it should not be quoted below 1k or above 32k.

### L2 — warm-path TTFT, measured directly

Same table, right column. A hit's TTFT grows only `85 → 232 ms` over a **32×** span of prompt length:
**4.4 µs/token** of residual (the row that cannot be served from cache, plus the fixed request
overhead). This is the quantity that makes the cache *worth* having, and it is the most robust number
in the package because it is the least sensitive to anything.

Per-row where the cell supports it, recomputed in this pass — predicate stated so a reader can re-run it
(the `cached_tokens == prompt_tokens` shortcut does **not** work: no row carries a full hit):

| Cell | Predicate | Warm median | Cold / blocked median |
|---|---|---:|---:|
| `U2/u2_cache_rows.jsonl` | `arm == "warm"` vs `arm == "cold"`, 44 rows each | **83 ms** | 199 ms (cold) |
| `E4/e4_rows.jsonl` | `cached_tokens > 0` (role `rep1`, n=40) vs role `cold` (n=85) | **75 ms** | 209 ms |
| `E4R/e4r_rows.jsonl` | same (rep1 n=5 / cold n=46) | **109 ms** | 245 ms |

All three agree that a warm first token costs roughly **a third** of a cold one at short lengths — the
same direction as U9's 0.412 at 1,024 tokens, and reached without any decode term.

### L3 — end-to-end, **by decomposition only** (see §3)

---

## 3. L3 is an assumption, and the assumption is the weak link

To turn TTFT into service latency one needs a decode term. **No cell varies `completion_tokens`
against a fixed prompt.** The pools are: 1 token (U9, 139 rows), 2 tokens (1,986 rows), 4 tokens
(9,323 rows), 8 (G5), 64 (U6), and a handful of singletons — `state/logs/lat_derive.out` §5. The one
cell with a slope across five distinct lengths is U6, **26.81 ms/token at r2 0.9919** — a *warm*
MoE cell sending 35–64 output tokens.

So a `T(L, G)` model can be **written down** —

```
T(L, G) ≈ TTFT(L) + G · r        r = 26.81 ms/token (U6, warm MoE)
```

— and it is not a fit. It grafts a warm-cell rate onto cold-path TTFT and assumes the two compose
linearly and without interaction. **The honest status is "usable to order magnitude, not citable as a
measurement."** The rows cannot distinguish `r` between a cold and a warm prefill, cannot test whether
decode and prefill serialise the way the formula assumes, and never hold L fixed while G moves.

**The manuscript already says this** (`MANUSCRIPT.md:710`): *"`max_tokens` was 4 and thinking was
disabled, so decode time is negligible and TTFT dominates."* That is true **and** it is exactly why
service latency is out of reach: the design that makes TTFT clean is the design that removes the second
term.

---

## 4. What honestly CANNOT be computed — and what each would need

| Metric | Why the rows can't carry it | Smallest design that would |
|---|---|---|
| **Prefill/queueing attribution** | Same box, same model, `ttft` slopes of **6.71 / 9.20 / 9.48 / 12.31 µs/token** across G3-LIMIT-V2 / DENSE-SGL / WIN-SGL / LIVE-MEAS (`lat_derive.out` §3), r2 0.83–0.97. No field distinguishes a slower kernel from a busier queue. | One sweep with a *sent-just-after-previous* flag, or server-side `request_start/exe` timestamps — neither exists in any row. |
| **Latency under concurrency** | **100 % serial.** No `parallel`/`semaphore`/`ThreadPool`/`concurrent` object exists in `experiments/context-cache/client.py` or `runner.py`; `CROSS-HTTP` is 3 rows. Every TTFT is an **unloaded** TTFT. | K concurrent clients at fixed arrival rate; needs a request cap and a lock. |
| **Real-service latency** | The workload is a synthetic serial corpus of constant-size turns. No arrival process, no generation length, no interleaved sessions. | A trace replay, not a corpus replay. |
| **P95 / P99 / any tail** | Per-condition n is 5–10 (U9: 7–22 per length; U10: 5 per cell). The tail of a 5-sample distribution is the maximum. | ≥100 samples per condition. The **wall** cells have the rows (WIN-SGL 1800, G3-LIMIT-V2 2780) but not the design. |
| **Cold-start / model-load TTFT** | No cell records first-request-after-restart separately. | One instrumented restart, **needs-restart** — forbidden without user approval. |
| **Server-side time to first token** | Both fields are client-side wall-clock; network + tokenisation bound the measurement from above but are not subtracted. | Client minimise-mode (pre-warmed connection, pre-tokenised prompt) or server instrumentation. |
| **Anything on the vLLM cross-engine pair** | `CROSS-HTTP` has **3 timing rows**; `MOE-VLLM`/`WIN-VLLM` carry `ttft_ms` but no `latency_ms`. | A cross-engine timing cell — not a cache cell. |

---

## 5. Correctness checks against what the package already publishes

Derived independently in this pass, these reproduce:

| Published | Recomputed here | Verdict |
|---|---|---|
| C33 ratio exponent −0.7837; miss L^1.0520 (r2 0.9934) | same U9 rows, same medians | **reproduces** |
| C34 miss 0.240736 ms/token vs hit 0.004659; 51.67× | OLS 0.229998 ms/token — C34's is a **log-log** OLS, this is **linear**, hence the gap | **consistent, differently parameterised** |
| U9 cold medians 207.4 / 348.1 / 692.9 / 1,421.9 / 3,054.9 / 7,529.0 | exact match on all six | **reproduces** |
| C40 "missed 1,024-token prefill costs 268.4 ms median TTFT" | U10 p1 `rep1` at L=1,024 = **268 ms**, exact | **reproduces — but it is a boundary-repeat measurement, not a cold prefill.** The cold send at the same length is **531 ms**; the honest cold-path figure is ~531 ms at 1,024. Read the 268 ms as "cost of the repeat that failed to hit," never as "cold prefill cost." |
| S17 "hit 4.66 µs/token vs miss 0.240736 ms/token" | U9-only, `completion_tokens=1` | **reproduces, and carries the only occurrence of the inflated denominator problem** — every other µs/token figure in the package uses 2- or 4-token rows |

---

## 6. The one place the package's latency framing is weakest

`S12`/`C60` read a **11.2344×** gap in *uncached tokens per turn* (TUNED 8,305.0 vs G3 739.25) and the
brief narrates it as a cost. Measured **in time**, on the same SGLang deployment:

| | median TTFT | uncached/turn | hit fraction |
|---|---:|---:|---:|
| G3 (production) | **439.5 ms** | 739.25 | 0.9742 |
| TUNED (SLRU at pressure) | **1,612.6 ms** | 8,305.00 | 0.0345 |
| **ratio** | **3.6693×** | **11.2344×** | — |

**The token ratio overstates the latency penalty by 3.06×.** The eleven-fold uncached cost buys only a
3.7× slower first token, because a prompt that is fully uncached still runs at the prefill rate while a
partially cached one pays fixed overheads the uncached one does not. A reader who converts "11.2× more
uncached work" into "11.2× slower service" is wrong by the full slope of the prefill curve — and this
is derivable from rows already on disk, with no new request.

**Attendance note.** This is a median-of-medians comparison, not a per-row paired ratio (TUNED and G3
share no paired turns); the per-row paired version is not computable from these two cells.

---

## 7. Standing scope

- **0 live requests, 0 locks, 0 writes outside this workspace.** Target repos untouched.
- Every number re-derives from `state/logs/lat_derive.py`; no value here is quoted from a document
  without being recomputed in §5.
- `partial` by construction: L3 is an assumption and the attribution/concurrency/tail metrics are
  named as missing rather than estimated.
