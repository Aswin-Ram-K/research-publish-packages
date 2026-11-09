# PREREG-TRANCHE-1 — the decision procedure for RUN-A*, frozen before any row exists

**Unit** `V-TRANCHE-1` · **dated (UTC)** `2026-10-26T18:22:00Z` · **requests: 0** · **rows read: 0** ·
**rows on disk at freeze time: 0** (`measure/rows-runA-*` absent; checked before this file was written).
Machine record: [`experiments/ptr-engine/measure/PREREG-TRANCHE-1.json`](../experiments/ptr-engine/measure/PREREG-TRANCHE-1.json)
(carries the sha256 of this document). Harness:
[`experiments/ptr-engine/tools/verify_tranche1.py`](../experiments/ptr-engine/tools/verify_tranche1.py);
tests: [`experiments/ptr-engine/tests/test_verify_tranche1.py`](../experiments/ptr-engine/tests/test_verify_tranche1.py).

This document is the **procedure**, not an analysis. It says exactly how `RUN-A*` will be read, so that
the second pass of this card can execute it and cannot choose a rule after seeing the intervals. If a
threshold is not in §7, it is an **addition, not a clarification**, and must not appear in a verdict.

---

## 0. Population and ordering

`RUN-A*` (`ad214412-c39c-4a47-afb1-2be328e03b1e`) is **10 cells**: `pointer-stable` ×3 reps,
`transcript-grow` ×3, `transcript-compact` ×2, `lease-reopen` ×2; 48 turns per cell; ≈660 requests.
Each cell writes one rows file `experiments/ptr-engine/measure/rows-runA-<arm>-<rep>-*.jsonl`, one live
gate manifest under `experiments/ptr-engine/longrun/manifests/`, and one `--hypothesis H2` claim sidecar
(`rows_path + ".claim.json"`). The tranche's allowed-cell set and H2 claim were rehearsed by
`TRANCH1-DRYRUN-2` (PASS).

Every figure below is computed **per arm, pooling that arm's reps**, never per cell. A cell is an
instrument for producing rows; it is never a unit of evidence. The pair comparison is
**C = `pointer-stable` vs A = `transcript-grow`**. `transcript-compact` and `lease-reopen` are reported
descriptively and never enter a C-vs-A verdict.

`R-all` is the frozen H1 reading. Its per-arm n at 3 reps is **144**; `lease-reopen` has 2 reps, so its
R-all n is **96**. Both clear the n floor. The number 144 is the frozen n for the **three-rep** arms; a
report that writes "n=144 per arm" over all four arms is arithmetically wrong about `lease-reopen`.

---

## 1. H1 — latency, exactly as a reader would execute it

**Claim (PARM-1, byte-unchanged).** C's p95 TTFT per turn is lower than A's.

1. Read every rows file. Select per-turn latency rows with
   `analyze_stats.turn_latency_rows(rows)` → one row per turn, `kind="turn-initial"` preferred, legacy
   `kind="turn"` fallback labelled, `tool-followup` dropped. Use the returned `meta` **verbatim** in the
   report (it names the fallback count and the dropped rows).
2. Per arm, concatenate the selected rows of all its reps — this is **R-all**. Values are `ttft_ms`.
3. Compute `point, lo, hi, n = analyze_stats.quantile_ci(values, 0.95)` with the module defaults:
   `resamples = RESAMPLES = 10000`, `seed = SEED = 20261020`, two-sided `LEVEL = 0.95`. Do **not** pass
   other values and do **not** substitute a nearest-rank p95.
4. **Refusal floor.** A p95 is admissible only when `n >= 60` and `n*(1-q) >= 3` — implemented as
   `analyze_stats.min_n_for(0.95) == 60` and `TAIL_MIN == 3`; `quantile_ci` itself raises
   `InsufficientSamples` below either. On refusal the verdict is `refused`, the refusal message is
   quoted, and p50 with its interval may be reported beside it. **The floor is never lowered.**
5. **Direction.** C is lower than A iff C's bootstrap `hi < A`'s bootstrap `lo` (strict).
6. **Overlap rule, in one sentence:** *when the two 95 % intervals overlap — including touching
   endpoints — the direction is refused and no ranking claim may be reported; both estimates travel
   with their n and interval.*

Verdicts: `separated_lower` (C hi < A lo) · `separated_higher` (A hi < C lo) · `overlap` ·
`refused` (floor not met). Only `separated_lower` supports H1.

---

## 2. H2 — total prompt work, both limbs, neither picked

**Claim (PARM-1).** C carries fewer total prompt tokens per completed turn than A.

- **Population.** Every row belonging to a turn selected by `turn_latency_rows` (so a turn's
  tool-follow-up requests are included and its latency row is not double-counted), deduplicated by
  `(arm, rep, turn, ts, content_sha256)` — the TVS duplicate rule — with `prompt_tokens` /
  `completion_tokens` null **excluded and counted**, never coerced to 0. Denominator = the number of
  such distinct billed rows whose turn is a completed turn.
- **Limb 1, cache-inclusive.** `mean(prompt_tokens)`. Pass iff `C_mean <= 0.95 * A_mean`.
- **Limb 2, uncached.** `mean(prompt_tokens - cached_tokens)`, `cached_tokens` absent treated as 0 and
  counted. Pass iff `C_mean < 1.00 * A_mean` (strict).
- **Sign.** H2 ✓ iff **both** limbs pass; H2 ✗ iff either fails. **Neither limb is picked**: a report
  may not say "H2 holds on the uncached limb" as if it were H2, and may not prefer the limb that
  passes. The two limb means, their difference and their denominators are always printed together, and
  a split verdict is reported as `h2_failed_split` naming which limb failed.

---

## 3. H3 — quality veto, both denominators

- **Source of cells.** `grade_v5` cells only, read through `analyze_stats.accuracy_from_grade(grade,
  arm)`. `decidable = pass + fail`; `undecidable` (`verdict "text"`) and `missing`
  (`reason == "turn_missing"`) leave the denominator and are printed **by name**. A row-derived
  denominator is forbidden.
- **Gate number is `x/12`.** Always report how many of `x` are NONE items and how many of `12-x` misses
  are NONE items. The three NONE ids are `cp.3.t14`, `cp.5.t20`, `cp.10.t42` (fixture
  `LR-01.v7.json`); they have a constant-`ANSWER: NONE` floor and are cheap passes.
- **Decomposition is `x/9`** over substantive (NUM/CALL) ids, labelled a decomposition, never the gate.
- **Margin.** H3 fails when C loses **more than 2 checkpoints of 12** against A (equivalently > 16.7 pp
  on the 12-item denominator). "Loses 2" passes; "loses 3" fails. The margin is fixed in checkpoints
  and is decided independently of McNemar.
- **Secondary veto.** Pairs are passed to `mcnemar_exact` in the order **`(C, A)`**, fixed here so the
  sign cannot be argued after the fact. Then `b` = C-wrong/A-right (C worse) and `c` = C-right/A-wrong
  (C better), and `b+c` is the discordant count. When `b+c >= 6` the test is computed and H3 fails iff
  the **exact two-sided p < 0.05 and `b > c`** (C worse). When `b+c < 6` the test is refused, its
  refusal message is quoted, and only the margin decides.
- **Unadjudicable.** If either arm's `decidable` is below **8 of 12**, H3 returns no verdict
  (`not_adjudicable`) and must not be read as a pass.
- **Two columns travel with every H3 number:** `answered_ratio = gradable answers / declared
  checkpoints` (per arm, from the same grade cells) and `contract_adherence` (the pre-check label,
  reported as its own column, never folded into accuracy).
- **Veto.** H3 ✗ vetoes any latency/work win. No cell may report a win for C when H3 ✗.

---

## 4. `tokens_to_verified_success` — definition and censoring

Definition of record (`docs/TVS.md`): `TVS(cell) = prompt_tokens + completion_tokens`, summed over
every **distinct** request from the run's first request through **the first checkpoint's own turn
inclusive**, where that checkpoint's cell was graded `pass` by `grade_v5`
(sha256 `6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`). Scope: the 3 v5 truth ids
of that arm — **never a fraction of 12**. Cache-inclusive by default; `cached_share` is a separate
diagnostic; null-token rows are excluded and counted; duplicate records are counted once and the skipped
count is reported.

**Censoring statement (frozen now).** When no declared TVS checkpoint passes for an arm, TVS is **not**
assigned a number and **not** treated as "the whole run's tokens". It is reported as
`{"tvs": null, "censored": true, "censored_at_turn": <last billed turn of that arm>,
"censor_kind": "no_verified_checkpoint"}`. A censored TVS is never compared with a realized TVS, never
averaged with one, and never enters an H1/H2/H3 verdict. Its censoring turn is reported so a reader can
see how far the run got.

---

## 5. What the harness does when the rows are absent

`verify_tranche1.py` refuses to run the procedure unless **all** expected artefacts are present: the ten
`rows-runA-*` files (one per declared arm/rep cell) and the gate manifests. When any is missing it writes
`{"verdict": "awaiting_rows", ...}` to `measure/tranche1-verify.json`, exits **0**, and computes **no
statistic** — it must not average over whichever subset happens to exist. If `rows-runA-*` exists at the
time the prereg is written, the honest verdict is `prereg_late`, and this unit stops.

## 6. Self-test contract

Synthetic rows are written under `/tmp` only, never into `measure/`. Each rule is exercised by a case
that passes under the frozen rule and **fails when the rule is reverted in the harness's rule table**:
floor 60→40 must turn the n=48 case red; the overlap rule inverted must turn the overlap case red; the
censoring rule replaced by "0" must turn the censored case red; `turn_missing` counted as a fail must
change the H3 denominator; the McNemar floor 6→0 must change the licensed/refused label. A rule that
cannot be implemented as written is reported `unimplementable` with the reason.

## 7. FROZEN THRESHOLD TABLE

Every number a verdict may use. Source is `file:line` as of this freeze. A threshold not in this table
that appears later is an **addition, not a clarification**, and is void.

| # | threshold | value | source `file:line` |
|---|---|---|---|
| T1 | H1 minimum usable n | **60** | `experiments/ptr-engine/longrun/analyze_stats.py:330` (`min_n_for`), `docs/PREREG-ARM-RUN.md:36` |
| T2 | tail observations required at q | **3** (`TAIL_MIN`) | `experiments/ptr-engine/longrun/analyze_stats.py:111` |
| T3 | absolute minimum n for any quantile | **20** (`MIN_N`) | `experiments/ptr-engine/longrun/analyze_stats.py:112` |
| T4 | interval level | **0.95** two-sided (`LEVEL`) | `experiments/ptr-engine/longrun/analyze_stats.py:110` |
| T5 | bootstrap resamples | **10000** (`RESAMPLES`) | `experiments/ptr-engine/longrun/analyze_stats.py:113` |
| T6 | bootstrap seed | **20261020** (`SEED`) | `experiments/ptr-engine/longrun/analyze_stats.py:114` |
| T7 | H1 direction rule | C `hi` < A `lo`; overlap ⇒ refused | `docs/PREREG-ARM-RUN.md:38-41` |
| T8 | H2 cache-inclusive margin | `C <= 0.95 × A` | `docs/PREREG-ARM-RUN.md:69` |
| T9 | H2 uncached margin | `C < 1.00 × A` | `docs/PREREG-ARM-RUN.md:70` |
| T10 | H3 fixed margin | loses **> 2 of 12** fails (2 passes) | `docs/PREREG-ARM-RUN.md:99` |
| T11 | H3 gate denominator | **x/12** | `docs/PARM-1-ERRATA.md:81` |
| T12 | H3 substantive decomposition | **x/9** and NONE flags | `docs/PARM-1-ERRATA.md:75-81` |
| T13 | H3 unadjudicable floor | decidable **< 8 of 12** ⇒ no verdict | `docs/PREREG-ARM-RUN.md:113` |
| T14 | McNemar discordant floor | **b+c >= 6** | `docs/PREREG-ARM-RUN.md:107`; `experiments/ptr-engine/longrun/analyze_stats.py:430` |
| T15 | McNemar alpha | **p < 0.05**, two-sided | `docs/PREREG-ARM-RUN.md:107`; `experiments/ptr-engine/longrun/analyze_stats.py:430` |
| T16 | promotion floor (scheduling only) | per-rep p50 gap **>= 100 ms** | `docs/PRICE-REPLICATION.md:156`; `docs/OPERATOR-BRIEF.md:48` |
| T17 | per-turn wall cap | **180 s** | `experiments/ptr-engine/longrun/cell.py:1824` |
| T18 | per-cell wall | **2880 s** | `experiments/ptr-engine/tools/tranch1_dryrun.py:63` |
| T19 | per-cell request ceiling | **900** | `experiments/ptr-engine/tools/tranch1_dryrun.py:62` |
| T20 | tranche cell count / turns | **10 cells × 48 turns** | `experiments/ptr-engine/tools/tranch1_dryrun.py:86-89` |

Hypothesis traceability: T1–T7 are H1; T8–T9 are H2; T10–T15 are H3; T16–T19 are operational and never
adjudicate a hypothesis.

## 8. Reads that remain open after the rows are visible

Stated now, before the data, so no later reader mistakes a judgement call for a measurement: the H2
denominator counts a turn's billed follow-up requests as part of that turn, so a turn whose own latency
row is absent but whose follow-ups exist contributes tokens to no completed turn and is dropped — a
reader could instead assign those follow-ups to the nearest completed turn, and that choice can move the
H2 means. It is frozen in §2 as "dropped", not as an omission.
