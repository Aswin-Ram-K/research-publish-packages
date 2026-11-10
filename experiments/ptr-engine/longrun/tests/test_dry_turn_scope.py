#!/usr/bin/env python3
"""test_dry_turn_scope.py - the dry-run preview and the live cell scope the SAME turns.

WHY THIS EXISTS (unit RUN-DRY-TURN-SCOPE, measured).  `--max-turns` was honoured by the
live path and ignored by the preview:

  * run_longrun.py `run_cell` (the live loop):  `n_turns = int(fixture["N"])` then
    `if max_turns > 0: n_turns = min(n_turns, max_turns)` -- a 12-turn cell runs 12 turns;
  * run_longrun.py `run_dry` (the preview):     `for t in range(1, int(fixture["N"]) + 1)`
    and `turns = int(fixture["N"]) * c["reps"]` -- the same cell was previewed at 48.

Measured on `tasks-v6/LR-01.v8.json` before the fix: `--dry-run` gave
`would_send_total=48`, and `--dry-run --max-turns 12` gave `would_send_total=48` too.
The cell's G2 gate prices `turns x 60 s`, so a 12-turn canary (720 s, inside the 900 s
canary wall) was priced at 2880 s and refused -- a preview that ignores the turn limit
makes the shortened cell impossible to gate.

WHAT IS PINNED HERE (3 independent assertions, so one bug cannot pass by moving another)
  (a) end-to-end: a real offline `--dry-run` subprocess prints `turn_requests` equal to
      min(fixture N, --max-turns), for max_turns in {1, 12, 24, 48, 96}; and
      `cell_total == turn_requests + digest_requests` with `would_send_total` their sum;
  (b) `turn_requests` also equals the LIVE price `projected_requests(cfg, fixture, arm)`
      -- the function `run_cell` reads for its budget (`budget = projected_requests(...)`),
      so the preview and the live cell cannot price different cells;
  (c) a SOURCE guard: `run_dry`'s own text loops `range(1, n_turns + 1)` and its count is
      `n_turns * c["reps"]` -- no `fixture["N"]` loop bound left in the preview. This is
      the assertion that goes red if the preview reverts to the fixture's N even when
      `fixture["N"]` happens to equal the cell's turns.

A full cell must also stay byte-identical: for max_turns in {0 (no flag), 48, 96} the
REQUEST-COUNT line keeps its exact pre-fix shape `(N=48 x reps=1)` -- a `--max-turns`
suffix appears only when the cell is genuinely shortened.

RED->GREEN (how to prove it can fail): point `RUNNER_UNDER_TEST` at a copy of the runner
whose `run_dry` loop was reverted to `range(1, int(fixture["N"]) + 1)` and whose count is
`int(fixture["N"]) * c["reps"]`; cases (a), (b) and (c) then fail. See the unit journal.

Every case is OFFLINE: `--dry-run` only, no request, no socket, no --base-url.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
PTR_ENGINE = os.path.dirname(LONGRUN)
ROOT = os.path.dirname(os.path.dirname(PTR_ENGINE))

# RUNNER_UNDER_TEST lets a red run point the same assertions at a mutated copy.
RUNNER = os.environ.get("RUNNER_UNDER_TEST") or os.path.join(LONGRUN, "run_longrun.py")
FIXTURE_ABS = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")
FIXTURE_ARGV = os.path.relpath(FIXTURE_ABS, ROOT)
ARM = "pointer-stable"
PY = sys.executable

if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import run_longrun as R  # noqa: E402

# `  pointer-stable      turn_requests=12 (N=48 --max-turns=12 x reps=1)  digest_requests=0  cell_total=12`
COUNT_RE = re.compile(
    r"^\s+(?P<arm>\S+)\s+turn_requests=(?P<turns>\d+) \((?P<scope>[^)]*)\)\s+"
    r"digest_requests=(?P<digest>\d+)\s+cell_total=(?P<cell>\d+)\s*$", re.M)
TOTAL_RE = re.compile(r"would_send_total=(\d+)\s*$", re.M)


class _Cfg:
    """The smallest cfg `projected_requests` / `cell_turns` read."""

    def __init__(self, max_turns=0, tools=""):
        self.max_turns = max_turns
        self.tools = tools
        self.fetch_rounds_per_turn = 3
        self.fetch_rounds_per_arm = 48


def _fixture() -> dict:
    with open(FIXTURE_ABS, encoding="utf-8") as fh:
        return json.load(fh)


def _dry_run(tmpdir, extra_args=()):
    """Run the runner's real offline dry-run and return its stdout."""
    cmd = [PY, RUNNER, "--fixture", FIXTURE_ARGV, "--arm", ARM, "--reps", "1",
           "--dry-run", "--manifest-dir", os.path.join(tmpdir, "manifests"),
           "--preview-root", os.path.join(tmpdir, "previews"),
           "--temperature", "0"]
    cmd += list(extra_args)
    env = dict(os.environ)
    # a copy under RUNNER_UNDER_TEST still needs the sibling modules to import
    env["PYTHONPATH"] = LONGRUN + (os.pathsep + env["PYTHONPATH"]
                                   if env.get("PYTHONPATH") else "")
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, (
        "dry-run exited %d\nstdout:\n%s\nstderr:\n%s"
        % (proc.returncode, proc.stdout, proc.stderr))
    return proc.stdout


def _counts(stdout):
    rows = COUNT_RE.findall(stdout)
    assert len(rows) == 1, "expected exactly one arm's request-count line, got %r" % (rows,)
    arm, turns, scope, digest, cell = rows[0]
    total = TOTAL_RE.search(stdout)
    assert total is not None, "no would_send_total line in:\n%s" % stdout
    return {"arm": arm, "turns": int(turns), "scope": scope,
            "digest": int(digest), "cell": int(cell), "total": int(total.group(1))}


@pytest.mark.parametrize("max_turns", [1, 12, 24, 48, 96])
def test_dry_run_projects_the_cells_turns(max_turns):
    """(a) end-to-end: the preview counts the turns the cell would run, not the fixture's."""
    fixture = _fixture()
    expected = min(int(fixture["N"]), max_turns)
    with tempfile.TemporaryDirectory() as tmp:
        got = _counts(_dry_run(tmp, ("--max-turns", str(max_turns))))

    assert got["arm"] == ARM
    assert got["turns"] == expected, (
        "dry run projected %d turns for --max-turns %d (fixture N=%d): the preview is not "
        "the cell" % (got["turns"], max_turns, fixture["N"]))
    assert got["cell"] == got["turns"] + got["digest"]
    assert got["total"] == got["cell"]


@pytest.mark.parametrize("max_turns", [1, 12, 24, 48, 96])
def test_dry_run_agrees_with_the_live_price(max_turns):
    """(b) the preview's turn count equals the LIVE budget function `run_cell` reads.

    `run_cell` does `budget = projected_requests(cfg, fixture, arm)`; for this arm the
    projection is turns only (no digests, tools off), so that budget IS the live n_turns.
    """
    fixture = _fixture()
    cfg = _Cfg(max_turns=max_turns)
    # digests enter the projection only for `transcript-compact`, and tools are off here,
    # so `projected_requests` for THIS arm is exactly the live turn count.
    assert ARM != "transcript-compact"
    assert R.tools_enabled(cfg) is False, "the projection must be turns only for this arm"
    live = R.projected_requests(cfg, fixture, ARM)
    assert live == R.cell_turns(cfg, fixture) == min(int(fixture["N"]), max_turns)

    with tempfile.TemporaryDirectory() as tmp:
        got = _counts(_dry_run(tmp, ("--max-turns", str(max_turns))))
    assert got["turns"] == live, (
        "dry run says %d turns, the live cell prices %d" % (got["turns"], live))


def test_run_dry_source_no_longer_loops_over_the_fixtures_n():
    """(c) source guard: the preview's loop bound and count are the cell's turns."""
    with open(RUNNER, encoding="utf-8") as fh:
        src = fh.read()
    body = src.split("def run_dry(", 1)[1].split("\ndef run_cell(", 1)[0]
    assert "for t in range(1, n_turns + 1):" in body, (
        "run_dry no longer loops over n_turns")
    assert 'range(1, int(fixture["N"]) + 1)' not in body, (
        "run_dry went back to the fixture's N as its loop bound")
    assert 'turns = n_turns * c["reps"]' in body, "run_dry no longer counts n_turns"
    assert 'int(fixture["N"]) * c["reps"]' not in body, (
        "run_dry went back to the fixture's N as its count")


@pytest.mark.parametrize("max_turns,argv", [(0, ()), (48, ("--max-turns", "48")),
                                            (96, ("--max-turns", "96"))])
def test_full_cell_pricing_block_is_byte_identical(max_turns, argv):
    """A full cell (no flag, or --max-turns >= N) keeps the exact pre-fix line shape."""
    fixture = _fixture()
    with tempfile.TemporaryDirectory() as tmp:
        got = _counts(_dry_run(tmp, argv))
    assert got["turns"] == int(fixture["N"]) == 48
    assert got["cell"] == 48
    assert got["total"] == 48
    assert got["scope"] == "N=48 x reps=1", (
        "the full-cell request-count line changed shape: %r" % (got["scope"],))
