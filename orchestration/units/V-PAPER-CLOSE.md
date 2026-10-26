# V-PAPER-CLOSE — independent re-check of the context-cache experiment close (§10)

Role: INDEPENDENT VERIFIER. Author of the close = PAPER-FINAL. Per orchestration/VERDICTS.md the
author's row is a report, not a verdict; this unit appends the missing verdict.

Checks (re-run, not trust prose):
1. `python papers/context-cache/verify_package.py` -> PASS, exit 0.
2. `python papers/context-cache/recompute.py all` -> COVERAGE GUARD PASS, C64 38/38, C65 48/48,
   C66 75/75, C67 85/85, C68 70/70, SYSOPT 50/50 (report actuals).
3. Release serving brief `--check` PASS.
4. `pytest tests/ -q` -> 1368 passed, 1 skipped (skip = live-model test; NO model requests).
5. Three §10 repairs carry red->green evidence on disk: (a) C63 "+-" double-sign gone from
   MANUSCRIPT.md and guards no longer require them; (b) release_serving_check.py check_divergence
   set-differences not swapped, declaration flags compared by value, declaration cannot discharge
   its own accusation; (c) tests/test_orchestration_handoffs.py baselines sha256-pinned, no gap laundried.
6. GAPS.md contains G17; state/gap-ledger.json = 3 closed / 3 narrowed / 11 open / 1 unverifiable.
7. RED->GREEN on one repair, reverted in scratch copy under /tmp only (never live file).
8. Own footprint: 0 model-endpoint requests (:8012/:8014), .occamy.lock untouched, no restarts,
   no /flush_cache.

HARD BOUND: <=30 tool calls. Write paths: this card, orchestration/handoffs/V-PAPER-CLOSE.json,
orchestration/VERDICTS.md (one verdict line). Verify only — never repair. Targets read-only.
