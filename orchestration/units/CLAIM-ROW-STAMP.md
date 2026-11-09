# CLAIM-ROW-STAMP

**Purpose.** Make the claim decision reach the ROWS: `run_longrun.py` gains
`--claim-mode` (claim_mode vocabulary, `plumbing` included), resolved ONCE by
`claim_mode.resolve_claim` and threaded on `cfg.claim`; `make_row` stamps `claim` and
`comparison_eligible` on every row literal it builds. `cell.py` threads its already
cached decision as `--claim-mode`. The stale `RED_GREEN` G3-silence anchor now targets
the new resolver.

**Bound.** <=22 tool calls, 0 requests. **Write paths.** run_longrun.py,
experiments/ptr-engine/longrun/tests/test_claim_wiring.py, experiments/ptr-engine/longrun/tests/test_claim_rows.py, experiments/ptr-engine/longrun/tests/test_cell_gates.py,
experiments/ptr-engine/longrun/tests/test_claim_mode.py, docs/GATE-CHAIN.md, unit/handoff/journal.

**Evidence.** experiments/ptr-engine/longrun/tests/test_claim_rows.py (row-level smoke/H2/failure/omitted/red-green),
experiments/ptr-engine/longrun/tests/test_cell_gates.py (new anchor), docs/GATE-CHAIN.md section "Claim stamp on every
per-turn row".
