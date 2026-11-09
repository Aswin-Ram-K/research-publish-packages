# UNIT `HARNESS-MAP-V2` — the map must describe the harness that exists

**Status** done · **Bound** ≤30 tool calls, zero inference requests, no network, no `git` · **Automated** (no questions)

## Purpose (one)
Re-derive `docs/HARNESS-MAP-V2.md` from the code — stages, reads, writes, exit codes verified at the raise site, gates —
and measure **this batch's own cost** from `orchestration/journals/*.jsonl` + `orchestration/handoffs/*.json`, re-rank the
14 v1 inefficiencies, add the ones this session discovered, and price the gate chain.

## Inputs (read-only)
- `docs/HARNESS-MAP.md` (42,410 B, 329 lines) — historical record, **never edited**
- `experiments/ptr-engine/longrun/{cell.py,run_longrun.py,client.py}`
- `experiments/ptr-engine/tools/{frozen_tree,request_ledger,unit_journal,handoff_lint,matrix_audit,stop_reason_audit}.py`
- `orchestration/journals/*.jsonl` (18), `orchestration/handoffs/*.json` (973 total, 20 this batch)

## Declared write paths (exactly)
1. `docs/HARNESS-MAP-V2.md`
2. `experiments/ptr-engine/measure/HARNESS-MAP-V2.json`
3. `orchestration/units/HARNESS-MAP-V2.md`
4. `orchestration/handoffs/HARNESS-MAP-V2.json`
5. `orchestration/journals/HARNESS-MAP-V2.jsonl`

Nothing else is written. No source, row, grade, fixture or handoff file is edited.

## Kill condition
If the exit-code set could not be verified at a raise site within the bound, the map reports those codes as
`not_verified` with the grep used — it does not estimate. A figure that cannot be measured is `not_measured` with the
reason.

## Deliverable shape
- Stage table (16 stages, re-derived) with reads/writes/exit/gate.
- Complete exit-code table `0,1,2,3,4,5,6,7,8,9,11` with path:line per code, plus `declared_but_unraised` (7) and
  `undeclared_but_raised` (1).
- Batch measurement: cards 20, rounds 20, live requests 0, zero-request rounds 20/20, tool calls 116 across 6 reporting
  cards, wall spans 15 cards / 6 473 s, heaviest stage = audit.
- The 14: closed 7 / narrowed 4 / open 2 / superseded 1; new ranked top 5.
- Five new inefficiencies (N1–N5) with artefact and fix.
- Gate-chain overhead: 54/71 recorded commands verification-shaped (76.1 %) vs 4 change-shaped.
- One-page ASCII pipeline + "where to look when a run fails".

## Result
`done` — see `orchestration/handoffs/HARNESS-MAP-V2.json` for the evidence lines.
