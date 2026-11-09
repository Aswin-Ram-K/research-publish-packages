# Results — TX-01 Cell 1 (ptr-engine)

Source of record: `orchestration/handoffs/CELLTX01.json` (unit `CELLTX01`, status `complete`), `orchestration/handoffs/CONTROLNOMASK.json` (control arm, status `done`), and `orchestration/handoffs/V-CELL01.json` (verifier, overall `partial`). Row file: `experiments/ptr-engine/measure/rows-longrun-CELLTX01.jsonl`. Instrument: `experiments/ptr-engine/longrun/tasks-v7/TX-01.v1.json`.

## Conditions

| Condition (arm) | Requests (rep 1 / rep 2) | Checkpoints rep 1 | Checkpoints rep 2 | Result | Source |
|---|---:|---:|---:|---|---|
| `masking-no-fetch` (masking ON) | 48 / 48 | 0/12 | 0/12 | 12 `ANSWER: NONE` abstentions | `CELLTX01.json` per_arm.masking-no-fetch |
| `masking-no-fetch` (masking OFF, control) | 48 / 48 | 12/12 | 12/12 | all 12 checkpoint facts recovered | `CONTROLNOMASK.json` per_checkpoint |
| `bounded-context-fetch` (masking ON + fetch) | 63 / 109 | 12/12 | 12/12 | all 12 checkpoint facts recovered | `CELLTX01.json` per_arm.bounded-context-fetch |

Replicate 2 rows: 205 total (48 + 48 + 109), all `task_id: TX-01`, same sha `44a1b435…`. Zero variance across two reps supports reproducibility but cannot estimate an interval.

Quoted raw answers (from `CELLTX01.json`):

- Passing checkpoint (turn 20, expected `3`): `ANSWER: NUM 3`.
- Abstaining checkpoint (turn 20, masking arm, expected `3`): `ANSWER: NONE`.

## Instrument identity

- Fixture: `experiments/ptr-engine/longrun/tasks-v7/TX-01.v1.json` (`CELLTX01.json`).
- `fixture_sha256`: `44a1b4356536a0a55757ed2a4c90f5ef7f9d0541836007dc195a50ab3db2ec21` (single value across rows; `CELLTX01.json` accounting).
- 48 turns; `tool_outputs` only on turn 1 (so the fact-carrying output is masked from turn 5 under `WINDOW_TURNS = 4`).
- 12 checkpoints at turns 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42 with expected values `3, 30, MAX_BATCH_SIZE, 5, PtrMissingRefError, E001, E002, E003, 128, 64, sha256, 7` (`CELLTX01.json`).

## Accounting

- Requests sent: 111 (`CELLTX01.json` totals.requests_sent); rows written: 111 (`rows_written`); all `task_id = TX-01` (`rows_task_id_all_TX01`); single `request_sha256` set `44a1b435…` (`single_fixture_sha256`).
- Cap: 2867 before, 2978 after, delta 111, advanced by exactly rows sent (`CELLTX01.json` accounting).
- Control run: 48 requests, 2978 → 3026 (`CONTROLNOMASK.json`).
- Per-arm rows: masking arm 48 rows; fetch arm 63 rows (`V-CELL01.json` contract discipline; 12 checkpoint answer rows + 12 tool-call intermediate rows among them).
- Marker fetches: 39 (`CELLTX01.json` totals.marker_fetches); tool-call finish rows: 16 (`totals.tool_call_finish_rows`).

## Verification qualifiers (from `V-CELL01.json`)

1. Per-turn `masked_rows` counts outputs *newly* masked that turn only: 3 at turns 5 and 21, 0 on all 36 checkpoint rows. It is not a per-turn "markers present" counter; do not use it as one.
2. The control's 12 answers are on-contract `NONE` *abstentions*, not wrong values. 0/12 counts 12 abstentions; abstentions sit in the denominator as passes-failed-by-policy, not as ungradeable failures.
3. Fetched bodies are not persisted on the rows; attribution rests on the fetch call (`fetch_rows=3`, `retrieval_outcomes=['OK','OK','OK']`, `marker_refs=['doc-config@r1','doc-errors@r1','doc-constants@r1']`) plus its OK outcome and fixture ground truth, not on body text.

## What this result does NOT show

One task (TX-01), one replicate per condition, no interval, no significance test, no cross-stack or cross-task generalisation. The fixture's facts are transient by construction (`CELLTX01.json` claim_limits). No quality floor was imposed; recommendations are labelled workload-specific only per the joint plan.

## Failures, with citations

- A 48-request run spent on a fixture with zero `tool_outputs` so the arm was inert: `orchestration/handoffs/AN1-POSCTRL.json` (confirms `masked_turns` empty every turn, fixture has no `tool_outputs`); `orchestration/handoffs/MASKDIG.json` — never persisted (handoff was never written); the inert-arm claim rests on the 48 rows with `masked_rows = 0` on every turn, not on a persisted handoff.
- 26 requests spent on the wrong task because `--fixture` defaulted to LR-01: `orchestration/handoffs/TASKGUARD.json` (rows carry `task_id: LR-01` for 26 rows).
- A fixture built then withdrawn for leaking every expected value in plaintext under both arms: `experiments/ptr-engine/longrun/WITHDRAWN-LR01-V10.md`.
- The refusal-token conflation: `orchestration/handoffs/V-REFUSAL.json` and `orchestration/handoffs/REFUSALFIX2.json`.
- The fetch written into the `ANSWER:` line: `orchestration/handoffs/FETCHALL.json`.
- The pointer-store cross-task fallback: `agent://VRUNNER/findings` (finding "Honor the task key when a stored body is missing"); `orchestration/handoffs/VRUNNER.json` — never persisted (handoff does not exist, content still readable at `agent://VRUNNER/findings`).

## Cross-stack (Stack A vs Stack B)

| condition | 8012 occamy-1.0 | 8014 qwen3.5-9b |
|---|---|---|
| `masking-no-fetch` masking ON | 0/12 and 0/12 (two reps) | 0/12 |
| `masking-no-fetch` masking OFF | 12/12 and 12/12 (two reps) | 8/12 |
| `bounded-context-fetch` masking ON | 12/12 and 12/12 (two reps) | 0/12 — blocked at T1 because the endpoint cannot execute tool calls |

**First-class finding — tool support is an infrastructure property, not a model property.** On Stack B (8014, vLLM, qwen3.5-9b) the fetch arm could not execute a single tool call, so the recovery treatment is untestable there. Record this as a negative result about the deployment, not as a model failure: the recovery-by-retrieval arm is gated on the deployment supporting tool calls.

**Preflight evidence.** Max prompt 758 tokens estimated and 1,392 tokens observed on rows, against a 32,768 window — so context was never the binding constraint; tool support was.

**Interpretation.** Mask-destroys-the-fact replicates across both stacks and both models; recovery without retrieval is model-dependent (12/12 vs 8/12); recovery by retrieval is gated on the deployment supporting tool calls, which is an infrastructure property, not a model property.

**What remains unshown.** Two reps on one stack, one rep on the other, no interval, no significance, one task, and a fixture whose facts are transient by construction.

## Link

Pre-registered spec: `experiments/ptr-engine/research-seed-concepts/JOINT-SERVING-CONTEXT-PLAN.md` (not edited by this unit).
