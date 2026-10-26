"""Thin streaming client for the SGLang OpenAI-compatible endpoint.

MUST NOT be exercised by unit U1 (offline unit tests only); a later unit does
the live gate.  The important measurement fact this wrapper relies on: with
``stream: true`` and ``stream_options: {"include_usage": true}`` SGLang emits a
final chunk carrying ``usage`` -- including ``prompt_tokens_details`` -- so
TTFT and the cached-token count come from ONE request.

``chat`` returns::

    (prompt_tokens, cached_tokens, completion_tokens, ttft_ms, wall_ms, status, text)

``prompt_tokens_details`` is ``null`` on a cold request; ``cached_tokens`` is
normalised to 0 there (see :func:`resextract.context.normalise_cache`).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

import httpx

from resextract.context.meter import normalise_cache

DEFAULT_BASE_URL = os.environ.get(
    "RESEXTRACT_OCCAMY_BASE_URL", "http://serving-host/v1"
)
DEFAULT_MODEL = os.environ.get("RESEXTRACT_OCCAMY_MODEL", "occamy-1.0")
DEFAULT_API_KEY = os.environ.get("RESEXTRACT_OCCAMY_API_KEY", "EMPTY")


@dataclass
class ChatClient:
    """One configured endpoint.  No request is made at construction time."""

    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    api_key: str = DEFAULT_API_KEY
    timeout: float = 120.0
    temperature: float = 0.0
    transport: httpx.BaseTransport | None = field(default=None, repr=False)

    def _http(self, timeout: float) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
            transport=self.transport,
        )

    def payload(
        self,
        messages: Iterable[Mapping[str, Any]],
        *,
        max_tokens: int,
        thinking: bool = False,
        stream: bool = True,
    ) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": list(messages),
            "max_tokens": int(max_tokens),
            "temperature": self.temperature,
            "chat_template_kwargs": {"enable_thinking": bool(thinking)},
            "stream": bool(stream),
            "stream_options": {"include_usage": True},
        }

    def chat(
        self,
        messages: Iterable[Mapping[str, Any]],
        *,
        max_tokens: int,
        thinking: bool = False,
        stream: bool = True,
        timeout: float = 120.0,
    ) -> tuple[int, int, int, float, float, int, str]:
        body = self.payload(messages, max_tokens=max_tokens, thinking=thinking, stream=stream)
        last_error: Exception | None = None
        for attempt in (1, 2):
            started = time.perf_counter()
            try:
                with self._http(timeout) as http:
                    if stream:
                        return self._stream_once(http, body, started)
                    return self._once(http, body, started)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code < 500:
                    raise
            if attempt == 1:
                continue
        raise RuntimeError(f"chat failed after 2 attempts: {last_error}") from last_error

    # ------------------------------------------------------------------ #
    # Wire paths
    # ------------------------------------------------------------------ #
    def _stream_once(
        self,
        http: httpx.Client,
        body: Mapping[str, Any],
        started: float,
    ) -> tuple[int, int, int, float, float, int, str]:
        chunks: list[str] = []
        usage: dict[str, Any] | None = None
        ttft_ms = 0.0
        with http.stream("POST", "/chat/completions", json=body) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event.get("usage"), Mapping):
                    usage = dict(event["usage"])
                for choice in event.get("choices") or []:
                    delta = choice.get("delta") or {}
                    piece = delta.get("content") or ""
                    if piece:
                        if ttft_ms == 0.0:
                            ttft_ms = (time.perf_counter() - started) * 1000.0
                        chunks.append(piece)
            status = response.status_code
        wall_ms = (time.perf_counter() - started) * 1000.0
        text = "".join(chunks)
        if ttft_ms == 0.0:
            ttft_ms = wall_ms
        prompt, cached = normalise_cache(usage)
        completion = int((usage or {}).get("completion_tokens") or 0)
        return (prompt, cached, completion, ttft_ms, wall_ms, status, text)

    def _once(
        self,
        http: httpx.Client,
        body: Mapping[str, Any],
        started: float,
    ) -> tuple[int, int, int, float, float, int, str]:
        response = http.post("/chat/completions", json=body)
        response.raise_for_status()
        wall_ms = (time.perf_counter() - started) * 1000.0
        data = response.json()
        usage = data.get("usage") if isinstance(data, Mapping) else None
        prompt, cached = normalise_cache(usage)
        completion = int((usage or {}).get("completion_tokens") or 0)
        choices = data.get("choices") or [{}]
        text = (choices[0].get("message") or {}).get("content") or ""
        return (prompt, cached, completion, wall_ms, wall_ms, response.status_code, text)


def chat(
    messages: Iterable[Mapping[str, Any]],
    *,
    max_tokens: int,
    thinking: bool = False,
    stream: bool = True,
    timeout: float = 120.0,
    client: ChatClient | None = None,
) -> tuple[int, int, int, float, float, int, str]:
    """Module-level convenience wrapper around :meth:`ChatClient.chat`."""

    return (client or ChatClient()).chat(
        messages,
        max_tokens=max_tokens,
        thinking=thinking,
        stream=stream,
        timeout=timeout,
    )
