"""GRID-STAMP-WIRING guard: a finished cell is STAMPED, and an unstamped one stops the grid.

Why this file exists
--------------------
`analyze_stats.py:749` is

    excluded = analyses is not None and len(analyses) == 0

so a missing `usable_for` key is False and the cell is INCLUDED in every comparison
(`analyze_stats.py:1753` prints `usable_for unstamped ... (included)`). `cell.py` is
frozen, so the writer lives beside the consumer:
`analyze_stats.write_cell_manifest_usable_for` (`:777`). RUN-A-STAR-2 made stamping a
prose step; prose is not a mechanism. These tests make the launcher's stamp a
mechanism: complete cells carry `h1,h2,h3`, abandoned / zero-marker /
stop_reason-degenerate cells carry `[]` PLUS the condition, and the launcher refuses
to start the next cell when the previous manifest cannot show the key at all.
"""
import json
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, "experiments/ptr-engine/tools")
LAUNCHER = os.path.join(TOOLS, "run_a_star.py")
MEASURE = os.path.join(REPO, "experiments/ptr-engine/measure")

sys.path.insert(0, TOOLS)
import run_a_star  # noqa: E402  (path set up above)


def _fixture(tmp_path, arm="pointer-stable", **manifest_extra):
    rows = tmp_path / "rows-cell-fixture.jsonl"
    rows.write_text('{"kind":"turn","turn":1,"stop_reason":"stop"}\n')
    man = tmp_path / "cell-fixture.json"
    man.write_text(json.dumps(dict({"rows_path": str(rows), "arm": arm},
                                   **manifest_extra), indent=1))
    return rows, man


def _rec(rows, man, arm="pointer-stable", **over):
    rec = {"cell": 1, "arm": arm, "rep": 1, "rc": 0, "turns": 20,
           "rows_file": str(rows), "manifest_path": str(man),
           "stats": {"turn_rows": 20,
                     "markers": {"evicted_turns": 0, "digest_rows": 0,
                                 "lease_ge2_turns": 0},
                     "degenerate_stop_turns": 0}}
    rec.update(over)
    return rec


def test_complete_cell_stamped_with_declared_value(tmp_path):
    """A complete cell's manifest carries the declared value, h1,h2,h3, with a reason."""
    rows, man = _fixture(tmp_path)
    rec = _rec(rows, man)
    out = run_a_star.stamp_cell(rec)
    stamped = json.loads(man.read_text())
    assert stamped["usable_for"] == ["h1", "h2", "h3"]
    assert out["usable_for"] == ["h1", "h2", "h3"]
    assert stamped["usable_for_reason"].startswith("complete:")
    assert "turn rows" in stamped["usable_for_reason"]


def test_abandoned_cell_is_stamped_empty_with_reason(tmp_path):
    """An abandoned cell gets [] AND a reason naming the condition (not a bare [])."""
    rows, man = _fixture(tmp_path)
    rec = _rec(rows, man, rc=9)
    run_a_star.stamp_cell(rec)
    stamped = json.loads(man.read_text())
    assert stamped["usable_for"] == []
    assert "abandoned" in stamped["usable_for_reason"]
    assert "rc=9" in stamped["usable_for_reason"]


def test_zero_marker_cell_is_stamped_empty_with_reason(tmp_path):
    """A zero-marker cell (arm requires a mechanism marker) is excluded with its cause."""
    rows, man = _fixture(tmp_path, arm="transcript-grow")
    rec = _rec(rows, man, arm="transcript-grow")
    run_a_star.stamp_cell(rec)
    stamped = json.loads(man.read_text())
    assert stamped["usable_for"] == []
    assert "zero-marker" in stamped["usable_for_reason"]
    assert "evicted_turns=0" in stamped["usable_for_reason"]


def test_stop_reason_degenerate_cell_is_stamped_empty_with_reason(tmp_path):
    """A stop_reason-degenerate cell is excluded, and the reason says which rule fired."""
    rows, man = _fixture(tmp_path)
    rec = _rec(rows, man)
    rec["stats"]["degenerate_stop_turns"] = 2
    run_a_star.stamp_cell(rec)
    stamped = json.loads(man.read_text())
    assert stamped["usable_for"] == []
    assert "stop_reason-degenerate" in stamped["usable_for_reason"]


def test_missing_key_makes_launcher_refuse_next_cell(tmp_path, capsys):
    """No `usable_for` key on the previous manifest -> SystemExit 4 naming the path."""
    rows, man = _fixture(tmp_path)  # deliberately unstamped
    rec = _rec(rows, man)
    with pytest.raises(SystemExit) as excinfo:
        run_a_star.check_previous_stamp(rec, 2)
    assert excinfo.value.code == run_a_star.EXIT_UNSTAMPED_CELL == 4
    err = capsys.readouterr().err
    assert str(man) in err
    assert "usable_for" in err
    assert "cell 2" in err


def test_stamped_previous_cell_is_not_refused(tmp_path):
    """Once the stamp is on disk the next cell is allowed through."""
    rows, man = _fixture(tmp_path)
    rec = _rec(rows, man)
    run_a_star.stamp_cell(rec)
    assert run_a_star.check_previous_stamp(rec, 2) is None


def test_stamp_is_the_analyzer_helper_not_reimplemented():
    """The launcher IMPORTS the writer; it constructs no `usable_for` field itself."""
    src = open(LAUNCHER, encoding="utf-8").read()
    assert "write_cell_manifest_usable_for(" in src
    assert "import analyze_stats" in src
    # No local construction of the manifest field: only reads (`"usable_for" in man`).
    assert 'man["usable_for"] =' not in src
    assert "usable_for_reason\"] =" not in src
    assert "['usable_for'] =" not in src


def test_stamp_call_present_red_green():
    """RED if the run_cell stamp call is removed; GREEN with it in place."""
    src = open(LAUNCHER, encoding="utf-8").read()
    call = 'rec["usable_for_stamp"] = stamp_cell(rec)'
    assert call in src
    red = src.replace(call, "")
    assert call not in red  # the guard's red state is a real removal
    refused = 'check_previous_stamp(results[-1], n)'
    assert refused in src
    assert refused not in src.replace(refused, "")


def test_dry_run_sends_zero_requests(monkeypatch, capsys):
    """The dry-run branch starts no cell process and reports requests=0."""
    calls = []

    def fake_run_cell(arm, rep, n, tools="", budget=108, hypothesis="H2",
                      dry_run=False, turns=48, max_wall=2880):
        calls.append((n, dry_run))
        return {"cell": n, "arm": arm, "rep": rep, "rc": 0, "dur_s": 0.0,
                "gates": ["dry-run G1 ok"], "would_refuse": [], "stats": {},
                "new_files": [], "rows_file": None}

    monkeypatch.setattr(run_a_star, "run_cell", fake_run_cell)
    monkeypatch.setattr(sys, "argv", ["run_a_star.py", "--dry-run", "--cell", "1"])
    rc = run_a_star.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert calls == [(1, True)]
    assert "requests=0" in out


def test_real_dry_run_creates_no_rows(monkeypatch):
    """A real --dry-run invocation writes no rows, whatever the pin record says."""
    before = {n for n in os.listdir(MEASURE)
              if n.startswith("rows-") and n.endswith(".jsonl")}
    proc = subprocess.run([sys.executable, LAUNCHER, "--dry-run", "--cell", "1"],
                          cwd=REPO, capture_output=True, text=True, timeout=300)
    after = {n for n in os.listdir(MEASURE)
             if n.startswith("rows-") and n.endswith(".jsonl")}
    assert after == before
    assert proc.returncode in (0, 1)
    # Either the preview ran (requests=0) or the frozen pin record refused the
    # launch before any request; both are zero-request outcomes. A SystemExit
    # message lands on stderr, so both streams are inspected.
    seen = proc.stdout + proc.stderr
    assert "requests=0" in seen or "HARNESS-PIN record disagrees" in seen
