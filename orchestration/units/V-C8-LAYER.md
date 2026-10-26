# V-C8-LAYER — transcription check of the C8-APPLY layer

**VERDICT: TRANSCRIPTION FAITHFUL.** No mismatch. Repaired nothing.
Block: `experiments/ptr-engine/RECORD.md:130`, from `**C8 re-derived independently 2026-10-26 (C8-REDERIVE).**` to end of line.

| claim | source | verdict |
|---|---|---|
| fit 387, all `role=measure`, = `meas()` | FIT-GAP-V2.md:9,11,14 | MATCH |
| 304 cached / 83 null | FIT-GAP-V2.md:12-13 | MATCH |
| `{0:160, −64:51, −128:6, −192:2, −1056:69, −2112:16}` | FIT-GAP-V2.md:21-26 | MATCH, row for row |
| no positive residual, `outlier 0` | FIT-GAP-V2.md:29,59 | MATCH |
| 144 non-zero, all grid multiples, all negative | FIT-GAP-V2.md:33,40-42 | MATCH |
| 85 vLLM / 59 SGLang | 78+7=85, :35-37 | MATCH (aggregated, correct) |
| 83 null = SGLang h0, `uncached==prompt` 83/83 | FIT-GAP-V2.md:47-48 | MATCH |
| `law_gap 387` count not classification; 0 inside fit | FIT-GAP-V2.md:60,66 | MATCH |
| `defect 321` withdrawn / not reproducible | FIT-GAP-V2.md:61,66; JSON hint | MATCH |
| 14 named predicates; no 708-of-774 partition | FIT-GAP-V2.md:61,67 | MATCH |
| 774 denominator | FIT-GAP-V2.md:3 | MATCH |
| date `2026-10-26` | absent from both sources | NOT-IN-SOURCE |

Independent recomputation from `experiments/miss-law/rows.jsonl` (grid 64 sglang / 1056 vllm, `L_app` non-null = fit):
rows 774 · fit 387, roles `{'measure': 387}` · cached 304 / null 83 · residual map identical to the layer ·
non-zero 144 = 85 vllm + 59 sglang · positive 0 · `{res % grid} == {0}` · nulls all sglang, `uncached==prompt` 83/83 ·
`meas()` complement 387 over 774 and 0 over the fit set.

Scope: nothing claimed wider than source. Two narrowings only (AND-axis list omits `B_measured`, `H_res`,
`L_res==residue`, `uncached==prompt`; the 83 rows' phase split 50/22/11 dropped). The 2026-10-26 date is the sole
unverifiable item — plausible under UTC (clock 2026-10-25T22:40‑05:00) but dated by neither file.

Blocker: none. 4 tool calls of 14.
