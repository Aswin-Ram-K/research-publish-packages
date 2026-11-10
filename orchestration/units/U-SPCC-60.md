# U-SPCC-60 — record U-SPCC-58's confabulation classification

**Status:** DONE. Documentation only: 0 endpoint requests, 0 model calls, no code or prompt
change.

## What was recorded

`U-SPCC-58` classified the 10 wrong answers in the `masking-no-fetch` arm of
`experiments/ptr-engine/measure/rows-e1-indexfix-2026-11-10.jsonl` (index fix `b38db8a`):
**9 pure confabulation, 1 cross-fact confusion, 0 index leakage**. The answered values occur
in no index line and no fixture body. The masking arm's **8/48 retention score is unchanged
and fair**; the **0→10 wrong count is a prompt-design artefact** of showing the arm an index
it cannot address, and must not be read as an arm property.

All 100 masking prompts were rebuilt through `Planner.build` + `checkpoint_prompt` with
**100/100 `sha256` match**, so the reconstruction is exact.

## The 10-row table

| turn | checkpoint | expected | answered | class | source |
|---:|---|---:|---:|---|---|
| 6 | `cp.TX-03.f01.d5` | 3001 | 4000 | pure confabulation | nowhere |
| 7 | `cp.TX-03.f01.d6` | 3002 | 5000 | pure confabulation | nowhere |
| 9 | `cp.TX-03.f01.d8` | 3003 | 3103 | cross-fact confusion | `doc-fact-02` body in L3, delivered T8 |
| 13 | `cp.TX-03.f02.d5` | 3101 | 4100 | pure confabulation | nowhere |
| 14 | `cp.TX-03.f02.d6` | 3102 | 4103 | pure confabulation | nowhere |
| 22 | `cp.TX-03.f03.d5` | 3201 | 4200 | pure confabulation | nowhere |
| 23 | `cp.TX-03.f03.d6` | 3202 | 4203 | pure confabulation | nowhere |
| 25 | `cp.TX-03.f03.d8` | 3203 | 4203 | pure confabulation | self-echo of its own T23 answer |
| 29 | `cp.TX-03.f04.d5` | 3301 | 4300 | pure confabulation | nowhere |
| 30 | `cp.TX-03.f04.d6` | 3302 | 4303 | pure confabulation | nowhere |

Counts: **9 pure confabulation, 1 cross-fact confusion, 0 index leakage**.

## Writes

- `experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` — one 7-column row
  (column count unchanged: 7-column rows 20 → 21).
- `docs/STATE.md`, `journal/2026-11-10.md`, `orchestration/STATUS.md` — the table and counts.
- `orchestration/units/U-SPCC-60.md`, `orchestration/handoffs/U-SPCC-60.json`.

## Checks

- `python3 tools/doc_check.py` → `OK docs clean`, exit 0.
- Ledger column count before/after: `15 10 / 7 3 / 20 7` → `15 10 / 7 3 / 21 7`.
