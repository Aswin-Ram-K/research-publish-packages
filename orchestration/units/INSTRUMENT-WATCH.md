# INSTRUMENT-WATCH

## Summary
Built campaign watcher and analyser plus offline fail-closed proof suite.

## Artifacts
- /home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/tools/watcher.py
- /home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/run/analyse.py
- /home/zer0null/.omp/wt/wt-20261104-060031-bd8df5c/experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/tests/test_instrument_failclosed.py

## Verification
- pytest: 8 passed (canonical runner)
- scenarios 1-8 proven by executing real components where available; scenario 3 watcher process killed + staleness simulated via pid file mtime; scenario 4 real ledger untouched verified by byte hash.

## Notes
- Watcher derives rows/intents/ledger paths from envelope; defaults provided.
- Analyser supports --paired-by and refuses pooling via stated independent unit.
