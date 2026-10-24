# POLL-VLLM — collect the detached occamy vLLM battery, analyse it, prove the restore

- Shape: collect-and-analyse; bound 15 tool calls. Live on the GX10; writes only to the paths below.
- Collected: `/home/zer0null/r2/OH1/{rows.jsonl,startup.txt,status}`, `/home/zer0null/r2/run.out.log`.
- Status: `STARTED 2026-10-24T03:35:22Z`; `HEALTH=200 attempt=49`; `DONE rc=0 2026-10-24T03:41:48Z`.
- Rows: **284** (4 arms x 71 turns), sha256 `895cf6d1847c0a7ba970e1c14dce862151ae732902fb17b2e98d438b57d883ec`; **0** null `cached_tokens`; **0** non-200; 120 observed zeros.
- `ARMS_IDENTICAL`: **0** occurrences in both logs.
- Startup: block_size 64; prefix_match_unit 16; mamba_cache_mode align; kv-cache fp8; gpu_memory_utilization 0.34; max_model_len 32768; KV cache 13.93 GiB / 1,029,213 tokens.

Per arm (hit = sum cached / sum prompt; CI = 10,000 turn resamples, seed 20251023):

| arm | hit | 95% CI | mean unc/turn | 95% CI |
|---|---|---|---|---|
| R | 0.887475 | [0.867459, 0.903734] | 1384.9577 | [1235.2535, 1532.1690] |
| A | 0.405844 | [0.329005, 0.474841] | 1350.0141 | [1218.7465, 1480.4648] |
| C | 0.493816 | [0.421381, 0.556251] | 1158.6761 | [1030.2113, 1286.7746] |
| H | 0.360813 | [0.282298, 0.431194] | 1528.1972 | [1359.6620, 1699.6197] |

Pooled across all 284 rows: hit **0.718493** [0.674601, 0.754672], mean unc **1355.4613** [1280.6268, 1430.5528]. Round 1 (occamy-on-vLLM) was **0.901212 / 1682.7218**; pooled delta hit **-0.182719**, unc **-327.26** (descriptive: Round 1's four arms were salt-separated replicates of one policy, this cell's four are different policies).

Grid law: **164/164** nonzero cached values are multiples of **16**, **0/164** are multiples of **2096**, gcd 48, 105/164 are 16 mod 2096. The 2096 grid is gone; `--prefix-match-unit 16` changed the granularity.

Restore: `r2oh1` stopped and removed, :8020 free; `gx10-qwen9b` restarted (running|2026-10-24T03:44:19.988344512Z|0), :8014 model qwen3.5-9b (max_model_len 32768) health 200; production :8012 health 200, `occamy-1.0`, max_model_len 131072; `gx10-occamy-nvfp4` StartedAt `2026-10-23T07:58:48.659913191Z|running` identical before/after.

Assumptions: Round-1 comparison is descriptive (arm designs differ); no Round-1 CI in the cited record; qwen9b binds 192.168.2.168 only; restore = qwen9b restart + prod untouched proof.
