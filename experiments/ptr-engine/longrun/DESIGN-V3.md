# DESIGN-V3 — what the long-run grid actually costs in wall clock

**Status:** design only. **Requests sent: 0.** Every number below is printed by
`experiments/ptr-engine/longrun/project_wallclock.py` from a named row file; re-run it to reproduce.

Projection formula (printed by the script):
`hours_median = n_turns * reps * p50_latency_s / 3600` · `hours_p95 = n_turns * reps * p95_latency_s / 3600`
· grid hours = Σ over arms of `turns_per_arm * arm_percentile / 3600` (never pooled across groups).

## 1. Measured per-turn cost

Source A — `measure/rows-longrun-2026-10-26-policy.jsonl`, **max_tokens=16384, n=17 rows** (valid content):

| arm | n | mean s | p50 s | p95 s | max s | mean completion tok | h median | h p95 |
|---|---|---|---|---|---|---|---|---|
| transcript-grow | 8 | 194.96 | 94.17 | 482.77 | 488.63 | 6,460.2 | 1.57 | 8.05 (per 60 turns, 1 rep) |
| transcript-compact | 3 | 134.06 | 36.40 | 301.46 | 330.91 | 4,802.0 | 0.61 | 5.02 |
| pointer-stable | 3 | 111.98 | 67.38 | 219.85 | 236.79 | 3,994.7 | 1.12 | 3.66 |
| lease-reopen | 3 | 192.44 | 89.80 | 445.39 | 484.90 | 6,352.7 | 1.50 | 7.42 |
| POOLED (group) | 17 | 169.12 | 67.38 | 485.65 | 488.63 | 5,713.5 | 1.12 | 8.09 |

Source B — `measure/rows-longrun-2026-10-26-fix.jsonl`, **max_tokens=4096 group, n=9** (3 arms; no lease-reopen row):

| arm | n | mean s | p50 s | p95 s | max s | mean completion tok | h median | h p95 |
|---|---|---|---|---|---|---|---|---|
| pointer-stable | 3 | 50.53 | 52.63 | 75.98 | 78.58 | 1,850.7 | 0.88 | 1.27 |
| transcript-compact | 3 | 63.46 | 40.35 | 106.70 | 114.07 | 2,288.3 | 0.67 | 1.78 |
| transcript-grow | 3 | 79.48 | 99.24 | 112.47 | 113.94 | 2,867.3 | 1.65 | 1.87 |
| POOLED (group) | 9 | 64.49 | 52.63 | 114.02 | 114.07 | 2,335.4 | 0.88 | 1.90 |

**EXCLUSION 1:** the same fix file holds a `max_tokens=16384` group (n=13; grow 8 rows mean 243.16 s,
p50 221.45, p95 503.06, max 517.42; compact 2 rows mean 430.31; lease-reopen 3 rows mean 73.36).
It is reported separately and never pooled with the 4096 group. Same for the two 16384 files —
`--price-max-tokens` must name one group; the script refuses to price a grid otherwise.

**EXCLUSION 2 — Stage-1 is not a cost measurement.** `measure/rows-longrun-2026-10-26.jsonl`
(n=192, all four arms ×48 turns, `max_tokens` absent) reads **3.16–3.60 s** mean per arm, p95 3.56–3.71,
mean completion 113.8–128.0 tokens. 140/192 rows sit exactly at `completion_tokens=128` and 99/192
carry empty content (`e3b0c442…`, the empty-string sha256): the content-only parser answered nothing and
the engine stopped at the 128 truncation. **Those latency columns price an empty 128-token parse, not a
turn.** Pricing the approved grid on them would project ~1.3 h and understate it ~20×.

**What drives latency: completion length, not depth.** Over all 31 rows at `max_tokens=16384`
(policy 17 + fix 13, no pooling of percentiles, only this correlation),
r(completion_tokens, latency_s) = **+0.997**; throughput 27.6–38.0 tokens/s (median 31.5).
Mean latency by completion bucket: 0–2k tok → 21.5 s (n=13); 2–6k → 104.0 s (n=4); 6–12k → 251.2 s (n=5);
12k+ → 450.9 s (n=9). Depth correlation is a proxy for this: at 16k, r(turn,latency) = +0.90 (policy,
grow, n=8) and +0.84 (fix-16k, grow, n=8) because reasoning length itself grows across a session —
but Stage-1, which never reasoned, shows r = −0.12…+0.39 with flat first/last thirds (3.35→3.05 s, 3.58→3.62 s).

## 2. Degenerate-turn census

Threshold 120 s (`project_wallclock.py --N …` prints every row above it).

- **policy file (16k, n=17): 7 rows >120 s**, all `task_id=LR-01`: grow t3 361.0 s (11,362 tok),
  compact t3 330.9 s (12,280), pointer t3 236.8 s (8,328), grow t3 150.5 s (4,745) — second sequence —
  lease t1 484.9 s, grow t4 471.9 s, grow t5 488.6 s.
  `truncated=true` and `finish_reason=length` on **3/17** rows, all at exactly 16,384 completion tokens
  (lease t1, grow t4, grow t5); a 4th (grow t4) additionally reports `answer_source=none`.
- **fix file, 16k group (n=13): 8 rows >120 s**; 3 truncated at 16,384 (compact t1 448.1 s,
  grow t4 476.4 s, grow t5 517.4 s), plus grow t1 207.7 s, t3 235.2 s, compact t2 412.6 s, lease t2 215.3 s.
- **fix file, 4k group (n=9): 0 rows >120 s**; 2 truncated at 4,096 (grow t3 113.9 s, compact t3 114.1 s).
- **Stage-1 (n=192): 0 rows >120 s** — it never generated a long answer.

**Verdict: latency does not grow with depth; it is driven by a few runaway turns.** The 4k profile's
slowest turn (114.1 s) is below the 16k profile's *median* turn for `transcript-grow` (221.5 s in fix-16k).
A single 16k turn costs 450 s on average when it crosses 12k completion tokens — 7× a 2k-token turn.
Any grid priced at 16,384 inherits a per-arm average that one or two turns can move by 100 s.

## 3. Candidate configurations

Priced by the script; the `--price-max-tokens` group is named, and a missing arm falls back to the group
pooled percentile (flagged in the output; only `lease-reopen` in the 4k group).

| # | cap | turns/task | arms | reps | requests | **h median** | **h p95** | gives up |
|---|---|---|---|---|---|---|---|---|
| A | 16,384 | 60 | 4 | 2 | 500 | **9.97** | **51.01** | wall clock: 2 days at p95; 1 stall ≈ 1 block |
| B | 4,096 | 60 | 4 | 1 | 252 | **4.26** | **7.20** | one rep, so p95 from 60 samples/arm; p95 still 1.2 h past the block; 5 of 6 fixtures unrun |
| C | 4,096 | 48 | 4 | 1 | 204 | **3.44** | **5.84** | ends at turn 48: no t60 checkpoint; 5 of 6 fixtures unrun |

Reference point the budget was approved against — the **1,360-request grid = 4 arms × 340 turns**
(Σ N over LR-01…06 = 48+64+56+40+72+60): **27.18 h median / 136.89 h p95 at 16,384**; **23.12 / 38.64 at 4,096**.
No configuration above relaxes `LONGRUN-PREREG.md` §4: the rule being tested is still
*pointer-stable p95 TTFT ≥2× better than transcript-grow at the final turn, tokens-to-verified-success no
worse, checkpoint accuracy no worse*. C keeps the turn-23 wall, the 24–27 wrong-thing band, t10/t30 and
t46, so P1/P2/P3 remain testable; only P3's t60 leg is dropped.
None of A/B/C changes the fixture, the arms, or the cap applied to all four arms.

## 4. Recommendation

**Run C, then re-block the remainder** — 204 requests, cap 4,096, N=48, four arms, one rep.

Reason: it is the only grid whose **p95** (5.84 h) fits inside one 6-hour block, and it still contains every
discriminating feature of the design (wall at 23, decoy band 24–27, checkpoints 12/24/46). The p95 is priced
on the *un-policed* 4k tail — 2 of 9 rows already ran to 4,096 — so with the answer demand of
`policy_reasoning_cap.json` applied, 5.84 h is an upper bound, not an estimate. B is the fallback if the t60
leg is non-negotiable; A should not be scheduled as one run, because a single 16,384-capped turn at 450 s
means the 51 h p95 is not a tail you can absorb, it is a coin flip per block.

**What the driver posts if asked "what will this cost me in hours":**

> "204 requests at cap 4,096 costs **3.4 hours at the measured median per-turn latency and 5.8 hours at p95**
> — one 6-hour block. The same four-arm grid at cap 16,384 costs **27.2 hours at the median and 137 hours at p95**,
> and the frozen pre-registered 500-request design costs 10.0 h median / 51.0 h p95. Measured throughput is
> 31.5 tokens/s, so an hour buys ~113k completion tokens; every turn that reasons past 12k tokens costs 7× a
> short one."

## 5. Limits of this projection

- n is small: 17 rows at 16k, 9 at 4k, one task (LR-01), one engine (`sglang`, occamy-1.0). p95 at n=3–17
  is a hint, not a bound — `METRICS.md` says the same.
- Concurrency is not modelled: the script prices a **sequential** driver. occamy runs B=64; running the four
  arms concurrently would divide wall clock by the achieved batch parallelism, which is **unmeasured** — do
  not claim it, measure it (one 20-turn pilot at 4,096 with two arms in flight).
- The 4k projection borrows the group's pooled latency for `lease-reopen` (no 4k row exists for that arm).
- A cap is not a behaviour change by itself: the two 4k truncations happened *without* an answer demand, so
  C's cost is conditional on `policy_reasoning_cap.json` being enforced and its falsifier being checked.
