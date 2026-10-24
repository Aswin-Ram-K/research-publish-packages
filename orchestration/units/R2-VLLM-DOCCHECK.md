# R2-VLLM-DOCCHECK — vLLM 0.27.1 API/flag documentation check

**Status:** done · **Tool calls:** 14 / 25 · **Blocker:** none

**Pinned ref:** tag `v0.27.1` = commit `6e448d0ea9bf3d88d898b65449ca6dc2aec170ac` (tagged 2026-08-11).
All quotes are verbatim from a shallow clone of that commit. Nothing was unreached, so no `main`
fallback and no drift caveat applies.

## Purpose

The vLLM cell `experiments/context-cache/cells/R2-VLLM/` reads
`usage.prompt_tokens_details.cached_tokens` from `POST /v1/chat/completions` streaming responses and
depends on the engine flag `--enable-prompt-tokens-details` (present on A1, absent on OH1/OH1L — the
defect being repaired). This unit confirms all five contract clauses from vLLM's own source.

## Answers

| # | Question | Answer |
|---|---|---|
| 1 | Flag exists / default / conditional? | Exists, default `False`, field populated **only** when set |
| 2 | Streaming: per chunk or final only? | **Final usage chunk only** |
| 3 | Flag absent + prefix caching: omitted or 0? | **Key absent** (never `0`) |
| 4 | Flag-independent surface? | Yes — `vllm:prefix_cache_hits` / `vllm:prefix_cache_queries` (no `gpu_` prefix), `vllm:kv_cache_usage_perc` |
| 5 | `--prefix-match-unit` semantics? | Positive int or unset; non-divisible ⇒ `ValueError`; **2096 % 8 == 0** |

### 1. The flag and its conditioning

`vllm/entrypoints/openai/cli_args.py:132-133`:

```python
    enable_prompt_tokens_details: bool = False
    """If set to True, enable prompt_tokens_details in usage."""
```

The flag name is auto-derived in `FrontendArgs.add_cli_args` (`:217-241`):
`frontend_group.add_argument(*extra_flags, f"--{key.replace('_', '-')}", **value)` ⇒
`--enable-prompt-tokens-details`.

The conditioning point is `vllm/entrypoints/openai/chat_completion/serving.py:88-109` —
`if not enable_prompt_tokens_details: return None` is the first statement of
`_make_prompt_tokens_details`. `UsageInfo.prompt_tokens_details` is typed
`PromptTokenUsageInfo | None = None` (`engine/protocol.py:119`).

### 2. Streaming with `stream_options: {"include_usage": true}`

Only the **final** chunk carries details (`chat_completion/serving.py:763-779`). Per-chunk usage, built
when `include_continuous_usage` is on, sets `prompt_tokens`/`completion_tokens`/`total_tokens` and
nothing else (`:534-538`, repeated at `:570-575`).

### 3. Flag absent → key absent, not zero

Two independent mechanisms, both quoted in `state/logs/R2-VLLM-doccheck.json`: the flag-false guard
returning `None`, and `chunk.model_dump_json(exclude_unset=True)` (`:761`) over a base model whose
`model_config` is `ConfigDict(extra="allow")` with no `exclude_none` (`engine/protocol.py:31-33`).

**Consequence for the cell:** a consumer must coalesce *missing → 0*. Even with the flag on,
`cached_tokens` is `int | None` and is `null` on a cold prompt — so `null → 0` is required in **both**
configurations.

### 4. Flag-independent cache-hit surface

`vllm/v1/metrics/loggers.py:584-601` defines `vllm:prefix_cache_queries` and `vllm:prefix_cache_hits`;
`:562` defines the gauge `vllm:kv_cache_usage_perc`. They are incremented from
`scheduler_stats.prefix_cache_stats` at `:1125-1129`, in **tokens**, monotonic per engine, and are
untouched by `--enable-prompt-tokens-details`.

⚠ The names in the unit card, `vllm:gpu_prefix_cache_hits_total` /
`vllm:gpu_prefix_cache_queries_total`, occur **nowhere** in the v0.27.1 tree — they are the pre-V1
spelling. Ratio must be taken from a **delta pair** of two scrapes, not absolute values.

### 5. `--prefix-match-unit`

`vllm/config/cache.py:56-69`: "The finest token boundary (in tokens) a prefix-cache hit can land on."
Valid values: any integer `> 0` (`Field(default=None, gt=0)`), or unset.

`vllm/v1/core/kv_cache_utils.py:678-690` raises on non-divisibility:

```python
    if any(bs % hash_block_size != 0 for bs in group_block_sizes):
        raise ValueError(
            f"Invalid prefix_match_unit={hash_block_size}; all KV cache group "
```

Two scope limits matter for any probe: the check is skipped entirely when `len(groups) <= 1`
(`:648-650`), and it is skipped when neither prefix caching nor a connector is enabled (`:663-664`).

## Findings for the cell (reported, not repaired here)

1. **The OH1L leniency probe's premise is false.** 2096 / 8 = 262 exactly ⇒ `2096 % 8 == 0` ⇒
   `--prefix-match-unit 8` is *valid* and raises nothing. To exercise the rejection path, use a unit
   that does not divide 2096 (`2096 % 3 == 2`, so `3` or `7`) and assert on the literal `ValueError`.
2. **Metric names are stale** (see §4).
3. **Missing-vs-zero** (see §3) is exactly the OH1/OH1L defect mechanism.

## Write paths

`state/logs/R2-VLLM-doccheck.json`, `orchestration/units/R2-VLLM-DOCCHECK.md`,
`orchestration/handoffs/R2-VLLM-DOCCHECK.json`

## Containment

GitHub (raw + git clone) only. Zero requests to `192.168.2.168`, zero model requests, no ssh, no
docker, no board operations, no `papers/**` edits.
