# UNIT CELLTX01

**Purpose.** Run both arms (masking-no-fetch C, bounded-context-fetch D) for all 48 turns, one rep, on TX-01; grade both via score_longrun; report conditional-on-compliance and control integrity.
**Bound.** <=130 live requests, <=90 tool calls. Actual: 111 requests, 39 marker fetches (15 tool-call turns).

## Accounting
- Fixture: experiments/ptr-engine/longrun/tasks-v7/TX-01.v1.json sha256 44a1b4356536a0a55757ed2a4c90f5ef7f9d0541836007dc195a50ab3db2ec21
- Rows file: experiments/ptr-engine/measure/rows-longrun-CELLTX01.jsonl (111 rows)
- task_id all TX-01; single fixture sha256; cap 2867 -> 2978 (+111).
- D scored 12/12 verified_success=True; C scored 0/12 (masking arm, expected).

## Per-arm 12-row tables

### masking-no-fetch
| checkpoint | expected | answer_raw | kind | verdict | reason | fetched_all_markers |
|---|---|---|---|---|---|---|
| 20 | 3 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'NUM' at turn 20 | False |
| 22 | 30 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'NUM' at turn 22 | False |
| 24 | MAX_BATCH_SIZE | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'TEXT' at turn 24 | False |
| 26 | 5 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'NUM' at turn 26 | False |
| 28 | PtrMissingRefError | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'TEXT' at turn 28 | False |
| 30 | E001 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'TEXT' at turn 30 | False |
| 32 | E002 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'TEXT' at turn 32 | False |
| 34 | E003 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'TEXT' at turn 34 | False |
| 36 | 128 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'NUM' at turn 36 | False |
| 38 | 64 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'NUM' at turn 38 | False |
| 40 | sha256 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'TEXT' at turn 40 | False |
| 42 | 7 | ANSWER: NONE | NONE | fail | answer kind 'NONE' != expected 'NUM' at turn 42 | False |

### bounded-context-fetch
| checkpoint | expected | answer_raw | kind | verdict | reason | fetched_all_markers |
|---|---|---|---|---|---|---|
| 20 | 3 | ANSWER: NUM 3 | NUM | pass | turn 20 answer '3' vs expected '3' | True |
| 22 | 30 | ANSWER: NUM 30 | NUM | pass | turn 22 answer '30' vs expected '30' | True |
| 24 | MAX_BATCH_SIZE | ANSWER: TEXT MAX_BATCH_SIZE | TEXT | pass | turn 24 answer 'MAX_BATCH_SIZE' vs expected 'MAX_BATCH_SIZE' | True |
| 26 | 5 | ANSWER: NUM 5 | NUM | pass | turn 26 answer '5' vs expected '5' | True |
| 28 | PtrMissingRefError | ANSWER: TEXT PtrMissingRefError | TEXT | pass | turn 28 answer 'PtrMissingRefError' vs expected 'PtrMissingR | True |
| 30 | E001 | ANSWER: TEXT E001 | TEXT | pass | turn 30 answer 'E001' vs expected 'E001' | True |
| 32 | E002 | ANSWER: TEXT E002 | TEXT | pass | turn 32 answer 'E002' vs expected 'E002' | True |
| 34 | E003 | ANSWER: TEXT E003 | TEXT | pass | turn 34 answer 'E003' vs expected 'E003' | True |
| 36 | 128 | ANSWER: NUM 128 | NUM | pass | turn 36 answer '128' vs expected '128' | True |
| 38 | 64 | ANSWER: NUM 64 | NUM | pass | turn 38 answer '64' vs expected '64' | True |
| 40 | sha256 | ANSWER: TEXT sha256 | TEXT | pass | turn 40 answer 'sha256' vs expected 'sha256' | True |
| 42 | 7 | ANSWER: NUM 7 | NUM | pass | turn 42 answer '7' vs expected '7' | True |

## Conditional on compliance
- D checkpoint turns with all markers fetched: 12, passed 12.
- D checkpoint turns with skipped marker / wrapped call: 0, passed 0.

## Control integrity (masking-no-fetch)
tools_declared=False on all 48 rows; tools_mode=off; fetch_rows=None; no tool_calls; protocol_violations=0; all 48 answers ANSWER: NONE. No read_file, pointer lookup, or copy from an earlier answer; grader 0/12.

## Answer-kind discipline
- masking-no-fetch: 48 on-contract (NONE), 0 OOV, 0 protocol violation.
- bounded-context-fetch: 47 on-contract answer rows (33 NONE, 8 TEXT, 6 NUM) + 1 no-answer turn (T27 tool_calls), 15 turn-initial no-answer rows, 0 OOV, 0 protocol violation.

## Claim
On TX-01, the bounded-context-fetch arm recovered all 12 checkpoint facts (12/12) by fetching all three markers on every checkpoint turn, while the masking-no-fetch arm answered NONE at all 12 checkpoints (0/12) because masked bodies are not recoverable without a fetch. This is one task, one replicate, so it gives no interval, significance, or cross-stack/cross-task generalisation. The contrast is between two policies on a fixture whose facts are transient by construction.

## Blocker / next
Blocker: none.
Next: Run a second replicate or a second task to test stability; probe turns where D fetches fewer than 3 markers (e.g. turn 27) for discipline failures.
