# AVAILABILITY.md — what ships, what is withheld, and under what licence

> **Update 2026-10-19 (UPKG2C).** The stimulus is **no longer withheld**: the same 190 cases, with
> the same per-kind counts (30/30/26/22/26/28/28), release with the **companion note** (paper #3,
> Zenodo concept DOI `10.5281/zenodo.23463944`) under a different neutralised tagging. The tag
> correspondence is recoverable from the per-kind sequence of `correct` values; the mapping is stated
> in `MANUSCRIPT.md` §7. The "what is withheld" text below is retained as **dated history** and
> describes the release boundary as it stood before that date. What remains withheld is the
> pre-registration's analysis script `tools/replay/exp7.ts` (unexecuted and unreleased).

> **Update 2026-10-19 (UDOIBACK2).** The release now carries a persistent identifier: Zenodo
> **concept DOI `10.5281/zenodo.23482511`** (version record `23482512`, concept record
> `23482511`). Cite the **concept** DOI — it resolves to the latest version of the deposit; the
> version DOI dies at the next version. The licence statement below is unchanged: the paper's own
> text is CC BY 4.0 and the released artifacts are source-available under PolyForm Noncommercial
> 1.0.0. The release boundary described below is also unchanged.


## Summary for a reviewer

This note is a re-analysis of two record files already on disk. It ships no new data, trains nothing,
and runs no model. What it adds is an exact, recomputable statement of what those records show when
the pre-registered definitions are applied literally: a replication control that reports **zero**
divergence, a V0 binding divergence of **476/1,140 = 41.7544 %**, and the observation that the second
record file is not an independent corpus but the same disagreements re-serialised with different
timings. The whole release is **1,261,035 bytes** of JSONL plus the definition and the analysis script;
the stimuli that would make the numbers *mean* something are **withheld**.

## What ships

| Artifact | Size | What it is |
|---|---|---|
| `decision-variants.jsonl` | 1,197,797 B / 3,040 lines | Per-row records: `model`, `variant`, `id`, `kind`, `correct`, `decomposable`, `picked_index`, `p_chosen`, `conf`, `ms`, and bookkeeping. sha256 `c5ec44a799ddeb963f862fc5c054ddad6ef2fce6ad90edfafd7c1755ac4370e7` |
| `l1-head-to-head.jsonl` | 63,238 B / 380 lines | Same 190 cases, two models. sha256 `6af0e0d8294cf4d7a20e2d8cb9bfe0c11ff70cc4c4b2792fcdedaf9246b2a1e7` |
| `EXP#7-replay-divergence.md` §3 | — | The five measurement definitions this note applies literally (`:48-55`), plus the pre-registration and the recorded limits |
| Analysis scripts | — | `scratch/urever2/verify_divergence.py` (pool rates, controls, stability, L1 identity) and `scratch/udraft2/recompute_per_variant.py` (per-variant table, L1 timing/probability agreement, L1 accuracies) |

Total released record bytes: **1,261,035** (1,197,797 + 63,238).

**Author block: the author-supplied name.** The byline is `\author{Aswin Ram Kalugasala Moorthy}` in `main.tex` — the author’s own name, supplied verbatim, name only, with no affiliation, institution or contact stated or invented. **SUPERSEDED WORDING (2026-10-16, retained as dated history):** ~~**Author block: a placeholder slot.** The byline is not a supplied author line. `main.tex` carries `\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}`; the author pastes the real name before the paper is submitted. No name, no affiliation and no institution has been invented.~~ At drafting the byline had not been provided and this document recorded that; that was accurate then. (Corrected 2026-10-16 by UINSTALL3: the shipped package carries the real name.)

## What is withheld

- **The stimulus.** Neither record file carries a question or an option. The 190 cases, their options
  and their correct-answer labels live only in
  `…/engine-a/evals/fixtures/reflex-decisions.ts` (145,031 B), which is **not** part of this release.
  A reader can recompute every number in the note and can check nothing about what was being decided
  or whether a label is right (see `GAPS.md` G-01, G-02).
- **Variant definitions.** What V0–V3 each change is not recorded in the released files
  (`GAPS.md` G-06).
- **The instrument and its run.** `…/engine-a/tools/replay/exp7.ts` (8,856 B) is not shipped, not read
  by this unit, and not run (`GAPS.md` G-04). No live replay was performed (`GAPS.md` G-05).

## The minimal reproducible subset

To reproduce every number in `MANUSCRIPT.md` and `CLAIMS.md`, a reader needs exactly:

1. `decision-variants.jsonl` (1,197,797 B) and `l1-head-to-head.jsonl` (63,238 B);
2. the definition of the correctness axis: a row's outcome is `picked_index == correct`, where
   `correct` is an **option index in 0–4**, not a boolean — in both files;
3. the five §3 definitions from `EXP#7-replay-divergence.md:48-55`;
4. the two analysis scripts above (no dependencies beyond a Python 3 standard library).

The fixture is needed only to see the stimulus, not to reproduce the rates.

## Licence

The paper's own text is **CC BY 4.0** (author decision, 2026-10-15), as is the subset's **content**.
Released artifacts are **source-available under PolyForm Noncommercial 1.0.0** with a paid commercial
licence offered by the author. The main repository stays fully proprietary and closed. The source
repository's own `LICENSE` governs it and is not restated, copied, or resolved here.

## Data notes — the schema trap

In **both** record files the column named `correct` holds the **index** of the correct option
(0–4), not a boolean. A replicator who reads `correct` as a correctness flag will sum indices and
compute a meaningless accuracy (the analysis script's own naive accuracy line prints `202/190`, which
should already read as impossible). Accuracy must be computed as `picked_index == correct`. The
`decision-variants.jsonl` rows carry the decision in `picked_index` and the outcome via
`picked_index == correct`, on a different axis; conflating them is the second way to get a plausible-looking wrong number, and `EXP#7:148-150` records
that it happened once in the source analysis.
