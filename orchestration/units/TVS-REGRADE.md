# UNIT `TVS-REGRADE`

**Card:** task-board tag `automated`. Turn the second headline metric from one data point into a table, and quantify the duplicate-row defect. **OFFLINE: zero inference requests, zero network.**

## Objective

1. Run `grade_v5.py` (judge sha256 `6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`) offline over the 8 long-run rows files that had no `grade_v5` output, writing each as a **new** `measure/cell-<…>-<stamp>.grade-v5.json`; never edit an existing grade file or any rows file.
2. Recompute TVS for all 23 declared run/arm pairs → `measure/TVS.json` + `docs/TVS-RESULTS.md`, reporting per pair arm · grid · tokens to first `grade_v5` pass · pass turn · cached share · `not_produced`+reason.
3. Measure the duplicate-row defect across **all 14** rows files against a rule defined before counting; give per-file raw vs de-duplicated counts, ledger impact, latency `n` impact, and a cause verdict. Publish in `measure/DUPLICATE-ROWS.md`; edit no ledger/latency report.

## Hard bound

≤32 tool calls, **0 inference requests**, ≤8 grade runs. `docs/TVS.md` frozen; judge/fixture/definition unchanged; `not_produced` an acceptable outcome; no fabricated denominator.

## Declared write paths (exactly)

`experiments/ptr-engine/measure/*.grade-v5.json` (new only) · `experiments/ptr-engine/measure/TVS.json` · `docs/TVS-RESULTS.md` · `experiments/ptr-engine/measure/DUPLICATE-ROWS.md` · `orchestration/units/TVS-REGRADE.md` · `orchestration/handoffs/TVS-REGRADE.json` · `orchestration/journals/TVS-REGRADE.jsonl`

## Decisions taken (recorded, since no human is present)

| decision | why |
|---|---|
| fixture `LR-01.v5.json` for all 8 gradings | it is the fixture the one pre-existing `grade_v5` output used, so all 23 pairs share one declared space (`cp.0.t12`, `cp.1.t24`, `cp.2.t46`). Using `LR-01.v6.json` (12 checkpoints) would change the declared space mid-metric and is a separate coverage card. |
| grade-file naming `cell-<gridtag>-<stamp>.grade-v5.json` | `grade_v5` emits **one file per rows file covering all arms**; a single-arm name would be false for the 7 multi-arm grids. `tokens_to_verified.py` keys these files by `rows_file`, so the mapping is unaffected. |
| `TVS.json` rewritten by the tool, not hand-edited | the tool is the artefact's author; its stale `pairs_not_produced_why` template string is disclosed in `docs/TVS-RESULTS.md` rather than patched. |
| duplicate rule reported as *decided* only where `content_sha256` + millisecond `ts` exist | on the 5 legacy-schema files the literal tuple over-merges demonstrably distinct requests (proof in `measure/DUPLICATE-ROWS.md` §2). |
| no ledger / latency report written | the card forbids it; corrected figures are proposed in `measure/DUPLICATE-ROWS.md` §3-§4 for a follow-up card. |

## Outcome

- 8/8 rows files graded, all offline, no exceptions, 8 grade runs used.
- TVS decided for **23/23** pairs, produced for **3/23**: 48,347 (v4/pointer-stable) · 50,847 (v4-tools/pointer-stable) · 111,994 (v6-tools/pointer-stable), all first pass `cp.0.t12` at turn 12.
- Duplicates: **30** decided excess rows (v6 11, v4-tools 17, v5-tools 2) → requests **1,101 → 1,071**; **G7 V4-TOOLS p95 n 68 → 51** falls below the n≥60 threshold; cause **writer bug** (one billed response written twice as `turn` + `tool-followup`), not a resumed-run artefact.
