"""Unit tests for `classify()` in tests/test_orchestration_handoffs.py.

Unit HANDOFF-SHAPE-CLASSIFY, 2026-10-26.  The guard's classifier decides which contract a
handoff is judged against, so a classifier bug does not report a wrong answer -- it
INVENTS a defect.  At HEAD f17663d1 the prefix test ran first and 13 documents carrying the
complete unit contract were reported as "new verifier-shape gaps"; the fix is to measure
shape by the document's keys, not by its name.

The tests below pin the four cases the rule has to get right, and then pin the property
that makes the fix safe: a reclassification to the unit shape can never forgive a missing
key, because it only happens when every key the unit shape requires is already present.
"""
import importlib.util
import json
import pathlib

import pytest

_HERE = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "handoff_shape_guard", _HERE / "test_orchestration_handoffs.py")
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

classify = guard.classify
CONTRACT = guard.CONTRACT


def _unit_doc(unit="U9.90", **extra):
    doc = {"unit": unit, "status": "done", "artifacts": [], "evidence": {},
           "blocker": "", "next_unit_hint": "", "write_paths": []}
    doc.update(extra)
    return doc


def _verdict_doc(unit="V9.91", **extra):
    doc = {"unit": unit, "overall": "pass", "checks": [], "blocker": "",
           "next_unit_hint": "", "write_paths": []}
    doc.update(extra)
    return doc


# ---------------------------------------------------------------------------
# 1. the defect: a V-prefixed document with the unit key set is a UNIT handoff
# ---------------------------------------------------------------------------
def test_unit_shape_with_v_prefix_is_unit():
    """`V` is a name a human chose, not a measurement of which keys the document has.

    This is the exact case that made the guard permanently red: 12 of the 13 reported
    files were "V"-named unit reports.  Under the old rule every one of them was judged
    against a contract requiring `overall`/`checks` -- keys a unit report never carries.
    """
    assert classify("V9.90.json", _unit_doc("V9.90")) == "unit"
    assert classify("VERDICT-EXAMPLE.json", _unit_doc("VERDICT-EXAMPLE")) == "unit"
    # ... and the name genuinely does not matter, in either direction:
    assert classify("V9.90.json", _unit_doc("V9.90")) == classify("U9.90.json", _unit_doc("U9.90"))


def test_v_prefixed_unit_report_is_gap_free_through_the_audit(tmp_path):
    """The classifier change is what turns the guard green; the document was always fine."""
    (tmp_path / "V9.90.json").write_text(json.dumps(_unit_doc("V9.90")))
    a = guard.audit(tmp_path)
    assert a["failures"] == [] and a["mid_write"] == []
    assert a["shapes"] == {"V9.90.json": "unit"}, a["shapes"]
    assert a["gaps"] == {}, a["gaps"]


# ---------------------------------------------------------------------------
# 2. the other shape: a verdict is still a verdict, named V or not
# ---------------------------------------------------------------------------
def test_verdict_shape_is_verifier():
    assert classify("V9.91.json", _verdict_doc()) == "verifier"
    # a verdict-shaped handoff that is NOT V-named is still a verdict: the key
    # corroborates the prefix, it does not replace it.
    assert classify("RECORD-REFRESH.json", _verdict_doc()) == "verifier"
    # and it is judged against the verifier contract's required keys.
    a_contract = guard.required_keys("verifier")
    assert "overall" in a_contract and "checks" in a_contract, a_contract


def test_verdict_missing_a_required_key_is_still_reported(tmp_path):
    """The guard's purpose after the fix: a genuinely incomplete verdict is caught."""
    (tmp_path / "V9.99.json").write_text(json.dumps(
        {"unit": "V9.99", "checks": [], "blocker": "", "write_paths": []}))
    a = guard.audit(tmp_path)
    assert a["shapes"]["V9.99.json"] == "verifier"
    assert a["gaps"] == {"V9.99.json": ["overall", "next_unit_hint"]}, a["gaps"]


# ---------------------------------------------------------------------------
# 3. the ambiguous case: unit key set AND "overall" -> UNIT, and here is why
# ---------------------------------------------------------------------------
def test_ambiguous_unit_keys_and_overall_goes_to_unit_and_can_forgive_nothing():
    """Deliberate precedence, stated so a later reader can disagree with reasons.

    A document carrying all 7 unit keys plus `overall` is judged as a UNIT handoff.
    Why that way: the unit key set is the specification of the unit report, so a document
    that carries all of it has, by construction, no unit gap to forgive -- the move can
    never hide a missing required key.  The cost is that such a document is not asked for
    `checks`; that is a recorded residual (docs/HANDOFF-SHAPE.md), not a silent one.

    The rescue is bounded, and the bound is the point: drop ONE unit key and the document
    falls through to the verdict test, where the gap is reported.
    """
    doc = _unit_doc("RECORD-REFRESH", overall="PASS")
    assert classify("RECORD-REFRESH.json", doc) == "unit"
    # nothing is forgiven, because nothing is missing:
    assert [k for k in CONTRACT if k not in doc] == []

    # one key short of the unit contract, it is no longer ambiguous -- it is a verdict,
    # judged against the verdict contract, and its gaps are reported by name.
    short = _unit_doc("RECORD-REFRESH", overall="PASS")
    del short["blocker"]
    assert classify("RECORD-REFRESH.json", short) == "verifier"
    assert "blocker" in guard.required_keys("verifier")


def test_ambiguous_shape_cannot_smuggle_a_missing_key(tmp_path):
    """Invariant, measured end-to-end: a half-unit, half-verdict document is still caught."""
    short = _unit_doc("REC9.90", overall="PASS")
    del short["write_paths"]
    (tmp_path / "REC9.90.json").write_text(json.dumps(short))
    a = guard.audit(tmp_path)
    assert a["shapes"]["REC9.90.json"] == "verifier"
    assert "write_paths" in a["gaps"]["REC9.90.json"], a["gaps"]


# ---------------------------------------------------------------------------
# 4. empty / other documents fall back to the unit shape (the fail-loud default)
# ---------------------------------------------------------------------------
def test_empty_or_unrecognised_document_falls_back_to_unit():
    """There is no third 'other' bucket, and the fallback is the LOUD one.

    An empty object or an unrelated key set has no verdict key and no "V" name, so it is
    read as a unit handoff -- which then owes all 7 contract keys, i.e. it is reported with
    7 gaps rather than waved through.  A document that only *looks* like a record cannot
    become exempt merely by being unrecognisable.
    """
    assert classify("U9.92.json", {}) == "unit"
    assert classify("WEIRD.json", {"notes": "nothing contracted here"}) == "unit"
    # a V-named empty document keeps the verifier reading (unchanged behaviour):
    assert classify("V9.92.json", {}) == "verifier"

    # and the fallback really is loud: the empty document produces the full gap list
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        (pathlib.Path(d) / "WEIRD.json").write_text("{}")
        a = guard.audit(d)
        assert a["shapes"] == {"WEIRD.json": "unit"}
        assert a["gaps"] == {"WEIRD.json": list(CONTRACT)}, a["gaps"]


# ---------------------------------------------------------------------------
# 5. the safety property, measured on the live corpus
# ---------------------------------------------------------------------------
def test_reclassification_never_forgives_a_missing_key_on_the_live_corpus():
    """Every document the classifier RESCUES to 'unit' really carries the whole unit contract.

    The rescue is the only place the new code can differ from the old: a document with a
    verdict sign (a "V" name or an `overall` key) that the old rule would have judged as a
    verdict, but which now reads as a unit handoff.  That is allowed exactly when the
    document carries all 7 unit keys -- i.e. when the unit shape owes it nothing.  A
    document that keeps the unit shape for want of any verdict sign is NOT a rescue, and may
    still carry recorded gaps (U0.22.json and the U8.15 baseline are exactly that).

    Measured against the handoffs on disk, not against a copy, so the property is re-checked
    as the corpus grows.
    """
    a = guard.audit()
    rescued = {name: [k for k in CONTRACT if k not in a["docs"][name]]
               for name, shape in a["shapes"].items()
               if shape == "unit" and (name.startswith("V") or "overall" in a["docs"][name])}
    assert rescued, "no rescued documents on the corpus: the measured claim would be vacuous"
    assert all(not missing for missing in rescued.values()), (
        "a document was rescued to the unit shape while missing unit-contract keys, so the "
        "reclassification hole is real: %s" % {n: m for n, m in rescued.items() if m})
