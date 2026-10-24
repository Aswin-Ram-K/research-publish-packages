# FIX-VXSTACK — repair cross-stack defects from V-XSTACK

**Unit:** FIX-VXSTACK · **Batch:** cross-stack repair · **Author:** delegated unit
**Date (UTC):** 2026-10-23 · **Bound:** <=60 tool calls; no live model requests; no engine restarts; no target repo writes
**Status:** done

## Objective

Repair the four defects reported by V-XSTACK:
- D1: TUNED claims `page_size 1 / no-grid`, while delivered replay rows follow the G3 64-token law.
- D2: 289/289 TUNED rows lack `stack`/`config_id`; analyzer silently accepts unattributable rows.
- D3: S1/S2/TUNED have no in-cell G0.
- D4: launch/restore record hygiene: missing `state/config/restore-diff.json`, tuned-restored sha mismatch, vLLM restore records store only `config_ok=true`.

## Declared write paths

- `orchestration/units/FIX-VXSTACK.md`
- `experiments/context-cache/cells/TUNED/win_tuned_analyze.py`
- `experiments/context-cache/cells/TUNED/rows.jsonl`
- `experiments/context-cache/cells/TUNED/run.json`
- `experiments/context-cache/cells/TUNED/analysis.json` (generated)
- `state/config/restore-diff.json`
- `state/config/tuned-restore-diff.json`
- `experiments/context-cache/cells/WIN-VLLM/logs/V1-restore.json`
- `experiments/context-cache/cells/WIN-VLLM/logs/V2-restore.json`
- `experiments/context-cache/cells/WIN-VLLM/logs/V3-restore.json`
- `experiments/context-cache/cells/WIN-VLLM/win_vllm_analyze.py`
- `papers/context-cache/GAPS.md`
- `orchestration/units/WIN-TUNED.md`
- `orchestration/handoffs/FIX-VXSTACK.json`

## Kill condition

Stop and report if a required write cannot be verified after the bounded attempts, or if editing a declared path would require modifying a target repository or running a live model request. Partial results are reported rather than stalling.
