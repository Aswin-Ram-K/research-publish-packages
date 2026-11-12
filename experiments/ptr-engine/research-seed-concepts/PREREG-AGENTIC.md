# PREREG-AGENTIC — does a compaction policy cost the agent re-reads?

**Status:** pre-registered 2026-11-11, before the first stage-2 request. Stage 1 (the chain instrument
on the replay runner) is complete and void as an instrument; its finding is what this design answers.

**Supersedes:** nothing. It is the stage-2 half of `docs/AGENTIC-COMPACTION-AB.md`, whose §8 records the
arm-set change from the approved plan.

---

## Hypothesis

A context policy that drops a tool result the agent will need again forces the agent to re-read it. The
cost of that re-read is the mechanism by which compaction is expensive, and it is invisible to every
accuracy-only measurement the programme has run so far.

**H1 (primary).** On an episode whose final question needs a value learned early, `bounded-context-fetch`
and `compact` recover the value more often than `masking-no-fetch`, and they pay for it in re-reads.

**H2 (secondary).** `pinned` recovers the value without re-reads, because the pin keeps it verbatim.

**H3 (cost).** `compact`'s mean prompt tokens are below `none`'s, and its accuracy is not below
`masking-no-fetch`'s.

## Design

An episode loop (`longrun/agentic_cell.py`), not the replay runner. The agent acts, the tools stay ON at
the graded turn, and the grade happens at the end. This is the property stage 1 proved the replay runner
lacks: `run_longrun.py:2405` makes checkpoint turns tools-off, so no arm could ever re-read at the moment
it mattered.

| dimension | value |
|---|---|
| tasks | 8 (`longrun/tasks-agentic/AG-01..08.v1.json`), each over the real `experiments/ptr-engine` tree |
| steps per episode | 10 work steps + 1 final question |
| reps | 2 |
| arms | `none`, `masking-no-fetch`, `pinned`, `bounded-context-fetch`, `compact` |
| window | `--window-tokens 4096` |
| temperature | 0.0, stated explicitly (the runner refuses a run that does not state it) |
| tools | `read_file` (≤200 lines / 8,000 chars), `grep` (≤40 matches / 4,000 chars) |
| endpoint | `http://192.168.2.168:8012/v1`, model `occamy-1.0` |

## Controls

- `none` is the control: nothing is dropped, so a failure there is model error, not policy cost.
- Every task's `final_question` is contract-checked to NOT contain the graded value, so no arm can answer
  from the question alone.
- `expected_present` is computed by the runner from the exact message list it sent, and is `null` when
  unknown. The analyser treats `null` as "not evidence", never as a pass.
- The task builder re-derives every `expected` by AST from the tree in `--check` mode, so a hand-typed
  value cannot enter.

## Primary metric

`lost_then_failed` per arm: graded rows that failed while `expected_present` was false. This is the only
class that attributes a failure to the policy rather than to the model.

## Secondary metrics

`present_then_failed` (model error), `unclassified` (unknown presence), accuracy, `refetch_count` (tool
calls at or after the first fold in the episode), mean `prompt_tokens`, mean `cached_tokens`, total
`dropped_turns`, total `pinned_tokens`.

## Predicted outcome (written before running)

`none` and `pinned` recover the value in most episodes; `masking-no-fetch` loses it in most;
`bounded-context-fetch` recovers it but with the highest `refetch_count`; `compact` sits between
`masking-no-fetch` and `bounded-context-fetch` on accuracy and has the lowest mean prompt tokens of the
four non-`none` arms.

## Falsifiers

1. **`instrument_failure`** — no arm has any `lost_then_failed` row. The policy never destroyed anything,
   so the instrument did not exercise its own mechanism.
2. **`null_model_error`** — `present_then_failed` exceeds `lost_then_failed` in every arm. The failures
   are the model's, and the experiment is a null that does not count as evidence about compaction.
3. **`pin_premise_fails`** — `pinned` accuracy is not above `none` accuracy. Pinning is not doing what
   the design assumes, and H2 is dead.
4. **`recovery_not_paid`** — `bounded-context-fetch`'s `refetch_count` equals `masking-no-fetch`'s. The
   recovery arm is not paying for recovery, so either it never needed to or the channel is not wired.
5. **`compaction_not_cheaper`** — `compact`'s mean `prompt_tokens` is not below `none`'s. The cost half
   of H3 is dead.

A fired falsifier is a result, not an error: the analyser exits 0 and prints the numbers that fired it.

## Budget ceiling (requests)

10,987 rows are spent against the 12,094 cap, so **1,107 remain**.

```
8 tasks x 2 reps x (4 arms x 12 requests + 1 arm x 16 requests) = 1,024
```

`compact` costs 16 because it buys one summary request per fold. 83 requests are held back for a smoke
episode. The plan's 1,280 assumed the full headroom; the two void stage-1 runs spent 800 of it, and the
invariant the plan set was the budget, not the task count.

## Instrument requirements before the first request

1. `longrun/agentic_contract.py` — the task schema, row schema, arm list, tool bounds, validators. **Done.**
2. `longrun/agentic_cell.py` — the episode loop, five policies, confined tool execution, budget gate,
   dry run. **In progress.**
3. `longrun/tasks-agentic/AG-01..08.v1.json` + `tools/build_agentic_tasks.py --check`. **In progress.**
4. `longrun/tools/analyze_agentic.py` — the attribution and the five falsifiers. **In progress.**
5. A dry run whose planned count equals the live run's row count for the same inputs.
6. The harness digest re-pinned to generation 10 once the runner files are final, because the episode
   runner is a new measurement input.

## What this does not claim

It does not measure a real user session's length: 10 steps is short by design, and the fold fires because
the window is 4,096, not because the episode is long. It does not compare against a production
compactor's summary quality. It does not price the summary call's own tokens beyond counting the request.

---

## Erratum, 2026-11-11 — the task count and the primary metric

This section is appended, not substituted. Nothing above is rewritten: the table row at line 34 and the
budget formula at line 103 stand as written, and this erratum supersedes them by reference. The
pre-registration is frozen once the run starts, so a correction that changes what the run measures has to
be recorded as a dated erratum rather than edited into the body.

### 1. The task set is four tasks, not eight

The run uses `longrun/tasks-agentic/AG-01..04.v1.json` — four tasks, not the eight the design table names.
Each is 16 turns with 4 checkpoints at turns 4, 8, 12 and 16, and `window_tokens 4096`. The `.v1` in the
filename is the *fixture* version, not a task-schema version: every one of the four files carries
`schema: consonance.longrun-fixture/2`.

The four `AG-05..08` files named in the table at line 34 were built in a bespoke `agentic-contract` shape.
That schema was dropped, and the files were removed with it. `agentic_cell.load_task` now refuses any
document whose `schema` is not `consonance.longrun-fixture/2`, raising
`unsupported_task_schema: <schema> (task <id>; only 'consonance.longrun-fixture/2' is accepted)` — a
foreign document is refused by name, never coerced into the accepted shape. The task count is therefore a
property of what the loader will accept, not a number chosen for the budget.

### 2. The primary metric `lost_then_failed` does not discriminate in stage 2

`lost_then_failed` was defined for the stage-1 scripted replay, where the graded value could be present in
the prompt and the fold could remove it. In an agentic episode the graded value is never in the prompt in
any arm — the model must read it from the snapshot — so `expected_present` is False by construction
everywhere, and every wrong answer classifies as `lost_then_failed`. The class is constant across arms and
carries no information about the policy.

The stage-2 primary metric is therefore **per-arm checkpoint accuracy**: 4 checkpoints × 4 tasks × 2 reps
= 32 observations per arm. The mechanism measure is **`refetch_count`**, which is what distinguishes a
policy that recovers the value by re-reading from one that never lost it. `lost_then_failed` is retained
only as a diagnostic and must not be quoted as a stage-2 result.

### 3. The arm set is four arms

The stage-2 run has four arms: `none`, `masking-no-fetch`, `pinned`, `compact`. `bounded-context-fetch`
and `spcc` are not in the stage-2 run. H1's comparison against `bounded-context-fetch` and falsifier 4
(`recovery_not_paid`) are consequently not exercised by this run; they remain on the record as the
hypothesis the arm set was designed to test, not as results.

---

## Erratum 2, 2026-11-11 — the first erratum's claim about `expected_present` is measured false, and `window_tokens` moved

Appended, not substituted. Erratum 1 stays as written; this corrects it by reference, because a
pre-registration's mistakes are part of the record.

### 1. `expected_present` is NOT False by construction

Erratum 1 §2 states that `expected_present` "is False by construction everywhere" in an agentic episode.
That was reasoned, not measured, and the measurement contradicts it. The presence test asks whether the
**source document revision** the checkpoint's value is derived from is still in the message list
(`agentic_cell._doc_anchor` over `_checkpoint_source`), not whether the derived value's literal text
appears — the literal test could never be true, because a CALL checkpoint's expected value is a derived
dict and a NUM constant is computed by `ast`, and 9 of the 16 checkpoints are absent from the document
body that carries them. Measured across three arms: `expected_present` was False at 3 checkpoints in each
folding arm and 0 in `none`, so `lost_then_failed` totals 1 rather than 32 and the class **does**
discriminate — it just discriminates on document presence, not on value text.

### 2. `window_tokens` is 8000, not 4096

The four fixtures now carry `window_tokens 8000` (`FOLD_AT_FRACTION 0.739`, threshold 5,912). At 4096 the
threshold was 3,027 against live prompts of ~3,700 and the `pinned` arm folded 12 times in 16 steps without
ever answering: the journal was dropped continuously, so the episode measured fold thrash and not policy.
The value was raised once, before the recorded run, and every number in the result comes from the 8000
fixtures. The fixtures' `documents` and `turns` are byte-identical to the 4096 versions, so the change
moved only the fold threshold.

### 3. The primary metric is coverage as well as accuracy

Per-arm accuracy alone is reported with its denominator for this reason: the folding arms answer 6 of 32
checkpoints where `none` answers 15, and no folding arm finishes a task. A `checkpoint_accuracy` quoted
without `graded` would say the folding arms win. The result record
(`measure/AGENTIC-2026-11-11-analysis.md`) prints both, and `docs/AGENTIC-COMPACTION-AB.md` §10 states the
reading.

### 4. `solved` is over ALL task checkpoints, and no arm reaches it

Erratum 2 §3 said "no folding arm finishes a task", implying the uncompressed arm does. That was an
artefact of the offline grader, not a result: `agentic_cell.offline_episodes` emitted only the ANSWERED
checkpoints, so `solved = all(ok)` there used a narrower denominator than `run_episode` uses on every
live arm. `none` was graded through `--offline`, so `AG-02 rep2` scored `solved` on one answered
checkpoint out of four. Corrected by `_episode_checkpoints` in `agentic_cell.py` (applied when
`--tasks` is passed to `--offline`), guarded by
`test_offline_keeps_the_live_checkpoint_denominator`, and the `none` record was re-graded.

Under one rule — an episode is solved only if every one of its four checkpoints is answered and right —
**all three arms are 0 of 8**. `none`'s best episode answers all four and gets three. The metric this
cell can support is checkpoint coverage and cost per arm; it cannot support a completion rate, and the
pre-registration's completion-based reading must not be written from these rows.
