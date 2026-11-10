# HL pilot — operator decision (2026-11-04)

**Question.** Find a serving configuration and a high-density typed append-only context
method that preserves task quality while reducing *actual* cache-adjusted work — including
compaction and recovery — for Duval-oriented agent work.

**Answer, one line.** No candidate was promoted and the production context policy is
unchanged. Typed append-only records cut prefill work 13.7 % (LR-04) and 40.8 % (LR-01) while
passing the same acceptance checks, but they also make the model run out of answer budget more
often (silent turns 5 → 7 of 40), the combined work proxy stays inside the 10 % bar it was
supposed to clear (−5.4 % / −8.6 %), and no arm reached the fixtures' own acceptance rule — so
"cost per verified success" is not a number this pilot may quote.

| Arm | What it is | Uncached (LR-04) | Output tokens | Combined proxy | Strict checks | Silent turns |
|---|---|---|---|---|---|---|
| A | append-only verbatim transcript | 29,646 | 25,831 | 55,477 | 4/8 | 5 / 40 |
| B | typed append-only records, sha8 refs, stable prefix | 25,584 (−13.7 %) | 26,890 | 52,474 (−5.4 %) | 4/8 | 7 / 40 |
| C | B + masking of work turns older than 12 | 42,216 (+42.4 %) | 28,362 | 70,578 (+27.2 %) | 4/8 | 9 / 40 |

"Silent turns" are calls whose entire 1,200-token budget went to reasoning and which returned
empty content (`finish_reason: length`). They are the reason the phrase "equal measured quality"
above is too generous: the *checks* land identically, but the arms do not answer equally often.

All three arms pass and fail **exactly the same** acceptance checks on the discovery fixture
(`LR-04`): the two planted-value checkpoints that are answerable in replay both pass in every
arm, the phrasing-exact checkpoint fails in every arm, and the three "run the tests and report
exit codes" checks are impossible for a text-only replay. Both negative constraints survive in
every arm.

## The three findings that change how we should think

**1. Reuse tracks the first rewrite, not the payload — and masking is a cache bomb.**
`E1C` (48 calls, 10,022-token frozen prefix, 9 offsets × 3 distinct rewrites, cell-isolated by
`/flush_cache` + reseed) measured `cached ≈ rewrite_offset` with a median residual of **9
tokens** and a spread of 841, no offset deviating by more than one 64-token block once warm.
There is no interior cliff: reuse is a linear function of where the first divergence lands.
That is why arm `C` is the expensive one — masking drops old turn text, which moves the first
divergence *earlier* on every single turn, so the engine re-prefills from there. `C` sent
6–8 % fewer prompt tokens than `A` and paid **+42 %** (LR-04) and **+155 %** (LR-01, E4 config)
more uncached prefill for it. Prompt size and prefill cost are anti-correlated here.

**2. Compaction does not reduce uncached work; it reduces payload.**
`E2` (93 calls, 30-step trajectory, three arms, three no-op controls) found total prompt
falling 39 % (A: 138,471 → B: 83,861) and 63 % (C: 50,898) while total uncached work moved by
**−3.3 %** and **−8.9 %** (counting a call with no reported cache details as fully uncached;
on the rows that carry a derived value only, the same comparison is −6.9 % / −11.3 % — the
sign and the order of magnitude do not depend on the convention). A checkpoint's rebuild cost was small (617 tokens for B; 351 and 526
for C) and the no-op control cost 57 / 50 / 290 tokens, i.e. approximately nothing. E2's
falsifier fires in its second clause: the gain is payload, not work. Folding history after the
fact cannot save work that was already cached; only *not sending it in the first place* can.

**3. On this stack, output tokens dominate the bill, not context — and the arms move them the
wrong way.**
The context policy moved input work by −13.7 % (B) on LR-04 while output moved +4.1 %
(25,831 → 26,890) and reasoning tokens +10.7 % (22,699 → 25,118); on LR-01 the same trade
becomes −40.8 % input for +30.0 % output (28,761 → 37,380). With any price schedule where
output costs more per token than input — every schedule we know of — B's input saving is
swamped, and the larger the transcript the worse the swap gets. This pilot has **no trustworthy price schedule** (the rig is a local
GB10; there is no invoice), so the plan's proxy is "uncached input + output tokens", and under
that proxy B is **−5.4 %**, short of the 10 % gate.

## Serving configuration

No configuration change was tested or needed: the pilot ran entirely against the existing
production endpoint, which was never restarted.

| Field | Value |
|---|---|
| model | `occamy-1.0` (Accio-Lab occamy-1.0-NVFP4, `modelopt_fp4`, bf16) |
| window | 131,072 tokens |
| engine | SGLang 0.0.0.dev1+g4ccff141d, image `sha256:72457f09d20e…` |
| flags | `--mem-fraction-static 0.45 --kv-cache-dtype fp8_e4m3 --max-mamba-cache-size 64 --mamba-radix-cache-strategy extra_buffer --mamba-track-interval 256 --chunked-prefill-size 8192 --max-running-requests 5` |
| session cache | `enable_session_radix_cache=false` — available in this build, deliberately off; the pilot did not enable it and credits it with nothing |
| second endpoint | vLLM `qwen3.5-9b`, `max_model_len 32768` — inventoried, not exercised; a 32K tier comparison needs its own fingerprinted run |

Production interruption: **0 minutes**. `/v1/models` 200 before and after; container `gx10-occamy-nvfp4`
started `2026-11-04T13:46:18.991Z` and was never restarted (same `StartedAt` and `Running=true` at
the check after the last run); all six restore keys identical before and after
(`page_size=1`, `mamba_radix_cache_strategy=extra_buffer`, `radix_eviction_policy=lru`,
`mem_fraction_static=0.45`, `kv_cache_dtype=fp8_e4m3`, `max_mamba_cache_size=64`).

## Limitations that must travel with these numbers

- **No arm reached the fixtures' acceptance rule.** Every arm fails it because one checkpoint
  demands a phrasing (`{0, 1} of P1 mod B`) no arm reproduces, and three checks require
  executing pytest. The fixtures assume a live tool channel and a writable checkout; this
  replay gave them neither. Quality is therefore compared *paired* (the same checks fail in
  every arm) and never quoted as an absolute success rate. Note the deliberate distinction:
  `E2` reports 30/30 "verified" checkpoints for arm B, but that is retention of a value the
  model had already computed, not a fixture acceptance — the two words are not interchangeable.
- **The loose gate in `notes/e5-analysis.json` says `passes: true` for B and is not the
  decision.** It scores input work alone; the plan's proxy adds output tokens, and on that
  proxy B is −5.4 %. The artifact is left as written so the difference stays inspectable.
- **One discovery fixture, one held-out fixture** (`LR-04` 40 turns, `LR-01` 48 turns), both
  `ptr_engine` tasks, not Duval tasks. DO_NOT_REDO §6 orders `LR-01..06` first; Duval remains
  untouched (`git --no-optional-locks status` 0 lines, HEAD unchanged, no writes).
- **Two generation configs.** `E4` ran with thinking off (quality void, cost valid); `E5` with
  thinking on. Rows from the two are never pooled — different fingerprints, different
  experiments.
- **The cold-seed exception.** The first request after a flush reports either nothing or
  exactly `chunked_prefill_size` (8,192) of a 10,022-token prefix, while later requests match at
  block granularity. Plausibly chunked-prefill commit ordering; that explanation is inference,
  not measurement.
- **A 3-request sample** decided the instrumentation contract: this engine omits
  `prompt_tokens_details` on a miss and reports it on a hit, so `cached_tokens` absent is
  recorded as `null` (unknown) and never as 0.

## What was fixed on the way (and what it cost)

| Run | Calls | Outcome |
|---|---|---|
| PREFLIGHT | 3 | engine omits cache details on a miss; repeat hit 704/720; head rewrite misses |
| E1 | 39 | **invalid** — reps were byte-identical to rep 1, two rewrites were no-ops, branches thrashed the 64-slot mamba cache |
| E1B | 14 | **aborted** by its own assertion (rotation 26 = identity) |
| E1C | 48 | valid boundary sweep |
| E2 | 93 | valid checkpoint cost |
| E4 | 264 | **quality void** (thinking disabled, pointed excerpts only); cost valid |
| E5 LR-04 | 120 | valid arm comparison on the discovery fixture |
| E5B LR-01 | 144 | held-out arm comparison |
| probes | 4 | thinking on/off answer shape; ask-string sensitivity |
| quarantined | 30 | aborted/interleaved rows, kept as evidence, excluded from analysis |
| **total** | **765** | under the 1,000-request cap |

## Recommendation

1. **Do not change the production context policy.** Nothing cleared the gate.
2. **Adopt one rule now, because it is measured and cheap:** never re-render history that has
   already been sent. Masking, sliding windows and in-place summaries all move the first
   divergence earlier and cost more than they save — `C` is +42 %/+155 % on two fixtures. If
   history must shrink, shrink it by *appending* a record that refers back, not by rewriting.
3. **Re-test B against a real price schedule and a runnable fixture.** B's ~14 % prefill saving
   is real and cache-safe; whether it is worth anything depends on the input/output price
   ratio, which this rig cannot supply. The instrument to fix is the fixture, not the arm: the
   checks that matter (planted-value recall, negative constraints) need values the model can
   actually derive and answers a replay can actually produce.

## Artifacts

- envelopes (frozen before their first call): `experiments/context-cache/cells/HL-PILOT/envelopes/{PREFLIGHT,E1,E1B,E1C,E2,E4,E5,E5B,fingerprints}.json`
- rows: `…/HL-PILOT/rows/{preflight,e1,e2,e4,e5,e5b}.jsonl`, quarantined: `rows/e5-lr01-aborted.jsonl`
- analyses: `…/HL-PILOT/notes/{preflight-summary,e1c-analysis,e2-analysis,e4-analysis,e5-analysis,e5b-analysis}.json`
- tools: `…/HL-PILOT/tools/{adapter,preflight,e1_boundary,e1b_sweep,e2_checkpoint,e4_arms,e5_arms,e5b_arms,fingerprints,pins}.py`
- guard: `tests/test_hl_adapter_contract.py` (7 tests; red on the null→0 mutant, green on the adapter)
- call ledger: `…/HL-PILOT/CALL-LEDGER.md`
- earlier servable-cliff correction: `experiments/context-cache/cells/STATE-CLIFF/RESIDENCY-BOUNDS.md`
- source-linked knowledge: `docs/research/session-cache-and-masking.md` + `measure/research/session-cache-and-masking.json`

## Held-out fixture (LR-01)

48 turns × 3 arms = 144 calls, 0 errored; 39 calls hit `finish_reason == "length"` with empty text (recorded as a defect, not retried).

| Arm | uncached | output | uncached+output | strict checks passed |
|---|---:|---:|---:|---:|
| A | 34,485 | 28,761 | 63,246 | 3/7 |
| B | 20,425 | 37,380 | 57,805 | 3/7 |
| C | 41,535 | 39,358 | 80,893 | 3/7 |

- Uncached deltas vs A: B −40.8 %, C +20.4 %. Combined (uncached+output) deltas vs A: B −8.6 %, C +27.9 %.
- Per-check map identical across arms and matches LR-04: 3 strict-passed, same negatives survived. But the silence count is not identical — **A 6 / B 14 / C 19 of 48** — so the held-out fixture reproduces the LR-04 pattern (5 / 7 / 9 of 40) at nearly three times the size: the denser and the masked context make the model reason past its 1,200-token budget and answer nothing. Checkpoint answers happen to survive this in all three arms; most of the rest does not.
- Because B and C leave two to three times as many turns unanswered, the held-out run *reinforces* the no-promotion recommendation rather than merely leaving it intact: B's uncached saving is real and cache-safe but its combined proxy is only ~8.6 % lower, below the 10 % gate once output tokens are included, and no arm cleared verified success, so production context policy stays unchanged.

## Verification

An independent unit (`orchestration/handoffs/V-HL-PILOT.json`) re-derived every headline number
from the row files and re-ran the guard's red→green: 7 passed clean, 3 failed / 4 passed with a
single mutated line (`cached = 0 if cached is None else cached`). It reproduced E1C (median
residual 9, max 41, no monotonicity violation), E2 (all six totals), E5 LR-04 (all twelve totals
and the 4/8 identical per-check map), the 765-call total, and Duval's 0-line porcelain. It
rejected four phrases that this report previously contained — container uptime "16 h
throughout", "no verified success anywhere", "48 calls" for E1, and a probe count of 5 — and all
four are corrected above. Its verdict is `partial`, with two open items: the held-out LR-01 arms
(§ below) and the absence of a second restore-key snapshot.
