# GRID-RUN-2 — unit card

**Purpose.** Run the promoted 16-cell era-B grid (pointer-stable 6 · transcript-grow 6 ·
transcript-compact 2 · lease-reopen 2; 48 turns each, rep 1 per cell, tools-on `read_file`, claim H2)
through the conductor `experiments/ptr-engine/tools/run_a_star.py`, sequentially, one invocation per
cell, and report H1/H2/H3/TVS in fixed terms.

**Hard bound.** 60 tool calls; 16 live cell invocations, one each, no retries; price 1,056 requests
against a 4,320 cap; wall ≈9–12 h if taken.

**Outcome.** **0 of 16 cells started, 0 requests sent.** The conductor refuses at its ledger gate
before cell 1, in both honest ledger states (§1 of `docs/GRID-RUN-2.md`). The grid was **not**
repaired: the card's write scope forbids `run_a_star.py`, `REQUEST-LEDGER.json` and every baseline,
which are the only files that could close the gap.

**Blocking measurement (quoted).**
* `RECONCILE baseline=1176 attributed_delta=115 live=1176 explained=1291 gap=-115` → exit 1 (stale file).
* `RECONCILE baseline=1176 attributed_delta=115 live=1321 explained=1291 gap=30` → exit 1 (owner's recount).
* The 30 = `kind="turn-initial"` rows (`2+7+13+6+1+1`) in six named rows files; `run_a_star.py:_row_counts()`
  drops that kind while `request_ledger.py` counts it conservatively.

**Preconditions verified before the stop.** pin generation 6 `efefd885…` (launcher wired to it);
`cell.py` standalone sha `c494e212…` recorded, not in the pin, unchanged; four arms cleared
(`CANARY-ERA-B-4` three arms `shape_ok`, `LEASE-REOPEN-23` `lease_arm_usable_for_grid: true`), no canary
re-run; tool channel live (`TOOL-CHANNEL-WIRE` `dda84411` PASS, verifier `V-TOOL-CHANNEL` overall
`partial`); `GRID-PARAMS.json` rev 3 = 16 cells / 6/6/2/2 / 1,056, enforced by the launcher;
`analyze_stats.py:749` still INCLUDES an unstamped cell (no rows written, so unexercised).

**Declared write paths.**
`experiments/ptr-engine/measure/GRID-RUN-2.json`, `docs/GRID-RUN-2.md`,
`orchestration/units/GRID-RUN-2.md`, `orchestration/handoffs/GRID-RUN-2.json`,
`orchestration/journals/GRID-RUN-2.jsonl`.

**Forbidden (honoured).** Every harness file (`cell.py`, `run_longrun.py`, `run_a_star.py`,
`client.py`, `analyze_stats.py`, `grade_v5.py`), `measure/HARNESS-PIN.json`,
`measure/GRID-PARAMS.json`, `measure/REQUEST-LEDGER.json`, any baseline, any fixture, any existing
rows file, any grade file, any published page. The only files that moved outside the declared set were
transient scratch rebuilds in `/tmp` (never in the workspace) and one probe output in the workspace
root that was deleted in the same call that created it.

**Kill condition honoured.** The gate refusal is the stop; no cell was started outside the conductor
and no ledger was fabricated to make the gate pass.

**Gaps recorded, not fixed.** (1) the turn-initial counter disagreement between
`run_a_star.py:_row_counts()` and `request_ledger.py` (⇒ the unblock in §4 of `docs/GRID-RUN-2.md`);
(2) `measure/REQUEST-LEDGER.json` stale at 1,176 / 3,144 against a 1,321 / 2,999 recount.

## Execution 2 (2026-10-28T02:45Z–03:36Z) — outcome: partial

Live 16-cell era-B tools-on grid executed, one invocation per cell, no retries, cell.py sha re-checked before every cell (unchanged). Spend 2,591 / 4,320 (delta +1,270 vs baseline-4 at 1,321), remaining 1,729, ledger gap 0 at every check.

- Usable: 6 cells (pointer-stable r1,r2,r5,r6; lease-reopen r1,r2) — `usable_for: ["h1","h2","h3"]`.
- Excluded by stamp: 8 cells — transcript-grow r1–r6 (`evicted_turns=0`) and transcript-compact r1–r2 (`digest_rows=0`): treatments never fired inside 48 turns.
- Refused, no manifest, excluded by name: 2 cells — pointer-stable r3, r4 (runner cap gate, cell.py exit 4, 47/46 turn rows).
- Report (`run_grid_report.py`, verdict row `.scratch/grid2/VERDICT-REC-2.json`, pass, exit 0): h1 `not_adjudicable_floor` (pointer n_eff 26.14 < 60; grow arm absent), h2 `not_adjudicable`, h3 `not_adjudicable`, tvs `UNDEFINED`.
- Harness defect found and reported (not repaired): cell.py nests `rows_path` under `run.rows_path`, so `analyze_stats.load_cell_manifests` cannot link rows→stamp; the report needed a census derived from the manifests (`--sanity`).
- Not done, by design: no canary re-run, no retry of any cell, no harness/GRID-PARAMS/ledger/baseline/grade edit, no era-A pooling.
