# R2-OPT-SIM — external-workspace pointer protocol + predictive cost model

Card kind: `task board` · tag `automated` · permission `workspace-write`
Status: **in progress** (owning unit; handoff written at the end to `orchestration/handoffs/R2-OPT-SIM.json`)

## OBJECTIVE

Rank prompt-layout x compaction candidates **offline**, before any of them spends a metered live
request, and give the constants a cost model needs that live in *another* workspace (GPU-side
prefill throughput, kernel timing, server configuration) a home that does not merge the two
workspaces. Deliverables: the pointer protocol below, a cost model calibrated only from rows
already on disk, a hold-out against measured rows, and a report.

## INPUT STATE (what already exists on disk)

- `experiments/context-cache/cells/LIVE-MEAS/rows.jsonl` — 960 measured rows, arms C/A/R/F × 2
  epochs × 80 turns (the hold-out).
- `experiments/context-cache/cells/U9/u9_trials.jsonl` — cold/warm length sweep, 139 rows,
  `completion_tokens == 1` on every row (so `ttft_ms` is pure prefill).
- `experiments/context-cache/cells/*/rows*.jsonl` — 33 cells; the layout scan
  (append vs rewrite) reads all of them.
- `src/resextract/context/{render,nodes,budget,meter,salt}.py` — the renderers and compaction
  policies whose cost this model prices.
- The external workspace this protocol points at is **not present** on this host and is not needed:
  every constant the model uses is derivable from the rows above. The protocol exists so that the
  one class of constants that is *not* derivable (GPU throughput ratios) can be added later without
  a merge.

## HARD BOUND

- **0 live requests. No `.occamy.lock`. No network.** Everything is derived from disk.
- Max 40 tool calls / 90 minutes of wall clock; stop and report `partial` if the hold-out still
  cannot be produced.
- No writes anywhere except the WRITE PATHS below; `/home/zer0null/Duval` and every registered
  target stay strictly read-only (no git at all is needed here — nothing is read from a target).

## WRITE PATHS

- `scratch/r2-opt-sim/**` (calibrate.py, cost_model.py, constants.json, report.json, selfcheck.py)
- `tests/test_r2_opt_sim.py`
- `orchestration/units/R2-OPT-SIM.md` (this card)
- `orchestration/handoffs/R2-OPT-SIM.json`
- `strategy/R2_OPT_SIM.md` (the report)

## VERDICT FORMAT

`orchestration/handoffs/R2-OPT-SIM.json`, unit shape (`unit`, `status`, `artifacts`, `evidence`,
`blocker`, `next_unit_hint`, `write_paths`) plus `assumptions`. Evidence is commands with their
actual output: the calibration rerun, the model run, the test suite, and the red→green self-check.

## DO NOT TOUCH

- Any file under `experiments/context-cache/cells/**` (read-only evidence).
- `src/**`, `docs/PLAN.md`, `orchestration/STATUS.md`, other units' handoffs or cards.
- Any systemd unit, DSH plugin or DSH service.
- `.occamy.lock` — never taken, because nothing here is metered.

## POINTER PROTOCOL

Three pointer roles, one manifest (this file). A pointer is a **path plus the manifest that declares
it**; resolution is per-workspace through named roots, so the same manifest yields a different
absolute path on another host and nothing is ever copied between workspaces.

| role | lives where | may be written by | absent is |
|---|---|---|---|
| `external` | outside this workspace (another machine's checkout) | nobody here — declared **read-only** | a status (`MISSING`), not an error |
| `cursor` | this workspace | this workspace (the boundary artifact an external reader consumes) | a status, not an error |
| `cell-source` | this workspace | nobody (evidence) | a status, not an error |

Rules that make the protocol safe:

1. **A constant must cite its source.** Every number in `constants.json` carries the `source_id`
   it came from and the cell (file + row selector). `validate_constants` refuses any constant
   without a pinned `source_id` or without a rerun command, and `cost_model.py` exits non-zero.
2. **External constants are normalised, never copied.** An external number is accepted only as a
   *ratio* against a same-unit in-workspace constant (throughput ratio, relative kernel time). A raw
   external latency never enters the model, because it was measured on another machine's state.
3. **Absence degrades, it never blocks.** A missing root or manifest downgrades a constant to
   `degraded` and the model reports it; the run still produces a ranking.
4. **Digest, not path.** A pointer may carry a `sha256`; a mismatch is `DIGEST_MISMATCH`, so a
   silently changed source cannot be mistaken for the one the model was fitted on.
5. **One writer per pointer.** Only the role table decides who may write; nothing here writes an
   `external` or `cell-source` pointer.

```json
{
  "schema": "resextract/r2-opt-sim/pointers/1",
  "unit": "R2-OPT-SIM",
  "roots": {
    "own": {"path": "/home/zer0null/reserach extarctor", "mode": "workspace-write", "declared": true},
    "external": {"path": "", "mode": "read-only", "declared": false, "reason": "no such workspace is reachable from this host; every constant used below is derivable from own-root cells"}
  },
  "pointers": [
    {"source_id": "experiments/context-cache/cells/LIVE-MEAS/rows.jsonl", "path": "experiments/context-cache/cells/LIVE-MEAS/rows.jsonl", "role": "cell-source", "manifest": "orchestration/units/R2-OPT-SIM.md", "bytes_expected": null, "note": "960 measured rows; hold-out tail turns 41-80 of every arm"},
    {"source_id": "experiments/context-cache/cells/U9/u9_trials.jsonl", "path": "experiments/context-cache/cells/U9/u9_trials.jsonl", "role": "cell-source", "manifest": "orchestration/units/R2-OPT-SIM.md", "bytes_expected": null, "note": "cold/warm length sweep, completion_tokens == 1"},
    {"source_id": "experiments/context-cache/cells/LIVE-MEAS/plan.json", "path": "experiments/context-cache/cells/LIVE-MEAS/plan.json", "role": "cell-source", "manifest": "orchestration/units/R2-OPT-SIM.md", "bytes_expected": null, "note": "budget 8192, keep_last 2, fold_schedule [18,35,53,71]"},
    {"source_id": "cross-feed-cursor", "path": "orchestration/cursors/r2-opt-sim.json", "role": "cursor", "manifest": "orchestration/units/R2-OPT-SIM.md", "bytes_expected": null, "note": "the boundary artifact an external reader consumes: {constants_sha256, report_sha256, written_at}; written by this unit, read by nobody here"},
    {"source_id": "external:gpu-prefill-throughput", "path": "bench/prefill_throughput.jsonl", "role": "external", "manifest": "orchestration/units/R2-OPT-SIM.md", "bytes_expected": null, "note": "DECLARED, ABSENT on this host; if present it is accepted only as a ratio against this workspace's measured us/token"}
  ]
}
```

## PLAN

1. Calibrate every constant from disk (`scratch/r2-opt-sim/calibrate.py`).
2. Price a candidate turn as `lookup(prompt) + excess_miss(uncached)` (`cost_model.py`).
3. Hold out: fit on turns 1-40 of all arms, predict turns 41-80.
4. Rank a candidate set; report the band and which orderings are robust.
5. Test the constants against their cells, with a red→green self-check.
