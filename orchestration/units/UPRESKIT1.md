# UPRESKIT1 — Submission kit assembly

**Purpose:** assemble one self-contained submission kit (`strategy/SUBMISSION_KIT.md`) + `submission-kit/` copies for the three papers. Assemble and cross-check only — no re-packaging, no redesign.

**Bound:** 25 tool calls.

**Write paths:** `strategy/SUBMISSION_KIT.md`, `submission-kit/**`, `orchestration/units/UPRESKIT1.md`, `orchestration/handoffs/UPRESKIT1.json`.

**Skeleton written first** (before any work), so state survives a budget cut.

## Checklist
- [ ] md5sum x3 archives vs card
- [ ] sha256sum x3 preprint zips vs card
- [ ] sha256sum x3 TMLR PDFs + pdfinfo page counts vs card
- [ ] titles read from MANUSCRIPT.md line 1 (not retyped)
- [ ] keywords verbatim from `tools/package/md2tex.py` PACKAGES registry
- [ ] abstract char counts + copies into submission-kit/abstracts/
- [ ] Conflicts of Interest position in each submission/main.tex
- [ ] copies into submission-kit/ + README with size+sha256 + verify copies
- [ ] strategy/SUBMISSION_KIT.md written
