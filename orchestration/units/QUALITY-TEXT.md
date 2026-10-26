# QUALITY-TEXT — inventory gap #3

**Purpose.** Make the package stop contradicting itself: withdraw the refuted 49,594 billed-token figure at its printing site in `experiments/ptr-engine/quality/RESULTS.md`, and add a scope/withdrawal section to `experiments/miss-law/LAW.md`. No measured number, table or formula changed.

**Bound.** 14 tool calls. **Write paths.** `experiments/ptr-engine/quality/RESULTS.md`, `experiments/miss-law/LAW.md`, `orchestration/handoffs/QUALITY-TEXT.json`, this file.

**Edits.**
1. `RESULTS.md:152` — the sentence printing C rep2's **49,594** bill now carries `— **REFUTED as a cost, see Corrections** (`runner.py:490`/`:495`; RECORD.md C3)`. No stale `runner.py:467` citation existed there; the two existing citations are already `:490`/`:495`.
2. `LAW.md` — appended `## Scope and withdrawals (2026-10-26)`: points at `RECORD.md:114` (C1) and `:118` (C3); withdraws the 5.2× overstatement reading as a general claim (C1, UNDECIDABLE) and any billed-token identity (C3/C10, `RECORD.md:134`); restates single-warm-append scope (§8, `LAW.md:205-206`).

**Result.** done. See `orchestration/handoffs/QUALITY-TEXT.json`.
