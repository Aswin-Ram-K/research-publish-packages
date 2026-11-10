# Watcher (read-only supervisor)

Must be started BEFORE the live run. Polls only files and process liveness; never HTTP; never writes rows.

Stop conditions honoured by driver: PROCESS_EXIT_NONZERO, PROCESS_VANISHED, STALL_NO_ROWS, ERROR_RATE, DEADLINE. DONE ends normally. A missing or silent watcher is itself a stop condition.

A watcher that emits no event for three consecutive intervals is a stop condition (silent watcher is a failure).
--pid must be the driver process pid, not a shell wrapper, because a wrapper's exit hides the real status.

Copy-paste:
python3 experiments/context-cache/cells/COMBINED-CONTEXT-SERVING/tools/watcher.py --rows rows/<run>.jsonl --log logs/<run>.log --pid <driver_pid> --stall-minutes 10 --deadline-utc <iso> --out watcher/events.jsonl --interval-seconds 120
