# UNIT V-STAMP-NEUTRAL

**Objective.** Prove the `GRADER-STAMP` change to `grade_v5.py` (`056eb605…`, version 5.1) is
additive: grading semantics did not move, the stamp is honest, and the stamp did not become a
second source of truth.

**Bound.** ≤22 tool calls, **0 network requests** (offline). Used 21 tool calls, 0 requests.

**Write paths (exactly).**
`experiments/ptr-engine/measure/V-STAMP-NEUTRAL.json`, `docs/V-STAMP-NEUTRAL.md`,
`orchestration/units/V-STAMP-NEUTRAL.md`, `orchestration/handoffs/V-STAMP-NEUTRAL.json`,
`orchestration/journals/V-STAMP-NEUTRAL.jsonl`.

**Method.** (1) reverse-diff a `/tmp` grader copy with only the stamp removed; regrade
17 stored pre-stamp grade documents with the current grader and diff field by field;
(2) mutate `/tmp` copies of the rows and of the grader and show each digest follows its own bytes;
force a digest failure and show exit 3 with no output file; (3) probe `tools/grader_identity.py`
on stamped, pre-stamp, partial and regrade-written documents, and run `regrade.py --check` against
both stamped and pre-stamp documents.

**Result.** Stamp additive (3 keys only). 45 differing paths outside the
allowed set — all `arms.<arm>.decidable_source`, from an earlier additive repair, no numeric change.
Findings F1 (stale `DEFAULT_GRADER_SHA` in `tools/regrade.py:44`, exit 3 by default) and F2
(regrade writer is 1/3 stamped, re-implements the sha). No masking of a genuine grader change found.

**Verdict.** `partial` — additivity proven, surrounding identity path needs F1/F2 fixed.

**Kill condition.** The pre-stamp grader binary is not on disk, so the pre-stamp *source* cannot be
byte-run; the additivity claim is instead proven by (a) the reverse diff and (b) the field-by-field
grid regrade against documents the pre-stamp grader wrote.
