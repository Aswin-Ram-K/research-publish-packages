"""Contract-compliant call adapter for the typed-context pilot.

This module exists because the shared meter is not contract-compliant:
``resextract.context.meter.normalise_cache`` maps an absent
``prompt_tokens_details`` to ``cached_tokens = 0``, which the interface contract
forbids ("cached_tokens … Absent means not reported (unknown) — never 0").
Fixing that function would change production behaviour, so the experiment
adapter is contract-compliant instead and the production path is left alone
until an independently verified winner justifies touching it.

Emitted row shape is ``consonance.call/1`` (see
``handoff from consonance/INTERFACE_CONTRACT.md`` §2):

* ``prompt_tokens``             — required, from the server's ``usage`` block;
* ``cached_tokens``             — ``int`` or ``None`` (never a fabricated 0);
* ``uncached_prefill_tokens``   — always ``None``: this engine does not expose
  measured prefill work, so it is unknown, not derived;
* ``derived``                   — named formula keys only, ``None`` when an
  input is unknown.

No retries are performed here. A retry is a request and the caller must count
it; hiding retries inside the adapter would make the request budget a lie.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import httpx

DEFAULT_BASE = "http://192.168.2.168:8012/v1"
DEFAULT_MODEL = "occamy-1.0"


class InstrumentError(RuntimeError):
    """The server answered without the usage block the contract requires."""


@dataclass
class Adapter:
    base_url: str = DEFAULT_BASE
    model: str = DEFAULT_MODEL
    api_key: str = "EMPTY"
    timeout: float = 300.0
    transport: httpx.BaseTransport | None = field(default=None, repr=False)
    calls_made: int = 0

    # ------------------------------------------------------------------ #
    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            transport=self.transport,
        )

    def body(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        max_tokens: int,
        temperature: float = 0.0,
        seed: int | None = None,
        session_id: str | None = None,
        thinking: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [dict(m) for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if seed is not None:
            payload["seed"] = seed
        if session_id is not None:
            payload["session_id"] = session_id
        if not thinking:
            # occamy is a reasoning model; keep the trajectory comparable by
            # asking for no thinking block where the template supports it.
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        return payload

    # ------------------------------------------------------------------ #
    def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        max_tokens: int,
        temperature: float = 0.0,
        seed: int | None = None,
        session_id: str | None = None,
        thinking: bool = False,
        run_id: str = "",
        arm: str = "",
        task_id: str = "",
        step: int = 0,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """One model request. Returns a ``consonance.call/1`` dict."""

        payload = self.body(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
            session_id=session_id,
            thinking=thinking,
        )
        raw_body = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
        import hashlib

        prompt_sha = hashlib.sha256(raw_body).hexdigest()
        t0 = time.perf_counter()
        first_token_at: float | None = None
        text_parts: list[str] = []
        usage: dict[str, Any] | None = None
        finish_reason: str | None = None
        status: int | None = None
        error: str | None = None
        content_type = ""

        try:
            with self._client(self.timeout) as client:
                with client.stream(
                    "POST", "/chat/completions", json=payload
                ) as resp:
                    status = resp.status_code
                    content_type = resp.headers.get("content-type", "")
                    if status != 200:
                        error = resp.read().decode("utf-8", "replace")[:2000]
                    else:
                        for line in resp.iter_lines():
                            if not line:
                                continue
                            if line.startswith("data: "):
                                line = line[6:]
                            if line.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            if chunk.get("usage"):
                                usage = chunk["usage"]
                            for choice in chunk.get("choices") or []:
                                delta = choice.get("delta") or {}
                                piece = delta.get("content")
                                if piece:
                                    if first_token_at is None:
                                        first_token_at = time.perf_counter()
                                    text_parts.append(piece)
                                if choice.get("finish_reason"):
                                    finish_reason = choice["finish_reason"]
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            error = f"{type(exc).__name__}: {exc}"
        total_ms = (time.perf_counter() - t0) * 1000.0
        self.calls_made += 1

        row: dict[str, Any] = {
            "schema": "consonance.call/1",
            "call_id": f"{run_id}:{arm}:{task_id}:{step}:{self.calls_made}",
            "run_id": run_id,
            "arm": arm,
            "task_id": task_id,
            "step": step,
            "model": self.model,
            "engine": "sglang",
            "prompt_sha256": prompt_sha,
            "prompt_bytes": len(raw_body),
            "prompt_tokens": None,
            "cached_tokens": None,
            "uncached_prefill_tokens": None,
            "ttft_ms": (
                round((first_token_at - t0) * 1000.0, 3)
                if first_token_at is not None
                else None
            ),
            "total_ms": round(total_ms, 3),
            "completion_tokens": None,
            "finish_reason": finish_reason,
            "status": status,
            "content_type": content_type,
            "text": "".join(text_parts),
            "derived": {},
        }

        if error is not None:
            row["error"] = error
            return row

        if not isinstance(usage, Mapping):
            raise InstrumentError(
                f"no usage block in streamed response (status={status}); "
                "prompt_tokens is required by consonance.call/1"
            )

        prompt_tokens = usage.get("prompt_tokens")
        row["prompt_tokens"] = int(prompt_tokens) if prompt_tokens is not None else None
        row["completion_tokens"] = usage.get("completion_tokens")

        # --- the one rule that matters -------------------------------- #
        # Absent cache details stay unknown. `prompt_tokens_details: null`
        # and a details dict without `cached_tokens` are both "not reported".
        details = usage.get("prompt_tokens_details")
        cached: int | None = None
        reported = False
        if isinstance(details, Mapping) and "cached_tokens" in details:
            value = details["cached_tokens"]
            cached = int(value) if value is not None else None
            reported = value is not None
        elif "cached_tokens" in usage and usage.get("cached_tokens") is not None:
            cached = int(usage["cached_tokens"])
            reported = True
        row["cached_tokens"] = cached
        row["cache_usage_reported"] = reported
        row["usage_raw"] = dict(usage)

        if cached is not None and row["prompt_tokens"] is not None:
            row["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"] = max(
                0, row["prompt_tokens"] - cached
            )
            row["derived"]["reuse_fraction_from_prompt_minus_cached"] = round(
                cached / row["prompt_tokens"], 6
            ) if row["prompt_tokens"] else None
        else:
            row["derived"]["uncached_prefill_tokens_from_prompt_minus_cached"] = None
            row["derived"]["reuse_fraction_from_prompt_minus_cached"] = None

        if extra:
            row.update(extra)
        return row


def messages_of(system: str, turns: Sequence[str]) -> list[dict[str, str]]:
    """Deterministic message assembly: one system message, then alternating
    user turns with fixed assistant placeholders. No hidden whitespace."""

    out: list[dict[str, str]] = [{"role": "system", "content": system}]
    for i, user in enumerate(turns, start=1):
        out.append({"role": "user", "content": user})
        out.append({"role": "assistant", "content": f"[turn {i} acknowledged]"})
    return out
