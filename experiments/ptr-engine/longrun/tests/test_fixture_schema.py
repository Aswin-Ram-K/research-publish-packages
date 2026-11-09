import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import run_longrun as R

PT_DIR = os.path.join(LONGRUN, "tasks-v6")
V1_FIXTURE = os.path.join(LONGRUN, "tasks-v4", "runtime-v4", "LR-01.v4.tools2.json")
SCRATCH = os.path.join(LONGRUN, "state", "scratch", "u11")
os.makedirs(SCRATCH, exist_ok=True)


def _write(data):
    d = tempfile.mkdtemp(dir=SCRATCH)
    p = os.path.join(d, "fx.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return p


def _base_pt():
    with open(os.path.join(PT_DIR, "PT-01.v9.json"), encoding="utf-8") as fh:
        return json.load(fh)


def test_pt_fixtures_load():
    for name in ("PT-01", "PT-02", "PT-03"):
        fx = R.load_fixture(os.path.join(PT_DIR, name + ".v9.json"))
        assert fx["schema"] == "consonance.longrun-fixture/2"
        assert isinstance(fx["wall_tokens"], int)
        assert isinstance(fx["bytes_per_token"], (int, float))
        assert isinstance(fx["system_prompt"], str) and fx["system_prompt"]
        assert isinstance(fx["items"], list) and fx["items"]
        assert "documents" in fx


def test_v1_fixture_still_loads():
    fx = R.load_fixture(V1_FIXTURE)
    assert fx["schema"] == "consonance.longrun-fixture/1"


def test_negative_unknown_doc_id():
    data = _base_pt()
    data["turns"][0]["tool_outputs"][0]["doc_id"] = "doc-ghost"
    with pytest_raises(R.FixtureError, "unknown doc_id"):
        R.load_fixture(_write(data))


def test_negative_unknown_revision():
    data = _base_pt()
    data["turns"][0]["tool_outputs"][0]["revision"] = 999
    with pytest_raises(R.FixtureError, "not in document"):
        R.load_fixture(_write(data))


def test_negative_inconsistent_revoke_turn():
    data = _base_pt()
    for doc in data["documents"]:
        if doc["doc_id"] == "doc-revoked":
            doc["revoked_at_turn"] = 999
    with pytest_raises(R.FixtureError, "inconsistent revoke turn"):
        R.load_fixture(_write(data))


def test_negative_inconsistent_expected_outcome():
    data = _base_pt()
    changed = 0
    for s in data["fetch_scenarios"]:
        if s["ref"] == "doc-secret@r1":
            s["expected_outcome"] = "OK"
            changed += 1
    assert changed == 1, f"expected exactly one scenario changed, got {changed}"
    with pytest_raises(R.FixtureError, "inconsistent"):
        R.load_fixture(_write(data))


# tiny context manager to avoid pytest import at module top issues
import contextlib

@contextlib.contextmanager
def pytest_raises(exc, match):
    try:
        yield
    except exc as e:
        assert match in str(e), f"{match!r} not in {str(e)!r}"
        return
    raise AssertionError(f"expected {exc.__name__}")
