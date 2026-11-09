# CANARY-ERA-B-4

**Purpose.** First live era-B canary that can actually answer a tool call: 4 arms (pointer-stable,
transcript-grow, transcript-compact, lease-reopen) × 12 turns, `--tools read_file`, `--thinking off`, to
measure whether `tools_schema_sent` / structured `tool_calls` / `tool-followup` / billed fetch rounds now
appear after `TOOL-CHANNEL-WIRE` (exec `dda84411`, PASS) and whether each arm classifies `shape_ok`.

**Bound.** 30 tool calls, one invocation, no retries, hard live cap 52 requests.

**Kill condition.** Any failed gate in the card's gate list ⇒ STOP without spending a request; if the
launcher or the pin is broken, report and do not repair.

**Write paths.**
- `experiments/ptr-engine/measure/CANARY-ERA-B-4.json`
- `docs/CANARY-ERA-B-4.md`
- `orchestration/units/CANARY-ERA-B-4.md` (this card)
- `orchestration/handoffs/CANARY-ERA-B-4.json`
- `journal/2026-10-26.md`

**Forbidden.** `cell.py`, `run_longrun.py`, `run_a_star.py`, `client.py`, `analyze_stats.py`, `grade_v5.py`,
`measure/HARNESS-PIN.json`, `measure/GRID-PARAMS.json`, `measure/REQUEST-LEDGER.json`, any fixture, any row,
any grade file, any published page.

**Outcome — first execution (preserved).** Stopped at gate 2 (launcher REFUSED on disagreeing ledger records,
exit 1). Zero requests sent. `grid_may_launch: false`. Deliverables written; no repair attempted.

**Outcome — second execution (current).** Gates 1–3 PASS: gen-6 pin, composite digest recomputed from disk to
`efefd885…`; dry run exit 0 printing `canary_arms=4 canary_requests=48 refused=0` plus `RUN-A DRY END
cells=4 refused=0`; argv carries `--expect-harness efefd885…` (`run_a_star.py:786`). Gate 4: the ledger did
not move (`requests 1176 / remaining 3144 / generated_at_utc 2026-10-26T22:33:00Z`, before and after) because
the launcher was killed before its rebuild — the row files bill 59 requests (10 tool-followup rows + 2
duplicate bodies) against a priced 48, reported as a finding.

The live canary ran **once** (`--tools read_file --canary --budget 108 --hypothesis smoke --max-wall 900`,
no `--reps`, no retry) and was interrupted by two host restarts. Three arms completed 12 turns
(pointer-stable 25 rows, transcript-grow 13, transcript-compact 14) and wrote their grade-v5/analysis/md
artefacts; `lease-reopen` stopped at 7 rows / turn 3 with no terminal row.

**The answer (headline).** The tool channel works: `tools_schema_sent` is `true` on **59/59** rows, **40/59**
carry a non-empty structured `tool_calls` (78 call items, 14 executed), there are **10** `tool-followup` rows,
and no row needed the text notation. This replaces the 0-of-36 result of `LIVE-CANARY-4ARM-3`.

**Shape.** pointer-stable, transcript-grow, transcript-compact = `shape_ok` (`answer_verified` 2/1/1, terminal
`finish_reason: stop`) — every one labelled as the **`finish_reason` fallback**, because `stop_signal_source`
is **absent on all 59 rows**; that `CANARY-ERA-B-FIX` gap is still open. `lease-reopen` = `shape_unknown`
(cut at turn 3 of 12). No cap-length completion anywhere.

**Decision.** `grid_may_launch: false` — three of four `shape_ok`; the hold is the missing fourth arm, not a
channel failure. Resolving measurement: one complete 12-turn `lease-reopen` cell on this generation-6 tree.

**Findings reported, not repaired.** (1) `cell.py` moved outside the pin after gen 6 froze (`0bddd4e0…` →
`c494e212679f8e73c84226cf486566d0716559c0f2cd677f20845b24057baf86`, mtime `2026-10-27T00:17:51Z`), digest
immune by design, change unattributed. (2) The card's invocation string carries five flags the launcher rejects
(`unrecognized arguments`, exit 2); the same values are hard-coded in `cell_argv` (`run_a_star.py:781-787`).
(3) `stop_signal_source` still absent on era-B rows.

**Tool calls.** ~24 of the 30-call bound; one live invocation, no retries.
