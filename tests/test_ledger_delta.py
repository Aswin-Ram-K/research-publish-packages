"""Tests for experiments/ptr-engine/tools/ledger_delta.py.

Unit LEDGER-GRID-BASELINE (2026-10-26) wrote the first four cases; unit
LEDGER-BASELINE-REPIN (2026-10-26) added the v2-default, explicit-v1, and
rows-inventory-guard cases.

Both directions are exercised:
  * green -- a baseline whose spend is consistent with its raw count, and a ledger
    that grew by exactly the delta, must exit 0 and print the closing arithmetic;
  * red   -- a baseline that was EDITED (spent raised by +5 while requests_raw was
    left alone) must exit 1 and name the discrepancy.  An edited baseline is the
    exact failure mode this unit exists to prevent: it would otherwise yield a
    plausible-looking delta that is 5 requests too small.

The rows guard is exercised both ways: a line count that moved with no sha change
(red, refused) and a genuine append that moved both (green, accepted).

Offline: no network, no inference; only local temp files.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "experiments", "ptr-engine", "tools", "ledger_delta.py")
FROZEN = os.path.join(ROOT, "experiments", "ptr-engine", "measure", "LEDGER-GRID-BASELINE.json")
FROZEN_V2 = os.path.join(ROOT, "experiments", "ptr-engine", "measure", "LEDGER-GRID-BASELINE-2.json")
REAL_LEDGER = os.path.join(ROOT, "experiments", "ptr-engine", "measure", "REQUEST-LEDGER.json")


def ledger_doc(spent: int, raw: int, remaining: int) -> dict:
    return {
        "unit": "REQUEST-LEDGER",
        "requests": raw,
        "requests_raw": raw,
        "requests_deduplicated": raw - 30,
        "remaining": remaining,
        "remaining_raw": remaining,
        "remaining_deduplicated": remaining + 30,
        "duplicate_excess": 30,
        "deduction_rule_sound": False,
        "budget": {"cap": 4320, "reserve": 0, "spent": spent, "spent_raw": spent, "remaining": remaining,
                   "remaining_raw": remaining, "within_budget": True},
        "diagnostic": {"deducted": False, "requests_deduplicated": raw - 30,
                       "duplicate_excess": 30, "remaining_deduplicated": remaining + 30},
    }


def baseline_doc(spent: int, raw: int, remaining: int) -> dict:
    doc = ledger_doc(spent, raw, remaining)
    doc.update({"unit": "LEDGER-GRID-BASELINE", "kind": "frozen_request_ledger_baseline",
                "label": "pre_grid", "captured_utc": "2026-10-26T18:24:48Z"})
    return doc


def with_inventory(doc: dict, entries: list) -> dict:
    doc = dict(doc)
    doc["rows_inventory" if doc.get("unit") != "REQUEST-LEDGER" else "per_file"] = entries
    return doc


def rows_entry(name: str, rows: int, sha: str) -> dict:
    return {"file": name, "rows": rows, "sha256": sha}


def write(path, doc) -> str:
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return str(path)


def run(baseline: str, ledger: str):
    return subprocess.run([sys.executable, TOOL, "--baseline", baseline, "--ledger", ledger],
                          capture_output=True, text=True, timeout=120)


def test_green_delta_closes(tmp_path):
    base = write(tmp_path / "baseline.json", baseline_doc(1101, 1101, 3219))
    cur = write(tmp_path / "ledger.json", ledger_doc(1761, 1761, 2559))
    r = run(base, cur)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "spent_before            1101" in r.stdout
    assert "spent_now               1761" in r.stdout
    assert "delta                   660" in r.stdout
    assert "remaining_now           2559" in r.stdout
    assert "remaining_before_minus_delta  2559" in r.stdout
    assert "deficit                 none" in r.stdout
    assert "OK" in r.stdout


def test_red_edited_baseline_exits_1(tmp_path):
    """RED CASE: baseline spent edited by +5, raw count untouched -> must exit 1."""
    base = write(tmp_path / "baseline.json", baseline_doc(1106, 1101, 3219))
    cur = write(tmp_path / "ledger.json", ledger_doc(1101, 1101, 3219))
    r = run(base, cur)
    assert r.returncode == 1, "an edited baseline must not be accepted: " + r.stdout
    assert "discrepancy" in r.stdout
    assert "baseline is internally inconsistent" in r.stdout
    assert "FAIL" in r.stdout


def test_red_remaining_drift_exits_1(tmp_path):
    base = write(tmp_path / "baseline.json", baseline_doc(1101, 1101, 3219))
    cur = write(tmp_path / "ledger.json", ledger_doc(1761, 1761, 2500))  # 59 too few remaining
    r = run(base, cur)
    assert r.returncode == 1, r.stdout
    assert "remaining_raw_now" in r.stdout
    assert "FAIL" in r.stdout


def test_never_deducts_deduplicated(tmp_path):
    """The de-duplicated figure must never be used: spend stays raw."""
    base = write(tmp_path / "baseline.json", baseline_doc(1101, 1101, 3219))
    cur = write(tmp_path / "ledger.json", ledger_doc(1761, 1761, 2559))
    r = run(base, cur)
    assert "diagnostic_deduplicated 1071" in r.stdout
    assert "NOT subtracted" in r.stdout
    assert "delta                   660" in r.stdout  # not 630


# --- rows-inventory guard (unit LEDGER-BASELINE-REPIN) ---------------------

def test_red_rows_count_moved_without_sha_change(tmp_path):
    """RED: a rows file gained 12 lines but its sha256 is unchanged -> refuse."""
    base = write(tmp_path / "baseline.json",
                 with_inventory(baseline_doc(1128, 1128, 3192), [rows_entry("rows-x.jsonl", 27, "a" * 64)]))
    cur = write(tmp_path / "ledger.json",
                with_inventory(ledger_doc(1128, 1128, 3192), [rows_entry("rows-x.jsonl", 39, "a" * 64)]))
    r = run(base, cur)
    assert r.returncode == 1, r.stdout
    assert "rows guard" in r.stdout
    assert "line count changed 27 -> 39 with NO sha change" in r.stdout
    assert "FAIL" in r.stdout


def test_red_rows_rewritten_in_place(tmp_path):
    """RED: sha moved while the line count did not -> rows files are append-only."""
    base = write(tmp_path / "baseline.json",
                 with_inventory(baseline_doc(1128, 1128, 3192), [rows_entry("rows-x.jsonl", 27, "a" * 64)]))
    cur = write(tmp_path / "ledger.json",
                with_inventory(ledger_doc(1128, 1128, 3192), [rows_entry("rows-x.jsonl", 27, "b" * 64)]))
    r = run(base, cur)
    assert r.returncode == 1, r.stdout
    assert "append-only" in r.stdout


def test_green_rows_appended_with_sha_change(tmp_path):
    """GREEN: a genuine append moves both count and sha, and new rows files are allowed."""
    base = write(tmp_path / "baseline.json",
                 with_inventory(baseline_doc(1128, 1128, 3192), [rows_entry("rows-x.jsonl", 27, "a" * 64)]))
    cur = write(tmp_path / "ledger.json",
                with_inventory(ledger_doc(1176, 1176, 3144),
                               [rows_entry("rows-x.jsonl", 27, "a" * 64),
                                rows_entry("rows-runA-1.jsonl", 48, "c" * 64)]))
    r = run(base, cur)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "rows_guard              checked 1 rows file(s); new since baseline: 1" in r.stdout
    assert "rows_guard_new          rows-runA-1.jsonl" in r.stdout
    assert "delta                   48" in r.stdout


# --- shipped baselines ----------------------------------------------------

@pytest.mark.skipif(not (os.path.exists(FROZEN_V2) and os.path.exists(REAL_LEDGER)),
                    reason="v2 baseline or live ledger absent")
def test_default_baseline_is_v2_and_delta_zero():
    """A bare invocation must quote v2, and nothing has run since the rebuild: delta 0."""
    r = subprocess.run([sys.executable, TOOL], capture_output=True, text=True, timeout=120,
                       cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "LEDGER-GRID-BASELINE-2.json" in r.stdout
    assert "spent_before            1128" in r.stdout
    assert "delta                   0" in r.stdout
    assert "deficit                 none" in r.stdout


@pytest.mark.skipif(not (os.path.exists(FROZEN) and os.path.exists(REAL_LEDGER)),
                    reason="frozen baseline or live ledger absent")
def test_explicit_v1_still_works():
    """v1 is a dated record: asking for it explicitly still measures against 1,101 (delta 27)."""
    r = subprocess.run([sys.executable, TOOL, "--baseline", FROZEN, "--ledger", REAL_LEDGER],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "spent_before            1101" in r.stdout
    assert "delta                   27" in r.stdout
    assert "deficit                 none" in r.stdout
