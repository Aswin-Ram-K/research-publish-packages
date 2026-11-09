"""test_row_count_guard_gen7.py - F1-GUARD: row-count guard is generation-aware.

gen-7 inputs assert hard on a bad row count; labelled legacy (gen-6 and earlier)
inputs are LEGACY-NONCONFORMING (printed, not raised).
"""
from __future__ import annotations

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
for path in (LONGRUN, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

import analyze_stats  # noqa: E402


def _bad_rows():
    # 3 rows where 2*2*2=8 expected -> bad count + non-unique keys
    return [
        {"arm": "a", "rep": 1, "cell": "c", "turn": 1, "generation": "gen-7"},
        {"arm": "a", "rep": 1, "cell": "c", "turn": 2, "generation": "gen-7"},
        {"arm": "a", "rep": 1, "cell": "c", "turn": 3, "generation": "gen-7"},
    ]


def test_gen7_bad_row_count_fires():
    rows = _bad_rows()
    try:
        analyze_stats.assert_row_count(rows, cells=2, turns=2, reps=2, generation="gen-7")
    except analyze_stats.RowCountAssertionError:
        return
    raise AssertionError("gen-7 guard did not fire on bad row count")


def test_legacy_bad_row_count_does_not_fire():
    rows = [{**r, "generation": "gen-6"} for r in _bad_rows()]
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        result = analyze_stats.assert_row_count(rows, cells=2, turns=2, reps=2,
                                                generation="gen-6")
    finally:
        sys.stdout = old
    assert result is False
    assert "LEGACY-NONCONFORMING" in buf.getvalue()
