# CAMPAIGN-TASKS

## Deliverables
- `experiments/context-cache/cells/CONTEXT-SERVING-CAMPAIGN/tasks/gen_instances.py` — deterministic generator, 8 instances (D1-D4 discovery, H1-H4 heldout), 12 turns each, cs.task/1 schema.
- `tasks/instances/D1.json..H4.json` — frozen instances.
- `tasks/grade.py` — cs.grade/1 grader: key=value parse, exact match, no extra keys, per-check booleans + ok; ok=null on truncated/unparseable with finish_reason=length; silent/length-exhausted classification.
- `tasks/contain/runner.py` — bwrap containment runner; refuses if unavailable/unprivileged.
- `tests/test_campaign_tasks.py` — 13 tests passing.

## bwrap
- `bwrap --version`: bubblewrap 0.11.1
- Containment engaged: YES (verified network denied, outside write denied, inside write allowed).

## Test result
- `PYTHONNOUSERSITE=1 python3 -m pytest tests/test_campaign_tasks.py -q` → `13 passed in 0.09s`

## Red proof
- Broken grader (/tmp copy) with forced mismatched key → reference artifact FAILS (ok=False).
- Restored grader → reference artifact PASSES (ok=True).

## Reference output
- D1 turn 1 output bytes `b'total=-1'` exactly match contracted `key=value`.

## Assumptions
- Tasks are text-answer (key=value), not executed artifacts; bwrap runner provided for any executed task and refuses if unavailable.
- Mean/median formatted as specified; grader uses exact string value match.
