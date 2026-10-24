# UEMIT1 — emitted-tree audit

**Purpose:** settle why units report 38/39 vs 109 emitted files and
1,689/1,410/1,398 vs 1,133 gate FAILs for the same promoted 29-file package.
**Status:** done (measured; nothing edited).
**Bound:** 15 tool calls — used 12.
**Write paths:** `scratch/uemit1/**`, `strategy/EMITTED_TREE.md`,
`orchestration/units/UEMIT1.md`, `orchestration/handoffs/UEMIT1.json`.

## Result

- Fresh build into `scratch/uemit1/dest/research-publish-packages`, log
  `scratch/uemit1/build.log`, exit 1 (gate FAIL, reproduced 1,133 exactly).
- Emitted: **109 incl `.git` / 39 excl `.git`** (70 `.git` files).
- Breakdown excl `.git`: `packages/` 29, root files 6, `vocabulary/` 4.
- Gate scans `$DEST` (`os.walk`), `SKIP_DIRS={".git"}`, skips top-level
  `vocabulary/` → **35-file scan set**; known vocabulary-self-scan defect not recurring.
- Gate measured: `flagged tokens: 1133` (prose-source 774 + data 359).
- Reconciliation: 109-vs-39 = `.git` in/out; 38-vs-39 = `vocabulary/data.txt` added
  between revisions; count fall = scoped gate declares 501 JSON keys and skips `vocabulary/`.
- Quote the deliverable as **39 files excluding `.git`** = 29-file promoted package +
  10-file author envelope (`README.md`, `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`,
  `.gitignore`, `gate.sh`, `vocabulary/{english,code,public,data}.txt`).

Findings: `strategy/EMITTED_TREE.md`.
