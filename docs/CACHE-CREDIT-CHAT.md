# CACHE-CREDIT-CHAT — is per-request cache credit measurable on the runner's own endpoint?

**Unit:** `CACHE-CREDIT-CHAT` · **Requests spent: 2 of 4** (stop rule hit on request 2)
**Endpoint under test:** `http://192.168.2.168:8012` — `/v1/chat/completions`, never loopback
**Sampled:** 2026-10-26T17:04:38Z · **Artefact:** [`measure/CACHE-CREDIT-CHAT.json`](../experiments/ptr-engine/measure/CACHE-CREDIT-CHAT.json)
**Probe (re-runnable):** [`tools/cache_credit_probe.py`](../experiments/ptr-engine/tools/cache_credit_probe.py)

## Verdict

**Yes — H2's cache limb is measurable on the frozen runner exactly as it stands. No patch.**
`measure/ENDPOINT-STATE.json` is right about `/v1/completions` and wrong as a statement about
the endpoint the runner calls. Its two load-bearing caveats are contradicted by two requests.

## 1. Provenance, from code (no requests)

| What | Where |
|---|---|
| Runner posts to the **chat** endpoint | `experiments/ptr-engine/longrun/client.py:661` — `url = cfg.base_url.rstrip("/") + "/chat/completions"` |
| The field the runner reads | `experiments/ptr-engine/longrun/client.py:604` `usage_cached_tokens()` → `usage["prompt_tokens_details"]["cached_tokens"]`; `None` when absent, never imputed |
| Streaming asks for usage | `experiments/ptr-engine/longrun/client.py:339-340` — `stream_options = {"include_usage": True}` |
| The row key | `experiments/ptr-engine/longrun/run_longrun.py:1755-1757` — `prompt_tokens`, `cached_tokens`, `uncached_tokens` (`uncached = prompt − cached`, `None` if either is `None`) |
| Row provenance stamp | `run_longrun.py:1776` `token_source` = `"usage.prompt_tokens;usage.prompt_tokens_details.cached_tokens"` — the literal string every rows file carries |
| Published cached share | `measure/TVS.json` `definition.cached_share` = `sum(cached_tokens)/sum(prompt_tokens)` over rows whose `cached_tokens` is non-null |

**Is 0.8523 reproducible from on-disk rows?** Yes, from key `cached_tokens/prompt_tokens`.
TVS's own numerator/denominator for `rows-longrun-v6-tools` / `pointer-stable` / `cp.0.t12` are
`cached_tokens 93568` and `prompt_tokens 109780`, and `93568/109780 = 0.852323 → 0.8523`
(exact match at 4 dp). *Scope note:* this checks the published numerator against the published
denominator; it does not independently re-derive the turn-window sums from the `.jsonl`.

So the 0.8523 was never a capability of `/v1/completions` — it comes from the chat path, whose
usage object this probe re-measured today.

## 2. The pair (2 requests, `stream:false`, `max_tokens:4`, `temperature:0`)

Prompt: 2106 tokens, 9,189 chars, sent twice **byte-identical** (same serialised body object).
`prompt_tokens_details` verbatim:

```
request 1: {"prompt_tokens": 2106, "total_tokens": 2110, "completion_tokens": 4,
            "prompt_tokens_details": null, "reasoning_tokens": 4}
request 2: {"prompt_tokens": 2106, "total_tokens": 2110, "completion_tokens": 4,
            "prompt_tokens_details": {"cached_tokens": 2048}, "reasoning_tokens": 4}
```

Request 1 is JSON-`null` (cold), request 2 credits **2048 of 2106** prompt tokens (97.2 %).
The streamed pair was **not** spent — the stop rule fired on the non-stream pair, as instructed.

## 3. Free counters, same pair (`GET /metrics` before/after each request)

| metric | Δ on req 1 | Δ on req 2 |
|---|---|---|
| `sglang:cached_tokens_total` | 0 | **+2048** |
| `sglang:cache_hit_rate` (gauge) | 0.0 | **0.9725** |
| `sglang:uncached_prompt_tokens_histogram_sum` | +2106 | +58 |
| `sglang:uncached_prompt_tokens_histogram_count` | +1 | +1 |
| `sglang:realtime_tokens_total` | +2110 | +2109 |

Two independent instruments agree to the token: the response field says 2048, the cumulative
counter moved by exactly 2048, and the uncached histogram fell to the 58-token residue
(`2106 − 2048 = 58`, SGLang's block rounding). A cumulative cache-credit counter **does** exist
on this server (`sglang:cached_tokens_total`), and `sglang:cache_hit_rate` is a live per-last-request
gauge, not a dead 0.0.

## 4. The three questions

**(a)** On `/v1/chat/completions`, yes: request 2 of a byte-identical pair reports
`prompt_tokens_details.cached_tokens = 2048` (req 1 `null`) and accrues +2048 on
`sglang:cached_tokens_total`.

**(b)** Through **both** keys — the response field `usage.prompt_tokens_details.cached_tokens`
(read at `client.py:604`) and the metric delta `sglang:cached_tokens_total` — and that response
field is **already** written into rows as `cached_tokens` by `run_longrun.py:1756`, with
`cached_reported`/`cached_source` beside it.

**(c)** **Yes — measurable on the frozen runner as it stands.** No patch to `client.py` or
`run_longrun.py`; nothing to apply, and nothing applied here.

## 5. What this does NOT close

The streamed path was inferred, not re-measured in this probe's own requests: the stop rule
forbids spending requests 3–4 once the non-stream pair showed credit. The streamed path rests on
`client.py:339-340` plus the existing `stream: true` rows that carry `cached_reported: true`
(e.g. `rows-longrun-v6-tools.jsonl`). If a verifier wants streamed usage re-measured live, that is
a fresh 2-request unit — not a defect in this verdict.

## 6. The sentence that should replace the `ENDPOINT-STATE` caveat

> `:8012`'s `/v1/chat/completions` does report cache credit per request —
> `usage.prompt_tokens_details.cached_tokens` (`null` on a cold request, `2048` of `2106` on the
> second of a byte-identical pair) — and `/metrics` carries the cumulative counter
> `sglang:cached_tokens_total`, whose delta equals the reported figure exactly, with
> `sglang:cache_hit_rate` as a 0.0-when-idle corroborating gauge; the missing field and missing
> counter on `/v1/completions` are properties of that endpoint, not of the engine.

`docs/ENDPOINT-STATE.md` and `measure/ENDPOINT-STATE.json` were **not** edited by this unit.
