# LMC — live-meas record correction (VLIVE → LIVE-MEAS)

**Objective (single).** Apply verifier `VLIVE`'s correction set to the LIVE-MEAS record. **Record repair
only**: 0 live requests, no `.occamy.lock`, no re-analysis, no new measurement. VLIVE's verdict is `pass` —
the numbers reproduce; only the *card-level words* overreached.

**Inputs.**
- `orchestration/handoffs/VLIVE.json`, `orchestration/units/VLIVE.md` (checks 2/5/6/7 + `overstated`,
  `not_reproduced`, `corrections`).
- `orchestration/handoffs/LIVE-MEAS.json`, `orchestration/units/LIVE-MEAS.md`.
- `experiments/context-cache/cells/LIVE-MEAS/{report.md,analysis.json,rows.jsonl}` (sha `6150e534…119b65`),
  read only.

**Corrections to apply (before → after).** C1 "A overtakes R after ~40 turns" → epoch-1 only; e2/e3 parity.
C2 "1.700x confirmed" → "consistent with 1.700x within 0.3–4.0 %", and the 80-turn headline is 1.30x.
C3 "prompt + cached identical in epochs 2–3" → only `cached` is identical; prompts are not (e2 spread 9 tok
at t10, 19 at t17). C4 "post-fold lag does not worsen" → holds for R and F only; A rises 384→896.
C5 "81 unexplained *ambient* misses" → *unattributed*, 54/81 within 2 turns of a fold. C6 manuscript-safety
sentence + note that 3 E4 residue-0 rows are flagged, two of them inside the 912-row E3 population.

**Rules.** Additive only: originals retained verbatim (`superseded_text` in the handoff; the corrected
sentences stay in place in the `.md`), plus `verifier_corrections`
(claim / as_written / corrected_to / verifier / applied) and a `## Corrections (VLIVE, applied by LMC)`
section at the top of `units/LIVE-MEAS.md`. `handoffs/LIVE-MEAS.json` keeps its 7 contracted keys (plus
`assumptions`) and its 960-row / 1.2988 / 113,166 = 5,081 + 108,085 data untouched; written temp → parse →
key check → `mv`.

**Bound.** ≤10 tool calls, ≤10 min. **Write paths.** `orchestration/units/LMC.md`,
`orchestration/handoffs/LMC.json`, `orchestration/units/LIVE-MEAS.md`, `orchestration/handoffs/LIVE-MEAS.json`.
No `cells/LIVE-MEAS/*`, no `src/`, no `tests/`, no `VERDICTS.md`, no `git`.

## Result (done — 6/6 corrections applied, 0 requests, 0 data changes)

All six re-derived from `rows.jsonl` / `analysis.json` offline before writing: pooled R/A **1.2988**;
t1–40 **1.7046 / 1.7682 / 1.7195**; t41–80 **0.9508 / 1.0296 / 1.0561**; F/A **1.0661**; 960 rows, 80 per
(epoch, arm); e2 prompts 5347/5354/5355/5356 at t10 with cached 4864 in all four arms; lag R 1152→448,
F 896→224, A 384→896; law 308 one-body / 81 unexplained of 912 with 54/81 within 2 turns of a fold.

`units/LIVE-MEAS.md` gains the corrections section at the top (original Result section byte-unchanged) and
`handoffs/LIVE-MEAS.json` gains `verifier_corrections` (6 entries), `superseded_text`,
`manuscript_safe_sentence`; its 7 contracted keys and every datum are unchanged. Handoff:
`orchestration/handoffs/LMC.json`.
