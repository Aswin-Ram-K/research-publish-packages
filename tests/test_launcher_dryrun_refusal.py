"""LAUNCH-CANARY-WALL — a dry run must not report green while a gate would refuse.

Two defects, both proven in orchestration/handoffs/CANARY-GATE-DRYRUN.json:

1. the canary's ``--max-wall`` default (600 s) could not price its own projection
   (12 turns x 60.0 s = 720 s at the artefact-mode calibration), so G2 said
   ``WOULD-REFUSE`` and the live cell would have aborted at stage 3b/7;
2. ``run_a_star.py --dry-run`` computed ``refused`` from ``rc`` alone, and
   ``cell.py``'s dry run always exits 0 — by its own contract (cell.py:1964-1975:
   "exit 0 means the PREVIEW ran, not that the gates allow"). So the launcher printed
   ``refused=0`` and exited 0 for a launch that could never send request 1.

Everything here is a DRY RUN of the real binaries: no socket, no endpoint, no runner.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAUNCHER = os.path.join(ROOT, "experiments/ptr-engine/tools/run_a_star.py")
PY = sys.executable

# One grid cell, deliberately under-walled: G2 bills 48 turns x 60.0 s against
# --max-wall 60, so the gate refuses and nothing is sent.
BLOCKED = [PY, LAUNCHER, "--cell", "1", "--max-wall", "60", "--dry-run"]
# The same cell with the wall it needs: the gate allows, refused must be 0.
ALLOWED = [PY, LAUNCHER, "--cell", "1", "--max-wall", "2880", "--dry-run"]

# A gate verdict line, not cell.py's closing sentence that merely names the words.
VERDICT = re.compile(r"dry-run G[123] WOULD-REFUSE\b")
END_RE = re.compile(r"DRY END cells=(\d+) refused=(\d+) requests=(\d+) "
                    r"claim=(\S+) turns=(\d+) max_wall=(\S+)")


def _run(argv, launcher=LAUNCHER, cwd=ROOT):
    env = os.environ.copy()
    env.pop("CELL_RUNNER_PATH", None)
    # argv is [python, launcher, ...flags]; the launcher path is the only variable.
    return subprocess.run([argv[0], launcher] + argv[2:], cwd=cwd,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, env=env)


def _end(out):
    """The launcher's own closing tally — the line callers are asked to parse."""
    lines = [ln for ln in out.splitlines() if "DRY END" in ln]
    assert lines, "no DRY END line in launcher output:\n%s" % out[-3000:]
    m = END_RE.search(lines[-1])
    assert m, "unparseable DRY END line: %r" % lines[-1]
    return {"cells": int(m.group(1)), "refused": int(m.group(2)),
            "requests": int(m.group(3)), "claim": m.group(4),
            "turns": int(m.group(5)), "max_wall": float(m.group(6)),
            "line": lines[-1]}


def test_would_refuse_counts_and_exits_nonzero():
    """A gate's WOULD-REFUSE line is a refusal: it counts, and rc is non-zero."""
    p = _run(BLOCKED)
    assert VERDICT.search(p.stdout), (
        "the blocked vector did not produce a gate WOULD-REFUSE verdict — the test "
        "vector itself is stale, not the fix:\n%s" % p.stdout[-3000:])
    e = _end(p.stdout)
    assert e["refused"] == 1, "refused must count the refusing cell: %r" % e
    assert e["requests"] == 0, "a dry run sends nothing: %r" % e
    assert p.returncode != 0, (
        "launcher reported %d would-refuse cell(s) but exited 0: %r"
        % (e["refused"], e["line"]))


def test_allow_counts_zero_and_exits_zero():
    """The allow path stays quiet: refused=0 and rc 0 (no false positive)."""
    p = _run(ALLOWED)
    assert not VERDICT.search(p.stdout), p.stdout[-3000:]
    e = _end(p.stdout)
    assert e["refused"] == 0, "an allowed launch must not report a refusal: %r" % e
    assert p.returncode == 0, "allowed dry run must exit 0: %r" % e


def test_red_reverting_the_detection_reports_green_again(tmp_path):
    """red→green: put the old `bad += rc != 0` back and the blocked case goes green.

    The revert is applied to a COPY of the launcher (ROOT is absolute inside it, so
    the copy still prices the real cell.py). This is the defect itself, not a mock:
    the same blocked vector, the same real binary, the old one-line tally.
    """
    src = open(LAUNCHER, encoding="utf-8").read()
    fixed = '            bad += 1 if (rec["rc"] != 0 or refused) else 0'
    reverted = '            bad += rec["rc"] != 0'
    assert src.count(fixed) == 1, "the refusal tally is not where this test expects"
    copy = tmp_path / "run_a_star_reverted.py"
    copy.write_text(src.replace(fixed, reverted), encoding="utf-8")
    p = _run(BLOCKED, launcher=str(copy))
    e = _end(p.stdout)
    # RED: the gate still says WOULD-REFUSE, yet the reverted launcher reports green.
    assert VERDICT.search(p.stdout), p.stdout[-3000:]
    assert e["refused"] == 0, "reverted launcher unexpectedly counted: %r" % e
    assert p.returncode == 0, "reverted launcher unexpectedly exited non-zero: %r" % e


def test_canary_wall_default_clears_its_projection():
    """The default wall must price 12 turns x 60.0 s = 720 s; the grid keeps 2880."""
    src = open(LAUNCHER, encoding="utf-8").read()
    m = re.search(r"^CANARY_MAX_WALL = (\d+)$", src, re.M)
    assert m, "CANARY_MAX_WALL is not declared as a literal constant"
    assert int(m.group(1)) >= 720, (
        "canary default wall %s cannot price 12 x 60.0 s = 720 s"
        % m.group(1))
    assert re.search(r"a\.max_wall = 2880 if a\.max_wall is None", src), (
        "the grid's 2880 s default must stay untouched")
