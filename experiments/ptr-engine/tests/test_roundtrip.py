"""compile -> parse -> resolve -> store.get returns the exact original bytes."""

from __future__ import annotations

import hashlib

import pytest

from ptr_engine import parse, resolve
from ptr_engine.reference import Reference


def test_every_entry_round_trips_to_the_exact_original_bytes(index, scope, store, material):
    original = {(item["kind"], item["id"]): item["body"] for item in material}
    checked = 0
    for entry in index.entries.values():
        # The object is what resolves: this never re-reads the index text.
        ref = Reference(
            kind=entry.kind,
            id=entry.id,
            pointer=entry.pointer,
            revision=entry.ref.revision,
            projection=entry.projection,
        )
        target = resolve(ref, scope)
        body = store.get(target)
        assert hashlib.sha256(body).hexdigest() == target.digest

        if entry.pointer is None:
            assert body.decode("utf-8") == original[(entry.kind, entry.id)]
        else:
            assert entry.size == len(body)
        checked += 1
    assert checked == len(material) == len(index.entries)


def test_pointer_entry_returns_the_selected_region(index, scope, store):
    target = resolve(parse("@artifact:plan#/goal@3"), scope)
    assert store.get(target) == b'"resolve lazily"'


def test_identical_bodies_are_stored_once(warmpool, store):
    first = store.put(b"the same bytes")
    second = store.put(b"the same bytes")
    assert first == second
    files = [p for p in warmpool.rglob("*") if p.is_file()]
    assert len(files) == 1
    assert store.get(first) == b"the same bytes"


def test_store_refuses_a_tampered_body(warmpool, store):
    from ptr_engine.errors import PtrHashMismatchError

    ref = store.put(b"trust me")
    store.path_of(ref).write_bytes(b"trust me!")
    with pytest.raises(PtrHashMismatchError) as excinfo:
        store.get(ref)
    assert excinfo.value.code == "PTR_HASH_MISMATCH"


def test_divergent_bodies_diverge_in_identity(store):
    a = store.put(b"one")
    b = store.put(b"two")
    assert a.hash != b.hash
    assert a.locator != b.locator


def test_projection_entry_still_resolves_to_its_body(index, scope, store):
    target = resolve(parse("@memory:m01@3?brief"), scope)
    assert store.get(target) == b"a remembered preference: never prefetch"


def test_a_superseded_revision_is_refused_but_its_bytes_survive(store, ledger, material):
    """SPEC.md section 4: the body is retained; the pinned Reference is refused."""
    from ptr_engine import Scope, compile_turn
    from ptr_engine.errors import PtrRevisionError

    first = compile_turn(
        material, revision=1, scope="sess-01", block_size=64, store=store
    )
    target = resolve(parse("@knowledge:k01@1"), Scope("sess-01", first), ledger)
    old_bytes = store.get(target)
    assert old_bytes.startswith(b"knowledge note 1")

    rewritten = [
        {"kind": "knowledge", "id": "k01", "body": "knowledge note 1, rewritten"}
    ] + [item for item in material if not (item["kind"] == "knowledge" and item["id"] == "k01")]
    second = compile_turn(
        rewritten, revision=2, scope="sess-01", block_size=64, store=store
    )

    with pytest.raises(PtrRevisionError) as excinfo:
        resolve(parse("@knowledge:k01@1"), Scope("sess-01", second), ledger)
    assert excinfo.value.code == "PTR_REVISION_MISMATCH"

    # The bytes are still there, addressed by the ResourceRef the older resolve returned.
    assert store.get(target) == old_bytes
