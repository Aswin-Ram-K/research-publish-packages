# HARNESS-MAP-V3

**Purpose.** Re-derive the harness stage map and the inefficiency ledger **after** the instrument batch
(`VERDICT-RITUAL`, `GATE-CHAIN` G1/G2/G3, `STOP-REASON`, `TVS`, `REQUEST-LEDGER`, `PROJECTION`, `ROW-PROVENANCE`,
`REGRADE-ONE-COMMAND`, `cell.py` as the one-command conductor), and state plainly whether building an experiment
got cheaper. **OFFLINE**: zero inference requests; read-only on every measurement.

**Origin.** `docs/HARNESS-MAP-V2.md` (unit `HARNESS-MAP-V2`, `2f004247`) refused to bank a 21× gain because the
batches did different work, and named its own three worst wastes: verification overhead, the 147 unlabelled rows,
and a journal that cannot report its own failure mode. This card re-tests all three against disk.

**Bound.** 30 tool calls; if a figure cannot be re-derived from the workspace, omit it and say the instrument is
missing — never estimate.

## Deliverable, exactly these sections

1. **Stage map as the code is today** — per stage (preflight/gates → fixture → runner → tool channel → row schema
   → grade → analyse → record → handoff → verdict): owning file, exercising command, measured or documented cost.
2. **Cost per experiment, measured** — rounds, tool calls, requests, wall-clock from unit handoffs and journals;
   median and range; offline and live batches reported separately, never averaged together.
3. **The 14 v1 inefficiencies re-adjudicated** — `closed` / `narrowed` / `open` / `superseded` with the proving
   artefact; "closed" without a test path is `narrowed`.
4. **New waste this batch introduced** — ranked, with counts and the owning card.
5. **Verdict rate before/after the ritual**, denominator stated (closures, not cards).
6. **One paragraph**: did building an experiment get cheaper, and by what measure — or `not measurable yet` with
   the specific missing instrument.

## Hard rules

- Never edit a rows file, grade file, ledger, TVS, latency report, fixture, `cell.py`, `client.py`,
  `run_longrun.py`, `analyze_stats.py`, or another card's handoff.
- No number without a path. Quote v2's figures with `v2` attached and give v3 beside them.
- Journal first; handoff within 5 calls of the deadline.

## Write paths (exactly)

`docs/HARNESS-MAP-V3.md` · `experiments/ptr-engine/measure/HARNESS-MAP-V3.json` ·
`orchestration/units/HARNESS-MAP-V3.md` · `orchestration/handoffs/HARNESS-MAP-V3.json` ·
`orchestration/journals/HARNESS-MAP-V3.jsonl`

## Kill condition

If the verdict rate or a per-experiment cost cannot be derived offline, state that and give the count actually
derived; deliver the document anyway (partial is a result).
