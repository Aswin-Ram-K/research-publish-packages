"""Paced, resilient SearXNG search client whose failure reporting is honest.

RECORDED FAILURE MODE (from this project's own research log, verbatim)::

    local_web_search (local SearXNG) -- "Worked for the first ~6 queries, then
    returned 'no results' for every subsequent query -- intermittent to
    broken. Treat discovery as unreliable."

A burst of *plausible-looking* zero-result responses must never be mistaken for
"the literature does not exist".  This client refuses to hide that failure:

* it **paces** every request it makes through one shared limiter
  (``min_interval_s`` +/- jitter, monotonic clock), including engine retries;
* it **rotates engines** on a zero-result response instead of accepting the
  first empty page as truth;
* it **latches degradation** on three paths: a *direct self-report* (SearXNG's
  envelope says an engine was unresponsive -- see below) latches at once; an
  ``ok=True`` empty that came back faster than ``fast_empty_ms`` (default 50 ms)
  is diagnostic on its own -- the live signature of this host's broken SearXNG
  is a *sub-50 ms* empty while real answers take 172-948 ms -- and three
  consecutive distinct *slow* empties latch it too.  ``degraded`` and
  ``degradation_reason`` are set for the client's lifetime and are *not* cleared
  by a later success, and *every* empty outcome then carries a loud note telling
  downstream code to label prior-art findings ``UNVERIFIED`` rather than "no
  prior art exists";
* it never conflates transport failure with absence: ``ok`` means the HTTP call
  succeeded, independent of result count.  ``ok=True, results=[]`` is "nothing
  found"; ``ok=False`` is "we could not ask".

THE SEMANTIC GUARANTEE, in one sentence: **an empty result set is never by
itself evidence that nothing exists; only a successful, quiet, slow-enough empty
search is** -- and that verdict is exposed as
:attr:`SearchOutcome.absence_is_meaningful`, never inferred from result count or
latency alone.

DIRECT SIGNAL (U3.4).  The envelope carries ``unresponsive_engines``, and this
client used to parse that field and discard it -- measured live on this host,
three paced queries returned zero results while the raw envelope carried
``[brave Suspended, duckduckgo CAPTCHA, qwant CAPTCHA]``.  SearXNG was telling us
it was broken and the client reported a plain empty.  The field is now normalised
(both the ``"engine reason"``/``"engine: reason"`` string shape and the
``[engine, reason]`` pair shape) onto every :class:`Attempt` and every
:class:`SearchOutcome`, passed through the ``sink`` so a later unit can persist it
into ``search_health``, and any non-empty report latches
``degradation_reason="engine_unresponsive"`` immediately: a directly-reported
failure outranks the latency and streak heuristics.

Observed SearXNG JSON field names (verified against the live local service):
result objects carry ``title``, ``url``, ``content`` (the snippet) and
``publishedDate`` (the publication date), plus ``engine`` and ``score``.
``snippet``/``published_date`` fallbacks are accepted defensively.  Every
envelope field is conditional/sparse: ``unresponsive_engines`` may be absent,
some hits carry no ``engine``/``score``, and ``publishedDate`` may be ``null``.
"""

from __future__ import annotations

import asyncio
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Iterable, Sequence

import httpx

__all__ = [
    "DEFAULT_ENGINES",
    "DEGRADATION_THRESHOLD",
    "Attempt",
    "ClientStats",
    "DegradationEvidence",
    "Result",
    "SearchOutcome",
    "SearXNGClient",
]

log = logging.getLogger(__name__)

DEFAULT_ENGINES: tuple[str, ...] = ("google", "duckduckgo", "bing", "arxiv")
DEGRADATION_THRESHOLD = 3


@dataclass
class Result:
    """One search hit, normalised across engines."""

    title: str
    url: str
    snippet: str = ""
    engine: str = ""
    published_date: str | None = None
    score: float | None = None


@dataclass
class Attempt:
    """One HTTP attempt.  One of these is emitted per request to ``sink``.

    ``unresponsive_engines`` is the envelope's own self-report, normalised to
    ``"engine: reason"`` strings (e.g. ``"duckduckgo: CAPTCHA"``).  It is empty
    both when every engine was fine *and* when the response carried no such field
    at all -- the absence of a report is not evidence that the search worked.
    ``responded_engines`` is derived from the hits actually parsed back, so it is
    empty on any zero-result response.
    """

    ts: float
    engine: str
    result_count: int
    ok: bool
    error: str | None = None
    latency_ms: float = 0.0
    unresponsive_engines: list[str] = field(default_factory=list)
    responded_engines: list[str] = field(default_factory=list)


@dataclass
class DegradationEvidence:
    """One zero-result observation that latched or confirmed degradation.

    ``reason`` is one of ``"engine_unresponsive"`` (SearXNG itself reported an
    engine as unresponsive -- a direct signal, latched immediately),
    ``"fast_empty"`` (the response arrived in under ``fast_empty_ms``: it did not
    search, it only answered) or ``"consecutive_empty"`` (the third distinct slow
    empty in a row).  ``latency_ms`` and ``ts`` are recorded so the claim is
    auditable, and ``engines`` carries the self-report verbatim when there was
    one.
    """

    query: str
    reason: str
    latency_ms: float | None = None
    ts: float = 0.0
    engines: list[str] = field(default_factory=list)


@dataclass
class SearchOutcome:
    """The honest verdict for one query.

    ``ok`` is about the *transport*, never the result count.  ``error`` doubles
    as the notes channel: an empty-but-ok outcome explains itself there,
    including the degradation warning.

    ``absence_is_meaningful`` is the field a prior-art stage may consume, and the
    only licit basis for concluding "nothing exists".  It is ``True`` **only**
    for an empty outcome that is successful (``ok``), quiet (no engine
    self-reported via ``unresponsive_engines``), slow enough (latency >=
    ``fast_empty_ms``) *and* produced while the client's degradation latch was
    clear.  It is ``False`` for every transport failure, every sub-threshold
    empty, every self-reported-unresponsive empty, every empty from an
    already-degraded client, and for any outcome that returned results (there is
    then no absence claim to make -- read ``results`` instead).  Whenever it is
    ``False`` on an empty outcome, ``absence_reason`` names the contributing
    conditions; never infer a conclusion from the result count alone.
    """

    query: str
    results: list[Result] = field(default_factory=list)
    ok: bool = False
    degraded: bool = False
    attempts: list[Attempt] = field(default_factory=list)
    error: str | None = None
    degradation_reason: str | None = None
    absence_is_meaningful: bool = False
    absence_reason: str | None = None
    unresponsive_engines: list[str] = field(default_factory=list)
    responded_engines: list[str] = field(default_factory=list)


@dataclass
class ClientStats:
    attempts: int
    ok: int
    empty: int
    errors: int
    degraded: bool
    mean_latency_ms: float
    degradation_reason: str | None = None


class SearXNGClient:
    """Paced SearXNG JSON-API client with engine rotation and degradation latch.

    ``clock`` and ``sleep`` are injected so pacing is testable without real
    sleeping: ``clock`` is a monotonic seconds source, ``sleep`` a callable
    taking seconds.  Attempt latency is measured on that same injected clock, so
    the ``fast_empty_ms`` escalation is testable with fake time.

    ``fast_empty_ms`` / ``fast_empty_escalates`` control the latency-based latch:
    a zero-result response that arrived in under ``fast_empty_ms`` is treated as
    proof the service did not search, and latches ``degraded`` immediately;
    ``fast_empty_escalates=False`` restores the old consecutive-empty-only rule.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        *,
        min_interval_s: float = 1.5,
        jitter_s: float = 0.5,
        max_attempts: int = 3,
        engines: Sequence[str] | None = None,
        timeout_s: float = 8.0,
        negative_ttl_s: float = 900.0,
        fast_empty_ms: float = 50.0,
        fast_empty_escalates: bool = True,
        sink: Callable[[Attempt], Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Any] = time.sleep,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.min_interval_s = float(min_interval_s)
        self.jitter_s = float(jitter_s)
        self.max_attempts = max(1, int(max_attempts))
        self.engines: list[str] = list(engines) if engines else list(DEFAULT_ENGINES)
        self.timeout_s = float(timeout_s)
        self.negative_ttl_s = float(negative_ttl_s)
        self.fast_empty_ms = float(fast_empty_ms)
        self.fast_empty_escalates = bool(fast_empty_escalates)
        self._sink = sink
        self._clock = clock
        self._sleep = sleep
        self._transport = transport

        # --- shared pacing limiter (monotonic, thread-safe) -----------------
        self._limiter_lock = threading.Lock()
        self._last_request_at: float | None = None

        # --- negative cache -------------------------------------------------
        self._negative_cache: dict[tuple[str, tuple[str, ...]], float] = {}

        # --- degradation tracking ------------------------------------------
        self._degraded = False
        self._degradation_reason: str | None = None
        self._degradation_evidence: list[DegradationEvidence] = []
        self._pending_streak: list[DegradationEvidence] = []
        self._last_empty_query: str | None = None

        # --- stats ----------------------------------------------------------
        self._n_attempts = 0
        self._n_ok = 0
        self._n_empty = 0
        self._n_error = 0
        self._latencies: list[float] = []

    # ------------------------------------------------------------------ props
    @property
    def degraded(self) -> bool:
        """True once the degradation latch has tripped; latched for life."""
        return self._degraded

    @property
    def degradation_reason(self) -> str | None:
        """How the latch tripped: ``"fast_empty"``, ``"consecutive_empty"``, None."""
        return self._degradation_reason

    @property
    def degradation_evidence(self) -> list[DegradationEvidence]:
        """Records that latched/confirmed it: query, reason, latency_ms, ts."""
        return list(self._degradation_evidence)

    # ----------------------------------------------------------------- helpers
    def _resolve_engines(self, engines: Sequence[str] | str | None) -> list[str]:
        if engines is None:
            return list(self.engines)
        if isinstance(engines, str):
            return [engines]
        return list(engines)

    def _elapsed_ms(self, wall0: float) -> float:
        """Milliseconds since ``wall0`` on the *injected* clock.

        Measuring on the injectable clock is what makes the latency-based
        fast-empty decision testable without real sleeping.
        """
        return (self._clock() - wall0) * 1000.0

    def _pace(self) -> None:
        """Block until at least the pacing interval has elapsed since the last request."""
        with self._limiter_lock:
            now = self._clock()
            if self._last_request_at is not None:
                target = self.min_interval_s + random.uniform(-self.jitter_s, self.jitter_s)
                wait = target - (now - self._last_request_at)
                if wait > 0:
                    self._sleep(wait)
                    now = self._clock()
            self._last_request_at = now

    def _backoff(self, wait_s: float) -> None:
        """Sleep for a 429 backoff and re-base the limiter on the new time."""
        if wait_s > 0:
            self._sleep(wait_s)
        with self._limiter_lock:
            self._last_request_at = self._clock()

    @staticmethod
    def _retry_after(resp: httpx.Response) -> float | None:
        raw = resp.headers.get("Retry-After")
        if not raw:
            return None
        raw = raw.strip()
        try:
            return max(0.0, float(raw))
        except ValueError:
            pass
        try:
            dt = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            return None
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())

    @staticmethod
    def _parse_results(payload: Any, engine: str) -> list[Result]:
        items = payload.get("results") if isinstance(payload, dict) else None
        out: list[Result] = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            snippet = item.get("content")
            if snippet is None:
                snippet = item.get("snippet")
            published = item.get("publishedDate")
            if published is None:
                published = item.get("published_date")
            if published is None:
                published = item.get("pubdate")
            score = item.get("score")
            out.append(
                Result(
                    title=str(item.get("title", "") or ""),
                    url=str(item.get("url", "") or ""),
                    snippet=str(snippet or ""),
                    engine=str(item.get("engine") or engine),
                    published_date=str(published) if published else None,
                    score=float(score) if isinstance(score, (int, float)) else None,
                )
            )
        return out

    @staticmethod
    def _normalise_unresponsive(raw: Any) -> list[str]:
        """Normalise SearXNG's ``unresponsive_engines`` into readable strings.

        The field is shaped differently across SearXNG versions and the proxies
        in front of it, so every observed shape is accepted:

        * ``["brave Suspended", "duckduckgo CAPTCHA"]`` -- one string per engine
          (also seen colon-separated: ``"brave: Suspended"``);
        * ``[["brave", "Suspended"], ["duckduckgo", "CAPTCHA"]]`` -- pairs;
        * ``[{"engine": "brave", "reason": "Suspended"}]`` -- defensive dict form.

        Everything becomes ``"<engine>: <reason>"`` (or bare ``"<engine>"`` when
        no reason was given).  Order is preserved and duplicates are dropped.
        """
        if raw is None:
            return []
        if isinstance(raw, (str, bytes, dict)):
            entries: list[Any] = [raw]
        elif isinstance(raw, (list, tuple)):
            entries = list(raw)
        else:
            return []
        out: list[str] = []
        for entry in entries:
            engine = ""
            reason = ""
            if isinstance(entry, dict):
                engine = str(entry.get("engine") or entry.get("name") or "")
                reason = str(entry.get("reason") or entry.get("error") or "")
            elif isinstance(entry, (list, tuple)):
                if entry:
                    engine = str(entry[0] or "")
                if len(entry) > 1:
                    reason = str(entry[1] or "")
            else:
                text = str(entry or "").strip()
                if ":" in text:
                    engine, _, reason = text.partition(":")
                elif " " in text:
                    engine, _, reason = text.partition(" ")
                else:
                    engine = text
            engine, reason = engine.strip(), reason.strip()
            if not engine:
                continue
            item = f"{engine}: {reason}" if reason else engine
            if item not in out:
                out.append(item)
        return out

    @staticmethod
    def _responded_engines(parsed: Sequence[Result]) -> list[str]:
        """Engines that demonstrably answered, derived from the hits parsed back."""
        out: list[str] = []
        for r in parsed:
            if r.engine and r.engine not in out:
                out.append(r.engine)
        return out

    @staticmethod
    def _merge_engines(attempts: Sequence[Attempt], attr: str) -> list[str]:
        """Union of one engine-list attribute across attempts, order-preserving."""
        out: list[str] = []
        for att in attempts:
            for name in getattr(att, attr, ()) or ():
                if name not in out:
                    out.append(name)
        return out

    def _record_attempt(self, att: Attempt) -> None:
        self._n_attempts += 1
        if att.ok:
            self._n_ok += 1
            if att.result_count == 0:
                self._n_empty += 1
        else:
            self._n_error += 1
        self._latencies.append(att.latency_ms)
        if self._sink is not None:
            try:
                self._sink(att)
            except Exception:  # a broken sink must never break search
                log.exception("search sink raised; ignoring")

    # ------------------------------------------------------- degradation logic
    def _degradation_note(self) -> str:
        queries = ", ".join(e.query for e in self._degradation_evidence) or "<none>"
        triage = ""
        direct = [e for e in self._degradation_evidence if e.reason == "engine_unresponsive"]
        if direct:
            engs = sorted({x for e in direct for x in e.engines})
            triage += (
                f" Direct signal: SearXNG itself reported unresponsive engines on "
                f"{len(direct)} of those queries "
                f"({'; '.join(engs) or 'engines unrecorded'}) -- this is not a "
                "latency heuristic, the service told us it was broken."
            )
        fast = [e for e in self._degradation_evidence if e.reason == "fast_empty"]
        if fast:
            lats = ", ".join(
                f"{e.latency_ms:.1f}ms" for e in fast if e.latency_ms is not None
            )
            triage += (
                f" Triage: {len(fast)} zero-result response(s) came back in under "
                f"{self.fast_empty_ms:g}ms ({lats or 'latency unrecorded'}) -- too "
                "fast to have searched anything."
            )
        return (
            f"DEGRADED ({self._degradation_reason}): {len(self._degradation_evidence)} "
            f"distinct empty queries [{queries}].{triage} SearXNG discovery is "
            "unreliable on this host -- treat any 'no results' as UNVERIFIED, NOT as "
            "evidence that no prior art exists."
        )

    def _note_empty(
        self,
        query: str,
        ts: float,
        *,
        latency_ms: float | None = None,
        fast_empty: bool = False,
        unresponsive: Sequence[str] = (),
    ) -> None:
        """Record a zero-result outcome and latch degradation on any of three paths.

        Path A (``engine_unresponsive``, a *direct* signal): SearXNG's own
        envelope named an unresponsive engine.  That is a reported failure, not a
        heuristic, so it latches at once and outranks the other two paths.

        Path B (``fast_empty``): an ``ok=True`` empty that arrived in under
        ``fast_empty_ms`` did not search; it only answered.  That is diagnostic
        on its own, so it latches at once rather than waiting for three of them.

        Path C: three consecutive distinct *slow* empties -- one slow empty is a
        legitimate "nothing found", a run of them is not.
        """
        if query == self._last_empty_query:
            return
        self._last_empty_query = query
        if unresponsive:
            reason = "engine_unresponsive"
            escalates = True
        else:
            escalates = fast_empty and self.fast_empty_escalates
            reason = "fast_empty" if escalates else "consecutive_empty"
        self._pending_streak.append(
            DegradationEvidence(query, reason, latency_ms, ts, list(unresponsive))
        )
        if not self._degraded:
            if escalates or reason == "fast_empty" or len(
                self._pending_streak
            ) >= DEGRADATION_THRESHOLD:
                self._degraded = True
                self._degradation_reason = reason
                self._degradation_evidence = list(self._pending_streak)
                log.warning(self._degradation_note())
        else:
            self._degradation_evidence.append(self._pending_streak[-1])

    def _note_success(self) -> None:
        """Clear the streak.  Deliberately does NOT clear the degradation latch:
        once this client has proven itself unreliable it stays marked, so a later
        lucky success cannot launder an earlier failure."""
        self._pending_streak.clear()
        self._last_empty_query = None

    def _absence_blockers(
        self, latency_ms: float | None, unresponsive: Sequence[str]
    ) -> list[str]:
        """The exact conditions that stop this empty from meaning "nothing exists"."""
        reasons: list[str] = []
        if unresponsive:
            reasons.append(
                f"{len(unresponsive)} engine(s) reported themselves unresponsive "
                f"({', '.join(unresponsive)}) -- SearXNG said the search was broken"
            )
        if latency_ms is None:
            reasons.append("no successful attempt recorded a latency for this empty")
        elif latency_ms < self.fast_empty_ms:
            reasons.append(
                f"the empty response arrived in {latency_ms:.1f}ms, under "
                f"fast_empty_ms={self.fast_empty_ms:g}ms -- too fast to have searched"
            )
        if self._degraded:
            reasons.append(
                f"the client's degradation latch is set ({self._degradation_reason}); "
                "empties from a degraded client are unverified for its lifetime"
            )
        return reasons

    def _empty_outcome(
        self,
        query: str,
        attempts: list[Attempt],
        *,
        notes: str | None = None,
        latency_ms: float | None = None,
        fast_empty: bool = False,
        count_streak: bool = True,
        unresponsive: Sequence[str] = (),
        responded: Sequence[str] = (),
        blockers: Sequence[str] = (),
    ) -> SearchOutcome:
        ts = self._clock()
        if count_streak:
            self._note_empty(
                query,
                ts,
                latency_ms=latency_ms,
                fast_empty=fast_empty,
                unresponsive=unresponsive,
            )
        out_unresponsive = list(unresponsive)
        out_responded = list(responded)
        absence_blockers = list(blockers) + self._absence_blockers(
            latency_ms, out_unresponsive
        )
        absence_ok = not absence_blockers
        parts: list[str] = []
        if notes:
            parts.append(notes)
        counter = "zero results (ok=True, not an error)"
        if not self._degraded:
            counter += (
                "; consecutive distinct-empty streak "
                f"{len(self._pending_streak)}/{DEGRADATION_THRESHOLD}"
            )
        parts.append(counter)
        if absence_ok:
            parts.append(
                "absence_is_meaningful=True: a successful, quiet, slow-enough empty "
                f"(latency {float(latency_ms):.1f}ms >= fast_empty_ms="
                f"{self.fast_empty_ms:g}ms, no engine reported itself unresponsive) -- "
                "this is the only shape of empty search that may be read as 'nothing "
                "was found'"
            )
        else:
            parts.append(
                "absence_is_meaningful=False: "
                + "; ".join(absence_blockers)
                + " -- do NOT read this empty result as 'no prior art exists'"
            )
        if self._degraded:
            parts.append(self._degradation_note())
        return SearchOutcome(
            query=query,
            results=[],
            ok=True,
            degraded=self._degraded,
            attempts=attempts,
            error=" | ".join(parts),
            degradation_reason=self._degradation_reason,
            absence_is_meaningful=absence_ok,
            absence_reason=None if absence_ok else "; ".join(absence_blockers),
            unresponsive_engines=out_unresponsive,
            responded_engines=out_responded,
        )

    # ------------------------------------------------------------------ search
    def search(
        self,
        query: str,
        *,
        engines: Sequence[str] | str | None = None,
        max_results: int = 10,
        categories: str | None = None,
        time_range: str | None = None,
        force: bool = False,
    ) -> SearchOutcome:
        """Run one query with pacing, engine rotation and honest reporting."""
        engine_set = self._resolve_engines(engines)
        key = (query.strip(), tuple(engine_set))

        if not force:
            expiry = self._negative_cache.get(key)
            if expiry is not None and expiry > self._clock():
                return self._empty_outcome(
                    query,
                    [],
                    notes=f"negative-cache hit (ttl {self.negative_ttl_s:.0f}s); no HTTP request made",
                    count_streak=False,
                    blockers=[
                        "answered from the negative cache: no search was performed "
                        "for this query in this call"
                    ],
                )

        attempts: list[Attempt] = []
        results: list[Result] = []
        last_error: str | None = None
        saw_ok = False

        with httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_s,
            transport=self._transport,
            headers={"Accept": "application/json", "User-Agent": "resextract-searxng/1.0"},
        ) as client:
            for i in range(self.max_attempts):
                engine = engine_set[i % len(engine_set)]
                params: dict[str, str] = {"q": query, "format": "json", "engines": engine}
                if categories:
                    params["categories"] = categories
                if time_range:
                    params["time_range"] = time_range

                self._pace()
                ts = self._clock()
                wall0 = self._clock()
                try:
                    resp = client.get("/search", params=params)
                except Exception as exc:  # transport failure
                    lat = self._elapsed_ms(wall0)
                    err = f"transport error: {exc.__class__.__name__}: {exc}"
                    att = Attempt(ts, engine, 0, False, err, lat)
                    self._record_attempt(att)
                    attempts.append(att)
                    last_error = err
                    continue

                lat = self._elapsed_ms(wall0)

                if resp.status_code == 429:
                    retry_after = self._retry_after(resp)
                    if retry_after is not None:
                        wait = retry_after
                        why = f"Retry-After: {retry_after:g}s"
                    else:
                        wait = min(60.0, (2**i) * 1.0) + random.uniform(0.0, 0.5)
                        why = f"exponential backoff {wait:.2f}s"
                    err = f"HTTP 429 rate-limited; honoured {why}"
                    att = Attempt(ts, engine, 0, False, err, lat)
                    self._record_attempt(att)
                    attempts.append(att)
                    last_error = err
                    self._backoff(wait)
                    continue

                if resp.status_code >= 400:
                    err = f"HTTP {resp.status_code} from SearXNG"
                    att = Attempt(ts, engine, 0, False, err, lat)
                    self._record_attempt(att)
                    attempts.append(att)
                    last_error = err
                    continue

                try:
                    payload = resp.json()
                except Exception as exc:
                    err = f"malformed JSON response: {exc.__class__.__name__}: {exc}"
                    att = Attempt(ts, engine, 0, False, err, lat)
                    self._record_attempt(att)
                    attempts.append(att)
                    last_error = err
                    continue

                if not isinstance(payload, dict):
                    err = (
                        "malformed JSON response: expected a JSON object, got "
                        f"{type(payload).__name__}"
                    )
                    att = Attempt(ts, engine, 0, False, err, lat)
                    self._record_attempt(att)
                    attempts.append(att)
                    last_error = err
                    continue

                # The engine self-report is the direct signal: surface it on the
                # attempt (and therefore on the sink) instead of discarding it.
                unresp = self._normalise_unresponsive(payload.get("unresponsive_engines"))
                parsed = self._parse_results(payload, engine)
                saw_ok = True
                att = Attempt(
                    ts,
                    engine,
                    len(parsed),
                    True,
                    None,
                    lat,
                    unresp,
                    self._responded_engines(parsed),
                )
                self._record_attempt(att)
                attempts.append(att)
                last_error = None

                if len(parsed) > 0:
                    results = parsed[:max_results] if max_results and max_results > 0 else parsed
                    break
                # ok=True with zero results -> rotate to the next engine

        all_unresponsive = self._merge_engines(attempts, "unresponsive_engines")
        all_responded = self._merge_engines(attempts, "responded_engines")

        if results:
            self._note_success()
            return SearchOutcome(
                query,
                results,
                True,
                self._degraded,
                attempts,
                None,
                self._degradation_reason,
                False,
                None,
                all_unresponsive,
                all_responded,
            )

        # The ok=True attempt that produced the (empty) verdict decides the
        # fast-empty escalation: a response under ``fast_empty_ms`` did not
        # search, it only answered.
        last_ok = next((a for a in reversed(attempts) if a.ok), None)
        fast_empty = bool(
            last_ok is not None
            and self.fast_empty_escalates
            and last_ok.latency_ms < self.fast_empty_ms
        )

        if saw_ok:
            self._negative_cache[key] = self._clock() + self.negative_ttl_s
            return self._empty_outcome(
                query,
                attempts,
                latency_ms=last_ok.latency_ms if last_ok is not None else None,
                fast_empty=fast_empty,
                unresponsive=all_unresponsive,
                responded=all_responded,
            )

        return SearchOutcome(
            query,
            [],
            False,
            self._degraded,
            attempts,
            last_error or "all attempts failed",
            self._degradation_reason,
            False,
            "transport failure: no attempt succeeded, so nothing was searched ("
            + (last_error or "all attempts failed")
            + ")",
            all_unresponsive,
            all_responded,
        )

    # --------------------------------------------------------------- async API
    async def search_many(
        self,
        queries: Iterable[str],
        *,
        concurrency: int = 2,
        **kwargs: Any,
    ) -> list[SearchOutcome]:
        """Run many queries with bounded concurrency over the *shared* limiter.

        Preserves input order.  Never raises: a crashed worker becomes an
        ``ok=False`` outcome so callers always get one outcome per query.
        """
        qs = list(queries)
        sem = asyncio.Semaphore(max(1, int(concurrency)))

        async def one(q: str) -> SearchOutcome:
            async with sem:
                try:
                    return await asyncio.to_thread(self.search, q, **kwargs)
                except Exception as exc:  # pragma: no cover - defensive
                    return SearchOutcome(
                        q,
                        [],
                        False,
                        self._degraded,
                        [],
                        f"search_many worker failed: {exc!r}",
                        self._degradation_reason,
                        False,
                        f"search worker raised before any search happened: {exc!r}",
                    )

        return list(await asyncio.gather(*(one(q) for q in qs)))

    # ------------------------------------------------------------------- stats
    def client_stats(self) -> ClientStats:
        mean = sum(self._latencies) / len(self._latencies) if self._latencies else 0.0
        return ClientStats(
            attempts=self._n_attempts,
            ok=self._n_ok,
            empty=self._n_empty,
            errors=self._n_error,
            degraded=self._degraded,
            mean_latency_ms=mean,
            degradation_reason=self._degradation_reason,
        )
