# Unit VERIFY-BATCH-1 — independent verification of four improvements

**Purpose.** Non-author verification of HARNESS-GUARDS, CHECKPOINT-COVERAGE, MATRIX-HONESTY, HANDOFF-LINT.
**Bound.** ≤45 tool calls, zero inference requests; handoff `partial` within 6 calls if needed.
**Attacks.** One mandatory per unit (A–E) plus extras; red→green only in throwaway copies.
**Write paths.** `orchestration/handoffs/VERIFY-BATCH-1.json`, `orchestration/verdicts/VERIFY-BATCH-1.md`,
`experiments/ptr-engine/measure/BATCH-1-VERIFICATION.json`, `orchestration/units/VERIFY-BATCH-1.md`.
**Result.** `pass` — all four units reproduce; five overstatements recorded; no defect fixed (a fresh card fixes them).
**Report.** `orchestration/verdicts/VERIFY-BATCH-1.md`.
