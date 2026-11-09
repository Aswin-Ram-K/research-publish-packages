# WITHDRAWN-INDEX — the register of withdrawn numbers

**Card contract:** one machine-readable register of every number this batch withdrew, with its superseder.
Offline (0 requests), additive only, no historical document rewritten. Bound: ≤22 tool calls, 0 requests.

## What was built

| path | role |
|---|---|
| `experiments/ptr-engine/measure/WITHDRAWN.json` | the register — 15 entries, machine-readable |
| `docs/WITHDRAWN.md` | the human surface, generated from the register (counts, table, per-entry detail) |
| `experiments/ptr-engine/tools/withdrawn_index.py` | the guard: `--check <file>` (exit 1 on an uncorrected withdrawn claim), `--self-test` (paths + fields) |
| `experiments/ptr-engine/longrun/tests/test_withdrawn_index.py` | 25 tests incl. red→green per entry |

## Entry schema

`id` · `claim` (the exact published string) · `claim_ref` (file:line or board message ref) · `kind`
(`wrong_denominator`/`wrong_unit`/`unsound_rule`/`retracted_finding`/`overstated_mechanism`) · `status`
(`withdrawn`/`superseded`/`disputed`) · `superseded_by` {`path`, `number`, `note`} · `decided_by` {`card`,
`handoff`} · `date` · `still_citable` · plus `quote`/`markers` (what the guard scans for) and an optional
`discrepancy` (where the seed and the artefact disagree).

## Seeds vs artefacts — three that did not match

1. **WI-002** — the seed cites `run_longrun.py:1493`; `REQUEST-LEDGER.json`'s own `evidence_note` records that
   the card's line drifted and the assignment is `run_longrun.py:1555` (869/869 rows hash the response).
   The deduction is visible but not applied (`deduction.applied false`).
2. **WI-004** — the withdrawal is real, but `docs/LATENCY-REPORT.md:45` still reads "`318.14 …` **stands**"
   while `:35`, `:90`, `:100`, `:153` say WITHDRAWN. Recorded as a live inconsistency; not edited here.
3. **WI-005** — the seed ("5/43 mixes grader eras") is **false as stated**: no artefact supports era-mixing,
   and 5/43 re-derives identically under `det_verify.py` sha `12ccc74e…`. Only the accusation is withdrawn;
   5/43 remains citable **with its instrument named**.

## Verification

- `--self-test` exit 0, 15 entries, 0 problems (every `decided_by` handoff exists and parses; every
  `superseded_by` artefact opens, except WI-004's literal `none — no replacement exists`).
- `--check` on a paragraph quoting `p95 318.14 [235.00, 526.41] n=68` verbatim → **exit 1**, `WITHDRAWN WI-004`.
  The same paragraph with its withdrawal attached → **exit 0**, CLEAN.
- `pytest` 25 passed, including a red→green case per entry (bare quote fires, corrected quote cleans).

## Honest limits

The guard matches published **strings**, so it catches a number quoted as published and misses a paraphrase
("about three hundred ms at p95"). Screening the 8 documents that currently fire is the follow-up work;
this unit records the hits rather than repairing the documents.
