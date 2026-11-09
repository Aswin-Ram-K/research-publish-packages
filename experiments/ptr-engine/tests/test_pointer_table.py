"""Tests for the pointer table."""

from __future__ import annotations

import hashlib

import pytest

from ptr_engine.pointer_table import (
    OUTCOMES,
    FetchResult,
    PointerEntry,
    build_table,
    fetch,
    mask_output,
    verify,
)


def _sha(b):
    return hashlib.sha256(b.encode()).hexdigest()


class _Counter:
    def __init__(self):
        self.calls = 0
    def __call__(self, text):
        self.calls += 1
        return len(text)


_TOK = _Counter()


def test_outcomes_tuple():
    assert OUTCOMES == ("OK", "NOT_FOUND", "STALE_OR_REVOKED", "SCOPE_UNGRANTED")


def test_mask_output_marker_and_entry():
    marker, entry = mask_output(
        "hello world body", logical_id="lid1", revision=2, since_turn=4, tokenizer=_TOK
    )
    assert "hello world body" not in marker
    assert entry.logical_id == "lid1"
    assert entry.revision == 2
    assert entry.since_turn == 4
    assert entry.state == "live"
    assert entry.digest == _sha("hello world body")
    # deterministic
    m2, e2 = mask_output(
        "hello world body", logical_id="lid1", revision=2, since_turn=4, tokenizer=_TOK
    )
    assert m2 == marker and e2 == entry


def test_build_table_duplicate_ref_raises():
    e1 = PointerEntry(ref="r", logical_id="a", revision=1, since_turn=1, body_tokens=1, digest=_sha("x"), state="live")
    e2 = PointerEntry(ref="r", logical_id="b", revision=2, since_turn=2, body_tokens=1, digest=_sha("y"), state="live")
    with pytest.raises(ValueError):
        build_table([e1, e2])


def test_build_table_deterministic_order():
    entries = [
        PointerEntry(ref="b", logical_id="b", revision=1, since_turn=1, body_tokens=1, digest=_sha("y"), state="live"),
        PointerEntry(ref="a", logical_id="a", revision=1, since_turn=1, body_tokens=1, digest=_sha("x"), state="live"),
    ]
    table = build_table(entries)
    assert list(table.keys()) == ["a", "b"]


def test_four_outcomes():
    body = "the body text"
    marker, live_entry = mask_output(body, logical_id="L", revision=1, since_turn=1, tokenizer=_TOK)
    stale_entry = PointerEntry(ref="s", logical_id="L", revision=1, since_turn=1, body_tokens=1, digest=_sha(body), state="stale")
    revoked_entry = PointerEntry(ref="v", logical_id="L", revision=1, since_turn=1, body_tokens=1, digest=_sha(body), state="revoked")
    ungranted_entry = PointerEntry(ref="u", logical_id="L", revision=1, since_turn=1, body_tokens=1, digest=_sha(body), state="ungranted")
    table = build_table([live_entry, stale_entry, revoked_entry, ungranted_entry])
    assert fetch(table, live_entry.ref, budget_tokens=1000, tokenizer=_TOK).outcome == "OK"
    assert fetch(table, "missing-ref", budget_tokens=1000, tokenizer=_TOK).outcome == "NOT_FOUND"
    assert fetch(table, "s", budget_tokens=1000, tokenizer=_TOK).outcome == "STALE_OR_REVOKED"
    assert fetch(table, "v", budget_tokens=1000, tokenizer=_TOK).outcome == "STALE_OR_REVOKED"
    assert fetch(table, "u", budget_tokens=1000, tokenizer=_TOK).outcome == "SCOPE_UNGRANTED"


def test_out_of_range_byte_range():
    body = "0123456789"
    marker, entry = mask_output(body, logical_id="L", revision=1, since_turn=1, tokenizer=_TOK)
    table = build_table([entry])
    res = fetch(table, entry.ref, byte_range=(5, 100), budget_tokens=1000, tokenizer=_TOK)
    assert res.outcome == "SCOPE_UNGRANTED"
    res2 = fetch(table, entry.ref, byte_range=(-1, 3), budget_tokens=1000, tokenizer=_TOK)
    assert res2.outcome == "SCOPE_UNGRANTED"


def test_budget_truncation_determinism():
    body = "a" * 100
    marker, entry = mask_output(body, logical_id="L", revision=1, since_turn=1, tokenizer=_TOK)
    table = build_table([entry])
    r1 = fetch(table, entry.ref, budget_tokens=10, tokenizer=_TOK)
    r2 = fetch(table, entry.ref, budget_tokens=10, tokenizer=_TOK)
    assert r1.truncated is True
    assert r1.text == r2.text
    assert r1.text == "a" * 10


def test_verify_body_edit_detection():
    body = "original body"
    marker, entry = mask_output(body, logical_id="L", revision=1, since_turn=1, tokenizer=_TOK)
    table = build_table([entry])
    assert verify(table, entry.ref, body) is True
    assert verify(table, entry.ref, "tampered body") is False
    assert verify(table, "nope", body) is False


def test_fetch_never_raises_on_none():
    assert fetch(None, None, budget_tokens=None, tokenizer=_TOK).outcome in OUTCOMES
    assert fetch({}, None, budget_tokens="x", tokenizer=_TOK).outcome in OUTCOMES


def test_byte_range_ok_slice():
    body = "0123456789"
    marker, entry = mask_output(body, logical_id="L", revision=1, since_turn=1, tokenizer=_TOK)
    table = build_table([entry])
    res = fetch(table, entry.ref, byte_range=(2, 5), budget_tokens=1000, tokenizer=_TOK)
    assert res.outcome == "OK"
    assert res.text == "234"
    assert res.truncated is False
