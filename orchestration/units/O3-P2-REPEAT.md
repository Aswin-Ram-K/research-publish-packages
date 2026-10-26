# O3-P2-REPEAT — replicate O3's P2 padding win on a fresh salt

**Status:** done · **Bound:** 40 calls / 500 requests, used 39 / 291 · **Grid:** observed 16 (declared 48)
**Salt:** `o3-repeat-20261024T11:05Z-a1` (a RUN-SALT line in the scaffold; every byte fresh)

## Objective
`R2-PROMPT-O23` reported O3 (occamy-1.0 x vLLM) P2 = -664.48 uncached/turn (-51.5%) from one n=71 run and called
it "the largest effect in the matrix". Replicate P0/P1/P2 on a fresh salt, explain the 1.0 quality mismatch,
prove the restore.

## What was measured
- Endpoint :8018 (container `r2o3`, the OH1 argv): block size resolved to **2112** ("Setting attention block
  size to 2112 tokens to ensure that attention page size is >= mamba page size"), prefix_match_unit 16,
  mamba_cache_mode align, enable_prompt_tokens_details true, no speculative config, GPU KV 1,648,826 tokens.
- 213 rows (P0/P1/P2 x 71), 0 non-200, 0 null cached_tokens, 291 live requests.

| arm | unc/turn | t-CI | hit | pad total |
|---|---|---|---|---|
| P0 | 1293.521127 | [1141.40, 1445.64] | 0.895143 | 0 |
| P1 | 1371.253521 | [1234.44, 1508.07] | 0.403843 | 0 |
| P2 | 389.408451 | [244.07, 534.75] | 0.832461 | 1713 (24.1/turn) |

P2/P0 = **-904.11** t-CI [-1101.70, -706.53], boot [-1087.86, -708.45] = **-69.9%** (ratio 0.301) — the -51.5%
replicates and grows numerically.

## Why it is not a padding win
The pad-alignment correction re-sends the same turn with a longer pad; the row keeps only the second send, whose
`cached_tokens` is the **first send's prompt**. Evidence, not inference:
- 68/71 repeat rows (70/71 in the original run — its handoff claimed "0 corrections") are corrected sends.
- Direct: attempt A1 prompt 4153, cached 4096 -> A2 prompt 4157, cached 4144 == A1.prompt rounded to 16.
- Prefix semantics control: prompt 4264 -> cached 4128; the same-length prompt with one sha8 changed mid-prompt
  -> cached 2112. So the near-full P2 hits are real prefix hits — of the same turn's first attempt, whose prefill
  no row records.
- True P2 cost ~= prompt_P2 - cached_P1 ~= 1395.38/turn vs P1's 1371.25: the padding saves nothing.
- Only 3 rows are genuinely first-attempt (t25 1760/0, t30 2016/1984, t67 3920/3888 vs P1 1733/0, 1994/0,
  3902/2112): an alignment effect is possible, n=3 is not evidence.

## Quality mismatch 1.0: answered, not a defect
P0 form (whole ~24 k history) answers by **quoting the span**; P1 form (pointer index) answers with the **span
length and sha8** — and P1's hashes are the verified ones (t003 `471d8e55`, t006 `35ea24b7` = sha256(delta_block)[:8]).
Both forms are correct; they expose different evidence. O1 also scored 1.0, so 1.0 is not O3-specific.

## Restore
`docker rm -f r2o3`; :8012 200 `occamy-1.0` max_model_len 131072 (sglang); :8014 200 `qwen3.5-9b` 32768;
`gx10-occamy-nvfp4` Up, never stopped/restarted/reconfigured; 59,687 MB available.

## Consequence for the merge card
No sentence may claim "grid-aligned padding halves cost" for O3. The matrix's O3 P2/P0 and the harness's
correction accounting need fixing before P2 numbers count as cost measurements (and O1/O2/O4 P2 were not tested
for the same artifact).
