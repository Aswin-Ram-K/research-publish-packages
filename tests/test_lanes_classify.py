"""Offline tests for :mod:`resextract.lanes.classify` — the guard table.

Every rule is interrogated one at a time through
:func:`resextract.lanes.classify.guards_passed` /
:func:`guards_failed`.  No network, no LLM.

RED -> GREEN, guard 1: "no paper without an external anchor"
------------------------------------------------------------
Reverting the guard (``if guards["external_anchor"] and guards["measured_result"]``
-> ``if guards["measured_result"]``) fails
``test_paper_ineligible_lane_is_downgraded_to_report`` with::

    tests/test_lanes_classify.py:107: in test_paper_ineligible_lane_is_downgraded_to_report
        assert result.type == "report"
    E   AssertionError: assert 'paper' == 'report'
    E
    E     - report
    E     + paper

The module was restored immediately after capturing that text (23 tests green
again in the same command), so the failure measures the guard, not the test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from resextract.lanes import (
    Classification,
    Lane,
    MeasuredResult,
    attach_evidence,
    build_lanes,
    classify_all,
    classify_lane,
    from_store,
    guards_failed,
    guards_passed,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "lanes-store"


def load_candidates() -> list[dict]:
    return json.loads((FIXTURES / "candidates.json").read_text(encoding="utf-8"))


def load_evidence() -> dict:
    return json.loads((FIXTURES / "evidence.json").read_text(encoding="utf-8"))


def fixture_candidates():
    """Same fixture rig as ``tests/test_lanes_build.py`` (duplicated to stay importable)."""
    evidence = load_evidence()
    graph = {row["graph_nodes_json"][0]: {"community": i + 1} for i, row in enumerate(load_candidates())}
    rows = from_store(load_candidates(), graph)
    return attach_evidence(rows, verdicts=evidence["verdicts"], results=evidence["results"])


def lane(**overrides) -> Lane:
    base = dict(
        slug="demo-lane",
        title="Demo Lane - measured_delta",
        thesis="Derived from 2 mined candidate(s) of kind(s) measured_delta x2; this sentence was "
        "generated from stored candidate titles and summaries, not written by a model.",
        thesis_source="derived",
        member_ids=(1, 2),
        kinds=("measured_delta",),
        maturity="medium",
        audience="evaluators",
    )
    base.update(overrides)
    return Lane(**base)


def fixtures():
    candidates = fixture_candidates()
    evidence = load_evidence()
    lanes = {lane.slug: lane for lane in build_lanes(candidates)}
    return candidates, evidence, lanes


# --------------------------------------------------------------------------- #
# The four required outcomes
# --------------------------------------------------------------------------- #


def test_paper_eligible_lane_is_a_paper():
    _, evidence, lanes = fixtures()
    result = classify_lane(
        lanes["orchid-bloom"],
        verdicts=evidence["verdicts"],
        results=evidence["results"],
        evidence=evidence["evidence"],
    )
    assert result.type == "paper"
    assert guards_passed(result, "external_anchor", "measured_result", "recomputable", "verifiable")
    assert "type=paper" in result.rationale and "EXTENDS" in result.rationale


def test_paper_ineligible_lane_is_downgraded_to_report():
    """No external anchor, but a measured result: report, and the guard says so."""
    _, evidence, lanes = fixtures()
    result = classify_lane(
        lanes["basalt-ridge"],
        verdicts=evidence["verdicts"],
        results=evidence["results"],
        evidence=evidence["evidence"],
    )
    assert result.type == "report"
    assert result.type != "paper"
    assert result.guards["external_anchor"] is False
    assert guards_passed(result, "external_anchor") is False
    assert guards_failed(result, "external_anchor") is True
    assert "external_anchor=false" in result.rationale
    assert "measured_result=true" in result.rationale


def test_result_without_a_command_is_not_recomputable_and_not_a_benchmark_card():
    _, evidence, lanes = fixtures()
    result = classify_lane(
        lanes["basalt-ridge"],
        verdicts=evidence["verdicts"],
        results=evidence["results"],
        evidence=evidence["evidence"],
    )
    assert result.guards["measured_result"] is True
    assert result.guards["recomputable"] is False
    assert result.type != "benchmark_card"
    assert "recomputable=false" in result.rationale


def test_recomputable_numbers_without_an_anchor_become_a_benchmark_card():
    _, evidence, lanes = fixtures()
    for slug in ("dune-drift", "flint-spark"):
        result = classify_lane(
            lanes[slug],
            verdicts=evidence["verdicts"],
            results=evidence["results"],
            evidence=evidence["evidence"],
        )
        assert guards_passed(result, "recomputable", "measured_result")
        assert guards_failed(result, "external_anchor")
        assert result.type == "benchmark_card"


def test_unverifiable_lane_is_memo_and_never_paper():
    _, evidence, lanes = fixtures()
    result = classify_lane(
        lanes["cobalt-haze"],
        verdicts=evidence["verdicts"],
        results=evidence["results"],
        evidence=evidence["evidence"],
    )
    assert result.type == "memo"
    assert result.type != "paper"
    assert guards_failed(result, "verifiable")
    assert "never paper" in result.rationale


# --------------------------------------------------------------------------- #
# MeasuredResult and the guard helpers
# --------------------------------------------------------------------------- #


def test_measured_result_recomputability():
    assert MeasuredResult("throughput", 10, "ops/s", "./bench.sh").recomputable is True
    assert MeasuredResult("throughput", 10, "ops/s", None).recomputable is False
    assert MeasuredResult("throughput", 10, "ops/s", "   ").recomputable is False
    assert MeasuredResult("throughput", 10, "ops/s", "").numeric is True


def test_guards_helpers_interrogate_one_rule_at_a_time():
    result = Classification(type="report", rationale="r", guards={"external_anchor": False, "measured_result": True})
    assert guards_passed(result, "measured_result") is True
    assert guards_failed(result, "external_anchor") is True
    assert guards_passed(result) is False  # not all guards pass
    assert guards_failed(result, "measured_result") is False
    with pytest.raises(KeyError):
        guards_passed(result, "no_such_guard")


# --------------------------------------------------------------------------- #
# Determinism and the "no verdicts" world
# --------------------------------------------------------------------------- #


def test_classification_is_deterministic():
    _, evidence, lanes = fixtures()
    kwargs = dict(verdicts=evidence["verdicts"], results=evidence["results"], evidence=evidence["evidence"])
    for slug in lanes:
        first = classify_lane(lanes[slug], **kwargs)
        second = classify_lane(lanes[slug], **kwargs)
        # shuffle the input order: still identical
        third = classify_lane(
            lanes[slug],
            verdicts=list(reversed(evidence["verdicts"])),
            results=list(reversed(evidence["results"])),
            evidence=list(reversed(evidence["evidence"])),
        )
        assert (first.type, first.rationale, dict(first.guards)) == (
            second.type,
            second.rationale,
            dict(second.guards),
        )
        assert (first.type, first.rationale, dict(first.guards)) == (
            third.type,
            third.rationale,
            dict(third.guards),
        )


def test_no_verdicts_and_no_results_refuses_paper_for_every_lane():
    """The real store has no claims and no verdicts: paper must be refused everywhere."""
    candidates = fixture_candidates()
    lanes = build_lanes(candidates)
    classified = classify_all(lanes)  # no verdicts, no results, no evidence
    assert len(classified) == len(lanes)
    assert all(classification.type != "paper" for _, classification in classified)
    assert all(guards_failed(classification, "external_anchor") for _, classification in classified)
    assert all(
        ("paper refused" in classification.rationale) or ("never paper" in classification.rationale)
        for _, classification in classified
    )


def test_unlinked_result_still_counts_for_the_lane_it_is_classified_with():
    bare = lane()
    unlinked = MeasuredResult("delta", 3, "x", "make bench")
    result = classify_lane(bare, results=[unlinked])
    assert result.guards["measured_result"] is True
    assert result.type == "benchmark_card"
    # ... but must not leak into a different lane by slug.
    other = lane(slug="other-lane")
    leaked = classify_lane(other, results=[{"candidate_id": 1, "lane_slug": "demo-lane", "name": "delta", "value": 3, "command": "make bench"}])
    assert leaked.guards["measured_result"] is False
    assert leaked.type == "report"
