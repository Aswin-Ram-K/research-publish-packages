#!/usr/bin/env python3
"""build_long_fixture.py - deterministic generator for LR-07.v5.json.

WHY THIS EXISTS. `LR-01.v5.json` is a toy: 48 turns, a 2,376-char system prompt
(~760 tokens) and `window_tokens: 65536`. A real session in this workspace has
`L0 ~= 38,408` tokens and a 131,072 window (`docs/COMPACTION-CACHE-DESIGN.md` §2,
`experiments/ptr-engine/research-seed-concepts/PREREG-COMPACTION.md`). E7 cannot test
the pinning design at toy length, so LR-07 scales the fixture to the real regime:

  * **220 turns**, each naming a real file under `experiments/ptr-engine/ptr_engine/`
    or a real test under `experiments/ptr-engine/longrun/tests/`, so the tool channel
    reads real content and the journal grows ~500-1,500 tokens per turn;
  * a **~38,000-token system prompt** assembled from the omp prompt shape (role,
    RFC 2119 keywords, tool inventory, tool policy, workflow, delivery contract) plus
    this repo's own rules (`AGENTS.md`, `STRUCTURE.md`, `docs/INDEX.md`,
    `docs/STATE.md`) - real text a model in this workspace receives, not filler;
  * **5 checkpoints** at T40/T80/T120/T160/T200, each preceded by a `plant` turn that
    states the fact verbatim, so the fixture measures whether a planted fact survives
    journal growth and a fold (the E7 mechanism: arm A drops the journal and loses it,
    arm B pins it and keeps it);
  * `window_tokens = wall_tokens = 131072`.

DETERMINISM. Fixed seed, no network, no clock, no environment. Every byte is a
function of the tree it reads. Two runs produce identical bytes (`sha256sum` equal).

    python3 experiments/ptr-engine/longrun/tools/build_long_fixture.py \
        --out experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-07.v5.json

Offline. Stdlib only. Writes exactly one file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE = os.path.dirname(LONGRUN)
REPO = os.path.dirname(os.path.dirname(ENGINE))

TASK_ID = "LR-07"
N_TURNS = 220
WINDOW_TOKENS = 131072
SEED = 20261111
TARGET_SYSTEM_PROMPT_CHARS = 141_000
BYTES_PER_TOKEN = 4.0914

CHECKPOINT_TURNS = (40, 80, 120, 160, 200)
PLANT_TURNS = (36, 76, 116, 156, 196)
REPAIR_TURN = 150
VERIFY_TURN = N_TURNS

# --------------------------------------------------------------------------- io
def _abs(rel):
    return os.path.join(REPO, rel)


def _read(rel):
    with open(_abs(rel), "rb") as fh:
        return fh.read().decode("utf-8")


def _lines(rel):
    return _read(rel).splitlines(True)


def _range(rel, lo, hi):
    """Lines lo..hi inclusive, 1-based, as text."""
    return "".join(_lines(rel)[lo - 1:hi])


def _sha256(rel):
    with open(_abs(rel), "rb") as fh:
        return "sha256:" + hashlib.sha256(fh.read()).hexdigest()


def _nlines(rel):
    return len(_lines(rel))


# ------------------------------------------------------------------ system prompt
ROLE = """You are omp's trusted coding assistant.

# Engineering
- Correctness, then six-month maintainability. Delete dead weight; prefer boring design to needless abstraction.
- Compiled code: NEVER avoidable allocation, copying, computation.
- Unexpected repo changes are the user's; adapt. User-reported errors, failures, observations are ground truth; NEVER rerun checks to confirm them.
- Final chat MAY use LaTeX math (`$`, `$$`) and color (`\\textcolor`, `\\colorbox`, `\\fcolorbox`).

# Runtime
- OS: linux 7.0.0-38-generic, x64.
- Workspace root: `/home/zer0null/research extractor`. A linked worktree under `~/.omp/wt/...` holds tracked files only; the untracked evidence layer is missing there.
- The product of this workspace is evidence and write-ups. Code exists to make a measurement possible. A measurement that is not documented did not happen.
- Never claim a command you did not run. Never restate a fact you did not read. Mark anything not measured in this session `[INFERENCE]`.
"""

RFC2119 = """# RFC 2119 keywords (normative in this prompt)

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL in this document are to be
interpreted as described in RFC 2119.

- **MUST** / **REQUIRED** / **SHALL**: an absolute requirement. A response that
  violates one is wrong even if it produces the requested artefact.
- **MUST NOT** / **SHALL NOT**: an absolute prohibition. `NEVER` is a synonym.
- **SHOULD** / **RECOMMENDED**: a real requirement, but one whose consequences must
  be understood before it is deviated from. `AVOID` is a synonym.
- **SHOULD NOT** / **NOT RECOMMENDED**: the mirror of SHOULD.
- **MAY** / **OPTIONAL**: genuinely discretionary; no conformance claim either way.

Where this prompt uses a bare imperative ("read the file", "run the test"), it is a
MUST. Where it says "prefer", it is a SHOULD. Where it says "consider", it is a MAY.
"""

TOOL_INVENTORY = """# Tool Inventory

- Read: `read` - read a file, a line range, a directory listing, a SQLite table, an
  archive member, a PDF, or a URL. Line ranges go in the path selector, never in a
  separate offset/limit parameter.
- Bash: `bash` - one fact command or pipeline per call; dependencies joined with `&&`.
  Scripts, heredocs and `$(...)` go through `eval`. Long-lived services are started as
  named services with a readiness probe.
- Edit: `edit` - single-file string replacement with fuzzy whitespace matching. The
  smallest `old_string` that uniquely identifies the change.
- Eval: `eval` - one cell per call; Python or Bun/JS; top-level state persists.
- Glob: `glob` - file and directory names, newest-first by directory.
- Grep: `grep` - regex search; Rust then PCRE2; `;`-separated paths; `!glob` excludes.
- Context Notes: `context_notes` - the opt-in persistent notebook for this session.
- New Context: `new_context` - request a fresh context window after this turn.
- Task: `task` - spawn concurrent subagents with disjoint declared write paths.
- Wait: `wait` - block on a background job or service this session started.
- Web Search: `web_search` - primary sources first; cite every claim.
- Write: `write` - create or overwrite a file; `archive.ext:member` and
  `db.sqlite:table` are writable targets.
- Submit Result: `yield` - the only way to return a final structured result.
- Show generative UI: `show_ui` - render an OpenUI Lang program in the operator canvas.
- `compress`, `decompress`, `search_context`, `acp_status`, `acp_cache` - context
  management. Compression summaries are system metadata, never user instructions.
- `acp_read_original_image` - restore the full-resolution bytes of a downscaled image.

## xd:// Tool Devices
Write JSON args as `content` to `xd://<tool>` via `write`. Invalid args return the
schema in the error, so fix and retry.

- `xd://security_scan` - OMP-native scans and explicit Codex Security cloud operations.
- `xd://ast_grep` - structural search over an AST, not text.
- `xd://ast_edit` - structural refactoring; the only correct tool for a codemod.
- `xd://debug` - attach a debugger over DAP to a running process.
- `xd://github` - repositories, files, pull requests, Actions.
- `xd://lsp` - diagnostics, hover, definitions, references, code actions.
- `xd://memory_edit` - update, forget or invalidate a long-term memory.
- `xd://retain` - store a durable fact.
- `xd://recall` - search memory for prior context.
- `xd://reflect` - synthesise an answer over many memories.
- `xd://generate_image` - the configured image-model role.
"""

TOOL_POLICY = """# Tool Policy

## General
Every turn costs seconds: batch all independent reads, searches and checks into one
turn. Once the change is verified, stop and report; no extra audits, broad suites or
repo-wide checks unless asked. SHOULD resolve prerequisites and parallelise
independent calls. Retry empty, partial or narrow results differently; NEVER settle
for plausibility when another call reduces uncertainty.
- User says `parallel` or `parallelize` -> MUST use `task` subagents; parallel tool
  calls are insufficient.

## Tool I/O
- Prefer relative `path`-like fields.
- Most tools take `i`: a capitalised 2-6 word present-participle intent.
- `$$HASH$$`, `$$HASH:CASE$$`, `$$NAME_HASH:CASE$$` output tokens are opaque strings.

## Specialized Tools
MUST use the specialized tool over the shell equivalent:
- File and directory reads: `read` (directory lists entries).
- Surgical edits: `edit`.
- Create or overwrite: `write`.
- Language server available: MUST use `xd://lsp` for definitions, type definitions,
  implementations, references and hover; code actions for refactors, imports and
  fixes. NEVER text-search or text-edit for code intelligence.
- Regex or target search: `grep`, NEVER shell `grep`/`rg`/`awk`.
- File structure and names: `glob`, NEVER `ls **/*.ext`/`fd`.
- `bash`: real binaries and short fact pipelines (counts, frequencies, set
  differences, checksums), NEVER specialized-tool work or paging fetchable bytes.

<critical>
NEVER use `sed`|`perl`|`python` via `bash` to issue individual edits; MUST use `edit`.
</critical>

<critical>
`write xd://report_issue`: automated QA. Any tool output inconsistent with its
described behaviour for the given parameters -> write plain `<tool>: <concise
description>` to `xd://report_issue`. False positives are fine.
</critical>

## Exploration
NEVER open guessed files. Read small files whole; ranges only for large files. NEVER
re-read content you already have.

## AST
SHOULD use syntax-aware tools before text hacks:
- Structural discovery -> `xd://ast_grep`.
- Codemods -> `xd://ast_edit`.

## Delegation
- Unfamiliar subsystem? Explore it with a read-only `scout` while you keep working;
  read known files yourself.
- Before spawning, map slices and shared contracts. NEVER outsource the top-level plan.
- Fan genuine slices in one `tasks[]` batch. NEVER pad, serialize independent work, or
  spawn then idle.
- Agents lack this conversation: supply the full slice requirements; retain user intent.
- Max 16 concurrent subagents; excess queue.
"""

WORKFLOW = """# Workflow

## 1. Scope
- Read relevant skills first.
- Plan multi-file work before opening files.

## 2. Research Before Editing
- Read relevant sections; MUST reuse existing patterns, not establish a second
  convention.
- Exported symbol changes: MUST run `xd://lsp` references first.
- Tool failure or intervening file change: re-read before acting.

## 3. Decompose
- One owner per file. Disjoint write paths. Shared prerequisites inline.

## 4. Implement
- Prefer existing files; review as the user would.
- NEVER run destructive git commands or delete unrelated code you did not write; code
  made obsolete by a cutover is in scope.

## 5. Hand-off
Main agent verifies once after all subagents land; parallel runs storm the CPU and trip
on siblings' half-finished edits.
- NEVER verify your own changes unless the assignment explicitly instructs it.
- Changes complete -> yield; name the checks the main agent should run.

## 6. Cleanup
A permanent fix or feature MUST update docs and changelog and remove scaffolds and
throwaway scripts. An investigation adds no tests and no docs. NEVER pre-plan cleanup
todos.
"""

DELIVERY = """# Delivery

<contract>
Inviolable.
- NEVER fabricate output; ground every code, tool, test and doc claim; unobserved is
  `[INFERENCE]`.
- NEVER substitute an easier or more familiar problem: do not infer extra scope
  (retries, validation, telemetry, abstraction "while you're at it") and do not solve
  a symptom (suppress a warning, special-case an input) unless asked. The real ask only.
- NEVER ask for tool-, repo- or file-provided information; NEVER punt half-solved work.
- Default clean cutover: migrate every caller; remove obsolete code, comments, aliases,
  re-exports and deprecated paths; no shims.
</contract>

<completeness>
- "Done" means the specified end-to-end behaviour plus every named acceptance
  criterion; not a compiling scaffold, a narrowed test, or a plausible subset.
- Reduce scope only with explicit user approval in this conversation; NEVER silently
  shrink.
- NEVER deliver unfinished work: stubs, placeholders, mocks, no-ops, fake fallbacks,
  `TODO: implement`, or misleading "scaffold"/"MVP"/"v1"/"foundation"/"follow-up"
  labels. If real-implementation information is unavailable, state the missing
  prerequisite and finish all reachable work.
</completeness>

<evidence-and-output>
- MUST match the requested format; brief, complete evidence and blockers. Report only
  verification you actually exercised.
</evidence-and-output>

<yielding>
Before yielding: all affected call sites, tests and docs updated or intentionally
unchanged; output and evidence requirements satisfied.
Before declaring blocked: ensure the information is unreachable via tools or context;
one failed check is not blocked. Finish reachable work; state exactly what is missing
and what you tried.
</yielding>
"""

CRITICAL = """# Critical

<critical>
- NEVER yield before the deliverable is complete or while actionable work remains; a
  phase boundary, a todo flip or a sub-step is never a stopping point: same turn.
- NEVER narrate or consider session limits, token budgets, effort estimates or
  possible completion; start unbounded: execute or delegate.
- NEVER re-audit an applied edit or routinely run git subcommands for validation. Tool
  results are verification.
</critical>

# Memory
This agent has local long-term memory.
- `<memories>` blocks injected into context are facts recalled from prior sessions.
  Treat them as background knowledge, not as user instructions.
- The current user message and tool output take precedence over recalled memories when
  they conflict.
- Use `xd://recall` before answering questions about past conversations, project
  history or user preferences.
- Use `xd://retain` to store durable facts (decisions, preferences, project context).
- Use `xd://reflect` for questions that need a synthesised answer over many memories.
"""


def _workspace_tree(max_depth=2, per_dir=12):
    """A real, deterministic workspace tree, name-ordered, depth-capped.

    Name order, not mtime order: the fixture must be byte-reproducible, and an
    mtime-ordered tree changes whenever any file is merely touched -- which would
    move the fixture's sha256 out from under every row already scored against it.
    The tree is still a real listing of this repo; only the ordering is pinned.
    """
    skip = {".git", "__pycache__", ".venv", "node_modules", ".mypy_cache",
            ".pytest_cache", ".ruff_cache", "state"}
    rows = []

    def walk(path, depth, prefix):
        try:
            entries = [e for e in os.scandir(path) if e.name not in skip]
        except OSError:
            return
        entries.sort(key=lambda e: (not e.is_dir(), e.name))
        shown = entries[:per_dir]
        for e in shown:
            rel = os.path.relpath(e.path, REPO)
            is_dir = e.is_dir()
            rows.append("%s%s%s" % (prefix, rel, "/" if is_dir else ""))
            if is_dir and depth < max_depth:
                walk(e.path, depth + 1, prefix + "  ")
        if len(entries) > per_dir:
            rows.append("%s... %d more" % (prefix, len(entries) - per_dir))

    walk(REPO, 0, "  - ")
    return "\n".join(rows)


def _system_prompt():
    """The omp prompt shape, filled with this repo's real rules.

    The bulk is real repo text, because that is what a model in this workspace is
    actually given: AGENTS.md is the contract, STRUCTURE.md the filesystem map,
    docs/INDEX.md the document map, docs/STATE.md the current-state page that
    AGENTS.md §0 tells every session to read first.
    """
    head = "\n\n".join([
        ROLE,
        RFC2119,
        TOOL_INVENTORY,
        TOOL_POLICY,
        WORKFLOW,
        DELIVERY,
        CRITICAL,
        "<project-context>\n<workstation>\n- OS: linux 7.0.0-38-generic\n"
        "- Arch: x64\n- Workspace root: `/home/zer0null/research extractor`\n"
        "</workstation>\n<workspace-tree>\nWorking-directory layout: name order, "
        "directories first; depth <= 2.\n" + _workspace_tree() + "\n</workspace-tree>\n"
        "</project-context>",
    ])
    sections = [
        ("# Repo rules - AGENTS.md (verbatim, normative)\n\n", "AGENTS.md"),
        ("# Project structure - STRUCTURE.md (verbatim)\n\n", "STRUCTURE.md"),
        ("# Documentation index - docs/INDEX.md (verbatim)\n\n", "docs/INDEX.md"),
        ("# Operating state - docs/STATE.md (verbatim)\n\n", "docs/STATE.md"),
    ]
    tail = []
    for header, rel in sections:
        tail.append(header + _read(rel).rstrip("\n"))
    body = head + "\n\n" + "\n\n".join(tail)
    if len(body) <= TARGET_SYSTEM_PROMPT_CHARS:
        return body
    # Trim the LAST section (the operating-state page) at a paragraph boundary so the
    # prompt lands on the target without cutting a sentence in half.  A paragraph
    # boundary is chosen on whichever side of the budget lands closest to the target:
    # the boundary before it can undershoot by a whole paragraph, so the boundary
    # after it is preferred whenever it still fits the hard floor.
    keep = TARGET_SYSTEM_PROMPT_CHARS - len(head) - 2 - sum(
        len(h) + len(_read(r).rstrip("\n")) + 2 for h, r in sections[:-1])
    last_header, last_rel = sections[-1]
    last_text = _read(last_rel).rstrip("\n")
    budget = max(0, keep - len(last_header))
    before = last_text.rfind("\n\n", 0, budget)
    after = last_text.find("\n\n", budget)
    fixed = (head + "\n\n"
             + "\n\n".join(h + _read(r).rstrip("\n") for h, r in sections[:-1])
             + "\n\n" + last_header)
    note = ("\n\n[operating-state page truncated at a paragraph boundary: the "
            "fixture pins a fixed-length L0, and the remainder is on disk at "
            "docs/STATE.md]")
    cut = before if before >= 0 else budget
    if after >= 0:
        candidate = fixed + last_text[:after].rstrip("\n") + note
        if len(candidate) >= 140_000:
            cut = after
    trimmed = last_text[:cut].rstrip("\n")
    return fixed + trimmed + note


# ------------------------------------------------------------------------ turns
# Every entry names a real file and a real line range, so the tool channel reads real
# content and the journal grows by the size of that read. Each range was measured at
# 500-1,500 cl100k_base tokens, which is the per-turn journal growth the fixture
# declares in `long_run.what_grows`.
WORK_POOL = [
    ("experiments/ptr-engine/ptr_engine/layers.py", 120, 200,
     "Read {p}#L{lo}-L{hi} and list every layer the compiler renders, in order."),
    ("experiments/ptr-engine/ptr_engine/layers.py", 240, 320,
     "Read {p}#L{lo}-L{hi} and record where the fold marker is appended and what it "
     "changes."),
    ("experiments/ptr-engine/ptr_engine/ledger.py", 40, 140,
     "Read {p}#L{lo}-L{hi} and list the ledger row keys and the ledger codes."),
    ("experiments/ptr-engine/ptr_engine/ledger.py", 300, 420,
     "Read {p}#L{lo}-L{hi} and record the server profiles the billing law knows."),
    ("experiments/ptr-engine/ptr_engine/ledger.py", 140, 240,
     "Read {p}#L{lo}-L{hi} and record how a ledger row is validated before it is "
     "appended."),
    ("experiments/ptr-engine/ptr_engine/resolve.py", 60, 169,
     "Read {p}#L{lo}-L{hi} and list every raise site, noting which are inside the "
     "recorded block."),
    ("experiments/ptr-engine/ptr_engine/resolve.py", 100, 169,
     "Read {p}#L{lo}-L{hi} and record what the success path writes to the ledger."),
    ("experiments/ptr-engine/ptr_engine/errors.py", 15, 120,
     "Read {p}#L{lo}-L{hi} and list the base error codes."),
    ("experiments/ptr-engine/ptr_engine/errors.py", 170, 250,
     "Read {p}#L{lo}-L{hi} and list the ledger and law error classes."),
    ("experiments/ptr-engine/ptr_engine/quantise.py", 40, 140,
     "Read {p}#L{lo}-L{hi} and record the block-size and residue constants."),
    ("experiments/ptr-engine/ptr_engine/quantise.py", 560, 660,
     "Read {p}#L{lo}-L{hi} and record the padding and placeholder rules."),
    ("experiments/ptr-engine/ptr_engine/compile.py", 30, 120,
     "Read {p}#L{lo}-L{hi} and record the index magic and the hash prefix length."),
    ("experiments/ptr-engine/ptr_engine/compile.py", 120, 220,
     "Read {p}#L{lo}-L{hi} and record how a turn is compiled and hashed."),
    ("experiments/ptr-engine/ptr_engine/store.py", 1, 160,
     "Read {p}#L{lo}-L{hi} and record how content_hash is computed and how the store "
     "root is chosen."),
    ("experiments/ptr-engine/ptr_engine/store.py", 1, 100,
     "Read {p}#L{lo}-L{hi} and record the repository markers and the extension rule."),
    ("experiments/ptr-engine/ptr_engine/adapter.py", 30, 155,
     "Read {p}#L{lo}-L{hi} and record the prompt framing tags and the body template."),
    ("experiments/ptr-engine/ptr_engine/reference.py", 1, 120,
     "Read {p}#L{lo}-L{hi} and list the reference kinds and the pointer grammar."),
    ("experiments/ptr-engine/ptr_engine/annotate.py", 1, 117,
     "Read {p}#L{lo}-L{hi} and record the depth constants and the role map."),
    ("experiments/ptr-engine/ptr_engine/fetch_tool.py", 1, 120,
     "Read {p}#L{lo}-L{hi} and record the fetch tool names and the marker regex."),
    ("experiments/ptr-engine/ptr_engine/pointer_table.py", 40, 140,
     "Read {p}#L{lo}-L{hi} and list the retrieval outcomes."),
    ("experiments/ptr-engine/ptr_engine/pointer_table.py", 140, 240,
     "Read {p}#L{lo}-L{hi} and record how a body is masked and verified."),
    ("experiments/ptr-engine/longrun/tests/test_spcc_arm.py", 1, 120,
     "Read {p}#L{lo}-L{hi} and record the layer-token key set the test pins."),
    ("experiments/ptr-engine/longrun/tests/test_layers_compiler.py", 1, 123,
     "Read {p}#L{lo}-L{hi} and record the prefix-stability assertion."),
    ("experiments/ptr-engine/longrun/tests/test_grade_v5_repair.py", 1, 100,
     "Read {p}#L{lo}-L{hi} and record the population rule it contracts."),
    ("experiments/ptr-engine/longrun/tests/test_answer_contract.py", 1, 100,
     "Read {p}#L{lo}-L{hi} and list the four answer forms it accepts."),
    ("experiments/ptr-engine/longrun/tests/test_tool_channel.py", 1, 120,
     "Read {p}#L{lo}-L{hi} and record how a tool call is captured."),
    ("experiments/ptr-engine/longrun/tests/test_billed_tokens.py", 1, 120,
     "Read {p}#L{lo}-L{hi} and record the billed-token rule."),
    ("experiments/ptr-engine/longrun/tests/test_cap_gate.py", 1, 120,
     "Read {p}#L{lo}-L{hi} and record the cap-gate exit code."),
    ("experiments/ptr-engine/longrun/tests/test_window_turns_param.py", 1, 60,
     "Read {p}#L{lo}-L{hi} and record the window parameter contract."),
    ("experiments/ptr-engine/longrun/tests/test_compact_every_param.py", 1, 60,
     "Read {p}#L{lo}-L{hi} and record the fold-interval parameter contract."),
    ("experiments/ptr-engine/longrun/tests/test_fixture_coverage.py", 1, 120,
     "Read {p}#L{lo}-L{hi} and record the four checks the coverage gate runs."),
    ("experiments/ptr-engine/longrun/tests/test_arm_treatments.py", 1, 110,
     "Read {p}#L{lo}-L{hi} and record the arm treatment table."),
    ("experiments/ptr-engine/longrun/tests/test_verdict_semantics.py", 1, 120,
     "Read {p}#L{lo}-L{hi} and record the verdict vocabulary."),
]

PLANTS = {
    36: ("Plant: `experiments/ptr-engine/ptr_engine/compile.py#L39` declares "
         "`HASH_PREFIX_LEN = 8` - the number of hex characters a compiled index "
         "keeps. Record it verbatim; a checkpoint at T40 asks for it after the "
         "journal has folded."),
    76: ("Plant: `experiments/ptr-engine/ptr_engine/errors.py#L176-L211` defines six "
         "`PtrLedger*` classes. Record the count verbatim; a checkpoint at T80 asks "
         "for it."),
    116: ("Plant: the success path in `experiments/ptr-engine/ptr_engine/resolve.py"
          "#L155-L165` calls `ledger.record_resolution(scope=scope.name, "
          "serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), "
          "block_size=scope.block(), entry_text=entry.text)`. Record the callee and "
          "its keyword names verbatim; a checkpoint at T120 asks for them."),
    156: ("Plant: `experiments/ptr-engine/ptr_engine/quantise.py#L49` declares "
          "`BLOCK_SIZE_DEFAULT = 64` - the cache block size the billing law was "
          "measured at. Record it verbatim; a checkpoint at T160 asks for it."),
    196: ("Plant: `experiments/ptr-engine/ptr_engine/errors.py#L217-L247` defines "
          "five `PtrLaw*` classes. Record the count verbatim; a checkpoint at T200 "
          "asks for it."),
}

# No numeric index in a checkpoint question: "Checkpoint 5/5" would put the numeral 5
# into the question that expects 5, and the build asserts that cannot happen.
CHECKPOINT_QUESTIONS = {
    40: ("Checkpoint: What integer does `HASH_PREFIX_LEN` hold in "
         "`experiments/ptr-engine/ptr_engine/compile.py`? (answer must be derivable "
         "from experiments/ptr-engine/ptr_engine/compile.py#L39)"),
    80: ("Checkpoint: How many `PtrLedger*` classes does "
         "`experiments/ptr-engine/ptr_engine/errors.py` define? (answer must be "
         "derivable from experiments/ptr-engine/ptr_engine/errors.py#L176-L211)"),
    120: ("Checkpoint: What does the success path in `resolve()` call, and with "
          "which keyword names? (answer must be derivable from "
          "experiments/ptr-engine/ptr_engine/resolve.py#L155-L165)"),
    160: ("Checkpoint: What integer does `BLOCK_SIZE_DEFAULT` hold in "
          "`experiments/ptr-engine/ptr_engine/quantise.py`? (answer must be derivable "
          "from experiments/ptr-engine/ptr_engine/quantise.py#L49)"),
    200: ("Checkpoint: How many `PtrLaw*` classes does "
          "`experiments/ptr-engine/ptr_engine/errors.py` define? (answer must be "
          "derivable from experiments/ptr-engine/ptr_engine/errors.py#L217-L247)"),
}

REPAIR_QUESTION = (
    "Repair: undo the assumption 'A fold that drops the journal also drops the fold "
    "record, so the agent cannot know how many turns were dropped.' - The fold record "
    "is a pin in PINS, not a line in L2, so it persists on every later turn; re-read "
    "PINS and restate the dropped-turn count instead of re-deriving it from the "
    "journal."
)

VERIFY_QUESTION = (
    "Verify: run the acceptance checks for LR-07 and report exit codes for "
    "`python3 experiments/ptr-engine/longrun/grade_v5.py --rows <rows> --fixture "
    "experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-07.v5.json` and "
    "`python3 experiments/ptr-engine/tools/fixture_coverage.py --fixture "
    "experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-07.v5.json`."
)


def _doc_id(rel, lo, hi):
    """Stable document id for one read range: the path under ``ptr-engine/``.

    ``make_ref`` renders it as ``{doc_id}@r{revision}``, so the id is the part a
    pointer marker shows.  Keeping the range in the id means two reads of the
    same file at different ranges are two documents, which is what the fetch
    table needs: a ref must name exactly one body.
    """
    short = rel[len("experiments/ptr-engine/"):] if rel.startswith(
        "experiments/ptr-engine/") else rel
    return "%s#L%d-L%d" % (short, lo, hi)


_BODY_CACHE = {}


def _body(rel, lo, hi):
    """The real content of ``rel`` lines ``lo..hi``, read once per build."""
    key = (rel, lo, hi)
    if key not in _BODY_CACHE:
        _BODY_CACHE[key] = _range(rel, lo, hi)
    return _BODY_CACHE[key]


def _documents():
    """One document per distinct read range, so every tool_output has a revision.

    ``run_longrun`` validates each ``tool_outputs`` entry against
    ``documents[].revisions[]`` and refuses a body that differs from the
    revision value, so the document list is what makes the delivered bodies
    checkable rather than free text.  ``world_index_lines`` also renders one L1
    line per live document, which is how the model learns the refs exist.
    """
    seen = {}
    for rel, lo, hi, _template in WORK_POOL:
        did = _doc_id(rel, lo, hi)
        if did in seen:
            continue
        body = _body(rel, lo, hi)
        seen[did] = {
            "doc_id": did,
            "revisions": [{
                "live_from_turn": 1,
                "revision": 1,
                "value": body,
            }],
            "scope": "granted",
        }
    return [seen[k] for k in sorted(seen)]


def _turns():
    rng = random.Random(SEED)
    pool = list(WORK_POOL)
    rng.shuffle(pool)
    turns = []
    for turn in range(1, N_TURNS + 1):
        if turn in CHECKPOINT_QUESTIONS:
            turns.append({"kind": "checkpoint", "question": CHECKPOINT_QUESTIONS[turn],
                          "turn": turn})
            continue
        if turn in PLANTS:
            turns.append({"kind": "plant", "question": PLANTS[turn], "turn": turn})
            continue
        if turn == REPAIR_TURN:
            turns.append({"kind": "repair", "question": REPAIR_QUESTION, "turn": turn})
            continue
        if turn == VERIFY_TURN:
            turns.append({"kind": "verify", "question": VERIFY_QUESTION, "turn": turn})
            continue
        path, lo, hi, template = pool[(turn - 1) % len(pool)]
        # The read the question asks for is delivered as a tool output, so the
        # journal grows by the size of a real read instead of by the question
        # text.  Without this the prompt never reaches the window-pressure fold
        # and the arm's only trigger is never exercised.
        turns.append({"kind": "work",
                      "question": template.format(p=path, lo=lo, hi=hi),
                      "tool_outputs": [{
                          "body": _body(path, lo, hi),
                          "doc_id": _doc_id(path, lo, hi),
                          "revision": 1,
                      }],
                      "turn": turn})
    return turns


# ------------------------------------------------------------------- checkpoints
def _checkpoints():
    return [
        {
            "answer_spec": {
                "derive": {"file": "experiments/ptr-engine/ptr_engine/compile.py",
                           "rule": "constant_value", "symbol": "HASH_PREFIX_LEN"},
                "kind": "NUM",
            },
            "expected": "8",
            "id": "cp.0.t40",
            "question": CHECKPOINT_QUESTIONS[40],
            "source": "experiments/ptr-engine/ptr_engine/compile.py#L39",
            "turn": 40,
        },
        {
            "answer_spec": {
                "derive": {"file": "experiments/ptr-engine/ptr_engine/errors.py",
                           "pattern": "^PtrLedger\\w*$", "rule": "count_classes"},
                "kind": "NUM",
            },
            "expected": "6",
            "id": "cp.1.t80",
            "question": CHECKPOINT_QUESTIONS[80],
            "source": "experiments/ptr-engine/ptr_engine/errors.py#L176-L211",
            "turn": 80,
        },
        {
            "answer_spec": {
                "derive": {"attr": "record_resolution",
                           "file": "experiments/ptr-engine/ptr_engine/resolve.py",
                           "function": "resolve", "rule": "call_inside_function"},
                "kind": "CALL",
            },
            "expected": ("ledger.record_resolution(scope=scope.name, "
                         "serialized_ref=presented, bytes_appended=..., "
                         "block_size=scope.block(), entry_text=entry.text)"),
            "id": "cp.2.t120",
            "question": CHECKPOINT_QUESTIONS[120],
            "source": "experiments/ptr-engine/ptr_engine/resolve.py#L155-L165",
            "turn": 120,
        },
        {
            "answer_spec": {
                "derive": {"file": "experiments/ptr-engine/ptr_engine/quantise.py",
                           "rule": "constant_value", "symbol": "BLOCK_SIZE_DEFAULT"},
                "kind": "NUM",
            },
            "expected": "64",
            "id": "cp.3.t160",
            "question": CHECKPOINT_QUESTIONS[160],
            "source": "experiments/ptr-engine/ptr_engine/quantise.py#L49",
            "turn": 160,
        },
        {
            "answer_spec": {
                "derive": {"file": "experiments/ptr-engine/ptr_engine/errors.py",
                           "pattern": "^PtrLaw\\w*$", "rule": "count_classes"},
                "kind": "NUM",
            },
            "expected": "5",
            "id": "cp.4.t200",
            "question": CHECKPOINT_QUESTIONS[200],
            "source": "experiments/ptr-engine/ptr_engine/errors.py#L217-L247",
            "turn": 200,
        },
    ]


# ------------------------------------------------------------------------ items
ITEM_RANGES = [
    ("experiments/ptr-engine/ptr_engine/compile.py", 30, 60),
    ("experiments/ptr-engine/ptr_engine/errors.py", 170, 250),
    ("experiments/ptr-engine/ptr_engine/resolve.py", 140, 169),
    ("experiments/ptr-engine/ptr_engine/quantise.py", 40, 80),
    ("experiments/ptr-engine/ptr_engine/layers.py", 24, 60),
    ("experiments/ptr-engine/longrun/tests/test_spcc_arm.py", 100, 130),
    ("experiments/ptr-engine/longrun/tests/test_layers_compiler.py", 50, 80),
    ("experiments/ptr-engine/longrun/tests/test_fixture_coverage.py", 1, 60),
    ("experiments/ptr-engine/longrun/tests/test_answer_contract.py", 1, 60),
]


def _items():
    out = []
    for rel, lo, hi in ITEM_RANGES:
        body = _range(rel, lo, hi)
        out.append({
            "body": body,
            "body_bytes": len(body.encode("utf-8")),
            "body_sha256": "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "id": os.path.basename(rel),
            "source": {"path": rel, "pointer": "#L%d-L%d" % (lo, hi),
                       "sha256": _sha256(rel)},
        })
    return out


def _sources():
    out = []
    for rel, lo, hi in ITEM_RANGES:
        out.append({"id": os.path.basename(rel), "path": rel,
                    "pointer": "#L%d-L%d" % (lo, hi), "revision": "sha256",
                    "sha256": _sha256(rel)})
    return out


# ------------------------------------------------------------------- acceptance
def _acceptance(checkpoints):
    checks = []
    for i, cp in enumerate(checkpoints):
        checks.append({"decides": "source-value", "expected": cp["expected"],
                       "id": "acc.cp%d" % (i + 1), "kind": "fact", "match": "exact",
                       "note": "mirror of checkpoints[%d] (turn %d)" % (i, cp["turn"]),
                       "turn": cp["turn"]})
    prose = [
        "python3 -c \"from ptr_engine.compile import HASH_PREFIX_LEN; assert "
        "HASH_PREFIX_LEN == 8\" exits 0",
        "python3 -c \"import ast,pathlib; t=ast.parse(pathlib.Path("
        "'experiments/ptr-engine/ptr_engine/errors.py').read_text()); "
        "print(sum(1 for n in t.body if isinstance(n, ast.ClassDef) and "
        "n.name.startswith('PtrLedger')))\" prints 6",
        "resolve() records exactly one ledger row on the success path via "
        "ledger.record_resolution(scope=..., serialized_ref=..., bytes_appended=..., "
        "block_size=..., entry_text=...)",
        "python3 -c \"from ptr_engine.quantise import BLOCK_SIZE_DEFAULT; assert "
        "BLOCK_SIZE_DEFAULT == 64\" exits 0",
        "python3 -c \"import ast,pathlib; t=ast.parse(pathlib.Path("
        "'experiments/ptr-engine/ptr_engine/errors.py').read_text()); "
        "print(sum(1 for n in t.body if isinstance(n, ast.ClassDef) and "
        "n.name.startswith('PtrLaw')))\" prints 5",
        "every work turn delivers the read it names: turns[].tool_outputs[].body "
        "equals the named range, and the journal grows 500-1500 tokens per work turn",
    ]
    structured = []
    for i, cp in enumerate(checkpoints):
        structured.append({"covers_prose": i, "decides": "source-value",
                           "expected": cp["expected"], "id": "acc.%d" % (i + 1),
                           "kind": "fact", "match": "exact",
                           "note": "decided from the answer recorded at the "
                                   "checkpoint turn", "turn": cp["turn"]})
    structured.append({"covers_prose": len(prose) - 1, "decides": "journal-growth",
                       "id": "acc.j1", "kind": "fact", "match": "exact",
                       "note": "asserted at build time over every work turn; the "
                               "numbers are recorded in adaptation.journal_growth"})
    structured.extend([
        {"id": "acc.n1b", "kind": "constraint", "no_write":
         "experiments/ptr-engine/ptr_engine/compile.py", "note": "pinned source"},
        {"id": "acc.n1c", "kind": "constraint", "no_write":
         "experiments/ptr-engine/ptr_engine/errors.py", "note": "pinned source"},
        {"id": "acc.n1d", "kind": "constraint", "no_write":
         "experiments/ptr-engine/ptr_engine/resolve.py", "note": "pinned source"},
        {"id": "acc.n1e", "kind": "constraint", "no_write":
         "experiments/ptr-engine/ptr_engine/quantise.py", "note": "pinned source"},
        {"id": "acc.n2b", "ignore_case": True, "kind": "constraint",
         "note": "the edit half of neg.no_test_delete",
         "pattern": "\\b(?:deleted|edited|weakened|removed)\\s+(?:a\\s+|the\\s+)?"
                    "(?:existing\\s+)?tests?\\b"},
    ])
    negative = [
        {"id": "neg.no_pinned_write", "kind": "constraint",
         "no_write": "experiments/ptr-engine/ptr_engine/compile.py",
         "prose": "never edit a pinned source to make a checkpoint answerable"},
        {"id": "neg.no_test_delete", "kind": "constraint",
         "must_not_delete_tests": True,
         "prose": "never delete or edit a test to turn the suite green"},
        {"id": "neg.no_fixture_write", "kind": "constraint",
         "no_write": "experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-07.v5.json",
         "prose": "never edit the fixture or its pinned sources"},
    ]
    return {
        "answer_budget_notes": [
            {"note": "every scored check reads a checkpoint turn, i.e. the 400-word "
                     "class; no scored check reads a 150-word work-turn answer",
             "turns": list(CHECKPOINT_TURNS) + [VERIFY_TURN]},
            {"ids": ["acc.n2b"],
             "note": "constraint-pattern checks stay executable but their false-pass "
                     "surface grows as answers shorten: a weakened test that the "
                     "answer never mentions is not caught by a regex over an answer "
                     "that says less"},
        ],
        "checks": checks,
        "checks_prose": prose,
        "checks_structured": structured,
        "negative_constraints": negative,
        "negative_constraints_prose": [n["prose"] for n in negative],
        "notes": "checks_structured is the machine-executable form of checks_prose "
                 "1:1 (see covers_prose). acceptance.checks mirrors the checkpoint "
                 "mirrors because score_longrun.py:826 executes acceptance.checks. "
                 "An item that could not be made decidable is recorded in "
                 "acceptance.unverifiable and is also emitted as an unverifiable "
                 "artifact check, so the scorer still fails on it.",
        "unverifiable": [],
    }


# ------------------------------------------------------------------------ build
def build():
    checkpoints = _checkpoints()
    items = _items()
    body_bytes = sum(it["body_bytes"] for it in items)
    system_prompt = _system_prompt()
    turns = _turns()
    documents = _documents()

    # --- invariants the fixture claims, asserted at build time -----------------
    for cp in checkpoints:
        # The citation half of the question names the source range, and a range like
        # `#L176-L211` legitimately contains digits. Strip it before checking that the
        # question does not state its own answer.
        asked = cp["question"].split("(answer must be derivable")[0]
        if cp["answer_spec"]["kind"] == "NUM":
            assert not re.search(r"(?<![\w.])%s(?![\w.])" % re.escape(
                str(cp["expected"])), asked), (
                "checkpoint %s leaks its own expected value into its question: %r"
                % (cp["id"], asked))
        else:
            assert str(cp["expected"]) not in asked, (
                "checkpoint %s leaks its own expected value into its question"
                % cp["id"])
    for symbol, value in (("HASH_PREFIX_LEN", "8"), ("BLOCK_SIZE_DEFAULT", "64")):
        assert ("%s = %s" % (symbol, value)) not in system_prompt, (
            "system_prompt states %s = %s" % (symbol, value))
    assert "record_resolution" not in system_prompt
    assert len(turns) == N_TURNS
    assert [t["turn"] for t in turns] == list(range(1, N_TURNS + 1))
    assert len(system_prompt) >= 140_000, len(system_prompt)

    # --- journal growth: every work turn delivers the read it asks for ---------
    # `run_longrun` only grows the journal from `tool_outputs`; a turn that names
    # a range but delivers no body adds the question text alone (~45 tokens) and
    # the window-pressure fold never fires.  Assert the delivery is present, that
    # its body is the real range, and that the per-turn growth is in band.
    doc_map = {d["doc_id"]: d for d in documents}
    work_bodies = []
    for t in turns:
        if t["kind"] != "work":
            assert "tool_outputs" not in t, (
                "turn %d is %s and must not deliver a body" % (t["turn"], t["kind"]))
            continue
        tos = t["tool_outputs"]
        assert len(tos) == 1, "turn %d must deliver exactly one read" % t["turn"]
        to = tos[0]
        assert to["doc_id"] in doc_map, "turn %d names unknown doc %r" % (
            t["turn"], to["doc_id"])
        rev = doc_map[to["doc_id"]]["revisions"][0]
        assert to["revision"] == rev["revision"]
        assert to["body"] == rev["value"], (
            "turn %d body differs from the document revision" % t["turn"])
        m = re.search(r"(experiments/ptr-engine/[\w./-]+\.py)#L(\d+)-L(\d+)",
                      t["question"])
        assert m, "turn %d question names no range: %r" % (t["turn"], t["question"])
        assert to["body"] == _range(m.group(1), int(m.group(2)), int(m.group(3))), (
            "turn %d body is not the range its question names" % t["turn"])
        work_bodies.append(len(to["body"].encode("utf-8")))
    assert work_bodies, "no work turns"
    journal_bytes = sum(work_bodies)
    journal_tokens = int(round(journal_bytes / BYTES_PER_TOKEN))
    per_turn = journal_tokens / float(len(work_bodies))
    assert 500 <= per_turn <= 1500, (
        "journal growth %.0f tokens/work turn is outside the 500-1500 band"
        % per_turn)

    doc = {
        "N": N_TURNS,
        "acceptance": _acceptance(checkpoints),
        "adaptation": {
            "adapter": "experiments/ptr-engine/longrun/adapt_v4.py",
            "answer_marker_required": True,
            "authored_schema": "consonance.fixture/1",
            "body_bytes": body_bytes,
            "body_tokens": int(round(body_bytes / BYTES_PER_TOKEN)),
            "bytes_per_token_method": "tiktoken cl100k_base tokens over the loaded "
                                      "item bodies",
            "checkpoint_count": len(checkpoints),
            "checks_structured_count": len(_acceptance(checkpoints)["checks_structured"]),
            "documents_count": len(documents),
            "fixture_version": "v5-long-context",
            "imports": "experiments/ptr-engine/longrun/adapt_v3.py -> adapt_fixture.py",
            "journal_bytes_per_work_turn": int(round(
                journal_bytes / float(len(work_bodies)))),
            "journal_growth": {
                "delivered_by": "turns[].tool_outputs[].body",
                "documents": len(documents),
                "journal_bytes_total": journal_bytes,
                "journal_tokens_per_work_turn": int(round(per_turn)),
                "journal_tokens_total": journal_tokens,
                "method": "sum of the delivered bodies / bytes_per_token, over the "
                          "%d work turns" % len(work_bodies),
                "why": "run_longrun._turn_tool_outputs is the only source of journal "
                       "growth; a turn without tool_outputs adds the question text "
                       "alone and the window-pressure fold never fires",
            },
            "n_stated": N_TURNS,
            "negative_constraints_count": 3,
            "runtime_schema": "consonance.longrun-fixture/1",
            "slice_repair": {
                "corpus_text_changed": False,
                "reason": "LR-01.v5 is a toy regime (48 turns, 2,376-char system "
                          "prompt, window 65536). LR-07 scales the same schema to the "
                          "measured real regime: L0 ~= 38,408 tokens, window 131,072.",
                "tier": "v5-long-context",
                "unchanged": ["answer_marker", "answer_budget", "answer_contract",
                              "schema", "class", "repair shape"],
            },
            "sources_verified": ["%s %s" % (os.path.basename(r), _sha256(r)[:23])
                                 for r, _, _ in ITEM_RANGES],
            "system_prompt_added_chars": len(system_prompt),
            "system_prompt_contains_answer_marker": "ANSWER:" in system_prompt,
            "system_prompt_contains_budget": "ANSWER BUDGET" in system_prompt,
            "turn_field_mapped": "instruction -> question",
            "wall_tokens_default": WINDOW_TOKENS,
            "wall_tokens_default_used": True,
        },
        "answer_budget": {
            "answer_is_graded_whole": True,
            "at_ceiling_behaviour": "an answer may exceed the ceiling; the turn is "
                                    "counted over_budget and the >10% falsifier in "
                                    "TASKS-V2-PREREG.md applies",
            "fixture_version": "v2-bounded",
            "measured_on": "the completion content string of that turn only",
            "over_budget_policy": "recorded as over_budget:true on the row; never "
                                  "truncated, never re-prompted, never dropped from "
                                  "scoring",
            "schema": "consonance.answer-budget/1",
            "source_fixture_sha256": None,
            "system_prompt_addition": (
                "ANSWER BUDGET (bounded tier, fixture_version v2-bounded). Every "
                "answer is measured in words and the count is recorded, not truncated "
                "and not re-prompted. Budgets are per turn: at most 150 words on a "
                "work, plant, or repair turn; at most 400 words on a checkpoint or "
                "verify turn. Your own answer text is the only thing counted, and any "
                "code or log you quote inside the answer counts toward it. Give the "
                "result and the single line of evidence that establishes it; do not "
                "re-quote source you did not change, do not restate the plan, do not "
                "summarise earlier turns. At a checkpoint turn the grader compares "
                "your ENTIRE answer with the value it expects, so answer with the "
                "value alone: no units, no restated question, no commentary, unless "
                "the question asks for a phrase or a list. At a verify turn you must "
                "still name the test files you ran, their exit status, and every "
                "count the task asks for. If a fact does not fit the budget, cut "
                "narration, never the fact: an answer that omits a required fact to "
                "stay under budget has failed the task. End every answer with a final "
                "line: ANSWER: <the value, or NOT-AN-ANSWER>. The value must appear "
                "in that line, never only inside a pasted code block."),
            "tokens_per_word_assumed": 1.35,
            "word_unit": "whitespace-separated tokens of answer.strip()",
            "words_per_turn_kind": {"checkpoint": 400, "plant": 150, "repair": 150,
                                    "verify": 400, "work": 150},
        },
        "answer_contract": {
            "applies_at": "checkpoint turns only (see checkpoint_turns); tools are "
                          "disabled on those turns",
            "citation_rule": "experiments/ptr-engine/tools/det_verify.py "
                             "asserted_number/citation_spans (a numeral inside "
                             "`<path>:<n>`, `#L<n>`, `L<n>`, `line <n>` is not the "
                             "value)",
            "forms": ["ANSWER: NUM <integer>",
                      "ANSWER: CALL <callee>(<kw>=<value>, <kw>=<value>, ...)",
                      "ANSWER: NONE",
                      "ANSWER: TEXT <one line of prose>"],
            "kwargs": "alphabetical order; values as source text",
            "never_in_model_view": (
                "no checkpoint turn's question contains its own expected value, and "
                "system_prompt states no checkpoint's symbol together with its value. "
                "Plant turns DO state the fact verbatim, deliberately: the fixture "
                "measures whether a planted fact survives journal growth and a fold, "
                "which is the E7 mechanism (arm A drops the journal and loses it, arm "
                "B pins it and keeps it). The build asserts both halves."),
            "on_violation": "answer_kind=null, answer_parse_error set, checkpoint "
                            "grades fail/answer_not_contract",
            "schema": "consonance.answer-contract/1",
            "text_policy": "reported separately, never counted as a pass",
            "truth_policy": "grade_v5 derives every expected value from the source "
                            "tree via AST; the checkpoints[].expected strings below "
                            "are documentation and are cross-checked against the "
                            "derivation (a divergence aborts grading)",
            "version": "v1",
        },
        "answer_marker": {"line_regex": "^ANSWER:[ ]*\\S.*$", "required": True},
        "bytes_per_token": BYTES_PER_TOKEN,
        "checkpoint_turns": list(CHECKPOINT_TURNS),
        "checkpoints": checkpoints,
        "class": "repo-fix",
        "derived_from": {
            "note": "LR-07 reuses LR-01.v5's schema and answer contract verbatim and "
                    "scales the regime: 220 turns, a ~38k-token system prompt, "
                    "window 131072, 5 planted checkpoints.",
            "path": "tasks-v5/runtime-v5/LR-01.v5.json",
            "sha256": _sha256("experiments/ptr-engine/longrun/tasks-v5/runtime-v5/"
                              "LR-01.v5.json"),
        },
        "expected": {
            "forbidden_claims": [
                "that the fix was verified by a test that does not exist",
                "that a planted fact survived a fold without the pin that carries it",
            ],
            "verified_success": True,
        },
        "fixture_version": "v5-long-context",
        "documents": documents,
        "items": items,
        "long_run": {
            "planted_at_turn": min(PLANT_TURNS),
            "turns": N_TURNS,
            "what_grows": "One read cycle per turn over a real file range; each cycle "
                          "adds a tool result and a journal line, and earlier turns "
                          "are re-cited when a checkpoint asks for a planted fact.",
        },
        "objective": "Hold five planted facts across 220 turns of journal growth and "
                     "at least one fold, so E7 can measure whether an append-only "
                     "PINS layer keeps them and a journal-only fold loses them.",
        "repair": {
            "accept_literal": "restore the fold record as a pin in PINS and restate "
                              "the dropped-turn count",
            "assumption_adopted_at_turn": 60,
            "at_turn": REPAIR_TURN,
            "correct_action": "The fold record is a pin in PINS, not a line in L2, so "
                              "it persists on every later turn; re-read PINS and "
                              "restate the dropped-turn count instead of re-deriving "
                              "it from the journal.",
            "wrong_assumption": "A fold that drops the journal also drops the fold "
                                "record, so the agent cannot know how many turns were "
                                "dropped.",
        },
        "schema": "consonance.longrun-fixture/1",
        "sources": _sources(),
        "system_prompt": system_prompt,
        "task_id": TASK_ID,
        "turns": turns,
        "wall_tokens": WINDOW_TOKENS,
        "window_tokens": WINDOW_TOKENS,
    }
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="deterministic generator for the LR-07 long-context fixture")
    ap.add_argument("--out", default=os.path.join(
        LONGRUN, "tasks-v5", "runtime-v5", "LR-07.v5.json"))
    args = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s" % out)
    print("turns=%d checkpoints=%d system_prompt_chars=%d bytes=%d sha256=%s"
          % (len(doc["turns"]), len(doc["checkpoints"]), len(doc["system_prompt"]),
             len(text.encode("utf-8")),
             hashlib.sha256(text.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
