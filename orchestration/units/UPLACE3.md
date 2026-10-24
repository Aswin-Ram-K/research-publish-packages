# UPLACE3 — Repoint paper #3's eight `analysis.json` provenance citations at shipped `results/REPORT.md`

**Status:** in progress
**Bound:** 25 tool calls. If any before-string does not occur exactly once, STOP and report.

## Purpose

Paper #3 (`papers/encoder-crossover-190/MANUSCRIPT.md`) cites `analysis.json` eight times by precise
key path. `analysis.json` does not ship and **must not** ship (33 of 184 neutralised mechanism
identifiers, 193 occurrences — see `strategy/ANALYSIS_JSON_RELEASABILITY.md`). Repoint each citation at
the shipped `results/REPORT.md` using that document's verified line-by-line mapping. No claim changes.

## Mapping (from `strategy/ANALYSIS_JSON_RELEASABILITY.md`)

| cited key | REPORT.md locator | verified |
|---|---|---|
| resolution | `:11` | yes |
| 0.6684 figure | `:36` / `:104` | yes |
| 0.6789 figure | `:39` / `:42` / `:99` | yes |
| p-value | `:63` / `:64` | yes |
| F4 falsifier | `:95` | yes |
| H4 verdict | `:109` | yes |
| lint record | `:134` | yes |
| dev-curve heading | `:170` | **section-level only — cite the section, no invented line** |

## Write paths

`papers/encoder-crossover-190/MANUSCRIPT.md`, `papers/encoder-crossover-190/submission/**`,
`scratch/uplace3/**`, `orchestration/units/UPLACE3.md`, `orchestration/handoffs/UPLACE3.json`

## Do not

Edit papers #1/#2, `tools/package/**`, `scratch/uneutral10/package/**`, released archive. Change any
number/claim/table/figure. Network. Write outside listed paths. Never hand-edit generated LaTeX;
regenerate with `python3 tools/package/md2tex.py --package encoder-crossover-190`.
