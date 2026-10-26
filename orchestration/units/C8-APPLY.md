# C8-APPLY — apply C8-REDERIVE to RECORD.md

## Purpose (one)
Append the settled C8-REDERIVE result to the existing `**C8 — residual detail` line
(line 130) of `experiments/ptr-engine/RECORD.md`. One line, one append, nothing else.

## Bound
12 tool calls; used 5. Stop condition: any invariant failure -> restore, report `failed`.

## Inputs (settled upstream, not re-derived here)
`experiments/miss-law/FIT-GAP-V2.md`, `orchestration/handoffs/C8-REDERIVE.json`.

## What was appended (single line, one leading space, after existing final char)
C8 re-derived independently 2026-10-26 (C8-REDERIVE): fit set 387 = `meas()`; 304 report
`cached_tokens`, 83 do not; residual over the 304 `{0:160, −64:51, −128:6, −192:2,
−1056:69, −2112:16}`, no positive residual -> `outlier 0` reproduces; 144 non-zero
deviations all whole-grid multiples, all negative (85 vLLM / 59 SGLang); 83 nulls are
SGLang `h0` with `uncached == prompt` 83/83 (missing no-hit term); `law_gap 387` is a
count, not a classification; **`defect 321` WITHDRAWN**.

## Evidence
- backup sha256 `e009c146…f20f`, 150 lines, 40310 bytes
- line 130: 4081 -> 5224 chars; new sha256 `b958fbe7…134e`
- prefix (129 lines) sha `b17570ed…ce0` identical before/after
- suffix (from 131) sha `f210c8cb…e81` identical before/after
- `wc -l` 150 -> 150; sentinels 5/1/1/1/1/3 unchanged; new marker count = 1
- `defect 321` 3 -> 4 (appended withdrawal sentence only)

## Result
done. No other file touched; no reformat; no re-derivation.
