"""spawn_record.py — classify every child process a cell makes, instead of counting them.

WHY THIS EXISTS. V-GATE-REPIN measured `not_reproduced` against the literal PASS rule
"`popen_calls == 0` on every refusal": a refusing invocation makes exactly ONE raw
Popen call, because `cell.py` stage 3/7 asks the RUNNER's own `--dry-run` what the cell
would send BEFORE any gate is evaluated. That spawn is a diagnostic self-check, not a
live runner, and no implementation could ever satisfy "zero spawns" while keeping the
self-check. The rule was therefore wrong, not the implementation — but the fix must not
be "stop counting". It is: COUNT BY PURPOSE, and keep the strictness where it belongs.

THE REPLACEMENT RULE (one sentence, mirrored in docs/GATE-CHAIN.md §11):

    A refusing invocation must have zero `runner_launch` spawns; any
    `preflight_self_check` spawn must be declared in the same record with its phase;
    an undeclared spawn (`purpose == other`, or a launch with no gate record) is a
    failure.

So the record keeps a raw count (nothing is hidden) AND a purpose for each spawn, and
the refusal test asserts `runner_launch == 0` plus "every observed spawn appears in the
record". A diagnostic spawn a reader can see and a launch that must never happen are
now different facts in the same document.

Stdlib only. No subprocess of its own: this module is the ledger, not the spawner.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

SCHEMA = "spawn-record/1"

# The closed taxonomy. There is no fourth value: an unclassified spawn must not exist,
# and a caller that has one cannot pass `PURPOSES` to `SpawnRecord.record`.
PURPOSES = ("preflight_self_check", "runner_launch", "other")

# Pipeline stages a spawn may carry as its `phase`. A declared preflight spawn names
# the stage that made it, so "declared" is more than a boolean flag.
PHASES = (
    "1/7 preflight",
    "2/7 harness",
    "3/7 budget",
    "3a/7 G1 ledger gate",
    "3b/7 projection",
    "3c/7 G3 prereg gate",
    "4/7 run",
    "5/7 grade",
    "6/7 analyse",
    "6b/7 consistency",
    "7/7 record",
    "0/7 dry-run",
)

PASS_RULE = (
    "a refusing invocation must have zero runner_launch spawns; any "
    "preflight_self_check spawn must be declared in the same record with its phase; "
    "an undeclared spawn (purpose == other, or a launch with no gate record) is a "
    "failure"
)


# WHAT THE INSTRUMENT CAN SEE (D4). The sitecustomize oracle in
# tests/test_spawn_classification.py is a `subprocess.Popen` SUBCLASS mounted inside the
# child: it observes `subprocess.Popen` -- and therefore `subprocess.run`/`call`/
# `check_output`, which all route through it -- and NOTHING ELSE. An `os.system`,
# `os.execv*`, `os.posix_spawn`, a raw `fork`, or a spawn made on another thread is
# invisible to it. That is not a caveat a reader may assume: it is a DECLARED SCOPE, and
# a record that does not carry this block cannot be validated, because "the record
# declares every spawn" would then be a claim about an instrument nobody named.
#
# The claim is therefore exactly, and only:
#   a refusing invocation must have zero `runner_launch` spawns for `subprocess`-shaped
#   spawns at every exit in {2,3,4,8,12}; spawns outside the declared instrumentation are
#   outside this guarantee and must be measured with a syscall-level oracle
#   (strace/execve) when the claim matters.
INSTRUMENTATION = {
    "primitive": "subprocess.Popen",
    "covers": ["subprocess.Popen", "subprocess.run", "subprocess.call",
               "subprocess.check_output", "subprocess.check_call"],
    "excludes": ["os.system", "os.execv", "os.execve", "os.execl", "os.spawnv",
                 "os.posix_spawn", "os.fork", "threads"],
    "oracle": ("a sitecustomize subclass of subprocess.Popen inside the child, or a "
               "syscall trace passed as --observed-from-syscall"),
}
INSTRUMENTATION_KEYS = ("primitive", "covers", "excludes")

# The exact command that produces a trace `read_syscall_trace` can read (D4). It is
# mirrored in docs/GATE-CHAIN.md 11:
#
#   strace -f -s 4096 -e trace=execve -o /tmp/srb/trace.txt \
#       python3 experiments/ptr-engine/longrun/cell.py <refusal argv>
#   python3 experiments/ptr-engine/longrun/spawn_record.py --validate /tmp/srb/refusal.json \
#       --exit-code 4 --observed-from-syscall /tmp/srb/trace.txt
#
# `-f` follows the children, `-s 4096` keeps long argv untruncated, `-e trace=execve`
# keeps ONLY execve so the count cannot be padded by other syscalls. The FIRST execve in
# the trace is the traced process itself (cell.py) and is excluded; every later execve is
# a spawn the record must name. A JSON trace (`[{"pid": 1, "argv": ["/usr/bin/python3",
# ...]}]`) lists spawns only -- no root entry to exclude.


class SpawnRecordError(ValueError):
    """A spawn was recorded with a purpose the taxonomy does not know."""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SpawnRecord:
    """An append-only ledger of every child process one cell invocation made."""

    def __init__(self):
        self._spawns = []

    def record(self, argv, purpose, phase, pid=None, label="", gate_record=None):
        """Record one spawn. Returns the entry, so a caller can attach it to a record.

        `declared` is not a caller-supplied opinion: it is DERIVED — the purpose must be
        in the taxonomy and the phase must be a known pipeline stage. A spawn with
        `purpose="other"` is recorded (the grade/analyse stages genuinely are "other"
        children) but it is never a valid spawn on a refusing invocation, and
        :func:`validate_refusal` says so.
        """
        if purpose not in PURPOSES:
            raise SpawnRecordError(
                "purpose %r is not one of %s; an unclassified spawn cannot be declared"
                % (purpose, PURPOSES))
        argv = [str(a) for a in (argv or [])]
        phase = str(phase or "").strip()
        declared = bool(phase) and purpose in PURPOSES
        entry = {
            "seq": len(self._spawns),
            "pid": pid,
            # the literal field the unit card asks for: the pid (when the stdlib exposes
            # one) and the argv it ran, as ONE string a reader can grep.
            "pid_argv": ("%s %s" % ("-" if pid is None else pid, " ".join(argv))).strip(),
            "argv": argv,
            "purpose": purpose,
            "phase": phase,
            "gate_record": gate_record,
            "label": label or (os.path.basename(argv[0]) if argv else ""),
            "declared": declared,
            "at": _now(),
        }
        self._spawns.append(entry)
        return entry

    # ------------------------------------------------------------------ inspection
    def spawns(self):
        return [dict(s) for s in self._spawns]

    def counts(self):
        counts = {p: 0 for p in PURPOSES}
        for s in self._spawns:
            counts[s["purpose"]] = counts.get(s["purpose"], 0) + 1
        return counts

    def as_dict(self):
        spawns = self.spawns()
        counts = self.counts()
        undeclared = [s for s in spawns if not s["declared"]]
        doc = {
            "schema": SCHEMA,
            "rule": PASS_RULE,
            "instrumentation": _instrumentation(),
            "spawns": spawns,
            "counts": counts,
            "runner_launch": counts["runner_launch"],
            "preflight_self_check": counts["preflight_self_check"],
            "declared": len(spawns) - len(undeclared),
            "undeclared": len(undeclared),
            "undeclared_detail": [
                {"seq": s["seq"], "purpose": s["purpose"], "phase": s["phase"],
                 "pid_argv": s["pid_argv"]} for s in undeclared],
        }
        # (D5) ONE record shape: the tree binding travels with the spawns, so a writer
        # cannot emit a record that certifies its spawns but not the code that made them.
        doc.update(tree_binding())
        return doc


# Exit codes on which the cell REFUSES. A refusal must launch no runner, so a
# `runner_launch` entry published for one of these contradicts the rule itself.
REFUSAL_EXITS = frozenset({2, 3, 4, 8, 12})


def _as_int(value):
    """An int, or None when the value is not one. Never guesses."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _declaration_block(published):
    """The part of a record that says WHAT it claims to have spawned, or None.

    A declaration block is the per-purpose `counts` mapping together with the
    `rule`/`classification` text it was judged against. A record whose `spawns` list is
    empty and which carries no such block is NOT a claim that "nothing spawned" -- it is
    an empty claim, indistinguishable from a truncated file. `counts` all-zero IS a
    declaration (a zero-spawn refusal is a real result); a missing or empty one is not.
    """
    if not isinstance(published, dict):
        return None
    counts = published.get("counts")
    if not isinstance(counts, dict) or not counts:
        return None
    rule = published.get("rule") or published.get("classification")
    if not isinstance(rule, str) or not rule.strip():
        return None
    return {"counts": counts, "rule": rule}


def _recomputed_counts(spawns):
    """Count the record's own instrumented entries, purpose by purpose."""
    counts = {p: 0 for p in PURPOSES}
    for s in spawns:
        purpose = s.get("purpose")
        counts[purpose] = counts.get(purpose, 0) + 1
    return counts


def _instrumentation():
    """A copy of the declared scope, so a caller cannot mutate the module constant."""
    return json.loads(json.dumps(INSTRUMENTATION))


# ----------------------------------------------------- (D5) THE TREE BINDING
# Gap D5: `validate_refusal` took NO tree identity, so a record certified ANY tree --
# reproduce it by making one gate permissive in a /tmp copy: the same argv moves exit
# 4 -> 12 and the HISTORICAL exit-4 record still validated OK (docs/GATE-CHAIN.md §11).
# The record now carries the sha256 of the two files that DECIDE the rule (`cell.py`,
# `spawn_record.py`), the exact process argv, and the tree's HEAD commit -- and the
# validator holds the record against the files named by `--cell-path` /
# `--spawn-record-path`. One sentence: a record certifies only the tree whose shas it
# carries.
TREE_UNSTAMPED = "unstamped"
BINDING_SHA_KEYS = ("cell_sha256", "spawn_record_sha256")
BINDING_KEYS = BINDING_SHA_KEYS + ("argv", "tree_sha")

_HERE = os.path.dirname(os.path.abspath(__file__))


def sha256_file(path):
    """sha256 of a file's bytes. Raises OSError when it cannot be read -- never guesses."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha(repo_dir=None):
    """The tree's HEAD commit, or the literal ``unstamped`` -- never a fabricated sha.

    Read as FILES, not by running `git`: a recorder that spawned a `git` child would
    appear in its OWN spawn ledger -- and in any syscall oracle -- as an undeclared
    spawn, which is the defect this module exists to catch. `.git/HEAD` is a ref or a
    detached sha; a ref is resolved through `.git/<ref>` or `packed-refs`. Anything
    unreadable, malformed or absent is `unstamped`: the honest label for a tree with no
    commit, never an empty field and never a plausible-looking invented sha.
    """
    path = os.path.abspath(repo_dir or _HERE)
    git = None
    while True:
        candidate = os.path.join(path, ".git")
        if os.path.isdir(candidate) or os.path.isfile(candidate):
            git = candidate
            break
        parent = os.path.dirname(path)
        if parent == path:
            return TREE_UNSTAMPED
        path = parent
    try:
        if os.path.isfile(git):                       # a worktree: "gitdir: <path>"
            with open(git, encoding="utf-8", errors="replace") as fh:
                line = fh.readline().strip()
            if not line.startswith("gitdir:"):
                return TREE_UNSTAMPED
            target = line.split(":", 1)[1].strip()
            git = target if os.path.isabs(target) else os.path.normpath(
                os.path.join(path, target))
        with open(os.path.join(git, "HEAD"), encoding="utf-8", errors="replace") as fh:
            head = fh.readline().strip()
        if re.fullmatch(r"[0-9a-f]{40}", head.lower()):
            return head.lower()
        if not head.startswith("ref:"):
            return TREE_UNSTAMPED
        ref = head.split(":", 1)[1].strip()
        ref_file = os.path.join(git, *ref.split("/"))
        if os.path.isfile(ref_file):
            with open(ref_file, encoding="utf-8", errors="replace") as fh:
                value = fh.readline().strip().lower()
            return value if re.fullmatch(r"[0-9a-f]{40}", value) else TREE_UNSTAMPED
        packed = os.path.join(git, "packed-refs")
        if os.path.isfile(packed):
            with open(packed, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    parts = line.strip().split(" ", 1)
                    if (len(parts) == 2 and parts[1] == ref
                            and re.fullmatch(r"[0-9a-f]{40}", parts[0].lower())):
                        return parts[0].lower()
    except OSError:
        return TREE_UNSTAMPED
    return TREE_UNSTAMPED


def tree_binding(argv=None, cell_path=None, spawn_record_path=None,
                 repo_dir=None):
    """The four keys that bind a record to the tree that produced it (D5).

    `cell_path` and `spawn_record_path` default to the files NEXT TO this module -- the
    on-disk pair `cell.py` runs -- so a caller cannot bind a record to a tree it did not
    run. What cannot be read is `None`, which the validator refuses by name rather than
    skipping.
    """
    cell_path = cell_path or os.path.join(_HERE, "cell.py")
    spawn_record_path = spawn_record_path or os.path.abspath(__file__)
    binding = {
        "cell_sha256": None,
        "spawn_record_sha256": None,
        "argv": [str(a) for a in (sys.argv if argv is None else argv)],
        "tree_sha": tree_sha(repo_dir or _HERE),
    }
    for key, path in (("cell_sha256", cell_path),
                      ("spawn_record_sha256", spawn_record_path)):
        try:
            binding[key] = sha256_file(path)
        except OSError:
            binding[key] = None
    return binding


def binding_failures(published, cell_path=None, spawn_record_path=None):
    """(D5) A record must name the tree it certifies, and the shas must still match.

    Three refusals, each naming its part:
      * no binding keys at all -> the D5 sentence, verbatim;
      * a key present but empty -> "omits", so stripping one field is not a bypass;
      * a recorded sha that disagrees with the file on disk -> BOTH shas and the field.
    """
    if not isinstance(published, dict):
        return []
    named = [k for k in BINDING_SHA_KEYS
             if isinstance(published.get(k), str) and published.get(k).strip()]
    if not named:
        return ["no tree binding (D5): record names neither cell_sha256 nor "
                "spawn_record_sha256 (a record that names no tree certifies any tree; "
                "regenerate it with the cell.py that produced the refusal)"]
    failures = []
    for key in BINDING_KEYS:
        value = published.get(key)
        if value is None or value == "" or value == []:
            failures.append(
                "no tree binding (D5): record omits %r: all of %s must be present, or "
                "the record certifies a tree it cannot name"
                % (key, ", ".join(BINDING_KEYS)))
    argv = published.get("argv")
    if argv is not None and not (isinstance(argv, list) and argv
                                 and all(isinstance(a, str) for a in argv)):
        failures.append("tree binding (D5): `argv` is not a non-empty list of strings "
                        "(%r): the record must name the invocation it describes" % (argv,))
    tree = published.get("tree_sha")
    if isinstance(tree, str) and tree.strip() and tree != TREE_UNSTAMPED:
        if not re.fullmatch(r"[0-9a-f]{40}", tree):
            failures.append(
                "tree binding (D5): `tree_sha` %r is neither a 40-hex commit nor %r: a "
                "fabricated stamp binds nothing" % (tree, TREE_UNSTAMPED))
    paths = {"cell_sha256": cell_path or os.path.join(_HERE, "cell.py"),
             "spawn_record_sha256": spawn_record_path or os.path.abspath(__file__)}
    for key in BINDING_SHA_KEYS:
        recorded = published.get(key)
        if not (isinstance(recorded, str) and recorded.strip()):
            continue
        path = paths[key]
        try:
            actual = sha256_file(path)
        except OSError as exc:
            failures.append(
                "tree binding (D5): record %s=%s names %s, which cannot be read (%s): a "
                "binding that cannot be checked is not a binding"
                % (key, recorded, path, exc))
            continue
        if actual != recorded:
            failures.append(
                "tree binding mismatch (D5): record %s=%s but %s=%s (%s): this record "
                "certifies only the tree whose shas it carries -- regenerate it with the "
                "cell.py under test" % (key, recorded, path, actual, key))
    return failures


def _instrumentation_failures(published):
    """(D4) A record that does not declare its instrumentation is refused by name.

    `primitive`, `covers` and `excludes` are the whole content of the claim: without them
    "every spawn is declared" quantifies over an instrument nobody named, which is exactly
    how an `os.system()` wrapper stayed invisible while the validator answered OK.
    """
    block = published.get("instrumentation")
    if block is None:
        return ["no `instrumentation` declaration: the record does not say WHICH spawn "
                "primitive its oracle observes, so 'every spawn is declared' is a claim "
                "about an unnamed instrument (declare {primitive, covers, excludes}; "
                "spawns outside that scope need a syscall-level oracle)"]
    if not isinstance(block, dict):
        return ["`instrumentation` is not an object (found %s): the declared scope "
                "cannot be read" % type(block).__name__]
    failures = []
    for key in INSTRUMENTATION_KEYS:
        if key not in block:
            failures.append("`instrumentation` omits %r: a scope without %s declares "
                            "nothing" % (key, key))
    primitive = block.get("primitive")
    if not (isinstance(primitive, str) and primitive.strip()):
        failures.append("`instrumentation.primitive` is empty or not a string (%r): the "
                        "oracle's primitive must be named" % (primitive,))
    covers = block.get("covers")
    if not (isinstance(covers, list) and covers
            and all(isinstance(c, str) and c.strip() for c in covers)):
        failures.append("`instrumentation.covers` is not a non-empty list of strings "
                        "(%r): the record must name what the oracle observes" % (covers,))
    excludes = block.get("excludes")
    if not isinstance(excludes, list):
        failures.append("`instrumentation.excludes` is not a list (%r): what the "
                        "instrument CANNOT see must be declared, not assumed empty"
                        % (excludes,))
    return failures


def complete_refusal_document(published):
    """A copy of an on-disk refusal document with the declaration block restored.

    (D6 -- FIXED in `cell.py`.) The refusal writer used to publish a FIXED key list
    (`spawns`, `counts`, `classification`, `observed`, `validation`) and therefore DROPPED
    the top-level `instrumentation` block that :meth:`SpawnRecord.as_dict` emits. It now
    writes the recorder's own dict, so a fresh `cell-<arm>-<stamp>.refusal.json` carries
    `instrumentation` and the D5 binding natively. This helper remains for documents
    written BEFORE the fix: it restores the declaration (a property of the RECORDER, not
    of the run) and deliberately does NOT invent a tree binding -- a missing binding is a
    refusal, not something a helper may paper over.
    """
    doc = json.loads(json.dumps(published))
    if isinstance(doc, dict) and "instrumentation" not in doc:
        doc["instrumentation"] = _instrumentation()
    return doc


# (D3) Duplicate JSON keys. `json.loads` is last-wins, so a `counts` object that says
# `preflight_self_check: 9` and then `preflight_self_check: 1` declares 1 -- a record can
# be rewritten by KEY ORDER. The loader below refuses any duplicated key by name, so key
# order can never rewrite a declaration.
class DuplicateKeyError(SpawnRecordError):
    """A JSON object carried the same key twice."""


class _PairsDict(dict):
    """A decoded object that remembers which of its keys appeared more than once."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.dups = []


def _pair_hook(pairs):
    d = _PairsDict()
    for key, value in pairs:
        if key in d:
            d.dups.append(key)
        d[key] = value
    return d


def _duplicates(node, path=()):
    """Every duplicated key path in a decoded document, as (full key path, object path)."""
    found = []
    if isinstance(node, dict):
        for key in getattr(node, "dups", []) or []:
            found.append((tuple(path) + (str(key),), path))
        for key, value in node.items():
            found.extend(_duplicates(value, path + (str(key),)))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found.extend(_duplicates(value, path + (str(i),)))
    return found


def _object_path(path):
    return "record" + "".join(".%s" % p for p in path)


def strict_loads(text, source="record"):
    """Parse JSON refusing duplicate keys, naming the duplicating path (D3)."""
    try:
        doc = json.loads(text, object_pairs_hook=_pair_hook)
    except ValueError as exc:
        raise DuplicateKeyError("%s: not valid JSON: %s" % (source, exc))
    dups = _duplicates(doc)
    if dups:
        msgs = []
        for key_path, obj_path in dups:
            msgs.append("duplicate key %r at %s"
                        % (".".join(key_path), _object_path(obj_path)))
        raise DuplicateKeyError("; ".join(msgs))
    return doc


def strict_load(path):
    with open(path, encoding="utf-8") as fh:
        return strict_loads(fh.read(), source=path)


# ---------------------------------------------------------- the syscall oracle (D4)
_EXECVE_RE = re.compile(
    r'\bexecve(?:at)?\((?:AT_FDCWD,\s*)?"((?:[^"\\]|\\.)*)",\s*\[(.*?)\]')
_ARGV_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _unescape(value):
    try:
        return json.loads('"%s"' % value)
    except ValueError:
        return value


def parse_strace_execve(text):
    """Every `execve(...)` in strace `-f -e trace=execve` output, in order (D4).

    Returns [{pid, exec, argv}]. The FIRST entry is the traced process itself
    (`cell.py`) and is NOT a spawn; :func:`read_syscall_trace` drops it.
    """
    out = []
    for line in text.splitlines():
        if "resumed>" in line or "execve" not in line:
            continue
        m = _EXECVE_RE.search(line)
        if not m:
            continue
        pid = None
        pid_m = re.match(r"\s*(\d+)\s", line)
        if pid_m:
            pid = int(pid_m.group(1))
        out.append({"pid": pid, "exec": _unescape(m.group(1)),
                    "argv": [_unescape(a) for a in _ARGV_RE.findall(m.group(2))]})
    return out


def read_syscall_trace(path):
    """Read a syscall trace: strace text, or a JSON `[{pid, argv}]` spawn list (D4).

    JSON form: `[{"pid": 123, "argv": ["/usr/bin/python3", "runner.py", "--dry-run"]}]`.
    It lists SPAWNS ONLY -- a strace trace additionally starts with the traced process's
    own execve, which is dropped here so both forms count the same thing.
    """
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    stripped = text.lstrip()
    if stripped.startswith("["):
        try:
            raw = strict_loads(text, source=path)
        except DuplicateKeyError:
            raise
        entries = []
        for i, item in enumerate(raw):
            if isinstance(item, dict):
                argv = item.get("argv") or item.get("args") or []
                if isinstance(argv, str):
                    argv = [argv]
                exec_path = item.get("exec") or (argv[0] if argv else "")
                entries.append({"pid": item.get("pid"), "exec": exec_path,
                                "argv": [str(a) for a in argv]})
            elif isinstance(item, list):
                entries.append({"pid": None,
                                "exec": str(item[0]) if item else "",
                                "argv": [str(a) for a in item]})
            else:
                raise DuplicateKeyError(
                    "%s: trace entry %d is neither an object nor a list" % (path, i))
        return entries
    entries = parse_strace_execve(text)
    if len(entries) > 1:
        entries = entries[1:]  # drop cell.py's own execve: it is not a spawn
    elif entries:
        entries = []  # only the traced process: it made no spawn
    return entries


def _norm_trace_entry(entry):
    """(exec basename, argv tail) -- argv[0] is compared by basename, the rest exactly."""
    exec_path = str(entry.get("exec") or "")
    argv = [str(a) for a in (entry.get("argv") or [])]
    tail = tuple(argv[1:]) if argv else ()
    return (os.path.basename(exec_path),) + tail


def _norm_declared(entry):
    argv = [str(a) for a in (entry.get("argv") or [])]
    if not argv:
        return ("",)
    return (os.path.basename(argv[0]),) + tuple(argv[1:])


def _syscall_failures(spawns, trace, exit_code):
    """(D4) Compare the DECLARED spawns with what the kernel actually exec'd."""
    failures = []
    declared = [_norm_declared(s) for s in spawns]
    traced = [_norm_trace_entry(t) for t in trace]
    if len(traced) != len(declared):
        failures.append(
            "syscall trace shows %d execve(s) (%d spawn(s) after the traced process "
            "itself) but the record declares %d spawn(s) at exit %r: %d spawn(s) outside "
            "the record (an os.system/exec*/posix_spawn/fork/thread spawn is invisible to "
            "the Popen instrumentation and only a syscall oracle can see it)"
            % (len(trace), len(trace), len(spawns), exit_code,
               abs(len(trace) - len(spawns))))
    remaining = list(declared)
    for i, (entry, norm) in enumerate(zip(trace, traced)):
        if norm in remaining:
            remaining.remove(norm)
        else:
            failures.append(
                "syscall trace execve #%d (%s) is not declared by the record: %s"
                % (i + 1, entry.get("pid"), " ".join(str(a) for a in (entry.get("argv")
                                                                      or [entry.get("exec")]))))
    for norm in remaining:
        failures.append(
            "the record declares a spawn the syscall trace does not show (basename + "
            "argv tail): %s" % (" ".join(str(a) for a in norm),))
    return failures


# (D2) COVERAGE. A refusal record set must declare every refusal exit; naming only the
# exits a run happened to reach is a claim about the record's shape, not about the
# refusal set. A SINGLE-invocation record describes exactly one exit and cannot be
# evidence of coverage -- that is why an aggregate record (`per_exit_code` /
# `covered_exits`) is what gets the coverage check.
COVERAGE_KEYS = ("per_exit_code", "covered_exits")


def _declared_coverage(published):
    """(kind, sorted exits the record claims to cover)."""
    per = published.get("per_exit_code")
    if isinstance(per, list):
        exits = []
        for item in per:
            value = _as_int(item.get("exit") if isinstance(item, dict) else item)
            if value is not None:
                exits.append(value)
        return "per_exit_code", sorted(set(exits))
    covered = published.get("covered_exits")
    if isinstance(covered, list):
        exits = [v for v in (_as_int(x) for x in covered) if v is not None]
        return "covered_exits", sorted(set(exits))
    value = _as_int(published.get("exit"))
    if value is not None:
        return "exit", [value]
    return None, []


def validate_refusal(published, exit_code=None, observed=None, trace=None,
                     required_exits=None, cell_path=None, spawn_record_path=None):
    """Judge a PUBLISHED spawn record against the refusal rule, RECOMPUTING it.

    `published` is either :meth:`SpawnRecord.as_dict` output or the `spawns`/`counts`
    block embedded in a refusal/cell record. Works on plain JSON, so a test can mutate
    it -- which is how the induced-undeclared test proves the rule is not vacuous.

    `observed` is the RAW number of real `subprocess.Popen` constructions an independent
    tripwire saw (the `sitecustomize` oracle). When supplied it is the ACCEPTANCE
    CRITERION: the number of spawns the record declares must equal it. When the record
    carries its own `validation.ok`, that claim is never trusted -- if the recomputation
    below disagrees, the self-report is itself a finding.

    `trace` is the STRONGEST oracle: a parsed syscall trace from
    :func:`read_syscall_trace` (strace `-f -s 4096 -e trace=execve`, or a JSON
    `[{pid, argv}]` spawn list). It compares COUNTS and ARGV, and it does not depend on a
    `Popen` subclass, so an `os.system`/`exec*`/`posix_spawn`/fork/thread spawn -- all
    outside `INSTRUMENTATION.covers` -- is caught here by the kernel, not by the record.

    `required_exits` overrides the refusal set the record's coverage is judged against
    (default :data:`REFUSAL_EXITS`).

    (D5) The record must also name the tree that produced it: `cell_sha256`,
    `spawn_record_sha256`, `argv` and `tree_sha` are REQUIRED, and the two shas are
    compared against `cell_path` / `spawn_record_path` (default: the on-disk pair next to
    this module). A record with no binding keys is refused with the D5 sentence; a sha
    that disagrees with the file on disk is refused naming both shas and the field.
    """
    failures = []
    if not isinstance(published, dict):
        return {"ok": False, "exit": exit_code, "observed": observed,
                "failures": ["published record is not a JSON object (found %s): it "
                             "cannot be read as a declaration"
                             % type(published).__name__],
                "spawns": 0, "declared": 0, "recomputed": {}, "phases": [],
                "runner_launch": 0, "preflight_self_check": 0, "rule": PASS_RULE}

    # (D5) the record must name the tree it certifies, and the shas must still match.
    failures.extend(binding_failures(published, cell_path=cell_path,
                                     spawn_record_path=spawn_record_path))

    # (D4) the record must declare WHAT its instrumentation observes.
    failures.extend(_instrumentation_failures(published))

    # (D2) COVERAGE. An aggregate record must name every refusal exit; naming only the
    # exits a run happened to reach is a claim about the record's shape.
    required = REFUSAL_EXITS if required_exits is None else frozenset(
        v for v in (_as_int(x) for x in required_exits) if v is not None)
    cov_kind, cov_exits = _declared_coverage(published)
    missing_coverage = []
    if cov_kind in COVERAGE_KEYS:
        missing_coverage = sorted(set(required) - set(cov_exits))
        if missing_coverage:
            failures.append(
                "missing refusal coverage: %s (the record's `%s` declares exits %s, but "
                "every refusal exit must be declared: the claim is about the refusal set "
                "{%s}, not about the exits one run happened to reach)"
                % (",".join(str(x) for x in missing_coverage), cov_kind,
                   ",".join(str(x) for x in cov_exits) or "none",
                   ",".join(str(x) for x in sorted(required))))

    # (1) a record with no `spawns` key is not evidence of anything.
    if "spawns" not in published:
        failures.append(
            "record has no `spawns` key at all: a published refusal must name every "
            "child it made (an empty or truncated record is not proof)")
        spawns = []
    else:
        raw = published.get("spawns")
        if not isinstance(raw, list):
            failures.append("`spawns` is not a list (found %s): the record cannot name "
                            "what it spawned" % type(raw).__name__)
            spawns = []
        else:
            spawns = [s for s in raw if isinstance(s, dict)]
            if len(spawns) != len(raw):
                failures.append("`spawns` carries %d entr(ies) that are not objects"
                                % (len(raw) - len(spawns)))

    # (2) `spawns: []` with no declaration block is an EMPTY CLAIM, not a zero result.
    declaration = _declaration_block(published)
    if not spawns and declaration is None:
        failures.append(
            "empty claim: `spawns` is empty AND the record carries no declaration block "
            "(`counts` + `rule`/`classification`); an empty declaration is not a "
            "declaration")

    launches, preflight, phases = [], [], []
    for s in spawns:
        purpose = s.get("purpose")
        phase = str(s.get("phase") or "").strip()
        pid_argv = s.get("pid_argv") or " ".join(s.get("argv") or [])
        if purpose not in PURPOSES:
            failures.append("unclassified spawn (purpose=%r): %s" % (purpose, pid_argv))
        if not phase:
            failures.append("spawn declared with no phase (purpose=%r): %s"
                            % (purpose, pid_argv))
        elif phase not in PHASES:
            failures.append("spawn declared with unknown phase %r (purpose=%r): %s"
                            % (phase, purpose, pid_argv))
        else:
            phases.append(phase)
        if purpose == "other":
            failures.append("undeclared spawn (purpose=other) on a refusing invocation: %s"
                            % pid_argv)
        if purpose == "runner_launch":
            launches.append(s)
            # (5) a launch on a refusal is a contradiction, and it names the exit code.
            if exit_code is not None and exit_code in REFUSAL_EXITS:
                failures.append(
                    "runner_launch entry for refusal exit code %r: %s (a refusal must "
                    "launch no runner)" % (exit_code, pid_argv))
            if not s.get("gate_record"):
                failures.append("runner_launch with no gate record: %s" % pid_argv)
        elif purpose == "preflight_self_check":
            preflight.append(s)

    # (3) a declaration block that declares preflight spawns but names no phase names
    # nothing that matters: the stage is what makes a spawn declared.
    decl_counts = (declaration or {}).get("counts") or {}
    decl_preflight = _as_int(decl_counts.get("preflight_self_check", 0))
    if decl_preflight and not phases:
        failures.append(
            "declaration block names no phase for the %d preflight spawn(s) it declares: "
            "a declaration without its stage is not a declaration" % decl_preflight)

    # (4) RECOMPUTE from the record's own instrumented entries; any disagreement with a
    # DECLARED count -- even by 1 -- is a rejection that names the pair and the exit code.
    recomputed = _recomputed_counts(spawns)
    if declaration is not None:
        for purpose in PURPOSES:
            declared = _as_int(decl_counts.get(purpose, 0))
            got = recomputed.get(purpose, 0)
            if declared is None:
                failures.append(
                    "counts[%s]: declared %r vs recomputed %d at exit %r (the declared "
                    "count is not an integer)"
                    % (purpose, decl_counts.get(purpose), got, exit_code))
            elif declared != got:
                failures.append(
                    "counts[%s]: declared %d vs recomputed %d at exit %r (the record's "
                    "declaration disagrees with its own instrumented entries)"
                    % (purpose, declared, got, exit_code))
    for key, purpose in (("runner_launch", "runner_launch"),
                         ("preflight_self_check", "preflight_self_check")):
        if key in published:
            declared = _as_int(published.get(key))
            got = recomputed.get(purpose, 0)
            if declared is None or declared != got:
                failures.append("%s: declared %r vs recomputed %d at exit %r"
                                % (key, published.get(key), got, exit_code))

    # THE ORACLE. The record may not certify itself: when a raw instrumentation count is
    # available, the declared spawn count must equal it exactly.
    if observed is not None:
        if len(spawns) != observed:
            failures.append(
                "declared %d spawn(s) vs recomputed %d from instrumentation at exit %r: "
                "a spawn happened that the record does not name"
                % (len(spawns), observed, exit_code))

    # (D4) THE SYSCALL ORACLE. Strongest check: the kernel's execve list against the
    # record's own spawns -- counts AND argv, independent of any Popen subclass.
    if trace is not None:
        failures.extend(_syscall_failures(spawns, trace, exit_code))

    if launches:
        failures.append("runner_launch=%d on a refusing invocation (must be 0)"
                        % len(launches))

    # (2, second half) never trust a self-reported `validation.ok`.
    self_report = published.get("validation")
    if isinstance(self_report, dict) and self_report.get("ok") is True and failures:
        recomputed_n = observed if observed is not None else len(spawns)
        failures.append(
            "self-reported validation.ok=true contradicted by recomputation at exit %r: "
            "declared %d spawn(s) vs recomputed %d; first disagreement: %s"
            % (exit_code, len(spawns), recomputed_n, failures[0]))

    return {
        "ok": not failures,
        "exit": exit_code,
        "observed": observed,
        "instrumentation": published.get("instrumentation"),
        "coverage": {"kind": cov_kind, "declares": cov_exits,
                     "required": sorted(required), "missing": missing_coverage},
        "syscall": {"traced": len(trace) if trace is not None else None},
        "failures": failures,
        "spawns": len(spawns),
        "declared": len([s for s in spawns if s.get("declared")]),
        "recomputed": recomputed,
        "phases": phases,
        "runner_launch": len(launches),
        "preflight_self_check": len(preflight),
        "rule": PASS_RULE,
    }


def main(argv=None):
    """CLI: `spawn_record.py --validate FILE --exit-code N [--observed N]
    [--observed-from-syscall TRACE] [--required-exits 2,3,4,8,12]`.

    Exit 0 only when the record survives RECOMPUTATION; 1 when it does not (each failure
    printed to stderr, naming the offending part), 2 on a usage/read error. The exit
    status is what makes "the validator must be able to say no" measurable by a test.

    THE SYSCALL ORACLE (D4). The strongest check reads the kernel's own execve list, so it
    does not depend on the sitecustomize `subprocess.Popen` subclass the record's
    instrumentation declares. The exact commands:

        strace -f -s 4096 -e trace=execve -o /tmp/srb/trace.txt \
            python3 experiments/ptr-engine/longrun/cell.py <refusal argv>
        python3 experiments/ptr-engine/longrun/spawn_record.py \
            --validate <refusal.json> --exit-code 4 \
            --observed-from-syscall /tmp/srb/trace.txt

    `-f` follows children, `-s 4096` keeps long argv untruncated, and
    `-e trace=execve` keeps only execve so the count cannot be padded. The trace's FIRST
    execve is the traced process itself (cell.py) and is excluded; a JSON trace
    (`[{"pid": 1, "argv": ["/usr/bin/python3", "runner.py", "--dry-run"]}]`) lists spawns
    only. Counts AND argv are compared, so an `os.system`/`exec*`/`posix_spawn`/fork/
    thread spawn -- outside the declared instrumentation -- is caught here.
    """
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="validate a published spawn record")
    ap.add_argument("--validate", required=True, metavar="FILE")
    ap.add_argument("--exit-code", type=int, default=None)
    ap.add_argument("--observed", type=int, default=None,
                    help="raw subprocess.Popen count from an independent tripwire")
    ap.add_argument("--observed-from-syscall", metavar="TRACE", default=None,
                    help="strace -f -e trace=execve output (or a JSON [{pid, argv}] "
                         "spawn list); compares counts AND argv")
    ap.add_argument("--required-exits", metavar="LIST", default=None,
                    help="refusal exits coverage is judged against "
                         "(default 2,3,4,8,12)")
    ap.add_argument("--cell-path", metavar="FILE", default=None,
                    help="the cell.py the record must name (default: the cell.py next "
                         "to this module); a recorded cell_sha256 that disagrees is a "
                         "tree-binding refusal (D5)")
    ap.add_argument("--spawn-record-path", metavar="FILE", default=None,
                    help="the spawn_record.py the record must name (default: this file)")
    args = ap.parse_args(argv)

    try:
        published = strict_load(args.validate)
    except DuplicateKeyError as exc:
        # (D3) a duplicated key is a REFUSAL (the record lied about its own shape), not a
        # read error: key order must never be able to rewrite a declaration.
        print("spawn_record: FAIL: %s" % exc, file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print("spawn_record: FAIL: cannot read %s: %s" % (args.validate, exc),
              file=sys.stderr)
        return 2

    trace = None
    if args.observed_from_syscall:
        try:
            trace = read_syscall_trace(args.observed_from_syscall)
        except (OSError, ValueError) as exc:
            print("spawn_record: FAIL: cannot read syscall trace %s: %s"
                  % (args.observed_from_syscall, exc), file=sys.stderr)
            return 2

    required = None
    if args.required_exits:
        required = []
        for part in str(args.required_exits).replace(" ", ",").split(","):
            if not part:
                continue
            value = _as_int(part)
            if value is None:
                print("spawn_record: FAIL: --required-exits %r is not an exit code"
                      % (part,), file=sys.stderr)
                return 2
            required.append(value)

    verdict = validate_refusal(published, args.exit_code, observed=args.observed,
                               trace=trace, required_exits=required,
                               cell_path=args.cell_path,
                               spawn_record_path=args.spawn_record_path)
    if verdict["ok"]:
        print("spawn_record: OK exit=%r spawns=%d runner_launch=%d coverage=%s syscall=%r"
              % (verdict["exit"], verdict["spawns"], verdict["runner_launch"],
                 verdict["coverage"]["kind"], verdict["syscall"]["traced"]))
        return 0
    for failure in verdict["failures"]:
        print("spawn_record: FAIL: %s" % failure, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
