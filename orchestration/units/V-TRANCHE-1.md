# V-TRANCHE-1 — preregistered verifier for RUN-A* (freeze pass)

**Card** `9d271c32-1e8e-4592-860c-bc4aee550b42` · **execution** `566042ac-c682-4625-9722-47b8296c78ee`
**Status:** done (freeze + harness; no real rows analysed) · **Requests:** 0 · **Bound:** 28 (see handoff overage note)
**Dated (UTC):** 2026-10-26T18:22:00Z

## Purpose
Freeze the decision procedure for the 660-request tranche **before** any grid row exists, and build the
machine-checkable executor, so the post-grid re-run cannot change a rule after seeing intervals.

## Produced
| artefact | what it holds |
|---|---|
| `docs/PREREG-TRANCHE-1.md` | H1/H2/H3/TVS procedure a reader can execute by hand; §7 frozen threshold table with `file:line`; sha256 `899d1367…` |
| `experiments/ptr-engine/measure/PREREG-TRANCHE-1.json` | thresholds + sources + document sha; `--check` target |
| `experiments/ptr-engine/tools/verify_tranche1.py` | discovery → `awaiting_rows` refusal; `analyze()` recomputes H1/H2/H3/TVS with `analyze_stats` imported, not copied; `--check`; `--self-test` |
| `experiments/ptr-engine/tests/test_verify_tranche1.py` | 17 tests: 5 synthetic verdicts + red variants + awaiting_rows + drift |

## Evidence
- `pytest …/test_verify_tranche1.py -q` → **17 passed**
- `verify_tranche1.py --check` → exit 0, drift [], 20 thresholds, sha matches
- default mode with no rows → `{"verdict":"awaiting_rows","analysis":null}`, exit 0
- `verify_tranche1.py --self-test` → all 7 synthetic cases ok (5 required + H2 split + McNemar)

## Not done / not claimed
- No `rows-runA-*` existed and none was created; no statistic over real data.
- PVALUE/interval numbers in the self-test are synthetic and are not published as measurements.
