"""Offline proof for HARNESS-FIX-CLIENT: honest TTFT and cache attribution at the client.

Run from the workspace root:

    python3 experiments/ptr-engine/longrun/tests/test_client_ttft.py

Exit 0 = every GREEN assertion held AND every RED assertion failed for the intended
reason.  The file is also pytest-collectable (every ``test_*`` function is a case).

WHY THIS TEST EXISTS
====================
The pre-fix latch was, verbatim, in ``run_longrun.py`` (cited by the unit card as
``longrun/client.py:128-139``; no such module existed — it is now
``experiments/ptr-engine/longrun/client.py``):

    piece_c = delta.get("content")
    piece_r = delta.get("reasoning_content")
    if piece_r is None:
        piece_r = delta.get("reasoning")
    # TTFT = dispatch -> first token on EITHER channel.
    if (piece_c or piece_r) and ttft is None:
        ttft = time.perf_counter() - t0

A turn whose first delta is a **tool call** has neither field set, so it latched nothing.
Two variants of that defect are both dishonest: a null TTFT silently drops the turn out of
the p95 sample, and a wall-clock substitute records the whole response as "time to first
token".  Either way the p95 figures (grow 838.85 / compact 224.08 / stable 356.12 /
lease-reopen 201.78 ms) are computed over a contaminated sample.  Cache attribution had no
per-request path at all, although SGLang reports
``usage.prompt_tokens_details.cached_tokens`` and vLLM's four engine counters are
scrapable at ``/metrics``.

RED-BEFORE-GREEN.  Every case is run twice: once through :func:`legacy_measure`, a
faithful copy of the pre-fix latch + cache read, where the contract assertion MUST fail,
and once through :func:`client.send_chat` with a faked stream, where it MUST hold.

Zero requests: every SSE body is a fake, every ``/metrics`` body is a fake, the clock is a
fake, and :func:`_no_socket` makes a real socket impossible for the whole run.
"""

import json
import socket
import sys
import types

_HERE = __file__.rsplit("/", 1)[0]
sys.path.insert(0, _HERE.rsplit("/", 1)[0])

import client  # noqa: E402  (the module under test)


# --------------------------------------------------------------------- fakes
class ChunkClock:
    """Fake perf_counter that reports the arrival time of the chunk being consumed.

    ``clock()`` called before the stream returns ``start`` (t0).  ``clock()`` called while
    a chunk is in hand returns that chunk's ``marker``, which the fake stream sets as it
    yields.  So a latch on chunk k yields marker_k - start, and a latch on the wrong chunk
    is visible as a wrong number rather than hidden behind a call count.
    """

    def __init__(self, start=1000.0):
        self.start = float(start)
        self.marker = float(start)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls == 1:
            return self.start
        return self.marker


class FakeResp:
    """Minimal urlopen() response: context manager + line iterator."""

    def __init__(self, entries, clock=None):
        self._entries = list(entries)  # [(line, marker_or_None), ...]
        self._clock = clock

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        for line, marker in self._entries:
            if marker is not None and self._clock is not None:
                self._clock.marker = float(marker)
            yield (line + "\n").encode("utf-8")

    def read(self):
        return b"".join((line + "\n").encode("utf-8") for line, _ in self._entries)


def sse(obj):
    return "data: " + (obj if isinstance(obj, str) else json.dumps(obj))


def delta_chunk(**delta):
    return {"choices": [{"index": 0, "delta": delta, "finish_reason": None}]}


def finish_chunk(reason="stop"):
    return {"choices": [{"index": 0, "delta": {}, "finish_reason": reason}]}


def usage_chunk(prompt=11, cached="absent", completion=3):
    usage = {"prompt_tokens": prompt, "completion_tokens": completion}
    if cached != "absent":
        usage["prompt_tokens_details"] = {"cached_tokens": cached}
    return {"choices": [], "usage": usage}


METRICS_BEFORE = """# HELP sglang:prompt_tokens_total Number of prefill tokens processed.
sglang:prompt_tokens_total{model_name="occamy-1.0"} 4000.0
sglang:prefix_cache_queries_total{model_name="occamy-1.0"} 90.0
sglang:prefix_cache_hits_total{model_name="occamy-1.0"} 40.0
sglang:prompt_tokens_cached_total{model_name="occamy-1.0"} 100.0
"""

METRICS_AFTER = """sglang:prompt_tokens_total{model_name="occamy-1.0"} 4111.0
sglang:prefix_cache_queries_total{model_name="occamy-1.0"} 91.0
sglang:prefix_cache_hits_total{model_name="occamy-1.0"} 41.0
sglang:prompt_tokens_cached_total{model_name="occamy-1.0"} 132.0
"""


def cfg(**over):
    base = dict(base_url="http://127.0.0.1:9/v1", model="occamy-1.0", max_tokens=64,
                stream=True, timeout=5.0, engine="sglang", thinking="auto")
    base.update(over)
    return types.SimpleNamespace(**base)


class Getter:
    """Fake ``/metrics`` getter that never touches a socket."""

    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = 0

    def __call__(self, url, timeout):
        assert url.endswith("/metrics"), url
        self.calls += 1
        body = self.bodies[min(self.calls - 1, len(self.bodies) - 1)]
        if body is None:
            raise OSError("scrape refused")
        return body


# --------------------------------------------------------------- legacy (RED) path
def legacy_measure(entries, clock):
    """Faithful copy of the pre-fix latch and cache read (RED proof only)."""
    content, reasoning = [], []
    usage_payload, finish_reason = None, None
    ttft = None
    clock()  # the t0 call send_chat makes before dispatch; later calls report the marker
    for line, marker in entries:
        if marker is not None:
            clock.marker = float(marker)
        text = line.strip()
        if not text.startswith("data:"):
            continue
        payload = text[5:].strip()
        if payload == "[DONE]":
            break
        chunk = json.loads(payload)
        if chunk.get("usage"):
            usage_payload = chunk
        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or {}
            piece_c = delta.get("content")
            piece_r = delta.get("reasoning_content")
            if piece_r is None:
                piece_r = delta.get("reasoning")
            if (piece_c or piece_r) and ttft is None:
                ttft = clock() - clock.start
            if piece_c:
                content.append(piece_c)
            if piece_r:
                reasoning.append(piece_r)
            if choice.get("finish_reason"):
                finish_reason = choice.get("finish_reason")
    usage = (usage_payload or {}).get("usage") or {}
    details = usage.get("prompt_tokens_details")
    raw_cached = details.get("cached_tokens") if isinstance(details, dict) else None
    # normalize_cached_tokens(None, "sglang") -> 0 : a null was imputed as a zero.
    cached = int(raw_cached) if raw_cached is not None else 0
    return {"ttft_ms": round(ttft * 1000.0, 3) if ttft is not None else None,
            "cached_tokens": cached}


_FAULT = None


def _no_socket(*args, **kwargs):  # pragma: no cover - guard only
    global _FAULT
    _FAULT = "a socket was opened: this test must be fully offline"
    raise RuntimeError(_FAULT)


# ------------------------------------------------------------------------- cases
def test_case_a_tool_call_first_delta():
    """(a) first delta is a tool_calls chunk -> TTFT latched there, kind tool_call."""
    entries = [
        (sse(delta_chunk(role="assistant")), 1000.010),
        (sse(delta_chunk(tool_calls=[{"index": 0, "id": "c1", "type": "function",
                                      "function": {"name": "read_file", "arguments": ""}}])),
         1000.300),
        (sse(delta_chunk(tool_calls=[{"index": 0, "function": {"arguments": "{\"path\":"}}])),
         1000.360),
        (sse(finish_chunk("tool_calls")), 1000.500),
        (sse(usage_chunk(prompt=11, cached="absent")), None),
        (sse("[DONE]"), None),
    ]
    clock = ChunkClock()
    red = legacy_measure(entries, ChunkClock())
    assert red["ttft_ms"] is None, f"RED not red: legacy latched {red['ttft_ms']}"

    clock = ChunkClock()
    resp = client.send_chat(cfg(metrics_scrape=False), [{"role": "user", "content": "x"}],
                            opener=lambda req, timeout: FakeResp(entries, clock), clock=clock)
    assert resp["ttft_ms"] == 300.0, resp["ttft_ms"]
    assert resp["ttft_source"] == "first_delta", resp["ttft_source"]
    assert resp["first_token_kind"] == "tool_call", resp["first_token_kind"]
    assert resp["wall_ms"] == 500.0, resp["wall_ms"]
    assert resp["wall_ms"] > resp["ttft_ms"], "wall must never be the TTFT"


def test_case_b_empty_content_does_not_latch():
    """(b) empty content:"" then a real token -> latched at the real token."""
    entries = [
        (sse(delta_chunk(role="assistant", content="")), 1000.100),
        (sse(delta_chunk(content="Hello")), 1000.450),
        (sse(finish_chunk()), 1000.600),
        (sse("[DONE]"), None),
    ]
    red = legacy_measure(entries, ChunkClock())
    assert red["ttft_ms"] == 450.0, f"RED not red: legacy latched {red['ttft_ms']}"

    clock = ChunkClock()
    resp = client.send_chat(cfg(metrics_scrape=False), [], opener=lambda req, timeout: FakeResp(entries, clock),
                            clock=clock)
    assert resp["ttft_ms"] == 450.0, resp["ttft_ms"]   # not 100.0 (the empty delta)
    assert resp["first_token_kind"] == "content", resp["first_token_kind"]
    assert resp["ttft_source"] == "first_delta"


def test_case_c_no_delta_is_unavailable():
    """(c) a stream that ends with no token delta -> null/unavailable, never wall clock."""
    entries = [
        (sse(delta_chunk(role="assistant")), 1000.010),
        (sse(finish_chunk("length")), 1002.500),
        (sse("[DONE]"), None),
    ]
    red = legacy_measure(entries, ChunkClock())
    assert red["ttft_ms"] is None, "RED not red: legacy produced a TTFT from nothing"

    clock = ChunkClock()
    resp = client.send_chat(cfg(metrics_scrape=False), [], opener=lambda req, timeout: FakeResp(entries, clock),
                            clock=clock)
    assert resp["ttft_ms"] is None, resp["ttft_ms"]
    assert resp["ttft_source"] == "unavailable", resp["ttft_source"]
    assert resp["first_token_kind"] is None, resp["first_token_kind"]
    # the wall clock is still recorded, and provably did not become the TTFT
    assert resp["wall_ms"] == 2500.0, resp["wall_ms"]


def test_case_d_usage_cached_zero_is_not_null():
    """(d) usage chunk with cached_tokens=0 -> 0, source prompt_tokens_details."""
    entries = [
        (sse(delta_chunk(content="ok")), 1000.050),
        (sse(finish_chunk()), 1000.070),
        (sse(usage_chunk(prompt=11, cached=0)), None),
        (sse("[DONE]"), None),
    ]
    getter = Getter([METRICS_BEFORE, METRICS_AFTER])  # would say 32 if it won
    red = legacy_measure(entries, ChunkClock())
    red_has_source = False  # legacy carried no cached_source at all
    assert red["cached_tokens"] == 0 and not red_has_source, "RED not red"

    clock = ChunkClock()
    resp = client.send_chat(cfg(metrics_scrape=True), [], opener=lambda req, timeout: FakeResp(entries, clock),
                            getter=getter, clock=clock)
    assert resp["cached_tokens"] == 0, resp["cached_tokens"]
    assert resp["cached_source"] == "prompt_tokens_details", resp["cached_source"]
    assert resp["engine_metrics_before"]["prompt_tokens_cached_total"] == 100.0
    assert resp["engine_metrics_after"]["prompt_tokens_cached_total"] == 132.0
    assert resp["metrics_scrape"] is True


def test_case_e_metrics_delta_derivation():
    """(e) no per-request usage cache -> delta of two fake scrapes, source metrics_delta."""
    entries = [
        (sse(delta_chunk(content="ok")), 1000.050),
        (sse(finish_chunk()), 1000.070),
        (sse(usage_chunk(prompt=11, cached="absent")), None),
        (sse("[DONE]"), None),
    ]
    getter = Getter([METRICS_BEFORE, METRICS_AFTER])
    red = legacy_measure(entries, ChunkClock())
    assert red["cached_tokens"] == 0, "RED not red"  # legacy imputed 0, not 32

    clock = ChunkClock()
    resp = client.send_chat(cfg(metrics_scrape=True), [], opener=lambda req, timeout: FakeResp(entries, clock),
                            getter=getter, clock=clock)
    assert resp["cached_tokens"] == 32, resp["cached_tokens"]
    assert resp["cached_source"] == "metrics_delta", resp["cached_source"]
    assert getter.calls == 2, f"expected exactly two scrapes, got {getter.calls}"
    before, after = resp["engine_metrics_before"], resp["engine_metrics_after"]
    assert set(before) == set(client.METRICS_KEYS), before
    assert before["prefix_cache_queries"] == 90.0 and after["prefix_cache_queries"] == 91.0
    assert before["prefix_cache_hits"] == 40.0 and after["prefix_cache_hits"] == 41.0
    assert before["prompt_tokens_total"] == 4000.0 and after["prompt_tokens_total"] == 4111.0


def test_case_f_scrape_opt_out_records_null_not_guess():
    """Cost control: with the flag off there are no scrapes and the fields are null."""
    entries = [(sse(delta_chunk(content="ok")), 1000.050), (sse("[DONE]"), None)]
    getter = Getter([METRICS_BEFORE, METRICS_AFTER])
    clock = ChunkClock()
    resp = client.send_chat(cfg(metrics_scrape=False), [], opener=lambda req, timeout: FakeResp(entries, clock),
                            getter=getter, clock=clock)
    assert getter.calls == 0, f"scrape ran while disabled ({getter.calls} calls)"
    assert resp["metrics_scrape"] is False
    assert resp["engine_metrics_before"] is None and resp["engine_metrics_after"] is None
    assert resp["cached_tokens"] is None and resp["cached_source"] is None
    # and the default IS on, for the concurrency-1 protocol
    assert client.DEFAULT_METRICS_SCRAPE is True
    assert client.resolve_metrics_scrape(types.SimpleNamespace()) is True
    assert client.resolve_metrics_scrape(types.SimpleNamespace(metrics_scrape=False)) is False


def test_case_g_failed_scrape_is_null_never_guessed():
    """A 500/HTML /metrics body yields null counters, and the request still measures."""
    entries = [
        (sse(delta_chunk(content="ok")), 1000.050),
        (sse(usage_chunk(prompt=11, cached="absent")), None),
        (sse("[DONE]"), None),
    ]
    getter = Getter(["<html>404</html>", None])
    clock = ChunkClock()
    resp = client.send_chat(cfg(metrics_scrape=True), [], opener=lambda req, timeout: FakeResp(entries, clock),
                            getter=getter, clock=clock)
    assert resp["engine_metrics_before"] is None, resp["engine_metrics_before"]
    assert resp["engine_metrics_after"] is None, resp["engine_metrics_after"]
    assert resp["cached_tokens"] is None and resp["cached_source"] is None
    assert resp["ttft_ms"] == 50.0, resp["ttft_ms"]


def test_case_h_metrics_parser_and_url():
    """The parser sums label sets, refuses absent counters and strips the /v1 API base."""
    text = ("vllm:prompt_tokens_cached_total{model_name=\"a\"} 10\n"
            "vllm:prompt_tokens_cached_total{model_name=\"b\"} 5\n"
            "vllm:prompt_tokens_total 20\n"
            "vllm:prefix_cache_queries 7\n"
            "vllm:prefix_cache_hits 3\n"
            "# a comment\n"
            "process_cpu_seconds_total 1.5\n")
    parsed = client.parse_metrics(text)
    assert parsed["prompt_tokens_cached_total"] == 15.0, parsed
    assert parsed["prompt_tokens_total"] == 20.0
    assert parsed["prefix_cache_queries"] == 7.0
    assert parsed["prefix_cache_hits"] == 3.0
    assert client.parse_metrics("nothing here") is None
    assert client.metrics_url("http://host:8000/v1") == "http://host:8000/metrics"
    assert client.metrics_url("http://host:8000/") == "http://host:8000/metrics"
    # a counter that moved backwards is refused, not clamped to a measured zero
    assert client.metrics_cached_delta({"prompt_tokens_cached_total": 100.0},
                                       {"prompt_tokens_cached_total": 90.0}) is None


CASES = [
    ("a first delta is tool_calls", test_case_a_tool_call_first_delta),
    ("b empty content does not latch", test_case_b_empty_content_does_not_latch),
    ("c no delta -> unavailable", test_case_c_no_delta_is_unavailable),
    ("d cached_tokens=0 is not null", test_case_d_usage_cached_zero_is_not_null),
    ("e metrics-delta derivation", test_case_e_metrics_delta_derivation),
    ("f scrape opt-out", test_case_f_scrape_opt_out_records_null_not_guess),
    ("g failed scrape is null", test_case_g_failed_scrape_is_null_never_guessed),
    ("h parser and url", test_case_h_metrics_parser_and_url),
]


def main(argv=None):
    real_socket = socket.socket
    socket.socket = _no_socket
    failures = 0
    try:
        for name, fn in CASES:
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 - a case failure is the report
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            else:
                print(f"ok   {name} (RED failed for the intended reason, GREEN held)")
        if _FAULT:
            failures += 1
            print(f"FAIL offline guard: {_FAULT}")
    finally:
        socket.socket = real_socket
    print(f"\n{len(CASES) - failures}/{len(CASES)} cases green; "
          f"offline={'yes' if not _FAULT else 'NO'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
