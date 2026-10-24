# GAPS.md — what this note does not establish, and what would establish it

> **Update 2026-10-19 (UPKG2C).** Gap A below — "the stimulus is withheld" — is **closed by
> reference**, not by shipping a fixture in this release: the companion note releases the same 190
> cases, with the same per-kind counts, under a different neutralised tagging (paper #3, Zenodo
> concept DOI `10.5281/zenodo.23463944`; correspondence in `MANUSCRIPT.md` §7). The gap text below is
> retained as **dated history**. The related limits that are *not* closed: neither release states the
> tag mapping as a table (it must be recovered from the per-kind sequence of `correct` values), and
> the fixture's labels remain unaudited for defensibility. The analysis script remains unexecuted.


Scope of this note: one task family, one frozen corpus of 190 cases, four model configurations, four
variants, two record files. Everything below is a limit of **evidence**, not a defect of the note. No
gap here is closed by argument; each names the artifact that would close it. (Numbering G-01…; grouped
by the kind of gap.)

---

## A. The stimulus is withheld — the central gap

**G-01 — A reader cannot see the cases, the options, or the correct answers.**
The two released record files carry no question text and no option text. `decision-variants.jsonl`
holds, per row, the model, variant, case id, kind, `correct` (an index), `decomposable`,
`picked_index`, `p_chosen`, `ms`, and bookkeeping fields — no stimulus. The same is true of
`l1-head-to-head.jsonl`. The stimuli exist only in
`…/engine-a/evals/fixtures/reflex-decisions.ts` (145,031 B, 190 cases), which is **not** part of the
record release.
*Consequence:* a reader can recompute every divergence rate in this note from the released files, but
**cannot** judge whether any individual divergence was a reasonable disagreement or an error, cannot
see what was being decided, and cannot check that a `correct` label is actually correct. The numbers
are checkable; their meaning is on trust.
*What would establish it:* releasing the fixture alongside the records (or a redacted, difficulty-
matched subset of it), so the trace can be read against the case it claims to encode. Until then this
gap is unclosable and the note says so.

**G-02 — The `correct` labels are not audited.**
The 190 labels come from the fixture and are used as given. This unit did not, and cannot, verify that
the labelled option is correct for its case.
*What would establish it:* a labelled audit of the fixture against the task's own acceptance criteria,
or an external ground-truth source per case.

## B. The timing file is not an independent corpus (the cross-check is void)

**G-03 — `l1-head-to-head.jsonl` cannot corroborate the divergence rate.**
It is not independent: the same 190 case ids, the same two models (`laya`, `decider-0.8b`), and the
identical `picked_index` on 190/190 rows per model versus the V0 rows of `decision-variants.jsonl`.
Its 98/190 = 51.5789 % divergence is the **same 98 disagreements** as the V0 decider-0.8b-vs-laya pair,
not a second measurement of them. The note therefore does not use it as corroboration. The only
difference it carries is timing (`ms` differs on 380/380 rows) — and even that is thin, because
`p_chosen`/`conf` are **identical** on 380/380 rows, which is what a re-serialisation of the same run
would produce, not necessarily a fresh run. The unrelated claim in
`…/experiments/EXP#7-replay-divergence.md:137` ("agrees independently at 51.6 %") is wrong on this
evidence.
*What would establish an independent cross-check:* a corpus over **different cases or different
models**, pre-registered before it is read; or releasing two runs of the same corpus with distinct run
provenance so the timing difference is interpretable.

## C. What was measured here, and what was not

**G-04 — The instrument itself was not inspected or run.**
`…/engine-a/tools/replay/exp7.ts` (8,856 B) is documented as implementing the five measurements. This
unit did not read it and did not run it; it re-implemented the §3 definitions
(`…/experiments/EXP#7-replay-divergence.md:48-55`) directly over the raw rows and reproduced every
published figure. That shows the definitions, applied literally, give these numbers; it does **not**
show that the tool implements those definitions.
*What would establish it:* a read of `exp7.ts` against §3, plus a run of it over the same inputs with
the outputs compared to the recomputation.

**G-05 — No live replay was performed.**
This is a study of a frozen record, not a re-run. Nothing here shows what happens when the recorded
trace is replayed against a live model now. `EXP#7:42` states "no live model, no new calls" as the
design; this note preserves that bound.
*What would establish it:* a pre-registered live replays of the traces, with the same divergence
estimator applied to fresh outputs.

**G-06 — The variant semantics are unknown.**
V0–V3 are used as given, and the per-variant binding rates range 40.0000–47.1053 % (a 7.11-point
range). What each variant *changes* is not recorded in the released files, so this note treats the
spread as a **definitional sensitivity** — the headline depends on which variant is called the record —
not as a finding about variants.
*What would establish it:* the variant definitions from the experiment record, so V0 can be justified
as the canonical record or the range reported as the result.

## D. Generalisation and extrapolation

**G-07 — No sampling frame; 190 cases and one task family.**
The 190 cases span 7 kinds (`acquisition`, `capability.family`, `context.package`, `escalation`,
`memory.admission`, `topology`, `worker.class`). There is no recorded frame from which they were
sampled, so the note cannot say they represent the task family, let alone any other. The rate is a
property of this corpus.
*What would establish it:* a stated sampling frame and a held-out corpus drawn from it.

**G-08 — The figure is per decision, not per trajectory.**
41.7544 % is the share of model-pair × case decisions at V0 on which the picks differ. `EXP#7:156-171`
notes a trajectory-level figure would be worse, because per-step divergence compounds; no
trajectory-level number exists in the records, so the note reports only the per-decision rate and does
not extrapolate.

**G-09 — The timing difference is unexplained.**
`ms` differs on 380/380 rows between the two files while `p_chosen`/`conf` are identical. Whether this
is re-serialisation, a re-run sharing outputs, or something else cannot be settled from the two files.
*What would establish it:* run provenance (timestamps, run ids, or a documented export path) for each
file.

---

## Closing note on what the note *can* support

The note's claim is deliberately narrow: applied literally to this frozen record, the five §3
definitions give a replication control of 0/244 divergent and a V0 binding divergence of
476/1,140 = 41.7544 % (outcome axis 324/1,140 = 28.4211 %), with the all-four-agree set at 31.5789 % of
cases. Every one of those numbers is recomputable from the released records by anyone. What a reader
cannot do is see the stimulus (G-01) or trust that the labels are correct (G-02) — and those are the
two things the note refuses to paper over.

---

## Addendum — 2026-10-16 (unit UBIB2)

The gap log above is retained as written. Two entries need a dated update rather than a rewrite:

* The note now cites eight external works in a related-work subsection. That addresses the
  "cites nothing" state of the paper; it does **not** close G-01/G-02 (stimulus withheld, labels
  unaudited), which remain the central gaps.
* The antecedent arXiv 2605.20173 is still not independently fetched. The related-work subsection
  says so explicitly and makes no claim rest on it.


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
  byte-identical to the on-disk file. **[UDOCSYNC1 2026-10-19: SUPERSEDED — the on-disk artefacts have
  since changed: `submission/main.tex` is now 32,350 B / sha256
  `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934`, and
  `submission/replay-record-not-decision.tar.gz` is now 11,425 B / sha256
  `e0973596e6237f7c1ea3ab6cedef21c0485800b69488f433ca0b324ea8e90797` (1 member `main.tex`).]**
- Also recorded: two `\pdfpagewidth`/`\pdfpageheight` preamble lines came from the concurrent converter
  fix (scratch/ufixtex1), not from this unit; the body numeric-literal multiset changed only by
  {2026, 10, 16}, from this unit's two dated author-block sentences. `submission/main.tex` is generated --
  it was regenerated with `python3 tools/package/md2tex.py`, never hand-edited.
