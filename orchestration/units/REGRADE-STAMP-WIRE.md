# Unit REGRADE-STAMP-WIRE

**Owner:** single unit, no subagents. **Bound:** ≤20 tool calls, 0 network requests.
**Status:** done. **HEAD at start:** f17663d1fed0162a7dc3c5a0a58d372c710974c3.

## Purpose

`V-STAMP-NEUTRAL` settled **partial with `evidence: null`** and named exactly two
defects. Make regrade resolve the grader instead of pinning it, and make its output
carry the same three stamps `grade_v5.py` writes.

* **F1** — `tools/regrade.py` pinned `DEFAULT_GRADER_SHA = 6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`, stale after
  `GRADER-STAMP` moved `grade_v5.py` to `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772`. Replace the constant with a
  run-time lookup through `tools/grader_identity.py`; any pin survives only as an
  *expected* value the resolver compares against.
* **F2** — regrade output must carry `grader_sha256`, `grader_version`, `rows_sha256`
  with `grade_v5`'s meaning. No historical document is restamped.

## Write paths (exactly)

* `experiments/ptr-engine/tools/regrade.py`
* `experiments/ptr-engine/longrun/tests/test_regrade_stamp.py`
* `experiments/ptr-engine/measure/REGRADE-STAMP-WIRE.json`
* `docs/REGRADE-STAMP-WIRE.md`
* `orchestration/units/REGRADE-STAMP-WIRE.md`
* `orchestration/handoffs/REGRADE-STAMP-WIRE.json`
* `orchestration/journals/REGRADE-STAMP-WIRE.jsonl`

`longrun/grade_v5.py` was read, never written. `/tmp` copies only for mutation.

## Result

* Resolver at `tools/regrade.py:72`, called at `tools/regrade.py:405`; the identity is
  `grader_identity.file_sha256(grader_path)`, `EXPECTED_GRADER_SHA` is an expectation
  only, `--sha256` remains the strict (exit 3) gate.
* Every regrade document carries all three stamps and is validated through
  `grader_identity.grader_identity()` (exit 3 on an invalid stamp).
* Proofs: historical grid differing paths = the four `*.decidable_source` era fields
  (finding); stamps provenance-only; clean pre-stamp case IDENTICAL exit 0; red stale
  pin quoted exit 3; edited grader `114e60a23e0bc03a12016690e91ff2d8680690a64c361d3197606b938090884a` caught by strict mode and recorded as
  drift; suites 6/8/6 passed.
* Open finding: `cell-pointer-stable-20261026T145722Z.grade-v5.json` does not reproduce
  (22 graded fields differ, pre-v5-era document) — separate card, not fixed here.

See `docs/REGRADE-STAMP-WIRE.md` for the full evidence and the verbatim red→green text.
