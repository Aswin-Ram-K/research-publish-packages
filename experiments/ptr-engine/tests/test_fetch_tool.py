"""Tests for fetch_tool."""

from __future__ import annotations

import json

import pytest

from ptr_engine.fetch_tool import (
    FETCH_TOOL,
    batched_fetch,
    parse_fetch_calls,
)
from ptr_engine.outcomes import NOT_FOUND, STALE_OR_REVOKED


def test_fetch_tool_schema():
    assert FETCH_TOOL["type"] == "function"
    fn = FETCH_TOOL["function"]
    assert fn["name"] == "fetch"
    params = fn["parameters"]
    assert "ref" in params["properties"]
    assert params["required"] == ["ref"]
    assert "range" in params["properties"]


def test_parse_fetch_calls_tolerates():
    assert parse_fetch_calls({}) == []
    assert parse_fetch_calls(None) == []
    msg = {"tool_calls": [{"id": "call-0", "function": {"name": "fetch", "arguments": "{bad json"}}]}
    res = parse_fetch_calls(msg)
    assert res == [{"ref": "", "range": None, "invalid": True, "tool_call_id": "call-0", "id": "call-0"}]
    msg2 = {"tool_calls": [{"id": "call-1", "function": {"name": "fetch", "arguments": json.dumps({"ref": "r1"})}}]}
    res2 = parse_fetch_calls(msg2)
    assert res2 == [{"ref": "r1", "range": None, "tool_call_id": "call-1", "id": "call-1"}]




class _FourCharTok:
    def count(self, text):
        return (len(text) + 3) // 4


def test_batched_fetch_budget_token_not_char():
    from ptr_engine.pointer_table import build_table, mask_output, PointerEntry
    tok = _FourCharTok()
    marker, e = mask_output("a" * 100, logical_id="r1", revision=1, since_turn=1, tokenizer=tok)
    entry = PointerEntry(
        ref=e.ref, logical_id="r1", revision=1, since_turn=1,
        body_tokens=e.body_tokens, digest=e.digest, state="live",
    )
    table = build_table([entry])
    res = batched_fetch(table, [{"ref": entry.ref, "range": None, "tool_call_id": "call-a"}], budget_tokens_per_turn=30, tokenizer=tok)
    assert len(res) == 1
    assert res[0].truncated is False

class _CharTok:
    def count(self, text):
        return len(text)


def _entry(ref, body, state="live"):
    from ptr_engine.pointer_table import PointerEntry, mask_output
    import hashlib
    tok = _CharTok()
    marker, e = mask_output(body, logical_id=ref, revision=1, since_turn=1, tokenizer=tok)
    return PointerEntry(
        ref=e.ref, logical_id=ref, revision=1, since_turn=1,
        body_tokens=len(body), digest=e.digest, state=state,
    )


def test_batched_fetch_budget_small():
    from ptr_engine.pointer_table import build_table
    entry = _entry("r1", "a" * 100)
    table = build_table([entry])
    reqs = [{"ref": entry.ref, "range": None, "tool_call_id": "call-a"}, {"ref": "missing", "range": None, "tool_call_id": "call-b"}]
    res = batched_fetch(table, reqs, budget_tokens_per_turn=5, tokenizer=_CharTok())
    assert len(res) == 2
    assert any(r.truncated is True for r in res)
    assert all(r.outcome is not None for r in res)


def test_determinism():
    from ptr_engine.pointer_table import build_table
    entry = _entry("r1", "a" * 100)
    table = build_table([entry])
    reqs = [{"ref": entry.ref, "range": None, "tool_call_id": "call-a"}]
    r1 = batched_fetch(table, reqs, budget_tokens_per_turn=5, tokenizer=_CharTok())
    r2 = batched_fetch(table, reqs, budget_tokens_per_turn=5, tokenizer=_CharTok())
    assert r1 == r2


def test_absent_ref_not_found():
    from ptr_engine.pointer_table import build_table
    entry = _entry("r1", "hello")
    table = build_table([entry])
    res = batched_fetch(table, [{"ref": "nope", "range": None, "tool_call_id": "call-a"}], budget_tokens_per_turn=100, tokenizer=_CharTok())
    assert res[0].outcome == NOT_FOUND


def test_revoked_stale():
    from ptr_engine.pointer_table import build_table
    entry = _entry("r1", "hello", state="revoked")
    table = build_table([entry])
    res = batched_fetch(table, [{"ref": entry.ref, "range": None, "tool_call_id": "call-a"}], budget_tokens_per_turn=100, tokenizer=_CharTok())
    assert res[0].outcome == STALE_OR_REVOKED
