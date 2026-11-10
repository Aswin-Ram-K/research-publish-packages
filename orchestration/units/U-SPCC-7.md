# U-SPCC-7 — scorecard guards & ledger reconcile

## Scope
Owned: `experiments/ptr-engine/longrun/score_longrun.py`, `experiments/ptr-engine/tools/request_ledger.py`, new tests.

## Changes
- `score_longrun.py`: added `billing_block()`; scorecard now carries `billing` (prompt/cached/uncached/billed tokens, cached_fraction, coverage, attribution) and `payload_tokens`. Cached nulls excluded from cached_fraction/coverage. Duplicate non-interim answers now raise with row indices. Denominator mismatch returns exit_code. OOV counted as ungradeable, not abstention.
- `request_ledger.py`: added `reconcile()` returning {rows_on_disk, ledger_spent, delta, verdict}; warning on mismatch; CLI `--reconcile`.

## Verification
- tests pass; 42/48 reproduced; reconcile 7869/7869 agree.
