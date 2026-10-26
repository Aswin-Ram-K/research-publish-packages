# CLAIMS.md — every quantitative claim in `papers/replay-record-not-decision/MANUSCRIPT.md`, with its source

**Purpose.** Enforce that no number in the manuscript was invented. Every row is a quantitative or
factual claim in `MANUSCRIPT.md`, traced to a file, a field, or a named arithmetic derivation from other rows. Rows marked **RE-DERIVED** were
recomputed by this unit from the raw per-row data rather than read from a summary table; the command
is named so the recomputation can be repeated.

**Source paths** (relative to the workspace root):

| abbrev | path |
|---|---|
| **DV** | `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/decision-variants.jsonl` — 1,197,797 B, 3,040 lines, sha256 `c5ec44a799ddeb963f862fc5c054ddad6ef2fce6ad90edfafd7c1755ac4370e7` |
| **L1** | `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/l1-head-to-head.jsonl` — 63,238 B, 380 lines, sha256 `6af0e0d8294cf4d7a20e2d8cb9bfe0c11ff70cc4c4b2792fcdedaf9246b2a1e7` |
| **EXP7** | `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/experiments/EXP#7-replay-divergence.md` — 9,347 B, 179 lines |
| **FIX** | `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/evals/fixtures/reflex-decisions.ts` — 145,031 B, 190 cases |
| **R2** | `strategy/PAPER2_REVERIFICATION.md` — the re-verification record (237 lines) |

**Recomputation commands** (read-only; both read only **DV** and **L1**):

```
python3 scratch/urever2/verify_divergence.py         # pool rates, controls, stability, l1, pick identity
python3 scratch/udraft2/recompute_per_variant.py     # per-variant table, l1 ms/p_chosen/accuracy
```

For JSON files, rows cite the **field/key path** rather than a line number, because a line number in a
serialized JSON object is not a stable locator (house convention).

---

## A. Records, schema, and the fixture

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C01 | `decision-variants.jsonl` size | 1,197,797 bytes | **DV** (`stat -c %s`) | sha256 `c5ec44a7…` |
| C02 | `decision-variants.jsonl` rows | 3,040 | **DV** (`wc -l`) | |
| C03 | `l1-head-to-head.jsonl` size | 63,238 bytes | **L1** (`stat -c %s`) | sha256 `6af0e0d8…` |
| C04 | `l1-head-to-head.jsonl` rows | 380 | **L1** (`wc -l`) | |
| C05 | Combined released record size | 1,261,035 bytes | arithmetic: 1,197,797 + 63,238 | |
| C06 | Corpus shape | 3,040 = 4 models × 190 cases × 4 variants | **DV** `model`×`variant`×`id` counters | RE-DERIVED |
| C07 | Model set | `decider-0.8b`, `decider-2b`, `decider-4b`, `laya` | **DV** distinct `model` | RE-DERIVED |
| C08 | Variant set | V0, V1, V2, V3 | **DV** distinct `variant` | RE-DERIVED |
| C09 | Distinct case ids | 190 | **DV** distinct `id` | RE-DERIVED |
| C10 | Case kinds | 7: acquisition, capability.family, context.package, escalation, memory.admission, topology, worker.class | **DV** distinct `kind` | RE-DERIVED |
| C11 | Non-decomposable cases | 61 distinct ids | **DV** `decomposable == false` | RE-DERIVED |
| C12 | Field counts | 21 fields (**DV**), 8 fields (**L1**); one key set per file | **DV**, **L1** (`sorted(r)` counter) | RE-DERIVED |
| C13 | Missing data | `error` null on 3,040/3,040; `error_stage` null on 3,040/3,040 | **DV** fields `error`, `error_stage` | RE-DERIVED: no row excluded |
| C14 | `correct` is an index, not a flag | value set `{0,1,2,3,4}` in **both** files | **DV**/**L1** distinct `correct` | RE-DERIVED |
| C15 | The schema-trap example | **DV** line 1: `correct`=1, `picked_index`=1; **L1** line 1: `correct`=0, `picked_index`=1 (a wrong pick whose `correct` is 0) | **DV**/**L1** line 1 | RE-DERIVED |
| C16 | The trap was hit in the source analysis | reported 0 % outcome divergence for every pair before correction | **EXP7:148-150** | quoted, not measured here |
| C17 | Fixture that holds the stimuli | 145,031 bytes; 190 cases; questions/options/labels live only here | **FIX** (`stat`, case count) | withheld from release (C56) |

## B. Definitions and denominators

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C18 | Correctness axis | `picked_index == correct` | **DV**, **L1** derived | the derived boolean; `correct` alone is an index (C14) |
| C19 | Binding denominator | 1,140 = 6 model pairs × 190 cases at V0 | arithmetic on **DV** | **not** the 3,040-row corpus |
| C20 | Prompt denominator | 760 = 4 models × 190 cases | arithmetic on **DV** | |
| C21 | Control denominator | 244 = 61 non-decomposable ids × 4 models | arithmetic on **DV** `decomposable` | RE-DERIVED |
| C22 | Five measurements | control, binding (V0), prompt (V0 vs V1), stability, outcome | **EXP7:48-55** | definition of record, implemented literally |

## C. Binding divergence at V0 (6 model pairs × 190 cases)

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C23 | decider-0.8b vs decider-2b | decision 51/190 = 26.84 %; outcome 30/190 = 15.79 % | **DV** `picked_index`, `correct` | RE-DERIVED |
| C24 | decider-0.8b vs decider-4b | decision 69/190 = 36.32 %; outcome 47/190 = 24.74 % | **DV** | RE-DERIVED |
| C25 | decider-0.8b vs laya | decision 98/190 = 51.58 %; outcome 61/190 = 32.11 % | **DV** | RE-DERIVED |
| C26 | decider-2b vs decider-4b | decision 50/190 = 26.32 %; outcome 35/190 = 18.42 % | **DV** | RE-DERIVED |
| C27 | decider-2b vs laya | decision 100/190 = 52.63 %; outcome 67/190 = 35.26 % | **DV** | RE-DERIVED |
| C28 | decider-4b vs laya | decision 108/190 = 56.84 %; outcome 84/190 = 44.21 % | **DV** | RE-DERIVED |
| C29 | **Pooled binding divergence at V0** | **476/1,140 = 41.7544 %** (41.8 % rounded) | **DV** | RE-DERIVED; denominator 1,140, **not** 3,040 and **not** four variants |
| C30 | Pooled outcome divergence at V0 | 324/1,140 = 28.4211 % | **DV** | RE-DERIVED |
| C31 | Divergence ordering | siblings 26.3–26.8 %; vs laya 51.6–56.8 % | derived from C23–C28 | descriptive |

## D. Prompt divergence (each model, V0 vs V1)

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C32 | decider-0.8b | 51/190 = 26.84 % | **DV** | RE-DERIVED |
| C33 | decider-2b | 30/190 = 15.79 % | **DV** | RE-DERIVED |
| C34 | decider-4b | 45/190 = 23.68 % | **DV** | RE-DERIVED |
| C35 | laya | **119/190 = 62.63 %** | **DV** | RE-DERIVED; the split the pool hides |
| C36 | Pooled prompt divergence | 245/760 = 32.2368 % (32.2 % rounded) | **DV** | RE-DERIVED |
| C37 | Decider range | 15.79–26.84 % ("15.8–26.8 %") | derived from C32–C34 | |

## E. The replication control

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C38 | V0↔V2 control | 244 comparisons, 244 identical, 0 divergent | **DV** `decomposable==false`, `picked_index` | RE-DERIVED |
| C39 | V1↔V3 control | 244 comparisons, 244 identical, 0 divergent | **DV** | RE-DERIVED |
| C40 | The first run's inverted predicate | would have published "51 % replication divergence"; control caught it | **EXP7:139-154** | quoted, not measured here |

## F. Stability

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C41 | All-four-agree cases at V0 | 60/190 = 31.5789 % (31.6 % rounded) | **DV** | RE-DERIVED |
| C42 | "68.4 % of cases diverge" | 1 − 0.315789 = 0.684211 (130/190) | arithmetic on C41 | stated as 68.4 % (130/190) |

## G. Per-variant sensitivity

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C43 | V0 binding / outcome | 476/1,140 = 41.7544 %; 324/1,140 = 28.4211 % | **DV** | RE-DERIVED |
| C44 | V1 binding / outcome | 537/1,140 = 47.1053 %; 371/1,140 = 32.5439 % | **DV** | RE-DERIVED |
| C45 | V2 binding / outcome | 456/1,140 = 40.0000 %; 358/1,140 = 31.4035 % | **DV** | RE-DERIVED |
| C46 | V3 binding / outcome | 494/1,140 = 43.3333 %; 383/1,140 = 33.5965 % | **DV** | RE-DERIVED |
| C47 | Spread across variants | 40.0000–47.1053 % = **7.11 points** | arithmetic on C43–C46 | **correction:** `R2:171` says "the 3.9 % spread"; 47.1053 − 40.0000 = 7.1053, so the record's "3.9 %" is wrong. The claim here uses the derived 7.11. |

## H. `l1-head-to-head.jsonl` is not an independent corpus

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C48 | L1 divergence | 98/190 = 51.5789 % (51.6 % rounded) | **L1** | RE-DERIVED |
| C49 | L1 cases | the **same 190** case ids as **DV** | **L1** vs **DV** distinct `id` | RE-DERIVED |
| C50 | L1 models | the same two (`laya`, `decider-0.8b`), 190 rows each | **L1** `model` counter | RE-DERIVED |
| C51 | Picks vs **DV** V0 | identical `picked_index` on 190/190 per model | **L1** vs **DV** | RE-DERIVED |
| C52 | Same disagreements | the 190/190 same disagreement pattern as the V0 decider-0.8b-vs-laya pair | **L1** vs **DV** | RE-DERIVED; hence the 98 are the same 98 as C25 |
| C53 | Timings vs **DV** V0 | `ms` differs on 380/380 rows | **L1** vs **DV** | RE-DERIVED |
| C54 | Probabilities vs **DV** V0 | `p_chosen` **identical** on 380/380 rows; `ms` differs on 380/380 rows | **L1** vs **DV** | RE-DERIVED. `conf` is not a field of **L1** (its 8 keys are `correct`, `error`, `id`, `kind`, `model`, `ms`, `p_chosen`, `picked_index`); it exists only in **DV**. **Correction:** `R2:152` says `ms`, `p_chosen` and `conf` differ on every row — false for `p_chosen` as measured, and unevaluable for `conf`. |
| C55 | L1 accuracies (cross-check of the source's own table) | `laya` 71/190 = 0.3737; `decider-0.8b` 100/190 = 0.5263 | **L1**, derived `picked_index==correct` | RE-DERIVED via `picked_index==correct`; **not** the naive sum of `correct` |

## I. Antecedent (quoted, not verified here)

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C56 | The phenomenon is named *replay divergence* | "an LLM consumer of a deterministic event log produces different outputs under model or prompt changes" | **EXP7:16-17** | quoted from the pre-registration; arXiv 2605.20173 **not** fetched here |
| C57 | Withheld stimulus | the record files carry no question and no option text | **DV**/**L1** key sets (C12) | the failure mode the manuscript states |

## J. Rounding / framing claims

| # | Claim in the manuscript | Value | Source | Note |
|---|---|---|---|---|
| C58 | 41.7544 % → "41.8 %" | 476/1140 = 0.417544 | arithmetic on C29 | 1 dp |
| C59 | 32.2368 % → "32.2 %" | 245/760 = 0.322368 | arithmetic on C36 | 1 dp |
| C60 | 31.5789 % → "31.6 %" | 60/190 = 0.315789 | arithmetic on C41 | 1 dp |
| C61 | 51.5789 % → "51.6 %" | 98/190 = 0.515789 | arithmetic on C48 | 1 dp |
| C62 | Three framing corrections (denominator 1,140; one arm not four; prompt split) | as stated in **R2:137-147** | **R2:137-147** | the inventory's framing is wrong in these three places; the manuscript uses the corrected form |

---

## Coverage

- Quantitative/factual claims enumerated: **62 rows** (C01–C62).
- Rows with an explicit file or field source: **50 of 62**. The other **12** (C05, C19, C20, C21, C31, C37, C42, C47, C58–C61) are arithmetic derived from other rows rather than read from a file or field, and each names what it is derived from.
- Rows **RE-DERIVED** from the raw records by this unit: C06–C15, C19, C21, C23–C30, C32–C39, C41, C43–C54, C55, C57.
- Rows sourced from the records' own prose (quoted, not re-measured): C16, C40, C22, C56, C62.
- Values that appear in the manuscript but could **not** be traced to a file on disk: **none**. Two
  *corrections to the re-verification record* are carried at C47 and C54 and are marked as corrections,
  not as manuscript numbers.

**Where a claim was left unsourced, none — but three claims are deliberately *weak* rather than
unsourced:** the antecedent (C56, quoted not fetched), the case-set representativeness (§6, no sampling
frame exists on disk), and the stimulus validity (§6, the fixture is withheld). Those are in `GAPS.md`.

---

## Addendum — 2026-10-16 (unit UBIB2): related work and bibliography added

History retained. The rows above trace measured claims only, and section I states (C56) that the
antecedent arXiv 2605.20173 was quoted from the pre-registration and not fetched. That remained true.
On 2026-10-16 a related-work subsection (`MANUSCRIPT.md` section 1.1) and an eight-entry bibliography
(`REFERENCES.bib`; verification record `REFS.md`) were added for review. **No row above changed and no
measured number in the manuscript changed.** The new references are documentation apparatus: they
source no number in this note. The antecedent remains unverified and the manuscript says so.


## Update 2026-10-16 (UFIXBIB4) --- bibliography and byline statements corrected

Earlier statements in this record are superseded. They are retained above as history (nothing deleted);
this note is the current truth.

- Superseded: that paper #2 uses `bib_source="none"` / `expected_bib_count=0` / `expect_zero_bib` and
  "ships no bibliography", and that its shipped `main.tex` carries no `\cite`, no `\bibitem` and no
  `thebibliography` (e.g. BUILD_NOTES.md:28-35, :51, :56). Paper #2 now ships a REAL bibliography:
  `bib_source="bibtex_file"`, `bib_file="REFERENCES.bib"`, `expected_bib_count=8`, `expect_zero_bib=False`,
  8 `\bibitem`, 8 distinct cited keys, 0 uncited, 0 unresolved.
- Superseded: `test_zero_bibliography_guard` (BUILD_NOTES.md:48) and the byline test's "no citation
  apparatus" half. Replaced by `test_replay_bibliography_guard` and `test_ships_author_slot_and_bibliography`,
  which red/green-prove BOTH directions of the cite/bibitem invariant on paper #2 and byte-check the shipped
  artefact. Nothing was weakened, disabled or deleted; the replacement is strictly stronger. The old
  `assert_no_citation_apparatus` helper is retained in `tests/test_md2tex.py` as history, uncalled.
- Superseded: any statement that the shipped paper has an unfilled byline / author slot. The shipped
  `submission/main.tex` carries exactly one `\author{Aswin Ram Kalugasala Moorthy}`; zero occurrences of
  `placeholder slot`.
- Shipped artefact after this unit: `submission/main.tex` 26974 bytes, sha256
  `eb63dd174ff8a7f5a95e2a38fa3af50f9f3e0f1ceeb7afba4ad62f958a993416`; tarball
  `submission/replay-record-not-decision.tar.gz` 9642 bytes, sha256
  `b9a89837e2a4285cc97c7665534ca5c6e6a3ccafa89af0e81294e15279613294`, single member `main.tex`
  byte-identical to the on-disk file. **[UFIXNOTE5 2026-10-18: SUPERSEDED — the on-disk artefacts have since changed: `submission/main.tex` is now 28,604 B / sha256 `2059e12bda2612a4bcbe3cbb490dc5538a56d6754c71d3f48cab3ce3b74fcf7a` (241 lines), and `submission/replay-record-not-decision.tar.gz` is now 10,254 B / sha256 `48bc61ed4551ed3cc517f787df4c82144e5e8a8ef575eedd543951406a8beed3` (1 member `main.tex`). The values above were correct for UFIXBIB4.]**
  **[UDOCSYNC1 2026-10-19: SUPERSEDED — the on-disk artefacts moved again: `submission/main.tex` is now
  32,350 B / sha256 `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934`, and
  `submission/replay-record-not-decision.tar.gz` is now 11,425 B / sha256
  `e0973596e6237f7c1ea3ab6cedef21c0485800b69488f433ca0b324ea8e90797` (md5
  `720164891c8996a8bf7437ba81588602`, 1 member `main.tex`).]**
- Also recorded: two `\pdfpagewidth`/`\pdfpageheight` preamble lines came from the concurrent converter
  fix (scratch/ufixtex1), not from this unit; the body numeric-literal multiset changed only by
  {2026, 10, 16}, from this unit's two dated author-block sentences. `submission/main.tex` is generated --
  it was regenerated with `python3 tools/package/md2tex.py`, never hand-edited.
