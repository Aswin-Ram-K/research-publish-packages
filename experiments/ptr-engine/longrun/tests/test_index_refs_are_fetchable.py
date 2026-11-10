"""INDEX-REF-COHERENCE (U-SPCC-55): every ref the world index advertises is fetchable.

The defect this pins: the index listed ``@knowledge:<item-id>@1`` ids, a
namespace the fetch tool does not accept, so the model guessed refs and 12 of
25 fetch attempts in the measured run resolved to NOT_FOUND (``ptr_engine/resolve.py``,
``knowledge/item-1@1``, ``knowledge/doc-fact-02.txt``, ...).  The index is the
only place the model learns which refs exist; it must not name a ref the fetch
tool would reject.

The invariant is checked against the real ``TX-03.v1.json`` fixture and the real
fetch path (``ArmCDState.all_entries`` -> ``build_table`` -> ``fetch``), not
against a hand-built table, so a drift between the index's notion of "live" and
the fetch table's notion fails here.
"""
from __future__ import annotations

import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_LONGRUN = os.path.dirname(_HERE)
_PTR_ENGINE = os.path.dirname(_LONGRUN)
for _p in (_LONGRUN, _PTR_ENGINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arm_cd  # noqa: E402
import run_longrun  # noqa: E402
from ptr_engine.pointer_table import build_table, fetch  # noqa: E402
from ptr_engine.quantise import StubTokenizer  # noqa: E402

FIXTURE_PATH = os.path.join(_LONGRUN, "tasks-v7", "TX-03.v1.json")
INDEX_TURN = 1
MAKE_REF_RE = re.compile(r"^doc-[A-Za-z0-9_.-]+@r\d+$")


def _fixture() -> dict:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _index_refs(lines) -> list:
    """Refs from index lines of the shape ``- {ref} {hash8} {bytes}``."""
    refs = []
    for line in lines:
        parts = line.split()
        assert len(parts) == 4 and parts[0] == "-", "malformed index line: %r" % (line,)
        assert parts[3].isdigit(), "index line has no byte length: %r" % (line,)
        refs.append(parts[1])
    return refs


def _fetch_table(fixture: dict, turn: int = INDEX_TURN) -> dict:
    """The table ``service_fetches`` builds: deduped entries, then ``build_table``."""
    state = arm_cd.ArmCDState(fixture=fixture, tokenizer=StubTokenizer())
    seen, uniq = set(), []
    for entry in state.all_entries(turn):
        if entry.ref in seen:
            continue
        seen.add(entry.ref)
        uniq.append(entry)
    return build_table(uniq)


def _assert_all_fetchable(lines, fixture: dict, turn: int = INDEX_TURN) -> int:
    """The invariant: every advertised ref fetches OK.  Raises on the first miss."""
    table = _fetch_table(fixture, turn)
    budget = int(fixture["fetch_budget_tokens"])
    tok = StubTokenizer()
    refs = _index_refs(lines)
    bad = []
    for ref in refs:
        res = fetch(table, ref, budget_tokens=budget, tokenizer=tok,
                    tool_call_id="index-ref-check")
        if res.outcome != "OK":
            bad.append((ref, res.outcome))
    assert not bad, "index advertises refs the fetch tool rejects: %r" % (bad,)
    return len(refs)


# ---------------------------------------------------------------- the invariant

def test_every_index_ref_fetches_ok():
    """Every ref in the TX-03 index resolves OK through the real fetch path."""
    fixture = _fixture()
    lines = run_longrun.index_lines(fixture).splitlines()
    assert lines, "index is empty: the model is shown no addressable ref at all"
    n = _assert_all_fetchable(lines, fixture)
    assert n == len(lines)


def test_index_carries_make_ref_form_not_knowledge_ids():
    """The index advertises ``doc-<name>@r<rev>`` refs, never ``@knowledge:<id>@1``."""
    fixture = _fixture()
    text = run_longrun.index_lines(fixture)
    assert "@knowledge:" not in text, (
        "index still advertises the @knowledge: id namespace, which the fetch "
        "tool does not accept:\n%s" % text)
    refs = _index_refs(text.splitlines())
    for ref in refs:
        assert MAKE_REF_RE.match(ref), "index ref is not make_ref form: %r" % (ref,)
    # the granted, live documents of the fixture are all advertised
    for expected in ("doc-config@r1", "doc-errors@r1", "doc-constants@r1",
                     "doc-fact-01@r1", "doc-fact-08@r1"):
        assert expected in refs, "index omits fetchable ref %r" % (expected,)


def test_both_arms_share_the_index():
    """The masking/fetch arm and the SPCC arm read byte-identical index lines."""
    fixture = _fixture()
    masking = run_longrun.index_lines(fixture).splitlines()
    spcc = arm_cd.spcc_world_index(fixture, StubTokenizer())
    assert masking == spcc, (
        "per-arm index divergence: the two arms would be compared on different "
        "world indexes\nmasking=%r\nspcc=%r" % (masking, spcc))
    # and the SPCC arm's own L1 state carries exactly those lines
    state = arm_cd.SpccArmState(fixture=fixture, tokenizer=StubTokenizer())
    assert list(state.index_lines) == masking


def test_corrupted_ref_fails_the_invariant_loudly():
    """A ref the fetch tool cannot resolve makes the invariant fail, not pass quietly."""
    fixture = _fixture()
    lines = run_longrun.index_lines(fixture).splitlines()
    assert lines
    parts = lines[0].split()
    corrupted = list(lines)
    corrupted[0] = "- doc-ghost@r1 %s %s" % (parts[2], parts[3])
    with pytest.raises(AssertionError) as exc:
        _assert_all_fetchable(corrupted, fixture)
    assert "doc-ghost@r1" in str(exc.value)
    assert "NOT_FOUND" in str(exc.value)
