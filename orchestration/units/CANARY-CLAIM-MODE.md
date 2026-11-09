# CANARY-CLAIM-MODE — settle the canary's claim mode by test

**Status:** done · **Cost:** 0 requests, 0 sockets, 0 live cells · **Bound:** 26 tool calls.

## Objective
Determine the exact argv that makes a 12-turn canary write rows that cannot enter the arm
comparison, and prove the analyser refuses them by name.

## Findings
- `run_longrun.py` accepts `--claim-mode smoke|plumbing|H1|H2|H3` (`:2831-2839`); resolves at
  `:2962`; absent/empty/`none`/unknown → exit 12 (`:2971-2975`). Temp-dir rows are exempt and
  auto-stamped `claim=none` (`:1754-1763`, `:2965-2970`).
- `cell.py` accepts `--hypothesis` (`:1887`) and **forwards the resolved claim to the runner**
  (`:1590-1594`), plus a `.claim.json` sidecar (`:1566-1587`) — no claim wiring is missing.
- `--tools` is the missing forward (no `cell.py` argument); `run_a_star.py:52-66`'s
  `CELL_RUNNER_PATH` runpy shim appends it without changing runner bytes.
- `analyze_stats.py` refuses `claim:"none"` rows by name: `incomparable_claim` (`:173`, `:216-240`).
- **Hazard measured in the launcher:** `run_a_star.py:182` hard-codes `"--hypothesis", "H2"`,
  so the card as written would pool 48 ungraded canary rows.

## Smallest wiring (NOT applied)
Make `run_a_star.cell_argv` carry its `hypothesis` parameter (recorded but unused at `:194`)
and pass `smoke` for the canary. One line; a separate card.

## Write paths
`docs/CANARY-ARGV.md`, `tests/test_canary_claim_mode.py`, this card, the handoff, the journal.
No runner, cell, analyser, rows, grades, thresholds or published pages were edited.
