"""AGENTIC-PIN: the stage-2 instrument pin fails when the tree moves.

The pin exists so a stage-2 row can say which bytes produced it.  A pin that passes after a
file changed is worse than no pin, because it certifies a run that did not happen.  The
red->green here is `test_check_fails_when_a_pinned_file_moves`: it writes a record, edits one
pinned file, and requires `check()` to fail naming that file.
"""
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)
TOOLS = os.path.join(ENGINE, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import agentic_pin as P  # noqa: E402


def _fake_engine(tmp_path, files=None):
    """A throwaway engine tree holding exactly the pinned file names."""
    engine = tmp_path / "ptr-engine"
    for name in (files or P.FILES):
        path = engine / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("original %s\n" % name, encoding="utf-8")
    return engine


def test_compute_covers_every_pinned_file(tmp_path):
    engine = _fake_engine(tmp_path)
    payload = P.compute(str(engine))
    assert payload["file_count"] == len(P.FILES)
    assert set(payload["files"]) == set(P.FILES)
    assert len(payload["harness_sha256"]) == 64


def test_digest_is_order_independent_and_content_sensitive(tmp_path):
    engine = _fake_engine(tmp_path)
    first = P.compute(str(engine))["harness_sha256"]
    assert P.compute(str(engine))["harness_sha256"] == first
    (engine / P.FILES[0]).write_text("changed\n", encoding="utf-8")
    assert P.compute(str(engine))["harness_sha256"] != first


def test_check_fails_when_a_pinned_file_moves(tmp_path):
    """Red->green: a moved file must fail the check and be named."""
    engine = _fake_engine(tmp_path)
    record = tmp_path / "AGENTIC-PIN.json"
    P.write(str(engine), str(record))
    ok, message = P.check(str(engine), str(record))
    assert ok is True, message
    (engine / P.FILES[1]).write_text("moved\n", encoding="utf-8")
    ok, message = P.check(str(engine), str(record))
    assert ok is False
    assert P.FILES[1] in message


def test_a_missing_record_is_a_failure_not_a_pass(tmp_path):
    engine = _fake_engine(tmp_path)
    ok, message = P.check(str(engine), str(tmp_path / "absent.json"))
    assert ok is False
    assert "no record" in message


def test_a_missing_instrument_file_is_refused(tmp_path):
    engine = _fake_engine(tmp_path)
    (engine / P.FILES[0]).unlink()
    with pytest.raises(SystemExit, match="missing instrument file"):
        P.compute(str(engine))


def test_the_record_names_the_instrument_and_does_not_claim_the_replay_pin(tmp_path):
    engine = _fake_engine(tmp_path)
    record = tmp_path / "AGENTIC-PIN.json"
    P.write(str(engine), str(record))
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["instrument"] == "agentic-episode-loop"
    assert "HARNESS-PIN.json" in payload["note"]
