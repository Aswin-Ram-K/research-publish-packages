# RESULTS -- lazy instruction loading

Corpus: 12 items (3 tools, 3 skills, 3 memory notes, 3 knowledge notes), 22,162 characters. The task requires exactly 2 of the 12 items (K-2, M-1) and the task text never names them.

Requests recorded: 21 rows across 12 runs. One JSONL row per request; an L1 run is 1 + one row per fetch round, C0 is exactly 1 row.


Fetch protocol used in the L1 arm: `occamy-1.0` = `native_function_calling`, `qwen3.5-9b` = `text_emulated`.


## Tokens per arm per model (prompt tokens over the whole run)

| model | arm | runs | prompt tokens (mean) | min | max | mean requests |
|---|---|---|---|---|---|---|
| occamy-1.0 | c0 | 3 | 5359 | 5359 | 5359 | 1.00 |
| occamy-1.0 | l1 | 3 | 2625 | 2625 | 2625 | 2.00 |
| qwen3.5-9b | c0 | 3 | 5359 | 5359 | 5359 | 1.00 |
| qwen3.5-9b | l1 | 3 | 3324 | 3324 | 3324 | 3.00 |

## Correctness per arm per model (both facts required)

| model | arm | correct runs | billing_retention_days=400 | scheduler_max_attempts=5 |
|---|---|---|---|---|
| occamy-1.0 | c0 | **3/3** | 3/3 | 3/3 |
| occamy-1.0 | l1 | **3/3** | 3/3 | 3/3 |
| qwen3.5-9b | c0 | **3/3** | 3/3 | 3/3 |
| qwen3.5-9b | l1 | **3/3** | 3/3 | 3/3 |

## L1 fetch-count distribution

| model | fetch counts per run | mean | fetched ids | required items retrieved |
|---|---|---|---|---|
| occamy-1.0 | [2, 2, 2] | 2.00 | K-2, M-1 | 6/6 |
| qwen3.5-9b | [2, 2, 2] | 2.00 | K-2, M-1 | 6/6 |

The required items were retrieved **without a miss** in every L1 run: the fetch count equals the number of required items exactly, so no run fetched a non-required item and no run needed a retry after a wrong id.


## Realised saving

`realised_saving = (C0 prompt - L1 prompt - fetched body tokens) / C0 prompt`

| model | C0 prompt (tok) | L1 prompt (tok) | fetched body chars | fetch overhead (tok) | fetched body (tok, est) | realised saving |
|---|---|---|---|---|---|---|
| occamy-1.0 | 5359 | 2625 | 3538 | 1761 | 1675 | **19.8%** |
| qwen3.5-9b | 5359 | 3324 | 3538 | 2688 | 1065 | **18.1%** |

Characters per prompt token, measured on the L1 index itself: `occamy-1.0` = 2.11, `qwen3.5-9b` = 3.32.

"fetch overhead" is the L1 prompt cost that is not the index: the assistant's own fetch request plus the protocol instruction, re-sent on each further round.


## Cache behaviour (`prompt_tokens_details.cached_tokens`)

| model | arm | rows | rows reporting cached_tokens | mean cached (tok) | mean cached fraction |
|---|---|---|---|---|---|
| occamy-1.0 | c0 | 3 | 3/3 | 5312 | 99.1% |
| occamy-1.0 | l1 | 6 | 5/6 | 1190 | 87.2% |
| qwen3.5-9b | c0 | 3 | 0/3 | not reported | not reported |
| qwen3.5-9b | l1 | 9 | 0/9 | not reported | not reported |

The `:8014` server never populates `prompt_tokens_details`, so cached-token overlap for `qwen3.5-9b` is **unmeasured**, not zero.

**This is the honest headline caveat.** At temperature 0 with a byte-identical prefix, `occamy-1.0` served the C0 arm at a **99.1% cache hit** in every rep, so C0's 5,359 prompt tokens are ~53 billable tokens each time after the first. L1 never reaches that steady state: each run is a fresh index seed followed by fetch rounds whose payload differs per rep. The realised saving above is therefore a **cold-cache** comparison, and it is the reading that flatters L1.


## Completion text (every run)

- `occamy-1.0` `c0` rep1: correct=True fetch=0 (-) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `occamy-1.0` `c0` rep2: correct=True fetch=0 (-) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `occamy-1.0` `c0` rep3: correct=True fetch=0 (-) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `occamy-1.0` `l1` rep1: correct=True fetch=2 (K-2,M-1) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `occamy-1.0` `l1` rep2: correct=True fetch=2 (K-2,M-1) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `occamy-1.0` `l1` rep3: correct=True fetch=2 (K-2,M-1) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `qwen3.5-9b` `c0` rep1: correct=True fetch=0 (-) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `qwen3.5-9b` `c0` rep2: correct=True fetch=0 (-) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `qwen3.5-9b` `c0` rep3: correct=True fetch=0 (-) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `qwen3.5-9b` `l1` rep1: correct=True fetch=2 (K-2,M-1) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `qwen3.5-9b` `l1` rep2: correct=True fetch=2 (K-2,M-1) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5
- `qwen3.5-9b` `l1` rep3: correct=True fetch=2 (K-2,M-1) err=None -> billing_retention_days: 400 / scheduler_max_attempts: 5

---

# Interpretation

## What was measured, and what it costs

The realised saving is real but modest. Over the whole run, including every tool
round trip, L1 sends **51% of C0's prompt tokens on `occamy-1.0`** (2,625 vs 5,359)
and **62% on `qwen3.5-9b`** (3,324 vs 5,359). Charging the returned body text back
into L1's bill, the net saving falls to **19.8%** and **18.1%**.

That second number is the one that matters, because a fetched body is not free: it
is prompt tokens on the next round, and it arrives *after* the first round rather
than inside it. Half of C0's advantage evaporates the moment the model actually
fetches the two items it needs.

## Lazy loading did not collapse into "fetch everything"

This is the case the card anticipated as the likely negative outcome, and on this
workload it did **not** happen. Both models fetched **exactly 2 items in 3/3 runs**,
both times the two required ones (K-2, M-1), with no wasted fetch and no wrong-id
retry. The 12-item corpus was not swept. So the "does not pay" verdict does not
apply here: for a 12-item library where 2 items are needed, lazy loading pays
about 18-20% on a cold cache.

The mechanics are visible in the two overhead columns. The index itself is cheap
(1,342 characters; 864 tokens on `occamy-1.0`), but each extra round re-sends the
growing history. On `qwen3.5-9b` the overhead (2,688 tok) is **more than twice**
the estimated body cost (1,065 tok), because its text-emulated protocol needs one
extra round to say "ANSWER". The overhead, not the corpus, is what sets the floor.

## The measurement flatters L1

The saving above is a **cold-cache** reading. `occamy-1.0` served every C0 rep at a
**99.1% cache hit** (5,312 of 5,359 tokens), because all three C0 reps send a
byte-identical prefix. L1 never stabilises that way: each run pays a fresh index
seed and fetch rounds whose payload varies per rep. In a cached deployment  -  the
normal case for a long-lived instruction prefix  -  C0's marginal prompt cost is
about 47 tokens per request, which no multi-round L1 run can beat.

**Whether lazy loading wins is therefore a question about cache state, not about
corpus size alone.** With a warm prefix cache, this rendering loses. With a cold
cache and a task needing a small fraction of a large corpus, it wins. Neither
number is a universal claim, and the cold-cache 18-20% must not be quoted as the
saving.

## Threats to validity, stated plainly

1. **Two models, three reps each, temperature 0.** Deterministic: every cell is
   3/3 identical values. Prompt tokens were byte-identical across reps for a given
   arm and model, so the reps establish stability, not variance. n=3 cannot
   detect small effects.
2. **The two L1 arms are not the same protocol.** `:8014` has no tool-call parser
   (`400: "auto" tool choice requires --enable-auto-tool-choice and
   --tool-call-parser"`) and must not be restarted, so `qwen3.5-9b` used a
   text-emulated fetch (3 rounds) while `occamy-1.0` used native function calling
   (2 rounds). Cross-model comparison is indicative, not clean. The extra round is
   why qwen's overhead is higher, not a difference in understanding.
3. **Fetched-body tokens are estimated**, from characters at the ratio each model
   realises on the index (2.11 and 3.32 chars/token). No tokenizer was available
   for either model. The estimate is applied symmetrically across both models.
4. **C0 and L1 saturate at 3/3 correct.** The task is not hard enough to separate
   the arms on accuracy. A failure for one arm could have been a failure of
   understanding rather than of loading, and this design cannot tell those apart  - 
   which is a limitation of this task, not evidence that the arms are equally
   robust.
5. **One corpus, one task.** No scaling sweep over corpus size or over the
   fraction of items needed. The 18-20% is one point on that curve.

## The first honest measurement, and its positive result

The body-replacement hypothesis had never been measured in this repository. It now
has one measurement: **the projection is faithfully resolvable, the models resolve
it correctly and cheaply, and the corpus is not swept.** The saving is 18-20% net
on a cold cache with a 12-item corpus and 2 items needed, and it inverts to a loss
under a warm prefix cache.

## What would make this decisive

- Repeat with a warm prefix cache on both arms, which is the deployment that matters.
- Sweep corpus size (e.g. 3k / 10k / 30k characters) and the needed fraction
  (2 of 12 vs 6 of 30), to find where the crossover actually sits.
- Give both models the same fetch protocol, so the cross-model row is fair.
- A task whose two facts are *harder to guess* from a description, so correctness
  separates the arms rather than saturating.
