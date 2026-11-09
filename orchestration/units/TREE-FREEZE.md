# UNIT `TREE-FREEZE`

**Purpose.** Make an audit race-proof: record the digests it saw and re-check them instead
of failing on drift. Offline, zero requests.

**Why.** Three audits of this batch were invalidated by a moving tree: `V-GATE-OPERAND`
pinned `cell.py 6b0ca83a…` while the file moved twice during its own check; `VERDICT-DISPUTE`
had to pin and bracket a 1313→1334-line concurrent rewrite; `SEAM-TEST-RED` settled
`FAIL exit-1` from another card's in-flight red. The defect is not that files move (concurrent
cards are the design), but that a claim is recorded against unnamed bytes and a settle-time
failure is reported as the claimant's fault.

**Hard bound.** ≤24 tool calls, 0 requests. `/tmp` copies for the moving-tree demos.

**Write paths (declared).** `experiments/ptr-engine/tools/tree_freeze.py`,
`experiments/ptr-engine/longrun/exit_codes.py` (code 13 only),
`experiments/ptr-engine/longrun/tests/test_tree_freeze.py`,
`experiments/ptr-engine/longrun/tests/test_exit_codes.py`,
`experiments/ptr-engine/measure/TREE-FREEZE.json`, `docs/TREE-FREEZE.md`,
`orchestration/units/TREE-FREEZE.md`, `orchestration/handoffs/TREE-FREEZE.json`,
`orchestration/journals/TREE-FREEZE.jsonl`.

**Out-of-list addition (recorded).** `docs/EXIT-CODES.md`: one row for code 13 plus one
sentence. The live guard `DocsTableTests.test_doc_table_matches_the_module_exactly` asserts
that the human table equals `EXIT_TABLE`; declaring 13 without the row would have left a red
guard, and weakening that guard would have been the larger defect. No hazard file
(`cell.py`, `run_longrun.py`, any grader) was touched.

**Acceptance.** freeze/verify/--wrap implemented; exit 13 added to `EXIT_TABLE` with an
owner (`EXTERNAL_CODES`) and the source-scan test still balanced both ways; red→green
classifier (moved → 13, clean → 0 `pass`); `failed` and `failed_and_moved` distinguishable;
docs rule paragraph. Evidence: `orchestration/handoffs/TREE-FREEZE.json`,
`experiments/ptr-engine/measure/TREE-FREEZE.json`.

**Status: done.**
