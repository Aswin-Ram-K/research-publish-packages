#!/usr/bin/env python3
"""Tests for `tools/verify_tranche1.py` — the prereg's rules, green and shown red.

Every adjudicating rule gets two tests: one that the frozen rule produces the
pre-registered verdict, and one that REVERTS the rule and shows the first test's
assertion goes red. Synthetic rows live in /tmp only; nothing is written to `measure/`.

Run: python3 -m pytest experiments/ptr-engine/tests/test_verify_tranche1.py -q
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "tools", "verify_tranche1.py")
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

_spec = importlib.util.spec_from_file_location("verify_tranche1", TOOL)
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)


def _rules(**over):
    rules = copy.deepcopy(V.RULES)
    rules.update(over)
    return rules


def _case(name):
    base, cases = V.synthetic_cases()
    return cases[name]


# --- H1 disjoint ------------------------------------------------------------
def test_disjoint_p95_is_separated_lower():
    case = _case("disjoint")
    report = V.analyze(case["rows"], case["grade"])
    assert report["h1"]["comparison"]["verdict"] == "separated_lower"
    assert report["h1"]["per_arm"]["pointer-stable"]["n"] == 144


def test_disjoint_red_when_direction_reverted():
    case = _case("disjoint")
    report = V.analyze(case["rows"], case["grade"], _rules(DIRECTION="C_higher"))
    # the frozen assertion above would now be false: the rule is load-bearing
    assert report["h1"]["comparison"]["verdict"] == "separated_higher"


# --- H1 overlap -------------------------------------------------------------
def test_overlapping_intervals_return_overlap():
    case = _case("overlap")
    report = V.analyze(case["rows"], case["grade"])
    assert report["h1"]["comparison"]["verdict"] == "overlap"


def test_overlap_red_when_disjointness_rule_dropped():
    case = _case("overlap")
    report = V.analyze(case["rows"], case["grade"],
                       _rules(DIRECTION_STRICT_DISJOINT=False))
    assert report["h1"]["comparison"]["verdict"] != "overlap"


# --- H1 refusal floor -------------------------------------------------------
def test_below_floor_is_refused_at_60():
    case = _case("below_floor")
    report = V.analyze(case["rows"], case["grade"])
    assert report["h1"]["per_arm"]["pointer-stable"]["reason"] == "insufficient_n_floor"
    assert report["h1"]["comparison"]["verdict"] == "refused"
    assert report["h1"]["per_arm"]["pointer-stable"]["floor"] == 60


def test_floor_red_when_lowered_to_40():
    case = _case("below_floor")
    report = V.analyze(case["rows"], case["grade"], _rules(MIN_N_USABLE=40))
    # n=48 now clears the lowered floor, so the pre-registered reason changes: RED
    assert report["h1"]["per_arm"]["pointer-stable"]["reason"] != "insufficient_n_floor"


# --- TVS censoring ----------------------------------------------------------
def test_no_passing_checkpoint_censors_tvs():
    case = _case("censored_tvs")
    report = V.analyze(case["rows"], case["grade"])
    tvs = report["tvs"]["pointer-stable"]
    assert tvs["tvs"] is None and tvs["censored"] is True
    assert tvs["censor_kind"] == "no_verified_checkpoint"
    assert tvs["censored_at_turn"] == 48


def test_censoring_red_when_censored_is_zeroed():
    case = _case("censored_tvs")
    report = V.analyze(case["rows"], case["grade"], _rules(TVS_CENSOR_AS_ZERO=True))
    assert report["tvs"]["pointer-stable"]["censored"] is not True


# --- H3 turn_missing --------------------------------------------------------
def test_turn_missing_leaves_the_denominator():
    case = _case("turn_missing")
    report = V.analyze(case["rows"], case["grade"])
    arm = report["h3"]["per_arm"]["pointer-stable"]
    assert arm["missing_ids"] == ["cp.0.t06"]
    assert arm["accuracy"]["decidable"] == 1          # only the pass cell decides
    assert report["h3"]["verdict"] == "not_adjudicable"


def test_turn_missing_red_when_counted_as_fail():
    case = _case("turn_missing")
    report = V.analyze(case["rows"], case["grade"],
                       _rules(TURN_MISSING_COUNTS_AS_FAIL=True))
    arm = report["h3"]["per_arm"]["pointer-stable"]
    assert arm["missing_ids"] == [] and arm["accuracy"]["decidable"] == 2   # RED


# --- H2 both limbs ----------------------------------------------------------
def test_h2_split_is_reported_as_split_not_as_h2():
    case = _case("h2_split")
    report = V.analyze(case["rows"], case["grade"])
    assert report["h2"]["verdict"] == "h2_failed_split"
    assert report["h2"]["pass_inclusive"] is True and report["h2"]["pass_uncached"] is False


def test_h2_red_when_one_limb_is_picked():
    case = _case("h2_split")
    report = V.analyze(case["rows"], case["grade"], _rules(H2_REQUIRE_BOTH=False))
    assert report["h2"]["verdict"] == "h2_pass"      # the wrong answer, by the reverted rule


# --- McNemar ----------------------------------------------------------------
def test_mcnemar_licensed_and_vetoes_c_worse():
    case = _case("mcnemar")
    report = V.analyze(case["rows"], case["grade"])
    mcn = report["h3"]["mcnemar"]
    assert mcn["licensed"] is True and mcn["b"] == 7 and mcn["c"] == 0
    assert mcn["p"] is not None and mcn["p"] < 0.05
    assert report["h3"]["veto"] is True


def test_mcnemar_red_when_alpha_tightened():
    case = _case("mcnemar")
    report = V.analyze(case["rows"], case["grade"], _rules(MCNEMAR_ALPHA=0.001))
    assert report["h3"]["veto"] is False             # RED: the veto rule is load-bearing


# --- awaiting rows ----------------------------------------------------------
def test_absent_rows_yield_awaiting_rows_and_no_statistic(tmp_path):
    out = tmp_path / "verify.json"
    empty = tmp_path / "measure"
    empty.mkdir()
    rc = V.main(["--rows-dir", str(empty), "--manifest-dir", str(empty),
                 "--gates", str(empty / "GATE-LEDGER.json"), "--out", str(out)])
    assert rc == 0
    doc = json.loads(out.read_text())
    assert doc["verdict"] == "awaiting_rows"
    assert doc["analysis"] is None
    assert doc["missing"]


# --- threshold drift check --------------------------------------------------
def test_check_passes_on_the_frozen_pair():
    result = V.check_prereg()
    assert result["drift"] == []


def test_check_exits_1_when_a_threshold_drifts(tmp_path):
    doc = open(os.path.join(ROOT, "docs", "PREREG-TRANCHE-1.md"), encoding="utf-8").read()
    assert "| T1 | H1 minimum usable n | **60** |" in doc
    tampered = doc.replace("| T1 | H1 minimum usable n | **60** |",
                           "| T1 | H1 minimum usable n | **40** |")
    path = tmp_path / "PREREG-TRANCHE-1.md"
    path.write_text(tampered)
    result = V.check_prereg(str(path))
    assert result["ok"] is False and result["drift"]
    rc = V.main(["--check"])  # the real pair still passes; the tampered copy fails above
    assert rc == 0
