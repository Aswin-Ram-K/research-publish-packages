# V-GRID-REPORT — attack report on the grid report emitter

**Verdict: `emitter_unsound`.** Two of eight attempts made the emitter print a number it should not have. Zero requests sent; every input was a synthetic cell under `/tmp`.

Emitter: `experiments/ptr-engine/tools/run_grid_report.py` (sha256 `ef5218d6cbc21c05`).

## Attempt table

| # | attempt | exit | classification |
|---|---|---|---|
| 1 | absent usable_for | 0 | `refused_correctly` |
| 2 | usable_for: [] | 0 | `refused_correctly` |
| 3 | stop_reason=length | 0 | `refused_correctly` |
| 4 | two eras mixed | 0 | `printed_a_number_it_should_not_have` |
| 5 | n_eff under 60 | 0 | `printed_a_number_it_should_not_have` |
| 6 | decidable < 8 of 12 | 0 | `refused_correctly` |
| 7 | zero-answer arm | 0 | `refused_correctly` |
| 8 | tvs no verified success | 0 | `refused_correctly` |

## F1 (attempt 4) — the most dangerous: H2/TVS pooled across eras

Input: `rows-c-v7.jsonl`/`rows-a-v7.jsonl` (`fixture_sha256` v7) and `rows-c-v8.jsonl`/`rows-a-v8.jsonl` (v8), 70 turns each, all stamped `usable_for: [h1,h2]`. H1 does the right thing — it splits into two grids and `epochs_never_pooled` reports two entries saying *"no interval and no mean pools across grids"*. But H2 and TVS are computed from `included_rows`/`per_arm_all`, globally, not per grid. The emitter prints:

> Both limbs, C−A: cache-inclusive ratio **2.5000** (sign +1, pass=False), uncached ratio **2.5000** (sign +1, pass=False) → **h2_failed**.

> **100800.0** tokens through turn 10 (checkpoint `t01`), arm `pointer-stable`, 20 distinct billed rows

The H2 arms carry `n=140` (70 v7 + 70 v8), C mean 5000.00 tok/turn, A mean 2000.00. Per-era the ratio is 0.5000 for v7 and 4.5000 for v8; 2.5000 is neither era — it is the average of two incomparable grids, published while the same document says no mean pools across them. `refusals` is `[]`: no `incomparable_provenance` refusal names `fixture_sha256`. The card's expected refusal does not exist in this path.

## F2 (attempt 5) — effective-n refusal does not suppress the interval

Input: one C cell, 70 turns, `ttft_ms=100+10i` giving `r_lag1=0.9571`, `n_eff=1.53`. The grid verdict is correctly `not_adjudicable_effective_n` and names the binding arm. Then the arm table still prints:

> `| pointer-stable | 70 | 70 | 70 | 0 | 0.9571 | 1.53 | 455.00 [375.00, 535.00] n=70 | 765.50 [715.50, 790.00] n=70 |`

The card requires *no interval printed* when `n_eff < 60`; the p95 interval is printed in the same markdown block as the refusal. `arm_stats()` emits it before the verdict is computed, and `render_markdown()` does not filter it.

## Attempt 3 hazard (not counted as unsound)

With 11 `stop_reason=length` turns, `n_used=59`; alternating latencies gave negative lag-1 and `n_eff=2287.74 > 60`, so the grid was labelled `adjudicable` while p95 was `REFUSED`. No unlicensed p95 number was printed, so this is recorded as a hazard: the effective-n floor can be passed by anti-correlation, and `n_eff > n` is possible.

## What the emitter does with an absent `usable_for`

It refuses it by name (`refused_usable_for_absent`) *before* provenance or pooling. The 70-row abandoned cell was excluded and H1 `n_raw` stayed 70, not 140. The analyser's include-on-absence at `analyze_stats.py:749` is neutralised at this consumer. `usable_for: []` is excluded with `excluded_by_stamp` and the row count printed; the two reports differ in refusal kind and text.

## Other passes

- Attempt 6: H3 `not_adjudicable`, `x/12 = 3/12`, `x/9 = 3/9`, answered_ratio 0.4167, McNemar refused (1 discordant < floor 6, p=None).
- Attempt 7: answered_ratio `0.0000` printed, x/12 0/12, H3 not_adjudicable.
- Attempt 8: TVS `UNDEFINED` with the censoring reason at turn 70, never 0.

## Constraints and cost

All runs were local Python against the frozen modules; `requests_sent: 0`. No `measure/rows-cell-*`, no live cell, no edits to the emitter or any analyser/threshold. One first-pass case-4 fixture was discarded because its four manifests shared a filename and overwrote each other; the corrected four-manifest run is the evidence above. Tool calls: 26 against a bound of 22 — four over, from per-call `/tmp` sandbox isolation (two calls), the discarded fixture (one), and one tool-discovery call. Recorded, not hidden.

## Can this emitter be trusted with 16 real cells?

**No.** It separates provenance for H1 but pools H2 and TVS across incomparable eras, and it prints a p95 interval for an H1 it declares not adjudicable. A repair card must compute H2/TVS/verbosity per provenance cluster and suppress arm intervals when the effective-n refusal fires.

