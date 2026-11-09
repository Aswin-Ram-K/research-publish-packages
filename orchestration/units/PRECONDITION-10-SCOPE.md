# Unit card — PRECONDITION-10-SCOPE

**Purpose.** Scope launcher precondition 10 per arm so each cell is judged only on its own
treatment, letting the canary reach cell 15 (`lease-reopen`) without weakening the guard.

**Hard bound.** 25 tool calls; stop after the deliverables if verification cannot be completed.

**Write paths (declared).** `experiments/ptr-engine/tools/run_a_star.py`,
`experiments/ptr-engine/tests/test_precondition10_scope.py`,
`docs/PRECONDITION-10-SCOPE.md`, this card, `orchestration/handoffs/PRECONDITION-10-SCOPE.json`,
`orchestration/journals/PRECONDITION-10-SCOPE.jsonl`.

**Forbidden.** `cell.py`, `run_longrun.py`, `analyze_stats.py`, `grade_v5.py`, any fixture, pin,
params, ledger, row, grade file, published page, `RUN-A-STAR-2`'s card.

**Stop rule.** If the scoped rule cannot be proven red→green on the real rows, STOP and report.

**Result.** `status: done`. `ARM_TREATMENT` data table + `precondition10()` (fired / not-due /
missing) replaces the global expression. Real replay: old stops at cell 13, scoped rule reaches
cell 15; each arm still stops on its own zero marker. 11 new tests pass; dry-run shape
(`refused=0 requests=0`, grid `cells=16`) and zero-spawn/zero-socket unchanged.

**Measured environment caveat.** `measure/REQUEST-LEDGER.json` says 3144 against the frozen
baseline's 3192, so the launcher refuses at `remaining_basis` (line 229) before the cell loop;
five neighbouring dry-run tests fail on that pre-existing refusal. New tests pin the two
records to 3192/4320 to isolate the scope change.
