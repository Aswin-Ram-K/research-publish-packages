#!/usr/bin/env python3
"""verdict_scope.py -- a verdict row must say WHICH FILES the command it judged read.

THE DEFECT, IN THE THREE INSTANCES THAT COST THIS BATCH THREE FAILS.

  1. `SEAM-TEST-RED` settled `FAIL exit-1`. Its own seam tests were 5/5. The acceptance
     run went over the whole longrun suite and `tests/test_cap_gate.py:205` reddened
     11:33:19 -> 11:33:43 because ANOTHER card was editing `cell.py`. The row said *what*
     and never *over what*, so a foreign red was read as the claimant's failure.
  2. `GRID-PARAMS-DIGEST-SUPERSEDE`: its `launch_contract_diff --check` passed at 19:27,
     then `grade_v5.py` moved at 14:44 and the same command exits 1. `FAIL exit-1` was
     recorded for work that was correct when it ran.
  3. `tests/test_cap_gate.py:205` itself was a stale assertion. It manufactured three FAILs
     before anyone looked at the assertion instead of the bytes.

A row `{command, exit, sha}` cannot be re-judged later: the commit sha is a statement
about the tree, not about the files the command read, and in this workspace the
load-bearing files (`cell.py`, `tree_freeze.py`, this tool) are UNTRACKED -- so
`sha f17663d1` names a commit that does not contain them.

TWO VERBS, AND WHAT EACH ANSWERS.

  run    verdict_scope.py run [--record R.json] --paths P [P...] -- CMD [ARG...]
         Freeze sha256+size+mtime of the named paths BEFORE, run CMD as an argv list,
         freeze/classify AFTER against the before freeze, and print ONE paste-ready
         `orchestration_verdict` payload line plus a `scope` block:
             {"command", "argv", "exitCode", "sha", "head_is_meaningful",
              "scope": {"paths": [{path, sha_before, sha_after, moved}],
                        "moved": [...], "exit": N, "command": "...",
                        "verdict": "clean" | "tree-moved"}}
         `command` is `shlex.join(argv)` -- the exact argv re-quoted for the row, never a
         shell-program string; `argv` carries the tokens unquoted so a reader never has to
         re-parse them. `exitCode` is the COMMAND's measured exit. `sha` is the repo HEAD,
         and `head_is_meaningful` is false when any NAMED path is untracked (or HEAD is
         unreadable), because HEAD then does not contain the bytes the row judged.
         If `moved` is non-empty the scope verdict is `tree-moved` and the process exits
         **13** -- `exit_codes.EXIT_TREE_MOVED`, "the tree moved", which is NOT a failure.
         Otherwise the process exits with the command's own exit code (0 clean pass, N
         failed). A refused path exits 2 before the command is ever started.

  check  verdict_scope.py check --row <json|FILE>
         Re-freeze the paths the row named NOW and classify the row against present
         bytes: `same` (present bytes are the bytes it judged), `moved_since` (the tree
         moved after the row), `path_missing` (a named path is gone), or `undatable`
         (a row with no `scope` at all -- absence is not a defect: it is a younger row,
         exit 0). Exit 1 ONLY for `path_missing` on a path the row named; `moved_since`
         is informational and exits 0, because a row that names its bytes has already
         said what it judged.

REUSE, NOT A SECOND MACHINERY. `tools/tree_freeze.py` already freezes
`{sha256, size, mtime_ns}`, classifies `same`/`moved`/`deleted`, records `created`, owns
exit 13 and its four verdicts, and samples HEAD read-only (`git --no-optional-locks`, no
index refresh, no network). This tool IMPORTS it: `run` is `tree_freeze.wrap(...)` plus a
`scope` block read back out of the record the wrapper wrote, and `check` uses
`tree_freeze.sha256_of`. Nothing here re-implements a digest, a classifier or a code.
(Finding, recorded rather than forked: `tree_freeze.wrap` returns `moved_detail` only for
the paths that MOVED, so `sha_after` for an unmoved path is taken from its own
`sha_before`; that is exact, not a guess -- a path absent from `moved_detail` was
classified `same` by the same read that produced the digest.)

Offline: stdlib only, no network, no request, no live cell. It RECORDS; it never repairs.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import time

TOOL_VERSION = 1

#: The one exit-code table. Imported through tree_freeze, which imports
#: `longrun/exit_codes.py` -- never re-typed here.
_TOOLS = os.path.dirname(os.path.abspath(__file__))
_LONGRUN = os.path.join(os.path.dirname(_TOOLS), "longrun")
for _p in (_LONGRUN, _TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import tree_freeze  # noqa: E402  (the machinery this tool reuses, not re-implements)

exit_codes = tree_freeze.exit_codes

EXIT_OK = 0
EXIT_CMD_FAILED = 1
EXIT_USAGE = 2
EXIT_TREE_MOVED = tree_freeze.EXIT_TREE_MOVED  # 13, `exit_codes.EXIT_TREE_MOVED`

CLEAN = "clean"
TREE_MOVED = "tree-moved"

SAME = "same"
MOVED_SINCE = "moved_since"
PATH_MISSING = "path_missing"
UNDATABLE = "undatable"

CHECK_STATES = (SAME, MOVED_SINCE, PATH_MISSING, UNDATABLE)


class Refused(Exception):
    """A scope operation that must not proceed. Exit 2, message names the reason."""


# --------------------------------------------------------------------------- tracking


def tracked(path, root=None):
    """Is `path` in the commit at HEAD? Read-only, lock-free, offline.

    `git ls-files --error-unmatch` answers from the index, which `--no-optional-locks`
    keeps from being refreshed (a bare `ls-files` does not write; the flag is passed so
    no future git version can change that). A missing git, a non-repository, or a path
    outside the repository all answer False -- "not in the commit" is the fact the row
    needs, and inventing `True` there would be the very defect this tool exists for.
    """
    root = root or os.getcwd()
    rel = path if not os.path.isabs(path) else os.path.relpath(path, root)
    try:
        done = subprocess.run(
            ["git", "--no-optional-locks", "-C", root, "ls-files", "--error-unmatch", "--", rel],
            capture_output=True, text=True)
    except OSError:
        return False
    return done.returncode == 0


def head_is_meaningful(paths, head, root=None):
    """-> (bool, reason). False when HEAD cannot contain the bytes the row judged."""
    if not head:
        return False, "no readable HEAD: the row's sha cannot name a tree at all"
    untracked = [p for p in paths if not tracked(p, root)]
    if untracked:
        return False, ("untracked at HEAD: %s -- the sha names a commit that does not "
                       "contain these bytes" % ", ".join(untracked))
    return True, "every named path is in the commit at HEAD"


# --------------------------------------------------------------------------- scope


def scope_block(record, before_document):
    """The scope block: per-path before/after digests, what moved, and the exit judged.

    `record` is tree_freeze's wrap record (it carries `moved_detail`); `before_document`
    is the before freeze it wrote. A named path absent from `moved_detail` was classified
    `same` by that run, so its after-digest IS its before-digest.
    """
    detail = {row["path"]: row for row in record.get("moved_detail") or []}
    rows = []
    for entry in before_document.get("files") or []:
        path = entry["path"]
        moved_row = detail.get(path)
        rows.append({
            "path": path,
            "sha_before": entry["sha256"],
            "sha_after": moved_row["after"] if moved_row else entry["sha256"],
            "moved": bool(moved_row),
        })
    # A file CREATED under a declared root is not a named path but it is still a byte the
    # command's run changed; hiding it would let a creation read as `clean`.
    named = {row["path"] for row in rows}
    for path, moved_row in detail.items():
        if path in named or moved_row.get("state") != tree_freeze.CREATED:
            continue
        rows.append({"path": path, "sha_before": None,
                     "sha_after": moved_row["after"], "moved": True})
    moved = [row["path"] for row in rows if row["moved"]]
    return {
        "paths": rows,
        "moved": moved,
        "exit": record.get("exit_code"),
        "command": record.get("command"),
        "verdict": TREE_MOVED if moved else CLEAN,
    }


def payload_for(record, before_document, root, stream=None):
    """-> (payload dict, block). One paste-ready `orchestration_verdict` payload."""
    block = scope_block(record, before_document)
    head, _dirty = tree_freeze._git_head(root) if root else (None, None)
    meaningful, reason = head_is_meaningful([row["path"] for row in block["paths"]
                                             if row["sha_before"] is not None], head, root)
    payload = {
        "command": record.get("command"),
        "argv": list(record.get("argv") or []),
        "exitCode": record.get("exit_code"),
        "sha": head or "unstamped",
        "head_is_meaningful": meaningful,
        "head_is_meaningful_because": reason,
        "scope": block,
    }
    return payload, block


def run(paths, argv, record_path=None, stream=None):
    """freeze -> run -> classify -> scope block. -> (payload, exit code)."""
    stream = stream or sys.stdout
    if not paths:
        raise Refused("refusing a verdict with no bytes: `run` needs at least one --paths "
                      "value (a row that names no bytes is the defect this tool exists for)")
    if not argv:
        raise Refused("`run` needs a command after `--`: nothing to run, nothing to judge")
    record_path = record_path or os.path.join(
        tempfile.gettempdir(), "verdict_scope.%d.%d.json" % (os.getpid(), time.time_ns()))
    try:
        record, code = tree_freeze.wrap(paths, record_path, argv, stream=stream,
                                       verdict_row=False)
    except tree_freeze.Refused as exc:
        raise Refused(str(exc))
    try:
        with open(record["freeze_before"], encoding="utf-8") as fh:
            before_document = json.load(fh)
    except (OSError, ValueError) as exc:
        raise Refused("the wrapper's before freeze is unreadable: %s" % (exc,))
    payload, block = payload_for(record, before_document, before_document.get("root"), stream)
    stream.write(json.dumps(payload, separators=(",", ":"), sort_keys=False) + "\n")
    stream.write("verdict=%s exit=%s moved=%d scope_paths=%d head_is_meaningful=%s record=%s\n"
                 % (block["verdict"], payload["exitCode"], len(block["moved"]),
                    len(block["paths"]), payload["head_is_meaningful"], record_path))
    if block["moved"]:
        stream.write("verdict_scope: UNSTAMPED -- %d path(s) moved while the command ran; "
                     "this row names bytes that no longer exist. Re-run against the "
                     "settled tree; do not re-read this run as a verdict.\n"
                     % len(block["moved"]))
        return payload, EXIT_TREE_MOVED
    if record.get("exit_code") is None:
        return payload, EXIT_USAGE
    return payload, int(record["exit_code"])


# --------------------------------------------------------------------------- check


def classify_row(row, root=None, sha_of=None):
    """Classify a recorded row against PRESENT bytes. -> (verdict, rows, exit code).

    A row with no `scope` (or an empty one) is `undatable`, exit 0: absence is not a
    defect, it is a row written before this tool existed.
    """
    sha_of = sha_of or tree_freeze.sha256_of
    block = row.get("scope") if isinstance(row, dict) else None
    if not isinstance(block, dict) or not isinstance(block.get("paths"), list) or not block["paths"]:
        return UNDATABLE, [], EXIT_OK
    root = root or os.getcwd()
    rows = []
    missing = False
    drifted = False
    for entry in block["paths"]:
        path = entry.get("path")
        expected = entry.get("sha_after")
        target = tree_freeze._resolve(root, path)
        resolved = target
        if not os.path.exists(resolved) or not os.path.isfile(resolved):
            state = PATH_MISSING
            missing = True
        else:
            current = sha_of(resolved)
            state = SAME if current == expected else MOVED_SINCE
            drifted = drifted or state == MOVED_SINCE
        rows.append({"path": path, "expected_sha": expected,
                     "present_sha": None if state == PATH_MISSING else
                     (expected if state == SAME else current),
                     "state": state})
    if missing:
        verdict = PATH_MISSING
    elif drifted:
        verdict = MOVED_SINCE
    else:
        verdict = SAME
    return verdict, rows, EXIT_CMD_FAILED if missing else EXIT_OK


def _load_row(spec):
    """`--row` takes inline JSON or a file holding it."""
    spec = (spec or "").strip()
    if not spec:
        raise Refused("`check` needs --row <json|FILE>")
    if spec.startswith("{"):
        try:
            return json.loads(spec)
        except ValueError as exc:
            raise Refused("--row is not valid JSON: %s" % (exc,))
    try:
        with open(spec, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        raise Refused("cannot read the row %r: %s" % (spec, exc))
    except ValueError as exc:
        raise Refused("the row %r is not valid JSON: %s" % (spec, exc))


def check(row, stream=None):
    """-> (report dict, exit code)."""
    stream = stream or sys.stdout
    verdict, rows, code = classify_row(row)
    report = {"verdict": verdict, "paths": rows,
              "row_verdict": (row.get("scope") or {}).get("verdict")
              if isinstance(row, dict) and isinstance(row.get("scope"), dict) else None}
    stream.write(json.dumps(report, separators=(",", ":"), sort_keys=False) + "\n")
    return report, code


USAGE = """usage:
  verdict_scope.py run [--record R.json] --paths P [P...] -- CMD [ARG...]
  verdict_scope.py check --row <json|FILE>
"""


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if not argv:
            raise Refused(USAGE)
        verb = argv[0]
        rest = argv[1:]
        if verb == "run":
            if "--" not in rest:
                raise Refused("`run` needs `--` before the command\n" + USAGE)
            sep = rest.index("--")
            options, command = rest[:sep], rest[sep + 1:]
            paths, record_path = [], None
            index = 0
            while index < len(options):
                token = options[index]
                if token == "--paths":
                    index += 1
                    while index < len(options) and not options[index].startswith("--"):
                        paths.append(options[index])
                        index += 1
                    continue
                if token == "--path":
                    if index + 1 >= len(options):
                        raise Refused("--path needs a value\n" + USAGE)
                    paths.append(options[index + 1])
                    index += 2
                    continue
                if token == "--record":
                    if index + 1 >= len(options):
                        raise Refused("--record needs a value\n" + USAGE)
                    record_path = options[index + 1]
                    index += 2
                    continue
                raise Refused("unknown `run` option %r\n%s" % (token, USAGE))
            payload, code = run(paths, command, record_path)
            return code
        if verb == "check":
            if len(rest) != 2 or rest[0] != "--row":
                raise Refused("check takes exactly --row <json|FILE>\n" + USAGE)
            _report, code = check(_load_row(rest[1]))
            return code
        raise Refused("unknown verb %r\n%s" % (verb, USAGE))
    except Refused as exc:
        sys.stderr.write("verdict_scope: refused -- %s\n" % (exc,))
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
