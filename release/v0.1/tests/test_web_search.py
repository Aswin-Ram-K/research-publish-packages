"""Offline tests for the paced, degradation-aware SearXNG client.

All HTTP is served by ``httpx.MockTransport`` and time is injected (fake clock +
fake sleep), so nothing here touches the network or really sleeps.
"""

from __future__ import annotations

import asyncio
import threading
import time

import httpx
import pytest

from resextract.web.search import (
    DEGRADATION_THRESHOLD,
    Attempt,
    Result,
    SearchOutcome,
    SearXNGClient,
)

# --------------------------------------------------------------------- helpers


class FakeTime:
    """Injected monotonic clock + sleep: sleeping advances the clock."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _hit(title: str, engine: str, url: str = "http://example.test/1") -> dict:
    return {
        "title": title,
        "url": url,
        "content": f"snippet for {title}",
        "engine": engine,
        "publishedDate": "2024-01-02T00:00:00+00:00",
        "score": 1.5,
    }


def _payload(results: list[dict], query: str = "q") -> dict:
    return {"query": query, "results": results, "unresponsive_engines": []}


def _engine_of(request: httpx.Request) -> str:
    return request.url.params.get("engines", "")


def _client(handler, **kwargs) -> SearXNGClient:
    kwargs.setdefault("jitter_s", 0.0)
    return SearXNGClient(transport=httpx.MockTransport(handler), **kwargs)


# ---------------------------------------------------------------------- pacing


def test_pacing_enforced_between_requests_without_real_sleeping():
    fake = FakeTime()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=_payload([_hit("t", _engine_of(request))]))

    client = _client(handler, min_interval_s=1.5, jitter_s=0.0, clock=fake.clock, sleep=fake.sleep)

    wall0 = time.perf_counter()
    client.search("alpha")
    client.search("beta")
    wall_elapsed = time.perf_counter() - wall0

    assert calls["n"] == 2
    assert fake.sleeps, "injected sleep must have been used for pacing"
    assert fake.now >= 1.5 - 0.0, f"clock advanced only {fake.now}"
    assert wall_elapsed < 0.5, "no real sleeping may happen with an injected sleep"


# ------------------------------------------------------------ engine rotation


def test_engine_rotation_on_empty_first_engine():
    def handler(request: httpx.Request) -> httpx.Response:
        if _engine_of(request) == "engine1":
            return httpx.Response(200, json=_payload([]))
        return httpx.Response(
            200, json=_payload([_hit("a", _engine_of(request)), _hit("b", _engine_of(request))])
        )

    client = _client(handler, engines=["engine1", "engine2"], max_attempts=2)
    outcome = client.search("rotation")

    assert outcome.ok is True
    assert len(outcome.results) == 2
    assert len(outcome.attempts) == 2
    assert outcome.attempts[0].engine == "engine1" and outcome.attempts[0].result_count == 0
    assert outcome.attempts[1].engine == "engine2" and outcome.attempts[1].result_count == 2
    assert {r.engine for r in outcome.results} == {"engine2"}


# ----------------------------------------------------------------- 429 backoff


def test_429_retry_after_backoff_then_success():
    fake = FakeTime()
    seen = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["n"] += 1
        if seen["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "1"})
        return httpx.Response(200, json=_payload([_hit("a", "google"), _hit("b", "google")]))

    client = _client(
        handler, min_interval_s=0.0, jitter_s=0.0, max_attempts=3,
        clock=fake.clock, sleep=fake.sleep,
    )
    outcome = client.search("rate limited")

    assert len(outcome.attempts) == 2
    assert outcome.attempts[0].ok is False and "429" in (outcome.attempts[0].error or "")
    assert any(s >= 1.0 for s in fake.sleeps), f"Retry-After not honoured: {fake.sleeps}"
    assert outcome.ok is True
    assert len(outcome.results) == 2
    assert outcome.error is None


# -------------------------------------------------- ok vs. empty vs. failure


def test_zero_results_is_ok_not_an_error():
    """``ok`` is about the transport, never the result count.

    U3.3 contract update (deliberate): an *instant* (sub-``fast_empty_ms``) empty
    now latches degradation by itself, so the old ``client.degraded is False``
    assertion is rewritten to the new contract.  What this test exists for is
    unchanged -- ``ok=True, results=[]`` is "nothing found", not "we could not
    ask".
    """
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_payload([]))

    client = _client(handler, max_attempts=3)
    outcome = client.search("nothing here")

    assert outcome.ok is True, "an empty result set is a successful HTTP call"
    assert outcome.results == []
    assert outcome.error is not None, "empty-but-ok must carry an explanatory note"
    assert "zero results" in outcome.error
    assert client.degraded is True, "an instant empty is the degradation signature"
    assert client.degradation_reason == "fast_empty"
    assert outcome.degradation_reason == "fast_empty"


def test_transport_error_is_ok_false():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client = _client(handler, max_attempts=2)
    outcome = client.search("unreachable")

    assert outcome.ok is False
    assert outcome.results == []
    assert outcome.error and "transport error" in outcome.error
    assert len(outcome.attempts) == 2
    assert all(a.ok is False for a in outcome.attempts)


# -------------------------------------------------------------- negative cache


def test_negative_cache_short_circuits_and_force_bypasses():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=_payload([]))

    client = _client(handler, max_attempts=1, negative_ttl_s=900.0)
    first = client.search("empty query")
    assert calls["n"] == 1 and first.ok is True

    second = client.search("empty query")
    assert calls["n"] == 1, "negative cache must make zero HTTP requests"
    assert second.ok is True and second.results == []
    assert second.error and "negative-cache" in second.error

    forced = client.search("empty query", force=True)
    assert calls["n"] == 2, "force=True must bypass the negative cache"
    assert forced.attempts and forced.attempts[0].result_count == 0


# ----------------------------------------------------------------- degradation


def test_degradation_latch_after_three_consecutive_distinct_slow_empties():
    """RED -> GREEN: the degradation latch is the guard this test exists for.

    U3.3: the empties here are deliberately *slow* (400 ms each), because an
    instant empty now latches through the ``fast_empty`` path instead.  The
    consecutive-empty rule is the second path, and this test is its guard.

    Reverted-latch run (``if not self._degraded and ...`` forced to ``if False``)
    produced, verbatim::

        >       assert outcomes[2].degraded is True, "3rd consecutive distinct empty must latch"
        E       AssertionError: 3rd consecutive distinct empty must latch
        E       assert False is True
        E        +  where False = SearchOutcome(query='q-three', results=[], ok=True, degraded=False, attempts=[Attempt(ts=2536784.217719349, engine='go... latency_ms=0.38440292701125145)], error='zero results (ok=True, not an error); consecutive distinct-empty streak 3/3').degraded

        tests/test_web_search.py:215: AssertionError
        =========================== short test summary info ============================
        FAILED tests/test_web_search.py::test_degradation_latch_after_three_consecutive_distinct_empties
        1 failed, 1 passed, 10 deselected in 6.02s

    Restoring the latch turns it green: ``2 passed, 10 deselected in 7.51s``.
    """

    fake = FakeTime()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.now += 0.4  # a slow, genuine "nothing found": >= fast_empty_ms
        return httpx.Response(200, json=_payload([]))

    client = _client(handler, max_attempts=1, clock=fake.clock, sleep=fake.sleep)
    queries = ["q-one", "q-two", "q-three"]
    outcomes = [client.search(q) for q in queries]

    assert outcomes[0].degraded is False
    assert outcomes[1].degraded is False
    assert outcomes[2].degraded is True, "3rd consecutive distinct empty must latch"
    assert client.degraded is True
    assert client.degradation_reason == "consecutive_empty"
    assert outcomes[2].degradation_reason == "consecutive_empty"
    evidence_queries = [e.query for e in client.degradation_evidence]
    assert evidence_queries == queries
    assert [e.reason for e in client.degradation_evidence] == ["consecutive_empty"] * 3
    assert all(
        e.latency_ms == pytest.approx(400.0, abs=1.0)
        for e in client.degradation_evidence
    )
    assert len(client.degradation_evidence) >= DEGRADATION_THRESHOLD
    assert outcomes[2].error and "DEGRADED" in outcomes[2].error
    assert "UNVERIFIED" in outcomes[2].error

    fourth = client.search("q-four")
    assert fourth.degraded is True, "the latch is for the client's lifetime"
    assert "DEGRADED" in (fourth.error or "")


# ------------------------------------------------------------------------ sink


def test_sink_receives_exactly_one_attempt_per_http_attempt():
    seen: list[Attempt] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if _engine_of(request) == "engine1":
            return httpx.Response(200, json=_payload([]))
        return httpx.Response(200, json=_payload([_hit("a", "engine2")]))

    client = _client(
        handler, engines=["engine1", "engine2"], max_attempts=2, sink=seen.append
    )
    outcome = client.search("sink me")

    assert len(outcome.attempts) == 2
    assert len(seen) == 2, "one Attempt per HTTP attempt, no more"
    assert [a.result_count for a in seen] == [0, 1]
    assert [a.ok for a in seen] == [True, True]
    assert [a.engine for a in seen] == ["engine1", "engine2"]
    assert all(isinstance(a.latency_ms, float) and a.latency_ms >= 0.0 for a in seen)
    assert all(isinstance(a.ts, float) and a.ts >= 0.0 for a in seen)


# ------------------------------------------------------------------ search_many


def test_search_many_bounds_concurrency_and_preserves_order():
    lock = threading.Lock()
    state = {"inflight": 0, "max": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        with lock:
            state["inflight"] += 1
            state["max"] = max(state["max"], state["inflight"])
        time.sleep(0.1)  # real, tiny: forces genuine overlap
        with lock:
            state["inflight"] -= 1
        q = request.url.params.get("q", "")
        return httpx.Response(200, json=_payload([_hit(q, "google")]))

    queries = [f"query-{i}" for i in range(6)]
    client = _client(handler, min_interval_s=0.0, jitter_s=0.0, max_attempts=1)

    outcomes = asyncio.run(client.search_many(queries, concurrency=2))

    assert [o.query for o in outcomes] == queries, "input order must be preserved"
    assert all(isinstance(o, SearchOutcome) and o.ok for o in outcomes)
    assert state["max"] <= 2, f"concurrency bound exceeded: {state['max']} in flight"
    assert state["max"] == 2, "two workers should actually overlap"


def test_search_many_never_raises_and_returns_one_outcome_per_query():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    client = _client(handler, max_attempts=1)
    outcomes = asyncio.run(client.search_many(["a", "b", "c"], concurrency=2))

    assert len(outcomes) == 3
    assert all(o.ok is False for o in outcomes)
    assert [o.query for o in outcomes] == ["a", "b", "c"]


# ----------------------------------------------------------------------- stats


def test_client_stats_counts_attempts_and_degradation():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("q") == "boom":
            raise httpx.ConnectError("down")
        if request.url.params.get("q") == "empty":
            return httpx.Response(200, json=_payload([]))
        return httpx.Response(200, json=_payload([_hit("a", "google")]))

    client = _client(handler, max_attempts=1)
    client.search("hit")
    client.search("empty")
    client.search("boom")
    stats = client.client_stats()

    assert stats.attempts == 3
    assert stats.ok == 2
    assert stats.empty == 1
    assert stats.errors == 1
    assert stats.degraded is True, "U3.3: the instant empty latches fast_empty"
    assert stats.degradation_reason == "fast_empty"
    assert stats.mean_latency_ms >= 0.0


def test_result_and_outcome_shapes():
    r = Result("t", "u", "s", "e", None, None)
    assert (r.title, r.url, r.snippet, r.engine, r.published_date, r.score) == (
        "t", "u", "s", "e", None, None,
    )
    o = SearchOutcome("q")
    assert o.results == [] and o.attempts == [] and o.ok is False and o.degraded is False
    assert o.degradation_reason is None
    # U3.4: the honest-absence fields default to "no absence claim".
    assert o.absence_is_meaningful is False
    assert o.absence_reason is None
    assert o.unresponsive_engines == [] and o.responded_engines == []
    a = Attempt(0.0, "e", 0, True, None, 0.0)
    assert a.engine == "e" and a.ok is True
    assert a.unresponsive_engines == [] and a.responded_engines == []


# ------------------------------------------------ latency-escalated degradation


def test_fast_empty_escalates_immediately_on_a_sub_threshold_latency():
    """RED -> GREEN guard #1: the latency-escalated degradation latch.

    Reverted-escalation run (the ``reason == "fast_empty"`` branch dropped, so
    only the 3-consecutive rule can latch) produced, verbatim::

        _______ test_fast_empty_escalates_immediately_on_a_sub_threshold_latency _______
        tests/test_web_search.py:389: in test_fast_empty_escalates_immediately_on_a_sub_threshold_latency
            assert outcome.degraded is True, "a sub-fast_empty_ms empty latches immediately"
        E   AssertionError: a sub-fast_empty_ms empty latches immediately
        E   assert False is True
        E    +  where False = SearchOutcome(query='dead searxng', results=[], ok=True, degraded=False, attempts=[Attempt(ts=0.0, engine='google', re...ms=5.0)], error='zero results (ok=True, not an error); consecutive distinct-empty streak 1/3', degradation_reason=None).degraded

    Restoring the branch turns it green.
    """
    fake = FakeTime()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.now += 0.005  # 5 ms: far too fast to have searched anything
        return httpx.Response(200, json=_payload([]))

    client = _client(handler, max_attempts=1, clock=fake.clock, sleep=fake.sleep)
    outcome = client.search("dead searxng")

    assert outcome.ok is True, "the HTTP call itself succeeded"
    assert outcome.attempts[0].latency_ms == pytest.approx(5.0)
    assert outcome.degraded is True, "a sub-fast_empty_ms empty latches immediately"
    assert outcome.degradation_reason == "fast_empty"
    assert client.degraded is True
    assert client.degradation_reason == "fast_empty"
    evidence = client.degradation_evidence
    assert [e.query for e in evidence] == ["dead searxng"]
    assert evidence[0].reason == "fast_empty"
    assert evidence[0].latency_ms == pytest.approx(5.0)
    assert outcome.error and "DEGRADED" in outcome.error
    assert "UNVERIFIED" in outcome.error


def test_slow_empty_does_not_escalate_alone_but_three_consecutive_do():
    fake = FakeTime()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.now += 0.4
        return httpx.Response(200, json=_payload([]))

    client = _client(handler, max_attempts=1, clock=fake.clock, sleep=fake.sleep)

    first = client.search("slow-one")
    assert first.degraded is False, "one slow empty is a legitimate 'nothing found'"
    assert client.degraded is False and client.degradation_reason is None

    second = client.search("slow-two")
    assert second.degraded is False, "two slow empties are not yet evidence"

    third = client.search("slow-three")
    assert third.degraded is True
    assert client.degradation_reason == "consecutive_empty"
    assert [e.reason for e in client.degradation_evidence] == ["consecutive_empty"] * 3


def test_fast_empty_escalation_disabled_restores_consecutive_only():
    fake = FakeTime()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.now += 0.005
        return httpx.Response(200, json=_payload([]))

    client = _client(
        handler,
        max_attempts=1,
        clock=fake.clock,
        sleep=fake.sleep,
        fast_empty_escalates=False,
    )
    outcomes = [client.search(q) for q in ("a", "b", "c")]

    assert outcomes[0].attempts[0].latency_ms == pytest.approx(5.0)
    assert outcomes[0].degraded is False, "5 ms alone must not latch when disabled"
    assert outcomes[1].degraded is False
    assert outcomes[2].degraded is True, "the consecutive rule still applies"
    assert client.degradation_reason == "consecutive_empty"


def test_fast_empty_threshold_is_configurable():
    fake = FakeTime()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.now += 0.005
        return httpx.Response(200, json=_payload([]))

    client = _client(
        handler, max_attempts=1, clock=fake.clock, sleep=fake.sleep, fast_empty_ms=1.0
    )
    first = client.search("five-ms-is-not-fast-enough")

    assert first.degraded is False, "5 ms >= fast_empty_ms=1.0 is not 'fast'"
    assert client.degradation_reason is None


# -------------------------------------------------------------- package surface


def test_package_surface_exposes_exactly_the_declared_names():
    """Guards the coupling hazard: importing either module runs ``__init__``."""
    import resextract.web as w
    import resextract.web.fetch as fetch_module
    import resextract.web.search as search_module

    required = {
        "SearXNGClient",
        "SearchOutcome",
        "Result",
        "Attempt",
        "Fetcher",
        "FetchResult",
        "FetchMeta",
    }
    assert required <= set(w.__all__), f"missing: {required - set(w.__all__)}"
    for name in w.__all__:
        assert hasattr(w, name), f"__all__ promises {name} but it does not resolve"
    # There is no SearchResult class; the real hit type is Result.
    assert "SearchResult" not in w.__all__
    assert w.Result is search_module.Result
    assert w.SearchOutcome is search_module.SearchOutcome
    assert w.SearXNGClient is search_module.SearXNGClient
    assert w.Fetcher is fetch_module.Fetcher
    assert w.FetchResult is fetch_module.FetchResult
    assert w.FetchMeta is fetch_module.FetchMeta

    # U3.4: exports may be ADDED, never removed, and the honest-absence contract
    # is pinned on the public dataclasses rather than left to a docstring.
    import dataclasses

    outcome_fields = {f.name for f in dataclasses.fields(search_module.SearchOutcome)}
    attempt_fields = {f.name for f in dataclasses.fields(search_module.Attempt)}
    assert {
        "absence_is_meaningful",
        "absence_reason",
        "unresponsive_engines",
        "responded_engines",
    } <= outcome_fields, f"missing on SearchOutcome: {outcome_fields}"
    assert {"unresponsive_engines", "responded_engines"} <= attempt_fields
    assert len(w.__all__) >= 13, "the declared surface may grow but never shrink"


# ==================================================================== U3.4 =====
# Honest-failure guards.  V3 proved each of these invariants by hand and found
# that NO test guarded them; a hand-proof dies with the session, so each one is
# pinned here.  Every test in this section is offline (MockTransport + injected
# clock/sleep).
# =================================================================================


def _payload_engine_report(results: list[dict], unresponsive, query: str = "q") -> dict:
    """An envelope carrying SearXNG's own ``unresponsive_engines`` self-report."""
    return {"query": query, "results": results, "unresponsive_engines": unresponsive}


def test_transport_failure_is_not_written_to_the_negative_cache():
    """Guard (V3 finding 3a): 'we could not ask' must never be cached as 'nothing exists'.

    A transport failure that got cached would make every later identical query
    return an empty outcome *without any HTTP call* -- i.e. a network outage would
    silently harden into a negative result.  Asserting the call count AND the
    cache is what makes this fail if that ever regresses.
    """
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ConnectError("connection refused")

    client = _client(handler, max_attempts=1, negative_ttl_s=900.0)
    first = client.search("unreachable-cache-check")
    second = client.search("unreachable-cache-check")

    assert calls["n"] == 2, "a transport failure must not be served from the negative cache"
    assert client._negative_cache == {}, "nothing may be cached from a failed search"
    assert first.ok is False and second.ok is False
    assert first.absence_is_meaningful is False
    assert second.absence_is_meaningful is False
    assert "transport failure" in (second.absence_reason or "")


def test_http_4xx_is_ok_false_and_never_a_meaningful_absence():
    """Guard (V3 finding 3b): a 4xx is a failure, not an empty result set."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad request"})

    client = _client(handler, max_attempts=2)
    outcome = client.search("bad request")

    assert outcome.ok is False
    assert outcome.results == []
    assert outcome.absence_is_meaningful is False
    assert outcome.absence_reason
    assert len(outcome.attempts) == 2
    assert all(a.ok is False for a in outcome.attempts)
    assert all("HTTP 400" in (a.error or "") for a in outcome.attempts)
    assert client._negative_cache == {}


def test_http_5xx_is_ok_false_and_never_a_meaningful_absence():
    """Guard (V3 finding 3c): a 5xx is the server admitting failure."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream unavailable")

    client = _client(handler, max_attempts=2)
    outcome = client.search("server on fire")

    assert outcome.ok is False
    assert outcome.results == []
    assert outcome.absence_is_meaningful is False
    assert all(a.ok is False for a in outcome.attempts)
    assert all("HTTP 503" in (a.error or "") for a in outcome.attempts)
    assert outcome.degraded is False and client.degraded is False
    assert client._negative_cache == {}


def test_empty_malformed_and_non_object_bodies_are_ok_false_with_the_parse_error_recorded():
    """Guard (V3 finding 3d): a body we cannot parse is recorded as an error, not raised.

    An empty body and a non-JSON body must both be ``ok=False`` with the parse
    error on the attempt; a JSON body that is not an object (e.g. a bare list) is
    equally unserveable and must not be mistaken for a clean zero-result answer.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        q = request.url.params.get("q")
        if q == "empty-body":
            return httpx.Response(200, content=b"")
        if q == "non-object-body":
            return httpx.Response(200, json=[1, 2, 3])
        return httpx.Response(200, content=b"<html>not json at all</html>")

    client = _client(handler, max_attempts=1)

    for query in ("empty-body", "malformed-body", "non-object-body"):
        outcome = client.search(query)
        assert outcome.ok is False, f"{query}: an unparseable body is not a success"
        assert outcome.results == []
        assert outcome.absence_is_meaningful is False
        err = outcome.attempts[0].error or ""
        assert err.startswith("malformed JSON response:"), err
        assert len(err) > len("malformed JSON response: "), "the parse error must be recorded"
        assert outcome.error, "the failure must be reported on the outcome too"

    assert client._negative_cache == {}, "an unparseable body must not be negatively cached"


def test_degradation_latch_survives_a_later_success():
    """Guard (V3 finding 3e): the latch is for the client's lifetime.

    If a lucky success could clear it, a client that has already been caught
    lying would go back to reporting confident-looking empties.
    """
    fake = FakeTime()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("q") == "dead":
            fake.now += 0.005  # sub-fast_empty_ms: the diagnostic empty
            return httpx.Response(200, json=_payload([]))
        return httpx.Response(200, json=_payload([_hit("a", "google")]))

    client = _client(handler, max_attempts=1, clock=fake.clock, sleep=fake.sleep)

    dead = client.search("dead")
    assert dead.degraded is True and client.degradation_reason == "fast_empty"
    evidence_before = client.degradation_evidence
    assert len(evidence_before) == 1

    good = client.search("alive")
    assert good.ok is True and len(good.results) == 1

    assert client.degraded is True, "a later success must not clear the latch"
    assert client.degradation_reason == "fast_empty"
    assert client.degradation_evidence == evidence_before, "evidence is retained"
    assert good.degraded is True, "the successful outcome still reports a degraded client"


def test_engine_unresponsive_latches_immediately_and_blocks_the_absence_claim():
    """RED -> GREEN guard #2 (U3.4): the direct self-report latch.

    SearXNG was measured telling the client it was broken
    (``[brave Suspended, duckduckgo CAPTCHA, qwant CAPTCHA]``) while returning
    zero results; the old code parsed that field and threw it away, so a broken
    search looked exactly like a quiet one.  The latency here is deliberately
    SLOW (400 ms), i.e. the heuristic paths alone would NOT latch -- only the
    direct signal can, which is what makes this test a guard on the new path.

    REVERTED-RUN OUTPUT (verbatim; line numbers are as produced before this
    docstring was filled in -- ``_note_empty`` reverted to ignore
    ``unresponsive_engines``, i.e. the ``if unresponsive:`` branch removed so only
    ``fast_empty``/``consecutive_empty`` can latch.  sha256(search.py) before the
    revert = after the restore = ``b79ff107df66b2cd6b6408cc61448418de309774393bf837ac925e5c8745fc7d``,
    run with ``PYTHONDONTWRITEBYTECODE=1`` and ``__pycache__`` purged both ways --
    see the U3.4 handoff)::

            assert outcome.ok is True, "the HTTP call itself succeeded"
            assert outcome.results == []
            assert outcome.attempts[0].latency_ms == pytest.approx(400.0)
            assert outcome.absence_is_meaningful is False, (
                "engines said they were broken; this empty cannot mean 'nothing exists'"
            )
        >       assert outcome.degradation_reason == "engine_unresponsive"
        E       AssertionError: assert None == 'engine_unresponsive'
        E        +  where None = SearchOutcome(query='capability-based security agent isolation', results=[], ok=True, degraded=False, attempts=[Attemp...NG said the search was broken', unresponsive_engines=['brave: Suspended', 'duckduckgo: CAPTCHA'], responded_engines=[]).degradation_reason

        tests/test_web_search.py:693: AssertionError
        =========================== short test summary info ============================
        FAILED tests/test_web_search.py::test_engine_unresponsive_latches_immediately_and_blocks_the_absence_claim
        1 failed, 29 deselected in 0.07s

    Note what the reverted dump proves: even with the latch reverted, the
    self-report is still surfaced (``unresponsive_engines=['brave: Suspended',
    'duckduckgo: CAPTCHA']``) -- so this test fails on the *latch*, not on the
    surfacing.

    Restoring the direct-signal branch turns it green.
    """
    fake = FakeTime()
    seen: list[Attempt] = []
    report = ["brave Suspended", "duckduckgo CAPTCHA"]

    def handler(request: httpx.Request) -> httpx.Response:
        fake.now += 0.4  # 400 ms: too slow for the fast-empty heuristic
        return httpx.Response(200, json=_payload_engine_report([], report))

    client = _client(
        handler, max_attempts=1, clock=fake.clock, sleep=fake.sleep, sink=seen.append
    )
    outcome = client.search("capability-based security agent isolation")

    assert outcome.ok is True, "the HTTP call itself succeeded"
    assert outcome.results == []
    assert outcome.attempts[0].latency_ms == pytest.approx(400.0)
    assert outcome.absence_is_meaningful is False, (
        "engines said they were broken; this empty cannot mean 'nothing exists'"
    )
    assert outcome.degradation_reason == "engine_unresponsive"
    assert client.degraded is True
    assert client.degradation_reason == "engine_unresponsive"
    assert "engine_unresponsive" in (outcome.error or "")
    assert "UNVERIFIED" in (outcome.error or "")
    assert outcome.unresponsive_engines == ["brave: Suspended", "duckduckgo: CAPTCHA"]
    assert "brave: Suspended" in (outcome.absence_reason or "")
    evidence = client.degradation_evidence
    assert len(evidence) == 1 and evidence[0].reason == "engine_unresponsive"
    assert evidence[0].engines == ["brave: Suspended", "duckduckgo: CAPTCHA"]
    assert evidence[0].latency_ms == pytest.approx(400.0)
    # the sink saw the self-report on the attempt, ready for search_health
    assert len(seen) == 1
    assert seen[0].unresponsive_engines == ["brave: Suspended", "duckduckgo: CAPTCHA"]
    assert seen[0].responded_engines == []
    assert seen == outcome.attempts


@pytest.mark.parametrize(
    "shape",
    [
        ["brave Suspended", "duckduckgo CAPTCHA"],
        ["brave: Suspended", "duckduckgo: CAPTCHA"],
        [["brave", "Suspended"], ["duckduckgo", "CAPTCHA"]],
        [{"engine": "brave", "reason": "Suspended"}, {"engine": "duckduckgo", "reason": "CAPTCHA"}],
    ],
)
def test_unresponsive_field_shapes_normalise_to_the_same_readable_form(shape):
    """SearXNG shapes ``unresponsive_engines`` differently across versions."""
    fake = FakeTime()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.now += 0.4
        return httpx.Response(200, json=_payload_engine_report([], shape))

    client = _client(handler, max_attempts=1, clock=fake.clock, sleep=fake.sleep)
    outcome = client.search("shape check")

    assert outcome.unresponsive_engines == ["brave: Suspended", "duckduckgo: CAPTCHA"]
    assert outcome.attempts[0].unresponsive_engines == outcome.unresponsive_engines
    assert outcome.absence_is_meaningful is False
    assert client.degradation_reason == "engine_unresponsive"


def test_clean_slow_empty_is_a_meaningful_absence_and_does_not_latch():
    """The one shape of empty search that may be read as 'nothing was found'."""
    fake = FakeTime()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.now += 0.4  # slow, and the envelope reports nothing unresponsive
        return httpx.Response(200, json=_payload([]))

    client = _client(handler, max_attempts=1, clock=fake.clock, sleep=fake.sleep)
    outcome = client.search("clean slow empty")

    assert outcome.ok is True and outcome.results == []
    assert outcome.unresponsive_engines == []
    assert outcome.absence_is_meaningful is True
    assert outcome.absence_reason is None
    assert "absence_is_meaningful=True" in (outcome.error or "")
    assert outcome.degraded is False
    assert client.degraded is False, "a single clean slow empty is not degradation"
    assert client.degradation_reason is None


def test_absence_is_meaningful_truth_table():
    """RED -> GREEN guard #3 (U3.4): the ``absence_is_meaningful`` truth table.

    This is the guard that stops "no prior art exists" from being concluded out
    of a broken search.  Each row below is a case where the naive reading (empty
    results == nothing exists) is wrong, or where an honest empty must still be
    allowed through.

    REVERTED-RUN OUTPUT (verbatim; line numbers are as produced before this
    docstring was filled in -- the blocker computation reverted to
    ``absence_blockers = list(blockers)``, i.e. no condition can block the claim.
    sha256(search.py) before the revert = after the restore =
    ``b79ff107df66b2cd6b6408cc61448418de309774393bf837ac925e5c8745fc7d``, run with
    ``PYTHONDONTWRITEBYTECODE=1`` and ``__pycache__`` purged both ways -- see the
    U3.4 handoff)::

        tests/test_web_search.py:796: in test_absence_is_meaningful_truth_table
            out_b = client_b.search("row-b fast empty")
            assert out_b.ok is True and out_b.results == []
        >       assert out_b.absence_is_meaningful is False
        E       AssertionError: assert True is False
        E        +  where True = SearchOutcome(query='row-b fast empty', results=[], ok=True, degraded=True, attempts=[Attempt(ts=0.0, engine='google',...on_reason='fast_empty', absence_is_meaningful=True, absence_reason=None, unresponsive_engines=[], responded_engines=[]).absence_is_meaningful

        tests/test_web_search.py:796: AssertionError
        =========================== short test summary info ============================
        FAILED tests/test_web_search.py::test_absence_is_meaningful_truth_table - Ass...
        1 failed, 29 deselected in 0.07s

    Read the dump closely: the reverted client had *already latched*
    ``degradation_reason='fast_empty'`` on a 5 ms empty and still reported
    ``absence_is_meaningful=True`` -- exactly the false "nothing exists" verdict
    this field exists to prevent.

    Restoring the blockers turns it green.
    """
    # --- row A: the ONLY meaningful case: ok, quiet, slow, latch clear --------
    fake_a = FakeTime()

    def clean_slow(request: httpx.Request) -> httpx.Response:
        fake_a.now += 0.4
        return httpx.Response(200, json=_payload([]))

    client_a = _client(clean_slow, max_attempts=1, clock=fake_a.clock, sleep=fake_a.sleep)
    out_a = client_a.search("row-a clean slow")
    assert (out_a.ok, out_a.results, out_a.unresponsive_engines) == (True, [], [])
    assert out_a.absence_is_meaningful is True and out_a.absence_reason is None

    # --- row B: sub-threshold latency -> not meaningful ----------------------
    fake_b = FakeTime()

    def fast_empty(request: httpx.Request) -> httpx.Response:
        fake_b.now += 0.005
        return httpx.Response(200, json=_payload([]))

    client_b = _client(fast_empty, max_attempts=1, clock=fake_b.clock, sleep=fake_b.sleep)
    out_b = client_b.search("row-b fast empty")
    assert out_b.ok is True and out_b.results == []
    assert out_b.absence_is_meaningful is False
    assert "fast_empty_ms" in (out_b.absence_reason or "")

    # --- row C: engines self-reported unresponsive -> not meaningful ---------
    fake_c = FakeTime()

    def unresponsive(request: httpx.Request) -> httpx.Response:
        fake_c.now += 0.4
        return httpx.Response(200, json=_payload_engine_report([], [["qwant", "CAPTCHA"]]))

    client_c = _client(unresponsive, max_attempts=1, clock=fake_c.clock, sleep=fake_c.sleep)
    out_c = client_c.search("row-c unresponsive")
    assert out_c.ok is True and out_c.results == []
    assert out_c.absence_is_meaningful is False
    assert "unresponsive" in (out_c.absence_reason or "")

    # --- row D: transport failure -> not meaningful, and says so -------------
    def dead(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    client_d = _client(dead, max_attempts=1)
    out_d = client_d.search("row-d transport failure")
    assert out_d.ok is False and out_d.results == []
    assert out_d.absence_is_meaningful is False
    assert "transport failure" in (out_d.absence_reason or "")

    # --- row E: results were returned -> there is no absence claim to make ---
    def hits(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_payload([_hit("a", "google")]))

    client_e = _client(hits, max_attempts=1)
    out_e = client_e.search("row-e with results")
    assert out_e.ok is True and out_e.results
    assert out_e.absence_is_meaningful is False
    assert out_e.absence_reason is None, "no absence is claimed, so no blocker is named"

    # --- row F: an already-degraded client cannot claim a meaningful absence -
    fake_f = FakeTime()

    def mixed(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("q") == "row-f latch":
            fake_f.now += 0.005
            return httpx.Response(200, json=_payload([]))
        fake_f.now += 0.4
        return httpx.Response(200, json=_payload([]))

    client_f = _client(mixed, max_attempts=1, clock=fake_f.clock, sleep=fake_f.sleep)
    assert client_f.search("row-f latch").degraded is True
    out_f = client_f.search("row-f clean later")
    assert out_f.ok is True and out_f.results == []
    assert out_f.absence_is_meaningful is False, (
        "a latched client's empties are unverified for its lifetime"
    )
    assert "latch" in (out_f.absence_reason or "")


def test_sink_receives_the_new_engine_fields_on_every_attempt():
    """The sink is how a later unit persists the self-report into search_health."""
    seen: list[Attempt] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if _engine_of(request) == "engine1":
            return httpx.Response(
                200, json=_payload_engine_report([], [["qwant", "CAPTCHA"]])
            )
        return httpx.Response(200, json=_payload([_hit("a", "engine2")]))

    client = _client(
        handler, engines=["engine1", "engine2"], max_attempts=2, sink=seen.append
    )
    outcome = client.search("sink engine fields")

    assert [a.unresponsive_engines for a in seen] == [["qwant: CAPTCHA"], []]
    assert [a.responded_engines for a in seen] == [[], ["engine2"]]
    assert seen == outcome.attempts
    assert outcome.unresponsive_engines == ["qwant: CAPTCHA"]
    assert outcome.responded_engines == ["engine2"]
    assert outcome.results and outcome.absence_is_meaningful is False
