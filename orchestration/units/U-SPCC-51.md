# U-SPCC-51 — record the corrected three-arm E1 cell

**Status:** DONE. Record-only unit: 0 endpoint requests, 0 model calls.

## What was recorded

`experiments/ptr-engine/measure/rows-e1-tools-2026-11-10.jsonl`, commit `08a7908`, 318
requests, 0 failed, 0 truncated, reconciliation delta 0 on all three arms (`spcc`
8,381→8,481/100; `masking` 8,481→8,581/100; fetch 8,581→8,699/118). Programme spend 8,699 of
12,094. `tools_mode: on:read_file`, `tools_schema_sent=true` on all 100 `spcc` and all 118
fetch rows.

| arm | value | contract | NONE | wrong | unparsed | graded | requests |
|---|---:|---:|---:|---:|---:|---:|---:|
| `spcc` | 22 | 21 | 26 | 0 | 0 | 48 | 100 |
| `masking-no-fetch` | 8 | 8 | 40 | 0 | 0 | 48 | 100 |
| `bounded-context-fetch` | 22 | 22 | 11 | 4 | 11 | 48 | 118 |

18 of 48 fetch rounds used; 18 checkpoints answered on a follow-up carrying a fetched body,
15 of those 18 correct; `fetch_prompt_serves=0`.

## Gaps against the measured ±2/48 band

- `spcc`−masking: **+14 value / +13 contract** — outside.
- fetch−masking: **+14 / +14** — outside.
- fetch−`spcc`: **0 value / +1 contract** — inside. The two retention mechanisms are not
  separable on this cell.

## The claim

The effect is **retention, not mechanism**. Masking destroys the body at turn 4; the
stable-prefix journal and fetch-on-demand both keep it reachable, and both land at 22/48.
Neither is separable from the other. Both fail at `d32` together.

## Caveats (all four recorded in every doc)

1. Fetch 22 is a **floor**: 10 of 48 checkpoints ended `finish_reason=tool_calls` with
   `content ''`, `tool_calls []`, `tool_call_ids null` and no follow-up — harness capture bug,
   fix in flight (`U-SPCC-49`). Not the arm's ceiling.
2. Rows carry **pre-fix** `fetch_rounds_used` stamps (0 on 52 rows, null on 66); the counter
   was dead at `run_longrun.py:3359`; the corrected counter (`a9b9b70`) appears only on the
   next cell. Rows must not be rewritten.
3. 16 rows carry `protocol_violation=answer_wrapped_tool_call` on fetch-arm turn-initial rows;
   each has a matching turn row that did fetch, so none stranded. Still open.
4. Temperature 0 + seed 42 is not reproducible on this endpoint (±2/48); every figure is a
   single-rep point estimate with that band.

## Verification performed

Re-derived from the rows file, not copied from the handoff: arm row counts (100/100/118),
`failed`/`truncated` = 0, `tools_mode`/`tools_schema_sent` per arm, `finish_reason` split,
`protocol_violation` count (16), `fetch_rounds_used` stamp distribution (52 zeros, 66 nulls),
`fetch_prompt_serves` (0 on 52, null on 66), `reconcile_delta_tokens` (0 on 313 rows, null on
5), billed totals (16,875 / 14,007 / 39,594), per-checkpoint merge of primary and
`fetch_followup` rows (48 checkpoints per arm; fetch 22 value / 11 NONE / 4 wrong / 11
unparsed), and per-distance buckets for all three arms.

**One correction to the shared context's table:** fetch `unparsed` is **11**, not 10 —
22+11+4+10 = 47, not 48. The 11th is `cp.TX-03.f02.d8`, which answered `ANSWER: CAL…` on a
follow-up (a malformed answer kind, not a harness capture). The 10 harness-capture rows are
exactly the ones with `tool_call_ids null`; three further stranded rows carry non-null
`tool_call_ids` and are counted in the 11.

## Writes

`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` (one 7-column row; column
count 18→19 rows at 7 columns, unchanged), `docs/STATE.md`, `journal/2026-11-10.md`,
`orchestration/STATUS.md`, `orchestration/units/U-SPCC-51.md`,
`orchestration/handoffs/U-SPCC-51.json`. `PREREG-SPCC.md` untouched.
