# E2C — `e2-record-correction`

**Status:** done — record repair. No re-measurement, no new experiment, 0 live requests, no lock.

## Purpose (one)

Repair **E2's record** so no later unit cites a statement that two independent verifiers ruled
overstated. **Record repair, not re-measurement.** VE24 (29 tool calls) and VE2 (20) reached the
*same* ruling independently, so nothing here is a contested claim: E2C applies their findings.

## Inputs read

`orchestration/handoffs/VE24.json`, `orchestration/units/VE24.md`, `orchestration/handoffs/VE2.json`,
`orchestration/units/VE2.md`, `orchestration/handoffs/E2.json`, `orchestration/units/E2.md`,
`experiments/context-cache/cells/E2/` (`rows.jsonl`, `rows_f2.jsonl`, `analysis.json`,
`analysis_f2.json`). Cell files were **read only** — `cells/E2/*`, `src/`, `tests/`, `VERDICTS.md`
and other units' files untouched; no `git`.

## Corrections applied (additive only)

| # | claim | ruling | verifier |
|---|---|---|---|
| 1 | F's t36–40 advantage "tracks cache-epoch warmth, not the fork marker" | OVERSTATED → *a warm epoch is necessary; the arm still contributes (an interaction) this design does not isolate* (E2F confounds warmth with missing t1–29 history, no cold-R control, one seed; U15 ran both arms warm from t1 and reproduces) | VE24 c4, VE2 5 |
| 2 | `E2.md` original :100 "E2F … reproduced **R's** depth" | FALSE / NOT REPRODUCED — E2F 768/768/2048 vs R 896/896/1792; magnitude only | VE24 c4b, VE2 5 |
| 3 | pre-fold lag "1–2"; F2 "lag 1" | CORRECTED — t10 is turn-lag 3 (cached 3,840 = floor64(prompt_7)); F2 t36 2048 is also floor64(prompt_3)/floor64(prompt_18), so lag 1 is non-unique | VE24 c2, VE2 2 |
| 4 | "14/16 post-fold", "0 % summary node" | SCOPED — 17/21 across all post-fold steady turns; 0 % summary is structural, not measured | VE2 corrections |
| 5 | re-prefill value list | INCOMPLETE — restore 384 (t11) and 1024 (t10); also 1152 (t19); 8,448 only on folds | VE2 corrections |
| 6 | `residual == 0.0` as evidence | ALGEBRAIC IDENTITY, cannot go red; evidence is 37/37 prefix-identical + 33/37 floor64 (red→green: plain `prompt_j` → 0/37) | VE24 c1, VE2 1/4 |

## Where the originals live

`E2.md` keeps every original verbatim under a top `## Corrections (VE24 + VE2, applied by E2C)`
section that quotes each original next to its corrected form. `E2.json` keeps every author value
untouched, adds `verifier_corrections` (6 entries, each `applied:true`), `superseded_text` (the
verbatim originals of the corrected strings, keyed by field / `E2.md:<original line>`), and
corrected **companions** (`evidence.F_vs_R_component_corrected`, `evidence.residual_is_identity`,
`evidence.attribution_scope`, `evidence.boundary_test_lag_scope`, `evidence.summary_test_scope`,
`evidence.re_prefill_values_full`, `next_unit_hint_corrected`). Original keys, original order and
the 7 contracted keys are intact.

## Facts left unchanged (re-checked offline from rows, not re-measured)

- decomposition **1,658.9375 = 456.6875 + 30.25 + 1,172.0** (residual arithmetic closes; identity, see #6)
- **37/37** prefix-identical steady turns, 0 changed message indices; **33/37** `cached == 64*floor(prompt_j/64)`
- **81/81** `re_prefill % 64 == 0`; one `head_sha` over all 40 R turns
- summary hash changes only at t18 (`11b8e9bc…`) and t35 (`a1273293…`)
- exact U15 reproduction: R t19–23 768/768/1920/1920/2816, t36–40 896/896/1792/1792/2688; F2 t35–38 768/2048/2048/2944 (`uncached` −1 / −3 per turn from salts)

## Bound honoured

8 tool calls of 12; ~6 min of 10; **0 live requests**; `.occamy.lock` never acquired; writes only to
the four declared paths; `E2.json` written temp → parse+keys validated → `os.replace`.
