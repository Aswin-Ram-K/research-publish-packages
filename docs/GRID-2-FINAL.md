# GRID-2-FINAL — what the six usable cells measure, and the price of what would settle it

**Unit:** `GRID-2-FINAL` · **Generated:** 2026-10-28T20:49:47Z · **Requests sent:** **0** · **Cells run:** **0**

This page does not adjudicate H1. It records what was measured in `GRID-RUN-2`, with its limits attached to each number, and states the arithmetic of closing the gap. Built by `experiments/ptr-engine/tools/grid2_final_report.py` from the 16 rows files and their manifests; every statistic is recomputed from those rows.

---

## 0. Census — the table the pinned reader cannot build

`analyze_stats.load_cell_manifests` (`:661-671`) requires a **top-level** `rows_path`; `cell.py` writes it as `run.rows_path` (finding A, repaired in `c15f086c…`). This census links each cell by its own nested path, so every `usable_for` below is the cell's OWN stamp, read from its own manifest.

| cell | arm | turns on disk | `usable_for` (verbatim) | reason | requests billed | turns vs manifest n |
|---:|---|---:|---|---|---:|---|
| 1 | lease-reopen | 48 | `["h1", "h2", "h3"]` | complete: 48/48 turn rows, markers={"digest_rows": 0, "evicted_turns": 0, "… | 91 | match (48) |
| 2 | lease-reopen | 48 | `["h1", "h2", "h3"]` | complete: 48/48 turn rows, markers={"digest_rows": 0, "evicted_turns": 0, "… | 96 | match (48) |
| 3 | pointer-stable | 48 | `["h1", "h2", "h3"]` | complete: 48/48 turn rows, markers={"digest_rows": 0, "evicted_turns": 0, "… | 96 | match (48) |
| 4 | pointer-stable | 48 | `["h1", "h2", "h3"]` | complete: 48/48 turn rows, markers={"digest_rows": 0, "evicted_turns": 0, "… | 93 | match (48) |
| 5 | pointer-stable | 47 | `ABSENT` | no manifest: cell.py refused (exit 4) | 94 | `ABSENT` (no manifest) |
| 6 | pointer-stable | 46 | `ABSENT` | no manifest: cell.py refused (exit 4) | 93 | `ABSENT` (no manifest) |
| 7 | pointer-stable | 48 | `["h1", "h2", "h3"]` | complete: 48/48 turn rows, markers={"digest_rows": 0, "evicted_turns": 0, "… | 94 | match (48) |
| 8 | pointer-stable | 48 | `["h1", "h2", "h3"]` | complete: 48/48 turn rows, markers={"digest_rows": 0, "evicted_turns": 0, "… | 89 | match (48) |
| 9 | transcript-compact | 48 | `[]` | zero-marker: digest_rows=0 for arm transcript-compact | 66 | match (48) |
| 10 | transcript-compact | 48 | `[]` | zero-marker: digest_rows=0 for arm transcript-compact | 81 | match (48) |
| 11 | transcript-grow | 48 | `[]` | zero-marker: evicted_turns=0 for arm transcript-grow | 77 | match (48) |
| 12 | transcript-grow | 48 | `[]` | zero-marker: evicted_turns=0 for arm transcript-grow | 53 | match (48) |
| 13 | transcript-grow | 48 | `[]` | zero-marker: evicted_turns=0 for arm transcript-grow | 56 | match (48) |
| 14 | transcript-grow | 48 | `[]` | zero-marker: evicted_turns=0 for arm transcript-grow | 56 | match (48) |
| 15 | transcript-grow | 48 | `[]` | zero-marker: evicted_turns=0 for arm transcript-grow | 82 | match (48) |
| 16 | transcript-grow | 48 | `[]` | zero-marker: evicted_turns=0 for arm transcript-grow | 53 | match (48) |

**Usable: 6 of 16** (lease-reopen, pointer-stable). Excluded: 10 — 8 stamped `[]` (a treatment marker never fired) and 2 with **no manifest at all**, whose `usable_for` is therefore `ABSENT`.

Request rows sum to **1270** across the 16 cells, which is the ledger delta exactly -- the census's billing column is a measurement, not an estimate.

> `ABSENT` is never rendered as usable. `analyze_stats.py:749` keeps an unstamped cell (`_usable_list(None) is None` ⇒ not excluded) and prints it `unstamped` — an absent stamp is included by that reader, and that is exactly how a rejected cell enters an analysis. The two `exit 4` cells are excluded **by name** here instead.

---

## 1. H1 — per-turn TTFT per arm, recomputed

Floor: `min_n_for(0.95)` = **60** raw turns for p95; effective-n floor **60**; `n_eff = n(1−r)/(1+r)` over the arm's own turn-ordered series.

| arm | n | lag-1 r | n_eff | p50 [CI] | p95 |
|---|---:|---:|---:|---|---|
| lease-reopen | 48 | -0.1188 | 60.95 | 198.39 [130.84, 270.90] n=48 | REFUSED — *refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60* |
| pointer-stable | 48 | 0.2949 | 26.14 | 156.15 [146.31, 291.93] n=48 | REFUSED — *refusing p95 at n=48: the 95% order-statistic span is ranks 43-48 (p89.6-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60* |

* **lease-reopen** — n=48, r=-0.1188 ⇒ n_eff **60.95** (floor 60): not_adjudicable_floor. 2 cell(s) on disk, contributing {"1": 44, "2": 4}.
* **pointer-stable** — n=48, r=0.2949 ⇒ n_eff **26.14** (floor 60): not_adjudicable_floor. 4 cell(s) on disk, contributing {"3": 42, "4": 4, "7": 2}.

**Reproduction test.** These are recomputed from the rows, not copied; they reproduce the grid's handoff to the digit (`p50 156.151 [146.306, 291.926] n=48 r=0.2949 n_eff=26.14`; `198.395 [130.843, 270.899] n=48 r=−0.1188 n_eff=60.95`). A reproduction that fails would have been the finding; it did not.

**The difference that matters is not in the digits — it is in `n`.** The six usable cells hold **288 turn rows**; the reading analyses **96**. `per_arm_series` dedupes on `(arm, rep, turn_index)` and *every gen-6 cell wrote `rep=1`* (`--reps 1`, one runner invocation per cell), so replicates of one arm collapse into a single 48-turn series: `dropped_duplicate=192`.

| cell | arm | p50 alone |
|---|---|---|
| 1 | lease-reopen | 136.43 [129.87, 266.58] n=48 |
| 2 | lease-reopen | 262.80 [131.56, 271.95] n=48 |
| 3 | pointer-stable | 156.15 [147.19, 291.93] n=48 |
| 4 | pointer-stable | 167.13 [151.59, 299.63] n=48 |
| 7 | pointer-stable | 156.84 [142.73, 166.66] n=48 |
| 8 | pointer-stable | 162.18 [147.18, 227.41] n=48 |

So each arm's printed interval is **one 48-turn pseudo-rep stitched across cells** (lease-reopen: 44 turns from one cell + 4 from another; pointer-stable: 42 + 4 + 2, with one of its four cells contributing **nothing**). Its p50 (198.40, 156.15) lies between the per-cell p50s, which is the signature of a merge, not of a rep-pooled arm. Consequently **p95 is refused at n=48 while 192 / 96 turn rows sit on disk**, and `n_eff` is measured on 48 turns regardless of how many cells were bought.

**Sensitivity (NOT the reading).** The same selector with the cell ordinal written into `rep` — what the rows support if the key is ever fixed:

| arm | n | r | n_eff | p50 [CI] | p95 [CI] |
|---|---:|---:|---:|---|---|
| lease-reopen | 96 | -0.0376 | 103.49 | 141.65 [131.56, 266.02] n=96 | 349.78 [284.27, 378.58] n=96 |
| pointer-stable | 192 | 0.2105 | 125.23 | 159.83 [154.60, 166.32] n=192 | 387.84 [357.95, 671.14] n=192 |

It is printed to price the collapse, **not** to rescue H1: swapping the estimator after the rows exist is an instrument change, and an instrument change mints a generation whose rows may not be pooled with gen 6. The H1 verdict below is computed on the frozen series only.

**H1 verdict: `not_adjudicable_floor`** (binding arm `pointer-stable`, n_eff 26.14 < 60).

---

## 2. H2 — prompt work per completed turn (the one limb with real evidence)

| arm | cached-inclusive / turn | uncached / turn | diff sign | n |
|---|---:|---:|---:|---:|
| lease-reopen | 1497.85 | 332.28 | +1 | 184 |
| pointer-stable | 5395.09 | 355.62 | +1 | 364 |

Sign is the same in both usable arms (**+1**): cached-inclusive prompt work per turn exceeds uncached in each, i.e. cache was credited in both.

A **two-arm** sign is not the four-arm claim H2 was frozen as. H2's frozen rule is a C-vs-A comparison (`pointer-stable` vs `transcript-grow`) on two limbs with both required; `transcript-grow` has **zero** usable cells, so `not_adjudicable`. What the two usable arms share is a within-own-arm fact (`cached ≥ uncached`), not evidence for the cross-arm claim.

---

## 3. H3 — placeholder, verbatim

| field | value (verbatim) |
|---|---|
| `x/12` | `x/12` |
| `x/9` | `x/9` |
| `answered_ratio` | `answered_ratio` |
| `contract_adherence` | *pre-check column; not folded into accuracy* |

The grid's own handoff recorded the placeholder zeros `{"x_12": 0, "x_9": 0, "answered_ratio": 0.0, "contract_adherence": "pre-check column; not folded into accuracy", "none_flagged": ["cp.3.t14 pass", "cp.5.t20 undecidable", "cp.10.t42 pass"]}`. They are placeholders, not measurements: `grade_v5` carries no contract-adherence column, and the `x/12` gate has no admissible emitter for this grid.

H3 therefore reports **answer production + accuracy, not contract compliance**, and only `pointer-stable` contributes (H3 is scoped to the C arm).

---

## 4. TVS — tokens to verified success

**UNDEFINED.** TVS needs a cell graded `pass` at its first declared checkpoint and, at arm level, a decidable verdict at every declared checkpoint; n_verified_success = 0 arm-level / 0 first-checkpoint in the six usable cells, so the denominator is undefined -- not zero, and not a token count

No token count is substituted. `n_verified_success` is **0** at arm level and **0** at first-declared-checkpoint level across the six usable cells.

---

## 5. The price of closing the gap — stated as arithmetic

The card asks for three shapes at **162 requests/cell**. That price is recomputable, and recomputing it changes the conclusion, so both are shown.

**Asserted price** (`GRID-GAP-DIAGNOSIS.md:188`): `2591 / 16 = 161.9 ≈ 162` requests/cell.

**Recomputed price**: this grid's 16 rows files hold **1270** request rows, and that sum equals the ledger delta exactly (`1321 → 2591`, baseline 4). So the marginal cost of the grid is **79.4 requests/cell**, and the asserted numerator includes **1321** requests billed *before* the grid started. The asserted figure charges this grid for its baseline.

The highest single-cell bill observed anywhere in the 16 cells is **96**. That is the only upper envelope the data support.

| shape | cells | at 162/cell (asserted) | vs 1729 | at 79.4/cell (measured) | vs 1729 |
|---|---:|---|---:|---|---|
| 6 pointer-stable + 6 transcript-grow | 12 | **1944** | short by 215 | **952** | fits (776 spare) |
| all 16 cells | 16 | **2592** | short by 863 | **1270** | fits (459 spare) |
| 3 reps/arm, rep-varied | 6 | **972** | fits (757 spare) | **476** | fits (1253 spare) |

Sixteen cells at the maximum observed per-cell bill would cost **1536** — still inside 1729. Within the measured envelope, the grid is **affordable**; only the asserted 162/cell makes it not. A gen-7 cell whose treatment actually fires could cost more than any gen-6 cell did, and that is the one real uncertainty in the cheaper column — but it is an uncertainty, not a measurement, and it is the asserted number, not this one, that has no derivation.

**Why the cheaper shape still is not a recommendation**, in order of how fatal the objection is:

1. **Under the frozen selector it buys nothing.** Every cell writes `rep=1`; `n` stays 48 per arm however many cells are run. Six cells would reproduce `n_eff = 26.14` for pointer-stable exactly.
2. **With the key fixed, the measured `r` supports 3 reps for pointer-stable** (`r=0.2949` ⇒ ≥111 raw turns ⇒ 3 × 48; 3 reps ⇒ n_eff ≈ 78), but transcript-grow has **no usable cell**, so its `r` is unmeasured and its rep count would be a guess, not arithmetic.
3. **Generation, not budget, is the wall.** A gen-7 fixture makes every gen-6 cell non-poolable, so the re-run must be all-or-nothing per arm regardless of what it costs.

So: no cheaper shape can be **shown** to clear `n_eff ≥ 60` from the measured data, and this report does not recommend one — but not because it is unaffordable. It is not.

---

## 6. Verdict, one line

**`not_adjudicable`** — H1, H2 and H3 are `not_adjudicable` and TVS is `UNDEFINED`; the one condition that would change it is: a gen-7 instrument in which (i) the context treatments actually fire inside the horizon and (ii) the selector's dedupe key carries cell identity, run on >= 6 cells/arm inside a 4,320-request ledger.

The card's sentence *"this cycle's binding constraint is the request budget, not the instrument"* is **declined**, and not on a technicality: the price it rests on divides total ledger spend by 16. Recomputed from the rows, this grid billed **1270** requests (**79.4/cell**), and 16 cells at the highest bill any cell actually produced cost **1536** — inside the **1729** remaining. The budget does not bind the re-run; the **instrument** binds it, twice: the treatments never fired (8 cells stamped `[]`) and the selector merges replicates (288 turn rows in, 96 out, `n_eff = 26.14`). A funded re-run that kept either defect would return this same verdict.

