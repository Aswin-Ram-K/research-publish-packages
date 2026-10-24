# UMERGE1 — act on UBEN1's ruling: merge `benayas2024comparative`, rewrite the falsified sentence, fix stale records

**Unit:** UMERGE1. **Date:** 2026-10-16. **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a.
**Purpose (one):** make the paper's sentences *true* again after UBEN1 proved by primary fetch that a
sentence at `MANUSCRIPT.md:182-190` (echoed `:681-683`) is false, and that a reference listed as
"not found" exists. Do not re-derive UBEN1's sourcing; verify only that the sentence is still as described.

## Prior unit's evidence (taken as given, spot-verified only)
- DOI `10.1007/s10579-024-09796-y` resolves HTTP 200; Crossref matches
  `papers/encoder-crossover-190/REFERENCES_ADDITIONS.bib:109-145` field-for-field.
- The source says "approximately 110-120 million parameters" and **never** prints "125M"; it never
  prints "+23.4 F1".
- Therefore the sentence "still has no locatable identifier" is false.

## Tasks
1. Quote the current sentence + both echo sites verbatim; assert each before-string occurs exactly once.
2. Merge `REFERENCES_ADDITIONS.bib:109-145` into `papers/encoder-crossover-190/REFERENCES.bib`; reconcile
   the claim at `REFERENCES.bib:80-82` that additions were already merged.
3. Rewrite the sentence truthfully using `strategy/ROBERTA_CLAIM_SOURCING.md` §5 wording; **do not**
   reinstate `94.27`/`70.87`/`+23.4` (do-not-cite policy, `orchestration/units/UPAPER9.md:65`);
   fix/drop the "125M" wording; keep the hedging (corpus's external claim, not this paper's measurement).
4. Fix stale records with dated notes, per the workspace LIVE-vs-FROZEN rule.
5. Regenerate LaTeX only via `python3 scratch/uprep1/md2tex.py`; prove idempotence (byte-identical twice),
   0 non-ASCII bytes, 13 `\bibitem` entries, 0 placeholders, and quote the new `\bibitem` line.
6. Change no other number anywhere. If an edit would move anything else, stop and report.

## Write paths
`papers/encoder-crossover-190/**` except `submission/ABSTRACT_METADATA.txt`; `orchestration/units/UMERGE1.md`;
`orchestration/handoffs/UMERGE1.json`; `scratch/umerge1/**`.

## Hard bound
20 tool calls. Back up every file before editing; record verbatim before/after per edit in the handoff.
`papers/` is untracked by git — the handoff is the only recovery record.

## Constraints
`/home/zer0null/Duval` read-only (git only with `--no-optional-locks`); never write
`/home/zer0null/research-publish-packages`; do not touch `scratch/uneutral*/` or any release tree.

## Status: IN PROGRESS

## Outcome: DONE (2026-10-16)

- Sentence at `MANUSCRIPT.md:182-190` rewritten true and citing `benayas2024comparative`; echo at `:681-683` rewritten; References prose corrected (kills the old `main.tex:428` claim).
- `benayas2024comparative` merged VERBATIM into `REFERENCES.bib`; printed list now 13 `\bibitem`.
- Stale records keep their bytes and gained dated `Note 2026-10-16 (UMERGE1)` pointers: `UNSOURCED_RETAINED.md:12,:21-24`, `REFERENCES.bib` header + 'STILL NOT INCLUDED' block, `submission/BUILD_NOTES.md` item 8.
- `main.tex` regenerated only via `python3 scratch/uprep1/md2tex.py`; two runs byte-identical (sha256 `0ee1b11f0692474c174e920b0e534d044937da076fecff41a85796ba14d6f160`); 0 non-ASCII; 0 placeholders.
- `94.27`/`70.87`/`+23.4` occur 0 times in `MANUSCRIPT.md`; `29`/`108` preserved; no other number moved outside the rewritten regions.
- Note: the card's `REFERENCES.bib:80-82` reference was stale — no merge claim there (that is inside `gcd2305_13971`); the claim is at `:10-12` and was partly true (benayas was the one withheld addition).
- Backup + verbatim before/after: `scratch/umerge1/backup/**`, `scratch/umerge1/edits.json`.
