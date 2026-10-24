# V-R2-VLLM-RERUN — verifier card (persisted)

**Role:** independent verifier of the `R2-VLLM-FIX` card (repair two proven instrument defects, re-run both
vLLM cells). Not an author of anything verified. Parent session `session-6c18de17-5945-4691-bb4f-7d769c5ad40a`.

**Mode:** offline only — 0 model requests, no ssh, no docker, no lock. The cell source, `rows.jsonl`,
`analysis.json` and `discarded-r1/` were not edited (live `pmu16_cell.py` sha256 verified unchanged
`2ae22c6c…635d0c9d` before/after every mutation run).

**Bound:** 20 tool calls.

**Write paths:**
- `orchestration/units/V-R2-VLLM-RERUN.md` (this file)
- `orchestration/handoffs/V-R2-VLLM-RERUN.json`
- transient scratch only inside the workspace (`.verifier-tmp/`, `.verifier-scratch/`), created and removed in the same command

**Verified units:** `R2-VLLM-REPAIR`, `R2-VLLM-REPAIR2`, `R2-VLLM-ANALYSE` and the row/log artefacts of the
live rerun they describe.

**Checks:** 9 (instrument flag/usage accounting · arm identity from bytes · cold pass · repeat pass ·
independent re-derivation of the per-(config,arm) table · A1 zero-pattern characterisation ·
containment/safety · red→green on a guard · four required operator facts).

**Result:** see `orchestration/handoffs/V-R2-VLLM-RERUN.json`.
