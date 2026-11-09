# UNIT LEDGER-REBUILD-27 — rebuild the request ledger, attribute the 27

**Status:** done. Offline, zero requests, no network.

## Objective
`measure/REQUEST-LEDGER.json` said `requests_raw 1101 / remaining 3219` while the grid derived
1852 from a fresh scan and the live corpus scan said 1128 / 3192. Rebuild from the row files with
the ledger's own builder, prove the delta is the one cell that stopped, and never hand-edit a figure.

## Builder
`experiments/ptr-engine/tools/request_ledger.py:build_report(paths, cap=4320, reserve=0, would_spend=0)`,
called over every `experiments/ptr-engine/measure/rows-*.jsonl` (15 files). Serialised exactly as the
module's own CLI does (`json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False) + "\n"`).

## Result (re-derived, not estimated)
| figure | superseded | rebuilt |
|---|---|---|
| `requests_raw` / `requests` | 1101 | **1128** |
| `requests_deduplicated` (diagnostic) | 1071 | **1098** |
| `duplicate_excess` | 30 | 30 |
| `remaining` / `remaining_raw` | 3219 | **3192** |
| `remaining_deduplicated` (diagnostic) | 3249 | **3222** |
| `diagnostic.deducted` | false | **false** |
| files / rows | 14 / 1101 | 15 / 1128 |
| files_deduped / not_applicable | 11 / 3 | 12 / 3 |

`spent_now - spent_before = 1128 - 1101 = 27`, exactly.

## Attribution
The 27 rows are `rows-cell-pointer-stable-20261026T182535Z.jsonl` **lines 1–27**: 27 rows, sha256
`46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1`, ts
`2026-10-26T18:25:56.773Z .. 2026-10-26T18:31:25.300Z`. Every one of the 14 pre-existing files has
the same sha256 it had in the superseded artefact, so no other file moved: removing this file's 27
requests from the rebuild returns exactly the old 1101.

## Deduction diagnostic preserved
The de-dup rule is disputed (`V-DUPLICATE-RULE` fail: `content_sha256` hashes assistant content, so
tuple identity is not request identity). The rebuild therefore publishes the RAW count and keeps
`requests_deduplicated` / `remaining_deduplicated` / `diagnostic.deducted: false` as a diagnostic that
is never deducted. The relationship did not change: raw is the budget figure, dedup is an audit figure;
the 27 new rows are all distinct, so `duplicate_excess` stayed 30.

## Artefacts
- `experiments/ptr-engine/measure/REQUEST-LEDGER.json` — superseding, carries `supersedes`
  `{spent 1101, remaining 3219, artefact_sha256_at_read 2f60b831…, read_at …}` and `reason`.
- `experiments/ptr-engine/measure/REQUEST-LEDGER.rebuild-2026-10-26.json` — byte-identical immutable
  snapshot (`sha256 6da0c1f19b7cd37203c9d99de5e5d8a9db879e002f389a2b525a776624c27806`).
- `measure/LEDGER-GRID-BASELINE.json` — **untouched**. It is stale against today's corpus but was
  correct at its own capture (`captured_utc 18:24:48Z`, 68 s before the cell's first row
  `18:25:56.773Z`), so its 1101/3219 is a dated pre-grid reading, not an error.

## Tests
`tests/test_ledger_delta.py`, `experiments/ptr-engine/tests/test_request_ledger_dedup.py`,
`experiments/ptr-engine/tests/test_request_ledger_sound.py`,
`experiments/ptr-engine/longrun/tests/test_request_ledger.py`.

Before: `2 failed, 39 passed` — `test_6_real_corpus_raw_1101_deduplicated_1071`
(`AssertionError: 1128 != 1101`) and `test_11_artefact_matches_a_fresh_scan`
(`AssertionError: 1101 != 1128 : artefact drifted from the rows: requests`).
After: `41 passed in 1.09s`.

Assertions that encoded the stale figure were updated **individually, with a comment naming the
cell**: `test_request_ledger_dedup.py:311`, `test_request_ledger_sound.py:223–230`, `:236`,
`:267`. `test_11` needed no edit — it asserts artefact == fresh scan and went green when the
artefact was rebuilt. Method names were left alone because `docs/FETCH-BUDGET-48.md` cites them.

## Bound
21 tool calls against a bound of 18 — overrun recorded in the handoff with the reason (four red
assertions across two files, plus one failed edit and its re-read).
