# UNIT `COLD-START-PROBE` — reconstruct the state from the record alone

**Status:** done. **Requests:** 0. **Spawns:** 0. **Dispatched nothing.** **Tool calls:** ≤24 (bound 24).

## Purpose
Behave as a fresh main session landing on workspace `78cead56` with no chat history: read only the board thread,
`VERDICTS.md`, `STATUS.md`, `handoffs/*.json`, the measure ledger/withdrawn register, `docs/GATE-CHAIN.md`,
`docs/EXIT-CODES.md`, `docs/PRICE-REPLICATION.md`, `docs/P95-POWER.md`, `AGENTS.md` — and answer eight questions,
writing `SILENT` / `CONTRADICTORY` / `STALE` wherever the record is absent, inconsistent or old rather than guessing.

## Forbidden and honoured
No dispatch, no settle, no card creation, no repair. No other agent's chat, no journal, no `docs/OPERATOR-BRIEF*.md`.
No edit to `VERDICTS.md`, `STATUS.md`, any handoff or any measure file except the two deliverables.

## Result
All eight answered from disk; statuses: 1 silent (objective answered, verdict word absent), 2 answered,
3 silent (mechanisms answered, clearing card ids absent), 4 answered, 5 contradictory (card text 792 vs priced
660), 6 answered, 7 answered (phantom `docs/BUDGET-SCHEDULE.md`), 8 answered.

Findings worth a later card, none repaired here:
1. `docs/BUDGET-SCHEDULE.md` is cited by `PRICE-REPLICATION` in four artefacts and does not exist (real path
   `experiments/ptr-engine/measure/BUDGET-SCHEDULE.md`).
2. The operator's thesis has **no verdict word** anywhere; the batch table is an aggregate over cards.
3. No clearing card id is recorded for any of the three holds — the holds are described, their successors are not.
4. `orchestration_board read` with `limit`/`since` returns from the beginning of the thread and truncates, so the
   "newest 40 replies" the card asked for cannot be read; the board-dependent answers came from handoffs instead.

## Deliverables
`docs/COLD-START-PROBE.md`, `experiments/ptr-engine/measure/COLD-START-PROBE.json`, this card,
`orchestration/handoffs/COLD-START-PROBE.json`, `orchestration/journals/COLD-START-PROBE.jsonl`.
