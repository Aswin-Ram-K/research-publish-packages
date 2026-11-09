# UNIT `GATE-LEDGER` — price the gate chain

**Status:** done · **Bound:** ≤30 tool calls · **Requests:** 0 · **Writes:** `experiments/ptr-engine/measure/GATE-LEDGER.json`,
`docs/GATE-LEDGER.md`, `experiments/ptr-engine/tools/gate_ledger.py`,
`experiments/ptr-engine/longrun/tests/test_gate_ledger.py`, `orchestration/units/GATE-LEDGER.md`,
`orchestration/handoffs/GATE-LEDGER.json`, `orchestration/journals/GATE-LEDGER.jsonl`, `/tmp/gl/**`

## Objective
Per gate (G1 cap, G2 projection, G3 prereg, and the refusal-spawn rule): what it prevents
(named incident or `nothing observed`), what would replace it, how many defects the guard
itself had, whether a live path can still bypass it (`thinking=off` separately from `on/auto`),
and a decision `keep` / `demote_to_advisory` / `retire` carrying one of the two licensed
compliance sentences. Cost tabulated per gate-related card from the handoff corpus and the
Host board ledger — counted, not estimated.

## Hard rules honoured
`cell.py`, `run_longrun.py`, the fixture, `EXIT_TABLE` and the normative table in
`docs/GATE-CHAIN.md` were **not edited** (the rehearsal pin). Offline, 0 requests.

## Bound used
~20 of 30 tool calls. 0 inference requests; one offline `--dry-run` (0 sockets, 0 subprocesses
of a live runner) at RUN-A*'s own flags to measure G1/G2/G3's decision.
