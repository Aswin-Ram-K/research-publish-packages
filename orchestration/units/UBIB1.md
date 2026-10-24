# UBIB1 — Repair the defective bibliography entries; settle the arXiv abstract limit

**Status:** done (2026-10-15) · **Bound:** 20 tool calls, 20 used.

## Write paths (nothing else written)
`papers/encoder-crossover-190/submission/**`, `papers/encoder-crossover-190/REFERENCES.bib`,
`papers/encoder-crossover-190/REFERENCES_ADDITIONS.bib`, `strategy/BIBLIOGRAPHY_REPAIR.md`,
`orchestration/units/UBIB1.md`, `orchestration/handoffs/UBIB1.json`, `scratch/ubib1/**`.

## Purpose
Complete the five defective bibliography entries from primary sources without inventing metadata; cross-check
each against the manuscript's attribution; make only surgical edits to the inlined `thebibliography`; settle
arXiv's metadata abstract-length rule.

## What changed
* `REFERENCES.bib` 14,873 → 17,575 B: four entries (`arxiv2602_06370`, `arxiv2512_12677`, `pride2309_03882`,
  `gcd2305_13971`) gained `author`, `title`, `year`, `url` and a sourcing note; `source_decider_stack_2026`'s
  placeholder note was replaced with a no-author-by-design ruling. 12 entries, all brace-balanced.
* `submission/main.tex` 78,405 → 78,864 B: five `\bibitem` lines (431-435) replaced in place and one sentence
  at `main.tex:428` updated because it asserted the four entries were still incomplete. **No wholesale
  rewrite; 0 non-ASCII bytes; 0 remaining `to be completed before submission` placeholders.**
* `MANUSCRIPT.md`, `GAPS.md`, `AVAILABILITY.md`, `CLAIMS.md`: untouched.
* `/home/zer0null/Duval`, `/home/zer0null/research-publish-packages`: never written; no `git` run at all.

## Honest gaps (carried, not papered over)
1. `arxiv2512_12677` resolves to a patent-classification paper whose **abstract does not contain** the
   93.45 / 1.88 / 1.26 samples/s or the ">= 97 % teacher F1 at ~45x" claims the manuscript attributes to it —
   flagged UNVERIFIED; the PDF body would be needed.
2. `benayas2024comparative` (complete in `REFERENCES_ADDITIONS.bib`) was never merged into `REFERENCES.bib`
   and is absent from the printed list; `main.tex:428` is consequently stale about the 125M-RoBERTa claim.
3. arXiv's own API (`export.arxiv.org/api/query`) returned `HTTP 429 Rate exceeded.`; the abs pages were used.

## Result
Abstract limit **confirmed at 1,920 characters** (`https://info.arxiv.org/help/prep.html`), so the manuscript's
3,415-character abstract needs a **shortened metadata abstract** for the web form; the PDF abstract is not
bounded by it.

Full detail: `strategy/BIBLIOGRAPHY_REPAIR.md`.
