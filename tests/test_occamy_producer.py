"""U2.4 — the real Occamy client declares ``producer="model"``, truthfully.

The assessment gate is fail-closed: an undeclared client resolves to
``unknown``, is treated as non-model, and any ``CONFIRMS`` it returns is capped
to ``EXTENDS``; only exactly ``producer == "model"`` grants model standing.  The
shipped :class:`~resextract.llm.occamy.OccamyClient` declared nothing, so *no*
client — not even a healthy one — could reach ``CONFIRMS``.  This module pins the
fix and the invariant that keeps it from re-opening the hole.

Everything here runs against ``httpx.MockTransport`` — zero network, zero live
LLM calls.

RED→GREEN guard (a) — *the real client declares model*.
    Reverting the fix (deleting the ``producer`` property / ``makes_requests``
    flag from ``OccamyClient``) makes ``_client_producer(real, None)`` fall back
    to ``unknown`` and cap the verdict, so
    :func:`test_real_client_declares_model` and
    :func:`test_confirms_end_to_end_through_gate` fail.  Real red output
    (``.venv/bin/python -m pytest tests/test_occamy_producer.py -q``)::

        E   AssertionError: assert 'unknown' == 'model'

RED→GREEN guard (b) — *declaring model requires making requests*.
    Reverting the property to an unconditional ``return "model"`` makes a
    request-free subclass read as model-produced, so
    :func:`test_model_declaration_requires_requests` fails.  Real red output::

        E   AssertionError: assert 'model' == 'replay'

Both guards were sha256-recorded before/after and restored bit-identically with
``PYTHONDONTWRITEBYTECODE=1`` and a ``__pycache__`` purge (see
``orchestration/handoffs/U2.4.json``).
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from conftest import chat_response
from resextract.assess.evidence import EvidenceRecord, GatherResult
from resextract.assess.verdicts import (
    ProducerDeclarationError,
    _client_producer,
    assess_claim,
    may_back_model_claim,
)
from resextract.llm import OccamyClient


CLAIM = {
    "claim_id": 1,
    "text": "the alpha_widget_bridge invariant still holds in the projector_module",
    "kind": "architectural",
}
EVIDENCE_ID = 7
VERDICT_JSON = json.dumps(
    {
        "verdict": "CONFIRMS",
        "rationale": "the fetched page states the invariant is enforced",
        "evidence_ids": [EVIDENCE_ID],
    }
)


def outcome_json(verdict: str = "CONFIRMS") -> str:
    return json.dumps(
        {
            "verdict": verdict,
            "rationale": "stubbed reasoning",
            "evidence_ids": [EVIDENCE_ID],
        }
    )


def one_record() -> EvidenceRecord:
    return EvidenceRecord(
        claim_id=1,
        source_kind="web",
        source_ref="https://example.test/bridge",
        sha256="0" * 64,
        quote="The alpha_widget_bridge invariant is enforced by the projector_module.",
        context="a fetched page that states the invariant",
        retrieved_at="2024-03-04T00:00:00+00:00",
        title="A page",
    )


def gather_one() -> GatherResult:
    return GatherResult(records=[one_record()], reasons=["1 clean search"])


def json_handler(payload: str):
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        return chat_response(content=payload)

    return handler


class StubClient:
    """Declares whatever it is told; makes no requests (a caller-side stub)."""

    def __init__(self, producer: str | None = None) -> None:
        if producer is not None:
            self.producer = producer
        self.calls = 0

    def call_json(self, messages, schema, **kwargs):  # noqa: ANN001
        self.calls += 1
        return schema(
            verdict="CONFIRMS", rationale="stubbed", evidence_ids=[EVIDENCE_ID]
        )


class NoRequestOccamyClient(OccamyClient):
    """A genuine subclass that answers locally: it must inherit the *cap*."""

    makes_requests = False

    def call_json(self, messages, schema, **kwargs):  # noqa: ANN001
        return schema(
            verdict="CONFIRMS", rationale="replayed locally", evidence_ids=[EVIDENCE_ID]
        )


class BadVocabOccamyClient(OccamyClient):
    """The real client's declaration site with an out-of-vocabulary value."""

    @property
    def producer(self) -> str:  # type: ignore[override]
        return "Model"  # wrong case: rejected, never normalised


# --------------------------------------------------------------------------- #
# guard (a): the real, request-making client declares model
# --------------------------------------------------------------------------- #


def test_real_client_declares_model(make_client) -> None:
    """RED→GREEN guard (a): a real client resolves to ``model``, predicate true.

    Revert the declaration and this fails with ``'unknown' == 'model'``.
    """
    harness = make_client(json_handler(VERDICT_JSON))
    resolved = _client_producer(harness.client, None)
    assert resolved == "model", (
        "the real, request-making OccamyClient must declare producer='model' "
        f"(got {resolved!r})"
    )
    assert may_back_model_claim(resolved) is True
    # the sync wrapper is the same real producer through the ``.client`` chain
    assert _client_producer(harness.client.sync(), None) == "model"


def test_confirms_end_to_end_through_gate(make_client) -> None:
    """The first legitimate `CONFIRMS`: a real client over a mocked transport."""
    harness = make_client(json_handler(VERDICT_JSON))
    verdict = assess_claim(
        CLAIM,
        gather_one(),
        client=harness.client.sync(),
        evidence_ids=[EVIDENCE_ID],
    )
    assert verdict.verdict == "CONFIRMS", (
        "a genuine, request-making model client must be able to reach CONFIRMS "
        f"(got {verdict.verdict!r}: {verdict.rationale})"
    )
    assert verdict.client_producer == "model"
    assert verdict.run_producer == "model"
    assert verdict.evidence_ids == [EVIDENCE_ID]
    assert verdict.model_calls == 1
    # a real transport request backed it — the declaration is not decorative
    assert len(harness.recorder.requests) == 1


# --------------------------------------------------------------------------- #
# the cap still bites for every non-model path
# --------------------------------------------------------------------------- #


def test_undeclared_client_is_unknown_and_capped() -> None:
    client = StubClient()
    assert _client_producer(client, None) == "unknown"
    assert may_back_model_claim(_client_producer(client, None)) is False
    verdict = assess_claim(CLAIM, gather_one(), client=client, evidence_ids=[EVIDENCE_ID])
    assert verdict.verdict == "EXTENDS"
    assert verdict.client_producer == "unknown"
    assert verdict.model_calls == 0


def test_replay_subclass_inherits_the_cap_not_the_declaration() -> None:
    """A request-free subclass of the real client must not gain ``model``."""
    client = NoRequestOccamyClient(
        transport=httpx.MockTransport(lambda request: chat_response(content=VERDICT_JSON)),
        api_key="local",
    )
    assert isinstance(client, OccamyClient)
    assert client.producer == "replay"
    assert _client_producer(client, None) == "replay"
    assert may_back_model_claim(_client_producer(client, None)) is False
    verdict = assess_claim(CLAIM, gather_one(), client=client, evidence_ids=[EVIDENCE_ID])
    assert verdict.verdict == "EXTENDS"
    assert verdict.client_producer == "replay"
    assert verdict.model_calls == 0
    asyncio.run(client.aclose())


def test_fixture_declaration_is_capped() -> None:
    client = StubClient(producer="fixture")
    assert _client_producer(client, None) == "fixture"
    assert may_back_model_claim(_client_producer(client, None)) is False
    verdict = assess_claim(CLAIM, gather_one(), client=client, evidence_ids=[EVIDENCE_ID])
    assert verdict.verdict == "EXTENDS"
    assert verdict.client_producer == "fixture"


def test_model_declaration_requires_requests(make_client) -> None:
    """RED→GREEN guard (b): declaration and request-making cannot disagree.

    Revert ``producer`` to an unconditional ``"model"`` and this fails with
    ``'model' == 'replay'``: a model declaration without requests would be
    accepted.
    """
    harness = make_client(json_handler(VERDICT_JSON))
    client = NoRequestOccamyClient(
        transport=httpx.MockTransport(lambda request: chat_response(content=VERDICT_JSON)),
        api_key="local",
    )
    assert client.makes_requests is False
    assert client.producer != "model", (
        "a client that declares model but makes no requests must be refused/capped"
    )
    assert _client_producer(client, None) == "replay"
    assert may_back_model_claim(_client_producer(client, None)) is False
    verdict = assess_claim(CLAIM, gather_one(), client=client, evidence_ids=[EVIDENCE_ID])
    assert verdict.verdict == "EXTENDS"
    assert verdict.model_calls == 0
    assert harness.recorder.requests == []
    asyncio.run(client.aclose())


# --------------------------------------------------------------------------- #
# vocabulary and case rule are unchanged (hardening, not loosening)
# --------------------------------------------------------------------------- #


# NOTE: a param literally named "live" is silently skipped by conftest (its live-smoke
# rule), which would leave this guard unrun -- use non-"live" out-of-vocabulary values.
@pytest.mark.parametrize("bad", ["Model", "MODEL", "", "cached", "human", "model "])
def test_out_of_vocabulary_declaration_raises(bad: str) -> None:
    with pytest.raises(ProducerDeclarationError):
        _client_producer(StubClient(producer=bad), None)


def test_real_client_declaration_site_is_validated_too() -> None:
    """The validation applies to the real client's own declaration site."""
    bad = BadVocabOccamyClient(
        transport=httpx.MockTransport(lambda request: chat_response(content=VERDICT_JSON)),
        api_key="local",
    )
    with pytest.raises(ProducerDeclarationError):
        _client_producer(bad, None)
    asyncio.run(bad.aclose())


def test_vocabulary_is_unchanged() -> None:
    from resextract.assess.verdicts import PRODUCER_VOCAB

    assert PRODUCER_VOCAB == ("model", "replay", "fixture", "unknown")
    assert _client_producer(StubClient(producer="model"), None) == "model"
