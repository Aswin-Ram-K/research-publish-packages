# UNIT JOURNAL-LINT — make the journal obligation checkable

**Purpose.** Five units were in flight with no `orchestration/journals/<UNIT>.jsonl` while
their work was visibly progressing on disk. The journal is the only artefact that survives
a session killed at the handoff — the failure mode that already lost `17a76d24`,
`4e559586`, `da4ba836` — so the artefact built to survive a kill was the one nobody wrote.
This unit turns "journal first" from prose into a check, forward-only so the historical
corpus is not failed retroactively.

**Bound.** ≤26 tool calls, 0 inference requests. Offline.

**Write paths (declared).**
- `experiments/ptr-engine/tools/handoff_lint.py` — the named module behind `HANDOFF-LINT`
  (`orchestration/handoffs/HANDOFF-LINT.json`); the card's WRITE PATHS block omitted it but
  step 2 orders "extend the existing linter", and a second linter is exactly what it
  forbids. Additive only: new functions + new codes, no existing code path changed.
- `experiments/ptr-engine/longrun/tests/test_journal_lint.py`
- `state/logs/journal-lint-baseline.json` (frozen, forward-only)
- `orchestration/units/JOURNAL-LINT.md`, `orchestration/handoffs/JOURNAL-LINT.json`,
  `orchestration/journals/JOURNAL-LINT.jsonl`

**Census (first, before any judgement; taken at 2026-10-26T12:06Z over
`orchestration/handoffs/*.json`).** 1023 handoffs carrying a unit name · 70 with a journal ·
953 missing · 0 empty · 0 unparseable · 52 whose last record carries no step number · 8 with
no timestamp · 18 stale (journal older than its handoff). The five units named in the card:
`GATE-OPERAND-VALIDATION` 4 lines step+ts · `P95-POWER-DIGEST-FIX` 6 lines step+ts ·
`LATENCY-ERA-CENSUS` 9 lines ts but **no step** · `TVS-CENSORED` 5 lines ts but **no step**
(a journal appeared during the unit's run) · `FIXTURE-TREATMENTS` absent when measured,
present with 4 ts-only lines by the time the census was re-run. Live corpus moves under a
census; the frozen baseline is the stable reference.

**Result.** `E_JOURNAL_MISSING` + `W_JOURNAL_STALE` added to the existing linter;
1009 historical misses frozen in `state/logs/journal-lint-baseline.json`; existing code
counts unchanged (E_MISSING_KEY 35, E_ARTIFACT_ABSENT 75, E_DONE_NO_EVIDENCE 4,
E_DONE_NO_ARTIFACTS 3, E_STUB 16, W_NO_COMMANDS 187, W_VERSION_STALE 21 — identical before
and after); 14/14 new tests pass and the three red→green cases fail against a pre-rule copy.

**Honest limit (also in the rule's docstring).** A linter that runs inside a unit's own test
suite cannot police a unit that never runs it — the unit that writes no journal is exactly
the unit that skips the suite. The alternative is a board-side pre-handoff hook that refuses
to settle a card whose journal is absent; that needs operator approval this workspace cannot
grant.
