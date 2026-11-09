# UNIT `HARNESS-FIX-CLIENT` — honest TTFT and cache attribution at the client

**Status:** partial (client module + tests complete and green; wiring into `run_longrun.py`
is Part B's, per the card's explicit prohibition on my editing it).
**Wave:** part A of three cards sharing seam contract v1.
**Bound:** ≤30 tool calls, zero inference requests. Used: 13 tool calls, 0 requests.

## Why

`docs/EXTERNAL-SERVING-PRACTICE.md` §6 and `docs/STACK-RECON.md`: TTFT was latched only on
`delta.content`, later widened to `delta.reasoning_content`; a turn whose first delta is a
**tool call** latched nothing. Cache attribution had no per-request path at all even though
SGLang reports `usage.prompt_tokens_details.cached_tokens` (streaming needs
`stream_options.include_usage`) and vLLM's four engine counters are scrapable at `/metrics`.

**Finding the card's premise missed.** `experiments/ptr-engine/longrun/client.py` did not
exist in this checkout; the latch is inline in `run_longrun.py:1069-1078`. No wall-clock
fallback exists there either — the pre-fix failure mode for a tool-call-first turn is a
**null** TTFT (`timing_usable=False`), which drops the turn from p95, not an inflated one.
Both variants are dishonest; both are closed by this unit. The card path is now real: the
client module is created at the path the card names, and `run_longrun.py` is untouched.

## The exact latch, old → new

Old (`run_longrun.py:1071-1078`, verbatim):

```python
piece_c = delta.get("content")
piece_r = delta.get("reasoning_content")
if piece_r is None:
    piece_r = delta.get("reasoning")
# TTFT = dispatch -> first token on EITHER channel.
if (piece_c or piece_r) and ttft is None:
    ttft = time.perf_counter() - t0
```

New (`client.py:token_kind` + `collect_stream`):

```python
kind = token_kind(delta)                       # non-empty content | reasoning_content | tool_calls
if kind is not None and ttft is None:
    ttft = clock() - t0
    first_token_kind = kind
```

with `TOKEN_DELTA_KEYS = ("content", "reasoning_content", "tool_calls")` and no other
assignment to `ttft` anywhere in the module.

## What was built

`experiments/ptr-engine/longrun/client.py` — public names preserved from the inline
implementation (`request_body`, `extract_usage`, `send_chat`, `RequestFailure`,
`thinking_setting`, `thinking_kwargs`); `send_chat` returns a **superset** of the old dict.

- `ttft_ms` / `ttft_source` / `first_token_kind`: latched on the first delta carrying any
  token; `null` + `"unavailable"` and `null` kind when none arrives.
- `wall_ms` / `latency_s`: kept, never an input to `ttft_ms`.
- `stream_options={"include_usage": True}` always on a stream; `cached_tokens` from
  `usage.prompt_tokens_details.cached_tokens` with `cached_source="prompt_tokens_details"`
  when present and non-null (a measured `0` stays `0`).
- `/metrics` scrape immediately before and after each request when enabled; four keys
  parsed (`prefix_cache_queries`, `prefix_cache_hits`, `prompt_tokens_cached_total`,
  `prompt_tokens_total`), label sets summed, absent counter = `None` not `0`, failed scrape
  = `null` snapshots and a still-measured request.
- Fallback derivation: usage cached null + both scrapes present →
  `prompt_tokens_cached_total` delta, `cached_source="metrics_delta"`; a counter that moved
  backwards is refused (server restart cannot be attributed to one request), never clamped.
- Opt-in flag: **`--metrics-scrape` / `--no-metrics-scrape`** (`cfg.metrics_scrape`,
  env `PTR_METRICS_SCRAPE`), registered by `add_metrics_scrape_argument(parser)`,
  `DEFAULT_METRICS_SCRAPE = True` for the concurrency-1 protocol; every response carries
  `metrics_scrape: bool`.
- `/metrics` URL is de-API-fied (`http://host:8000/v1` → `http://host:8000/metrics`).
- No per-pinned-range attribution is claimed anywhere.

## Tests — `experiments/ptr-engine/longrun/tests/test_client_ttft.py`, 8/8 green, offline

Each case runs twice: through `legacy_measure()` (a faithful copy of the pre-fix latch and
cache read) where the contract assertion must **fail**, and through `send_chat` with faked
SSE, faked `/metrics` and a fake chunk clock, where it must hold. `socket.socket` is
replaced by a raising stub for the whole run.

| case | GREEN result | pre-fix result |
|---|---|---|
| a. first delta is `tool_calls` | `ttft_ms=300.0`, kind `tool_call`, wall 500.0 | `ttft_ms=None` — RED |
| b. `content:""` then real token | `ttft_ms=450.0` (not the 100.0 empty delta) | latched correctly but carried no `first_token_kind`/`ttft_source` — RED on contract |
| c. stream ends with no token delta | `ttft_ms=None`, `"unavailable"`, kind null, wall 2500.0 | no `ttft_source` — RED on contract |
| d. usage `cached_tokens=0` with scrapes present | `0`, `"prompt_tokens_details"` (usage beats the delta) | `0` but no source — RED on contract |
| e. no usage cache, two scrapes | `32`, `"metrics_delta"`, both snapshots with all four keys | imputed `0` — RED |
| f. flag off | 0 scrapes, null counters, `metrics_scrape=False`, default is True | no fields — RED |
| g. `/metrics` returns HTML / raises | null snapshots, `cached_tokens=None`, request still measured | n/a — new surface |
| h. parser + URL | sums label sets, absent → `None`, `/v1` stripped, backwards refused | n/a |

Honest red→green: (a) and (e) fail behaviourally against the pre-fix code; (b), (c), (d)
already measured the right *number* but could not attribute it (`cached_source`,
`ttft_source`, `first_token_kind` absent), so their contract assertions are red too. Case
(f) proves the cost control: with the flag off the wire sees no extra request.

Run: `python3 experiments/ptr-engine/longrun/tests/test_client_ttft.py` → exit 0,
`8/8 cases green; offline=yes`; `python3 -m pytest -q …/test_client_ttft.py` → `8 passed`.

## What Part B must do (not done here — `run_longrun.py` is theirs)

1. `import client` and replace the inline `send_chat`/`request_body`/`extract_usage` with
   `client.send_chat(cfg, messages)` (one call site, ~line 1196).
2. Add the flag: `cfg = client.add_metrics_scrape_argument(ap).parse_args(argv)` — or add
   the two `add_argument` calls and `--metrics-timeout` (default 5.0).
3. Pass through the new row fields in `make_row`: `ttft_source`, `first_token_kind`,
   `cached_tokens`, `cached_source`, `engine_metrics_before`, `engine_metrics_after`,
   `metrics_scrape`, `wall_ms`. Leave `answer_kind`/`answer_value`/`answer_raw` to Part B/C.
4. Decide the fate of `normalize_cached_tokens(resp["raw_cached"], engine)`: it imputes
   `0` for SGLang nulls, which contradicts "never a guess". The client already returns the
   contract value in `resp["cached_tokens"]`; `make_row` should prefer it.
5. Re-run the growth arms afterwards: the p95 TTFT numbers cited in the card
   (grow 838.85 / compact 224.08 / stable 356.12 / lease-reopen 201.78 ms) are computed
   over the contaminated sample and must be recomputed, not reused.
