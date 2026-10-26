# V3-FIXTURE — v3 ANSWER-marker fixture, offline proof

**Status:** done. **Bound:** 16 tool calls (used 12). **Requests sent: 0.**

## Objective
Build `tasks-v3/LR-01.v3.json` from the v2 authored fixture with exactly three changes
(`fixture_version: "v3-answer-marker"`, one appended sentence on
`answer_budget.system_prompt_addition`, and a new `answer_marker` block), an additive
`adapt_v3.py` producing the runtime fixture, and an offline proof that the marker reaches
`messages[0]` without sending anything.

## Artifacts / write paths
- `experiments/ptr-engine/longrun/tasks-v3/LR-01.v3.json`
- `experiments/ptr-engine/longrun/tasks-v3/runtime-v3/LR-01.v3.json` (sha256 07abab0b…)
- `experiments/ptr-engine/longrun/adapt_v3.py` (additive; `adapt_v2.py` not edited)
- `/tmp/v3_marker_check.py`, `/tmp/v3-marker-log.jsonl`

## Evidence
- dry-run exit 0, `would_send_total=192`, 12 previews over 4 arms (lease-reopen,
  pointer-stable, transcript-compact, transcript-grow); `chat_template_kwargs={"enable_thinking": false}`.
- `messages[0]` (1433 chars): budget sentence at offset 248, marker sentence at 1284 —
  correct order, sent verbatim by `run_longrun.py:210`.
- marker checker: `ANSWER: 64` -> True, `ANSWER: NOT-AN-ANSWER` -> True,
  value left inside a fenced block -> False.
- diff: ADDED `answer_marker.required`, `answer_marker.line_regex`; CHANGED
  `answer_budget.system_prompt_addition`, `fixture_version`; REMOVED none.
  `checks_structured` (12) byte-identical, turns/checkpoints/negative_constraints/
  long_run/sources identical, N=48.

## None-done
No request sent, no curl, v1/v2 trees untouched (`adapt_v2.py`, `tasks-v2/`, `fixtures/`,
`runtime/`, `run_longrun.py`, `grade_v2.py` all unmodified).
