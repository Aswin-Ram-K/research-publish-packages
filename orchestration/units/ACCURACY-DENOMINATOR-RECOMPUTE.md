# UNIT `ACCURACY-DENOMINATOR-RECOMPUTE`

**Status:** done · **Bound:** 26 calls (used 22) · **Inference requests:** 0 (offline) ·
**Historical measurement files edited:** none (new files only).

## Purpose

Recompute every analyser-derived accuracy block under the shared denominator rule and publish the delta,
**adding** new records rather than editing published ones.

- Rule owner: `grade_v5.decidable_population(cells)` — `experiments/ptr-engine/longrun/grade_v5.py:752-789`
  (`decidable = pass + fail`; `fail` includes `reason == "turn_missing"`; `text`/`undecidable` outside).
- Consumer: `analyze_stats.accuracy_from_grade` — `experiments/ptr-engine/longrun/analyze_stats.py:714-757`
  (now a caller, no private copy). Neither file was modified by this unit.

## Classification discriminator

| class | test |
|---|---|
| `private_rule` | reported denominator `== pass + fail - missing`, `missing > 0` |
| `row_population` | denominator is the run's row count and no `missing` field → `unclassifiable_by_private_rule_discriminator` |
| `shared_rule` | denominator `== pass + fail`, `missing` beside it |
| `no_missing` | `missing == 0`, rules agree |

## Findings

- **REC-01** `measure/regrade-det.json` `per_run_arm` — `private_rule`; **10 of 23** pairs affected;
  denominators short by exactly `len(missing)`; aggregate `5/43 → 5/79` (36 turn-missing charged).
  Examples: `longrun-2026-10-26/pointer-stable 0/1 → 0/4`,
  `longrun-2026-10-26-fix/transcript-grow 0/1 → 0/4`, `longrun-2026-10-26-policy/transcript-grow 0/2 → 0/4`,
  three pairs read `0/0` and now read `0/4`.
- **REC-02..04** `measure/cell-*.analysis.json` (+ `.md`/`.json` twins) — `unclassifiable` by the private-rule
  hint (row population): `55/64`, `55/64`, `0/0 over 72 rows` → checkpoint `3/3`, `3/3`, `1/3`.
- **25 `cell-*.grade-v5.json` arms blocks** — 24 already `shared_rule`; 1 is a counter-field gap
  (`cell-pointer-stable…grade-v5.json` omits `failed`/`missing` but its 3 cells are 1 pass + 2 fail).
- **`5/43` does not move** (36 missing already inside the 38 fails of 92 declared cells).
  **`3/25` does not move** (grade_v5 arms already charge turn_missing). The analyser's `5/8` was never persisted.
- **14 doc lines need correction** listed, not rewritten: `measure/cell-*.md:36` ×3,
  `cell-pointer-stable…md:41`, `measure/REGRADE-DET.md:76,78-86` (plus the rule sentence at `:66-67`).

## Deliverables

`experiments/ptr-engine/measure/ACCURACY-RECOMPUTED.json` ·
`experiments/ptr-engine/measure/ACCURACY-RECOMPUTED.md` ·
`experiments/ptr-engine/measure/REC-01-recomputed.json` … `REC-04-recomputed.json` ·
`orchestration/journals/ACCURACY-DENOMINATOR-RECOMPUTE.jsonl` ·
`orchestration/handoffs/ACCURACY-DENOMINATOR-RECOMPUTE.json`

## Reproduction / verdict command

```
python3 -c "import json;d=json.load(open('experiments/ptr-engine/measure/ACCURACY-RECOMPUTED.json'));open('/tmp/gen.py','w').write(d['generator'])"
python3 /tmp/gen.py --outdir /tmp/regen
diff /tmp/regen/ACCURACY-RECOMPUTED.json experiments/ptr-engine/measure/ACCURACY-RECOMPUTED.json
```

Empty diff → the consolidated record regenerates byte-identically from the historical sources.
