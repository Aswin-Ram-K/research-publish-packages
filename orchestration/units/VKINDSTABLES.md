# UNIT `VKINDSTABLES`

**Status:** done · **Bound:** 60 calls · **Inference requests:** 0 (offline) ·
**Historical measurement files edited:** none (read-only).

## Purpose

Independently recompute the four-kind result tables for TX-SUP, TX-HOP, TX-AGG, TX-ABS
(masking-no-fetch vs bounded-context-fetch) from the six row files, using the shipped
scorer `experiments/ptr-engine/longrun/score_longrun.py --answer-contract`. Do not trust
the two RESULTS-KINDS-2 documents.

## Scorer commands (verbatim)

```
cd "/home/zer0null/research extractor"
.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py --answer-contract experiments/ptr-engine/longrun/tasks-v7/TX-SUP.v1.json experiments/ptr-engine/measure/rows-sup2-masking.jsonl
.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py --answer-contract experiments/ptr-engine/longrun/tasks-v7/TX-SUP.v1.json experiments/ptr-engine/measure/rows-sup2-fetch.jsonl
.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py --answer-contract experiments/ptr-engine/longrun/tasks-v7/TX-HOP.v1.json experiments/ptr-engine/measure/rows-hop2-masking.jsonl
.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py --answer-contract experiments/ptr-engine/longrun/tasks-v7/TX-HOP.v1.json experiments/ptr-engine/measure/rows-hop2-fetch.jsonl
.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py --answer-contract experiments/ptr-engine/longrun/tasks-v7/TX-AGG.v1.json experiments/ptr-engine/measure/rows-agg2-2026-11-09.jsonl
.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py --answer-contract experiments/ptr-engine/longrun/tasks-v7/TX-ABS.v1.json experiments/ptr-engine/measure/rows-abs2-2026-11-09.jsonl
```

## Recomputed totals (contract-level == value-level; kind_mismatch=0 in every cell)

| Fixture | Arm | d=2 | d=6 | d=20 | d=32 | Total | Claimed | Verdict |
|---|---|---|---|---|---|---|---|---|
| TX-SUP | masking-no-fetch | 11/12 | 0/12 | 0/12 | 0/12 | 11/48 | 11/48 | reproduced |
| TX-SUP | bounded-context-fetch | 1/12 | 10/12 | 3/12 | 4/12 | 18/48 | 18/48 | reproduced |
| TX-HOP | masking-no-fetch | 12/12 | 0/12 | 0/12 | 0/12 | 12/48 | 12/48 | reproduced |
| TX-HOP | bounded-context-fetch | 9/12 | 0/12 | 0/12 | 0/12 | 9/48 | 9/48 | reproduced |
| TX-AGG | masking-no-fetch | 0/12 | 0/12 | 0/12 | 0/12 | 0/48 | 0/48 | reproduced |
| TX-AGG | bounded-context-fetch | 0/12 | 0/12 | 1/12 | 3/12 | 4/48 | 4/48 | reproduced |
| TX-ABS | masking-no-fetch | 3/12 | 0/12 | 0/12 | 0/12 | 3/48 | 3/48 | reproduced |
| TX-ABS | bounded-context-fetch | 6/12 | 6/12 | 3/12 | 0/12 | 15/48 | 15/48 | reproduced |

All eight arm/fixture combinations reproduce exactly (totals and per-bucket).

## Activation verification (turns with fetch_rows>0)

| Fixture | Arm | turns>0 | sum fetch_rows | Gate | Verdict |
|---|---|---|---|---|---|
| TX-SUP | masking-no-fetch | 0 | 0 | 0 required | PASS |
| TX-SUP | bounded-context-fetch | 42 | 226 | >=40 | PASS |
| TX-HOP | masking-no-fetch | 0 | 0 | 0 required | PASS |
| TX-HOP | bounded-context-fetch | 28 | 30 | >=40 | FAIL |
| TX-AGG | masking-no-fetch | 0 | 0 | 0 required | PASS |
| TX-AGG | bounded-context-fetch | 29 | 82 | >=40 | FAIL |
| TX-ABS | masking-no-fetch | 0 | 0 | 0 required | PASS |
| TX-ABS | bounded-context-fetch | 42 | 50 | >=40 | PASS |

Retrieval outcomes: SUP fetch 113 OK / 103 STALE_OR_REVOKED / 10 NOT_FOUND (42 turns);
HOP fetch 30 OK (28 turns); AGG fetch 77 OK / 4 NOT_FOUND / 1 STALE_OR_REVOKED (29 turns);
ABS fetch 46 OK / 3 NOT_FOUND / 1 SCOPE_UNGRANTED (42 turns). All match claimed.

## ABS five-way classification (48 checkpoints per arm) — reproduced exactly

Masking: correct_refusal 12, false_refusal 24, correct_value 3, wrong_value 9, ungradeable 0.
Fetch: correct_refusal 8, false_refusal 7, correct_value 15, wrong_value 16, ungradeable 2.
Per-bucket tables match the claimed doc exactly (d2/d6/d20/d32).

## SUP stale-recall — reproduced exactly

Answers equal to the fixture stale value: masking 1/48 (turn 64), fetch 2/48 (turns 12, 64);
all at d=2. Distinct-checkpoint counts match claimed.

## AGG partial-sum claim — count reproduces, mechanism does not

Of the 42 wrong numeric answers (20 masking + 22 fetch), exactly 3 equal a subset sum of the four
member VALUEs of their group:
- cp.TX-AGG.g03.d2 turn 15: 82650 = a single member (f4)
- cp.TX-AGG.g04.d2 turn 22: 113436 = 77976 + 35460 (two members)
- cp.TX-AGG.g11.d2 turn 53: 115846 = 32874 + 82972 (two members)

Count 3 of 42 reproduces. But the claim's parenthetical "(three of four members)" is wrong:
0 of the 3 equal a three-member (three-of-four) sum, and 1 equals a single member value,
contradicting the claim's "none equals a single omitted or duplicated member".

## Exclusion / integrity checks

- Mixed fixtures in one file: none (single task_id per file; sha matches disk for all four).
- Pooled replications: none (rep=1 only in every file).
- Duplicate (arm,turn,kind): none except AGG fetch multi-round fetches at non-checkpoint
  turns 91-94, 97 (legitimate multi-round turns, not duplicates).
- Truncated turns (stop_reason=length): 2, AGG fetch turns 91 and 97. Matches claimed.
- Empty final-answer checkpoint turns (counted as ungradeable, retained): SUP fetch 13,
  HOP fetch 6, AGG fetch 4, ABS fetch 2. Matches claimed ungradeable counts.
- answer_parse_error totals: sup masking 0 / sup fetch 55 / hop masking 0 / hop fetch 37 /
  agg 42 / abs 44 (includes turn-initial no-answer rows, as expected).
- Row accounting: sup masking 103, sup fetch 145, hop masking 180, hop fetch 208,
  agg masking 100, agg fetch 142, abs masking 100, abs fetch 142. Matches claimed.
- Fixture shas on disk match row fixture_sha256 for all four.

## Numbers that do NOT reproduce

1. AGG partial-sum mechanism: claim says the 3 subset-sum wrong answers are "three of four members"
   and that "none equals a single ... member". Actual: 0 three-member, 1 single-member, 2 two-member.
   (Count of 3 reproduces; composition does not.)
2. No other number failed to reproduce. All eight totals, all per-bucket cells, all activation
   counts, the ABS five-way table (including per-bucket), and SUP stale-recall match exactly.

## Non-discrepancies noted (for completeness)

- SUP fetch scorer reports ungradeable 13 and abstained 10 (claimed doc states 18/48 correct;
  no failure split published for SUP, so nothing to contradict).
- HOP fetch ungradeable 6, abstained 20 (claimed doc publishes these; match).
- kind_mismatch_value_correct = 0 in all eight cells, so contract and value levels coincide
  numerically (as claimed).
