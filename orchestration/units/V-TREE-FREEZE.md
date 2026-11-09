# V-TREE-FREEZE — independent attack on `tools/tree_freeze.py`

**Purpose.** I did not write the tool. I attack it offline (zero inference requests, no network),
in the repo and `/tmp/vtreefreeze`, and never edit the audited files.

**Target.** `experiments/ptr-engine/tools/tree_freeze.py` (325 lines) plus its claims in
`orchestration/handoffs/TREE-FREEZE.json`, `docs/TREE-FREEZE.md`, `experiments/ptr-engine/measure/TREE-FREEZE.json`,
and the exit-code table `experiments/ptr-engine/longrun/exit_codes.py` (13 = `tree-moved`, declared
`EXTERNAL_CODES`).

**Attacks.** 1 real move · 2 bytes-not-mtime (touch, then one-byte edit with size+mtime_ns restored) ·
3 phantom delete (and delete *during* `--wrap`) · 4 exit 13 vs genuine failure + `rc != 0` caller ·
5 all four `--wrap` verdicts · 6 exit-code table / scan-test red→green · 7 scope honesty.
Each attack run twice.

**Hard bound.** 24 tool calls. **Write paths.** this card; `orchestration/handoffs/V-TREE-FREEZE.json`;
`orchestration/journals/V-TREE-FREEZE.log`; `experiments/ptr-engine/measure/TREE-FREEZE-ATTACK.json`;
`/tmp/vtreefreeze/**`. No edits to audited files; all mutations to `exit_codes.py`/`cell.py` were made on
copies under `/tmp/vtreefreeze/mut`.

**Deliverable.** verdict handoff + attack measurement JSON, plus one recorded verdict row.
