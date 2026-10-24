# U2 — instrument-gate: evidence

**Unit:** U2 `instrument-gate` · **Status:** done · **UTC:** 2026-10-20T23:03:42Z → 2026-10-20T23:04:02Z
**Verdict:** G0 **PASS** (6/6 checks) · E2 tax law **CONFIRMED** (44/44 lengths, `residual == 0`, max |residual| = 0).
**Budget:** 97/200 live requests · 20.45 s wall · lock held with `flock` for the whole run · **`/flush_cache` never called**.

## 1. Literal commands

```
cd "/home/zer0null/reserach extarctor"
fcntl.flock(experiments/context-cache/.occamy.lock, LOCK_EX)   # in-process, 1800 s deadline; acquired in 0.00 s
python3 experiments/context-cache/cells/U2/u2_gate.py
python3 - <<'PY'   # independent re-check with the instrument's own analyzer
  analyze.rows_from_jsonl("experiments/context-cache/cells/U2/u2_cache_rows.jsonl")
  analyze.tax_error([warm rows])  -> 0
PY
```

Driver: `experiments/context-cache/cells/U2/u2_gate.py` (uses `client.ChatClient.chat`,
`make_salt`, `normalise_cache`, `CacheRow`; patches only the client's *imported*
`normalise_cache` name to archive the raw `usage`). No private HTTP client was written.

## 2. Server archive (read-only GETs, sha256)

| GET | sha256 | bytes | status |
| --- | --- | --- | --- |
| `http://192.168.2.168:8012/server_info` | `0e00599527236be57b03cbfd97a34de5a294b8e69e43ba841ba59ef14d244bfd` | 32584 | 200 |
| `http://192.168.2.168:8012/get_model_info` | `1750b16ee1a0c0673d51a886c2c97e09027773b0fe2b866d4f9f65cec8ea9b87` | 1451 | 200 |

Captured `2026-10-20T23:03:42Z` → `experiments/context-cache/cells/U2/server_config.json` (bodies in full).
Confirmed from the bodies: `page_size=1`, `chunked_prefill_size=8192`, `max_total_num_tokens=1306681`,
`max_running_requests=5`, `schedule_policy=fcfs`, `disable_radix_cache=false`, `kv_cache_dtype=fp8_e4m3`,
`mem_fraction_static=0.45`, `model_type=qwen3_5_moe`, `architectures=["Qwen3_5MoeForConditionalGeneration"]`.

## 3. G0 — gate evidence

**G0.1 cold → `prompt_tokens_details` null.** Raw `usage` dict, verbatim, L=841, fresh salt `f2898d9da6d48639` (make_salt(90001)):

```json
{"completion_tokens": 2, "prompt_tokens": 841, "prompt_tokens_details": null, "reasoning_tokens": 0, "total_tokens": 843}
```

`prompt_tokens_details` is **present as JSON null** (not `{"cached_tokens": 0}`); `cached_tokens` coerced to 0.

**G0.2 identical repeat.** L=841 → cached **832**, `832 <= 841`. Warm row: `uncached=9 = 841 mod 64`. ✔

**G0.3 streaming single-pass.** Same three requests carried `ttft_ms` = [72.727, 67.89, 71.179] **and** `cached_tokens` = [832, 832, 832] from one `stream: true` + `stream_options.include_usage` request each. ✔

**G0.4 determinism.** Three identical repeats in a row:

| rep | prompt_tokens | cached_tokens | ttft_ms |
| --- | --- | --- | --- |
| 1 | 841 | 832 | 72.727 |
| 2 | 841 | 832 | 67.89 |
| 3 | 841 | 832 | 71.179 |

All three identical → **deterministic**. ✔

| check | result |
| --- | --- |
| `cold_cached_zero` | PASS |
| `cold_details_absent` | PASS |
| `deterministic` | PASS |
| `repeat_cached_le_prompt` | PASS |
| `repeat_cached_positive` | PASS |
| `stream_single_pass_ttft_and_cache` | PASS |

## 4. E2 — full sweep table (44 lengths, 2 requests each: cold then identical warm)

Cold isolation = fresh `make_salt(seed)` at token 0 of the prompt. **Every cold request returned `cached=0`**
(`cold_cached_nonzero = []`), confirming the salt really isolates the radix prefix.

| n | L | L%64 | cold cached | warm cached | warm uncached | residual | TTFT ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
|   10 |   314 |  58 |    0 |   256 |   58 |   58 |   +0 |    89.8 |
|   11 |   354 |  34 |    0 |   320 |   34 |   34 |   +0 |    90.0 |
|   12 |   370 |  50 |    0 |   320 |   50 |   50 |   +0 |   100.6 |
|   13 |   391 |   7 |    0 |   384 |    7 |    7 |   +0 |    85.3 |
|   14 |   445 |  61 |    0 |   384 |   61 |   61 |   +0 |    93.9 |
|   15 |   451 |   3 |    0 |   448 |    3 |    3 |   +0 |    60.9 |
|   16 |   495 |  47 |    0 |   448 |   47 |   47 |   +0 |    82.2 |
|   17 |   549 |  37 |    0 |   512 |   37 |   37 |   +0 |    97.0 |
|   18 |   539 |  27 |    0 |   512 |   27 |   27 |   +0 |   110.4 |
|   19 |   581 |   5 |    0 |   576 |    5 |    5 |   +0 |    64.6 |
|   20 |   569 |  57 |    0 |   512 |   57 |   57 |   +0 |    91.9 |
|   21 |   609 |  33 |    0 |   576 |   33 |   33 |   +0 |    89.5 |
|   22 |   642 |   2 |    0 |   640 |    2 |    2 |   +0 |    59.7 |
|   23 |   689 |  49 |    0 |   640 |   49 |   49 |   +0 |   101.4 |
|   24 |   732 |  28 |    0 |   704 |   28 |   28 |   +0 |    77.1 |
|   25 |   759 |  55 |    0 |   704 |   55 |   55 |   +0 |   101.0 |
|   26 |   706 |   2 |    0 |   704 |    2 |    2 |   +0 |    61.8 |
|   27 |   769 |   1 |    0 |   768 |    1 |    1 |   +0 |    69.8 |
|   28 |   794 |  26 |    0 |   768 |   26 |   26 |   +0 |    79.6 |
|   29 |   848 |  16 |    0 |   832 |   16 |   16 |   +0 |    72.0 |
|   30 |   870 |  38 |    0 |   832 |   38 |   38 |   +0 |    92.8 |
|   31 |   915 |  19 |    0 |   896 |   19 |   19 |   +0 |    76.2 |
|   32 |   885 |  53 |    0 |   832 |   53 |   53 |   +0 |   100.8 |
|   33 |   958 |  62 |    0 |   896 |   62 |   62 |   +0 |    87.9 |
|   34 |   968 |   8 |    0 |   960 |    8 |    8 |   +0 |    64.8 |
|   35 |   977 |  17 |    0 |   960 |   17 |   17 |   +0 |    78.0 |
|   36 |  1043 |  19 |    0 |  1024 |   19 |   19 |   +0 |    74.5 |
|   37 |  1052 |  28 |    0 |  1024 |   28 |   28 |   +0 |    80.0 |
|   38 |  1069 |  45 |    0 |  1024 |   45 |   45 |   +0 |    86.5 |
|   39 |  1109 |  21 |    0 |  1088 |   21 |   21 |   +0 |    80.1 |
|   40 |  1143 |  55 |    0 |  1088 |   55 |   55 |   +0 |    95.6 |
|   41 |  1148 |  60 |    0 |  1088 |   60 |   60 |   +0 |    95.6 |
|   42 |  1193 |  41 |    0 |  1152 |   41 |   41 |   +0 |    88.9 |
|   43 |  1210 |  58 |    0 |  1152 |   58 |   58 |   +0 |    83.2 |
|   44 |  1252 |  36 |    0 |  1216 |   36 |   36 |   +0 |    96.2 |
|   45 |  1321 |  41 |    0 |  1280 |   41 |   41 |   +0 |    81.2 |
|   46 |  1249 |  33 |    0 |  1216 |   33 |   33 |   +0 |    99.0 |
|   47 |  1302 |  22 |    0 |  1280 |   22 |   22 |   +0 |    67.2 |
|   48 |  1402 |  58 |    0 |  1344 |   58 |   58 |   +0 |    89.4 |
|   49 |  1358 |  14 |    0 |  1344 |   14 |   14 |   +0 |    63.9 |
|   50 |  1372 |  28 |    0 |  1344 |   28 |   28 |   +0 |    65.9 |
|   51 |  1428 |  20 |    0 |  1408 |   20 |   20 |   +0 |    64.5 |
|   52 |  1435 |  27 |    0 |  1408 |   27 |   27 |   +0 |    81.6 |
|   53 |  1550 |  14 |    0 |  1536 |   14 |   14 |   +0 |    64.5 |

## 5. Statistics — the 64-token tax law

| quantity | value |
| --- | --- |
| lengths tested | **44** |
| distinct `L mod 64` | **33** (> 20 required) |
| residues covered | [1, 2, 3, 5, 7, 8, 14, 16, 17, 19, 20, 21, 22, 26, 27, 28, 33, 34, 36, 37, 38, 41, 45, 47, 49, 50, 53, 55, 57, 58, 60, 61, 62] |
| length range | 314 – 1550 tokens (37 lengths ≥ 512) |
| `residual == 0` | **44/44** |
| mean residual | 0.0 |
| max abs residual | **0** |
| \|residual\| > 32 | **0** (kill threshold: ≥ 2 of 12+) |
| rows violating `cached == 64*floor(L/64)` | 0/44 (independent recheck) |
| `analyze.tax_error(warm rows)` | **0** |
| distinct warm `cached` values | 20 |
| weighted hit rate over warm rows | 38400/39815 = 0.9645 |

**Residual distribution: `{"0": 44}`** — a point mass at zero, no tail.
**Verdict: CONFIRMED.** `uncached == L mod 64` on every one of 44 warm requests; the tax is
exactly the unaligned tail, as claimed.

**Chunked prefill (8192).** No sweep length reaches 8192 (max 1550), so chunked prefill never
splits a sweep prompt — residuals cannot be attributed to it. A dedicated probe past the boundary:
**L=15787**, cold cached 0, warm cached 15744,
uncached 43 = `15787 mod 64`,
**residual +0** — the law survives a two-chunk prefill. So no residual is
explainable by chunked prefill; there are no residuals at all.

## 6. Boundary — prompt shorter than 64 tokens

L = [42, 42] (< 64), sent twice with the same salt:
cached = [0, 0]. **`cached > 0` never occurs below one 64-token block** — the
boundary matches `64*floor(L/64)` = 0.

## 7. Raw-usage coercion accounting

97 live requests → 97 captured raw `usage` dicts. **49 coercions** (null/absent `prompt_tokens_details` → 0).
These are exactly the cold requests plus the two short-prompt requests (L=42 has no cached block, so
SGLang reports no details even on the repeat): 1 G0-cold + 44 E2-cold + 1 cal + 1 long-cold + 2 short = 49.
The 48 warm requests with `cached > 0` all carried a non-null `prompt_tokens_details`.
Raw log: `experiments/context-cache/cells/U2/u2_raw_usage.jsonl` (one line per request, `usage` verbatim, null retained).

## 8. Artifacts

| path | contents |
| --- | --- |
| `experiments/context-cache/cells/U2/server_config.json` | both GET bodies, sha256, UTC timestamp |
| `experiments/context-cache/cells/U2/u2_report.json` | G0 checks + E2 stats + verdict + counts |
| `experiments/context-cache/cells/U2/u2_rows.jsonl` | 44 swept lengths (cold+warm per record) — source of the table |
| `experiments/context-cache/cells/U2/u2_cache_rows.jsonl` | 88 `CacheRow`s (44 cold, 44 warm) for `analyze.py` |
| `experiments/context-cache/cells/U2/u2_raw_usage.jsonl` | 97 raw usage dicts |
| `experiments/context-cache/cells/U2/u2_gate.py` | reproducible driver |
| `experiments/context-cache/.occamy.lock` | the mandated lock file (created, flocked, released) |

## 9. What this licenses downstream

1. A cache measurement is trustworthy when taken warm with a fixed salt: `cached` is exactly
   `64*floor(L/64)` and indistinguishable run to run.
2. **Cold requests must be coerced** — reading `usage.prompt_tokens_details.cached_tokens` naively
   raises on `None`. `normalise_cache` is correct; a harness that trusts the key will crash or
   silently miscount.
3. Any harness-side residual > 0 on a warm, byte-identical repeat is a **harness bug** (prefix broken
   by a changed byte), not server noise — the server's own residual is 0 across 44 lengths and a
   15,787-token prompt.
4. TTFT is only meaningful from serialised requests: `max_running_requests=5` on a shared box,
   single-flight in this sweep.

**Caveat for cost claims:** all of the above measures *server accounting of cached tokens*, not GPU
time saved. `residual == 0` proves the meter is aligned to the 64-token grid; it does not by itself
prove the wall-clock saving of a cache hit, which needs the TTFT contrast at scale.
