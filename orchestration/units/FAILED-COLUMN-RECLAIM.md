# FAILED-COLUMN-RECLAIM

**Purpose.** Turn the board's `failed` column into a work list: for each card, decide from
artefacts and a fresh run today whether the unit finished (and is still green), finished but is
red today, cannot be judged (no runnable command — reason named), or left nothing on disk.

**Extends** `UNSTAMPED-104` (`orchestration/handoffs/UNSTAMPED-104.json`), which proved nobody had
measured these cards from their rows. This unit asks whether the *work* exists.

**Bound.** ≤34 tool calls; offline (0 requests); no board mutation; read-only commands only.

**Write paths.** `experiments/ptr-engine/measure/FAILED-COLUMN-RECLAIM.json`, `docs/FAILED-COLUMN.md`,
`experiments/ptr-engine/tools/failed_column.py`,
`experiments/ptr-engine/longrun/tests/test_failed_column.py`, this card, its handoff and journal.

**Deliverables.**
1. Per-card record `{card, unit, execution_id, class, artifacts_present[], command, exit_today,
   first_failure_line, next_action}` for all 104 census cards.
2. `docs/FAILED-COLUMN.md` — ranked table (green first), arithmetic 104 → 99 in scope, and the
   "what this column is not" paragraph.
3. `failed_column.py --check` — exit 1 on unclassified card, a green card whose command now exits
   non-zero, or totals that miss the census. Tests red→green on a fabricated green card.
4. Eight-card priority list with reasons.

**Arithmetic correction recorded.** The census's 96 `never_had_a_row` already excludes the 5
superseded; in scope = 96 + 2 drift rows + 1 exit-124 row = **99**, not 94. Totals sum 99 + 5 = 104.

**Result.** 9 green, 1 red (`PROBE-CP3-V6`, tools-off drift), 29 not runnable, 60 no artefacts,
5 superseded. Exit 124 recommended as a *refusing* code in `EXIT_TABLE` (not edited here).
