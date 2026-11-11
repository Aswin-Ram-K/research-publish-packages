"""AGENTIC-CONTRACT: the one definition of a stage-2 episode, its task, and its rows.

Stage 1 (the chain instrument on the replay runner) established that the replay runner
cannot measure recovery: `run_longrun.py:2405` states that at a checkpoint turn the tools
are OFF, the checkpoint contract says "emit exactly one line and nothing else", and the
fetch channel is serviced only for `arm_cd.ARM_D`.  The only turn that asks for a lost
value is therefore a tools-off checkpoint, so no arm can ever re-read at the moment it
matters.  Stage 2 replaces the replay with an episode loop in which the agent acts, the
tools stay ON, and the grade happens at the end.

This module is the contract every stage-2 piece imports.  It holds no logic beyond
validation, so the runner, the task builder and the analyser cannot drift apart.

TASK (one JSON file per task, `longrun/tasks-agentic/<TASK_ID>.v1.json`)::

    {
      "task_id": "AG-01",
      "version": "AG-01.v1",
      "root": "experiments/ptr-engine",          # snapshot root, relative to the repo
      "statement": "...",                        # the system prompt's task paragraph
      "steps": [                                 # work turns, in order
        {"prompt": "...", "expect_tool": true},
        ...
      ],
      "final_question": "...",                   # asked with the tools still ON
      "expected": "4017",                        # the graded value
      "answer_form": "NUM",                      # NUM | TEXT
      "fact": {                                  # the value the episode must carry
        "value": "4017",
        "introduced_at_step": 2,                 # 1-based index into steps
        "source_path": "ptr_engine/tx05_constants.py"
      },
      "checkpoints": [                           # optional mid-episode probes
        {"step": 3, "question": "...", "expected": "4011", "fact_id": "SYM_01"}
      ]
    }

ROW (one JSON object per request, appended to `measure/rows-agentic-<arm>-<stamp>.jsonl`)::

    {
      "run_id": "...", "arm": "...", "task_id": "AG-01", "rep": 1,
      "step": 3, "kind": "work" | "final" | "summary",
      "prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0,
      "tool_calls": [{"name": "read_file", "arguments": {...}, "ok": true, "bytes": 0}],
      "fold_event": false, "fold_kind": null, "dropped_turns": 0, "pinned_tokens": 0,
      "answer": null, "expected": null, "verified": null, "expected_present": null,
      "ts": "...", "model": "...", "temperature": 0.0
    }

`expected_present` is the E3 field: whether the graded value appears in the prompt that
produced this row, computed by the runner from the exact message list it sent.  It is
NEVER defaulted to true — an unknown is null, and the analyser treats null as "not
evidence", never as a pass.

ARMS (five, and the reason each exists)::

    none                  no policy; the transcript grows and nothing is dropped
    masking-no-fetch      old tool results replaced by a pointer marker, no fetch channel
    pinned                pinned facts kept verbatim, the rest folded
    bounded-context-fetch fold + a fetch channel that can re-read a dropped body
    compact               fold + a model-written summary of the dropped turns

`spcc` is deliberately absent: it is the layer compiler over a fixture's world index, and
an episode loop has no world index to compile.  `compact` is the arm every real system
runs, so it takes the slot.
"""

from __future__ import annotations

import json
import os

ARMS = ("none", "masking-no-fetch", "pinned", "bounded-context-fetch", "compact")

#: Arms whose episodes buy an extra request per fold (the summary call).
SUMMARY_ARMS = ("compact",)

#: The tool surface an episode may declare.  `grep` is bounded: it returns at most
#: GREP_MAX_MATCHES lines and never the whole file.
TOOL_NAMES = ("read_file", "grep")
READ_MAX_LINES = 200
READ_MAX_CHARS = 8000
GREP_MAX_MATCHES = 40
GREP_MAX_CHARS = 4000

ANSWER_FORMS = ("NUM", "TEXT")

REQUIRED_TASK_KEYS = ("task_id", "version", "root", "statement", "steps",
                      "final_question", "expected", "answer_form", "fact")
REQUIRED_ROW_KEYS = ("run_id", "arm", "task_id", "rep", "step", "kind",
                     "prompt_tokens", "tool_calls", "fold_event", "fold_kind",
                     "answer", "expected", "verified", "expected_present", "ts")


class ContractError(ValueError):
    """A task or a row that does not satisfy this contract."""


def validate_task(task: dict) -> dict:
    """Return the task unchanged, or raise ContractError naming the first defect."""
    if not isinstance(task, dict):
        raise ContractError("task is not an object: %r" % (type(task).__name__,))
    for key in REQUIRED_TASK_KEYS:
        if key not in task:
            raise ContractError("task %r is missing required key %r"
                                % (task.get("task_id"), key))
    if task["answer_form"] not in ANSWER_FORMS:
        raise ContractError("task %r answer_form %r is not one of %r"
                            % (task["task_id"], task["answer_form"], ANSWER_FORMS))
    steps = task["steps"]
    if not isinstance(steps, list) or not steps:
        raise ContractError("task %r steps must be a non-empty list" % (task["task_id"],))
    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict) or not isinstance(step.get("prompt"), str):
            raise ContractError("task %r step %d has no prompt string"
                                % (task["task_id"], i))
    fact = task["fact"]
    if not isinstance(fact, dict) or "value" not in fact:
        raise ContractError("task %r fact has no value" % (task["task_id"],))
    introduced = fact.get("introduced_at_step")
    if not isinstance(introduced, int) or not (1 <= introduced <= len(steps)):
        raise ContractError("task %r fact.introduced_at_step %r is outside 1..%d"
                            % (task["task_id"], introduced, len(steps)))
    # The graded value must not be restated in the final question, or no fold could
    # ever destroy it and the episode measures nothing.
    if str(fact["value"]) in str(task["final_question"]):
        raise ContractError("task %r final_question restates the graded value %r"
                            % (task["task_id"], fact["value"]))
    for cp in task.get("checkpoints") or []:
        if not isinstance(cp, dict) or "step" not in cp or "expected" not in cp:
            raise ContractError("task %r has a checkpoint without step/expected"
                                % (task["task_id"],))
        if not (1 <= int(cp["step"]) <= len(steps)):
            raise ContractError("task %r checkpoint step %r is outside 1..%d"
                                % (task["task_id"], cp["step"], len(steps)))
    return task


def validate_row(row: dict) -> dict:
    """Return the row unchanged, or raise ContractError naming the first defect."""
    if not isinstance(row, dict):
        raise ContractError("row is not an object: %r" % (type(row).__name__,))
    for key in REQUIRED_ROW_KEYS:
        if key not in row:
            raise ContractError("row for %r step %r is missing required key %r"
                                % (row.get("task_id"), row.get("step"), key))
    if row["arm"] not in ARMS:
        raise ContractError("row arm %r is not one of %r" % (row["arm"], ARMS))
    if row["kind"] not in ("work", "final", "summary"):
        raise ContractError("row kind %r is not work/final/summary" % (row["kind"],))
    if not isinstance(row["tool_calls"], list):
        raise ContractError("row tool_calls must be a list, got %r"
                            % (type(row["tool_calls"]).__name__,))
    return row


def load_task(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return validate_task(json.load(fh))


def load_tasks(directory: str) -> list:
    """Every `*.json` in `directory`, sorted by task_id, each validated."""
    out = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        out.append(load_task(os.path.join(directory, name)))
    return out


def episode_cost(task: dict, arm: str, folds: int = 0) -> int:
    """Requests one episode of `task` costs on `arm`.

    One per work step, one for the final question, plus one summary call per fold on a
    summary arm.  `folds` is an estimate the caller supplies; the runner's dry run
    reports the same number it will spend.
    """
    base = len(task["steps"]) + 1
    if arm in SUMMARY_ARMS:
        base += max(0, int(folds))
    return base
