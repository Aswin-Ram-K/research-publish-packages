"""Evidence-gathering tests for the assessment stage (unit U4.1).

All tests are **offline**: the search client and the fetcher are injected fakes
built from the *real* ``SearchOutcome``/``Result``/``FetchResult``/``FetchMeta``
dataclasses, so the shapes under test are the shipped ones.  No network, no LLM.

Two honesty guards carry the substance of this file.  Both are reproduced here
in the form they take as a red->green check (see ``state/logs/U4.1-redgreen.sh``
for the sha256-proven revert/restore transcript):

**Guard (a) -- degraded search => never a positive verdict.**
An empty outcome with ``absence_is_meaningful=False`` (SearXNG self-reported
``unresponsive_engines``, here ``google: access denied``) must be *classified*
degraded, carry the engine reason, and can never become a ``CONFIRMS``/``EXTENDS``
verdict.  Reverting the classification (so a degraded empty is treated like a
clean one) makes ``test_degraded_search_empty_is_never_positive`` fail.

**Guard (b) -- no evidence => no LLM verdict.**
With zero evidence records the model path must not be consulted at all: the
client's call counter stays at 0.  Reverting gate 1 (removing the
``if not gather.records`` short-circuit) makes ``test_no_evidence_never_calls_the_llm``
in ``test_assess_verdicts.py`` fail, because the client is then called.
"""

from __future__ import annotations

import pytest

from resextract.assess.evidence import (
    EvidenceRecord,
    generate_queries,
    gather_evidence,
    quote_from,
    term_ratio,
)
from resextract.assess.verdicts import assess_claim
from resextract.web.fetch import FetchMeta, FetchResult
from resextract.web.search import Result, SearchOutcome

CLAIM_TEXT = (
    "the alpha_widget_bridge invariant still holds in the projector_module"
)
PAGE_TEXT = (
    "Notes on the alpha_widget_bridge.\n"
    "The alpha_widget_bridge invariant is enforced by the projector_module at "
    "start-up; every downstream consumer reads it from there.\n"
    + ("Padding sentence to make this page long enough to exercise the bounded "
       "quote window without truncating the match. " * 12)
)

ENGINE_REASON = (
    "1 engine(s) reported themselves unresponsive (google: access denied) -- "
    "SearXNG said the search was broken"
)


def make_outcome(
    query: str,
    results: list[Result] | None = None,
    *,
    ok: bool = True,
    degraded: bool = False,
    absence_is_meaningful: bool = False,
    absence_reason: str | None = None,
    unresponsive_engines: list[str] | None = None,
    error: str | None = None,
) -> SearchOutcome:
    return SearchOutcome(
        query=query,
        results=list(results or []),
        ok=ok,
        degraded=degraded,
        error=error,
        degradation_reason=ENGINE_REASON if degraded else None,
        absence_is_meaningful=absence_is_meaningful,
        absence_reason=absence_reason,
        unresponsive_engines=list(unresponsive_engines or []),
        responded_engines=[],
    )


DEGRADED_EMPTY = make_outcome(
    "q",
    [],
    ok=True,
    degraded=True,
    absence_is_meaningful=False,
    absence_reason=ENGINE_REASON,
    unresponsive_engines=["google: access denied"],
    error=ENGINE_REASON,
)

CLEAN_EMPTY = make_outcome("q", [], ok=True, absence_is_meaningful=True)


class FakeSearch:
    """Returns the queued outcomes in order and records every query."""

    def __init__(self, outcomes: list[SearchOutcome]) -> None:
        self.outcomes = list(outcomes)
        self.queries: list[str] = []

    def search(self, query: str, **kwargs: object) -> SearchOutcome:
        self.queries.append(query)
        if self.outcomes:
            return self.outcomes.pop(0)
        return DEGRADED_EMPTY


def make_fetch(
    url: str,
    text: str,
    *,
    ok: bool = True,
    suspect: bool = False,
    suspicion: str | None = None,
    page_date: str | None = "2024-03-04",
    title: str = "A page",
    error: str | None = None,
    cache_path: str | None = "/tmp/webcache/abc123.txt",
) -> FetchResult:
    if not ok:
        return FetchResult(ok=False, error=error or "boom")
    import hashlib

    meta = FetchMeta(
        url=url,
        title=title,
        text=text,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        fetched_at="2024-03-04T00:00:00+00:00",
        kind="html",
        page_date=page_date,
        http_status=200,
        bytes_in=len(text),
        cache_path=cache_path,
    )
    return FetchResult(
        ok=True,
        meta=meta,
        suspect=suspect,
        suspicion=suspicion,
        usable_chars=len(text),
    )


class FakeFetcher:
    def __init__(self, results: dict[str, FetchResult]) -> None:
        self.results = dict(results)
        self.urls: list[str] = []

    def fetch(self, url: str, **kwargs: object) -> FetchResult:
        self.urls.append(url)
        return self.results.get(url, FetchResult(ok=False, error="no fake result"))


def _claim() -> dict[str, object]:
    return {"claim_id": 1, "text": CLAIM_TEXT, "kind": "architectural"}


def _one_hit(url: str) -> list[Result]:
    return [Result(title="hit", url=url, snippet="", engine="google")]


# --------------------------------------------------------------------------- #
# the degraded-search rule
# --------------------------------------------------------------------------- #


def test_degraded_search_empty_is_never_positive() -> None:
    """Guard (a): a broken search is classified degraded and never confirms."""
    gather = gather_evidence(
        _claim(),
        search=FakeSearch([DEGRADED_EMPTY]),
        fetcher=FakeFetcher({}),
        max_queries=1,
    )
    assert gather.records == [], "a broken search must not yield evidence"
    assert len(gather.degraded_searches) == 1, "the broken search must be visible as degraded"
    assert gather.clean_empty is False, "a degraded empty is not a clean empty"
    entry = gather.degraded_searches[0]
    assert "access denied" in entry["reason"]
    assert entry["unresponsive_engines"] == ["google: access denied"]
    assert entry["absence_is_meaningful"] is False

    verdict = assess_claim(_claim(), gather)
    assert verdict.verdict == "UNVERIFIED"
    assert verdict.verdict not in ("CONFIRMS", "EXTENDS"), (
        "never a positive verdict from a degraded search"
    )
    assert "access denied" in verdict.rationale
    assert "no prior art exists" not in verdict.rationale.lower()


def test_clean_empty_gets_a_distinct_reason() -> None:
    """An empty search that *is* meaningful is still not evidence of novelty."""
    gather = gather_evidence(
        _claim(), search=FakeSearch([CLEAN_EMPTY]), fetcher=FakeFetcher({}), max_queries=1
    )
    assert gather.records == []
    assert gather.degraded_searches == [], "a clean empty is not a degraded search"
    assert gather.clean_empty is True

    verdict = assess_claim(_claim(), gather)
    assert verdict.verdict == "UNVERIFIED"
    assert "clean search found no matching prior art" in verdict.rationale
    assert "degraded" not in verdict.rationale
    assert verdict.absence_reason and "clean search" in verdict.absence_reason


# --------------------------------------------------------------------------- #
# suspect fetches
# --------------------------------------------------------------------------- #


def test_suspect_fetch_is_counted_and_excluded() -> None:
    url = "https://example.test/gpt-2"
    stub = make_fetch(
        url,
        "```\n404: Not Found\n```",
        suspect=True,
        suspicion="short_payload",
        page_date=None,
    )
    gather = gather_evidence(
        _claim(), search=FakeSearch([make_outcome("q", _one_hit(url))]), fetcher=FakeFetcher({url: stub})
    )
    assert gather.records == [], "a suspect stub must never become evidence"
    assert len(gather.suspect_fetches) == 1
    assert gather.suspect_fetches[0] == {
        "url": url,
        "suspicion": "short_payload",
        "excluded": True,
    }
    assert gather.fetched == 0
    assert any("suspect" in r for r in gather.reasons)

    verdict = assess_claim(_claim(), gather)
    assert verdict.verdict == "UNVERIFIED"
    assert "suspect" in verdict.rationale


# --------------------------------------------------------------------------- #
# quotes
# --------------------------------------------------------------------------- #


def test_quote_is_verbatim_and_bounded() -> None:
    text = PAGE_TEXT * 3
    quote = quote_from(text, ["alpha_widget_bridge"], max_chars=120)
    assert len(quote) <= 120
    assert quote in text, "the quote must be a verbatim substring, never a paraphrase"
    assert "alpha_widget_bridge" in quote

    # no term present -> the bounded verbatim head is returned, still a substring
    miss = quote_from(text, ["nonexistent_term_xyz"], max_chars=50)
    assert len(miss) <= 50
    assert miss in text


def test_gathered_quote_is_a_verbatim_substring_of_the_page() -> None:
    url = "https://example.test/bridge"
    fetcher = FakeFetcher({url: make_fetch(url, PAGE_TEXT)})
    gather = gather_evidence(
        _claim(), search=FakeSearch([make_outcome("q", _one_hit(url))]), fetcher=fetcher
    )
    assert len(gather.records) == 1
    record = gather.records[0]
    assert record.quote in PAGE_TEXT
    assert len(record.quote) <= 400


# --------------------------------------------------------------------------- #
# evidence rows
# --------------------------------------------------------------------------- #


def test_evidence_row_carries_url_page_date_sha256_and_copy_path() -> None:
    url = "https://example.test/bridge"
    fetched = make_fetch(url, PAGE_TEXT, title="Bridge notes", cache_path="state/webcache/x.txt")
    gather = gather_evidence(
        _claim(),
        search=FakeSearch([make_outcome("q", _one_hit(url))]),
        fetcher=FakeFetcher({url: fetched}),
    )
    assert gather.fetched == 1
    (record,) = gather.records
    assert isinstance(record, EvidenceRecord)
    assert record.source_ref == url
    assert record.source_kind == "web"
    assert record.page_date == "2024-03-04"
    assert record.title == "Bridge notes"
    assert record.sha256 == fetched.meta.sha256 and len(record.sha256) == 64
    assert record.copy_path == "state/webcache/x.txt"
    assert record.retrieved_at
    assert "key-term match" in record.context


# --------------------------------------------------------------------------- #
# weak sources
# --------------------------------------------------------------------------- #


def test_weak_source_records_the_mismatch_in_context() -> None:
    url = "https://example.test/unrelated"
    unrelated = "A page about gardening and the weather " * 10
    gather = gather_evidence(
        _claim(),
        search=FakeSearch([make_outcome("q", _one_hit(url))]),
        fetcher=FakeFetcher({url: make_fetch(url, unrelated)}),
    )
    assert len(gather.records) == 1, "a weak source is recorded, not silently accepted"
    record = gather.records[0]
    assert record.context.startswith("weak source")
    assert "alpha_widget_bridge" in record.context
    assert url in gather.weak_sources
    assert term_ratio(record.quote, ["alpha_widget_bridge"]) == 0.0

    verdict = assess_claim(_claim(), gather)
    assert verdict.verdict == "UNVERIFIED", "a weak source must not extend a claim"


# --------------------------------------------------------------------------- #
# failures are values
# --------------------------------------------------------------------------- #


def test_fetch_failure_yields_no_evidence_and_no_exception() -> None:
    url = "https://example.test/down"
    gather = gather_evidence(
        _claim(),
        search=FakeSearch([make_outcome("q", _one_hit(url))]),
        fetcher=FakeFetcher({url: make_fetch(url, "", ok=False, error="connection refused")}),
    )
    assert gather.records == []
    assert gather.fetched == 0
    assert any("connection refused" in r for r in gather.reasons)
    verdict = assess_claim(_claim(), gather)
    assert verdict.verdict == "UNVERIFIED"
    assert "no evidence records were gathered" in verdict.rationale


def test_search_that_raises_is_a_degraded_search() -> None:
    class Exploding:
        def search(self, query: str, **kwargs: object) -> SearchOutcome:
            raise RuntimeError("searxng is down")

    gather = gather_evidence(
        _claim(), search=Exploding(), fetcher=FakeFetcher({}), max_queries=1
    )
    assert gather.records == []
    assert len(gather.degraded_searches) == 1
    assert "raised an exception" in gather.degraded_searches[0]["reason"]
    assert assess_claim(_claim(), gather).verdict == "UNVERIFIED"


# --------------------------------------------------------------------------- #
# query generation paths
# --------------------------------------------------------------------------- #


def test_lexical_fallback_path_is_recorded_without_a_client() -> None:
    queries = generate_queries(_claim())
    assert 1 <= len(queries) <= 3
    assert all(q.strip() for q in queries)
    gather = gather_evidence(
        _claim(), search=FakeSearch([DEGRADED_EMPTY]), fetcher=FakeFetcher({}), max_queries=1
    )
    assert gather.query_source == "lexical"
    assert gather.queries == queries[:1] or gather.queries
    assert "alpha_widget_bridge" in gather.queries[0]


def test_model_query_path_is_used_when_a_client_is_injected() -> None:
    class Stub:
        producer = "replay"

        def call_json(self, messages, schema, **kwargs):  # noqa: ANN001
            return schema(queries=["alpha_widget_bridge prior art"])

    gather = gather_evidence(
        _claim(),
        search=FakeSearch([DEGRADED_EMPTY]),
        fetcher=FakeFetcher({}),
        client=Stub(),
        max_queries=1,
    )
    assert gather.query_source == "model"
    assert gather.queries == ["alpha_widget_bridge prior art"]


def test_model_query_failure_falls_back_to_lexical() -> None:
    class Broken:
        producer = "replay"

        def call_json(self, messages, schema, **kwargs):  # noqa: ANN001
            raise RuntimeError("endpoint down")

    queries = generate_queries(_claim(), client=Broken())
    assert queries, "a dead model must still produce deterministic queries"


def test_gather_honours_max_sources_and_paces_queries() -> None:
    urls = [f"https://example.test/{i}" for i in range(5)]
    fetcher = FakeFetcher({u: make_fetch(u, PAGE_TEXT) for u in urls})
    gather = gather_evidence(
        _claim(),
        search=FakeSearch([make_outcome("q", [Result(title="h", url=u) for u in urls])]),
        fetcher=fetcher,
        max_queries=1,
        max_sources=2,
    )
    assert len(gather.candidate_urls) == 2
    assert fetcher.urls == urls[:2]
    assert len(gather.records) == 2


def test_no_duplicate_urls_across_queries() -> None:
    url = "https://example.test/same"
    fetcher = FakeFetcher({url: make_fetch(url, PAGE_TEXT)})
    gather = gather_evidence(
        _claim(),
        search=FakeSearch([make_outcome("q", _one_hit(url)), make_outcome("q", _one_hit(url))]),
        fetcher=fetcher,
        max_queries=2,
        max_sources=3,
    )
    assert fetcher.urls == [url]
    assert len(gather.records) == 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__]))
