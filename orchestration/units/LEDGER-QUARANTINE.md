# LEDGER-QUARANTINE

Voided 318 synthetic stub attempts (append-only) via label-prefix predicate. Added `void` verb to ledger.py; status now subtracts voided from reserved/spent and reports `voided`/`voided_by_reason`, `--include-voided`. Driver stub mode now defaults to temp ledger unless `--allow-stub-ledger`, writes `synthetic: true` + `engine.mode: stub` with no endpoint. Analyser excludes synthetic rows. Moved 11 stub row files to `run/rows-quarantine/`. Tests green (63 passed), journal hash unchanged across suite.
