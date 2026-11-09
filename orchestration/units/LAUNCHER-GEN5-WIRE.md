# LAUNCHER-GEN5-WIRE

**Purpose.** Make `experiments/ptr-engine/tools/run_a_star.py` obey the records it is
launched against instead of carrying copies of three numbers that had already moved:
the harness pin (gen 4 `fa6fd8cc` vs record gen 5 `35ff41b7`), the cell plan (10 vs
16), and the remaining figure (`3219` at four sites vs the ledger's `3,192`). The
launcher aborted before cell 1 with `HARNESS-PIN record disagrees with the launcher`,
which made every launcher suite red for a reason that was not its own.

**Hard bound.** 30 tool calls. Stop and report if the record and the launcher cannot
be reconciled without editing a forbidden file.

**Write paths (declared).**
- `experiments/ptr-engine/tools/run_a_star.py`
- `experiments/ptr-engine/tests/test_launcher_pin_and_cells.py` (new)
- `docs/LAUNCHER-WIRING.md` (new)
- `orchestration/units/LAUNCHER-GEN5-WIRE.md`
- `orchestration/handoffs/LAUNCHER-GEN5-WIRE.json`
- `orchestration/journals/LAUNCHER-GEN5-WIRE.jsonl`

**Forbidden.** `longrun/cell.py`, `run_longrun.py`, `analyze_stats.py`, `grade_v5.py`,
`measure/GRID-PARAMS.json`, `measure/HARNESS-PIN.json`, `measure/REQUEST-LEDGER.json`,
any row/grade/fixture, any published page. No threshold, factor or cap moved; the
2,880 s grid wall and the 900 s canary wall are untouched.

## What changed

| number | before | after | owner now |
|---|---|---|---|
| pin | constant gen 4 `fa6fd8cc` at `:51`, check `gen != 4` | `PIN_EXPECTED_GENERATION=5` / `PIN_EXPECTED_DIGEST=35ff41b7…`, record read at import | `measure/HARNESS-PIN.json` |
| cells | literal 10-tuple `:99-103` | `SHAPE_EXPECTATION` 6/6/2/2 data + `plan_cells(record)` | `measure/GRID-PARAMS.json` `shape.arms` |
| price | no price line at all | `PRICE … price_total=1056 … remaining=3192 remaining_basis=ledger:baseline-2 cap=4320 cells=16` | `measure/GRID-PARAMS.json` `price.total` |
| remaining | `3219 - (spend() - spent0)` ×4 | `base_remaining - (spend() - spent0)`, basis `ledger:baseline-2` | `LEDGER-GRID-BASELINE-2.json` + `REQUEST-LEDGER.json` |

Both records are now gates in `main()` before any plan is built (`pinned_digest()`,
`grid_record()`), so a launcher that cannot read — or does not agree with — its
records never reaches the cell loop.

## Evidence

- dry run: `RUN-A DRY END cells=16 refused=0 requests=0 claim=H2 turns=48 max_wall=2880 …`, rc 0.
- canary dry run unchanged in shape: `cells=4 … canary_requests=48`, rc 0.
- new suite `test_launcher_pin_and_cells.py`: **12 passed**.
- existing suites: baseline **12 failed, 2 passed** → after **1 failed, 13 passed**;
  the survivor is `tests/test_run_a_star_claim.py:103` `assertEqual(PIN_GEN, 4)` —
  a stale expectation outside this card's write paths, quoted not fixed.

## Red → green

Each guard was reverted in a copy under `state/logs/launcher-gen5-red/` and run with
`RUN_A_STAR_PATH`; the red message is quoted in the handoff. The dry runs opened no
socket and launched no live `cell.py`; 0 model requests, 0 source requests.
