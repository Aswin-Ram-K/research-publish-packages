"""Fetch, content-hash cache and change detection for ``resextract``.

**Why a content-hash cache exists.**  A docket's claims are only worth as much as
the evidence behind them, and evidence retrieved from the web decays: pages are
edited, retracted, moved or taken down.  So every fetched URL is written down
twice — metadata as ``state/webcache/<sha256(url)>.json`` and the extracted text
as ``state/webcache/<sha256(url)>.txt`` (``fetch`` hashes the *URL*, the cache is
keyed by identity, not by content).  The text's own ``sha256`` is the fingerprint
of *what we actually read*.

**Why ``refresh`` compares content hashes instead of trusting HTTP status.**  An
HTTP ``200`` only says the server answered; it says nothing about whether the
bytes are the same ones the sentence in the docket was written from.  A blog post
can be silently rewritten, an arXiv abstract can be replaced across versions, a
"200 OK" can carry a changed article or a soft-404 holding page — and gzip,
Cloudflare and edge caches make anything derived from headers or ``Content-Length``
unreliable.  The only honest test of "is my evidence still true?" is: refetch, and
compare the hash of the normalised text against the hash we recorded.  Different
digest ⇒ the evidence is stale (``changed=True``); identical digest ⇒ it is still
the same text (``changed=False``).  A missing previous copy is *not* "unchanged" —
it means we cannot certify anything, so it reports ``changed=True`` with
``note="no_previous_copy"``.

Text is NFC-normalised (``unicodedata.normalize("NFC", ...)``) *before* hashing
and before being stored, because the same visible text can arrive as composed or
decomposed code points (``é`` as U+00E9 vs ``e`` + U+0301) depending on the
server's encoding path; without normalisation non-ASCII corpora would hash
differently across runs and the refresh engine would cry wolf.

The layer talks to the local crawl/scrape bridge (default
``http://127.0.0.1:8891``): ``POST /crawl`` first, and if that yields fewer than
``min_chars`` usable characters, ``POST /scrape`` as a fallback.  A payload that
is *still* short is never silently passed off as a page: the result stays
``ok=True`` (the transport worked) but carries ``suspect=True`` and
``suspicion="short_payload"`` with the observed ``usable_chars``, so a docket can
refuse to cite a stub.  With ``suspect_is_error=True`` the same payload becomes
``ok=False, error="short_payload"``.  Nothing here raises: every failure is
returned as ``ok=False`` with a specific ``error`` string.  PDFs are recorded as
``pdf_not_supported`` rather than faked, because the Docling PDF bridge is not a
dependency of this layer.

SSRF: every URL is checked *before* any request — non-http(s) schemes, loopback,
link-local, private ranges and the cloud metadata address are refused with
``error="blocked_url"`` unless ``allow_private=True``.  Hostnames are resolved
first, so a DNS name that points at loopback is refused too; a hostname that
cannot be resolved at all is not blocked by the guard (there is nothing to judge)
and simply fails later as a transport error.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import time
import unicodedata
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlsplit

import httpx

__all__ = [
    "FetchMeta",
    "FetchResult",
    "Fetcher",
    "content_sha256",
    "normalise_text",
]

# --------------------------------------------------------------------------- #
# Errors returned in FetchResult.error
# --------------------------------------------------------------------------- #

ERR_BLOCKED = "blocked_url"
ERR_PDF = "pdf_not_supported"
ERR_EMPTY = "empty_response"
ERR_SHORT = "short_payload"
ERR_TIMEOUT = "timeout"
ERR_HTTP = "bridge_http_error"

# --------------------------------------------------------------------------- #
# Text normalisation + hashing
# --------------------------------------------------------------------------- #


def normalise_text(text: Optional[str]) -> str:
    """NFC-normalise decoded text.  Never returns ``None``."""
    return unicodedata.normalize("NFC", text or "")


def content_sha256(text: Optional[str]) -> str:
    """sha256 over the NFC-normalised UTF-8 encoding of ``text``."""
    return hashlib.sha256(normalise_text(text).encode("utf-8")).hexdigest()


def _usable_chars(text: Optional[str]) -> int:
    """Length of ``text`` after NFC normalisation and stripping whitespace."""
    return len(normalise_text(text).strip())


# --------------------------------------------------------------------------- #
# SSRF guard
# --------------------------------------------------------------------------- #

_PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(net)
    for net in (
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)

_METADATA_ADDRESSES = frozenset({"169.254.169.254", "fd00:ec2::254"})
_BLOCKED_HOST_NAMES = frozenset({"localhost", "metadata", "metadata.google.internal"})


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def _ip_is_blocked(ip_text: str) -> bool:
    """True for loopback / link-local / private / metadata addresses."""
    try:
        ip: Any = ipaddress.ip_address(ip_text.strip("[]"))
    except ValueError:
        return True  # unparseable => refuse rather than guess
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if str(ip) in _METADATA_ADDRESSES:
        return True
    if ip.is_loopback or ip.is_link_local or ip.is_private or ip.is_reserved:
        return True
    if ip.is_multicast or ip.is_unspecified:
        return True
    for net in _PRIVATE_NETWORKS:
        if ip.version == net.version and ip in net:
            return True
    return False


def _resolve_host(host: str) -> list[str]:
    """Resolve ``host`` to a list of IP strings; ``[]`` when unresolvable.

    Kept module-level and side-effect free so tests can monkeypatch it and keep
    the suite offline.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return []
    out: list[str] = []
    for info in infos:
        try:
            out.append(str(ipaddress.ip_address(info[4][0])))
        except Exception:
            continue
    return out


def _ssrf_blocked(url: str, allow_private: bool) -> bool:
    """Return True when ``url`` must not be requested."""
    parts = urlsplit(url)
    if parts.scheme.lower() not in ("http", "https"):
        return True
    host = parts.hostname
    if not host:
        return True
    if allow_private:
        return False
    lowered = host.lower().rstrip(".")
    if lowered in _BLOCKED_HOST_NAMES or lowered.endswith(".localhost"):
        return True
    if _is_ip_literal(host):
        return _ip_is_blocked(host)
    for ip in _resolve_host(host):
        if _ip_is_blocked(ip):
            return True
    return False


# --------------------------------------------------------------------------- #
# Page-date extraction
# --------------------------------------------------------------------------- #

_ARXIV_DATE_RE = re.compile(
    r"(?:Submitted\s+on|last\s+revised|Submitted)\s+"
    r"(\d{1,2})\s+([A-Za-z]{3,9})\.?\s+(\d{4})",
    re.IGNORECASE,
)
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_TIME_TAG_RE = re.compile(
    r"""<time[^>]*\bdatetime\s*=\s*["']([^"']+)["']""", re.IGNORECASE
)

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_ISO_HEAD_CHARS = 3000


def _iso_or_none(year: int, month: int, day: int) -> Optional[str]:
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


def _parse_iso_prefix(value: str) -> Optional[str]:
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value.strip())
    if not match:
        return None
    return _iso_or_none(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def extract_page_date(text: Optional[str]) -> Optional[str]:
    """Best-effort publication/update date as ``YYYY-MM-DD``, else ``None``.

    Handles, in priority order: arXiv-style ``Submitted on 29 May 2025`` /
    ``last revised 12 Mar 2026``; a ``<time datetime="...">`` tag; a bare ISO
    ``YYYY-MM-DD`` in the first :data:`_ISO_HEAD_CHARS` characters (which covers
    markdown meta lines such as ``Published: 2025-01-02``).  Never invents a
    date: an unparsable or absent date yields ``None``.
    """
    raw = text or ""
    if not raw.strip():
        return None

    for match in _ARXIV_DATE_RE.finditer(raw):
        month = _MONTHS.get(match.group(2)[:3].lower())
        if month is None:
            continue
        date = _iso_or_none(int(match.group(3)), month, int(match.group(1)))
        if date:
            return date

    for match in _TIME_TAG_RE.finditer(raw):
        date = _parse_iso_prefix(match.group(1))
        if date:
            return date

    for match in _ISO_DATE_RE.finditer(raw[:_ISO_HEAD_CHARS]):
        date = _iso_or_none(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if date:
            return date

    return None


# --------------------------------------------------------------------------- #
# Payload helpers
# --------------------------------------------------------------------------- #

_TEXT_KEYS = ("markdown", "text", "content", "result", "body", "data")


def _extract_payload(response: httpx.Response) -> tuple[str, str]:
    """Pull ``(title, text)`` out of a bridge response (JSON or plain text)."""
    try:
        data = response.json()
    except Exception:
        return "", response.text or ""
    if isinstance(data, dict):
        title = data.get("title") or ""
        for key in _TEXT_KEYS:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return str(title), value
        return str(title), ""
    if isinstance(data, str):
        return "", data
    return "", ""


def _looks_like_pdf(response: httpx.Response, text: str) -> bool:
    ctype = (response.headers.get("content-type") or "").lower()
    if "application/pdf" in ctype:
        return True
    body = response.content or b""
    head = body[:1024].lstrip()
    if head.startswith(b"%PDF-"):
        return True
    return "%PDF-" in (text or "")[:64]


def _is_pdf_url(url: str) -> bool:
    return urlsplit(url).path.lower().rstrip("/").endswith(".pdf")


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #


@dataclass
class FetchMeta:
    """Everything we know about one fetched URL."""

    url: str
    title: str = ""
    text: str = ""
    sha256: str = ""
    fetched_at: str = ""
    kind: str = ""
    page_date: Optional[str] = None
    http_status: Optional[int] = None
    bytes_in: int = 0
    cache_path: Optional[str] = None


@dataclass
class FetchResult:
    """Outcome of a fetch/refresh; failures are values, never exceptions."""

    ok: bool
    meta: Optional[FetchMeta] = None
    error: Optional[str] = None
    from_cache: bool = False
    changed: bool = False
    detail: Optional[dict[str, Any]] = None
    note: Optional[str] = None
    suspect: bool = False
    suspicion: Optional[str] = None
    usable_chars: int = 0

    @property
    def text(self) -> str:
        return self.meta.text if self.meta else ""

    @property
    def sha256(self) -> Optional[str]:
        return self.meta.sha256 if self.meta else None

    @property
    def page_date(self) -> Optional[str]:
        return self.meta.page_date if self.meta else None


_META_FIELD_NAMES = tuple(f.name for f in fields(FetchMeta))


def _meta_from_dict(payload: dict[str, Any]) -> FetchMeta:
    return FetchMeta(**{k: v for k, v in payload.items() if k in _META_FIELD_NAMES})


# --------------------------------------------------------------------------- #
# Fetcher
# --------------------------------------------------------------------------- #


class Fetcher:
    """Fetch URLs through the local bridge, caching text + metadata on disk.

    ``clock`` and ``sleep`` are injected so per-host pacing is testable without
    real waiting; ``transport`` (an ``httpx`` transport, e.g.
    ``httpx.MockTransport``) makes the whole class testable offline.
    """

    def __init__(
        self,
        bridge_url: str = "http://127.0.0.1:8891",
        *,
        cache_dir: str | Path = "state/webcache",
        timeout_s: float = 45.0,
        max_length: int = 12000,
        scrape_fallback: bool = True,
        min_chars: int = 200,
        suspect_is_error: bool = False,
        min_interval_s: float = 1.0,
        allow_private: bool = False,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.bridge_url = bridge_url.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.timeout_s = float(timeout_s)
        self.max_length = int(max_length)
        self.scrape_fallback = bool(scrape_fallback)
        self.min_chars = max(0, int(min_chars))
        self.suspect_is_error = bool(suspect_is_error)
        self.min_interval_s = float(min_interval_s)
        self.allow_private = bool(allow_private)
        self._clock = clock
        self._sleep = sleep
        self._transport = transport
        self._last_request: dict[str, float] = {}
        self.stats = {"http_calls": 0, "cache_hits": 0, "pacing_sleeps": 0}

    # -- public API -------------------------------------------------------- #

    def fetch(
        self,
        url: str,
        *,
        force: bool = False,
        max_length: Optional[int] = None,
        mode: Optional[str] = None,
    ) -> FetchResult:
        """Fetch ``url`` (cache first unless ``force``); never raises.

        The SSRF guard runs before the cache lookup *and* before any request, so
        a cached-but-now-private URL is refused rather than served.
        """
        return self._fetch(url, force=force, max_length=max_length, mode=mode)

    def refresh(
        self,
        url: str,
        *,
        mode: Optional[str] = None,
        max_length: Optional[int] = None,
    ) -> FetchResult:
        """Re-fetch ``url`` and say whether its content changed.

        ``changed`` is ``sha256(new text) != sha256(cached text)``.  With no
        previous copy there is nothing to compare, so ``changed=True`` and
        ``note="no_previous_copy"`` — an uncertifiable docket is stale, not
        unchanged.  ``detail`` always carries ``old_sha256`` / ``new_sha256``.

        A suspect (short) payload is re-flagged on the re-fetch, so refreshing a
        stub can never upgrade it into evidence.
        """
        prior = self._cached_meta(url)
        result = self._fetch(url, force=True, max_length=max_length, mode=mode)
        old = prior.sha256 if prior and prior.sha256 else None
        new = result.meta.sha256 if result.ok and result.meta else None
        if not result.ok:
            result.changed = True
            result.note = "refresh_failed"
            result.detail = {"old_sha256": old, "new_sha256": new}
            return result
        if old is None:
            result.changed = True
            result.note = "no_previous_copy"
        elif old == new:
            result.changed = False
            result.note = "unchanged"
        else:
            result.changed = True
            result.note = "content_changed"
        result.detail = {"old_sha256": old, "new_sha256": new}
        return result

    def check(
        self, url: str, *, use_cache: bool = False, max_length: int = 600
    ) -> tuple[bool, Optional[str], bool]:
        """Cheap reachability probe for link-rot checks: ``(ok, error, suspect)``.

        Uses a short fetch cached under a separate ``-check`` key so it never
        overwrites the full-text copy.  By default it probes live.

        ``suspect`` distinguishes "the link is gone" (``ok=False``) from "the
        link answered with a stub" (``ok=True, suspect=True``) — a link-rot sweep
        must not report a stub as a healthy citation.
        """
        result = self._fetch(
            url,
            force=not use_cache,
            max_length=min(int(max_length), self.max_length),
            suffix="-check",
            compare=False,
        )
        return result.ok, result.error, result.suspect

    # -- internals --------------------------------------------------------- #

    def _client(self) -> httpx.Client:
        kwargs: dict[str, Any] = {"timeout": self.timeout_s, "follow_redirects": True}
        if self._transport is not None:
            kwargs["transport"] = self._transport
        return httpx.Client(**kwargs)

    def _cache_key(self, url: str, suffix: str = "") -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest() + suffix

    def _meta_path(self, url: str, suffix: str = "") -> Path:
        return self.cache_dir / f"{self._cache_key(url, suffix)}.json"

    def _text_path(self, url: str, suffix: str = "") -> Path:
        return self.cache_dir / f"{self._cache_key(url, suffix)}.txt"

    def _read_cache(
        self, url: str, suffix: str = ""
    ) -> Optional[tuple[FetchMeta, bool, Optional[str], dict[str, Any]]]:
        meta_path = self._meta_path(url, suffix)
        if not meta_path.exists():
            return None
        try:
            payload = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        meta = _meta_from_dict(payload)
        text_path = self._text_path(url, suffix)
        try:
            if text_path.exists():
                meta.text = normalise_text(text_path.read_text(encoding="utf-8"))
        except Exception:
            meta.text = ""
        meta.cache_path = str(meta_path)
        extras: dict[str, Any] = {
            "suspect": bool(payload.get("suspect", False)),
            "suspicion": payload.get("suspicion"),
            "usable_chars": payload.get("usable_chars"),
        }
        return meta, bool(payload.get("ok", True)), payload.get("error"), extras

    def _cached_meta(self, url: str, suffix: str = "") -> Optional[FetchMeta]:
        cached = self._read_cache(url, suffix)
        return cached[0] if cached else None

    def _write_cache(
        self,
        meta: FetchMeta,
        ok: bool,
        error: Optional[str],
        suffix: str = "",
        *,
        suspect: bool = False,
        suspicion: Optional[str] = None,
        usable_chars: Optional[int] = None,
    ) -> Path:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        meta_path = self._meta_path(meta.url, suffix)
        text_path = self._text_path(meta.url, suffix)
        text_path.write_text(meta.text, encoding="utf-8")
        payload = asdict(meta)
        payload["ok"] = ok
        payload["error"] = error
        payload["cache_path"] = str(meta_path)
        payload["suspect"] = bool(suspect)
        payload["suspicion"] = suspicion
        payload["usable_chars"] = (
            _usable_chars(meta.text) if usable_chars is None else int(usable_chars)
        )
        meta.cache_path = str(meta_path)
        tmp = meta_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(meta_path)
        return meta_path

    def _pace(self, host: str) -> None:
        if self.min_interval_s <= 0:
            return
        last = self._last_request.get(host)
        if last is not None:
            wait = self.min_interval_s - (self._clock() - last)
            if wait > 0:
                self._sleep(wait)
                self.stats["pacing_sleeps"] += 1
        self._last_request[host] = self._clock()

    def _fetch(
        self,
        url: str,
        *,
        force: bool,
        max_length: Optional[int] = None,
        mode: Optional[str] = None,
        suffix: str = "",
        compare: bool = True,
    ) -> FetchResult:
        limit = int(max_length) if max_length else self.max_length

        # 1) SSRF guard — before the cache and before any socket.
        if _ssrf_blocked(url, self.allow_private):
            return FetchResult(ok=False, meta=None, error=ERR_BLOCKED)

        # 2) PDFs are recorded, never faked.
        if _is_pdf_url(url):
            meta = self._pdf_meta(url)
            self._write_cache(meta, False, ERR_PDF, suffix)
            return FetchResult(ok=False, meta=meta, error=ERR_PDF)

        # 3) Cache first (zero HTTP calls on a hit).
        if not force:
            cached = self._read_cache(url, suffix)
            if cached is not None:
                meta, stored_ok, stored_error, extras = cached
                self.stats["cache_hits"] += 1
                cached_usable = extras.get("usable_chars")
                usable = (
                    _usable_chars(meta.text)
                    if cached_usable is None
                    else int(cached_usable)
                )
                suspect = bool(extras.get("suspect")) or (
                    stored_ok and usable < self.min_chars
                )
                return FetchResult(
                    ok=stored_ok,
                    meta=meta,
                    error=None if stored_ok else (stored_error or ERR_EMPTY),
                    from_cache=True,
                    changed=False,
                    detail={"cache_path": meta.cache_path},
                    suspect=suspect,
                    suspicion="short_payload" if suspect else None,
                    usable_chars=usable,
                )

        prior = self._cached_meta(url, suffix) if compare else None

        # 4) Live fetch.  ``usable`` counts the received payload's stripped
        #    characters *before* max_length truncation: suspicion is about what
        #    the source gave us, not about our own storage cap.
        meta, error, usable = self._fetch_live(url, limit, mode)
        if error is not None:
            result = FetchResult(ok=False, meta=meta, error=error)
            if meta is not None:
                self._write_cache(meta, False, error, suffix)
            return result

        assert meta is not None  # for type checkers; error is None here

        # 5) A payload too short to be a page is not silently a page.  It is
        #    still cached, so refresh() can see it change -- and refresh() on it
        #    stays suspect, so no docket can upgrade a stub into evidence.
        suspect = usable < self.min_chars
        suspicion = "short_payload" if suspect else None
        if suspect and self.suspect_is_error:
            self._write_cache(
                meta,
                False,
                ERR_SHORT,
                suffix,
                suspect=True,
                suspicion=suspicion,
                usable_chars=usable,
            )
            return FetchResult(
                ok=False,
                meta=meta,
                error=ERR_SHORT,
                suspect=True,
                suspicion=suspicion,
                usable_chars=usable,
            )

        changed = False
        detail: Optional[dict[str, Any]] = None
        if prior is not None and prior.sha256 and prior.sha256 != meta.sha256:
            changed = True
            detail = {"old_sha256": prior.sha256, "new_sha256": meta.sha256}
        self._write_cache(
            meta,
            True,
            None,
            suffix,
            suspect=suspect,
            suspicion=suspicion,
            usable_chars=usable,
        )
        return FetchResult(
            ok=True,
            meta=meta,
            error=None,
            from_cache=False,
            changed=changed,
            detail=detail,
            suspect=suspect,
            suspicion=suspicion,
            usable_chars=usable,
        )

    def _pdf_meta(self, url: str) -> FetchMeta:
        return FetchMeta(
            url=url,
            title="",
            text="",
            sha256=content_sha256(""),
            fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            kind="pdf",
            page_date=None,
            http_status=None,
            bytes_in=0,
            cache_path=str(self._meta_path(url)),
        )

    def _fetch_live(
        self, url: str, limit: int, mode: Optional[str]
    ) -> tuple[Optional[FetchMeta], Optional[str], int]:
        """Crawl, then scrape when the crawl payload is short.

        Returns ``(meta, error, usable_chars)``.  ``usable_chars`` is the stripped
        length of the *received* payload before ``max_length`` truncation.  The
        longer of the two payloads wins, so a scrape can only improve on a thin
        crawl and never downgrade a usable one.
        """
        host = (urlsplit(url).hostname or "").lower()
        crawl_status: Optional[int] = None
        crawl_error: Optional[str] = None
        best_text = ""
        best_title = ""
        best_kind = ""
        best_status: Optional[int] = None

        try:
            self._pace(host)
            with self._client() as client:
                self.stats["http_calls"] += 1
                response = client.post(
                    f"{self.bridge_url}/crawl", json={"url": url, "maxLength": limit}
                )
                crawl_status = response.status_code
                if response.status_code == 200:
                    if _looks_like_pdf(response, ""):
                        meta = self._pdf_meta(url)
                        meta.http_status = crawl_status
                        return None, ERR_PDF, 0
                    title, text = _extract_payload(response)
                else:
                    title, text = "", ""
                crawl_usable = _usable_chars(text)
                if crawl_usable > 0:
                    best_text = text
                    best_title = title
                    best_kind = "crawl"
                    best_status = crawl_status

                if crawl_usable >= self.min_chars:
                    return (
                        self._build_meta(
                            url, best_title, best_text, best_status, best_kind, limit
                        ),
                        None,
                        crawl_usable,
                    )

                # Thin (or empty) crawl: try the scrape path when allowed.
                if not self.scrape_fallback:
                    if crawl_usable > 0:
                        return (
                            self._build_meta(
                                url, best_title, best_text, best_status, best_kind, limit
                            ),
                            None,
                            crawl_usable,
                        )
                    return None, (ERR_HTTP if crawl_status != 200 else ERR_EMPTY), 0

                scrape_status: Optional[int] = None
                scrape_error: Optional[str] = None
                try:
                    self._pace(host)
                    self.stats["http_calls"] += 1
                    response = client.post(
                        f"{self.bridge_url}/scrape",
                        json={"url": url, "mode": mode or "smart", "maxLength": limit},
                    )
                    scrape_status = response.status_code
                    if scrape_status == 200:
                        if _looks_like_pdf(response, ""):
                            meta = self._pdf_meta(url)
                            meta.http_status = scrape_status
                            return None, ERR_PDF, 0
                        scrape_title, scrape_text = _extract_payload(response)
                        scrape_usable = _usable_chars(scrape_text)
                        if scrape_usable >= max(crawl_usable, 1):
                            best_text = scrape_text or ""
                            best_title = best_title or scrape_title
                            best_kind = "scrape"
                            best_status = scrape_status
                except httpx.TimeoutException:
                    scrape_error = ERR_TIMEOUT
                except Exception as exc:  # transport failure, DNS, protocol…
                    scrape_error = f"transport_error: {type(exc).__name__}: {exc}"

                if best_text.strip():
                    return (
                        self._build_meta(
                            url, best_title, best_text, best_status, best_kind, limit
                        ),
                        None,
                        _usable_chars(best_text),
                    )
                if scrape_error is not None:
                    return None, scrape_error, 0
                if scrape_status is not None and scrape_status != 200:
                    return None, f"transport_error: bridge returned HTTP {scrape_status}", 0
                return None, ERR_EMPTY, 0
        except httpx.TimeoutException:
            crawl_error = ERR_TIMEOUT
        except Exception as exc:
            crawl_error = f"transport_error: {type(exc).__name__}: {exc}"

        if crawl_error is not None:
            return None, crawl_error, 0
        if crawl_status is not None and crawl_status != 200:
            return None, f"transport_error: bridge returned HTTP {crawl_status}", 0
        return None, ERR_EMPTY, 0

    def _build_meta(
        self,
        url: str,
        title: str,
        text: str,
        status: Optional[int],
        kind: str,
        limit: int,
    ) -> FetchMeta:
        full = normalise_text(text)
        stored = full[:limit] if limit > 0 else full
        return FetchMeta(
            url=url,
            title=normalise_text(title).strip(),
            text=stored,
            sha256=content_sha256(text),
            fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            kind=kind,
            page_date=extract_page_date(full),
            http_status=status,
            bytes_in=len(full.encode("utf-8")) if full else len(stored),
            cache_path=str(self._meta_path(url)),
        )
