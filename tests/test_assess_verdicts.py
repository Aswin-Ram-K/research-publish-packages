"""Verdict tests for the assessment stage (unit U4.1).

Offline: a stub client, fake search and fake fetcher are injected.  The stub
client counts its calls, so "no evidence => no LLM verdict" is a real assertion
rather than a comment.

Two honesty guards live here (both also documented in
``tests/test_assess_evidence.py``); the red->green transcript with sha256
before/after and a bit-identical restore is at ``state/logs/U4.1-redgreen.sh``:

**Guard (a) -- degraded search => never a positive verdict.**
Reverting the degraded classification in :mod:`resextract.assess.evidence`
(so a broken empty is read like a clean one) turns
``test_degraded_searches_never_produce_a_positive_verdict`` red.

**Guard (b) -- no evidence => no LLM verdict.**
Gate 1 of :func:`resextract.assess.verdicts.assess_claim` must short-circuit
*before* the client is consulted; the counter stays 0.  Reverting gate 1
(``if not gather.records``) turns ``test_no_evidence_never_calls_the_llm`` red,
because the client is then called for a claim with nothing behind it.

**Guard (c) -- the producer default fails closed (U4.3).**  An *undeclared*
client must resolve to ``"unknown"`` (non-model, capped at ``EXTENDS``).
Reverting ``DEFAULT_CLIENT_PRODUCER`` from ``"unknown"`` to ``"model"`` turns
``test_undeclared_client_is_capped_and_recorded_unknown`` red: the bare
``call_json``-only client's ``CONFIRMS`` is then accepted uncapped.

**Guard (d) -- a producer declaration is validated, not coerced (U4.3).**
``_validate_declaration`` must raise :class:`ProducerDeclarationError` for a
declaration outside ``PRODUCER_VOCAB``.  Reverting its body to
``return str(declared)`` turns
``test_out_of_vocabulary_declaration_is_rejected`` red, because ``"gpt"``,
``"Model"`` and ``""`` are then silently accepted as producer values.

Both guards were re-run red, then green, with sha256 before/after and a
bit-identical restore: ``state/logs/U4.3-redgreen.txt``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from resextract import store
from resextract.assess.evidence import EvidenceRecord, GatherResult, gather_evidence
from resextract.assess.verdicts import (
    PRODUCER_VOCAB,
    PROMPT_VERSION,
    ProducerDeclarationError,
    _client_producer,
    assess_claim,
    assess_claims,
    may_back_model_claim,
)
from resextract.llm import Budget
from resextract.web.fetch import FetchMeta, FetchResult
from resextract.web.search import Result, SearchOutcome

CLAIM_TEXT = "the alpha_widget_bridge invariant still holds in the projector_module"
PAGE_TEXT = (
    "The alpha_widget_bridge invariant is enforced by the projector_module.\n" * 8
)
ENGINE_REASON = (
    "1 engine(s) reported themselves unresponsive (google: access denied) -- "
    "SearXNG said the search was broken"
)


# --------------------------------------------------------------------------- #
# fakes
# --------------------------------------------------------------------------- #


class CountingClient:
    """A stub client: records every call, so zero-call claims are provable."""

    def __init__(
        self,
        evidence_ids: list[int] | None = None,
        verdict: str = "CONFIRMS",
        producer: str = "replay",
    ):
        self.calls: list[dict] = []
        self._ids = evidence_ids if evidence_ids is not None else []
        self._verdict = verdict
        self.producer = producer

    def call_json(self, messages, schema, **kwargs):  # noqa: ANN001
        self.calls.append({"messages": messages, "kwargs": kwargs})
        return schema(
            verdict=self._verdict,
            rationale="stubbed reasoning",
            evidence_ids=list(self._ids),
        )


class FailingClient:
    producer = "replay"

    def call_json(self, messages, schema, **kwargs):  # noqa: ANN001
        raise RuntimeError("endpoint down")


def make_outcome(
    query: str,
    results: list[Result] | None = None,
    *,
    ok: bool = True,
    degraded: bool = False,
    absence_is_meaningful: bool = False,
    absence_reason: str | None = None,
    unresponsive_engines: list[str] | None = None,
) -> SearchOutcome:
    return SearchOutcome(
        query=query,
        results=list(results or []),
        ok=ok,
        degraded=degraded,
        error=ENGINE_REASON if degraded else None,
        degradation_reason=ENGINE_REASON if degraded else None,
        absence_is_meaningful=absence_is_meaningful,
        absence_reason=absence_reason,
        unresponsive_engines=list(unresponsive_engines or []),
    )


DEGRADED_EMPTY = make_outcome(
    "q",
    [],
    degraded=True,
    absence_is_meaningful=False,
    absence_reason=ENGINE_REASON,
    unresponsive_engines=["google: access denied"],
)


class FakeSearch:
    def __init__(self, outcomes: list[SearchOutcome]) -> None:
        self.outcomes = list(outcomes)
        self.queries: list[str] = []

    def search(self, query: str, **kwargs: object) -> SearchOutcome:
        self.queries.append(query)
        if self.outcomes:
            return self.outcomes.pop(0)
        return DEGRADED_EMPTY


def make_fetch(url: str, text: str, **over: object) -> FetchResult:
    import hashlib

    meta = FetchMeta(
        url=url,
        title="A page",
        text=text,
        sha256=hashlib.sha256(text.encode()).hexdigest(),
        fetched_at="2024-03-04T00:00:00+00:00",
        kind="html",
        page_date="2024-03-04",
        http_status=200,
        bytes_in=len(text),
        cache_path="state/webcache/x.txt",
    )
    return FetchResult(ok=True, meta=meta, **over)  # type: ignore[arg-type]


class FakeFetcher:
    def __init__(self, results: dict[str, FetchResult]) -> None:
        self.results = dict(results)

    def fetch(self, url: str, **kwargs: object) -> FetchResult:
        return self.results.get(url, FetchResult(ok=False, error="no fake result"))


URL = "https://example.test/bridge"


def gathering_search_and_fetcher() -> tuple[FakeSearch, FakeFetcher]:
    return (
        FakeSearch([make_outcome("q", [Result(title="h", url=URL)])]),
        FakeFetcher({URL: make_fetch(URL, PAGE_TEXT)}),
    )


def claim_dict(claim_id: int, text: str = CLAIM_TEXT) -> dict[str, object]:
    return {"claim_id": claim_id, "text": text, "kind": "architectural"}


@pytest.fixture()
def store_path(tmp_path: Path) -> Path:
    return store.init_db(tmp_path / "assess.sqlite")


def seed_claims(path: Path, texts: list[str]) -> list[dict[str, object]]:
    con = store.connect(path)
    try:
        out = []
        for text in texts:
            cid = store.insert_claim(
                con, kind="architectural", text=text, provenance_json=[{"ref": "fixture"}]
            )
            out.append(claim_dict(cid, text))
        con.commit()
    finally:
        con.close()
    return out


# --------------------------------------------------------------------------- #
# guard (b): no evidence => no LLM verdict
# --------------------------------------------------------------------------- #


def test_no_evidence_never_calls_the_llm() -> None:
    """Guard (b): an empty gather short-circuits gate 1 before the client."""
    # search returns hits but every fetch fails -> zero records, no degradation
    search = FakeSearch([make_outcome("q", [Result(title="h", url=URL)])])
    fetcher = FakeFetcher({URL: FetchResult(ok=False, error="connection refused")})
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    assert gather.records == []
    assert gather.degraded_searches == []

    client = CountingClient(evidence_ids=[1])
    verdict = assess_claim(claim_dict(1), gather, client=client)
    assert client.calls == [], "a claim with no evidence must not reach the model"
    assert verdict.verdict == "UNVERIFIED"
    assert verdict.producer == "none"
    assert verdict.model_calls == 0


def test_all_degraded_searches_name_the_engine_errors() -> None:
    gather = gather_evidence(
        claim_dict(1),
        search=FakeSearch([DEGRADED_EMPTY]),
        fetcher=FakeFetcher({}),
        max_queries=1,
    )
    verdict = assess_claim(claim_dict(1), gather, client=CountingClient())
    assert verdict.verdict == "UNVERIFIED"
    assert "access denied" in verdict.rationale
    assert "degraded" in verdict.rationale
    assert verdict.verdict not in ("CONFIRMS", "EXTENDS")


# --------------------------------------------------------------------------- #
# guard (a): degraded search never yields a positive verdict
# --------------------------------------------------------------------------- #


def test_degraded_searches_never_produce_a_positive_verdict() -> None:
    gather = gather_evidence(
        claim_dict(1), search=FakeSearch([DEGRADED_EMPTY]), fetcher=FakeFetcher({}), max_queries=1
    )
    assert gather.degraded_searches, "the broken search must be classified degraded"
    verdict = assess_claim(claim_dict(1), gather, client=CountingClient(evidence_ids=[1]))
    assert verdict.verdict == "UNVERIFIED"
    assert verdict.verdict not in ("CONFIRMS", "EXTENDS")
    assert "no prior art exists" not in verdict.rationale.lower()


# --------------------------------------------------------------------------- #
# gate 3: the model path, constrained to cite evidence
# --------------------------------------------------------------------------- #


def test_llm_verdict_citing_zero_evidence_is_rejected() -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    assert len(gather.records) == 1

    client = CountingClient(evidence_ids=[], verdict="CONFIRMS")
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert len(client.calls) == 1
    assert verdict.verdict == "UNVERIFIED"
    assert verdict.rationale == "no evidence cited"
    assert verdict.rejected is True
    assert verdict.evidence_ids == []


def test_llm_verdict_citing_a_real_evidence_id_is_accepted() -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    # a *model*-produced client may assert CONFIRMS (with a cited id); a replay
    # client is capped at EXTENDS and is covered by its own test below.
    client = CountingClient(evidence_ids=[7], verdict="CONFIRMS", producer="model")
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert verdict.verdict == "CONFIRMS"
    assert verdict.evidence_ids == [7]
    assert verdict.rejected is False
    assert verdict.producer == "model"
    assert verdict.model_calls == 1


def test_llm_citation_of_an_unknown_id_is_rejected() -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    client = CountingClient(evidence_ids=[999], verdict="CONFIRMS")
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert verdict.verdict == "UNVERIFIED"
    assert verdict.rationale == "no evidence cited"
    assert verdict.rejected is True


def test_a_replay_client_cannot_assert_confirms() -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    client = CountingClient(evidence_ids=[7], verdict="CONFIRMS")  # producer == "replay"
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert verdict.verdict == "EXTENDS", "a replay path may not assert CONFIRMS"
    assert verdict.producer == "replay"
    assert "capped at EXTENDS" in verdict.rationale
    assert verdict.model_calls == 0 and verdict.replay_calls == 1


def test_model_path_failure_falls_back_to_unverified() -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    verdict = assess_claim(claim_dict(1), gather, client=FailingClient(), evidence_ids=[7])
    assert verdict.verdict == "UNVERIFIED"
    # U4.3: ``run_producer`` records what actually ran (the declaring replay
    # client was called) while ``client_producer`` records what it declared.
    # The old hardcoded "none" here is what made the two differently-scoped
    # fields confusable.
    assert verdict.run_producer == "replay" and verdict.client_producer == "replay"
    assert "no usable verdict" in verdict.rationale


# --------------------------------------------------------------------------- #
# gate 4: deterministic, never CONFIRMS
# --------------------------------------------------------------------------- #


def test_no_client_never_confirms_and_caps_at_extends() -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    assert len(gather.records) == 1
    verdict = assess_claim(claim_dict(1), gather, evidence_ids=[3])
    assert verdict.verdict == "EXTENDS"
    assert verdict.verdict != "CONFIRMS"
    assert verdict.evidence_ids == [3]
    assert verdict.producer == "none"
    assert "never asserts CONFIRMS" in verdict.rationale


def test_deterministic_path_refuses_a_positive_verdict_without_a_citable_id() -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    verdict = assess_claim(claim_dict(1), gather)
    assert verdict.verdict == "UNVERIFIED"
    assert "no evidence ids are available to cite" in verdict.rationale


def test_weak_evidence_does_not_extend() -> None:
    url = "https://example.test/unrelated"
    gather = gather_evidence(
        claim_dict(1),
        search=FakeSearch([make_outcome("q", [Result(title="h", url=url)])]),
        fetcher=FakeFetcher({url: make_fetch(url, "gardening and weather " * 20)}),
        max_queries=1,
    )
    verdict = assess_claim(claim_dict(1), gather, evidence_ids=[1])
    assert verdict.verdict == "UNVERIFIED"
    assert "key terms" in verdict.rationale


# --------------------------------------------------------------------------- #
# producer on every verdict
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "outcome",
    ["no_records", "degraded", "accepted", "rejected", "deterministic"],
)
def test_producer_is_recorded_on_every_verdict(outcome: str) -> None:
    if outcome == "no_records":
        gather = GatherResult(reasons=["nothing at all"])
        verdict = assess_claim(claim_dict(1), gather, client=CountingClient([1]))
        assert verdict.producer == "none"
    elif outcome == "degraded":
        gather = gather_evidence(
            claim_dict(1), search=FakeSearch([DEGRADED_EMPTY]), fetcher=FakeFetcher({})
        )
        verdict = assess_claim(claim_dict(1), gather, client=CountingClient([1]))
        assert verdict.producer == "none"
    elif outcome == "accepted":
        search, fetcher = gathering_search_and_fetcher()
        gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
        verdict = assess_claim(
            claim_dict(1), gather, client=CountingClient([1], "EXTENDS"), evidence_ids=[1]
        )
        assert verdict.producer == "replay"
    elif outcome == "rejected":
        search, fetcher = gathering_search_and_fetcher()
        gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
        verdict = assess_claim(
            claim_dict(1), gather, client=CountingClient([], "CONFIRMS"), evidence_ids=[1]
        )
        assert verdict.run_producer == "replay" and verdict.rejected
        assert verdict.client_producer == "replay"
    else:
        search, fetcher = gathering_search_and_fetcher()
        gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
        verdict = assess_claim(claim_dict(1), gather, evidence_ids=[1])
        assert verdict.producer == "none"
    assert verdict.producer in ("model", "replay", "none")
    assert verdict.checked_at


# --------------------------------------------------------------------------- #
# assess_claims: store writes, isolation, budget, resume, outputs
# --------------------------------------------------------------------------- #


def test_assess_claims_persists_evidence_and_verdict_rows(store_path: Path, tmp_path: Path) -> None:
    claims = seed_claims(store_path, [CLAIM_TEXT])
    search, fetcher = gathering_search_and_fetcher()
    report = assess_claims(
        claims,
        search=search,
        fetcher=fetcher,
        store_path=store_path,
        out_dir=tmp_path / "assess",
        max_queries=1,
    )
    assert report.claims_assessed == 1
    assert report.by_verdict == {"CONFIRMS": 0, "EXTENDS": 1, "CONTRADICTS": 0, "UNVERIFIED": 0}
    assert report.evidence_rows == 1
    assert report.searches == 1 and report.fetches == 1
    assert report.model_calls == 0 and report.producer == "none"

    con = store.connect(store_path)
    try:
        assert store.count(con, "evidence") == 1
        assert store.count(con, "verdicts") == 1
        evidence_ids = [r["id"] for r in con.execute("SELECT id FROM evidence")]
        verdict_row = con.execute("SELECT * FROM verdicts").fetchone()
        assert json.loads(verdict_row["evidence_ids_json"]) == evidence_ids
        assert verdict_row["verdict"] == "EXTENDS"
        assert verdict_row["claim_id"] == claims[0]["claim_id"]
        ev = con.execute("SELECT * FROM evidence").fetchone()
        assert ev["source_ref"] == URL and ev["sha256"] and ev["quote"] in PAGE_TEXT
    finally:
        con.close()

    run_dir = Path(report.run_dir)
    for name in ("EVIDENCE.md", "VERDICTS.md", "evidence.jsonl", "verdicts.jsonl", "report.json"):
        assert (run_dir / name).exists(), name
    assert URL in (run_dir / "EVIDENCE.md").read_text()
    assert "2024-03-04" in (run_dir / "EVIDENCE.md").read_text()
    body = json.loads((run_dir / "report.json").read_text())
    assert body["claims_assessed"] == 1 and body["producer"] == "none"


def test_assess_claims_is_isolated_per_claim(store_path, tmp_path, monkeypatch) -> None:
    claims = seed_claims(store_path, [CLAIM_TEXT, "a second claim about widgets"])
    from resextract.assess import verdicts as verdicts_mod

    real = verdicts_mod.gather_evidence

    def flaky(claim, **kwargs):  # noqa: ANN001
        if "second" in str(claim.get("text") if isinstance(claim, dict) else claim):
            raise RuntimeError("this claim exploded")
        return real(claim, **kwargs)

    monkeypatch.setattr(verdicts_mod, "gather_evidence", flaky)
    search, fetcher = gathering_search_and_fetcher()
    report = assess_claims(
        claims,
        search=search,
        fetcher=fetcher,
        store_path=store_path,
        out_dir=tmp_path / "a",
        max_queries=1,
    )
    assert report.claims_assessed == 1, "the good claim must still be assessed"
    assert len(report.degradations) == 1
    assert "exploded" in report.degradations[0]["error"]


def test_budget_exhaustion_stops_and_keeps_everything(store_path, tmp_path) -> None:
    claims = seed_claims(store_path, [CLAIM_TEXT, CLAIM_TEXT])
    search, fetcher = gathering_search_and_fetcher()
    client = CountingClient(evidence_ids=[1], verdict="EXTENDS")
    report = assess_claims(
        claims,
        client=client,
        search=search,
        fetcher=fetcher,
        store_path=store_path,
        budget=Budget(max_calls=2),
        out_dir=tmp_path / "a",
        max_queries=1,
    )
    assert report.partial is True
    assert report.claims_assessed == 1
    assert len(report.verdicts) == 1
    assert report.verdicts[0]["verdict"] == "EXTENDS"
    # one call rewrote the query, one judged the claim: both are charged, so the
    # second claim is stopped by the ceiling rather than silently spending more.
    assert len(client.calls) == 2
    con = store.connect(store_path)
    try:
        assert store.count(con, "verdicts") == 1, "prior rows must be persisted"
    finally:
        con.close()


def test_second_run_over_unchanged_inputs_makes_zero_searches(store_path, tmp_path) -> None:
    claims = seed_claims(store_path, [CLAIM_TEXT])
    out = tmp_path / "assess"
    search1, fetcher1 = gathering_search_and_fetcher()
    first = assess_claims(
        claims,
        search=search1,
        fetcher=fetcher1,
        store_path=store_path,
        out_dir=out,
        max_queries=1,
    )
    assert first.searches == 1 and len(search1.queries) == 1

    search2 = FakeSearch([])
    second = assess_claims(
        claims,
        search=search2,
        fetcher=FakeFetcher({}),
        store_path=store_path,
        out_dir=out,
        max_queries=1,
    )
    assert search2.queries == [], "a resumed run must make zero searches"
    assert second.searches == 0
    assert second.resumed_claims == 1
    assert second.claims_assessed == 1
    assert second.by_verdict == first.by_verdict
    assert second.run_key == first.run_key
    assert second.evidence_rows == 1, "resumed evidence must still be reported"
    assert second.verdicts == first.verdicts
    assert (Path(second.run_dir) / "EVIDENCE.md").read_text().count(URL) == 1


def test_prompt_version_change_invalidates_the_resume(store_path, tmp_path) -> None:
    claims = seed_claims(store_path, [CLAIM_TEXT])
    out = tmp_path / "assess"
    s1, f1 = gathering_search_and_fetcher()
    assess_claims(
        claims, search=s1, fetcher=f1, store_path=store_path, out_dir=out, max_queries=1
    )
    s2 = FakeSearch([make_outcome("q", [Result(title="h", url=URL)])])
    report = assess_claims(
        claims,
        search=s2,
        fetcher=FakeFetcher({URL: make_fetch(URL, PAGE_TEXT)}),
        store_path=store_path,
        out_dir=out,
        prompt_version="assess-v2",
        max_queries=1,
    )
    assert len(s2.queries) == 1, "a new prompt version must re-search"
    assert report.resumed_claims == 0


def test_report_is_deterministic_across_identical_runs(tmp_path) -> None:
    """Two identical runs over identical inputs produce identical reports.

    Each run gets its own freshly seeded store, so the evidence ids (store
    rowids) are identical too and any real nondeterminism still shows up.
    """
    outs = []
    for i in range(2):
        path = store.init_db(tmp_path / f"store{i}.sqlite")
        claims = seed_claims(path, [CLAIM_TEXT])
        search, fetcher = gathering_search_and_fetcher()
        report = assess_claims(
            claims,
            search=search,
            fetcher=fetcher,
            store_path=path,
            out_dir=tmp_path / f"run{i}",
            max_queries=1,
        )
        body = report.as_dict()
        body.pop("wall_s")
        body.pop("run_dir")
        outs.append(json.dumps(body, sort_keys=True))
    assert outs[0] == outs[1]


def test_verdict_vocabulary_matches_the_store() -> None:
    from resextract.assess.verdicts import VERDICT_VOCAB

    assert VERDICT_VOCAB == ("CONFIRMS", "EXTENDS", "CONTRADICTS", "UNVERIFIED")
    assert PROMPT_VERSION.startswith("assess-")
    for verdict in VERDICT_VOCAB:
        assert verdict in store.VERDICT_VOCAB
    assert isinstance(EvidenceRecord, type)


# --------------------------------------------------------------------------- #
# U4.3: the producer declaration is a load-bearing safety gate
# --------------------------------------------------------------------------- #
#
# Guard (c) -- the fail-closed default.  An undeclared client resolves to
# "unknown" (non-model) and is capped.  Reverting DEFAULT_CLIENT_PRODUCER to
# "model" turns test_undeclared_client_is_capped_and_recorded_unknown red.
#
# Guard (d) -- the vocabulary rejection.  An out-of-vocabulary declaration
# raises ProducerDeclarationError instead of being coerced.  Reverting
# _validate_declaration to `return str(declared)` turns
# test_out_of_vocabulary_declaration_is_rejected red.
#
# sha256 before/after + bit-identical restore: state/logs/U4.3-redgreen.txt


class BareClient:
    """Undeclared *by omission*: only ``call_json``, no producer marker at all."""

    def __init__(self, verdict: str = "CONFIRMS", evidence_ids: list[int] | None = None):
        self.calls: list[dict] = []
        self._verdict = verdict
        self._ids = list(evidence_ids if evidence_ids is not None else [7])

    def call_json(self, messages, schema, **kwargs):  # noqa: ANN001
        self.calls.append({"messages": messages, "kwargs": kwargs})
        return schema(
            verdict=self._verdict,
            rationale="undeclared client reasoning",
            evidence_ids=list(self._ids),
        )


def test_undeclared_client_is_capped_and_recorded_unknown() -> None:
    """**The central U4.3 test: omission is not a model declaration.**

    The client below declares nothing.  Before U4.3 ``_client_producer``
    defaulted it to ``"model"``, so its ``CONFIRMS`` was accepted uncapped; the
    cap must not rest on the client's self-declaration.
    """
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    client = BareClient()
    assert not hasattr(client, "producer"), "the client under test must be undeclared"
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert len(client.calls) == 1, "the undeclared client is still consulted"
    assert verdict.verdict == "EXTENDS", "an undeclared client may never publish CONFIRMS"
    assert verdict.client_producer == "unknown"
    assert verdict.client_producer != "none", "undeclared is unknown, never none"
    assert verdict.run_producer == "replay", "an unknown client counts as non-model"
    assert verdict.model_calls == 0 and verdict.replay_calls == 1
    assert "capped at EXTENDS" in verdict.rationale


def test_only_an_explicit_model_declaration_enables_confirms() -> None:
    """Exactly ``producer="model"`` -- with a genuine request -- grants standing."""
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    client = CountingClient(evidence_ids=[7], verdict="CONFIRMS", producer="model")
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert len(client.calls) == 1, "model standing also requires a real request"
    assert verdict.verdict == "CONFIRMS"
    assert verdict.client_producer == "model" and verdict.run_producer == "model"
    assert verdict.model_calls == 1 and verdict.replay_calls == 0
    assert may_back_model_claim(verdict.client_producer) is True


@pytest.mark.parametrize("declared", ["replay", "fixture"])
def test_declaring_replay_or_fixture_is_capped(declared: str) -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    client = CountingClient(evidence_ids=[7], verdict="CONFIRMS", producer=declared)
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert verdict.verdict == "EXTENDS"
    assert verdict.client_producer == declared and verdict.run_producer == "replay"
    assert may_back_model_claim(verdict.client_producer) is False


@pytest.mark.parametrize("declared", ["gpt", "Model", "MODEL", "", "none", "mixed"])
def test_out_of_vocabulary_declaration_is_rejected(declared: str) -> None:
    """A declaration outside the shared vocabulary is a typed error, not a guess.

    ``""`` is the dangerous case: a declaration of *nothing* must not be read as
    a model.  ``"none"`` is included because U4.3 removed that value from the
    client side entirely -- the store vocabulary has no such producer.
    """
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    client = CountingClient(evidence_ids=[7], verdict="CONFIRMS", producer=declared)
    with pytest.raises(ProducerDeclarationError) as excinfo:
        assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert excinfo.value.allowed == PRODUCER_VOCAB
    assert repr(declared) in str(excinfo.value)
    assert client.calls == [], "the declaration is validated before any request"


def test_producer_hint_is_validated_and_cannot_upgrade_standing() -> None:
    """U2.6 ITEM 2: the client's own declaration is authoritative.

    A ``producer_hint`` may never **upgrade** standing -- it may be ignored or
    deny/downgrade.  ``BareClient`` declares nothing, so ``producer_hint="model"``
    is ignored and its positive verdict is capped rather than published as
    ``CONFIRMS``.  (U4.3's test asserted the opposite; that was the bypass.)
    """
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    with pytest.raises(ProducerDeclarationError):
        assess_claim(
            claim_dict(1), gather, client=BareClient(), evidence_ids=[7], producer_hint="Model"
        )
    hinted = assess_claim(
        claim_dict(1), gather, client=BareClient(), evidence_ids=[7], producer_hint="model"
    )
    assert hinted.verdict == "EXTENDS", "a hint may not upgrade an undeclared client"
    assert hinted.client_producer == "unknown"


def test_vocabulary_matches_the_store_and_exactly_model_grants_standing() -> None:
    assert PRODUCER_VOCAB == ("model", "replay", "fixture", "unknown")
    assert PRODUCER_VOCAB == store.PRODUCER_VOCAB, "reuse the store vocabulary verbatim"
    assert "none" not in PRODUCER_VOCAB
    for producer in PRODUCER_VOCAB:
        assert may_back_model_claim(producer) is (producer == "model")
    assert may_back_model_claim(None) is False
    assert may_back_model_claim("Model") is False


def test_report_producer_fields_are_distinguishable(store_path, tmp_path) -> None:
    """``run_producer`` (what ran) vs ``client_producer`` (what was declared).

    An undeclared client yields ``client_producer == "unknown"`` -- never
    ``"none"``, which stays reserved for the run-scoped "no client was
    consulted" case, so the two fields differ by name *and* by value.
    """
    claims = seed_claims(store_path, [CLAIM_TEXT])
    search, fetcher = gathering_search_and_fetcher()
    report = assess_claims(
        claims,
        client=BareClient(evidence_ids=[1]),  # the freshly seeded store's rowid
        search=search,
        fetcher=fetcher,
        store_path=store_path,
        out_dir=tmp_path / "a",
        max_queries=1,
    )
    body = report.as_dict()
    assert body["client_producer"] == "unknown"
    assert body["run_producer"] == "replay"
    assert body["client_producer"] != "none"
    assert body["client_producer"] != body["run_producer"]
    assert body["producer"] == body["run_producer"], "legacy alias mirrors run_producer"
    assert body["by_verdict"]["CONFIRMS"] == 0, "an undeclared client published nothing positive"
    row = body["verdicts"][0]
    assert row["verdict"] == "EXTENDS" and row["client_producer"] == "unknown"
    assert row["run_producer"] == "replay" and row["producer"] == row["run_producer"]
    on_disk = json.loads((Path(report.run_dir) / "report.json").read_text())
    assert on_disk["client_producer"] == "unknown" and on_disk["run_producer"] == "replay"
    assert _client_producer(BareClient(), None) == "unknown"


def test_mixed_real_and_fabricated_citations_keep_only_the_real_one() -> None:
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    client = CountingClient(evidence_ids=[7, 999], verdict="CONFIRMS", producer="model")
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert verdict.verdict == "CONFIRMS"
    assert verdict.evidence_ids == [7], "a fabricated id never rides along with a real one"


@pytest.mark.parametrize("ids", [[], [7], [7, 8, 9]])
def test_no_client_path_never_confirms(ids: list[int]) -> None:
    """No client at all: no evidence-id shape may yield CONFIRMS."""
    search, fetcher = gathering_search_and_fetcher()
    gather = gather_evidence(claim_dict(1), search=search, fetcher=fetcher, max_queries=1)
    verdict = assess_claim(claim_dict(1), gather, evidence_ids=ids)
    assert verdict.verdict in ("EXTENDS", "UNVERIFIED")
    assert verdict.verdict != "CONFIRMS"
    assert verdict.client_producer is None, "no client verdict => no declaration"
    assert verdict.run_producer == "none"


def test_all_degraded_refuses_before_any_client_is_consulted() -> None:
    gather = gather_evidence(
        claim_dict(1), search=FakeSearch([DEGRADED_EMPTY]), fetcher=FakeFetcher({}), max_queries=1
    )
    client = BareClient()
    verdict = assess_claim(claim_dict(1), gather, client=client, evidence_ids=[7])
    assert verdict.verdict == "UNVERIFIED"
    assert client.calls == [], "a degraded/empty gather never reaches the client"
    assert verdict.run_producer == "none" and verdict.client_producer is None
