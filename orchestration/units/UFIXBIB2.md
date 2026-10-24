# UFIXBIB2 — close the md2tex regeneration hole for the UBIB1 bibliography repairs

**Status:** in progress (skeleton written before work)

## Purpose
`papers/encoder-crossover-190/submission/main.tex` is generated from `MANUSCRIPT.md` by
`scratch/uprep1/md2tex.py`. Regeneration silently loses two earlier hand-patches (UPAPER9 finding),
so the next regeneration ships a broken bibliography. Reproduce both, fix them **at the source**
(`REFERENCES.bib` + `md2tex.py`), regenerate, and prove idempotence.

## The two patches regeneration loses
1. `submission/main.tex:428` — sentence claiming the four externally-sourced entries are
   "carried as-is, each still missing a title/author/venue". True before UBIB1; its true source is
   `MANUSCRIPT.md:852-855`, already corrected by UPAPER9. Regeneration must emit the corrected
   sentence from `MANUSCRIPT.md`, not a hard-coded string.
2. `submission/main.tex:431-435` — five `\bibitem` lines. Regeneration drops UBIB1's repairs and,
   for `source_decider_stack_2026`, emits the placeholder
   "[Author and/or title not recorded ...]" because `REFERENCES.bib` has no author for it. Truth:
   it is an unpublished internal corpus document with no attributable author.

## Method
1. Back up `main.tex`; run `scratch/uprep1/md2tex.py` into `scratch/ufixbib2/`; diff vs shipped.
2. Fix `papers/encoder-crossover-190/REFERENCES.bib` (honest authorless representation) and
   `scratch/uprep1/md2tex.py` (emit that wording; keep `howpublished`/URL for the four repaired
   entries; take the :428 sentence from `MANUSCRIPT.md`). ASCII-only.
3. Regenerate; diff must be clean or only intended lines; second run byte-identical; 0 non-ASCII
   bytes; 12 `\bibitem` entries; quote UBIB1's five repairs.

## Do not
- merge `benayas2024comparative` (ambiguous; `BUILD_NOTES.md:54-55` records deliberate exclusion)
- reintroduce 125M-RoBERTa 94.27/70.87 (do-not-cite, unsourced)
- change any other scientific number or prose; if a fix would alter another line of `main.tex`, STOP and report
- touch `scratch/uneutral*/`, `MANUSCRIPT.md`, `CLAIMS.md`, `GAPS.md`, `submission/ABSTRACT_METADATA.txt`

## Write paths
`scratch/uprep1/md2tex.py`, `papers/encoder-crossover-190/REFERENCES.bib`,
`papers/encoder-crossover-190/submission/main.tex`, `orchestration/units/UFIXBIB2.md`,
`orchestration/handoffs/UFIXBIB2.json`, `scratch/ufixbib2/**`

## Hard bound
15 tool calls. Before every edit assert the before-string matches exactly once and record the
verbatim before/after in the handoff. Back up `main.tex` before regenerating.
