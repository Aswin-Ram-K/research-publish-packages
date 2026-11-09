# Unit LEDGER-GRID-BASELINE

**Purpose (one):** freeze the **pre-grid** request-ledger reading into a dated, digested artefact, so `RUN-A*`'s spend is measured as a delta against a pinned baseline rather than a re-read of a moved file.

**Hard bound:** 20 tool calls · offline · zero inference requests (no `:8012`/`:8014`) · no `ask_user_question`.

**Write paths (exactly):**
`experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json` · `docs/LEDGER-GRID-BASELINE.md` · `experiments/ptr-engine/tools/ledger_delta.py` · `tests/test_ledger_delta.py` · `orchestration/units/LEDGER-GRID-BASELINE.md` · `orchestration/handoffs/LEDGER-GRID-BASELINE.json` · `orchestration/journals/LEDGER-GRID-BASELINE.jsonl`

**Do not modify:** `REQUEST-LEDGER.json`, any rows file, any grade file, `cell.py`, `run_longrun.py`, `PARM-1*`, the grid card. This unit freezes a reading; it does not re-derive the ledger.

**Deliverables**

1. `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json` — spent/requests_raw 1101, remaining_raw 3219, dedup 1071 labelled diagnostic (`deducted: false`), 14 rows files each with sha256 + UTC/local mtime + row count, label `pre_grid`, `how_to_compute_delta`, expected tranche-1 block.
2. `docs/LEDGER-GRID-BASELINE.md` — values, shas, capture instant (UTC + local), exact command, delta block, expectation, red→green.
3. `experiments/ptr-engine/tools/ledger_delta.py` — exit 0 when the arithmetic closes, exit 1 with a named `discrepancy`/`deficit` when it does not.
4. `tests/test_ledger_delta.py` — 5 tests, including the red edited-baseline case (exit 1).

**Verification**

- green: `.venv/bin/python experiments/ptr-engine/tools/ledger_delta.py --baseline experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json` → `delta 0 · deficit none · verdict OK`, **exit 0**
- red: baseline `budget.spent` 1101 → 1106 → `spent_before 1106 · delta -5 · deficit 5 · FAIL`, **exit 1**
- `.venv/bin/python -m pytest tests/test_ledger_delta.py -q` → **5 passed**
- recomputation: 14 rows files re-counted and re-hashed, 1101 rows = ledger total, all shas match the artefact → **agreement, no finding**

**Kill condition honoured:** the artefact's numbers stayed the baseline; the 1,071 was recorded and never deducted.
