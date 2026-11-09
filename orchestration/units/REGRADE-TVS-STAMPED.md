# UNIT REGRADE-TVS-STAMPED

**Purpose.** Give the three headline tvs figures (48,347 / 50,847 / 111,994, all `cp.0.t12`, turn 12) a grader stamp by re-grading their rows with the CURRENT `grade_v5.py` into NEW documents, and report whether the numbers move.
**Bound.** 20 tool calls. Offline, zero requests. No `ask_user_question`.
**Write paths.** `experiments/ptr-engine/measure/cell-longrun-*.grade-v5-restamped.json`, `experiments/ptr-engine/measure/TVS-RESTAMPED.json`, `orchestration/units/REGRADE-TVS-STAMPED.md`, `orchestration/handoffs/REGRADE-TVS-STAMPED.json`, `orchestration/journals/REGRADE-TVS-STAMPED.jsonl`.

## Source pairs (rows -> grade document that produced the figure)

| grid | rows file (sha256) | old grade doc (sha256) | old tvs |
|---|---|---|---|
| rows-longrun-v4-2026-10-26 | `measure/rows-longrun-v4-2026-10-26.jsonl` `999f298d…c28e` | `measure/cell-longrun-v4-20261026T1556Z.grade-v5.json` `0257b3fa…eee1` | 48,347 |
| rows-longrun-v4-tools-2026-10-26 | `measure/rows-longrun-v4-tools-2026-10-26.jsonl` `f11391aa…e77f` | `measure/cell-longrun-v4-tools-20261026T1556Z.grade-v5.json` `32b862ac…2229` | 50,847 |
| rows-longrun-v6-tools | `measure/rows-longrun-v6-tools.jsonl` `1e78d75f…531e` | `measure/cell-pointer-stable-20261026T145722Z.grade-v5.json` `e4eaef24…b6fe` | 111,994 |

All three old documents are unstamped (`grader_sha256`, `grader_version`, `rows_sha256` all absent) — `grader_identity` reports `source="derived"`, `requires="regrade_result"`.

## Reproduction from the OLD documents (before any change)

`tokens_to_verified.py --rows <rows> --grade <old doc> --arm pointer-stable` returned 48347 / 50847 / 111994, `pass_turns=["cp.0.t12"]`, `reason=null` for all three — byte-identical to `TVS.json`. The old numbers reproduce, so this is a stamping gap, not a different defect.

## Re-grade (current grader, NEW documents)

`longrun/grade_v5.py --rows <rows> --fixture longrun/tasks-v5/runtime-v5/LR-01.v5.json --out measure/cell-longrun-<grid>.grade-v5-restamped.json`

Each new document carries `grader_sha256=056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772`, `grader_version=5.1`, `rows_sha256=<that grid's rows sha>`.

| grid | old tvs -> new tvs | cp.0.t12 old -> new | decidable old -> new | grader_sha256 |
|---|---|---|---|---|
| v4 | 48,347 -> **48,347** | pass/num_equal -> **pass/num_equal** | true -> true | 056eb605… |
| v4-tools | 50,847 -> **50,847** | pass/num_equal -> **pass/num_equal** | true -> true | 056eb605… |
| v6-tools | 111,994 -> **111,994** | pass/num_equal -> **pass/num_equal** | true -> true | 056eb605… |

## Result: nothing moved

The T3 non-answer grading change alters `fail` vs `undecidable` for NON-ANSWERS. These three cells answer (`asserted=64 == expected=64`, `num_equal`), so the change never reaches them: the checkpoint stays `pass`, the window still ends at turn 12, and the token bytes are unchanged. No figure is withdrawn (the claims are true) and none is superseded (the numbers are identical) — `measure/WITHDRAWN.json` correctly gains no entry, and it is outside this unit's write paths anyway.

The tvs definition survives: no grid collapses to `null`/`no_verified_success`. All three headline figures exist, and each is now traceable to BOTH its bytes (`rows_sha256`) and its grader (`grader_sha256` + version 5.1).

## docs/TVS.md lines that now need editing (report only — file untouched)

- `docs/TVS.md:6` — stale grader pin `6893d559…3077`; the current grader is `056eb605…2672`.
Other figure-bearing lines (`:48`, `:53`, `:55`, `:58`) still describe `cp.0.t12` as pass/num_equal and remain true; they only lack the new `grader_sha256` provenance and could cite `measure/TVS-RESTAMPED.json`.

## Not touched

`cell.py`, `run_longrun.py`, `longrun/grade_v5.py`, `tools/tokens_to_verified.py`, every `rows-*.jsonl`, every original grade document, `PARM-1*`, `GRID-*.json`, `docs/TVS.md`, `measure/WITHDRAWN.json`.
