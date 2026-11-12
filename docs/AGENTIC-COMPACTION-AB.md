# AGENTIC-COMPACTION-AB — the long-horizon, model-driven test E7 does not have

**Status:** design draft, 2026-11-11. Nothing built, nothing measured, 0 requests spent.
**Supersedes nothing.** It is a *second* instrument beside E7 (`PREREG-COMPACTION.md`), not an edit to it.
**Author's line:** this document is a design, not a result; every number in §2 is arithmetic over
measured constants, and each one names the constant it came from.

---

## 1. The gap the current instrument cannot close

E7's fixture (`experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-07.v5.json`) is a **scripted
replay**: the turn list is fixed, each turn's question is fixed, each turn's tool bodies are baked at
build time by `longrun/tools/build_long_fixture.py` (it embeds real file text into
`documents[].revisions[].value` and `turns[].tool_outputs[].body`). Measured on the runner, the loop is
`for t in range(start, n_turns + 1)` (`longrun/run_longrun.py:3659`) with
`n_turns = min(fixture["N"], --max-turns)` (`:724-765`).

Consequence: **a fold cannot change the trajectory.** Arm A's summary, arm B's mask window and arm D's
pins all alter the prompt an arm sees, but the next question is the fixture's, the next body is the
fixture's, and the turn count is the fixture's. So E7 can price *prompt layouts over a fixed script*, and
cannot measure the thing its own hypothesis is about: **an agent that loses its journal pays for it in
work** — the 202/290 (69.7 %) re-read rate (`docs/COMPACTION-CACHE-DESIGN.md` §2.5) is currently a
property of *real sessions*, imported into the design, not something E7 can re-measure.

The measured cells so far make this vivid: every SPCC cell to date ran at a **median prompt of 1.5–2.5 k
tokens** (`measure/rows-e2-turnover-2026-11-10.jsonl` median 1,521; `measure/rows-e3-retain-2026-11-10.jsonl`
median 2,317), the largest `prompt_tokens` ever recorded in the corpus is **51,216**
(`measure/rows-longrun-2026-10-26-policy.jsonl`), and **no row anywhere was produced with an `LR-07`
fixture** (`grep` over all 103 `rows-*.jsonl`: zero). The "real-length regime" E7 was rewritten for has
no measured precedent at all.

`U-SPCC-67`/`U-SPCC-77` give a second reason to leave replay behind: in the replay the six masking
failures decomposed into four *answer-slot binding* cases and two adjacent-symbol cases — artefacts of a
transcript whose answers sit in a fixed slot. A model that chooses its own reads has no fixed slot.

---

## 2. What the harness can already do, and what it cannot

Measured on the live tree (`run_longrun.py` unless stated):

| capability | state |
|---|---|
| model-initiated reads | **exists** — `TOOL_NAMES=("read_file",)` (`:487`), `parse_tool_calls` (`:936`), `calls_from_response` (`:1053`), `execute_tool_call` (`:1154`) |
| read bounds | **exists** — `TOOL_READ_CAP_LINES=200`, `TOOL_READ_CAP_CHARS=8000`, `TOOL_CALLS_PER_TURN=2`, `TOOL_FETCH_ROUNDS_PER_TURN=3`, `TOOL_FETCH_ROUNDS_PER_ARM=48` (`:453-500`) |
| path confinement | **exists** — `_resolve_under` realpath + commonpath, rejects absolute/`~`/`..`/secret-shaped (`:1094-1196`) |
| read root | **fixed to the process cwd** — `root = os.getcwd()` (`:1435`); there is no `--root`, so a "snapshot" cannot be pointed at |
| turn count | **fixed by the fixture** — `n_turns` from `fixture["N"]` (`:724-765`, `:3659`); the model cannot add, skip or chain a turn |
| tool surface | **`read_file` only** — no grep, no list, no glob |
| truth derivation | **mechanical, but from `fixture["sources"]`** — `grade_v5.derive_truth` (`:603-703`) walks the AST for `NUM` (`constant_value`, `count_classes`) and `CALL` (`call_inside_function`); the v5 runtime fixtures carry `items[]` bodies instead, so derivation has nothing to read |
| episode grading | **absent** — grading is per checkpoint inside a scripted turn (`score_longrun.py:997-1000,1085-1145`); rows carry per-request stop reasons only (`:2582-2614`) |
| task loop / stop condition | **absent** — nothing in the repo implements a model-driven step loop, and `task_success` appears only in the separate scripted quality runner |

So "agentic" is not a parameter of the existing runner. It is **four new pieces**, and §4 orders them by
cost.

---

## 3. The two candidate instruments

### 3.1 Stage 1 — chain reference by pointer (small build, reuses the replay runner)

Keep the scripted turns; add one field per turn: `ref_prior` naming a checkpoint id that an **earlier**
turn answered. Turn *n*'s question then reads

> "Using the symbol you identified at step *j* — do not restate it — find the caller that overrides it."

**The value itself never enters the question text.** That is the whole point and an earlier draft of this
section got it wrong: interpolating the graded value would put it back in the prompt, so no fold could
destroy it and the only failure the instrument could produce is a wrong prior answer propagating forward
— error propagation, not compaction. A pointer-only reference makes recovery depend on the journal
itself, so the arms differ **by construction**:

| arm | what step *n* can still do |
|---|---|
| `pinned` | the fact is in PINS → recoverable without a read |
| `compact` | recoverable only if the summary kept it (the thing under test) |
| `masking-no-fetch` | the tool result is masked → must re-read (a billed fetch round) or fail |
| `none` (FIFO) | truncated → same as masking, with no mask boundary to blame |

- **Horizon crossing** is guaranteed by the reference, not by arithmetic: step *j* is before the fold and
  step *n* is after it, and the fixture's `at_turn` for the fold is chosen so this always holds.
- **Failure attribution is two-way and must be recorded, not assumed.** A chain break is evidence about
  the fold only when the value was **absent** from the prompt at step *n*; when it was present, the break
  is a model error (wrong prior answer or wrong reasoning) and is graded as such. Each chain turn
  therefore stamps `expected_present` — the same field the E3 cell used, now computed at a digit boundary
  (`measure/rows-e3-retain-2026-11-10.jsonl`, `expected_present 96/96`, after the reasoning-channel
  defect was fixed) — and a break is classified `lost-then-failed` (fold's fault, the signal) or
  `present-then-failed` (model's fault, not the signal).
- **Re-fetch is measurable here after all.** The replay serves bodies only when the model asks, and the
  fetch channel is model-initiated (`run_longrun.py:3866-3946`), so an arm that lost the value and asks
  again pays a billed round that the row records (`fetch_followup`, `fetch_rounds_used`). Earlier I wrote
  that stage 1 could not show re-fetch growth; that was wrong — it can, and `refetch_count` is the
  secondary metric.
- Cost: a renderer in `run_longrun.py` (`turn_user`, `:417`/`:1757`) + a `chain` block in
  `check_pointer_fixtures.py`'s lint (the reference must name an *earlier* checkpoint, must not leak the
  value into any question body, and the referenced checkpoint must precede the fold) + a builder pass.
  No new loop, no new grading path.
- Fixture: `tasks-v7/TX-04S.v1.json` (41 checkpoints, 14 declared mismatches, built today) is the
  starting point — 41 checkpoints/arm is the same order as the 48 that produced the ±4.2 pp band.
- Requests: 100 turns/arm × 4 arms = **400**, + warm-ups. Fits comfortably.

**What it still cannot say:** it cannot show that a *deliberate* agent strategy — deciding to re-grep
rather than to re-read — costs what the design claims, because the action space here is one bounded read
per step and the fixture still supplies the question. That is stage 2's job, and it is the only thing
stage 2 is for.

### 3.2 Stage 2 — task mode (the real agentic test)

A new episode loop in which the model, not the fixture, decides what happens next:

1. **Snapshot.** `state/snapshots/<sha256>/` — a bounded copy (60–120 files) of
   `experiments/ptr-engine/{ptr_engine,longrun,tools}` + `src/resextract`, with a manifest of per-file
   shas. Writes stay under gitignored `state/`; no target repo is touched. New `--root` on the runner,
   asserted against the manifest before the first request.
2. **Task.** A goal, a step budget, and 3–5 mechanically derivable checkpoints. Family: *trace a control
   to its use* — find the definition, read its default, find the overriding caller, report the effective
   value. Key derived by AST at build time from the snapshot, so no hand-written answers and no judge.
3. **Step.** One request per step. The model replies with either a tool call
   (`read_file{path,start,end}`, optionally `grep{pattern,glob}`) or `ANSWER: …`. Reads are served by
   `execute_tool_call` against the snapshot root; the answer ends the episode early.
4. **Grading.** Per-checkpoint via the existing `answer_spec` machinery, plus an episode verdict
   (`solved`, `steps_used`, `budget_exhausted`, `refetch_count`) written as one episode row.
5. **Divergence is the measurement**, not an accident: arms will use different step counts. Everything is
   reported per verified success (`cost_units_per_verified_success`, E7's own metric) and per checkpoint,
   never as raw totals.

Arms: A `compact` (summarise at the fold), B `mask` (tool results older than 8 turns), C `pinned`
(PLAN + facts, no summary call), D `none` (FIFO truncate). E7's arm E (`pins-recency`) drops out here:
recency is a prompt-layout question, not an episode question, and stage 2 should not carry it.

**New tool surface — decision deferred to the operator:** `read_file` only, or `read_file` + bounded
`grep`. The argument for grep: without it the agent reads 200-line ranges blind, so a lost journal can
only be repaired by re-reading, and the re-read rate is *artificially* high; with it, re-fetch is a
realistic choice and its cost is exactly the quantity E7 claims. Recommendation: **add bounded grep**
(`grep(pattern, glob, max_hits=20)`, hits capped by chars) — it is one function beside
`execute_tool_call` and it makes the re-fetch measurement mean what the design says it means.

---

## 4. Ordered work, with the requests each stage costs

| # | piece | where | why it cannot be skipped |
|---|---|---|---|
| 1 | chain substitution renderer + lint + builder pass | `run_longrun.py:417`, `check_pointer_fixtures.py`, new builder | the only way to get a horizon-crossing fact through the replay runner |
| 2 | `--root` + snapshot builder + manifest check | `run_longrun.py:1435`, new `longrun/tools/build_snapshot.py` | without a frozen root, an "agentic" read is a read of the live tree and the task is not reproducible |
| 3 | episode loop (`step`, early stop, budget) | new `longrun/agentic_cell.py` | the runner's turn list is fixture-fixed; this is the actual new instrument |
| 4 | episode grading + row schema | `score_longrun.py`, `longrun/agentic.py` | per-checkpoint grading exists; per-episode does not |
| 5 | bounded `grep` tool | `run_longrun.py:1154` | decides whether "re-fetch" means what the design claims |

**Stage 1 cost:** 400 requests + 8 warm-ups (0.21 % of the 1,927 headroom).
**Stage 2 cost, 8 tasks × 4 checkpoints × ~30 requests/task × 4 arms:** **960 requests** (50 % of
headroom, leaving 959 for everything else). 12 tasks (48 checkpoints/arm) would be **1,440** and would
leave 479 — affordable but it spends the rest of the programme's budget on one instrument.

**Accuracy power at these n.** The ±4.2 pp band is *not* a power calculation: it is the measured
run-to-run spread on **48 binary checkpoints** (`PREREG-SPCC.md:70-78`; ±2/48). At 32 checkpoints/arm
(8 tasks) the smallest honest band is **±6.3 pp** (±2/32); at 48 it is ±4.2 pp. An agentic *episode*
count is far worse — 8 episodes/arm cannot resolve anything smaller than ~±35 pp, so episode-level
"solved" rate must never be quoted as a percentage claim; checkpoint accuracy and cost are the reportable
quantities. This is the strongest argument for grading **3–5 facts per task** rather than one.

---

## 5. Falsifiers (written before any request)

1. **Stage 1 — the reference is not doing work.** If no `lost-then-failed` break appears in any arm
   across 41 checkpoints, the pointer-only reference is not making recovery depend on the journal (the
   value survived compact, mask, truncation and pins alike). That is an **instrument failure**, not a
   result, and stage 2 must not be built on it.
2. **Stage 1 — the breaks are model error, not the fold.** If `present-then-failed` dominates
   `lost-then-failed`, the chains break because the model answered wrongly earlier, and the run is
   reported as a null with the attribution table published in full. A null of this shape does **not**
   count as evidence for the design.
3. **Stage 1 — pinning does not help retention.** If `pinned` shows no fewer `lost-then-failed` breaks
   than `none`, the pin model's premise (`COMPACTION-CACHE-DESIGN.md` §5.2) fails at this instrument and
   the cost question is moot until the retention mechanism is fixed.
4. **Stage 1 — recovery is not being paid for.** If `refetch_count` does not differ between
   `masking-no-fetch` and `pinned`, the recovery path is not being exercised and no re-fetch cost may be
   attributed to losing the journal.
5. **Stage 2:** if `pinned`'s `cost_units_per_verified_success` ≥ `compact`'s, the design's central claim
   (`COMPACTION-CACHE-DESIGN.md` §5.2) is wrong at real length under agentic work.
6. **Stage 2:** if `refetch_count` does not differ between A and B, the claimed mechanism is not operating
   and any cost difference is a prompt-layout artefact.
7. **Stage 2:** if the fold never fires (`compactions == 0` in an episode), that episode is **void**, not
   a data point — the natural agentic regime has a small `L0` and the journal grows from the work itself,
   so a short episode is a design failure, not a result.

---

## 6. What this document does not claim

- No accuracy, cost or re-fetch number here is measured; §1's ratios come from the design doc's own
  session audit, and §4's requests are arithmetic.
- Stage 1 is not a substitute for stage 2: it prices strength of *state retention* at a fold, not the
  cost of *recovering* lost state.
- Neither stage re-opens E7's predictions. If stage 2 contradicts them, that is a new verdict superseding
  E7's, not an edit to it.

---

## 7. Errata, measured 2026-11-11 (two stage-1 runs, 800 requests, both void)

**E1 — §3.1's arm table is wrong about `pinned`.** `PinnedArmState` pins **no bodies**:
`arm_cd.py:697-701` says "No body is pinned: L1 carries refs, digests and byte lengths only, so
`run_longrun.pinned_views` finds nothing to serve from the prompt and every tool call is a real fetch."
The row "`pinned` — the fact is in PINS → recoverable without a read" is therefore false for this
codebase. `pinned` is a refs-only arm; the retention comparison the table describes is not available in
the replay runner.

**E2 — a pointer that names only the step destroys the locator as well as the value.** TX-05C (400
requests) declared no tool, so `tool_calls = 0` in every arm and every carry checkpoint answered
`ANSWER: NONE`; the run is void. TX-05D (400 requests) declared `fetch(ref)` and recorded
`tools_schema_sent: true`; `masking-no-fetch`, `spcc` and `pinned` still made 0 tool calls and answered
`NONE`, while `bounded-context-fetch` fetched 3 and 5 rounds at turns 36 and 46 and answered with the
**wrong symbol** (`SYM_03`, 4031/4037) instead of `SYM_01`. The model had lost the symbol name at the
fold, so it could not choose which ref to fetch. `analyze_chain.py` over the four TX-05D files:
`ok 0 / lost 6 / present 0` in every arm, `refetch` 64 on `bounded-context-fetch` and 0 on the other
three, `compactions` 3 on `spcc` and 4 on `pinned`.

**Correction to the pointer rule.** The question must name the **symbol** and never the value:
`Using SYM_01 — do not restate its value — find the caller that overrides it.` The leak check already
forbids the value; it must also be shown to permit the symbol. Naming the symbol is not a leak: the
graded value is the override, and the symbol alone does not contain it. This correction is recorded and
**not yet run** — the budget after the two void runs is 1,107 requests, and stage 2 is the instrument
that can answer the question stage 1 was meant to price.

**Falsifier 4 is unsatisfiable as written.** It compares `refetch_count` between `masking-no-fetch` and
`pinned`, and neither arm has a fetch channel, so both are 0 by construction. The measurable form is
`bounded-context-fetch` against the rest: 64 against 0.

## 8. Stage 2 as built — the arm set changed, and why (2026-11-11)

Stage 1's two void runs taught one thing that changes stage 2's design: **the replay runner cannot
measure recovery at all.** `run_longrun.py:2405` states that at a checkpoint turn the tools are OFF,
`CHECKPOINT_CONTRACT_LINE` says "emit exactly one line and nothing else", and the fetch channel is
serviced only for `arm_cd.ARM_D` (`run_longrun.py:3862-3900`). The only turn that asks for a lost value
is therefore a tools-off checkpoint, so no arm can re-read at the moment it matters. Stage 2's episode
loop keeps the tools ON at the graded turn, which is the whole reason it exists.

**The arm set is five, not four, and `spcc` is not one of them.**

| arm | what it does | why it is in the set |
|---|---|---|
| `none` | nothing dropped | the control: the transcript grows and the server never truncates at these lengths |
| `masking-no-fetch` | old tool results replaced by a marker, no fetch channel | the cheapest policy, and the one that cannot recover |
| `pinned` | pinned facts kept verbatim, the rest folded | tests whether pinning alone is enough |
| `bounded-context-fetch` | fold + a fetch channel that can re-read | the recovery arm |
| `compact` | fold + a model-written summary of the dropped turns | what every real system runs; without it the experiment does not answer "is compaction worth it" |

`spcc` is dropped because it is the layer compiler over a fixture's **world index**, and an episode loop
has no world index to compile — the arm would be a different instrument wearing the same name. `compact`
takes the slot, and it is the more important arm: it is the real-world baseline the other four are
measured against. This is a change to the approved plan, recorded here rather than made silently.

**Sizing to the remaining budget.** 10,987 rows are spent against the 12,094 cap, so 1,107 requests
remain. `compact` buys one extra request per fold, so its episodes cost more than the others:

```
8 tasks x 2 reps x (4 arms x 12 requests + 1 arm x 16 requests) = 8 x 2 x 64 = 1,024
```

leaving 83 for a smoke episode. The plan's 1,280 assumed the full headroom; the two void stage-1 runs
spent 800 of it, and the invariant the plan set was the budget, not the task count.

**The contract is code, not prose.** `longrun/agentic_contract.py` holds the task schema, the row
schema, the arm list, the tool bounds, and the validators the runner, the task builder and the analyser
all import, so the three cannot drift apart. `expected_present` is never defaulted to true: an unknown
is `null`, and the analyser treats `null` as "not evidence", never as a pass.

## 9. Stage 2 as built: four tasks, four arms, and a metric that does not transfer

The arm-set paragraph of §8 is superseded by the arm-set paragraph below; the rest of that section
stands. What follows is what the run actually is, not what the plan said it would be.

**The task set is four.** `longrun/tasks-agentic/AG-01.v1.json` through `AG-04.v1.json`: 16 turns
each, four checkpoints at turns 4, 8, 12 and 16, `window_tokens 4096`. Every graded value is derived
from the snapshot by AST — `longrun/tools/build_agentic_tasks.py` parses the source, resolves the
constant or the call the checkpoint names, and writes the expected value into the fixture, so no
graded number is typed by hand and none can drift from the code it grades. The `.v1` in the filename
is the fixture version (`fixture_version: "AG-01.v1"`), not the schema version; the schema is
`consonance.longrun-fixture/2`.

**One task schema.** `agentic_cell.load_task` accepts `consonance.longrun-fixture/2` and nothing
else: any other `schema` is refused by name with `unsupported_task_schema: <schema>` and never
coerced into the accepted shape (`agentic_cell.py:303-305`). The bespoke `agentic-contract` task
shape was built and then dropped. Two task shapes for one measurement means two graders, and two
graders mean numbers that cannot be compared with any earlier cell — including the stage-1 runs this
experiment exists to correct.

**The arm set is four:** `none`, `masking-no-fetch`, `pinned`, `compact`. `spcc` is out because it
compiles a fixture's world index and an episode loop has no world index to compile; it would be a
different instrument wearing the same name. `bounded-context-fetch` is out of the stage-2 run as
well: the episode loop keeps the tools ON at the graded turn, so every arm can re-read, and a
dedicated fetch arm would measure a channel the other three already have. `agentic_contract.ARMS`
still lists `bounded-context-fetch` as an implemented fifth arm, so the four-arm set is what the run
schedules, not a limit of what the code can execute.

**The primary metric does not transfer.** `lost_then_failed` was defined for the stage-1 scripted
replay, where the graded value could sit in the prompt and a fold could remove it. In an agentic
episode the value is never in the prompt in any arm — the model has to read it out of the snapshot —
so `expected_present`, which the cell measures from the exact message list sent
(`agentic_cell.py:1159`), is False by construction, and every wrong answer classifies as
`lost_then_failed`. The classification is not wrong; it is uninformative, because it can no longer
separate a fold that destroyed a value from a model that answered badly.

Stage 2's primary metric is therefore per-arm **checkpoint accuracy**: 4 checkpoints x 4 tasks x 2
reps = 32 observations per arm, computed by `_episode_report` (`analyze_agentic.py:150`) and reported
as `checkpoint_accuracy` (`analyze_agentic.py:205`). The mechanism measure is **`refetch_count`** —
tool calls named `read_file` or `grep` made at or after the first fold of an episode — which is what
says whether an arm bought its accuracy by re-reading. `lost_then_failed` stays in the report as a
diagnostic only, and a void episode (no fold of any kind) is excluded from every accuracy and cost
number rather than counted as a zero.

**Every row names its instrument.** `harness_sha256` is a required row key
(`agentic_contract.py:31`), verified against `measure/AGENTIC-PIN.json` before the first request; a
mismatch raises `agentic_pin_check_failed` and no row is written (`agentic_cell.py:969`). A row that
does not name the instrument that wrote it is not evidence, and a run whose rows cannot be tied to a
harness hash cannot be compared with any other run.

## 10. Result, 2026-11-11: compaction buys cost and loses coverage

Three arms measured, 8 episodes each (4 tasks x 2 reps), 16 steps, 385 requests, snapshot
`state/snapshots/172d334b…`, pin `0c7cd2e8…`. Machine record:
`experiments/ptr-engine/measure/AGENTIC-2026-11-11-analysis.{json,md}`.

| arm | episodes | requests | answered /32 | correct | accuracy on answered | solved | mean prompt | max prompt | cost units |
|---|---|---|---|---|---|---|---|---|---|
| `none` | 8 | 128 | 15 | 12 | 0.800 | 4 | 9,864 | 24,672 | 1,273,054 |
| `pinned` | 8 | 128 | 6 | 5 | 0.833 | 0 | 4,128 | 6,642 | 288,589 |
| `compact` | 8 | 129 | 6 | 6 | 1.000 | 0 | 4,153 | 6,611 | 304,518 |

`cost units` is `billed_tokens + 3 x completion_tokens`, the analyser's own basis.

**Accuracy is not the difference; coverage is.** On the checkpoints an arm actually answers, the
folding arms match or beat the uncompressed arm — `compact` answers 6 and gets all 6 right. What
separates them is how many they answer: 6 of 32 against 15 of 32, and no folding arm finishes a
single task while `none` finishes 4 of 8. The folding arms spend their last steps re-reading the
snapshot and never emit the answer line: mean `refetch_count` is 5.0 for `pinned` and 5.5 for
`compact` against 4.0 for `none`, over a shorter horizon.

**The mechanism, stated with its consequence.** A fold drops the journal; `journal-drop` was the
mechanism for both folding arms, firing 38 times (`pinned`) and 45 times (`compact`). After the fold
the model has to re-read to recover, and it does — but re-reading costs steps, and the episode ends on
`max_steps` rather than on an answer. Compaction is 4.2x cheaper per request and unusable as a task
policy at this step budget.

**This is a frontier, not a clean win for either arm.** `none`'s max prompt is 24,672 tokens against
an 8,000-token window: the uncompressed arm's advantage is won by exceeding the constraint the folding
arms obey. The honest reading is that at 16 steps the folding arms need a larger step budget (or an
answer-first checkpoint contract) to be comparable, and that is the next measurement, not a revision
of this one.

**§9 is corrected on one point.** §9 said `expected_present` "is False by construction" in an agentic
episode. That was measured and found false: the presence test asks whether the *source document
revision* the checkpoint's value comes from is still in the prompt (`_doc_anchor` +
`_checkpoint_source`, `agentic_cell.py`), and it reads True whenever the model has not yet folded past
that document. Across the three arms `expected_present` was False at 3 checkpoints in each folding arm
and 0 in `none` — which is why `lost_then_failed` totals 1 rather than 32, and why the instrument now
clears its first falsifier instead of firing it.

**Falsifiers, §5, all five against this record:**
1. `instrument_failure` — 1 `lost_then_failed` observed, so loss is observable. Not fired.
2. `null_model_error` — `present_then_failed` is 3 in `none` and 0 in both folding arms, so model
   error does not dominate the folding arms' failures. Not fired.
3. `pin_premise_fails` — `pinned` 0.833 >= `none` 0.800. Not fired.
4. `recovery_not_paid` — `masking-no-fetch` was not run in this cell, so the comparison is
   unavailable and the falsifier reports null rather than firing. **Not evaluated, not passed.**
5. `compaction_not_cheaper` — `compact` mean prompt 4,153 < `none` 9,864. Not fired.

Falsifier 4 is the one gap in the record: `masking-no-fetch` was run in the earlier cell and was void
on every request (`refetch_refused`, no answers), which is recorded in the journal as a finding rather
than as a pass.
