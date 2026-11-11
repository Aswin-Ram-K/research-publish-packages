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
