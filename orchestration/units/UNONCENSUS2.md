# UNONCENSUS2 — classify the census-missed strings by provenance; measure MANIFEST source exposure

**Status:** in_progress (card written early; updated as classifications land)
**Hard bound:** 25 tool calls. Classify + measure only. No release-tree modification.
**Write paths:** `strategy/NONCENSUS_CLASSIFICATION.md`, `orchestration/units/UNONCENSUS2.md`,
`orchestration/handoffs/UNONCENSUS2.json`, `scratch/unoncensus2/**`.

## Purpose
UNONCENSUS1 proved `imajev` is a third-party public model (HF `mohit67890/imajev-4b`, apache-2.0,
base `Qwen/Qwen3.5-4B`) cited as an external contender, so it STAYS. The lesson: "not in our census"
!= "ours". Apply that provenance test to every other census-missed string in
`scratch/ubij3/tree-three-r2`, using `/home/zer0null/Duval` (read-only) + this workspace.

Categories: (a) third-party public (STAY) · (b) study's own name already public under CC BY 4.0 (STAY) ·
(c) internal & not otherwise public (neutralise) · (d) ambiguous (say what evidence is missing).

Also: measure MANIFEST.json `source`/`source_sha256` disclosure exposure. Do NOT build a neutralised
tree, do NOT re-run tokeniser-overlap diagnostics.

## Method (log as it happens)
- [ ] Read frozen census + NONCENSUS_LEAKS.md to fix the string list
- [ ] For each string: locate first definition/introduction (tree, Duval, this workspace)
- [ ] H-A / H-B: establish denotation before classifying
- [ ] LEAD / D09 / D15 / D25 rulings
- [ ] MANIFEST source exposure measurement (record manifest sha256)

## Outcome (final)
**done.** 16 of 19 census rows are (a) public citations or (b) names the released CC BY 4.0 manuscript already
uses — `H-A`/`H-B` are the two 200-case **held-out corpus strata** (`MANUSCRIPT.md:335`, `:498-500`), not arm
or hypothesis labels. Only `D09`/`D15`/`D25`/`D35`/`D44` are (c); `LEAD` and `no-union` are (d). The
"already-substituted neutral tag" claim at `strategy/COHERENT_BIJECTION_EXTENSION_2.md:277` is refuted by
`/home/zer0null/Duval/.worktrees/GATE-score/docs/DECISION_LOG.md:155,260,612`. MANIFEST exposure measured:
44/44 `source`, 40 `source_sha256` of non-shipped files, 41/43 origins outside the package.
Full rulings + literal evidence: `strategy/NONCENSUS_CLASSIFICATION.md`.
**Bound:** 25 allowed, 28 used (read-only + writes). No release tree touched.
