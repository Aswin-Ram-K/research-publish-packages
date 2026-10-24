# LICENCE_TODO.md — the code licence for this subset is **NOT YET DECIDED**

**Status: open. Do not publish this subset until this file is resolved.**

## The plain statement

The code licence for `repro/encoder-crossover-190/` has **not been chosen**. This unit (UREPRO) did **not**
pick one, did **not** draft one, and did **not** copy the target repository's `LICENSE` into this tree. Any
licence text added here by someone else is a decision that must be taken deliberately, by the author.

## What is known

- **Author intent (stated):** a licence under which **commercial use is not free**, and the intended
  approach is to **disclose the terms in pieces** rather than as one blanket grant.
- **Owner of the analysis:** unit **UCODE1** is analysing the options; the decision is the author's.
- **Papers are public.** By the author decision of 2026-10-15 the papers are CC BY 4.0. The fixture's
  *content* — `fixture/reflex-decisions.ts`, the hand-authored 190-case instrument — is covered by that
  decision as part of the paper's published material. This file concerns the **code** licence of the
  harness, the tooling scripts and the subset as a whole; it does not reopen the paper decision.
- **Third-party licences are already fixed and independent of this decision.** The harness fetches three
  **public** checkpoints at run time and records their licences in `harness/tcmodel.py`:
  `answerdotai/ModernBERT-base` (Apache-2.0), `microsoft/deberta-v3-base` (MIT),
  `sentence-transformers/all-mpnet-base-v2` (Apache-2.0). **No weights are shipped**, so no model licence
  is being redistributed here; the subset's licence cannot narrow those terms or relicense the checkpoints.
- **The measurement's own licence record.** `harness/tcmodel.py` carries a licence record for the arms;
  `results/REPORT.md` carries a licence caveat. Read them before choosing.

## The constraint that makes this urgent

**A published licence is permanent for that version.** Once a version of this subset is released under a
licence — on Zenodo, a public repo, a paper artefact, or anywhere a third party can obtain it — that grant
is irrevocable **for that version**, whatever the author later intends. A later version may carry different
terms, but the published version cannot be un-licensed, recalled, or retroactively narrowed. Therefore:

1. **Do not publish this tree until the licence is decided and written here.**
2. If a release is wanted before the analysis finishes, the author should decide whether to publish the
   **fixture and results only** (covered by the CC BY 4.0 paper decision, and the reproducibility subset's
   core) and hold the **harness code** back — rather than publish the code under a default that cannot be
   undone.
3. Because the intent is "disclose in pieces", the piecewise decision must be made **before the first
   publication**, not assembled after it.

## Action

- [ ] UCODE1 delivers its options analysis to the author.
- [ ] Author decides the code licence (and whether to split fixture/results from harness code).
- [ ] The chosen licence text is added at `repro/encoder-crossover-190/LICENSE` and this file is replaced
      with a one-line resolution naming the decision and its date.
