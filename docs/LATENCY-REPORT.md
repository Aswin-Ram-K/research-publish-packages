# LATENCY-REPORT — p50 / p95 TTFT and tokens-to-verified-success, per grid

**Unit:** `LATENCY-UNDER-DISPUTE` (re-issue 3 of `LATENCY-REPORT`, supersedes `LATENCY-REPORT-2`) · **Generated:** 2026-10-26 · **Re-issued:** 2026-10-26 · **Live requests: 0** · **Network: none**  
**Analyser:** [`experiments/ptr-engine/longrun/analyze_stats.py`](experiments/ptr-engine/longrun/analyze_stats.py) sha256 `2d3d473a6269d8979baa6c159778af56c4372e88dadbf9a3261f7bfef97cb163`
**Machine-readable twin:** [`experiments/ptr-engine/measure/LATENCY-REPORT.json`](experiments/ptr-engine/measure/LATENCY-REPORT.json)
> **Fallback notice (2026-10-26, `LATENCY-FIGURE-HONESTY`):** every latency figure in this document is the legacy `kind='turn'` selector under `definition_fallback: true`, because no rows file on disk carries `kind='turn-initial'` — read [docs/LATENCY-FALLBACK.md](docs/LATENCY-FALLBACK.md) before quoting any of them.

This document assembles the latency half of the operator's comparison from row files that already exist.
It runs no cell, edits no row or grade file, and computes no quantile outside the official analyser.
**Re-issue 2 recomputes every cell on de-duplicated rows** (rule R, `TVS-REGRADE`); §“Re-issue 2” below lists
every figure that moved and every figure that was withdrawn. **Re-issue 3 derives no new quantile**: it adds the
both-count floor policy (§ below), labels the disputed de-duplication on every tool-grid p95, and leaves G7 withdrawn.
The quality half is reported per cell with its honest denominator, and `tokens_to_verified_success`
is reported as **NOT PRODUCED** because no grid has a defensible verified success to divide by.

**Analyser lines quoted throughout** (all in [`analyze_stats.py`](experiments/ptr-engine/longrun/analyze_stats.py)): `wilson_ci` :90 · `quantile_ci` :187 · `_insufficient_message` :175 · `ttft_values` :367 · `MIN_N` :72 · `TAIL_MIN` :71.

---

## Re-issue 3 — the both-count floor policy, and the rule the report stands on

**Policy (one line):** a cell's p95 is produced **only if `n_raw ≥ 60` and `n_dedup ≥ 60`**; otherwise it is refused
**by name with both counts quoted** — because rule R's justification failed verification
(`V-DUPLICATE-RULE`: `content_sha256` is `sha256(assistant content)`, a **response** hash, 869/869 rows at
`run_longrun.py:1493`), and a de-duplication whose basis is disputed must not be able to **raise** the evidence to
publication.

**Why both counts and not one.** `n_dedup` alone lets the disputed rule decide what is printable; `n_raw` alone lets a
duplicate-inflated count decide it. Only “both clear the floor” survives either reading of the dispute, and it is
strictly stronger than the previous `n_dedup ≥ 60` rule — so the floor was **not** lowered: the generator raises if any
cell publishes a p95 with either count below 60, and every refusal is the analyser's own text or the policy's, never a
quantile computed by hand.

| grid | n_raw | n_dedup | p95 verdict | p95 ms [95% CI] |
|---|---:|---:|---|---|
| G7 V4-TOOLS `pointer-stable` | 68 | 51 | **WITHDRAWN** — 51 < 60, refused by name | — (the withdrawn published figure was `318.14 [235.00, 526.41] n=68`) |
| G8 V5-TOOLS `pointer-stable` | 72 | 70 | **PUBLISHED** — both counts ≥ 60 | `397.41 [273.84, 659.70] n=70` |
| G9 V6-TOOLS `pointer-stable` | 72 | 61 | **PUBLISHED** — both counts ≥ 60 | `429.70 [318.80, 477.06] n=61` |

> **Correction (2026-10-26) — `LATENCY-REDERIVE-TRUNCATED`:** the three verdicts above are **superseded** by the section
> “Correction (2026-10-26)” before §1. With truncated turns excluded **and** the per-turn TTFT definition applied, the
> tool-grid p95 samples are n=30 / 45 / 37, so **G8 and G9 are withdrawn too** and the project publishes **0 p95 values**.
> The old verdicts and numbers remain printed here, undeleted.

All three cells carry, in `measure/LATENCY-REPORT.json`, `dedup_rule_status: "disputed (V-DUPLICATE-RULE fail: response
hash, not request identity)"`, `n_raw`, `n_dedup` and `withdrawal_basis`, so a reader sees the number is **conditional**
without opening the card.

**What the disputed 30 rows can and cannot do.** If the 30 rows are double-writes, G7's true n is **51** and its p95 is
**unmeasurable** at the current corpus. If they are genuine requests, its n is **68** and the p95
`318.14 [235.00, 526.41]` **stands**. The measurement that decides it is a **`request_sha256` on future rows**, or a
**writer-level double-append proof** — both owned by `DEDUPE-ROOT-CAUSE`. Until one lands, the **withdrawn** reading is
the one to quote.

> **Correction (2026-10-26):** the `318.14 [235.00, 526.41] n=68` in the paragraph above is **withdrawn** —
> register entry `WI-004` in `experiments/ptr-engine/measure/WITHDRAWN.json`: the de-duplicated sample is 51,
> below the n>=60 order-statistic floor for p95 (n*(1-q)=2.6 < 3), so no lower-n estimate replaces it and the
> analyser refuses the cell by name (`measure/LATENCY-REPORT.json` `p95_withheld`; :35, :90, :100 and :316 of
> this file already say WITHDRAWN). "Stands" is superseded: the citable reading is **withdrawn**, pending a
> `request_sha256` proof of the disputed 30 rows (`DEDUPE-ROOT-CAUSE`).


**Not recomputed, because rule R cannot touch it.** **12** cells carry a p50; **9** are bit-identical to
`LATENCY-REPORT` (their files have zero excess). The **3** that moved sit on the only three files rule R touched — G7
202.22 → **198.72 [166.05, 206.66] n=51**, G8 145.45 → **143.91 [140.23, 151.95] n=70**, G9 158.19 →
**147.59 [144.26, 168.07] n=61** — and each remains above the p50 floor `n ≥ 20` under **both** counts (smallest raw
68, smallest de-duplicated 51). The **G4 (RUN-C-V2) four-arm p50 table is untouched**: 4 arms × **48 raw = 48
de-duplicated** rows, **0** removed, every p50 identical. No quality block, comparison, ledger figure or TVS figure is
recomputed here; they have owners.

**One number for the operator.** After this policy the project has **2 p95 values**, in **2 grids**, in **1 arm**
(`pointer-stable`, tools ON) — both **single-arm** grids, so **0 arm-versus-arm p95 differences** and
`any_inter_arm_comparison: false`. The 8 comparison rows are G4/G5/G6 **p50-only** (`p95_available_both: false`). A
latency comparison *between arms* is still **not produced**; what exists is two within-arm p95 descriptions of
conditional standing.

**Field note — `cells_with_p95_raw` is not a refusal count.** `p95_inventory.cells_with_p95_raw` in `measure/LATENCY-REPORT.json` (written at `experiments/ptr-engine/tools/latency_report.py:672-674`) counts the cells of the **prior** `LATENCY-REPORT` artefact that carry a p95 point — the "before" for `p95_inventory.cells_with_p95` ("after") — so a `0` there means *no cell of the previous artefact published a p95*, never *no cell was refused*: refusals are what `cells_with_p95 = 0` says against `cells_with_p50 = 11` of 24 cells, and each is named in `p95_withheld`.

---

## Re-issue 2 — what changed and why (de-duplicated rows)

`TVS-REGRADE` measured **30 defensible duplicate request rows** across the 14 rows files: rule R, i.e. two rows are
duplicates iff they share `(ts, content_sha256, prompt_tokens, completion_tokens)` **within one file**, first occurrence
kept (source: `orchestration/handoffs/TVS-REGRADE.json` → `duplicate_rows.rule`; `measure/DUPLICATE-ROWS.md` §1 Rule R
— the two agree, so there is no rule conflict to report). Those duplicates are second writes of **one** response by the
tool-calling writer, so every duplicate row is a second copy of a single latency measurement.

**Where the rule applies, and where it cannot.** R is applied only to files whose every row carries a non-empty
`content_sha256` **and** a millisecond `ts`: `decided` on **11** of the 14 files. The other **3** files
(`rows-baseline-2026-10-26.jsonl` 105 rows, `rows-equalinfo-2026-10-26.jsonl` 100, `rows-live-2026-10-26.jsonl` 27 =
**232 rows**) are the legacy schema — no `content_sha256`, one-second `ts_utc` — where the literal tuple collapses rows
that are demonstrably distinct requests (different `rep`, different `latency_s`). Their status is **`not_applicable`**,
excess forced to **0**, and they are **not** de-duplicated.
*Discrepancy stated plainly:* the brief and `DUPLICATE-ROWS.md` §1 both say "five legacy files", but both the measured
schema and `DUPLICATE-ROWS.md`'s own §2 table show **three**; the 232 legacy rows reproduce exactly, so the file count,
not the row count, was mis-stated. Recorded here rather than silently adopted.

Ledger effect (**cited, owned elsewhere, not re-derived here**): `REQUEST-LEDGER` raw **1,101 → 1,071** (−30) is
`REQUEST-LEDGER-2`'s figure. This report only re-uses the same 30-row exclusion.

### Figures that moved (old beside new)

| cell | n raw → de-duplicated | p50 ms — old → new | p95 ms — old → new |
|---|---|---|---|
| G7 V4-TOOLS `pointer-stable` | 68 → **51** (48→31 turn, 20→20 follow-up) | 202.22 [172.86, 207.55] n=68 → **198.72 [166.05, 206.66] n=51** | **318.14 [235.00, 526.40] n=68 → WITHDRAWN** (refused at n=51) |
| G8 V5-TOOLS `pointer-stable` | 72 → **70** (48→46 turn, 24→24 follow-up) | 145.45 [140.74, 153.64] n=72 → **143.91 [140.23, 151.95] n=70** | 433.19 [284.48, 659.70] n=72 → **397.41 [273.84, 659.70] n=70** |
| G9 V6-TOOLS `pointer-stable` | 72 → **61** (48→37 turn, 24→24 follow-up) | 158.19 [146.19, 200.61] n=72 → **147.59 [144.26, 168.07] n=61** | 435.27 [346.51, 529.89] n=72 → **429.70 [318.80, 477.06] n=61** |

Also moved inside those three cells (AD HOC, no interval): mean TTFT 205.59 → 197.69 / 188.47 → 185.12 / 213.40 → 205.91 ms;
prompt tokens 289346 → 216951 / 387480 → 372095 / 356740 → 296275; completion tokens 9709 → 8229 / 12302 → 10715 /
12615 → 11105. **No other cell moved**: the remaining 21 cells sit on files with zero excess.

### Figures withdrawn

- **G7 V4-TOOLS, `pointer-stable`, p95 = `318.14 [235.00, 526.40] n=68` — WITHDRAWN (duplicate-inflated n, and a
  disputed de-duplication rule — §Re-issue 3).**
  17 of that n=68 were duplicate mirrors of rows already counted, so the de-duplicated n is **51** and the analyser
  refuses p95 by name: `refusing p95 at n=51: the 95% order-statistic span is ranks 46-51 (p90.2-p100.0) and n*(1-q)=2.6 < 3; minimum n for p95 is 60`.
  The value is **not replaced** by a smaller-n estimate and not quietly re-pointed: it is withdrawn. Its basis is now doubly explicit: the both-count floor policy refuses it on `n_dedup = 51` **and**
  rule R's own justification is disputed, so the withdrawal is the reading to quote under either account. This is the exact
  defect the hint named — the cell reached the `n ≥ 60` floor only by counting the same measurement twice.
- No other figure is withdrawn. G8 and G9 keep a p95 *because their de-duplicated n still reaches the floor*; their
  numbers are **recomputed**, not withdrawn.

### The floor was not lowered

`analyze_stats.min_n_for(0.95)` is **60** and is read from the module (`TAIL_MIN` :71, `MIN_N` :72) — unchanged, and
this report raises rather than prints any p95 whose n is below it or any p95 without interval *and* n.

### What survives, stated as evidence

After de-duplication this project has **two** p95 values, **both in one arm's tool grids** (`pointer-stable`, tools ON),
with **overlapping intervals**: G8 **397.41 [273.84, 659.70] n=70** and G9 **429.70 [318.80, 477.06] n=61**. Both carry
`dedup_rule_status: "disputed (V-DUPLICATE-RULE fail: response hash, not request identity)"` beside `n_raw 72` /
`n_dedup 70` and `72` / `61` — conditional on a disputed rule, not certified by it — and both are
single-arm grids, so they license no arm-versus-arm p95 difference; `pairs_with_p95` stays **0**. And because the
surviving n counts **requests** (turn + tool-follow-up rows with a TTFT), not turn rows alone, the de-duplicated
**turn** counts are 46 (G8) and 37 (G9) — an honest reader should carry that with the number.

---

## 0. The one-screen table

`n` is **turn rows only**; `req` is every request the cell wrote (turn rows + `tool-followup` rows), because a follow-up request has its own TTFT. `used` is the `n` the analyser actually took, after dropping null / non-finite / `ttft_source = "unavailable"` values (`ttft_values`, :367). **On this re-issue every count is the de-duplicated count**; for the three cells whose file carried duplicates the raw count is shown as `raw → de-duplicated`. A `REFUSED` p95 is the analyser's own refusal, not a gap I filled.

| grid | arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | quality_status | comparable-with (same grid) |
|---|---|---:|---:|---:|---|---|---|---|
| G1 stage1 | `lease-reopen` | 48 | 48 | 0 | REFUSED (n=0) | REFUSED (n=0) | measured 0/3 | pointer-stable, transcript-compact, transcript-grow |
| G1 stage1 | `pointer-stable` | 48 | 48 | 0 | REFUSED (n=0) | REFUSED (n=0) | undecidable | lease-reopen, transcript-compact, transcript-grow |
| G1 stage1 | `transcript-compact` | 48 | 48 | 0 | REFUSED (n=0) | REFUSED (n=0) | measured 0/3 | lease-reopen, pointer-stable, transcript-grow |
| G1 stage1 | `transcript-grow` | 48 | 48 | 0 | REFUSED (n=0) | REFUSED (n=0) | undecidable | lease-reopen, pointer-stable, transcript-compact |
| G2 smoke-rp | `lease-reopen` | 3 | 3 | 3 | REFUSED (n=3) | REFUSED (n=3) | undecidable | pointer-stable, transcript-compact, transcript-grow |
| G2 smoke-rp | `pointer-stable` | 3 | 3 | 3 | REFUSED (n=3) | REFUSED (n=3) | undecidable | lease-reopen, transcript-compact, transcript-grow |
| G2 smoke-rp | `transcript-compact` | 3 | 3 | 3 | REFUSED (n=3) | REFUSED (n=3) | undecidable | lease-reopen, pointer-stable, transcript-grow |
| G2 smoke-rp | `transcript-grow` | 31 | 31 | 31 | 8800.75 [3204.15, 10377.45] n=31 | REFUSED (n=31) | undecidable | lease-reopen, pointer-stable, transcript-compact |
| G3 fix-smoke | `lease-reopen` | 3 | 3 | 3 | REFUSED (n=3) | REFUSED (n=3) | undecidable | pointer-stable, transcript-compact, transcript-grow |
| G3 fix-smoke | `pointer-stable` | 3 | 3 | 3 | REFUSED (n=3) | REFUSED (n=3) | undecidable | lease-reopen, transcript-compact, transcript-grow |
| G3 fix-smoke | `transcript-compact` | 5 | 5 | 5 | REFUSED (n=5) | REFUSED (n=5) | undecidable | lease-reopen, pointer-stable, transcript-grow |
| G3 fix-smoke | `transcript-grow` | 18 | 18 | 18 | REFUSED (n=18) | REFUSED (n=18) | undecidable | lease-reopen, pointer-stable, transcript-compact |
| G4 RUN-C-V2 | `lease-reopen` | 48 | 48 | 48 | 134.96 [132.50, 136.98] n=48 | REFUSED (n=48) | measured 0/3 | pointer-stable, transcript-compact, transcript-grow |
| G4 RUN-C-V2 | `pointer-stable` | 48 | 48 | 48 | 167.02 [163.26, 168.33] n=48 | REFUSED (n=48) | measured 1/3 | lease-reopen, transcript-compact, transcript-grow |
| G4 RUN-C-V2 | `transcript-compact` | 48 | 48 | 48 | 202.49 [198.74, 206.49] n=48 | REFUSED (n=48) | measured 0/3 | lease-reopen, pointer-stable, transcript-grow |
| G4 RUN-C-V2 | `transcript-grow` | 48 | 48 | 48 | 482.24 [410.55, 556.41] n=48 | REFUSED (n=48) | measured 0/3 | lease-reopen, pointer-stable, transcript-compact |
| G5 V3 | `pointer-stable` | 48 | 48 | 48 | 167.49 [162.85, 176.21] n=48 | REFUSED (n=48) | measured 0/3 | transcript-grow |
| G5 V3 | `transcript-grow` | 48 | 48 | 48 | 200.65 [178.63, 204.45] n=48 | REFUSED (n=48) | measured 0/3 | pointer-stable |
| G6 V4 | `pointer-stable` | 48 | 48 | 48 | 187.90 [181.90, 191.63] n=48 | REFUSED (n=48) | measured 1/3 | transcript-grow |
| G6 V4 | `transcript-grow` | 48 | 48 | 48 | 199.79 [196.27, 202.40] n=48 | REFUSED (n=48) | measured 0/3 | pointer-stable |
| G7 V4-TOOLS | `pointer-stable` | 31 | 68 → **51** | 51 | 198.72 [166.05, 206.66] n=51 | **REFUSED (n=51) — 318.14 [235.00, 526.40] n=68 WITHDRAWN** | measured 1/3 | — (single arm) |
| G8 V5-TOOLS | `pointer-stable` | 46 | 72 → **70** | 70 | 143.91 [140.23, 151.95] n=70 | 397.41 [273.84, 659.70] n=70 | measured 0/3 | — (single arm) |
| G9 V6-TOOLS | `pointer-stable` | 37 | 72 → **61** | 61 | 147.59 [144.26, 168.07] n=61 | 429.70 [318.80, 477.06] n=61 | measured 2/3 | — (single arm) |
| G10 CELL-145758Z | `pointer-stable` | 6 | 6 | 6 | REFUSED (n=6) | REFUSED (n=6) | not_graded | — (single arm) |

**Read the table this way:** after de-duplication a p95 number appears in exactly **2** of 24 cells, and both are **single-arm** grids (`G8`, `G9` — pointer-stable with tools on, the only arm ever run with tools). `G7`'s p95 is **WITHDRAWN**: its published n=68 counted 17 duplicate rows, and at the honest n=51 the analyser refuses it. Every grid that holds two or more arms has **n = 48 per arm**, where the analyser refuses p95 because `48 · (1−0.95) = 2.4 < 3` (`TAIL_MIN`, :71). Every tool-grid p95 here carries the dispute label and both counts in the JSON twin (§Re-issue 3). 

---

---

## Correction (2026-10-26) — truncated turns excluded, re-derived on the current analyser

**Unit:** `LATENCY-REDERIVE-TRUNCATED` · **offline:** zero requests, no network · **bounded:** 18 tool calls.
**Analyser:** [`experiments/ptr-engine/longrun/analyze_stats.py`](experiments/ptr-engine/longrun/analyze_stats.py) sha256 `800c8f6c2a483895febbe1bdc1a946408d6d4d01bdb7c1accda83d70364cdf6c`
(the header above quotes sha256 `2d3d473a…`, the analyser that produced the old figures; this section is the current one).
**This section is additive.** Every figure it names stays legible above and is **not deleted**. Where it says “superseded”,
the old number remains printed and the corrected number stands beside it.

### Two measured causes, kept separate

- **(T) truncated turns excluded** — `truncated-turns/1` drops every turn with `truncated: true` from **p50 and p95**.
  The floor is untouched: `min_n_for(0.95)` is still **60** (`TAIL_MIN` :71, `MIN_N` :72), and the bootstrap, seed, resample
  count and every threshold are unchanged.
- **(D) the per-turn TTFT definition** — `ttft-definition/1` takes **one row per turn** (`kind='turn-initial'`, else the
  legacy `kind='turn'` row, `definition_fallback: true`); a `kind='tool-followup'` row is a request **inside** a turn and is
  never a turn's latency. The published n on G7/G8/G9 counted **requests** (turn + follow-up rows), which the current
  analyser does not.

**(D) is why this correction is larger than the unit card predicted.** The card's arithmetic — `51 → 50`, `70 → 69`, `72/61`
unchanged — is correct for **request counts only**. The current analyser prints **turn-row counts**, so the measured p95 n is
**30 / 45 / 37** for G7 / G8 / G9, and **all three tool-grid p95s are refused**, G8 and G9 included. The prediction is
recorded as a prediction that did not reproduce; it is not adopted.

### Commands (quoted exactly, one invocation per grid)

```
cd experiments/ptr-engine && python3 longrun/analyze_stats.py --rows measure/rows-longrun-v4-tools-2026-10-26.jsonl --json /tmp/g7.json
cd experiments/ptr-engine && python3 longrun/analyze_stats.py --rows measure/rows-longrun-v5-tools.jsonl            --json /tmp/g8.json
cd experiments/ptr-engine && python3 longrun/analyze_stats.py --rows measure/rows-longrun-v6-tools.jsonl            --json /tmp/g9.json
cd experiments/ptr-engine && python3 longrun/analyze_stats.py --rows measure/rows-cell-pointer-stable-20261026T182535Z.jsonl
```

**On the raw rows** (turn selection on, no de-duplication) the three tool grids print:

- G7: `truncated_turns  excluded=1 of 48 selected turn(s)  fraction=2.1%  from the latency quantiles (p50 and p95)  surviving n=47` · `ttft_p50 n=47  201.64ms [169.52, 208.44]` · `ttft_p95  REFUSED at n=47  refusing p95 at n=47: the 95% order-statistic span is ranks 42-47 (p89.4-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`
- G8: `truncated_turns  excluded=1 of 48 selected turn(s)  fraction=2.1% … surviving n=47` · `ttft_p50 n=47  139.43ms [134.60, 142.46]` · p95 refused at n=47 (same refusal text).
- G9: `turns selected=48` · `ttft_p50 n=48  144.81ms [143.49, 149.52]` · `ttft_p95  REFUSED at n=48  refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60` — **0 truncated turns**, so G9's move comes from (D) alone.

**On the de-duplicated rows the JSON twin publishes** (`tools/latency_report.py`, rule R unchanged, one analyser call per grid)
the p95 samples are `n=30` / `n=45` / `n=37`, and the analyser's own refusals are:

- G7 — `refusing p95 at n=30: the 95% order-statistic span is ranks 27-30 (p90.0-p100.0) and n*(1-q)=1.5 < 3; minimum n for p95 is 60`
- G8 — `refusing p95 at n=45: the 95% order-statistic span is ranks 41-45 (p91.1-p100.0) and n*(1-q)=2.3 < 3; minimum n for p95 is 60`
- G9 — `refusing p95 at n=37: the 95% order-statistic span is ranks 33-37 (p89.2-p100.0) and n*(1-q)=1.9 < 3; minimum n for p95 is 60`

### Old figure → corrected figure, for every cell whose numbers moved

12 of 24 cells move. Cells that do **not** move (bit-identical p50 and p95): G1 `lease-reopen`, G1 `pointer-stable`, G1 `transcript-compact`, G1 `transcript-grow`, G2 `pointer-stable`, G2 `transcript-compact`, G3 `lease-reopen`, G3 `pointer-stable`, G4 `transcript-compact`, G4 `transcript-grow`, G5 `transcript-grow`, G6 `transcript-grow`.
`n` is the analyser's used sample (`p50.n`); the de-duplicated request count on the tool grids (G7 51, G8 70, G9 61) is
unchanged and is now **not** the sample a p95 is computed from.

| cell | n old → new | p50 ms — old → new | p95 ms — old → new | status |
|---|---|---|---|---|
| G2 smoke-rp `lease-reopen` | 3 → **2** | REFUSED → **REFUSED** | REFUSED → **REFUSED** | figures move; verdict unchanged |
| G2 smoke-rp `transcript-grow` | 31 → **12** | 8800.748 [3204.146, 10377.454] n=31 → **REFUSED** | REFUSED → **REFUSED** | **p50 WITHDRAWN** (new n < 20) |
| G3 fix-smoke `transcript-compact` | 5 → **2** | REFUSED → **REFUSED** | REFUSED → **REFUSED** | figures move; verdict unchanged |
| G3 fix-smoke `transcript-grow` | 18 → **7** | REFUSED → **REFUSED** | REFUSED → **REFUSED** | figures move; verdict unchanged |
| G4 RUN-C-V2 `lease-reopen` | 48 → **34** | 134.964 [132.498, 136.977] n=48 → **136.174 [132.498, 137.725] n=34** | REFUSED → **REFUSED** | figures move; verdict unchanged |
| G4 RUN-C-V2 `pointer-stable` | 48 → **47** | 167.020 [163.259, 168.327] n=48 → **166.957 [163.259, 168.327] n=47** | REFUSED → **REFUSED** | figures move; verdict unchanged |
| G5 V3 `pointer-stable` | 48 → **47** | 167.493 [162.848, 176.207] n=48 → **168.268 [162.879, 176.454] n=47** | REFUSED → **REFUSED** | figures move; verdict unchanged |
| G6 V4 `pointer-stable` | 48 → **40** | 187.898 [181.895, 191.629] n=48 → **187.809 [180.184, 191.822] n=40** | REFUSED → **REFUSED** | figures move; verdict unchanged |
| G7 V4-TOOLS `pointer-stable` | 51 → **30** | 198.723 [166.047, 206.660] n=51 → **159.526 [145.564, 206.115] n=30** | REFUSED → **REFUSED** | figures move; verdict unchanged |
| G8 V5-TOOLS `pointer-stable` | 70 → **45** | 143.915 [140.228, 151.955] n=70 → **137.514 [133.464, 141.807] n=45** | 397.411 [273.839, 659.703] n=70 → **REFUSED** | **p95 WITHDRAWN** (refused at new n) |
| G9 V6-TOOLS `pointer-stable` | 61 → **37** | 147.585 [144.258, 168.073] n=61 → **143.628 [142.601, 144.956] n=37** | 429.696 [318.804, 477.058] n=61 → **REFUSED** | **p95 WITHDRAWN** (refused at new n) |
| G10 CELL-145758Z `pointer-stable` | 6 → **5** | REFUSED → **REFUSED** | REFUSED → **REFUSED** | figures move; verdict unchanged |

### Withdrawal status of the three tools-on cells, stated once each

- **`G7` V4-TOOLS `pointer-stable` — WITHDRAWN, and stays withdrawn.** Refused at the old request count `n=51` (`refusing p95 at n=51: … n*(1-q)=2.6 < 3; minimum n for p95 is 60`) **and** at the current per-turn count `n=30` (`n*(1-q)=1.5 < 3`). Two independent bases, one floor: `60`. The floor did not move, so a smaller number cannot bring this cell back.
- **`G8` V5-TOOLS `pointer-stable` — now WITHDRAWN (was PUBLISHED at n=70).** Its published n counted **24 tool-follow-up requests** as latency measurements; under `ttft-definition/1` its turn-row sample is 46, minus one truncated turn = **45**, and the analyser refuses: `refusing p95 at n=45: … n*(1-q)=2.3 < 3; minimum n for p95 is 60`. The old `397.411 [273.839, 659.703] n=70` is **not replaced** — it is withdrawn.
- **`G9` V6-TOOLS `pointer-stable` — now WITHDRAWN (was PUBLISHED at n=61).** `0` truncated turns, so its move is cause (D) alone: 37 turn rows, refused by name — `refusing p95 at n=37: … n*(1-q)=1.9 < 3; minimum n for p95 is 60`. Old `429.696 [318.804, 477.058] n=61` withdrawn, not replaced.

### No figure was promoted

`cells_with_p95` **2 → 0**; `cells_with_p50` **12 → 11**; `arms_with_a_p95` **[]**; `grids_with_a_p95` **[]**;
`pairs_with_p95` **0**; `any_inter_arm_comparison` **false**. Every surviving p50 has `n` **lower than** its published n
(G4 48→34 and 48→47; G5 48→47; G6 48→40; G7 51→30; G8 70→45; G9 61→37), and the one p50 that existed on a thin sample
(G2 `transcript-grow`, `8800.748 [3204.146, 10377.454] n=31`) is **withdrawn** at `n=12`, below the 20 floor
(`refusing p50 at n=12: … minimum n for p50 is 20`). A correction may lower evidence, never raise it: nothing here raises any.

### Document totals, corrected

- **era A excluded by name.** `measure/rows-cell-pointer-stable-20261026T182535Z.jsonl` is stamped `usable_for: []` in
  `measure/GRID-CELL-SANITY.json` (27 rows). The analyser excludes it and refuses rather than printing an empty table:
  `usable_for EXCLUDED  … 27 row(s) NOT analysed  source=sanity  usable_for=[]  reason=(none recorded)` then
  `usable_for EXCLUDED every cell: no usable cells (…)` — **exit 1**, stderr
  `no usable cells: every input cell is stamped usable_for: [] -- refusing rather than printing an empty table as success`.
  (With `--no-census` the same file is included as *unstamped, not a certification* — that switch is why the stamp, not the file, decides.) The analyser's document total for the era-A + long-run pair is **`n_rows = 192`, not 219**.
- **Rows.** On disk now **15 files / 1,128 rows raw → 1,098 de-duplicated**; the era-A cell is
  inventoried (`feeds_grid: false`) and contributes **0** analysed rows. **Analysed: 1,101 raw → 1,071 de-duplicated** —
  the figure §7 prints, now labelled as *excluding era A*, not as the disk total.
- **Cells.** Still **24 cells in 10 grids**. p95-bearing cells **2 → 0**; p50-bearing cells **12 → 11**. The census also
  stamps the G10 cell `rows-cell-pointer-stable-20261026T145758Z.jsonl` `usable_for: []` (6 rows) — G10 already publishes
  no figure (all refused), so no published number changes, but its 6 rows are likewise not certifiable for any analysis.
- **Quality totals unchanged:** 92 declared cells, **13 measured / 10 undecidable / 1 not_graded** over the 24 cells
  (carried from `MATRIX-HONESTY`, owned elsewhere, not re-derived here).

### Superseded statements left in place above

- §Re-issue 3: “`G8` **PUBLISHED**”, “`G9` **PUBLISHED**”, and the `397.41 … n=70` / `429.70 … n=61` cells.
- §0 read-paragraph: “a p95 number appears in exactly **2** of 24 cells”, and the callout naming `G8`/`G9` as p95-bearing.
- §0 one-screen table: the G7/G8/G9 p50 and p95 cells, and the G2/G4/G5/G6/G10 p50 cells in the moved list above.
- §Re-issue 2 “Figures that moved” and “What survives” (both pre-correction), and §1's `p95`-floor paragraph remains true:
  the floor is still 60.
- “One number for the operator” (2 p95 values, 2 grids, 1 arm) is superseded by: **0 p95 values, 0 grids, 0 arms**, and
  therefore **no inter-arm p95 comparison**; the 8 comparison rows stay **p50-only** (`p95_available_both: false`).

## 1. Method, and why there is no pooled number anywhere in this document

A **grid** is `(fixture_sha256, tools on/off, harness era, arm)`. The rows on disk were produced by a harness that
changed underneath them: `ttft_s` only, then `ttft_ms`, then a client whose first-delta latch was fixed by
`WIRE-CLIENT` (`orchestration/units/WIRE-CLIENT.md`), then tool-channel runs, then a mid-cell version change.
A p95 pooled across those is a number about the harness history, not about an arm — the error this project keeps repeating.

So `analyze_stats.py` is invoked **once per grid** (`--rows <that grid's rows>`), which is the only way to use it
without its internal group-by-arm silently pooling grids that share an arm name:

```
python3 experiments/ptr-engine/longrun/analyze_stats.py --rows <grid rows> --json <out>   # x10 grids
```

Estimability is the analyser's, fixed in one place: `n ≥ 20` (`MIN_N`, :72) **and** `n·(1−q) ≥ 3` (`TAIL_MIN`, :71), which puts the first admissible p95 at **n = 60**. Where it refuses, the refusal text is reproduced verbatim in §3 — never replaced by a quantile I computed by hand.

`tokens_to_verified_success`, `mean TTFT`, and prompt/completion token totals are **not** outputs of `analyze_stats.py`.
Means and totals are marked **AD HOC** in §8 with their formula; they are description, not estimates, and carry no interval.

---

## 2. Rows, by cell

One subsection per grid. `used` is the analyser's n; `mean ms` is AD HOC (§8.4). Refusals are reproduced verbatim at
the end of each grid.

### G1 · stage1 — `rows-longrun-2026-10-26.jsonl`

fixture **fixture v2 72c3832d** · tools **off** · harness **pre-guard inline latch** · rows 192 (192 turn, 0 tool-followup) · window `2026-10-26T07:26:41.810Z` → `2026-10-26T07:39:07.122Z`

_max_tokens unset; ttft_ms absent on all 192 rows (ttft_s present on 93)_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `lease-reopen` | 48 | 48 | 0 | REFUSED n=0 | REFUSED n=0 | — | 8916 | 5463 | measured 0/3 |
| `pointer-stable` | 48 | 48 | 0 | REFUSED n=0 | REFUSED n=0 | — | 89396 | 5929 | undecidable |
| `transcript-compact` | 48 | 48 | 0 | REFUSED n=0 | REFUSED n=0 | — | 205309 | 5504 | measured 0/3 |
| `transcript-grow` | 48 | 48 | 0 | REFUSED n=0 | REFUSED n=0 | — | 133030 | 6144 | undecidable |

- **`lease-reopen` p50 refusal, verbatim:** `refusing p50 at n=0: the 95% order-statistic span is ranks 0-0 (p0.0-p0.0) and n*(1-q)=0.0 < 3; minimum n for p50 is 20`
- **`lease-reopen` p95 refusal, verbatim:** `refusing p95 at n=0: the 95% order-statistic span is ranks 0-0 (p0.0-p0.0) and n*(1-q)=0.0 < 3; minimum n for p95 is 60`
- **`pointer-stable` p50 refusal, verbatim:** `refusing p50 at n=0: the 95% order-statistic span is ranks 0-0 (p0.0-p0.0) and n*(1-q)=0.0 < 3; minimum n for p50 is 20`
- **`pointer-stable` p95 refusal, verbatim:** `refusing p95 at n=0: the 95% order-statistic span is ranks 0-0 (p0.0-p0.0) and n*(1-q)=0.0 < 3; minimum n for p95 is 60`
- **`transcript-compact` p50 refusal, verbatim:** `refusing p50 at n=0: the 95% order-statistic span is ranks 0-0 (p0.0-p0.0) and n*(1-q)=0.0 < 3; minimum n for p50 is 20`
- **`transcript-compact` p95 refusal, verbatim:** `refusing p95 at n=0: the 95% order-statistic span is ranks 0-0 (p0.0-p0.0) and n*(1-q)=0.0 < 3; minimum n for p95 is 60`
- **`transcript-grow` p50 refusal, verbatim:** `refusing p50 at n=0: the 95% order-statistic span is ranks 0-0 (p0.0-p0.0) and n*(1-q)=0.0 < 3; minimum n for p50 is 20`
- **`transcript-grow` p95 refusal, verbatim:** `refusing p95 at n=0: the 95% order-statistic span is ranks 0-0 (p0.0-p0.0) and n*(1-q)=0.0 < 3; minimum n for p95 is 60`


### G2 · smoke-rp — `rows-longrun-2026-10-26-policy.jsonl`

fixture **fixture v2 72c3832d** · tools **off** · harness **smoke-rp 0310Z..1130Z** · rows 40 (40 turn, 0 tool-followup) · window `2026-10-26T08:09:52.830Z` → `2026-10-26T11:52:48.974Z`

_max_tokens 16384; rows appended 08:09Z..11:52Z (mid-file drift)_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `lease-reopen` | 3 | 3 | 3 | REFUSED n=3 | REFUSED n=3 | 118.96 | 577 | 19058 | undecidable |
| `pointer-stable` | 3 | 3 | 3 | REFUSED n=3 | REFUSED n=3 | 144.39 | 4162 | 11984 | undecidable |
| `transcript-compact` | 3 | 3 | 3 | REFUSED n=3 | REFUSED n=3 | 203.94 | 6954 | 14406 | undecidable |
| `transcript-grow` | 31 | 31 | 31 | 8800.75 [3204.15, 10377.45] n=31 | REFUSED n=31 | 7135.94 | 1044736 | 340786 | undecidable |

- **`lease-reopen` p50 refusal, verbatim:** `refusing p50 at n=3: the 95% order-statistic span is ranks 1-3 (p33.3-p100.0) and n*(1-q)=1.5 < 3; minimum n for p50 is 20`
- **`lease-reopen` p95 refusal, verbatim:** `refusing p95 at n=3: the 95% order-statistic span is ranks 3-3 (p100.0-p100.0) and n*(1-q)=0.2 < 3; minimum n for p95 is 60`
- **`pointer-stable` p50 refusal, verbatim:** `refusing p50 at n=3: the 95% order-statistic span is ranks 1-3 (p33.3-p100.0) and n*(1-q)=1.5 < 3; minimum n for p50 is 20`
- **`pointer-stable` p95 refusal, verbatim:** `refusing p95 at n=3: the 95% order-statistic span is ranks 3-3 (p100.0-p100.0) and n*(1-q)=0.2 < 3; minimum n for p95 is 60`
- **`transcript-compact` p50 refusal, verbatim:** `refusing p50 at n=3: the 95% order-statistic span is ranks 1-3 (p33.3-p100.0) and n*(1-q)=1.5 < 3; minimum n for p50 is 20`
- **`transcript-compact` p95 refusal, verbatim:** `refusing p95 at n=3: the 95% order-statistic span is ranks 3-3 (p100.0-p100.0) and n*(1-q)=0.2 < 3; minimum n for p95 is 60`
- **`transcript-grow` p95 refusal, verbatim:** `refusing p95 at n=31: the 95% order-statistic span is ranks 28-31 (p90.3-p100.0) and n*(1-q)=1.6 < 3; minimum n for p95 is 60`


### G3 · fix-smoke — `rows-longrun-2026-10-26-fix.jsonl`

fixture **MIXED v2 72c3832d(27)+b7e303a6(2)** · tools **off** · harness **fix-smoke** · rows 29 (29 turn, 0 tool-followup) · window `2026-10-26T08:00:05.779Z` → `2026-10-26T09:39:20.637Z`

_max_tokens MIXED 4096(9)/16384(20)_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `lease-reopen` | 3 | 3 | 3 | REFUSED n=3 | REFUSED n=3 | 122.14 | 577 | 6817 | undecidable |
| `pointer-stable` | 3 | 3 | 3 | REFUSED n=3 | REFUSED n=3 | 124.17 | 4153 | 5552 | undecidable |
| `transcript-compact` | 5 | 5 | 5 | REFUSED n=5 | REFUSED n=5 | 820.76 | 27213 | 37306 | undecidable |
| `transcript-grow` | 18 | 18 | 18 | REFUSED n=18 | REFUSED n=18 | 1488.67 | 319991 | 114299 | undecidable |

- **`lease-reopen` p50 refusal, verbatim:** `refusing p50 at n=3: the 95% order-statistic span is ranks 1-3 (p33.3-p100.0) and n*(1-q)=1.5 < 3; minimum n for p50 is 20`
- **`lease-reopen` p95 refusal, verbatim:** `refusing p95 at n=3: the 95% order-statistic span is ranks 3-3 (p100.0-p100.0) and n*(1-q)=0.2 < 3; minimum n for p95 is 60`
- **`pointer-stable` p50 refusal, verbatim:** `refusing p50 at n=3: the 95% order-statistic span is ranks 1-3 (p33.3-p100.0) and n*(1-q)=1.5 < 3; minimum n for p50 is 20`
- **`pointer-stable` p95 refusal, verbatim:** `refusing p95 at n=3: the 95% order-statistic span is ranks 3-3 (p100.0-p100.0) and n*(1-q)=0.2 < 3; minimum n for p95 is 60`
- **`transcript-compact` p50 refusal, verbatim:** `refusing p50 at n=5: the 95% order-statistic span is ranks 1-5 (p20.0-p100.0) and n*(1-q)=2.5 < 3; minimum n for p50 is 20`
- **`transcript-compact` p95 refusal, verbatim:** `refusing p95 at n=5: the 95% order-statistic span is ranks 5-5 (p100.0-p100.0) and n*(1-q)=0.3 < 3; minimum n for p95 is 60`
- **`transcript-grow` p50 refusal, verbatim:** `refusing p50 at n=18: the 95% order-statistic span is ranks 6-14 (p33.3-p77.8) and n*(1-q)=9.0 < 3; minimum n for p50 is 20`
- **`transcript-grow` p95 refusal, verbatim:** `refusing p95 at n=18: the 95% order-statistic span is ranks 16-18 (p88.9-p100.0) and n*(1-q)=0.9 < 3; minimum n for p95 is 60`


### G4 · RUN-C-V2 — `rows-longrun-c-2026-10-26.jsonl`

fixture **0a07db1b** · tools **off** · harness **old inline latch** · rows 192 (192 turn, 0 tool-followup) · window `2026-10-26T09:36:45.966Z` → `2026-10-26T10:40:59.913Z`

_max_tokens 4096; 4 arms x 48 turns_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `lease-reopen` | 48 | 48 | 48 | 134.96 [132.50, 136.98] n=48 | REFUSED n=48 | 142.82 | 20628 | 65659 | measured 0/3 |
| `pointer-stable` | 48 | 48 | 48 | 167.02 [163.26, 168.33] n=48 | REFUSED n=48 | 189.21 | 104468 | 8936 | measured 1/3 |
| `transcript-compact` | 48 | 48 | 48 | 202.49 [198.74, 206.49] n=48 | REFUSED n=48 | 205.36 | 185617 | 1804 | measured 0/3 |
| `transcript-grow` | 48 | 48 | 48 | 482.24 [410.55, 556.41] n=48 | REFUSED n=48 | 507.65 | 901109 | 30455 | measured 0/3 |

- **`lease-reopen` p95 refusal, verbatim:** `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`
- **`pointer-stable` p95 refusal, verbatim:** `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`
- **`transcript-compact` p95 refusal, verbatim:** `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`
- **`transcript-grow` p95 refusal, verbatim:** `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`


### G5 · V3 — `rows-longrun-v3-2026-10-26.jsonl`

fixture **07abab0b (v3)** · tools **off** · harness **pre-guard** · rows 96 (96 turn, 0 tool-followup) · window `2026-10-26T10:54:46.137Z` → `2026-10-26T11:00:32.316Z`

_max_tokens 4096; grow+stable x48_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `pointer-stable` | 48 | 48 | 48 | 167.49 [162.85, 176.21] n=48 | REFUSED n=48 | 180.85 | 106294 | 7995 | measured 0/3 |
| `transcript-grow` | 48 | 48 | 48 | 200.65 [178.63, 204.45] n=48 | REFUSED n=48 | 200.68 | 171011 | 1113 | measured 0/3 |

- **`pointer-stable` p95 refusal, verbatim:** `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`
- **`transcript-grow` p95 refusal, verbatim:** `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`


### G6 · V4 — `rows-longrun-v4-2026-10-26.jsonl`

fixture **5a5f8c4b (v4)** · tools **off** · harness **pre-guard** · rows 96 (96 turn, 0 tool-followup) · window `2026-10-26T11:18:33.764Z` → `2026-10-26T11:40:56.509Z`

_max_tokens 4096; grow+stable x48_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `pointer-stable` | 48 | 48 | 48 | 187.90 [181.90, 191.63] n=48 | REFUSED n=48 | 198.12 | 195396 | 37646 | measured 1/3 |
| `transcript-grow` | 48 | 48 | 48 | 199.79 [196.27, 202.40] n=48 | REFUSED n=48 | 221.27 | 260564 | 1134 | measured 0/3 |

- **`pointer-stable` p95 refusal, verbatim:** `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`
- **`transcript-grow` p95 refusal, verbatim:** `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`


### G7 · V4-TOOLS — `rows-longrun-v4-tools-2026-10-26.jsonl`

fixture **a592a48f** · tools **ON** · harness **pre-guard** · rows **68 → 51 de-duplicated** (48→31 turn, 20→20 tool-followup; 17 duplicate rows removed, rule R `decided`) · window `2026-10-26T11:55:35.461Z` → `2026-10-26T12:05:28.579Z`

_max_tokens 4096; pointer-stable only; 48 turn + 20 tool-followup_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `pointer-stable` | 31 | 68 → **51** | 51 | 198.72 [166.05, 206.66] n=51 | **REFUSED (n=51)** | 197.69 | 216951 | 8229 | measured 1/3 |

- **`pointer-stable` p95 refusal, verbatim:** `refusing p95 at n=51: the 95% order-statistic span is ranks 46-51 (p90.2-p100.0) and n*(1-q)=2.6 < 3; minimum n for p95 is 60`
- **WITHDRAWN:** the previously published `318.14 [235.00, 526.40] n=68` is withdrawn as **duplicate-inflated n** — 17 of its 68 rows were duplicate mirrors of rows already counted. It is not replaced by a lower-n estimate; the analyser refuses the cell by name.
- `n=51` is **requests with a TTFT** (31 turn + 20 tool-follow-up rows), not 51 turn rows.



### G8 · V5-TOOLS — `rows-longrun-v5-tools.jsonl`

fixture **5bf5f639** · tools **ON** · harness **pre-guard** · rows **72 → 70 de-duplicated** (48→46 turn, 24→24 tool-followup; 2 duplicate rows removed, rule R `decided`) · window `2026-10-26T12:17:29.765Z` → `2026-10-26T12:24:37.760Z`

_max_tokens 4096; pointer-stable only; 48 turn + 24 tool-followup_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `pointer-stable` | 46 | 72 → **70** | 70 | 143.91 [140.23, 151.95] n=70 | 397.41 [273.84, 659.70] n=70 | 185.12 | 372095 | 10715 | measured 0/3 |

- **Superseded p95:** `433.19 [284.48, 659.70] n=72` → **`397.41 [273.84, 659.70] n=70`** (recomputed on de-duplicated rows; not withdrawn — n=70 still clears the floor).
- `n=70` is **requests with a TTFT** (46 turn + 24 tool-follow-up rows).



### G9 · V6-TOOLS — `rows-longrun-v6-tools.jsonl`

fixture **5bf5f639** · tools **ON** · harness **pre-guard + mid-cell version mix turns 1-6** · rows **72 → 61 de-duplicated** (48→37 turn, 24→24 tool-followup; 11 duplicate rows removed, rule R `decided`) · window `2026-10-26T13:16:13.529Z` → `2026-10-26T13:23:48.856Z`

_max_tokens 4096; fetch cap 3/turn; 48 turn + 24 tool-followup_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `pointer-stable` | 37 | 72 → **61** | 61 | 147.59 [144.26, 168.07] n=61 | 429.70 [318.80, 477.06] n=61 | 205.91 | 296275 | 11105 | measured 2/3 |

- **Superseded p95:** `435.27 [346.51, 529.89] n=72` → **`429.70 [318.80, 477.06] n=61`** (recomputed; n=61 clears the floor by **one** sample, so this p95 is named as fragile in the re-issue note above).
- `n=61` is **requests with a TTFT** (37 turn + 24 tool-follow-up rows).



### G10 · CELL-145758Z — `rows-cell-pointer-stable-20261026T145758Z.jsonl`

fixture **967cef03** · tools **off** · harness **post-WIRE-CLIENT client (ttft_source=first_delta)** · rows 6 (6 turn, 0 tool-followup) · window `2026-10-26T15:01:37.220Z` → `2026-10-26T15:17:04.891Z`

_max_tokens 16384; single cell, 6 turn rows_

| arm | n (turn) | req | used | p50 ms [95% CI] | p95 ms [95% CI] | mean ms (AD HOC) | prompt tok | completion tok | quality_status |
|---|---:|---:|---:|---|---|---:|---:|---:|---|
| `pointer-stable` | 6 | 6 | 6 | REFUSED n=6 | REFUSED n=6 | 373.66 | 24288 | 39827 | not_graded |

- **`pointer-stable` p50 refusal, verbatim:** `refusing p50 at n=6: the 95% order-statistic span is ranks 2-6 (p33.3-p100.0) and n*(1-q)=3.0 < 3; minimum n for p50 is 20`
- **`pointer-stable` p95 refusal, verbatim:** `refusing p95 at n=6: the 95% order-statistic span is ranks 5-6 (p83.3-p100.0) and n*(1-q)=0.3 < 3; minimum n for p95 is 60`

---

## 3. Comparability, stated pair by pair

**Within one grid, at p50 — the only quantity the analyser will license for a two-arm grid:**

| grid | pair | n per arm | p50 A | p50 B | difference (A−B) ms | intervals overlap? | p95 both? | difference interval |
|---|---|---:|---:|---:|---:|---|---|---|
| G4 RUN-C-V2 | `lease-reopen` vs `pointer-stable` | 48 / 48 | 134.96 | 167.02 | -32.06 | no | **no — both refused** | **NOT PROVIDED** |
| G4 RUN-C-V2 | `lease-reopen` vs `transcript-compact` | 48 / 48 | 134.96 | 202.49 | -67.53 | no | **no — both refused** | **NOT PROVIDED** |
| G4 RUN-C-V2 | `lease-reopen` vs `transcript-grow` | 48 / 48 | 134.96 | 482.24 | -347.28 | no | **no — both refused** | **NOT PROVIDED** |
| G4 RUN-C-V2 | `pointer-stable` vs `transcript-compact` | 48 / 48 | 167.02 | 202.49 | -35.47 | no | **no — both refused** | **NOT PROVIDED** |
| G4 RUN-C-V2 | `pointer-stable` vs `transcript-grow` | 48 / 48 | 167.02 | 482.24 | -315.22 | no | **no — both refused** | **NOT PROVIDED** |
| G4 RUN-C-V2 | `transcript-compact` vs `transcript-grow` | 48 / 48 | 202.49 | 482.24 | -279.75 | no | **no — both refused** | **NOT PROVIDED** |
| G5 V3 | `pointer-stable` vs `transcript-grow` | 48 / 48 | 167.49 | 200.65 | -33.16 | no | **no — both refused** | **NOT PROVIDED** |
| G6 V4 | `pointer-stable` vs `transcript-grow` | 48 / 48 | 187.90 | 199.79 | -11.90 | no | **no — both refused** | **NOT PROVIDED** |

Eight within-grid pairs exist, all at **n = 48 per arm**, and in every one the per-arm p50 intervals are disjoint.
That is a real, tool-blessed latency difference **at that grid**. It is not a p95 statement, it says nothing about
quality, and it does not transfer to any other grid. **No p95 difference interval exists anywhere in this report**, for
two independent reasons: the analyser refuses p95 at n = 48, and `analyze_stats.py` has no quantile-difference
routine at all (`wilson_ci` :90 is the only difference-capable function, and it is for proportions).

**Across grids — `NOT COMPARABLE`, with the differing axis named:**

| arms compared | verdict | the difference that forbids it |
|---|---|---|
| `transcript-grow` in G4 vs G5 vs G6 | **NOT COMPARABLE** | fixture `0a07db1b` vs `07abab0b` (v3) vs `5a5f8c4b` (v4); p50 moves 482.24 → 200.65 → 199.79 ms across fixtures, which is the fixture difference, not the arm |
| `pointer-stable` in G4 vs G5 vs G6 | **NOT COMPARABLE** | same three fixtures; p50 167.02 → 167.49 → 187.90 ms |
| G4/G5/G6 vs G7/G8/G9 | **NOT COMPARABLE** | tools **off** vs tools **on**, plus G7/G8/G9 are different fixtures again (`a592a48f`, `5bf5f639`) |
| G8 vs G9 | **NOT COMPARABLE** | same fixture `5bf5f639`, both tools on, but G9 carries a **mid-cell version mix in turns 1–6** and a different fetch cap (`fetch_rounds_cap_per_turn = 3`); the harness changed between them, so this is the exact case a pooled p95 would smear |
| G7 vs G8/G9 | **NOT COMPARABLE** | different fixture (`a592a48f` vs `5bf5f639`) |
| G2/G3 vs anything | **NOT COMPARABLE** | smoke grids: `max_tokens` 16384 in G2, **mixed 4096(9)/16384(20) inside G3's single file**, and G3 also mixes two fixtures (`72c3832d` 27 rows + `b7e303a6` 2 rows) |
| G1 vs everything after it | **NOT COMPARABLE** | G1 predates `HARNESS-GUARDS`; and its rows carry **no `ttft_ms` at all** (see below) |
| G10 vs everything | **NOT COMPARABLE** | different fixture (`967cef03`), `max_tokens` 16384, and it is the only rows file whose TTFT comes from the fixed client (`ttft_source = first_delta`, 6/6 rows) — a 6-row cell, not a grid |

**G1 is the sharpest case of why 'a number without its grid is a defect'.** `rows-longrun-2026-10-26.jsonl` holds 192 turn
rows across all four arms — apparently the richest grid in the corpus — and the analyser refuses **both** p50 and p95 at
**n = 0** for every arm, because the file's `ttft_ms` is null on all 192 rows while a `ttft_s` column exists on 93 of them.
`ttft_values` (:367) reads `ttft_ms` only, and a null is dropped and counted, never coerced to 0 and never rewritten from a
sibling column. I did **not** convert `ttft_s` to ms to rescue the cell: that would be an AD HOC quantile wearing the
analyser's authority. The audit's own verdict on this file is in §2 above — 192 rows, **0 usable TTFT**.

---

## 4. The quality column, honestly

Source of truth: `measure/MATRIX-HONESTY.json` (`MATRIX-HONESTY`, card `6e839685`), which audits **92 declared cells**
= (rows file, arm, checkpoint, rep) against the instrument `tools/det_verify.py`. Its totals: **5 pass · 38 fail ·
36 missing · 13 undecidable** (`{"fail": 38, "missing_answer_empty": 7, "missing_turn_absent": 29, "pass": 5, "undecidable": 13}`).

Two facts drive every `undecidable` in this report:

1. **`repair.t30` is undecidable in all 13 run/arm pairs that even reach it** — the judge returns `undecidable` for that
   checkpoint everywhere. That is an instrument limit, not an arm failing, so it is excluded from every denominator and
   named in every cell. It is also the reason no cell can be a *full-run* pass.
2. **Missing answers** (`missing_turn_absent` 29 + `missing_answer_empty` 7) land on whole arms in the smoke grids and on
   `transcript-grow` / `pointer-stable` in G1, where the rows exist but carry empty content.

| grid | arm | decided / denominator | pass | fail | repair.t30 | quality_status | why |
|---|---|---:|---:|---:|---|---|---|
| G1 | `lease-reopen` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G1 | `pointer-stable` | — | 0 | 1 | — | **undecidable** | 2 of the 3 truth checkpoints carry no answer (cp.1.t24,cp.2.t46: missing_answer_empty,missing_answer_empty) - the run is a partial grid |
| G1 | `transcript-compact` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G1 | `transcript-grow` | — | 0 | 0 | — | **undecidable** | 3 of the 3 truth checkpoints carry no answer (cp.0.t12,cp.1.t24,cp.2.t46: missing_answer_empty,missing_answer_empty,missing_answer_empty) - the run is a partial grid |
| G2 | `lease-reopen` | — | 0 | 0 | — | **undecidable** | 3 of the 3 truth checkpoints carry no answer (cp.0.t12,cp.1.t24,cp.2.t46: missing_turn_absent,missing_turn_absent,missing_turn_absent) - the run is a partial grid |
| G2 | `pointer-stable` | — | 0 | 0 | — | **undecidable** | 3 of the 3 truth checkpoints carry no answer (cp.0.t12,cp.1.t24,cp.2.t46: missing_turn_absent,missing_turn_absent,missing_turn_absent) - the run is a partial grid |
| G2 | `transcript-compact` | — | 0 | 0 | — | **undecidable** | 3 of the 3 truth checkpoints carry no answer (cp.0.t12,cp.1.t24,cp.2.t46: missing_turn_absent,missing_turn_absent,missing_turn_absent) - the run is a partial grid |
| G2 | `transcript-grow` | — | 0 | 2 | — | **undecidable** | 1 of the 3 truth checkpoints carry no answer (cp.2.t46: missing_turn_absent) - the run is a partial grid |
| G3 | `lease-reopen` | — | 0 | 0 | — | **undecidable** | 3 of the 3 truth checkpoints carry no answer (cp.0.t12,cp.1.t24,cp.2.t46: missing_turn_absent,missing_turn_absent,missing_turn_absent) - the run is a partial grid |
| G3 | `pointer-stable` | — | 0 | 0 | — | **undecidable** | 3 of the 3 truth checkpoints carry no answer (cp.0.t12,cp.1.t24,cp.2.t46: missing_turn_absent,missing_turn_absent,missing_turn_absent) - the run is a partial grid |
| G3 | `transcript-compact` | — | 0 | 0 | — | **undecidable** | 3 of the 3 truth checkpoints carry no answer (cp.0.t12,cp.1.t24,cp.2.t46: missing_turn_absent,missing_turn_absent,missing_turn_absent) - the run is a partial grid |
| G3 | `transcript-grow` | — | 0 | 1 | — | **undecidable** | 2 of the 3 truth checkpoints carry no answer (cp.1.t24,cp.2.t46: missing_turn_absent,missing_turn_absent) - the run is a partial grid |
| G4 | `lease-reopen` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G4 | `pointer-stable` | 1/3 | 1 | 2 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G4 | `transcript-compact` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G4 | `transcript-grow` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G5 | `pointer-stable` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G5 | `transcript-grow` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G6 | `pointer-stable` | 1/3 | 1 | 2 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G6 | `transcript-grow` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G7 | `pointer-stable` | 1/3 | 1 | 2 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G8 | `pointer-stable` | 0/3 | 0 | 3 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G9 | `pointer-stable` | 2/3 | 2 | 1 | undecidable | **measured** | denominator = the 3 truth checkpoints (cp.0.t12, cp.1.t24, cp.2.t46); repair.t30 is judge-undecidable in all 13 run/arm pairs that reach it, so it is excluded everywhere and the cell is a PARTIAL GRID by matrix_audit's own marker |
| G10 | `pointer-stable` | — | — | — | — | **not_graded** | not in MATRIX-HONESTY's declared cell space (rows-cell-*, pilot and non-longrun files never enter the grid: matrix_audit.py:30-33) |

Totals over the 24 cells in this report: **13 measured, 10 undecidable, 1 not_graded**.
Every `measured` cell is a **PARTIAL GRID** by `matrix_audit.py`'s own marker, and carries `full_run: false` in the JSON:
it decides 3 of the 4 declared checkpoints, and the 4th is the judge-undecidable `repair.t30`. No cell claims `measured` on a
denominator that is not printed beside it.

Where a `measured` denominator exists, the analyser's Wilson interval is quoted:

| grid | arm | pass/den | Wilson 95% |
|---|---|---:|---|
| G1 | `lease-reopen` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G1 | `transcript-compact` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G4 | `lease-reopen` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G4 | `pointer-stable` | 1/3 | 0.333 [0.061, 0.792] n=3 |
| G4 | `transcript-compact` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G4 | `transcript-grow` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G5 | `pointer-stable` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G5 | `transcript-grow` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G6 | `pointer-stable` | 1/3 | 0.333 [0.061, 0.792] n=3 |
| G6 | `transcript-grow` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G7 | `pointer-stable` | 1/3 | 0.333 [0.061, 0.792] n=3 |
| G8 | `pointer-stable` | 0/3 | 0.000 [0.000, 0.561] n=3 |
| G9 | `pointer-stable` | 2/3 | 0.667 [0.208, 0.939] n=3 |

Read the two 1/3 cells against their 0/3 partners before reading any story into them: at n = 3 the Wilson intervals
are enormous and they overlap (`0/3` reaches up to 0.56, `1/3` spans 0.061–0.79), so **quality is not separable in any
grid in this corpus** — which is exactly the state `MATRIX-HONESTY` recorded, and not a gap this report may fill by
picking a prettier denominator.

---

## 5. `tokens_to_verified_success` — **NOT PRODUCED**

| grid | value | mechanical reason |
|---|---|---|
| G1 stage1 | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G2 smoke-rp | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G3 fix-smoke | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G4 RUN-C-V2 | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G5 V3 | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G6 V4 | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G7 V4-TOOLS | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G8 V5-TOOLS | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G9 V6-TOOLS | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |
| G10 CELL-145758Z | **null / NOT PRODUCED** | `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints |

The denominator is zero, so the ratio is undefined — not small, not estimated, **undefined**. There is no grid in which
`n_verified_success > 0` for a full run, therefore the field is `null` in every cell and I do not substitute a proxy
(tokens per *turn*, tokens per *checkpoint answer*, or tokens per *decidable* checkpoint are all different quantities and
naming one of them `tokens_to_verified_success` is the defect this report exists to avoid).

**What would have to be true for it to exist:**

1. `repair.t30` becomes decidable, **or** the fixture drops it and the declared cell space in `matrix_audit.py` is restated —
   otherwise no run can ever be a full-run pass and the denominator stays 0 forever.
2. A run answers `cp.0.t12`, `cp.1.t24` and `cp.2.t46` with a verdict (no `missing_answer_empty`, no `missing_turn_absent`),
   so the pass is a *verified success* rather than a structural one.
3. The grade file for that grid is named in this report beside the number, with its denominator printed — as this report
   does for the quality column.

---

## 6. The one comparison the rows can support

Grid **G4 / RUN-C-V2** (`rows-longrun-c-2026-10-26.jsonl`, fixture `0a07db1b`, tools off, `max_tokens` 4096) is the only
grid with both `transcript-grow` and `pointer-stable` at n ≥ 20 **and** a decided quality verdict for both. n = 48 per arm.

**p95 — what the analyser says:** nothing. It refuses, in both arms, verbatim:

- `transcript-grow` p95: `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`
- `pointer-stable` p95: `refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60`

So the p95 difference **cannot be quoted with an interval from the analyser** — the order-statistic span it names
(ranks 43–48 = p89.6–p100.0) is the honest width of a p95 at n = 48, i.e. about three observations out of 48 carry the number.

**The p95s that are on record, and their standing:** `RUN-C-V2` reported `pointer-stable` **356.12 ms** versus
`transcript-grow` **838.85 ms** (`orchestration/units/RUN-C-V2.md:15-17`, `docs/PREREG-ARM-RUN.md:49`). Two things must
travel with those numbers: (i) they were produced by the **old inline TTFT latch**, which `WIRE-CLIENT`
(`orchestration/units/WIRE-CLIENT.md:16`) explicitly rules **out of reuse** because it was blind to a first delta carrying
only `tool_calls`; (ii) they are the very quantity the analyser now refuses at this n. I therefore quote them as *reported*,
not as measured here, and I do not compute a difference or an interval for them.

**What is tool-blessed at this grid is p50:** `transcript-grow` **482.24 ms** [410.55, 556.41] versus `pointer-stable` **167.02 ms** [163.26, 168.33] — difference **-315.22 ms**, per-arm intervals disjoint, at this grid, tools off, fixture `0a07db1b`.

**And the token side, measured from the rows:** over 48 requests each, `transcript-grow` carries **901,109 prompt tokens**
total against `pointer-stable`'s **104,468**. The recollection that `pointer-stable` had the *higher* total prompt tokens does
**not reproduce** in this grid: the pointer arm is the *cheaper* one on prompt tokens and still wins on p50. Both facts
belong in the same sentence, and so does the correction — an operator who believes the expensive arm was the pointer arm
is holding a claim these rows contradict.

**What this licenses, exactly:** a p50 TTFT difference **inside G4**, between these two arms, with tools off and on this
fixture. It licenses **nothing** about p95, **nothing** about quality (0/3 vs 1/3, intervals overlapping — see §4), and
**nothing** about G5, G6, G7, G8, G9 or any grid where the fixture or the harness differs. The thesis is neither live nor
dead on this evidence; it is unmeasured at the tail and unmeasurable at the tail at n = 48.

---

## 7. What is missing to finish this report

**Grids without n ≥ 60 per arm (so p95 is refused everywhere):** G1 (192 rows, 0 usable TTFT), G2 (31/3/3/3),
G3 (18/5/3/3), G4/G5/G6 (48 per arm), G7 (**51 de-duplicated**, was 68 — now **below** the floor), G10 (6 rows).
Only **G8 (70)** and **G9 (61)** clear the analyser's bar after de-duplication, and each is a **single-arm** grid.
Read the bar honestly: those n count **requests with a TTFT** (turn + tool-follow-up), not turn rows — the turn
counts are 46 and 37.

**Arms with no comparable partner in their own grid:**

- `pointer-stable` in G7, G8, G9: **no `transcript-grow` was ever run with tools on**, at any fixture. The tools-on
  dimension therefore has no arm comparison at all — the three grids can describe the pointer arm and nothing else.
- Any arm in G1: no usable TTFT for any of the four.
- `lease-reopen` and `transcript-compact`: never appear in a grid with decided quality for a full run.

**What the next cell must record for this report to complete:**

1. **n ≥ 60 turn rows per arm in one grid** (p95's minimum is 60, `TAIL_MIN` :71). At 12 turns per rep that is ≥ 5 reps,
   and the reps must land in one grid — same fixture, same tools setting, same harness commit.
2. **`transcript-grow` with tools ON**, on the same fixture as a `pointer-stable` tools-on arm, so the tools dimension
   stops being single-arm.
3. **`ttft_ms` populated on every row** (G1's 192 all-null `ttft_ms` is a pure loss of the largest grid on disk), and
   **`ttft_source = first_delta`** on every row, so the fixed client's provenance travels with the number.
4. **One `max_tokens` and one fixture per rows file.** G2 (16384) vs G3 (4096/16384 mixed, two fixtures in one file)
   is the anti-pattern; G9's mid-cell version mix in turns 1–6 must not repeat.
5. **A decidable `repair.t30`** (or its removal from the declared space) — without it `tokens_to_verified_success`
   cannot exist at all, no matter how many reps are run.
6. A **quantile-difference** routine in the analyser (paired by turn), so an arm gap can carry an interval instead of
   two overlapping per-arm intervals and an eyeball.

---

## 8. Provenance

### 8.1 Every row file, with its sha256

| rows file | rows | sha256 |
|---|---:|---|
| [`rows-baseline-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-baseline-2026-10-26.jsonl) | 105 | `638c84942e3bcdba4b416cceda9214f3fdcc99c42171639bf5c52736f40e032d` |
| [`rows-cell-pointer-stable-20261026T145758Z.jsonl`](experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T145758Z.jsonl) | 6 | `5ac9dd992f5d8715696925f56c225024e172cb98b4b9a937a0ee63bd099e9800` |
| [`rows-equalinfo-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-equalinfo-2026-10-26.jsonl) | 100 | `c01c7b4a477fe24bc55370ceddf26d885a1fe827e7135023cdde48b271e8c934` |
| [`rows-live-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl) | 27 | `3d02b4d473304f0012b34024cc517c70d7f23b60de1103c1ca1b93a7e2752e5b` |
| [`rows-longrun-2026-10-26-fix.jsonl`](experiments/ptr-engine/measure/rows-longrun-2026-10-26-fix.jsonl) | 29 | `9d4ad90ce34cb781c04e9f73fba50ffb47d5b35d6d1491389d22a49044516405` |
| [`rows-longrun-2026-10-26-policy.jsonl`](experiments/ptr-engine/measure/rows-longrun-2026-10-26-policy.jsonl) | 40 | `9b1097234bf8d2464a4d24ec48cf0cccc1ecd64bd853815fc6643b1ad3da3368` |
| [`rows-longrun-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-longrun-2026-10-26.jsonl) | 192 | `bc61d38192d4e4316021ec8d3d0e21dcb8e6153f463260a0138da21969d0b21e` |
| [`rows-longrun-c-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl) | 192 | `aa7d6cfe9adedf9e408480f6b76022da840cad95f05dafc1ee0adb6faca9ae0c` |
| [`rows-longrun-v3-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-longrun-v3-2026-10-26.jsonl) | 96 | `80d85fe0e977af164a5ffeca8b2f95350c6614d2112455c3ace93765530ff921` |
| [`rows-longrun-v4-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-longrun-v4-2026-10-26.jsonl) | 96 | `999f298dac8b83569c4059946e7789b76ec485b24a5c9a39d6c1616f0501c28e` |
| [`rows-longrun-v4-tools-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.jsonl) | 68 | `f11391aa2989949f904b8092074cb7b85b65dfe5b8c89431930fe921b28de77f` |
| [`rows-longrun-v5-tools.jsonl`](experiments/ptr-engine/measure/rows-longrun-v5-tools.jsonl) | 72 | `586b66f27939bd05e09d8b48dad745a5fa268c3f31103695746df3e3f8443cb5` |
| [`rows-longrun-v6-tools.jsonl`](experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl) | 72 | `1e78d75f259afbe0406643825941a65b4773b4342b847698005ad5908b3e531e` |
| [`rows-pilot-thinking-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-pilot-thinking-2026-10-26.jsonl) | 6 | `6b81a6281ce0b266f45ab1b95fc3834e446bea5708e5466988b28e133a0e9e10` |

Total **14 files / 1,101 rows raw → 1,071 de-duplicated** (30 defensible duplicate rows removed: v4-tools 17, v6-tools 11, v5-tools 2; the 3 legacy-schema files are `not_applicable` and keep every row). Long-run chain: **10 files / 863 rows raw → 833 de-duplicated** — this reproduces the brief's 863 exactly. The brief's
"13 files / 1095 rows" reads **14 / 1101** here because `measure/rows-cell-pointer-stable-20261026T145758Z.jsonl`
(6 rows) was written at 10:41 local, after the brief was composed; that is a counting difference, not a missing file.
`rows-longrun-2026-10-26.jsonl` is still `bc61d381…` as required, and nothing in `measure/` was modified except the two
paths this unit is allowed to write (`LATENCY-REPORT.json` and the four declared report files).

### 8.2 Non-long-run corpus — inventoried, and excluded from every cell

| rows file | rows | why it is not a cell |
|---|---:|---|
| [`rows-baseline-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-baseline-2026-10-26.jsonl) | 105 | arms `C0`/`R`/`C` are **not** the four long-run arms; no `ttft_ms`, no `ttft_s`, no `fixture_sha256` on any row |
| [`rows-equalinfo-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-equalinfo-2026-10-26.jsonl) | 100 | arms `C0F`/`C0FT`/`R` are **not** the four long-run arms; no timing column on any row |
| [`rows-live-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl) | 27 | `arm` is null on all 27 rows; no timing column |
| [`rows-pilot-thinking-2026-10-26.jsonl`](experiments/ptr-engine/measure/rows-pilot-thinking-2026-10-26.jsonl) | 6 | `transcript-grow` pilot, 6 rows — below `MIN_N` and outside the declared cell space (`matrix_audit.py:30-33`) |

### 8.3 What this unit did **not** do

- No pooled p95, pooled p50, or pooled mean across grids — not even as a footnote.
- No quantile computed by hand where the analyser refused; every refusal is printed verbatim.
- No `ttft_s → ttft_ms` conversion to rescue G1; no substituting cos-mean for a missing `ttft_ms`.
- No invented metric in place of `tokens_to_verified_success`.
- No write to any row file, grade file, fixture, `cell.py`, `run_longrun.py`, `client.py`, `grade_v5.py`,
  `analyze_stats.py`, `fixture_coverage.py`, `matrix_audit.py`, `handoff_lint.py` or `det_verify.py`.
- No inference request and no network call (`live_requests: 0`).

### 8.4 AD HOC numbers (formula shown, no interval, not analyser-blessed)

`mean_ttft_ms_ADHOC = Σ ttft_ms / n`, over **exactly the same rows** `analyze_stats.ttft_values()` accepts for that cell, so
the mean and the quantiles rest on one population. `prompt_tokens` / `completion_tokens` are **column sums over the cell's rows**
(turn rows plus tool-followup rows), not per-turn averages. `analyze_stats.py` prints no mean and no sum, so none of these
carries the analyser's authority or an interval; they are in the JSON under the same `_ADHOC` name and should not be quoted
as estimates.

| grid | arm | mean ms (AD HOC) | n | prompt tok | completion tok |
|---|---|---:|---:|---:|---:|
| G1 | `lease-reopen` | — | 0 | 8916 | 5463 |
| G1 | `pointer-stable` | — | 0 | 89396 | 5929 |
| G1 | `transcript-compact` | — | 0 | 205309 | 5504 |
| G1 | `transcript-grow` | — | 0 | 133030 | 6144 |
| G2 | `lease-reopen` | 118.96 | 3 | 577 | 19058 |
| G2 | `pointer-stable` | 144.39 | 3 | 4162 | 11984 |
| G2 | `transcript-compact` | 203.94 | 3 | 6954 | 14406 |
| G2 | `transcript-grow` | 7135.94 | 31 | 1044736 | 340786 |
| G3 | `lease-reopen` | 122.14 | 3 | 577 | 6817 |
| G3 | `pointer-stable` | 124.17 | 3 | 4153 | 5552 |
| G3 | `transcript-compact` | 820.76 | 5 | 27213 | 37306 |
| G3 | `transcript-grow` | 1488.67 | 18 | 319991 | 114299 |
| G4 | `lease-reopen` | 142.82 | 48 | 20628 | 65659 |
| G4 | `pointer-stable` | 189.21 | 48 | 104468 | 8936 |
| G4 | `transcript-compact` | 205.36 | 48 | 185617 | 1804 |
| G4 | `transcript-grow` | 507.65 | 48 | 901109 | 30455 |
| G5 | `pointer-stable` | 180.85 | 48 | 106294 | 7995 |
| G5 | `transcript-grow` | 200.68 | 48 | 171011 | 1113 |
| G6 | `pointer-stable` | 198.12 | 48 | 195396 | 37646 |
| G6 | `transcript-grow` | 221.27 | 48 | 260564 | 1134 |
| G7 | `pointer-stable` | 197.69 | 51 | 216951 | 8229 |
| G8 | `pointer-stable` | 185.12 | 70 | 372095 | 10715 |
| G9 | `pointer-stable` | 205.91 | 61 | 296275 | 11105 |
| G10 | `pointer-stable` | 373.66 | 6 | 24288 | 39827 |

---

## 9. Answer to the operator, in one line

**Latency can be told today as p50 only, inside single grids:** eight within-grid p50 pairs at n = 48 with disjoint
intervals (all with tools off), **two** single-arm p95s with intervals (tools on, n = **70** and **61**, no partner arm,
intervals overlapping), and **no p95 arm-versus-arm difference anywhere** — because every two-arm grid sits at n = 48 and
the analyser refuses a p95 there, and because `tokens_to_verified_success` has a zero denominator in every grid.
The third p95 this report used to carry (`G7`, n=68) is **withdrawn as duplicate-inflated**. None of that costs a request.

**The honest denominator for H1: this project has exactly 2 p95 values, in 1 arm (`pointer-stable`), across 2 single-arm
grids (`G8` V5-TOOLS n=70, `G9` V6-TOOLS n=61) — and 0 p95 differences between arms.**

