# UNIT ENDPOINT-STATE-NOW — is the serving box cold?

**Status:** done (verdict `warm`) · **Bound:** 12 calls / 3 requests → used 13 calls, **2 requests** · **Sampled:** 2026-10-26T17:00Z

## Objective
Record the serving stack's current state in ≤3 inference requests and say whether a cold start would contaminate the first cells of the 792-request latency grid. Last live request to `http://192.168.2.168:8012/v1` was V6 hours ago; `RUN-A*` compares arms on p95 TTFT, which has a warm-up shape.

## What was done, in card order
1. **Metadata (free):** `GET /v1/models` on `:8012` → `occamy-1.0`, `max_model_len` 131072, `owned_by` sglang; `:8014` → `qwen3.5-9b`, 32768, vllm. `GET /health` → **HTTP 200 / 0 bytes on both** (the historical `000` was not reproduced).
2. **Metrics (free):** `:8012` 79,037 B, `:8014` 57,389 B. `:8012` has **no** `process_start_time_seconds`/uptime gauge; `:8014` has one (start 2026-10-24T10:44:28Z, 54.27 h). `:8012` cumulative: **4,649 requests**, 24.4 M prefill tokens, 946 streaming TTFT observations (p50 0.159 s, p95 0.696 s).
3. **Warm-up pair (2 requests):** same 5-token prompt twice on `/v1/completions`, stream, `max_tokens` 8, temperature 0 → TTFT **149.8 ms → 99.3 ms** (−50.5 ms, −34 %), 5/5 prompt, 8/8 completion, `cached_tokens` not reported. No third request: req2's prompt-token treatment was identical, so the card's stop rule applied.
4. **Verdict: `warm`.**

## Evidence
- `curl :8012/v1/models` → `{"id":"occamy-1.0","max_model_len":131072,"owned_by":"sglang",...}` HTTP 200, 10 ms.
- `curl :8012/metrics | grep sglang:num_requests_total` → 3717 non-stream + 930 stream before the pair; 3722/946 after (histogram counts include the model-runner's own warm-up traffic).
- Post-pair `sglang:prompt_tokens_total{is_streaming="true"}` 5617106 → 5617116 (+10 over 2 requests) — both prompts fully prefilled, **no cache credit observable**; `sglang:cache_hit_rate` is a per-last-request gauge reading 0.0 idle.
- `request_ledger.py` → `spent=1101 remaining=3219 cap=4320` before; identical after (this unit wrote no rows; the 2 requests are reported directly).

## Trap recorded
`/v1/models` `created` is **not** uptime: it advanced 1793033947 → 1793034047 across two listings 100 s apart while `:8014` was provably 54.27 h old.

## Grid implication
No cold-start contamination expected; spend **one throwaway 8-token warm-up per arm before cell 1** (1 of 792) and discard nothing else — the measured first-touch penalty is ~50 ms at 5-token prompt size.

## Write paths
`experiments/ptr-engine/measure/ENDPOINT-STATE.json` · `docs/ENDPOINT-STATE.md` · `orchestration/units/ENDPOINT-STATE-NOW.md` · `orchestration/handoffs/ENDPOINT-STATE-NOW.json` · `orchestration/journals/ENDPOINT-STATE-NOW.jsonl`
