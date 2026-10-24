# UREC1 — repair the orchestration record (ULIC) and sweep for missing/broken records

**Unit:** UREC1 · **Status:** done · **Date:** 2026-10-15
**Hard bound:** max 40 tool calls · **used: 21** (incl. report-back) · no retry exceeded 1 attempt
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a

## Purpose (one)

Repair the `ULIC` orchestration record into valid JSON **without inventing any value**, and find any
other records of the same class (missing or broken handoffs). Everything except `ULIC.json` is
report-only.

## Declared write paths (all honoured — nothing else touched)

- `orchestration/handoffs/ULIC.json` (repaired — deliverable)
- `orchestration/RECORD_REPAIR.md` (created — deliverable)
- `orchestration/units/UREC1.md`, `orchestration/handoffs/UREC1.json`

**Not touched:** `strategy/`, `repro/`, `papers/`, `jobs/`, `journal/`, `experiments/`, `state/`, any
other handoff or unit card. **No writes to `/home/zer0null/Duval`** (not read in this unit either).

## Findings

1. **`ULIC.json` was structurally defective, not truncated.** 4021 bytes, mtime `2026-10-15
   15:05:39`, **stable** (identical md5 `5000652a…` across two reads 1 s apart). Delimiter census
   `{`=2 / `}`=**1**; depth trace puts `blocker`, `next_unit_hint`, `write_paths` at depth 2 **inside
   `evidence`**, so the single trailing `}` closed `evidence` and the outer object was never
   terminated → `JSONDecodeError: Expecting ',' delimiter: line 3 column 1 (char 4021)`.
2. **Repair:** inserted the one missing `}` after the `commands` array (the unique `"],"blocker":` →
   `"]},"blocker":`). Result **4022 bytes**, md5 `86e2f2a9306a8bc67d436ddb32d1bf31`, parses, and the
   top-level keys are exactly the seven contracted. The edit is provably **one delimiter**: removing it
   reproduces the original bytes exactly. The alternative (append `}` at EOF) was rejected because it
   would bury three required keys inside `evidence` — a *new* shape gap. Both readings are recorded in
   `RECORD_REPAIR.md`.
3. **Salvage: 0 unrecoverable fields.** All 7 top-level fields and all 9 `evidence` members (including
   **11 command records**) were present and are carried verbatim. The failure was structural, not
   informational. `status:"done"` is recovered from the card and corroborated by the three artifacts on
   disk (`LICENSE_ANALYSIS.md` 42249 B, `CHECKLIST.md` 15136 B, `OPEN_QUESTIONS.md` 11412 B).
4. **Sweep confirmed the orchestrator exactly:** 271 handoffs, **1** invalid before (`ULIC.json`) and
   **0** after. Guard green: `PYTHONPATH=src python3 -m pytest tests/test_orchestration_handoffs.py -q`
   → **13 passed**.
5. **Missing records:** exactly **1** card without a handoff — **`U1.7`** (card says *in progress*;
   deliverables exist; **superseded by `U1.7R`**, whose handoff carries a `supersedes` key). Of the four
   previously-dead units named in the brief, `UPIPE`, `UCORR2` and `UCONS2` now all **have** valid
   handoffs; **`JOB7b` still has neither a card nor a handoff** — it exists only as prose in
   `jobs/MASTER_SHORTLIST.md`. Also found **14 handoffs with no card** (reverse gap).
6. **Shapes respected.** 206 unit-shaped / 64 verdict-shaped; no verdict-shaped handoff is missing a
   core key. Flagged but **not rewritten**: `UVER1`–`UVER7` + `U8.72` (verdict shape under non-`V`
   names — correct shape) and `V4R` + `V5F` (`V`-named but unit-shaped). Six pre-existing frozen-baseline
   key gaps are reported, not touched.

## Blockers

None. **No reconstruction of `U1.7` or `JOB7b` was performed** — that is a separate unit's job by this
card's own instruction; they are named and handed off in `RECORD_REPAIR.md` §4 and in the handoff's
`next_unit_hint`.
