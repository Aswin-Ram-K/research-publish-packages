"""Web retrieval for ``resextract``: SearXNG discovery, page fetch, and cache.

This package owns exactly two capabilities and one cache:

* :mod:`resextract.web.search` -- a paced SearXNG client that reports empty and
  failed discovery honestly instead of dressing it up as "no prior art exists";
* :mod:`resextract.web.fetch` -- the local crawl/scrape bridge client that
  normalises, content-hashes and caches fetched pages under ``state/webcache``,
  so ``refresh()`` can prove whether cited evidence still says what it said.

The one invariant that matters: **an empty or stub response is never evidence of
absence, and never evidence of content.**  A zero-result search carries
``degraded`` plus a ``degradation_reason``; a page too short to be a page carries
``suspect`` plus ``suspicion="short_payload"``.  Neither may be cited as a
finding.

The public surface is exactly :data:`__all__`.  Note there is no ``SearchResult``
class: the search hit type is :class:`resextract.web.search.Result` (an earlier
handoff guessed a name that the module never had).
"""

from resextract.web.fetch import (
    FetchMeta,
    FetchResult,
    Fetcher,
    content_sha256,
    normalise_text,
)
from resextract.web.search import (
    DEFAULT_ENGINES,
    DEGRADATION_THRESHOLD,
    Attempt,
    ClientStats,
    DegradationEvidence,
    Result,
    SearchOutcome,
    SearXNGClient,
)

__all__ = [
    # search
    "DEFAULT_ENGINES",
    "DEGRADATION_THRESHOLD",
    "Attempt",
    "ClientStats",
    "DegradationEvidence",
    "Result",
    "SearchOutcome",
    "SearXNGClient",
    # fetch + cache
    "FetchMeta",
    "FetchResult",
    "Fetcher",
    "content_sha256",
    "normalise_text",
]
