#!/usr/bin/env python3
"""build_agentic_tasks.py - derive the stage-2 agentic task set from a snapshot root.

WHAT A TASK IS.  One task is one `consonance.longrun-fixture/2` fixture: a 16-step
episode in which the model, not a script, decides what to read next.  Four checkpoints
sit at turns 4, 8, 12 and 16 and ask for a fact that lives in the snapshot's source
tree.  The family is "trace a control to its use": find the definition, read its
default, find the overriding caller, report the effective value.

EVERY KEY IS DERIVED, NEVER TYPED.  Each checkpoint's `expected` is produced by
`det_verify.constant_value` / `det_verify.call_inside_function` on the snapshot, and
then re-derived a second time by `grade_v5.derive_truth` (the grader's own path) and
compared.  A hand-written key would be a claim about the tree that nothing checks.

A KEY THAT IS NOT UNIQUE IS NOT A FACT.  If the snapshot defines the same constant
twice, or calls the same attribute twice inside the same function, the "answer" is a
coin flip and the task is refused (`TaskRefused`) instead of written.  The scan covers
the whole snapshot, tests included, because a duplicate anywhere makes the question
ambiguous.

    python3 experiments/ptr-engine/longrun/tools/build_agentic_tasks.py \
        --root . --out experiments/ptr-engine/longrun/tasks-agentic
    python3 .../build_agentic_tasks.py --check      # re-derive, compare, write nothing

Zero model requests: this reads Python source only.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ENGINE = os.path.dirname(LONGRUN)
REPO = os.path.dirname(os.path.dirname(ENGINE))
for _p in (LONGRUN, os.path.join(LONGRUN, "tools"), os.path.join(ENGINE, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arm_cd                      # noqa: E402
import det_verify as dv            # noqa: E402
import grade_v5 as g5              # noqa: E402

SCHEMA = "consonance.longrun-fixture/2"
OUT_DIR = "experiments/ptr-engine/longrun/tasks-agentic"
STEPS = (4, 8, 12, 16)
N_STEPS = 16
WINDOW_TOKENS = 4096
BYTES_PER_TOKEN = 4.0914
GENERATION = "gen-7"
ERRORS_PY = "experiments/ptr-engine/ptr_engine/errors.py"
SNAPSHOT_DIRS = (
    "src/resextract",
    "experiments/ptr-engine/ptr_engine",
    "experiments/ptr-engine/longrun",
    "experiments/ptr-engine/tools",
)

TOOL_BLOCK = (
    "You have one tool. Call it as:\n"
    "  read_file(path=\"<repo-relative path>\", start_line=<int>, end_line=<int>)\n"
    "The index below lists document ids; a document body is served by\n"
    "  fetch(ref=\"<doc_id>\")\n"
    "Call a tool whenever you need source text. Do not answer from memory."
)

ANSWER_CONTRACT = (
    "Answer every question on its own line, in exactly one of these forms:\n"
    "  ANSWER: NUM <integer>\n"
    "  ANSWER: CALL <callee>(<kw>=<value>, <kw>=<value>, ...)   # kwargs alphabetical\n"
    "  ANSWER: NONE\n"
    "  ANSWER: TEXT <free text>\n"
    "A CALL answer is the call exactly as written in the source, with every keyword "
    "argument and its value; a NUM answer is the integer alone."
)


class TaskRefused(RuntimeError):
    """A task whose key is not a fact about the snapshot."""


# ------------------------------------------------------------------ the task set
TASKS = [
    {
        "task_id": "AG-01",
        "file": "src/resextract/refresh/writer.py",
        "statement": (
            "Audit the untracked-file writer. Establish the cap it applies to a single "
            "directory walk, the call it makes on each directory entry, the cap it "
            "applies to the whole untracked set, and the call it makes to read a "
            "policy file, then report each of them."
        ),
        "checkpoints": [
            {"turn": 4, "kind": "NUM", "symbol": "DEFAULT_MAX_FILES",
             "question": "What is the value of `DEFAULT_MAX_FILES` in "
                         "`src/resextract/refresh/writer.py`?"},
            {"turn": 8, "kind": "CALL", "function": "_walk_untracked_dir", "attr": "is_dir",
             "question": "In `_walk_untracked_dir` in `src/resextract/refresh/writer.py`, "
                         "report the single call made on a directory entry, exactly as "
                         "written, with its keyword arguments."},
            {"turn": 12, "kind": "NUM", "symbol": "DEFAULT_MAX_UNTRACKED_PATHS",
             "question": "What is the value of `DEFAULT_MAX_UNTRACKED_PATHS` in "
                         "`src/resextract/refresh/writer.py`?"},
            {"turn": 16, "kind": "CALL", "function": "policy_for_target", "attr": "read_text",
             "question": "In `policy_for_target` in `src/resextract/refresh/writer.py`, "
                         "report the single call that reads the policy file, exactly as "
                         "written, with its keyword arguments."},
        ],
    },
    {
        "task_id": "AG-02",
        "file": "src/resextract/doctor.py",
        "statement": (
            "Audit the doctor's dashboard probe. Establish the port it assumes, the "
            "client call it makes to the crawl bridge, the column width it uses for "
            "its table, and the call it makes to read a config file, then report each "
            "of them."
        ),
        "checkpoints": [
            {"turn": 4, "kind": "NUM", "symbol": "DASHBOARD_PORT",
             "question": "What is the value of `DASHBOARD_PORT` in "
                         "`src/resextract/doctor.py`?"},
            {"turn": 8, "kind": "CALL", "function": "probe_crawl_bridge", "attr": "Client",
             "question": "In `probe_crawl_bridge` in `src/resextract/doctor.py`, report "
                         "the single client call it makes, exactly as written, with its "
                         "keyword arguments."},
            {"turn": 12, "kind": "NUM", "symbol": "CLASS_WIDTH",
             "question": "What is the value of `CLASS_WIDTH` in "
                         "`src/resextract/doctor.py`?"},
            {"turn": 16, "kind": "CALL", "function": "endpoints", "attr": "read_text",
             "question": "In `endpoints` in `src/resextract/doctor.py`, report the "
                         "single call that reads the config file, exactly as written, "
                         "with its keyword arguments."},
        ],
    },
    {
        "task_id": "AG-03",
        "file": "experiments/ptr-engine/longrun/tools/build_long_fixture.py",
        "statement": (
            "Audit the long-fixture builder. Establish the system-prompt size it "
            "targets, the call it makes to render a turn template, the repair turn it "
            "reserves, and the call it makes to order workspace entries, then report "
            "each of them."
        ),
        "checkpoints": [
            {"turn": 4, "kind": "NUM", "symbol": "TARGET_SYSTEM_PROMPT_CHARS",
             "question": "What is the value of `TARGET_SYSTEM_PROMPT_CHARS` in "
                         "`experiments/ptr-engine/longrun/tools/build_long_fixture.py`?"},
            {"turn": 8, "kind": "CALL", "function": "_turns", "attr": "format",
             "question": "In `_turns` in "
                         "`experiments/ptr-engine/longrun/tools/build_long_fixture.py`, "
                         "report the single call that renders a turn template, exactly "
                         "as written, with its keyword arguments."},
            {"turn": 12, "kind": "NUM", "symbol": "REPAIR_TURN",
             "question": "What is the value of `REPAIR_TURN` in "
                         "`experiments/ptr-engine/longrun/tools/build_long_fixture.py`?"},
            {"turn": 16, "kind": "CALL", "function": "_workspace_tree", "attr": "sort",
             "question": "In `_workspace_tree` in "
                         "`experiments/ptr-engine/longrun/tools/build_long_fixture.py`, "
                         "report the single call that orders the entries, exactly as "
                         "written, with its keyword arguments."},
        ],
    },
    {
        "task_id": "AG-04",
        "file": "src/resextract/kg/staging.py",
        "statement": (
            "Audit the KG staging reader. Establish the element cap it enforces, the "
            "call it makes to read a manifest, the row cap it enforces, and the call "
            "it makes to order provenance suffixes, then report each of them."
        ),
        "checkpoints": [
            {"turn": 4, "kind": "NUM", "symbol": "XML_MAX_ELEMENTS",
             "question": "What is the value of `XML_MAX_ELEMENTS` in "
                         "`src/resextract/kg/staging.py`?"},
            {"turn": 8, "kind": "CALL", "function": "_load_manifest", "attr": "read_text",
             "question": "In `_load_manifest` in `src/resextract/kg/staging.py`, report "
                         "the single call that reads the manifest, exactly as written, "
                         "with its keyword arguments."},
            {"turn": 12, "kind": "NUM", "symbol": "XML_TABLE_ROWS",
             "question": "What is the value of `XML_TABLE_ROWS` in "
                         "`src/resextract/kg/staging.py`?"},
            {"turn": 16, "kind": "CALL", "function": "resolve_provenance", "attr": "sort",
             "question": "In `resolve_provenance` in `src/resextract/kg/staging.py`, "
                         "report the single call that orders the suffixes, exactly as "
                         "written, with its keyword arguments."},
        ],
    },
]


# ------------------------------------------------------------------ snapshot scan
def _abs(root: str, rel: str) -> str:
    return rel if os.path.isabs(rel) else os.path.join(root, rel)


def _py_files(root: str):
    for d in SNAPSHOT_DIRS:
        base = _abs(root, d)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(n for n in dirnames
                                 if n not in ("__pycache__", ".git", ".venv", "node_modules"))
            for name in sorted(filenames):
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)


def scan(root: str):
    """(constants, calls) over the whole snapshot: name -> [(rel, lineno)]."""
    consts, calls = {}, {}
    for path in _py_files(root):
        rel = os.path.relpath(path, root)
        try:
            tree, _sha = dv.parse_module(path)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for node in tree.body:
            names = []
            if isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                names = [node.target.id] if isinstance(node.target, ast.Name) else []
            for name in names:
                try:
                    dv.constant_value(tree, name)
                except (SystemExit, ValueError):
                    continue
                consts.setdefault(name, []).append((rel, node.lineno))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)):
                    calls.setdefault((node.name, sub.func.attr), []).append(
                        (rel, sub.lineno))
    return consts, calls


def _where(hits) -> str:
    return ", ".join("%s:%d" % (rel, line) for rel, line in hits)


def _unique_const(consts, name: str):
    hits = consts.get(name) or []
    if len(hits) != 1:
        raise TaskRefused(
            "constant %r is not unique in the snapshot: %d definition(s) (%s)"
            % (name, len(hits), _where(hits) or "none"))
    return hits[0]


def _unique_call(calls, function: str, attr: str):
    hits = calls.get((function, attr)) or []
    if len(hits) != 1:
        raise TaskRefused(
            "call %r is not unique in the snapshot: %d occurrence(s) (%s)"
            % ("%s.%s" % (function, attr), len(hits), _where(hits) or "none"))
    return hits[0]


# ------------------------------------------------------------------ derivation
def _render_call(value: dict) -> str:
    return "%s(%s)" % (value["callee"],
                       ", ".join("%s=%s" % (k, v) for k, v in value["kwargs"].items()))


def _derive(root: str, cp: dict, consts, calls) -> dict:
    """One checkpoint's derived value, its source file and its answer_spec."""
    if cp["kind"] == "NUM":
        rel, _line = _unique_const(consts, cp["symbol"])
        tree, _sha = dv.parse_module(_abs(root, rel))
        value, lineno = dv.constant_value(tree, cp["symbol"])
        return {"kind": "NUM", "file": rel, "line": lineno, "value": int(value),
                "expected": str(int(value)),
                "answer_form": "ANSWER: NUM %d" % int(value),
                "answer_spec": {"kind": "NUM",
                                "derive": {"rule": "constant_value",
                                           "symbol": cp["symbol"],
                                           "file": _source_path(root, rel)}}}
    if cp["kind"] == "CALL":
        rel, _line = _unique_call(calls, cp["function"], cp["attr"])
        tree, _sha = dv.parse_module(_abs(root, rel))
        call = dv.call_inside_function(tree, cp["function"], cp["attr"])
        value, err = g5._parse_call(call["unparsed"])
        if err:
            raise TaskRefused("call %r in %s is not a kwarg-only call (%s): %s"
                              % ("%s.%s" % (cp["function"], cp["attr"]), rel, err,
                                 call["unparsed"]))
        rendered = _render_call(value)
        return {"kind": "CALL", "file": rel, "line": call["lineno"], "value": value,
                "expected": rendered,
                "answer_form": "ANSWER: CALL %s" % rendered,
                "answer_spec": {"kind": "CALL",
                                "derive": {"rule": "call_inside_function",
                                           "function": cp["function"],
                                           "attr": cp["attr"],
                                           "file": _source_path(root, rel)}}}
    raise TaskRefused("unknown checkpoint kind %r" % cp["kind"])


def _source_path(root: str, rel: str) -> str:
    """Repo-relative when the root IS the repo, absolute otherwise."""
    if os.path.abspath(root) == os.path.abspath(dv.ROOT):
        return rel
    return _abs(root, rel)


def _documents(root: str, rels) -> list:
    out = []
    for rel in rels:
        with open(_abs(root, rel), encoding="utf-8") as fh:
            text = fh.read()
        doc_id = "doc-" + os.path.splitext(os.path.basename(rel))[0].replace("_", "-")
        out.append({"doc_id": doc_id, "scope": "granted", "revoked": False,
                    "revoked_at_turn": None,
                    "revisions": [{"revision": 1, "value": text, "live_from_turn": 1}]})
    return out


def _turns(spec: dict, derived) -> list:
    by_turn = {cp["turn"]: cp["question"] for cp in spec["checkpoints"]}
    out = []
    for t in range(1, N_STEPS + 1):
        question = by_turn.get(t) or (
            "Read `%s` and note what it defines." % spec["file"])
        out.append({"turn": t, "kind": "work", "question": question,
                    "tool_outputs": []})
    return out


def _fixture(spec: dict, root: str, consts, calls) -> dict:
    rel = spec["file"]
    if not os.path.isfile(_abs(root, rel)):
        raise TaskRefused("task %s: source %r does not exist under %s"
                          % (spec["task_id"], rel, root))
    derived = [_derive(root, cp, consts, calls) for cp in spec["checkpoints"]]
    if [d["kind"] for d in derived] != ["NUM", "CALL", "NUM", "CALL"]:
        raise TaskRefused("task %s: checkpoint kinds must alternate NUM/CALL"
                          % spec["task_id"])

    documents = _documents(root, [rel, ERRORS_PY])
    sources = [{"id": "resolve.py", "path": _source_path(root, rel)},
               {"id": "errors.py", "path": _source_path(root, ERRORS_PY)}]
    checkpoints = []
    for cp, d in zip(spec["checkpoints"], derived):
        checkpoints.append({
            "id": "cp.%s.t%d" % (spec["task_id"], cp["turn"]),
            "turn": cp["turn"],
            "question": cp["question"],
            "expected": d["expected"],
            "answer_form": d["answer_form"],
            "source": "tool_output:%s@r1" % documents[0]["doc_id"],
            "ground_truth": {"doc": documents[0]["doc_id"], "revision": 1,
                             "value": d["expected"]},
            "match": "exact",
            "answer_spec": d["answer_spec"],
        })

    task = {
        "schema": SCHEMA,
        "task_id": spec["task_id"],
        "generation": GENERATION,
        "N": N_STEPS,
        "turns": _turns(spec, derived),
        "window_tokens": WINDOW_TOKENS,
        "window_tokens_basis": (
            "PinnedArmState folds at FOLD_AT_FRACTION x window_tokens (~3028 tokens); "
            "at 65536 a 16-step episode never folds and is VOID by design §5 falsifier 7"),
        "documents": documents,
        "revision_schedule": [],
        "checkpoints": checkpoints,
        "checkpoint_turns": list(STEPS),
        "fetch_scenarios": [],
        "outcomes_reachable": [],
        "bytes_per_token": BYTES_PER_TOKEN,
        "system_prompt": spec["statement"] + "\n\n" + TOOL_BLOCK + "\n\n" + ANSWER_CONTRACT,
        "items": [{"id": "item-1",
                   "body": "snapshot index: %d documents, %d checkpoints"
                           % (len(documents), len(checkpoints))}],
        "fetch_budget_tokens": 20000,
        "fetch_budget_tokens_basis": "16 steps x 1 fetch x 8000 chars / 4.0914",
        "lease_reopen_turns": [],
        "fixture_version": "%s.v1" % spec["task_id"],
        "sources": sources,
    }
    index = arm_cd.world_index_lines(task)
    task["wall_tokens"] = int((len(task["system_prompt"]) + len("\n".join(index))
                               + sum(len(it["body"]) for it in task["items"]))
                              / BYTES_PER_TOKEN) + 1
    task["wall_tokens_basis"] = "L0 (system_prompt + index + items) / bytes_per_token"
    if os.path.abspath(root) == os.path.abspath(dv.ROOT):
        verify(task, root)
    return task


def build(root: str) -> list:
    consts, calls = scan(root)
    return [_fixture(spec, root, consts, calls) for spec in TASKS]


def serialise(task: dict) -> bytes:
    return (json.dumps(task, indent=1, sort_keys=True) + "\n").encode("utf-8")


def verify(task: dict, root: str = None) -> list:
    """The grader's own derivation must reproduce every documented key.

    `answer_spec.derive.file` is stored repo-relative so the fixture is portable.
    `grade_v5._derive_one` only joins paths that start with `experiments/`, so a
    `src/...` path is opened relative to the process cwd; this resolves it against
    `root` on a copy before handing the fixture to the grader.
    """
    import copy
    probe = copy.deepcopy(task)
    for cp in probe["checkpoints"]:
        derive = cp.get("answer_spec", {}).get("derive") or {}
        path = derive.get("file")
        if path and not os.path.isabs(path):
            derive["file"] = _abs(root or REPO, path)
    truth = g5.derive_truth(probe)
    if len(truth) != len(task["checkpoints"]):
        raise TaskRefused("%s: derive_truth returned %d cells for %d checkpoints"
                          % (task["task_id"], len(truth), len(task["checkpoints"])))
    for cp, cell in zip(task["checkpoints"], truth):
        derived = cell["expected"]
        if isinstance(derived, dict):
            derived = _render_call(derived)
        if str(derived) != str(cp["expected"]):
            raise TaskRefused("%s: %s documents %r but derive_truth says %r"
                              % (task["task_id"], cp["id"], cp["expected"], derived))
    return truth


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=REPO, help="snapshot root (default: the repo)")
    ap.add_argument("--out", default=None,
                    help="output directory (default: %s)" % OUT_DIR)
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare with disk; write nothing")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    out_dir = args.out or os.path.join(REPO, OUT_DIR)
    try:
        tasks = build(root)
    except TaskRefused as exc:
        print("REFUSED: %s" % exc)
        print("nothing written")
        return 1

    if args.check:
        bad = 0
        for task in tasks:
            path = os.path.join(out_dir, "%s.json" % task["task_id"])
            try:
                with open(path, "rb") as fh:
                    on_disk = fh.read()
            except OSError:
                print("%s: MISSING (%s)" % (task["task_id"], path))
                bad += 1
                continue
            if on_disk != serialise(task):
                print("%s: DRIFT (%s)" % (task["task_id"], path))
                bad += 1
                continue
            print("%s: OK (%d checkpoints)" % (task["task_id"], len(task["checkpoints"])))
        return 1 if bad else 0

    os.makedirs(out_dir, exist_ok=True)
    for task in tasks:
        path = os.path.join(out_dir, "%s.json" % task["task_id"])
        with open(path, "wb") as fh:
            fh.write(serialise(task))
        print("%s: wrote %s (%d B)" % (task["task_id"], os.path.relpath(path, REPO),
                                       os.path.getsize(path)))
        for cp in task["checkpoints"]:
            print("  t%-2d %-4s %s" % (cp["turn"], cp["answer_spec"]["kind"], cp["expected"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
