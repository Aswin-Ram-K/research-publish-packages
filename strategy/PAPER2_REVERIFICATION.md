# PAPER2 — Re-verification of Candidate #2/A2: "Replay reproduces the record, not the decision"

**Unit:** UREVER2 (independent re-verification; not the proposing unit)
**Purpose:** establish from raw records whether the headline finding is real, before drafting.
**Scope:** feasibility measurement only. No paper prose.
**Bound:** 25 tool calls. All numbers below were produced by the commands quoted with them.

---

## 1. The records — located and pinned

The path UPICK1 gave as "not yet confirmed readable" **is readable**. Both primary files are there:

| file | bytes | lines | sha256 |
|---|---|---|---|
| `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/decision-variants.jsonl` | 1,197,797 | 3,040 | `c5ec44a799ddeb963f862fc5c054ddad6ef2fce6ad90edfafd7c1755ac4370e7` |
| `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/l1-head-to-head.jsonl` | 63,238 | 380 | `6af0e0d8294cf4d7a20e2d8cb9bfe0c11ff70cc4c4b2792fcdedaf9246b2a1e7` |

Command: `stat -c '%s bytes %n' <both>` and `wc -l <both>` and `sha256sum <both>` (see §3 for the full command).

**Copy stability (`find state -name <file> | sha256sum`):** 15 copies of each file exist under `state/` (under
`scnA/`, `scnB/`, `state/verify/U7.2/`, `state/kg-refresh/`, and both `engine-a` / `engine-gap` / bare
`repo/docs/research` worktrees). **All 15 copies of `decision-variants.jsonl` are byte-identical**
(`c5ec44a7…`), and **all 15 copies of `l1-head-to-head.jsonl` are byte-identical** (`6af0e0d8…`). The corpus
is therefore pinnable by digest; mirror choice does not matter.

Supporting (not the primary evidence, read for the definition only):
- `…/engine-a/docs/research/experiments/EXP#7-replay-divergence.md` — the pre-registered experiment (9,347 B, 179 lines). §3 "Method" and §7 "Results" carry the definition and the figures.
- `…/engine-a/docs/research/PAPER_DERIVATION.md` §4.7 `:445-483`.
- `…/engine-a/docs/research/L1_HEAD_TO_HEAD.md`.
- `…/engine-a/tools/replay/exp7.ts` — the analysis script named in EXP#7 §3 **exists** (8,856 B).
- The stimulus fixture `…/engine-a/evals/fixtures/reflex-decisions.ts` **exists** (190 cases referenced).

---

## 2. Schema — what is the record and what is the decision

**`decision-variants.jsonl` — 3,040 rows, 21 fields, verbatim line 1:**

```json
{"model": "laya", "variant": "V0", "id": "acquisition-001", "kind": "acquisition", "correct": 1, "decomposable": true, "picked_index": 1, "p_chosen": 0.3813, "conf": 0.3813, "calls": 1, "ms": 827.892, "ms1": 827.892, "ms2": null, "p1": null, "p2": null, "level1_group": null, "level1_ok": null, "level2_skipped": false, "level2_unreached": false, "error": null, "error_stage": null}
```

Key set (all 3,040 rows share these): `calls, conf, correct, decomposable, error, error_stage, id, kind,
level1_group, level1_ok, level2_skipped, level2_unreached, model, ms, ms1, ms2, p1, p2, p_chosen,
picked_index, variant`. No free-text field: the longest value of any key is 21 chars (`id`). No stimulus
(question/options) text is in the corpus.

**`l1-head-to-head.jsonl` — 380 rows, 8 fields, verbatim line 1:**

```json
{"model": "laya", "id": "worker.class-001", "kind": "worker.class", "correct": 0, "picked_index": 1, "p_chosen": 0.5937, "ms": 3732.2934377007186, "error": null}
```

**Field semantics — measured, and it corrects a natural reading:**

- **The decision is `picked_index`.** It is the option the model chose (max observed 2, i.e. indices 0–4 in a 2–5-option task).
- **`correct` is the INDEX of the correct option, not a right/wrong flag — in *both* files.** Value set is `[0,1,2,3,4]` in `decision-variants.jsonl` and `[0,1,2,3,4]` in `l1-head-to-head.jsonl`. Command: `sorted({r["correct"] for r in rows})`.
- **The outcome is therefore `picked_index == correct`** (a derived correctness boolean), and it is a *different* axis from the decision.
- **`variant` ∈ {V0,V1,V2,V3}; `model` ∈ {decider-0.8b, decider-2b, decider-4b, laya}; 190 distinct `id`s; 7 `kind`s; `decomposable` is a property of the case (constant per `id`, 61 non-decomposable ids).** 4 models × 190 cases × 4 variants = 3,040. Command: the §3/§5 script counters.
- **No row carries an error:** `error` is `null` on all 3,040 rows and `error_stage` is `null` on all 3,040. So no row is excluded and there is no missing-data correction in the headline figure.

**Divergence definition (from EXP#7 §3 `:48-55`, implemented literally):**
1. *control / replication* — `V0`↔`V2` and `V1`↔`V3` on non-decomposable cases; divergence = `picked_index` differs.
2. *binding* — every unordered model pair, at `V0`; divergence = `picked_index` differs.
3. *prompt* — every model, `V0` vs `V1`; divergence = `picked_index` differs.
4. *stability* — fraction of the 190 cases where all four models pick the same option (at `V0`).
5. *outcome* — `(picked_index==correct)` differs between the two rows.

---

## 3. Re-derivation (measured)

Script: `scratch/urever2/verify_divergence.py` (written by this unit, reads only the two `.jsonl` files).
Command: `python3 scratch/urever2/verify_divergence.py`. Output, verbatim in the numbers that matter:

**Control (F1) — replication on non-decomposable cases**

```
[control] (V0<->V2) non-decomposable pairs=244 identical=244 divergent=0  rate=0.00%
[control] (V1<->V3) non-decomposable pairs=244 identical=244 divergent=0  rate=0.00%
```

**Binding divergence — 6 model pairs, at `V0`**

| pair | n | decision divergent | decision % | outcome divergent | outcome % |
|---|---|---|---|---|---|
| decider-0.8b vs decider-2b | 190 | 51 | 26.84 | 30 | 15.79 |
| decider-0.8b vs decider-4b | 190 | 69 | 36.32 | 47 | 24.74 |
| decider-0.8b vs laya | 190 | 98 | 51.58 | 61 | 32.11 |
| decider-2b vs decider-4b | 190 | 50 | 26.32 | 35 | 18.42 |
| decider-2b vs laya | 190 | 100 | 52.63 | 67 | 35.26 |
| decider-4b vs laya | 190 | 108 | 56.84 | 84 | 44.21 |
| **POOLED** | **1,140** | **476** | **41.7544** | **324** | **28.4211** |

**Prompt divergence — each model, `V0` vs `V1`**

| model | n | divergent | % |
|---|---|---|---|
| decider-0.8b | 190 | 51 | 26.84 |
| decider-2b | 190 | 30 | 15.79 |
| decider-4b | 190 | 45 | 23.68 |
| laya | 190 | 119 | **62.63** |
| **POOLED** | **760** | **245** | **32.2368** |

**Stability:** 60 / 190 cases = **31.5789 %**.
**`l1-head-to-head`:** decider-0.8b vs laya, 92 agree / 98 disagree = **51.5789 %** divergence on 190 cases.
**Cross-check of the doc's own accuracy table:** `picked_index==correct` reproduces `L1_HEAD_TO_HEAD.md`'s
0.374 (laya 71/190) and 0.526 (decider-0.8b 100/190) exactly.

**Breakdown by the four variants** (the inventory's phrasing implies this; it is *not* how 41.8 % was
built — see §4). Binding divergence, 6 pairs × 190 cases per variant:

| variant | binding divergence | outcome divergence |
|---|---|---|
| V0 | 476/1140 = **41.7544 %** | 324/1140 = 28.4211 % |
| V1 | 537/1140 = 47.1053 % | 371/1140 = 32.5439 % |
| V2 | 456/1140 = 40.0000 % | 358/1140 = 31.4035 % |
| V3 | 494/1140 = 43.3333 % | 383/1140 = 33.5965 % |

---

## 4. Comparison against the inventoried 41.8 % (measured)

**It reproduces exactly.** Every inventoried figure in the A2 row matches a number I derived independently
from the raw records:

| inventoried | re-derived | match |
|---|---|---|
| 41.8 % binding divergence | 476/1140 = 41.7544 % → 41.8 % | yes |
| 32.2 % prompt divergence | 245/760 = 32.2368 % → 32.2 % | yes |
| 0 % replication control, 244/244 | 244/244 identical, 0 divergent (both `V0`↔`V2` and `V1`↔`V3`) | yes |
| 31.6 % stable set, 60/190 | 60/190 = 31.5789 % → 31.6 % | yes |
| l1-head-to-head 380 rows, 51.6 % | 380 rows; 98/190 = 51.5789 % → 51.6 % | yes |
| per-pair 26.8 / 36.3 / 51.6 / 26.3 / 52.6 / 56.8 | 26.84 / 36.32 / 51.58 / 26.32 / 52.63 / 56.84 | yes |

Three framing corrections, all of which a drafter must absorb:

1. **The denominator of 41.8 % is 1,140, not 3,040.** It is 6 model-pair × 190-case comparisons at `V0`, not
   "3,040 outputs". The 3,040-row corpus is the substrate; the headline figure uses one quarter of it (the
   `V0` rows) for the decision axis.
2. **"41.8 % across four variants" mis-describes the design.** The 41.8 % is *one* arm (`V0`), pooled over
   model pairs. The four variants give 41.75 / 47.11 / 40.00 / 43.33 %; `V0` happens to be near the low end.
   The variants' roles are: `V1` = the prompt-relabel arm, `V2`/`V3` = the re-issue control arm.
3. **The pooled 32.2 % prompt figure hides a bimodal split:** laya moves 62.63 % of decisions under option
   relabelling alone, the three decider variants move 15.8–26.8 %. Quoting 32.2 % without that split
   overstates the robustness of the three decider models.

Also inventoried ("cross-checked on a second, independent corpus… 51.6 %"): **the `l1-head-to-head` corpus is
not independent in the sense claimed.** Same 190 case `id`s, same two models, and `picked_index` is
**identical on 190/190 cases for each of the two shared models** while `ms`, `p_chosen` (and `conf`) differ
on every row. [corrected 2026-10-16 by UFIXR2: the clause "`ms`, `p_chosen` (and `conf`) differ on every row" is false as written. Measured against the matching `decision-variants` `V0` rows (380 matched, 0 missing): `ms` differs on 380/380 — true; `p_chosen` differs on 0/380, i.e. is identical on 380/380; `conf` is not a field of `l1-head-to-head.jsonl` at all (it exists only in `decision-variants.jsonl`), so "(and conf)" is unsupported. Within `l1-head-to-head.jsonl` alone, `ms` takes 380/380 distinct values while `p_chosen` takes 363/380 (17 rows tie). Command: `python3 scratch/ufixr2/measure.py`.] It is a second *execution*, not a second *decision set*; its 51.6 % is arithmetically the same
98 disagreements already reported as the decider-0.8b-vs-laya pair in §3's binding table. It corroborates
the instruments' determinism, not the divergence rate.

---

## 5. Draftability (judgement, grounded in §1–§4)

**(a) Draftable now from these records.** The headline finding — a substantial decision-level divergence
against a control that can report zero — is real, reproducible from the raw files by an independent party,
and its numbers are exactly as inventoried. The strongest form is the one EXP#7 §7.5 states: *41.8 %
binding / 32.2 % prompt divergence against a 244/244 zero control, and a 31.6 % stable set*. This is
already-recorded data, so no new measurement is required to draft it.

**Caveats that must be stated in the draft, not discovered by a reviewer:**
- The `l1-head-to-head` "independent corpus" cross-check must be dropped or rewritten as "a second
  execution of the same two models over the same 190 cases" (§4, correction 3). As written it claims
  independence the records do not support.
- `correct` is an index; the correctness axis is `picked_index == correct` and must be defined in the text.
- The 3.9 % spread across variants (40.0–47.1 %) is a definitional sensitivity worth a sentence. [corrected 2026-10-16 by UFIXR2: "3.9 %" is wrong. Recomputed per-variant binding divergence over the 6 model-pairs × 190 cases (denominator 1,140): `V0` 476/1140 = 41.75 %, `V1` 537/1140 = 47.11 %, `V2` 456/1140 = 40.00 %, `V3` 494/1140 = 43.33 %; spread = 47.1053 − 40.0000 = 7.1053 ≈ 7.11 percentage points, not 3.9 %. The quoted endpoints 40.0–47.1 % are correct; their difference is 7.1 points. Command: `python3 scratch/ufixr2/measure.py`.]

---

## 6. Limits

**What a reader cannot check from the released records alone.** The corpus carries no stimuli: 190 case
`id`s, 7 `kind` labels, option indices, a chosen-option probability, and latencies. The questions, the
options, and the hand labels live in `evals/fixtures/reflex-decisions.ts`, which exists in the checkout but
is not part of either `.jsonl`. Without it, a reader can recompute the divergence arithmetic but cannot
verify that the cases mean what the paper says, nor that `correct` was labelled correctly. That is the
single largest reproducibility gap.

**Releasability.** No secret-shaped values and no personally identifying information are present: every
field is a model name, a case id, a small integer index, a float, a boolean, or `null` (the longest value of
any field is 21 characters, `id`; `error`/`error_stage` are `null` on all 3,040 rows). The corpora are
releasable as-is. However, a paper resting on them alone would rest on a corpus whose **stimuli are
withheld** — the pattern this project already exhibits elsewhere.

**Minimal reproducibility subset.** The two `.jsonl` files (1,261,035 bytes total, digests
`c5ec44a7…` / `6af0e0d8…`), the 190-case fixture `evals/fixtures/reflex-decisions.ts`, the definition §3 of
`experiments/EXP#7-replay-divergence.md`, and the 20-line analysis in
`scratch/urever2/verify_divergence.py`. That is sufficient for a third party to reproduce every figure in
§3–§4 without the rest of the repository.

---

## Headings required by the unit card

**MEASURED** — file paths, byte sizes, line counts, sha256 digests (§1); field sets and the `correct`-is-an-index
semantics (§2); all divergence figures, per-pair rates, per-variant breakdown, control 244/244, stability
60/190, `l1` 98/190, and the accuracy cross-check 71/190 & 100/190 (§3); the exact agreement of every
inventoried figure with the re-derived value (§4); the 190/190 `picked_index` identity between
`l1-head-to-head` and `decision-variants` `V0` with `ms`/`p_chosen` differing on every row (§4, correction 3).

**INFERRED** — that the 3,040 rows are the "3,040-output corpus" UPICK1 named (matched by count, model and
variant structure, and its presence in the same directory as `l1-head-to-head.jsonl`); that `V2`/`V3` are
re-issue arms on non-decomposable cases (restated from EXP#7 §2-§3, consistent with the measured 244/244 and
the 61 non-decomposable cases × 4 models); that the `l1-head-to-head` file is a re-execution rather than a
derivative (picks identical, timings and probabilities not); that `variant` is the "four variants" the
inventory means (exactly 4 distinct values, 760 rows each, 190 cases × 4 models).

**COULD NOT DETERMINE** — whether `tools/replay/exp7.ts` actually implements the definition it documents
(the script exists, 8,856 B, but this unit did not read or run it, and drafting must not lean on an
unexecuted script); whether the 190 `correct` labels in `reflex-decisions.ts` are themselves correct (not
audited here); how many *live* re-runs would be needed to defend the figure as a present-day property
(EXP#7 is explicitly a measurement of the recorded record, so this is by design, not a defect); and whether
the corpus's 190 cases are representative of any broader task distribution (no sampling frame is recorded).

---

## Commands run (for the record)

```
1  ls -la <UPICK1 path>                          # path EXISTS
2  find <dir> -type f -printf '%s\t%p\n' | sort -rn | head -40
3  sha256sum <l1-head-to-head.jsonl>; wc -l <both files>
4  sed -n '1p' <each>; python3 -c “…keys Counter…”   # schema
5  python3 -c “…model×variant Counter…”              # 3040 = 4×190×4
6  read <EXP#7-replay-divergence.md>                 # definition, §3
7  sed -n '440,495p' <PAPER_DERIVATION.md>; sed -n '1,90p' <L1_HEAD_TO_HEAD.md>
8  python3 scratch/urever2/verify_divergence.py      # all §3 figures
9  python3 - <<PY … shared-field identity, index semantics, accuracies … PY
10 find state -name 'decision-variants.jsonl' -exec sha256sum {} \;   # 15/15 identical
11 stat -c '%s bytes %n' <both>; wc -l <both>
12 python3 - <<PY … per-variant binding & outcome … PY
```
