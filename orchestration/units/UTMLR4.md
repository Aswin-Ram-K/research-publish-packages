# UTMLR4 — Rebuild TMLR anonymised variant (paper #3)

**Purpose (one):** rebuild paper #3's anonymised TMLR variant from current source
`papers/encoder-crossover-190/MANUSCRIPT.md`, into a FRESH dir `scratch/utmlr4/tmlr/`, reusing the
established recipe (`scratch/utmlr2/make_tmlr2.py` + `scratch/utmlr2/fix_tmlr2.py`), and verify
compliance + anonymity + citation freshness.

**Hard bound:** 25 tool calls. If the recipe cannot be run as-is → STOP and report the blocker;
do NOT hand-edit a variant.

**Write paths (only):** `scratch/utmlr4/**`, `orchestration/units/UTMLR4.md`,
`orchestration/handoffs/UTMLR4.json`.

**Read-only / never write:** `scratch/utmlr1/**`, `scratch/utmlr2/**`, `papers/**`,
`tools/package/**`, `scratch/uneutral10/package/**`, released archive.

**Policy of record:** `strategy/TMLR_POLICY.md`, `strategy/TMLR_SUBMISSION.md`,
`strategy/TMLR_VERIFICATION.md`, `strategy/TMLR_VERIFICATION_2.md`.

**Source of truth:** `papers/encoder-crossover-190/MANUSCRIPT.md` → `tools/package/md2tex.py
--package encoder-crossover-190` → identified `submission/main.tex` 84,695 B
sha256 397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca.

**Must report:** exit code, `Undefined control sequence` count, `!` count, page count, PDF bytes+sha256,
main.tex bytes+sha256, double-build byte-identity, PDF-text anonymity proof (author/email/affiliation = 0),
`analysis.json` count = 0, citation locators vs current source, diff vs utmlr2 build.

**Status:** in progress.
