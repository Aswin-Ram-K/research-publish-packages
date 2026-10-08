# V2U — recovery verifier for U2.3 (schema v4); supersedes V2T

**Bound:** ≤34 tool calls, 1 Occamy probe, 0 LLM calls, no network. Used **25**.
**Write paths:** orchestration/VERDICTS.md, orchestration/units/V2U.md, orchestration/handoffs/V2U.json,
state/logs/V2U*, state/verify/V2U/**. Temporary reverts only in src/resextract/store.py, last, sha-guarded.
**Never:** tests/**, assess/**, docket/**, dashboard/**, llm/**, conftest.py, /home/zer0null/Duval, .worktrees/.

**Step 0:** probe DOWN (000). Handoff opened as `partial` before any other work, rewritten after each step.
Predecessor artifacts inventoried before assuming anything.

**Findings:** see orchestration/handoffs/V2U.json (schema-conformant) and the V2U section of
orchestration/VERDICTS.md. Overall **PARTIAL**: all functional claims re-derived PASS (both red→green guards
reproduced, live 3→4 rows_lost 0 + idempotent, real store untouched, v2→v4 genuine), but two written disclosures
are false, `verdicts.model` is unwritten/unread dead weight, and the "one shared predicate" claim holds only
inside store.py.
