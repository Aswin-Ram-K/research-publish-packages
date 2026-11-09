# UNIT LATENCY-FIGURE-HONESTY

**Status:** done · **Bound:** 26 tool calls · **Used:** 30 (overran by 4 — cases e/f of the same test moved after case_d was fixed; one call proved a screen finding pre-existed)

**Purpose.** Make the latency record state what it can and cannot support, additively, and re-pin the one
test the artefact moved.

## Census facts this unit stands on (no recomputation of the census itself)

`orchestration/handoffs/TURN-CENSUS-60.json`: 0 of 15 rows files and 0 of 15 arm-by-file rows reach 60
usable turns; corpus maximum 48 turns per cell per arm; 48 x 0.05 = 2.4 < TAIL_MIN = 3, so a per-rep p95 is
inadmissible by arithmetic. `measure/GRID-CELL-SANITY.json` stamps both cells `usable_for: []`, the 27-row
cell with reason *"cell in progress: 27/48 turns on disk — a statistic computed now would be from a
truncated cell file."* Every rows file reports `definition_fallback: true` (no `kind='turn-initial'` row on
disk).

## 1. Recomputation before correction

Pinned rows file `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`,
sha256 `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1`, 27 lines.

| site | figure | verdict |
|---|---|---|
| `docs/RUNAWAY-POLICY.md:34` | `ttft_ms_p50 141.58` | **reproduces** — 27 selected, `fallback_rows: 27`, `explicit_initial_rows: 0`, 27 non-null `ttft_ms`, 25 `stop` + 1 `length` + 1 `runaway_turn`, `quantile_ci(0.50) = (141.58, 131.354, 166.378, 27)` |
| `docs/ANALYSIS-PATH.md:33` | `ttft_p50 n=27 141.58ms [131.35, 166.38]` | **reproduces** to printed precision; the current CLI now refuses the cell outright (`usable_for EXCLUDED … no usable cells`), so what reproduces is the arithmetic, not a runnable analyser table |
| `docs/ANALYSIS-CONSUMER.md:100` | `27 -> 25` | **reproduces as counts, not as labelled** — 27 turns selected; all **27** carry `ttft_ms`; `25 = 27 - 2 truncated` = the `stop_reason='stop'` count, so the column headed "rows with ttft" is off by two |

## 2. The caveat as added (identical stamp and sha at all three sites)

```
> **Dated caveat (2026-10-26) — `LATENCY-FIGURE-HONESTY`, the `ttft_ms_p50 141.58` figure in §2:** `experiments/ptr-engine/measure/GRID-CELL-SANITY.json` stamps this cell `usable_for: []` (reason: *"cell in progress: 27/48 turns on disk — a statistic computed now would be from a truncated cell file"*); the 60-turn census that consumed that stamp is `orchestration/handoffs/TURN-CENSUS-60.json` (unit `TURN-CENSUS-60`): **0 of 15** rows files and **0 of 15** arm-by-file rows reach 60 usable turns, the largest is **48**, so `n=27` gives `27 x 0.05 = 1.35 < TAIL_MIN = 3` and no p95 can exist here.
>
> Rows file this figure was computed on: `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`, sha256 `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1` (`wc -l` = 27).
>
> **What the number may still be used for:** nothing pooled and nothing comparative — it is one cell's legacy `kind='turn'` p50 (`definition_fallback: true`, see `docs/LATENCY-FALLBACK.md`), quoted only with its `n` and never beside another cell's value.
```

## 3. `docs/LATENCY-FALLBACK.md` — one line

No rows file on disk carries `kind='turn-initial'`, so every published latency figure is the legacy
`kind='turn'` selector under `definition_fallback: true`; the corrected turn definition is therefore
**forward-only**, and any figure produced before era B is a fallback figure. Linked from
`docs/LATENCY-REPORT.md` by one inserted line.

## 4. Test re-pin — old expectation · recomputed value · new expectation

| case | old expectation | recomputed | new expectation |
|---|---|---|---|
| (d) G8 | `p["point"] is not None`; `p["n"] == n_dedup` = **70** | selector 48 turns / 48 non-null ttft / 1 truncated; `n_turn_dedup` 46; **`ttft_used` 45** | `p["n"] == c["ttft_used"] == 45`, `point is None`, refused text contains `n=45` and `minimum n for p95 is 60`; both-count gate still publishable at 72/70 |
| (d) G9 | same shape, `n == n_dedup` = **61** | **`ttft_used` 37** | `p["n"] == 37`, refused at 37; gate publishable at 72/61 |
| (d) basis | `"not withdrawn" in withdrawal_basis` | artefact now prints `both counts clear the floor: n_raw=72, n_dedup=70 (floor 60)` | assert the recomputed counts appear, not the wording |
| (e) | 12 p50 cells, 9 bitexact | 11 cells carry a p50 point (11 of 24); 8 bitexact + 3 moved = 11 | 11 / 8 / 3 with the arithmetic asserted |
| (f) | 2 p95 values, 1 arm `pointer-stable` | 0 published p95, 2 refused (`cells_with_p95_raw`), arms `[]` | 0 published / 2 refused / 0 pairs |

**Artefact vs recomputation:** they agree on every number the artefact prints (45/37, 11 p50 points). They
disagree with the *census prose* on G8's "47 raw turns": the selector selects **48**, and 47 is the
untruncated count. Not silently adopted either way — recorded. Also recorded: the 48 → 46 turn
de-duplication cannot be re-derived from `content_sha256` distinctness (43), so it is the report tool's own
step.

`python3 experiments/ptr-engine/longrun/tests/test_latency_floor_policy.py` → exit 0, 6/6 PASS;
`LATENCY_FLOOR_POLICY=off` → exit 1, red-green preserved.

## 5. Consequence for the objective

With zero cells at `n ≥ 60`, what remains **quotable today** is: a per-cell **p50** with its `n` and its
interval (11 cells still carry one, and the era A `141.58 [131.35, 166.38] n=27` is one of them, on a
`usable_for: []` cell so it is evidence about that one truncated run and nothing else), **per-turn means and
counts** over the rows that exist (labelled `mean_ttft_ms_ADHOC` wherever they appear), row/stop-reason
census counts, and the **refusal messages themselves**, which are exact. What **cannot exist** in this
corpus is any per-cell **p95** (48 x 0.05 = 2.4 < 3 by arithmetic, not by shortage of effort), any **pooled
or comparative** statement across cells or arms, and any **non-fallback** latency figure at all. Those wait
for one artefact that does not exist on disk: the grid's **three reps pooled per arm on disk** (3 x 48 = 144
turns, 144 x 0.05 = 7.2 ≥ 3, enough for a p95 with an honest interval), written by an era-B writer that
emits `kind='turn-initial'`.

## 6. Pre-existing failures recorded, not fixed (outside this unit's write paths)

`python3 -m pytest experiments/ptr-engine/longrun/tests experiments/ptr-engine/tests -q` → **13 failed, 824
passed**. The re-pinned file is green. `docs/RUNAWAY-POLICY.md` shows 2 `WI-014` findings in
`tools/withdrawn_index.py`, **identical with and without this unit's inserted block** (verified by stripping
the block into `/tmp/rp_pre.md`), because the file is new since the frozen screen baseline. The my-other-edits
files scan clean (0 findings, strict and non-strict).
