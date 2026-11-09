# UNIT V-DUPLICATE-RULE — attacker of the duplicate rule

**Purpose.** Attacks the dedupe rule that three published numbers now rest on:
`orchestration/handoffs/TVS-REGRADE.json` → `duplicate_rows`: two rows are duplicates iff,
within the same file, they share `(ts, content_sha256, prompt_tokens, completion_tokens)`;
first kept → groups 41 · excess 54 · decided 30 · `excess_defensible` 30, so spend 1,101 →
1,071 and remaining 3,219 → 3,249.

**Independence.** Did not write the rule, did not import the author's helper, did not repair
anything. Five attacks, each with a written finding; the verdict is `fail`, but for a reason
that is not "some of the 30 were retries" — none is. It is that the dropped row is the only
row standing in for a billed send the writer never recorded separately.

**Bound.** 26 tool calls; 19 used. **Write paths** (only these):
`orchestration/handoffs/V-DUPLICATE-RULE.json`,
`orchestration/units/V-DUPLICATE-RULE.md`,
`orchestration/journals/V-DUPLICATE-RULE.jsonl`,
`experiments/ptr-engine/measure/DUPLICATE-ATTACK.md`,
`experiments/ptr-engine/tools/duplicate_attack.py`.
Nothing under `measure/*.jsonl`, no grade file, no `REQUEST-LEDGER*`, `LATENCY-REPORT*`,
`TVS.json`, `docs/TVS.md` was written.

**Result in one line.** 41/54/30/30 reproduces exactly; no dropped row is a second attempt;
`content_sha256` is a response hash, not a request hash; the skip covers 3 files / 232 rows
(not 5); and because each follow-up turn writes N+1 rows for N+1 sends with the turn row
re-recording follow-up N, **1,071 understates sends by 30 — the defensible figure is 1,101
and remaining is 3,219.**
