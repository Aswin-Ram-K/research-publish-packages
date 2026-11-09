# V6 verdict — gen-7 readiness final gate

Offline audit, 0 model requests, 0 service changes. Evidence is file:line in the real checkout at `/home/zer0null/research extractor` (branch `research/next-candidates-2026-10-24`, HEAD `f17663d`).

## 1. Suite counts now

| suite | command | result |
|---|---|---|
| ptr-engine | `pytest experiments/ptr-engine/tests/` | **40 failed, 370 passed, 1 xfailed** |
| longrun | `pytest experiments/ptr-engine/longrun/tests/` (excl. `test_verdict_semantics` collection error) | **67 failed, 573 passed, 31 subtests** + 1 collection error (`test_verdict_semantics.py`: exit-code partition drift, code 14 unclassified) |
| root | `pytest tests/` | **27 failed, 1517 passed, 1 skipped, 10 errors** |

Triage baseline was `ptr-engine 41F/369P`, `longrun 51F/565P +1E`, `root 44F/1505P/10E`. Current counts are better on passes but still red; residual failures fall into three classes:
- **wave-caused** (repeat-identity guard still in `make_row` at `run_longrun.py:2074`; pin generation 6→7 drift in `embedded_digests_match_pin`, `launcher_pin_and_cells`, `pin_propagation`; ledger re-read deltas in `ledger_reconcile`/`ledger_delta`): ~15 ptr-engine + ~? longrun.
- **not wave-caused / environmental**: graphify venv path typo `reserach extarctor` (`test_doctor`, `test_kg_graphify*`, `test_mine_candidates`, `test_cli` console bind), stale `report2.json` (`test_r2_opt_sim2`), harness-map citation drift (`test_harness_map_check`), ledger delta format, orchestration handoff schema gaps (`A2/A3/A4-FIX`, `G4-CAP`, `T2-TRIAGE`), package build path.
- **out of scope**: `test_verdict_semantics` collection error (pre-existing partition gap, not caused by G5 modules).

## 2. `launch_contract_diff` residual (F2's 4)

Classification: **mixed (a)+(b), not incidental.**
- `(a) stale historical digest references`: `harness_pin_digest` carries 10 occurrences of the superseded digest `efefd885…` alongside the live `d20f9cd3…` (`tests/test_launch_contract_diff.py:...` duplicate-occurrence failure; `measure/LAUNCH-CONTRACT-DIFF.json` disagreements list). These are legitimately orphaned by the gen-7 bump and the `_mutate_tolerant`/`_repin` fixture cannot fully reconcile them.
- `(b) genuine contract breaks`: `ledger_spent` (2591 vs 1128), `ledger_remaining` (9503 vs 3192), `ledger_cap` (12094 vs 4320), `price_total`/`price_remaining_after` (1056 vs 1016, missing canary+warm-ups), `floor_n60` (doc drift at `docs/GATE-CHAIN.md:292`). These are real disagreements between `REQUEST-LEDGER.json`, `GRID-PARAMS.json`, `cell.py:141` and docs.

It **does block** a clean run declaration: `check_exit=1` (`launch_contract_diff.py` disagrees on 7 numbers), so the launcher/runbook are not single-valued. It does not necessarily abort `run_cell` (pin digest is already the new one), but it blocks an adjudicable contract.

## 3. Gate 0.1 resolution

`verified_success` is the composite: `all(required checks pass)` (see `score_longrun.py:1108-1114`, `passed`/`failed_required`). The positive control `pos-full` (`score_longrun.py:1197-1216`) passes its 7 formerly-failing target checks (`cp.t12`, `cp.t24`, `cp.t46`, `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1`) — assertion at `:1204-1206` holds — but `verified_success=False` because `acc.2`, `acc.3`, `acc.4` also fail (self-test output: `failed_required: ["acc.2","acc.3","acc.4"]`).

**The two contradict:** a row whose 7 target checks pass is labelled `verified_success=False`. That is a gate-0.1 contradiction. Mark gate 0.1 **PARTIAL/FAIL**. F4's tamper control (fabricated-over-absent raises) works, but the positive control is not actually positive.

## 4. Gate re-audit 0.1–0.11 (final)

| gate | verdict | evidence (file:line) |
|---|---|---|
| 0.1 positive control can pass | **FAIL/PARTIAL** | `score_longrun.py:1197-1216` (target checks pass, composite false); `:1108-1114` |
| 0.2 ≥12 gradeable checkpoints | **PASS** | `grade_v5.py:661-734`; `derive_truth` returns 12 on `LR-01.v8.json` |
| 0.3 fixture wall from measured growth | **PASS** | `tasks-v6/LR-01.v9.json` wall 6629; `check_wall_reachability.py` ALL_REACHABLE=true; 6 v9 files present |
| 0.4 four fingerprints frozen | **PARTIAL** | `run_longrun.py:1938-2013`: model id/digest if exposed, renderer digest local; engine image/argv unexposed |
| 0.5 replicate identity | **PARTIAL** | `run_longrun.py:3107-3111` run_id includes rep; `analyze_stats.py:1642` guard exists but not auto-wired into run path |
| 0.6 activation gating | **PARTIAL** | `tools/run_a_star.py:603-693`: 4 arms gated; `masked_rows`/`fetch_rows`/`oracle_injections`/`retrieval_outcomes` absent from code |
| 0.7 budget preflight | **PARTIAL/UNKNOWN** | `measure/RESERVATIONS.json` (consumption UNKNOWN); `CAP-AUTHORISATION-2026-11-07.json` |
| 0.8 independent verifier | **PASS** | `score_longrun.py:58-59,350,805-849` (tamper exit 2) |
| 0.9 scorer retrieval miss + abstention | **PASS** | `score_longrun.py:59-60,1079-1102,1118-1119`; self-test fabricated/abstention controls |
| 0.10 prototype offline-deterministic | **PARTIAL** | `ptr_engine/quantise.py` alignment pad; `tests/test_determinism.py:46`; fetch batching/retrieval vocab missing |
| 0.11 law package re-derived | **PASS** | `experiments/miss-law/rows.jsonl` recomputed residuals |

Red→green evidence: 0.1 target checks (`score_longrun.py:1204-1206`), 0.3 (`check_wall_reachability.py` ALL_REACHABLE), 0.4 fingerprint block (`run_longrun.py:1583-1608`), 0.5 guard test (`test_row_count_guard_gen7.py` 2 passed), 0.6 predicates (`run_a_star.py:603-625`), 0.7 cap gate (`run_longrun.py:503`), 0.9 self-test PASS, 0.10 determinism test.

## 5. Guard integrity

- `assert_repeat_identity` fires on broken gen-7 input: verified (`FIRED: row_count=3 != …=8`; manual call raised `RowCountAssertionError`).
- Legacy exemption is **by recorded generation**, not silent: `assert_repeat_identity` prints `LEGACY-NONCONFORMING` and returns True for gen-6 and earlier (`run_longrun.py:2028-2045`); `assert_row_count` does the same (`analyze_stats.py:1658-1692`).
- **Discrepancy vs F1 claim:** F1 handoff says it removed the guard from `make_row` and kept it in `run_cell`, but `make_row` still calls `assert_repeat_identity` at `run_longrun.py:2074`. So the guard is still on the make_row path; F1's claim is not borne out. Legacy exemption is correctly generation-keyed, but the removal did not happen.

## 6. Cap and authorisation

- `cell.py:141`: `PROJECT_QUOTA = 12094`.
- `REQUEST-LEDGER.json` `budget.cap = 12094`, `spent = 2591`, `remaining = 9503`; `12094 − 2591 = 9503` (recomputed, matches).
- `CAP-AUTHORISATION-2026-11-07.json` fields verified: `old_cap 4320`, `new_cap 12094`, `headroom 9503`, `programme_core 12094.2`, `shortfall_pending_authorisation 2591.2`, reservation `consumption: UNKNOWN`. Reservation `CCS-2026-11-05`, amount 1500, `rows_after_reservation: 0`.
- No file states the reservation was `unspent` or that the cap is `14686` (searched repo excluding `.venv`/baselines; only incidental `unspent` wording in docs, unrelated).
- **F3 contradiction:** F3 reported `CAP-AUTHORISATION-2026-11-07.json: MISSING (not found in workspace)`, but the file exists at `experiments/ptr-engine/measure/CAP-AUTHORISATION-2026-11-07.json` (793 B). F3 must have checked the wrong path (e.g. repo-root `measure/` or `orchestration/`) or its handoff is stale; the repo is correct, F3's claim is wrong.

## 7. Pin updates

`PIN-UPDATES.md` exists at `experiments/ptr-engine/longrun/PIN-UPDATES.md`, gen-7 labelled, carries old→new digests and reasons (generation 6→7; `harness_sha256` `efefd…`→`d20f…`; per-file digests; era_b grader sha). Fixture bytes unchanged (verified; no `.v8`/`.v9` fixture bytes modified). `HARNESS-PIN.json` generation = 7 (`test_pin_record_matches_launcher` passes).

## 8. v9 fixtures

Six `.v9.json` present (`LR-01..LR-06`) and valid. Wall reachability independently re-derived: `LR-01` transcript-grow `5134 + 64.979*(24-1) = 6628.5 → 6629` (matches `wall_tokens`); `check_wall_reachability.py` reports `ALL_REACHABLE=true` for all six. `.v8.json` mtimes are 2026-10-26, predating today (2026-11-08).

## 9. Hygiene

- Scratch dir `experiments/ptr-engine/state/scratch/v6/` does not exist (deleted).
- No file written outside this workspace by this verification; only `/tmp` scratch and the two declared outputs (`V6-verdict.md`, `V6-VERIFY.json`). Test runs may have touched `state/` artefacts under the workspace (in scope).
- Workspace is very dirty in general (1573 modified/untracked files from prior waves), but that pre-dates this verification and is not attributable to it.

## 10. Go / no-go

**NO-GO.** A funded five-arm cell cannot be run on `192.168.2.168:8012` today and produce adjudicable data. Blockers:
1. Gate 0.1 not closed: positive control passes 7 target checks but `verified_success=False` (acc.2–4 fail) — contradicts the positive-control requirement.
2. Gate 0.6 incomplete: activation predicates for arms C/D/E (`masked_rows`, `fetch_rows`, `oracle_injections`, `retrieval_outcomes`) are absent from code, so treatment activation cannot be computed.
3. Gate 0.4 partial: engine image digest and exact argv remain unobservable, so cross-run fingerprints are not fully frozen.
4. Launch contract not single-valued: 7 disagreements (harness digest, ledger, price, floor) → `check_exit=1`.
5. F1's claimed guard removal from `make_row` did not land (`run_longrun.py:2074` still asserts), leaving ~40 ptr-engine failures and repeat-identity red tests.
6. Reservation consumption is UNKNOWN (budget uncertainty, though cap is authorised at 12094).

Until (1) and (2) close, any run would yield non-adjudicable data.
