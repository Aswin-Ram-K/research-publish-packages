# RESULTS-TRAIL-NOTE — disclose the 01:07–01:10 repair trail and correct C4's premise

Card unit. Workspace `/home/zer0null/reserach extarctor`. Bound 12 tool calls. Automated: no questions, no input.
Zero live requests. Documentation only — **no measured number changed**.

## Why this unit exists
Unit `CONTAINMENT-RULING` (`orchestration/units/CONTAINMENT-RULING.md`, `orchestration/handoffs/CONTAINMENT-RULING.json`)
ruled **KEEP (a)** on the five artefacts written into `experiments/ptr-engine/quality/` between 01:07 and 01:10 after
the QUALITY-ARM handoff (00:39), found that **nothing published cites them**, and found **one record defect**:
`experiments/ptr-engine/RECORD.md:120` (C4) stated that BILL-REPAIR "never ran ... is a stub". It ran at 01:07–01:10
and its own alignment guard stopped it. C4 stays **OPEN**; only its premise was wrong.

Provenance is *not* re-derived here. The ruling and its handoff carry the evidence; this unit cites them.

## The two edits (both documentation, in place)
1. `experiments/ptr-engine/quality/RESULTS.md` — inside the existing `## Corrections (2026-10-25)` section, one
   paragraph inserted **after numbered item 3** (which ends `… 6 tokens against a 17,193-token gap.`) and **before
   item 4** (`4. \`RESULTS.md:147\` — the C/T4 avalanche cell …`). Paragraph title: **Repair trail, undisclosed at
   handoff (01:07-01:10).** It names the five files, the guard failure (`rerun-corrected.log:16`), the absence of
   an aggregate, and states C4 stays OPEN and the files may not be cited as a measurement.
   Located by heading + the four numbered items, **not** by the ruling's `:257`/`:259` (the file was repaired at
   02:40 by `REPAIR-QP-A/B`, shifting lines).
2. `experiments/ptr-engine/RECORD.md` — contradiction **C4** (line 120): the false premise
   ("the repair unit never ran … is a stub") corrected to what happened — ran at 01:07-01:10, edited `runner.py` in
   place, executed `rerun_corrected.py`, aborted on its own guard, 9 rows / arm A rep 0, no `results-corrected.json`,
   0 of 4 arms completed. Cites `orchestration/handoffs/CONTAINMENT-RULING.json` and
   `rerun-corrected.log:16`. **Verdict preserved: OPEN.** The row is not deleted and not weakened.

## Constraints honoured
- Wrote only the four declared paths. Did **not** touch `rows.jsonl`, `rows-corrected.jsonl`, `runner.py`,
  `PREREG.json`, `VERDICTS.md`, any test, `papers/**`, `state/**`.
- Zero live requests. No git command run at all (target `/home/zer0null/Duval` untouched).
- No renumbering, reordering or reformatting of surrounding content; item 4 keeps its number (`4.`) and the blank
  line between it and item 3 now separates item 3 from the new paragraph.

## Deliverables
- `experiments/ptr-engine/quality/RESULTS.md` (one inserted paragraph)
- `experiments/ptr-engine/RECORD.md` (C4 sentence corrected)
- `orchestration/handoffs/RESULTS-TRAIL-NOTE.json`
