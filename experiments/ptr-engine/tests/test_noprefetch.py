"""No prefetch: the adapter cannot materialise a body that was not resolved.

``build_prompt`` has no store, so it cannot fetch. It only echoes what it was
handed -- and it checks that whatever it was handed really is a resolved body of an
enumerated ref, so a host cannot pass a body it never resolved.
"""

from __future__ import annotations

import pytest

from ptr_engine import build_prompt, parse, resolve
from ptr_engine.adapter import BODIES_OPEN, INDEX_OPEN
from ptr_engine.errors import PtrBodyMismatchError, PtrUnresolvedRefError


def test_zero_resolutions_yields_the_index_only(index, ledger):
    prompt = build_prompt(index, {}, ledger)
    assert INDEX_OPEN in prompt
    assert BODIES_OPEN not in prompt
    for text in index.texts():
        assert text in prompt
    for body in ("knowledge note 1", "knowledge note 5", "never prefetch", "resolve lazily"):
        assert body not in prompt
    assert len(prompt) < index.index_size + 64


def test_build_prompt_raises_for_a_ref_with_no_resolve_row(index, ledger):
    assert len(ledger) == 0
    with pytest.raises(PtrUnresolvedRefError) as excinfo:
        build_prompt(index, {parse("@knowledge:k01@3"): b"x"}, ledger)
    assert excinfo.value.code == "PTR_UNRESOLVED_REF"
    assert len(ledger) == 0, "the adapter must not write resolution rows of its own"


def test_build_prompt_raises_for_a_ref_outside_the_index(index, ledger, scope, store):
    resolve(parse("@knowledge:k01@3"), scope, ledger)
    with pytest.raises(PtrUnresolvedRefError):
        build_prompt(index, {parse("@knowledge:k99@3"): b"ghost"}, ledger)


def test_build_prompt_refuses_bytes_that_are_not_the_resolved_body(index, ledger, scope, store):
    ref = parse("@knowledge:k01@3")
    target = resolve(ref, scope, ledger)
    # the content check is unconditional: no ledger needed to catch invented bytes
    with pytest.raises(PtrBodyMismatchError):
        build_prompt(index, {ref: b"plausible but wrong"}, None)
    with pytest.raises(PtrBodyMismatchError):
        build_prompt(index, {ref: b""}, None)
    good = store.get(target)
    assert "knowledge note 1" in build_prompt(index, {ref: good}, None)
    assert "knowledge note 1" in build_prompt(index, {ref: good}, ledger)


def test_only_the_resolved_body_appears(index, ledger, scope, store):
    ref = parse("@knowledge:k02@3")
    target = resolve(ref, scope, ledger)
    prompt = build_prompt(index, {ref: store.get(target)}, ledger)
    assert "knowledge note 2" in prompt
    for other in ("knowledge note 1", "knowledge note 3", "never prefetch"):
        assert other not in prompt
    assert prompt.count(BODIES_OPEN) == 1


def test_two_resolutions_are_ordered_deterministically(index, ledger, scope, store):
    first = parse("@knowledge:k02@3")
    second = parse("@knowledge:k01@3")
    bodies = {
        first: store.get(resolve(first, scope, ledger)),
        second: store.get(resolve(second, scope, ledger)),
    }
    prompt_a = build_prompt(index, bodies, ledger)
    prompt_b = build_prompt(index, dict(reversed(list(bodies.items()))), ledger)
    assert prompt_a == prompt_b
    assert prompt_a.index("@knowledge:k01") < prompt_a.index("@knowledge:k02")


def test_fetch_tool_spec_is_the_single_tool(index):
    from ptr_engine import fetch_tool_spec

    spec = fetch_tool_spec()
    assert spec["name"] == "fetch"
    assert list(spec["input_schema"]["properties"]) == ["ref"]
    assert spec["input_schema"]["required"] == ["ref"]
    assert spec["input_schema"]["additionalProperties"] is False
    spec["name"] = "mutated"
    assert fetch_tool_spec()["name"] == "fetch", "the spec must be a copy"
