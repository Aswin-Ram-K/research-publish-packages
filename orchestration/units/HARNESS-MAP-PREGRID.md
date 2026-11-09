# UNIT `HARNESS-MAP-PREGRID`

**pre_grid: true** · 2026-10-26 · offline, zero requests · ≤30 tool calls (used 27).

## Purpose

Write the batch's scoreboard **on the corpus that exists**, before the grid, so it cannot be fitted to a
result. It grades the harness and this unit's conduct, not the arms. `HARNESS-MAP-V4` is structurally
post-grid (it needs `handoffs/OPERATOR-BRIEF-5.json`), so this card carries the pre-grid view and writes
its own paths.

## Contract

1. Stage map at HEAD from disk, with `unlocated` allowed and never guessed; diff vs `docs/HARNESS-MAP.md`.
2. Two cost tables, never averaged: offline per settled card (`handoffs/*.json`), live per cell (row files).
3. Re-adjudicate the 14 v1 inefficiencies: `closed` only with a proving refusal site or test path.
4. Rank new waste this batch introduced **including this unit's own**.
5. Verdict-rate table before/after the ritual; retroactive rows reported separately.
6. One of three words, with the number or the missing instrument.

## Hard rules observed

- No `ask_user_question`; zero sockets; write only the five declared paths.
- Never read `rows-cell-*` as a completed cell — both are `usable_for: []` and are cited only as launch
  mechanics.
- Never edit `docs/HARNESS-MAP.md`, `docs/HARNESS-MAP-V2.md`, `docs/HARNESS-MAP-V3.md`, or any card text.

## Result

`not measurable yet` — the missing instrument is one gated, completed cell. 13 stages, 0 `unlocated`;
6 closed / 7 narrowed / 1 open on the 14; verdict rate 2.6 % → 94.1 % after the ritual, with 35
retroactive rows reported separately.

Full report: `docs/HARNESS-MAP-PREGRID.md`; machine form:
`experiments/ptr-engine/measure/HARNESS-MAP-PREGRID.json`.
