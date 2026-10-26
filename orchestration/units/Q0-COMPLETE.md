# Q0-COMPLETE — unit card (copy)

**Unit:** `Q0-COMPLETE` (card `17a76d24`) · **Lane:** OFFLINE, ZERO LIVE REQUESTS · **Date:** 2026-10-26
**Status:** done · **Live requests spent:** 0 · **Tool calls used:** 12 of 20 bound

## Why this card exists

Card `17a76d24` (unit `Q0-ANSWER-DEGENERACY`) was killed by a harness restart at its handoff step.
`task_board_get` recorded `result: failed, error: "agent turn ended without completing: interrupted"`,
failed execution `da4ba836-93ac-4ec4-a77f-6ac5bfca9444`. The driver snapshot taken at
`2026-10-26T13:08Z` (08:08 local) found two of four deliverables on disk —
`experiments/ptr-engine/measure/ANSWER-DEGENERACY.md` (20,170 B, 314 lines) and
`experiments/ptr-engine/tools/answer_degeneracy_check.py` (7,742 B) — and recorded
`orchestration/handoffs/Q0-ANSWER-DEGENERACY.json` and the unit card as missing.

**A card that reports success with no handoff is a failed card.** The job of this unit was to make that
one true: finish the record, do not redo the analysis.

## Objective

Persist a valid, machine-readable handoff whose `evidence.table` is independently reproduced; prove the
checker bites; leave the doc's numbers untouched (append a dated corrections block **only** on
disagreement).

## What was actually found on disk (deviation from the card's premise)

Both files the card declared missing **were present** when this unit started, both with mtime
`2026-10-26 08:09` local — roughly one minute *after* the driver's snapshot:

- `orchestration/handoffs/Q0-ANSWER-DEGENERACY.json` — 14,155 B, 116 lines, unit shape, with verdict,
  the 12-cell table, quoted rows, ranked causes, per-arm failing reasons.
- `orchestration/units/Q0-ANSWER-DEGENERACY.md` — 4,277 B, 78 lines, the original card.

Their content is substantive, not a stub. So this unit **verified and augmented** them instead of
rewriting them. No pre-existing text was deleted or reworded. This is the "one minute late" tail of the
interrupted run landing on disk, and it is recorded in the handoff under
`evidence.completion.snapshot_staleness_note` so no later reader mistakes the driver's snapshot for the
current state.

## Verification performed (and what was deliberately not)

1. **Independent recomputation.** `answer_degeneracy_check.py --table-json` → 4 arms × t12/t24/t46, all
   **12 cells `NO_MARKER`**. This was built by the checker from the 192 rows of
   `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl`, **not** copied from the doc.
2. **Doc vs checker.** The doc's table at `ANSWER-DEGENERACY.md:43-L48` equals the recomputed table cell
   for cell → `evidence.doc_matches_checker: true`, and therefore **no corrections block was appended**
   and no number in the doc was edited.
3. **Quoted rows spot-checked** against the row file: `:142` pointer-stable t46 = 3 words,
   `prompt_tokens` 2240; `:108` pointer-stable t12 = 89 words, 2225; `:156` lease-reopen t12 = 1 word,
   446; `:168` lease-reopen t24 = 36 words and contains `<tool_call>`. All four match the doc.
4. **Marker inertness re-confirmed** from the recorded grade sidecar: `row_count 192`, and all four arms
   carry `marker_census {"marker_lines": 0, "turns": 48}`; no failing reason in any arm is
   `marker_missing`.
5. **`--handoff` argument.** Requirement (1) of the card was **already satisfied on disk**: the checker
   declares `--handoff` at line 145 and resolves it at line 152, defaulting to
   `orchestration/handoffs/Q0-ANSWER-DEGENERACY.json`. The file was left **byte-identical** (sha256
   `2892b65b…`) so no classification rule could drift. Editing it would have been a no-op diff.
6. **Not re-done, on purpose:** the v4 / v4-tools / v5 grid quotes and `grids_classified` entries, and
   the `LR-01.v2.json` item census. They are outside the table this card's acceptance compares, and the
   card forbids re-deriving the analysis. They remain the interrupted session's claims — unrefuted, and
   recorded as unconfirmed here.

## Acceptance (executed, exact exits)

**GREEN** — `python3 experiments/ptr-engine/tools/answer_degeneracy_check.py --handoff orchestration/handoffs/Q0-ANSWER-DEGENERACY.json`

```
=== Q0-ANSWER-DEGENERACY: per arm x per checkpoint-turn class ===
rows: experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl (192 rows)
arm                 t12                 t24                 t46
--------------------------------------------------------------------------------
transcript-grow     NO_MARKER           NO_MARKER           NO_MARKER
transcript-compact  NO_MARKER           NO_MARKER           NO_MARKER
pointer-stable      NO_MARKER           NO_MARKER           NO_MARKER
lease-reopen        NO_MARKER           NO_MARKER           NO_MARKER
...
PASS: recomputed table equals recorded evidence.table (12/12 cells)
```
**exit 0** — re-run *after* the handoff was augmented, so the recorded table is the table of the final file.

**RED** — the checker must bite. Copy to `/tmp/q0-red.json`, change exactly **one** cell
(`lease-reopen.t24`: `NO_MARKER` → `MARKER_ACCEPTED`), run `--handoff /tmp/q0-red.json`:

```
FAIL: 1 cell(s) differ from evidence.table
  lease-reopen       t24  handoff=MARKER_ACCEPTED  recomputed=NO_MARKER
```
**exit 1** — the differing arm and turn are named. The real handoff and every row file were **not**
touched; the mutation exists only in the `/tmp` copy.

**JSON** — `python3 -c "import json;json.load(open('orchestration/handoffs/Q0-ANSWER-DEGENERACY.json'))"`
→ **exit 0** (`JSON_OK unit=Q0-ANSWER-DEGENERACY status=done doc_matches=True`).

## Handoff shape delivered

Unit shape, all seven contracted keys present — `unit`, `status`, `artifacts`, `evidence`, `blocker`,
`next_unit_hint`, `write_paths` — plus `evidence.verdict`, `evidence.table[<arm>][<t>]` for all 12 cells,
`evidence.commands`, `evidence.doc_matches_checker`, `evidence.completion` (second-session provenance,
the failed execution id, verbatim green/red/JSON commands and outputs) and top-level `provenance`.
It records honestly that the handoff was completed by a **second, fresh session** after the interruption.

## Deviations and corrections recorded

- The existing `commands[3].output` was value-identical to the re-run but listed arms in a different
  order; the verbatim output is re-recorded under `evidence.completion_commands`.
- `commands[1].cmd` is a paraphrase ("same command against …LR-01.v4.json") and `commands[2].output` is
  a summarised meaning rather than raw stdout. Both left as the interrupted session wrote them; neither
  is acceptance-bearing.
- The checker's supplementary census reports `present=False` for **all** 12 cells including
  pointer-stable t46, because it tests the expected string's first token, which for t46 is the literal
  `ledger.record_refusal(scope=...,` with an ellipsis. That is a substring artefact, not a refutation of
  reading `:142` as the substantively correct call.

## Hard bound, respected

20 tool calls declared, **12 used**. **0 live requests** — no socket opened, no POST to `:8012`/`:8014`,
no model contact. No grid re-run, no grader/fixture/row-file edit, no re-scoring of a recorded grid.

## Environment note (not a blocker for this card)

`python3 -m pytest tests/test_orchestration_handoffs.py -q` cannot run in this session: its
`tests/conftest.py:19` does `from resextract.llm import OccamyClient` and the `resextract` package is not
installed in the environment (`ModuleNotFoundError: No module named 'resextract'`). That is a suite-wide
import failure, not a defect in this handoff. The property that test enforces — every
`orchestration/handoffs/*.json` parses as JSON — was checked directly for this file:
`python3 -c "import json;json.load(open(...))"` → exit 0.

## Forbidden, respected

No edit to any row file, fixture, `grade_v3.py`, `score_longrun.py`, `grade_v2.py`, `run_longrun.py`, or
to the doc's existing numbers. No `ask_user_question`.

## Write paths (exactly these four)

- `orchestration/handoffs/Q0-ANSWER-DEGENERACY.json` — **written** (augmented)
- `orchestration/units/Q0-COMPLETE.md` — **written** (this file)
- `experiments/ptr-engine/tools/answer_degeneracy_check.py` — **not modified**, `--handoff` already present
- `experiments/ptr-engine/measure/ANSWER-DEGENERACY.md` — **not modified**, checker agreed with the doc

## Result in one line

The record is now true: 12/12 config-C checkpoint cells classify `NO_MARKER`, the doc's 4×3 table matches
the checker cell for cell, the checker exits 0 on the recorded handoff and 1 on a one-cell mutation — and
the card's own premise (two missing files) was one minute stale.
