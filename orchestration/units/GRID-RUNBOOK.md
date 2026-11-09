# UNIT GRID-RUNBOOK

**Purpose:** write the page a fresh session reads before touching a running or interrupted grid.
Documentation only — no harness edit, zero requests.

**Write paths (exactly):** `docs/GRID-RUNBOOK.md` · `orchestration/units/GRID-RUNBOOK.md` ·
`orchestration/handoffs/GRID-RUNBOOK.json` · `orchestration/journals/GRID-RUNBOOK.jsonl`

**Hard bound:** 24 tool calls; journal first; handoff within 6 calls; verdict row before handoff.
**Never** `ask_user_question`; zero sockets.

**Kill condition:** if a command cannot be verified from `--help`/source in ≤2 tries, print it marked
`UNVERIFIED` and continue.

## Delivered
`docs/GRID-RUNBOOK.md` — 7 sections: pre-flight checklist (11 rows + the stale-pin trap + the
12×60=720 s G2 canary wall), resume procedure (grid_resume shape, counting command, 4-row decision
table), exit-code table 0–13 with the 5/6 asymmetry, between-cell ritual (4 lines), killed-session
recovery (5 prohibitions + 2 truth commands), stop-report format (8 classes), and 8 named unknowns.

## Measured findings recorded
- HARNESS-PIN is **generation 4** `fa6fd8cc…`; GRID-PARAMS rev 2 still says
  `--expect-harness 2b4d4808…` (generation 3) → that value exits **2** at `2/7 harness`.
- Grid state: **0 of 10 cells complete**; `pointer-stable r1` has **two** rows files (6 turns on an
  earlier fixture sha `967cef03…`; 27 turns `era_a_excluded`, `tools_mode=off` 27/27,
  `stop_reason=runaway_turn` at 27).
- Ledger: spent 1,128 / remaining 3,192 / cap 4,320 / delta 0; baseline sha `3b79f476…`.
- `min_n_for(0.95) = 60` (TAIL_MIN 3, MIN_N 20 → ceil(3/0.05)=60).
- Card said `cell.py:1568` maps runner 9 → runner-crash; the actual site is **`cell.py:1616`**.
- Card described exit `6` as "abandon"; the authoritative table says **6 = runaway** and nothing in
  `cell.py`/`run_a_star.py` raises an "abandon" code.
