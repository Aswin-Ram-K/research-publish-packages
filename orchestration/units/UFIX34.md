# UFIX34 — records fix: one wrong line reference + one stale recital

Purpose: close two records defects found by UVER34 (`strategy/VERIFICATION_REPORT_34.md`).
Change no substantive claim.

1. `orchestration/handoffs/UMERGE1.json` — evidence string `REFERENCES.bib:80-82` is attributed
   to the wrong entry (`@misc{pride2309_03882,` spans `:71-85`; `gcd2305_13971` begins `:86`).
   UMERGE1 is FROZEN/dated: append a dated `corrections_2026_10_16` key, do not rewrite values.
2. `papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md` — `:81` and `:156` recite the old
   "unsourced / not cited" conclusion with no dated pointer. Historical dated log → dated pointer
   note, keep every original byte (same rule as `UNSOURCED_RETAINED.md:12`, `BUILD_NOTES.md` item 8).

Write paths: `orchestration/handoffs/UMERGE1.json`, `papers/encoder-crossover-190/MANUSCRIPT_CHANGES.md`,
`orchestration/units/UFIX34.md`, `orchestration/handoffs/UFIX34.json`, `scratch/ufix34/**`
(`papers/encoder-crossover-190/submission/main.tex` only if MANUSCRIPT.md is edited — it is not).

Hard bound: 8 tool calls.

STATUS: done (both fixes applied and verified)
