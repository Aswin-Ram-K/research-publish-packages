# COMBINED-CONTEXT-SERVING preregistration

## Selection rule (frozen before any data)
Discovery tasks: T1.discovery, T2.discovery.
A candidate arm qualifies only if every task's grader returns `verified_success: true`
for it and no negative constraint fires.
Among qualifying arms, choose the lowest total `uncached + completion` tokens,
including retries and grading-triggered recomputation.
Then run the chosen arm and arm A on held-out tasks T3.heldout, T4.heldout
and apply the same rule.

## Live run commands
```bash
cd experiments/context-cache/cells/COMBINED-CONTEXT-SERVING
# watcher (start before driver)
python3 tools/watcher.py --rows rows/ccs.jsonl --log run/driver.log \
  --pid $DRIVER_PID --stall-minutes 10 \
  --deadline-utc 2026-11-05T23:59:59Z --out run/watcher.jsonl \
  --interval-seconds 120 &
# driver
python3 run/driver.py
```

## Watcher invocation
`python3 tools/watcher.py --rows rows/ccs.jsonl --log run/driver.log --pid $DRIVER_PID --stall-minutes 10 --deadline-utc 2026-11-05T23:59:59Z --out run/watcher.jsonl --interval-seconds 120`

## Cost note
A null `cached_tokens` on any call makes the precise combined cost unquotable;
report sensitivity bounds only.
