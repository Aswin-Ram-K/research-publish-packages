# LAUNCH-PACKAGE-AUDIT

**Purpose.** Read the six launch artefacts together and say whether the package a launcher would read is
self-consistent: pool, per-cell budget, price, remaining headroom, canary N, harness pin, ledger baseline,
and the per-cell command. Read-only; offline; no file audited is edited.

**Bound.** 20 tool calls (used 11), zero requests, zero network, never asks the user.

**Write paths.** `docs/LAUNCH-PACKAGE.md` · `experiments/ptr-engine/measure/LAUNCH-PACKAGE.json` ·
`orchestration/units/LAUNCH-PACKAGE-AUDIT.md` · `orchestration/handoffs/LAUNCH-PACKAGE-AUDIT.json` ·
`orchestration/journals/LAUNCH-PACKAGE-AUDIT.jsonl`.

**Result.** `ready_to_launch: false`. Pin MOVED (`1f7c6791…` → `2b4d4808…`, `run_longrun.py` written at
19:04:32Z). Price 1,016 exists in card prose only. Canary N=5 still prescribed in two docs. GRID-SHAPE
still carries `--budget 67` and `--fetch-followup-allowance 24`.

**Deliverables.** go/no-go sheet + machine-readable package (see write paths).
