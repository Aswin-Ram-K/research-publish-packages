# PREREG-ARM-RUN — the arm comparison, frozen before any v6 data exists

**Unit:** `PREREG-ARM-RUN`. **Status:** FROZEN / DESIGN-ONLY. **Requests in this card: 0.**
**Rule id:** `PARM-1`. **Superseded by nothing yet.**

This document is the normative rule for the claim the operator actually wants settled
(board #438 / FINAL-GOAL `a2b5ff2d`):

> `pointer-stable` beats `transcript-grow` **at p95 TTFT** *and* **on total work**, at
> **equal-or-better verified quality**.

Everything between `<!-- parm-rule:begin -->` and `<!-- parm-rule:end -->` is the **rule body**;
its sha256 is recorded in §8, *outside* the body, together with a command that recomputes it.
Nothing in the body is a measurement: this card runs nothing, picks no final n, and declares no
arm better or worse.

<!-- parm-rule:begin -->
## 1. Hypotheses

The comparison is always `pointer-stable` (call it **C**) against `transcript-grow` (**A**), both
read out of one grid (§3). `transcript-compact` (**B**) and `lease-reopen` (**D**) are carried in the
same grid for context and are **not** part of the operator's claim; a C-vs-B or C-vs-D result is
reported as descriptive only and never as a win.

### H1 — latency (the p95 claim)

**Claim.** Within the adjudicating grid, C's **p95 TTFT per turn** is **lower** than A's.

- **Estimator (frozen):** `quantile_ci(values, q=0.95)` from
  `experiments/ptr-engine/longrun/analyze_stats.py:187-247` — linear-interpolated sample quantile
  (`_quantile_sorted`, `:112`), over that arm's admissibly-timed turns.
- **Interval procedure (frozen):** percentile bootstrap inside `quantile_ci`, `resamples=10000`,
  `seed=20261020` (`:73-74`), two-sided `LEVEL=0.95` (`:70`), clamped to bracket the point
  (`:238`). Printed by `render_estimate` (`:467`), which refuses a point without n and interval.
- **Admissibility (frozen, single place `:223`):** `n >= MIN_N (=20)` **and**
  `n*(1-q) >= TAIL_MIN (=3)`; at `q=0.95` that fixes **n ≥ 60** (`min_n_for`, `:167-172`). A p95
  at n=48 (RUN-C-V2's grid, where 48·0.05 = 2.4 < 3) is **refused**, not quoted with a caveat.
- **Ranking rule (frozen, conservative):** the CI must be *disjoint* —
  C's bootstrap **hi** < A's bootstrap **lo**. `analyze_stats.py` contains no paired quantile test
  (its paired machinery, `paired_by_turn` `:327` and `mcnemar_exact` `:267`, is for item outcomes),
  so disjoint 95 % intervals are the frozen ranking rule; overlapping intervals mean **no ranking
  claim**, and the run reports both estimates with their intervals.
- **What happens to a run that misses the n:** if the settled grid leaves any arm below n=60 usable
  timings (`quantile_ci` raises `InsufficientSamples`, and `analyze` records `refused` at
  `:550-551`), the run is **not adjudicable for H1**. The fallback is to report p50 with its
  interval and the refused p95 message verbatim — **never** to lower the threshold, and never to
  quote a nearest-rank p95 from `analyze_longrun.py`'s per-arm table as if it were the estimator.
- **Recorded p95 disagreement (do not silently resolve):** two p95 numbers already exist for the
  same RUN-C-V2 rows — `838.85 ms` / `356.12 ms` (interpolated, `measure/rows-longrun-c-2026-10-26.analysis.txt`)
  and `840.4 ms` / `371.7 ms` (nearest-rank, the `PER-ARM TABLE` in the same file). This rule binds
  **`analyze_stats.quantile_ci` only**; the nearest-rank numbers are described as the older
  reporting path and are not admissible evidence under H1.

### H2 — total work (primary; the hypothesis most likely to fail)

**Claim.** Within the same grid, C carries **fewer total prompt tokens per completed turn** than A.

- **Unit of account:** **prompt tokens**, summed over the arm's non-excluded, completed turns and
  divided by that same count. Not wall time (H1 already owns latency), not request count (identical
  by construction: one request per turn per arm), and not completion tokens as the primary — H3
  already owns answer behaviour, and a shorter answer is only a work saving if the prompt did not
  grow to buy it.
- **Primary field:** `prompt_tokens` (per row), cache-inclusive — the total the engine was billed
  for and the total the ledger records.
- **Second field (must agree):** uncached work, `prompt_tokens - cached_tokens` (with
  `cached_tokens` absent treated as 0 and counted). Rationale: a cached token is cheap in TTFT but
  is still prompt work, and a cache-inclusive total and a compute total can point opposite ways.
  H2 is ✓ **only if both** are lower for C by the materiality margin.
- **Materiality margin (frozen):** C's per-turn total must be **≤ 0.95 × A's** (a **5 %** reduction)
  on the primary field, and `< 1.00 ×` on the uncached field. The 5 % is a declared design choice,
  not a measurement: prompt tokens are deterministic for a fixed (fixture, arm, turn) — the frozen
  index prefix and the appended bodies are fixed text — so a win must not rest on a rounding-level
  difference. It says nothing about whether 5 % is *useful*, only what counts as "fewer".
- **Why primary:** the pointer design's whole mechanism is not re-sending history, so if it does not
  reduce carried prompt work then the p95 win — if any — is a serving artefact, not the thesis.
  Treat an H2 ✗ as the thesis's structural refutation even when H1 ✓.
- **Recorded disagreement with the card's premise (do not silently resolve):** this card's brief
  says RUN-C-V2 recorded pointer-stable with **the higher** total prompt tokens. Re-summed from
  `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` the direction is the opposite —
  A 901,109 prompt tokens / 48 turns (18,773 per turn), C 104,468 / 48 (2,176 per turn), B 185,617
  (3,867), D 20,628 (430) — and the same direction holds in every other row file on disk
  (`rows-longrun-v3`: A 3,563 vs C 2,214; `rows-longrun-v4`: A 5,428 vs C 4,071;
  `rows-longrun-2026-10-26`: A 2,771 vs C 1,862). Those grids were v2/v4 fixtures with 3 checkpoint
  items and a different prompt composition, and **no v6 rows exist**. The premise is therefore
  **not reproduced**, not refuted; H2 stays primary precisely because the v6 prompt composition (a
  wider `resolve.py` pin, twelve checkpoint turns, bodies appended after the frozen index) is
  exactly where C's constant prefix could stop dominating.

### H3 — quality guard (a veto, not a footnote)

**Claim.** C is **no worse** than A on **checkpoint accuracy over the decidable denominator** by
more than the stated margin.

- **Population:** `grade_v5.py` cells only, one per (arm, truth checkpoint), read through
  `accuracy_from_grade(grade, arm)` (`analyze_stats.py:431-463`). `decidable = pass + fail`;
  `undecidable` (verdict `text`) and `missing` (`reason == "turn_missing"`) leave the denominator
  and are printed by name. A row-derived denominator is **forbidden** (the v6 rows carry
  `answer_kind = null`, `:437-446`).
- **Margin (frozen): 2 checkpoints out of the 12 declared checkpoints = 16.7 percentage points.**
  It is a **fixed** margin in checkpoints, not a McNemar-defined one: at 12 items the exact
  two-sided McNemar can only reach p=0.0386 at a 10–2 split (`docs/CHECKPOINT-COVERAGE.md` §4), so
  a p-value-shaped margin would license a 3-checkpoint loss at some splits and refuse it at others.
  The margin is stated on the 12-item denominator, so "no worse than 2 checkpoints" and "no worse
  than 16.7 pp" are the same rule; a run that loses more than 2 checkpoints fails H3 even if the
  paired test is silent.
- **Secondary veto (when licensed):** if the paired item data reaches `b + c >= 6`
  (`mcnemar_exact`, `:295`) and the exact two-sided p < 0.05 with C worse (**c** = C-right/A-wrong),
  H3 fails regardless of the margin. Below 6 discordant pairs the test is refused (its message is
  quoted) and only the fixed margin decides.
- **Veto rule, stated plainly:** a quality **failure vetoes a latency win**. "Equal-or-better
  quality" is a **gate** on every other result in this document, not a footnote and not a tiebreak.
  If H3 ✗, no cell may report a win for C, whatever H1 and H2 say.
- **Unadjudicable clause:** if either arm's `decidable` is below **8 of 12**, H3 returns **no
  verdict** and the run is `not adjudicable`; it must not be read as a pass.

## 2. Endpoints and their exact sources

| endpoint | source (path, field) | admissible values / rule |
|---|---|---|
| `ttft_ms` | row JSONL, field `ttft_ms` | finite number; **`ttft_source == "unavailable"` is dropped** even when a number is present (`analyze_stats.py:376-398`), as are null/non-finite — each drop is counted, never coerced to 0.0 |
| `ttft_source` | row field | `"unavailable"` ⇒ out of the timing population; any other recorded source is in, and the per-source counts are printed beside the estimate |
| `wall_ms` | row field `latency_s` × 1000 (the rows carry seconds; `wall_ms` is that value, used descriptively only) | never an H1 input; reported per turn so a TTFT win cannot hide a total-latency loss |
| prompt tokens | row `prompt_tokens`; uncached = `prompt_tokens - cached_tokens` (`cached_tokens` absent ⇒ 0, counted) | H2 primary + secondary fields |
| completion tokens | row `completion_tokens` | descriptive only; not an H2 input |
| `stop_reason` | row `stop_reason` (closed vocabulary, `docs/STOP-REASON.md`) | **`PENDING: RECORD-STOP-REASON`** (card `3f5f1ee7-c687-47b7-bbb8-ed0db424453e`). Until it lands, the classification falls back to `finish_reason ∈ {length, max_tokens}` and `truncated == true`, and the fallback is named in the report. When it lands it *adds* a field; it changes which rows are `cap_truncated` (exclusion E3) and therefore the excluded fraction |
| checkpoint verdicts | `grade_v5.py` output document, `cells[]` with `arm`, `id`, `turn`, `verdict`, `reason`; arm summary `arms[arm].decidable` / `.checkpoint_accuracy` | `verdict ∈ {pass, fail, text}`; `reason == "turn_missing"` is missing, not fail |
| denominator | `decidable = pass + fail` per arm | `empty`/`absent`/prose answers are **undecidable**, never `fail`; they leave the denominator |

`grade_v5` output is the **only** accuracy input. If a report quotes `accuracy_from_grade`'s
`grade_decidable` beside its own `decidable` and the two differ, the difference is printed and the
run is flagged, not reconciled by hand.

## 3. The design

- **Arms (4):** `transcript-grow`, `transcript-compact`, `pointer-stable`, `lease-reopen`
  (`run_longrun.py:64`). H1/H2/H3 adjudicate **C = pointer-stable vs A = transcript-grow** only.
- **Turns per arm:** **48** — fixture `N = 48`
  (`experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json`), 12 work turns carrying the
  12 checkpoints plus verify turn 48.
- **Reps:** **`PENDING: BUDGET-SCHEDULE` (card `21254578-7b0e-4150-9c8f-3f89d31abdd8`)**. This card
  does **not** pick the final n. What the estimator needs is stated instead: each arm's usable
  timing population is `turns × reps` minus excluded turns, so H1 needs **reps ≥ 2** at N=48
  (96 raw turns; the admissibility rule is applied to the *usable* count after exclusions, so
  reps ≥ 2 is necessary, not sufficient). A settled schedule of reps = 1 makes H1 undecided by
  construction, and the run must say so.
- **Grid / strata:** one request per turn; quarters of the run (turns 1–12, 13–24, 25–36, 37–48)
  are reported as descriptive strata (`depth`), and checkpoint turns are
  **{6, 8, 12, 14, 18, 20, 24, 26, 32, 36, 42, 46}**. No H1 claim is made inside a stratum; strata
  exist so a latency win concentrated in the last quarter is visible.
- **The one grid in which H1 is adjudicated:** fixture `LR-01.v6.json`; served model
  `occamy-1.0-NVFP4`; engine `sglang`; `max_tokens = 4096`; `thinking = off`; `stream = true`; all
  four arms in the **same** grid with identical `fixture_sha256` and identical reasoning policy.
  Runs at another cap, another model, or with thinking on are **descriptive only** and can never
  overturn or support H1. (The cap-16,384 grid priced in `longrun/DESIGN-V3.md` is 27.2 h at the
  median and is not the adjudicating grid.)
- **12 checkpoint ids (the coverage gate's approved set — `docs/CHECKPOINT-COVERAGE.md` §2, and
  the ids read back from `LR-01.v6.json`; the two agree):**
  `cp.3.t06`, `cp.4.t08`, `cp.0.t12`, `cp.5.t14`, `cp.6.t18`, `cp.7.t20`, `cp.1.t24`, `cp.8.t26`,
  `cp.9.t32`, `cp.10.t36`, `cp.11.t42`, `cp.2.t46`.
- **Recorded id disagreement (do not choose silently):** every row file on disk carries the **v2**
  checkpoint ids `cp.t12`, `cp.t24`, `cp.t46` (3 items, plus `acc.*` checks), because those grids
  ran against `tasks-v2/runtime-v2/LR-01.v2.json`. The 12 ids above exist only in the v6 fixture.
  Therefore **no existing row file can adjudicate H3**: accuracy for this rule must come from rows
  produced against `LR-01.v6.json`, and any report that mixes v2-id cells with the v6 denominator
  is void.
- **Where the design cannot supply the n:** if the settled schedule funds fewer than 2 reps, or
  exclusions leave any arm below 60 usable timings, H1 is reported as **refused with its CI and the
  estimator's own refusal message**. The standard is not lowered.

## 4. Exclusion rules (written before the data)

A turn is excluded for one of these **named mechanical** reasons, and for no other:

| id | name | mechanical test |
|---|---|---|
| E1 | `host_error` | `http_status` null/0, or ≥ 500, or a transport/connection error is recorded; `failed_turn == true` with no HTTP status is E1 |
| E2 | `http_failure` | `400 <= http_status < 500` |
| E3 | `cap_truncated` | `truncated == true`, or `finish_reason ∈ {length, max_tokens}`; once `RECORD-STOP-REASON` lands, `stop_reason == "cap"` |
| E4 | `digest_mismatch` | the row's `fixture_sha256` or `run_manifest_sha256` differs from the freeze the run declared |

- **An arm's bad answer is never an exclusion.** A wrong, wrong-headed, truncated-*answer*
  (content present, cap hit) or absurdly verbose answer is **graded**, not deleted; only E1–E4
  remove a turn, and E3 removes it because the turn did not finish its work, not because its
  answer was poor.
- **`ttft_source == "unavailable"` is not an exclusion.** It removes that turn from the *timing*
  population only (`analyze_stats.py:383`), and its count is reported next to the estimate; the
  turn still counts for H2 and H3.
- **Counting is mandatory per arm:** `excluded` counts by reason per arm, plus the timing drops
  (`dropped_null`, `dropped_unavailable`), are printed for every arm in every report.
- **Not-adjudicable threshold:** if excluded turns exceed **10 % of an arm's turns**, that arm's
  columns are `not adjudicable`; if the run-wide excluded fraction exceeds **10 %**, the whole run
  is `not adjudicable` — reported as such, with the excluded table, and no verdict of any kind.

## 5. The decision matrix

H1 (p95 TTFT lower) × H2 (total work lower) × H3 (quality not worse by > 2/12). Verdict wording is
fixed so the operator gets the same sentence whichever cell the data lands in.

| # | H1 | H2 | H3 | verdict | wording to the operator |
|---|---|---|---|---|---|
| 1 | ✓ | ✓ | ✓ | **CONFIRMED** | "pointer-stable beats transcript-grow on p95 TTFT (C hi < A lo) and on total prompt work per completed turn, with quality no worse than 2 of 12 checkpoints. The operator's three-part claim holds in this grid." |
| 2 | ✓ | ✓ | ✗ | **QUALITY VETO** | "Latency and work both favour pointer-stable, but the quality gate fails by more than 2 of 12 checkpoints (or a licensed McNemar finds it worse). Equal-or-better quality is a gate, so no win is claimed; the thesis is not supported." |
| 3 | ✗ | ✓ | ✓ | **DEAD AT LATENCY** | "Total prompt work is lower for pointer-stable but p95 TTFT is not distinguished (intervals overlap or the p95 was refused at n<60). Work alone does not satisfy the claim; the thesis as stated is not supported." |
| 4 | ✗ | ✗ | ✓ | **THE THESIS IS DEAD** | "In the adjudicating grid pointer-stable shows neither a p95 TTFT win nor a total-work win while quality holds. **The thesis is dead**: the pointer design does not pay on either cost axis, and the quality result removes quality as the explanation." |
| 5 | ✗ | ✗ | ✗ | **THE THESIS IS DEAD (with a quality regression)** | "Neither cost axis favours pointer-stable and its quality is worse by more than 2 of 12 checkpoints. The thesis is dead and the arm is additionally unacceptable on quality." |
| 6 | ✓ | ✗ | ✗ | **DEAD (work + quality)** | "A p95 TTFT win is recorded, but total prompt work is not lower and quality fails. The win is a serving artefact; the thesis is not supported." |
| 7 | ✗ | ✓ | ✗ | **DEAD (latency + quality)** | "Work is lower, but p95 TTFT is not distinguished and quality fails. The thesis is not supported." |
| 8 | — | — | ✗ | *(subsumed by the cells above)* | H3 ✗ never appears without a cost column, so it always lands in cell 2, 5, 6 or 7. |

- **The canonical death cell is #4 (`H1 ✗ ∧ H2 ✗ ∧ H3 ✓`)**: both cost axes fail while the quality
  gate passes, which is the only combination that attributes the failure squarely to the mechanism
  rather than to the answers. Cell #5 states the same death with a quality regression attached.
- A cell with any `—` (unadjudicable: H1 refused for n, H3 below 8/12 decidable, or exclusions over
  10 %) produces **no verdict** and the sentence: "the run is not adjudicable on <axis>; the
  operator's claim is neither confirmed nor refuted, and no arm is declared better or worse."

## 6. Stopping rule

The run is stopped early and reported as a **negative result** — not as a pending run — on any of:

1. **Cost ceiling reached before the planned n.** `PENDING: BUDGET-SCHEDULE` (card `21254578`) owns
   the request numbers and the ceiling; until it settles, the ceiling is `PENDING` and no request
   count is stated here. When it costs out, its ceiling replaces this placeholder verbatim. The
   stop itself: stop at the last complete (rep, turn) boundary, report observed n, and refuse the
   H1 ranking claim if n < 60.
2. **Repeated cap truncation.** If any arm's E3 rate exceeds 10 % (or the run-wide rate exceeds
   10 %), stop and report: the cap is an instrument setting that the grid must hold constant, and
   a truncated comparison measures the cap, not the arms. (Reference point, sourced: RUN-C-V2's
   cap-4,096 grid truncated 15 of 192 turns, with 14 of them in `lease-reopen` alone — the reason
   a per-arm rate, not a run-wide total, is the trigger.)
3. **Harness digest drift.** If `fixture_sha256`, `run_manifest_sha256`, or the grader's rule-body
   digest changes mid-run, stop: cells before and after the drift are different instruments and may
   not be pooled. Report which digest moved and at which turn.
4. **A judge that fails its own attack.** Before any grid is spent, `grade_v5` must catch the
   directed-attack fixture (`longrun/QUALITY-POSITIVE-CONTROL.md`). If it does not, H3 has no
   instrument: stop, and H3 is `unadjudicable` for this rule — a green quality number from a judge
   that cannot fail its own attack is not a quality result.
5. **Estimator inadmissibility at the end.** If the surviving n leaves p95 refused (`n < 60` per
   arm), stop the ranking attempt and report the interval and refusal text; do not attribute the
   stop to the arms.

A stopped run keeps every completed turn, publishes the excluded table, and states which clause
stopped it. Cost overruns discovered after the fact are reported as overruns, never back-dated as a
pre-planned n.

## 7. What this card does NOT do

- It **runs nothing**: zero inference requests, no cell, no re-grade, no `git`.
- It **does not pick the final n or reps** — that is `PROJECTION-CALIBRATION`
  (`c0c7d1c8-8fc5-41ed-958e-df92d2188d66`) for the projection and `BUDGET-SCHEDULE`
  (`21254578-7b0e-4150-9c8f-3f89d31abdd8`) for the schedule and ceiling.
- It **does not declare any arm better or worse**, and it quotes no verdict for any existing grid.
- It **does not edit** any row file, grade file, fixture, or any of `cell.py`, `run_longrun.py`,
  `client.py`, `grade_v5.py`, `analyze_stats.py`, `fixture_coverage.py`, `matrix_audit.py`,
  `handoff_lint.py`, `det_verify.py`, `frozen_tree.py`, `request_ledger.py`.
<!-- parm-rule:end -->

## 8. Attestation (the self-freeze)

The digest below is the sha256 of the **rule body only** — the lines strictly between
`<!-- parm-rule:begin -->` and `<!-- parm-rule:end -->`, joined with `\n` and terminated by one
`\n`, read as UTF-8, nothing stripped. Because the digest is recorded *outside* the delimited body,
it is stable: any later edit inside the body changes it, and a later reader can tell whether the
rule moved after the data arrived.

```
python3 - <<'PY'
import hashlib, pathlib
t = pathlib.Path('docs/PREREG-ARM-RUN.md').read_text(encoding='utf-8')
body = t.split('<!-- parm-rule:begin -->\n',1)[1].split('<!-- parm-rule:end -->',1)[0]
print(hashlib.sha256(body.encode('utf-8')).hexdigest())
PY
```

- written at (UTC): `2026-10-26T15:41:12Z`
- **sha256 of the PARM-1 rule body:** `21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8`
- copies of the same digest: `experiments/ptr-engine/measure/PREREG-ARM-RUN.json` →
  `rule_sha256`, and `orchestration/handoffs/PREREG-ARM-RUN.json` → `evidence.rule_sha256`.

## 9. Provenance of every figure in this document

| figure | source |
|---|---|
| `MIN_N=20`, `TAIL_MIN=3`, `LEVEL=0.95`, `RESAMPLES=10000`, `SEED=20261020`, p95 ⇒ n≥60 | `experiments/ptr-engine/longrun/analyze_stats.py:70-74`, `:167-172`, `:223` |
| bootstrap interval, rank-span reference interval | `analyze_stats.py:187-247`, `:139-160` |
| McNemar refuses `b+c<6`; 10–2 split p=0.0386 | `analyze_stats.py:267-304`; `docs/CHECKPOINT-COVERAGE.md` §4 |
| `decidable = pass + fail`; v6 rows carry `answer_kind = null` | `analyze_stats.py:431-463` |
| 12 checkpoint ids and their turns | `docs/CHECKPOINT-COVERAGE.md` §2; ids re-read from `LR-01.v6.json` |
| arms (4) and 48 turns | `run_longrun.py:64`; `LR-01.v6.json` `"N": 48` |
| RUN-C-V2 p95 838.85 / 356.12 vs nearest-rank 840.4 / 371.7 | `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.analysis.txt` |
| per-arm prompt tokens (A 901,109 … D 20,628) | re-summed from `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` |
| truncation 15/192, 14 in `lease-reopen` | same row file (`truncated` flag) and its run summary line |
| cap-16,384 grid = 27.2 h median | `experiments/ptr-engine/longrun/DESIGN-V3.md` |
| `stop_reason` not yet recorded | `orchestration/handoffs/RECORD-STOP-REASON.json` (`status: partial`); the rows carry `finish_reason`, not `stop_reason` |
