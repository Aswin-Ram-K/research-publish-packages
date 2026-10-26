# V3-PILOT - does the ANSWER: line make the model state the numbers?

Fixture `experiments/ptr-engine/longrun/tasks-v3/runtime-v3/LR-01.v3.json`
(sha256 07abab0b...3e0b, verified on disk). Arms: transcript-grow, pointer-stable.
48 turns each, `--thinking off`, max_tokens 4096, 1 rep. Endpoint 192.168.2.168:8012.

## Result: MARKER-FAILS

| arm | marker % | cp1 (64) | cp2 (31) | acc cp1/2/3 | over_budget |
|---|---|---|---|---|---|
| transcript-grow | 100.0 | NOT-AN-ANSWER | NOT-AN-ANSWER | fail/fail/fail | 0.0% |
| pointer-stable | 64.58 | NOT-AN-ANSWER | ANSWER: 7 (wrong) | fail/fail/fail | 4.17% |

grade_v2 0/10 both arms (old == new). score_longrun exit 1 (normal failed-check status).

## Why: the fixture is unanswerable by construction
The injected bodies are truncated excerpts containing neither expected number.
resolve.py body = 1680 chars, stops mid-`resolve()`, never reaches L39. errors.py body
= 331 chars, 3 class stubs, cut mid-class at `class PtrBodyMismatchError(PtrError):`.
The model states this itself at turn 46: "I cannot answer from the pinned body because
`resolve.py` is truncated at the `PtrUnknownIdError(`".

So NOT-AN-ANSWER is honest. The marker line works as a formatting device and cannot
supply a missing fact.

## Bound
96 requests (48 + 48), both arms serialised, one background job each. No truncation
in arm 1; 1 in arm 2 (T19, finish_reason=length at 4096).
