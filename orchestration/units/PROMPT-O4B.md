# PROMPT-O4B — five-arm prompt cell on vLLM 0.27.1 (GX10), adopted corrected variant

**Purpose.** Measure the five prompt arms (R / A / C / H / C0) against the corrected
vLLM container `gx10-p-o4` — the variant no card owned. Arms are the *same artefacts*
as the SGLang cells (`PROMPT-O2-EXTRA`), so the engines stay comparable.

**Card state found.** `experiments/context-cache/cells/PROMPT-O4/` already held a
`GAMMA: unavailable` cell (0 rows) written 01:36 by a prior attempt that died in the
delta carry-over before phase A. Its `analysis.json` and `orchestration/handoffs/PROMPT-O4.json`
show the blocker as a **`stream_options` 400** — that was an artefact of the earlier
harness, not the container. Those files were overwritten by this run; the dead attempt's
rows count was 0, so nothing measurable was lost.

**Endpoint.** `http://192.168.2.168:8016/v1`, container `gx10-p-o4`
(`qwen3.5-9b`, `modelopt_fp4`, `kv-cache-dtype fp8`, `block-size 64`,
`prefix-match-unit 16`, `mamba-cache-mode align`, `max-model-len 32768`,
`--enable-prompt-tokens-details`). Readiness: `:8016` answered `000` on the first poll,
the container restarted mid-attempt, and the second poll reached **200 in 120 s**.

**Method.** 5 arms × 71 turns = 355 rows, budget 32768 tokens, `max_tokens=8`.
- `uncached_tokens = prompt_tokens − usage.prompt_tokens_details.cached_tokens`
- per-arm mean + two-sided 95 % t-interval, ddof=1, df=70
- deltas vs R paired over turns (n=71), `excludes_zero` flag
- `cached_tokens` is recorded exactly as the wire reports it — a null stays JSON `null`

**G0 gate (passed).** Two identical chat calls, 5631 prompt tokens each:
call 1 `cached_tokens = 0`, call 2 **`cached_tokens = 5616`**.

**Resolved geometry (docker logs).**
```
INFO [interface.py:911] Setting attention block size to 1088 tokens to ensure that
     attention page size is >= mamba page size.
INFO [interface.py:935] Padding mamba page size by 3.82% to ensure that mamba page size
     and attention page size are exactly equal.
INFO [kv_cache_utils.py:2235] GPU KV cache size: 677,500 tokens
```
`block_size` flag 64, `prefix_match_unit` 16, `mamba_cache_mode align`;
resolved **attention block size 1088 = 64 × 17**, KV cache 677,500 tokens.

**Result.** 355 rows, arms `{A, C, C0, H, R}`, 0 cached-null, 0 non-200, 284 rows with
`cached_tokens > 0`. Observed grid **gcd = 1088** (min positive 1088, max 23936, all
rows ≡ 0 mod 64 and mod 16) — i.e. the floor is the *resolved attention block*, not
`--prefix-match-unit 16`.

| arm | n | unc/turn | 95 % CI | weighted hit |
|---|---|---|---|---|
| R   | 71 | 915.7 | 840.2 – 991.1  | 0.9257 |
| A   | 71 | 921.0 | 846.7 – 995.3  | 0.5996 |
| C   | 71 | 932.9 | 858.6 – 1007.2 | 0.5965 |
| H   | 71 | 1099.0 | 940.6 – 1257.4 | 0.5453 |
| C0  | 71 | 913.8 | 838.1 – 989.4  | 0.9270 |

Deltas vs R: **A−R +5.3** [−101.0, 111.7] no · **C−R +17.2** [−89.1, 123.5] no ·
**H−R +183.3** [1.0, 365.6] **YES** · **C0−R −1.9** [−93.9, 90.1] no.
ARMS_IDENTICAL guard: no collisions (turn-1 sha256 identical to O2-EXTRA per arm).
Requests used: **357** of the 500 cap.

**Restore.** `gx10-p-o4` removed (already absent — `docker ps -a` grep count 0),
`:8014` → 200 `qwen3.5-9b`, `:8012` → 200 `occamy-1.0`, both production containers Up.
`gx10-occamy-nvfp4` never touched; `gx10-qwen9b` never stopped.

**Reading.** On vLLM the per-arm prompt layout is *not* what buys reuse — R (plain
resend) already holds the best weighted hit (0.926), and no arm improves on it. H is
the only arm that significantly differs from R, and it is **worse** by +183.3
uncached tok/turn: mid-context compaction destroys the stable prefix. The SGLang
result (`A−R −71.3`, `C−R −53.1`, `C0−R +111.7`) does **not** reproduce here, so the
arm effect is engine-specific — which is the finding, not a defect.

**Bound.** 18 tool calls, 357 live requests (cap 500).
**Write paths.** `experiments/context-cache/cells/PROMPT-O4/**`,
`orchestration/handoffs/PROMPT-O4B.json`, `orchestration/units/PROMPT-O4B.md`.
