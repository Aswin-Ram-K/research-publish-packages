#!/usr/bin/env python3
"""cell.py - ONE COMMAND PER CELL (conductor, not a second implementation).

WHY THIS EXISTS (docs/HARNESS-MAP.md, measured): a question -> one trustworthy
graded cell has cost 40 card rounds and 863 live requests, 31 of those rounds
spending ZERO requests on process. The waste was not the science; it was a chain
of hand-run steps (dry-run -> run -> grade -> re-grade -> analyse, each a round)
plus ask-before-running checks that were done by hand, late, or not at all: a
fixture with no system_prompt cost 386 unreadable requests, a harness edited
mid-cell cost 12 re-run requests, and a p95 was published with no n and no CI.

This module is the CONDUCTOR. It never re-implements a sibling:

    preflight   fixture can be graded at all (exit 2)
    harness     freeze the sha256 of every file that can move a measurement (exit 2)
    budget      the runner's own --dry-run, +10 % headroom, against --budget (exit 3)
    G1 ledger   turns x arms x reps + fetch follow-up allowance must fit the remaining
                quota of the ledger artefact, counted by request_ledger.build_report --
                the ledger's own function, never a second accounting (exit 4)
    G2 project  projected_requests x --projected-turn-wall (p90 via --projected-from,
                default from the calibrated PROJECTION.json) against --max-wall (exit 8);
                printed term by term with its sources, beside the HARD CEILING
                turns x --turn-wall-cap (policy, true by construction, not compared)
    G3 prereg   n = turns x reps must satisfy PARM-1's minimum for the hypothesis the
                cell will claim (H1 needs n >= 60; H2 the per-turn ratio at n >= 1; H3
                needs >= 8 of the 12 checkpoints); a cell declaring no hypothesis is
                refused (exit 12, its own code) -- silence is not a claim you may spend on
    run         run_longrun.py, unchanged, streamed through (exit 4 cap / 5 crash /
                6 runaway / 7 row write, propagated distinctly, never collapsed)
    grade       grade_v5.py on the rows (exit 10)
    analyse     analyze_stats.py; a number or its explicit refusal (exit 11)
    record      one JSON + one markdown in experiments/ptr-engine/measure/ (exit 9/7)

THE GATE CHAIN IS THE ONLY DOOR. G1, G2 and G3 run on every live path, in that order,
after the budget stage (so a budget refusal is never preempted) and before any
request. Their verdicts and the sha256 of every artefact they consulted are written to
the run manifest (cell-<arm>-<stamp>-p<pid>-<serial>.gates.json and the cell record), so
a later reader can prove which limits a live run passed under.

THE EXIT-CODE TABLE LIVES IN exit_codes.py -- THIS FILE HAS NO COPY OF IT. The table is
appended to this docstring at import time from exit_codes.EXIT_TABLE, printed by
`python3 exit_codes.py`, and enforced by tests/test_exit_codes.py, which fails when the
raised set and the declared set disagree in EITHER direction. Before that test existed
the raised set and the prose table disagreed: code 7 (record) was declared and NEVER
raised -- the record stage's OSError surfaced as an undeclared 1 -- and 1 itself
appeared in no table, indistinguishable from a generic crash.

One invocation per cell:

    python3 experiments/ptr-engine/longrun/cell.py \
        --arm transcript-grow --fixture experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json \
        --turns 48 --reps 1 --budget 220 [--endpoint URL] [--expect-harness SHA]

    # CI / zero-request exercise of the whole conductor:
    python3 experiments/ptr-engine/longrun/cell.py --arm X --fixture F --offline rows.jsonl

Offline. Stdlib only. Reads the siblings, writes only its own record.
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timezone

try:
    import exit_codes
except ImportError:
    # Imported by path from a cwd that does not have this directory on sys.path (the gate
    # tests do exactly this): load the sibling file instead of failing the import, so the
    # single-table rule does not make the conductor unimportable for a neighbour suite.
    import importlib.util as _importlib_util
    _spec = _importlib_util.spec_from_file_location(
        "exit_codes", os.path.join(os.path.dirname(os.path.abspath(__file__)), "exit_codes.py"))
    exit_codes = _importlib_util.module_from_spec(_spec)
    _spec.loader.exec_module(exit_codes)
    del _spec, _importlib_util

try:
    import spawn_record
except ImportError:
    import importlib.util as _spawn_util
    _spawn_spec = _spawn_util.spec_from_file_location(
        "spawn_record", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "spawn_record.py"))
    spawn_record = _spawn_util.module_from_spec(_spawn_spec)
    _spawn_spec.loader.exec_module(spawn_record)
    del _spawn_spec, _spawn_util

# The docstring's table is RENDERED from the single source of truth, never typed here.
__doc__ = (__doc__ or "").rstrip() + "\n\n" + exit_codes.render_table() + "\n"

# Every child process THIS invocation makes, classified by purpose. One ledger per
# process: a refusal publishes it (docs/GATE-CHAIN.md §11), so "zero runner_launch"
# is checkable in the refusal's own record instead of by counting Popen calls outside.
SPAWNS = spawn_record.SpawnRecord()

def _observed_spawns():
    """Raw `subprocess.Popen` count from an INDEPENDENT tripwire, or None.

    When a `sitecustomize` oracle is mounted (`SPAWN_ORACLE_LOG` points at its log),
    every real Popen construction inside this process and its python descendants is
    logged there. Counting those lines gives the validator a number the record cannot
    write itself -- that is the difference between recomputing and self-reporting.
    """
    path = os.environ.get("SPAWN_ORACLE_LOG")
    if not path:
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return len([ln for ln in fh if ln.strip()])
    except OSError:
        return None

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)                       # experiments/ptr-engine
ROOT = os.path.dirname(os.path.dirname(ENGINE))      # workspace root
MEASURE = os.path.join(ENGINE, "measure")
HANDOFFS = os.path.join(ROOT, "orchestration", "handoffs")
RUNNER = os.environ.get("CELL_RUNNER_PATH") or os.path.join(HERE, "run_longrun.py")
GRADER = os.environ.get("CELL_GRADER_PATH") or os.path.join(HERE, "grade_v5.py")
ANALYZE = os.environ.get("CELL_ANALYZE_PATH") or os.path.join(HERE, "analyze_stats.py")

# Files whose bytes can change what a cell MEASURES. The list is named here, in
# one place, because a digest over an unnamed list is not a freeze.
HARNESS_FILES = (
    (os.path.join(HERE, "run_longrun.py"), "run_longrun.py"),
    (os.path.join(HERE, "client.py"), "client.py"),
    (os.path.join(HERE, "grade_v5.py"), "grade_v5.py"),
    (os.path.join(HERE, "analyze_stats.py"), "analyze_stats.py"),
    (os.path.join(ENGINE, "tools", "det_verify.py"), "tools/det_verify.py"),
)  # the fixture is added per invocation: it is the 6th measurement input

# The project's request budget for this vector (docs/HARNESS-MAP.md). The runner
# does not report a quota, so the remainder here is BEST-EFFORT: it is computed
# from the row files already on disk and is labelled as such wherever printed.
PROJECT_QUOTA = 12094  # operator-selected 2026-11-07: 9503 headroom after spent 2591; priced core 12094.2 leaves shortfall 2591.2 pending separate authorisation
BUDGET_HEADROOM = 0.10

# --------------------------------------------------------------- gate artefacts
# The three offline cards that built the conditions for spending a request each froze an
# artefact. The gate chain CONSUMES them; it never edits or re-derives them.
LEDGER_ARTEFACT = (os.environ.get("CELL_LEDGER_ARTEFACT")
                   or os.path.join(MEASURE, "REQUEST-LEDGER.json"))
PROJECTION_ARTEFACT = (os.environ.get("CELL_PROJECTION_ARTEFACT")
                       or os.path.join(MEASURE, "PROJECTION.json"))
PREREG_ARTEFACT = (os.environ.get("CELL_PREREG_ARTEFACT")
                   or os.path.join(MEASURE, "PREREG-ARM-RUN.json"))
REQUEST_LEDGER_TOOL = os.path.join(ENGINE, "tools", "request_ledger.py")

# Measured, not guessed: 68 rows of kind "tool-followup" against 801 rows of kind "turn"
# in experiments/ptr-engine/measure/rows-*.jsonl -- the corpus REQUEST-LEDGER bundled.
# The ledger counts a follow-up as a request (docs/REQUEST-LEDGER.md rule 2), so a cell
# that fetches must budget for them or G1 understates what it is about to spend.
FETCH_FOLLOWUP_RATIO = 68.0 / 801.0

GATE_LEDGER = "G1"
GATE_PROJECTION = "G2"
GATE_PREREG = "G3"

# What run_longrun.py's own non-zero exits mean. They are propagated UNMODIFIED (never
# collapsed into one code) and their meanings are DECLARED in exit_codes.EXIT_TABLE --
# there is deliberately no second dict here to drift from it.
_RUNNER_CODES = exit_codes.RUNNER_CODES
# The one declared runner->cell remap (9 -> 14, capgate-unrecorded). Kept in the table
# module so the scan test can see it as a claim, not as an `elif` inside stage_run.
_RUNNER_MAPPED_TO_CELL = exit_codes.RUNNER_MAPPED_TO_CELL


class Abort(Exception):
    """A stage refused. `code` is the distinct exit code of that stage."""

    def __init__(self, code, stage, message, detail=None):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.message = message
        self.detail = detail or {}


# ------------------------------------------------------------------ utilities
def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _now():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _repo_rel(path):
    try:
        return os.path.relpath(os.path.abspath(path), ROOT)
    except ValueError:
        return os.path.abspath(path)


def _run(argv, capture=True, label="", purpose="other", phase=""):
    """Invoke a sibling process. Returns (rc, stdout, stderr).

    The spawn is CLASSIFIED as it is made (`purpose` in spawn_record.PURPOSES, `phase`
    the pipeline stage) instead of merely counted: the count could never distinguish
    the pre-gate dry-run self-check from a live runner launch.
    """
    proc = subprocess.run(argv, stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None, text=True)
    SPAWNS.record(argv=argv, purpose=purpose, phase=phase,
                  pid=getattr(proc, "pid", None),
                  label=label or (os.path.basename(str(argv[0])) if argv else ""))
    out = (proc.stdout or "") if capture else ""
    err = (proc.stderr or "") if capture else ""
    return proc.returncode, out, err


def _count_rows(path):
    if not path or not os.path.exists(path):
        return 0
    n = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


def _load_fixture(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


# ------------------------------------------------------- record/rows-file join
def cell_rows_path(record):
    """The rows file a cell record describes, from EITHER shape it has been written in.

    GRID-GAP-DIAG: ``stage_run`` returns its detail under ``record["run"]`` (so the rows
    file was nested at ``record["run"]["rows_path"]``), while the pinned reader
    ``analyze_stats.load_cell_manifests`` accepts only a TOP-LEVEL ``rows_path``
    (analyze_stats.py:655-687, ``man.get("rows_path")``).  It therefore dropped every
    record cell.py wrote and GRID-RUN-2's report had to build its census by hand.

    This accessor is the single place that knows both shapes.  The reader stays pinned
    and unchanged; the writer emits the flat key (see :func:`with_rows_path`).
    """
    if not isinstance(record, dict):
        return None
    flat = record.get("rows_path")
    if flat:
        return flat
    run = record.get("run")
    if isinstance(run, dict) and run.get("rows_path"):
        return run["rows_path"]
    return None


def with_rows_path(record, rows_path=None):
    """Add the TOP-LEVEL ``rows_path`` join key to a cell record, in place, and return it.

    ``rows_path`` defaults to the nested ``record["run"]["rows_path"]`` -- the value
    ``stage_run`` already resolved.  The nested key is KEPT: existing consumers read it,
    and this is an additive join key, not a schema replacement.  A record that describes
    no rows file gains no key at all (never a null join key).
    """
    if not isinstance(record, dict):
        return record
    rows = rows_path or cell_rows_path(record)
    if rows:
        record["rows_path"] = rows
    return record


def _runner_arms():
    """The runner's own arm list, read from its source (never duplicated here)."""
    try:
        with open(RUNNER, encoding="utf-8") as fh:
            src = fh.read()
        m = re.search(r"^ARMS\s*=\s*\(([^)]*)\)", src, re.M)
        if m:
            return tuple(re.findall(r'["\']([^"\']+)["\']', m.group(1)))
    except OSError:
        pass
    return ()


# --------------------------------------------------------------- 1. preflight
def stage_preflight(args):
    """Refuse (2) any fixture that cannot be graded, naming the exact key."""
    try:
        fixture = _load_fixture(args.fixture)
    except (OSError, json.JSONDecodeError) as exc:
        raise Abort(2, "1/7 preflight", "fixture does not parse: %s: %s"
                    % (_repo_rel(args.fixture), exc))

    sp = fixture.get("system_prompt")
    if not isinstance(sp, str) or not sp.strip():
        raise Abort(2, "1/7 preflight",
                    "fixture lacks a non-empty 'system_prompt' (key 'system_prompt' "
                    "is absent or empty) - a cell without it sends an unreadable "
                    "prompt; refusing to run it")

    arms = _runner_arms()
    if arms and args.arm not in arms:
        raise Abort(2, "1/7 preflight", "arm %r is not one of the runner's arms %s"
                    % (args.arm, list(arms)))

    checkpoints = fixture.get("checkpoints") or []
    if not checkpoints:
        raise Abort(2, "1/7 preflight", "fixture declares no 'checkpoints'")

    for idx, cp in enumerate(checkpoints):
        cid = str(cp.get("id") or "cp.%d" % idx)
        turn = cp.get("turn")
        if not isinstance(turn, int) or turn <= 0:
            raise Abort(2, "1/7 preflight", "checkpoint %s has no integer 'turn'" % cid)
        q = cp.get("question")
        if not isinstance(q, str) or not q.strip():
            raise Abort(2, "1/7 preflight", "checkpoint %s has no non-empty 'question'" % cid)
        # v5 derives truth from the source tree; `expected` is its documented form.
        if cp.get("truth") is None and cp.get("expected") is None:
            raise Abort(2, "1/7 preflight",
                        "checkpoint %s has no 'truth' (and no 'expected' documenting it)"
                        % cid)
        if not cp.get("answer_spec"):
            raise Abort(2, "1/7 preflight", "checkpoint %s has no 'answer_spec' to derive "
                        "its truth from the source tree" % cid)

    # Truth must be DERIVABLE from the pinned source tree by AST, per checkpoint.
    # The derivation is grade_v5.derive_truth (canonical); we call it, never copy it.
    sys.path.insert(0, HERE)
    try:
        import grade_v5  # noqa: E402
    except Exception as exc:  # pragma: no cover - import would be a broken tree
        raise Abort(2, "1/7 preflight", "cannot import grade_v5 for truth derivation: %s" % exc)

    for idx, cp in enumerate(checkpoints):
        cid = str(cp.get("id") or "cp.%d" % idx)
        one = dict(fixture)
        one["checkpoints"] = [cp]
        try:
            derived = grade_v5.derive_truth(one)
        except SystemExit as exc:
            raise Abort(2, "1/7 preflight", "checkpoint %s truth is not derivable: %s"
                        % (cid, exc.code))
        except Exception as exc:
            raise Abort(2, "1/7 preflight", "checkpoint %s truth is not derivable from the "
                        "source tree: %s: %s" % (cid, type(exc).__name__, exc))
        if not derived:
            raise Abort(2, "1/7 preflight", "checkpoint %s derived no truth" % cid)

    # The answer contract the grader enforces must be IN the system prompt:
    # a contract the model never sees is a contract the grader invents.
    contract = fixture.get("answer_contract") or {}
    forms = contract.get("forms") or ["ANSWER: NUM <integer>", "ANSWER: CALL ",
                                      "ANSWER: NONE", "ANSWER: TEXT"]
    missing = [f for f in forms if f not in sp]
    if missing:
        raise Abort(2, "1/7 preflight", "the answer contract is not in the system prompt: "
                    "missing form(s) %s" % missing)

    truth = grade_v5.derive_truth(fixture)
    detail = {"checkpoints": len(truth), "turns": [t["turn"] for t in truth],
              "kinds": [t["kind"] for t in truth],
              "system_prompt_chars": len(sp), "fixture_version": fixture.get("fixture_version")}
    return fixture, truth, detail


# ----------------------------------------------------------- 2. harness freeze
def stage_harness(args, fixture):
    """Freeze every measurement input; refuse (2) on a moved digest."""
    files = {}
    for path, name in HARNESS_FILES:
        if not os.path.exists(path):
            raise Abort(2, "2/7 harness", "harness file is missing: %s" % _repo_rel(path))
        files[name] = _sha256_file(path)
    files["fixture"] = _sha256_file(args.fixture)

    combined = hashlib.sha256()
    for name in sorted(files):
        combined.update(("%s:%s\n" % (name, files[name])).encode("utf-8"))
    digest = combined.hexdigest()

    if args.expect_harness and args.expect_harness != digest:
        raise Abort(2, "2/7 harness",
                    "harness changed mid-cell: --expect-harness %s but the current "
                    "digest is %s (files: %s)"
                    % (args.expect_harness, digest, ", ".join(sorted(files))),
                    {"expected": args.expect_harness, "actual": digest,
                     "files": files})
    return {"harness_sha256": digest, "files": files}


# ------------------------------------------------------------------ 3. budget
def stage_budget(args):
    """Ask the RUNNER's own dry-run what the cell would send; refuse (3) over budget."""
    if args.budget is None:
        raise Abort(3, "3/7 budget", "--budget is required for a live cell (offline mode "
                    "skips stages 3-4)")
    argv = [sys.executable, RUNNER, "--dry-run", "--fixture", args.fixture,
            "--arms", args.arm, "--reps", str(args.reps)]
    # BUDGET-TURN-SCOPE: price the cell the LIVE path will actually run. stage_run caps a
    # partial cell at --turns (same condition, read the same way: n_turns set AND different
    # from the fixture's N); this argv used to omit it, so the runner priced the fixture.
    n_turns = int(args.turns or 0)
    fixture_n = 0
    try:
        fixture_n = int(_load_fixture(args.fixture).get("N") or 0)
    except (OSError, json.JSONDecodeError):
        pass
    truncated = bool(n_turns and fixture_n and n_turns != fixture_n)
    if truncated:
        argv += ["--max-turns", str(n_turns)]
    if args.endpoint:
        argv += ["--base-url", args.endpoint]
    rc, out, err = _run(argv, purpose="preflight_self_check", phase="3/7 budget",
                        label="budget-dry-run")
    m = re.search(r"would_send_total=(\d+)", out or "")
    if rc != 0 or not m:
        raise Abort(3, "3/7 budget", "the runner's --dry-run produced no would_send_total "
                    "(exit %d): %s" % (rc, (err or out or "").strip().splitlines()[-1:]))
    would = int(m.group(1))
    # The runner's --dry-run cannot see the flag it was just handed: run_dry prices
    # range(1, fixture["N"] + 1) (run_longrun.py:2079) and prints int(fixture["N"])
    # (run_longrun.py:2121-2127), so --max-turns moved the LIVE run and left the price at
    # N. Scope the TURN component here, in one line: remove exactly the turns that will
    # not run, priced at the runner's own per-arm N. Digest requests and tool follow-ups
    # stay priced (never under-state what has already been committed). `priced_n` is read
    # from the runner's own line, so a runner that honours --max-turns later makes this a
    # no-op instead of a double discount.
    priced_n = max([int(x) for x in re.findall(r"N=(\d+)", out or "")] or [fixture_n])
    if truncated and priced_n > n_turns:
        would -= (priced_n - n_turns) * _arms_count(args.arm) * int(args.reps or 1)
    required = int(math.ceil(would * (1.0 + BUDGET_HEADROOM)))

    spent, nfiles = 0, 0
    if os.path.isdir(MEASURE):
        for name in sorted(os.listdir(MEASURE)):
            if name.startswith("rows-") and name.endswith(".jsonl"):
                spent += _count_rows(os.path.join(MEASURE, name))
                nfiles += 1
    remaining = PROJECT_QUOTA - spent
    # Budget preflight printout (operator 2026-11-07): spent, cap, headroom, reservation.
    print("PREFLIGHT: spent=%d cap=%d headroom=%d reservation=CCS-2026-11-05 (UNKNOWN)"
          % (spent, PROJECT_QUOTA, remaining), file=sys.stderr)
    # Refuse when headroom unknown or cell cost exceeds headroom, naming the deficit.
    if remaining < 0:
        raise Abort(3, "3/7 budget",
                    "headroom UNKNOWN (spent=%d, cap=%d); refusing"
                    % (spent, PROJECT_QUOTA), detail)
    if would > remaining:
        raise Abort(3, "3/7 budget",
                    "cell cost %d exceeds headroom %d by %d (deficit)"
                    % (would, remaining, would - remaining), detail)
    after = remaining - would

    detail = {"would_send_total": would, "headroom": BUDGET_HEADROOM,
              "required_with_headroom": required, "budget": args.budget,
              "quota_project": PROJECT_QUOTA, "quota_spent_best_effort": spent,
              "quota_rows_files": nfiles, "quota_remaining": remaining,
              "quota_after_this_cell": after, "quota_basis":
              "best-effort: project cap %d minus rows on disk in %s (%d files); the "
              "runner reports no quota" % (PROJECT_QUOTA, _repo_rel(MEASURE), nfiles)}
    if required > args.budget:
        raise Abort(3, "3/7 budget",
                    "would_send_total=%d +%.0f%% headroom = %d exceeds --budget %d "
                    "(project quota remaining %d, best-effort)"
                    % (would, BUDGET_HEADROOM * 100, required, args.budget, remaining),
                    detail)
    return detail


# ------------------------------------------------------------------ 3b. projection
def _p90(values):
    """Linear-interpolated 90th percentile of a non-empty list (offline, no numpy)."""
    vals = sorted(values)
    if not vals:
        return None
    if len(vals) == 1:
        return float(vals[0])
    pos = 0.9 * (len(vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(vals) - 1)
    return float(vals[lo] + (vals[hi] - vals[lo]) * (pos - lo))


def _rows_carry_a_wall(path):
    """True when the file holds at least one row that DECLARES a measured wall.

    Used to tell "you named an empty file" (a bad argument, exit 2) from "you named a
    file whose walls all price at <= 0 s" (a projection that cannot price a turn, exit
    8). The distinction is the difference between a typo and a switched-off gate.
    """
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and ("wall_ms" in row or "latency_s" in row):
                return True
    return False


def turn_walls_from_rows(path):
    """``[(wall_s, completion_tokens)]`` for every usable row of a rows-*.jsonl.

    A row is usable when it carries a measured wall — ``wall_ms`` (the one-command cell
    rows) or ``latency_s`` (the older measure rows) — and no ``error``. A row that was
    aborted by the guard is not evidence of a normal turn and is dropped.
    """
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("error"):
                continue
            wall = None
            if isinstance(row.get("wall_ms"), (int, float)):
                wall = float(row["wall_ms"]) / 1000.0
            elif isinstance(row.get("latency_s"), (int, float)):
                wall = float(row["latency_s"])
            if wall is None or wall <= 0:
                continue
            ct = row.get("completion_tokens")
            out.append((wall, ct if isinstance(ct, (int, float)) else None))
    return out


_THINKING_MODES = ("absent", "off", "auto", "on")
_P90_SELECTOR = "p90"


def thinking_mode(args):
    """The cell's thinking mode, as a key of the artefact's per-mode table.

    A cell that never names ``--thinking`` is the calibration's ``off/absent`` group:
    ``run_longrun.py``'s own default is thinking OFF (HARNESS-GUARDS (e)), so an
    undeclared cell really runs off and is priced off. Any spelling outside
    ``absent|off|auto|on`` is refused (exit 8) — never pooled.
    """
    raw = getattr(args, "thinking", None)
    if raw is None:
        return "absent"
    return str(raw).strip().lower()


def thinking_for_runner(args):
    """The value handed to run_longrun.py: ``absent`` is spelled ``off`` there."""
    mode = thinking_mode(args)
    return "off" if mode == "absent" else mode


def _projection_refusal(stage, computed, limit, flag, consequence, artefact, digest,
                        code=8):
    """Refuse (exit 8) in the UNSAFE direction: a mode we cannot price is not a mode.

    ``code`` is 8 for every numeric-domain violation of G2 and 2 only for a value that is
    not a number at all (argparse's own usage-error convention).
    """
    verdict = {
        "gate": GATE_PROJECTION, "what": "projection", "ok": False,
        "computed": computed, "limit": limit,
        "artefact": _repo_rel(artefact), "artefact_sha256": digest,
        "flag": flag, "consequence": consequence,
        "projection": "projected_requests x projected_turn_wall",
        "short": "%s %s of %s" % (GATE_PROJECTION, computed, limit),
    }
    raise Abort(code, stage, _gate_message(verdict), verdict)


def _mode_wall(defaults, mode, percentile, stage, artefact, digest):
    """The artefact's OWN per-turn figure for this mode, or a refusal (exit 8).

    ``percentile`` is ``p50`` (the expected turn) or ``p90`` (``--projected-from p90``).
    A mode missing from the table refuses: guessing here is how a 60-turn thinking-auto
    cell was admitted at 3,600 s while its own calibration measured 13,092 s.
    """
    key = ("projected_turn_wall_s_by_mode" if percentile == "p50"
           else "projected_turn_wall_s_p90_by_mode")
    table = (defaults or {}).get(key)
    allowed = sorted((table or {}).keys()) or list(_THINKING_MODES)
    if not isinstance(table, dict) or table.get(mode) is None:
        _projection_refusal(
            stage,
            "mode=%r has no calibrated per-turn wall (%s)" % (mode, key),
            "mode in one of {%s}" % ", ".join(allowed),
            "--thinking",
            ("the artefact carries no %s figure for thinking mode %r, so this cell "
             "cannot be priced; add the mode to %s or name a mode the calibration "
             "measured" % (percentile, mode, key)),
            artefact, digest)
    ok, fact = _num_facts(table[mode], "%s[%r]" % (key, mode), "--thinking",
                          lo=0, hi=MAX_TURN_WALL_S, lo_inclusive=False, code=8)
    if not ok:
        _projection_refusal(
            stage, "%s=%r" % (fact["operand"], fact["raw"]), fact["limit"],
            "--thinking",
            ("%s. The artefact's own per-turn figure cannot price a turn, so this cell "
             "has no projection: fix %s or name a mode it measured" % (fact["reason"], key)),
            artefact, digest, code=fact["code"])
    return fact["value"]


def projected_turn_wall(args, defaults=None, artefact=None, digest=None):
    """``(seconds, source, kind, override)`` — the per-turn figure to multiply.

    The figure is the CALIBRATED artefact's own per-mode value:
    ``defaults.projected_turn_wall_s_by_mode[thinking]`` (or the ``_p90_by_mode`` twin
    when ``--projected-from p90`` selects the tail). Precedence, highest first:

    1. ``--projected-from ROWS_JSONL`` — that file's p90 (a measurement, kind ``p90``);
    2. ``--projected-from p90`` — the artefact's measured p90 for THIS mode;
    3. ``--projected-turn-wall SECONDS`` — an operator override, ALWAYS recorded as
       ``projection_override`` (kind ``flag``);
    4. the artefact's per-mode p50.

    ``--turn-wall-cap`` is NOT this number: it stays the live abort threshold and only
    appears as the worst case.
    """
    stage = "3b/7 projection"
    artefact = artefact or PROJECTION_ARTEFACT
    defaults = defaults or {}
    mode = thinking_mode(args)
    allowed = sorted(((defaults.get("projected_turn_wall_s_by_mode") or {})).keys()) \
        or list(_THINKING_MODES)
    if mode not in allowed:
        _projection_refusal(
            stage,
            "thinking mode=%r is not a calibrated mode" % mode,
            "mode in one of {%s}" % ", ".join(allowed),
            "--thinking",
            ("every cell must declare a thinking mode the calibration measured; an "
             "unknown spelling is refused rather than silently priced with a pooled "
             "default, which admitted a thinking-auto cell whose own calibration said "
             "it would overrun"),
            artefact, digest)

    selector = getattr(args, "projected_from", None)
    if selector == _P90_SELECTOR:
        return (_mode_wall(defaults, mode, "p90", stage, artefact, digest),
                _repo_rel(artefact), "p90-default", None)
    if selector:
        if not os.path.exists(selector):
            raise Abort(2, stage,
                        "--projected-from row file does not exist: %s" % selector)
        walls = [w for w, _ in turn_walls_from_rows(selector)]
        # GATE-OVERRIDE-FIX F1: a row file that HOLDS wall rows but cannot price ONE
        # positive turn (every wall was zero or less) has a p90 of <= 0. That is the
        # same defect as a non-positive --projected-turn-wall: it multiplies G2's
        # projection down to nothing and lets a live run past a 1 s ceiling. Refuse it
        # (exit 8) instead of falling back to the artefact's p50. A file with NO wall
        # row at all stays a bad argument (exit 2): there is no measurement to price.
        if not walls:
            if _rows_carry_a_wall(selector):
                _projection_refusal(
                    stage,
                    "--projected-from=%s p90 <= 0 s (no row prices a positive turn)"
                    % selector,
                    "a positive per-turn wall (> 0 s)",
                    "--projected-from",
                    ("every wall row in %s measured zero seconds or less, so the p90 "
                     "cannot price a turn; G2 must not be switched off by the file it "
                     "reads. Point --projected-from at a rows file with measured "
                     "positive walls, or drop the flag to use the calibrated p50"
                     % selector),
                    artefact, digest)
            raise Abort(2, stage,
                        "--projected-from row file has no usable turn wall: %s"
                        % selector)
        p90 = _p90(walls)
        ok, fact = _num_facts(p90, "--projected-from=%s p90" % selector,
                              "--projected-from", lo=0, hi=MAX_TURN_WALL_S,
                              lo_inclusive=False, code=8)
        if not ok:
            _projection_refusal(
                stage, "%s=%r s" % (fact["operand"], fact["raw"]), fact["limit"],
                "--projected-from",
                ("%s. A non-positive, non-finite or absurd per-turn wall cannot price a "
                 "turn and switches G2 off rather than narrowing it. Point "
                 "--projected-from at a rows file with measured positive walls"
                 % fact["reason"]),
                artefact, digest, code=fact["code"])
        return fact["value"], selector, "p90", None

    explicit = getattr(args, "projected_turn_wall", None)
    if explicit is not None:
        # GATE-OVERRIDE-FIX F1 refused zero/negative here; GATE-OPERAND-VALIDATION also
        # refuses non-finite and absurd values (1e308, inf, nan) and a value so small the
        # projection rounds to 0 s, because all of them switch G2 off rather than narrow
        # it. The same five facts, the same exit code, one surface: `_num_facts`.
        ok, fact = _num_facts(explicit, "--projected-turn-wall", "--projected-turn-wall",
                              lo=0, hi=MAX_TURN_WALL_S, lo_inclusive=False, code=8)
        if not ok:
            limit = ("a positive per-turn ceiling (> 0 s) and <= %s s"
                     % _num(MAX_TURN_WALL_S) if fact["code"] == 8 else fact["limit"])
            _projection_refusal(
                stage, "%s=%r" % (fact["operand"], fact["raw"]), limit,
                "--projected-turn-wall",
                ("%s. A per-turn wall that is not finite, is zero or less, or lies above "
                 "the runner's outermost abort cannot price a turn, so G2 must not be "
                 "switched off by an override. Pass a positive number of seconds, or drop "
                 "the flag to use the calibrated figure (source=artefact-mode)"
                 % fact["reason"]),
                artefact, digest, code=fact["code"])
        value = fact["value"]
        calibrated = _mode_wall(defaults, mode, "p50", stage, artefact, digest)
        override = None
        if abs(value - calibrated) > 1e-9:
            override = {
                "value": value, "mode": mode, "calibrated_s": calibrated,
                "direction": "optimistic" if value < calibrated else "conservative",
                "reason_required": True,
                "warning": ("--projected-turn-wall %.1fs overrides the calibrated %.1fs "
                            "for thinking %s (%s): record why in the cell handoff"
                            % (value, calibrated, mode,
                               "BELOW the measured p50" if value < calibrated
                               else "above the measured p50")),
            }
            print("cell: 3b/7 projection OVERRIDE %s" % override["warning"], flush=True)
        return value, "flag", "flag", override

    value = _mode_wall(defaults, mode, "p50", stage, artefact, digest)
    return value, _repo_rel(artefact), "artefact-mode", None


def projection_source_label(kind, source, mode, artefact=None):
    """WHERE the per-turn figure came from, named as the flag or artefact key a reader can audit.

    G2-BOUND-PRICE: the printed price must let a reader check every term against the
    artefact without reading the code, so the label is the exact selector -- a
    ``PROJECTION.json:defaults.<key>['<mode>']`` path, ``--projected-from <file>`` or
    ``--projected-turn-wall`` -- never a bare ``source=<kind>`` token.
    """
    rel = _repo_rel(artefact or PROJECTION_ARTEFACT)
    if kind == "artefact-mode":
        return "%s:defaults.projected_turn_wall_s_by_mode[%r]" % (rel, mode)
    if kind == "p90-default":
        return "%s:defaults.projected_turn_wall_s_p90_by_mode[%r]" % (rel, mode)
    if kind == "p90":
        return "--projected-from %s" % source
    return "--projected-turn-wall"


def projection_price(args, turns, reps, requests, projected, per_turn, turn_cap,
                     kind, source, artefact=None):
    """The projection as an ADDITION of priced terms, beside the bound it cannot exceed.

    G2-BOUND-PRICE prices the projection from the artefact term by term instead of
    printing one pooled number, so a reader can see BOTH of the things the old line
    conflated:

      * the FITTED ESTIMATE -- turns x the calibrated per-turn wall for the declared
        thinking mode, plus whatever the runner's own dry-run priced on top of the turns
        (digests/warm-ups). This is the figure G2 compares against ``--max-wall``, and it
        is UNCHANGED from before this card: 48 turns x 60 s = 2,880 s.
      * the HARD CEILING -- ``turns x --turn-wall-cap``: arithmetic on a policy the
        runner enforces live (it aborts any turn that reaches the cap). No run can
        exceed it, which is what makes it true by construction rather than fitted.

    The fetch follow-up allowance is priced here, not folded into the comparison: G1
    already reserves those requests in the ledger, and G2's per-turn wall is measured
    over turns whose own wall includes the follow-ups they make, so adding them again to
    the compared figure would double-count the turn they ride inside. It is printed with
    its own seconds so the gap GATE-LEDGER recorded as G2-D6 is VISIBLE instead of silent.
    """
    mode = thinking_mode(args)
    turn_requests = turns * reps
    turn_s = int(round(turn_requests * per_turn))
    # Keep the addition EXACT to the second: the extras term is the runner's own priced
    # remainder, never a second rounding of the same product.
    extra_requests = requests - turn_requests
    extra_s = projected - turn_s
    # ONE source of the 68/801 ratio: the function G1 itself uses, which reads
    # FETCH_FOLLOWUP_RATIO (cell.py) unless --fetch-followup-allowance overrides it.
    allowance = fetch_followup_allowance(args, turn_requests)
    allowance_s = int(round(allowance * per_turn))
    all_in = projected + allowance_s
    ceiling = int(round(turns * turn_cap))
    src = projection_source_label(kind, source, mode, artefact)
    line = (
        "fitted estimate %d s = turns %d x %.1f s/turn [source %s] = %d s "
        "+ runner-priced extras %d x %.1f s/turn [source runner --dry-run "
        "would_send_total %d - turns x reps %d] = %d s; "
        "fetch follow-up allowance ceil(%d x 68/801) = %d x %.1f s/turn "
        "[source FETCH_FOLLOWUP_RATIO in cell.py, reserved by G1] = %d s -> "
        "all-in estimate %d s; HARD CEILING %d s = turns %d x --turn-wall-cap %.0f s "
        "[policy bound, not a measurement: the runner aborts any turn that reaches it]"
        % (projected, turns, per_turn, src, turn_s, extra_requests, per_turn,
           requests, turn_requests, extra_s, turn_requests, allowance, per_turn,
           allowance_s, all_in, ceiling, turns, turn_cap))
    return {
        "line": line,
        "thinking_mode": mode,
        "per_turn_wall_s": per_turn,
        "per_turn_source": src,
        "turns": turns, "reps": reps, "turn_requests": turn_requests,
        "fitted_estimate_s": projected,
        "terms": [
            {"term": "turns", "requests": turn_requests, "seconds": turn_s,
             "source": src},
            {"term": "runner-priced extras (digests/warm-ups)",
             "requests": extra_requests, "seconds": extra_s,
             "source": "runner --dry-run would_send_total %d - turns x reps %d"
                       % (requests, turn_requests)},
            {"term": "fetch follow-up allowance", "requests": allowance,
             "seconds": allowance_s,
             "source": "FETCH_FOLLOWUP_RATIO (cell.py) / --fetch-followup-allowance"},
        ],
        "all_in_estimate_s": all_in,
        "hard_ceiling_s": ceiling,
        "hard_ceiling_basis": "turns x --turn-wall-cap (policy, not a measurement)",
    }


def eval_gate_projection(args, budget):
    """Evaluate G2: does the CALIBRATED wall clock fit --max-wall?

    TASK 3 of HARNESS-GUARDS projected `projected_requests x --turn-wall-cap`, i.e. it
    multiplied every request by the live abort threshold. That is a worst case, not a
    forecast: a 48-turn cell projected 8,640 s and was refused, and the 60-turn operator
    comparison projected 10,800 s — so the guard refused the very experiments it exists to
    protect. PROJECTION-CALIBRATION replaces the multiplier with
    ``--projected-turn-wall`` (default 60 s), or the p90 of a prior row file when
    ``--projected-from`` names one; the worst case is still PRINTED next to it, uncensored.

    ``--turn-wall-cap`` keeps its meaning unchanged: :func:`stage_run` still hands it to
    the runner, which still aborts any live turn that reaches it. The projection does not
    weaken that abort; it only stops billing every turn at the abort threshold.

    It runs after :func:`stage_budget` because it consumes that stage's
    ``would_send_total`` and must never preempt a budget refusal (exit 3) with exit 8.
    Nothing live has been sent at this point: the only process run so far was the
    offline `--dry-run`.
    """
    stage = "3b/7 projection"
    _doc, digest = _load_gate_artefact(PROJECTION_ARTEFACT, GATE_PROJECTION, stage,
                                       "projection")
    defaults = _doc.get("defaults") or {}
    # Operands are read RAW: converting with float()/int() before validation is exactly
    # how a hostile value used to become an admission (or an uncaught ValueError).
    turns = _as_int(getattr(args, "turns", None), 0)
    reps = _as_int(getattr(args, "reps", None), 1)
    requests = _as_int((budget or {}).get("would_send_total"), 0)
    if requests <= 0:
        requests = turns * reps
    mode = thinking_mode(args)
    proj_turn, source, kind, override = projected_turn_wall(
        args, defaults, PROJECTION_ARTEFACT, digest)
    ok, facts = validate_g2(getattr(args, "max_wall", None),
                            getattr(args, "turn_wall_cap", None), proj_turn, requests)
    cap_turn = facts.get("turn_wall_cap")
    max_wall = facts.get("max_wall")
    verdict = {
        "gate": GATE_PROJECTION, "what": "projection", "ok": False,
        "turns": turns, "reps": reps, "projected_requests": requests,
        "projected_wall_s": facts.get("projected"),
        "worst_case_wall_s": (int(round(requests * cap_turn)) if cap_turn else 0),
        "max_wall_s": max_wall, "turn_wall_cap_s": cap_turn,
        "projected_turn_wall_s": proj_turn,
        "thinking_mode": mode,
        "projected_turn_wall_source": kind,
        "projected_from_file": source if kind == "p90" else None,
        "projection_override": override,
        "projection": "projected_requests x projected_turn_wall(thinking mode)",
        "artefact": _repo_rel(PROJECTION_ARTEFACT),
        "artefact_sha256": digest,
    }
    if not ok:
        # GATE-CHAIN-FIX D1 made a non-positive ceiling a refusal instead of a bypass;
        # GATE-OPERAND-VALIDATION makes EVERY operand that can switch G2 off a refusal:
        # max_wall, turn_wall_cap, projected_turn_wall and the request count, whether the
        # value arrived as a flag, a p90 or the artefact. There is no unlimited mode.
        _refuse_from_operands(verdict, facts, 8,
                              "--max-wall / --turn-wall-cap / --projected-turn-wall")
        return verdict
    projected = facts["projected"]
    requests = facts["requests"]
    worst = int(round(requests * cap_turn))
    line = ("turns=%d projected_requests=%d projected_wall~=%ds "
            "(cap-per-turn %.0fs -> worst case %ds) cap=%ds "
            "projected-turn-wall=%.1fs source=%s thinking=%s%s%s"
            % (turns, requests, projected, cap_turn, worst, int(max_wall),
               proj_turn, kind, mode,
               (" file=%s" % source) if kind == "p90" else "",
               " OVERRIDE" if override else ""))
    print("cell: 3b/7 projection %s" % line, flush=True)
    # G2-BOUND-PRICE: price the projection from the ARTEFACT term by term, and print the
    # hard ceiling (turns x --turn-wall-cap) beside it. The number G2 COMPARES is the
    # fitted estimate, exactly as before; the bound is printed because it is true by
    # construction, not because it replaces the calibrated per-turn wall.
    price = projection_price(args, turns, reps, requests, projected, proj_turn,
                             cap_turn, kind, source, PROJECTION_ARTEFACT)
    print("cell: 3b/7 projection PRICE %s" % price["line"], flush=True)
    # GATES-MESSAGE-CONSISTENCY: the allow and refuse families are chosen by `ok`, never
    # by which computation ran. The old sentence said "exceeds the allowed 2880s" on a
    # verdict that was ADMITTED at the boundary (V-GATE-CHAIN-2: allow 2,880, refuse
    # 2,881) and called the 48-turn multiplier "48 request(s)". Requests are the
    # runner's would-send count and are named as requests; turns are named as turns.
    admitted = max_wall > 0 and projected <= max_wall
    #: G2's allow family: what the projection is made of, and that it fits.
    g2_allow = (
        "G2 admits: projected wall %d s = %d requests to send (%d turn(s) x %d "
        "rep(s)) x %.1f s calibrated per-turn wall for thinking %s (source %s), "
        "within the %d s allowed by --max-wall by %d s of slack. The worst case "
        "priced at the %.0f s per-turn abort is %d s; that abort still kills any "
        "live turn that reaches it. Beside that fitted estimate stands the HARD "
        "CEILING turns x --turn-wall-cap = %d s: policy arithmetic, not a measurement"
        % (projected, requests, turns, reps, proj_turn, mode, kind, int(max_wall),
           int(max_wall) - projected, cap_turn, worst, price["hard_ceiling_s"]))
    #: G2's refuse family: the same numbers, stated as the refusal they are.
    g2_refuse = (
        "projected wall %d s = %d requests to send (%d turn(s) x %d rep(s)) x "
        "calibrated per-turn wall %.1f s for thinking %s (source %s) exceeds the "
        "allowed %d s by %d s: this cell would spend its whole budget waiting on "
        "runaway turns. The HARD CEILING turns x --turn-wall-cap = %d s is the "
        "policy bound, not a measurement, and it is not what this refusal compares"
        % (projected, requests, turns, reps, proj_turn, mode, kind, int(max_wall),
           projected - int(max_wall), price["hard_ceiling_s"]))
    verdict.update({
        "ok": (max_wall > 0 and projected <= max_wall),
        "projected_requests": requests, "projected_wall_s": projected,
        "worst_case_wall_s": worst,
        "projection_price": price,
        "fitted_estimate_s": price["fitted_estimate_s"],
        "all_in_estimate_s": price["all_in_estimate_s"],
        "hard_ceiling_s": price["hard_ceiling_s"],
        "hard_ceiling_basis": price["hard_ceiling_basis"],
        "line": line,
        "computed": "%d s" % projected,
        "limit": "%d s (--max-wall)" % int(max_wall),
        "flag": ("--projected-turn-wall / --thinking / --max-wall" if override else
                 "--thinking / --projected-from p90 / --max-wall"),
        "short": "%s %s s of %s s" % (GATE_PROJECTION, _num(projected),
                                      _num(int(max_wall))),
    })
    if not (max_wall > 0):
        # GATE-CHAIN-FIX D1: the old verdict was
        # `ok = not (max_wall > 0 and projected > max_wall)`, which ALLOWED a non-positive
        # ceiling -- `--max-wall 0` and `--max-wall -1` switched G2 off. Neither the help
        # text nor docs/GATE-CHAIN.md declares an "unlimited" mode, so a ceiling of zero
        # or less is a REFUSAL, named as such, never a bypass.
        verdict.update({
            "ok": False,
            "computed": "--max-wall=%s s" % _num(max_wall),
            "limit": "a positive ceiling (> 0 s)",
            "short": "%s max-wall=%s s (non-positive)" % (GATE_PROJECTION, _num(max_wall)),
            "consequence": ("--max-wall %s is not a wall: a ceiling of zero or less is "
                            "not 'unlimited' and does not disable the gate. Pass a "
                            "positive number of seconds; there is no unlimited mode"
                            % _num(max_wall)),
        })
    elif verdict["ok"]:
        verdict["consequence"] = g2_allow
    else:
        verdict["consequence"] = g2_refuse
    return verdict


def stage_projection(args, budget):
    """Enforce G2: refuse (8) when the calibrated wall clock exceeds --max-wall."""
    return _enforce(eval_gate_projection(args, budget), "3b/7 projection", 8)


# ----------------------------------------------- gate helpers (ONE refusal format)
def _num(value):
    """Thousands-separated integer, so a reader can compare a number at a glance."""
    try:
        return "{:,}".format(int(value))
    except (TypeError, ValueError, OverflowError):
        return str(value)


# ------------------------------------------- gate operand validation (pure functions)
# GATE-OPERAND-VALIDATION. Every numeric operand a gate READS is validated against the
# REQUIREMENT, not against what the gate's formula happens to print. The bounds are the
# requirement's own words made arithmetic:
#   * a projection cannot be priced by a per-turn wall of zero or less, nor by one larger
#     than the runner's outermost per-turn abort (a figure that is not a turn);
#   * a ceiling longer than the longest cell this project could ever run is not a ceiling;
#   * a ledger cap larger than any possible spend is not a cap, and zero/negative is not
#     an "unlimited" mode;
#   * a cell with no positive request count has no projection and no n.
MAX_WALL_S = 30 * 24 * 3600      # 2,592,000 s -- the longest wallclock a cell may plan
MAX_TURN_WALL_S = 24 * 3600      # 86,400 s -- no single turn is priced past a day
MAX_LEDGER_CAP = 1000000         # requests -- a cap above this cannot bind any spend
MAX_TURNS = 100000               # turns in one cell (the project quota is 4,320)
MAX_REPS = 10000                 # repetitions of one arm in one cell


def _num_facts(value, name, flag, lo=None, hi=None, integral=False,
               lo_inclusive=True, code=0):
    """Validate ONE numeric operand from the requirement. PURE: no I/O, never raises.

    ``code`` is the GATE's own refusal code for a numeric-domain violation (4/8/12); a
    value that is not a number at all carries 2, argparse's own usage-error convention
    and the artefact loader's code. Returns ``(ok, fact)`` so a caller can both decide
    and quote the operand, the limit it broke and the flag that would change the answer.
    """
    fact = {"operand": name, "flag": flag, "raw": value, "value": None,
            "ok": True, "code": 0, "limit": None, "reason": None}
    if value is None:
        fact.update(ok=False, code=2, limit="a number (not absent)",
                    reason="%s was not given" % name)
        return False, fact
    if isinstance(value, bool):
        fact.update(ok=False, code=2, limit="a number (not a bool)",
                    reason="%s=%r is a boolean, not a number" % (name, value))
        return False, fact
    try:
        num = float(value)
    except (TypeError, ValueError, OverflowError):
        fact.update(ok=False, code=2, limit="a number",
                    reason="%s=%r is not a number" % (name, value))
        return False, fact
    fact["value"] = num
    if not math.isfinite(num):
        fact.update(ok=False, code=code, limit="a FINITE number",
                    reason="%s=%s is not finite" % (name, _num(num)))
        return False, fact
    if integral and num != int(num):
        fact.update(ok=False, code=code, limit="an INTEGER count",
                    reason="%s=%s is not an integer count" % (name, _num(num)))
        return False, fact
    if lo is not None and ((num < lo) if lo_inclusive else (num <= lo)):
        fact.update(ok=False, code=code,
                    limit="%s %s %s" % (name, ">=" if lo_inclusive else ">", _num(lo)),
                    reason="%s=%s is %s the required minimum %s"
                           % (name, _num(num), "below" if num < lo else "at", _num(lo)))
        return False, fact
    if hi is not None and num > hi:
        fact.update(ok=False, code=code, limit="%s <= %s" % (name, _num(hi)),
                    reason="%s=%s exceeds the upper bound %s"
                           % (name, _num(num), _num(hi)))
        return False, fact
    return True, fact


def _as_int(value, default=None):
    """Best-effort integer view of an operand (DERIVED arithmetic only, never a gate)."""
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _refuse_from_operands(verdict, facts, default_code, default_flag):
    """Render the FIRST failed operand as the one refusal surface, on an existing verdict.

    The verdict keeps its artefact/digest keys; this adds the computed value, the limit
    it broke, the flag that would change the answer, the gate's own exit code and the
    consequence. A refusal a reader cannot act on is a crash with better grammar.
    """
    bad = (facts.get("refusals") or [None])[0]
    verdict["ok"] = False
    if not bad:
        verdict.update({"computed": "unknown", "limit": "valid operands",
                        "flag": default_flag, "exit": default_code,
                        "consequence": "no operand facts were produced",
                        "short": "%s unvalidated operands" % verdict["gate"]})
        return verdict
    verdict.update({
        "computed": "%s=%r" % (bad["operand"], bad["raw"]),
        "limit": bad["limit"],
        "flag": bad["flag"],
        "exit": bad.get("code") or default_code,
        "consequence": "%s | requirement: %s%s"
                       % (bad["reason"], bad["limit"],
                          (" | a ceiling of zero or less is not 'unlimited' and does not "
                           "disable the gate; pass a positive number of seconds"
                           if bad["operand"] == "--max-wall" else "")),
        "short": "%s refused %s" % (verdict["gate"], bad["operand"]),
        "operand": bad["operand"],
    })
    return verdict


def validate_g1(turns, reps, arms, allowance, cap, reserve, ratio=None):
    """G1's operands, validated from the requirement. PURE: no I/O, no raise.

    Requirement: spend never exceeds the cap; a non-positive or non-integer cap,
    allocation or allowance is refused BEFORE any request; cap=0 never reaches the
    runner. ``allowance=None`` means "derive it from the cell's shape", and the derived
    value is validated too.
    """
    facts = {"gate": GATE_LEDGER, "ok": True, "operands": {}, "refusals": [],
             "turns": None, "reps": None, "arms": None, "turns_total": 0,
             "allowance": None, "would_spend": 0, "cap": None, "reserve": None}
    bad = facts["refusals"]

    def take(name, value, flag, **kw):
        ok, fact = _num_facts(value, name, flag, **kw)
        facts["operands"][name] = fact
        if not ok:
            bad.append(fact)
        return fact

    t = take("--turns", turns, "--turns", lo=1, hi=MAX_TURNS, integral=True, code=4)
    r = take("--reps", reps, "--reps", lo=1, hi=MAX_REPS, integral=True, code=4)
    a = take("--arm (count)", arms, "--arm", lo=1, hi=MAX_REPS, integral=True, code=4)
    c = take("budget.cap", cap, "a larger cap in the ledger", lo=0, hi=MAX_LEDGER_CAP,
             integral=True, lo_inclusive=False, code=4)
    v = take("budget.reserve", reserve, "the ledger's reserve", lo=0, hi=MAX_LEDGER_CAP,
             integral=True, code=4)
    if bad:
        facts["ok"] = False
        return False, facts
    facts.update(turns=int(t["value"]), reps=int(r["value"]), arms=int(a["value"]),
                 cap=int(c["value"]), reserve=int(v["value"]))
    turns_total = facts["turns"] * facts["arms"] * facts["reps"]
    facts["turns_total"] = turns_total
    if turns_total > MAX_LEDGER_CAP:
        facts["ok"] = False
        bad.append({"operand": "--turns x --arm x --reps", "flag": "--turns / --reps",
                    "raw": turns_total, "value": turns_total, "ok": False, "code": 4,
                    "limit": "<= %s requests" % _num(MAX_LEDGER_CAP),
                    "reason": "the cell's own shape (%s requests) exceeds every cap this "
                              "project can hold" % _num(turns_total)})
        return False, facts
    if allowance is None:
        if ratio is None:
            ratio = FETCH_FOLLOWUP_RATIO
        allowance = int(math.ceil(turns_total * ratio))
    al = take("--fetch-followup-allowance", allowance, "--fetch-followup-allowance",
              lo=0, hi=MAX_LEDGER_CAP, integral=True, lo_inclusive=False, code=4)
    if bad:
        facts["ok"] = False
        return False, facts
    facts["allowance"] = int(al["value"])
    facts["would_spend"] = turns_total + facts["allowance"]
    if facts["reserve"] >= facts["cap"]:
        facts["ok"] = False
        bad.append({"operand": "budget.reserve", "flag": "the ledger's reserve",
                    "raw": facts["reserve"], "value": facts["reserve"], "ok": False,
                    "code": 4, "limit": "reserve < cap",
                    "reason": "reserve %s leaves no headroom inside cap %s"
                              % (_num(facts["reserve"]), _num(facts["cap"]))})
        return False, facts
    if facts["would_spend"] < 1:
        facts["ok"] = False
        bad.append({"operand": "would_spend", "flag": "--turns / --reps",
                    "raw": facts["would_spend"], "value": facts["would_spend"],
                    "ok": False, "code": 4, "limit": "a positive request cost",
                    "reason": "the cell would spend %s requests, so there is nothing for "
                              "the cap to gate" % _num(facts["would_spend"])})
        return False, facts
    return True, facts


def validate_g2(max_wall, turn_wall_cap, proj_turn, requests):
    """G2's operands, validated from the requirement. PURE: no I/O, no raise.

    Requirement: a cell is admitted only when the COMPUTED projected wall is finite,
    positive and <= a finite positive --max-wall. Every numeric operand is validated for
    finiteness, sign and bound whether it arrives as a flag, a p90 or an artefact field.
    """
    facts = {"gate": GATE_PROJECTION, "ok": True, "operands": {}, "refusals": [],
             "max_wall": None, "turn_wall_cap": None, "proj_turn": None,
             "requests": None, "projected": 0}
    bad = facts["refusals"]

    def take(name, value, flag, **kw):
        ok, fact = _num_facts(value, name, flag, **kw)
        facts["operands"][name] = fact
        if not ok:
            bad.append(fact)
        return fact

    # Sign is refused by the pinned D1 branch below (it carries the documented wording);
    # this check owns finiteness and the absurd upper bound.
    w = take("--max-wall", max_wall, "--max-wall", hi=MAX_WALL_S, code=8)
    # A per-turn abort below one second cannot be met by any request (TTFT alone is
    # larger), so it is a non-cap, not a tight cap.
    cp = take("--turn-wall-cap", turn_wall_cap, "--turn-wall-cap", lo=1,
              hi=MAX_TURN_WALL_S, code=8)
    pt = take("projected_turn_wall", proj_turn, "--projected-turn-wall / --thinking / "
              "--projected-from", lo=0, hi=MAX_TURN_WALL_S, lo_inclusive=False, code=8)
    rq = take("projected_requests", requests, "--turns / --arm / --reps", lo=1,
              hi=MAX_LEDGER_CAP * 1000, integral=True, code=8)
    if bad:
        facts["ok"] = False
        return False, facts
    facts.update(max_wall=w["value"], turn_wall_cap=cp["value"],
                 proj_turn=pt["value"], requests=int(rq["value"]))
    projected = int(round(facts["requests"] * facts["proj_turn"]))
    facts["projected"] = projected
    if projected < 1:
        facts["ok"] = False
        bad.append({"operand": "projected_wall_s", "flag": "--projected-turn-wall / "
                    "--turns", "raw": projected, "value": projected, "ok": False,
                    "code": 8, "limit": "a computed projection >= 1 s",
                    "reason": "%s request(s) x %s s per turn rounds to %s s: a projection "
                              "that prices nothing is not a projection"
                              % (_num(facts["requests"]), _num(facts["proj_turn"]),
                                 _num(projected))})
        return False, facts
    return True, facts


def validate_g3(hypothesis, turns, reps, checkpoints, known, min_n_h1=None,
                h1_basis=None, checkpoint_min=8, smoke=False):
    """G3's operands and thresholds, derived from the requirement. PURE: no I/O.

    Requirement: a live run declares a hypothesis or smoke; silence is a refusal (12);
    turns/reps are positive integers. ``known`` is the prereg artefact's hypotheses map.
    """
    facts = {"gate": GATE_PREREG, "ok": True, "branch": None, "hypothesis": hypothesis,
             "operands": {}, "refusals": [], "n": 0, "min_n": None, "thresholds": {}}
    bad = facts["refusals"]
    if isinstance(checkpoints, bool) or not isinstance(checkpoints, int) or checkpoints < 0:
        facts["ok"] = False
        facts["branch"] = "operand"
        facts["refusals"].append({
            "operand": "fixture checkpoints", "flag": "--fixture", "raw": checkpoints,
            "value": checkpoints, "code": 12, "ok": False, "reason":
            "%r is not a checkpoint count: H3 is adjudicated over a whole number of "
            "fixture checkpoints" % (checkpoints,)})
        facts["operands"]["checkpoints"] = facts["refusals"][-1]
        return False, facts

    def take(name, value, flag, **kw):
        ok, fact = _num_facts(value, name, flag, **kw)
        facts["operands"][name] = fact
        if not ok:
            bad.append(fact)
        return fact

    t = take("--turns", turns, "--turns", lo=1, hi=MAX_TURNS, integral=True, code=12)
    r = take("--reps", reps, "--reps", lo=1, hi=MAX_REPS, integral=True, code=12)
    if bad:
        facts.update(ok=False, branch="operand")
        return False, facts
    facts["n"] = int(t["value"]) * int(r["value"])
    if smoke:
        # WIRE-CLAIM-MODE: a DECLARED smoke/plumbing cell makes no PARM-1 claim, so no
        # admissibility threshold applies to it -- but its operands were still validated
        # above (turns/reps positive integers), so smoke cannot smuggle a nonsense
        # projection past G3 either. The claim=no-claim DECISION is claim_mode's.
        facts.update(branch="smoke", min_n=0, ok=True, thresholds={
            "min_n": 0,
            "basis": ("a cell that declares claim=none makes no PARM-1 claim, so no n "
                      "threshold applies; claim_mode.resolve_claim is the only resolver "
                      "of that decision")})
        return True, facts
    name = hypothesis
    if not name or str(name).strip().upper() in ("NONE", "NULL", "-"):
        facts.update(ok=False, branch="silence")
        return False, facts
    if name not in known:
        facts.update(ok=False, branch="unknown")
        return False, facts
    entry = known.get(name) or {}
    if name == "H1":
        mn = int(min_n_h1 if min_n_h1 is not None else 60)
        facts.update(branch="H1", min_n=mn, thresholds={
            "estimator": entry.get("estimator"),
            "admissibility": entry.get("admissibility"),
            "ranking_rule": entry.get("ranking_rule"),
            "min_n": mn, "q": 0.95,
            "basis": h1_basis or "PARM-1 H1 admissibility (n >= 60 at q=0.95)"})
    elif name == "H3":
        cps = checkpoints if isinstance(checkpoints, int) and checkpoints >= 0 else 0
        facts.update(branch="H3", min_n=checkpoint_min, thresholds={
            "claim": entry.get("claim"),
            "unadjudicable_clause": entry.get("unadjudicable_clause"),
            "margin_checkpoints": entry.get("margin_checkpoints"),
            "margin_denominator": entry.get("margin_denominator"),
            "min_decidable": checkpoint_min, "checkpoints_in_fixture": cps})
        facts["ok"] = cps >= checkpoint_min
        return facts["ok"], facts
    else:                                        # H2, and any other declarable claim
        facts.update(branch=name, min_n=1, thresholds={
            "claim": entry.get("claim"),
            "unit_of_account": entry.get("unit_of_account"),
            "materiality_margin": entry.get("materiality_margin"),
            "min_n": 1,
            "basis": "a per-turn ratio needs at least one completed turn per arm"})
    facts["ok"] = facts["n"] >= facts["min_n"]
    return facts["ok"], facts


def _load_gate_artefact(path, gate, stage, label):
    """Read one gate artefact and freeze its digest (the thing an audit needs)."""
    if not os.path.exists(path):
        raise Abort(2, stage,
                    "%s %s: artefact is missing (%s) — a gate that cannot read its "
                    "limit must refuse, never allow" % (gate, label, _repo_rel(path)))
    try:
        doc = _load_fixture(path)
    except (OSError, ValueError) as exc:
        raise Abort(2, stage, "%s %s: artefact does not parse (%s): %s"
                    % (gate, label, _repo_rel(path), exc))
    if not isinstance(doc, dict):
        raise Abort(2, stage, "%s %s: artefact is not a JSON object (%s)"
                    % (gate, label, _repo_rel(path)))
    return doc, _sha256_file(path)


def _gate_message(verdict):
    """THE refusal format: gate id, computed value, limit, artefact, action.

    A refusal a reader cannot act on is a crash with better grammar, so every gate
    refusal carries the same five facts and then the one flag that changes the answer.
    """
    return ("%s %s REFUSED: computed %s | limit %s | artefact %s (sha256 %s) | "
            "to change this decision pass %s | %s"
            % (verdict["gate"], verdict["what"], verdict["computed"], verdict["limit"],
               verdict["artefact"], verdict["artefact_sha256"], verdict["flag"],
               verdict.get("consequence", "")))


def _enforce(verdict, stage, code):
    """Raise the gate's pinned exit code when its verdict is a refusal.

    GATE-OPERAND-VALIDATION: a refusal may carry its OWN ``exit`` -- 2 for a value that
    is not a number at all, otherwise the gate's pinned code -- and the caller's ``code``
    is only the default. No gate can silently renumber another gate's refusal, and no
    gate can turn a usage error into a measurement refusal.
    """
    if not verdict.get("ok"):
        raise Abort(verdict.get("exit", code), stage, _gate_message(verdict), verdict)
    return verdict


def _arms_count(spec):
    parts = [p.strip() for p in str(spec or "").split(",") if p.strip()]
    return len(parts) or 1


def fetch_followup_allowance(args, turns_total):
    """Requests to reserve for the tool loop's fetch follow-ups (G1 must include them)."""
    fixed = getattr(args, "fetch_followup_allowance", None)
    if fixed is not None:
        return max(0, int(fixed))
    return int(math.ceil(max(0, turns_total) * FETCH_FOLLOWUP_RATIO))


def _ledger_module():
    """The ledger's own module — its accounting is used, never re-implemented."""
    tools = os.path.join(ENGINE, "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import request_ledger  # noqa: E402
    return request_ledger


def _ledger_row_paths(doc):
    out = []
    for entry in doc.get("files") or []:
        name = (entry or {}).get("file")
        if not name:
            continue
        if os.path.isabs(name):
            out.append(name)
        elif os.path.exists(os.path.join(ENGINE, name)):
            out.append(os.path.join(ENGINE, name))
        else:
            out.append(os.path.join(MEASURE, name))
    return out


def eval_gate_ledger(args):
    """G1 — the projected request cost must fit the ledger's remaining quota.

    The cost is the cell's own shape (turns x arms x reps) PLUS the fetch follow-up
    allowance, because the ledger counts a follow-up as a billed request. The decision
    is taken by ``request_ledger.build_report`` over the very row files the artefact
    lists, so the gate cannot drift from the tool that owns the counting; a refusal
    reuses the ledger's own exit code (4 = EXIT_OVER).
    """
    stage = "3a/7 G1 ledger gate"
    doc, digest = _load_gate_artefact(LEDGER_ARTEFACT, GATE_LEDGER, stage, "ledger-cap")
    budget = doc.get("budget") or {}
    if "cap" not in budget:
        raise Abort(2, stage, "%s ledger-cap: artefact has no budget.cap (%s) — cannot "
                    "gate blind" % (GATE_LEDGER, _repo_rel(LEDGER_ARTEFACT)))
    reserve_raw = budget["reserve"] if "reserve" in budget else 0
    ok, facts = validate_g1(getattr(args, "turns", None), getattr(args, "reps", None),
                            _arms_count(getattr(args, "arm", None)),
                            getattr(args, "fetch_followup_allowance", None),
                            budget.get("cap"), reserve_raw, ratio=FETCH_FOLLOWUP_RATIO)
    verdict = {
        "gate": GATE_LEDGER, "what": "ledger-cap", "ok": False,
        "turns_total": facts.get("turns_total"), "arms": facts.get("arms"),
        "fetch_followup_allowance": facts.get("allowance"),
        "would_spend": facts.get("would_spend"),
        "spent": None, "cap": facts.get("cap"), "reserve": facts.get("reserve"),
        "headroom": None, "projected": None, "remaining": None,
        "artefact": _repo_rel(LEDGER_ARTEFACT), "artefact_sha256": digest,
        "flag": "--turns / --reps / --fetch-followup-allowance (or a larger cap in the "
                "ledger)",
    }
    if not ok:
        _refuse_from_operands(verdict, facts, 4, verdict["flag"])
        return verdict
    turns, reps, arms = facts["turns"], facts["reps"], facts["arms"]
    turns_total = facts["turns_total"]
    allowance = facts["allowance"]
    would_spend = facts["would_spend"]
    ledger = _ledger_module()
    try:
        report = ledger.build_report(_ledger_row_paths(doc), facts["cap"],
                                     facts["reserve"], would_spend)
    except Exception as exc:                      # RowsUnreadable and anything else
        raise Abort(2, stage, "%s ledger-cap: the ledger's own counter could not read "
                    "its row files (%s); an uncountable budget must refuse, never allow"
                    % (GATE_LEDGER, exc))
    b = report["budget"]
    # GATES-MESSAGE-CONSISTENCY: ONE sentence family per verdict, chosen by the verdict's
    # own `ok`. This branch used to print the refusal sentence unconditionally, so an
    # ADMITTED cell recorded "this cell needs 1,154 requests ... but only 4,320 remain:
    # shortfall -3,166 requests" -- where 1,154 is the CUMULATIVE spend after the cell,
    # 4,320 is the cap (limit = cap - reserve), and a negative shortfall is no shortfall.
    unspent = b["cap"] - b["reserve"] - b["spent"]     # spendable BEFORE this cell
    if b["within_budget"]:
        g1_consequence = (
            "G1 admits: this cell's own %s requests (would_spend: %d turn(s) x %d arm(s) "
            "x %d rep(s) = %d requests, plus a %d-request fetch follow-up allowance, "
            "ceil(%d turns x 68/801) unless --fetch-followup-allowance overrides it) are "
            "added to the %s requests already spent, so cumulative spend after this cell "
            "(projected) is %s requests against a limit of %s requests (cap %s - reserve "
            "%s): the cell fits, leaving %s requests of headroom after it, of which %s "
            "were unspent before it"
            % (_num(b["would_spend"]), turns, arms, reps, turns_total, allowance,
               turns_total, _num(b["spent"]), _num(b["projected"]),
               _num(b["headroom"]), _num(b["cap"]), _num(b["reserve"]),
               _num(b["remaining"]), _num(unspent)))
    else:
        g1_consequence = (
            "this cell would need %s requests (would_spend: %d turn(s) x %d arm(s) x %d "
            "rep(s) = %d requests, plus a %d-request fetch follow-up allowance) on top "
            "of the %s requests already spent, taking cumulative spend (projected) to %s "
            "requests against a limit of %s requests (cap %s - reserve %s): shortfall %s "
            "requests, so it must not send"
            % (_num(b["would_spend"]), turns, arms, reps, turns_total, allowance,
               _num(b["spent"]), _num(b["projected"]), _num(b["headroom"]),
               _num(b["cap"]), _num(b["reserve"]),
               _num(b["projected"] - b["headroom"])))
    verdict.update({
        "gate": GATE_LEDGER, "what": "ledger-cap", "ok": bool(b["within_budget"]),
        "spent": b["spent"], "headroom": b["headroom"], "projected": b["projected"],
        "remaining": b["remaining"],
        "counting_tool": _repo_rel(REQUEST_LEDGER_TOOL),
        "computed": "%s requests" % _num(b["projected"]),
        "limit": "%s requests (cap %s - reserve %s - spent %s)"
                 % (_num(b["headroom"]), _num(b["cap"]), _num(b["reserve"]),
                    _num(b["spent"])),
        "short": "%s %s/%s requests" % (GATE_LEDGER, _num(b["projected"]),
                                       _num(b["headroom"])),
        "consequence": g1_consequence,
    })
    return verdict


def _h1_min_n():
    """PARM-1's H1 minimum, taken from analyze_stats' own estimator, not a copy."""
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import analyze_stats  # noqa: E402
        return int(analyze_stats.min_n_for(0.95)), "analyze_stats.min_n_for(q=0.95)"
    except Exception:
        return 60, "PARM-1 H1 admissibility (n >= 60 at q=0.95; fallback constant)"


def _claim_module():
    """THE claim resolver — `claim_mode` owns the decision; this cell keeps no copy."""
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import claim_mode  # noqa: E402  stdlib only, no I/O, no request
    return claim_mode


#: WIRE-CLAIM-MODE: ONE resolution per invocation. The dry run reads three gate
#: verdicts and the live chain reads three again, so the flag text is resolved once and
#: the SAME frozen record answers both — a second parse is what let `smoke` be an
#: "unknown hypothesis" while the module already knew the three shapes.
_CLAIM_CACHE = {}


def _resolved_claim(args):
    """Resolve ``--hypothesis`` through :mod:`claim_mode` exactly once -> record|refusal.

    Returns a ``ClaimRecord`` (smoke|plumbing -> ``claim="none"``,
    ``comparison_eligible=False``; H1|H2|H3 -> comparable) or, for absent/empty/
    ``none``/unknown, the module's ``ClaimRefusal`` (code 12, G3's stage, its text).
    The inline parse that used to live here is deleted, not kept beside the call.
    """
    mod = _claim_module()
    text = getattr(args, "hypothesis", None)
    key = "" if text is None else str(text).strip()
    if key not in _CLAIM_CACHE:
        try:
            _CLAIM_CACHE[key] = mod.resolve_claim(text)
        except mod.ClaimRefusal as exc:
            _CLAIM_CACHE[key] = exc
    return _CLAIM_CACHE[key]


def _refusal_flag(args):
    """The flag as declared, upper-cased, and whether it named a hypothesis at all."""
    text = str(getattr(args, "hypothesis", None) or "").strip().upper()
    return text, bool(text) and text not in ("NONE", "NULL", "-")


def _refusal_computed(args, hyps):
    text, named = _refusal_flag(args)
    if named and text not in hyps:
        return "hypothesis=%s" % text
    return "hypothesis=none declared"


def _refusal_limit(args, hyps):
    text, named = _refusal_flag(args)
    if named and text not in hyps:
        return "one of %s" % (", ".join(sorted(hyps)) or "H1|H2|H3")
    return ("a declared claim (smoke|plumbing, or one of %s)"
            % (", ".join(sorted(hyps)) or "H1|H2|H3"))


def _refusal_consequence(args, hyps, module_text):
    """The pre-wiring sentence, then the module's refusal VERBATIM.

    WIRE-CLAIM-MODE: the decision is claim_mode's and its words are carried unchanged;
    the first clause is the wording G3's own readers and tests already key on, so the
    wiring changes who decides the claim without changing how a refusal reads.
    """
    text, named = _refusal_flag(args)
    if named and text not in hyps:
        first = "PARM-1 does not define hypothesis %r" % text
    else:
        first = ("a live cell spends requests on a claim it must name; no hypothesis "
                 "was declared, and silence is not a claim you may spend on")
    return "%s | %s" % (first, module_text)


def eval_gate_prereg(args, fixture):
    """G3 — the cell's own n must support the claim it will make, under PARM-1.

    H1 (p95 TTFT) is admissible only at n >= ``analyze_stats.min_n_for(0.95)`` = 60;
    at n < 60 the estimator itself raises InsufficientSamples, so a smaller cell may not
    claim it. H2 (per-turn prompt work) is a ratio over completed turns: n >= 1. H3
    (quality) is unadjudicable below 8 of the 12 checkpoints, so a fixture carrying
    fewer than 8 checkpoints cannot support it. A cell that declares NO hypothesis is
    refused with exit 12 -- G3's own code, distinct from preflight's 2: silence is not a
    claim you may spend on.
    """
    stage = "3c/7 G3 prereg gate"
    doc, digest = _load_gate_artefact(PREREG_ARTEFACT, GATE_PREREG, stage, "prereg")
    hyps = doc.get("hypotheses") or {}
    claim = _resolved_claim(args)
    if isinstance(claim, Exception):                 # absent/empty/none/unknown
        # The module's refusal text is the refusal: G3's own code (12), G3's own stage,
        # verbatim -- so no caller can mistake this for a different gate's decision.
        text = str(claim)
        return {
            "gate": GATE_PREREG, "what": "prereg", "rule_id": doc.get("rule_id"),
            "rule_sha256": doc.get("rule_sha256"),
            "hypothesis": str(getattr(args, "hypothesis", "") or ""),
            "hypothesis_source": "refused:claim_mode.resolve_claim",
            "n": 0, "artefact": _repo_rel(PREREG_ARTEFACT), "artefact_sha256": digest,
            "flag": "--hypothesis smoke|plumbing|H1|H2|H3",
            "thresholds": {}, "ok": False, "exit": claim.code,
            "claim": None, "comparison_eligible": False, "mode": None,
        # The DECISION is the module's; the refusal still names the same facts it
        # always named (computed/limit), and carries the module's sentence VERBATIM.
        "computed": _refusal_computed(args, hyps),
            "limit": _refusal_limit(args, hyps),
            "short": "%s n=0 (no claim declared)" % GATE_PREREG,
            "consequence": _refusal_consequence(args, hyps, text),
            "refusal_message": text,
            "refusal_stage": claim.stage, "refusal_code": claim.code,
        }
    name = claim.claim
    source = "flag:--hypothesis (%s)" % claim.mode
    min_n_h1, h1_basis = _h1_min_n()
    checkpoints = len((fixture or {}).get("checkpoints") or [])
    ok, facts = validate_g3(claim.claim, getattr(args, "turns", None),
                            getattr(args, "reps", None), checkpoints, hyps,
                            min_n_h1=min_n_h1, h1_basis=h1_basis,
                            smoke=claim.is_smoke)
    n = facts.get("n") or 0
    verdict = {
        "gate": GATE_PREREG, "what": "prereg", "rule_id": doc.get("rule_id"),
        "rule_sha256": doc.get("rule_sha256"),
        "hypothesis": name, "hypothesis_source": source, "n": n,
        "claim": claim.claim, "comparison_eligible": claim.comparison_eligible,
        "mode": claim.mode,
        "artefact": _repo_rel(PREREG_ARTEFACT), "artefact_sha256": digest,
        "flag": "--hypothesis / --turns / --reps",
        "thresholds": facts.get("thresholds") or {},
    }
    branch = facts.get("branch")
    if branch == "smoke":
        # ALLOWED, and non-comparable by declaration: the module builds this verdict so
        # the smoke branch has one author, not two.
        smoke = dict(_claim_module().smoke_prereg_verdict(verdict, n))
        smoke.update({"claim": claim.claim, "comparison_eligible": False,
                      "mode": claim.mode, "exit": 0})
        return smoke
    if not ok and branch == "operand":
        # turns/reps must be POSITIVE INTEGERS before any n is computed: turns=0 used to
        # reach the H3 branch, which only counted checkpoints, and ran in full.
        _refuse_from_operands(verdict, facts, 12, "--turns / --reps")
        return verdict
    if not ok and branch == "silence":
        verdict.update({
            "ok": False, "n": 0,
            "computed": "hypothesis=none declared",
            "limit": "a named hypothesis (%s)" % (", ".join(sorted(hyps)) or "H1|H2|H3"),
            "short": "%s n=%d (no hypothesis)" % (GATE_PREREG, n),
            "consequence": ("a live cell spends requests on a claim it must name; no "
                            "hypothesis was declared, and silence is not a claim you may "
                            "spend on"),
        })
        return verdict
    if not ok and branch == "unknown":
        verdict.update({
            "ok": False, "computed": "hypothesis=%s" % name,
            "limit": "one of %s" % ", ".join(sorted(hyps)),
            "short": "%s n=%d (unknown %s)" % (GATE_PREREG, n, name),
            "consequence": "PARM-1 does not define hypothesis %r" % name,
        })
        return verdict

    min_n = facts.get("min_n")
    if branch == "H1":
        ok = n >= min_n
        verdict["thresholds"] = {
            "estimator": facts["thresholds"].get("estimator"),
            "admissibility": facts["thresholds"].get("admissibility"),
            "ranking_rule": facts["thresholds"].get("ranking_rule"),
            "min_n": min_n, "q": 0.95, "basis": facts["thresholds"].get("basis"),
        }
        verdict["consequence"] = (
            "PARM-1 admits H1 (p95 TTFT, q=0.95) only at n >= %d completed turns; this "
            "cell would have n=%d, so its own n cannot support the claim it would state"
            % (min_n, n))
    elif branch == "H3":
        verdict["consequence"] = (
            "PARM-1's H3 returns no verdict below %d decidable of 12 checkpoints; this "
            "fixture carries %d checkpoint(s), so the claim is unsupportable"
            % (min_n, checkpoints))
    else:
        verdict["consequence"] = (
            "PARM-1's %s needs at least %d completed turn per arm; this cell would have "
            "n=%d" % (name, min_n, n))
    verdict.update({
        "ok": ok,
        "computed": "n=%d" % n,
        "limit": "n >= %d" % min_n,
        "short": "%s n=%d %s %d" % (GATE_PREREG, n, "≥" if ok else "<", min_n),
    })
    return verdict


_MANIFEST_SERIAL = [0]


def gate_manifest_path(out_dir, stamp, arm):
    """The manifest path for ONE run: unique per process AND per write, always.

    GATE-OVERRIDE-FIX F2: the name used to be ``cell-<arm>-<stamp>.gates.json`` with
    ``stamp`` at second resolution, and the default ``--out-dir`` is the repo's
    ``measure/`` directory — so two cells started in the same second wrote ONE file and
    the second overwrote the first run's gate verdicts (observed as transient rc=1/rc=0
    while a live path was probed). A gate verdict that can be overwritten is not a
    verdict, so the name now carries the pid and a per-process serial. Two concurrent
    PROCESSES differ by pid; two writes in one process differ by serial; ``stamp`` still
    keeps the clock legible. :func:`write_gate_manifest` additionally creates the file
    with O_EXCL and retries the serial, so even a pid reused inside one second cannot
    collide.
    """
    _MANIFEST_SERIAL[0] += 1
    return os.path.join(out_dir, "cell-%s-%s-p%d-%03d.gates.json"
                        % (arm, stamp, os.getpid(), _MANIFEST_SERIAL[0]))


def write_gate_manifest(out_dir, stamp, arm, gates, hypothesis):
    """Record the gate verdicts AND the artefact digests they consulted.

    A gate that leaves no trace cannot be audited after the fact, so the manifest is
    written before the runner is invoked: if the cell later crashes, the limits it
    passed under are still on disk. The file is created EXCLUSIVELY (``O_EXCL``): if a
    sibling process already holds this name, the serial advances instead of overwriting
    another run's verdicts.
    """
    os.makedirs(out_dir, exist_ok=True)
    doc = {
        "unit": "WIRE-GATES", "arm": arm, "stamp": stamp,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hypothesis": hypothesis,
        "verdicts": gates,
        "projection_override": next((g.get("projection_override") for g in gates
                                     if g.get("projection_override")), None),
        "artefact_digests": {g["artefact"]: g["artefact_sha256"] for g in gates},
        "counted_by": _repo_rel(REQUEST_LEDGER_TOOL),
        "note": ("verdicts were taken BEFORE the runner was invoked; each digest pins the "
                 "artefact the limit came from"),
    }
    payload = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    for _attempt in range(100):
        path = gate_manifest_path(out_dir, stamp, arm)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            continue
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
        except BaseException:
            raise
        return _repo_rel(path)
    raise OSError("could not create a unique gate manifest under %s" % out_dir)


def _runner_exit_code(rc):
    """The CELL's exit code for a runner exit: propagated, declared-remapped, or crash.

    The runner's own codes are propagated distinctly -- collapsing them into one number is
    how a runaway abort became indistinguishable from a crash.  The one declared remap is
    `RUNNER_MAPPED_TO_CELL` (the runner's cap-gate 9 -> the cell's 14): a cap-gate refusal
    must reach the caller under its own name, never as runner-crash.
    """
    if rc in _RUNNER_CODES:
        return rc
    return _RUNNER_MAPPED_TO_CELL.get(rc, exit_codes.EXIT_RUNNER_CRASH)


def _capgate_abort(rc, err_lines, rows_path, detail=None):
    """The cap-gate refusal AT CELL LEVEL: its own code, the gate's own words, its delta.

    A refusal that says "unmapped runner failure" sends a reader to look for a crash that
    did not happen (measured: V-CAPGATE-REFUSE, defect (a)).  The runner's refusal line is
    quoted verbatim so the delta and the headroom travel with the code.
    """
    return Abort(exit_codes.EXIT_CAPGATE_UNRECORDED, "4/7 run",
                 "cap gate refused: unrecorded spend — %s (runner rc %r) — rows kept at %s"
                 % (_capgate_quote(err_lines), rc, _repo_rel(rows_path)), detail)


def _tee_stderr(proc, sink):
    """Echo the runner's stderr live and keep every line, so a refusal is quotable."""
    try:
        for line in proc.stderr:
            sink.append(line)
            sys.stderr.write(line)
            sys.stderr.flush()
    finally:
        try:
            proc.stderr.close()
        except Exception:
            pass


def _capgate_quote(lines):
    """The runner's own cap-gate refusal line, verbatim, whitespace-collapsed.

    Never paraphrase it: the delta and the headroom are the evidence, and a summarised
    refusal ("the gate refused") is exactly what the caller could not act on.
    """
    for line in lines or ():
        if "CAP GATE UNRECORDED" in line or "CAP GATE RECONCILE DIVERGENCE" in line:
            return " ".join(line.split())
    tail = " ".join("".join(lines or ()).split())
    return tail[-400:] if tail else "(the runner printed no reason)"


# --------------------------------------------------------------------- 4. run
def stage_run(args, rows_path, gate_manifest=None):
    """Invoke run_longrun.py UNCHANGED, streaming its output through."""
    argv = [sys.executable, RUNNER, "--fixture", args.fixture, "--arms", args.arm,
            "--reps", str(args.reps), "--rows", rows_path,
            "--turn-wall-cap", str(float(args.turn_wall_cap)),
            "--runaway-turns", str(int(args.runaway_turns)),
            "--thinking", thinking_for_runner(args)]
    if args.endpoint:
        argv += ["--base-url", args.endpoint]
    n_turns = int(args.turns or 0)
    fixture_n = 0
    try:
        fixture_n = int(_load_fixture(args.fixture).get("N") or 0)
    except (OSError, json.JSONDecodeError):
        pass
    truncated = bool(n_turns and fixture_n and n_turns != fixture_n)
    if truncated:
        argv += ["--max-turns", str(n_turns)]
    claim = _resolved_claim(args)
    claim_fields, claim_sidecar = None, None
    if not isinstance(claim, Exception):
        # The resolved claim travels WITH the run: one record, written once, beside the
        # rows file the runner writes. analyze_stats reads it and refuses a claim="none"
        # cell by name (incomparable_claim), so a smoke cell's numbers can be reported
        # and can never be pooled with an H1/H2/H3 arm.
        claim_fields = {"claim": claim.claim,
                        "comparison_eligible": claim.comparison_eligible,
                        "mode": claim.mode}
        claim_sidecar = rows_path + ".claim.json"
        try:
            with open(claim_sidecar, "w", encoding="utf-8") as fh:
                json.dump({"claim": claim.claim,
                           "comparison_eligible": claim.comparison_eligible,
                           "mode": claim.mode,
                           "resolver": "claim_mode.resolve_claim",
                           "rows_path": _repo_rel(rows_path),
                           "note": ("one claim decision per invocation; a claim=none "
                                    "cell is reported on its own and never compared")},
                          fh, indent=1, sort_keys=True)
                fh.write("\n")
        except OSError:
            claim_fields, claim_sidecar = claim_fields, None
    # CLAIM-ROW-STAMP: thread the ALREADY-resolved claim (cell's cached record, one
    # parse in claim_mode) to the runner, so every row it writes is stamped.
    _claim_rec = _resolved_claim(args)
    if not isinstance(_claim_rec, Exception):
        argv += ["--claim-mode", "smoke" if _claim_rec.is_smoke else _claim_rec.claim]
    print("cell:   invoking: %s" % " ".join(argv), flush=True)
    # The runner's stderr is streamed to the cell's own stderr AND kept line by line: it
    # carries the cap-gate arithmetic, and a refusal must be QUOTED to the caller rather
    # than summarised as "unmapped runner failure".
    err_lines = []
    proc = subprocess.Popen(argv, stderr=subprocess.PIPE, text=True, bufsize=1)
    _pump = threading.Thread(target=_tee_stderr, args=(proc, err_lines), daemon=True)
    _pump.start()
    proc.wait()
    _pump.join(timeout=10)
    rc = proc.returncode
    # THE runner launch, and the only one: it carries the gate record it ran under, so
    # a launch with no gate record is detectable rather than merely discouraged.
    SPAWNS.record(argv=argv, purpose="runner_launch", phase="4/7 run",
                  pid=getattr(proc, "pid", None), label="run_longrun",
                  gate_record=gate_manifest)
    detail = {"argv": argv, "exit": rc, "rows_path": _repo_rel(rows_path),
              "rows_written": _count_rows(rows_path),
              "turns_requested": n_turns, "turns_truncated": truncated,
              "claim": claim_fields,
              # absolute, not repo-relative: the sidecar lives beside the rows file,
              # which may be outside the repo (a scratch out_dir) and `_repo_rel` would
              # then invent a "../../.." path that cannot be opened.
              "claim_sidecar": (claim_sidecar
                                if claim_sidecar and os.path.exists(claim_sidecar)
                                else None)}
    if rc != 0:
        code = _runner_exit_code(rc)
        if code == exit_codes.EXIT_CAPGATE_UNRECORDED:
            raise _capgate_abort(rc, err_lines, rows_path, detail)
        raise Abort(code, "4/7 run",
                    "run_longrun.py exited %d (%s) — rows kept at %s"
                    % (rc, exit_codes.describe(rc) if rc in _RUNNER_CODES
                       else exit_codes.describe(code), _repo_rel(rows_path)), detail)
    return detail


# ------------------------------------------------------------------- 5. grade
def stage_grade(args, rows_path, out_dir, stamp):
    grade_path = os.path.join(out_dir, "cell-%s-%s.grade-v5.json" % (args.arm, stamp))
    argv = [sys.executable, GRADER, "--rows", rows_path, "--fixture", args.fixture,
            "--out", grade_path]
    rc, out, err = _run(argv, purpose="other", phase="5/7 grade", label="grade_v5")
    detail = {"argv": argv, "exit": rc, "output": (out or "").splitlines(),
              "stderr": (err or "").splitlines()[-20:],
              "grade_path": _repo_rel(grade_path)}
    if rc != 0:
        raise Abort(10, "5/7 grade", "grade_v5.py exited %d: %s"
                    % (rc, (err or out or "").strip()))
    verdicts = {}
    for line in (out or "").splitlines():
        line = line.strip()
        if line.startswith("acc=") or " acc=" in line:
            parts = line.split()
            if parts:
                verdicts[parts[0]] = line
    detail["verdicts"] = verdicts
    return detail


# ----------------------------------------------------------------- 6. analyse
def stage_analyse(args, rows_path, out_dir, stamp, grade_path=None):
    json_path = os.path.join(out_dir, "cell-%s-%s.analysis.json" % (args.arm, stamp))
    argv = [sys.executable, ANALYZE, "--rows", rows_path, "--json", json_path]
    # The accuracy population is the GRADER's checkpoint cells, not the rows:
    # the analyser must consume grade_v5's verdicts, never re-derive them.
    if grade_path:
        argv += ["--grade", grade_path]
    rc, out, err = _run(argv, purpose="other", phase="6/7 analyse",
                        label="analyze_stats")
    if rc != 0:
        raise Abort(11, "6/7 analyse", "analyze_stats.py exited %d: %s"
                    % (rc, (err or out or "").strip()))

    doc = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except json.JSONDecodeError:
            doc = {}

    # The card's contract: per arm print n, dropped-null, p50, p95 WITH interval,
    # accuracy passed/decidable WITH Wilson interval; per pair a McNemar line or
    # its refusal. Anything unavailable must be a printed REFUSAL, never a number.
    checks, refusals = [], []
    for arm, entry in (doc.get("arms") or {}).items():
        checks.append({"arm": arm, "n_rows": entry.get("n_rows")})
        t = entry.get("ttft") or {}
        nulls = t.get("dropped_null")
        if nulls is None:
            refusals.append("arm %s: dropped-null count not reported" % arm)
        for key in ("p50", "p95"):
            est = entry.get(key) or {}
            if est.get("point") is not None and est.get("lo") is not None:
                checks.append({"arm": arm, key: {"point": est["point"],
                                                 "lo": est["lo"], "hi": est["hi"],
                                                 "n": est.get("n")}})
            elif est.get("refused"):
                refusals.append("arm %s %s: %s" % (arm, key, est["refused"]))
            else:
                refusals.append("arm %s %s: analyze_stats printed neither a number "
                                "nor a refusal" % (arm, key))
        acc = entry.get("accuracy") or {}
        if acc.get("decidable", 0) > 0:
            checks.append({"arm": arm, "accuracy": "%s/%s"
                           % (acc.get("passed"), acc.get("decidable"))})
            if "wilson95" not in (out or ""):
                refusals.append("arm %s accuracy: Wilson interval not printed" % arm)
        else:
            refusals.append("arm %s accuracy: no decidable turns (n=0)" % arm)
    for rec in doc.get("pairs") or []:
        if rec.get("mcnemar"):
            checks.append({"pair": "%s vs %s" % (rec.get("arm_a"), rec.get("arm_b")),
                           "mcnemar": rec["mcnemar"]})
        else:
            refusals.append("pair %s vs %s McNemar refused: %s"
                            % (rec.get("arm_a"), rec.get("arm_b"), rec.get("refused")))
    if not doc.get("arms"):
        refusals.append("analyze_stats reported no arms at all for %s"
                        % _repo_rel(rows_path))

    for line in refusals:
        print("cell:   REFUSAL %s" % line, flush=True)

    return {"argv": argv, "exit": rc, "output": (out or "").splitlines(),
            "stderr": (err or "").splitlines()[-20:],
            "analysis_path": _repo_rel(json_path), "checks": checks,
            "refusals": refusals,
            "populations": {arm: (entry.get("accuracy") or {})
                            for arm, entry in (doc.get("arms") or {}).items()}}


# --------------------------------------- 6b. consistency gate (exit 9)
GRADE_DECIDABLE_SRC = "grade_v5.py:653"
ANALYSE_GRADED_SRC = "analyze_stats.py:457"


def stage_consistency(args, grade_doc, analysis):
    """Refuse (9) a cell whose grader and analyser disagree about the population.

    Authoritative facts must not silently disagree: a record whose accuracy
    numerator came from grade_v5 while its denominator came from a different
    population in analyze_stats is the exact defect that produced "decidable=3"
    and "UNDECIDABLE (n=0)" from one run. `--allow-inconsistent` overrides and
    the override is recorded in the cell record.
    """
    arms = grade_doc.get("arms") or {}
    grader_n = sum(int((a or {}).get("decidable") or 0) for a in arms.values())
    graded = sum(int((p or {}).get("graded_n") or 0)
                 for p in (analysis.get("populations") or {}).values())
    line = ("grader decidable=%d (%s) vs analyser graded_n=%d (%s)"
            % (grader_n, GRADE_DECIDABLE_SRC, graded, ANALYSE_GRADED_SRC))
    contradictory = (grader_n > 0) != (graded > 0)
    detail = {"grader_decidable": grader_n, "analyser_graded_n": graded,
              "line": line, "contradictory": contradictory, "override": False}
    if contradictory:
        if not getattr(args, "allow_inconsistent", False):
            raise Abort(9, "7 consistency",
                        "authoritative facts disagree — %s" % line)
        detail["override"] = True
    return detail


# ------------------------------------------------------------------ 7. record
def stage_record(args, stamp, frames, record, analysis, grade, budget, harness, run):
    out_dir = args.out_dir
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        raise Abort(7, "7/7 record", "the record directory %s could not be created: %s"
                    % (_repo_rel(out_dir), exc))
    json_path = os.path.join(out_dir, "cell-%s-%s.json" % (args.arm, stamp))
    md_path = os.path.join(out_dir, "cell-%s-%s.md" % (args.arm, stamp))
    try:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1, sort_keys=True)
            fh.write("\n")
    except OSError as exc:
        raise Abort(7, "7/7 record", "the cell record %s could not be written: %s"
                    % (_repo_rel(json_path), exc))

    lines = ["# CELL %s — %s" % (args.arm, stamp), "",
             "- fixture: `%s`" % _repo_rel(args.fixture),
             "- arm: `%s`  turns: %s  reps: %s  mode: %s"
             % (args.arm, args.turns, args.reps,
                "offline (%s)" % _repo_rel(args.offline) if args.offline else "live"),
             "- harness_sha256: `%s`" % harness["harness_sha256"],
             "- harness files: %s" % ", ".join("`%s`" % k for k in sorted(harness["files"])),
             "- requests actually used: **%s**" % record["requests_used"], ""]
    lines.append("## stages")
    lines.append("")
    for fr in frames:
        lines.append("- `%s`" % fr["line"])
    if budget:
        lines += ["", "## budget", "",
                  "would_send_total=%s  budget=%s  required_with_headroom=%s  "
                  "quota_remaining=%s (%s)"
                  % (budget["would_send_total"], budget["budget"],
                     budget["required_with_headroom"], budget["quota_remaining"],
                     budget["quota_basis"])]
    gates = record.get("gates") or {}
    if gates.get("verdicts"):
        lines += ["", "## gate chain (verdicts taken before the runner was invoked)", ""]
        for v in gates["verdicts"]:
            lines.append("- `%s %s` computed=%s limit=%s artefact=`%s` sha256=`%s`"
                         % (v["gate"], "allow" if v.get("ok") else "refuse",
                            v.get("computed"), v.get("limit"), v.get("artefact"),
                            v.get("artefact_sha256")))
        hyp = record.get("hypothesis") or {}
        if hyp:
            lines.append("- hypothesis: `%s` (%s), n=%s, rule_sha256=`%s`"
                         % (hyp.get("name"), hyp.get("source"), hyp.get("n"),
                            hyp.get("rule_sha256")))
        if gates.get("manifest"):
            lines.append("- manifest: `%s`" % gates["manifest"])
    lines += ["", "## grade (verbatim)", "", "```"]
    lines += grade["output"] or ["(no output)"]
    lines += ["```", "", "## analysis (verbatim)", "", "```"]
    lines += analysis["output"] or ["(no output)"]
    lines += ["```"]
    if analysis["refusals"]:
        lines += ["", "## refusals (numbers withheld on purpose)", ""]
        lines += ["- %s" % r for r in analysis["refusals"]]
    try:
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError as exc:
        raise Abort(7, "7/7 record", "the cell markdown %s could not be written: %s"
                    % (_repo_rel(md_path), exc))
    out = {"json": _repo_rel(json_path), "markdown": _repo_rel(md_path)}
    if not args.no_cell_handoff:
        # Stage 7 also reports the cell in the unit shape, beside the other handoffs.
        out["handoff"] = _repo_rel(write_handoff(
            "CELL-%s-%s" % (args.arm, stamp), "done",
            [out["json"], out["markdown"]],
            {"command_or_count": "exit 0; requests_used=%s; refusal_lines=%d"
             % (record["requests_used"], len(analysis["refusals"])),
             "commands": [" ".join(record.get("_argv") or []) or
                          "python3 experiments/ptr-engine/longrun/cell.py --arm %s"
                          % args.arm]},
            next_hint="re-run with --expect-harness %s to prove the harness has not moved"
            % harness["harness_sha256"],
            write_paths=[out["json"], out["markdown"]]))
    return out


def write_handoff(unit, status, artifacts, evidence, blocker="", next_hint="",
                  write_paths=None, assumptions=None):
    os.makedirs(HANDOFFS, exist_ok=True)
    doc = {"unit": unit, "status": status, "artifacts": artifacts,
           "evidence": evidence, "blocker": blocker, "next_unit_hint": next_hint,
           "write_paths": write_paths or []}
    if assumptions:
        doc["assumptions"] = assumptions
    path = os.path.join(HANDOFFS, "%s.json" % unit)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return path


# ------------------------------------------------------------------------ cli
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="ONE COMMAND PER CELL: preflight -> harness freeze -> budget -> "
                    "run -> grade -> analyse -> record. Refuses rather than publishes "
                    "a number it cannot qualify.")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--turns", type=int, default=48)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--budget", type=int, default=None,
                    help="maximum requests this cell may send (required unless --offline)")
    ap.add_argument("--endpoint", default=None)
    ap.add_argument("--expect-harness", default=None)
    ap.add_argument("--offline", default=None, metavar="ROWS_JSONL",
                    help="skip stages 3-4 and grade/analyse/record an existing row file")
    ap.add_argument("--out-dir", default=MEASURE)
    ap.add_argument("--thinking", default=None, metavar="absent|off|auto|on",
                    help="the cell's thinking mode. Drives BOTH the runner payload "
                         "(--thinking; absent means off, the runner's own default) and "
                         "the per-turn projection figure read from PROJECTION.json "
                         "defaults.projected_turn_wall_s_by_mode. An unknown spelling is "
                         "refused with exit 8 rather than priced with a pooled default")
    ap.add_argument("--turn-wall-cap", type=float, default=180.0,
                    help="per-turn wall ceiling handed to the runner; a turn past it is "
                         "aborted LIVE (default 180). Also printed as the projection's "
                         "worst case; it is not the projection multiplier")
    ap.add_argument("--projected-turn-wall", type=float, default=None,
                    help="EXPECTED per-turn wall in seconds, used for the preflight "
                         "projection (default: the calibrated value in "
                         "experiments/ptr-engine/measure/PROJECTION.json, 60). "
                         "Calibrated in docs/PROJECTION-CALIBRATION.md from measured "
                         "rows; NOT the abort threshold --turn-wall-cap")
    ap.add_argument("--fetch-followup-allowance", type=int, default=None,
                    dest="fetch_followup_allowance",
                    help="requests G1 must also reserve for the tool loop's fetch "
                         "follow-ups (default: ceil(turns x arms x reps x %.4f), measured "
                         "from the ledger's own row corpus)" % FETCH_FOLLOWUP_RATIO)
    ap.add_argument("--hypothesis", default=None, metavar="H1|H2|H3",
                    help="the PARM-1 hypothesis this cell will claim; G3 refuses (exit 12) "
                         "a cell whose n cannot support it (H1 needs n >= 60). There is NO "
                         "default: an absent flag is read as 'none' and refused, and an "
                         "unknown name is refused too -- silence is not a claim you may "
                         "spend on")
    ap.add_argument("--dry-run", action="store_true",
                    help="print all three gate verdicts (G1 ledger cap, G2 projection, "
                         "G3 prereg) with their numbers and what the run would cost, then "
                         "exit 0 without contacting any endpoint")
    ap.add_argument("--projected-from", default=None, metavar="ROWS_JSONL|p90",
                    help="use this prior rows-*.jsonl's p90 turn wall as the projection "
                         "multiplier, or the literal 'p90' for the artefact's measured "
                         "p90 of the cell's own thinking mode; the preflight line names "
                         "which source was used")
    ap.add_argument("--runaway-turns", type=int, default=2,
                    help="runaway turns that end the cell with the runner's exit 6 "
                         "(default 2)")
    ap.add_argument("--max-wall", type=float, default=3600.0,
                    help="projected wall-clock ceiling in seconds; G2 refuses (exit 8) "
                         "when projected_requests x the calibrated per-turn wall exceeds "
                         "it (default 3600). It must be POSITIVE: zero or negative is "
                         "refused (exit 8) and is not an 'unlimited' mode")
    ap.add_argument("--handoff-unit", default=None,
                    help="also write orchestration/handoffs/<UNIT>.json for this cell")
    ap.add_argument("--no-cell-handoff", action="store_true",
                    help="skip the per-cell CELL-<arm>-<stamp>.json handoff (tests use "
                         "this so a test run leaves no handoff behind)")
    ap.add_argument("--allow-inconsistent", action="store_true",
                    help="record a cell whose grader and analyser disagree about the "
                         "decided population instead of exiting 9 (override recorded)")
    args = ap.parse_args(argv)

    stamp = _now()
    frames, record = [], {}
    fixture = truth = None
    harness = budget = run = grade = analysis = None
    projection = None
    gate_verdicts, gate_manifest, hypothesis = [], None, None
    os.makedirs(args.out_dir, exist_ok=True)

    def emit(stage, status, text):
        line = "%s %s %s" % (stage, status, text)
        frames.append({"stage": stage, "status": status, "line": line})
        print("cell: %s" % line, flush=True)

    try:
        # 1
        fixture, truth, pdet = stage_preflight(args)
        emit("1/7 preflight", "ok", "checkpoints=%d turns=%s kinds=%s fixture=%s"
             % (pdet["checkpoints"], pdet["turns"], pdet["kinds"],
                pdet["fixture_version"]))

        # 2
        harness = stage_harness(args, fixture)
        emit("2/7 harness", "ok", "harness_sha256=%s files=%d"
             % (harness["harness_sha256"], len(harness["files"])))

        if args.offline:
            if not os.path.exists(args.offline):
                raise Abort(2, "4/7 run", "--offline row file does not exist: %s"
                            % _repo_rel(args.offline))
            rows_path = os.path.abspath(args.offline)
            emit("3/7 budget", "skipped", "offline mode: no request is sent")
            emit("4/7 run", "skipped", "offline mode: rows reused from %s"
                 % _repo_rel(rows_path))
            budget = None
            run = {"argv": [], "exit": None, "rows_path": _repo_rel(rows_path),
                   "rows_written": _count_rows(rows_path), "offline": True}
        elif args.dry_run:
                # A dry run prints the DECISION, not a promise. It takes the three
                # verdicts, prints their numbers, and exits 0 without a runner, a
                # socket or an endpoint: nothing here can send a request.
                #
                # GATE-OVERRIDE-FIX F3 (the documented contract): exit 0 means "the
                # preview ran", NOT "the gates allow". A dry run that reports a would-be
                # refusal still exits 0 by design -- it authorises nothing -- and the
                # caller MUST parse the `WOULD-REFUSE` verdict lines (or the count in the
                # final line) rather than the exit code. That divergence from "refusal
                # surfaces carry exit codes" is written down in docs/GATE-CHAIN.md §7 and
                # asserted by tests/test_gate_override.py.
                turns_total = (int(args.turns or 0) * _arms_count(args.arm)
                               * int(args.reps or 1))
                gate_verdicts = [
                    eval_gate_ledger(args),
                    eval_gate_projection(args, {"would_send_total": turns_total}),
                    eval_gate_prereg(args, fixture),
                ]
                print("cell: 0/7 dry-run " + " · ".join(g["short"] for g in gate_verdicts),
                      flush=True)
                print("cell: 0/7 dry-run exit-codes declared=%s (%d codes, read from "
                      "exit_codes.EXIT_TABLE -- the only copy)"
                      % (",".join(str(c) for c in sorted(exit_codes.EXIT_TABLE)),
                         len(exit_codes.EXIT_TABLE)), flush=True)
                print("cell: 0/7 dry-run would cost: turns=%d arms=%d reps=%d -> %d "
                      "requests (incl. follow-up allowance %d), ~%d s projected wall; "
                      "0 requests sent, no endpoint contacted"
                      % (int(args.turns or 0), _arms_count(args.arm), int(args.reps or 1),
                         gate_verdicts[1]["projected_requests"],
                         gate_verdicts[0]["fetch_followup_allowance"],
                         gate_verdicts[1]["projected_wall_s"]), flush=True)
                for g in gate_verdicts:
                    print("cell: 0/7 dry-run %s %s computed=%s limit=%s artefact=%s "
                          "sha256=%s flag=%s"
                          % (g["gate"], "allow" if g["ok"] else "WOULD-REFUSE",
                             g["computed"], g["limit"], g["artefact"],
                             g["artefact_sha256"], g["flag"]), flush=True)
                print("cell: 0/7 dry-run hypothesis=%s (%s) thresholds=%s"
                      % (gate_verdicts[2]["hypothesis"],
                         gate_verdicts[2]["hypothesis_source"],
                         json.dumps(gate_verdicts[2]["thresholds"], sort_keys=True)),
                      flush=True)
                print("cell: 0/7 dry-run claim=%s comparison_eligible=%s mode=%s "
                      "resolver=claim_mode.resolve_claim (one resolution per invocation)"
                      % (gate_verdicts[2].get("claim"),
                         gate_verdicts[2].get("comparison_eligible"),
                         gate_verdicts[2].get("mode")), flush=True)
                would = len([g for g in gate_verdicts if not g["ok"]])
                print("cell: EXIT 0 — dry run: %d of 3 gate(s) would refuse; exit 0 means "
                      "the PREVIEW ran, not that the gates allow: callers MUST parse this "
                      "line or the WOULD-REFUSE verdict lines, never the exit code; "
                      "nothing was sent" % would, flush=True)
                return 0

        else:
            budget = stage_budget(args)
            emit("3/7 budget", "ok",
                 "would_send_total=%d +%.0f%%=%d <= budget=%d (quota_remaining=%d %s)"
                 % (budget["would_send_total"], BUDGET_HEADROOM * 100,
                    budget["required_with_headroom"], budget["budget"],
                    budget["quota_remaining"], "best-effort"))

            # ---- THE GATE CHAIN: the only door to a request --------------------
            gate_verdicts = []
            ledger_gate = _enforce(eval_gate_ledger(args), "3a/7 G1 ledger gate", 4)
            gate_verdicts.append(ledger_gate)
            emit("3a/7 G1 ledger gate", "ok",
                 "%s · cap %s - reserve %s - spent %s (counted by %s)"
                 % (ledger_gate["short"], _num(ledger_gate["cap"]),
                    _num(ledger_gate["reserve"]), _num(ledger_gate["spent"]),
                    os.path.basename(ledger_gate["counting_tool"])))
            projection = _enforce(eval_gate_projection(args, budget), "3b/7 projection", 8)
            gate_verdicts.append(projection)
            emit("3b/7 projection", "ok", projection["line"])
            prereg_gate = _enforce(eval_gate_prereg(args, fixture), "3c/7 G3 prereg gate", 12)
            gate_verdicts.append(prereg_gate)
            emit("3c/7 G3 prereg gate", "ok",
                 "%s · claim %s (PARM-1 %s) under %s"
                 % (prereg_gate["short"], prereg_gate["hypothesis"],
                    prereg_gate["rule_sha256"] or "rule",
                    json.dumps(prereg_gate["thresholds"], sort_keys=True)))
            hypothesis = {
                "name": prereg_gate["hypothesis"],
                "source": prereg_gate["hypothesis_source"],
                "rule_id": prereg_gate["rule_id"],
                "rule_sha256": prereg_gate["rule_sha256"],
                "n": prereg_gate["n"],
                "thresholds": prereg_gate["thresholds"],
                "claim": prereg_gate.get("claim"),
                "comparison_eligible": prereg_gate.get("comparison_eligible"),
                "mode": prereg_gate.get("mode"),
            }
            gate_manifest = write_gate_manifest(args.out_dir, stamp, args.arm,
                                                gate_verdicts, hypothesis)
            emit("gates", "recorded", "%s (%d verdicts, %d artefact digest(s))"
                 % (gate_manifest, len(gate_verdicts),
                    len({g["artefact"] for g in gate_verdicts})))

            rows_path = os.path.join(
                args.out_dir, "rows-cell-%s-%s.jsonl" % (args.arm, stamp))
            run = stage_run(args, rows_path, gate_manifest)
            emit("4/7 run", "ok", "rows=%d path=%s"
                 % (run["rows_written"], run["rows_path"]))

        # 5
        grade = stage_grade(args, rows_path, args.out_dir, stamp)
        emit("5/7 grade", "ok", "verdicts=%s"
             % ("; ".join(grade["verdicts"].values()) or "-"))

        # 6 — accuracy is taken FROM the grade document, never re-derived
        grade_doc_path = os.path.join(
            args.out_dir, "cell-%s-%s.grade-v5.json" % (args.arm, stamp))
        analysis = stage_analyse(args, rows_path, args.out_dir, stamp,
                                 grade_path=grade_doc_path)
        emit("6/7 analyse", "ok", "checks=%d refusals=%d (a refusal is printed, "
             "never replaced by a number)" % (len(analysis["checks"]),
                                              len(analysis["refusals"])))

        # 6b — exit 9: the grader's decidable count and the analyser's graded
        # population must agree about whether anything was decided at all.
        grade_doc = {}
        if os.path.exists(grade_doc_path):
            with open(grade_doc_path, encoding="utf-8") as fh:
                grade_doc = json.load(fh)
        consistency = stage_consistency(args, grade_doc, analysis)
        emit("6b/7 consistency", "OVERRIDDEN" if consistency["override"] else "ok",
             consistency["line"])

        requests_used = (run["rows_written"] if not args.offline
                         else 0)
        record = {
            "unit": "CELL-ONE-COMMAND", "arm": args.arm,
            "fixture": _repo_rel(args.fixture), "fixture_version": fixture.get("fixture_version"),
            "turns": args.turns, "reps": args.reps, "offline": bool(args.offline),
            "timestamp": stamp, "generated_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds"),
            "harness": harness, "budget": budget, "run": run,
            "projection": projection, "consistency": consistency,
            "gates": {"manifest": gate_manifest, "verdicts": gate_verdicts,
                      "skipped": bool(args.offline),
                      "skipped_reason": ("offline mode sends no request, so no gate is "
                                         "consulted" if args.offline else None),
                      "artefact_digests": {g["artefact"]: g["artefact_sha256"]
                                           for g in gate_verdicts}},
            "hypothesis": hypothesis,
            "grade": grade, "analysis": analysis,
            "requests_used": requests_used,
            "requests_note": ("offline: zero requests" if args.offline else
                              "rows written by the runner (one row per request)"),
            "stages": frames,
            "spawns": SPAWNS.as_dict(),
        }
        # RECORD-ROWS-JOIN (GRID-GAP-DIAG): the pinned reader only links a TOP-LEVEL
        # `rows_path`; `run.rows_path` alone is invisible to it. Additive, no gen bump:
        # cell.py is not in the harness pin's file list (cell.py:129-135).
        record = with_rows_path(record)
        # 7
        paths = stage_record(args, stamp, frames, record, analysis, grade, budget,
                             harness, run)
        record["records"] = paths
        final_path = os.path.join(args.out_dir, "cell-%s-%s.json" % (args.arm, stamp))
        try:
            with open(final_path, "w", encoding="utf-8") as fh:
                json.dump(record, fh, indent=1, sort_keys=True)
                fh.write("\n")
        except OSError as exc:
            raise Abort(7, "7/7 record", "the cell record %s could not be written: %s"
                        % (_repo_rel(final_path), exc))
        emit("7/7 record", "ok", "json=%s md=%s"
             % (paths["json"], paths["markdown"]))

        if args.handoff_unit:
            hp = write_handoff(
                args.handoff_unit, "done",
                [paths["json"], paths["markdown"]],
                {"command_or_count": "exit 0; would_send_total=%s; refusal_lines=%d"
                 % (budget["would_send_total"] if budget else "offline",
                    len(analysis["refusals"])),
                 "commands": ["python3 experiments/ptr-engine/longrun/cell.py "
                              "--arm %s --fixture %s %s"
                              % (args.arm, _repo_rel(args.fixture),
                                 ("--offline %s" % _repo_rel(args.offline))
                                 if args.offline else "--budget %s" % args.budget)]},
                next_hint="run one live cell through cell.py with --expect-harness %s"
                % harness["harness_sha256"],
                write_paths=[paths["json"], paths["markdown"]])
            emit("handoff", "ok", _repo_rel(hp))

        print("cell: EXIT 0 — cell %s %s recorded (%d stage lines, %d refusals)"
              % (args.arm, stamp, len(frames), len(analysis["refusals"])), flush=True)
        return 0

    except Abort as exc:
        line = "%s REFUSED(%d) %s" % (exc.stage, exc.code, exc.message)
        frames.append({"stage": exc.stage, "status": "refused", "line": line})
        print("cell: %s" % line, flush=True)
        print("cell: EXIT %d — refused at stage %s; nothing was measured"
              % (exc.code, exc.stage), flush=True)
        if args.handoff_unit:
            try:
                write_handoff(args.handoff_unit, "failed",
                              [exc.stage], {"command_or_count": line, "commands": []},
                              blocker=exc.message)
            except OSError:
                pass
        # A refusal PUBlishes what it spawned; the strictness lives in the rule
        # (runner_launch == 0, every diagnostic spawn declared with its phase).
        spawn_doc = SPAWNS.as_dict()
        # The verdict is RECOMPUTED and, when a tripwire is mounted, held against the
        # raw count -- a record may not certify itself by setting validation.ok.
        observed_spawns = _observed_spawns()
        spawn_verdict = spawn_record.validate_refusal(
            spawn_doc, exc.code, observed=observed_spawns)
        print("cell: spawns runner_launch=%d preflight_self_check=%d declared=%d "
              "undeclared=%d observed=%r record=%s"
              % (spawn_doc["runner_launch"], spawn_doc["preflight_self_check"],
                 spawn_doc["declared"], spawn_doc["undeclared"], observed_spawns,
                 "ok" if spawn_verdict["ok"]
                 else "; ".join(spawn_verdict["failures"])), flush=True)
        try:
            refusal_path = os.path.join(
                args.out_dir, "cell-%s-%s.refusal.json" % (args.arm, stamp))
            # ONE record shape (D6 + D5). This used to write a FIXED key list, which
            # dropped the `instrumentation` block that `SpawnRecord.as_dict()` emits --
            # so the on-disk refusal failed the very check the in-process verdict passed.
            # The refusal document now starts FROM the recorder's dict (spawns, counts,
            # instrumentation, and the tree binding) and adds the refusal's own facts;
            # there is no second implementation of the record shape to drift.
            refusal_doc = dict(spawn_doc)
            refusal_doc.update({
                "unit": "PREFLIGHT-SPAWN-DECLARE", "arm": args.arm,
                "stamp": stamp, "exit": exc.code, "stage": exc.stage,
                "message": exc.message, "command": " ".join(sys.argv),
                "classification": spawn_doc["rule"],
                "observed": observed_spawns, "validation": spawn_verdict})
            with open(refusal_path, "w", encoding="utf-8") as fh:
                json.dump(refusal_doc, fh, indent=1, sort_keys=True)
                fh.write("\n")
        except OSError:
            pass
        return exc.code

    except Exception:
        # Code 1 is DECLARED (exit_codes.EXIT_INTERNAL), not a shrug. An unclassified
        # exception must still NAME the run and keep its traceback, or the code tells a
        # reader only "something crashed" -- which is what an undeclared 1 used to mean.
        import traceback
        _a = locals().get("args")
        ident = "arm=%s fixture=%s out_dir=%s" % tuple(
            getattr(_a, k, "?") for k in ("arm", "fixture", "out_dir"))
        print("cell: INTERNAL ERROR %s -- an exception the conductor did not classify; "
              "the traceback below is this run's evidence" % ident,
              file=sys.stderr, flush=True)
        traceback.print_exc()
        print("cell: EXIT 1 -- internal error (%s); a harness defect, not a measurement"
              % ident, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
