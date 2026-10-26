# CLAIMS.md — the context-cache findings package

**Purpose.** Enforce that no number in `MANUSCRIPT.md` was invented. Every row below names
one claim as it appears in the manuscript, its values, the raw row file it comes from, and a
single command that recomputes it from those rows. A reviewer who runs the command gets the
value printed side by side with the paper's value, and `PASS` or `FAIL`.

```bash
cd "/home/zer0null/reserach extarctor"

::  every claim in this file, one summary line at the end
.venv/bin/python papers/context-cache/recompute.py all

::  any single claim
.venv/bin/python papers/context-cache/recompute.py C17

::  the two claims that are recomputed by the independent verifier's own scripts
.venv/bin/python experiments/context-cache/cells/CX-V2/u5_recon.py   # C01
.venv/bin/python experiments/context-cache/cells/CX-V2/u4_recon.py   # C16
```

`recompute.py` reads only the row files named below (plus `cells/U4/u4_cell.py` for one
static check) and never contacts the endpoint. Tolerances are per-row (`1e-3` relative for
ratios, exact integers otherwise) and are embedded next to the expected values; a mismatch is
reported, never silently rounded. `python3` (bare) is not used: it cannot import
`resextract`, which the runner-side scripts need.

### Source rows and digests

These are the files every value in this document is derived
from. Sizes are bytes, counts are the file's own row count, digests are sha256 of the file.

| Abbrev | Path | Bytes | Rows | sha256 |
|---|---|---:|---:|---|
| U2-rows | `experiments/context-cache/cells/U2/u2_cache_rows.jsonl` | 34,336 | 88 | `ff31f7db0a73ad291ec20f1afcc99efbb3278df2958d07c40062fac3dac6c2f5` |
| U4-rows | `experiments/context-cache/cells/U4/u4_rows.jsonl` | 193,121 | 438 | `56e8176882eb586c76586e2155a23eae7f7a411ef31d7b0d0ab52038bb5e0c9b` |
| U4b-rows | `experiments/context-cache/cells/U4b/rows.jsonl` | 4,600 | 24 | `c16d1783e42510120fb155ede9c87a6e2fbe6f8e5252bee975ccce90509e3246` |
| U5-rows | `experiments/context-cache/cells/U5/u5_raw.jsonl` | 830,365 | 760 | `e0fe2a29da00f667e23f53d522404c0c61500db40d16c82d70883056db1ce7a6` |
| U9-rows | `experiments/context-cache/cells/U9/u9_trials.jsonl` | 50,417 | 139 | `863df39ec2c8c9236ab413dc5365fbd763ff5d37671e5ade1236b653f580663f` |
| U15-rows | `experiments/context-cache/cells/U15/rows.jsonl` | 130,144 | 160 | `7d93f7950ed0eb98a1b429e10eeb00b4646b1ace7355b12b773f0ba13517d8f8` |
| G1-rows | `experiments/context-cache/cells/G1/rows.jsonl` | 269,543 | 264 | `9242ad383281b360ec3c4be92bc59e7de7d5cd751eb7e15c0944f2261497ae66` |
| G3-rows | `experiments/context-cache/cells/G3/rows.jsonl` | 721,318 | 888 | `d6313f72c2eca0bc2192922bfcf1bad08c853c9dd11fbd67b0e65f85428759ee` |
| WIN-SGL-rows | `experiments/context-cache/cells/WIN-SGL/rows.jsonl` | 1,740,191 | 1,800 | `ea5728760540352a752bca501fe77aaae054ec0a88deba4db9bdf8a9f3c5e6c7` |
| WIN-VLLM-rows | `experiments/context-cache/cells/WIN-VLLM/rows.jsonl` | 579,172 | 692 | `a606ca06a23145a52d2bb50f82baff1b6e8d0689164c80ce987c441ce83cf1d7` |
| TUNED-rows | `experiments/context-cache/cells/TUNED/rows.jsonl` | 260,531 | 289 | `be59b3bf8d5572cca38a5c74f5b8348152ec6b8a29b4b270fc4374baa62905cc` |
| G3V2-rows | `experiments/context-cache/cells/G3-LIMIT-V2/rows.jsonl` | 2,553,510 | 2,780 | `589662cef35cbdf6c54b3f75ff11dff9a86e618fc8c77fa3dbcc0d5a2d573382` |
| MOE-VLLM-rows | `experiments/context-cache/cells/MOE-VLLM/rows.jsonl` | 283,033 | 306 | `6658227689a35eeedbe3e2645a9093fb099771ca5b6793bb9bb17582758a07a1` |
| DENSE-SGL-rows | `experiments/context-cache/cells/DENSE-SGL/rows.jsonl` | 712,756 | 894 | `7a0beb4e7d67d0df97f7b4b5b7c0e9388dea94d0a74aa39a3c1a5d1ea07ef80d` |
| G5-rows | `experiments/context-cache/cells/G5/rows.jsonl` | 108,237 | 192 | `8fd7f9d2534b88d682a44709120ae98dd8f46b9b9678c9a8cae4bf42734faa05` |
| M4-rows | `experiments/context-cache/cells/M4/rows.jsonl` | 330,529 | 327 | `08be0204fc2e27d00f6574b597e66f709005e33605497b81d28ded9f64050be5` |
| REPAD-rows | `experiments/context-cache/cells/P2-REPAD/rows.jsonl` | 165,417 | 213 | `1e55300788daf62c01376486beee5f1174b2dc8c8c53b60d0b8900a8131a5f44` |
| U4-events | `experiments/context-cache/cells/U4/u4_events.jsonl` | 45,243 | 54 | `a82532f7344ab346eb5cd109ac1121c4c18578ddf6c98c55bf27ad72f559b02d` |
| U10-p1 | `experiments/context-cache/cells/U10/u10_rows.jsonl` | 27,896 | 65 | `9ca7e4e37a2114f7ef212677fa0c8d6e982618b21622340bc91bda8d9c798cc5` |
| U10-p23 | `experiments/context-cache/cells/U10/u10_rows_p23.jsonl` | 22,589 | 55 | `da0b90ee4aee76bbb2bdbd295056cd30650a23347e631cf66e3b5b0be37b79e6` |
| U13 | `experiments/context-cache/cells/U13/u13_fork_marker.json` | 7,703 | 116 | `0de4a3afec1eeb3fa7e26fadccc1c6b55f4d4c857bf134471b53baf051976879` |
| U14 | `experiments/context-cache/cells/U14/u14_append_note.json` | 7,133 | 135 | `2a8329cfff09b92f511a2a3d12a8f079501366d77b7eb27e6ef26143b3c1fdd9` |
| G3V2-events | `experiments/context-cache/cells/G3-LIMIT-V2/events.jsonl` | 121,367 | 18 | `76c50cb9bd1a8430ec756db2393558559c6b013c348c9d9ab08b4b1af1c91b6b` |
| M4-analysis | `experiments/context-cache/cells/M4/analysis.json` | 37,556 | — | `21e761dbfffef025fe133b32ea56fd885df62e3e51f29c738998f524a63d813f` |
| G1-analysis | `experiments/context-cache/cells/G1/analysis.json` | 156,766 | — | `16b3d51bacd8bb6532e7ca73b412810f9aed214bb30dff0e9d5fe675fb8f4934` |
| E1-corpus | `experiments/context-cache/corpora/endtoend.json` | 240,410 | — | `f853d3ea1ecda7e6fd11e6b732e55493725041acb8bc741abf539aeadcf79ff2` |
| C1-corpus | `experiments/context-cache/corpora/compaction.json` | 351,975 | — | `d702f8f4af2f9d34f68fbca3aa2a096fc8b9cb5f7f7fb32f282c869cbd1f2961` |
| V1-corpus | `experiments/context-cache/corpora/volatility.json` | 388,652 | — | `6e2fe8979f67e1fe762c3daaa0ff53c30bd59c0d607b796d503e7d710e2bc7db` |
| R2P-O1 | `experiments/context-cache/cells/R2-PROMPT/O1/rows.jsonl` | 164,659 | 284 | `8d71a88f22310d59f6e63a1d43a0d6ed009c3dfe48de14d50f7a3d942c71db55` |
| R2P-O2 | `experiments/context-cache/cells/R2-PROMPT/O2/rows.jsonl` | 189,933 | 284 | `1b8268d5b70f237cd68531033f1be716f92841b108a053ac333300411879197a` |
| R2P-O3 | `experiments/context-cache/cells/R2-PROMPT/O3/rows.jsonl` | 189,257 | 284 | `a6fabb637dbf20135641d5f69c75ac0bc44543ec4b3babe05ea77e918e92cbef` |
| R2P-O4 | `experiments/context-cache/cells/R2-PROMPT/O4/rows.jsonl` | 189,373 | 284 | `23547e3a9611d0b5591f1b55726e854a607e9360fb123527b2b6c38ad25d4aab` |
| TRACK-t256-rows | `experiments/context-cache/cells/TRACK-INTERVAL/t256/rows.jsonl` | 238,796 | 355 | `d846a9ec550e84fda6b2e86ce93467e34ea07fdb39637c0d052fea170e5f03f1` |
| TRACK-t128 | `experiments/context-cache/cells/TRACK-INTERVAL/t128/rows.jsonl` | 238,793 | 355 | `acca510cbd1568ae0d4400e0a9f1a20bf35229a2b27dd330e9de609204849c59` |
| TRACK-t64 | `experiments/context-cache/cells/TRACK-INTERVAL/t64/rows.jsonl` | 238,437 | 355 | `055c54525afc762679e123fca98891a6fe4d55488b331b116481647dfe7681e6` |
| SYSOPT-moe | `experiments/context-cache/cells/SYS-OPT/rows-moe.jsonl` | 164,856 | 213 | `5727d2a6dedb538bd5707a17537d3e49de1ead8e91e4bbe9653dae9b3cc399bb` |
| SYSOPT-dense | `experiments/context-cache/cells/SYS-OPT/rows-dense.jsonl` | 164,946 | 213 | `8e61190888d56b9ec6dcf235172d253f6bd45caecb7726726a927087efe55b3f` |

## A. Rendering

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C01 | POINTER and NAIVE_APPEND render byte-identically (§2) | 760/760 cells, 0 bytes differing, 0 differing cells listed | U5-rows, rebuilt | `.venv/bin/python experiments/context-cache/cells/CX-V2/u5_recon.py` |
| C02 | U5 ran cleanly and covers 190 cases in 4 conditions (§4) | 760 rows, 0 non-200, 0 errors, 190 cases, 4 (depth, condition) pairs | U5-rows | `.venv/bin/python papers/context-cache/recompute.py C02` |
| C03 | deep summarise and deep fork prompts are identical; the 760 rows carry 570 distinct prompts (§2, §5) | 190/190 equal; distinct digests 570 of 760 rows | U5-rows | `.venv/bin/python papers/context-cache/recompute.py C03` |
| C13 | U4's driver used one renderer for every arm and never imported the pointer fork (§5) | `RENDER = naive_append`; `POINTER_FORK` absent from source | `cells/U4/u4_cell.py` (static) | `.venv/bin/python papers/context-cache/recompute.py C13` |

## B. Fan-out placement

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C04 | U4b arm totals and per-branch cached tokens (§3) | prompt 15,400 each; uncached A 4,648 / B 15,400 / C 4,648; per-branch uncached 1,925, 1,925, then 133 x 6 | U4b-rows | `.venv/bin/python papers/context-cache/recompute.py C04` |
| C05 | Branching late reproduces the win with no pointer machinery (§3, §1 abstract) | B/A = 3.3133 (**superseded** as an effect size by G5's race-free 6.744, C53; kept as this cell's measured value); C/A = 1.0000; 24 requests | U4b-rows | `.venv/bin/python papers/context-cache/recompute.py C05` |
| C06 | The 3.3133 measured here is **not** a floor: with all seven warm branches this cell's counterfactual is 5.3922, above it, and a race-free reference sits above that (the floor/upper-bound reading is retracted — §3) | A would be 2,856 uncached; B/A = 5.3922, above the measured 3.3133 and below G5's race-free 6.744, so a **lower** reference rather than an upper bound (the card's 3.99 does not reproduce — see Coverage) | U4b-rows, G5-rows | `.venv/bin/python papers/context-cache/recompute.py C06` |

## C. Compaction and content loss

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C07 | MCQ accuracy barely moves across conditions (§4) | shallow 126/190 (66.3 %); baseline 137/190 (72.1 %); summarise 134/190 (70.5 %); fork 132/190 (69.5 %) | U5-rows | `.venv/bin/python papers/context-cache/recompute.py C07` |
| C08 | No accuracy difference is significant and none reaches 5 points (§4) | max delta 2.632 pts; McNemar summarise-vs-baseline 11/8 p = 0.647606; fork-vs-baseline 13/8 p = 0.383310; summarise-vs-fork 7/5 p = 0.774414 | U5-rows | `.venv/bin/python papers/context-cache/recompute.py C08` |
| C09 | A gold line planted mid-history is retained by baseline cells and by neither compacted arm (§4, abstract) | baseline 190/190; shallow 0/190; summarise 0/190; fork 0/190 | U5-rows | `.venv/bin/python papers/context-cache/recompute.py C09` |
| C10 | The 90 % agreement flag fired, and the identical-prompt arms agree only 91.6 % (§4) | baseline-vs-summarise 167/190 = 87.9 %; fork-vs-baseline 165/190 = 86.8 %; summarise-vs-fork 174/190 = 91.6 % | U5-rows | `.venv/bin/python papers/context-cache/recompute.py C10` |

## D. The invalid comparison

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C11 | U4's paired break costs are identical between summarise and fork, and the permutation test is degenerate (§5) | 21 pairs, median 0, 18/21 exactly 0, max abs delta 64, p = 1.0 (50,000 draws) | U4-rows | `.venv/bin/python papers/context-cache/recompute.py C11` |
| C12 | The only three nonzero deltas are one 64-token chunk of salt rounding (§5) | -64 at u4-s1 t17 (6174 vs 6172), +64 at u4-s1 t32 (6145 vs 6143), -64 at u4-s3 t17 (6224 vs 6221) | U4-rows | `.venv/bin/python papers/context-cache/recompute.py C12` |
| C14 | U4's provenance: 438 rows, 54 events on a 5-turn schedule, 3 sessions (§5) | 438 rows; 54 events (21 summarise, 21 fork, 12 sliding); sessions 3; batch 438 + probe 13 = 451 recorded in files; the card's 454 adds 3 smoke sends that appear only in the card | U4-rows, U4-events | `.venv/bin/python papers/context-cache/recompute.py C14` |
| C16 | Under the fixed library the two arms differ from turn 12 onward (§5) | body equal 11/44 turns (turns 1-11); body bytes 2,857 vs 2,857 at turn 1, 19,998 vs 20,173 at turn 12; head digest 44/44 both arms | U4-rows, rebuilt | `.venv/bin/python experiments/context-cache/cells/CX-V2/u4_recon.py` |
| C15 | U13 gives fork a genuinely distinct, content-addressed marker (§5) | fork `b812c99d` vs summarise/legacy `dc591b7e`; +175 chars (7,966 vs 7,791 prompts); marker line 171 chars; about 44 tokens; suffix after the marker equals the bare summary | U13 | `.venv/bin/python papers/context-cache/recompute.py C15` |

## E. The decisive comparison (U15)

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C17 | Arm R, summarise-in-place (§6) | prompt 194,788; cached 143,616; uncached 51,172; hit 0.7373; 40 rows | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C17` |
| C18 | Arm F, fork with marker (§6) | prompt 198,376; cached 151,296; uncached 47,080; hit 0.7627; 40 rows | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C18` |
| C19 | Arm A, append-a-note (§6) | prompt 412,177; cached 382,080; uncached 30,097; hit 0.9270; 40 rows | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C19` |
| C20 | Arm C, no-compaction control (§6) | prompt 403,259; cached 372,736; uncached 30,523; hit 0.9243; 40 rows | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C20` |
| C21 | A beats R by 1.700x on total uncached tokens; R and F are within 8.7 % (§6, abstract) | A/R = 1.7002359 (passes the 1.5x test); R/F = 1.0869159; F/A = 1.5642755; gap 8.69 % | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C21` |
| C22 | Only 7.8 % of R's excess is break cost; 92.2 % is steady state (§6, abstract) | net break 1,620; excess 20,649; share 0.078454; steady 19,029; share 0.921546 | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C22` |
| C23 | Turns 19-34 re-prefill rates (§6) | R 1,659.9375 uncached on a 5,811.9375 prompt; C 754.9375 on 12,838.9375; A 722.9375 on 13,146.9375; F 1,678.9375 on 5,942.9375 | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C23` |
| C24 | The break-only counterfactual would score 1.068x, not 1.700x (§6, abstract) | counterfactual R = 32,143; R/counterfactual-A = 1.0679802 | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C24` |
| C25 | A never shrinks; its window cost is unbounded (§6) | first 1,186; last 19,583; growth 18,397 (16.5118x); total prompt 412,177 vs control 403,259 (+8,918); R last prompt 4,134 | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C25` |
| C26 | Only the rewriting arms break, at turns 18 and 35 (§6) | R breaks [18, 35]; F breaks [18, 35]; A breaks []; C breaks [] | U15-rows | `.venv/bin/python papers/context-cache/recompute.py C26` |

## F. Latency

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C27 | 1,024 tokens: miss 208.7 ms, hit 86.4 ms (§7) | ratio 0.4140; delta 122.1 ms | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C27` |
| C28 | 2,028 tokens (§7) | 349.2 / 87.2; 0.2498; delta 259.8 ms | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C28` |
| C29 | 3,955 tokens (§7) | 674.6 / 105.2; 0.1560; delta 559.8 ms | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C29` |
| C30 | 7,863 tokens (§7) | 1,431.6 / 114.3; 0.0798; delta 1,311.7 ms | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C30` |
| C31 | 15,701 tokens (§7) | 3,039.5 / 139.2; 0.0458; delta 2,892.1 ms | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C31` |
| C32 | 31,415 tokens: 7,541.9 ms falls to 231.6 ms (§7, abstract) | ratio 0.0307; delta 7,251.0 ms | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C32` |
| C33 | The hit/miss ratio falls as L^-0.7837 (§7, abstract) | ratio exponent -0.7837 (r2 0.9962); miss L^1.0520 (r2 0.9934); hit L^0.2683 (r2 0.8631); x = measured pair length | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C33` |
| C34 | OLS length terms differ by 51.67x; a hit still costs about 4.66 us/token (§7, abstract) | miss 0.240736 ms/token; hit 0.004659; ratio 51.67x; 4.66 us/token | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C34` |
| C35 | All 42 paired deltas are positive (§7) | 42/42; 7 reps per length; sign p = 0.0078 one-sided (0.0156 two-sided) | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C35` |
| C36 | U9 resolved six lengths from 139 requests (§7) | 139 rows, 139 requests, 0 non-200, 6 lengths, 1 calibration, 20 prime, 20 noise-hit, 10 noise-cold | U9-rows | `.venv/bin/python papers/context-cache/recompute.py C36` |

## G. The 64-token grid

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C37 | For byte-identical repeats the grid holds exactly (§8) | 44/44 warm repeats satisfy `cached = 64*((L-1)//64)`; 44/44 residual 0; lengths 314-1,550; no L mod 64 == 0; 0/44 cold non-zero | U2-rows | `.venv/bin/python papers/context-cache/recompute.py C37` |
| C38 | For appends it fails on every row (§8, abstract) | 372/372 warm appends deviate; residual 832-7,936, median 1,792; 15 buckets; warm-append prompts 1,802-12,393 | U4-rows | `.venv/bin/python papers/context-cache/recompute.py C38` |
| C39 | U2 and U4 share no rows, so the two law statements are about different data (§8) | 0 shared (case_id, salt) rows; U2 314-1,550; U4 931-12,393 | U2-rows, U4-rows | `.venv/bin/python papers/context-cache/recompute.py C39` |
| C40 | Only lengths that are a multiple of 64 miss on the immediate repeat (§9) | 1,024 and 1,088: 5/5 misses then 5/5 hits; 1,008/1,023/1,025: 0/5; rep2 10/10 at the law; the missed 1,024-token prefill costs 268.4 ms median TTFT | U10-p1 | `.venv/bin/python papers/context-cache/recompute.py C40` |
| C41 | The boundary split is not chance (§9) | 10/10 vs 0/15, Fisher p = 3.0593e-07; wider pool 35/35 vs 0/15, p = 4.4428e-13 | U10-p1, U10-p23 | `.venv/bin/python papers/context-cache/recompute.py C41` |
| C42 | Time and interleaved traffic do not repair the boundary miss (§9) | delay 0.25/0.5/1.0/2.0 s: 20/20 misses; intervening 63-token request: 5/5 misses | U10-p23 | `.venv/bin/python papers/context-cache/recompute.py C42` |
| C43 | The boundary effect is not a warm-up artefact (§9) | cold requests 55/55 with cached 0 | U10-p23 | `.venv/bin/python papers/context-cache/recompute.py C43` |
| C44 | G1 decomposition of U15's 1.700x: per-break cost ratio E/F = 1.038, not within 10 % on 4/6 events; the 1.700x is post-compaction window truncation, not break-event cost (§6, abstract) | n=264 rows (132 per arm E/F); 6 break events; 2/6 within 10 %; mean gross E=1,728.0, F=1,664.0; ratio=1.0384615; u15_1_700x_survives_decomposition=False; rows sha256 9242ad38... | G1-rows, G1-analysis | `.venv/bin/python papers/context-cache/recompute.py C44` |

## Coverage

**63 claims, all re-derived.** `recompute.py all` prints one line per value and
`60 claims checked, all match` at the end, then the graph guard (`GRID GUARD PASS  7/7 configs`)
and the count guard (`COVERAGE GUARD PASS  63 claims documented, 61 runnable here + 2 script-backed`).
The counts are **derived, not typed**: `COVERAGE GUARD` reads the claim ids out of this file and the
runners out of `recompute.py`, and fails the run if a claim row has no runner, a runner has no claim
row, a claim row is duplicated, or a script-backed claim's script is missing from disk. No prose
count in this section or in `PACKAGE.md` is an input to it, so a stale figure here cannot survive
`recompute.py all`.

Where the 63 resolve: 60 are stored-value claims (`FUNCS`, printed as one `OK`/`FAIL` block each),
C61 is the grid guard and prints its own `GRID GUARD` PASS/FAIL rather than a stored value, and C01 and
C16 are not in `recompute.py` at all — they are recomputed by the independent verifier's own scripts
(`cells/CX-V2/u5_recon.py`, `cells/CX-V2/u4_recon.py`, unchanged from the versions CX-V2 pinned), which
is why the run's own line says `60 claims checked` and not 63. 60 + 1 + 2 = 63.

**Every value was recomputed from the raw rows before this document was written**, not copied
from a unit card. Where the rows and a card disagreed, the rows won and the disagreement is
named below.

## Cross-stack cache-hit granularity (X-SYNTH)

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C45 | WIN-SGL rows: 1,800 rows, 900 per config (S1 page_size 64, S2 page_size 128), all status 200, sha256 ea5728760540352a752bca501fe77aaae054ec0a88deba4db9bdf8a9f3c5e6c7 | 1,800 / 900 / 900, 1,800 OK | WIN-SGL-rows | `.venv/bin/python papers/context-cache/recompute.py C45` |
| C46 | WIN-SGL battery: hit fraction and mean uncached per turn per config, plus steady-state grid (gcd, odd64) | S1 hit 0.974202, unc/turn 740.4 (32k 729.2, 64k 746.01), gcd 64, odd64 351; S2 hit 0.973778, unc/turn 752.6 (32k 745.2, 64k 756.28), gcd 128, odd64 0; steady n 880 each | WIN-SGL-rows | `.venv/bin/python papers/context-cache/recompute.py C46` |
| C47 | G3 S0 baseline (page_size 1, production default): battery + steady grid | 888 rows, 888 OK, hit 0.974242, unc/turn 739.2 (32k 725.74, 64k 746.01), steady 880, gcd 64, odd64 351, sha d6313f72c2eca0bc2192922bfcf1bad08c853c9dd11fbd67b0e65f85428759ee | G3-rows | `.venv/bin/python papers/context-cache/recompute.py C47` |
| C48 | WIN-VLLM rows: 692 rows across V1/V2/V3, all status 200, sha256 a606ca06a23145a52d2bb50f82baff1b6e8d0689164c80ce987c441ce83cf1d7 | 692 / 358 / 312 / 22, 692 OK | WIN-VLLM-rows | `.venv/bin/python papers/context-cache/recompute.py C48` |
| C49 | WIN-VLLM grid law: gcd and exact-match count per config | V1 gcd 1088, exact 10/70, 19 distinct L; V2 gcd 1056, exact 10/26, 11 distinct L; V3 gcd 2096, exact 15/20, 5 distinct L | WIN-VLLM-rows | `.venv/bin/python papers/context-cache/recompute.py C49` |
| C50 | WIN-VLLM battery: hit fraction and mean uncached per turn | V1 hit 0.869037, unc/turn 2230.8 (n=284); V2 hit 0.868144, unc/turn 2246.0 (n=284) | WIN-VLLM-rows | `.venv/bin/python papers/context-cache/recompute.py C50` |
| C51 | Cross-stack comparison SGLang S0 (32k) vs vLLM V1 | S0 32k uncached 725.74, hit 0.974242; V1 uncached 2230.8, hit 0.869037; ratio 3.074x | G3-rows, WIN-VLLM-rows | `.venv/bin/python papers/context-cache/recompute.py C51` |
| C52 | TUNED rows: 289 rows (phase P 259 + R 30), status 200, grid gcd 64, 10/30 exact, odd64 3, variant wt-slru, policy slru, sha be59b3bf8d5572cca38a5c74f5b8348152ec6b8a29b4b270fc4374baa62905cc | 289 / 259 / 30, 289 OK, gcd 64, exact 10, odd64 3 | TUNED-rows | `.venv/bin/python papers/context-cache/recompute.py C52` |
| C53 | G5 fan-out (race-free): B/A = 6.744331504 [4.04542649, 9.44323652], C/A = 1.105174403; A 123,240 prompt / 102,912 cached / 20,328 uncached; B 123,256 prompt / 0 cached / 123,256 uncached; C 19,792 uncached; 8 fan-outs x 8 branches; replaces 3.31/5.39 band | G5-rows | `.venv/bin/python papers/context-cache/recompute.py C53` |
| C54 | M4 resident capacity: `resident_capacity_ratio_of_capacity` W in [30,31] documents = [258035,266636] tokens = [0.1592,0.1645] of 1,620,892 declared capacity, at 1.501724x pressure (2,434,133 tokens, 283 docs); binding constraint state cache (max_mamba_cache_size 64), not KV token capacity; verdict consistent_with_lru; token-pool LRU 188.45 excluded | M4-rows, M4-analysis | `.venv/bin/python papers/context-cache/recompute.py C54` |

## Cross-stack grid laws, second pass (X-SYNTH)

New numbers only; every row is one number-or-bundle with the single command that re-derives it.
`C61` is the loud guard: it fails the run if any of the `config_id`s cited above has no rows in
its cell.

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C55 | The grid unit per stack, measured over every hot row of the cell (gcd of `cached_tokens`; "holds" = every hot row is an exact multiple) (§9a) | S0 64 on 880/880; S1 64 on 888/888; S2 128 on 888/888; V1 1088 on 300/300; V2 1056 on 268/268; V3 2096 on 16/16; TUNED 64 on 10/10 | G3, WIN-SGL, WIN-VLLM, TUNED rows | `.venv/bin/python papers/context-cache/recompute.py C55` |
| C56 | vLLM: the unit is identified, not fitted — 1056 is not a divisor of V1's rows and 1088 is not a divisor of V2's (§9a) | V1 hot vs 1056: 0/264, vs 1088: 264/264; V2 hot vs 1088: 0/264, vs 1056: 264/264; V3 hot vs 2096: 16/16, vs 1088: 0/16; step gcd V1 1088, V2 1056; minimum hot cached V1 1088, V2 1056 | WIN-VLLM rows | `.venv/bin/python papers/context-cache/recompute.py C56` |
| C57 | SGLang returns multiples of its unit on every hot row at any page size, and `--page-size 64` does not move the grid away from the production default (§9a) | S0 880/880 gcd 64, 351 odd-unit; S1 880/880 gcd 64, 351 odd-unit; S2 880/880 gcd 128, 478 odd-unit (i.e. cached mod 128 = 64); S1 vs S0 887/888 identical over 888 paired rows | G3, WIN-SGL rows | `.venv/bin/python papers/context-cache/recompute.py C57` |
| C58 | The one condition that moved the grid moves it by exactly one block, with no measurable latency effect (§9a) | 900 paired rows: 534 identical, 353 lower by 64, 13 higher; delta set {-64, 0, 832, 896}; mean uncached S1 740.4 vs S2 752.58; paired TTFT ratio median 1.005 (0.435–45.798) | WIN-SGL rows | `.venv/bin/python papers/context-cache/recompute.py C58` |
| C59 | TUNED delivers grid 64 under `--disable-chunked-prefix-cache` true and SLRU at 1.505083x pressure; its replay hits only the newest band (§9a) | 289 rows (P 259 / R 30), 10 hot rows all multiples of 64, gcd 64, 3 odd-unit; bands newest 10/10, middle 0/10, oldest 0/10; token_capacity 1,480,094; docs_pushed 259; pressure ratio 1.505083 | TUNED rows + `run.json` | `.venv/bin/python papers/context-cache/recompute.py C59` |
| C60 | Cross-engine: the unit differs per stack (5 distinct units across 7 stacks) and the unit does not predict per-turn uncached cost (§9a) | TUNED 8,305.0/turn hit 0.034474; S0 739.25/turn hit 0.974242; TUNED/S0 11.2344; V1/S0 3.0176; V1/TUNED 0.2686 | TUNED, G3, WIN-VLLM rows | `.venv/bin/python papers/context-cache/recompute.py C60` |
| C61 | Guard: no grid claim rests on a `config_id` with no rows in any cell (§9a) | 7/7 configs present (S0 888, S1 900, S2 900, V1 358, V2 312, V3 22, TUNED 289) | all four cells | `.venv/bin/python papers/context-cache/recompute.py grid-guard` |

## The compaction boundary, measured live (G3-FOLD)

Section 6a's numbers. Every value is re-derived from `cells/G3-LIMIT-V2/rows.jsonl` by the one
command in the last column; the intervals are percentile bootstraps over turns (10,000
resamples, seed 20251023) of `mean(compacting arm) - mean(matched baseline)` on the SAME turn,
restricted to turns after the arm's first compaction (`post_*`) or before it (`pre_*`).

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C62 | Compaction at a real 32k/64k boundary costs the compacting arm +134.6 to +747.2 uncached tokens per turn ON AVERAGE after it, and nothing before it — a range of twelve arm means, NOT a per-turn range: per turn the same segment runs -927 to +5,473 and all 12 arms have a turn below baseline (§6a, abstract, §10 rule 5) | 2,780 rows, 18 compactions, 12 arm-instances (6 arms x 2 budgets); first compaction at turn 71 (32k) and 143 (64k); post-boundary arm means 134.6-747.2, 11/12 intervals excluding zero; per-turn post-boundary range -927 to +5,473 (min 64k S turn 146, max 64k S turn 151), 12/12 arms with at least one negative turn, 12/12 arms with a transition turn above baseline; resting-turn means identical for 11/12 arms, 32k F-ptr +134.6 -> +112.5 (CI [-33.7, 264.3] crosses zero); pre-boundary delta -11.8 to +51.0, 0/12 intervals excluding zero; boundary turn 1,826-3,033 uncached over all 18 compaction rows (2,972 is F-ptr's first only) vs the baseline's own window-drop turns 1,236-1,321 across 6 drop rows (the 32k baseline drops twice, 1,236 at turn 71 and 1,320 at turn 141); last-turn prompt B 9,896 / S 13,325 / S-ptr 13,321 / F 13,542 / F-ptr 13,546 / S-k800 11,009 / F-k800 11,717 at 32k and 22,063 / 23,632 / 23,634 / 23,762 / 23,765 / 22,643 / 14,197 at 64k | G3V2-rows, G3V2-events | `.venv/bin/python papers/context-cache/recompute.py C62` |

## The four-cell model x engine matrix (MATRIX-FOLD)

Section 9b's numbers. All four cells measured the same 32k schedule (4 arms x 71 turns, battery
phase); their prompt prefix digests and lengths match (`prefix_sha256` 284/284, `chars` 284/284
on all six cell pairs) because the sibling cells
share one driver, and the chat template moves `prompt_tokens` by at most 4 on 140 of the 284 rows
in the SGLang cells. No compaction fires at 32k, so the four arms are salt-separated replicates
and the turn is the resampling unit: the intervals are percentile bootstraps over the 71 turns
(10,000 resamples, seed 20251023), not over the 284 (arm, turn) rows. The engine main effect is
`vLLM - SGLang` averaged over the two models; the model main effect is `qwen3.5-9b - occamy-1.0`
averaged over the two engines; the interaction is the difference of the two engine effects.

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C63 | The engine, not the model, sets the per-turn uncached bill: on one shared 32k/71-turn schedule (prompt prefix digest and length equal on all six cell pairs) the engine main effect is +549.33 uncached tokens/turn while the model main effect is -400.02, the opposite sign. The model column is near-identical under SGLang (the two SGLang cells sit 3.61 uncached tokens/turn apart) and only separates under vLLM, where the MoE checkpoint pays 803.65 MORE than the dense one. That inversion is the interaction: -403.63 [-479.7, -328.5], significant, and in magnitude almost the whole of the engine effect. The engine is worth 2.3058x on the MoE checkpoint against 1.1987x on the dense one, so the model column costs (or saves) money only under the engine that exposes its block geometry (§9b, abstract). | 1,136 rows = 4 cells x 284 (4 arms x 71 turns). Cells (model/engine, hit, uncached/turn, hot gcd, rows): occamy-1.0/vllm 0.901212, 1,682.7218, 2,096, 284; occamy-1.0/sglang 0.957153, 729.7641, 64, 284; qwen3.5-9b/vllm 0.817432, 879.0669, 1,088, 284; qwen3.5-9b/sglang 0.956941, 733.3697, 64, 284. **Engine main effect 549.33 [462.4, 631.9]**, 66/71 turns positive; **model main effect -400.02 [-474.2, -326.5]**, 8/71; **interaction -403.63 [-479.7, -328.5]**, 8/71. Engine within model: MoE 952.96 [805.7, 1,099.8] (67/71), dense 145.70 [81.2, 210.5] (48/71). Model within engine: vLLM -803.65 [-953.6, -655.2] (8/71), SGLang 3.61 [0.0, 10.8] (1/71). Ratios: **engine 2.3058x MoE / 1.1987x dense**, engine 1.7523x mean; model 0.5224x vLLM / 1.0049x SGLang, mean 0.7636x; engine/model -1.3733x. Engine = 0.5459 of the 1,006.2306 grand mean, model = -0.3975; the model effect is -222.8887x larger under vLLM than under SGLang (divided from the unrounded per-turn means, 4 dp; dividing the rounded operands is an arithmetic artefact, NOT this figure). Replicate-arm check: engine 395.7-657.9 and model -546.4 to -296.8 across R/A/C/H. History: the 2026-10-24 MTP correction on the vLLM dense cell is relocated to **Superseded (C63)** below. | MOE-VLLM-rows, G3-rows, R2P-O4 (state/config/rows.jsonl, stack=vllm-0.27.1, config_id=O4), DENSE-SGL-rows | `.venv/bin/python papers/context-cache/recompute_r2.py C63` (independent re-derivation; `.venv/bin/python papers/context-cache/recompute.py C63` remains the original) |

### Superseded (C63)

The line below is the historical correction block that C63's Value cell used to carry inline.
Nothing in it is deleted: it is relocated here, and every superseded value it names stays
readable. The date is the batch date, **2026-10-24** — the block was first published as
`MTP CORRECTION (2024-10-24)`, a year typo corrected by C63-CELL (see `orchestration/STATUS.md` §10
and the `PAPER-FINAL-V2C`/`PAPER-FINAL-V2D` handoffs).

**Superseded — MTP CORRECTION (2026-10-24): the Round-1 vLLM dense cell ran with `--speculative-config mtp`; removing it re-measured that cell 2,230.7782 -> 879.0669 uncached tokens/turn (a 2.54x drop, CI [824.78, 933.35]). Every value this claim carried before that correction is SUPERSEDED and replaced here: engine effect 1,225.18 [1,132.2, 1,313.3] -> 549.33 [462.4, 631.9]; model effect +275.83 [194.3, 357.6] -> -400.02 [-474.2, -326.5]; interaction +272.23 [190.1, 354.6] -> -403.63 [-479.7, -328.5]; model within vLLM +548.06 -> -803.65; engine within dense +1,497.41 -> 145.70; ratios 2.6738x/3.0418x/1.3257x/1.1653x -> 1.7523x/1.1987x/0.5224x/0.7636x; engine/model 4.4418 -> -1.3733; engine share 0.9115 -> 0.5459. The superseded block is kept in `recompute.py` (`C63_SUPERSEDED`) and in `RUN.json` marked superseded. WHAT SURVIVES: the engine still dominates what remains of the model axis (engine within MoE is unchanged at 952.96 by construction, and the engine still costs 2.3058x on the MoE), but the model effect is no longer a small positive quantity — it is negative under vLLM and near zero under SGLang. MTP was a decoder-speed feature that also changed prompt-cache behaviour; that is a finding about the coupling of decoding and caching, not a correction of the workload.


## Round 2 — padding, the 2x2 re-check, the grid sweep, the prompt round (ROUND2-FOLD)

Sections 8a and 9c of the manuscript. Every value below is re-derived by
`papers/context-cache/recompute_r2.py` from the raw `rows*.jsonl` files named in the source
table above; nothing is read from a unit handoff, a cell's `analysis.json`, or a rendered
document. Round 2 changed what can be claimed and it also **withdrew** something: the padding
result it first reported was a measurement artefact, and the correction is the first claim
below.

```bash
::  the five Round-2 claims, one PASS/FAIL block each
.venv/bin/python papers/context-cache/recompute_r2.py all

::  the source-falsification guard: every claim must MOVE when its rows are broken
.venv/bin/python papers/context-cache/recompute_r2.py redgreen

::  what the Round-2 cells say about themselves, in evidence form (not manuscript numbers)
.venv/bin/python papers/context-cache/recompute_r2.py EVIDENCE
```

| # | Claim in the manuscript | Value | Source | One recompute command |
|---|---|---|---|---|
| C64 | Grid-aligned padding **costs** on a one-send-per-turn cell: +20.8429 uncached tokens/turn over the plain pointer layout, and the alignment it buys recovers about four fifths of what it pays (§8a)   **Correction (C64a).** **Supersedes** the padding win this paper first reported: the original P2 arm's −51.5 % (O3) and −14.0 % (O2) were same-turn self-hits, because the arm resent a turn until the pad aligned and recorded only the second send's cache state — a cost figure, not a saving | P0 541.0704 [501.676, 581.507] hit 0.956139; P1 528.6429 [521.186, 536.129] hit 0.772737; P2 549.4857 [542.171, 556.800] hit 0.773036; **P2-P1 +20.8429 [10.014, 31.586]**, 70 pairs, excludes 0 (ratio of means 1.039427); P2-P0 +6.5000 [-34.971, 46.914] null; P1-P0 -14.3429 [-57.186, 27.114] null; pad on the 70 countable P2 rows: range 64-127 tokens, mean 94.90, total 6,643; 70/70 of those P2 rows aligned on 64; extra cache vs the same turn's P1 row 0x9 / +64x41 / +128x20, mean 74.0571 = **78.0 % of the pad recovered, 22.0 % paid**; 213 rows, 0 multi-send, 0 corrected, 2 rows carry `cached_tokens: "unavailable"` (turn 1 of P1 and of P2) and are excluded and counted. The full pad over all 71 P2 turns is 6,737 / 94.89 (the cell's own `RESULTS.md`, counting a turn no cache counter exists for); 6,643 / 94.90 is the same quantity over the rows a token figure may be read from | REPAD-rows | `.venv/bin/python papers/context-cache/recompute_r2.py C64` |<!-- tier: pinned -->
| C65 | The engine/model 2x2 **survives** every Round-2 re-check, and it is the engine that sets the per-turn bill: the engine main effect is 549.33 uncached tokens/turn against a model main effect of −400.02, on 1,136 rows re-derived without `recompute.py` (§9c) | cells (hit, unc/turn, rows): occamy-1.0/vLLM 0.901212, 1,682.7218; occamy-1.0/SGLang 0.957153, 729.7641; qwen3.5-9b/vLLM 0.817432, 879.0669; qwen3.5-9b/SGLang 0.956941, 733.3697 — 284 rows each. Engine 549.3275 [463.1, 631.8], 66/71 turns positive; model −400.0246 [−472.9, −324.3], 8/71; interaction −403.6303 [−478.4, −327.3], 8/71. Engine within MoE 952.9577 [802.9, 1,094.9] (67/71), within dense 145.6972 [79.3, 211.6] (48/71); model within vLLM −803.6549 [−950.6, −651.5] (8/71), within SGLang 3.6056 [0.0, 10.8] (1/71). Grand mean 1,006.2306; engine 0.5459 of it, model −0.3975. Engine/model −1.3732; the model effect is −222.8887x larger under vLLM. Per-arm replication (R/A/C/H): engine 560.0/583.7/395.7/657.9, model −384.8/−372.0/−546.4/−296.8 | MOE-VLLM-rows, G3-rows, R2P-O4, DENSE-SGL-rows | `.venv/bin/python papers/context-cache/recompute_r2.py C65` |<!-- tier: pinned -->
| C66 | `mamba_track_interval` is **not** a grid lever: 256, 128 and 64 all deliver the same 64-token cache grid with 0 off-grid hot rows, and no arm moves outside one 64-token page (§9c) | 355 rows per interval, 0 non-200; hot cached-token gcd 64 at all three. Arms (256 / 128 / 64) unc/turn: R 600.27/600.27/600.27, A 529.30/527.49/524.79, C 547.08/547.08/547.08, H 961.97/961.97/960.17, C0 709.86/709.86/709.86. Paired over turns vs 256: R 0.0 [0.0, 0.0], C 0.0, C0 0.0 at both 128 and 64; A −1.803 [−5.41, 1.80] at 128 and −4.507 [−12.62, 2.70] at 64; H −1.803 at 64. No interval's CI excludes zero on any arm | TRACK-t256-rows, TRACK-t128, TRACK-t64 | `.venv/bin/python papers/context-cache/recompute_r2.py C66` |<!-- tier: pinned -->
| C67 | The prompt-layout round, after P2 was withdrawn: the pointer index is **null** against full history on both production setups, **costs** on the vLLM dense setup, and the edit control is null on three of four setups and **costs** on the fourth (§9d)   **Correction (C67a).** **Supersedes** one reading in C67: the edit control (P3) is null on three setups and **costs** on the fourth — O4 P3 - P1 = +23.5211 [8.39, 53.48], which excludes zero. Writing a mid-run edit into a cached prefix is not free anywhere it was measurable, and the "null on all four" framing is withdrawn | 284 rows and 4 arms per setup, 0 non-200. P1−P0: O1 −7.6761 (null), O2 −7.6761 (null), O3 +55.6479 [−136.49, 246.01] (null), **O4 −219.5070 [−353.83, −88.85] (P1 cheaper)**. P3−P1: O1 −2.1690 (null), O2 −3.0704 (null), O3 −140.3099 [−289.10, 8.21] (null), O4 +23.5211 [8.39, 53.48] (**P3 costs**). Arm means: O1 530.3944/522.7183/541.7465/520.5493; O2 530.3944/522.7183/456.1127/519.6479; O3 1290.0563/1345.7042/625.5775/1205.3944; O4 1883.8592/1664.3521/2271.0986/1687.8732 (P0/P1/P2/P3). No cell's stored `analysis.json` disagrees with its own rows | R2P-O1, R2P-O2, R2P-O3, R2P-O4 | `.venv/bin/python papers/context-cache/recompute_r2.py C67` |<!-- tier: pinned -->
| C68 | The four Round-2 batteries are four distinct configurations, not one measurement filed four times: every pair carries a distinct `config_sha256`, model, setup, stack and wall time, and no pair is caught by the prompt-identity + configuration-difference test (§9c) | config_sha256 O1 `f2efaaac…`, O2 `652ff99d…`, O3 `f8ab1dce…`, O4 `163a5db6…`; each cell 284 distinct prompt digests and 0 rows repeating its own P0 digest across P1/P2/P3; 6 of 6 cell pairs have all of config_id/config_sha256/model or setup/stack/wall_ms differing row for row; pairs counted twice: **0**; cells distinct: 4. Same-turn cache counters differ on 62 (O1 vs O2), 277 (O1 vs O3), 284 (O1 vs O4), 277 (O2 vs O3), 284 (O2 vs O4) and 158 (O3 vs O4) of their 284 shared keys | R2P-O1, R2P-O2, R2P-O3, R2P-O4 | `.venv/bin/python papers/context-cache/recompute_r2.py C68` |<!-- tier: pinned -->
| C69 | The version round at the ceiling is a **no_signal** result and it is published as one: on both production checkpoints the headline prompt form costs more uncached tokens per turn than the shipped one, the preregistered quality falsification fires on both, and the ceiling declares V0 the best version — the memory never gets cheaper, so the round ends there (§10) | **MoE (O1, SGLang)**: V0 522.7183; V1 P1 **652.8310**, P0 593.5493, P3 630.8310 unc/turn, n=71 each. Paired by turn, V1 P1 - V0 = **+130.1127 [+121.7183, +138.3944]**, excludes 0 on all 71 pairs — 1.249x the shipped bill. **Dense (O4, vLLM)**: V0 1664.3521; V1 P1 **1893.1690**, P0 1896.9859, P3 1916.6901; paired by turn V1 P1 - V0 = **+228.8169 [+140.3099, +319.1831]**, excludes 0, 71 pairs — 1.137x. **Quality, like for like** (the same 20 probes, asked in the P1 form, before and after the change): MoE 20/20 -> 20/20 mismatching, dense 19/20 -> 18/20. The preregistered falsification was a >=10 pp fall in hit rate against a cost ceiling of 45 unc/turn; the hit rate does not fall at all and the cost is 2.9x / 5.1x that ceiling, so it is **falsified on both models**. The 40-probe after-set (20 P0-form + 20 P1-form) scores 0/40 on MoE and 2/40 on dense. Stored mismatch counts reproduce exactly under two readings — mismatch iff whole-answer `ok` is false, and mismatch iff `span_ok` alone is false; a third reading (`span_ok` AND `sha8_ok`) does not reproduce them and is reported as the alternative, not adopted. Drift control: identical P0 bytes in the same run sit 63.1549 (MoE) / 13.1268 (dense) unc/turn from the pinned cell's P0, which bounds how much of either delta can be the change. 213 usable rows per model, 0 non-200, 0 corrections; V0 read from the pinned P1 rows of O1 / O4 (sha256 `8d71a88f...` / `23547e3a...`) | SYSOPT-moe, SYSOPT-dense, R2P-O1, R2P-O4 | `.venv/bin/python papers/context-cache/recompute_r2.py SYSOPT` |<!-- tier: pinned -->

### Corrections to the source cards

| # | Source card said | Rows give | Where in the manuscript |
|---|---|---|---|
| 1 | U4b: "with 7/7 hits A would be 3,856 and B/A = 3.99" (`units/U4b.md`) | 15,400 - 1,792 = 2,856; B/A = 5.3922 (C06) | §3, C06 |
| 2 | U4: warm-append residual "0.9-2.7k tokens" (`orchestration/handoffs/U4.json`) | range 832-7,936, median 1,792; the histogram omits six buckets (C38) | §8, C38 |
| 3 | U4: the edit-vs-fork hypothesis is "REFUTED" (`orchestration/handoffs/U4.json`) | the comparison measured renderer identity; the hypothesis is untested at n>0 (C13, C16) | §5, abstract |
| 4 | U4: 454 live requests (`units/U4.md`) | 438 batch + 7 + 6 probe = 451 in files; 3 smoke sends are card-only (C14) | C14 |
| 5 | U5/U4 fork arms are fork arms | their prompts equal the summarise prompts byte for byte (C03); they are second summarise arms | §2, §5 |
| 6 | CX-V2: replay body digests identical "44/44" (`orchestration/handoffs/CX-V2.json`) | still true of the build that ran U4; re-running today gives 11/44 because U13's marker separates the arms from turn 12 (C16) | §5, C16 |
| 7 | U15: "avoiding the break saves the prefix" / 1.700x as a break-cost win (`orchestration/handoffs/U15.json`, abstract, §6, §10 rule 2) | the 1.700x is a post-compaction window-truncation effect (92.2 % of R's excess), not break-event cost: G1 isolates the break cost at E/F = 1.038 (within measurement noise; only 2 of 6 break events within 10 %) (C21, C22, C24 superseded by G1; C44) | §6, abstract, §10 |

Correction 6 is not a contradiction of the verifier: the verifier's 44/44 was correct for the
library it measured, and U13 changed that library afterwards. The manuscript states both.

### Supersessions by G1

- `C21` — observed `A/R = 1.7002359` stands, but its causal reading "avoiding the break saves the prefix"
  is superseded by G1: the 1.700x is a post-compaction window-truncation effect, not a break-event cost.
- `C22` — the 7.8 % / 92.2 % decomposition stands and is corroborated by G1's `u15_decomposition_note`;
  the break-cost half is re-measured by G1 at `E/F = 1.038` (within measurement noise).
- `C24` — the U15 break-only counterfactual (1.068x) is superseded for the break-cost claim by G1's
  per-break ratio 1.038; the counterfactual value itself remains as U15's arithmetic.
- New `C44` registers the G1 decomposition (264 rows, sha256 `9242ad383281b360ec3c4be92bc59e7de7d5cd751eb7e15c0944f2261497ae66`).

### What is not claimed here

- No claim that the fork policy is better or worse than summarise: the fork hypothesis is
  untested at n>0 under the fixed library (see `GAPS.md`).
- No claim of a general 64-token law for growing contexts: the grid holds for repeats
  (C37) and fails for appends (C38).
- No claim of zero prefill cost: the residual is 4.66 us/token (C34).
- No claim that U4's 438 rows can be repaired: they are not used for any conclusion except
  the demonstration that they measured one renderer (C13, C16).
- No claim that the boundary cost is independent of `keep_last`, of the run length after the
  boundary, or of the compaction trigger: C62 reports one cell in which the trigger was the
  budget's headroom, the arms fire once (64k) or twice (32k), and the post-boundary segment is
  47 to 89 turns (`GAPS.md` G3).
- No claim that C63's model effect is an architecture effect: the model axis is two
  checkpoints (occamy-1.0 MoE vs qwen3.5-9b dense), so it carries size and architecture
  together, and the engine axis carries per-model launch flags (vLLM block 1,088 vs 2,096;
  SGLang mem-fraction-static 0.22 on the dense cell). The claim is a measured 2x2 at one
  band (32k, 71 turns, one seed, one GPU), not a law over models or engines (`GAPS.md` G4).
