#!/usr/bin/env python3
"""U14 red->green: mutate APPEND_NOTE so it rewrites one head node.

The guard under test is ``tests/test_context_append_note.py::
test_head_is_byte_identical_after_append_note``.  If that test can still pass
when the policy rewrites a head node, it proves nothing -- so this script
applies exactly that mutation to ``src/resextract/context/budget.py`` in place,
runs the test file (expect failures), restores the file, verifies its sha256 is
byte-identical to the pre-mutation state, and re-runs (expect all green).

Mutation: ``new_chain = [*chain, note]`` becomes a rebuild in which ``chain[1]``
gains a trailing space -- one rewritten head turn, everything else unchanged.
That is the smallest possible violation of "the head is never rewritten".

Offline only; no network.  No file outside this unit's declared write paths is
touched (``budget.py`` is one of them).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BUDGET = REPO / "src" / "resextract" / "context" / "budget.py"
BACKUP = HERE / "budget.py.premutation.bak"
TEST = "tests/test_context_append_note.py"

ANCHOR = "        new_chain = [*chain, note]\n"
MUTANT = """        _rewritten = list(chain)
        _rewritten[1] = StateNode.create(
            _rewritten[1].text + " ", _rewritten[1].kind, parent=_rewritten[0]
        )
        new_chain = [*_rewritten, note]
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pytest_summary() -> str:
    proc = subprocess.run(
        [str(REPO / ".venv" / "bin" / "python"), "-m", "pytest", TEST, "-q"],
        cwd=REPO,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else f"<no output; rc={proc.returncode}>"


def main() -> int:
    source = BUDGET.read_text(encoding="utf-8")
    if ANCHOR not in source:
        raise SystemExit(f"anchor not found in {BUDGET}; the branch changed shape")

    original_sha = sha256(BUDGET)
    shutil.copy2(BUDGET, BACKUP)
    print(f"budget.py sha256 before mutation: {original_sha}")
    print(f"green (unmutated): {pytest_summary()}")

    try:
        BUDGET.write_text(source.replace(ANCHOR, MUTANT, 1), encoding="utf-8")
        print(f"budget.py sha256 mutated      : {sha256(BUDGET)}")
        red = pytest_summary()
        print(f"red  (head-rewriting mutant)  : {red}")
    finally:
        BUDGET.write_text(source, encoding="utf-8")
        BACKUP.unlink(missing_ok=True)

    restored_sha = sha256(BUDGET)
    print(f"budget.py sha256 restored     : {restored_sha}")
    if restored_sha != original_sha:
        print("RESTORE MISMATCH -- budget.py is not byte-identical", file=sys.stderr)
        return 1

    green = pytest_summary()
    print(f"green (restored)              : {green}")
    if "failed" in red and "failed" not in green:
        print("verdict: RED->GREEN confirmed (guard fails when the head is rewritten)")
        return 0
    print("verdict: NOT CONFIRMED -- the mutant did not fail the guard", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
