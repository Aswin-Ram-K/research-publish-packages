# RESULTS — lazy instruction loading: cold/warm crossover sweep

Requests recorded: **147** rows across **66** runs. One JSONL row per request; a C0 run is exactly 1 request, an L1 run is 1 + one request per fetch round, so L1's extra round trips are counted, not hidden.

Fetch protocol on the L1 arm, both models: `text_emulated` — the native-tool-call vs text-emulation confound of the first arm is removed. C0 rows carry no fetch protocol by construction (nothing to fetch).


**Cache instrument is blind on: qwen3.5-9b.** That server returns `prompt_tokens_details: null` on every call, so `cached_tokens` is unknown there, not zero. Its rows are recorded with `cache_reporting: false` and the billed column for it assumes 0 cached — the only defensible client assumption, and an upper bound on L1's disadvantage. Its *realised* column is unaffected: `prompt_tokens` is real either way.


### Table 1 — realised saving

`(C0_prompt − L1_prompt − fetched_body_tokens) / C0_prompt`. Positive = L1 cheaper. Credits L1 for the bodies it never fetched. Fetched body tokens are estimated as `fetched_body_chars × chars_per_token`, where the ratio is measured on that same model's C0 request for that same corpus.

| items | corpus chars | needed | occamy-1.0 cold | occamy-1.0 warm | qwen3.5-9b cold | qwen3.5-9b warm |
|---|---|---|---|---|---|---|
| 12 | 3,000 | 17% | -288.4% | -291.0% | -288.1% | -289.7% |
| 12 | 10,000 | 17% | -307.3% | -307.8% | missing | missing |
| 12 | 30,000 | 17% | -324.3% | -324.5% | missing | missing |
| 30 | 3,000 | 20% | -751.2% | -910.2% | missing | missing |
| 30 | 10,000 | ? | missing | missing | missing | missing |
| 30 | 30,000 | ? | missing | missing | missing | missing |

### Table 2 — billed saving (the one that decides)

`(C0_uncached − L1_uncached) / C0_uncached`, `uncached = prompt_tokens − cached_tokens`. A cached prefix token is not billed, so a warm C0 ships 30k chars for almost nothing while L1 still pays a round trip per fetch.

| items | corpus chars | needed | occamy-1.0 cold | occamy-1.0 warm | qwen3.5-9b cold | qwen3.5-9b warm |
|---|---|---|---|---|---|---|
| 12 | 3,000 | 17% | -107.0% | -1288.9% | -106.9% | -105.7% |
| 12 | 10,000 | 17% | -2.5% | -2192.3% | missing | missing |
| 12 | 30,000 | 17% | +44.8% | -702.8% | missing | missing |
| 30 | 3,000 | 20% | -542.6% | -1781.2% | missing | missing |
| 30 | 10,000 | ? | missing | missing | missing | missing |
| 30 | 30,000 | ? | missing | missing | missing | missing |

### Table 2b - absolute uncached prompt tokens (the base under Table 2's percentages)

A percentage over a ~20-token base is not a cost decision on its own, so the absolute tokens are shown: this is what a warm C0 and a warm L1 each still bill after the prefix is cached.

| items | corpus chars | needed | occamy-1.0 cold | occamy-1.0 warm | qwen3.5-9b cold | qwen3.5-9b warm |
|---|---|---|---|---|---|---|
| 12 | 3,000 | 17% | +104470.0% | +600.0% | +104570.0% | +103000.0% |
| 12 | 10,000 | 17% | +246000.0% | +1300.0% | missing | missing |
| 12 | 30,000 | 17% | +649200.0% | +1200.0% | missing | missing |
| 30 | 3,000 | 20% | +145570.0% | +3200.0% | missing | missing |
| 30 | 10,000 | ? | missing | missing | missing | missing |
| 30 | 30,000 | ? | missing | missing | missing | missing |

| items | corpus chars | model | cache | C0 uncached | L1 uncached | delta (L1 - C0) |
|---|---|---|---|---|---|---|
| 12 | 3,000 | occamy-1.0 | cold | 1045 | 2162 | +1117 |
| 12 | 3,000 | occamy-1.0 | warm | 6 | 83 | +77 |
| 12 | 3,000 | qwen3.5-9b | cold | 1046 | 2163 | +1118 |
| 12 | 3,000 | qwen3.5-9b | warm | 1030 | 2119 | +1089 |
| 12 | 10,000 | occamy-1.0 | cold | 2460 | 2523 | +63 |
| 12 | 10,000 | occamy-1.0 | warm | 13 | 298 | +285 |
| 12 | 30,000 | occamy-1.0 | cold | 6492 | 3582 | -2910 |
| 12 | 30,000 | occamy-1.0 | warm | 12 | 96 | +84 |
| 30 | 3,000 | occamy-1.0 | cold | 1456 | 9353 | +7898 |
| 30 | 3,000 | occamy-1.0 | warm | 32 | 602 | +570 |

### Table 3 — correctness (reps correct / reps) and fetch counts

| items | corpus chars | model | cache | C0 correct | L1 correct | L1 mean fetches | L1 fetched ids | L1 facts found |
|---|---|---|---|---|---|---|---|---|
| 12 | 3,000 | occamy-1.0 | cold | 3/3 | 3/3 | 2.0 | K-2, M-1 | 2.0 |
| 12 | 3,000 | occamy-1.0 | warm | 3/3 | 3/3 | 2.0 | K-2, M-1 | 2.0 |
| 12 | 3,000 | qwen3.5-9b | cold | 3/3 | 3/3 | 2.0 | K-2, M-1 | 2.0 |
| 12 | 3,000 | qwen3.5-9b | warm | 3/3 | 2/3 | 2.0 | K-2, M-1 | 1.3 |
| 12 | 10,000 | occamy-1.0 | cold | 3/3 | 3/3 | 2.0 | K-2, M-1 | 2.0 |
| 12 | 10,000 | occamy-1.0 | warm | 3/3 | 3/3 | 2.0 | K-2, M-1 | 2.0 |
| 12 | 30,000 | occamy-1.0 | cold | 3/3 | 3/3 | 2.0 | K-2, M-1 | 2.0 |
| 12 | 30,000 | occamy-1.0 | warm | 3/3 | 3/3 | 2.0 | K-2, M-1 | 2.0 |
| 30 | 3,000 | occamy-1.0 | cold | 3/3 | 2/3 | 5.0 | K-2, K-4, M-1, M-4, S-4, T-4 | 5.3 |
| 30 | 3,000 | occamy-1.0 | warm | 3/3 | 3/3 | 6.0 | K-2, K-4, M-1, M-4, S-4, T-4 | 6.0 |

### Table 4 — the regime, proved per cell rather than assumed

| model | cache state | mean cached / prompt (C0) | mean cached / prompt (L1) | cache reported |
|---|---|---|---|---|
| occamy-1.0 | cold | 0.0% | 0.0% | NO — null |
| occamy-1.0 | warm | 99.1% | 93.9% | yes |
| qwen3.5-9b | cold | 0.0% | 0.0% | NO — null |
| qwen3.5-9b | warm | 0.0% | 0.0% | NO — null |

### Crossover point

- **occamy-1.0, cold**: billed saving is positive from 30,000 chars / 12 items (17% needed) — +44.8% there.
- **occamy-1.0, warm**: NO crossover in the swept range — L1 loses on billed tokens in all 4 cells.
- occamy-1.0, warm, worst cell: 10,000 chars / 12 items → billed -2192.3%, realised -307.8%.
- **qwen3.5-9b, cold**: NO crossover in the swept range — L1 loses on billed tokens in all 1 cells.
- **qwen3.5-9b, warm**: NO crossover in the swept range — L1 loses on billed tokens in all 1 cells.
- qwen3.5-9b, warm, worst cell: 3,000 chars / 12 items → billed -105.7%, realised -289.7%.
