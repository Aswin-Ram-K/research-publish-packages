# X1 — Pointer/fetch fixture audit (current bytes)

Adjudication of 12 claims against current tree. Read-only; no code changed.

## Verdict table

| Claim | Verdict | Location (opened) | Decisive line / wrong value |
|---|---|---|---|
| X1.1 | TRUE | `ptr_engine/pointer_table.py:36-38,95` ; PT-01/02/03 `:281/:321/:241` | `_BODIES: dict = {}` (no reset/namespacing); `_BODIES[ref] = body`; all three fixtures declare `doc-live@r1` (rev1 value `"alpha-v1"` identical across all three) |
| X1.2 | TRUE | `longrun/run_longrun.py:375,1497` | `markers.append(f"[MASKED {did}@r{rev}]")` built inline, not via `make_ref`; missing revision leaves `rev = to.get("revision")` → `@rNone` |
| X1.3 | TRUE | `longrun/tasks-v6/PT-0*.v9.json:281/321/241` ; LR-01 `wall_tokens_basis` | `wall_tokens: 6629` with `"basis": "UNMEASURED"`; 6629 = LR-01 `5134 + 64.979*23` (transcript-grow), inherited, not derived from PT items (N differs 48/56/40) |
| X1.4 | TRUE | `longrun/check_pointer_fixtures.py:60,96-98,160-165` | `missing_ref_ok` computed unused; checkpoint nonexistent doc → `pass`; no fetch_scenarios ref→doc resolution; no tool_outputs required |
| X1.5 | FALSE | `longrun/run_longrun.py:1385,1485-1505` | No rebind of `turn` in masked loop; loop uses `turn_i`; `current = turn_user(t, turn)` uses the turn from `:1385`. Claim stale |
| X1.6 | PARTIAL | `longrun/arm_cd.py:54-132,135-137,209,261` | `_doc_entries` calls `mask_output` (tokenizer+sha256+_BODIES write) per access; `masked_entries` property itself is not read in the per-turn loop (`all_entries` is used in `service_fetches`) |
| X1.7 | PARTIAL | `ptr_engine/fetch_tool.py:102` | `tool_call_id: getattr(result, "tool_call_id", None)` → `null` (FetchResult has no field); no blanket `except` around `fetch` in fetch_tool (only `_coerce_range`/parse) |
| X1.8 | TRUE | `tests/test_fetch_tool.py:30-33,54-60` | malformed args asserted `{"ref": "", "range": None}` (fabricated empty fetch); budget test uses `_CharTok` (char==token), cannot distinguish |
| X1.9 | TRUE | `longrun/arm_cd.py:30-31` ; plan `:98-99` | `ARM_C="mask-no-fetch"`, `ARM_D="bounded-fetch"` vs plan names `masking-no-fetch`, `bounded-context-fetch` (BRCV) |
| X1.10 | TRUE | `longrun/arm_cd.py:252` ; `longrun/run_longrun.py:3023` | fetch budget `1024` default with no provenance in plan/fixture and not stamped on rows |
| X1.11 | TRUE | `longrun/tests/test_fixture_schema.py:72-74` | mutation loop has no count assertion; ref drift makes the `if` body a no-op |
| X1.12 | PARTIAL | `longrun/run_longrun.py:1650-1666` | `_simulate` exists and runs offline; needs numeric `wall_tokens`; does not exercise model/fetch/grading, so not a real end-to-end proof |

## Ranked TRUE/PARTIAL items

1. blocker — X1.1 `_BODIES` global keyed by bare ref, no reset/namespacing; PT-01/02/03 all `doc-live@r1` collide in one process; bodies identical.
2. blocker — X1.3 PT `wall_tokens=6629` unmeasured, inherited from LR-01, not derived from PT items.
3. high — X1.4 checker cannot fail on nonexistent-doc checkpoint, unresolvable fetch ref, or missing tool_outputs; `missing_ref_ok` unused.
4. high — X1.9 arm names mismatch plan of record (`mask-no-fetch`/`bounded-fetch` vs `masking-no-fetch`/`bounded-context-fetch`).
5. high — X1.10 1024 fetch budget unprovenanced and unstamped.
6. high — X1.2 inline markers not via `make_ref`; missing revision emits `@rNone`.
7. high — X1.8 tests assert fabricated empty fetch and char==token accounting.
8. medium — X1.6 `mask_output` recomputed on every access (tokenizer+sha256+_BODIES write).
9. medium — X1.7 `tool_call_id` emitted null.
10. low — X1.11 mutation loop lacks count assertion.
11. low — X1.12 `_simulate` is model-free; not end-to-end proof.

## FALSE (closed/not present in current bytes)

- X1.5: no `turn` rebind in the masked-entries loop; `turn_user(t, turn)` uses the turn captured at build entry.