"""Occamy LLM client — OpenAI-compatible, metered and budget-aware.

Thinking policy (why this module exists)
---------------------------------------
Occamy-1.0 runs behind SGLang at ``http://serving-host/v1`` with a
262144-token context.  Its per-request thinking switch is
``chat_template_kwargs.enable_thinking``:

* ``enable_thinking: false`` -> the server answers directly.  Measured:
  **~0.25 s, ~2 completion tokens, 0 reasoning tokens**.
* key omitted (thinking on) -> the server first emits a long private
  chain-of-thought into ``choices[0].message.reasoning_content``.  Measured for
  the *same trivial question*: **~10.5 s and 397 reasoning tokens**.

That is a ~40x wall-time/token lever on identical input, so the switch is a
**per-call** argument here, never a global setting: mechanical stages (graph
work, extraction, classification) call with ``thinking=False``; only mining,
assessment and drafting buy reasoning.  The default in this module is
``thinking=False`` everywhere except :meth:`OccamyClient.run_tool_loop`, which
defaults to ``True`` because an agent loop is exactly the work that needs it.

Two invariants this module enforces, because downstream dashboards show them
side by side and must never be lied to:

1. ``content`` (what the user sees) and ``reasoning_content`` (private
   chain-of-thought) are **separate fields** and are never concatenated.
2. A streaming continuation delta may carry ``"function": {"name": null}``.
   A null/empty name is never emitted as a name, and it never clobbers a name
   already announced for the same tool-call index.

Dependencies: stdlib + ``httpx`` + ``pydantic`` only.  No secrets handling: the
``api_key`` defaults to a dummy (``local``) and is never logged, echoed into a
trace, or attached to any metering record.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import re
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Literal, Mapping, Sequence

import httpx
from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Budget",
    "BudgetExhausted",
    "ChatResult",
    "ModelRequestError",
    "OccamyClient",
    "OccamyConfig",
    "SyncOccamyClient",
    "ToolCall",
    "ToolExecution",
    "ToolLoopResult",
    "ToolLoopStep",
    "UnparseableOutput",
    "Usage",
    "UsageRecord",
    "build_request_body",
    "load_config",
]

# --------------------------------------------------------------------------- #
# Defaults — verified against the live GX10 box (config/resextract.toml wins).
# --------------------------------------------------------------------------- #

DEFAULT_BASE_URL = "http://serving-host/v1"
DEFAULT_MODEL = "occamy-1.0"
DEFAULT_API_KEY = "local"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TIMEOUT_S = 180.0
MAX_ATTEMPTS = 4
DEFAULT_BACKOFF_BASE_S = 0.5
DEFAULT_BACKOFF_CAP_S = 8.0
DEFAULT_MAX_RETRY_AFTER_S = 30.0

_THINKING_KWARG = "chat_template_kwargs"


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class OccamyError(Exception):
    """Base class for every error raised by this module."""


class ModelRequestError(OccamyError):
    """A non-retryable HTTP failure (e.g. ``400``) or retries exhausted.

    Carries the status and a bounded body preview.  The API key is never part
    of ``body`` or of ``str(exc)``.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        body: str = "",
        url: str = "",
        attempts: int = 1,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.body = body
        self.url = url
        self.attempts = attempts

    def __str__(self) -> str:  # pragma: no cover - trivial
        bits = [super().__str__()]
        if self.status is not None:
            bits.append(f"status={self.status}")
        if self.attempts != 1:
            bits.append(f"attempts={self.attempts}")
        if self.body:
            bits.append(f"body={self.body[:400]!r}")
        return " | ".join(bits)


class UnparseableOutput(OccamyError):
    """``call_json`` could not obtain a schema-valid object after the retry.

    ``raw_text`` is the last model text verbatim; ``last_error`` is the
    validation/decoding error string.  A partial object is never returned.
    """

    def __init__(
        self,
        raw_text: str,
        last_error: str,
        *,
        attempts: int = 2,
        schema_name: str = "",
    ) -> None:
        super().__init__(
            f"model output did not satisfy {schema_name or 'schema'} "
            f"after {attempts} attempts: {last_error}"
        )
        self.raw_text = raw_text
        self.last_error = last_error
        self.attempts = attempts
        self.schema_name = schema_name


class BudgetExhausted(OccamyError):
    """Raised by :class:`Budget` when a call or token ceiling would be broken."""

    def __init__(
        self,
        message: str,
        *,
        reason: Literal["calls", "tokens"],
        tokens_used: int,
        max_tokens: int | None,
        calls_used: int,
        max_calls: int | None,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.tokens_used = tokens_used
        self.max_tokens = max_tokens
        self.calls_used = calls_used
        self.max_calls = max_calls


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

_REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_RELPATH = Path("config") / "resextract.toml"


@dataclass(frozen=True)
class OccamyConfig:
    """Endpoint facts for the Occamy route (``config/resextract.toml``)."""

    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    api_key: str = DEFAULT_API_KEY
    timeout_s: float = DEFAULT_TIMEOUT_S
    max_tokens: int = DEFAULT_MAX_TOKENS
    max_attempts: int = MAX_ATTEMPTS


def find_config_path(start: Path | str | None = None) -> Path | None:
    """Locate ``config/resextract.toml`` (env var, then cwd walk-up, then repo)."""
    env = os.environ.get("RESEXTRACT_CONFIG")
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p
    here = Path(start) if start is not None else Path.cwd()
    for base in [here, *here.parents]:
        candidate = base / CONFIG_RELPATH
        if candidate.is_file():
            return candidate
    fallback = _REPO_ROOT / CONFIG_RELPATH
    return fallback if fallback.is_file() else None


def load_config(path: Path | str | None = None, **overrides: Any) -> OccamyConfig:
    """Read the endpoint block; fall back to the measured defaults.

    Unreadable/absent TOML is not an error — the verified constants above are
    the defaults (that behaviour is what makes this unit offline-testable).
    """
    cfg_path = Path(path) if path is not None else find_config_path()
    values: dict[str, Any] = {}
    if cfg_path is not None and cfg_path.is_file():
        try:
            with cfg_path.open("rb") as fh:
                data = tomllib.load(fh)
            endpoints = data.get("endpoints", {}) if isinstance(data, dict) else {}
            if isinstance(endpoints, dict):
                if endpoints.get("occamy_base_url"):
                    values["base_url"] = str(endpoints["occamy_base_url"])
                if endpoints.get("occamy_model"):
                    values["model"] = str(endpoints["occamy_model"])
        except (tomllib.TOMLDecodeError, OSError):
            values = {}
    values.update({k: v for k, v in overrides.items() if v is not None})
    return OccamyConfig(**values)


# --------------------------------------------------------------------------- #
# Budget
# --------------------------------------------------------------------------- #


@dataclass
class Budget:
    """A token/call ceiling shared by every call in one run.

    ``begin_call`` is checked *before* a request leaves the process, so an
    exhausted budget never spends money.  ``charge`` adds measured usage after
    the reply and raises if the token ceiling is now blown — the CLI maps that
    to exit code 3 ("budget exhausted with work remaining").
    """

    max_tokens: int | None = None
    max_calls: int | None = None
    tokens_used: int = 0
    calls_used: int = 0

    @property
    def remaining_tokens(self) -> int | None:
        if self.max_tokens is None:
            return None
        return max(0, self.max_tokens - self.tokens_used)

    @property
    def remaining_calls(self) -> int | None:
        if self.max_calls is None:
            return None
        return max(0, self.max_calls - self.calls_used)

    def check(self) -> None:
        """Raise ``BudgetExhausted`` if the limits are already met/exceeded."""
        if self.max_calls is not None and self.calls_used >= self.max_calls:
            raise BudgetExhausted(
                f"call budget exhausted: {self.calls_used}/{self.max_calls} calls used",
                reason="calls",
                tokens_used=self.tokens_used,
                max_tokens=self.max_tokens,
                calls_used=self.calls_used,
                max_calls=self.max_calls,
            )
        if self.max_tokens is not None and self.tokens_used >= self.max_tokens:
            raise BudgetExhausted(
                f"token budget exhausted: {self.tokens_used}/{self.max_tokens} tokens used",
                reason="tokens",
                tokens_used=self.tokens_used,
                max_tokens=self.max_tokens,
                calls_used=self.calls_used,
                max_calls=self.max_calls,
            )

    def begin_call(self) -> None:
        """Reserve the next call (raises before any HTTP request is made)."""
        self.check()
        self.calls_used += 1

    def charge(self, tokens: int) -> None:
        """Add measured token usage; raises if the ceiling is now exceeded."""
        self.tokens_used += max(0, int(tokens))
        if self.max_tokens is not None and self.tokens_used > self.max_tokens:
            raise BudgetExhausted(
                f"token budget exceeded: {self.tokens_used}/{self.max_tokens} tokens used",
                reason="tokens",
                tokens_used=self.tokens_used,
                max_tokens=self.max_tokens,
                calls_used=self.calls_used,
                max_calls=self.max_calls,
            )


# --------------------------------------------------------------------------- #
# Typed results
# --------------------------------------------------------------------------- #


class Usage(BaseModel):
    """Token accounting for one call.  ``reasoning_tokens`` is always split out."""

    model_config = ConfigDict(extra="forbid")

    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: "Usage") -> "Usage":
        if not isinstance(other, Usage):  # pragma: no cover - defensive
            return NotImplemented
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class ToolCall(BaseModel):
    """One tool call: name, decoded argument dict, and the raw JSON string."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)
    raw_arguments: str = ""
    args_error: str | None = None


class ChatResult(BaseModel):
    """One model turn.  ``content`` and ``reasoning_content`` never merge."""

    model_config = ConfigDict(extra="forbid")

    content: str = ""
    reasoning_content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    finish_reason: str | None = None
    usage: Usage = Field(default_factory=Usage)
    wall_ms: float = 0.0
    model: str = ""
    request_id: str | None = None
    thinking: bool = False
    streamed: bool = False
    attempts: int = 1
    raw_usage: dict[str, Any] = Field(default_factory=dict)


class UsageRecord(BaseModel):
    """One metering row handed to the caller's usage sink.  Never holds a key."""

    model_config = ConfigDict(extra="forbid")

    label: str = "chat"
    model: str = ""
    thinking: bool = False
    streamed: bool = False
    ok: bool = True
    status: int | None = None
    attempts: int = 1
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    wall_ms: float = 0.0
    request_id: str | None = None
    error: str | None = None


class ToolCallRecord(BaseModel):
    """Serialisable view of one requested tool call inside a loop step."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)
    raw_arguments: str = ""
    args_error: str | None = None


class ToolExecution(BaseModel):
    """Serialisable outcome of running one handler."""

    model_config = ConfigDict(extra="forbid")

    name: str = ""
    tool_call_id: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    ok: bool = False
    result: Any = None
    result_digest: str = ""
    result_truncated: bool = False
    error: str | None = None
    duration_ms: float = 0.0


class ToolLoopStep(BaseModel):
    """One iteration of :meth:`OccamyClient.run_tool_loop`.

    This is the record the dashboard's reasoning view renders, so every field
    is JSON-serialisable (``model_dump(mode="json")`` round-trips).
    """

    model_config = ConfigDict(extra="forbid")

    step: int = 0
    thinking: bool = False
    finish_reason: str | None = None
    content: str = ""
    reasoning_content: str = ""
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    executions: list[ToolExecution] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    wall_ms: float = 0.0
    request_id: str | None = None
    error: str | None = None


class ToolLoopResult(BaseModel):
    """Full trace of a bounded tool loop."""

    model_config = ConfigDict(extra="forbid")

    content: str = ""
    stopped_reason: Literal["final_answer", "max_steps"] = "final_answer"
    steps: list[ToolLoopStep] = Field(default_factory=list)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    total_wall_ms: float = 0.0
    tool_calls: int = 0


# --------------------------------------------------------------------------- #
# Request construction (pure — the thinking guard lives here)
# --------------------------------------------------------------------------- #


def build_request_body(
    *,
    model: str,
    messages: Sequence[Mapping[str, Any]],
    thinking: bool,
    max_tokens: int,
    temperature: float = 0.0,
    tools: Sequence[Mapping[str, Any]] | None = None,
    tool_choice: Any = None,
    stream: bool = False,
    schema: type[BaseModel] | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the OpenAI-compatible request body.

    **The thinking guard**: ``thinking=False`` *must* send
    ``chat_template_kwargs.enable_thinking = false``; ``thinking=True`` *must
    not* send the key at all (SGLang's template default is on, and an explicit
    ``true`` is not universally accepted by other OpenAI-compatible servers).
    """
    body: dict[str, Any] = {
        "model": model,
        "messages": [dict(m) for m in messages],
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
    }
    if not thinking:
        body[_THINKING_KWARG] = {"enable_thinking": False}
    if tools:
        body["tools"] = [dict(t) for t in tools]
        body["tool_choice"] = tool_choice if tool_choice is not None else "auto"
    if stream:
        body["stream"] = True
        body["stream_options"] = {"include_usage": True}
    if schema is not None:
        body["response_format"] = {"type": "json_object"}
    return body


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #


def _elapsed_ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000.0, 3)


def _as_text(value: Any) -> str:
    """Normalise an OpenAI content field (str, None, or list of parts) to str."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Mapping):
        return _as_text(value.get("text")) or _as_text(value.get("content"))
    if isinstance(value, Iterable):
        parts = []
        for item in value:
            if isinstance(item, Mapping):
                parts.append(_as_text(item.get("text") or item.get("content")))
            else:
                parts.append(_as_text(item))
        return "".join(parts)
    return str(value)


def parse_usage(raw: Any) -> Usage:
    """Read token usage from the several shapes SGLang/OpenAI emit."""
    if not isinstance(raw, Mapping):
        return Usage()
    prompt = int(raw.get("prompt_tokens") or 0)
    completion = int(raw.get("completion_tokens") or 0)
    total_raw = raw.get("total_tokens")
    total = int(total_raw) if isinstance(total_raw, (int, float)) else prompt + completion
    reasoning = 0
    details = raw.get("completion_tokens_details")
    if isinstance(details, Mapping):
        value = details.get("reasoning_tokens")
        if isinstance(value, (int, float)):
            reasoning = int(value)
    if not reasoning:
        value = raw.get("reasoning_tokens")
        if isinstance(value, (int, float)):
            reasoning = int(value)
    if not reasoning:
        value = raw.get("reasoning_content_tokens")
        if isinstance(value, (int, float)):
            reasoning = int(value)
    return Usage(
        prompt_tokens=prompt,
        completion_tokens=completion,
        reasoning_tokens=reasoning,
        total_tokens=total,
    )


@dataclass
class _ToolCallAcc:
    """Accumulator for one tool-call index across streamed deltas."""

    id: str | None = None
    name: str = ""
    arg_parts: list[str] = field(default_factory=list)
    arg_obj: dict[str, Any] | None = None

    def merge(self, delta: Mapping[str, Any]) -> None:
        if not isinstance(delta, Mapping):
            return
        # A null id must never clobber an announced one either.
        new_id = delta.get("id")
        if isinstance(new_id, str) and new_id.strip():
            self.id = new_id
        fn = delta.get("function")
        if not isinstance(fn, Mapping):
            return
        # THE QUIRK: continuation deltas may carry "name": null.  Only a
        # non-empty string may set/overwrite the announced name.
        name = fn.get("name")
        if isinstance(name, str) and name.strip():
            self.name = name.strip()
        args = fn.get("arguments")
        if isinstance(args, str):
            if args:
                self.arg_parts.append(args)
        elif isinstance(args, Mapping):
            if self.arg_obj is None:
                self.arg_obj = {}
            self.arg_obj.update(args)

    def build(self) -> ToolCall:
        raw = "".join(self.arg_parts)
        if not raw and self.arg_obj is not None:
            raw = json.dumps(self.arg_obj)
        args: dict[str, Any] = {}
        args_error: str | None = None
        if raw:
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, ValueError) as exc:
                args_error = f"{type(exc).__name__}: {exc}"
            else:
                if isinstance(parsed, Mapping):
                    args = dict(parsed)
                elif parsed is None:
                    args = {}
                else:
                    args = {"value": parsed}
        elif self.arg_obj is not None:
            args = dict(self.arg_obj)
        return ToolCall(
            id=self.id,
            name=self.name,  # never None — empty string if truly unnamed
            arguments=args,
            raw_arguments=raw,
            args_error=args_error,
        )


def _merge_stream_tool_calls(
    accs: dict[int, _ToolCallAcc], deltas: Any
) -> None:
    if not isinstance(deltas, Iterable) or isinstance(deltas, (str, bytes, Mapping)):
        return
    for position, delta in enumerate(deltas):
        if not isinstance(delta, Mapping):
            continue
        index = delta.get("index")
        key = index if isinstance(index, int) else position
        acc = accs.get(key)
        if acc is None:
            acc = _ToolCallAcc()
            accs[key] = acc
        acc.merge(delta)


def _tool_calls_from_message(raw: Any) -> list[ToolCall]:
    """Decode a non-streamed ``message.tool_calls`` array (index-aware)."""
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes, Mapping)):
        return []
    return [acc.build() for _, acc in sorted(_iter_tool_accs(raw).items())]


def _iter_tool_accs(raw: Iterable[Any]) -> dict[int, _ToolCallAcc]:
    accs: dict[int, _ToolCallAcc] = {}
    for position, item in enumerate(raw):
        if not isinstance(item, Mapping):
            continue
        index = item.get("index")
        key = index if isinstance(index, int) else position
        acc = accs.get(key)
        if acc is None:
            acc = _ToolCallAcc()
            accs[key] = acc
        acc.merge(item)
    return accs


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json_object(text: str) -> Any:
    """Pull the first JSON object/array out of model prose or a code fence."""
    if not text or not text.strip():
        raise json.JSONDecodeError("empty model output", text or "", 0)
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    fenced = _JSON_FENCE_RE.search(stripped)
    candidate = fenced.group(1).strip() if fenced else None
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        return json.loads(stripped[start : end + 1])
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start != -1 and end > start:
        return json.loads(stripped[start : end + 1])
    raise json.JSONDecodeError("no JSON object found in model output", stripped, 0)


def _jsonable(value: Any, _depth: int = 0) -> Any:
    """Recursive JSON-safe copy (tool results reach the dashboard as JSON)."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if _depth > 12:
        return repr(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item, _depth + 1) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted((_jsonable(item, _depth + 1) for item in value), key=repr)
    if isinstance(value, (list, tuple)):
        return [_jsonable(item, _depth + 1) for item in value]
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", "replace")
    return str(value)


def _digest(value: Any) -> str:
    try:
        blob = json.dumps(_jsonable(value), sort_keys=True, default=str)
    except (TypeError, ValueError):  # pragma: no cover - _jsonable covers this
        blob = str(value)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit] + f"...[truncated {len(text) - limit} chars]", True


def _parse_retry_after(value: str | None, cap: float) -> float | None:
    if not value:
        return None
    value = value.strip()
    try:
        seconds = float(value)
    except ValueError:
        # HTTP-date form: fall back to a small fixed pause rather than guessing.
        return min(cap, 1.0)
    if seconds < 0:
        return 0.0
    return min(cap, seconds)


class _RetryableStatus(Exception):
    def __init__(self, status: int, body: str, retry_after: float | None = None) -> None:
        super().__init__(f"retryable status {status}")
        self.status = status
        self.body = body
        self.retry_after = retry_after


# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #

UsageSink = Callable[[UsageRecord], Any]


def _noop_sink(record: UsageRecord) -> None:  # pragma: no cover - trivial
    return None


class OccamyClient:
    """Async OpenAI-compatible client for Occamy-1.0.

    Parameters not given fall back to ``config/resextract.toml`` (endpoint and
    model) or to the measured defaults in this module.
    """

    #: This class genuinely issues outbound HTTP requests to the model endpoint,
    #: so it may declare itself a ``model`` producer.  A replay/stub subclass
    #: that answers locally MUST set this to ``False``; :attr:`producer` reads
    #: this flag, so the declaration and the request-making cannot disagree.
    makes_requests: bool = True

    @property
    def producer(self) -> str:
        """Which producer value this client *declares* (see ``PRODUCER_VOCAB``).

        ``model`` **only** for an instance that genuinely makes requests.  A
        request-free subclass therefore inherits the *cap*, not the declaration:
        its producer resolves to a non-model value.  The ``is_replay``/``is_stub``
        shorthands win over the capability flag, so a replay client that
        subclasses or wraps this class can never be read as model-produced.  An
        undeclared client never returns ``model`` and there is no fallback.
        """
        if getattr(self, "is_replay", False) or getattr(self, "is_stub", False):
            return "replay"
        return "model" if self.makes_requests else "replay"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout_s: float | None = None,
        max_tokens: int | None = None,
        max_attempts: int | None = None,
        budget: Budget | None = None,
        usage_sink: UsageSink | None = None,
        client: httpx.AsyncClient | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
        rng: random.Random | None = None,
        backoff_base_s: float = DEFAULT_BACKOFF_BASE_S,
        backoff_cap_s: float = DEFAULT_BACKOFF_CAP_S,
        max_retry_after_s: float = DEFAULT_MAX_RETRY_AFTER_S,
        config_path: str | Path | None = None,
        label: str = "occamy",
    ) -> None:
        cfg = load_config(config_path)
        self.base_url = (base_url or cfg.base_url).rstrip("/")
        self.model = model or cfg.model
        self.api_key = api_key if api_key is not None else cfg.api_key
        self.timeout_s = float(timeout_s if timeout_s is not None else cfg.timeout_s)
        self.default_max_tokens = int(max_tokens if max_tokens is not None else cfg.max_tokens)
        self.max_attempts = int(
            max_attempts if max_attempts is not None else cfg.max_attempts
        )
        self.budget = budget
        self.usage_sink: UsageSink = usage_sink or _noop_sink
        self.label = label
        self._sleep = sleep or asyncio.sleep
        self._rng = rng or random.Random()
        self._backoff_base_s = backoff_base_s
        self._backoff_cap_s = backoff_cap_s
        self._max_retry_after_s = max_retry_after_s
        self._owns_client = client is None
        self._http = client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_s), transport=transport
        )

    # -- lifecycle --------------------------------------------------------- #

    async def __aenter__(self) -> "OccamyClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    def sync(self) -> "SyncOccamyClient":
        """Return a blocking wrapper sharing this client's config and budget."""
        return SyncOccamyClient(self)

    # -- request plumbing --------------------------------------------------- #

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self, *, stream: bool = False) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
            "User-Agent": "resextract/0.1 occamy-client",
        }

    def _backoff_delay(self, attempt: int) -> float:
        """Exponential backoff with jitter (attempt is 1-based)."""
        raw = self._backoff_base_s * (2 ** max(0, attempt - 1))
        capped = min(self._backoff_cap_s, raw)
        return round(capped * (0.5 + 0.5 * self._rng.random()), 6)

    async def _emit(self, record: UsageRecord) -> None:
        result = self.usage_sink(record)
        if asyncio.iscoroutine(result):
            await result

    # -- chat --------------------------------------------------------------- #

    async def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        *,
        thinking: bool,
        max_tokens: int | None = None,
        temperature: float = 0.0,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: Any = None,
        stream: bool = False,
        schema: type[BaseModel] | Mapping[str, Any] | None = None,
        label: str | None = None,
        sink: UsageSink | None = None,
    ) -> ChatResult:
        """One metered, budgeted chat completion.

        ``thinking=False`` sends ``chat_template_kwargs.enable_thinking=false``;
        ``thinking=True`` omits the key entirely.  Retries: 5xx / timeout /
        connection errors and ``429`` (honouring ``Retry-After``) up to
        ``max_attempts``; ``400`` and other 4xx raise :class:`ModelRequestError`
        immediately.
        """
        max_tokens = int(max_tokens if max_tokens is not None else self.default_max_tokens)
        body = build_request_body(
            model=self.model,
            messages=messages,
            thinking=thinking,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
            tool_choice=tool_choice,
            stream=stream,
            schema=schema,
        )
        if self.budget is not None:
            self.budget.begin_call()

        t0 = time.perf_counter()
        attempt = 0
        last_error: Exception | None = None
        while attempt < self.max_attempts:
            attempt += 1
            try:
                if stream:
                    result = await self._stream_chat(body, thinking=thinking, attempt=attempt)
                else:
                    result = await self._post_chat(body, thinking=thinking, attempt=attempt)
            except _RetryableStatus as exc:
                last_error = exc
                if attempt >= self.max_attempts:
                    break
                delay = (
                    exc.retry_after
                    if exc.retry_after is not None
                    else self._backoff_delay(attempt)
                )
                await self._sleep(delay)
                continue
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                if attempt >= self.max_attempts:
                    break
                await self._sleep(self._backoff_delay(attempt))
                continue
            except ModelRequestError as exc:
                # A 4xx is a completed call: meter it (zero tokens) then re-raise.
                await self._emit(
                    UsageRecord(
                        label=label or self.label,
                        model=self.model,
                        thinking=thinking,
                        streamed=stream,
                        ok=False,
                        status=exc.status,
                        attempts=attempt,
                        wall_ms=_elapsed_ms(t0),
                        error=str(exc)[:500],
                    )
                )
                raise
            else:
                wall_ms = _elapsed_ms(t0)
                result = result.model_copy(update={"wall_ms": wall_ms, "attempts": attempt})
                await self._emit(self._record(result, label=label, ok=True))
                if self.budget is not None:
                    self.budget.charge(result.usage.total_tokens)
                return result

        wall_ms = _elapsed_ms(t0)
        status = getattr(last_error, "status", None)
        text = str(last_error)
        await self._emit(
            UsageRecord(
                label=label or self.label,
                model=self.model,
                thinking=thinking,
                streamed=stream,
                ok=False,
                status=status,
                attempts=attempt,
                wall_ms=wall_ms,
                error=text[:500],
            )
        )
        if isinstance(last_error, _RetryableStatus):
            raise ModelRequestError(
                f"model request failed after {attempt} attempts (status {last_error.status})",
                status=last_error.status,
                body=last_error.body,
                url=self.chat_url,
                attempts=attempt,
            )
        raise ModelRequestError(
            f"model request failed after {attempt} attempts: {text}",
            status=status,
            url=self.chat_url,
            attempts=attempt,
        )

    def _record(self, result: ChatResult, *, label: str | None, ok: bool) -> UsageRecord:
        return UsageRecord(
            label=label or self.label,
            model=result.model or self.model,
            thinking=result.thinking,
            streamed=result.streamed,
            ok=ok,
            status=200,
            attempts=result.attempts,
            prompt_tokens=result.usage.prompt_tokens,
            completion_tokens=result.usage.completion_tokens,
            reasoning_tokens=result.usage.reasoning_tokens,
            total_tokens=result.usage.total_tokens,
            wall_ms=result.wall_ms,
            request_id=result.request_id,
        )

    async def _post_chat(
        self, body: dict[str, Any], *, thinking: bool, attempt: int
    ) -> ChatResult:
        response = await self._http.post(
            self.chat_url, json=body, headers=self._headers()
        )
        status = response.status_code
        if status >= 500:
            raise _RetryableStatus(status, response.text[:2000])
        if status == 429:
            raise _RetryableStatus(
                status,
                response.text[:2000],
                retry_after=_parse_retry_after(
                    response.headers.get("retry-after"), self._max_retry_after_s
                ),
            )
        if status >= 400:
            raise ModelRequestError(
                f"model rejected the request (status {status})",
                status=status,
                body=response.text[:2000],
                url=self.chat_url,
                attempts=attempt,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ModelRequestError(
                f"model returned non-JSON body: {exc}",
                status=status,
                body=response.text[:2000],
                url=self.chat_url,
                attempts=attempt,
            ) from None
        return self._parse_payload(
            payload,
            thinking=thinking,
            streamed=False,
            request_id=response.headers.get("x-request-id"),
        )

    async def _stream_chat(
        self, body: dict[str, Any], *, thinking: bool, attempt: int
    ) -> ChatResult:
        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        accs: dict[int, _ToolCallAcc] = {}
        finish_reason: str | None = None
        model = self.model
        request_id: str | None = None
        raw_usage: dict[str, Any] = {}
        async with self._http.stream(
            "POST", self.chat_url, json=body, headers=self._headers(stream=True)
        ) as response:
            status = response.status_code
            if status >= 500:
                await response.aread()
                raise _RetryableStatus(status, response.text[:2000])
            if status == 429:
                await response.aread()
                raise _RetryableStatus(
                    status,
                    response.text[:2000],
                    retry_after=_parse_retry_after(
                        response.headers.get("retry-after"), self._max_retry_after_s
                    ),
                )
            if status >= 400:
                await response.aread()
                raise ModelRequestError(
                    f"model rejected the request (status {status})",
                    status=status,
                    body=response.text[:2000],
                    url=self.chat_url,
                    attempts=attempt,
                )
            request_id = response.headers.get("x-request-id")
            async for line in response.aiter_lines():
                if not line:
                    continue
                if line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if not data or data == "[DONE]":
                    if data == "[DONE]":
                        break
                    continue
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if not isinstance(chunk, Mapping):
                    continue
                model = chunk.get("model") or model
                request_id = chunk.get("id") or request_id
                if isinstance(chunk.get("usage"), Mapping):
                    raw_usage = dict(chunk["usage"])
                for choice in chunk.get("choices") or []:
                    if not isinstance(choice, Mapping):
                        continue
                    finish_reason = choice.get("finish_reason") or finish_reason
                    delta = choice.get("delta") or choice.get("message") or {}
                    if not isinstance(delta, Mapping):
                        continue
                    piece = _as_text(delta.get("content"))
                    if piece:
                        content_parts.append(piece)
                    reasoning = _as_text(
                        delta.get("reasoning_content") or delta.get("reasoning")
                    )
                    if reasoning:
                        reasoning_parts.append(reasoning)
                    _merge_stream_tool_calls(accs, delta.get("tool_calls"))
        return ChatResult(
            content="".join(content_parts),
            reasoning_content="".join(reasoning_parts),
            tool_calls=[acc.build() for _, acc in sorted(accs.items())],
            finish_reason=finish_reason,
            usage=parse_usage(raw_usage),
            model=model,
            request_id=request_id,
            thinking=thinking,
            streamed=True,
            raw_usage=raw_usage,
        )

    def _parse_payload(
        self,
        payload: Any,
        *,
        thinking: bool,
        streamed: bool,
        request_id: str | None,
    ) -> ChatResult:
        if not isinstance(payload, Mapping):
            raise ModelRequestError(
                "model returned a non-object JSON body",
                body=json.dumps(_jsonable(payload))[:2000],
                url=self.chat_url,
            )
        choices = payload.get("choices") or []
        if not isinstance(choices, Sequence) or not choices:
            raise ModelRequestError(
                "model response contained no choices",
                body=json.dumps(_jsonable(payload))[:2000],
                url=self.chat_url,
            )
        choice = choices[0] if isinstance(choices[0], Mapping) else {}
        message = choice.get("message") or {}
        if not isinstance(message, Mapping):
            message = {}
        raw_usage = payload.get("usage")
        return ChatResult(
            content=_as_text(message.get("content")),
            reasoning_content=_as_text(
                message.get("reasoning_content") or message.get("reasoning")
            ),
            tool_calls=_tool_calls_from_message(message.get("tool_calls")),
            finish_reason=choice.get("finish_reason"),
            usage=parse_usage(raw_usage),
            model=str(payload.get("model") or self.model),
            request_id=request_id or payload.get("id"),
            thinking=thinking,
            streamed=streamed,
            raw_usage=dict(raw_usage) if isinstance(raw_usage, Mapping) else {},
        )

    # -- tool loop ---------------------------------------------------------- #

    async def run_tool_loop(
        self,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
        handlers: Mapping[str, Callable[[dict[str, Any]], Any]],
        *,
        max_steps: int = 12,
        thinking: bool = True,
        max_tokens: int | None = None,
        temperature: float = 0.0,
        tool_choice: Any = "auto",
        label: str = "tool_loop",
        sink: UsageSink | None = None,
    ) -> ToolLoopResult:
        """Bounded agent loop: execute handlers, append results, stop on answer.

        Every step becomes a :class:`ToolLoopStep` (reasoning kept apart from
        content; tool args, result digest and duration recorded) and the whole
        result round-trips through ``model_dump(mode="json")`` for the
        dashboard.  A missing/failing handler never aborts the loop — it is
        recorded as an error tool result and handed back to the model.
        """
        convo: list[dict[str, Any]] = [dict(m) for m in messages]
        steps: list[ToolLoopStep] = []
        total_usage = Usage()
        tool_call_count = 0
        t0 = time.perf_counter()

        for step_index in range(max(0, int(max_steps))):
            result = await self.chat(
                convo,
                thinking=thinking,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=tools,
                tool_choice=tool_choice,
                label=f"{label}.step{step_index + 1}",
                sink=sink,
            )
            total_usage = total_usage + result.usage
            records = [
                ToolCallRecord(
                    id=tc.id,
                    name=tc.name,
                    arguments=tc.arguments,
                    raw_arguments=tc.raw_arguments,
                    args_error=tc.args_error,
                )
                for tc in result.tool_calls
            ]
            if not result.tool_calls:
                steps.append(
                    ToolLoopStep(
                        step=step_index + 1,
                        thinking=thinking,
                        finish_reason=result.finish_reason,
                        content=result.content,
                        reasoning_content=result.reasoning_content,
                        tool_calls=[],
                        executions=[],
                        usage=result.usage,
                        wall_ms=result.wall_ms,
                        request_id=result.request_id,
                    )
                )
                return ToolLoopResult(
                    content=result.content,
                    stopped_reason="final_answer",
                    steps=steps,
                    messages=convo,
                    usage=total_usage,
                    total_wall_ms=_elapsed_ms(t0),
                    tool_calls=tool_call_count,
                )

            assistant_turn: dict[str, Any] = {
                "role": "assistant",
                "content": result.content or None,
                "tool_calls": [
                    _assistant_tool_call(tc, position)
                    for position, tc in enumerate(result.tool_calls)
                ],
            }
            convo.append(assistant_turn)

            executions: list[ToolExecution] = []
            for position, tc in enumerate(result.tool_calls):
                execution = await self._execute_tool(tc, handlers)
                executions.append(execution)
                tool_message: dict[str, Any] = {
                    "role": "tool",
                    "tool_call_id": tc.id or f"call_{step_index}_{position}",
                    "content": _tool_result_text(execution),
                }
                if tc.name:
                    tool_message["name"] = tc.name
                convo.append(tool_message)
                tool_call_count += 1

            steps.append(
                ToolLoopStep(
                    step=step_index + 1,
                    thinking=thinking,
                    finish_reason=result.finish_reason,
                    content=result.content,
                    reasoning_content=result.reasoning_content,
                    tool_calls=records,
                    executions=executions,
                    usage=result.usage,
                    wall_ms=result.wall_ms,
                    request_id=result.request_id,
                )
            )

        last = steps[-1] if steps else None
        return ToolLoopResult(
            content=last.content if last else "",
            stopped_reason="max_steps",
            steps=steps,
            messages=convo,
            usage=total_usage,
            total_wall_ms=_elapsed_ms(t0),
            tool_calls=tool_call_count,
        )

    async def _execute_tool(
        self,
        call: ToolCall,
        handlers: Mapping[str, Callable[[dict[str, Any]], Any]],
    ) -> ToolExecution:
        started = time.perf_counter()
        base = ToolExecution(
            name=call.name,
            tool_call_id=call.id,
            arguments=dict(call.arguments),
        )
        if not call.name:
            base.error = "tool call carried no function name"
            base.duration_ms = _elapsed_ms(started)
            return base
        handler = handlers.get(call.name)
        if handler is None:
            base.error = f"no handler registered for tool {call.name!r}"
            base.duration_ms = _elapsed_ms(started)
            return base
        try:
            outcome = handler(dict(call.arguments))
            if hasattr(outcome, "__await__"):
                outcome = await outcome
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            base.ok = False
            base.error = f"{type(exc).__name__}: {exc}"
            base.duration_ms = _elapsed_ms(started)
            return base
        safe = _jsonable(outcome)
        text = safe if isinstance(safe, str) else json.dumps(safe, default=str)
        _text_value, truncated = _truncate(text, 20000)
        base.ok = True
        base.result = safe if not truncated else _text_value
        base.result_truncated = truncated
        base.result_digest = _digest(safe)
        base.duration_ms = _elapsed_ms(started)
        return base

    # -- JSON helper -------------------------------------------------------- #

    async def call_json(
        self,
        messages: Sequence[Mapping[str, Any]],
        schema: type[BaseModel],
        *,
        thinking: bool = False,
        max_tokens: int = 512,
        temperature: float = 0.0,
        label: str = "call_json",
        sink: UsageSink | None = None,
    ) -> BaseModel:
        """Call the model and return a **validated** ``schema`` instance.

        The first attempt adds only a generic "JSON only" instruction.  On a
        decode/validation failure the retry echoes the JSON schema and the
        exact error back to the model.  A second failure raises
        :class:`UnparseableOutput` carrying the raw text — never a partial
        object.
        """
        schema_name = getattr(schema, "__name__", str(schema))
        base: list[dict[str, Any]] = [dict(m) for m in messages]
        base.append({"role": "user", "content": _JSON_INSTRUCTION})
        convo = list(base)
        last_text = ""
        last_error: str | None = None

        for attempt in (1, 2):
            result = await self.chat(
                convo,
                thinking=thinking,
                max_tokens=max_tokens,
                temperature=temperature,
                schema=schema,
                label=f"{label}.attempt{attempt}",
                sink=sink,
            )
            last_text = result.content
            try:
                payload = extract_json_object(result.content)
                if not isinstance(payload, Mapping):
                    raise ValueError(
                        f"expected a JSON object, got {type(payload).__name__}"
                    )
                return schema.model_validate(dict(payload))
            except Exception as exc:  # noqa: BLE001 - re-raised below
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt == 2:
                    break
                convo = [
                    *base,
                    {"role": "assistant", "content": result.content},
                    {
                        "role": "user",
                        "content": _retry_instruction(schema, last_error),
                    },
                ]

        raise UnparseableOutput(
            raw_text=last_text,
            last_error=last_error or "unknown validation failure",
            attempts=2,
            schema_name=schema_name,
        )


_JSON_INSTRUCTION = (
    "Respond with a single JSON object and nothing else — no prose, no code "
    "fences. It must validate against the required JSON schema."
)


def _retry_instruction(schema: type[BaseModel], error: str) -> str:
    try:
        schema_json = json.dumps(schema.model_json_schema(), indent=2, default=str)
    except Exception:  # pragma: no cover - defensive
        schema_json = "{}"
    return (
        "Your previous reply was not valid for the required schema.\n"
        f"Validation error: {error}\n"
        "Required JSON schema:\n"
        f"{schema_json}\n"
        "Reply with ONLY a JSON object that satisfies it."
    )


def _assistant_tool_call(call: ToolCall, position: int) -> dict[str, Any]:
    """Rebuild the assistant's tool_calls entry for the follow-up request."""
    entry: dict[str, Any] = {
        "id": call.id or f"call_{position}",
        "type": "function",
        "function": {
            "name": call.name,
            "arguments": call.raw_arguments or json.dumps(call.arguments),
        },
    }
    return entry


def _tool_result_text(execution: ToolExecution) -> str:
    if not execution.ok:
        payload: Any = {"error": execution.error or "tool failed"}
    else:
        payload = execution.result
    text = payload if isinstance(payload, str) else json.dumps(payload, default=str)
    bounded, _ = _truncate(text, 20000)
    return bounded


# --------------------------------------------------------------------------- #
# Sync convenience wrapper
# --------------------------------------------------------------------------- #


class SyncOccamyClient:
    """Blocking façade over :class:`OccamyClient` (CLI / scripts).

    Each method drives its own event loop via ``asyncio.run``.  Calling it from
    inside a running loop is a programming error and raises ``RuntimeError``
    naming the async method to use instead.
    """

    def __init__(self, client: OccamyClient) -> None:
        self._client = client

    @property
    def client(self) -> OccamyClient:
        return self._client

    def _run(self, coro: Awaitable[Any], method: str) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)  # type: ignore[arg-type]
        coro.close()  # type: ignore[attr-defined]
        raise RuntimeError(
            f"SyncOccamyClient.{method}() was called from a running event loop; "
            f"await OccamyClient.{method}() instead"
        )

    def chat(self, messages: Sequence[Mapping[str, Any]], **kwargs: Any) -> ChatResult:
        return self._run(self._client.chat(messages, **kwargs), "chat")

    def call_json(
        self,
        messages: Sequence[Mapping[str, Any]],
        schema: type[BaseModel],
        **kwargs: Any,
    ) -> BaseModel:
        return self._run(self._client.call_json(messages, schema, **kwargs), "call_json")

    def run_tool_loop(
        self,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
        handlers: Mapping[str, Callable[[dict[str, Any]], Any]],
        **kwargs: Any,
    ) -> ToolLoopResult:
        return self._run(
            self._client.run_tool_loop(messages, tools, handlers, **kwargs),
            "run_tool_loop",
        )

    def close(self) -> None:
        self._run(self._client.aclose(), "aclose")
