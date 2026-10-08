"""Shared test rig for the resextract offline suite.

Every test that talks to Occamy goes through ``httpx.MockTransport`` — the
suite is fully offline.  The single ``@pytest.mark.live`` smoke test is skipped
unless ``--live`` or ``RESEXTRACT_LIVE=1`` is passed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

from resextract.llm import OccamyClient

# A path that deliberately does not exist, so tests use the module's measured
# defaults instead of whatever the developer's config/resextract.toml says.
NO_CONFIG = Path(__file__).resolve().parent / "_no_such_config.toml"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="run @pytest.mark.live tests against the real Occamy endpoint",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "live: hits the real Occamy endpoint (:8012)")


# --------------------------------------------------------------------------- #
# The ``live`` convention: an explicit marker, never a name.
#
# ``live`` used to be decided by ``if "live" in item.keywords``.  That is not a
# check of the test's name — pytest injects a *bare* keyword key for every
# parametrisation id (and for module/class names and mark names), so
# ``@pytest.mark.parametrize("mode", ["live"])``, or a class/module named
# ``live``, silently skipped tests that never touch the network.  A silent skip
# reports success, so it was a false-green generator.  Only an explicit
# ``@pytest.mark.live`` marker skips anything now.
# --------------------------------------------------------------------------- #

LIVE_SKIP_REASON = "live test — run with --live or RESEXTRACT_LIVE=1"


def _live_enabled(config: pytest.Config) -> bool:
    """``--live`` (CLI) and ``RESEXTRACT_LIVE=1`` (env) both mean "run live tests"."""
    return bool(config.getoption("--live")) or os.environ.get("RESEXTRACT_LIVE") == "1"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _live_enabled(config):
        return
    skip = pytest.mark.skip(reason=LIVE_SKIP_REASON)
    for item in items:
        # Explicit marker only — item.get_closest_marker also honours
        # ``pytestmark``/class/module-level marking, but not names or ids.
        if item.get_closest_marker("live") is not None:
            item.add_marker(skip)


def pytest_terminal_summary(
    terminalreporter: Any, exitstatus: int, config: pytest.Config
) -> None:
    """Make skipped live tests loud, so "N skipped" is never read as "N passed"."""
    if _live_enabled(config):
        return
    skipped = 0
    for report in terminalreporter.stats.get("skipped", []):
        longrepr = getattr(report, "longrepr", None)
        reason = longrepr[2] if isinstance(longrepr, tuple) and len(longrepr) >= 3 else ""
        # The report repr is prefixed ("Skipped: <reason>"); match on the reason.
        if LIVE_SKIP_REASON in str(reason):
            skipped += 1
    if skipped:
        terminalreporter.write_sep(
            "=",
            f"{skipped} live test(s) SKIPPED — NOT run and NOT passed; "
            "rerun with --live or RESEXTRACT_LIVE=1",
            red=True,
        )


class FakeSleep:
    """Records backoff delays instead of waiting."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)


@dataclass
class Recorder:
    requests: list[httpx.Request] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.requests)

    def body(self, index: int) -> dict[str, Any]:
        return json.loads(self.requests[index].content.decode("utf-8"))

    def last_body(self) -> dict[str, Any]:
        return self.body(-1)


@dataclass
class Harness:
    client: OccamyClient
    recorder: Recorder
    sleep: FakeSleep


@pytest.fixture
def fake_sleep() -> FakeSleep:
    return FakeSleep()


@pytest.fixture
def make_client(fake_sleep: FakeSleep) -> Callable[..., Harness]:
    """Factory: ``make_client(handler, **client_kwargs) -> Harness``.

    ``handler(request, call_index) -> httpx.Response``.  The client owns the
    httpx instance (it is built from a transport), so ``async with h.client``
    closes it.
    """

    def _make(
        handler: Callable[[httpx.Request, int], httpx.Response],
        **kwargs: Any,
    ) -> Harness:
        recorder = Recorder()

        def wrapped(request: httpx.Request) -> httpx.Response:
            index = len(recorder.requests)
            recorder.requests.append(request)
            return handler(request, index)

        kwargs.setdefault("sleep", fake_sleep)
        kwargs.setdefault("config_path", NO_CONFIG)
        kwargs.setdefault("api_key", "local")
        client = OccamyClient(transport=httpx.MockTransport(wrapped), **kwargs)
        return Harness(client=client, recorder=recorder, sleep=fake_sleep)

    return _make


# --------------------------------------------------------------------------- #
# Response builders
# --------------------------------------------------------------------------- #


def chat_response(
    *,
    content: str | None = "ok",
    reasoning: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    finish_reason: str = "stop",
    usage: dict[str, Any] | None = None,
    request_id: str = "req-1",
    model: str = "occamy-1.0",
) -> httpx.Response:
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if reasoning is not None:
        message["reasoning_content"] = reasoning
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    payload = {
        "id": request_id,
        "object": "chat.completion",
        "model": model,
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
        "usage": usage
        or {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
            "completion_tokens_details": {"reasoning_tokens": 0},
        },
    }
    return httpx.Response(200, json=payload)


def tool_call(
    name: str | None,
    arguments: str,
    *,
    call_id: str | None = "call_1",
    index: int | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": arguments},
    }
    if index is not None:
        entry["index"] = index
    return entry


def sse_response(chunks: list[dict[str, Any] | str], *, status: int = 200) -> httpx.Response:
    lines: list[str] = []
    for chunk in chunks:
        if isinstance(chunk, str):
            lines.append(f"data: {chunk}")
        else:
            lines.append("data: " + json.dumps(chunk))
        lines.append("")
    lines.append("data: [DONE]")
    body = ("\n".join(lines) + "\n").encode("utf-8")
    return httpx.Response(
        status, content=body, headers={"content-type": "text/event-stream"}
    )
