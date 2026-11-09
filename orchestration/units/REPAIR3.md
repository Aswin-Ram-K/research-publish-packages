# REPAIR3

## Findings closed

| # | red proof | green proof | file:line changed |
|---|-----------|-------------|-------------------|
| 9 | dry-run issued 3 HTTP GETs | socket denied: rc 0, no socket | run_longrun.py:1811-1826 |
| 2/12 | tools_enabled only read_file | fetch recognised; 47 tests pass | client.py tools_enabled |
| 8/10 | C advertised fetch/read_file | C tools="" per arm; fetch routed | run_longrun.py run_cell + _call_from_arguments |
| 1 | fetch follow-up dropped tool_calls | assistant preserves tool_calls | run_longrun.py D block |
| 14 | retrieval double-stamped | stamp only on turn row | run_longrun.py _retrieval_stamp |
| 3/11 | refused/failed follow-ups no row | initial row on every path | run_longrun.py D/generic handlers |
| 4 | OOV counted as miss | ungradeable, excluded | score_longrun.py eval_fact |
| 7 | TEXT 3 accepted for NUM | kind checked via answer_spec | score_longrun.py eval_fact |
| 15 | fallback returned other task body | PtrStoreMissError on explicit miss | pointer_table.py fetch |
| 5/6 | T24 revealed MAX_BATCH_SIZE; T28 mismatch | all 12 checkpoint turns rewritten | tasks-v7/TX-01.v1.json |

## 12-checkpoint absence
All 12 checkpoint turns: expected value absent from C-arm prompt (word-boundary search).

## Fatal findings
- Finding 1: fetch follow-up dropped tool_calls (fixed).
- Finding 2: tools_enabled only read_file (fixed).

## Open
None.