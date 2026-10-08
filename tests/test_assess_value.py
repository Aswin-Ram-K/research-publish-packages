"""Offline tests for ``resextract.assess.value`` (unit U4.4).

Everything here is offline and deterministic: no network, no live model.  Model
paths are exercised with injected stub clients.

The honesty guards this file pins
---------------------------------

**(a) no source => ``unknown``.**  Guard site:
``resextract/assess/value.py::_axes_from_payload`` —::

    if not value or not source:
        ... Axis(substantiated=False, reason="the model returned no usable source ...")

Reverting that test to ``if not value:`` makes ``test_unsourced_axes_are_downgraded``
fail.  Because the empty-source rejection inside ``verify_axis_source`` is a
*second*, defence-in-depth enforcement of the same rule, the honest revert must
remove both (guard: ``if not value or not source:`` -> ``if not value:``; verifier
path: ``if not ok:`` -> ``if not ok and source:``).  Observed in this unit::

    sha256(value.py) before   = 6f60b282dc2c279c3242f296e9fda66116b39522baca92db65f2e792e5537300
    sha256(value.py) reverted = 92aabda53b369b196de4a6e004fc5fd1fb567d7604d05915487a359de092da73
    pytest -q tests/test_assess_value.py::test_unsourced_axes_are_downgraded
      -> FAILED ... AssertionError: assert 1 == 5
         E + where 5 = ValueAssessment(..., axes=[Axis(name='...', substantiated=True,
           value='...', source='', producer='model', ...)] ...).substantiated_count
         (four unsourced axes were accepted and substantiated)
    restore -> sha256 = 6f60b282... (bit-identical)

**(b) fabricated ref rejection.**  Guard site:
``resextract/assess/value.py::_axes_from_payload`` —::

    if not ok:
        ... Axis(substantiated=False, reason="the axis source was rejected ...")

Reverting that test (``if not ok:`` -> ``if False:``) makes
``test_fabricated_span_is_rejected`` fail.  Observed in this unit::

    sha256(value.py) before   = 6f60b282dc2c279c3242f296e9fda66116b39522baca92db65f2e792e5537300
    sha256(value.py) reverted = 196b69368b228449af7059971d3cb56793d19cd6a52bcd312a797378d5a19290
    pytest -q tests/test_assess_value.py::test_fabricated_span_is_rejected
      -> FAILED tests/test_assess_value.py::test_fabricated_span_is_rejected - Asserti...
         (a fabricated README.md#L99999-L100000 span substantiated the axis)
    restore -> sha256 = 6f60b282... (bit-identical)

Both reverts were restored bit-identically (sha256 checked) under
``PYTHONDONTWRITEBYTECODE=1`` with a ``__pycache__`` purge; the full file then
passed ``11 passed``.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from resextract.assess.value import (
    AXIS_NAMES,
    Axis,
    ValueAssessment,
    ValueReport,
    assess_value,
    assess_values,
    verify_axis_source,
)
from resextract.llm import UnparseableOutput


# --------------------------------------------------------------------------- #
# fixtures and stubs
# --------------------------------------------------------------------------- #


def _axis(value: str = "", source: str = "") -> SimpleNamespace:
    return SimpleNamespace(value=value, source=source)


def _payload(**overrides: SimpleNamespace) -> SimpleNamespace:
    base = {name: _axis() for name in AXIS_NAMES}
    base.update(overrides)
    return SimpleNamespace(**base)


class _ModelStub:
    """A *declared* model client (producer='model')."""

    producer = "model"

    def __init__(self, payload: SimpleNamespace | None = None, exc: Exception | None = None):
        self.payload = payload
        self.exc = exc
        self.calls = 0
        self.schema = None
        self.messages = None

    def call_json(self, messages, schema, **kwargs):  # noqa: ANN001, ANN003
        self.calls += 1
        self.schema = schema
        self.messages = messages
        if self.exc is not None:
            raise self.exc
        return self.payload


class _UndeclaredStub:
    """A client that declares nothing at all — fail-closed => producer 'unknown'."""

    def __init__(self, payload: SimpleNamespace):
        self.payload = payload
        self.calls = 0

    def call_json(self, messages, schema, **kwargs):  # noqa: ANN001, ANN003
        self.calls += 1
        return self.payload


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    """A tiny read-only-style target tree with a licence and a short file."""
    (tmp_path / "pkg.json").write_text(
        '{\n  "name": "demo",\n  "license": "MIT",\n  "version": "1.0.0"\n}\n',
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\nshort file\n", encoding="utf-8")
    return tmp_path


def _claim(cid: int = 1, text: str = "the demo primitive holds", refs=None) -> dict:
    return {
        "id": cid,
        "text": text,
        "provenance_json": json.dumps(refs if refs is not None else []),
    }


def _refs(*refs: str) -> list[dict]:
    return [
        {"ref": ref, "kind": "graph_node", "exists": True, "detail": "lines 3-3 of 5"}
        for ref in refs
    ]


EVIDENCE = [
    {
        "id": 1,
        "source_kind": "web",
        "source_ref": "https://example.test/a",
        "quote": "a supporting quote",
        "sha256": "0" * 64,
    }
]


# --------------------------------------------------------------------------- #
# no client — deterministic, never invented
# --------------------------------------------------------------------------- #


def test_no_client_substantiates_only_real_claim_data(tree: Path) -> None:
    claim = _claim(refs=_refs("pkg.json#L3"))
    result = assess_value(claim, target_root=tree)

    assert isinstance(result, ValueAssessment)
    assert [a.name for a in result.axes] == list(AXIS_NAMES)
    for axis in result.axes:
        if axis.substantiated:
            assert axis.value, f"{axis.name} substantiated without a value"
            assert axis.source, f"{axis.name} substantiated without a source"
        else:
            assert axis.reason, f"{axis.name} unknown without a reason"

    repro = result.by_name("reproducibility")
    assert repro is not None and repro.substantiated
    assert repro.source == "pkg.json#L3"
    ok, detail = verify_axis_source(repro.source, target_root=tree)
    assert ok, detail

    licence = result.by_name("licensing")
    assert licence is not None and licence.substantiated
    assert "MIT" in (licence.value or "")
    assert (licence.source or "").startswith("pkg.json#L")

    # judgement axes are never invented without a client
    for name in ("affected_parties", "unblocks", "cost", "measured_delta"):
        axis = result.by_name(name)
        assert axis is not None and not axis.substantiated
    assert result.producer == "fixture"


def test_no_client_invents_nothing_without_claim_data() -> None:
    result = assess_value(_claim(refs=[]))
    assert [a.name for a in result.axes] == list(AXIS_NAMES)
    assert result.substantiated_count == 0
    assert result.unknown_count == 6
    assert all(a.reason for a in result.axes)
    # nothing may carry a value without a source
    assert all(a.source is None for a in result.axes)


def test_measured_delta_only_from_a_verifiable_stored_result() -> None:
    claim = _claim(refs=[])
    unverifiable = [{"claim_id": 1, "metric": "p99 latency", "value": -42, "unit": "ms"}]
    assert assess_value(claim, results=unverifiable).by_name("measured_delta").substantiated is False

    verifiable = [
        {"claim_id": 1, "metric": "p99 latency", "value": -42, "unit": "ms", "source": "evidence:1"}
    ]
    axis = assess_value(claim, results=verifiable, evidence=EVIDENCE).by_name("measured_delta")
    assert axis is not None and axis.substantiated
    assert axis.source == "evidence:1"
    assert "42" in (axis.value or "")


# --------------------------------------------------------------------------- #
# fabricated sources are rejected
# --------------------------------------------------------------------------- #


def test_fabricated_span_is_rejected(tree: Path) -> None:
    stub = _ModelStub(
        _payload(affected_parties=_axis("everyone", "README.md#L99999-L100000"))
    )
    result = assess_value(_claim(refs=[]), client=stub, target_root=tree)

    axis = result.by_name("affected_parties")
    assert axis is not None
    assert axis.substantiated is False
    assert axis.value is None
    assert "rejected" in (axis.reason or "")
    assert result.substantiated_count == 0
    assert any(d.get("axis") == "affected_parties" for d in result.degradations)


def test_nonexistent_evidence_id_is_rejected() -> None:
    stub = _ModelStub(_payload(licensing=_axis("MIT", "evidence:999")))
    result = assess_value(_claim(refs=[]), client=stub, evidence=EVIDENCE)

    axis = result.by_name("licensing")
    assert axis is not None and axis.substantiated is False
    assert "does not exist" in (axis.reason or "")
    assert result.substantiated_count == 0
    assert any(d.get("axis") == "licensing" for d in result.degradations)


# --------------------------------------------------------------------------- #
# model path: sources required, producers declared
# --------------------------------------------------------------------------- #


def test_unsourced_axes_are_downgraded() -> None:
    """GUARD (a): an axis without a usable source is unknown, with a reason."""
    stub = _ModelStub(
        _payload(
            affected_parties=_axis("operators of the demo", "evidence:1"),
            unblocks=_axis("a decision"),  # no source
            measured_delta=_axis(""),  # nothing
            reproducibility=_axis("re-run it"),  # no source
            cost=_axis("cheap"),  # no source
            licensing=_axis("MIT"),  # no source
        )
    )
    result = assess_value(_claim(refs=[]), client=stub, evidence=EVIDENCE)

    assert result.model_calls == 1
    assert stub.calls == 1
    assert stub.schema is not None  # one strict-schema call

    kept = result.by_name("affected_parties")
    assert kept is not None and kept.substantiated and kept.source == "evidence:1"
    assert kept.producer == "model"
    assert result.substantiated_count == 1
    assert result.unknown_count == 5
    for name in ("unblocks", "measured_delta", "reproducibility", "cost", "licensing"):
        axis = result.by_name(name)
        assert axis is not None and not axis.substantiated
        assert axis.reason, f"{name} was downgraded without a reason"
    # the four that carried a value but no source must say exactly that
    for name in ("unblocks", "reproducibility", "cost", "licensing"):
        assert "source" in (result.by_name(name).reason or "")
    # every axis is still present
    assert [a.name for a in result.axes] == list(AXIS_NAMES)


def test_undeclared_client_is_unknown_and_non_model() -> None:
    """Fail-closed: an undeclared client is 'unknown', never 'model'."""
    stub = _UndeclaredStub(_payload(affected_parties=_axis("everyone", "evidence:1")))
    result = assess_value(_claim(refs=[]), client=stub, evidence=EVIDENCE)

    assert result.producer == "unknown"
    assert result.substantiated_count == 0
    assert all(a.producer != "model" for a in result.axes)
    assert stub.calls == 0, "an unattributable client must not even be called"
    assert result.degradations


def test_truncation_yields_all_unknown() -> None:
    exc = UnparseableOutput(
        raw_text="",
        last_error="finish_reason=length with empty content",
        attempts=2,
        schema_name="_AxesOut",
    )
    stub = _ModelStub(exc=exc)
    result = assess_value(_claim(refs=[]), client=stub)

    assert [a.name for a in result.axes] == list(AXIS_NAMES)
    assert result.substantiated_count == 0
    assert result.unknown_count == 6
    assert any(d.get("truncated") is True for d in result.degradations)

    # the same via an explicit truncated payload
    truncated = SimpleNamespace(finish_reason="length", **{n: _axis() for n in AXIS_NAMES})
    result2 = assess_value(_claim(refs=[]), client=_ModelStub(truncated))
    assert result2.unknown_count == 6
    assert any(d.get("truncated") is True for d in result2.degradations)


# --------------------------------------------------------------------------- #
# report level: determinism and counts
# --------------------------------------------------------------------------- #


def _three_claims() -> list[dict]:
    return [
        _claim(3, "third", _refs("pkg.json#L3")),
        _claim(1, "first", _refs("pkg.json#L3")),
        _claim(2, "second", _refs("README.md#L1-L2")),
    ]


def test_values_jsonl_is_deterministic(tree: Path, tmp_path: Path) -> None:
    claims = _three_claims()
    r1 = assess_values(claims, target_root=tree, out_dir=tmp_path / "o1")
    r2 = assess_values(claims, target_root=tree, out_dir=tmp_path / "o2")

    b1 = (Path(r1.run_dir) / "values.jsonl").read_bytes()
    b2 = (Path(r2.run_dir) / "values.jsonl").read_bytes()
    assert b1 == b2, "identical inputs must produce byte-identical values.jsonl"
    assert b1.endswith(b"\n")
    assert r1.run_key == r2.run_key
    assert len(b1.decode().strip().splitlines()) == r1.claims_assessed == 3


def test_report_counts_match_jsonl(tree: Path, tmp_path: Path) -> None:
    report = assess_values(_three_claims(), target_root=tree, out_dir=tmp_path / "out")
    assert isinstance(report, ValueReport)

    rows = (Path(report.run_dir) / "values.jsonl").read_text("utf-8").strip().splitlines()
    assert report.substantiated + report.unknown == len(rows) * 6

    on_disk = json.loads((Path(report.run_dir) / "report.json").read_text("utf-8"))
    assert on_disk["substantiated"] == report.substantiated
    assert on_disk["unknown"] == report.unknown
    assert on_disk["claims_assessed"] == len(rows)
    assert set(on_disk["axes_by_name"]) == set(AXIS_NAMES)
    per_axis = sum(v["substantiated"] + v["unknown"] for v in on_disk["axes_by_name"].values())
    assert per_axis == report.substantiated + report.unknown
    # the store gap is reported, not dropped
    assert "no value table" in on_disk["store_gap"]
    assert "schema v3" in on_disk["store_gap"]
    assert (Path(report.run_dir) / "VALUE.md").is_file()


class BudgetExhausted(Exception):
    """Local stand-in so ``type(exc).__name__`` matches the real contract."""


class _Budget:
    def __init__(self, limit: int = 2):
        self.calls = 0
        self.limit = limit

    def check(self) -> None:
        self.calls += 1
        if self.calls > self.limit:
            raise BudgetExhausted("stop")

    def begin_call(self) -> None:
        pass


def test_budget_exhausted_marks_partial_and_keeps_work(tree: Path, tmp_path: Path) -> None:
    report = assess_values(
        _three_claims(),
        target_root=tree,
        out_dir=tmp_path / "b",
        client=_ModelStub(_payload()),
        budget=_Budget(limit=2),
    )
    assert report.partial is True
    assert report.claims_assessed == 2  # what was done is kept
    assert any(d.get("stage") == "budget" for d in report.degradations)
