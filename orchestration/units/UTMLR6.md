# UTMLR6 — rebuild the TMLR anonymised variant against the DOI-bearing source

**Unit:** UTMLR6 · **Status:** done · **Bound:** 25 tool calls (used 22) · **Date:** 2026-10-18

## Purpose

The identified source gained the published Zenodo DOI after the UTMLR5 build. A DOI is a link to an
identified version, so it must not appear in the TMLR submission PDF. Rebuild the anonymised variant
from the **current** source, extend the residue scrub to the DOI, and prove anonymity from the
**compiled PDF's own text and metadata**.

## Inputs (read-only)

- `papers/encoder-crossover-190/submission/main.tex` — **84,786 B**, sha256
  `1468b61e5baf1a2dc110e5612b70c9d83adc0a91e3101a9fe5b5cfdac6294c6b` (**card values reproduce**).
  `10.5281/zenodo.23463945` ×3 (L375, L407, L427); `10.5281/zenodo.23463944` ×1 (L427).
- Chain reused, not reinvented: `scratch/utmlr2/make_tmlr2.py`, `scratch/utmlr5/build.py`.
  P1 (3-line byline literal) and P2 (`\setcitestyle{numbers}` **after** `\usepackage{tmlr}`) carried
  verbatim; `SCRUB3` (UTMLR5's 8 re-anchored rules) carried verbatim.

## Method

`scratch/utmlr6/build.py` copies the three frozen scripts, rebases their write paths onto
`scratch/utmlr6/` (asserted: no `utmlr1`/`utmlr2` write path survives), runs the chain, applies
`SCRUB3` + a new `SCRUB4` (3 re-anchored pass-1 rules for the DOI + 2 safety-net rules), measures,
compiles with Tectonic, sweeps the PDF text/metadata and diffs against UTMLR5.

## Result

- Final variant `scratch/utmlr6/tmlr/main.tex` — **83,785 B**, sha256
  `8d6b036c23e4195e9119f67d2a7493831e836bfd68a9a2d73849eecdfbbf0fd0`, 476 lines.
- **Byte-identical** to `scratch/utmlr5/tmlr/main.tex` (`cmp` silent, `diff` +0/−0). So the UTMLR5
  *artifact* was correct; the UTMLR5 *driver* is stale — re-run now, its 3 DOI anchors match 0 and the
  DOI would survive.
- PDF: 16 pages, 176,971 B, sha256 `a777d2a30e1f8707d84673d401a8a231cd4526b4ee78f5a1163070961929acdf`,
  exit 0, 0 errors, no `-Z continue-on-errors`.
- DOI literals: source 3/1 → final **0/0**; `10.5281` 4→0; `Zenodo` 7→0.

## Rules applied (absolute found counts — `scratch/utmlr6/evidence.json → rule_counts`)

| set | rules | found |
|---|---|---|
| SCRUB3 (UTMLR5 re-anchors) | 1–7 | 1,1,1,1,1,1,1 |
| SCRUB4 (DOI re-anchors) | 1–3 | 1,1,1 |
| SCRUB4 (safety net) | 4–5 | 0,0 |
| frozen `make_tmlr26` PAIRS | 68 applied | 12 expected-1 anchors found=0 (documented stale set) |
| frozen `fix_tmlr26` FIX | — | 3 misses (2 genuine, re-anchored; 1 is an n=2 duplicate match) |

## Bounds honoured

Nothing under `papers/**`, `tools/**`, `scratch/utmlr1/**`, `scratch/utmlr2/**`, `scratch/utmlr4/**`,
`scratch/utmlr5/**` written. No network write, no upload, no git command, `/home/zer0null/Duval`
untouched. Wrote only `scratch/utmlr6/**`, the three strategy documents (dated appends) and
`orchestration/units|handoffs/UTMLR6.*`.
