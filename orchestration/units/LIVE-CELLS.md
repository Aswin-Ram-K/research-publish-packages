# LIVE-CELLS — three live cells, 2026-10-26

**Status: BLOCKED at STEP 0.** No engine answered; no cell attempted; zero rows written.

## Purpose
Fill the three cells offline evidence could not settle: A = SGLang `:8012` occamy-1.0 residue-0 warm
(decides C1); B = SGLang `:8012` compact-index UNPADDED (decides C5); C = vLLM `:8014` G6 at residue 1
(closes C2). Rows go to a NEW file; existing row files stay untouched.

## What happened
- `curl -sS -m 5 http://127.0.0.1:8012/get_server_info` → exit 7,
  `curl: (7) Failed to connect to 127.0.0.1 port 8012 after 0 ms: Could not connect to server`, 0-byte body.
- `curl -sS -m 5 http://127.0.0.1:8014/v1/models` → exit 7,
  `curl: (7) Failed to connect to 127.0.0.1 port 8014 after 0 ms: Could not connect to server`, 0-byte body.
- Refused, not timed out (0 ms), so this is "nothing listening on loopback", not a slow server.

## Consequence
STEP 0 makes an unreachable engine a finding and forbids fabricated rows, so cells A/B/C were **not**
sent and `experiments/ptr-engine/measure/rows-live-2026-10-26.jsonl` was created **empty (0 bytes)**.
`rows_written = 0`, `cached_nulls = 0`, `engine_reachable = false`. C1, C5 and C2 still lack their rows.

## Open discrepancy for the operator
`experiments/miss-law/LAW.md` §1 documents these same servers at `http://192.168.2.168:8012/v1` and
`http://192.168.2.168:8014/v1`; this card names `127.0.0.1` and forbids other hosts, so the LAN address
was **not** probed. Either the engines bind only the LAN interface (card host wrong) or they are down.
Deciding that needs an operator, not a guess.

## To resume
Re-issue unchanged when a probe answers on both loopback ports; or have the operator authorise
`192.168.2.168` and change the endpoint string — the cell definitions need no other rework.

**Bound used: 6 tool calls.** Handoff: `orchestration/handoffs/LIVE-CELLS.json`.
