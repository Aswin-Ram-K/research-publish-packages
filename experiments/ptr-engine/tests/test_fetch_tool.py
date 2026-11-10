"""Tests for fetch_tool."""

from __future__ import annotations

import json

import pytest

from ptr_engine.fetch_tool import (
    FETCH_TOOL,
    batched_fetch,
    parse_fetch_calls,
    render_fetch_result,
)
from ptr_engine.outcomes import NOT_FOUND, STALE_OR_REVOKED
from ptr_engine.pointer_table import PointerEntry, build_table, mask_output
import hashlib


def _sha(b):
    return hashlib.sha256(b.encode()).hexdigest()


def _table_with_body(ref, body, state="live"):
    marker, entry = mask_output(body, logical_id=ref, revision=1, since_turn=1)
    entry = PointerEntry(
        ref=ref,
        logical_id=ref,
        revision=1,
        since_turn=1,
        body_tokens=len(body),
        digest=entry.digest,
        state=state,
    )
    return build_table([entry]), body


def test_fetch_tool_schema():
    assert FETCH_TOOL["type"] == "function"
    fn = FETCH_TOOL["function"]
    assert fn["name"] == "fetch"
    params = fn["parameters"]
    assert "ref" in params["properties"]
    assert params["required"] == ["ref"]
    # range optional
    assert "range" in params["properties"]


def test_parse_fetch_calls_tolerates():
    # missing tool_calls
    assert parse_fetch_calls({}) == []
    assert parse_fetch_calls(None) == []
    # malformed json
    msg = {"tool_calls": [{"function": {"name": "fetch", "arguments": "{bad json"}}]}
    res = parse_fetch_calls(msg)
    assert res == [{"ref": "", "range": None}]
    # absent range
    msg2 = {"tool_calls": [{"function": {"name": "fetch", "arguments": json.dumps({"ref": "r1"})}}]}
    res2 = parse_fetch_calls(msg2)
    assert res2 == [{"ref": "r1", "range": None}]


def test_batched_fetch_budget_small():
    table, body = _table_with_body("r1", "a" * 100)
    # add a second ref absent
    reqs = [{"ref": "r1", "range": None}, {"ref": "missing", "range": None}]
    res = batched_fetch(table, reqs, budget_tokens_per_turn=5)
    assert len(res) == 2
    assert any(r.truncated is True for r in res)
    # every request has outcome
    assert all(r.outcome is not None for r in res)


def test_determinism():
    table, body = _table_with_body("r1", "a" * 100)
    reqs = [{"ref": "r1", "range": None}]
    r1 = batched_fetch(table, reqs, budget_tokens_per_turn=5)
    r2 = batched_fetch(table, reqs, budget_tokens_per_turn=5)
    assert r1 == r2


def test_absent_ref_not_found():
    table, body = _table_with_body("r1", "hello")
    res = batched_fetch(table, [{"ref": "nope", "range": None}], budget_tokens_per_turn=100)
    assert res[0].outcome == NOT_FOUND


def test_revoked_stale():
    table, body = _table_with_body("r1", "hello", state="revoked")
    res = batched_fetch(table, [{"ref": "r1", "range": None}], budget_tokens_per_turn=100)
    assert res[0].outcome == STALE_OR_REVOKED
