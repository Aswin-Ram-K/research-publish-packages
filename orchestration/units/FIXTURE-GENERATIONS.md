# UNIT FIXTURE-GENERATIONS

**Card:** one spec, one generator for LR-01 runtime fixtures. **Automated, offline:** zero inference
requests. **Bound:** ≤32 tool calls; handoff written before the bound. **Mode:** workspace-write.
**Status:** done.

## Objective
Replace six hand-edited runtime fixtures with a single spec (`fixtures-spec/LR-01.spec.json`), a single
generator (`tools/build_fixture.py`) and a guard (`longrun/experiments/ptr-engine/longrun/tests/test_build_fixture.py`), and record the
inventory in `docs/FIXTURE-GENERATIONS.md` — without modifying or deleting any existing runtime fixture.

## Deliverables (write paths, exactly)
- `experiments/ptr-engine/longrun/fixtures-spec/LR-01.spec.json`
- `experiments/ptr-engine/tools/build_fixture.py`
- `experiments/ptr-engine/longrun/tests/test_build_fixture.py`
- `docs/FIXTURE-GENERATIONS.md`
- `orchestration/units/FIXTURE-GENERATIONS.md` (this card)
- `orchestration/handoffs/FIXTURE-GENERATIONS.json`
- `orchestration/journals/FIXTURE-GENERATIONS.jsonl`

## Method
1. Inventory from disk: every `schema: consonance.longrun-fixture/1` document (not just
   `tasks*/runtime*/`), plus the digests pinned by row files that have no file behind them.
2. Spec = `base` (v1 document) + one named **deep merge-patch** per generation + per-variant `emit`
   block. `@order` is a reserved patch key so key order is reproduced, because order is bytes.
3. Generator: `--variant`, `--out`, `--check` (all paths or one file), `--force-frozen`; refuses frozen
   by recorded path *or* by digest and prints the referencing rows.
4. Guard: 5 tests, red→green (red: generator absent → 5 failed; green: 5 passed).

## Acceptance evidence
- `v5` regenerates to `967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567` (== live file).
- `v6` regenerates byte-identically (`ff89625d…`, 50254 bytes) — `cmp` clean.
- `--check` over all ten recorded paths: 10 × `ok`, exit 0.
- Frozen overwrite of byte-identical copy in `/tmp`: exit 3, rows named, target bytes unchanged.
- Sibling fixtures `LR-0[2-6]` (v1 and v2) untouched: all ten digest prefixes verified after the work.

## Constraints honoured
No inference requests. No existing runtime fixture written, moved or deleted. No edits to
`grade_v5.py`, `cell.py`, `client.py`, `run_longrun.py`, `analyze_stats.py`, `fixture_coverage.py`.
