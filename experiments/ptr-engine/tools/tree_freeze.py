#!/usr/bin/env python3
"""tree_freeze.py -- a verdict must name the bytes it judged.

THE DEFECT THIS TOOL EXISTS FOR. Concurrent cards editing the same tree is the design;
an audit that records a claim against UNNAMED bytes is the defect. Three audits of this
batch were invalidated by exactly that: `V-GATE-OPERAND` recorded its pin against
`cell.py 6b0ca83a…` while cell.py moved twice during its own check (0136052e, 24627d7b),
so the pin named a file that no longer existed; `VERDICT-DISPUTE` had to pin and bracket a
concurrent rewrite (1313 -> 1334 lines) before its adjudication meant anything; and
`SEAM-TEST-RED` settled `FAIL exit-1` because `tests/test_cap_gate.py:205` was red from
ANOTHER card's in-flight change -- a foreign red became a verdict against the claimant.

So: the tree moving is not a failure, and a failure is not the tree moving. This tool
separates the two facts and refuses to let one stand in for the other.

THE BASELINE IS THE BEFORE FREEZE. `--wrap` takes a freeze BEFORE the command runs and
classifies the tree AFTER it against THAT frozen document -- never against a fresh freeze
of whatever is on disk now. A fresh after-freeze would judge a path the command deleted
against a baseline that never existed (it refuses the missing path and exits 2, writing no
record at all: defect D1 found by `V-TREE-FREEZE`). Classification therefore has three
pre-declared states plus one for files the declaration did not cover:

  same      bytes identical to the before freeze (a bare `touch` is `same (touched)`)
  moved     bytes differ from the before freeze
  deleted   present in the before freeze, absent after  -> `before` sha, `after: null`
  created   absent before, present after, inside a declared root but not in the declared
            path set -> `before: null`, `after` sha, and the output says the declared set
            did not cover it (a creation is REPORTED, never silently folded into `pass`)

A path handed to `freeze` that does not exist is REFUSED (exit 2) BEFORE the wrapped
command is ever started: a freeze never records a phantom, because a phantom digest is
indistinguishable from a path deleted mid-run, and a baseline of nothing cannot be
classified against. Creation is therefore outside the DECLARED-PATH contract and inside
the WITNESSED contract: the wrapper also scans the declared roots (the parent directories
of the declared paths) before and after the run, so a new file there is a `created` row
that forces `moved_during_run` instead of an invisible `pass`.

  freeze(paths, out)  -> writes {"at", "root", "files": [{path, sha256, size, mtime_ns}],
                                 "tree_sha256"}.
  verify(freeze_path) -> re-hashes every recorded file and classifies each
                                 `same` / `moved` / `deleted`, printing
                                 `path, recorded_sha, current_sha, verdict`.
                                 A structurally invalid freeze document is REFUSED
                                 (exit 2), never a KeyError traceback and never 1 (which
                                 is the command-failed code): defect D2.
                                 Exit 0 if every file is `same`; exit 13 (a DISTINCT
                                 code, `exit_codes.EXIT_TREE_MOVED`) if any moved or was
                                 deleted -- "the tree moved" is not "the work failed".
  --wrap OUT [--path P]… [--verdict-row] -- CMD…
                      -> freeze, run CMD, classify against the BEFORE freeze, and write
                                 one JSON record
                                 {command, exit_code, freeze_before, freeze_after, moved,
                                  moved_detail, verdict, …} whose `verdict` is
                                 pass              command exited 0, nothing changed
                                 moved_during_run  command exited 0, paths moved/deleted/
                                                   created
                                 failed            command failed, nothing changed
                                 failed_and_moved  both
                                 `moved_during_run` is UNSTAMPED, never FAIL: the remedy is
                                 a re-run against the settled tree, not a re-reading of
                                 the result. The record -- not the process status -- is the
                                 authoritative classification; the process status
                                 collapses `failed_and_moved` onto `failed` (1) because a
                                 non-zero command is the more urgent fact, while the
                                 record keeps the command's own `exit_code`.
  --verdict-row       with `--wrap`: after the command, print a PASTE-READY
                      `orchestration_verdict` payload on ONE stdout line
                      `{"command", "exitCode", "sha"}` where `command` is the exact command
                      string run, `exitCode` is the COMMAND's real exit (never the
                      wrapper's 13), and `sha` is `git rev-parse HEAD` sampled at wrap
                      start. Then a second human-readable line `verdict=…` with per-path
                      `before -> after` (or `deleted` / `created`). If any declared path is
                      moved, deleted or created the payload line is prefixed
                      `UNSTAMPED: ` and the run exits 13 -- a row must never name bytes
                      that no longer exist as though it had judged them. A dirty tree at
                      HEAD prints a WARNING on stderr: the row names a commit that does
                      not contain these bytes. An empty set of paths is refused (exit 2):
                      a verdict with no bytes is the defect this tool exists for.

WHAT COUNTS AS MOVED: the BYTES. A file whose sha256 changed is `moved`; a file whose
bytes are identical is `same` even if its mtime moved (`mtime_ns` and `size` are recorded
for forensics, and a bare `touch` is reported as `touched: true` without changing the
verdict). `tree_sha256` is the sha256 of the canonical JSON of the sorted (path, sha256)
pairs -- one identity per set of CONTENTS, independent of when it was frozen and of
mtime, so the same bytes frozen twice keep one name and one changed byte changes it.

Exit codes (CLI): 0 ok/same/pass · 1 command failed (or failed_and_moved) · 2 usage, a
refused path, or an invalid freeze document · 13 tree moved
(`exit_codes.EXIT_TREE_MOVED`, declared in the project's one exit-code table rather than
re-typed here).

Stdlib only, offline: no network, no `git`, no request of any kind. It RECORDS; it never
repairs and never rewrites a file it measures.

Usage::

  python3 experiments/ptr-engine/tools/tree_freeze.py freeze --out F.json PATH...
  python3 experiments/ptr-engine/tools/tree_freeze.py verify F.json
  python3 experiments/ptr-engine/tools/tree_freeze.py --wrap REC.json -- CMD [ARGS...]
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import tempfile
import sys
import time
from pathlib import Path

TOOL_VERSION = 3

EXIT_OK = 0
EXIT_CMD_FAILED = 1
EXIT_USAGE = 2


def _exit_codes():
    """The project's single exit-code table. Imported, never re-typed."""
    longrun = Path(__file__).resolve().parents[1] / "longrun"
    if str(longrun) not in sys.path:
        sys.path.insert(0, str(longrun))
    import exit_codes  # noqa: WPS433 (deliberate: the table is the source of truth)
    return exit_codes


exit_codes = _exit_codes()

#: Declared in exit_codes.EXIT_TABLE (code 13). "The tree moved" is not "the work failed",
#: so it must NOT share a number with a command that failed.
EXIT_TREE_MOVED = exit_codes.EXIT_TREE_MOVED

SAME = "same"
MOVED = "moved"
DELETED = "deleted"
CREATED = "created"

STATES = (SAME, MOVED, DELETED, CREATED)

VERDICT_PASS = "pass"
VERDICT_MOVED = "moved_during_run"
VERDICT_FAILED = "failed"
VERDICT_FAILED_AND_MOVED = "failed_and_moved"

VERDICTS = (VERDICT_PASS, VERDICT_MOVED, VERDICT_FAILED, VERDICT_FAILED_AND_MOVED)

#: Directories that are never witnesses of a wrapped command's work: scanning them would
#: report cache churn as a creation and make "the tree moved" true of every run.
_SCAN_SKIP = frozenset({".git", "__pycache__", "node_modules", ".venv", "venv",
                        ".mypy_cache", ".pytest_cache", ".ruff_cache"})


class Refused(Exception):
    """A freeze/verify that must not proceed. Exit 2, message names the path."""


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256_of(path):
    """Digest of the file's BYTES, read once."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tree_sha256(files):
    """One identity for a set of contents: canonical JSON of sorted (path, sha256)."""
    pairs = sorted([f["path"], f["sha256"]] for f in files)
    blob = json.dumps(pairs, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _resolve(root, path):
    return path if os.path.isabs(path) else os.path.join(root, path)


def freeze(paths, out):
    """Digest every path and write the freeze document. Refuses a path that is not there."""
    if not paths:
        raise Refused("refusing to freeze an empty set: a freeze of nothing names nothing")
    root = os.getcwd()
    files = []
    for path in paths:
        target = _resolve(root, path)
        if not os.path.exists(target):
            raise Refused(
                "refusing to freeze a path that does not exist: %r (resolved %r). A freeze "
                "records the bytes it saw; a phantom digest would later be "
                "indistinguishable from a file deleted mid-run." % (path, target))
        if not os.path.isfile(target):
            raise Refused("refusing to freeze a non-regular file: %r is not a file" % (path,))
        st = os.stat(target)
        files.append({
            "path": path,
            "sha256": sha256_of(target),
            "size": st.st_size,
            "mtime_ns": st.st_mtime_ns,
        })
    doc = {"at": _now(), "root": root, "tool_version": TOOL_VERSION,
           "files": files, "tree_sha256": tree_sha256(files)}
    out_dir = os.path.dirname(os.path.abspath(out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=False)
        fh.write("\n")
    return doc


def classify(recorded, root=None):
    """Classify the tree NOW against the freeze document GIVEN (never against a new one).

    -> list of rows carrying, per path:
         state         same | moved | deleted   (the authoritative classifier)
         before        the sha256 the freeze recorded (a real digest, never None: a
                       document that records a phantom is refused, not classified)
         after         the sha256 on disk now, or None when the path is gone
         recorded_sha  / current_sha / verdict   (the pre-existing shape, kept so earlier
                       consumers and this suite's earlier assertions keep reading it)
         touched       mtime/size differ while the bytes did not
    """
    rows = []
    for entry in recorded["files"]:
        path = entry["path"]
        target = _resolve(root or recorded.get("root") or os.getcwd(), path)
        row = {"path": path, "state": DELETED, "before": entry["sha256"], "after": None,
               "recorded_sha": entry["sha256"],
               "current_sha": None, "verdict": DELETED, "touched": False}
        if not os.path.exists(target):
            rows.append(row)
            continue
        if not os.path.isfile(target):
            row["state"] = MOVED
            row["after"] = "<not-a-file>"
            row["verdict"] = MOVED
            row["current_sha"] = "<not-a-file>"
            rows.append(row)
            continue
        st = os.stat(target)
        current = sha256_of(target)
        row["after"] = current
        row["current_sha"] = current
        row["touched"] = bool(st.st_mtime_ns != entry.get("mtime_ns")
                              or st.st_size != entry.get("size"))
        row["state"] = SAME if current == entry["sha256"] else MOVED
        row["verdict"] = row["state"]
        rows.append(row)
    return rows


def classify_verdict(exit_code, changed):
    """The FOUR verdicts, and no fifth. The mapping is ONE function, tested.

    exit 0  + nothing changed -> pass              (CLI 0)
    exit 0  + anything changed -> moved_during_run (CLI 13, UNSTAMPED: not a FAIL)
    nonzero + nothing changed -> failed            (CLI 1)
    nonzero + anything changed -> failed_and_moved (CLI 1; the record keeps the command's
                                                    own exit_code)
    """
    if exit_code == EXIT_OK:
        return VERDICT_MOVED if changed else VERDICT_PASS
    return VERDICT_FAILED_AND_MOVED if changed else VERDICT_FAILED


def _git_head(root):
    """`git rev-parse HEAD` at wrap start, and whether the tree is dirty there.

    Read-only and lock-free (`--no-optional-locks`): no index refresh, no network, no
    request. A missing git or a non-repository is reported honestly as `(None, None)` so the
    row can say `unstamped` rather than inventing a commit.
    """
    def run(*args):
        try:
            return subprocess.run(["git", "--no-optional-locks", "-C", root] + list(args),
                                  capture_output=True, text=True)
        except OSError:
            return None
    head = run("rev-parse", "HEAD")
    if head is None or head.returncode != 0:
        return None, None
    status = run("status", "--porcelain")
    dirty = None if status is None or status.returncode != 0 else bool(status.stdout.strip())
    return head.stdout.strip(), dirty


def verdict_row_view(argv, record, rows, head, dirty):
    """-> (payload_line, human_line). One row, and the sentence that explains it.

    The payload line is prefixed `UNSTAMPED: ` whenever the tree moved under the command:
    a caller that pipes it into `orchestration_verdict` cannot mistake a row naming dead
    bytes for a row that judged them. `sha` is `unstamped` (never a guess) when git cannot
    answer.
    """
    payload = {"command": shlex.join(argv), "exitCode": record.get("exit_code"),
               "sha": head or "unstamped"}
    line = json.dumps(payload, separators=(",", ":"), sort_keys=False)
    if any(r["state"] != SAME for r in rows):
        line = "UNSTAMPED: " + line
    pieces = []
    for row in rows:
        if row["state"] == DELETED:
            pieces.append("%s:deleted (was %s)" % (row["path"], row["before"]))
        elif row["state"] == CREATED:
            pieces.append("%s:created (%s)" % (row["path"], row["after"]))
        else:
            pieces.append("%s:%s->%s" % (row["path"], row["before"], row["after"]))
    human = "verdict=%s %s" % (record.get("verdict"), "; ".join(pieces))
    return line, human


def _scan_roots(paths, root=None):
    """The declared roots: the directories the declared paths live in (deduplicated)."""
    roots = []
    for path in paths:
        target = os.path.abspath(_resolve(root or os.getcwd(), path))
        directory = os.path.dirname(target)
        if directory and directory not in roots:
            roots.append(directory)
    return roots


def scan(root):
    """-> {absolute path: sha256} for every regular file under `root`, recursively."""
    seen = {}
    if not os.path.isdir(root):
        return seen
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in _SCAN_SKIP)
        for name in sorted(filenames):
            target = os.path.join(dirpath, name)
            if not os.path.isfile(target):
                continue
            try:
                seen[target] = sha256_of(target)
            except OSError:
                continue
    return seen


def _witness(paths, root):
    """The files the declared roots contained before the command ran."""
    witness = {}
    for directory in _scan_roots(paths, root):
        witness.update(scan(directory))
    return witness


def _created_rows(paths, root, before, witness):
    """Files inside a declared root that were neither declared nor present before."""
    declared = {os.path.abspath(_resolve(root, f["path"])) for f in before["files"]}
    rows = []
    for directory in _scan_roots(paths, root):
        for target, digest in sorted(scan(directory).items()):
            if target in declared or target in witness:
                continue
            rows.append({"path": target, "state": CREATED, "before": None,
                         "after": digest, "recorded_sha": None, "current_sha": digest,
                         "verdict": CREATED, "touched": False})
    return rows


def _after_document(before, rows):
    """The after-freeze document: the paths that still exist, with the bytes they now have.

    Never produced by `freeze()`: `freeze()` refuses a missing path, and a deletion is a
    fact to record, not a reason to abort the run before any record exists (D1).
    """
    files = []
    absent = []
    for row in rows:
        if row["state"] == DELETED or row["after"] is None:
            absent.append(row["path"])
            continue
        files.append({"path": row["path"], "sha256": row["after"]})
    return {"at": _now(), "root": before.get("root"), "tool_version": TOOL_VERSION,
            "baseline": "classify(before)", "files": files, "absent": absent,
            "tree_sha256": tree_sha256(files)}


def verify(freeze_path, stream=None):
    """Re-hash a freeze and print one line per file. -> exit code (0 same / 13 moved)."""
    stream = stream or sys.stdout
    try:
        with open(freeze_path, encoding="utf-8") as fh:
            recorded = json.load(fh)
    except (OSError, ValueError) as exc:
        raise Refused("cannot read the freeze document %r: %s" % (freeze_path, exc))
    if not isinstance(recorded, dict) or not isinstance(recorded.get("files"), list):
        raise Refused("not a freeze document: %r has no `files` list" % (freeze_path,))
    for index, entry in enumerate(recorded["files"]):
        if (not isinstance(entry, dict) or not isinstance(entry.get("path"), str)
                or not isinstance(entry.get("sha256"), str)):
            raise Refused("not a freeze document: %r entry %d is not {path, sha256}"
                          % (freeze_path, index))
    rows = classify(recorded)
    stream.write("path, recorded_sha, current_sha, verdict\n")
    for row in rows:
        stream.write("%s, %s, %s, %s%s\n" % (
            row["path"], row["recorded_sha"], row["current_sha"] or "<absent>",
            row["state"], " (touched)" if row["touched"] and row["state"] == SAME else ""))
    moved = [r for r in rows if r["state"] != SAME]
    stream.write("tree_sha256 recorded=%s files=%d moved_or_deleted=%d\n"
                 % (recorded.get("tree_sha256"), len(rows), len(moved)))
    return EXIT_TREE_MOVED if moved else EXIT_OK


def wrap(paths, out, argv, stream=None, verdict_row=False):
    """freeze -> run argv -> classify AGAINST THE BEFORE FREEZE -> one JSON record."""
    if not argv:
        raise Refused("--wrap needs a command after `--`: nothing to run, nothing to judge")
    stream = stream or sys.stdout
    before_path = out + ".before.json"
    after_path = out + ".after.json"
    # THE BASELINE. Refuses here (exit 2, no record, command never started) when a
    # declared path is missing -- never a baseline of nothing, never a phantom digest.
    before = freeze(paths, before_path)
    root = before.get("root")
    head, dirty = _git_head(root) if verdict_row else (None, None)
    if verdict_row and head is None:
        sys.stderr.write("WARNING: could not read git HEAD; the row's sha is `unstamped`\n")
    elif verdict_row and dirty:
        sys.stderr.write("WARNING: dirty tree at HEAD %s; the row names a commit that does "
                         "not contain these bytes\n" % head)
    witness = _witness(paths, root)
    started = _now()
    try:
        exit_code = subprocess.call(argv)
    except OSError as exc:
        record = _record(argv, None, before_path, after_path, before, None, [],
                         VERDICT_FAILED, started, str(exc))
        _write_record(out, record)
        stream.write("tree_freeze: could not run %r: %s\n" % (argv[0], exc))
        return record, EXIT_USAGE
    rows = classify(before, root=root)          # <-- the BEFORE freeze is the baseline
    created = _created_rows(paths, root, before, witness)
    rows = rows + created
    after = _after_document(before, rows)
    _write_document(after_path, after)
    detail = [dict(r) for r in rows if r["state"] != SAME]
    verdict = classify_verdict(exit_code, bool(detail))
    record = _record(argv, exit_code, before_path, after_path, before, after, detail,
                     verdict, started, None)
    _write_record(out, record)
    for row in created:
        stream.write("tree_freeze: declared set did not cover new file %s "
                     "(state=created, sha256 %s); report it, do not read it as absent\n"
                     % (row["path"], row["after"]))
    if verdict == VERDICT_MOVED:
        code = EXIT_TREE_MOVED
    elif verdict == VERDICT_PASS:
        code = EXIT_OK
    else:
        code = EXIT_CMD_FAILED
    stream.write("tree_freeze: verdict=%s exit_code=%s changed=%d record=%s\n"
                 % (verdict, exit_code, len(detail), out))
    if verdict in (VERDICT_MOVED, VERDICT_FAILED_AND_MOVED):
        stream.write("tree_freeze: UNSTAMPED -- %d path(s) moved, deleted or created while "
                     "the command ran; this result names bytes that no longer exist. "
                     "Re-run against the settled tree; do not re-read this run as a "
                     "verdict.\n" % len(detail))
    if verdict_row:
        line, human = verdict_row_view(argv, record, rows, head, dirty)
        stream.write(line + "\n")
        stream.write(human + "\n")
    return record, code


def _record(argv, exit_code, before_path, after_path, before, after, detail, verdict,
            started, error):
    return {
        "at": started,
        "tool_version": TOOL_VERSION,
        "command": shlex.join(argv),
        "argv": list(argv),
        "exit_code": exit_code,
        "freeze_before": before_path,
        "freeze_after": after_path,
        "baseline": "before",
        "tree_sha256_before": before["tree_sha256"],
        "tree_sha256_after": (after or {}).get("tree_sha256"),
        "moved": [r["path"] for r in detail],
        "deleted": [r["path"] for r in detail if r["state"] == DELETED],
        "created": [r["path"] for r in detail if r["state"] == CREATED],
        "moved_detail": detail,
        "verdict": verdict,
        "error": error,
    }


def _write_document(path, doc):
    out_dir = os.path.dirname(os.path.abspath(path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")


def _write_record(out, record):
    _write_document(out, record)


USAGE = """usage:
  tree_freeze.py freeze --out F.json PATH [PATH...]
  tree_freeze.py verify F.json
  tree_freeze.py --wrap REC.json [--path P]... [--verdict-row] -- CMD [ARGS...]
"""


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        # `--path P --verdict-row -- CMD` is the ONE-COMMAND form: no OUT to name, so the
        # record goes to a temp file and only the row is the deliverable.
        sep = argv.index("--") if "--" in argv else None
        head_tokens = argv[:sep] if sep is not None else argv
        if head_tokens and head_tokens[0] != "--wrap" and "--verdict-row" in head_tokens:
            argv = ["--wrap", os.path.join(tempfile.gettempdir(),
                                           "tree_freeze_row.%d.%d.json"
                                           % (os.getpid(), time.time_ns()))] + argv
        if argv and argv[0] == "--wrap":
            rest = argv[1:]
            if len(rest) < 2 or "--" not in rest:
                raise Refused("--wrap needs OUT and a command after `--`\n" + USAGE)
            sep = rest.index("--")
            options, positionals, paths = rest[:sep], [], []
            verdict_row = False
            index = 0
            while index < len(options):
                token = options[index]
                if token == "--verdict-row":
                    verdict_row = True
                elif token == "--path":
                    if index + 1 >= len(options):
                        raise Refused("--path needs a value\n" + USAGE)
                    paths.append(options[index + 1])
                    index += 1
                elif token.startswith("--path="):
                    paths.append(token.split("=", 1)[1])
                elif token.startswith("--"):
                    raise Refused("unknown --wrap option %r\n%s" % (token, USAGE))
                else:
                    positionals.append(token)
                index += 1
            if not positionals:
                raise Refused("--wrap needs an OUT record path\n" + USAGE)
            out = positionals[0]
            paths = positionals[1:] + paths
            if not paths:
                raise Refused("refusing a verdict with no bytes: --wrap needs at least one "
                              "path to freeze before `--` (a row that names no bytes is the "
                              "defect this tool exists for)\n" + USAGE)
            _record_out, code = wrap(paths, out, rest[sep + 1:], verdict_row=verdict_row)
            return code
        if not argv:
            raise Refused(USAGE)
        verb = argv[0]
        if verb == "freeze":
            if len(argv) < 4 or argv[1] != "--out":
                raise Refused("freeze needs --out FILE and at least one path\n" + USAGE)
            doc = freeze(argv[3:], argv[2])
            print("frozen %d file(s) at %s -> %s (tree_sha256 %s)"
                  % (len(doc["files"]), doc["at"], argv[2], doc["tree_sha256"]))
            for entry in doc["files"]:
                print("  %-60s %s %d bytes" % (entry["path"], entry["sha256"], entry["size"]))
            return EXIT_OK
        if verb == "verify":
            if len(argv) != 2:
                raise Refused("verify needs exactly one freeze document\n" + USAGE)
            return verify(argv[1])
        raise Refused("unknown verb %r\n%s" % (verb, USAGE))
    except Refused as exc:
        sys.stderr.write("tree_freeze: refused -- %s\n" % (exc,))
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
