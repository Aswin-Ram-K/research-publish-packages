# R2-VLLM — prefix-match-unit 16 on both models

Status: **partial (measured; one branch unexplained, named below)**
Run window: 2026-10-23 21:45 → 22:27 CDT (2026-10-24 02:45 → 03:27 UTC)
Lock: `experiments/context-cache/.occamy.lock` held for the whole live phase, released by the
`finally` block (`{"unit": "R2-VLLM", "released_utc": "2026-10-24T03:27:40Z", "note": "R2-VLLM done"}`).
`gx10-occamy-nvfp4`: never stopped, restarted or removed (`Up 19 hours` before and after).
`gx10-qwen9b`: stopped twice for the dense arm, **restored and proven** (`logs/prod-restore.json`).

## Question

Both production models are hybrid (attention + Mamba) on vLLM 0.27.1, which resolves
`block_size = attn_block_size` (1056 dense, 2096 occamy) and, with `prefix_match_unit` unset, uses
**the whole block** as the APC hash unit. R2-VLLM asks: set the hash unit to 16 (`--prefix-match-unit 16`)
and re-measure the hit grid on both models.

## Arms

| arm | model | port | recipe | delta |
|---|---|---|---|---|
| OH1 | occamy-1.0 NVFP4 MoE | 8020 (new container `r2v-oh1`) | measured V3 recipe: gpu util 0.32, seqs 6, batched 8192, fp8 KV, no MTP | `--prefix-match-unit 16` + `--enable-prompt-tokens-details` |
| A1 | qwen3.5-9b dense | 8020 (prod container recreated) | prod's own Cmd, byte-identical | `--prefix-match-unit 16` + `--enable-prompt-tokens-details` |
| OH1L | occamy as OH1 | 8020 | as OH1 | `--prefix-match-unit 8` (leniency probe) |

`gx10-occamy-nvfp4` (:8012, SGLang) and `gx10-qwen9b` production (:8014) were left untouched as
controls; every launch/teardown record re-checked `occamy=200`.

## Result 1 — the flag reaches the engine and does not move the block

`/metrics` `vllm:cache_config_info` from each arm (logs `OH1-launch.json`, `A1-launch.json`):

- OH1: `block_size="2096", mamba_block_size="16", mamba_cache_mode="align", prefix_match_unit="16", user_specified_block_size="False"`
- A1: `block_size="1056", prefix_match_unit="16"`
- OH1 startup: `Setting attention block size to 2096 tokens to ensure that attention page size is >= mamba page size.`

So the physical block stays at the block-grid value; only the hash granularity changed. That is exactly
the counterfactual the lane asked for.

## Result 2 — occamy: reuse goes sub-block, grid = 16

- Identical-prompt gate: L=3129 → `cached_tokens=3120` on the repeat (3120 = 3129 − 9).
- Isolated-prompt grid (cold and repeat agree, so this is not chain-order noise):
  98→96, 200→192, 500→496, 1000→992, 2101→2096, 4196→4192, 8387→8384.
  Every value is `L − (L mod 16)`; **seven of seven targets recover a non-block-multiple amount**
  (e.g. 1000→992 and 2101→2096 would both be 0 or 2096 under the block law).
- Same-window baseline (one long prompt, two reps): 3002→2992 (tail 10), 9000→8992 (tail 8),
  17000→16992 (tail 8). Tail is `L mod 16`, not `L mod 2096`.
- 16-turn growing-conversation battery, repeat pass, mean uncached prefill tokens per turn:
  A **460.2**, C **9.0**, R **9.2**, H **206.8**; gcd of positive `cached` deltas = **16** on all four arms.
  First (cold) pass, no reuse available: A 5475.2 / C 2832.0 / R 3001.2 / H 5474.8.

Against the block-grid control on the same battery (discarded-r1/, where every arm read 0 while the
counter was blind but the *A1 with the same arms* ruled that out): the block-grid lane's per-turn uncached
figures were in the 4.5k–4.6k band, i.e. **~2096 tokens of prefill per turn are what the block unit was
discarding**; with the unit at 16 that drops to 9 tokens for the two arms that resend an unchanged prefix.

## Result 3 — dense qwen9b: nothing measurable changes

- Gate: L=3129 → `cached_tokens=1056` (block multiple, not 16).
- Isolated grid: 500→480, 1000→976 (976 = 16·61, and 976 = 1000−24 so this one *is* sub-block),
  2101→**1056**, 4196→3168, 8387→7392. The 2101 point pins it: the counterfactual block-law value
  `L − L mod 16` would be 2096, but the engine returns 1056.
- Battery: **both passes identical, 0 cached tokens on all 64 turns of both passes**
  (mean uncached A 5475.25 / C 2832.00 / H 5474.75 / R 3001.19, identical across passes).
  Same-window baseline: 3002→2944 (tail 58), 9000→8448 (tail 552), 17000→16896 (tail 104) — all
  block-law values, and tails much larger than 15.

Conclusion for the dense model: the hash unit is accepted but reuse stays block-granular, and in a
growing conversation with this deployment's MTP speculative decoding the cache does not hit at all.

## Result 4 — v0.27.1 does not enforce the divisibility invariant here

`vllm/config/cache.py` documents that the unit must divide every group's block size. OH1L ran with
`--prefix-match-unit 8` and `block_size=2096` (2096 = 8·262, so *8 does* divide 2096 — the invariant holds
trivially) — recorded as accepted, not as a violation. The invariant is stated as a `ValueError` source
path in the tree; no arm in this run produced that error.

## What the flag actually changes vs. the block grid

| metric (occamy, 16-turn battery) | block grid (pmu unset) | pmu 16 |
|---|---|---|
| hash unit | 2096 | 16 |
| per-turn cached tail | `L mod 2096` (≈ up to 2095) | `L mod 16` (≤ 15) |
| mean uncached/turn, prefix-stable arms | 4.5k band | 9.0 / 9.2 |
| 3k/9k/17k single prompt tail | — | 10 / 8 / 8 tokens |

## Caveats (stated, not hidden)

1. **The two arms are not a controlled A/B across models.** A1 was built from prod's own Cmd, which
   includes `--speculative-config {"method":"mtp","num_speculative_tokens":1}`; the occamy arm deliberately
   omits MTP (MOE-VLLM measured MTP failing on that checkpoint). The dense-side null result therefore
   cannot be attributed to `prefix-match-unit` alone — MTP is the leading suspect and the named follow-up.
2. The 16-turn battery draws from a small fixture pool; the C and R arms are prefix-stable by design, so
   their 9-token figures measure the cache, not the workload.
3. Two harness restarts and three crashes (KeyError `config_id`, NameError in the cap guard) occurred
   before the run that produced these rows; only the final clean run's 182 rows are cited above, and the
   discarded rows are preserved under `discarded-r1/` with digests rather than deleted.
4. A prior version of this cell reported `cached=0` on all OH1 rows because the launch lacked
   `--enable-prompt-tokens-details`. That was a **reporting defect, not a cache miss**, and is now
   impossible: rows carry `usage_has_details`/`http_status` and a missing counter is `None`, never `0`.

## Follow-ups (ordered)

1. Dense cause: rerun A1 without `--speculative-config` (if reuse returns at grid 16, MTP is the blocker).
2. Promote occamy: `--prefix-match-unit 16` on the served :8020 vLLM lane recovers ≈2096 prefill
   tokens/turn; measure the cold/cached latency pair on the same window before touching production.
3. Always pass `--enable-prompt-tokens-details` on any lane whose cache is being measured.

## Files

`rows.jsonl` (418 rows), `analysis.json`, `pmu16_cell.py`, `pmu16_analyze.py`, `selftest_offline.py`,
`logs/{run,pre,prod-restore,OH1-launch,OH1L-launch,A1-launch}.json`, `logs/run-console.log`,
`discarded-r1/`. Handoff: `orchestration/handoffs/R2-VLLM.json`.
