# PTR-ENGINE-P0.1 — close the four verifier defects

**Purpose.** Small, surgical fixes to `experiments/ptr-engine/` for the four defects in
`orchestration/handoffs/V-ENGINE-P0.json`: (1) the one-way guard tests only a synthetic
`ResourceRef`; (2) SPEC.md:86-87 promises superseded-revision resolution the code refuses;
(3) SPEC.md:166 promises every failure is a `PtrError`, 6 bare `ValueError` sites remain;
(4) two SPEC overstatements plus dead `TurnIndex.body_bytes`.

**Bound.** 35 tool calls; no network, no live model calls, no server.

**Write paths.** `experiments/ptr-engine/**` (incl. `SPEC.md`, `CHANGELOG-P0.1.md`,
`.p0-scratch/**`), `orchestration/units/PTR-ENGINE-P0.1.md`,
`orchestration/handoffs/PTR-ENGINE-P0.1.json`.

**Forbidden.** `release/**`, `papers/**`, `src/**`, `experiments/agentic-lazy/**`,
`experiments/miss-law/**`, `/home/zer0null/Duval`. The seven existing negative-control
codes must not change; no existing test weakened or deleted.

**Deliverable.** Updated engine + SPEC, `CHANGELOG-P0.1.md` (one entry per defect with an
evidence line), handoff JSON with `evidence.command_or_count` + `commands`, new test count
and unchanged `r` = 30000/447 = 67.1x.

**Status:** done -- all four defects closed; evidence in `orchestration/handoffs/PTR-ENGINE-P0.1.json` and `experiments/ptr-engine/CHANGELOG-P0.1.md`.
