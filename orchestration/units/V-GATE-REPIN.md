# V-GATE-REPIN (unit card, persisted)

## Objective
Decide the gate precondition on the tree as it stands, with the right oracle. Offline, zero requests.
Fix the spawn oracle (instrument `subprocess.Popen`/`os.posix_spawn`, not `cell._run`), re-run the four
original breaks twice each, re-run the six F-cases, and state whether the 800-request grid may launch.

## Hard bound
<=22 tool calls, 0 requests. No edits to `cell.py`, `run_longrun.py`, `exit_codes.py` or any grader.

## Write paths
`experiments/ptr-engine/measure/V-GATE-REPIN.json`, `docs/V-GATE-REPIN.md`,
`orchestration/units/V-GATE-REPIN.md`, `orchestration/handoffs/V-GATE-REPIN.json`,
`orchestration/journals/V-GATE-REPIN.jsonl`.

## Result
`partial` — see `docs/V-GATE-REPIN.md`. All four breaks refuse with the right codes (8,8,12,12) and all
six F-cases match (8,8,8,4,4,8) with zero live runner spawns; the repo-root unittest is green. The one
unmet PASS item: the raw primitive count is 1, not 0, per invocation — a pre-gate
`run_longrun.py --dry-run` harness self-check at stage 2/7.

## Instruments
`/tmp/vgate_repin/probe.py` (tripwired Popen oracle; not persisted — /tmp is per-call on this host).
