# UVER34 — independent verification of UMERGE1

**Unit:** UVER34 (verifier; not the author). **Date:** 2026-10-16. **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a.
**Purpose (one):** independently re-check each of the 10 claims made by UMERGE1 (bibliography merge +
falsified-sentence rewrite) and record pass/fail.

## Inputs read
`orchestration/units/UMERGE1.md`, `orchestration/handoffs/UMERGE1.json`, `strategy/ROBERTA_CLAIM_SOURCING.md`
(UBEN1), `strategy/VERIFICATION_REPORT_33.md` (UVER33), plus the live paper files and
`scratch/umerge1/backup/**` as the before-image.

## Method
- All measurements re-run from the live disk; no reliance on the author's evidence block.
- `md2tex.py` executed twice against the real tree; red→green done on patched **copies** under
  `scratch/uver34/**` so the live paper was never reverted.
- Frozen-record integrity checked as before/after diff against `scratch/umerge1/backup/**`.
- No file under `papers/encoder-crossover-190/` was hand-edited by this unit; the only writes to the paper
  tree are the two sanctioned `python3 scratch/uprep1/md2tex.py` runs, which reproduced byte-identical output.

## Result: PASS (9/10 confirmed; 1 contradicted detail, non-material)
Full evidence and quotes: `strategy/VERIFICATION_REPORT_34.md`.

## Verdict
- Checks 1–8, 10: PASS.
- Check 9: PASS on substance (no merge claim at `REFERENCES.bib:80-82`; the real claim is `:10-12`, partly
  true), CONTRADICTED on one detail — the handoff places `:80-82` inside `gcd2305_13971`, but it is inside
  `pride2309_03882` (`:71-85`); `gcd2305_13971` starts at `:86`.
- md2tex run1 = run2 = `0ee1b11f0692474c174e920b0e534d044937da076fecff41a85796ba14d6f160`; live `main.tex`
  already had that hash before my runs.
- Red→green: 12 `\bibitem` / benayas absent (sha `277fd733…`) vs 13 `\bibitem` / sha `0ee1b11f…`. Not vacuous.
- Frozen records: 0 deleted lines in `REFERENCES.bib`, `UNSOURCED_RETAINED.md`, `submission/BUILD_NOTES.md`;
  additions only, all dated notes.

## Hard bound
20 tool calls; 11 used.

## Write paths
`strategy/VERIFICATION_REPORT_34.md`, `orchestration/units/UVER34.md`, `orchestration/handoffs/UVER34.json`,
`scratch/uver34/**`.

## Status: DONE (2026-10-16)
