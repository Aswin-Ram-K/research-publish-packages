# U-SPCC-44 — E1's three-arm cell ran; the fetch arm never fetched

## What was run

G3 was confirmed admissible **without spending**, by calling `cell.eval_gate_prereg`
directly with the runner's own operands (`hypothesis=E1, turns=100, reps=1, arms=3`)
against `longrun/tasks-v7/TX-03.v1.json`:

```
{"gate": "G3", "hypothesis": "E1", "n": 300, "ok": true, "exit": null,
 "thresholds": {"request_ceiling": [200, 500], "checkpoints_required": 48,
                "checkpoints_in_fixture": 48,
                "basis": "PREREG-SPCC E1: 200-500 requests over 48 checkpoints"},
 "rule_id": "PREREG-SPCC"}
```

`--dry-run` returns before the gate, so it cannot show a G3 verdict; the direct call is
the only zero-request proof.

The cell then ran as specified:

```
run_longrun.py --fixture longrun/tasks-v7/TX-03.v1.json \
  --arms spcc,masking-no-fetch,bounded-context-fetch --reps 1 \
  --temperature 0 --seed 42 --model occamy-1.0 \
  --base-url http://192.168.2.168:8012/v1 --claim-mode E1 --budget-cap 12094 \
  --run-id e1-final-2026-11-10 \
  --rows experiments/ptr-engine/measure/rows-e1-final-2026-11-10.jsonl
```

`rows=300 requests=300 truncated=0 failed_turns=0`, all `finish_reason: stop`, all
`content_source: content`. Each arm reconciled at delta 0
(`spent_at_start` 8081 → 8181 → 8281 → 8381). Programme spend after the cell: 8,381 of
12,094.

## Scores (`score_answer_contract_rows`, one call per arm)

| arm | value_correct | contract_correct | NONE | wrong | unparsed | graded | total |
|---|---:|---:|---:|---:|---:|---:|---:|
| `spcc` | 22 | 21 | 26 | 0 | 0 | 48 | 48 |
| `masking-no-fetch` | 8 | 8 | 40 | 0 | 0 | 48 | 48 |
| `bounded-context-fetch` | 5 | 5 | 0 | 0 | 0 | 5 | 48 |

`spcc`'s 22 value-correct vs 21 contract-correct is the `TEXT 3700` case: turn 70,
`cp.TX-03.f08.d2`, answered `ANSWER: TEXT 3700` where `NUM` was required. Value right,
contract wrong — `kind_mismatch_value_correct: 1`.

`bounded-context-fetch` is **not a fetch arm in this run**. Its manifest records
`tools_mode: "off"`, `tools_schema_sent: false`, and `--tools` was not passed. The
runner's fetch service is gated on
`if arm == arm_cd.ARM_D and (fetch_tools_enabled(cfg) or tools_enabled(cfg))`
(`run_longrun.py:3566`), so it never ran: `service_fetches`, `fetch_rows`,
`fetch_tokens` and `retrieval_attempt` are null on all 300 rows. 43 of the 48
checkpoint turns emitted `ANSWER: CALL fetch(ref="doc-fact-01@1")`, were stamped
`interim: true`, `interim_reason: fetch_followup`,
`protocol_violation: answer_wrapped_tool_call`, and no follow-up was ever sent
(`send_index` is 0 on all 100 rows of that arm). The scorer skips interim rows, so
those 43 checkpoints have no final answer and are counted as failures in `total`.

A corrected fetch arm needs `--tools fetch`. It was **not** re-run: G3 refuses a
single-arm cell (`n=100 < 200`), so a corrected fetch arm requires all three arms
again (~343 requests), which would put E1 at 643 requests — over its own 200–500
preregistered ceiling and over this unit's 500-request bound.

## `spcc` pass turns

21 contract-correct passes (the 22nd value-correct pass is the `TEXT` row above).

Pre-compaction (`turn < 24`), 12 passes: turns 3, 6, 7, 9, 10, 13, 14, 16, 19, 21, 22, 23.
Post-compaction (`turn >= 24`), 9 passes: turns 47, 54, 57, 58, 60, 63, 67, 69, 72.

Compaction count changes at turns 25, 49, 73, 97 (`compactions` 0→1→2→3→4). **No pass
crosses a compaction boundary.** Every post-compaction pass is for a fact introduced
after the most recent compaction: fact-05 intro 45 → pass T47; fact-06 intro 52 →
passes T54/57/58/60/72; fact-07 intro 61 → passes T63/67/69. The two facts introduced
just before a compaction — fact-04 (intro 24, compaction at 25) and fact-08 (intro 68,
compaction at 73) — have **zero** passes. The one `d2` miss at turn 26 is
`cp.TX-03.f04.d2`, answered `ANSWER: NONE`: the fact was introduced at turn 24 and the
journal was dropped at turn 25.

## Verdict

E1's preregistered prediction (`PREREG-SPCC.md`): *"`spcc` scores ≥ fetch on single-fact
and > masking everywhere; billed tokens ≤ masking."*

- `spcc` ≥ fetch on single-fact: **unadjudicable** — the fetch arm never fetched.
- `spcc` > masking everywhere: **FAILED**. `d2` is 6/8 vs 8/8; `d32` is 0/8 vs 0/8.
- billed tokens ≤ masking: **held** — 9,066 vs 9,730.

E1's preregistered falsifier: *"`spcc` below fetch on single-fact, or `spcc` not strictly
above masking on any checkpoint class, or billed tokens above masking."*

**The falsifier did not fire.** `spcc` is strictly above masking on `d5` (4>0), `d6`
(5>0), `d8` (4>0) and `d20` (2>0), so the "not strictly above on any class" clause is
false; `spcc` is not below fetch; billed tokens are below masking.

The prediction failed on its "everywhere" clause while the falsifier stayed silent —
the two are not the same statement, and the prereg's own deviation note predicted
exactly this split.

## Disagreement with the earlier single-arm observation

`rows-e1-spcc-2026-11-10.jsonl` (one arm, 100 requests) gave `spcc` 20/48 value,
19/48 contract. This cell gives 22/48 and 21/48. Same arm, same fixture, same
temperature 0 and seed 42, so the 2-checkpoint difference is run-to-run
non-determinism on the serving stack, not a treatment effect. **This cell is the E1
evidence**: it is the preregistered three-arm design, all three arms in one invocation
under one manifest, and it replaces the single-arm cell that was inadmissible (one arm,
below the floor). The single-arm numbers stay in the ledger as a replication, not as
the headline.

## What this does not establish

- Nothing about `bounded-context-fetch`. The arm is degenerate here.
- Nothing about position vs presence (E3).
- No cross-build claim: `image_digest` and `exact_argv` are `UNSOURCEABLE` in all three
  manifests.
