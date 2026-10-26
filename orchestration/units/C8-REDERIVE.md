# C8-REDERIVE — re-derive contradiction C8 from the row file

**Status:** done · **Bound:** 18 tool calls (used 10) · **Mode:** automated, offline, read-only on the repo except three declared paths.

## Purpose

C8's recorded classification (`outlier 0 · law_gap 387 · defect 321`) had lost its provenance: the artefact
`orchestration/units/C8-FIT-GAP.md` was rewritten 40 → 13 lines by another session and now reads
`law_gap 0 / defect 21`. A classification nobody can re-derive is a claim, not evidence. This unit derives a
fresh one from `experiments/miss-law/rows.jsonl` with its own code and states what of the old one survives.

## Method

No verdict read first: neither `C8-FIT-GAP.md` nor `experiments/ptr-engine/RECORD.md` was opened before
deriving. Single source of truth: the 774-row `rows.jsonl`. Grid from `server` prefix (`sglang` 64, `vllm`
1056); `residual = cached_tokens − prompt_tokens//grid*grid`; fit set = rows with non-null `L_app`.
Exact python in `orchestration/handoffs/C8-REDERIVE.json` → `evidence.commands` (18 lines).

## Results

- Fit set **387**, all `role == measure`; 304 carry `cached_tokens`, 83 do not (`sglang` only, h0 cells).
- Residuals: 0 ×160, −64 ×51, −128 ×6, −192 ×2, −1056 ×69, −2112 ×16. **Never positive.**
- 144 non-zero residuals = 78 `vllm`/residue + 59 `sglang`/residue + 7 `vllm`/B; every one a whole grid multiple (`residual % grid == 0` for all 144).
- Null-`cached` rows carry `uncached == prompt_tokens` (83/83); the plain law `uncached = residue + L_app` holds for **0** of 387 and violates for 387 — no no-hit term.
- Integrity: 0 errors; 381 duplicate `(server, cell, rep)` keys are prime↔measure pairs (3 remain once `role` joins the key); 2 rows sit below the grid size (`vllm Bprobe-400`).
- Verdict: `outlier 0` REPRODUCED · `law_gap 387` REPRODUCED as a count but it is the non-`meas()` population (0 inside the fit set) · `defect 321` **NOT REPRODUCIBLE** — no predicate, single or 2-way over 24 conditions, yields it.

## Deliverable

`experiments/miss-law/FIT-GAP-V2.md` (67 lines). RECORD.md deliberately untouched — applying this is a separate unit.
