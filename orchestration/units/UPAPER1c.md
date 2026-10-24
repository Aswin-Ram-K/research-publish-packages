# UPAPER1c — apply UREFS's reference findings to the manuscript

**Unit:** UPAPER1c. **Workspace:** `/home/zer0null/reserach extarctor` (write only). **Target:**
`/home/zer0null/Duval` — **strictly read-only**, never written.
**Hard bound:** 50 tool calls. **Used:** ~33. **Status:** done.

## Purpose (one)

Apply the reference findings from unit **UREFS** to `papers/encoder-crossover-190/MANUSCRIPT.md`: merge the
sourced references into §2, **narrow the novelty claim**, and add the honest weakness the counter-case
exposes.

## Work order read

- `REFS_VERIFIED.md`, `REFERENCES_ADDITIONS.bib`, `RELATED_WORK_NOTES.md` (UREFS)
- `MANUSCRIPT.md` (§1, §2, §5, §6, References), `REFERENCES.bib`, `CLAIMS.md` (number cross-check only)

## Declared write paths (all touched; nothing else)

- `papers/encoder-crossover-190/MANUSCRIPT.md` (edited)
- `papers/encoder-crossover-190/REFERENCES.bib` (merged)
- `papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md` (new)
- `papers/encoder-crossover-190/UNSOURCED_RETAINED.md` (new)
- `orchestration/units/UPAPER1c.md`, `orchestration/handoffs/UPAPER1c.json`

**Not touched (owned by ULIC):** `CHECKLIST.md`, `OPEN_QUESTIONS.md`, `LICENSE_ANALYSIS.md`.
**Not touched:** `journal/`, `strategy/`, `jobs/`, `experiments/`.

## What was done

1. **References merged into §2** (`MANUSCRIPT.md` §2.1/§2.2, `REFERENCES.bib`). 7 entries added, 4 sourced
   (`simmering2025modernbert`, `zaratiana2024gliner`, `zaratiana2025gliner2`, `stepanov2025gliclass`) and 3
   kept marked **ADJACENT** (`kostina2025llmtextclassification`, `li2025smalllanguagemodels`,
   `weller2025seqvsseq`). The 5 pre-existing entries are preserved unchanged; the file header was updated.
2. **Novelty narrowed — 8 edits.** The counter-case is cited and **no priority is claimed for the direction**
   of "fine-tuned generative beats encoder" (abstract, §1 Thesis, new §1 "Novelty, stated narrowly",
   Contributions 1–2, §2.1, §5.1). Priority is claimed only for: the sealed typed single-label decision
   fixture, the option-order permutation control, and the majority-class control that outranks every head.
3. **The counter-case engaged** (§2.1): Simmering 2025 cited as a **blog post, not peer-reviewed, no DOI**,
   with the equal-effort numbers (93.1 vs 89.2; 152 vs 87 ex/s; 42 ex/s with vLLM prep) and the recognition
   that its **prompted** arm (80.7) corroborates the artefact thesis.
4. **Weakness added to §6** — new **§6.6**: the reviewer's under-training objection quoted in the reviewer's
   voice and answered as far as the evidence goes; the parts it cannot answer are named as open questions.
5. **Corpus correction carried** (§2.2): the "GLiNER = span extraction only" sentence is accurate for GLiNER
   2023/2024 but **not** for `fastino/GLiNER2.5-Decide` (a text-classification decision model).
6. **Unsourced items handled without invention:** the 125M-RoBERTa 94.27/70.87 figure is **dropped** and
   explicitly labelled unsourced; the literature-absence claim keeps its *"we were able to locate"* hedge
   (never upgraded to "no such work exists"). Recorded in `UNSOURCED_RETAINED.md`.
7. **The forbidden sentence was NOT imported:** `DECIDER_STACK_DECISION.md` §11.2's salvage (*"an encoder wins
   at equal training budget on closed label sets…"*) appears nowhere in `MANUSCRIPT.md` (grep: no match).

## Evidence / verification

- **Existing numbers unchanged: 0.** Occurrence check after editing: `0.6789`×24, `0.6684`×22, `0.3474`×28,
  `0.4526`×13, `0.2316`×6, `0.2911`×9, `0.1053`×7, `0.3316`×14, `0.3210`×10, `0.1595`×3, `4.167`×7,
  `0.6368`×2, `0.6650`×2. All copied verbatim from `CLAIMS.md`-verified values.
- **`REFERENCES.bib`:** 12 `@`-entries, 12 unique keys, balanced braces (122 `{` / 122 `}`, comments
  excluded).
- **Target read-only:** HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` **before and after**;
  `status --porcelain` identical both times (4 pre-existing untracked entries, attributed to the unrelated
  concurrent session: `.ci-trunk.txt`, `.relay/`, `docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`,
  `docs/migration/`); `git diff --stat` for tracked files empty — **no tracked file modified by this unit**.
- Full change log: `MANUSCRIPT_CHANGES.md`. Unsourced record + the queries already run: `UNSOURCED_RETAINED.md`.

## Handoff

`orchestration/handoffs/UPAPER1c.json` — status **done**, blocker empty.
