#!/usr/bin/env python3
"""test_spcc_claim.py - U-SPCC-34: the SPCC claim namespace.

Before this unit the runner's claim vocabulary was PARM-1's alone: ``claim_mode``
resolved only ``H1|H2|H3`` (plus the smoke declaration), and ``cell.eval_gate_prereg``
validated every claim against ``measure/PREREG-ARM-RUN.json`` with PARM-1's thresholds.
An E1 cell therefore had no legal declaration: ``smoke``/``plumbing`` marks its rows
``comparison_eligible: False`` (so they cannot support the preregistered test) and
``H1|H2|H3`` would mislabel an SPCC cell as a PARM-1 claim.

This file pins the namespace:
  * ``resolve_claim("E1")`` is a hypothesis-mode, comparison_eligible record;
  * ``H1``/``H2``/``H3`` resolve to EXACTLY the records they resolved to before;
  * G3 selects the artefact by namespace and adjudicates an E* claim against
    PREREG-SPCC's own terms (E1: 200-500 requests over 48 checkpoints);
  * an unknown id is refused with the accepted spellings, E ids included.

Offline: no request, no row file, no network.
"""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
for path in (LONGRUN, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

import cell          # noqa: E402
import claim_mode    # noqa: E402

#: The records H1/H2/H3 resolved to BEFORE this unit. Asserted as whole dicts: a
#: namespace addition that changed any field of an existing claim would be a change of
#: meaning, not an addition.
PRE_CHANGE = {
    "H1": {"mode": "hypothesis", "claim": "H1", "comparison_eligible": True},
    "H2": {"mode": "hypothesis", "claim": "H2", "comparison_eligible": True},
    "H3": {"mode": "hypothesis", "claim": "H3", "comparison_eligible": True},
}
SMOKE = {"mode": "smoke", "claim": "none", "comparison_eligible": False}


def _args(**kw):
    base = dict(hypothesis=None, turns=3, reps=1)
    base.update(kw)
    return SimpleNamespace(**base)


def _fixture(n=48):
    return {"checkpoints": [{"id": "cp%02d" % i} for i in range(n)]}


def _gate(**kw):
    n_cp = kw.pop("checkpoints", 48)
    cell._CLAIM_CACHE.clear()
    return cell.eval_gate_prereg(_args(**kw), _fixture(n_cp))


# --- the resolver ---------------------------------------------------------------
def test_e1_resolves_to_a_comparable_hypothesis_record():
    rec = claim_mode.resolve_claim("E1")
    assert dict(rec) == {"mode": "hypothesis", "claim": "E1",
                         "comparison_eligible": True}, dict(rec)
    assert rec.mode == claim_mode.MODE_HYPOTHESIS
    assert rec.claim == "E1"
    assert rec.comparison_eligible is True
    assert rec.is_smoke is False
    # case-insensitive, like every other id
    assert dict(claim_mode.resolve_claim(" e1 ")) == dict(rec)


def test_every_spcc_id_resolves_and_is_comparable():
    for name in claim_mode.SPCC_CLAIM_IDS:
        rec = claim_mode.resolve_claim(name)
        assert dict(rec) == {"mode": "hypothesis", "claim": name,
                             "comparison_eligible": True}, (name, dict(rec))


def test_h1_h2_h3_records_are_unchanged():
    for name, want in PRE_CHANGE.items():
        rec = claim_mode.resolve_claim(name)
        assert dict(rec) == want, (name, dict(rec), want)
        assert rec.as_dict() == want, (name, rec.as_dict(), want)


def test_smoke_still_non_comparable():
    for spelling in ("smoke", "plumbing"):
        rec = claim_mode.resolve_claim(spelling)
        assert dict(rec) == SMOKE, (spelling, dict(rec))
        assert rec.comparison_eligible is False


def test_e1_rows_are_comparable_but_smoke_rows_are_not():
    e1 = [{"arm": "spcc", "rep": 1, "turn": 1, "claim": "E1",
           "comparison_eligible": True}]
    assert claim_mode.assert_comparable(e1)["comparable"] is True
    try:
        claim_mode.assert_comparable(e1 + [{"arm": "plumbing", "rep": 1, "turn": 1,
                                            "claim": "none",
                                            "comparison_eligible": False}])
    except claim_mode.IncomparableClaim as exc:
        assert "incomparable_claim" in str(exc), str(exc)
    else:
        raise AssertionError("a claim-free row entered an E1 comparison")


# --- G3: the artefact is selected by namespace ----------------------------------
def test_e1_within_ceiling_and_checkpoints_is_accepted():
    verdict = _gate(hypothesis="E1", turns=250, reps=1)
    assert verdict["ok"] is True, verdict
    assert verdict["claim"] == "E1", verdict
    assert verdict["comparison_eligible"] is True, verdict
    assert verdict["mode"] == "hypothesis", verdict
    assert verdict["n"] == 250, verdict
    assert verdict["artefact"].endswith("PREREG-SPCC.json"), verdict["artefact"]
    assert verdict["thresholds"]["request_ceiling"] == [200, 500], verdict["thresholds"]
    assert verdict["thresholds"]["checkpoints_required"] == 48, verdict["thresholds"]


def test_e1_over_its_request_ceiling_is_refused():
    verdict = _gate(hypothesis="E1", turns=600, reps=1)
    assert verdict["ok"] is False, verdict
    assert verdict["n"] == 600, verdict
    assert "200-500" in verdict["consequence"], verdict["consequence"]
    assert verdict["limit"] == "n in [200, 500] and >= 48 checkpoint(s)", verdict["limit"]
    try:
        cell._enforce(verdict, "3c/7 G3 prereg gate", 12)
    except cell.Abort as exc:
        assert exc.code == 12, exc.code
    else:
        raise AssertionError("an E1 cell over its ceiling was allowed")


def test_e1_under_its_request_floor_is_refused():
    verdict = _gate(hypothesis="E1", turns=100, reps=1)
    assert verdict["ok"] is False, verdict
    assert verdict["n"] == 100, verdict


def test_e1_fixture_below_48_checkpoints_is_refused():
    cell._CLAIM_CACHE.clear()
    verdict = cell.eval_gate_prereg(_args(hypothesis="E1", turns=250, reps=1),
                                    _fixture(12))
    assert verdict["ok"] is False, verdict
    assert verdict["thresholds"]["checkpoints_in_fixture"] == 12, verdict["thresholds"]
    assert "48 checkpoints" in verdict["consequence"], verdict["consequence"]
    try:
        cell._enforce(verdict, "3c/7 G3 prereg gate", 12)
    except cell.Abort as exc:
        assert exc.code == 12, exc.code
    else:
        raise AssertionError("an E1 cell with 12 checkpoints was allowed")


def test_h2_still_uses_the_parm1_artefact_and_thresholds():
    verdict = _gate(hypothesis="H2", turns=3, reps=1)
    assert verdict["ok"] is True, verdict
    assert verdict["claim"] == "H2", verdict
    assert verdict["artefact"].endswith("PREREG-ARM-RUN.json"), verdict["artefact"]
    assert verdict["limit"] == "n >= 1", verdict["limit"]


# --- the refusal names the accepted spellings, E ids included -------------------
def test_unknown_e9_is_refused_naming_the_accepted_spellings():
    try:
        claim_mode.resolve_claim("E9")
    except claim_mode.ClaimRefusal as exc:
        text = str(exc)
        assert "three accepted forms" in text, text
        for name in ("E1", "E6", "H1", "H3", "smoke", "plumbing"):
            assert name in text, (name, text)
    else:
        raise AssertionError("E9 resolved")

    verdict = _gate(hypothesis="E9", turns=250, reps=1)
    assert verdict["ok"] is False, verdict
    assert verdict["exit"] == 12, verdict
    assert "E1" in verdict["limit"] and "E6" in verdict["limit"], verdict["limit"]
    assert "PREREG-SPCC does not define experiment" in verdict["consequence"], verdict
    assert verdict["artefact"].endswith("PREREG-SPCC.json"), verdict["artefact"]


def test_unknown_h9_still_names_parm1():
    verdict = _gate(hypothesis="H9", turns=3, reps=1)
    assert verdict["ok"] is False, verdict
    assert "PARM-1 does not define hypothesis" in verdict["consequence"], verdict
    assert "E1" in verdict["limit"], verdict["limit"]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok  %s" % name)
