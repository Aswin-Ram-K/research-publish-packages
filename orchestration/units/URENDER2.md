# Unit URENDER2 — re-render papers #3 and #7 after the byline fix

**Workspace:** `/home/zer0null/reserach extarctor`  **Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a

## One purpose
Re-render `papers/encoder-crossover-190` (paper #3) and `papers/gated-read-batching` (paper #7)
from their current sources, so their PDFs/DOCX carry the author's real byline
`Aswin Ram Kalugasala Moorthy` instead of the stale drafting placeholder.

## Hard bound
15 tool calls. Chrome gets `timeout 120` per render; if it exceeds that, kill and record.

## Declared write paths
- `papers/encoder-crossover-190/rendered/**`
- `papers/gated-read-batching/rendered/**` (the `rendered/` dir did not exist; created here)
- `strategy/PDF_ROUTE.md` (append only)
- `orchestration/units/URENDER2.md`, `orchestration/handoffs/URENDER2.json`
- `scratch/urender2/**`

## Do not touch
`papers/replay-record-not-decision/**` (another unit is editing it); any `MANUSCRIPT.md`;
any `submission/main.tex`; `tools/package/md2tex.py`; `/home/zer0null/Duval` (read-only, no git).

## Root cause established
- `papers/encoder-crossover-190/rendered/encoder-crossover-190.pdf` rendered 22:25:57;
  `papers/encoder-crossover-190/submission/main.tex` (the byline source) written 22:28:15 — the
  byline fix landed **after** the render.
- Old PDF, `pdftotext -layout`: `AUTHOR SLOT` count = 1 (page-1 line 5), `Aswin Ram Kalugasala Moorthy` = 0.
- Authoritative pipeline: authored markdown = `MANUSCRIPT.md`; `tools/package/md2tex.py` builds
  `submission/main.tex` from it with `author_line="\author{Aswin Ram Kalugasala Moorthy}"`
  (`md2tex.py:115,149,232`). The rendered-HTML converter reads `MANUSCRIPT.md` and lifts the
  byline out of `submission/main.tex`.

## Method
- Generic HTML converter (`scratch/urender2/convert_generic.py`), copied to each paper's
  `rendered/convert.py`; auto-detects its paper dir, reads `MANUSCRIPT.md`, lifts `\author{}`
  from `submission/main.tex`, and **fails loudly** if the lifted byline contains `AUTHOR SLOT`.
- PDF: `/usr/bin/google-chrome --headless=new --print-to-pdf` (all paths quoted — the workspace
  path contains a space).
- DOCX: LibreOffice HTML -> ODT -> DOCX (direct HTML->DOCX has no export filter).
- Proof: `pdftotext` on the produced PDF (real text extraction, not inference from the HTML).

## Status
See `orchestration/handoffs/URENDER2.json`.
