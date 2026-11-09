# VERBOSITY — does the grow arm's longer answer explain the TTFT gap?

_Generated offline by `experiments/ptr-engine/longrun/tests/test_verbosity.py` (sha256 `9f6aa0e984b6595d`) at 2026-10-26T17:52:26Z from 14 rows files. Zero inference requests._

**Verdict: `confound_immaterial`.** holding completion length equal leaves 86.7% of the TTFT gap in which arm a (pointer-stable) is 0.37x the first-token latency of arm b (transcript-grow), i.e. b is 2.67x slower; the fitted b_completion is +0.0720 per ln-token and completion length differs 0.19x between the arms, so verbosity covers only 13.3% of it

Scope: p95 TTFT is refused corpus-wide at arm level (no cell reaches n>=60), so this verdict is stated on the median/mean TTFT gap plus the log-log decomposition; p90 is the reported tail.

## 1. Corpus (pinned)

| rows file | rows | completed turns | sha256 |
|---|---|---|---|
| `rows-baseline-2026-10-26.jsonl` | 105 | 84 | `638c84942e3bcdba4b416cceda9214f3fdcc99c42171639bf5c52736f40e032d` |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | 5 | `5ac9dd992f5d8715696925f56c225024e172cb98b4b9a937a0ee63bd099e9800` |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | 61 | `c01c7b4a477fe24bc55370ceddf26d885a1fe827e7135023cdde48b271e8c934` |
| `rows-live-2026-10-26.jsonl` | 27 | 0 | `3d02b4d473304f0012b34024cc517c70d7f23b60de1103c1ca1b93a7e2752e5b` |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | 24 | `9d4ad90ce34cb781c04e9f73fba50ffb47d5b35d6d1491389d22a49044516405` |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | 23 | `9b1097234bf8d2464a4d24ec48cf0cccc1ecd64bd853815fc6643b1ad3da3368` |
| `rows-longrun-2026-10-26.jsonl` | 192 | 93 | `bc61d38192d4e4316021ec8d3d0e21dcb8e6153f463260a0138da21969d0b21e` |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | 177 | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | 95 | `80d85fe0e977af164a5ffeca8b2f95350c6614d2112455c3ace93765530ff921` |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | 88 | `999f298dac8b83569c4059946e7789b76ec485b24a5c9a39d6c1616f0501c28e` |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 47 | `f11391aa2989949f904b8092074cb7b85b65dfe5b8c89431930fe921b28de77f` |
| `rows-longrun-v5-tools.jsonl` | 72 | 47 | `586b66f27939bd05e09d8b48dad745a5fa268c3f31103695746df3e3f8443cb5` |
| `rows-longrun-v6-tools.jsonl` | 72 | 48 | `1e78d75f259afbe0406643825941a65b4773b4342b847698005ad5908b3e531e` |
| `rows-pilot-thinking-2026-10-26.jsonl` | 6 | 5 | `6b81a6281ce0b266f45ab1b95fc3834e446bea5708e5466988b28e133a0e9e10` |

## 2. Per-arm distributions, grouped by file (n in every row)

| file | arm | n | completion tok mean / med / p90 / max | answer chars mean / med / p90 | tok/char | prompt tok med / p90 | TTFT ms mean / med / p90 | TTFT p95 |
|---|---|---|---|---|---|---|---|---|
| `rows-baseline-2026-10-26.jsonl` | C | 24 | 225.7 / 300.0 / 300.0 / 300.0 | 150.8 / 200.0 / 200.0 | 1.4970 | 2059.0 / 2637.0 | — | — (no TTFT field) |
| `rows-baseline-2026-10-26.jsonl` | C0 | 24 | 236.1 / 300.0 / 300.0 / 300.0 | 175.4 / 200.0 / 200.0 | 1.3464 | 5131.0 / 6571.0 | — | — (no TTFT field) |
| `rows-baseline-2026-10-26.jsonl` | R | 36 | 46.7 / 5.5 / 197.0 / 300.0 | 38.1 / 12.0 / 126.0 | 1.2261 | 4317.5 / 6429.0 | — | — (no TTFT field) |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | pointer-stable | 5 | 4688.6 / 1415.0 / 10984.0 / 13126.0 | 366.4 / 152.0 / 781.2 | 12.7964 | 4312.0 / 4336.8 | 408.7 / 399.6 / 658.0 | refused (n=5<60) |
| `rows-equalinfo-2026-10-26.jsonl` | C0F | 15 | 4.0 / 2.0 / 7.0 / 7.0 | 4.4 / 2.0 / 8.0 | 0.9091 | 22575.0 / 22594.0 | 1004.9 / 183.8 / 3152.0 | refused (n=15<60) |
| `rows-equalinfo-2026-10-26.jsonl` | C0FT | 18 | 96.5 / 4.5 / 283.0 / 283.0 | 3.0 / 2.0 / 8.0 | 32.1667 | 22617.5 / 22700.0 | 3115.8 / 192.5 / 9130.2 | refused (n=18<60) |
| `rows-equalinfo-2026-10-26.jsonl` | R | 28 | 78.8 / 7.0 / 249.7 / 298.0 | 9.9 / 2.0 / 22.0 | 7.9675 | 2578.0 / 12937.6 | 2697.8 / 603.1 / 7722.1 | refused (n=28<60) |
| `rows-longrun-2026-10-26-fix.jsonl` | transcript-grow | 14 | 3483.1 / 2097.5 / 7477.2 / 14501.0 | 3337.3 / 1860.0 / 6754.7 | 1.0437 | 2794.5 / 37404.4 | 1550.1 / 226.3 / 3904.4 | refused (n=14<60) |
| `rows-longrun-2026-10-26-policy.jsonl` | transcript-grow | 15 | 5242.8 / 4720.0 / 12952.6 / 14352.0 | 20645.8 / 13174.0 / 57129.8 | 0.2539 | 36840.0 / 49531.8 | 5279.6 / 3204.1 / 12574.3 | refused (n=15<60) |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen | 39 | 110.5 / 119.0 / 128.0 / 128.0 | 246.6 / 239.0 / 423.6 | 0.4482 | 185.0 / 202.0 | 1547.1 / 1567.9 / 2208.6 | refused (n=39<60) |
| `rows-longrun-2026-10-26.jsonl` | pointer-stable | 12 | 110.1 / 128.0 / 128.0 / 128.0 | 439.9 / 527.5 / 683.5 | 0.2502 | 1872.5 / 1918.0 | 919.9 / 525.9 / 1688.7 | refused (n=12<60) |
| `rows-longrun-2026-10-26.jsonl` | transcript-compact | 41 | 112.4 / 107.0 / 128.0 / 128.0 | 238.9 / 243.0 / 260.0 | 0.4705 | 4390.0 / 6425.0 | 908.9 / 630.1 / 1466.5 | refused (n=41<60) |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen | 34 | 244.6 / 87.5 / 538.8 / 2470.0 | 802.5 / 272.5 / 1717.2 | 0.3047 | 429.0 / 442.4 | 140.7 / 136.2 / 143.3 | refused (n=34<60) |
| `rows-longrun-c-2026-10-26.jsonl` | pointer-stable | 47 | 103.0 / 73.0 / 151.8 / 964.0 | 387.6 / 272.0 / 609.8 | 0.2657 | 2213.0 / 2219.0 | 185.3 / 167.0 / 206.6 | refused (n=47<60) |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-compact | 48 | 37.6 / 36.0 / 40.0 / 62.0 | 149.4 / 140.0 / 168.0 | 0.2516 | 3867.0 / 5263.6 | 205.4 / 202.5 / 216.9 | refused (n=48<60) |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-grow | 48 | 634.5 / 550.0 / 1358.1 / 1500.0 | 2480.1 / 2050.0 / 4945.4 | 0.2558 | 18239.5 / 31642.4 | 507.7 / 482.2 / 767.4 | refused (n=48<60) |
| `rows-longrun-v3-2026-10-26.jsonl` | pointer-stable | 47 | 83.0 / 54.0 / 120.4 / 1070.0 | 312.7 / 190.0 / 396.0 | 0.2653 | 2250.0 / 2262.8 | 181.4 / 168.3 / 217.7 | refused (n=47<60) |
| `rows-longrun-v3-2026-10-26.jsonl` | transcript-grow | 48 | 23.2 / 23.0 / 26.0 / 26.0 | 78.5 / 79.0 / 95.0 | 0.2955 | 3545.5 / 4708.4 | 200.7 / 200.7 / 214.7 | refused (n=48<60) |
| `rows-longrun-v4-2026-10-26.jsonl` | pointer-stable | 40 | 122.0 / 34.0 / 279.0 / 1694.0 | 449.5 / 131.5 / 1028.0 | 0.2713 | 4105.0 / 4124.4 | 200.4 / 187.8 / 253.4 | refused (n=40<60) |
| `rows-longrun-v4-2026-10-26.jsonl` | transcript-grow | 48 | 23.6 / 22.0 / 29.0 / 29.0 | 81.4 / 72.0 / 113.0 | 0.2902 | 5409.0 / 6585.7 | 221.3 / 199.8 / 215.4 | refused (n=48<60) |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | pointer-stable | 47 | 75.8 / 63.0 / 118.4 / 268.0 | 250.6 / 212.0 / 407.2 | 0.3025 | 4213.0 / 4326.4 | 198.7 / 201.6 / 251.7 | refused (n=47<60) |
| `rows-longrun-v5-tools.jsonl` | pointer-stable | 47 | 117.9 / 69.0 / 152.8 / 1146.0 | 390.5 / 247.0 / 465.4 | 0.3018 | 4253.0 / 4269.8 | 159.5 / 139.4 / 159.2 | refused (n=47<60) |
| `rows-longrun-v6-tools.jsonl` | pointer-stable | 48 | 206.8 / 62.5 / 323.1 / 3283.0 | 648.4 / 219.0 / 1038.0 | 0.3189 | 4259.5 / 5755.0 | 177.2 / 144.8 / 269.5 | refused (n=48<60) |
| `rows-pilot-thinking-2026-10-26.jsonl` | transcript-grow | 5 | 4470.2 / 2027.0 / 11160.4 / 15624.0 | 13353.6 / 6559.0 / 32775.6 | 0.3348 | 8453.0 / 24191.2 | 1320.7 / 675.7 / 3049.6 | refused (n=5<60) |

Cells withheld (n<5), listed so no small cell masquerades as a distribution:

- `rows-longrun-2026-10-26-fix.jsonl` / `lease-reopen`: n=3 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-fix.jsonl` / `pointer-stable`: n=3 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-fix.jsonl` / `transcript-compact`: n=4 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-policy.jsonl` / `lease-reopen`: n=2 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-policy.jsonl` / `pointer-stable`: n=3 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26-policy.jsonl` / `transcript-compact`: n=3 < 5: not reported as a distribution, no p90/p95
- `rows-longrun-2026-10-26.jsonl` / `transcript-grow`: n=1 < 5: not reported as a distribution, no p90/p95

## 3. The decomposition

Regression pooled across arms **within one file**, so no slope crosses a file boundary:

| file | n | b_prompt | b_completion | R² | c_completion (prompt omitted, upper bound) | corr(ln prompt, ln completion) |
|---|---|---|---|---|---|---|
| `rows-equalinfo-2026-10-26.jsonl` | 67 | -0.0244 | +0.6549 | 0.693 | +0.6610 | -0.397 |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | +0.6665 | -0.0957 | 0.622 | +0.2102 | 0.414 |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | +0.9527 | +0.0987 | 0.851 | +0.8526 | 0.589 |
| `rows-longrun-2026-10-26.jsonl` | 93 | -0.1842 | +0.8194 | 0.344 | +0.7240 | 0.078 |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | +0.3184 | +0.0720 | 0.721 | +0.0724 | 0.001 |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | +0.0373 | -0.0531 | 0.052 | -0.0583 | -0.385 |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | -0.1902 | -0.0297 | 0.036 | -0.0227 | -0.316 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | -2.0609 | +0.0635 | 0.295 | +0.0187 | 0.203 |
| `rows-longrun-v5-tools.jsonl` | 72 | +0.2432 | +0.0759 | 0.064 | +0.0661 | -0.133 |
| `rows-longrun-v6-tools.jsonl` | 72 | +1.8084 | +0.0748 | 0.775 | +0.0310 | -0.128 |

A positive `b_prompt` is prefill cost — more prompt tokens, later first token. `b_completion` is the number the confound hypothesis needs: if longer answers delayed the first token it would be positive and material. TTFT is clocked to the first streamed delta, so the answer is produced **after** that instant.

| file | arms (a − b) | TTFT ratio | completion × | b_prompt·Δln p | b_completion·Δln c | residual | gap share prompt / completion / residual | survives completion normalisation | survives: most conservative (used) |
|---|---|---|---|---|---|---|---|---|---|
| `rows-equalinfo-2026-10-26.jsonl` | C0F − C0FT | 0.48x | 0.26x | +0.000 | -0.890 | +0.165 | -0% / 123% / -23% | -22.7% | -813.7% |
| `rows-equalinfo-2026-10-26.jsonl` | C0F − R | 0.40x | 0.26x | -0.051 | -0.881 | +0.011 | 6% / 96% / -1% | 4.3% | 3.4% |
| `rows-equalinfo-2026-10-26.jsonl` | C0FT − R | 0.82x | 1.01x | -0.051 | +0.008 | -0.153 | 26% / -4% / 78% | 104.2% | 64.1% |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen − pointer-stable | 1.96x | 1.02x | +0.427 | +0.018 | +0.226 | 64% / 3% / 34% | 97.4% | 97.4% |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen − transcript-compact | 1.69x | 0.97x | +0.573 | -0.027 | -0.024 | 110% / -5% / -5% | 105.2% | 90.4% |
| `rows-longrun-2026-10-26.jsonl` | pointer-stable − transcript-compact | 0.86x | 0.95x | +0.146 | -0.045 | -0.249 | -98% / 30% / 168% | 69.8% | 69.8% |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen − pointer-stable | 0.77x | 1.24x | -0.514 | +0.016 | +0.244 | 202% / -6% / -96% | 106.1% | 106.1% |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen − transcript-compact | 0.69x | 2.57x | -0.687 | +0.068 | +0.249 | 185% / -18% / -67% | 118.3% | 116.1% |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen − transcript-grow | 0.29x | 0.24x | -1.146 | -0.102 | +0.012 | 93% / 8% / -1% | 91.7% | 89.8% |
| `rows-longrun-c-2026-10-26.jsonl` | pointer-stable − transcript-compact | 0.89x | 2.07x | -0.173 | +0.052 | +0.005 | 150% / -45% / -4% | 145.4% | 126.4% |
| `rows-longrun-c-2026-10-26.jsonl` | pointer-stable − transcript-grow | 0.37x | 0.19x | -0.632 | -0.118 | -0.232 | 64% / 12% / 24% | 88.0% | 86.7% |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-compact − transcript-grow | 0.42x | 0.09x | -0.459 | -0.170 | -0.237 | 53% / 20% / 27% | 80.3% | 77.8% |
| `rows-longrun-v3-2026-10-26.jsonl` | pointer-stable − transcript-grow | 0.91x | 2.41x | -0.017 | -0.047 | -0.026 | 19% / 52% / 29% | 48.1% | 43.0% |
| `rows-longrun-v4-2026-10-26.jsonl` | pointer-stable − transcript-grow | 0.93x | 2.13x | +0.053 | -0.022 | -0.105 | -71% / 30% / 141% | 70.0% | 70.0% |

How to read the table: arms are listed `a − b`, so `TTFT ratio` is arm a's mean-log TTFT over arm b's (below 1 means a is faster), `completion ×` is `exp(delta ln completion)` = arm a's answer length relative to arm b's, the three share columns are `beta * delta` in log units, and the last two columns are the share of the gap that survives removing the fitted completion-length term (the most conservative of the mean-log model, the completion-only upper bound, and the p50 basis is the one the verdict uses). Shares outside 0-100% are honest arithmetic on near-zero gaps, not errors.

**Headline (G4 / `rows-longrun-c-2026-10-26.jsonl`).** `pointer-stable` answers at **0.19x** the completion length of `transcript-grow` — the other arm's answers are **5.14x** longer — yet `pointer-stable`'s mean-log TTFT is **0.37x** that of `transcript-grow`. Split by the fitted coefficients: prompt tokens -0.632, completion length -0.118, residual -0.232 of a -0.982 log gap. **88.0% of the gap survives holding completion length equal.**

On the **p50** basis the gap is **0.35x** (prompt -0.672, completion -0.142, residual -0.247 of -1.060); the completion-only upper bound is -0.118 of that gap, and the most conservative surviving fraction across all three accountings — mean-log model, completion-only upper bound, p50 basis — is **86.7%**, which is the number the verdict rests on.

## 4. Can the arms be compared on quality at all?

**No, not on any answer-length-sensitive metric.** Same grid, same treatment controls, answer length differing by roughly an order of magnitude: an `ANSWER:`-line rate or a verified-answer count then measures answer length as much as treatment. Per-arm answer length beside those counts:

| file | arm | n | median completion tok | median answer chars | `ANSWER:` line rate | answer_verified rate |
|---|---|---|---|---|---|---|
| `rows-baseline-2026-10-26.jsonl` | C | 24 | 300 | 200 | 0.00 | 0.00 |
| `rows-baseline-2026-10-26.jsonl` | C0 | 24 | 300 | 200 | 0.00 | 0.00 |
| `rows-baseline-2026-10-26.jsonl` | R | 36 | 6 | 12 | 0.00 | 0.00 |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | pointer-stable | 5 | 1415 | 152 | 0.00 | 0.00 |
| `rows-equalinfo-2026-10-26.jsonl` | C0F | 15 | 2 | 2 | 0.00 | 0.00 |
| `rows-equalinfo-2026-10-26.jsonl` | C0FT | 18 | 4 | 2 | 0.00 | 0.00 |
| `rows-equalinfo-2026-10-26.jsonl` | R | 28 | 7 | 2 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26-fix.jsonl` | transcript-grow | 14 | 2098 | 1860 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26-policy.jsonl` | transcript-grow | 15 | 4720 | 13174 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26.jsonl` | lease-reopen | 39 | 119 | 239 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26.jsonl` | pointer-stable | 12 | 128 | 528 | 0.00 | 0.00 |
| `rows-longrun-2026-10-26.jsonl` | transcript-compact | 41 | 107 | 243 | 0.00 | 0.00 |
| `rows-longrun-c-2026-10-26.jsonl` | lease-reopen | 34 | 88 | 272 | 0.00 | 0.00 |
| `rows-longrun-c-2026-10-26.jsonl` | pointer-stable | 47 | 73 | 272 | 0.00 | 0.00 |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-compact | 48 | 36 | 140 | 0.00 | 0.00 |
| `rows-longrun-c-2026-10-26.jsonl` | transcript-grow | 48 | 550 | 2050 | 0.00 | 0.00 |
| `rows-longrun-v3-2026-10-26.jsonl` | pointer-stable | 47 | 54 | 190 | 0.66 | 0.02 |
| `rows-longrun-v3-2026-10-26.jsonl` | transcript-grow | 48 | 23 | 79 | 1.00 | 0.00 |
| `rows-longrun-v4-2026-10-26.jsonl` | pointer-stable | 40 | 34 | 132 | 0.75 | 0.03 |
| `rows-longrun-v4-2026-10-26.jsonl` | transcript-grow | 48 | 22 | 72 | 1.00 | 0.00 |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | pointer-stable | 47 | 63 | 212 | 0.19 | 0.02 |
| `rows-longrun-v5-tools.jsonl` | pointer-stable | 47 | 69 | 247 | 0.09 | 0.00 |
| `rows-longrun-v6-tools.jsonl` | pointer-stable | 48 | 62 | 219 | 0.15 | 0.02 |
| `rows-pilot-thinking-2026-10-26.jsonl` | transcript-grow | 5 | 2027 | 6559 | 0.00 | 0.00 |

## 5. What `RUN-A*` must report so this can never be ambiguous again

`RUN-A*` must publish, **per arm and per grid, with n and the rows-file sha256**: (1) `completion_tokens` and answer characters as mean/median/p90/max, so verbosity is never inferred from a slope; (2) TTFT at mean/median/p90 and a p95 **only** where n≥60, with the refusal stated below that floor; (3) the fitted `b_prompt`/`b_completion` with R², so a TTFT gap is decomposed rather than asserted; (4) `ANSWER:`-line rate and `answer_verified` rate **beside** median answer length, because a count metric that grows with answer length is not treatment evidence. A gap quoted without those four numbers is a slope with treatment and verbosity still tangled inside it.

## 6. Limits

- No p95 is published for any cell: the largest per-(file,arm) completed-turn cell is 48 rows, below the 60 floor. Mean/median/p90 published with n.
- TTFT is clocked to the first streamed delta; completion tokens are produced after that instant, so completion length cannot mechanically delay TTFT. b_completion is the load-bearing test of that.
- Answer length remains a real confound for quality and for ANSWER:-line production, which is a different dependent variable from TTFT.
- No field in these rows separates prefill *compute* from server queueing/wait: `ttft_ms` is one client-side first-delta clock. The prompt-side share is therefore a **proxy** (fitted on prompt tokens), not measured prefill FLOPs. A server-side `prefill_ms` (or per-request `queue_wait_ms`) is what would split them.
