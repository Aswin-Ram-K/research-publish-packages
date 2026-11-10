# V5 verdict — gate re-audit (2026-11-07)

Re-audit of VALIDATION-ROADMAP gates against code as it stands. Verifier: V5Verify.
No model requests, no service changes, no target writes, no fixture/grader changes made by this audit.

## Per-gate table

| Gate | Previous verdict (handoff/roadmap) | Claimed by G-unit | My verdict | Evidence (file:line) |
|---:|---|---|---|---|
| 0.1 | PASS (G2 self-test) | G2-SCORER done; 4 red->green outcomes | PASS (self-test) / PARTIAL (abstained_correctly guard) | `longrun/score_longrun.py:1142` self_test prints "self_test: PASS"; asserts 7 target checks pass, wrong_value verified_success False, fab False, abs True. Forcing `abstained_correctly=True` unconditionally (`/tmp/scratchpad/score_broken.py`) leaves self-test PASS (not caught) — gap: abstained_correctly tampering not guarded. Forcing `verified=True` is caught (`AssertionError` at self_test:1185). |
| 0.3 | PASS (G1 checker ALL_REACHABLE) | G1-FIXTURE done | PASS | `longrun/check_wall_reachability.py` output: ALL_REACHABLE=true, 6 files gen-7, turns_to_wall < N all arms. Independent arithmetic LR-01 transcript-grow: P1=5134, slope=64.979, target_turn=floor(48/2)=24 -> wall=5134+round(64.979*23)=6629; checker turns_to_wall=25 (<48). `.v8.json` mtime 2026-10-26 12:02 (predates session). |
| 0.4 | PASS (G3) | G3-RUNNER done | PASS | `longrun/run_longrun.py:1917` UNSOURCEABLE + `:1919` names probe; `probe_fingerprints` (:1937) emits "probe" per field; no `"unknown"` value from probe (only harness_sha256 provenance path, not fingerprints). |
| 0.5 | PASS (G3) | G3-RUNNER done | PASS | `longrun/run_longrun.py:1309-1317` `_activation_counts` computed from rows; `analyze_stats.py:1642` `assert_row_count` pre-analysis assertion; verified GOOD PASS on 48 unique rows, BROKEN caught (duplicate -> RowCountAssertionError). |
| 0.6 | PASS (G3) | G3-RUNNER done | PASS | `ACTIVATION_PREDICATES` 5 entries A-E at run_longrun.py:1298; `activation_predicate` computed from rows; 5 predicates exist. |
| 0.7 | PASS (G4) | G4-CAP done | PASS | `longrun/cell.py:141` PROJECT_QUOTA=12094; `measure/REQUEST-LEDGER.json` budget.cap=12094, headroom=9503, spent=2591; 12094-2591=9503 recomputed. `CAP-AUTHORISATION-2026-11-07.json`: headroom=9503, shortfall_pending_authorisation=2591.2; reservation consumption="UNKNOWN" (not unspent); only "unspent" mention is assumption_if_unspent key, explicitly "stated as an assumption, not a conclusion". |
| 0.9 | PASS (G2) | G2-SCORER done | PASS (red->green on verified_success) / PARTIAL (abstained_correctly not guarded) | self-test fabricated_over_absent verified_success=False; correct_abstention verified_success=True, abstained_correctly=True; wrong_value fails cp.t12/acc.cp1/acc.1. Forcing abstained_correctly=True not caught (see 0.1). |
| 0.10 | PASS (G5) | G5-DETERMINISM done | PASS (code) / PARTIAL (pytest 7.4.0 vs py3.14) | `ptr_engine/outcomes.py`, `fetch_batch.py`, `resume.py`, `tests/test_batch_resume_vocab.py` exist; manual assertions reported. pytest run of longrun/tests: 66 failed, 565 passed (see counts below); test_verdict_semantics collection error (exit-code 14 unclassified). |

## Integration pass (only suite run)

- ptr-engine/tests: 41 failed, 369 passed, 1 xfailed.
- ptr-engine/longrun/tests (excl. test_verdict_semantics): 66 failed, 565 passed, 31 subtests passed.
- test_verdict_semantics: collection ERROR (exit-code partition drift: unclassified exit code 14).
- root tests/: 44 failed, 1505 passed, 1 skipped, 1 warning, 10 errors.
Key failures: repeat-identity guard (rep not in run_id) in tool_channel tests; embedded-digest pin mismatch after gen-7 edits; ledger raw 2591 vs 1176 expected; quality_carry_forward drift (STATUS.md line 392 vs 396); precondition10 scope refusals; test_verdict_semantics collection error.

## Collateral sweep (last 90 min, non-pycache)

All modified code files classify as (a) declared G/S handoff write paths or (b) disclosed side effects (cell.py cap wire-in, REQUEST-LEDGER/CAP-AUTH, docs/CHECKPOINT-COVERAGE.md touched with no content diff). No (c) UNEXPLAINED content modifications. __pycache__/.pytest_cache are build artefacts.

## Generation labels

v9 fixtures labelled gen-7 (6 files); v8 (LR-01 only) and v7 remain generation-neutral/untagged and were not rewritten. No gen-6 row/file rewritten to look gen-7.

## Verdict

PASS with two PARTIALs (0.1/0.9 abstained_correctly guard not exercised by self-test; 0.10 pytest collection error) and 151 test failures across suites (reported verbatim, not fixed).
