# GROUND-TRUTH-R — live 40-turn arm-R re-measurement (production :8012)

**Status:** done. 40 rows / 40 requests / 0 failures. No restart, no variant container, HTTP only.

## Design (U15 arm-R generator, unchanged)
- endpoint `http://192.168.2.168:8012/v1`, model `occamy-1.0`, no launch
- corpus `experiments/context-cache/corpora/endtoend.json` scenario E1, turns 1-40
- `SUMMARISE_IN_PLACE`, `NAIVE_APPEND` renderer, budget 8192, keep_last 2, max_tokens 4, no thinking
- compaction schedule re-derived: `[18, 35]`
- **salt `d7f4975ba19f6c64` (seed 9501)** — new; U15 arm R used `d727998b0e061e0b` (seed 1501)

## Counts
`wc -l` = 40 · non-200 = 0 · cached>0 = 38 (turns 1 and 18 are cold) · warm retries = 0 · live requests 40/60
rows sha256 `711c77ab55258c69c073c34083291209ff93b124c374013fa2e8d87d4fe40a3f`

## The two means against both hypotheses
| window | fresh | published | Δ vs published | repaired | Δ vs repaired |
|---|---|---|---|---|---|
| uncached/turn 1-40 | **1278.3000** | 1279.3000 | **-0.08 %** | 1118.5250 | +14.28 % |
| uncached/turn 19-34 | **1658.9375** | 1659.9375 | **-0.06 %** | 1314.7500 | +26.18 % |

The fresh run misses both published means by exactly **-1.0 token/turn** — the prompts are uniformly one token
shorter and `cached_tokens` is identical, i.e. this is a prompt-rendering offset, not a cache effect. It is not
"between" the two hypotheses: it sits on the published values and 14-26 % away from the repaired ones.

## Per-turn `cached_tokens` (40 numbers)
```
[0, 1152, 1152, 2048, 2048, 2944, 2944, 3840, 3840, 3840, 4864, 5696, 5696, 6592, 6592, 7552, 7552, 0, 768, 768, 1920, 1920, 2816, 2816, 3776, 3776, 4608, 4608, 5504, 5504, 6464, 6464, 7360, 7360, 768, 896, 896, 1792, 1792, 2688]
```

## Does the flagged pattern appear? YES
18 of 39 adjacent pairs hold **identical** `cached_tokens>0` while `prompt_tokens` grows:
turns `[3, 5, 7, 9, 10, 13, 15, 17, 20, 22, 24, 26, 28, 30, 32, 34, 37, 39]` — 8 of them inside the 19-34 window, and **exactly the same 18 turns as U15 arm R**.
The whole 40-value cached series is bit-identical to U15's despite the new salt.

That last fact is the important one and it cuts both ways: the server's cache accounting is a
**deterministic staircase in prompt length**, so a new salt changes nothing. The detector fires on the
flat steps of that staircase; a fresh run reproduces them, so a repair that treats every flat step as
stale credit is correcting a reproducible quantity, not a recording accident.

## Verdict
**The server supports hypothesis 2: the published means stand and the repair over-corrects** — deltas
-0.08 % / -0.06 % against published versus +14.28 % / +26.18 % against repaired.

**Caveat that must not be dropped:** this design establishes reproducibility, not independence. Because
the cached series is the same function of prompt length on both runs, the fresh measurement cannot
audit whether that function is truthful. Falsifying the stale-credit model needs a row whose credit the
server is forced to recompute (an exact repeat of an identical prompt, or a cache-disabled control),
not a longer staircase.

## Writes
`experiments/context-cache/cells/GROUND-TRUTH-R/{rows.jsonl,analysis.json,run.py}`,
`orchestration/handoffs/GROUND-TRUTH-R.json`, this file. No `cells/U15/**`, no `papers/**`, no config, no tests.
