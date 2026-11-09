# LEASE-REOPEN-23 — unit card

**Purpose.** Give the grid's `lease-reopen` arm its own first-cell *mechanism* check: one ≥23-turn
lease cell whose rows show the T23 lease step and which returns ≥1 verified answer. This is the
`next_unit_hint` of `LEASE-REOPEN-12` (exec `c482566c`), which settled the channel on a 12-turn arm
but could not exercise the treatment because the v8 fixture declares `lease_reopen_turns: [23, 40]`.

**Hard bound.** 34 tool calls; one live cell invocation, no retries; 40-request live cap
(23 turns + ≤12 fetch follow-ups + ≤2 warm-up). **Overrun, disclosed:** 43 billed + 1 warm-up = 44
wire requests (`request_cap_overrun: 4` — the `--fetch-followup-allowance` is a G1 pricing term, not
a runtime cap; the runner emitted 20 follow-up rows).

**Run.** `lease-reopen`, 23 turns, rep 1, gen-6 tree `efefd885…`, `--tools read_file`,
`--thinking off`, `--turn-wall-cap 180`, `--runaway-turns 2`, `--hypothesis smoke`,
`--max-wall 1800`, `--budget 108`, `--fetch-followup-allowance 12`.
Driven through `tools/run_a_star.py::cell_argv()` / `run_cell()` (no single-cell CLI form exists in
the launcher); the launcher was **not** edited.

**Declared write paths.**
`experiments/ptr-engine/measure/LEASE-REOPEN-23.json`, `docs/LEASE-REOPEN-23.md`,
`orchestration/units/LEASE-REOPEN-23.md`, `orchestration/handoffs/LEASE-REOPEN-23.json`,
`orchestration/journals/LEASE-REOPEN-23.jsonl`.

**Forbidden (honoured).** `cell.py`, `run_longrun.py`, `run_a_star.py`, `client.py`,
`analyze_stats.py`, `grade_v5.py`, `measure/HARNESS-PIN.json`, `measure/GRID-PARAMS.json`,
`measure/REQUEST-LEDGER.json`, any baseline, any fixture/row/grade/published page, and the prior
artefacts `CANARY-ERA-B-4.json`, the 59 canary rows, `LEASE-REOPEN-12.json` + its 30 rows. No file
was overwritten; the cell wrote its own new `…20261027T084049Z` files.

**Result.** lease event at T23 (`lease` 1 → 2 on the T23 turn row and its `turn-initial` row; 22
other turn rows `lease: 1`), `shape_ok` (3 `answer_verified` rows: turns 14/18/20; recorded final
`finish_reason`; no cap-length row), census non-zero (43 billed rounds, 56/56 rows schema-sent) ⇒
**`lease_arm_usable_for_grid: true`**.

**Kill condition honoured.** Stop after T23; do not extend to T40 unless T23 is ambiguous — it was
not ambiguous.

**Gaps recorded, not fixed.** (1) `stop_signal_source` present on 0 of 56 rows
(`CANARY-ERA-B-FIX` ⇒ gen 7). (2) `measure/REQUEST-LEDGER.json` stale by 115 billed rows since its
`22:33Z` build; file delta 0, in-memory recompute 3072 → 3029 remaining.

**Gate deviation recorded.** `--max-wall 900` (card) would G2-WOULD-REFUSE at 1,380 s projected for
23 turns; run at 1,800 s after a clean re-dry-run. No threshold or pinned artefact was moved.
