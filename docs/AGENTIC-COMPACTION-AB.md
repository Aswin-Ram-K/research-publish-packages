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

### 3.1 Stage 1 — chain substitution (small build, reuses the replay runner)

Keep the scripted turns; add one field per turn: `question_from` naming a checkpoint id whose graded
answer is **interpolated into the next question's text**. Turn *n*'s question then reads
"…the symbol you reported at step *j* …", and the only way to answer it is to still hold the value learned
at step *j*.

- Horizon crossing is guaranteed **by construction**: the substituted value is learned before the fold and
  used after it.
- Failure mode is observable and gradable: a wrong prior answer makes the step unanswerable, and the
  chain end carries the checkpoint.
- Cost: a renderer in `run_longrun.py` (`turn_user`, `:417`/`:1757`) + a `chain` block in
  `check_pointer_fixtures.py`'s lint + a fixture builder pass. No new loop, no new grading path.
- Fixture: `tasks-v7/TX-04S.v1.json` (41 checkpoints, 14 declared mismatches, built today) is the
  starting point — 41 checkpoints/arm is the same order as the 48 that produced the ±4.2 pp band.
- Requests: 100 turns/arm × 4 arms = **400**, + warm-ups. Fits comfortably.

**What it still cannot say:** it cannot show *re-fetch* growth, because the harness still serves the
bodies it was told to serve. It shows only whether the fold *breaks the chain*.

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

1. **Stage 1:** if no arm produces a chain break, the instrument is not exercising horizon crossing and
   the fixture must change before stage 2 is built.
2. **Stage 1:** if breaks occur in every arm equally, the fold is not the mechanism and pinning has
   nothing to win.
3. **Stage 2:** if `pinned`'s `cost_units_per_verified_success` ≥ `compact`'s, the design's central claim
   (`COMPACTION-CACHE-DESIGN.md` §5.2) is wrong at real length under agentic work.
4. **Stage 2:** if `refetch_count` does not differ between A and B, the claimed mechanism is not operating
   and any cost difference is a prompt-layout artefact.
5. **Stage 2:** if the fold never fires (`compactions == 0` in an episode), that episode is **void**, not
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
