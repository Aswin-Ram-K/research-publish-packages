# V7 verdict — arms C/D activation proof

Offline audit, 0 model requests, 0 service changes. Real checkout `/home/zer0null/research extractor` (branch `research/next-candidates-2026-10-24`, HEAD `f17663d`). `arm_cd.py` final mtime `2026-11-08 01:07:26.417718355 -0600` (U5 rewrite landed mid-audit; re-read before running checks 3–5).

## Per-check table

| # | check | result | evidence |
|---|---|---|---|
| 1 | stub grep over `pointer_table.py`, `fetch_tool.py`, `arm_cd.py` | **PASS-with-note** | `fetch_tool.py` (line 7) and `arm_cd.py` now hard-import `pointer_table` with **0** `except Exception`. `pointer_table.py` still has 4 broad `except Exception` at 65/129/194/205 — all defensive guards (tokenizer fallback, table lookup), not stubs. Pre-rewrite `arm_cd.py` had fallback stub at 26–62; recorded as FAIL finding, fixed by U5. |
| 2 | real code paths | **PASS** | `arm_cd.py:47` `mask_output(...)`; `:54` `masked_entries.append(entry)`; `:108` `build_table(state.masked_entries)`; `:109` `batched_fetch(...)`; tool results + 2nd model call at `run_longrun.py:2838-2841`. No placeholders. |
| 3 | tests | **PASS (relevant)** | `pytest tests/test_pointer_table.py tests/test_fetch_tool.py longrun/tests/test_arm_cd_wiring.py -q` → **22 passed in 0.45s**. Full `longrun/tests/` run has unrelated collection errors/timeouts (numpy/verdict-semantics partition drift) not caused by C/D. |
| 4 | model-free E2E | **PASS** | C row (turn 5): `masked_rows=1, masked_entry=[{ref:turn-1@r1,...}], fetch_rows=None, retrieval_outcomes=None, fetch_tokens=None`. D row (turn 6): `masked_rows=1, fetch_rows=1, retrieval_outcomes=['OK'], fetch_tokens=11`. D two-fetch turn: exactly **2** model calls. A/B rows: `masked_rows/fetch_rows/fetch_tokens` all **None**, not 0. |
| 5 | stamp layer | **PASS** | `run_longrun.instrument_status`/`analyze_stats.instrument_status`: C and D produced rows → **VALID**; zeroed rows → **INVALID-INSTRUMENT** (predicate named: `masked_rows` / `fetch_rows`). |
| 6 | fixtures | **PASS** | `check_pointer_fixtures.py` → 3 files OK, all four outcomes, 4 checkpoints each. Sample checkpoint `cp.PT-01.t12`: ground_truth `{doc:doc-live, revision:1, value:alpha-v1}`, `stale_value=alpha-v0` (differs). |
| 7 | existing arms | **PASS** | `transcript-grow, transcript-compact, pointer-stable, lease-reopen` import; `test_guards.py` 1 passed. |
| 8 | path deviation | **noted** | `longrun/tests/test_arm_cd_wiring.py` collects 6 tests (`--collect-only`); suite discovers it. Matters only as a carded-path deviation; no functional impact. |
| 9 | red→green | **PASS** | Scratch copy of `pointer_table.py` with `mask_output` returning body unmasked → `test_mask_output_marker_and_entry` fails (`assert 'hello world body' not in 'hello world body'`). Original untouched; scratch deleted. |

## Defects found
- `arm_cd.py` pre-U5 fallback stub (lines 24–62, mtime 01:01:08) — **fixed** by U5 (new mtime 01:07:26; `grep -c "except Exception"` = 0; no local `mask_output`/`batched_fetch`/`PointerEntry`/`FetchResult`).
- `pointer_table.py:65/129/194/205` broad `except Exception` are defensive, not stubs, but are the only remaining silently-swallowing sites in the new path.

## Verdict
**PASS** for checks 1–9 on final file state. No unreachable outcomes in C/D. Residual broad-except sites in `pointer_table.py` are defensive guards, not silently-OK stubs.
