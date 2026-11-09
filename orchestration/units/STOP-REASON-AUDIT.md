# UNIT `STOP-REASON-AUDIT` — why do seven cells contain nothing?

**Status:** done · **Requests:** 0 · **Mode:** offline, read-only over existing rows
**Opened from:** `MATRIX-HONESTY` `next_unit_hint` ("7 cells carry empty content with 128 completion
tokens … a serving/truncation fact, not a wrong answer").

## Purpose

Classify the 7 `missing_answer_empty` cells, decide whether 128 is a harness cap, count the pattern
across every `rows-*.jsonl`, fix the classification rule in writing, and say whether the harness
recorded anything about those turns.

## Write paths (exactly these, nothing else)

- `experiments/ptr-engine/tools/stop_reason_audit.py`
- `experiments/ptr-engine/longrun/tests/test_stop_reason.py`
- `experiments/ptr-engine/measure/STOP-REASON.json`
- `docs/STOP-REASON.md`
- `orchestration/units/STOP-REASON-AUDIT.md`
- `orchestration/handoffs/STOP-REASON-AUDIT.json`
- `orchestration/journals/STOP-REASON-AUDIT.jsonl`

Row files, grade files and fixtures were opened read-only and never rewritten. No endpoint was
contacted; no cell was re-run.

## Findings

| # | question | answer |
|---|---|---|
| 1 | What are the 7? | `empty_content: unrecorded_empty_content`. `content` = `""` (`content_sha256` = SHA-256 of the empty string), `completion_tokens` = 128 on all 99 empty rows of the file, `http_status` null, `error` null, and **no `finish_reason`, `truncated`, `max_tokens` or reasoning field exists in that row schema**. Not a truncated answer (no partial text); not provably reasoning-only (no reasoning channel recorded). |
| 2 | Is 128 a cap? | **Yes, a harness cap.** `manifests/stage1-lr01-lease-reopen-r1.json:36` `"max_tokens": 128`; raised to 16384 at `manifests/v6-run-longrun-pre-edit.py:1557`, with the history at `:1548-1552`. Corroborated by `METRICS.md:60` ("completions capped at 128, 99/192 rows without TTFT"). |
| 3 | How widespread? | 186 empty rows corpus-wide, **172 with non-zero completion tokens**, **0 with reasoning text**, 52 truncated answers. The seven cells' file contributes 99 of them; every file that records `finish_reason` contributes **zero**. |
| 4 | The rule | `empty_content: <cause>`, never `fail`, counted `missing_answer_empty` with the cause attached — written into `docs/STOP-REASON.md` with the per-arm arithmetic quoted from `MATRIX-COVERAGE.json`. |
| 5 | Did the harness object? | **No — silent.** `http_status` null, `error` null, and the objection fields absent from the schema (0/192 rows carry `finish_reason` or `truncated`). A harness defect, not an unhandled recorded outcome. |

## Verification

- `python3 experiments/ptr-engine/tools/stop_reason_audit.py` → writes `STOP-REASON.json`,
  `rows 1101, answered 915, empty 186, empty-with-tokens 172, reasoning-with-empty-content 0`.
- `python3 -m pytest experiments/ptr-engine/longrun/tests/test_stop_reason.py -q` → **15 passed**.
- **Red:** with the scanner absent the suite errors at collection (`ModuleNotFoundError`); with a
  pre-fix stub that has no cause vocabulary (every empty row routed to `fail`) the suite reports
  **7 failed, 3 errors, 1 passed**. **Green:** with the real scanner, **15 passed**.

## Lesson recorded

Reading only `content` would have libelled 84 of 105 baseline rows and 61 of 100 equalinfo rows as
empty answers — their answers live in `answer_text`. The scanner now resolves the answer text by
key presence (`content` → `answer_text` → `answer_raw`), and
`test_old_schema_answer_text_is_an_answer_not_an_empty_row` holds that line.

## Bound

≤28 tool calls; used 25. Handoff written on completion rather than at call 5, because the analysis
needed the row list first and the row list *is* the evidence; nothing was blocked.
