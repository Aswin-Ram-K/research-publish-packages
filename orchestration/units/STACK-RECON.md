# UNIT STACK-RECON — serving-stack observability audit

**Status:** done (partial scope: doc gaps recorded, not resolved)
**Run:** 2026-10-26T09:23–09:34 America/Chicago
**Tag:** `automated` — no human answerer; `ask_user_question` never called.
**Bound:** ≤25 tool calls. **Used: 19.**

## Purpose

The project asserts prefix-cache behaviour and TTFT tails from a row schema that may not be able to see
either. Before another measurement cell runs, establish what our own servers (SGLang :8012, vLLM :8014 on
`gx10` at 192.168.2.168) actually expose. Operator directive (m00372 / m00379): live, relevant findings —
not a literature review.

## Hard constraints honoured

- **Zero inference requests.** No completion, chat, or tool call. Only `GET` on
  `/v1/models`, `/metrics`, `/metrics/`, `/version`, `/health`, `/get_server_info`.
- No server restart, no flag change, no mutating endpoint (SGLang `flush_cache` / vLLM
  `/reset_prefix_cache` deliberately untouched).
- Writes confined to the three declared paths.

## What was done

1. Probed 6 endpoints × 2 ports, recording every HTTP status (§1 of `docs/STACK-RECON.md`).
2. Dumped both `/metrics` bodies and extracted every metric family with its declared type, filtered to
   prefix cache / KV cache / queue / prompt+generation tokens / TTFT (§3).
3. Read SGLang `/get_server_info` (32,588 B) for the authoritative cache config (§2).
4. Checked current primary docs: vLLM metrics design page, vLLM tool-calling page,
   SGLang production-metrics page, vLLM GitHub issue search (§5).
5. Built a per-measurement verdict table (§6) and a 10-line bottom line (§7).

## Findings that change the plan

- **Card facts corrected:** SGLang model id is `occamy-1.0`, not `occamy-1.0-NVFP4`; SGLang `/health`
  now returns 200; SGLang has no `/version` (404).
- **vLLM is not blind to cache.** `prompt_tokens_details` is `null` in the response, but
  `vllm:prompt_tokens_cached_total` = 4,114,176 of 8,324,862 prompt tokens = **49.4 % lifetime**
  token-weighted hit rate. The `null` is a protocol gap.
- **SGLang is per-request observable** for cached tokens: `enable_cache_report=true` is already live, so
  `usage.prompt_tokens_details.cached_tokens` is populated — except on streaming rows unless
  `stream_options.include_usage` is sent (`stream_response_default_include_usage=false`).
- **No per-range attribution anywhere.** Both servers expose cumulative token counters and token-length
  histograms; neither names a prompt span.
- **Granularity differs:** SGLang `page_size=1` (token-granular) vs vLLM `block_size=1056` (auto-resolved)
  — the same pinned range reports different cached-token counts on the two servers.
- **Queueing is fabricated above 5 concurrent on SGLang:** `max_running_requests=5`.

## Not done / deliberately left

- Did not attempt to make `prompt_tokens_details` non-null on vLLM — that needs an inference request, which
  is out of bounds. Recorded as a hypothesis list plus a no-restart workaround (counter deltas at
  concurrency 1).
- Did not probe `--enable-per-request-metrics` behaviour — **requires-restart**, recorded as such.
- Public docs could not settle the exact population rule for vLLM's `prompt_tokens_details`. Marked
  unresolved rather than guessed.

## Deliverables

- `docs/STACK-RECON.md` — the audit (metric lists verbatim, verdict table, bottom line).
- `orchestration/handoffs/STACK-RECON.json` — machine-readable handoff.

## Next unit hint

A measurement unit that adopts the concurrency-1 `/metrics` delta protocol before running the pointer arm;
and a schema change to record `usage.prompt_tokens_details.cached_tokens` for SGLang rows plus a
pre/post `/metrics` snapshot pair for vLLM rows.
