# CONTRAST24

Status: done

Run: both arms, turns 1-24, task TX-01, rep 1.
Rows: experiments/ptr-engine/measure/rows-contrast24-tx01-20261109.jsonl (51 rows: 24 C + 27 D).
Cap: 2688 -> 2739 (51 requests; bound 52).

Dry-run offline: printed turn-20 contract text, markers `[MASKED doc-config@r1]`, `[MASKED doc-constants@r1]`, `[MASKED doc-errors@r1]` (3), and D's advertised `fetch` schema; no socket opened.

Turn 20 raw answers:
- masking-no-fetch: "ANSWER: NONE" (kind NONE; fact masked, no fetch) -> fail.
- bounded-context-fetch: "ANSWER: NONE" (kind NONE; fetched doc-constants@r1, needed doc-config@r1 unfetched) -> fail.

Turn 22 raw answers:
- masking-no-fetch: "ANSWER: NONE" (kind NONE) -> fail.
- bounded-context-fetch: "ANSWER: NONE" (kind NONE; fetched doc-constants@r1, needed doc-config@r1 unfetched) -> fail.

Headline: D fetched an unrelated ref at the checkpoint turns and answered NONE, so the retrieval mandate was not honoured (unfetched marker could have supplied the fact). C correctly could not answer (masked). Neither arm produced the expected NUM.

Scorecard (score_longrun): C 0/12 checkpoints (turns 20/22/24 fail); D 0/12 (20/22 fail, 24 answer "The config key is MAX_BATCH_SIZE." vs expected "MAX_BATCH_SIZE"). log.completeness fails (only 24 of 48 turns).

Accounting: 51 rows, all task_id TX-01, one fixture_sha256 44a1b4356536a0a55757ed2a4c90f5ef7f9d0541836007dc195a50ab3db2ec21. Cap advanced by exactly 51.