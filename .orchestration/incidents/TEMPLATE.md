# INCIDENT — <code>

- at: <ISO-8601 UTC>
- kind: snag | bug | perf | refusal
- code: <machine-readable: stalled | command-refused | judge-unavailable | …>
- severity: low | medium | high
- repo: <absolute path>
- task: <card id, or ->
- execution: <run id, or ->
- session: <session id, or ->

## What happened
One or two sentences. What did the orchestration do that it should not have done,
or fail to do that it should have?

## Evidence
Exact commands, file paths, error strings, numbers. Never a claim without one.

## Suspected cause
The mechanism, if known; "unknown" is an acceptable answer and better than a guess.

## Suggested fix
The change that would prevent a repeat, and how it would be verified.
