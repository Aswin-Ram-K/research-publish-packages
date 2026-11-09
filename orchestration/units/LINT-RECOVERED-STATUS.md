# UNIT LINT-RECOVERED-STATUS

**Purpose.** Close the linter hole reported by `HANDOFF-RECOVERY`: `handoff_lint.py` had no
`recovered` status, so `E_STUB` was evaluated only for `partial`/`stub` and the evidence gate only
for `done` — a `status:"recovered"` record could list nothing, prove nothing, and lint clean. One
recovered file also exited `None` instead of 0.

**Bound.** ≤22 tool calls, zero inference requests. Handoff `partial` within 4 calls.

**Write paths (exactly).** `experiments/ptr-engine/tools/handoff_lint.py`,
`experiments/ptr-engine/longrun/tests/test_handoff_lint.py`,
`experiments/ptr-engine/measure/HANDOFF-LINT.json`, `docs/HANDOFF-LINT.md`,
`orchestration/units/LINT-RECOVERED-STATUS.md`, `orchestration/handoffs/LINT-RECOVERED-STATUS.json`,
`orchestration/journals/LINT-RECOVERED-STATUS.jsonl`.

**What changed in the tool.**
- `recovered` is a third valid unit status (`UNIT_STATUSES`); no `E_SHAPE` for it.
- It must satisfy the full unit shape (`unit, status, artifacts, evidence, blocker,
  next_unit_hint, write_paths`) plus `E_ARTIFACT_ABSENT` per absent artifact.
- New `E_RECOVERED_NO_EVIDENCE`: `recovered` with empty/absent `evidence`, or no `recovery` block.
- New `E_RECOVERED_NO_PROVENANCE`: `recovery` missing `from_stub_sha256` or `evidence_basis`.
- `E_STUB` now also covers `recovered` with no artifacts and no evidence (and still does not fire
  when both are present).
- Exit discipline: `exit_code_for()` returns 0/1/2; the `__main__` wrapper normalises anything else
  to 2, so no invocation can return `None`.
- `partial`/`stub` and `done`/`pass` semantics untouched.

**Inputs are read-only.** Nothing under `orchestration/handoffs/` was edited; the eight recovered
records were linted as inputs.
