# CAMPAIGN-TASKS-V2

Revised task/quality instrument under $CAMPAIGN/tasks/. V1 preserved at
`tasks/superseded-v1/`.

## Families
- Discovery (2 families x 2): running_numeric_aggregate (D1 sum, D2 range+count);
  file_state_recall (D3 string keys, D4 integer keys; asks previous value).
- Held-out (2 families x 2): multi_step_edit_application (H1 token sequence,
  H2 text buffer); constraint_precedence_resolution (H3 base-wins rule at turn 2,
  H4 priority-ranked early constraints).

## Dependency / exact-body table
| ID | family | turns | req counts per turn | dep<=6 | exact | ref |
|----|--------|-------|---------------------|--------|-------|-----|
| D1 | running_numeric_aggregate | 12 | 1..12 | 11 | 0 | PASS |
| D2 | running_numeric_aggregate | 12 | 1..12 | 11 | 0 | PASS |
| D3 | file_state_recall | 12 | 1 x12 | 6 | 11 | PASS |
| D4 | file_state_recall | 12 | 1 x12 | 6 | 11 | PASS |
| H1 | multi_step_edit_application | 12 | 1..12 | 11 | 7 | PASS |
| H2 | multi_step_edit_application | 12 | 1..12 | 11 | 11 | PASS |
| H3 | constraint_precedence_resolution | 12 | 1,1,1,1,1,1,2,2,2,2,2,2 | 6 | 0 | PASS |
| H4 | constraint_precedence_resolution | 12 | 1,1,1,1,1,1,4,3,3,4,3,3 | 6 | 0 | PASS |

`dep<=6` counts turns whose answer needs a source turn strictly earlier than
the current turn and <=6 (the `mask_after=6` region). Every instance >=6.

## Tests
`PYTHONNOUSERSITE=1 python3 -m pytest tests/test_campaign_tasks.py -q` -> 18 passed

New tests: two distinct disjoint families per split; independent
requires_turns replay (aggregate/state/H3/H4); dependency count >=6; exact-body
turn present with non-numeric value; exact-body answer absent from the current
event JSON.

## Mutant matrix (re-proved)
reference D1-D4/H1-H4 PASS; wrong answer FAIL; missing key FAIL (count);
seed-perturbed hardcode 12/12 FAIL; unresolved reference FAIL; outside write
denied; network denied.

## Red proof
Set `MASK_AFTER=0` in the test -> `test_dependency_count_at_least_six` fails
(`('D1', [])`, 0 >= 6). Restored to 6 -> 18 passed.

## Containment
`contain/runner.py --probe` -> bwrap 0.11.1 available; tests show network
denied, outside write denied, inside write allowed.
