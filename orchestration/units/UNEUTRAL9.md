# UNEUTRAL9 — Whole-class neutralisation

**Purpose.** Remove every remaining identifier of the author's system from the release package and
replace it with generic `G`-prefixed equivalents, so a reader gets the smallest useful harness for
testing the claim in neutral tags.

**Source (read-only).** `scratch/uneutral8/package/` (29 files).
**Work tree.** `scratch/uneutral9/package/`; before-state at `scratch/uneutral9/before_pkg/`.
**Write paths.** `scratch/uneutral9/**`, `strategy/WHOLE_CLASS_NEUTRALISATION.md`,
`orchestration/units/UNEUTRAL9.md`, `orchestration/handoffs/UNEUTRAL9.json`.
**Bound.** 30 tool calls (used 30).

**Authority lists, in order.** (1) `scratch/uagnostic1/census.tsv` (184 ids, `c-mechanism`);
(2) `scratch/ugate1/classify_oov.py`; (3) `scratch/uneutral8/`; (4) own scan
(`scratch/uneutral9/scan.py`) for identifier-shaped strings the lists miss.

**Result.** 32 tokens renamed, 6177 occurrences, 17 of 29 files changed. Injective, case-sensitive,
prefix `G`, longest-first; map held in memory only, never written or shipped. The three shipped tools
run and exit 0; MANIFEST regenerated and independently verified; residual inside-stimulus identifiers
2 distinct.

**Deliverable.** `strategy/WHOLE_CLASS_NEUTRALISATION.md`.
