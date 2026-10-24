# UABSTRACT1 — arXiv metadata abstract (≤1920 chars)

**Purpose.** Produce `papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt`: a plain-ASCII,
citation-free, LaTeX-free metadata abstract of at most **1,920 characters including spaces**, for the
manuscript at `papers/encoder-crossover-190/MANUSCRIPT.md` (abstract copied at
`papers/encoder-crossover-190/submission/ABSTRACT.txt`, 3,415 chars).

**Confirmed rule (quoted).** `https://info.arxiv.org/help/prep.html`, section "Abstract: required":
"Keep it short — abstracts longer than 1920 characters will not be accepted; abridge your abstract if
necessary." (verified by unit UBIB1).

**Must preserve.**
- Question: whether a cheap encoder-style classifier can substitute for a heavier decision model on a
  sealed single-label decision task.
- Design: five encoder-based arms plus a decider, on a sealed 190-case fixture.
- Result: best encoder arms κ ≈ 0.347 vs decider ≈ 0.668 (separation ≈ 0.33); majority-class floor
  0.4526; shuffled-label control 0.2316; paired test p ≈ 4.2e−09.
- Scope: one task, one corpus, one decision model; evaluation harness withheld, so recorded results are
  verifiable but the measurement cannot be re-run.
- Conclusion: encoders do not substitute; failure mode is characterised, not merely reported.

**Must not.** Invent numbers; claim generality; drop the scope sentence; name/describe the author's
withheld system (code-agnostic release — describe the task generically).

**Source to read.** `MANUSCRIPT.md` abstract + introduction + results (so the shortened version states
what the paper actually shows).

**Write paths (nothing else).**
`papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt`,
`orchestration/units/UABSTRACT1.md`, `orchestration/handoffs/UABSTRACT1.json`, `scratch/uabstract1/**`.

**Hard bound.** 10 tool calls. Stop condition: if the source abstract cannot be read within 3 calls,
STOP and report `failed` with the blocker.

**Forbidden.** Editing `MANUSCRIPT.md`, `ABSTRACT.txt`, `main.tex`, or any other file (a peer unit is
regenerating `main.tex` concurrently). `/home/zer0null/Duval` is read-only; never write
`/home/zer0null/research-publish-packages`.
