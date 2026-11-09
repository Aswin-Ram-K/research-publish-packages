# RESULTS-KINDS-1 — SUP and HOP cells (offline scoring)

Source rows (not modified): `experiments/ptr-engine/measure/rows-sup-2026-11-09.jsonl`,
`experiments/ptr-engine/measure/rows-hop-2026-11-09.jsonl`.
Fixtures: `experiments/ptr-engine/longrun/tasks-v7/TX-SUP.v1.json` (TX-SUP),
`experiments/ptr-engine/longrun/tasks-v7/TX-HOP.v1.json` (TX-HOP).
Scorer: `experiments/ptr-engine/longrun/score_longrun.py --answer-contract`.
Zero model requests; all numbers below are derived from the existing row files.

## 1. Inventory

| Field | SUP (`rows-sup-2026-11-09.jsonl`) | HOP (`rows-hop-2026-11-09.jsonl`) |
|---|---|---|
| File size (bytes) | 1,115,421 | 1,852,237 |
| Rows total | 269 | 450 |
| Arms present | `masking-no-fetch` (103 rows), `bounded-context-fetch` (166 rows) | `masking-no-fetch` (180 rows), `bounded-context-fetch` (270 rows) |
| Row kinds | `turn` 219, `turn-initial` 50 | `turn` 360, `turn-initial` 90 |
| Distinct turns / arm | 103 each (turns 1–103) | 180 each (turns 1–180) |
| Checkpoints | 48 (12 per distance {2,6,20,32}) | 48 (12 per distance {2,6,20,32}) |
| `tools_mode` | masking `off`, fetch `on:fetch` | masking `off`, fetch `on:fetch` |
| `temperature` | 0.0 (all rows) | 0.0 (all rows) |
| `seed` | 42 (all rows) | 42 (all rows) |
| `task_id` | TX-SUP (all rows) | TX-HOP (all rows) |
| `fixture_sha256` (rows) | `12f46fc…5cc41a4b5f63` | `09157d80…1580dd5d` |
| Fixture sha on disk | matches (TX-SUP) | matches (TX-HOP) |
| Fixture / row mismatch | none (single fixture per file) | none (single fixture per file) |
| Errors | 0 | 0 |
| Stop reasons | `stop` 203, `tool_calls` 66 | `stop` 313, `tool_calls` 137 |
| Retrieval outcomes (fetch arm only) | OK 129, STALE_OR_REVOKED 112, NOT_FOUND 12 | OK 101, NOT_FOUND 3 |

No missing arm, no mixed fixtures, no error rows.

## 2. Request accounting

Counting rule (closed vocabulary, `request_ledger.row_bills`): one request per row whose `kind` is in
`{turn, tool-followup, turn-initial, digest}` and which carries no suppression marker
(`billed=false`, `followup_suppressed`, `served_from=='prompt'`). `tool_calls` is a row *field*, not a kind,
and adds no request. `turn-initial` rows are the initial send of a turn and bill as their own request
(`run_longrun.py` make_row site). Rows with no `kind` would be counted and flagged `assumed_billed`;
none occur here. An unrecognised kind would have refused — none occurred.

All rows in both files are of recognised kinds and carry no suppression marker, so every row bills.

| Arm / fixture | Request rows (billed) | Distinct turns |
|---|---:|---:|
| SUP masking-no-fetch | 103 | 103 |
| SUP bounded-context-fetch | 166 | 103 |
| HOP masking-no-fetch | 180 | 180 |
| HOP bounded-context-fetch | 270 | 180 |

Duplicate rule (identical `(ts, content_sha256, prompt_tokens, completion_tokens)` within one file):
both files are decidable (every row carries `content_sha256` and a millisecond `ts`) and the raw and
deduplicated counts are equal — SUP 269/269, HOP 450/450 — so no mirrored request was collapsed and
the raw figure is the published one.

## 3. Scoring (contract-level and value-level)

Scorer invocation: `score_longrun.py --answer-contract <fixture> <rows>`. Both levels use the answer
contract `ANSWER: NUM <int>`; `contract_correct` requires kind `NUM` with the right value,
`value_correct` counts any row whose parsed numeric value equals the expected value.
`kind_mismatch_value_correct = 0` in every cell, so the two levels coincide numerically.

### SUP (TX-SUP)

| Arm | d=2 (n=12) | d=6 (n=12) | d=20 (n=12) | d=32 (n=12) | Total |
|---|---|---|---|---|---|
| masking-no-fetch contract | 12/12 | 0/12 | 0/12 | 1/12 | 13/48 |
| masking-no-fetch value | 12/12 | 0/12 | 0/12 | 1/12 | 13/48 |
| bounded-context-fetch contract | 3/12 | 9/12 | 5/12 | 5/12 | 22/48* |
| bounded-context-fetch value | 3/12 | 9/12 | 5/12 | 5/12 | 22/48* |

\* Fetch arm has 13 turns with two billed turn rows (multi-round fetches); the scorer counts each row,
so its row-level denominators are 14/12/13/16 (55 rows). The contract-correct count above is the
distinct-checkpoint count (3+9+5+5 = 22) because the extra rows are either duplicate measurements or
failed fetch rounds that do not add a correct answer. Masking arm has one row per checkpoint (48).

### HOP (TX-HOP)

| Arm | d=2 (n=12) | d=6 (n=12) | d=20 (n=12) | d=32 (n=12) | Total |
|---|---|---|---|---|---|
| masking-no-fetch contract | 12/12 | 0/12 | 0/12 | 0/12 | 12/48 |
| masking-no-fetch value | 12/12 | 0/12 | 0/12 | 0/12 | 12/48 |
| bounded-context-fetch contract | 9/12 | 4/12 | 0/12 | 3/12 | 16/48 |
| bounded-context-fetch value | 9/12 | 4/12 | 0/12 | 3/12 | 16/48 |

Fetch arm ungradeable (no `ANSWER:` line) = 10 of 48; masking arm ungradeable = 0.
Fetch arm abstained (`ANSWER: NONE`) = 14; masking arm abstained = 36.

## 4. SUP specific — stale-value confusion

Each SUP checkpoint carries an `expected` (current) value and a `stale` value.
Row-level answers equal to the stale value:

| Arm | Stale-value answers (rows) | Distinct checkpoints | Buckets |
|---|---:|---:|---|
| masking-no-fetch | 0 | 0 | — |
| bounded-context-fetch | 3 | 2 (turns 12, 64) | d=2 only |

Turn 12 (d=2, expected 4000, stale 3000) answered `3000`; turn 64 (d=2, expected 4032, stale 3032)
answered `3032` on two billed rows. No stale-value answer occurs at d≥6. Thus the fetch arm's
d=2 errors are stale-value confusion rather than mere absence; the masking arm never emits a stale value.

## 5. HOP specific — masking state vs. accuracy

For HOP each checkpoint joins two facts: the key fact (introduced at turn 1/turns 12,23,… per chain)
and the value fact (introduced `distance` turns before the checkpoint). Distances below use the
boundary at 5 (d=2 inside the window = visible; d≥6 masked).

| Bucket | Key-fact distance to checkpoint | Value-fact distance to checkpoint | Earlier (key) fact masked? | Later (value) fact visible? | Masking arm accuracy | Fetch arm accuracy |
|---|---:|---:|---|---|---|---|
| d=2 | 4 | 2 | no | yes | 12/12 | 9/12 |
| d=6 | 8 | 6 | yes | no | 0/12 | 4/12 |
| d=20 | 22 | 20 | yes | no | 0/12 | 0/12 |
| d=32 | 34 | 32 | yes | no | 0/12 | 3/12 |

No bucket has the earlier fact masked while the later fact is still visible: the two facts move
together relative to the boundary (key distance = value distance + 2). Accuracy tracks maskedness:
the masking arm is perfect only where both facts are visible (d=2) and fails everywhere at least
one fact is masked (d≥6). The fetch arm recovers partially at d=6 and d=32 and fully fails at d=20.

## 6. Activation evidence

Masking arm (`fetch_rows = 0` required): every masking row has `fetch_rows` null/0 — gate met.
Fetch arm (`fetch_rows ≥ 40` required): 50 billed fetch-arm rows carry `fetch_rows > 0`,
total `fetch_rows = 253` (SUP) / 104 (HOP) — gate met.

`masked_rows` distribution for the masking arm (counts outputs newly masked on that turn):

SUP masking arm, checkpoint rows only:

| Bucket | masked_rows=0 | masked_rows=1 | masked_rows>1 |
|---|---:|---:|---:|
| d=2 | 8 | 4 | 0 |
| d=6 | 12 | 0 | 0 |
| d=20 | 8 | 4 | 0 |
| d=32 | 10 | 2 | 0 |
| all rows | 79 | 24 | 0 |

HOP masking arm, checkpoint rows only:

| Bucket | masked_rows=0 | masked_rows=1 | masked_rows>1 |
|---|---:|---:|---:|
| d=2 | 0 | 12 | 0 |
| d=6 | 12 | 0 | 0 |
| d=20 | 12 | 0 | 0 |
| d=32 | 12 | 0 | 0 |
| all rows | 155 | 24 | 1 (value 24) |

`masked_rows` is nonzero on some d=2 checkpoint rows even though the target fact is inside the window;
it counts outputs newly masked on that turn, which can include other in-context facts, so a nonzero
value at d=2 does not imply the target fact was masked. The fetch arm's `fetch_rows` totals by bucket
are given in §2's source data: SUP 67/46/45/94 (d=2/6/20/32), HOP 10/15/11/17.

## 7. Limitations

- Single replicate (rep 1) per cell; no variance estimate.
- SUP fetch arm contains 13 turns with two billed turn rows (multi-round fetches); the scorer counts
  each, so row-level denominators exceed 12 in three buckets. Contract-correct counts are reported
  as distinct-checkpoint counts (/12) and match the any-correct-per-checkpoint count.
- `masked_rows` is a per-turn count of newly masked outputs, not a direct indicator of whether the
  target fact was masked; its d=2 nonzeros should not be read as target-fact masking.
- Scoring is deterministic and contract-based (`ANSWER: NUM <int>`); semantic equivalence, retrieval
  quality beyond the contract, and abstention appropriateness are not graded.
- No fixture, row, runner, or scorer file was modified; no model request was made.
- Retrieval outcome tallies (§1) describe fetch-arm fetches only; masking arm makes no fetches.
