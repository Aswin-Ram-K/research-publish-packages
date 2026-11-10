# CACHE-ACCOUNTING-PROBE — can this server report cache reuse, and how?

**Verdict:** `PER_REQUEST_FIELD_AVAILABLE`. `usage.prompt_tokens_details.cached_tokens` is populated
on real hits with no special request field, provided the server runs `--enable-cache-report`
(currently true). Controlling parameter: `enable_cache_report` in `server_args.py:1382`.

**What was done**
1. Derived the real reporting parameter from SGLang source inside the container (no guessing).
2. Tested request shapes: default fields, `return_meta_info`, `return_cached_tokens_details`, and
   ignored candidates (`return_meta`, `return_cached_tokens`, `extra_body`).
3. Byte-identical repeat probes: 45-token prompt (no hit) and 1280/2816-token aligned prompts
   (full/partial hits), with `sglang:prefill_effective_tokens_total` deltas.
4. Wrote `experiments/.../CONTEXT-SERVING-CAMPAIGN/notes/CACHE-ACCOUNTING.md`.

**Budget:** 22 preflight spent (8 prior + 14 this unit). 21 rows + 1 failed attempt, reconciled.

**Handoff:** `orchestration/handoffs/CACHE-ACCOUNTING-PROBE.json`.
