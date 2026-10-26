"""Guard: the operator brief must keep re-deriving from the cells it cites.

Added by unit SERVING-BRIEF. ``papers/context-cache/SERVING-BRIEF.md`` is a synthesis, so
its only defence against drift is that every figure is regenerated from a measurement cell
by ``papers/context-cache/serving_brief.py``.  ``--check`` re-computes each claim with
``recompute.FUNCS`` (and the row- and artefact-backed items from their cells), compares to
``recompute.EXPECTED`` inside ``recompute.TOLERANCE``, re-hashes the pinned row files, and
re-parses the two generated tables plus every prose number against the ledger.

The red/green is the point: edit any EXPECTED value, any cell row, or any figure inside the
brief's generated tables, and ``--check`` must fail with the item named.

No live request is made and nothing is written: ``--check`` is read-only.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "papers" / "context-cache" / "serving_brief.py"
LEDGER = ROOT / "state" / "serving-brief.json"
BRIEF = ROOT / "papers" / "context-cache" / "SERVING-BRIEF.md"


def test_brief_recomputes_from_cells() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SERVING-BRIEF CHECK PASS" in proc.stdout


def test_ledger_shape() -> None:
    ledger = json.loads(LEDGER.read_text())
    items = ledger["items"]
    assert len(items) == 19
    assert [it["id"] for it in items] == [f"S{i:02d}" for i in range(1, 20)]
    for it in items:
        # every item names where its number came from and how it re-derives
        assert it["cell"]
        assert it["source"]
        assert it["value"]
        assert it["measured"]


def test_brief_carries_both_generated_tables() -> None:
    text = BRIEF.read_text()
    for marker in ("SERVING-BRIEF NUMBERS", "SERVING-BRIEF MATRIX"):
        assert f"<!-- BEGIN {marker} -->" in text
        assert f"<!-- END {marker} -->" in text
    # the tables are generated, not hand-pasted: a spot check of one row per writer
    assert "| S01 |" in text
    assert "| S02 | occamy-1.0 (MoE) |" in text
