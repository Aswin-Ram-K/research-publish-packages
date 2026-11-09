# POSCTRL-LR01 — 48-request positive-control run (gate 0.1 evidence)

## Objective
Execute the authorised 48-request positive-control run on the live SGLang endpoint
for fixture `experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json`,
arm `masking-no-fetch`, one rep, and record rows so gate 0.1 can be graded from a
measured transcript. No grading, tuning, or fabrication.

## Arm selection
Chosen: `masking-no-fetch` (ARM_C). Justification: dry-render of graded turns
(T12, T24, T46, T48) shows the required source facts present in the rendered
prompt (working_set_block pinned: resolve.py, errors.py, test_scope.py,
test_negative_controls.py; PtrNotAReferenceError, PTR_NOT_A_REFERENCE, ledger,
`def test_`, `9` present at every graded turn). `bounded-context-fetch` rendered
byte-identical prompts in the dry run, and fetch follow-ups would exceed the
48-completion hard cap, so the minimal arm that delivers the complete working
set was selected. `exit 0` is a runtime claim, not a source fact, and is
absent from the fixture by construction.

## Pre-flight (all shown)
1. Engine identity: `engine_identity.py` verdict — model_id `occamy-1.0`,
   served `occamy-1.0`, engine_version `0.0.0.dev1+g4ccff141d`,
   model_snapshot_digest `fa865dc5e80a13b9a2d8ae8d65ed2ee332f33652` — matches
   `measure/ENGINE-IDENTITY-PIN.json`. No completion path touched.
2. Fixture loads under unified schema (runtime-v4): N=48, wall_tokens=65536,
   bytes_per_token=4.0914. Turn-1 prompt 13591 B = 3322 est tokens vs wall 65536.
3. Dry-render of graded turns: required source facts present (see arm selection).
   Official `--dry-run`: 48 turn requests, 0 digests, cell_total=48.
4. Cap preflight: rows before=2591, headroom=9503; 48 fit (after=9455).

## Recording
Harness `run_longrun.py`, rows appended to
`experiments/ptr-engine/measure/rows-posctrl-2026-11-08.jsonl` (48 rows).
Each row carries arm, policy, cell, rep, turn index, prompt_tokens, cached_tokens,
completion_tokens, latency, full assistant text. All 48 turns stop/stop, 0
truncated, 0 failed turns, content_source=content for all.

## Stop conditions
None triggered. Run completed all 48 turns.

## Verify turn (T48)
Content: "I'll run the acceptance checks for LR-01. Let me first check what tests
exist and the project structure.\n\nANSWER: NOT-AN-ANSWER". No exit codes, no
test file names, no counts reported by the model.

## Positive-control assessment
NOT a positive control. Evidence:
- T48 content lacks acc.2 regex targets (test_scope.py, test_negative_controls.py,
  exit 0): acc.2 requires all three; only none of "exit 0" appear in T48.
- T48 content lacks acc.3 targets (PtrNotAReferenceError, PTR_NOT_A_REFERENCE,
  ledger): PtrNotAReferenceError and PTR_NOT_A_REFERENCE absent from the entire
  transcript.
- T48 content lacks acc.4 targets (def test_, test_scope.py, 9): "def test_"
  absent from the entire transcript.
- Across all 48 turns: PtrNotAReferenceError=0, PTR_NOT_A_REFERENCE=0,
  exit 0=0, "def test_"=0 occurrences in assistant content. test_scope.py=9,
  test_negative_controls.py=1, ledger=2 (mentions only, not the required values).

The transcript is therefore not a positive control; gate 0.1 grading is left to
the verifier.

## Cap accounting
Before: 2591 spent, 9503 headroom. After: 2639 spent, 9455 headroom. This run: 48.

## Hard bound
48 paid completions used; no retries beyond harness defaults; zero state-changing
routes called; no service restart; no fixture/grader modification.
