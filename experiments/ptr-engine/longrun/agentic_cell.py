#!/usr/bin/env python3
"""agentic_cell.py — Stage-2 episode loop: the MODEL, not a fixture, decides what to read.

WHY THIS FILE EXISTS
--------------------
Every compaction cell in this repo before stage 2 is a *scripted replay*: the turn list is
fixed by the fixture, each turn's question is the fixture's, and each turn's tool bodies
are baked at build time.  A fold can therefore change the prompt an arm sees but never the
trajectory, so the design's own mechanism — *an agent that lost its journal pays for it in
work* — cannot be measured there (``docs/AGENTIC-COMPACTION-AB.md`` §1, and
``run_longrun.py:2405``: at a checkpoint turn the tools are OFF, so no arm can re-read at
the moment it matters).

This module is the instrument that can: one episode = one task, one arm, one rep, in which
the model chooses every read and the episode ends when it answers or the budget runs out.
It is plan step 8 (``agentic-compaction-ab-plan.md``).

THE TASK IS A ``consonance.longrun-fixture/2``
---------------------------------------------
One task schema is accepted.  ``run_longrun.load_fixture:164`` +
``grade_v5.derive_truth:603`` already read it, so the loader adds nothing but the schema
check: a document whose ``schema`` is not ``consonance.longrun-fixture/2`` is refused by
name (``unsupported_task_schema: <schema>``), never coerced into one.  The bespoke
``agentic-contract`` shape lost the ruling (Main, 2026-11-11) and is gone; a second task
shape would be a second convention for the same measurement.

A task is read as follows:

* ``statement`` / ``fixture["system_prompt"]`` -> the L0 goal paragraph.
* ``run_longrun.index_lines(fixture)`` -> L0's world index (refs, digests, byte lengths;
  no fact values).  It is in L0, not L1, so all five arms see the same world and the only
  difference between them is the fold policy.  A contract task has no fixture world, so
  its index is empty and the model reads the snapshot with tools.
* ``turns[i]["question"]`` -> the work text of step ``i+1``.
* ``turns[i]["tool_outputs"]`` -> IGNORED.  An episode executes the model's real tool
  calls against the snapshot instead of replaying baked bodies; that is the whole
  difference between this instrument and the replay.
* ``checkpoints`` -> the graded probes, each carrying ``turn``, ``kind``, ``expected`` and
  a ``derivation`` — exactly the ``truth`` mapping ``grade_v5.grade_cell`` grades.

WHAT IS REUSED, NEVER REIMPLEMENTED
-----------------------------------
* the request            — ``client.send_chat`` (the ONE HTTP client in this repo)
* the tool surface       — ``client.tools_body_members`` + ``run_longrun``'s grep bounds
* the tool executor      — ``run_longrun.execute_tool_call(call, root)`` (dispatches
                           ``read_file`` and ``grep``)
* the call parser        — ``run_longrun.calls_from_response`` (structured first, text second)
* the answer parser      — ``grade_v5.parse_answer_contract``
* the verdict            — ``grade_v5.grade_cell``
* the bill               — ``score_longrun.billed_of``
* the quota              — ``cell.PROJECT_QUOTA`` and ``cell._count_rows``
* the fold               — ``arm_cd.SpccArmState`` / ``arm_cd.PinnedArmState`` (the layer
                           compiler's journal drop) and ``arm_cd.ArmCDState.mask_old_turns``
                           (the masking window).  This file contains NO fold logic.

THE IMMUTABLE LAYER CARRIES THE GOAL (stage-1 lesson, 2026-11-11)
-----------------------------------------------------------------
Stage 1 failed because a pointer named a step whose symbol had been folded out: the model
lost the *locator* and could not choose what to fetch (0/6 carry in every arm; the fetch
arm paid 64 refetch rounds to answer with the wrong symbol).  The same defect would make
every episode here void, so the task statement, the snapshot index and EVERY checkpoint
question live in L0 (the run's system text) — never in the foldable journal.  Only the
per-step work, the model's replies and the tool results ride the journal.  Each request
records ``expected_present`` (measured from the exact message list sent, never asserted)
so a later reader can tell a fold-induced failure from a model error.

ARMS (five, and what each one is here)
--------------------------------------
``none``                  no policy: the transcript grows and nothing is dropped.
``masking-no-fetch``      ``ArmCDState.mask_old_turns``: tool results older than
                          ``--window-turns`` become ``[MASKED <ref>]``, and a body already
                          served is NOT re-servable — the arm that cannot recover.
``pinned``                ``PinnedArmState``: the goal is pinned, the journal folds, and a
                          body already served is not re-servable — pinning alone.
``bounded-context-fetch`` ``SpccArmState``: the journal folds and every read is re-servable
                          — the recovery arm.
``compact``               ``PinnedArmState`` plus a MODEL-WRITTEN summary of the dropped
                          turns, pinned at each fold.  One extra request per fold.

The re-read rule is the replay's own: only ``bounded-context-fetch`` had its fetch channel
serviced (``run_longrun.py:3862-3900``), so only it may re-read a body it already had.  A
first read of a new path is never a re-fetch and is always served.

ROWS
----
Two files, because the contract and the episode summary answer different questions:

* ``measure/rows-agentic-<arm>-<stamp>.jsonl`` — ONE ROW PER REQUEST, validated by
  :func:`validate_row`.  This is what the analyser consumes.
* ``--out`` (default ``measure/AGENTIC-<date>.jsonl``) — ONE ROW PER EPISODE: ``solved``,
  ``checkpoints``, ``steps_used``, ``requests``, ``refetch_count``, ``compactions``,
  ``evicted``, ``prompt_tokens_max``, ``billed_tokens``, plus the attribution fields
  (``verdict``, ``goal_present``, ``fact_present``, ``fold_mechanism``).

``compactions`` is the layer compiler's own count, so it is 0 on ``masking-no-fetch`` and
``none`` — those arms do not fold, they mask / do nothing, and ``fold_mechanism`` says
which.  Design §5 falsifier 7 ("``compactions == 0`` ⇒ the episode is void") therefore
applies to ``fold_mechanism == "journal-drop"`` only; the row's ``verdict`` implements
exactly that.

BUDGET
------
This cell calls the client directly, so it does not inherit the runner's cap gate and
must carry its own.  Before the first request it reads the ledger's spent count the way
``cell.py:461`` does and refuses when ``spent + planned_max > cell.PROJECT_QUOTA``, naming
spent, quota and the planned maximum.  A live run also requires ``--budget`` and aborts if
the actual request count would exceed it.  The planned maximum is written into every
episode row, so the record states what was authorised.

CLI
---
``--tasks <dir> --arms <list> --reps 2 --steps 16 --max-requests 20 --root <snapshot>
--snapshot-manifest <path> --out measure/AGENTIC-<date>.jsonl --budget <n>``

``--offline ROWS_JSONL`` re-grades an existing per-request row file into episode rows and
sends nothing, mirroring ``cell.py --offline``.

No request is sent by any test in this repo: the tests inject a scripted ``send``.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_LONGRUN_HERE = os.path.dirname(os.path.abspath(__file__))
if _LONGRUN_HERE not in sys.path:
    sys.path.insert(0, _LONGRUN_HERE)
_PTR_ENGINE_ROOT = os.path.dirname(_LONGRUN_HERE)
if _PTR_ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _PTR_ENGINE_ROOT)

import agentic_contract  # noqa: E402  the ONE row contract (ARMS, REQUIRED_ROW_KEYS, validate_row)
import arm_cd  # noqa: E402  the fold machinery (SpccArmState / PinnedArmState / ArmCDState)
import cell as cell_mod  # noqa: E402  PROJECT_QUOTA + the ledger row counter
import client  # noqa: E402  the ONE HTTP client
import grade_v5  # noqa: E402  the ONE answer parser + verdict + truth derivation
import run_longrun  # noqa: E402  the ONE fixture loader, index renderer, tool executor
import score_longrun  # noqa: E402  the ONE bill rule
from ptr_engine import layers  # noqa: E402  the ONE L0 renderer

# ------------------------------------------------------------------ constants
#: The five arms, in the order the design lists them.  ``spcc`` is deliberately absent:
#: it is the layer compiler over a fixture's world index, and an episode loop has no world
#: index to compile (docs/AGENTIC-COMPACTION-AB.md, "The arm set is five").  Declared in
#: ``agentic_contract`` and imported, so the analyser and the cell cannot drift apart.
ARMS = agentic_contract.ARMS
ARM_NONE, ARM_MASK, ARM_PINNED, ARM_FETCH, ARM_COMPACT = ARMS

#: Arms whose episodes buy an extra request per fold (the summary call).
SUMMARY_ARMS = (ARM_COMPACT,)

#: The one task schema this cell accepts.  Anything else is refused by name.
FIXTURE_SCHEMA = "consonance.longrun-fixture/2"

DEFAULT_STEPS = 16
DEFAULT_MAX_REQUESTS = 20
DEFAULT_REPS = 2
#: The episode's fold distance.  NOT the replay runner's ``COMPACT_EVERY`` (24): a
#: 16-step episode that never folds is VOID by design §5 falsifier 7, so the episode
#: instrument folds at 8 steps and the fold is guaranteed to fire inside the budget.
DEFAULT_COMPACT_EVERY = 8
#: Design §3.2: "tool results older than 8 turns".
DEFAULT_WINDOW_TURNS = 8
#: The window the pin arms fold at when a fixture declares none.  A v2 fixture always
#: carries ``window_tokens``, so this default never overrides one; it exists so a fixture
#: that omits the key still gets a number to take ``FOLD_AT_FRACTION`` of rather than a
#: ``TypeError``.  4096 is the stage-1 chain fixture's window.
DEFAULT_WINDOW_TOKENS = 4096

ANSWER_PREFIX = "ANSWER:"
GENERATION = "gen-8"

#: The answer contract rendered into L0/L4.  One line, four forms — the same vocabulary
#: ``grade_v5.parse_answer_contract`` accepts, so a compliant reply is always gradeable.
ANSWER_CONTRACT = (
    "Reply with EITHER one tool call OR exactly one answer line.\n"
    "Tool call: <tool_call>{\"path\": \"<relpath>\", \"start_line\": 1, \"end_line\": 40}</tool_call>\n"
    "Tool call: <tool_call>{\"pattern\": \"<regex>\", \"glob\": \"*.py\"}</tool_call>\n"
    "Answer:    ANSWER: NUM <int> | ANSWER: TEXT <value> | ANSWER: NONE"
)

#: The summary request ``compact`` buys at each fold.  It asks for the DURABLE content of
#: the dropped turns only — names, values, paths — because that is what a fold must not
#: lose and what the arm is being measured on.
SUMMARY_PROMPT = (
    "Summarise the work below in at most 6 lines. Keep every constant name and its value, "
    "every file path, and every question you answered. No commentary, no preamble.\n\n"
)

#: The per-request row's required keys.  The analyser reads these; a row missing one is a
#: defect in this file, not in the data, so it is refused at write time.  Declared in
#: ``agentic_contract`` and imported — one definition for the writer and the analyser.
REQUIRED_ROW_KEYS = agentic_contract.REQUIRED_ROW_KEYS

#: A task whose ``system_prompt`` names none of these cannot fetch, so an episode against
#: it would spend its whole budget answering from the index alone.  Refused by name
#: (``prompt_declares_no_tool``) before the first request rather than measured as a
#: model failure — stage 1's TX-05D showed the schema on the wire is not sufficient, but
#: a prompt that never mentions the tool is fatal.
TOOL_DECLARATIONS = ("read_file", "grep", "tool")

#: The client's own body builder, captured BEFORE any patch, so
#: :func:`episode_tools_body_members` can extend it instead of recursing into itself.
_ORIGINAL_TOOLS_BODY_MEMBERS = client.tools_body_members


class TaskError(ValueError):
    """A task file this cell cannot run.  Raised, never guessed around."""


class SnapshotMismatch(RuntimeError):
    """The snapshot on disk is not the snapshot the manifest froze."""


class BudgetRefusal(RuntimeError):
    """The planned or actual request count would exceed the authorised budget."""


#: A per-request row that does not satisfy :data:`REQUIRED_ROW_KEYS`.  The contract's own
#: error, so a caller catching it catches the same class the analyser raises.
RowError = agentic_contract.ContractError


# ------------------------------------------------------------------ task loading
@dataclass(frozen=True)
class Task:
    """One v2 fixture, with its checkpoints already derived and graded-ready."""

    task_id: str
    fixture: dict
    statement: str
    turns: Tuple[dict, ...]
    checkpoints: Tuple[dict, ...]
    index_text: str
    window_tokens: int = 0
    path: str = ""

    @property
    def n_turns(self) -> int:
        return len(self.turns)

    @property
    def final_turn(self) -> int:
        """The turn of the LAST checkpoint — the episode's early-stop condition."""
        return max(int(cp["turn"]) for cp in self.checkpoints)

    def checkpoint_at(self, step: int) -> Optional[dict]:
        for cp in self.checkpoints:
            if int(cp["turn"]) == int(step):
                return cp
        return None

    def question_at(self, step: int) -> str:
        """The work text of ``step`` (1-based).  Past the turn list, a step marker."""
        if 1 <= step <= self.n_turns:
            return str(self.turns[step - 1].get("question") or "")
        return "STEP %d: continue." % step


def _task_from_fixture(path: str) -> Task:
    """A ``consonance.longrun-fixture/2`` document -> :class:`Task` (the original path)."""
    fixture = run_longrun.load_fixture(path)
    checkpoints = grade_v5.derive_truth(fixture)
    if not checkpoints:
        raise TaskError("%s: derive_truth returned no checkpoints" % path)
    for cp in checkpoints:
        if int(cp.get("turn", -1)) < 1:
            raise TaskError("%s: checkpoint %r has no positive turn"
                            % (path, cp.get("id")))
    return Task(task_id=str(fixture["task_id"]), fixture=fixture,
                statement=str(fixture.get("system_prompt") or ""),
                turns=tuple(fixture["turns"]), checkpoints=tuple(checkpoints),
                index_text=run_longrun.index_lines(fixture),
                window_tokens=int(fixture.get("window_tokens") or 0), path=path)


def load_task(path: str) -> Task:
    """One task file -> :class:`Task`.  Only ``consonance.longrun-fixture/2`` is accepted.

    The bespoke ``agentic-contract`` schema lost the ruling (Main, 2026-11-11): every
    fixture in ``tasks-agentic/`` is a v2 replay fixture, so a second task shape would be
    a second convention for the same measurement.  A document whose ``schema`` is not v2
    is refused by name — ``unsupported_task_schema: <schema>`` — never coerced into one.
    """
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    schema = doc.get("schema") if isinstance(doc, dict) else None
    if schema != FIXTURE_SCHEMA:
        raise TaskError("unsupported_task_schema: %s (task %s; only %s is accepted)"
                        % (schema, os.path.basename(path), FIXTURE_SCHEMA))
    return _task_from_fixture(path)


def load_tasks(tasks_dir: str) -> List[Task]:
    """Every ``*.json`` in ``tasks_dir``, sorted by filename.  Refuses an empty set."""
    if not os.path.isdir(tasks_dir):
        raise TaskError("--tasks is not a directory: %s" % tasks_dir)
    paths = sorted(os.path.join(tasks_dir, n) for n in os.listdir(tasks_dir)
                   if n.endswith(".json"))
    if not paths:
        raise TaskError("--tasks holds no *.json task files: %s" % tasks_dir)
    return [load_task(p) for p in paths]


# ------------------------------------------------------------------ snapshot
def verify_snapshot_manifest(root: str, manifest_path: str) -> dict:
    """Re-hash every manifest entry under ``root``; refuse on any difference.

    Accepts both manifest shapes the builder may write: ``{"files": {rel: sha}}`` and a
    flat ``{rel: sha, "root_sha256": ...}``.  A missing file and a changed file are the
    same refusal (``snapshot_manifest_mismatch: <relpath>``) because both mean the read
    the model is about to make is not the read the task was built against.
    """
    with open(manifest_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc, dict):
        raise SnapshotMismatch("snapshot_manifest_invalid: %s" % manifest_path)
    files = doc.get("files")
    if not isinstance(files, dict):
        files = {k: v for k, v in doc.items()
                 if isinstance(v, str) and k != "root_sha256"}
    if not files:
        raise SnapshotMismatch("snapshot_manifest_empty: %s" % manifest_path)
    for rel in sorted(files):
        want = files[rel]
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            raise SnapshotMismatch("snapshot_manifest_mismatch: %s" % rel)
        with open(path, "rb") as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
        if got != want:
            raise SnapshotMismatch("snapshot_manifest_mismatch: %s" % rel)
    # ``files`` is the verified mapping itself, not a count: the index renderer needs the
    # paths, and a caller that only wants the size reads ``count``.
    return {"files": dict(files), "count": len(files),
            "root_sha256": doc.get("root_sha256")}


# ------------------------------------------------------------------ tool surface
def grep_tool_schema() -> dict:
    """The bounded ``grep`` schema, with every bound read from the executor's constants.

    ``client.tools_body_members`` knows ``read_file`` and ``fetch``; the episode's second
    tool is ``grep``, whose executor and bounds live in ``run_longrun`` (``GREP_MAX_HITS``,
    ``GREP_MAX_PATTERN_CHARS``, ``GREP_MAX_LINE_CHARS``, ``GREP_DEFAULT_GLOB``).  The
    schema is BUILT from those constants rather than restating them, so the description
    the model reads cannot drift from the bound the executor enforces.
    """
    return {
        "type": "function",
        "function": {
            "name": run_longrun.GREP_TOOL_NAME,
            "description": (
                "Search the workspace for a regular expression. Returns at most %d "
                "`path:line: text` hits, each truncated to %d characters. Use it to "
                "locate a symbol instead of re-reading whole files."
                % (run_longrun.GREP_MAX_HITS, run_longrun.GREP_MAX_LINE_CHARS)),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Python regular expression, at most %d characters"
                                       % run_longrun.GREP_MAX_PATTERN_CHARS},
                    "glob": {
                        "type": "string",
                        "description": "Basename glob, e.g. *.py (default %s)"
                                       % run_longrun.GREP_DEFAULT_GLOB},
                    "max_hits": {
                        "type": "integer", "minimum": 1,
                        "maximum": run_longrun.GREP_MAX_HITS},
                },
                "required": ["pattern"],
            },
        },
    }


def episode_tools_body_members(cfg) -> dict:
    """The episode's tool surface: the client's own members plus bounded ``grep``.

    ``read_file`` comes from ``client.tools_body_members`` unchanged (one definition of
    that schema in the repo).  ``grep`` is appended only when the client did not already
    provide it, so the day the client learns the schema this function defers to it.
    """
    members = _ORIGINAL_TOOLS_BODY_MEMBERS(cfg)
    names = client.tool_names(cfg)
    if run_longrun.GREP_TOOL_NAME not in names:
        return members
    tools = list(members.get("tools") or [])
    have = {(t.get("function") or {}).get("name") for t in tools if isinstance(t, dict)}
    if run_longrun.GREP_TOOL_NAME not in have:
        tools.append(grep_tool_schema())
    members["tools"] = tools
    members.setdefault("tool_choice", client.tools_choice(cfg))
    return members


@contextlib.contextmanager
def grep_on_the_wire():
    """Hand the model the ``grep`` schema through the client's OWN body builder.

    ``client.send_chat`` builds its body with ``client.request_body``, which calls
    ``client.tools_body_members``.  Extending that seam for the duration of the episode
    keeps ONE body builder and ONE HTTP client; the alternative — a second body builder
    beside ``send_chat`` — is exactly the duplication this repo has paid for before
    (``docs/TOOL-CHANNEL-ROOT-CAUSE.md``).  Restored in ``finally``, so a caller that
    runs an episode inside a larger process sees the client unchanged afterwards.
    """
    client.tools_body_members = episode_tools_body_members
    try:
        yield
    finally:
        client.tools_body_members = _ORIGINAL_TOOLS_BODY_MEMBERS


# ------------------------------------------------------------------ tool helpers
def resolve_read_path(path: str, root: str, allow_dir: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """``(target, reason)`` for one read, delegating to the runner's own resolver.

    ``run_longrun.resolve_read_path_base`` is the ONE path policy (absolute, ``~``, ``..``,
    realpath escape, secret-shaped basenames).  This wrapper only adds the ``allow_dir``
    switch the grep tool needs, so a directory is a legal grep root and still an illegal
    read.
    """
    target, reason, _base = run_longrun.resolve_read_path_base(path, root, None,
                                                               allow_dir=allow_dir)
    if target is None:
        return None, reason
    if os.path.isdir(target) and not allow_dir:
        return None, "path_not_found"
    return target, None


def grep_text(root: str, pattern: str, glob: str = "") -> Tuple[str, dict]:
    """``(text, record)`` for one bounded grep, delegating to the runner's executor."""
    call = {"tool": run_longrun.GREP_TOOL_NAME, "pattern": pattern,
            "glob": glob or run_longrun.GREP_DEFAULT_GLOB}
    res = run_longrun.execute_tool_call(call, root)
    return res.get("text") or "", res.get("record") or {}


# ------------------------------------------------------------------ prompt helpers
def prompt_text(messages) -> str:
    """Every message's content, joined — the exact text the model was sent."""
    return "\n".join(str(m.get("content") or "") for m in (messages or []))


def _system_text(task: Task) -> str:
    """L0's system text: the goal, the world index and EVERY checkpoint question.

    All three are immutable for the episode.  The questions are here, not in the journal,
    because a fold that erases a question erases the thing the step is graded on (the
    stage-1 failure, 2026-11-11).
    """
    lines = ["TASK %s" % task.task_id, task.statement, "", "INDEX",
             task.index_text.rstrip("\n"), "", "CHECKPOINTS"]
    for cp in task.checkpoints:
        lines.append("- turn %d (%s): %s"
                     % (int(cp["turn"]), cp.get("id") or "cp", cp.get("question") or ""))
    return "\n".join(lines)


def check_prompt_declares_tool(task: Task) -> str:
    """Refuse a task whose prompt never names the tool, by name.

    Stage 1's TX-05D had the schema on the wire and three arms still made zero calls, so
    the schema alone is not sufficient — but a prompt that never mentions ``read_file`` or
    ``grep`` is fatal: the episode would spend its whole budget answering from the index.
    Refusing here costs nothing; discovering it after 20 requests costs the cell.

    A CONTRACT task declares the same fact in the contract's own vocabulary: its
    ``statement`` is a goal paragraph, and each step carries ``expect_tool``.  A task whose
    steps declare a tool is therefore accepted on that declaration, not on a text match
    the statement was never written to satisfy.
    """
    text = str(task.statement or "")
    for name in TOOL_DECLARATIONS:
        if name in text:
            return name
    if task.fixture.get("expect_tool"):
        return "expect_tool"
    raise TaskError("prompt_declares_no_tool: task %s system_prompt names none of %s; "
                    "the episode could not fetch" % (task.task_id, list(TOOL_DECLARATIONS)))


def _run_dict(task: Task, system_text: str, model: str) -> dict:
    """The run mapping the layer compiler renders L0 from (``layers._l0_text``)."""
    return {
        "system": system_text,
        "tool_schema": None,
        "answer_grammar": ANSWER_CONTRACT,
        "model": model,
        "fixture": task.task_id,
        "generation": GENERATION,
        "run_id": "agentic:%s" % task.task_id,
        "contract_line": ANSWER_CONTRACT,
    }


def _goal_present(prompt: str, statement: str) -> bool:
    """MEASURED: is the goal still in the prompt this step?  Never asserted."""
    text = (statement or "").strip()
    return bool(text) and text in prompt


def _value_present(prompt: str, value) -> bool:
    """MEASURED: is a graded value in the prompt at grading time?

    A numeric value is matched on digit boundaries so a digest that happens to contain
    the digits is not read as the fact being present; text is matched literally.
    """
    text = str(value)
    if re.fullmatch(r"-?\d+", text):
        return re.search(r"(?<!\d)%s(?!\d)" % re.escape(text), prompt) is not None
    return text in prompt


def _estimate_tokens(text: str) -> int:
    """The compiler's own size estimate (``layers.CHARS_PER_TOKEN``), not a word count."""
    return int(len(text) / layers.CHARS_PER_TOKEN)


def _block_path(block: str) -> str:
    """The path a ``<tool_result …>`` block was served from, or ``""``."""
    m = re.search(r'path="([^"]+)"', block or "")
    return m.group(1) if m else ""


# ------------------------------------------------------------------ arms
class EpisodeArm:
    """One arm's prompt policy for one episode.

    ``observe`` records what the step produced; ``render`` consumes it and returns the
    next prompt.  The split exists because a tool result is produced AFTER the request
    that asked for it, so it can only enter the next prompt.
    """

    name = ""
    fold_mechanism = ""
    #: May the model re-read a body it was already served?  Only the recovery arm may.
    allow_refetch = False

    def __init__(self, task: Task, system_text: str, model: str = "offline-model"):
        self.task = task
        self.system_text = system_text
        self.model = model
        self.run = _run_dict(task, system_text, model)
        self._pending: Optional[Tuple[str, List[str]]] = None
        self.served: set = set()
        self.refused_refetch = 0

    # -- lifecycle -------------------------------------------------------
    def begin(self) -> None:
        """Called once, before step 1."""

    def observe(self, step: int, reply: str, blocks: List[str]) -> None:
        self._pending = (reply or "", list(blocks or []))

    def render(self, step: int, work: str) -> str:
        raise NotImplementedError

    def refetch_allowed(self, path: str) -> bool:
        """A first read is never a re-fetch; a second read of the same path is."""
        if self.allow_refetch:
            return True
        return path not in self.served

    def note_served(self, path: str) -> None:
        if path:
            self.served.add(path)

    # -- evidence --------------------------------------------------------
    @property
    def compactions(self) -> int:
        return 0

    @property
    def evicted(self) -> int:
        return 0

    @property
    def fold_event(self) -> bool:
        return False

    @property
    def fold_kind(self) -> Optional[str]:
        return None

    @property
    def dropped_turns(self) -> int:
        return 0

    @property
    def pinned_tokens(self) -> int:
        return 0

    def wants_summary(self) -> bool:
        """``compact`` buys a summary request when a fold has just fired."""
        return False

    def summary_prompt(self) -> str:
        return ""

    def apply_summary(self, text: str) -> None:
        """No-op for the arms that do not summarise."""


class _CompilerArm(EpisodeArm):
    """Shared body for the arms rendered by the layer compiler (pinned, fetch, compact)."""

    fold_mechanism = "journal-drop"

    def __init__(self, task, system_text, model="offline-model", compact_every=None,
                 window_tokens=None):
        super().__init__(task, system_text, model)
        self.compact_every = compact_every
        self.window_tokens = int(window_tokens or task.window_tokens or 0)
        self._last = None
        self._pre_journal: List[str] = []
        self._folded_this_step = False
        self._state = self._make_state()

    def _make_state(self):
        raise NotImplementedError

    def begin(self) -> None:
        self._pin_goal()

    def _pin_goal(self) -> None:
        """No-op for the arms that do not carry PINS."""

    def render(self, step: int, work: str) -> str:
        if self._pending is not None:
            reply, blocks = self._pending
            self._pending = None
            # A reply and a tool result are TRANSCRIPT content: they ride the journal
            # line (``add_delivery``), so they persist in L2 until the fold and are gone
            # after it.  That is the mechanism under test; ``add_fetch`` would put them
            # in L3 for one turn only and no fold could ever cost anything.
            if reply:
                self._state.add_delivery(reply)
            for block in blocks:
                self._state.add_delivery(block)
        before = int(getattr(self._state.state, "compactions", 0) or 0)
        self._pre_journal = list(getattr(self._state.state, "journal", []) or [])
        prompt = self._state.build(step, work)
        self._last = prompt
        self._folded_this_step = int(getattr(prompt, "compactions", 0) or 0) > before
        return str(prompt)

    @property
    def compactions(self) -> int:
        return int(getattr(self._last, "compactions", 0) or 0)

    @property
    def fold_event(self) -> bool:
        return bool(self._folded_this_step)

    @property
    def fold_kind(self) -> Optional[str]:
        if not self._folded_this_step:
            return None
        return str(getattr(self._last, "fold_trigger", None) or "interval")

    @property
    def dropped_turns(self) -> int:
        """Journal lines the compiler's own fold records say were dropped.

        Read from the fold pins (``P<n>|fold|T<t>|<n> turns dropped at epoch <e>``) — the
        compiler's record, not a second count kept here.
        """
        total = 0
        for line in getattr(self._state.state, "pins", []) or []:
            m = re.search(r"\|(\d+) turns dropped at epoch", str(line))
            if m:
                total += int(m.group(1))
        return total

    @property
    def evicted(self) -> int:
        return self.dropped_turns

    @property
    def pinned_tokens(self) -> int:
        return arm_cd._pin_tokens(getattr(self._state.state, "pins", []) or [])


class FetchArm(_CompilerArm):
    """``bounded-context-fetch`` — ``SpccArmState``: the journal folds, reads re-serve."""

    name = ARM_FETCH
    allow_refetch = True

    def _make_state(self):
        return arm_cd.SpccArmState(fixture=self.task.fixture, run=self.run,
                                   index_lines=[], compact_every=self.compact_every)


class PinnedArm(_CompilerArm):
    """``pinned`` — ``PinnedArmState``: the goal is pinned, the journal folds, no re-read."""

    name = ARM_PINNED

    def _make_state(self):
        return arm_cd.PinnedArmState(fixture=self.task.fixture, run=self.run,
                                     index_lines=[], compact_every=self.compact_every,
                                     fold_at_fraction=arm_cd.FOLD_AT_FRACTION)

    def _pin_goal(self) -> None:
        """Pin the goal: the design's "PLAN + facts, no summary call" (arm C)."""
        try:
            self._state.pin("goal", self.task.statement)
        except arm_cd.PinCapExceeded:
            # A goal that does not fit the pin budget is a task defect, not a run
            # failure: the goal is still in L0, so the episode stays runnable and the
            # refusal is visible in the row's ``pin_refused``.
            self.pin_refused = True


class CompactArm(PinnedArm):
    """``compact`` — the same fold, plus a MODEL-WRITTEN summary pinned at each fold.

    The summary is the arm's whole mechanism: a real system does not drop the journal, it
    replaces it with a summary, and the question is whether that summary keeps the fact.
    It costs one extra request per fold, which the episode counts like any other request.
    """

    name = ARM_COMPACT

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.summary_refused = 0
        self.summaries = 0

    def wants_summary(self) -> bool:
        return self._folded_this_step and bool(self._pre_journal)

    def summary_prompt(self) -> str:
        return SUMMARY_PROMPT + "\n".join(self._pre_journal)

    def apply_summary(self, text: str) -> None:
        body = (text or "").strip()
        if not body:
            self.summary_refused += 1
            return
        try:
            self._state.pin("fold", body)
            self.summaries += 1
        except arm_cd.PinCapExceeded:
            self.summary_refused += 1


class MaskArm(EpisodeArm):
    """``masking-no-fetch`` — ``ArmCDState``: old tool results become ``[MASKED <ref>]``.

    The masking implementation is ``arm_cd.ArmCDState.mask_old_turns``, which reads a
    fixture-shaped ``turns`` list.  The episode presents itself as that list — one turn
    per step, carrying the step's tool result — so the window, the marker and the ref are
    the arm's own, not a second implementation of them.
    """

    name = ARM_MASK
    fold_mechanism = "mask"

    def __init__(self, task, system_text, model="offline-model",
                 window_turns=DEFAULT_WINDOW_TURNS):
        super().__init__(task, system_text, model)
        self.window_turns = int(window_turns)
        self.fixture = {"task_id": task.task_id, "turns": []}
        self.state = arm_cd.ArmCDState(fixture=self.fixture, window_turns=self.window_turns)
        self.blocks: List[dict] = []
        self.masked_ref: Dict[int, str] = {}
        self._masked_total = 0
        self.l0 = layers._l0_text(self.run)

    def render(self, step: int, work: str) -> str:
        if self._pending is not None:
            reply, blocks = self._pending
            self._pending = None
            self._absorb(step, reply, blocks)
        masked_rows, entries = self.state.mask_old_turns(step)
        for entry in entries or []:
            self.masked_ref[int(entry["since_turn"])] = str(entry["ref"])
        self._masked_total += int(masked_rows or 0)
        return self._render(step, work)

    def _absorb(self, step: int, reply: str, blocks: List[str]) -> None:
        """Append the step's transcript to the episode's own fixture-shaped turn list."""
        tool_outputs = []
        for block in blocks:
            path = _block_path(block)
            tool_outputs.append({"doc_id": path or ("step-%d" % step), "revision": 1,
                                 "body": block})
        self.fixture["turns"].append({"tool_outputs": tool_outputs})
        if reply:
            self.blocks.append({"step": step, "kind": "reply", "text": reply})
        for block in blocks:
            self.blocks.append({"step": step, "kind": "tool", "text": block})

    def _render(self, step: int, work: str) -> str:
        parts = [self.l0]
        for block in self.blocks:
            if block["kind"] == "tool" and block["step"] in self.masked_ref:
                parts.append("TOOL %d\n[MASKED %s]"
                             % (block["step"], self.masked_ref[block["step"]]))
            else:
                parts.append("%s %d\n%s" % (block["kind"].upper(), block["step"],
                                            block["text"]))
        parts.append(work)
        return "\n\n".join(parts)

    @property
    def evicted(self) -> int:
        return self._masked_total

    @property
    def dropped_turns(self) -> int:
        """Masked rows ARE the dropped turns for this arm — the same number, one name."""
        return self._masked_total


class NoneArm(EpisodeArm):
    """``none`` — no policy: the transcript grows and nothing is dropped.

    The control arm.  It is deliberately the simplest possible renderer, because its job
    is to be the arm with no retention mechanism at all; the design's own note is that the
    server does not truncate at these lengths, so nothing needs to be dropped.
    """

    name = ARM_NONE
    fold_mechanism = "none"
    allow_refetch = True

    def __init__(self, task, system_text, model="offline-model"):
        super().__init__(task, system_text, model)
        self.blocks: List[dict] = []
        self.l0 = layers._l0_text(self.run)

    def render(self, step: int, work: str) -> str:
        if self._pending is not None:
            reply, blocks = self._pending
            self._pending = None
            if reply:
                self.blocks.append({"step": step, "kind": "reply", "text": reply})
            for block in blocks:
                self.blocks.append({"step": step, "kind": "tool", "text": block})
        parts = [self.l0]
        for block in self.blocks:
            parts.append("%s %d\n%s" % (block["kind"].upper(), block["step"], block["text"]))
        parts.append(work)
        return "\n\n".join(parts)


def make_arm(name: str, task: Task, system_text: str, *, model: str = "offline-model",
             compact_every: int = DEFAULT_COMPACT_EVERY,
             window_turns: int = DEFAULT_WINDOW_TURNS,
             window_tokens: Optional[int] = None) -> EpisodeArm:
    """The arm named by ``--arms``.  An unknown name is refused, never defaulted."""
    if name == ARM_FETCH:
        return FetchArm(task, system_text, model, compact_every=compact_every,
                        window_tokens=window_tokens)
    if name == ARM_PINNED:
        return PinnedArm(task, system_text, model, compact_every=compact_every,
                         window_tokens=window_tokens)
    if name == ARM_COMPACT:
        return CompactArm(task, system_text, model, compact_every=compact_every,
                          window_tokens=window_tokens)
    if name == ARM_MASK:
        return MaskArm(task, system_text, model, window_turns=window_turns)
    if name == ARM_NONE:
        return NoneArm(task, system_text, model)
    raise TaskError("unknown arm %r; known: %s" % (name, list(ARMS)))


def dry_run_folds(task: Task, arm_name: str, *, steps: int = DEFAULT_STEPS,
                  compact_every: int = DEFAULT_COMPACT_EVERY,
                  window_turns: int = DEFAULT_WINDOW_TURNS,
                  window_tokens: Optional[int] = None,
                  model: str = "offline-model") -> dict:
    """Drive the arm's policy with a synthetic transcript and count what it drops.

    Sends nothing.  The fold is a function of the step count and the arm's own thresholds,
    so this is the real count, not an estimate: the same ``render``/``observe`` calls the
    live loop makes, with a placeholder reply and one placeholder tool block per step.
    A dry run that cannot show the fold firing is a dry run that cannot authorise a live
    cell (design §5 falsifier 7: ``compactions == 0`` makes the episode void).
    """
    system_text = _system_text(task)
    arm = make_arm(arm_name, task, system_text, model=model,
                   compact_every=compact_every, window_turns=window_turns,
                   window_tokens=window_tokens)
    arm.begin()
    limit = min(int(steps), task.n_turns)
    for step in range(1, limit + 1):
        arm.render(step, task.question_at(step))
        arm.observe(step, "ANSWER: NONE", ['<tool_result path="x.py"/>'])
        if arm.wants_summary():
            arm.apply_summary("(dry run)")
    return {"arm": arm_name, "steps": limit, "compactions": int(arm.compactions),
            "evicted": int(arm.evicted), "fold_mechanism": arm.fold_mechanism,
            "fold_kind": arm.fold_kind, "dropped_turns": int(arm.dropped_turns),
            "void": arm.fold_mechanism == "journal-drop" and arm.compactions == 0}


# ------------------------------------------------------------------ rows
def validate_row(row: dict) -> dict:
    """Return the row unchanged, or raise :class:`RowError` naming the first defect.

    Delegates to ``agentic_contract.validate_row`` — the analyser validates the same rows
    with the same function, so a row this cell writes and the analyser accepts cannot
    disagree about what a row is.
    """
    return agentic_contract.validate_row(row)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _call_key(call: dict) -> tuple:
    """The identity of one tool call, for the re-fetch count."""
    if call.get("tool") == run_longrun.GREP_TOOL_NAME:
        return ("grep", str(call.get("pattern")), str(call.get("glob")))
    return ("read_file", str(call.get("path")), int(call.get("start_line") or 1),
            int(call.get("end_line") or 1))


def _call_record(call: dict, result: dict) -> dict:
    """One ``tool_calls`` entry for the per-request row."""
    rec = result.get("record") or {}
    args = {k: v for k, v in call.items() if k not in ("source", "call_id")}
    return {"name": call.get("tool") or "read_file", "arguments": args,
            "ok": bool(rec.get("executed")), "bytes": len(result.get("text") or ""),
            "error": rec.get("error"), "truncated": bool(rec.get("truncated"))}


def _row(run_id, arm_name, task, rep, step, kind, resp, call_records, arm, *,
         answer, expected, verified, expected_present, model,
         prompt_tokens_max=None, tools_schema_sent=False) -> dict:
    """One per-request row (:data:`REQUIRED_ROW_KEYS`) for one request.

    ``fetch_rounds`` is the number of tool calls this request actually executed, and
    ``compactions``/``evicted`` are the arm's running totals AT this request — so a reader
    can see the fold land on the row where it happened instead of only in the episode
    summary.  ``tools_schema_sent`` is measured from the body the client would build, not
    asserted: a row that claims the schema without it is the defect stage 1 paid for.
    """
    return {
        "run_id": run_id,
        "arm": arm_name,
        "task_id": task.task_id,
        "rep": int(rep),
        "step": int(step),
        "kind": kind,
        "prompt_tokens": resp.get("prompt_tokens"),
        "completion_tokens": resp.get("completion_tokens"),
        "cached_tokens": resp.get("cached_tokens"),
        "prompt_tokens_max": prompt_tokens_max,
        "tool_calls": list(call_records or []),
        "fetch_rounds": len(call_records or []),
        "tools_schema_sent": bool(tools_schema_sent),
        "fold_event": bool(arm.fold_event),
        "fold_kind": arm.fold_kind,
        "dropped_turns": int(arm.dropped_turns),
        "pinned_tokens": int(arm.pinned_tokens),
        "compactions": int(arm.compactions),
        "evicted": int(arm.evicted),
        "answer": answer,
        "expected": expected,
        "verified": verified,
        "expected_present": expected_present,
        "ts": _now(),
        "model": model,
        "temperature": 0.0,
    }


# ------------------------------------------------------------------ the episode
def run_episode(task: Task, arm_name: str, rep: int, *, cfg, send, root: str,
                steps: int = DEFAULT_STEPS, max_requests: int = DEFAULT_MAX_REQUESTS,
                compact_every: int = DEFAULT_COMPACT_EVERY,
                window_turns: int = DEFAULT_WINDOW_TURNS,
                window_tokens: Optional[int] = None,
                model: Optional[str] = None, run_id: str = "",
                on_row=None) -> dict:
    """Run ONE episode and return its summary row.  ``send`` is ``client.send_chat`` or a fake.

    The loop is the whole instrument: one request per step, the model's reply parsed as
    either a tool call (executed against ``root``, appended to the transcript) or an
    ``ANSWER:`` line (graded against the checkpoint at that turn).  The arm's fold policy
    is applied by ``arm.render`` — this function contains no fold logic.

    ``on_row`` receives every per-request row as it is produced, so the caller owns the
    file and a test can inspect the rows without touching the disk.
    """
    model = model or getattr(cfg, "model", "offline-model")
    run_id = run_id or "agentic:%s:%s:rep%d" % (task.task_id, arm_name, int(rep))
    system_text = _system_text(task)
    arm = make_arm(arm_name, task, system_text, model=model,
                   compact_every=compact_every, window_turns=window_turns,
                   window_tokens=window_tokens)
    arm.begin()

    limit = min(int(steps), task.n_turns)
    records: List[dict] = []
    answered: Dict[int, dict] = {}
    goal_present: List[bool] = []
    fact_present: List[Optional[bool]] = []
    seen_calls: set = set()
    refetch = 0
    requests = 0
    steps_used = 0
    prompt_tokens_max: Optional[int] = None
    billed_known = 0
    billed_unknown = 0
    error: Optional[str] = None
    stopped = "budget"
    final_answer: Optional[str] = None
    final_ok: Optional[bool] = None
    final_turn = task.final_turn

    # Refuse a task that cannot fetch BEFORE the first request: a prompt that never names
    # the tool would spend the whole budget answering from the index (Main, m00447).
    check_prompt_declares_tool(task)
    # Measured from the body the client would build, not asserted: the row must say what
    # was actually on the wire.
    tools_schema_sent = bool(episode_tools_body_members(cfg).get("tools"))

    def emit(row: dict) -> None:
        if on_row is not None:
            on_row(validate_row(row))

    def row_for(step, kind, resp, call_records, **kw) -> dict:
        return _row(run_id, arm_name, task, rep, step, kind, resp, call_records, arm,
                    model=model, prompt_tokens_max=prompt_tokens_max,
                    tools_schema_sent=tools_schema_sent, **kw)

    for step in range(1, limit + 1):
        if requests >= int(max_requests):
            stopped = "max_requests"
            break
        is_final = step == final_turn
        kind = "final" if is_final else "work"
        work = task.question_at(step)
        prompt = arm.render(step, work)
        goal_present.append(_goal_present(prompt, task.statement))
        fact_present.append(_value_present(prompt, task.fixture.get("fact", {}).get("value")
                                           if isinstance(task.fixture.get("fact"), dict)
                                           else None))
        messages = [{"role": "system", "content": system_text},
                    {"role": "user", "content": prompt}]
        requests += 1
        steps_used = step
        try:
            resp = send(cfg, messages)
        except client.RequestFailure as exc:
            error = "request_failed: %s" % (exc,)
            stopped = "request_failed"
            break

        prompt_tokens = resp.get("prompt_tokens")
        if isinstance(prompt_tokens, (int, float)):
            prompt_tokens_max = (int(prompt_tokens) if prompt_tokens_max is None
                                 else max(prompt_tokens_max, int(prompt_tokens)))
        billed, _source = score_longrun.billed_of(
            {"prompt_tokens": prompt_tokens, "cached_tokens": resp.get("cached_tokens"),
             "turn": step})
        if billed is None:
            billed_unknown += 1
        else:
            billed_known += int(billed)

        calls, _refusals = run_longrun.calls_from_response(resp)
        blocks: List[str] = []
        call_records: List[dict] = []
        if calls:
            for call in calls[:run_longrun.TOOL_CALLS_PER_TURN]:
                key = _call_key(call)
                path = str(call.get("path") or "")
                if key in seen_calls:
                    refetch += 1
                seen_calls.add(key)
                if path and not arm.refetch_allowed(path):
                    # The arm has no fetch channel: a body it already served is not
                    # re-servable.  Recorded as a refusal, never silently dropped.
                    arm.refused_refetch += 1
                    result = {"record": {"path": path, "executed": False,
                                         "error": "refetch_refused"},
                              "block": '<tool_result error="refetch_refused"/>', "text": ""}
                else:
                    result = run_longrun.execute_tool_call(call, root)
                    arm.note_served(path)
                blocks.append(result["block"])
                call_records.append(_call_record(call, result))
            arm.observe(step, resp.get("content") or "", blocks)
            emit(row_for(step, kind, resp, call_records, answer=None, expected=None,
                         verified=None, expected_present=None))
            continue

        parsed = grade_v5.parse_answer_contract(resp.get("content") or "")
        if parsed.get("answer_raw") is None:
            # Neither a tool call nor an ANSWER line: the step is spent, the episode
            # continues.  Recorded so a silent no-op can never look like progress.
            arm.observe(step, resp.get("content") or "", [])
            emit(row_for(step, kind, resp, call_records, answer=None, expected=None,
                         verified=None, expected_present=None))
            continue

        cp = task.checkpoint_at(step)
        if cp is None:
            arm.observe(step, resp.get("content") or "", [])
            emit(row_for(step, kind, resp, call_records,
                         answer=parsed.get("answer_raw"), expected=None, verified=None,
                         expected_present=None))
            continue

        cell = grade_v5.grade_cell(cp, parsed)
        ok = cell.get("verdict") == "pass"
        answered[step] = {"step": step, "expected": cp.get("expected"),
                          "answer": parsed.get("answer_raw"), "ok": bool(ok),
                          "expected_present": _value_present(prompt, cp.get("expected")),
                          "answered_at": step, "verdict": cell.get("verdict"),
                          "reason": cell.get("reason")}
        emit(row_for(step, kind, resp, call_records,
                     answer=parsed.get("answer_raw"), expected=cp.get("expected"),
                     verified=bool(ok),
                     expected_present=answered[step]["expected_present"]))
        arm.observe(step, resp.get("content") or "", [])
        if is_final:
            final_answer = parsed.get("answer_raw")
            final_ok = bool(ok)
            stopped = "final_answer"
            break

        # ``compact`` buys its summary AFTER the fold that dropped the journal, so the
        # summary covers exactly the turns the model can no longer see.  It is a request
        # like any other and is refused when the budget is spent.
        if arm.wants_summary():
            if requests >= int(max_requests):
                stopped = "max_requests"
                break
            requests += 1
            try:
                sresp = send(cfg, [{"role": "system", "content": system_text},
                                   {"role": "user", "content": arm.summary_prompt()}])
            except client.RequestFailure as exc:
                error = "summary_failed: %s" % (exc,)
                break
            arm.apply_summary(sresp.get("content") or "")
            emit(row_for(step, "summary", sresp, [], answer=None, expected=None,
                         verified=None, expected_present=None))

    for cp in task.checkpoints:
        turn = int(cp["turn"])
        if turn in answered:
            records.append(answered[turn])
        else:
            records.append({"step": turn, "expected": cp.get("expected"), "answer": None,
                            "ok": False, "expected_present": None, "answered_at": None,
                            "verdict": "unanswered", "reason": "not_answered"})

    solved = all(r["ok"] for r in records)
    compactions = arm.compactions
    verdict = _verdict(solved, records, compactions, arm.fold_mechanism)
    row = {
        "task": task.task_id,
        "arm": arm_name,
        "rep": int(rep),
        "solved": bool(solved),
        "checkpoints": records,
        "steps_used": int(steps_used),
        "requests": int(requests),
        "refetch_count": int(refetch),
        "compactions": int(compactions),
        "evicted": int(arm.evicted),
        "prompt_tokens_max": prompt_tokens_max,
        "billed_tokens": billed_known if (billed_known or not billed_unknown) else None,
        "billed_unknown_requests": int(billed_unknown),
        "verdict": verdict,
        "goal_present": goal_present,
        "fact_present": fact_present,
        "fold_mechanism": arm.fold_mechanism,
        "stopped": stopped,
        "final_answer": final_answer,
        "final_ok": final_ok,
        "refused_refetch": int(arm.refused_refetch),
        "tools_schema_sent": bool(tools_schema_sent),
        "model": model,
        "run_id": run_id,
        "steps_budget": int(steps),
        "max_requests": int(max_requests),
    }
    if isinstance(arm, CompactArm):
        row["summaries"] = int(arm.summaries)
        row["summary_refused"] = int(arm.summary_refused)
    if error:
        row["error"] = error
    return row


def _verdict(solved: bool, records: List[dict], compactions: int,
             fold_mechanism: str) -> str:
    """The episode's classification, in the order the design's falsifiers apply.

    ``void`` first: design §5 falsifier 7 says an episode whose fold never fired is not a
    data point.  That rule is about the JOURNAL-DROP arms; ``masking-no-fetch`` and
    ``none`` do not fold, so their mechanism is named instead of being called void.
    """
    if fold_mechanism == "journal-drop" and compactions == 0:
        return "void"
    lost = [r for r in records if not r["ok"] and r.get("expected_present") is False]
    if lost:
        return "lost_then_failed"
    present = [r for r in records if not r["ok"] and r.get("expected_present") is True]
    if present:
        return "present_then_failed"
    if solved:
        return "solved"
    return "unsolved"


# ------------------------------------------------------------------ budget
def ledger_spent(measure_dir: Optional[str] = None) -> Tuple[int, int]:
    """``(spent, nfiles)`` from the row files on disk, the way ``cell.py:461`` counts.

    Best-effort by construction: the runner reports no quota, so the remainder is derived
    from the rows already written and is labelled as such wherever it is printed.
    """
    measure = measure_dir or os.path.join(_PTR_ENGINE_ROOT, "measure")
    spent, nfiles = 0, 0
    if os.path.isdir(measure):
        for name in sorted(os.listdir(measure)):
            if name.startswith("rows-") and name.endswith(".jsonl"):
                spent += cell_mod._count_rows(os.path.join(measure, name))
                nfiles += 1
    return spent, nfiles


def plan(tasks, arm: str, reps: int, max_steps: int,
         window_tokens: Optional[int] = None, repo_root: Optional[str] = None) -> dict:
    """The maximum requests one cell may send, and the per-episode shape behind it.

    ``max_steps`` is the cap, so the plan is the WORST case: every episode spends its
    whole step budget.  A summary arm adds one request per fold, and the fold count is
    bounded by ``max_steps // compact_every``; the plan therefore uses that bound rather
    than a guess.
    """
    if arm not in ARMS:
        raise TaskError("unknown arm %r; known: %s" % (arm, list(ARMS)))
    per_episode = int(max_steps)
    if arm in SUMMARY_ARMS:
        per_episode += max(1, int(max_steps) // max(1, DEFAULT_COMPACT_EVERY))
    planned = len(tasks) * int(reps) * per_episode
    return {"planned": planned, "per_episode_max": per_episode, "arm": arm,
            "reps": int(reps), "tasks": len(tasks), "max_steps": int(max_steps)}


def check_budget(planned: int, spent: int, budget_cap: Optional[int] = None,
                 quota: int = cell_mod.PROJECT_QUOTA) -> dict:
    """Refuse when the plan would exceed the quota or the authorised budget.

    Two independent gates, because they answer different questions: the QUOTA is the
    project's remaining headroom (``cell.PROJECT_QUOTA`` minus the rows on disk), and the
    BUDGET is what this cell was authorised to spend.  Either one refusing is a refusal.
    """
    remaining = int(quota) - int(spent)
    if remaining < 0:
        raise BudgetRefusal("headroom UNKNOWN (spent=%d, cap=%d); refusing"
                            % (spent, quota))
    if int(planned) > remaining:
        raise BudgetRefusal("planned=%d exceeds headroom %d by %d (spent=%d, cap=%d)"
                            % (planned, remaining, int(planned) - remaining,
                               spent, quota))
    if budget_cap is not None and int(planned) > int(budget_cap):
        raise BudgetRefusal("planned=%d exceeds --budget %d by %d"
                            % (planned, int(budget_cap), int(planned) - int(budget_cap)))
    return {"planned": int(planned), "spent": int(spent), "quota": int(quota),
            "remaining": remaining, "budget": budget_cap,
            "after": remaining - int(planned)}


# ------------------------------------------------------------------ cell driver
class EpisodeCfg:
    """The config object ``client.request_body`` / ``client.send_chat`` read.

    Constructed here rather than duplicating a schema: the tool members come from
    ``client.tools_body_members`` (extended by :func:`episode_tools_body_members`), so
    this class only carries the scalar knobs the client already understands.
    """

    def __init__(self, *, model: str, base_url: str = "", engine: str = "",
                 max_tokens: int = 4096, temperature: float = 0.0,
                 seed: Optional[int] = None, thinking: str = "off",
                 timeout: float = 900.0, tools: str = "read_file,grep",
                 metrics_scrape: bool = False):
        self.model = model
        self.base_url = base_url
        self.engine = engine
        self.max_tokens = int(max_tokens)
        self.temperature = float(temperature)
        self.seed = seed
        self.thinking = thinking
        self.timeout = float(timeout)
        self.tools = tools
        self.tool_choice = client.TOOL_CHOICE_AUTO
        self.stream = True
        self.turn_wall_cap = None
        self.metrics_scrape = bool(metrics_scrape)


def _transport_send(transport, cfg, tools: str):
    """Adapt a transport's ``send(messages, tools=…)`` to the episode's ``send(cfg, msgs)``."""
    def send(_cfg, messages):
        return transport.send(messages, tools=tools)
    return send


def run_cell(tasks, arm: str, reps: int, transport, *, out_path: Optional[str] = None,
             run_id: str = "", window_tokens: Optional[int] = None,
             max_steps: int = DEFAULT_STEPS,
             max_requests: int = DEFAULT_MAX_REQUESTS,
             temperature: float = 0.0, model: str = "fake",
             tools: str = "read_file,grep", budget_cap: Optional[int] = None,
             spent: int = 0, repo_root: Optional[str] = None, log=print,
             dry_run: bool = False, compact_every: int = DEFAULT_COMPACT_EVERY,
             window_turns: int = DEFAULT_WINDOW_TURNS,
             rows_path: Optional[str] = None) -> dict:
    """Run one cell (tasks x reps on one arm) and return its summary.

    ``dry_run`` sends nothing and returns the plan, so the operator can price a cell
    before authorising it.  A live run refuses BEFORE the first request when the plan
    exceeds the quota or ``budget_cap``, and aborts mid-run if the actual count would
    exceed ``budget_cap``.
    """
    if arm not in ARMS:
        raise TaskError("unknown arm %r; known: %s" % (arm, list(ARMS)))
    root = os.path.abspath(repo_root or os.getcwd())
    # Every task must be able to fetch before a single request is spent on any of them.
    for task in tasks:
        check_prompt_declares_tool(task)
    planned = plan(tasks, arm, reps, max_steps, window_tokens, root)
    gate = check_budget(planned["planned"], spent, budget_cap)
    if dry_run:
        folds = [dry_run_folds(task, arm, steps=max_steps, compact_every=compact_every,
                               window_turns=window_turns, window_tokens=window_tokens,
                               model=model)
                 for task in tasks]
        compactions = sum(f["compactions"] for f in folds)
        evicted = sum(f["evicted"] for f in folds)
        log("planned_requests=%d arm=%s reps=%d tasks=%d max_steps=%d spent=%d "
            "quota=%d remaining=%d budget=%s compactions=%d evicted=%d void=%s"
            % (planned["planned"], arm, int(reps), len(tasks), int(max_steps),
               int(spent), gate["quota"], gate["remaining"], budget_cap,
               compactions, evicted, any(f["void"] for f in folds)))
        return {"planned": planned["planned"], "rows": 0, "dry_run": True,
                "gate": gate, "arm": arm, "reps": int(reps),
                "compactions": compactions, "evicted": evicted, "folds": folds}

    cfg = EpisodeCfg(model=model, temperature=temperature, tools=tools)
    send = _transport_send(transport, cfg, tools)
    rows: List[dict] = []
    req_rows: List[dict] = []
    used = 0
    with grep_on_the_wire():
        for task in tasks:
            for rep in range(1, int(reps) + 1):
                if budget_cap is not None and used >= int(budget_cap):
                    raise BudgetRefusal("actual requests reached --budget %d before "
                                        "task %s rep %d" % (budget_cap, task.task_id, rep))
                row = run_episode(
                    task, arm, rep, cfg=cfg, send=send, root=root,
                    steps=max_steps, max_requests=max_requests,
                    compact_every=compact_every, window_turns=window_turns,
                    window_tokens=window_tokens, model=model,
                    run_id=run_id or "agentic:%s:%s:rep%d" % (task.task_id, arm, rep),
                    on_row=req_rows.append)
                used += int(row["requests"])
                if budget_cap is not None and used > int(budget_cap):
                    raise BudgetRefusal("actual requests %d exceed --budget %d"
                                        % (used, budget_cap))
                row["planned_max"] = planned["planned"]
                row["budget"] = budget_cap
                rows.append(row)
                log("%s %-22s rep%d  solved=%s steps=%d requests=%d compactions=%d "
                    "evicted=%d refetch=%d verdict=%s"
                    % (task.task_id, arm, rep, row["solved"], row["steps_used"],
                       row["requests"], row["compactions"], row["evicted"],
                       row["refetch_count"], row["verdict"]))

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
    if rows_path:
        os.makedirs(os.path.dirname(os.path.abspath(rows_path)), exist_ok=True)
        with open(rows_path, "a", encoding="utf-8") as fh:
            for row in req_rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
    return {"rows": len(rows), "requests": used, "planned": planned["planned"],
            "gate": gate, "arm": arm, "reps": int(reps), "episodes": rows,
            "request_rows": req_rows}


# ------------------------------------------------------------------ offline
def offline_episodes(rows_path: str) -> List[dict]:
    """Re-grade a per-request row file into episode rows.  Sends nothing.

    Mirrors ``cell.py --offline``: the rows already on disk are the measurement, and this
    only re-derives the episode summary from them.  A row file that carries no ``verified``
    field is refused rather than silently graded as unsolved.
    """
    with open(rows_path, "r", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    if not rows:
        raise TaskError("--offline row file is empty: %s" % rows_path)
    groups: Dict[tuple, List[dict]] = {}
    for row in rows:
        validate_row(row)
        key = (row["run_id"], row["task_id"], row["arm"], int(row["rep"]))
        groups.setdefault(key, []).append(row)
    out = []
    for (run_id, task_id, arm, rep), group in sorted(groups.items()):
        graded = [r for r in group if r.get("expected") is not None]
        checkpoints = [{"step": r["step"], "expected": r["expected"],
                        "answer": r.get("answer"), "ok": bool(r.get("verified")),
                        "expected_present": r.get("expected_present"),
                        "answered_at": r["step"], "verdict": None, "reason": None}
                       for r in graded]
        # ``compactions``/``evicted``/``dropped_turns`` are RUNNING TOTALS on every row, so
        # the episode's value is the last one, never the sum of the column.
        compactions = max([int(r.get("compactions") or 0) for r in group] or [0])
        evicted = max([int(r.get("evicted") or 0) for r in group] or [0])
        seen, refetch = set(), 0
        for r in group:
            for call in r.get("tool_calls") or []:
                key = json.dumps([call.get("name"), call.get("arguments")],
                                 sort_keys=True)
                if key in seen:
                    refetch += 1
                seen.add(key)
        solved = bool(checkpoints) and all(c["ok"] for c in checkpoints)
        mechanism = _mechanism_of(arm)
        out.append({
            "task": task_id, "arm": arm, "rep": rep,
            "solved": solved,
            "checkpoints": checkpoints,
            "steps_used": max(int(r["step"]) for r in group),
            "requests": len(group),
            "refetch_count": refetch,
            "compactions": compactions,
            "evicted": evicted,
            "prompt_tokens_max": max([int(r["prompt_tokens"]) for r in group
                                      if isinstance(r.get("prompt_tokens"), (int, float))]
                                     or [0]) or None,
            "billed_tokens": sum(int(r.get("prompt_tokens") or 0)
                                 + int(r.get("completion_tokens") or 0)
                                 for r in group),
            "verdict": _verdict(solved, checkpoints, compactions, mechanism),
            "goal_present": [],
            "fact_present": [],
            "fold_mechanism": mechanism,
            "stopped": "offline",
            "run_id": run_id,
            "offline": True,
        })
    return out


def _mechanism_of(arm: str) -> str:
    """The fold mechanism an arm name implies, for a re-grade that has no arm object."""
    if arm == ARM_MASK:
        return "mask"
    if arm == ARM_NONE:
        return "none"
    return "journal-drop"


# ------------------------------------------------------------------ CLI
def _default_out() -> str:
    repo = os.path.dirname(os.path.dirname(_PTR_ENGINE_ROOT))
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(repo, "experiments", "ptr-engine", "measure",
                        "AGENTIC-%s.jsonl" % date)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="agentic_cell.py",
        description="Stage-2 episode loop: the model chooses every read (plan step 8).")
    ap.add_argument("--tasks", default=None, metavar="DIR",
                    help="directory of v2 fixture task files (plan step 9)")
    ap.add_argument("--arms", default=ARM_FETCH, metavar="LIST",
                    help="comma-separated arms: %s (default: %s)"
                         % (",".join(ARMS), ARM_FETCH))
    ap.add_argument("--reps", type=int, default=DEFAULT_REPS)
    ap.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    ap.add_argument("--max-requests", type=int, default=DEFAULT_MAX_REQUESTS)
    ap.add_argument("--root", default=None, metavar="DIR",
                    help="the frozen snapshot the model reads (default: cwd)")
    ap.add_argument("--snapshot-manifest", default=None, metavar="PATH",
                    help="manifest.json of the snapshot; re-hashed before the first request")
    ap.add_argument("--out", default=None, metavar="PATH",
                    help="per-episode NDJSON (default: measure/AGENTIC-<date>.jsonl)")
    ap.add_argument("--rows-dir", default=None, metavar="DIR",
                    help="per-request rows (default: the --out directory)")
    ap.add_argument("--budget", type=int, default=None, metavar="N",
                    help="maximum requests this cell may send (required for a live run)")
    ap.add_argument("--offline", default=None, metavar="ROWS_JSONL",
                    help="re-grade an existing per-request row file; sends nothing")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and send nothing")
    ap.add_argument("--model", default=run_longrun.DEFAULT_MODEL)
    ap.add_argument("--base-url", default=run_longrun.DEFAULT_BASE_URL)
    ap.add_argument("--engine", default=run_longrun.DEFAULT_ENGINE)
    ap.add_argument("--max-tokens", type=int, default=client.DEFAULT_MAX_TOKENS)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--thinking", default=client.DEFAULT_THINKING)
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--tools", default="read_file,grep", metavar="LIST",
                    help="tool channel(s) on the wire (default: read_file,grep)")
    ap.add_argument("--compact-every", type=int, default=DEFAULT_COMPACT_EVERY,
                    help="journal fold distance for the folding arms (default: %d)"
                         % DEFAULT_COMPACT_EVERY)
    ap.add_argument("--window-turns", type=int, default=DEFAULT_WINDOW_TURNS,
                    help="masking window for masking-no-fetch (default: %d)"
                         % DEFAULT_WINDOW_TURNS)
    ap.add_argument("--window-tokens", type=int, default=None,
                    help="window the pinned arms fold at 73.9%% of (default: the fixture's)")
    client.add_metrics_scrape_argument(ap)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    out_path = args.out or _default_out()

    if args.offline:
        if not os.path.exists(args.offline):
            print("refused: --offline row file does not exist: %s" % args.offline,
                  file=sys.stderr)
            return 2
        try:
            episodes = offline_episodes(args.offline)
        except (TaskError, RowError, OSError, ValueError) as exc:
            print("refused: %s" % (exc,), file=sys.stderr)
            return 2
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "a", encoding="utf-8") as fh:
            for row in episodes:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        print("offline: %d episode row(s) from %s -> %s"
              % (len(episodes), args.offline, out_path))
        return 0

    arms = [a.strip() for a in str(args.arms or "").split(",") if a.strip()]
    if not arms:
        print("refused: --arms is empty", file=sys.stderr)
        return 2
    for name in arms:
        if name not in ARMS:
            print("refused: unknown arm %r; known: %s" % (name, list(ARMS)), file=sys.stderr)
            return 2
    if args.steps < 1 or args.max_requests < 1 or args.reps < 1:
        print("refused: --steps, --max-requests and --reps must be >= 1", file=sys.stderr)
        return 2
    if not args.tasks:
        print("refused: --tasks is required", file=sys.stderr)
        return 2
    if not args.snapshot_manifest:
        # Without a frozen root the model's read is a read of the live tree and the task
        # is not reproducible (design §3.2 step 1).  Refused, not defaulted.
        print("refused: --snapshot-manifest is required (a frozen root is the "
              "instrument's precondition)", file=sys.stderr)
        return 2
    if args.budget is None and not args.dry_run:
        print("refused: --budget is required for a live cell (offline mode and --dry-run "
              "send nothing)", file=sys.stderr)
        return 2

    root = os.path.abspath(args.root or os.getcwd())
    try:
        manifest = verify_snapshot_manifest(root, args.snapshot_manifest)
        tasks = load_tasks(args.tasks)
    except (SnapshotMismatch, TaskError, run_longrun.FixtureError, OSError, ValueError) as exc:
        print("refused: %s" % (exc,), file=sys.stderr)
        return 2
    del manifest  # the index comes from the fixture, not the snapshot listing

    spent, nfiles = ledger_spent()
    planned = sum(plan(tasks, a, args.reps, args.steps)["planned"] for a in arms)
    print("PREFLIGHT: spent=%d cap=%d headroom=%d planned=%d arms=%d"
          % (spent, cell_mod.PROJECT_QUOTA, cell_mod.PROJECT_QUOTA - spent, planned,
             len(arms)), file=sys.stderr)
    try:
        gate = check_budget(planned, spent, args.budget)
    except BudgetRefusal as exc:
        print("refused: %s" % (exc,), file=sys.stderr)
        return 3
    if args.dry_run:
        print("planned_requests=%d arms=%s reps=%d tasks=%d max_steps=%d spent=%d "
              "quota=%d remaining=%d budget=%s"
              % (planned, ",".join(arms), args.reps, len(tasks), args.steps, spent,
                 gate["quota"], gate["remaining"], args.budget))
        # A dry run that cannot show the fold firing cannot authorise a live cell: design
        # §5 falsifier 7 makes an episode with ``compactions == 0`` void.  The count is the
        # real one — ``dry_run_folds`` drives the arm's own policy with a synthetic
        # transcript and sends nothing.
        void = []
        for arm_name in arms:
            folds = [dry_run_folds(task, arm_name, steps=args.steps,
                                   compact_every=args.compact_every,
                                   window_turns=args.window_turns,
                                   window_tokens=args.window_tokens,
                                   model=args.model)
                     for task in tasks]
            compactions = sum(f["compactions"] for f in folds)
            evicted = sum(f["evicted"] for f in folds)
            is_void = any(f["void"] for f in folds)
            if is_void:
                void.append(arm_name)
            print("dry_run arm=%-22s compactions=%d evicted=%d mechanism=%-11s void=%s"
                  % (arm_name, compactions, evicted, folds[0]["fold_mechanism"],
                     is_void))
        if void:
            print("refused: arm(s) %s would fold zero times in %d steps; the episode "
                  "would be VOID (design §5 falsifier 7)" % (",".join(void), args.steps),
                  file=sys.stderr)
            return 3
        return 0

    cfg = EpisodeCfg(model=args.model, base_url=args.base_url, engine=args.engine,
                     max_tokens=args.max_tokens, temperature=args.temperature,
                     seed=args.seed, thinking=args.thinking, timeout=args.timeout,
                     tools=args.tools, metrics_scrape=client.resolve_metrics_scrape(args))
    rows_dir = args.rows_dir or os.path.dirname(os.path.abspath(out_path))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    os.makedirs(rows_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    total_rows = 0
    total_requests = 0
    with grep_on_the_wire(), open(out_path, "a", encoding="utf-8") as fh:
        for arm_name in arms:
            req_path = os.path.join(rows_dir, "rows-agentic-%s-%s.jsonl"
                                    % (arm_name, stamp))
            with open(req_path, "a", encoding="utf-8") as req_fh:
                def on_row(row, _fh=req_fh):
                    _fh.write(json.dumps(row, sort_keys=True) + "\n")
                    _fh.flush()
                for task in tasks:
                    for rep in range(1, int(args.reps) + 1):
                        if total_requests >= int(args.budget):
                            print("refused: actual requests reached --budget %d"
                                  % args.budget, file=sys.stderr)
                            return 3
                        row = run_episode(
                            task, arm_name, rep, cfg=cfg, send=client.send_chat,
                            root=root, steps=args.steps,
                            max_requests=args.max_requests,
                            compact_every=args.compact_every,
                            window_turns=args.window_turns,
                            window_tokens=args.window_tokens, model=args.model,
                            on_row=on_row)
                        total_requests += int(row["requests"])
                        if total_requests > int(args.budget):
                            print("refused: actual requests %d exceed --budget %d"
                                  % (total_requests, args.budget), file=sys.stderr)
                            return 3
                        row["planned_max"] = planned
                        row["budget"] = args.budget
                        fh.write(json.dumps(row, sort_keys=True) + "\n")
                        fh.flush()
                        total_rows += 1
                        print("%s %-22s rep%d  solved=%s steps=%d requests=%d "
                              "compactions=%d evicted=%d refetch=%d verdict=%s"
                              % (task.task_id, arm_name, rep, row["solved"],
                                 row["steps_used"], row["requests"], row["compactions"],
                                 row["evicted"], row["refetch_count"], row["verdict"]))
    print("wrote %d episode row(s) to %s" % (total_rows, out_path))
    print("wrote per-request rows to %s" % rows_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
