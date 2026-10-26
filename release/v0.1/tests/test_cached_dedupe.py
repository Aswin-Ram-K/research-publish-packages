"""Red/green guard for tools/audit/cached_dedupe.py.

Three things are pinned, and the third is the point of the whole card:

  1. GREEN  the reproducer fires on the known-bad fixture
            cells/PROMPT-O1/rows.pre-correction.jsonl -> arm R fires 39/71 rows.
  2. RED    the clean control is silent
            cells/R2-P1-O1/rows.jsonl -> arm R, 0 fires.
  3. RED    the signature is NOT discriminating: it fires just as hard on
            cells/GROUND-TRUTH-PROMPT/rows.jsonl, a fresh independent re-measurement
            (37/69), and on other full-resend R arms (PROMPT-O2-EXTRA, R2-P1-O2, 39/71).
            A test that asserted silence there would be asserting a falsehood, so the
            guard asserts the OPPOSITE: pattern fires are never verdict-bearing.

Deliberate-failure run (proves the green is load-bearing):

    sed -i 's/^BAND_LO_QUANTA = 0.9/BAND_LO_QUANTA = 5.0/' tools/audit/cached_dedupe.py
    .venv/bin/python -m pytest tests/test_cached_dedupe.py -q     # MUST fail
    .venv/bin/python -m pytest tests/test_cached_dedupe.py -q     # restore, green

Read-only: every fixture is opened for reading; nothing is written.
"""
import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "audit"))

import cached_dedupe as cd  # noqa: E402

CELLS = os.path.join(ROOT, "experiments", "context-cache", "cells")
O1 = os.path.join(CELLS, "PROMPT-O1")


def check(path, arm="R"):
    series, unavail = cd.load_arm(path, arm)
    return cd.judge(series, [])


# --------------------------------------------------------------- 1. GREEN: it fires
def test_reproducer_fires_on_known_bad_fixture():
    res = check(os.path.join(O1, "rows.pre-correction.jsonl"))
    assert res["rows"] == 71
    assert res["pattern_fires"] == 39, f"expected 39 fires, got {res['pattern_fires']}"
    assert res["rate"] > 0.5
    turns = [f["turn"] for f in res["first_three"]]
    assert turns == [5, 6, 8], turns
    # the two-turn 736/755 spike the card describes
    assert res["first_three"][0] == {"turn": 5, "prompt": 1824, "cached": 1088, "gap": 736,
                                     "test": "C1_PATTERN", "cached_repeats_neighbour": True}
    assert res["first_three"][1]["gap"] == 755 and res["first_three"][1]["cached"] == 1408
    # baseline ~ one sawtooth gap, quantum = the 64-block advance
    assert 370 <= res["baseline_gap"] <= 400
    assert res["cache_quantum"] in (320, 384)


# --------------------------------------------------------------- 2. RED: it is silent
def test_silent_on_clean_control():
    res = check(os.path.join(CELLS, "R2-P1-O1", "rows.jsonl"))
    assert res["pattern_fires"] == 0, res["first_three"]
    assert res["impossible_fires"] == 0
    assert res["class"] == "clean"
    assert res["arm_quantum"] == 64


# ------------------------------------- 3. RED: the same signature fires on ground truth
def test_signature_is_not_discriminating():
    gt = check(os.path.join(CELLS, "GROUND-TRUTH-PROMPT", "rows.jsonl"))
    assert gt["pattern_fires"] >= 35, gt["pattern_fires"]
    # ...therefore a pattern-only verdict may never be `corrupt`
    assert gt["class"] != "corrupt"
    for cell in ("PROMPT-O2-EXTRA", "R2-P1-O2"):
        other = check(os.path.join(CELLS, cell, "rows.jsonl"))
        assert other["pattern_fires"] >= 35, (cell, other["pattern_fires"])


# ------------------------------------------- the fabricated artefact is impossible
def test_withdrawn_repair_is_physically_impossible():
    res = check(os.path.join(O1, "rows.repaired-DO-NOT-USE.jsonl"))
    assert res["arm_quantum"] is None, "a mixed grid must not resolve to a quantum"
    assert res["off_grid_vs_64"] == 40
    assert res["class"] == "corrupt" and "S1_GRID_INCOHERENT" in res["reasons"]
    # ...and each fabricated value IS "prompt - R2-P1-O1's gap", turn for turn: arithmetic,
    # not a measurement. This is the transplant, asserted directly instead of by sequence
    # similarity (R2-P1-O1 has two 'unavailable' rows, so the sequences cannot align index-wise).
    rep, _ = cd.load_arm(os.path.join(O1, "rows.repaired-DO-NOT-USE.jsonl"), "R")
    r2, _ = cd.load_arm(os.path.join(CELLS, "R2-P1-O1", "rows.jsonl"), "R")
    gap_r2 = {t: p - c for t, p, c in r2}
    checked = 0
    for turn, prompt, cached in rep:
        if turn in gap_r2 and cached % 64 != 0:
            assert cached == prompt - gap_r2[turn], (turn, cached, prompt - gap_r2[turn])
            checked += 1
    assert checked >= 30, checked  # 40 off-grid minus the turns R2-P1-O1 lacks


def test_rows_jsonl_is_byte_identical_to_pre_correction():
    """The card's 'repaired rows.jsonl' control does not exist: RESTORE-O1 restored it."""
    a = hashlib.sha256(open(os.path.join(O1, "rows.jsonl"), "rb").read()).hexdigest()
    b = hashlib.sha256(open(os.path.join(O1, "rows.pre-correction.jsonl"), "rb").read()).hexdigest()
    assert a == b and a.startswith("dc0774d8ef7dc4dc")


# -------------------------------------------------------- red -> green on the guard
def test_red_green_synthetic_mutation(tmp_path):
    src = os.path.join(CELLS, "R2-P1-O1", "rows.jsonl")
    rows = [json.loads(l) for l in open(src) if l.strip()]
    clean = tmp_path / "clean.jsonl"
    clean.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert check(str(clean))["impossible_fires"] == 0

    bad = tmp_path / "bad.jsonl"
    bad.write_text("".join(
        json.dumps(dict(r, cached_tokens=r["prompt_tokens"] - 415)
                   if (str(r.get("arm")) == "R" and isinstance(r.get("prompt_tokens"), int)
                       and 5 <= r.get("turn", 0) <= 20) else r) + "\n" for r in rows))
    res = check(str(bad))
    assert res["class"] == "corrupt", res["reasons"]
    assert res["off_grid_vs_64"] >= 10
    assert res["impossible_detail"][0]["turn"] == 6  # turn 5 lands on-grid (1823-415=1408)
    assert res["impossible_detail"][0]["cached"] == 1747 and res["impossible_detail"][0]["cached"] % 64 != 0
    assert res["class"] == "corrupt"


def test_cli_json_mode_runs():
    assert cd.main(["--json"]) == 0
