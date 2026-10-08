"""Offline tests for :mod:`resextract.lanes.build` and ``lanes.split``.

Fixtures live in ``tests/fixtures/lanes-store/`` (12 candidates across six
themes).  No network, no LLM, no dependency on the real store.

RED -> GREEN, guard 2: the split rule
-------------------------------------
Reverting the split rule (making
:func:`resextract.lanes.split.independent_members` return ``True``
unconditionally, so provenance-file independence is ignored) fails
``test_lane_with_non_independent_members_is_never_split`` with::

    tests/test_lanes_build.py:264: in test_lane_with_non_independent_members_is_never_split
        assert split_lane(parent, candidates) == [parent]
    E   AssertionError: assert [Lane(slug='flint-spark-high', title='Flint Spark - measured_delta - high',
    E   ... member_ids=(211,), maturity='high', audience='evaluators', parent_slug='flint-spark',
    E   split_reason='maturity axis differs across independent primary members whose provenance files
    E   are disjoint (high: 211; medium: 212); split into 2 item(s), one per maturity.')]
    E   == [Lane(slug='flint-spark', ... split_reason=None)]

The module was restored immediately after capturing that text (23 tests green
again in the same command), so the failure measures the guard, not the test.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from resextract import store
from resextract.lanes import (
    LaneCandidate,
    attach_evidence,
    audience_for_members,
    build_lanes,
    from_store,
    maturity_for_members,
    persist_lanes,
    split_lane,
    write_lanes_md,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "lanes-store"


def load_candidates() -> list[dict]:
    return json.loads((FIXTURES / "candidates.json").read_text(encoding="utf-8"))


def load_evidence() -> dict:
    return json.loads((FIXTURES / "evidence.json").read_text(encoding="utf-8"))


def fixture_graph() -> dict:
    return {row["graph_nodes_json"][0]: {"community": i + 1} for i, row in enumerate(load_candidates())}


def fixture_candidates():
    evidence = load_evidence()
    rows = from_store(load_candidates(), fixture_graph())
    return attach_evidence(rows, verdicts=evidence["verdicts"], results=evidence["results"])


def only(lanes, slug):
    return next(lane for lane in lanes if lane.slug == slug)


# --------------------------------------------------------------------------- #
# from_store
# --------------------------------------------------------------------------- #


def test_from_store_counts_provenance_and_attaches_communities():
    rows = from_store(load_candidates(), fixture_graph())
    by_id = {candidate.id: candidate for candidate in rows}
    assert by_id[201].verified_refs == 2
    assert by_id[201].total_refs == 2
    assert by_id[201].graph_nodes == ("orchid_harness",)
    assert by_id[201].communities == frozenset({1})
    # Unverifiable provenance: refs counted, none verified.
    assert by_id[205].verified_refs == 0
    assert by_id[205].total_refs == 1


def test_from_store_tolerates_raw_sqlite_rows(tmp_path):
    """A raw ``sqlite3`` row keeps ``*_json`` columns as strings; decode them."""
    db = tmp_path / "state.sqlite"
    store.init_db(db)
    con = store.connect(db)
    try:
        run_id = store.insert_run(con, target="duval")
        for row in load_candidates():
            store.insert_candidate(
                con,
                run_id=run_id,
                kind=row["kind"],
                title=row["title"],
                summary=row["summary"],
                provenance_json=row["provenance_json"],
                graph_nodes_json=row["graph_nodes_json"],
                score=row["score"],
                state=row["state"],
            )
        raw = [dict(r) for r in con.execute("SELECT * FROM candidates ORDER BY id")]
        assert isinstance(raw[0]["provenance_json"], str)
        built = from_store(raw, fixture_graph())
        assert built[0].verified_refs == 2
        assert built[0].communities == frozenset({1})
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# build_lanes: clustering, slugs, determinism
# --------------------------------------------------------------------------- #


def test_fixture_themes_cluster_into_six_lanes():
    lanes = build_lanes(fixture_candidates())
    assert [lane.slug for lane in lanes] == [
        "basalt-ridge",
        "cobalt-haze",
        "dune-drift",
        "ember-gate",
        "flint-spark",
        "orchid-bloom",
    ]
    assert only(lanes, "orchid-bloom").member_ids == (201, 202)
    assert only(lanes, "cobalt-haze").member_ids == (205, 206)


def test_community_overlap_bonus_is_the_only_reason_to_merge():
    """Two candidates sharing no tokens merge on a low threshold only with communities."""
    left = LaneCandidate(id=1, kind="novel_primitive", title="Alpha widget", summary="")
    right = LaneCandidate(id=2, kind="novel_primitive", title="Bravo gadget", summary="")
    unmerged = build_lanes([left, right])
    assert [lane.member_ids for lane in unmerged] == [(1,), (2,)]  # def. threshold 0.34: nothing shared
    same = [
        LaneCandidate(id=1, kind="novel_primitive", title="Alpha widget", summary="", communities=frozenset({9})),
        LaneCandidate(id=2, kind="novel_primitive", title="Bravo gadget", summary="", communities=frozenset({9})),
    ]
    lanes = build_lanes(same, similarity_threshold=0.1)
    assert len(lanes) == 1
    assert lanes[0].member_ids == (1, 2)


def test_slug_title_thesis_are_stable_across_shuffle_and_two_runs():
    candidates = fixture_candidates()
    first = build_lanes(candidates)
    again = build_lanes(candidates)
    reversed_input = build_lanes(list(reversed(candidates)))
    assert [(l.slug, l.member_ids, l.title, l.thesis) for l in first] == [
        (l.slug, l.member_ids, l.title, l.thesis) for l in again
    ]
    assert [(l.slug, l.member_ids) for l in first] == [(l.slug, l.member_ids) for l in reversed_input]
    assert all(lane.thesis_source == "derived" for lane in first)
    assert only(first, "orchid-bloom").title.startswith("Orchid Bloom")


def test_lanes_json_is_byte_identical_under_shuffle(tmp_path):
    candidates = fixture_candidates()
    write_lanes_md(build_lanes(candidates), tmp_path / "a")
    write_lanes_md(build_lanes(list(reversed(candidates))), tmp_path / "b")
    assert (tmp_path / "a" / "lanes.json").read_bytes() == (tmp_path / "b" / "lanes.json").read_bytes()
    assert (tmp_path / "a" / "LANES.md").read_bytes() == (tmp_path / "b" / "LANES.md").read_bytes()
    payload = json.loads((tmp_path / "a" / "lanes.json").read_text(encoding="utf-8"))
    assert [lane["slug"] for lane in payload["lanes"]] == sorted(l["slug"] for l in payload["lanes"])


def test_maturity_and_audience_come_from_evidence_only():
    candidates = fixture_candidates()
    by_id = {candidate.id: candidate for candidate in candidates}
    assert maturity_for_members([by_id[201]]) == "high"  # verified + measured result
    assert maturity_for_members([by_id[202]]) == "medium"  # verified only
    assert maturity_for_members([by_id[205]]) == "low"  # nothing verified
    lanes = build_lanes(candidates)
    assert only(lanes, "orchid-bloom").maturity == "medium"
    assert only(lanes, "cobalt-haze").maturity == "low"
    assert audience_for_members([by_id[201]]) == "evaluators"
    assert audience_for_members([by_id[202]]) == "practitioners"
    assert only(lanes, "dune-drift").audience == "evaluators"
    assert only(lanes, "ember-gate").audience == "practitioners"
    assert all(lane.maturity in {"low", "medium", "high"} for lane in lanes)


# --------------------------------------------------------------------------- #
# persist_lanes
# --------------------------------------------------------------------------- #


def _tmp_connection(tmp_path) -> sqlite3.Connection:
    db = tmp_path / "state" / "state.sqlite"
    store.init_db(db)
    return store.connect(db)


def test_persist_lanes_twice_creates_no_duplicate_rows(tmp_path):
    lanes = build_lanes(fixture_candidates())
    con = _tmp_connection(tmp_path)
    try:
        first = persist_lanes(lanes, con, "duval")
        second = persist_lanes(lanes, con, "duval")
        assert store.count(con, "lanes") == len(lanes)
        assert first == second
        row = store.get_lane_by_slug(con, "duval", "orchid-bloom")
        assert row["thesis"].startswith("Derived from 2 mined candidate(s)")
        assert row["audience"] == "evaluators"
        assert row["status"] == "draft"
    finally:
        con.close()


def test_persist_lanes_honours_type_vocabulary_and_accepts_a_path(tmp_path):
    lanes = build_lanes(fixture_candidates())
    db = tmp_path / "state" / "state.sqlite"
    store.init_db(db)
    ids = persist_lanes(lanes, db, "duval", types={"orchid-bloom": "paper"})
    assert len(ids) == len(lanes)
    con = store.connect(db)
    try:
        assert store.get_lane_by_slug(con, "duval", "orchid-bloom")["type"] == "paper"
        assert store.get_lane_by_slug(con, "duval", "ember-gate")["type"] is None
    finally:
        con.close()
    with pytest.raises(ValueError, match="lane type must be one of"):
        persist_lanes(lanes, db, "duval", types={"basalt-ridge": "not-a-type"})


# --------------------------------------------------------------------------- #
# split_lane
# --------------------------------------------------------------------------- #


def test_multi_audience_lane_splits_into_two_siblings_and_keeps_every_member():
    candidates = fixture_candidates()
    evidence = load_evidence()
    parent = only(build_lanes(candidates), "dune-drift")
    siblings = split_lane(parent, candidates, verdicts=evidence["verdicts"], results=evidence["results"])
    assert [s.slug for s in siblings] == ["dune-drift-evaluators", "dune-drift-practitioners"]
    assert all(sibling.parent_slug == "dune-drift" for sibling in siblings)
    assert all(sibling.split_reason and "audience" in sibling.split_reason for sibling in siblings)
    assert all("207" in sibling.split_reason and "208" in sibling.split_reason for sibling in siblings)
    assert sorted(m for sibling in siblings for m in sibling.member_ids) == [207, 208]
    assert siblings[0].audience == "evaluators" and siblings[1].audience == "practitioners"
    # Deterministic, including under a shuffled candidate list.
    assert [s.slug for s in split_lane(parent, list(reversed(candidates)))] == [s.slug for s in siblings]
    assert [s.member_ids for s in split_lane(parent, list(reversed(candidates)))] == [
        s.member_ids for s in siblings
    ]


def test_homogeneous_lane_is_not_split():
    candidates = fixture_candidates()
    parent = only(build_lanes(candidates), "ember-gate")
    result = split_lane(parent, candidates)
    assert result == [parent]
    assert result[0] is parent  # returned unchanged, not rebuilt


def test_lane_with_non_independent_members_is_never_split():
    """flint-spark members differ in maturity but share a provenance file."""
    candidates = fixture_candidates()
    parent = only(build_lanes(candidates), "flint-spark")
    by_id = {candidate.id: candidate for candidate in candidates}
    assert parent.member_ids == (211, 212)
    assert maturity_for_members([by_id[211]]) != maturity_for_members([by_id[212]])
    assert split_lane(parent, candidates) == [parent]


def test_split_raises_rather_than_silently_losing_a_member():
    candidates = fixture_candidates()
    parent = only(build_lanes(candidates), "dune-drift")
    with pytest.raises(ValueError, match="references candidates not supplied"):
        split_lane(parent, [c for c in candidates if c.id != 208])
