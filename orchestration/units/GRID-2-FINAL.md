# Unit card — GRID-2-FINAL

**Purpose (one):** produce the best honest report the six usable gen-6 cells support, with the
price of what would settle H1 — without adjudicating H1, without a live request, without a cell.

**Hard bound:** 34 tool calls; no ask_user_question (automated session); stop at the deliverable.

**Write paths (only these):**
- `experiments/ptr-engine/tools/grid2_final_report.py` (new)
- `experiments/ptr-engine/tests/test_grid2_final.py` (new)
- `experiments/ptr-engine/measure/GRID-2-FINAL.json` (new)
- `docs/GRID-2-FINAL.md` (new)
- `orchestration/units/GRID-2-FINAL.md`, `orchestration/handoffs/GRID-2-FINAL.json`,
  `orchestration/journals/GRID-2-FINAL.jsonl`, `.scratch/grid2/`

**Forbidden (checked, untouched):** `cell.py`, `run_longrun.py`, `client.py`, `analyze_stats.py`,
`grade_v5.py`, any fixture, any rows file, `HARNESS-PIN.json`, `GRID-PARAMS.json`,
`REQUEST-LEDGER.json`, any baseline, any grade file, any published page, `docs/GRID-RUN-2.md`,
`measure/GRID-RUN-2.json`. No floor moved; no interval widened; no era pooled; no stamped-out
cell pooled.

**Kill condition:** if the frozen H1 reading could not be reproduced from the rows on disk, STOP
and report the divergence instead of printing a number.
