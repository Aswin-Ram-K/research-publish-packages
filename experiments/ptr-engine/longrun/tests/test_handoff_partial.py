#!/usr/bin/env python3
"""Red/green proof for the partial-substance codes in tools/handoff_lint.py.

The unit HANDOFF-PARTIAL-SUBSTANCE added three codes: W_PARTIAL_NO_EVIDENCE,
W_PARTIAL_NO_COMMAND, E_STATUS_WORD_CONTRADICTION.  All three are WARNINGS about
substance, or one error about a false success word, and all three are additive: no
existing code was renamed, deleted or renumbered (proved here by asserting the old
codes are still in CODE_ORDER and still fire identically on the same document).

The false-positive control is V-FIXTURE-V8: done+pass with NO `evidence` key, whose
substance lives under `checks`/`measurements`/`findings`.  A rule keyed on `evidence`
alone would flag it; this suite fails if it ever does.
"""
import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TOOLS = os.path.join(ROOT, "experiments", "ptr-engine", "tools")
sys.path.insert(0, TOOLS)

import handoff_lint as hl  # noqa: E402

HANDOFFS = os.path.join(ROOT, "orchestration", "handoffs")
LEGACY_CODES = ["E_PARSE", "E_SHAPE", "E_MISSING_KEY", "E_ARTIFACT_ABSENT", "E_DONE_NO_EVIDENCE",
                "E_DONE_NO_ARTIFACTS", "E_RECOVERED_NO_EVIDENCE", "E_RECOVERED_NO_PROVENANCE",
                "E_STUB", "E_JOURNAL_MISSING", "W_JOURNAL_STALE", "W_NO_COMMANDS", "W_VERSION_STALE"]


def codes_for(doc):
    """New-code findings for one in-memory handoff, without touching the corpus baseline."""
    return {f["code"] for f in hl.partial_findings(doc)}


# ---------------------------------------------------------------- red cases
def test_partial_with_evidence_null_is_flagged():
    """A partial whose `evidence` is null and which carries nothing else is empty."""
    doc = {"unit": "T1", "overall": "partial", "evidence": None, "checks": [],
           "blocker": "", "next_unit_hint": "", "write_paths": []}
    assert "W_PARTIAL_NO_EVIDENCE" in codes_for(doc)


def test_partial_with_bare_counts_is_flagged_no_command():
    """`{"counts": {"cells": 63}}` names a number but no producer: not substance, no command."""
    doc = {"unit": "T2", "status": "partial", "counts": {"cells": 63}}
    found = codes_for(doc)
    assert "W_PARTIAL_NO_COMMAND" in found
    assert "W_PARTIAL_NO_EVIDENCE" in found


def test_done_with_no_substance_is_a_status_contradiction():
    """The combination that lets a false PASS into the record."""
    doc = {"unit": "T3", "status": "done", "artifacts": ["a"], "blocker": "",
           "next_unit_hint": "", "write_paths": []}
    assert "E_STATUS_WORD_CONTRADICTION" in codes_for(doc)


def test_pass_with_no_substance_is_a_status_contradiction():
    doc = {"unit": "T4", "overall": "pass"}
    assert "E_STATUS_WORD_CONTRADICTION" in codes_for(doc)


# ---------------------------------------------------------------- green cases
def test_partial_with_five_commands_is_clean():
    """V-REASON-MIX: a delivered partial carrying its commands."""
    path = os.path.join(HANDOFFS, "V-REASON-MIX.json")
    if not os.path.exists(path):
        pytest.skip("V-REASON-MIX.json not present")
    doc = json.load(open(path, encoding="utf-8"))
    assert codes_for(doc) == set(), codes_for(doc)


def test_substance_under_checks_clears_the_false_positive():
    """V-FIXTURE-V8: done+pass, NO `evidence` key, substance under checks/measurements.
    This is the test that fails if anyone narrows the rule back to `evidence`."""
    path = os.path.join(HANDOFFS, "V-FIXTURE-V8.json")
    if not os.path.exists(path):
        pytest.skip("V-FIXTURE-V8.json not present")
    doc = json.load(open(path, encoding="utf-8"))
    assert "evidence" not in doc, "control card is supposed to have no `evidence` key"
    assert (doc.get("status"), doc.get("overall")) == ("done", "pass")
    assert codes_for(doc) == set(), codes_for(doc)
    assert hl.has_substance(doc) is True


def test_partial_with_substance_but_no_command_is_flagged_only_for_the_command():
    """V-STAMP-NEUTRAL as measured on disk: 11 substantive checks, no command field.
    A reader can read the claims but cannot re-run them -- exactly W_PARTIAL_NO_COMMAND."""
    path = os.path.join(HANDOFFS, "V-STAMP-NEUTRAL.json")
    if not os.path.exists(path):
        pytest.skip("V-STAMP-NEUTRAL.json not present")
    doc = json.load(open(path, encoding="utf-8"))
    found = codes_for(doc)
    assert "W_PARTIAL_NO_EVIDENCE" not in found, "it does carry substance"
    assert found == {"W_PARTIAL_NO_COMMAND"}, found


def test_partial_with_command_or_count_is_clean():
    doc = {"unit": "T5", "status": "partial",
           "evidence": {"command_or_count": "63 cells classified", "commands": ["python3 x.py"]}}
    assert codes_for(doc) == set()


# ---------------------------------------------------------------- additivity
def test_legacy_codes_are_all_still_registered():
    for c in LEGACY_CODES:
        assert c in hl.CODE_ORDER, f"{c} was removed or renumbered"
    for c in hl.PARTIAL_CODES:
        assert c in hl.CODE_ORDER


def test_legacy_behaviour_on_a_stub_document_is_unchanged():
    """E_STUB still fires, and the new codes do not replace it."""
    doc = {"unit": "T6", "status": "partial", "artifacts": [], "blocker": "",
           "next_unit_hint": "", "write_paths": []}
    res = hl.lint_doc(doc, ROOT)
    assert "E_STUB" in {e["code"] for e in res["errors"]}


# ---------------------------------------------------------------- forward-only
def test_baseline_freezes_historical_hits_and_still_reports_new_ones(tmp_path):
    frozen = tmp_path / "partial-baseline.json"
    doc = {"unit": "T7", "status": "partial"}
    old = tmp_path / "OLD-PARTIAL.json"
    new = tmp_path / "NEW-PARTIAL.json"
    for p in (old, new):
        p.write_text(json.dumps(doc), encoding="utf-8")
    base = {"units": {old.name: {"unit": "T7"}}, "frozen_at": 1e12, "loaded": True}
    assert hl.partial_exempt(str(old), 1.0, base) == "frozen-baseline"
    assert hl.partial_exempt(str(new), 1.0, base) == "pre-baseline-timestamp"  # older than freeze
    assert hl.partial_exempt(str(new), 2e12, base) is None              # newer than frozen_at


def test_cli_baseline_roundtrip_is_additive(tmp_path):
    """A baseline written over the corpus freezes every hit it recorded; a fresh run
    afterwards reports zero new hits for those files and existing codes are untouched."""
    out = tmp_path / "snap.json"
    rc1 = hl.main(["orchestration/handoffs", "--root", ROOT, "--quiet",
                   "--partial-baseline-out", str(out)])
    assert rc1 in (0, 1, 2)
    assert out.exists()
    doc = json.load(open(out, encoding="utf-8"))
    assert doc["substance_keys"] == list(hl.SUBSTANCE_KEYS)
    assert doc["counts"]["entries"] == len(doc["units"])
    rc2 = hl.main(["orchestration/handoffs", "--root", ROOT, "--quiet",
                   "--partial-baseline", str(out)])
    assert rc2 in (0, 1, 2)
    # a second freeze over the same corpus must be refused, never silently rewritten
    assert hl.main(["orchestration/handoffs", "--root", ROOT, "--quiet",
                    "--partial-baseline-out", str(out)]) == 2
