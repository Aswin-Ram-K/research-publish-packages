# U-SPCC-9B — Repair repairable class-(a) failures (derived artefacts only)

No `rows-*.jsonl` edited. No test file edited. No digest invented.

## Regenerated artefacts

|Artefact|Generator|First output line|
|---|---|---|
|`experiments/ptr-engine/measure/STOP-REASON.json`|`tools/stop_reason_audit.py`|`{"unit": "STOP-REASON-AUDIT", "generated_by": "experiments/ptr-engine/tools/stop_reason_audit.py", ...}` — `--check OK matches fresh scan`|
|`experiments/ptr-engine/measure/VERBOSITY.json` + `docs/VERBOSITY.md`|`longrun/tests/test_verbosity.py` (build() inside the test)|`{"unit": "VERBOSITY-CONFOUND", "generated_utc": "2026-11-09T14:05:25Z", "offline": true, ...}` — `cells=108 p95_ok=32 refused=73`, `VALIDATE_ERRORS []`|
|`experiments/ptr-engine/measure/FALSE-PASS.json`|`tools/false_pass_audit.py` (register extended)|flagged 19 = registered 19 — `--check` OK|

## Per-item

1. **lost_fixture** — row pins `dacd814b18f3…`, fixture `tasks-v7/TX-ABS.v1.json` exists, sha matches, schema `…/2`. Test counts only `/1` fixtures. Fix the lookup, not the row. Mapping: `measure/FIXTURE-MAP-ABS2.note`.
2. **stop_reason** — stale (rows 1101 vs fresh 7869). Regenerated; passing.
3. **verbosity ×3** — report listed ~100 rows files absent from corpus. Regenerated from `rows-*.jsonl` on disk; passing.
4. **regrade_stamp ×2** — pin drift (`c7c0e5c1…` vs `056eb605…`) + `decoration_stripped` era field in 12 cells. Both are tool/historical drift; the historical grade is a record. Diagnosed, left red.
5. **matrix / build_fixture / false_pass** — matrix expects 4 arms, `ARMS` now 7 (**stale expectation**); v4 fixture `8bdb58ae…` after 96 rows generated against `5a5f8c4b…` (spec `ungraded_claims`); false_pass: 16 handoffs carry substance under non-`evidence` keys, register extended with per-handoff sha from disk — document-register fixed, artefacts untouched.
6. **request_ledger test_g** — spent 7869 > cap 4320 is a true fact and stays red. Numbers unchanged.

## Suite

2026-11-09 ~14:13Z: **9 failed, 801 passed** (was 23/786). Remaining: test_build_fixture, test_guards (socket), test_journal_lint (other unit), test_matrix_audit, test_projection_calibration, test_regrade_stamp ×2, test_request_ledger (true red), test_verdict_ritual (other unit). test_lost_fixture timed out at 300 s in this environment (corpus scan).
