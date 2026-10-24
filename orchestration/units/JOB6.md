# Unit card — JOB6 (Discovery via repaired search)

**Purpose:** Be the first unit to *discover* job targets by query (local SearXNG repaired) instead of
from a hand-written list, and record verified openings whose subject matter is the unit's subdomain:
agent runtimes, durable/stateful agent execution, event-sourced/replayable agent state, agent evals
infrastructure, LLM decision/routing systems, agent memory — global, employer type unrestricted but
with `cap_exempt_likely` recorded.

## Hard bounds
- Wall clock: **30 minutes non-stop**, or **90 tool calls**, whichever first.
- Verification rule: no record without a direct fetch of the posting page (or its platform's official
  API when the HTML page is bot-blocked — then the blocked status is recorded as a coverage gap).
- Never invent a job/URL/company; beware look-alike slugs (employer identity read from posting body).

## Write paths (declared, checked against concurrently running units)
- `jobs/agent-runtime-global/**` (JOBS.jsonl, FINDINGS.md, raw/*.html)
- `orchestration/units/JOB6.md`
- `orchestration/handoffs/JOB6.json`

## Stop condition
30 minutes elapsed OR 90 tool calls OR deliverables written after the final burst — whichever first.

## Status at end: **done**
- 49 openings recorded, 27 employers, 19 search queries, board enumeration across Ashby/Greenhouse/Lever.
- 3 cap-exempt (METR ×2, Apollo Research ×1); 46 cap-subject; 0 unclear.
- 2 unreachable human-facing URLs (Netskope 403 ×2) with API fallback documented; 3 discovery gaps named.
