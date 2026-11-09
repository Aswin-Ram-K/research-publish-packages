# Unit CONSONANCE-BC-REPORT

**Objective.** Write `research/next-candidates/consonance-bounded-context-report.md`: an evidence-grounded
research recommendation for the bounded recoverable context view (BRCV), correcting ten prior claims,
mapping the design to the `consonance.call/1` / `consonance.fixture/1` contract without inventing APIs,
and stating the exact next E1/E2 decision with its no-go conditions.

**Status:** done.

**Bound:** 60 tool calls (unit contract). Used well under it; no source needed more than one attempt
except the G5 row path (`papers/context-cache/cells/G5/rows.jsonl` does not exist; the real path is
`experiments/context-cache/cells/G5/rows.jsonl`, resolved from `recompute.py:32` `CELLS = ROOT / "experiments" / "context-cache" / "cells"`).

**Declared write paths.**
- `research/next-candidates/consonance-bounded-context-report.md` (deliverable)
- `orchestration/units/CONSONANCE-BC-REPORT.md`
- `orchestration/handoffs/CONSONANCE-BC-REPORT.json`

**Requests sent:** 0. No endpoint, no `curl`, no GPU, no model lock, no server restart, no `/home/zer0null/Duval` access.

**What I read (all under `/home/zer0null/research extractor`).**
- `handoff from consonance/{README,INTERFACE_CONTRACT,MEASURED_FACTS,EXPERIMENTS,DO_NOT_REDO}.md`
- `experiments/ptr-engine/RECORD.md`, `experiments/ptr-engine/ADOPTION.md`, `experiments/ptr-engine/BOUNDARY-PREREG.md`
- `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md`
- `experiments/ptr-engine/longrun/fixtures/LR-01..06.json` (field-level inspection, not prose)
- `docs/STATE.md`, `docs/GRID-2-FINAL.md`, `docs/CHECKPOINT-COVERAGE.md` (grep)
- `papers/context-cache/{CLAIM-HEALTH,CLAIM-SENSITIVITY,CONSONANCE-INTEGRATION}.md`
- `papers/context-cache/MANUSCRIPT.md` §8a (lines 494-520)
- `papers/context-cache/CLAIMS.md` C53/C54/C64 rows; `papers/context-cache/recompute.py` c53 function
- `experiments/agentic-lazy/crossover/RESULTS.md`
- `orchestration/STATUS.md` §7.1 (line 155, `E1` fork-break-cost)

**What I ran (offline, 0 network).**
- `.venv/bin/python papers/context-cache/recompute.py C53` → `PASS 18/18 values match`
- independent per-fan-out recompute, 192 rows, sha256 `8fd7f9d2534b88d682a44709120ae98dd8f46b9b9678c9a8cae4bf42734faa05`
  → 8 ratios, mean 6.744331504, stdev 3.227761582, ratio-of-totals 6.063360882

**Assumptions recorded.**
1. Where `papers/context-cache/recompute.py` documents the estimator, that estimator (unweighted mean of
   per-fan-out ratios) is the published one; the ratio of totals is reported only as the contrast number.
2. `docs/STATE.md` (2026-10-28) is the newest current-state page; nothing after it is cited as state.
3. The six `fixtures/LR-0*.json` are the eligible fixture set; `tasks-v6/LR-01.v8.json` is the gen-6
   fixture whose wall was priced from declared padding and is not used as evidence.
4. The addendum from the main session (padding C64 measurement; workspace `E1` fork-break-cost) was
   received mid-unit and folded in as §3 E-25 / E-26 and correction 4.7, with the naming collision kept
   explicit.
