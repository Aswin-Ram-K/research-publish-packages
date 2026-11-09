# HANDOFF-PARTIAL-SUBSTANCE

**Objective.** Extend `experiments/ptr-engine/tools/handoff_lint.py` so a *partial* handoff is
judgeable: three additive codes, warnings not errors, with a forward-only baseline. Offline,
zero requests.

**Bounds.** ≤20 tool calls · 0 requests · additive only (no code renamed, deleted or renumbered).

**Codes.**
`W_PARTIAL_NO_EVIDENCE` — partial with no substance under any contracted key.
`W_PARTIAL_NO_COMMAND` — partial with substance but no command and no non-trivial countable.
`E_STATUS_WORD_CONTRADICTION` — `done`/`pass` with no substance.

**Substance keys accepted:** `evidence`, `checks`, `measurements`, `findings`, `commands`,
`command_or_count`. A bare `counts` dict is not substance. A rule keyed on `evidence` alone is a
false-positive generator: `V-FIXTURE-V8` is done+pass with no `evidence` key and is fully
substantive.

**Write paths.** `experiments/ptr-engine/tools/handoff_lint.py`,
`experiments/ptr-engine/longrun/tests/test_handoff_partial.py`,
`state/logs/handoff-partial-baseline.json`, `docs/HANDOFF-PARTIAL.md`,
`orchestration/units/HANDOFF-PARTIAL-SUBSTANCE.md`,
`orchestration/handoffs/HANDOFF-PARTIAL-SUBSTANCE.json`,
`orchestration/journals/HANDOFF-PARTIAL-SUBSTANCE.jsonl`.

**Proof.** Existing code counts unchanged; three red cases; green `V-REASON-MIX` and
`V-FIXTURE-V8`; the prompting cards appear in the new-code output before the baseline and not
after.

**Stop condition.** If a rule that keeps `V-FIXTURE-V8` clean cannot flag a prompting card, the
card's premise is stale — record the measured result, do not bend the rule.
