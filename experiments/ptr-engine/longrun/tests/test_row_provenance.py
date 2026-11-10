"""ROW-PROVENANCE: every row says what produced it, and unlike cells refuse to compare.

WHY
---
`HARNESS-MAP-V2` had to infer a "harness era" axis from file mtimes because rows carried
no harness, fixture generation, model or thinking identity; `LATENCY-REPORT` then had to
mark every era-load-bearing pair NOT COMPARABLE, and four revisions of the same fixture
(`LR-01.v2 -> v4 -> v5 -> v6/v7`) changed the task while the rows stayed anonymous.

WHAT IS PINNED HERE
-------------------
(a) a row written by ``make_row`` carries every provenance field;
(b) two cells whose ``fixture_sha256`` differs are NOT comparable, and the refusal names
    the field;
(c) two cells differing only in ``arm`` ARE comparable -- the arm is the measurement;
(d) ``thinking`` "off" vs "auto" is a refusal;
(e) a missing provenance value is the STRING "unknown" plus ``provenance_complete:
    false``, never ``null``;
(f) red->green: if ``make_row`` stops stamping the block, (f) fails.

Offline: zero requests, no network, no lock.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import client  # noqa: E402
import run_longrun as R  # noqa: E402

FIXTURE_PATH = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")


class _Cfg:
    """The smallest cfg ``make_row`` reads -- every attribute it touches is present."""

    def __init__(self, **kw):
        self.model = "occamy-1.0-NVFP4"
        self.base_url = "http://192.168.2.168:8012/v1"
        self.engine = "sglang"
        self.max_tokens = 4096
        self.thinking = "off"
        self.tools = ""
        self.stream = True
        self.dry_run = False
        self.metrics_scrape = None
        for k, v in kw.items():
            setattr(self, k, v)


def _fixture() -> dict:
    with open(FIXTURE_PATH, encoding="utf-8") as fh:
        fx = json.load(fh)
    fx["_sha256"] = R.sha256_file(FIXTURE_PATH)
    fx["_path"] = "experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json"
    return fx


def _row(cfg=None, fixture=None, arm="transcript-grow"):
    return R.make_row(cfg or _Cfg(), fixture or _fixture(), arm, 1, "run-provenance-r1", 1,
                      None, None, None, "manifest-sha", {})


# ------------------------------------------------------------------ (a) the block
def test_a_written_row_carries_every_provenance_field():
    row = _row()
    for name in client.PROVENANCE_FIELDS:
        assert name in row, "row is missing provenance field %r" % name
        assert row[name] is not None, "provenance field %r is null (must be a value or 'unknown')" % name
        assert row[name] != "", "provenance field %r is blank (use 'unknown')" % name
    # and the concrete values that the runner really holds
    assert row["arm"] == "transcript-grow"
    assert row["model"] == "occamy-1.0-NVFP4"
    assert row["endpoint"] == "http://192.168.2.168:8012/v1"
    assert row["fixture_sha256"] == _fixture()["_sha256"]
    assert row["max_tokens"] == 4096
    assert row["thinking"] == "off"
    assert row["tools_mode"] == "off"
    assert row["fixture_id"].startswith("LR-01")
    # the harness digest is either a real 64-hex digest or an admitted gap
    assert row["harness_sha256"] == "unknown" or len(row["harness_sha256"]) == 64
    assert row["provenance_complete"] is (row["harness_sha256"] != "unknown")
    assert row["provenance_missing"] == ([] if row["provenance_complete"] else ["harness_sha256"])


def test_a_run_manifest_publishes_the_same_block():
    manifest = R.build_manifest(_Cfg(), _fixture(), "transcript-grow", 1,
                                "run-provenance-r1", "rows-x.jsonl")
    prov = manifest["provenance"]
    row = _row()
    for name in client.PROVENANCE_FIELDS:
        assert prov[name] == row[name], "manifest/row disagree on %r" % name
    assert prov["provenance_complete"] == row["provenance_complete"]


# --------------------------------------------------- (b) fixture sha is load-bearing
def test_b_different_fixture_sha_refuses_and_names_the_field():
    a = _row()
    b = dict(a)
    b["fixture_sha256"] = "0" * 64
    ok, differing = client.same_provenance(a, b)
    assert ok is False
    assert differing == ["fixture_sha256"], differing


# ------------------------------------------------ (c) differing only in arm is FINE
def test_c_same_provenance_ignores_the_arm():
    a = _row(arm="transcript-grow")
    b = _row(arm="pointer-stable")
    assert a["arm"] != b["arm"]
    assert client.same_provenance(a, b) == (True, [])


# ------------------------------------------------------- (d) thinking is load-bearing
@pytest.mark.parametrize("left,right", [("off", "auto"), ("off", "on"), ("auto", "on")])
def test_d_thinking_settings_are_not_poolable(left, right):
    a = _row(_Cfg(thinking=left))
    b = _row(_Cfg(thinking=right))
    assert client.same_provenance(a, b) == (False, ["thinking"])


def test_d_tools_mode_is_load_bearing():
    a = _row()
    b = _row(_Cfg(tools="read_file,list_dir"))
    assert b["tools_mode"] == "on:read_file,list_dir"
    assert client.same_provenance(a, b) == (False, ["tools_mode"])


# ------------------------------------- (e) a missing value is "unknown", never null
def test_e_missing_value_is_unknown_and_marks_the_row_incomplete():
    incomplete = client.provenance_block(arm="transcript-grow", model=None,
                                         endpoint="", fixture_id="LR-01",
                                         fixture_sha256=None, harness_sha256=None,
                                         max_tokens=None, thinking=None, tools_mode=None)
    assert incomplete["provenance_complete"] is False
    for name in ("model", "endpoint", "fixture_sha256", "harness_sha256",
                 "max_tokens", "thinking", "tools_mode"):
        assert incomplete[name] == "unknown", name
        assert incomplete[name] is not None
    assert incomplete["provenance_missing"] == [
        "model", "endpoint", "fixture_sha256", "harness_sha256", "max_tokens",
        "thinking", "tools_mode"]
    # the known field is untouched and still complete-able
    assert incomplete["arm"] == "transcript-grow"


def test_e_a_bare_cfg_still_stamps_unknowns_rather_than_null():
    class Bare:
        # a cfg that predates the provenance inputs: engine/stream/tools exist, but the
        # identity fields do not.  ``stream`` is read by the rest of make_row; the
        # provenance fields must degrade to "unknown", not crash and not go null.
        max_tokens = 4096
        engine = "sglang"
        stream = True
        tools = ""
        thinking = None

    row = R.make_row(Bare(), _fixture(), "pointer-stable", 1, "run-provenance-r1", 1,
                     None, None, None, "manifest-sha", {})
    assert row["model"] == "unknown"
    assert row["endpoint"] == "unknown"
    # ``thinking`` is NOT "unknown" here: it is stamped with ``client.thinking_setting``
    # -- the very function the row's own ``thinking`` field uses -- so provenance can
    # never contradict the row.  A cfg without the attribute therefore reads "auto",
    # which is what such a cfg means; a DIRECTLY declared None still becomes "unknown"
    # (see test_e_missing_value_is_unknown_and_marks_the_row_incomplete).
    assert row["thinking"] == "auto" == client.thinking_setting(Bare())
    assert row["tools_mode"] == "off"
    assert row["provenance_complete"] is False
    assert "model" in row["provenance_missing"]
    assert row["fixture_sha256"] == _fixture()["_sha256"]


def test_e_unknown_never_compares_equal():
    a = dict(_row(), model="unknown")
    b = _row()
    assert client.same_provenance(a, b) == (False, ["model"])


# ------------------------------------------------------------------ (f) red -> green
def test_f_make_row_itself_stamps_the_block():
    """RED when ``make_row``'s ``row.update(provenance_for(...))`` line is deleted.

    Deliberately asserts on a row from the REAL writer (not on ``provenance_block``),
    so the guard covers the wiring and not just the helper.
    """
    row = _row()
    stamped = {name for name in client.PROVENANCE_FIELDS if name in row}
    assert stamped == set(client.PROVENANCE_FIELDS), \
        "make_row no longer stamps: %s" % sorted(set(client.PROVENANCE_FIELDS) - stamped)
    assert row.get("provenance_complete") is not None
