"""The text form is a serialization, not the primitive.

``parse``/``format`` round-trip, and the **object** is what resolves: a
``Reference`` built in code, never rendered to text, resolves exactly as well as one
parsed from a prompt. If the engine resolved strings, the second test could not pass.
"""

from __future__ import annotations

import pytest

from ptr_engine import parse, resolve
from ptr_engine.reference import Reference, ResourceRef, format
from ptr_engine.errors import PtrPointerError, PtrSyntaxError, PtrUnknownKindError

SHAPES = (
    Reference(kind="knowledge", id="k01"),
    Reference(kind="artifact", id="plan", pointer="/tools/0"),
    Reference(kind="artifact", id="plan", pointer="/goal", revision=3),
    Reference(kind="artifact", id="plan", revision=7, projection="brief"),
    Reference(kind="artifact", id="plan", pointer="/a~1b", revision=0, projection="full"),
    Reference(kind="decision", id="D-1", pointer="", revision=12),
)


@pytest.mark.parametrize("ref", SHAPES, ids=[format(r) for r in SHAPES])
def test_round_trip(ref):
    text = format(ref)
    back = parse(text)
    assert back == ref
    assert format(back) == text


def test_the_object_resolves_without_ever_becoming_text(scope, store):
    ref = Reference(kind="knowledge", id="k02", revision=3)  # never formatted
    target = resolve(ref, scope)
    assert store.get(target).startswith(b"knowledge note 2")

    # ... and a text round-trip names the very same content.
    same = resolve(parse(format(ref)), scope)
    assert same == target


def test_pointer_may_contain_an_at_sign():
    ref = parse("@artifact:x#/a@b@2")
    assert ref.pointer == "/a@b"
    assert ref.revision == 2


def test_revision_is_read_from_the_rightmost_at():
    ref = parse("@artifact:x@2?brief")
    assert (ref.revision, ref.projection) == (2, "brief")


@pytest.mark.parametrize(
    "text",
    ["", "task:k01", "@", "@task", "@task:", "@:k01", "@task:k01@", "@task:k01@@3"],
)
def test_malformed_tokens_raise_syntax(text):
    with pytest.raises(PtrSyntaxError) as excinfo:
        parse(text)
    assert excinfo.value.code == "PTR_SYNTAX"


@pytest.mark.parametrize("text", ["@widget:x", "@Task:x", "@everything:1"])
def test_unknown_kind_is_its_own_error(text):
    with pytest.raises(PtrUnknownKindError) as excinfo:
        parse(text)
    assert excinfo.value.code == "PTR_UNKNOWN_KIND"


@pytest.mark.parametrize("pointer", ["/a~2b", "a/b", "/a/b~"])
def test_bad_pointer_syntax_is_its_own_error(pointer):
    with pytest.raises(PtrPointerError) as excinfo:
        parse(f"@artifact:x#{pointer}")
    assert excinfo.value.code == "PTR_POINTER_INVALID"


def test_format_refuses_a_resourceref():
    ref = ResourceRef(scheme="artifact", locator="ab/x.txt", hash="sha256:" + "b" * 64)
    with pytest.raises(PtrSyntaxError):
        format(ref)  # type: ignore[arg-type]


def test_reference_is_frozen_and_hashable():
    ref = parse("@knowledge:k01@3")
    with pytest.raises(Exception):
        ref.id = "k02"  # type: ignore[misc]
    assert {ref, parse("@knowledge:k01@3")} == {ref}
