# UNIT `RECORD-STOP-REASON`

**One purpose.** Make a stop explainable from the row alone: capture `finish_reason` (per
choice and the one that ended the stream), `max_tokens` as actually sent, a derived
`stop_reason` from a **closed vocabulary**, `truncated`, and the evidence a contentless stop
carries. Recording only — no verdict, grader, guard semantics or historical row changes.

**Why.** `STOP-REASON-AUDIT` (`10195e9e`): seven arm-checks `cap-exhausted` with content `""`,
`completion_tokens` 128 on all 99 empty rows, and no `finish_reason` / `truncated` /
`max_tokens` on the row — a cap stop and a refusal were indistinguishable.

**Bound:** ≤24 tool calls, zero inference requests, handoff `partial` within 4 calls, journal
first. **Met:** 22 calls, 0 requests.

**Write paths (exactly):**
`experiments/ptr-engine/longrun/client.py`,
`experiments/ptr-engine/longrun/run_longrun.py`,
`experiments/ptr-engine/longrun/tests/test_record_stop_reason.py`,
`docs/STOP-REASON.md`, `orchestration/units/RECORD-STOP-REASON.md`,
`orchestration/handoffs/RECORD-STOP-REASON.json`,
`orchestration/journals/RECORD-STOP-REASON.jsonl`.

**Not edited:** `cell.py`, `grade_v*.py`, `analyze_stats.py`, `matrix_audit.py`,
`det_verify.py`, `orchestration/handoffs/` (other than this unit's own), any historical row.

**Result:** done — see `orchestration/handoffs/RECORD-STOP-REASON.json` and
[`docs/STOP-REASON.md`](../../docs/STOP-REASON.md).
