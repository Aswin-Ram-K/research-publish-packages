# UPDF1 — Can paper #3 be turned into a PDF on this host?

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Hard bound:** 20 tool calls. Render timeout 120 s per command (kill + record if exceeded).
**No installs. No network.**

## One purpose
Settle by experiment whether a usable PDF of `papers/encoder-crossover-190` can be produced here
without LaTeX, and produce the best artifact if so.

## Declared write paths
- `papers/encoder-crossover-190/rendered/**`
- `strategy/PDF_ROUTE.md`
- `orchestration/units/UPDF1.md`, `orchestration/handoffs/UPDF1.json`
- `scratch/updf1/**`

## Do-not-touch
`/home/zer0null/Duval` (read-only, no git). `submission/main.tex`, `MANUSCRIPT.md`, companions — render only.

## Routes to test (literal command, exit code, size, extracted text)
1. Chrome/Chromium headless `--print-to-pdf` from markdown→HTML.
2. LibreOffice `--convert-to pdf` from (a) HTML, (b) ODT.
3. LibreOffice `--convert-to docx` from HTML.

## Deliverables
PDF + DOCX + HTML + converter script under `rendered/`; determinism check (two runs, byte compare);
honest visual assessment (pages, tables, font embedding, text extraction, Unicode fidelity, abstract
as text, byline slot); `strategy/PDF_ROUTE.md` with recommendation for Preprints.org / TMLR.

## Facts learned before starting
- `markdown` 3.10.2 at `/usr/lib/python3/dist-packages/markdown/__init__.py` — has `tables` extension.
- `pdftotext` **is** present at `/usr/bin/pdftotext` (the card's "may be absent" does not apply).
- `libreoffice`, `soffice`, `google-chrome`, `/snap/bin/chromium` all present.
- MANUSCRIPT.md: 919 lines, H1 title + `## Abstract` + `## 1..7` + post-body sections + `## References`.
- 5 pipe tables (delim rows at MANUSCRIPT.md:268, :300, :318, :398, :748).
- Unicode in manuscript: § 63, → 23, κ 31, × 13, ≥ 10, Δ 8, ψ 7, ± 4, ≈ 3.
- Byline slot lives only in `submission/main.tex:10`: `\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}`.
