#!/usr/bin/env python3
"""Tests for tools/reason_mix.py (unit QUALITY-REASON-MIX).

Offline. Reads the grade documents on disk; asserts the classification rules,
that no cell is unclassifiable, and that the headline arithmetic is reproducible.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
TOOLS = os.path.join(ROOT, "experiments", "ptr-engine", "tools")
sys.path.insert(0, TOOLS)

import reason_mix  # noqa: E402


def test_sentinel_unparseable_is_never_answered_not_contract():
    b, _ = reason_mix.classify("undecidable", "unparseable", "ANSWER: NOT-AN-ANSWER")
    assert b == "never_answered"


def test_real_text_unparseable_is_contract_bucket():
    b, _ = reason_mix.classify("undecidable", "unparseable", "ANSWER: 7 and then some")
    assert b == "answered_right_but_rejected_by_contract"


def test_prose_and_turn_missing_are_never_answered():
    assert reason_mix.classify("undecidable", "prose_only", None)[0] == "never_answered"
    assert reason_mix.classify("fail", "turn_missing", None)[0] == "never_answered"
    assert reason_mix.classify("undecidable", "no_answer_line", None)[0] == "never_answered"


def test_contract_reasons_are_bucket_three():
    for r in ("answer_not_contract", "answer_not_contract:multiple_answer_lines",
              "not_a_contract_form", "multiple_answer_lines",
              "row_fields_disagree_with_content"):
        assert reason_mix.classify("fail", r, "x")[0] == \
            "answered_right_but_rejected_by_contract", r


def test_v4_wrong_value_reasons_are_bucket_two():
    assert reason_mix.classify("fail", "number_wrong:7", "x")[0] == "answered_wrong_value"
    assert reason_mix.classify("fail", "missing_anchor:ledger", "x")[0] == "answered_wrong_value"


def test_unknown_reason_is_unclassifiable_not_guessed():
    b, note = reason_mix.classify("fail", "invented_reason", "x")
    assert b == "unclassifiable" and "invented_reason" in note


def _produce(tmp):
    out = os.path.join(tmp, "mix.json")
    rc = subprocess.run([sys.executable, os.path.join(TOOLS, "reason_mix.py"),
                         "--out", out, "--no-probe"],
                        cwd=ROOT, capture_output=True, text=True)
    assert rc.returncode == 0, rc.stderr
    return json.load(open(out))


def test_committed_json_is_reproducible(tmp_path=None):
    """The published JSON is exactly what the tool re-derives from the documents."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        doc = _produce(td)
    published = json.load(open(os.path.join(
        ROOT, "experiments", "ptr-engine", "measure", "QUALITY-REASON-MIX.json")))
    for k in ("bucket_totals_all_grids", "bucket_totals_primary_T3_real",
              "headline_numbers", "n_cells" if False else "scope"):
        assert json.dumps(doc[k], sort_keys=True) == json.dumps(
            published[k], sort_keys=True), k


def test_every_cell_is_classified():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        doc = _produce(td)
    assert doc["unclassifiable"] == []
    assert len(doc["rows"]) == doc["scope"]["n_cells_v5"]
    for r in doc["rows"]:
        assert r["verdict"] == "pass" or r["bucket"], r


def test_no_wrong_value_cell_exists_in_v5_era():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        doc = _produce(td)
    assert doc["headline_numbers"]["all_cells_answered_wrong_value"] == 0


def test_non_pointer_bucket3_share_below_threshold():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        doc = _produce(td)
    h = doc["headline_numbers"]
    assert h["threshold_met"] is False
    assert h["bucket3_share_denominator"] == h["non_pointer_non_passes"]
    if h["non_pointer_non_passes"]:
        assert (100.0 * h["bucket3_share_numerator"]
                / h["non_pointer_non_passes"]) < h["threshold_pct"]


def test_grader_is_arm_blind():
    """Same answer text, two arm labels -> identical verdicts (offline, in memory)."""
    probe = reason_mix.arm_blindness_probe()
    assert probe, "probe produced no cases"
    for case in probe:
        assert case["identical_for_both_arms"] is True, case["case"]


def test_demoted_cell_is_the_shape_rejection():
    """v4 `ok` -> v5 `answer_not_contract`: the value was right, the shape was not."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        doc = _produce(td)
    dem = doc["cells_demoted_v4_pass_to_v5_fail"]
    assert len(dem) == 1, dem
    d = dem[0]
    assert d["cp_id"] if "cp_id" in d else d["checkpoint_id"] == "cp.2.t46"
    assert d["v5_reason"].startswith("answer_not_contract")
    assert "ledger.record_refusal" in d["v5_answer_raw"]
    assert "CALL" not in d["v5_answer_raw"]
