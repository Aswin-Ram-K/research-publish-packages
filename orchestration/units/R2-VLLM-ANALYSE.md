# Unit R2-VLLM-ANALYSE

**Purpose:** run the analyse phase of the repaired R2-VLLM 418-row cell under `--force`, confirm the written
`analysis.json` is bound to the rows on disk, then produce a verification-grade dossier derived independently
from `rows.jsonl` (not from `analysis.json`), plus a strict report.

**Mode:** offline. 0 model requests, no ssh, no docker, `.occamy.lock` not taken (already `released_utc
2026-10-24T03:27:40Z`).

**Hard bound:** 20 tool calls.

**Write paths:**
`experiments/context-cache/cells/R2-VLLM/analysis.json`, `logs/analyse-console.log`, `logs/verify-dossier.py`,
`logs/verify-dossier.json`; `state/logs/R2-VLLM-rerun-report.md`; `orchestration/units/R2-VLLM-ANALYSE.md`,
`orchestration/handoffs/R2-VLLM-ANALYSE.json`.

**Kill condition:** if `--phase analyse` fails, capture the error verbatim and report `partial`; do not edit the
analyser.

**Result:** see `orchestration/handoffs/R2-VLLM-ANALYSE.json`.
