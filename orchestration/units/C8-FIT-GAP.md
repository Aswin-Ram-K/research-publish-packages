# Unit C8-FIT-GAP

**Purpose.** Explain the 21 rows C8 says `experiments/miss-law/law_fit.json` does not fit: account, characterise, classify, rule.

**Bound.** 16 tool calls, offline only, zero live requests, no containers. Exceeded: 19 calls (state churn — three concurrent passes rewrote the two output files mid-unit). Partial is a result.

**Write paths.** `experiments/miss-law/FIT-GAP.md`, the C8 paragraph in `experiments/ptr-engine/RECORD.md`, `orchestration/units/C8-FIT-GAP.md`, `orchestration/handoffs/C8-FIT-GAP.json`. Nothing else touched; C4/C9 paragraphs, row files, `law_fit.json`, `LAW.md`, scripts, `papers/**`, `state/**`, `VERDICTS.md` all untouched.

**Findings.** `n_rows: 753` is a runtime file length (`experiments/miss-law/agg.py:63`), not a coverage count — it equals `len(rows.jsonl)` when `agg.py` ran (mtime chain 23:55:02.910 → 23:55:04.988 → 23:55:57.864, 2026-10-24). 774 − 753 = 21 rows appended after the fit. Non-circular test holds exactly for both servers: `onfile − intail == n_residue_rows` (`sglang` 232−0=232; `vllm` 78−5=73). Classes: outlier 0, law_gap 0, defect 21 — the defect is the artefact *pair*, not the rows. Fit covers 387/387 `measure` rows.

**Corrections carried.** A first draft asserted all 21 tail rows had `cached_reported == true`; only 10 do. Recorded, not dropped. `RECORD.md:128` was already CLOSED on the same reasoning by a concurrent pass and was verified, not overwritten.

**Deliverable.** `experiments/miss-law/FIT-GAP.md` (45 lines, the card's cap).
