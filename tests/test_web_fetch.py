"""Offline tests for ``resextract.web.fetch`` — fetch, cache, change detection.

Everything here is hermetic: ``httpx.MockTransport`` for the bridge, an injected
clock/sleep for pacing, a monkeypatched ``_resolve_host`` so the SSRF guard never
touches DNS, and ``tmp_path`` for the cache.  No test in this file makes a network
call; live evidence for this unit was gathered separately.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import httpx
import pytest

from resextract.web import fetch as fetch_mod
from resextract.web.fetch import (
    FetchMeta,
    FetchResult,
    Fetcher,
    content_sha256,
    extract_page_date,
    normalise_text,
)

PUBLIC_IP = "93.184.216.34"

# Hostnames the fake resolver knows about.  Unknown hosts resolve to a public IP
# so a test that forgets to register one still exercises the fetch path, not DNS.
RESOLVER_TABLE: dict[str, list[str]] = {
    "example.org": [PUBLIC_IP],
    "arxiv.org": [PUBLIC_IP],
    "raw.example.org": [PUBLIC_IP],
    "evil.example": ["127.0.0.1"],
    "v6loop.example": ["::1"],
    "linklocal.example": ["fe80::1"],
    "meta.example": ["169.254.169.254"],
    "private.example": ["10.1.2.3"],
    "mapped.example": ["::ffff:127.0.0.1"],
}


@pytest.fixture(autouse=True)
def fake_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the suite offline: the guard resolves names without touching DNS."""

    def _resolve(host: str) -> list[str]:
        lowered = host.lower().rstrip(".")
        if lowered == "localhost" or lowered.endswith(".localhost"):
            return ["127.0.0.1"]
        return list(RESOLVER_TABLE.get(lowered, [PUBLIC_IP]))

    monkeypatch.setattr(fetch_mod, "_resolve_host", _resolve)


# --------------------------------------------------------------------------- #
# Rig
# --------------------------------------------------------------------------- #


@dataclass
class Recorder:
    requests: list[httpx.Request] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.requests)

    def paths(self) -> list[str]:
        return [r.url.path for r in self.requests]

    def body(self, index: int) -> dict[str, Any]:
        return json.loads(self.requests[index].content.decode("utf-8"))


class FakeClock:
    """A clock that only moves when the injected sleep moves it."""

    def __init__(self, start: float = 1_000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t


class FakeSleep:
    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock
        self.delays: list[float] = []

    def __call__(self, delay: float) -> None:
        self.delays.append(delay)
        self.clock.t += delay


@dataclass
class Rig:
    fetcher: Fetcher
    recorder: Recorder
    clock: FakeClock
    sleep: FakeSleep


def make_rig(
    handler: Callable[[httpx.Request, int], httpx.Response],
    tmp_path: Path,
    **kwargs: Any,
) -> Rig:
    recorder = Recorder()

    def wrapped(request: httpx.Request) -> httpx.Response:
        index = len(recorder.requests)
        recorder.requests.append(request)
        return handler(request, index)

    clock = FakeClock()
    sleeper = FakeSleep(clock)
    kwargs.setdefault("min_interval_s", 0.0)
    # The payload-length *policy* is pinned to 1 for the mechanism tests below:
    # the real threshold (200) would route every short fixture through the scrape
    # path and change what those tests exercise.  The short-payload contract is
    # asserted explicitly with min_chars=200 in the dedicated tests at the end.
    kwargs.setdefault("min_chars", 1)
    fetcher = Fetcher(
        cache_dir=tmp_path,
        transport=httpx.MockTransport(wrapped),
        clock=clock,
        sleep=sleeper,
        **kwargs,
    )
    return Rig(fetcher=fetcher, recorder=recorder, clock=clock, sleep=sleeper)


def crawl(markdown: str, title: str = "A Paper", status: int = 200) -> httpx.Response:
    return httpx.Response(status, json={"title": title, "markdown": markdown})


def scrape(text: str, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json={"title": "", "text": text})


# Exactly 25 usable characters -- the size of the real gpt-2 stub this unit exists
# for (https://raw.githubusercontent.com/openai/gpt-2/main/README.md).
THIN = "short stub of exactly 25."
FULL = "y" * 900


def bridge(payloads: dict[str, list[httpx.Response]]) -> Callable[[httpx.Request, int], httpx.Response]:
    """Route by path, popping one canned response per call; empty ⇒ empty 200."""

    def handler(request: httpx.Request, index: int) -> httpx.Response:
        queue = payloads.get(request.url.path, [])
        if queue:
            return queue.pop(0)
        if request.url.path == "/crawl":
            return crawl("")
        return scrape("")

    return handler


# --------------------------------------------------------------------------- #
# fetch: crawl, scrape fallback, failures
# --------------------------------------------------------------------------- #


def test_crawl_success_captures_title_text_and_stable_sha(tmp_path: Path) -> None:
    text = "Attention Is All You Need\n\nWe propose a new architecture."
    rig = make_rig(bridge({"/crawl": [crawl(text, "Attention Is All You Need")]}), tmp_path)

    first = rig.fetcher.fetch("https://example.org/paper")

    assert first.ok is True
    assert first.error is None
    assert first.from_cache is False
    assert first.meta is not None
    assert first.meta.title == "Attention Is All You Need"
    assert first.meta.text == text
    assert first.meta.kind == "crawl"
    assert first.meta.page_date is None
    assert first.meta.http_status == 200
    assert first.meta.sha256 == content_sha256(text)
    assert rig.recorder.paths() == ["/crawl"]

    # Digest is stable across two calls on identical text (second is a cache hit
    # for the same URL, so use a fresh fetcher to force the crawl path again).
    other = make_rig(bridge({"/crawl": [crawl(text, "T")]}), tmp_path / "second")
    second = other.fetcher.fetch("https://example.org/paper")
    assert second.meta is not None and first.meta is not None
    assert second.meta.sha256 == first.meta.sha256


def test_nfc_normalisation_before_hashing(tmp_path: Path) -> None:
    composed = "Caf\u00e9 society: na\u00efve r\u00e9sum\u00e9"
    decomposed = unicodedata.normalize("NFD", composed)
    assert decomposed != composed  # guards the fixture, not the code

    assert content_sha256(decomposed) == content_sha256(composed)

    rig = make_rig(bridge({"/crawl": [crawl(decomposed, "Caf\u00e9")]}), tmp_path)
    result = rig.fetcher.fetch("https://example.org/nfc")

    assert result.ok is True and result.meta is not None
    assert result.meta.text == composed
    assert result.meta.sha256 == content_sha256(composed)
    assert result.meta.sha256 == hashlib.sha256(composed.encode("utf-8")).hexdigest()


def test_crawl_empty_triggers_scrape_fallback(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl("   \n  ")], "/scrape": [scrape("Scraped body text")]}),
        tmp_path,
    )

    result = rig.fetcher.fetch("https://example.org/thin")

    assert result.ok is True and result.meta is not None
    assert result.meta.kind == "scrape"
    assert result.meta.text == "Scraped body text"
    assert rig.recorder.paths() == ["/crawl", "/scrape"]
    body = rig.recorder.body(1)
    assert body["mode"] == "smart" and body["url"] == "https://example.org/thin"


def test_crawl_non_200_falls_back_to_scrape(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl("", status=500)], "/scrape": [scrape("fallback text")]}),
        tmp_path,
    )

    result = rig.fetcher.fetch("https://example.org/err")

    assert result.ok is True and result.meta is not None
    assert result.meta.kind == "scrape"
    assert result.meta.http_status == 200
    assert rig.recorder.paths() == ["/crawl", "/scrape"]


def test_scrape_mode_is_forwarded(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl("")], "/scrape": [scrape("stealthy text")]}), tmp_path
    )

    result = rig.fetcher.fetch("https://example.org/stealth", mode="stealthy")

    assert result.ok is True
    assert rig.recorder.body(1)["mode"] == "stealthy"


def test_both_paths_empty_is_a_specific_error_not_an_exception(tmp_path: Path) -> None:
    rig = make_rig(bridge({"/crawl": [crawl("")], "/scrape": [scrape("")]}), tmp_path)

    result = rig.fetcher.fetch("https://example.org/nothing")

    assert result.ok is False
    assert result.error == "empty_response"
    assert result.meta is None
    assert result.from_cache is False
    assert rig.recorder.paths() == ["/crawl", "/scrape"]


def test_transport_error_is_returned_not_raised(tmp_path: Path) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        raise httpx.ConnectError("bridge is down")

    rig = make_rig(handler, tmp_path)

    result = rig.fetcher.fetch("https://example.org/down")

    assert result.ok is False
    assert result.error is not None and result.error.startswith("transport_error")


def test_timeout_is_reported_as_timeout(tmp_path: Path) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        raise httpx.ReadTimeout("too slow")

    rig = make_rig(handler, tmp_path)

    result = rig.fetcher.fetch("https://example.org/slow")

    assert result.ok is False
    assert result.error == "timeout"


def test_scrape_fallback_disabled(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl("")], "/scrape": [scrape("should not be used")]}),
        tmp_path,
        scrape_fallback=False,
    )

    result = rig.fetcher.fetch("https://example.org/nofallback")

    assert result.ok is False
    assert result.error == "empty_response"
    assert rig.recorder.paths() == ["/crawl"]


# --------------------------------------------------------------------------- #
# cache behaviour
# --------------------------------------------------------------------------- #


def test_cache_hit_performs_zero_http_calls(tmp_path: Path) -> None:
    rig = make_rig(bridge({"/crawl": [crawl("cached body")]}), tmp_path)
    url = "https://example.org/cached"

    first = rig.fetcher.fetch(url)
    second = rig.fetcher.fetch(url)

    assert first.ok is True and second.ok is True
    assert rig.recorder.count == 1  # zero HTTP calls for the second fetch
    assert second.from_cache is True
    assert second.meta is not None and first.meta is not None
    assert second.meta.text == "cached body"
    assert second.meta.sha256 == first.meta.sha256

    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    assert (tmp_path / f"{key}.json").exists()
    assert (tmp_path / f"{key}.txt").read_text(encoding="utf-8") == "cached body"


def test_force_bypasses_the_cache(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl("v1"), crawl("v2")]}), tmp_path
    )
    url = "https://example.org/force"

    first = rig.fetcher.fetch(url)
    second = rig.fetcher.fetch(url, force=True)

    assert rig.recorder.count == 2
    assert first.meta is not None and second.meta is not None
    assert first.meta.text == "v1" and second.meta.text == "v2"
    assert second.from_cache is False
    assert second.changed is True
    assert second.detail == {
        "old_sha256": first.meta.sha256,
        "new_sha256": second.meta.sha256,
    }


def test_max_length_truncates_stored_text_but_bytes_in_reports_full(tmp_path: Path) -> None:
    body = "x" * 5000
    rig = make_rig(bridge({"/crawl": [crawl(body)]}), tmp_path)

    result = rig.fetcher.fetch("https://example.org/long", max_length=100)

    assert result.ok is True and result.meta is not None
    assert len(result.meta.text) == 100
    assert result.meta.bytes_in == 5000
    # usable_chars is measured on the *received* payload, before max_length
    # truncates our own copy: a deliberate storage cap is not a stub.
    assert result.usable_chars == 5000
    assert result.suspect is False
    stored = (tmp_path / f"{hashlib.sha256(b'https://example.org/long').hexdigest()}.txt")
    assert len(stored.read_text(encoding="utf-8")) == 100


def test_corrupt_cache_metadata_is_ignored(tmp_path: Path) -> None:
    url = "https://example.org/corrupt"
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / f"{key}.json").write_text("{not json", encoding="utf-8")
    rig = make_rig(bridge({"/crawl": [crawl("fresh")]}), tmp_path)

    result = rig.fetcher.fetch(url)

    assert result.ok is True and result.meta is not None
    assert result.meta.text == "fresh" and result.from_cache is False


# --------------------------------------------------------------------------- #
# refresh / change detection
# --------------------------------------------------------------------------- #


def test_refresh_unchanged_reports_changed_false(tmp_path: Path) -> None:
    """The invariant partner of the red→green pair below: this one must stay
    ``changed=False``.  With change detection reverted (``refresh`` setting
    ``changed = False`` unconditionally) this test *still* passes — which is
    exactly why the proof of detection lives in
    ``test_refresh_detects_changed_content_and_reports_both_digests``, where the
    reverted build fails.  GREEN: identical text ⇒ ``changed=False``, note
    ``unchanged``, both digests equal.
    """
    rig = make_rig(bridge({"/crawl": [crawl("same body"), crawl("same body")]}), tmp_path)
    url = "https://example.org/stable"

    first = rig.fetcher.fetch(url)
    again = rig.fetcher.refresh(url)

    assert first.ok is True and again.ok is True
    assert again.from_cache is False
    assert again.changed is False
    assert again.note == "unchanged"
    assert again.meta is not None and first.meta is not None
    assert again.detail == {
        "old_sha256": first.meta.sha256,
        "new_sha256": again.meta.sha256,
    }
    assert again.detail["old_sha256"] == again.detail["new_sha256"]


def test_refresh_detects_changed_content_and_reports_both_digests(tmp_path: Path) -> None:
    """RED (change detection reverted): ``refresh`` was reverted to
    ``result.changed = False`` unconditionally.  Observed failure::

        tests/test_web_fetch.py:418: in test_refresh_detects_changed_content_and_reports_both_digests
            assert changed.changed is True
        E   AssertionError: assert False is True
        E    +  where False = FetchResult(ok=True, meta=FetchMeta(url='https://example.org/moving', title='A Paper', text='version two', sha256='a67...e6ac7880ac765d16', 'new_sha256': 'a67d5f46542514f52d658493fc9405829d2922cf1647574c838b6b86f125477a'}, note='unchanged').changed

    ``test_refresh_without_previous_copy_is_changed_not_unchanged`` failed on the
    same revert (line 432, ``assert result.changed is True``).  GREEN: the changed
    copy reports ``changed=True`` with both digests (note ``content_changed``);
    identical content reports ``changed=False``.
    """
    rig = make_rig(
        bridge({"/crawl": [crawl("version one"), crawl("version two")]}), tmp_path
    )
    url = "https://example.org/moving"

    first = rig.fetcher.fetch(url)
    changed = rig.fetcher.refresh(url)

    assert changed.ok is True and changed.meta is not None and first.meta is not None
    assert first.meta.sha256 != changed.meta.sha256
    assert changed.changed is True
    assert changed.note == "content_changed"
    assert changed.detail == {
        "old_sha256": first.meta.sha256,
        "new_sha256": changed.meta.sha256,
    }


def test_refresh_without_previous_copy_is_changed_not_unchanged(tmp_path: Path) -> None:
    rig = make_rig(bridge({"/crawl": [crawl("first ever copy")]}), tmp_path)

    result = rig.fetcher.refresh("https://example.org/brand-new")

    assert result.ok is True and result.meta is not None
    assert result.changed is True
    assert result.note == "no_previous_copy"
    assert result.detail is not None
    assert result.detail["old_sha256"] is None
    assert result.detail["new_sha256"] == result.meta.sha256


def test_refresh_ignores_a_cached_copy_when_deciding(tmp_path: Path) -> None:
    """refresh must hit the network, not the cache, or it cannot see change."""
    rig = make_rig(bridge({"/crawl": [crawl("old"), crawl("new")]}), tmp_path)
    url = "https://example.org/nocache"

    rig.fetcher.fetch(url)
    result = rig.fetcher.refresh(url)

    assert rig.recorder.count == 2
    assert result.changed is True


# --------------------------------------------------------------------------- #
# page_date
# --------------------------------------------------------------------------- #


def test_page_date_from_arxiv_style_text(tmp_path: Path) -> None:
    page = (
        "Title: A Study of Something\n"
        "Authors: A. Author\n"
        "Submitted on 29 May 2025\n"
        "last revised 12 Mar 2026\n"
        "Abstract: we study things."
    )
    rig = make_rig(bridge({"/crawl": [crawl(page, "A Study of Something")]}), tmp_path)

    result = rig.fetcher.fetch("https://arxiv.org/abs/2505.22954")

    assert result.ok is True and result.meta is not None
    assert result.meta.page_date == "2025-05-29"


def test_page_date_last_revised_only() -> None:
    assert extract_page_date("some header\nlast revised 12 Mar 2026\n") == "2026-03-12"


def test_page_date_from_iso_near_top_and_time_tag() -> None:
    assert extract_page_date("Published: 2024-02-29\nbody text") == "2024-02-29"
    assert extract_page_date('<time datetime="2021-07-04T12:00:00Z">x</time>') == "2021-07-04"


def test_page_date_dateless_page_is_none(tmp_path: Path) -> None:
    assert extract_page_date("No dates here at all, just prose about methods.") is None
    assert extract_page_date("") is None
    assert extract_page_date(None) is None

    rig = make_rig(bridge({"/crawl": [crawl("prose without any date")]}), tmp_path)
    result = rig.fetcher.fetch("https://example.org/undated")
    assert result.meta is not None and result.meta.page_date is None


def test_page_date_never_invents_a_date() -> None:
    assert extract_page_date("2025-13-45 is not a date") is None
    assert extract_page_date("submitted on 31 Feb 2025") is None
    # A date buried past the head window is not treated as the page date.
    assert extract_page_date("lead\n" + ("x" * 4000) + "\n2024-01-01") is None


# --------------------------------------------------------------------------- #
# PDFs
# --------------------------------------------------------------------------- #


def test_pdf_url_is_recorded_as_unsupported_and_not_fetched(tmp_path: Path) -> None:
    rig = make_rig(bridge({}), tmp_path)

    result = rig.fetcher.fetch("https://example.org/paper.pdf")

    assert result.ok is False
    assert result.error == "pdf_not_supported"
    assert rig.recorder.count == 0  # no request, no exception
    assert result.meta is not None and result.meta.kind == "pdf"
    assert result.meta.text == ""
    # a cached PDF stays a recorded non-result rather than becoming text
    again = rig.fetcher.fetch("https://example.org/paper.pdf")
    assert again.ok is False and again.error == "pdf_not_supported"
    assert rig.recorder.count == 0


def test_pdf_bytes_from_bridge_are_not_treated_as_text(tmp_path: Path) -> None:
    def handler(request: httpx.Request, index: int) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj",
            headers={"content-type": "application/pdf"},
        )

    rig = make_rig(handler, tmp_path)

    result = rig.fetcher.fetch("https://example.org/download")

    assert result.ok is False
    assert result.error == "pdf_not_supported"


# --------------------------------------------------------------------------- #
# SSRF guard
# --------------------------------------------------------------------------- #


def test_ssrf_guard_refuses_non_http_schemes(tmp_path: Path) -> None:
    """RED (guard reverted): the guard call in ``_fetch`` was replaced by
    ``if False:``.  Observed failure::

        tests/test_web_fetch.py:555: in test_ssrf_guard_refuses_non_http_schemes
            assert result.error == "blocked_url", url
        E   AssertionError: file:///etc/passwd
        E   assert 'empty_response' == 'blocked_url'
        E     - blocked_url
        E     + empty_response

    That single revert broke 18 of the 19 SSRF/allow-private/check tests in this
    file (``18 failed, 1 passed, 33 deselected``), including ``http://127.0.0.1/x``,
    ``http://169.254.169.254/latest/meta-data/``, the DNS-name-to-loopback cases and
    ``check()`` on a metadata URL.  GREEN: the guard refuses before any request.
    """
    rig = make_rig(bridge({}), tmp_path)

    for url in ("file:///etc/passwd", "ftp://example.org/x", "gopher://example.org/1"):
        result = rig.fetcher.fetch(url)
        assert result.ok is False, url
        assert result.error == "blocked_url", url
    assert rig.recorder.count == 0


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/x",
        "http://127.9.9.9:8080/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://192.168.2.1/",
        "http://10.0.0.5/internal",
        "http://172.16.4.4/",
        "http://[::1]:9000/",
        "http://localhost:8891/health",
        "http://evil.example/",  # DNS name pointing at loopback
        "http://v6loop.example/",
        "http://linklocal.example/",
        "http://meta.example/",
        "http://private.example/",
        "http://mapped.example/",
    ],
)
def test_ssrf_guard_refuses_private_and_metadata_targets(url: str, tmp_path: Path) -> None:
    rig = make_rig(bridge({}), tmp_path)

    result = rig.fetcher.fetch(url)

    assert result.ok is False
    assert result.error == "blocked_url"
    assert result.from_cache is False
    assert rig.recorder.count == 0


def test_ssrf_guard_is_enforced_on_a_cached_url_too(tmp_path: Path) -> None:
    """A guard that only runs on a cache miss is not a guard."""
    import shutil

    rig = make_rig(bridge({"/crawl": [crawl("local doc")]}), tmp_path, allow_private=True)
    private = "http://127.0.0.1:8891/health"

    assert rig.fetcher.fetch(private).ok is True  # cached while permitted

    strict = make_rig(bridge({}), tmp_path / "strict")
    (tmp_path / "strict").mkdir(parents=True, exist_ok=True)
    for path in list(tmp_path.glob("*.json")) + list(tmp_path.glob("*.txt")):
        shutil.copy(path, tmp_path / "strict" / path.name)

    result = strict.fetcher.fetch(private)

    assert result.ok is False
    assert result.error == "blocked_url"
    assert strict.recorder.count == 0


def test_allow_private_true_permits_a_loopback_target(tmp_path: Path) -> None:
    rig = make_rig(bridge({"/crawl": [crawl("local doc")]}), tmp_path, allow_private=True)

    result = rig.fetcher.fetch("http://127.0.0.1:8891/health")

    assert result.ok is True and result.meta is not None
    assert result.meta.text == "local doc"
    assert rig.recorder.count == 1
    assert rig.recorder.body(0)["url"] == "http://127.0.0.1:8891/health"


def test_allow_private_does_not_whitelist_other_schemes(tmp_path: Path) -> None:
    rig = make_rig(bridge({}), tmp_path, allow_private=True)

    result = rig.fetcher.fetch("file:///etc/passwd")

    assert result.ok is False and result.error == "blocked_url"


def test_public_host_is_allowed(tmp_path: Path) -> None:
    rig = make_rig(bridge({"/crawl": [crawl("public text")]}), tmp_path)

    assert rig.fetcher.fetch("https://example.org/ok").ok is True
    assert rig.recorder.count == 1


# --------------------------------------------------------------------------- #
# pacing
# --------------------------------------------------------------------------- #


def test_per_host_pacing_uses_injected_clock_and_sleep(tmp_path: Path) -> None:
    rig = make_rig(
        bridge(
            {
                "/crawl": [
                    crawl("one"),
                    crawl("two"),
                    crawl("three"),
                    crawl("four"),
                ]
            }
        ),
        tmp_path,
        min_interval_s=1.0,
    )

    rig.fetcher.fetch("https://example.org/one")
    assert rig.sleep.delays == []  # first request is never delayed
    rig.fetcher.fetch("https://example.org/two")
    assert len(rig.sleep.delays) == 1
    assert rig.sleep.delays[0] == pytest.approx(1.0)

    # A second host has its own bucket: its first request waits for nothing.
    rig.fetcher.fetch("https://raw.example.org/file")
    assert len(rig.sleep.delays) == 1
    # ...and only its second request is paced.
    rig.fetcher.fetch("https://raw.example.org/file2")
    assert len(rig.sleep.delays) == 2
    assert rig.sleep.delays[1] == pytest.approx(1.0)


def test_no_pacing_when_interval_is_zero(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl("a"), crawl("b")]}), tmp_path, min_interval_s=0.0
    )
    rig.fetcher.fetch("https://example.org/a")
    rig.fetcher.fetch("https://example.org/b")

    assert rig.sleep.delays == []


def test_cache_hit_does_not_sleep(tmp_path: Path) -> None:
    rig = make_rig(bridge({"/crawl": [crawl("body")]}), tmp_path, min_interval_s=5.0)
    rig.fetcher.fetch("https://example.org/x")
    rig.fetcher.fetch("https://example.org/x")

    assert rig.sleep.delays == []
    assert rig.recorder.count == 1


# --------------------------------------------------------------------------- #
# check()
# --------------------------------------------------------------------------- #


def test_check_probes_and_returns_ok_error_suspect_tuple(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl("fine"), crawl("")], "/scrape": [scrape("")]}), tmp_path
    )
    url = "https://example.org/link"

    ok, error, suspect = rig.fetcher.check(url)
    assert (ok, error) == (True, None)
    assert suspect is False

    ok, error, suspect = rig.fetcher.check("https://example.org/rotted")
    assert ok is False and error == "empty_response"
    assert suspect is False, "a rotted link is gone, not a stub"


def test_check_uses_a_separate_cache_key(tmp_path: Path) -> None:
    rig = make_rig(bridge({"/crawl": [crawl("short probe"), crawl("full body")]}), tmp_path)
    url = "https://example.org/both"

    rig.fetcher.check(url)
    full = rig.fetcher.fetch(url)

    assert full.ok is True and full.meta is not None
    assert full.meta.text == "full body"  # the probe did not poison the full copy
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_check_never_raises_on_a_blocked_url(tmp_path: Path) -> None:
    rig = make_rig(bridge({}), tmp_path)

    ok, error, suspect = rig.fetcher.check("http://169.254.169.254/latest/meta-data")

    assert ok is False and error == "blocked_url"
    assert suspect is False


# --------------------------------------------------------------------------- #
# result surface
# --------------------------------------------------------------------------- #


def test_fetch_result_properties_and_failure_shape(tmp_path: Path) -> None:
    rig = make_rig(bridge({}), tmp_path)

    result = rig.fetcher.fetch("http://10.0.0.1/x")

    assert isinstance(result, FetchResult)
    assert result.text == "" and result.sha256 is None and result.page_date is None
    assert result.suspect is False and result.suspicion is None
    assert result.usable_chars == 0


def test_meta_dataclass_field_order_matches_the_contract() -> None:
    names = list(FetchMeta.__dataclass_fields__)
    assert names == [
        "url",
        "title",
        "text",
        "sha256",
        "fetched_at",
        "kind",
        "page_date",
        "http_status",
        "bytes_in",
        "cache_path",
    ]


def test_normalise_text_is_idempotent() -> None:
    decomposed = unicodedata.normalize("NFD", "r\u00e9sum\u00e9")
    once = normalise_text(decomposed)
    assert once == unicodedata.normalize("NFC", decomposed)
    assert normalise_text(once) == once
    assert normalise_text(None) == ""


# --------------------------------------------------------------------------- #
# short payloads: fallback, suspicion, and refresh
# --------------------------------------------------------------------------- #


def test_short_crawl_falls_back_to_scrape_and_the_page_is_not_suspect(
    tmp_path: Path,
) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl(THIN)], "/scrape": [scrape(FULL)]}),
        tmp_path,
        min_chars=200,
    )

    result = rig.fetcher.fetch("https://example.org/stub")

    assert result.ok is True and result.meta is not None
    assert result.meta.kind == "scrape", "a 25-char crawl must not be accepted"
    assert result.meta.text == FULL
    assert result.suspect is False and result.suspicion is None
    assert result.usable_chars == 900
    assert rig.recorder.paths() == ["/crawl", "/scrape"]


def test_short_payload_is_suspect_not_evidence(tmp_path: Path) -> None:
    """RED -> GREEN guard #2: a short payload is flagged, never cited.

    Reverted-suspicion run (``suspect = usable < self.min_chars`` replaced by
    ``suspect = False``) produced, verbatim::

        __________________ test_short_payload_is_suspect_not_evidence __________________
        tests/test_web_fetch.py:839: in test_short_payload_is_suspect_not_evidence
            assert result.suspect is True
        E   AssertionError: assert False is True
        E    +  where False = FetchResult(ok=True, meta=FetchMeta(url='https://example.org/stub', title='A Paper', text='short stub of exactly 25.',...), error=None, from_cache=False, changed=False, detail=None, note=None, suspect=False, suspicion=None, usable_chars=25).suspect

    Restoring the comparison turns it green.
    """
    assert len(THIN) == 25
    rig = make_rig(
        bridge({"/crawl": [crawl(THIN)], "/scrape": [scrape(THIN)]}),
        tmp_path,
        min_chars=200,
    )

    result = rig.fetcher.fetch("https://example.org/stub")

    assert result.ok is True, "the bridge answered; that is not the same as a page"
    assert result.suspect is True
    assert result.suspicion == "short_payload"
    assert result.usable_chars == 25
    assert result.error is None
    assert result.meta is not None and result.meta.text == THIN


def test_full_page_is_not_suspect_and_does_not_fall_back(tmp_path: Path) -> None:
    rig = make_rig(bridge({"/crawl": [crawl(FULL)]}), tmp_path, min_chars=200)

    result = rig.fetcher.fetch("https://example.org/full")

    assert result.ok is True and result.meta is not None
    assert result.suspect is False and result.suspicion is None
    assert result.usable_chars == 900
    assert rig.recorder.paths() == ["/crawl"], "a full crawl needs no scrape"


def test_suspect_is_error_turns_the_stub_into_a_failure(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl(THIN)], "/scrape": [scrape(THIN)]}),
        tmp_path,
        min_chars=200,
        suspect_is_error=True,
    )

    result = rig.fetcher.fetch("https://example.org/stub")

    assert result.ok is False
    assert result.error == "short_payload"
    assert result.suspect is True and result.suspicion == "short_payload"
    assert result.usable_chars == 25


def test_short_crawl_without_fallback_is_suspect_not_an_error(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl(THIN)]}),
        tmp_path,
        min_chars=200,
        scrape_fallback=False,
    )

    result = rig.fetcher.fetch("https://example.org/stub")

    assert result.ok is True and result.suspect is True
    assert result.usable_chars == 25
    assert rig.recorder.paths() == ["/crawl"]


def test_refresh_can_never_upgrade_a_suspect_stub(tmp_path: Path) -> None:
    rig = make_rig(
        bridge(
            {
                "/crawl": [crawl(THIN), crawl(THIN)],
                "/scrape": [scrape(THIN), scrape(THIN)],
            }
        ),
        tmp_path,
        min_chars=200,
    )
    url = "https://example.org/stub"

    first = rig.fetcher.fetch(url)
    assert first.ok is True and first.suspect is True

    again = rig.fetcher.refresh(url)
    assert again.ok is True
    assert again.suspect is True, "refreshing a stub must not launder it"
    assert again.suspicion == "short_payload"
    assert again.usable_chars == 25
    assert again.changed is False and again.note == "unchanged"

    cached = rig.fetcher.fetch(url)
    assert cached.from_cache is True
    assert cached.suspect is True, "a cached stub stays a stub"


def test_check_distinguishes_gone_from_stub(tmp_path: Path) -> None:
    rig = make_rig(
        bridge({"/crawl": [crawl(THIN)], "/scrape": [scrape(THIN)]}),
        tmp_path,
        min_chars=200,
    )

    ok, error, suspect = rig.fetcher.check("https://example.org/stub")

    assert ok is True and error is None
    assert suspect is True


def test_default_thresholds_are_the_documented_contract(tmp_path: Path) -> None:
    fetcher = Fetcher(cache_dir=tmp_path)
    assert fetcher.min_chars == 200
    assert fetcher.suspect_is_error is False


def test_pdf_is_not_reported_as_a_short_payload(tmp_path: Path) -> None:
    """An empty text field is only a *stub* if the transport said ok."""
    rig = make_rig(bridge({}), tmp_path, min_chars=200)
    url = "https://example.org/paper.pdf"

    first = rig.fetcher.fetch(url)
    again = rig.fetcher.fetch(url)
    ok, error, suspect = rig.fetcher.check(url, use_cache=True)

    assert first.ok is False and first.error == "pdf_not_supported"
    assert again.ok is False and again.error == "pdf_not_supported"
    assert again.usable_chars == 0
    assert again.suspect is False, "a refused PDF is not a short text payload"
    assert (ok, error, suspect) == (False, "pdf_not_supported", False)
    assert rig.recorder.count == 0, "no HTTP call for a PDF URL"
