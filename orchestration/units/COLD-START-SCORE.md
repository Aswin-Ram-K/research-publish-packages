# UNIT `COLD-START-SCORE`

**Status:** done · **Date:** 2026-10-26 · **Requests:** 0 · **Spawns:** 0

## Purpose
Score `COLD-START-PROBE`'s fresh-main reconstruction against the eight-item rubric frozen **before** the
probe ran. Measure the inheritance gap: what a competent fresh session gets wrong from the record alone.
Score only — repair nothing.

## Hard bound
18 tool calls. Never ask the user. Offline: zero inference requests.

## Deliverables (write paths, exactly)
- `experiments/ptr-engine/measure/COLD-START-SCORE.json`
- `docs/COLD-START-SCORE.md` (<=60 lines)
- `orchestration/units/COLD-START-SCORE.md`
- `orchestration/handoffs/COLD-START-SCORE.json`
- `orchestration/journals/COLD-START-SCORE.jsonl`

## Result
4.5 / 8. 3 CORRECT, 3 HALF, 1 WRONG, 0 GAP_HONEST, 1 GAP_DISHONEST (item 1: probe wrote `silent` where
`OPERATOR-BRIEF.json` records `not adjudicable`; item 5 WRONG: claims the card still prices 792 when it
prices 660 / 10 cells). Record is **not yet sufficient** for a successor: no first-read file states the
thesis verdict in one line.
