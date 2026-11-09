# GRID-RESUME-TOOL

**Purpose:** make resumption of the ≈9 h live grid `RUN-A-STAR-2` mechanical: one
read-only command reads the disk and prints what is done, what is partial, what is
era A, and what to run next — so a killed session resumes from evidence, not memory.

**Bound:** 24 tool calls; journal first; verdict before handoff. Offline: zero requests,
no sockets. Unit session, `workspace-write`.

**Write paths:** `experiments/ptr-engine/tools/grid_resume.py`,
`tests/test_grid_resume.py`, `orchestration/units/GRID-RESUME-TOOL.md`,
`orchestration/handoffs/GRID-RESUME-TOOL.json`,
`orchestration/journals/GRID-RESUME-TOOL.jsonl`.

## Declared grid (from `run_a_star.py:CELLS` + the card)

10 era B cells in declared order — pointer-stable r1–r3, transcript-grow r1–r3,
transcript-compact r1–r2, lease-reopen r1–r2 — plus the 4 canary arms
(pointer-stable, transcript-grow, transcript-compact, lease-reopen) gated at N=12
(`measure/CANARY-ERA-B-FIX.json: gate_recommendation`).

## State rules (explicit, evidenced)

| state | rule | evidence quoted |
|---|---|---|
| `done` | turn rows on disk == 48, era B, no stamp says `usable_for: []` | turn count + `usable_for` |
| `partial` | 1..47 turn rows (a killed invocation; resumable only by a fresh cell) | turn count |
| `abandoned` | a row has `stop_reason ∈ {runaway_turn, runaway_abort}` or a journal line names the cell ABANDONED | stop_reason/turn + journal line |
| `era_a_excluded` | the file's own rows say `tools_mode: "off"` (corroborated by `usable_for: []` stamps) | `tools_mode` count, stamp path+value |
| `absent` | no rows file for that cell/rep | file list |

Era A and era B share the same fixture: current `LR-01.v8` sha256 is
`0804b51575cc…`, which is also the era A rows' `fixture_sha256`. So fixture sha and
filename cannot separate eras — the tool reads the rows' `tools_mode` and the
stamping documents (`GRID-CELL-SANITY.json`, `ANALYSIS-PATH.json`,
`longrun/manifests/*.json`) and quotes them. Files are assigned to a cell by the
rows' own `rep`, so a rep-1 file is never multiplied across reps 2/3.

## Measured on today's corpus (2026-10-26, `next_cell` = first non-done)

- pointer-stable r1: `partial` — two files: `rows-cell-pointer-stable-20261026T145758Z.jsonl`
  6/48 turns (fixture `967cef03…`, pre-run), and
  `rows-cell-pointer-stable-20261026T182535Z.jsonl` 27/48 turns
  **`file_state=era_a_excluded`**, `tools_mode=off in 27/27`, stamped `usable_for: []`.
- pointer-stable r2/r3 and every other era B cell: `absent` (0 files).
- `next_cell = pointer-stable r1`; `canary_next = pointer-stable` (no canary rows yet).
- ledger vs v2 (`3b79f476…`): `spent_now 1128`, `remaining_now 3192`, `delta 0`,
  verdict OK; next cell price 108, fits=True.

## Proofs

1. **/tmp state machine** (`/tmp/gr-proof/measure`): 48-turn file → `file_state=done`
   (`turns=48/48 ttft=48`); 47-turn file → `file_state=partial` (`turns=47/48`);
   20-turn file with `runaway_turn` at turn 19 → `file_state=abandoned`
   (`evidence: stop_reason=runaway_turn at turn(s) 19`).
2. **Read-only:** sha256 of all 15 `measure/rows-*.jsonl` captured before and after a
   full run — equal (`diff` empty). Files are opened with mode `"r"` only; the sole
   subprocess is `tools/ledger_delta.py` (itself read-only).
3. **Red→green:** `DONE_TURNS 48 → 47` ⇒ 5 failed / 2 passed
   (`test_done_needs_exactly_48_turns`, `test_one_turn_missing_is_partial_not_done`,
   `test_usable_for_empty_stamp_excludes_a_48_turn_file`,
   `test_next_cell_is_first_not_done_in_declared_order`,
   `test_cli_is_read_only_on_rows_files`); restored to 48 ⇒ `7 passed`.

## Assumptions (recorded, no human to ask)

- `--done-turns` defaults to 48 and `--canary-turns` to 12; both overridable, no
  threshold in any frozen file was edited.
- Per-cell token figures are `tokens_spent` = sum of `prompt_tokens` on disk and
  `projected48` = 48 × last row's `prompt_tokens`; labelled as a projection, not a price.
- The next-cell price (108 requests) is read from `GRID-PARAMS.json`
  (`per_cell_budget`) with 108 as the documented fallback; `--budget` is NOT treated
  as a ceiling (fetch rounds are priced separately by the cap gate).

## What a resumed session must do differently

A resumed session must not re-derive its position from the transcript or from the
last thing it remembers doing: it runs `grid_resume.py`, trusts only `state`, and
starts a **fresh** cell at `next_cell` (never appends to a `partial` file, never
re-runs a `done` one, never counts an `era_a_excluded` file as progress). It also
does what a fresh session need not: re-check the ledger delta against v2 and the
price fit before launching, because the killed invocation may have spent nothing or
everything since the last check; it re-runs the canary gate at N=12 if
`canary_next` is not absent, and it treats `abandoned` as a stop signal to report,
not as a turn count to top up.
