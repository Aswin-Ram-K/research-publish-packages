"""Honest client-side measurement for the long-run harness.

WHY THIS MODULE EXISTS
======================
`docs/EXTERNAL-SERVING-PRACTICE.md` §6 and `docs/STACK-RECON.md` found two defects in
this repo's measurement:

1. TTFT was latched on the first non-empty ``delta.content`` (later widened to
   ``reasoning_content``); a turn whose first delta is a **tool call** therefore recorded
   no TTFT at all, and any wall-clock substitute would record the *whole* response.
   The upstream references do the opposite: vLLM's bench latches on the first chunk that
   carries ``choices`` of any kind, SGLang gates on a non-empty choice.
2. Per-request cache attribution was available and unused: SGLang reports
   ``usage.prompt_tokens_details.cached_tokens`` (streaming needs
   ``stream_options.include_usage``) and vLLM's engine counters
   (``prefix_cache_queries``, ``prefix_cache_hits``, ``prompt_tokens_cached_total``,
   ``prompt_tokens_total``) are scrapable at ``/metrics``.

**No per-pinned-range attribution exists on either server.** This module never claims it:
every cache number it reports is either the server's own per-request usage or a delta of
two server-wide counter scrapes taken around exactly one request.

SEAM CONTRACT (v1) — the fields every row written or consumed by this wave uses
--------------------------------------------------------------------------------
``ttft_ms`` (float|null)          ms from send to the FIRST stream delta carrying a token,
                                  a token being any non-empty member of ``choices[0].delta``
                                  in {``content``, ``reasoning_content``, ``tool_calls``}.
                                  ``null`` when no such delta arrives.  NEVER a wall-clock
                                  fallback.
``ttft_source`` (string)          ``"first_delta"`` | ``"unavailable"``.
``first_token_kind``              ``"content"`` | ``"tool_call"`` | ``"reasoning"`` | null.
``cached_tokens`` (int|null)
``cached_source``                 ``"prompt_tokens_details"`` | ``"metrics_delta"`` | null.
``engine_metrics_before``/``_after``  four-key dict (numbers) or null when the scrape failed.
``answer_kind``/``answer_value``/``answer_raw``  NOT populated here (Part B); this module
                                  passes them through untouched because it never drops keys
                                  from the caller's dict.

Cost control: a ``/metrics`` scrape per request doubles the request count on the wire, so
the scrape is opt-in behind ``--metrics-scrape`` / ``cfg.metrics_scrape`` / the
``PTR_METRICS_SCRAPE`` env var, and defaults **on** for the single-request-per-cell
protocol (concurrency 1).  Whether it was on is stamped on every response as
``metrics_scrape``.

Zero network in this module's own tests; every stream is faked.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------- contract constants
TTFT_SOURCE_FIRST_DELTA = "first_delta"
TTFT_SOURCE_UNAVAILABLE = "unavailable"

#: A token is any non-empty member of ``choices[0].delta`` in this set.  This is the seam
#: contract's exact set: the legacy ``reasoning`` alias is used for *text assembly* only
#: and deliberately does NOT latch TTFT, so rows stay comparable across the three cards.
TOKEN_DELTA_KEYS = ("content", "reasoning_content", "tool_calls")
_KIND_FOR_KEY = {
    "content": "content",
    "reasoning_content": "reasoning",
    "tool_calls": "tool_call",
}

CACHED_SOURCE_USAGE = "prompt_tokens_details"
CACHED_SOURCE_METRICS = "metrics_delta"

METRICS_KEYS = (
    "prefix_cache_queries",
    "prefix_cache_hits",
    "prompt_tokens_cached_total",
    "prompt_tokens_total",
)

#: The per-request ``/metrics`` scrape flag, default ON (single-request-per-cell protocol).
METRICS_SCRAPE_FLAG = "--metrics-scrape"
METRICS_SCRAPE_ENV = "PTR_METRICS_SCRAPE"
DEFAULT_METRICS_SCRAPE = True

_TRUTHY_OF = ("0", "false", "off", "no", "")

# ---------------------------------------------------------------- stop reasons (RECORD-STOP-REASON)
#: The CLOSED vocabulary every row now carries.  WHY: `STOP-REASON-AUDIT` (10195e9e) found 7
#: cap-exhausted arm-checks recorded as content `""` with 128 completion tokens and
#: ``finish_reason``/``max_tokens``/``truncated`` absent from the row, so a cap stop and a
#: silent refusal were indistinguishable without sha-hunting and token arithmetic.  A row
#: must say WHY the response ended; nothing outside this tuple may ever be written.
STOP_REASON_STOP = "stop"
STOP_REASON_LENGTH = "length"
STOP_REASON_TOOL_CALLS = "tool_calls"
STOP_REASON_CONTENT_FILTER = "content_filter"
STOP_REASON_TURN_WALL_CAP = "turn_wall_cap"
STOP_REASON_RUNAWAY_TURN = "runaway_turn"
STOP_REASON_HTTP_ERROR = "http_error"
STOP_REASON_STREAM_ERROR = "stream_error"
STOP_REASON_EMPTY = "empty_response"
STOP_REASON_UNKNOWN = "unknown"

STOP_REASONS = (
    STOP_REASON_STOP,
    STOP_REASON_LENGTH,
    STOP_REASON_TOOL_CALLS,
    STOP_REASON_CONTENT_FILTER,
    STOP_REASON_TURN_WALL_CAP,
    STOP_REASON_RUNAWAY_TURN,
    STOP_REASON_HTTP_ERROR,
    STOP_REASON_STREAM_ERROR,
    STOP_REASON_EMPTY,
    STOP_REASON_UNKNOWN,
)

#: The server's own ``finish_reason`` names, mapped onto the closed vocabulary.  A string
#: NOT in this table is recorded as ``unknown`` -- never squeezed into a neighbouring box.
_FINISH_REASON_TO_STOP = {
    "stop": STOP_REASON_STOP,
    "length": STOP_REASON_LENGTH,
    "tool_calls": STOP_REASON_TOOL_CALLS,
    "function_call": STOP_REASON_TOOL_CALLS,
    "content_filter": STOP_REASON_CONTENT_FILTER,
}

#: ``truncated`` is TRUE only when a ceiling cut the generation short, NULL only when no
#: response ever completed, FALSE for every other end.  A wall-capped turn DID generate
#: and WAS cut short, so it stays TRUE (the harness guards read this truthiness).
_TRUNCATED_FOR_STOP = {
    STOP_REASON_LENGTH: True,
    STOP_REASON_TURN_WALL_CAP: True,
    STOP_REASON_RUNAWAY_TURN: True,
    STOP_REASON_EMPTY: None,
    STOP_REASON_HTTP_ERROR: None,
    STOP_REASON_STREAM_ERROR: None,
}


def derive_stop_reason(finish_reason, *, content_present, completion_tokens=None,
                       max_tokens=None, error_code=None, tool_calls_present=False):
    """WHY the response ended, in ONE word of the closed vocabulary.

    Precedence, most causally specific first:

    1. ``error_code`` -- a harness/transport code already in the vocabulary wins: the
       harness or the wire ended it, not the model.
    2. The server's own ``finish_reason`` when it maps (``stop``/``length``/``tool_calls``/
       ``content_filter``); an unmappable string becomes ``unknown``.
    3. NO finish chunk but at least one ``tool_calls``/``function_call`` delta: the model
       DID produce a call, so the stream is ``tool_calls`` -- never ``empty_response``.
    4. NO finish chunk at all, and ``completion_tokens >= max_tokens``: the generation ran
       into the completion ceiling and the server closed without a final chunk -- this is
       exactly the 128-token case that used to look like a refusal, so it is ``length``.
    5. NO finish chunk, no tool-call delta and no usable content: ``empty_response`` --
       nothing was produced at all.
    6. Anything else: ``unknown``.  Never guessed.
    """
    if isinstance(error_code, str) and error_code in STOP_REASONS:
        return error_code
    if isinstance(finish_reason, str) and finish_reason.strip():
        key = finish_reason.strip().lower()
        if key in _FINISH_REASON_TO_STOP:
            return _FINISH_REASON_TO_STOP[key]
        if key in STOP_REASONS:
            return key
        return STOP_REASON_UNKNOWN
    if tool_calls_present:
        # STOP-REASON-HOLES: a dispatched tool call whose stream carried no finish chunk
        # and no assistant text is a PRODUCTION, not a silent refusal.
        return STOP_REASON_TOOL_CALLS
    if completion_tokens is not None and max_tokens is not None:
        try:
            if int(completion_tokens) >= int(max_tokens):
                return STOP_REASON_LENGTH
        except (TypeError, ValueError):
            pass
    if not content_present:
        return STOP_REASON_EMPTY
    return STOP_REASON_UNKNOWN


def truncated_for(stop_reason):
    """The row's ``truncated`` value for one ``stop_reason`` (see ``_TRUNCATED_FOR_STOP``)."""
    return _TRUNCATED_FOR_STOP.get(stop_reason, False)


class RequestFailure(RuntimeError):
    """A request that produced no measurement.  Never retried, never imputed.

    Carries the closed-vocabulary ``stop_reason`` of the failure: an HTTP status is
    ``http_error``, anything else that broke the stream is ``stream_error``.
    """

    def __init__(self, status, message, stop_reason=None):
        super().__init__(message)
        self.status = status
        self.stop_reason = (stop_reason
                            or (STOP_REASON_HTTP_ERROR if status is not None
                                else STOP_REASON_STREAM_ERROR))


# ---------------------------------------------------------------- request body
def thinking_setting(cfg) -> str:
    """The --thinking setting, tolerant of plain namespaces built without the flag."""
    return str(getattr(cfg, "thinking", "auto") or "auto")


def thinking_kwargs(thinking: str):
    """chat_template_kwargs for one thinking setting ('auto' -> omitted entirely)."""
    if thinking == "auto":
        return None
    if thinking == "on":
        return {"enable_thinking": True}
    return {"enable_thinking": False}


# HARNESS-GUARDS: the ceiling a cell may not cross. A live cell on 2026-10-26T145758Z
# produced a 16,384-token, 7m56s turn because nothing in the harness objected. The
# request now ALWAYS carries a finite completion ceiling; there is no code path that
# sends a request without one.
DEFAULT_MAX_TOKENS = 4096
DEFAULT_THINKING = "off"


def coerce_max_tokens(value) -> int:
    """A finite, positive completion ceiling or a refusal — never ``None``, never 0."""
    if isinstance(value, bool):
        raise ValueError("max_tokens must be a positive integer, not a bool")
    try:
        cap = int(value)
    except (TypeError, ValueError):
        raise ValueError("max_tokens is required and must be a finite positive integer, "
                         "got %r" % (value,)) from None
    if cap <= 0:
        raise ValueError("max_tokens must be > 0, got %r" % (value,))
    return cap


class TurnWallCap(RequestFailure):
    """A turn ran past ``--turn-wall-cap``: the stream was closed, the turn aborted.

    Carries the partial fold so the row still records honest TTFT, first-token kind and
    the tokens the server had already emitted when the cap fired.
    """

    error_code = "turn_wall_cap"
    stop_reason = STOP_REASON_TURN_WALL_CAP

    def __init__(self, wall_s: float, fields: dict):
        super().__init__(None, "turn_wall_cap: turn wall %.1fs exceeded the cap %.1fs"
                              % (wall_s, float(fields.get("turn_wall_cap_s") or 0.0)),
                         stop_reason=STOP_REASON_TURN_WALL_CAP)
        self.wall_s = float(wall_s)
        self.fields = fields

    def as_response(self, cfg) -> dict:
        """A response-shaped dict so ``make_row`` records the aborted turn, not a blank."""
        f = self.fields
        return {
            "content": f.get("content_raw") or "",
            "content_raw": f.get("content_raw") or "",
            "reasoning": f.get("reasoning") or "",
            "content_source": f.get("content_source") or "none",
            "finish_reason": None,
            "finish_reasons": list(f.get("finish_reasons") or []),
            # RECORD-STOP-REASON: the harness closed this stream; that is not ``length``
            # and must never be read as one.
            "stop_reason": STOP_REASON_TURN_WALL_CAP,
            "truncated": True,
            "max_tokens": int(f.get("max_tokens") or coerce_max_tokens(
                getattr(cfg, "max_tokens", DEFAULT_MAX_TOKENS))),
            "prompt_tokens": None,
            "raw_cached": None,
            "token_source": "absent",
            "completion_tokens": f.get("completion_tokens"),
            "ttft_s": f.get("ttft_s"),
            "ttft_ms": f.get("ttft_ms"),
            "ttft_source": f.get("ttft_source") or TTFT_SOURCE_UNAVAILABLE,
            "first_token_kind": f.get("first_token_kind"),
            "cached_tokens": None,
            "cached_source": None,
            "engine_metrics_before": f.get("engine_metrics_before"),
            "engine_metrics_after": f.get("engine_metrics_after"),
            "metrics_scrape": bool(f.get("metrics_scrape")),
            "latency_s": f.get("latency_s"),
            "wall_ms": f.get("wall_ms"),
            # REQUEST-IDENTITY: the body bytes were serialised and sent before the cap
            # fired, so a wall-cap row can carry the request identity too.  ``unknown``
            # and complete=false only when the raise site never stamped it (no guess).
            "request_sha256": f.get("request_sha256") or REQUEST_SHA_UNKNOWN,
            "request_identity_complete": bool(f.get("request_sha256")),
            # TOOL-CHANNEL-WIRE: the request body (with the schema, on a tools-on run) was
            # serialised and sent before the cap fired, so the wire fact holds here too.
            "tool_calls": list(f.get("tool_calls") or []),
            "tool_calls_present": bool(f.get("tool_calls_present")),
            "tools_declared": bool(tools_enabled(cfg)),
            "tools_schema_sent": bool(tools_enabled(cfg)),
            "usage_missing": True,
        }


# ------------------------------------------------------------- request identity
#: Written when the exact wire body was not retained.  A row must never carry a
#: plausible-looking hash it cannot justify; ``unknown`` + complete=false is the honest
#: value and the ledger must treat it as non-deduplicable.
REQUEST_SHA_UNKNOWN = "unknown"


def request_digest(body: dict) -> str:
    """sha256 over the EXACT bytes ``send_chat`` hands to the wire for ``body``.

    The identity is the REQUEST (model, messages, temperature, max_tokens, stream,
    stream_options, chat_template_kwargs/thinking — and ``tools`` where an engine takes
    them as a body member), never the response.  Two different requests that happen to
    produce byte-identical response text therefore get different digests, and a re-send
    of one request gets the same digest.
    """
    return hashlib.sha256(json.dumps(body).encode("utf-8")).hexdigest()


# ------------------------------------------------------------- tool channel (wire)
# TOOL-CHANNEL-WIRE: the runner's tool channel was a TEXT protocol (run_longrun.py
# parse_tool_calls scans `content` for `<tool_call>`), but the request body never carried
# a `tools` member, so the model was never handed a schema to call and answered in prose
# (docs/TOOL-CHANNEL-ROOT-CAUSE.md).  This schema is exactly what the executor already
# serves (`execute_tool_call`: path, start_line, end_line) and exactly the arguments the
# live probe returned, so a served call needs no adapter.
READ_FILE_TOOL_NAME = "read_file"
FETCH_TOOL_NAME = "fetch"

FETCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "fetch",
        "description": (
            "Retrieve a masked body by reference. Ranges are byte offsets into "
            "the stored body."),
        "parameters": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Pointer reference."},
                "range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "integer"},
                        "end": {"type": "integer"},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
            "required": ["ref"],
            "additionalProperties": False,
        },
    },
}

READ_FILE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": READ_FILE_TOOL_NAME,
        "description": (
            "Read a bounded, 1-based inclusive line range from a file in the workspace. "
            "Use it instead of guessing at file contents."),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string",
                         "description": "Repository-relative path, e.g. ptr_engine/resolve.py"},
                "start_line": {"type": "integer", "description": "First line, 1-based"},
                "end_line": {"type": "integer",
                             "description": "Last line, 1-based, inclusive"},
            },
            "required": ["path", "start_line", "end_line"],
        },
    },
}

TOOL_CHOICE_AUTO = "auto"
TOOL_CHOICE_REQUIRED = "required"
TOOL_CHOICES = (TOOL_CHOICE_AUTO, TOOL_CHOICE_REQUIRED)


def tool_names(cfg) -> list[str]:
    """The tools this run DECLARED (``--tools``); an empty list means tools off."""
    return [n.strip() for n in str(getattr(cfg, "tools", "") or "").split(",") if n.strip()]


def tools_enabled(cfg) -> bool:
    """Whether the request body carries the ``read_file`` schema — THE single gate.

    ``run_longrun.tools_enabled`` delegates here, so the flag that labels a run and the
    flag that puts bytes on the wire can never disagree.
    """
    names = tool_names(cfg)
    return (READ_FILE_TOOL_NAME in names) or (FETCH_TOOL_NAME in names)


def fetch_tools_enabled(cfg) -> bool:
    """Whether the request body carries the ``fetch`` schema."""
    return FETCH_TOOL_NAME in tool_names(cfg)


def tools_choice(cfg) -> str:
    """``tool_choice`` for a tools-on body: ``auto`` unless an explicit valid choice."""
    value = str(getattr(cfg, "tool_choice", "") or "").strip().lower()
    return value if value in TOOL_CHOICES else TOOL_CHOICE_AUTO


def tools_body_members(cfg) -> dict:
    """The body members the tool channel adds — EMPTY on a tools-off run.

    Returning ``{}`` is what keeps a tools-off body byte-identical (same keys, same
    order, same ``request_digest``) to every request this client sent before the fix.
    """
    names = tool_names(cfg)
    schemas = []
    if READ_FILE_TOOL_NAME in names:
        schemas.append(READ_FILE_TOOL_SCHEMA)
    if FETCH_TOOL_NAME in names:
        schemas.append(FETCH_TOOL_SCHEMA)
    if not schemas:
        return {}
    return {"tools": [json.loads(json.dumps(s)) for s in schemas],
            "tool_choice": tools_choice(cfg)}


def parse_tool_arguments(raw):
    """``(parsed_object|None, error|None)`` for one call's ``arguments``.  Never raises.

    Malformed argument bytes become a RECORDED refusal in the runner, never a silent
    no-op: the caller writes the error on the row instead of dropping the call.
    """
    if isinstance(raw, dict):
        return raw, None
    if raw is None:
        return None, "missing_arguments"
    if isinstance(raw, str):
        if not raw.strip():
            return None, "empty_arguments"
        try:
            obj = json.loads(raw)
        except ValueError as exc:
            return None, "malformed_arguments_json: %s" % (exc,)
        if not isinstance(obj, dict):
            return None, "arguments_not_an_object"
        return obj, None
    return None, "arguments_not_a_string"


def structured_tool_calls(message) -> list[dict]:
    """Surface ``message.tool_calls`` as DATA (name + parsed arguments), never a boolean.

    Each record keeps the raw argument string beside the parse result and, when the parse
    failed, the error — so the layer above can refuse the call on a row instead of
    inventing an empty one.
    """
    out: list[dict] = []
    for pos, call in enumerate((message or {}).get("tool_calls") or []):
        if not isinstance(call, dict):
            continue
        fn = call.get("function") or {}
        if not isinstance(fn, dict):
            fn = {}
        raw = fn.get("arguments")
        parsed, err = parse_tool_arguments(raw)
        out.append({
            "index": call.get("index", pos),
            "id": call.get("id"),
            "type": call.get("type"),
            "name": fn.get("name") or call.get("name"),
            "arguments": raw if isinstance(raw, str) else json.dumps(raw),
            "arguments_json": parsed,
            "arguments_error": err,
        })
    return out


def request_body(cfg, messages: list, max_tokens=None) -> dict:
    """The OpenAI-ish body.  Streaming ALWAYS asks for the usage chunk.

    ``stream_options.include_usage`` is what makes SGLang report
    ``usage.prompt_tokens_details.cached_tokens`` on a stream at all; without it the
    final chunk carries no usage and the only cache signal left is the engine counter
    delta.

    ``max_tokens`` is non-negotiable: an explicit argument wins, else ``cfg.max_tokens``,
    else :data:`DEFAULT_MAX_TOKENS`.  A missing or nonsensical value raises; it is never
    silently omitted from the wire.
    """
    if max_tokens is None:
        max_tokens = getattr(cfg, "max_tokens", DEFAULT_MAX_TOKENS)
    cap = coerce_max_tokens(max_tokens)
    body = {
        "model": cfg.model,
        "messages": messages,
        "temperature": getattr(cfg, "temperature", 0),
        "max_tokens": cap,
        "stream": bool(cfg.stream),
    }
    if getattr(cfg, "seed", None) is not None:
        body["seed"] = int(cfg.seed)
    if cfg.stream:
        body["stream_options"] = {"include_usage": True}
    kwargs = thinking_kwargs(thinking_setting(cfg))
    if kwargs is not None:
        body["chat_template_kwargs"] = kwargs
    # TOOL-CHANNEL-WIRE: the schema the model is actually handed.  ``tools_body_members``
    # is empty unless the run declared the tool, so a tools-off body keeps its exact
    # bytes and its request_digest; a tools-on body GAINS two keys and therefore a NEW
    # digest — provenance moves on purpose (see docs/TOOL-CHANNEL-WIRE.md).
    body.update(tools_body_members(cfg))
    return body


def resolve_metrics_scrape(cfg) -> bool:
    """Whether to scrape ``/metrics`` around each request.

    Precedence: an explicit ``cfg.metrics_scrape`` (the CLI flag) > the
    ``PTR_METRICS_SCRAPE`` env var > :data:`DEFAULT_METRICS_SCRAPE` (True).  The flag is
    the only thing that reaches the wire, so a caller that forgets it still gets the
    conservative default for the concurrency-1 protocol.
    """
    explicit = getattr(cfg, "metrics_scrape", None)
    if explicit is not None:
        return bool(explicit)
    env = os.environ.get(METRICS_SCRAPE_ENV)
    if env is not None:
        return env.strip().lower() not in _TRUTHY_OF
    return DEFAULT_METRICS_SCRAPE


def add_metrics_scrape_argument(parser):
    """Register the opt-in flag on the runner's parser (Part B owns ``run_longrun.py``)."""
    parser.add_argument(
        METRICS_SCRAPE_FLAG,
        dest="metrics_scrape",
        action="store_true",
        default=DEFAULT_METRICS_SCRAPE,
        help="scrape /metrics before and after every request for per-request cache "
             "attribution (default on: one request per cell means ~2x wire requests)",
    )
    parser.add_argument(
        "--no-metrics-scrape",
        dest="metrics_scrape",
        action="store_false",
        help="disable the per-request /metrics scrape (rows then carry null counters)",
    )
    return parser


# ---------------------------------------------------------------- engine counters
def metrics_url(base_url: str) -> str:
    """``/metrics`` lives at the server root, NOT under ``/v1``."""
    base = (base_url or "").rstrip("/")
    for suffix in ("/v1/chat", "/v1", "/api/v1"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break
    return base + "/metrics"


def parse_metrics(text: str):
    """Parse the four engine counters out of a Prometheus text body.

    Returns a dict with exactly :data:`METRICS_KEYS`, or ``None`` when no listed counter
    appeared at all (a scrape that returned HTML, a 404 body, or a server that only
    exposes HTTP metrics).  Label sets are summed: these are totals, and one vLLM process
    may report one series for its only model while a router reports several.  A counter
    that is absent from the body stays ``None`` rather than ``0`` — absence is not a
    measured zero.
    """
    if not text:
        return None
    out = {key: None for key in METRICS_KEYS}
    seen = False
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            head, value = line.rsplit(None, 1)
            value = float(value)
        except ValueError:
            continue
        name = head.split("{", 1)[0]
        if ":" in name:
            name = name.split(":", 1)[1]
        for key in METRICS_KEYS:
            candidates = {key}
            if key.endswith("_total"):
                candidates.add(key[: -len("_total")])
            else:
                candidates.add(key + "_total")
            if name in candidates:
                out[key] = value if out[key] is None else out[key] + value
                seen = True
                break
    return out if seen else None


def _http_get(url: str, timeout: float) -> str:
    req = urllib.request.Request(url, headers={"Accept": "text/plain"})
    with urllib.request.urlopen(req, timeout=float(timeout)) as resp:
        return resp.read().decode("utf-8", "replace")


def scrape_metrics(base_url: str, timeout: float = 5.0, getter=None):
    """GET ``/metrics`` and return the four counters, or ``None`` if anything failed.

    A failed scrape is recorded as ``null``; it is never guessed, and it never fails the
    measured request.
    """
    getter = _http_get if getter is None else getter
    try:
        text = getter(metrics_url(base_url), float(timeout))
    except Exception:  # noqa: BLE001 - a scrape must never break a measured request
        return None
    return parse_metrics(text)


def metrics_cached_delta(before, after):
    """``prompt_tokens_cached_total`` delta, or ``None`` when it cannot be derived.

    Both snapshots must carry the counter; a counter that went backwards (a server
    restart inside one request) cannot be attributed to this request, so it is refused
    rather than clamped.
    """
    if not before or not after:
        return None
    b = before.get("prompt_tokens_cached_total")
    a = after.get("prompt_tokens_cached_total")
    if b is None or a is None:
        return None
    delta = float(a) - float(b)
    if delta < 0:
        return None
    return int(round(delta))


# ---------------------------------------------------------------- streaming
def iter_stream_chunks(lines):
    """Yield decoded SSE chunks from an iterable of byte/str lines."""
    for raw_line in lines:
        line = (raw_line.decode("utf-8", "replace")
                if isinstance(raw_line, (bytes, bytearray)) else str(raw_line)).strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(chunk, dict):
            yield chunk


def token_kind(delta):
    """The contract's token test: non-empty ``content``/``reasoning_content``/``tool_calls``."""
    if not isinstance(delta, dict):
        return None
    for key in TOKEN_DELTA_KEYS:
        value = delta.get(key)
        if key in ("content", "reasoning_content"):
            if isinstance(value, str) and value != "":
                return _KIND_FOR_KEY[key]
        elif value:
            # a non-empty tool_calls list is a token: the argument stream may follow, but
            # the call itself is the first thing the server emitted.
            return _KIND_FOR_KEY[key]
    return None


def _accumulate_tool_call_deltas(acc: dict, delta: dict) -> None:
    """Fold ONE streamed ``delta.tool_calls`` fragment into ``acc`` (keyed by index).

    The OpenAI/SGLang stream sends a call as an id/name fragment followed by argument
    fragments; the assembled call is what the runner must see, otherwise a streamed
    tools-on turn would still be recorded as a bare ``tool_calls_present`` boolean.
    """
    pieces = delta.get("tool_calls")
    if not pieces and delta.get("function_call"):
        # legacy single-function shape: no index, no id
        pieces = [{"index": 0, "function": delta.get("function_call")}]
    for pos, piece in enumerate(pieces or []):
        if not isinstance(piece, dict):
            continue
        idx = piece.get("index", pos)
        slot = acc.setdefault(idx, {"index": idx, "id": None, "type": "function",
                                    "function": {"name": "", "arguments": ""}})
        if piece.get("id"):
            slot["id"] = piece["id"]
        if piece.get("type"):
            slot["type"] = piece["type"]
        fn = piece.get("function") or {}
        if not isinstance(fn, dict):
            continue
        if isinstance(fn.get("name"), str) and fn["name"]:
            slot["function"]["name"] += fn["name"]
        args = fn.get("arguments")
        if isinstance(args, str) and args:
            slot["function"]["arguments"] += args
        elif isinstance(args, dict):
            slot["function"]["arguments"] += json.dumps(args)


def collect_stream(chunks, t0: float, clock, wall_cap_s=None, max_tokens=None):
    """Fold an SSE chunk sequence into content, reasoning, usage and honest TTFT.

    TTFT is latched on the first chunk carrying a token of ANY kind and is never
    substituted afterwards.  ``wall`` is the end-to-end elapsed time and is reported
    separately; it must never feed ``ttft_ms``.

    ``wall_cap_s`` is the per-turn ceiling: the moment a chunk arrives after it, the fold
    is abandoned and :class:`TurnWallCap` is raised with the partial fold attached.  The
    caller's ``with opener(...)`` closes the socket, so the stream is not drained.
    """
    content_parts: list = []
    reasoning_parts: list = []
    usage_payload = None
    finish_reason = None
    finish_reasons: list = []
    ttft = None
    first_token_kind = None
    token_pieces = 0
    tool_calls_present = False
    tool_call_acc: dict = {}

    for chunk in chunks:
        if wall_cap_s is not None and (clock() - t0) > float(wall_cap_s):
            wall = clock() - t0
            content_raw = "".join(content_parts)
            reasoning_raw = "".join(reasoning_parts)
            content_source = ("both" if (content_raw and reasoning_raw)
                              else "content" if content_raw
                              else "reasoning" if reasoning_raw
                              else "none")
            raise TurnWallCap(wall, {
                "content_raw": content_raw,
                "reasoning": reasoning_raw,
                "content_source": content_source,
                # No final usage chunk arrives on an aborted stream: this is the count of
                # emitted delta pieces, recorded as the completion tokens the turn had
                # already spent, never as a server-reported measurement.
                "completion_tokens": token_pieces,
                "ttft_s": ttft,
                "ttft_ms": round(ttft * 1000.0, 3) if ttft is not None else None,
                "ttft_source": (TTFT_SOURCE_FIRST_DELTA if ttft is not None
                                else TTFT_SOURCE_UNAVAILABLE),
                "first_token_kind": first_token_kind,
                "latency_s": wall,
                "wall_ms": round(wall * 1000.0, 3),
                "max_tokens": (coerce_max_tokens(max_tokens)
                               if max_tokens is not None else None),
                "turn_wall_cap_s": float(wall_cap_s),
                "finish_reasons": list(finish_reasons),
                "tool_calls_present": tool_calls_present,
                "stop_reason": STOP_REASON_TURN_WALL_CAP,
            })
        if chunk.get("usage"):
            usage_payload = chunk
        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or {}
            piece_c = delta.get("content")
            piece_r = delta.get("reasoning_content")
            if piece_r is None:
                # text-only alias some builds emit; assembled, but it never latches TTFT
                # because the seam contract's token set does not contain it.
                piece_r = delta.get("reasoning")
            kind = token_kind(delta)
            if kind is not None and ttft is None:
                ttft = clock() - t0
                first_token_kind = kind
            if isinstance(piece_c, str) and piece_c:
                content_parts.append(piece_c)
                token_pieces += 1
            if isinstance(piece_r, str) and piece_r:
                reasoning_parts.append(piece_r)
                token_pieces += 1
            if delta.get("tool_calls") or delta.get("function_call"):
                # STOP-REASON-HOLES: ANY tool-call delta (id, name, or argument fragment)
                # is a production signal even when no text and no finish chunk follow.
                tool_calls_present = True
                # TOOL-CHANNEL-WIRE: keep the CALL, not just its existence.
                _accumulate_tool_call_deltas(tool_call_acc, delta)
            if choice.get("finish_reason"):
                # PER-CHOICE provenance: every choice that named a stop is kept, and the
                # LAST one is the finish_reason that ended the stream.
                finish_reason = choice.get("finish_reason")
                finish_reasons.append({"index": choice.get("index"),
                                       "finish_reason": finish_reason})

    wall = clock() - t0
    return {
        "content_raw": "".join(content_parts),
        "reasoning": "".join(reasoning_parts),
        "usage_payload": usage_payload,
        "finish_reason": finish_reason,
        "finish_reasons": finish_reasons,
        "ttft": ttft,
        "first_token_kind": first_token_kind,
        "tool_calls_present": tool_calls_present,
        # TOOL-CHANNEL-WIRE: the assembled structured calls (empty when the turn made none).
        "tool_calls": structured_tool_calls(
            {"tool_calls": [tool_call_acc[i] for i in sorted(tool_call_acc)]}),
        "wall": wall,
    }


def usage_cached_tokens(usage_payload):
    """Per-request cached tokens from ``usage.prompt_tokens_details.cached_tokens``.

    ``0`` is a real measurement and is returned as ``0``.  ``None``/absent is returned as
    ``None`` — the null is then resolved by the metrics delta, never imputed.
    """
    usage = (usage_payload or {}).get("usage") or {}
    details = usage.get("prompt_tokens_details")
    if isinstance(details, dict):
        value = details.get("cached_tokens")
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


# ---------------------------------------------------------------- one request
def _urlopen(req, timeout):
    return urllib.request.urlopen(req, timeout=float(timeout))


def send_chat(cfg, messages: list, *, opener=None, getter=None, clock=None,
              max_tokens=None, wall_cap_s=None) -> dict:
    """Send one chat request and return the measured response.

    Public name kept identical to the inline implementation it replaces, so callers are
    unchanged.  The returned dict is a superset of the old one: every legacy key is still
    present, and the seam-contract fields are added.

    ``opener``/``getter``/``clock`` are injection points so the tests can fake the whole
    stream and both scrapes without a socket.

    ``max_tokens`` defaults to ``cfg.max_tokens`` (then :data:`DEFAULT_MAX_TOKENS`) and is
    always on the wire.  ``wall_cap_s`` defaults to ``cfg.turn_wall_cap``; when set, a
    stream that crosses it is CLOSED and :class:`TurnWallCap` is raised instead of being
    read to the end.
    """
    opener = _urlopen if opener is None else opener
    clock = time.perf_counter if clock is None else clock
    cap = coerce_max_tokens(getattr(cfg, "max_tokens", DEFAULT_MAX_TOKENS)
                            if max_tokens is None else max_tokens)
    if wall_cap_s is None:
        wall_cap_s = getattr(cfg, "turn_wall_cap", None)
    metrics_scrape = resolve_metrics_scrape(cfg)
    timeout = float(getattr(cfg, "timeout", 900.0))
    metrics_timeout = float(getattr(cfg, "metrics_timeout", 5.0))

    before = scrape_metrics(cfg.base_url, metrics_timeout, getter=getter) if metrics_scrape else None

    body = request_body(cfg, messages, max_tokens=cap)
    data = json.dumps(body).encode("utf-8")
    # REQUEST-IDENTITY: sha256 over the exact bytes built here and handed to urlopen.
    # The row carries this, never a hash of the response: a duplicate row is two rows
    # from ONE send, and two different sends cannot collide on this field.
    request_sha = hashlib.sha256(data).hexdigest()
    url = cfg.base_url.rstrip("/") + "/chat/completions"
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json",
                 "Accept": "text/event-stream" if cfg.stream else "application/json"},
    )

    t0 = clock()
    ttft = None
    first_token_kind = None
    usage_payload = None
    finish_reason = None
    finish_reasons: list = []
    tool_calls_present = False
    tool_calls: list[dict] = []
    # TOOL-CHANNEL-WIRE: the fact this row is allowed to claim — was a schema on the wire?
    # ``declared`` comes from the flag, ``sent`` from the body actually serialised here.
    tools_declared = tools_enabled(cfg)
    tools_schema_sent = bool(body.get("tools"))
    try:
        with opener(req, timeout) as resp:
            if not cfg.stream:
                payload = json.loads(resp.read().decode("utf-8"))
                wall = clock() - t0
                choice0 = (payload.get("choices") or [{}])[0]
                message = choice0.get("message") or {}
                content_raw = message.get("content") or ""
                reasoning_raw = message.get("reasoning_content") or message.get("reasoning") or ""
                finish_reason = choice0.get("finish_reason")
                # TOOL-CHANNEL-WIRE: the CALL, not a boolean.  A malformed argument
                # string is retained with its error rather than dropped.
                tool_calls = structured_tool_calls(message)
                tool_calls_present = bool(tool_calls or message.get("function_call"))
                finish_reasons = ([{"index": choice0.get("index"),
                                    "finish_reason": finish_reason}]
                                  if finish_reason else [])
                usage_payload = payload
                # A non-streamed turn carries no delta at all: unavailable, not a
                # wall-clock stand-in.
                ttft, first_token_kind = None, None
            else:
                folded = collect_stream(iter_stream_chunks(resp), t0, clock,
                                        wall_cap_s=wall_cap_s, max_tokens=cap)
                content_raw = folded["content_raw"]
                reasoning_raw = folded["reasoning"]
                usage_payload = folded["usage_payload"]
                finish_reason = folded["finish_reason"]
                finish_reasons = folded["finish_reasons"]
                tool_calls_present = folded.get("tool_calls_present", False)
                tool_calls = folded.get("tool_calls") or []
                ttft = folded["ttft"]
                first_token_kind = folded["first_token_kind"]
                wall = folded["wall"]
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read()[:500].decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            detail = ""
        raise RequestFailure(exc.code, f"HTTP {exc.code}: {detail}",
                             stop_reason=STOP_REASON_HTTP_ERROR) from exc
    except TurnWallCap as exc:
        # REQUEST-IDENTITY: this request DID reach the wire; the wall-cap row may record
        # its identity instead of "unknown".
        exc.fields.setdefault("request_sha256", request_sha)
        raise
    except RequestFailure:
        raise
    except Exception as exc:  # noqa: BLE001 - recorded, never retried
        raise RequestFailure(None, f"{type(exc).__name__}: {exc}",
                             stop_reason=STOP_REASON_STREAM_ERROR) from exc

    after = scrape_metrics(cfg.base_url, metrics_timeout, getter=getter) if metrics_scrape else None

    # ---- cache attribution: the server's own per-request usage first, then the engine
    # counter delta around exactly this request, then an honest null.
    cached_tokens = usage_cached_tokens(usage_payload)
    cached_source = CACHED_SOURCE_USAGE if cached_tokens is not None else None
    if cached_tokens is None:
        derived = metrics_cached_delta(before, after)
        if derived is not None:
            cached_tokens = derived
            cached_source = CACHED_SOURCE_METRICS

    prompt, raw_cached, token_source = extract_usage(usage_payload or {}, cfg.engine)
    usage = (usage_payload or {}).get("usage") or {}
    completion = int(usage["completion_tokens"]) if usage.get("completion_tokens") is not None else None

    content_source = ("both" if (content_raw and reasoning_raw)
                      else "content" if content_raw
                      else "reasoning" if reasoning_raw
                      else "none")
    answer = content_raw if content_raw else reasoning_raw

    # RECORD-STOP-REASON: one closed-vocabulary word for WHY this ended, derived once,
    # here, from the finish chunk (per choice) plus the completion ceiling that was
    # actually sent.  ``truncated`` is derived FROM it, so the two can never disagree.
    content_present = bool((content_raw or "").strip() or (reasoning_raw or "").strip())
    sent_cap = int((body or {}).get("max_tokens") or cap)
    stop_reason = derive_stop_reason(finish_reason, content_present=content_present,
                                     completion_tokens=completion, max_tokens=sent_cap,
                                     tool_calls_present=tool_calls_present)
    truncated = truncated_for(stop_reason)

    return {
        # --- legacy contract (unchanged names) ---
        "content": answer,
        "content_raw": content_raw,
        "reasoning": reasoning_raw,
        "content_source": content_source,
        "finish_reason": finish_reason,
        "finish_reasons": finish_reasons,
        "stop_reason": stop_reason,
        "truncated": truncated,
        "tool_calls_present": bool(tool_calls_present),
        # TOOL-CHANNEL-WIRE: structured calls (name + parsed arguments + parse error),
        # the data ``run_longrun.calls_from_response`` consumes BEFORE any text scan.
        "tool_calls": list(tool_calls),
        # TOOL-CHANNEL-WIRE: DECLARED (the run's --tools) vs ACTUALLY SENT (this body).
        "tools_declared": bool(tools_declared),
        "tools_schema_sent": bool(tools_schema_sent),
        # the ceiling AS SENT on the wire (read back from the body, not re-derived):
        "max_tokens": sent_cap,
        "prompt_tokens": prompt,
        "raw_cached": raw_cached,
        "token_source": token_source,
        "completion_tokens": completion,
        "ttft_s": ttft,
        # --- seam contract v1 ---
        "ttft_ms": round(ttft * 1000.0, 3) if ttft is not None else None,
        "ttft_source": (TTFT_SOURCE_FIRST_DELTA if ttft is not None
                        else TTFT_SOURCE_UNAVAILABLE),
        "first_token_kind": first_token_kind,
        "cached_tokens": cached_tokens,
        "cached_source": cached_source,
        "engine_metrics_before": before,
        "engine_metrics_after": after,
        "metrics_scrape": bool(metrics_scrape),
        # --- request identity (one send == one identity) ---
        "request_sha256": request_sha,
        "request_identity_complete": True,
        # --- timing that is NOT TTFT ---
        "latency_s": wall,
        "wall_ms": round(wall * 1000.0, 3),
        "usage_missing": prompt is None,
    }


def extract_usage(payload: dict, engine: str):
    """Return (prompt_tokens, raw_cached, token_source) from an OpenAI-ish response."""
    payload = payload or {}
    usage = payload.get("usage") or {}
    meta = payload.get("meta_info") or {}
    prompt, src = None, []
    if usage.get("prompt_tokens") is not None:
        prompt = int(usage["prompt_tokens"])
        src.append("usage.prompt_tokens")
    elif meta.get("prompt_tokens") is not None:
        prompt = int(meta["prompt_tokens"])
        src.append("meta_info.prompt_tokens")
    raw_cached = None
    details = usage.get("prompt_tokens_details")
    if isinstance(details, dict) and "cached_tokens" in details:
        raw_cached = details.get("cached_tokens")
        src.append("usage.prompt_tokens_details.cached_tokens")
    elif "cached_tokens" in usage:
        raw_cached = usage.get("cached_tokens")
        src.append("usage.cached_tokens")
    elif "cached_tokens" in meta:
        raw_cached = meta.get("cached_tokens")
        src.append("meta_info.cached_tokens")
    return prompt, raw_cached, (";".join(src) or "absent")


# ------------------------------------------------------- row provenance (ROW-PROVENANCE)
# WHY THIS BLOCK EXISTS
# ---------------------
# `HARNESS-MAP-V2` had to infer a "harness era" axis from FILE MTIMES because a row
# carried no harness, fixture-generation, model or thinking identity.  `LATENCY-REPORT`
# then had to mark every pair whose era was load-bearing NOT COMPARABLE, and four
# revisions of the same fixture (`LR-01.v2 -> v4 -> v5 -> v6/v7`) changed the task while
# the rows stayed anonymous.  Every row this module helps write now names its own
# provenance, so "which grid is this?" is read, not inferred.
#
# The one rule: an unknown provenance field is the STRING "unknown" and the row carries
# ``provenance_complete: false``.  Never null, never a plausible guess -- a wrong value
# is worse than an admitted gap.
PROVENANCE_UNKNOWN = "unknown"

#: Every provenance field a row and a run manifest carry.
PROVENANCE_FIELDS = (
    "arm",
    "model",
    "endpoint",
    "fixture_id",
    "fixture_sha256",
    "harness_sha256",
    "max_tokens",
    "thinking",
    "tools_mode",
)

#: The subset a comparison between two cells must agree on.  ``arm`` is deliberately
#: NOT here: the arm is the variable under test, not a confounder.  ``endpoint`` and
#: ``max_tokens`` are not here either -- both are already implied by ``model`` +
#: ``fixture_sha256``/``harness_sha256`` in practice, and ROW-PROVENANCE keeps the
#: load-bearing set to exactly the four fields the unit contract names.
PROVENANCE_LOAD_BEARING = ("fixture_sha256", "model", "thinking", "tools_mode")

#: The tool-mode strings ROW-PROVENANCE uses.  ``tools_mode`` is the literal switch, in
#: the same spirit as ``thinking``: "off" when the run sent no tools, "on:<csv>" naming
#: the tools it did send, and "unknown" when nothing on disk says which.
TOOLS_MODE_OFF = "off"
TOOLS_MODE_KNOWN_PREFIX = "on:"


def tools_mode_label(names) -> str:
    """``tools_mode`` for a run's tool list: "off", "on:<csv>", never a bare guess."""
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",") if n.strip()]
    names = [str(n) for n in (names or []) if str(n).strip()]
    if not names:
        return TOOLS_MODE_OFF
    return TOOLS_MODE_KNOWN_PREFIX + ",".join(names)


def is_provenance_known(value) -> bool:
    """A provenance value is known when it is present and is not the unknown marker."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() in ("", PROVENANCE_UNKNOWN):
        return False
    return True


def _prov(value):
    """Coerce one provenance value: missing/None/blank -> "unknown" (never null)."""
    if isinstance(value, str):
        text = value.strip()
        return text if text else PROVENANCE_UNKNOWN
    if value is None:
        return PROVENANCE_UNKNOWN
    return value


def provenance_block(arm=None, model=None, endpoint=None, fixture_id=None,
                     fixture_sha256=None, harness_sha256=None, max_tokens=None,
                     thinking=None, tools_mode=None, tools_schema_sent=None) -> dict:
    """The provenance block written on ONE row and on the run manifest.

    Every missing argument becomes the string ``"unknown"`` and ``provenance_complete``
    is ``False``.  ``provenance_missing`` names the fields that are unknown, so a
    retrofit report never has to re-derive which ones needed looking for.

    TOOL-CHANNEL-WIRE: ``tools_mode`` is the DECLARED switch (``on:read_file`` names what
    the run asked for).  ``tools_schema_sent`` is the separate WIRE fact — ``True`` only
    once a ``tools`` member was actually serialised into a request body.  Before this
    field existed, every historical ``on:read_file`` row was a label with no schema
    behind it; those rows are NOT retrofitted and carry no ``tools_schema_sent``.
    """
    block = {
        "arm": _prov(arm),
        "model": _prov(model),
        "endpoint": _prov(endpoint),
        "fixture_id": _prov(fixture_id),
        "fixture_sha256": _prov(fixture_sha256),
        "harness_sha256": _prov(harness_sha256),
        "max_tokens": _prov(max_tokens),
        "thinking": _prov(thinking),
        "tools_mode": _prov(tools_mode),
        "tools_schema_sent": _prov(tools_schema_sent),
    }
    missing = [name for name in PROVENANCE_FIELDS if not is_provenance_known(block[name])]
    block["provenance_complete"] = not missing
    block["provenance_missing"] = missing
    return block


def fixture_label(fixture, fallback_id=None) -> str:
    """``fixture_id`` = ``<task_id>.<fixture_version>`` when both are declared.

    A fixture that declares no ``fixture_version`` is named by its ``task_id`` alone
    (the truth on disk) rather than by a version guessed from its filename.
    """
    if isinstance(fixture, dict):
        task = fixture.get("task_id")
        version = fixture.get("fixture_version")
        if task and version:
            return "%s.%s" % (task, version)
        if task:
            return str(task)
    return _prov(fallback_id)


def same_provenance(cell_a, cell_b) -> tuple[bool, list[str]]:
    """Do two cells share every LOAD-BEARING provenance field?

    Returns ``(True, [])`` when they do, else ``(False, [differing fields])``.  A cell
    is either a row, a whole-file provenance block, or a plain dict of the nine
    fields; only ``PROVENANCE_LOAD_BEARING`` is compared, so two cells that differ
    only in ``arm`` are the SAME provenance (that difference is the measurement).
    An unknown on either side counts as differing: two unknowns are not evidence of
    agreement, and one unknown cannot be asserted equal to a known value.
    """
    a = cell_a or {}
    b = cell_b or {}
    differing = []
    for name in PROVENANCE_LOAD_BEARING:
        va, vb = _prov(a.get(name) if isinstance(a, dict) else None), \
                 _prov(b.get(name) if isinstance(b, dict) else None)
        if not is_provenance_known(va) or not is_provenance_known(vb) or va != vb:
            differing.append(name)
    return (not differing), differing
