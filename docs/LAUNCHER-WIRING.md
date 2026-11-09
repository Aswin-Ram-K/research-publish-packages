# LAUNCHER-WIRING — one number, one owner

`experiments/ptr-engine/tools/run_a_star.py` is the only thing that starts a grid or
canary cell. It used to carry its own copies of three numbers that records under
`experiments/ptr-engine/measure/` own, and by 2026-10-26 all three copies were stale:

| number | the record said | the launcher said | consequence |
|---|---|---|---|
| harness pin | gen 5 `35ff41b7…` | gen 4 `fa6fd8cc…` | **every cell aborted** with `HARNESS-PIN record disagrees with the launcher` |
| cells | 16 (6/6/2/2) | 10 (3/3/2/2) | a dry run reported `cells=10` against a 16-cell record |
| price | 1,056 | *nothing printed* | the record's price had no launch-side witness |
| remaining | 3,192 (cap 4,320) | `3219` at four sites | the pre-rebuild total, off by 27 |

## The rule

A launcher **obeys** its records and **refuses** when it cannot:

1. **pin** — `measure/HARNESS-PIN.json` `generation` + `harness_sha256` are read at
   import time. `PIN_EXPECTED_GENERATION` / `PIN_EXPECTED_DIGEST` are the launcher's
   signed-off expectation; a record that moved without them is a refusal naming both
   digests. A launcher that silently follows any pin is the same defect in the other
   direction — the pin exists so a launch happens against bytes somebody froze.
2. **cells** — `measure/GRID-PARAMS.json` `shape.arms` is the plan; the launcher's
   `SHAPE_EXPECTATION` must equal it and `plan_cells()` derives the `(arm, rep)` list.
   Promoting the shape is a data edit to both, in one card.
3. **price** — `price.total` is read and printed beside the remaining figure the
   price is drawn from. Its absence is `GRID-PARAMS price.total MISSING at <path>`,
   never a blank line.
4. **remaining** — one basis, stated in the printed line: `remaining_basis=ledger:baseline-2`
   (`LEDGER-GRID-BASELINE-2.json`, cross-checked against `REQUEST-LEDGER.json`). Two
   records that disagree are a refusal, not a choice. `3,219` appears nowhere.

Both records are gates in `main()` before any plan is built, so a refused record can
start no cell at all (`pinned_digest()`, `grid_record()`).

## What a dry run prints

```
RUN-A PRICE source=experiments/ptr-engine/measure/GRID-PARAMS.json price_total=1056 \
  price_remaining_after=2136 remaining=3192 remaining_basis=ledger:baseline-2 \
  cap=4320 cells=16 price_approved=false
RUN-A DRY END cells=16 refused=0 requests=0 claim=H2 turns=48 max_wall=2880 \
  canary_arms=16 canary_requests=0
```

## Test hooks (test-only, both read at import)

- `RUN_A_STAR_PIN` — read the pin from another record (the `/tmp` mismatch proof).
- `RUN_A_STAR_GRID` — read the grid record from another path (the missing-price proof).
- `RUN_A_STAR_PATH` — used by the suite's own red runs to load a reverted launcher.

## Verification

```
.venv/bin/python -m pytest experiments/ptr-engine/tests/test_launcher_pin_and_cells.py -q
.venv/bin/python experiments/ptr-engine/tools/run_a_star.py --dry-run
```

Guards: real pin ⇒ proceeds; wrong digest ⇒ refusal naming both digests; shape
disagreeing with the signed-off promotion ⇒ refusal; missing `price.total` ⇒ named
refusal; ledger disagreement ⇒ refusal; dry run ⇒ no socket, no live `cell.py`, no
warm-up. See `orchestration/handoffs/LAUNCHER-GEN5-WIRE.json` for the red→green quotes.
