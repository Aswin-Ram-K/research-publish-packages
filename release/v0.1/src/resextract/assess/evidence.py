"""Evidence gathering for the assessment stage (unit U4.1).

This module turns one claim into a small set of *auditable* evidence records by
researching the outside world through the already-verified web layer
(:mod:`resextract.web.search`, :mod:`resextract.web.fetch`).

The honesty rules of that web layer are consumed exactly as documented, never
second-guessed:

* :attr:`SearchOutcome.absence_is_meaningful` is a **hard gate**.  An empty
  outcome with ``absence_is_meaningful=False`` is a *broken* search: it is
  counted in :attr:`GatherResult.degraded_searches` together with the engine
  reason, and it can never become evidence for anything.  An empty outcome with
  ``absence_is_meaningful=True`` is a *clean* "nothing found" -- which is still
  **not** evidence of novelty, so it gets its own, distinct reason string.
* :attr:`FetchResult.suspect` marks a stub (the real ``gpt-2`` README case
  returned a 25-char GitHub ``404: Not Found`` body).  A suspect fetch is
  counted in :attr:`GatherResult.suspect_fetches` and is **excluded** from the
  evidence records.
* A fetch whose text contains none of the claim's key terms is a **weak**
  source.  It is recorded (so the mismatch stays visible and auditable) but its
  ``context`` names the mismatch instead of silently accepting it.

Nothing in here decides whether a claim is true or novel; that is
:mod:`resextract.assess.verdicts`.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "EvidenceRecord",
    "GatherResult",
    "STOPWORDS",
    "generate_queries",
    "gather_evidence",
    "key_terms",
    "quote_from",
    "term_ratio",
    "utcnow",
]

#: Bounded number of characters kept in any recorded quote.
DEFAULT_QUOTE_CHARS = 400

#: Terms too common to discriminate one claim from any other page.
STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or but if then than that this these those of in on at to for from by with
    without into over under about as is are was were be been being do does did done has have
    had having will would shall should can could may might must not no nor so such very more
    most other some any all each every both few many much own same too only just also it its
    they them their there here when where which who whom what why how while during before after
    above below up down out off again further once because until against between through our
    your his her him she he we you i us me my mine ours yours theirs still exists exist
    """.split()
)

#: Claim kinds whose wording is metadata noise rather than a searchable assertion.
_META_PREFIXES: tuple[str, ...] = (
    "the miner ref ",
    "the candidate ",
)

_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+#./:-]*")


def utcnow() -> str:
    """Second-resolution UTC timestamp, matching the store's own convention."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------- #
# records
# --------------------------------------------------------------------------- #


@dataclass
class EvidenceRecord:
    """One auditable piece of outside-world evidence for a claim."""

    claim_id: int | None
    source_kind: str
    source_ref: str
    sha256: str
    quote: str
    context: str
    retrieved_at: str
    copy_path: str | None = None
    page_date: str | None = None
    title: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "sha256": self.sha256,
            "quote": self.quote,
            "context": self.context,
            "retrieved_at": self.retrieved_at,
            "copy_path": self.copy_path,
            "page_date": self.page_date,
            "title": self.title,
        }


@dataclass
class GatherResult:
    """Everything one claim's evidence pass did -- including what it refused to do."""

    records: list[EvidenceRecord] = field(default_factory=list)
    searches: list[dict[str, Any]] = field(default_factory=list)
    degraded_searches: list[dict[str, Any]] = field(default_factory=list)
    suspect_fetches: list[dict[str, Any]] = field(default_factory=list)
    fetched: int = 0
    reasons: list[str] = field(default_factory=list)
    #: additive, observable without changing the required fields
    queries: list[str] = field(default_factory=list)
    query_source: str = "none"
    weak_sources: list[str] = field(default_factory=list)
    clean_empty: bool = False
    fetch_attempts: int = 0
    candidate_urls: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "records": [r.as_dict() for r in self.records],
            "searches": list(self.searches),
            "degraded_searches": list(self.degraded_searches),
            "suspect_fetches": list(self.suspect_fetches),
            "fetched": self.fetched,
            "reasons": list(self.reasons),
            "queries": list(self.queries),
            "query_source": self.query_source,
            "weak_sources": list(self.weak_sources),
            "clean_empty": self.clean_empty,
            "fetch_attempts": self.fetch_attempts,
            "candidate_urls": list(self.candidate_urls),
        }


# --------------------------------------------------------------------------- #
# query generation
# --------------------------------------------------------------------------- #


def key_terms(text: str) -> list[str]:
    """Ordered, de-duplicated content terms of ``text`` (identifiers kept whole)."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in _TOKEN_RE.findall(text or ""):
        tok = raw.strip(".,;:()[]{}<>\"'`").lower()
        if len(tok) < 3 or tok in STOPWORDS:
            continue
        if tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
    return out


def lexical_queries(claim: Any, *, max_queries: int = 3) -> list[str]:
    """Deterministic, model-free queries derived purely from the claim text.

    Used whenever no LLM client is supplied; :func:`generate_queries` records
    which of the two paths produced the query list.
    """
    text = _claim_text(claim)
    terms = key_terms(text)
    # Keep the most distinctive tokens first: long identifiers (snake_case,
    # dotted paths) discriminate far better than short English words.
    ranked = sorted(terms, key=lambda t: (-_specificity(t), terms.index(t)))
    queries: list[str] = []
    if ranked:
        queries.append(" ".join(ranked[:8]))
    if len(ranked) > 2:
        queries.append(" ".join(ranked[:4]))
        queries.append(" ".join(ranked[:2] + ["prior", "art"]))
    if not queries:
        queries.append(text.strip()[:120])
    out: list[str] = []
    for q in queries:
        q = " ".join(q.split())
        if q and q not in out:
            out.append(q)
        if len(out) >= max(1, int(max_queries)):
            break
    return out


def _specificity(term: str) -> int:
    score = 1 if ("_" in term or "/" in term or "." in term or "-" in term) else 0
    return score * 10 + len(term)


def _claim_text(claim: Any) -> str:
    if isinstance(claim, Mapping):
        return str(claim.get("text") or "")
    return str(getattr(claim, "text", "") or "")


def _claim_identity(claim: Any) -> str:
    if isinstance(claim, Mapping):
        cid = claim.get("claim_id", claim.get("id"))
        return f"claim:{cid}" if cid is not None else str(claim.get("text") or "")
    cid = getattr(claim, "claim_id", None)
    return f"claim:{cid}" if cid is not None else _claim_text(claim)


def generate_queries(claim: Any, *, client: Any = None, max_queries: int = 3) -> list[str]:
    """1--3 search queries for ``claim``.

    With ``client`` (an occurrence of the project's Occamy client, or any object
    exposing ``call_json``) the queries are model-written with **thinking off**
    and a small token budget, because this is a cheap rewriting step.  Without a
    client the deterministic :func:`lexical_queries` fallback is used.  The path
    actually taken is recorded on :class:`GatherResult.query_source`.
    """
    queries, _ = generate_queries_with_source(claim, client=client, max_queries=max_queries)
    return queries


def generate_queries_with_source(
    claim: Any, *, client: Any = None, max_queries: int = 3, budget: Any = None
) -> tuple[list[str], str]:
    """Like :func:`generate_queries` but also returns ``"model"``/``"lexical"``.

    ``budget`` (when given) is charged for the model call *before* it leaves the
    process, so a query-rewriting call is never free: every model call in this
    stage counts against the same ceiling.
    """
    limit = max(1, int(max_queries))
    if client is not None:
        try:
            if budget is not None:
                budget.begin_call()
            model = _query_schema()
            payload = client.call_json(
                [
                    {
                        "role": "system",
                        "content": (
                            "You write web search queries that would find prior art "
                            "for one technical claim. Reply with JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Claim: {_claim_text(claim)}\n"
                            f"Write at most {limit} short search queries, most specific first."
                        ),
                    },
                ],
                model,
                thinking=False,
                max_tokens=512,
                label="assess.queries",
            )
            raw = list(getattr(payload, "queries", []) or [])
            queries = [" ".join(str(q).split()) for q in raw if str(q).strip()]
            queries = [q for q in dict.fromkeys(queries) if q][:limit]
            if queries:
                return queries, "model"
        except Exception as exc:  # noqa: BLE001 - a model failure degrades to lexical
            if type(exc).__name__ == "BudgetExhausted":
                raise
            pass
        return lexical_queries(claim, max_queries=limit), "lexical"
    return lexical_queries(claim, max_queries=limit), "lexical"


def _query_schema() -> type:
    from pydantic import BaseModel

    class _QueryList(BaseModel):
        queries: list[str]

    return _QueryList


# --------------------------------------------------------------------------- #
# verbatim quoting
# --------------------------------------------------------------------------- #


def quote_from(text: str, terms: Sequence[str], *, max_chars: int = DEFAULT_QUOTE_CHARS) -> str:
    """A bounded, **verbatim** excerpt of ``text`` centred on the best match.

    "Best match" is the longest claim term that actually occurs in the page --
    longer terms are more specific.  The returned value is always a literal
    substring of ``text`` (never a paraphrase) and never longer than
    ``max_chars``; when no term occurs the bounded head of the page is returned
    verbatim so the reader can see the mismatch for themselves.
    """
    text = text or ""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    low = text.lower()
    best_pos, best_len = -1, 0
    for term in terms or []:
        t = str(term or "").strip().lower()
        if not t:
            continue
        pos = low.find(t)
        if pos >= 0 and len(t) > best_len:
            best_pos, best_len = pos, len(t)
    if best_pos < 0:
        return text[:max_chars]
    span = max_chars - best_len
    start = max(0, best_pos - span // 2)
    end = min(len(text), start + max_chars)
    start = max(0, end - max_chars)
    # Snap to whitespace so the excerpt starts on a word, not mid-token.
    if start > 0:
        nxt = text.find(" ", start)
        if nxt != -1 and nxt < best_pos:
            start = nxt + 1
    if end < len(text):
        prev = text.rfind(" ", start, end)
        if prev != -1 and prev > best_pos:
            end = prev
    return text[start:end]


def term_ratio(text: str, terms: Sequence[str]) -> float:
    """Fraction of ``terms`` that occur in ``text`` (0.0 when there are none)."""
    terms = [t for t in (str(x).strip() for x in (terms or [])) if t]
    if not terms:
        return 0.0
    low = (text or "").lower()
    hits = sum(1 for t in terms if t.lower() in low)
    return hits / len(terms)


# --------------------------------------------------------------------------- #
# gathering
# --------------------------------------------------------------------------- #


def gather_evidence(
    claim: Any,
    *,
    search: Any,
    fetcher: Any,
    client: Any = None,
    budget: Any = None,
    max_queries: int = 3,
    max_sources: int = 3,
    max_quote_chars: int = DEFAULT_QUOTE_CHARS,
    max_length: int | None = None,
    min_term_ratio: float = 0.0,
    retrieved_at: str | None = None,
    clock: Any = None,
) -> GatherResult:
    """Research one claim and return evidence -- or an honest account of why not.

    Rule for a **weak** source: a fetched page whose text contains **none** of
    the claim's key terms (``term_ratio == 0.0``) is recorded with ``context``
    naming the mismatch, so a page that merely mentions the claim's topic is
    never silently promoted to evidence.

    Never raises for network trouble: search and fetch failures are values.
    """
    del min_term_ratio  # the strict rule is ratio == 0.0; kept for signature stability
    now = retrieved_at or utcnow()
    clock = clock or time.monotonic
    result = GatherResult()

    queries, source = generate_queries_with_source(
        claim, client=client, max_queries=max_queries, budget=budget
    )
    result.queries = queries
    result.query_source = source
    if not queries:
        result.reasons.append("no search queries could be derived from this claim")
        return result

    claim_terms = key_terms(_claim_text(claim))
    urls: list[str] = []
    seen_urls: set[str] = set()

    for query in queries:
        outcome = _run_search(search, query)
        entry = _search_entry(query, outcome)
        result.searches.append(entry)
        if outcome is None:
            result.degraded_searches.append(entry)
            result.reasons.append(f"search failed for {query!r}: {entry['reason']}")
            continue
        hits = list(getattr(outcome, "results", []) or [])
        if hits:
            for hit in hits:
                url = str(getattr(hit, "url", "") or "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    urls.append(url)
            continue
        if not getattr(outcome, "absence_is_meaningful", False):
            result.degraded_searches.append(entry)
            result.reasons.append(
                f"search for {query!r} returned nothing but is not meaningful: "
                f"{entry['reason']}"
            )
        else:
            result.clean_empty = True
            result.reasons.append(
                f"a clean search ({query!r}) found no matching prior art; "
                "finding nothing is not evidence of novelty"
            )

    result.candidate_urls = urls[: max(0, int(max_sources))]

    for url in result.candidate_urls:
        result.fetch_attempts += 1
        fetched = _run_fetch(fetcher, url, max_length=max_length)
        if fetched is None:
            result.reasons.append(f"fetch failed for {url}: no result returned")
            continue
        if not getattr(fetched, "ok", False):
            result.reasons.append(
                f"fetch failed for {url}: {getattr(fetched, 'error', None) or 'unknown error'}"
            )
            continue
        if getattr(fetched, "suspect", False):
            result.suspect_fetches.append(
                {
                    "url": url,
                    "suspicion": getattr(fetched, "suspicion", None) or "suspect",
                    "excluded": True,
                }
            )
            result.reasons.append(
                f"fetch for {url} is suspect "
                f"({getattr(fetched, 'suspicion', None) or 'suspect'}); excluded from evidence"
            )
            continue
        meta = getattr(fetched, "meta", None)
        text = getattr(fetched, "text", "") or ""
        title = str(getattr(meta, "title", "") or "")
        page_date = getattr(meta, "page_date", None) or getattr(fetched, "page_date", None)
        sha = getattr(meta, "sha256", "") or ""
        copy_path = getattr(meta, "cache_path", None)
        ratio = term_ratio(text, claim_terms)
        quote = quote_from(text, claim_terms, max_chars=max_quote_chars)
        if ratio <= 0.0:
            result.weak_sources.append(url)
            context = (
                "weak source: fetched text contains none of the claim's key terms "
                f"({', '.join(claim_terms[:8]) or 'no terms'}); terms present: "
                f"{', '.join(sorted(set(key_terms(text))))[:200] or 'none'}"
            )
            result.reasons.append(f"weak source (no key terms matched): {url}")
        else:
            context = (
                f"key-term match {ratio:.2f}; terms present: "
                f"{', '.join(t for t in claim_terms if t in text.lower())[:200]}"
            )
        result.records.append(
            EvidenceRecord(
                claim_id=None,
                source_kind="web",
                source_ref=url,
                sha256=sha,
                quote=quote,
                context=context,
                retrieved_at=now,
                copy_path=str(copy_path) if copy_path else None,
                page_date=str(page_date) if page_date else None,
                title=title,
            )
        )
        result.fetched += 1

    if not result.records and not result.reasons:
        result.reasons.append("the search produced no candidate sources to fetch")
    return result


def _run_search(search: Any, query: str) -> Any:
    try:
        return search.search(query)
    except Exception:  # noqa: BLE001 - a crashed search is a degraded search
        return None


def _run_fetch(fetcher: Any, url: str, *, max_length: int | None) -> Any:
    try:
        if max_length is None:
            return fetcher.fetch(url)
        return fetcher.fetch(url, max_length=max_length)
    except TypeError:
        try:
            return fetcher.fetch(url)
        except Exception:  # noqa: BLE001
            return None
    except Exception:  # noqa: BLE001 - a crashed fetch is a failed fetch
        return None


def _search_entry(query: str, outcome: Any) -> dict[str, Any]:
    if outcome is None:
        return {
            "query": query,
            "ok": False,
            "results": 0,
            "degraded": True,
            "absence_is_meaningful": False,
            "reason": "search raised an exception before returning an outcome",
        }
    results = list(getattr(outcome, "results", []) or [])
    reason = (
        getattr(outcome, "absence_reason", None)
        or getattr(outcome, "degradation_reason", None)
        or getattr(outcome, "error", None)
        or "unknown"
    )
    return {
        "query": query,
        "ok": bool(getattr(outcome, "ok", False)),
        "results": len(results),
        "degraded": bool(getattr(outcome, "degraded", False))
        or (not results and not getattr(outcome, "absence_is_meaningful", False)),
        "absence_is_meaningful": bool(getattr(outcome, "absence_is_meaningful", False)),
        "absence_reason": getattr(outcome, "absence_reason", None),
        "unresponsive_engines": list(getattr(outcome, "unresponsive_engines", []) or []),
        "reason": str(reason),
    }


def evidence_hash(records: Iterable[EvidenceRecord | Mapping[str, Any]]) -> str:
    """Content hash of an evidence set (used for resume/idempotency keys)."""
    parts: list[str] = []
    for rec in records:
        d = rec.as_dict() if isinstance(rec, EvidenceRecord) else dict(rec)
        parts.append(
            "|".join(
                str(d.get(k) or "")
                for k in ("source_ref", "sha256", "quote", "page_date")
            )
        )
    blob = "\n".join(sorted(parts))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
