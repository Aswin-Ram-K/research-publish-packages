"""Bodies are keyed by (task_id, ref), not bare ref."""

from __future__ import annotations

import hashlib

import pytest

from ptr_engine.errors import PtrStoreMissError
from ptr_engine.pointer_table import (
    PointerEntry,
    build_table,
    fetch,
    mask_output,
    reset_bodies,
)


def _sha(b):
    return hashlib.sha256(b.encode()).hexdigest()


def test_body_namespacing_by_fixture():
    reset_bodies()
    ref = "doc-live@r1"
    body_a = "ALPHA body"
    body_b = "BETA body"

    m1, e1 = mask_output(body_a, logical_id="doc-live", revision=1, since_turn=1, task_id="fixture-a")
    m2, e2 = mask_output(body_b, logical_id="doc-live", revision=1, since_turn=1, task_id="fixture-b")
    assert e1.ref == ref and e2.ref == ref

    table_a = build_table([e1], task_id="fixture-a")
    table_b = build_table([e2], task_id="fixture-b")

    assert fetch(table_a, ref, budget_tokens=1000, task_id="fixture-a").text == body_a
    assert fetch(table_b, ref, budget_tokens=1000, task_id="fixture-b").text == body_b

    # declared ref with no stored body must raise
    entry = PointerEntry(
        ref="ghost@r1", logical_id="ghost", revision=1, since_turn=1,
        body_tokens=1, digest=_sha("x"), state="live",
    )
    table = build_table([entry])
    with pytest.raises(PtrStoreMissError):
        fetch(table, "ghost@r1", budget_tokens=1000)