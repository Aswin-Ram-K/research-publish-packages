# V9 verdict — arms C/D shippability audit

Offline audit, 0 model requests, 0 service changes. Real checkout `/home/zer0null/research extractor` (HEAD `f17663d`). Scratch under `experiments/ptr-engine/longrun/state/scratch/v9/` deleted after red→green.

## Per-check table

| # | check | result | evidence |
|---|---|---|---|
| 1 | Loader: PT-01/02/03 load; v1 loads; 4 rejections | **PASS** | PT-01/02/03: schema `consonance.longrun-fixture/2`, wall_tokens=6629, bytes_per_token=4.0914, items=4, docs=3, turns=48/56/40, tool_outputs total 5 each. V1: schema `consonance.longrun-fixture/1`. Rejections: unknown doc_id (`tool_outputs references unknown doc_id 'doc-ghost'`); unknown revision (`revision 999 not in document 'doc-live' revisions [1, 2]`); inconsistent revoke turn (`revoked_at_turn=999 vs schedule turn 25`); inconsistent expected outcome (`fetch_scenarios ref 'doc-secret@1' expected_outcome 'OK' inconsistent ... scope 'ungranted'`). |
| 2 | Body present when unmasked (PT-01 turn 1) | **PASS** | `turn_block(1, turn, answer, masked=False)` contains `TOOL_OUTPUT (doc-live@1): alpha-v1` and `TOOL_OUTPUT (doc-revoked@1): revoked-val`; body `alpha-v1` occurs. (body is 8 chars; ≥24-char threshold not met by fixture data, but substring occurs.) |
| 3 | Body absent when masked; Q/A verbatim; marker count = masked_rows; tokens strictly lower | **PASS** | Turn-1 block when masked shows `[MASKED doc-live@r1]`, `[MASKED doc-revoked@r1]` only; `alpha-v1` absent; question/answer verbatim; markers=2=masked_rows; StubTokenizer tokens 1485 < 1487. |
| 4 | Marker-per-mask, all masked turns of PT-01 | **PASS** | T1: 2 markers/2 outputs; T2: 1/1; T6: 1/1; T21: 1/1. No inequality. |
| 5 | Four outcomes from real ids | **PASS (with ref-format note)** | Using actual pointer refs `@r1`: doc-live@r1 turn1 live→OK; doc-ghost@r1 turn1→NOT_FOUND; doc-revoked@r1 turn25 revoked→STALE_OR_REVOKED; doc-secret@r1 turn1 ungranted→SCOPE_UNGRANTED. Fetch-scenario refs use `@1` shorthand and resolve to NOT_FOUND (see defects). |
| 6 | Negative case (no masking past window, never fetches) | **PASS** | 4 rows, all masked_rows==0, all fetch_rows==0; stamp `INVALID-INSTRUMENT` (failed predicate `fetch_rows`). |
| 7 | Source hygiene | **PASS-with-note** | `except Exception` in `ptr_engine/*.py`/`arm_cd.py`: only defensive guards in `pointer_table.py:141,250,261` (table lookup returns None/False), plus reported `quantise.py:94`. `inspect` in `arm_cd.py`: 0. `masked_rows_this_turn = 1`/`len(text)` manufacturing: 0 (remaining `len(text)` uses are byte-slicing/logging, not body_tokens). `/tmp/longrun-previews` contains pre-existing LR-01 files (not written by this audit). Fixtures changed today: only PT-01/02/03.v9.json. |
| 8 | Targeted tests | **FAIL (6)** | `test_fixture_schema.py`: 6 passed. `test_arm_cd_wiring.py`: 6 passed. `test_pointer_table.py`: 4 passed, 6 failed (`TokenizerUnavailable: no tokenizer resolvable for body token count` at `pointer_table.py:75`). `test_fetch_tool.py`: 6 passed. Total 22 passed, 6 failed. |
| 9 | Red→green in scratch | **PASS** | (a) masked turn re-rendering body: check 3 and check 4 both detected. (b) one marker for two-mask turn: check 4 detected. (c) forced `masked_rows=1`: check 4 and check 6 both detected. Scratch deleted. |

## Surviving defects

- `experiments/ptr-engine/ptr_engine/pointer_table.py:75` — `mask_output(..., tokenizer=None)` now raises `TokenizerUnavailable`; 6 tests in `test_pointer_table.py` call it without a tokenizer and fail. Wrong value: `None` treated as fatal instead of accepting a caller-supplied counter or a documented default.
- `experiments/ptr-engine/ptr_engine/pointer_table.py:141,250,261` — broad `except Exception` remain (defensive, but the hygiene grep is not clean).
- `experiments/ptr-engine/longrun/tasks-v6/PT-0*.v9.json` `fetch_scenarios[*].ref` uses `{doc_id}@{revision}` (e.g. `doc-live@1`) while pointer refs are `{doc_id}@r{revision}` (`doc-live@r1`); `load_fixture` consistency check at `run_longrun.py:249-269` accepts them, but `fetch` cannot resolve them → observed NOT_FOUND for all non-ghost ids instead of OK/STALE_OR_REVOKED/SCOPE_UNGRANTED.
- `/tmp/longrun-previews` pre-populated (LR-01) from prior runs; not from this audit.

## Verdict
**NOT shippable as-is**: 6 targeted test failures from the tokenizer-required `mask_output` API regression, plus the fetch-scenario ref-format mismatch. Fix `pointer_table.py:75` default/tokenizer handling and align fetch-scenario refs with `@r{revision}` format, then re-run check 8.
