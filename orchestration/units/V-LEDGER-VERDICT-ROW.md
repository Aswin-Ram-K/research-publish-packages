# UNIT V-LEDGER-VERDICT-ROW

**Purpose.** Record the verdict row that `V-LEDGER-BASELINE` could not, on its already-settled
execution (`5c76ff79-e431-422d-aed2-cdaf1257c559` / exec `6ef278ec-6182-4ea4-a5e4-6d0974dc2b26`),
and measure how many other finished cards are in the same state. OFFLINE — zero inference requests.

**Bound.** ≤14 tool calls (overrun recorded: 17 used; the extra calls went to establishing what the
closure actually measured, without which the class numbers would have been wrong).

## What was done, in order

1. Read `orchestration/handoffs/V-LEDGER-BASELINE.json`; `overall: pass`, `verdict: baseline_sound`,
   14 tool calls. Its `reproduce` line, verbatim:

   `bash -c "PATH=.venv/bin:$PATH python -m pytest tests/test_ledger_delta.py tests/test_grid_resume.py -q" (16 passed, exit 0) plus the offline recount in experiments/ptr-engine/measure/V-LEDGER-BASELINE.json :: check_1_row_count`

2. Re-ran that exact command from the workspace root: **exit 0, 16 passed** in 0.32 s.
3. Recorded the row on the settled ids with that command, `exitCode: 0`, sha `f17663d1`.
   **Accepted, not refused.**
4. Sized the class from the board ledger + handoffs + the verdict/closure stores.
5. Wrote this card, the measure JSON, the journal and the handoff.

## Corrections this unit owes the card

- **The row was not missing.** `~/.dsh/storages/orchestration/verdict.jsonl` already held
  `5c76ff79:6ef278ec` with `exitCode: 0`, commandHash `b817fec33809911d`, at 1793045113928. My
  record call re-recorded the identical command and the plugin accepted it as a retry.
- **127 was not the allow-list.** `bash` is allowed and the command starts with `bash`; the closure's
  own `verdictRow.output` is `bash: line 1: python: command not found` with `claimedExitCode: 0`.
  The judge re-runs the frozen command in its **own scratch cwd**, where the RELATIVE prefix
  `.venv/bin` does not resolve. The card's hypothesis (allow-list refused `.venv/bin/python`) is
  wrong on the evidence; the real defect is a relative PATH in the recorded command.
- Because the row already said `exitCode: 0` while the closure says `exit-127`, the row is not what
  the failed column is derived from.

## Columns

Do not use `task_board_manage` on `5c76ff79`. A retroactive row is a record about a past execution,
not a re-judgement of it, and it does not move a column.

## Class size

`pass_without_row` **19** · `of_which_runner_refused` **0** · `total_settled_scanned` **1062**.
Separately, the exit-127 family is **4** settled closures (`f5debfd9`, `16957dac`, `11bf5265`,
`5c76ff79`), all failing on `python`/`.venv/bin/python` not found in the judge's scratch tree.

Method and limits: join the board ledger's settled executions against handoff `overall` by unit
name, and verdict/closure stores by `taskId:executionId`; a card counts as runner-refused only if the
refusal text is on disk. 18 of the 19 carry `reason: null` (never judged) and 1 `no-verdict`, so the
rest of the class is unclassifiable by construction.

## Write paths

`experiments/ptr-engine/measure/V-LEDGER-VERDICT-ROW.json` ·
`orchestration/units/V-LEDGER-VERDICT-ROW.md` ·
`orchestration/handoffs/V-LEDGER-VERDICT-ROW.json` ·
`orchestration/journals/V-LEDGER-VERDICT-ROW.jsonl`
