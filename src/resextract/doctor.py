"""Dependency prober: classify each leg as ``core`` or ``optional``.

Exit contract: **0** when every core leg is green (optional legs may be down),
**2** when any core leg is down.  No probe ever raises: a failure is data
(``ok=False`` + a human detail string), never an exception.

Timeouts: 5 s per leg, 30 s for the Occamy completion probe.  **A timeout is not
a verdict of its own.**  When a leg's full probe exceeds its bound the doctor runs
a cheap TCP-connect liveness check on the same host:port and distinguishes
``state="slow"`` (something is listening and accepting, but the full probe did not
finish in time) from ``state="down"`` (the cheap check failed too -- connection
refused, unreachable).  A slow leg is *not* green, is kept out of ``core_down``
(so it cannot manufacture a failure), and is reported in ``core_slow``.  The
per-leg bound itself is unchanged.

Re-probe policy (added for the control-path stall): a leg that reported **DOWN**
is remembered for at most ``negative_ttl_s()`` seconds (default
``DEFAULT_NEGATIVE_TTL_S``) so a *known-down* dependency -- the Occamy model
endpoint, down by user decision -- is not force-probed on every single call.
Reuse only ever suppresses the **probe**, never the **verdict**: the remembered
leg dict is returned unchanged, an UP result is never remembered, and
``force=True`` always performs a fresh probe.  Same idea as the negative cache
and degradation latch in :mod:`resextract.web.search`, but strictly bounded in
time (that client's latch is latched for life; this one expires).
"""

from __future__ import annotations

import inspect
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit

import httpx

CORE = "core"
OPTIONAL = "optional"

#: Per-leg classification states.  ``UP``/``DOWN`` are the historical booleans
#: (``ok``); ``SLOW`` is the distinct degraded state for a leg whose full probe
#: timed out while a cheap liveness check proved something is still accepting.
UP = "up"
DOWN = "down"
SLOW = "slow"

HTTP_TIMEOUT = 5.0
OCCAMY_COMPLETION_TIMEOUT = 30.0
DASHBOARD_PORT = 8901

#: Bound for the *cheap* liveness check used only to classify a timed-out leg.
#: Deliberately far below ``HTTP_TIMEOUT``: it must be able to answer "is
#: anything accepting there?" while the failing probe is already 5 s late.
SLOW_LIVENESS_TIMEOUT = 0.5

#: Exceptions that mean "the probe did not answer in time" (not "refused").
TIMEOUT_EXCEPTIONS: tuple[type[BaseException], ...] = (httpx.TimeoutException, TimeoutError)

#: Default seconds a DOWN verdict may be reused before a fresh probe is forced.
#: Short on purpose: the dashboard's health view must reflect a recovery
#: promptly, but a control action must not pay the Occamy connect timeout
#: (``HTTP_TIMEOUT`` = 5 s) on every click.
DEFAULT_NEGATIVE_TTL_S = 30.0
NEGATIVE_TTL_ENV = "RESEXTRACT_DOCTOR_NEGATIVE_TTL_S"

#: The one leg whose DOWN state is remembered (a model endpoint the user keeps
#: deliberately down).  Other legs stay semantics-identical: they probe afresh.
OCCAMY_CACHE_KEY = "Occamy"

DEFAULT_ENDPOINTS: dict[str, str] = {
    "occamy_base_url": "http://192.168.2.168:8012/v1",
    "occamy_model": "occamy-1.0",
    "searxng_base_url": "http://127.0.0.1:8080",
    "crawl_scrape_base_url": "http://127.0.0.1:8891",
    "docling_bridge_base_url": "http://127.0.0.1:8893",
}

RENDERERS = ("pdflatex", "pandoc", "tectonic")

#: Monotonic clock used by the negative memory; tests monkeypatch this to fake
#: time instead of sleeping.  Probe *latency* measurement keeps ``time.monotonic``.
_clock: Callable[[], float] = time.monotonic

#: leg key -> (expiry, remembered DOWN leg dict)
_NEGATIVE_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def utcnow() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def endpoints() -> dict[str, str]:
    """Verified endpoint defaults, optionally overridden by config/resextract.toml."""
    ep = dict(DEFAULT_ENDPOINTS)
    candidates = [
        Path("config/resextract.toml"),
        Path(__file__).resolve().parents[2] / "config" / "resextract.toml",
    ]
    for cfg in candidates:
        if not cfg.exists():
            continue
        try:
            import tomllib

            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
            for key, value in (data.get("endpoints") or {}).items():
                if isinstance(value, str):
                    ep[key] = value
            break
        except Exception:  # pragma: no cover - never fail the doctor on config
            break
    return ep


def negative_ttl_s() -> float:
    """Seconds a DOWN verdict may be reused before a fresh probe is forced.

    Precedence: ``RESEXTRACT_DOCTOR_NEGATIVE_TTL_S`` env var, then ``[doctor]
    negative_ttl_s`` in ``config/resextract.toml``, then
    :data:`DEFAULT_NEGATIVE_TTL_S`.  ``0`` disables reuse (every call probes).
    """
    raw = os.environ.get(NEGATIVE_TTL_ENV)
    if raw is not None and raw.strip():
        try:
            return max(0.0, float(raw))
        except ValueError:
            pass
    candidates = [
        Path("config/resextract.toml"),
        Path(__file__).resolve().parents[2] / "config" / "resextract.toml",
    ]
    for cfg in candidates:
        if not cfg.exists():
            continue
        try:
            import tomllib

            value = (tomllib.loads(cfg.read_text(encoding="utf-8")).get("doctor") or {}).get(
                "negative_ttl_s"
            )
        except Exception:  # pragma: no cover - never fail the doctor on config
            break
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return max(0.0, float(value))
        break
    return DEFAULT_NEGATIVE_TTL_S


def remember_down(key: str, result: dict[str, Any]) -> dict[str, Any]:
    """Remember a DOWN result for at most ``negative_ttl_s()`` seconds; return it.

    The remembered value is a copy of the leg dict exactly as probed, so a
    reuse cannot change what the doctor reports.
    """
    ttl = negative_ttl_s()
    if ttl > 0:
        _NEGATIVE_CACHE[key] = (_clock() + ttl, dict(result))
    return result


def reuse_down(key: str, *, force: bool = False) -> dict[str, Any] | None:
    """Return a still-fresh remembered DOWN result, or ``None`` to probe.

    ``force=True`` always returns ``None``: an explicit force never reuses.
    An expired entry is dropped rather than returned.
    """
    if force:
        return None
    entry = _NEGATIVE_CACHE.get(key)
    if entry is None:
        return None
    expiry, result = entry
    if _clock() >= expiry:
        _NEGATIVE_CACHE.pop(key, None)
        return None
    return dict(result)


def finish(key: str, result: dict[str, Any]) -> dict[str, Any]:
    """Record ``result`` as DOWN (or clear the memory when it is UP/slow); return it.

    Only a genuine **DOWN** is remembered.  A ``slow`` leg is transient by
    definition (the service answered the cheap check), so caching it would turn a
    momentary stall into a sticky verdict -- the very defect this module fixes.
    """
    if result.get("ok") or result.get("state") == SLOW:
        _NEGATIVE_CACHE.pop(key, None)
    else:
        remember_down(key, result)
    return result


def leg(leg_name: str, klass: str, ok: bool, detail: str, **extra: Any) -> dict[str, Any]:
    """Build a leg dict.  ``state`` defaults to ``up``/``down`` from ``ok``."""
    out: dict[str, Any] = {
        "leg": leg_name,
        "class": klass,
        "ok": bool(ok),
        "state": UP if ok else DOWN,
        "detail": detail,
    }
    out.update(extra)
    return out


def _host_port(base_url: str) -> tuple[str, int] | None:
    """``(host, port)`` for ``base_url`` (scheme default when no port is given)."""
    parts = urlsplit(base_url)
    if not parts.hostname:
        return None
    try:
        port = parts.port
    except ValueError:  # malformed port
        return None
    if port is None:
        port = 443 if parts.scheme == "https" else 80
    return parts.hostname, int(port)


def cheap_alive(base_url: str, *, timeout: float = SLOW_LIVENESS_TIMEOUT) -> tuple[bool, str]:
    """Is anything *accepting* at ``base_url``'s host:port?  ``(alive, evidence)``.

    Evidence for "reachable", never proof that the service works: a hung server
    accepts a connection and then never replies, and a blackholed host neither
    accepts nor refuses.  Used only to classify a leg whose *full* probe exceeded
    its bound; never as a green check.
    """
    target = _host_port(base_url)
    if target is None:
        return False, f"no host:port in {base_url!r}"
    host, port = target
    sock = socket.socket()
    try:
        sock.settimeout(max(0.05, float(timeout)))
        sock.connect((host, port))
        return True, f"TCP connect to {host}:{port} accepted within {timeout}s"
    except OSError as exc:
        return False, f"TCP connect to {host}:{port} failed ({type(exc).__name__}: {exc})"
    finally:
        sock.close()


def classify_timeout(
    leg_name: str, klass: str, base_url: str, exc: BaseException, **extra: Any
) -> dict[str, Any]:
    """Classify a **timed-out** leg: reachable-but-slow vs DOWN.

    ``slow`` means: the full probe exceeded its bound, but the cheap liveness
    check on the same host:port succeeded, so the dependency is *reachable*.
    ``ok`` stays ``False`` -- slow is not green -- but ``state="slow"`` keeps it
    out of ``core_down`` wherever a caller aggregates.
    """
    alive, how = cheap_alive(base_url)
    if alive:
        return leg(
            leg_name,
            klass,
            False,
            f"{_short(exc)}; {how} -> reachable but slow (per-leg bound {HTTP_TIMEOUT}s)",
            state=SLOW,
            slow=True,
            bound_s=HTTP_TIMEOUT,
            **extra,
        )
    return leg(leg_name, klass, False, f"{_short(exc)}; {how} -> down", **extra)


def _short(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    return text[:300]


# --------------------------------------------------------------------------- #
# Probes (each returns a leg dict and never raises)
# --------------------------------------------------------------------------- #


def probe_occamy(*, force: bool = False) -> dict[str, Any]:
    """GET /v1/models, then a max_tokens=8 completion with thinking disabled.

    A **DOWN** verdict is remembered for at most ``negative_ttl_s()`` seconds
    (default 30 s) so a known-down endpoint is not re-probed on every call, and
    the staleness bound is exactly that TTL: no DOWN result is reused past its
    expiry and ``force=True`` never reuses one.  An **UP** verdict is never
    remembered, so a recovery is observed on the first probing call.
    """
    cached = reuse_down(OCCAMY_CACHE_KEY, force=force)
    if cached is not None:
        return cached
    ep = endpoints()
    base = ep["occamy_base_url"].rstrip("/")
    wanted = ep.get("occamy_model")
    started = time.monotonic()
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            models = client.get(f"{base}/models")
        if models.status_code != 200:
            return finish(
                OCCAMY_CACHE_KEY,
                leg("Occamy", CORE, False, f"GET /models -> HTTP {models.status_code}"),
            )
        ids: list[str] = []
        try:
            data = models.json()
            ids = [m.get("id") for m in (data.get("data") or []) if isinstance(m, dict) and m.get("id")]
        except Exception:
            ids = []
        model_id = wanted if wanted in ids else (ids[0] if ids else None)
        with httpx.Client(timeout=OCCAMY_COMPLETION_TIMEOUT) as client:
            completion = client.post(
                f"{base}/chat/completions",
                json={
                    "model": model_id or wanted or "occamy-1.0",
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 8,
                    "chat_template_kwargs": {"enable_thinking": False},
                },
            )
        ms = int((time.monotonic() - started) * 1000)
        ok = completion.status_code == 200
        detail = (
            f"model={model_id or 'none'}; completion HTTP {completion.status_code}"
            f" (thinking=off, max_tokens=8, {ms} ms)"
        )
        return finish(
            OCCAMY_CACHE_KEY,
            leg(
                "Occamy",
                CORE,
                ok,
                detail,
                model=model_id,
                models=ids,
                http_status=completion.status_code,
                latency_ms=ms,
            ),
        )
    except Exception as exc:
        if isinstance(exc, TIMEOUT_EXCEPTIONS):
            return finish(OCCAMY_CACHE_KEY, classify_timeout("Occamy", CORE, base, exc))
        return finish(OCCAMY_CACHE_KEY, leg("Occamy", CORE, False, _short(exc)))


def probe_searxng() -> dict[str, Any]:
    base = endpoints()["searxng_base_url"].rstrip("/")
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.get(f"{base}/search", params={"q": "doctor probe", "format": "json"})
        if response.status_code != 200:
            return leg("SearXNG", CORE, False, f"GET /search -> HTTP {response.status_code}")
        try:
            results = response.json().get("results")
        except Exception:
            results = None
        if not isinstance(results, list):
            return leg("SearXNG", CORE, False, "HTTP 200 but no 'results' array")
        return leg(
            "SearXNG",
            CORE,
            True,
            f"HTTP 200, results={len(results)}",
            http_status=200,
            result_count=len(results),
        )
    except Exception as exc:
        if isinstance(exc, TIMEOUT_EXCEPTIONS):
            return classify_timeout("SearXNG", CORE, base, exc)
        return leg("SearXNG", CORE, False, _short(exc))


def probe_crawl_bridge() -> dict[str, Any]:
    base = endpoints()["crawl_scrape_base_url"].rstrip("/")
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.get(f"{base}/health")
        ok = False
        detail = f"GET /health -> HTTP {response.status_code}"
        if response.status_code == 200:
            try:
                payload = response.json()
                ok = bool(payload.get("ok"))
                detail = f"HTTP 200, ok={payload.get('ok')}"
            except Exception:
                ok = False
                detail = "HTTP 200 but body is not JSON"
        return leg("crawl bridge", CORE, ok, detail, http_status=response.status_code)
    except Exception as exc:
        if isinstance(exc, TIMEOUT_EXCEPTIONS):
            return classify_timeout("crawl bridge", CORE, base, exc)
        return leg("crawl bridge", CORE, False, _short(exc))


def _venv_tool(name: str) -> str | None:
    """Locate a console script shipped in this venv (never resolve the python symlink)."""
    exe = Path(sys.executable)
    candidates = [
        exe.parent / name,  # e.g. <venv>/bin/graphify (sys.executable is <venv>/bin/python)
        Path(sys.prefix) / "bin" / name,
        exe.resolve().parent / name,  # last resort: the real interpreter dir
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which(name)


def probe_graphify() -> dict[str, Any]:
    exe = _venv_tool("graphify")
    if exe is None:
        return leg("graphify", CORE, False, "graphify executable not found")
    try:
        proc = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=HTTP_TIMEOUT)
    except Exception as exc:
        return leg("graphify", CORE, False, _short(exc))
    version = (proc.stdout or proc.stderr or "").strip().splitlines()
    version_text = version[0] if version else "unknown"
    if proc.returncode != 0:
        return leg("graphify", CORE, False, f"graphify --version exit {proc.returncode}: {version_text}")
    try:
        proc2 = subprocess.run(
            [sys.executable, "-c", "import openai; print(openai.__version__)"],
            capture_output=True,
            text=True,
            timeout=HTTP_TIMEOUT,
        )
    except Exception as exc:
        return leg("graphify", CORE, False, _short(exc))
    openai_version = (proc2.stdout or "").strip() or "missing"
    ok = proc2.returncode == 0
    detail = f"{version_text}; openai {openai_version}"
    if not ok:
        detail = f"{version_text}; import openai FAILED (exit {proc2.returncode})"
    return leg("graphify", CORE, ok, detail, version=version_text, openai=openai_version)


def probe_docling() -> dict[str, Any]:
    base = endpoints()["docling_bridge_base_url"].rstrip("/")
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.get(f"{base}/health")
        ok = False
        detail = f"GET /health -> HTTP {response.status_code} (optional)"
        if response.status_code == 200:
            try:
                ok = bool(response.json().get("ok"))
                detail = f"HTTP 200, ok={response.json().get('ok')} (optional)"
            except Exception:
                detail = "HTTP 200 but body is not JSON (optional)"
        return leg("docling bridge", OPTIONAL, ok, detail, http_status=response.status_code)
    except Exception as exc:
        if isinstance(exc, TIMEOUT_EXCEPTIONS):
            return classify_timeout("docling bridge", OPTIONAL, base, exc)
        return leg("docling bridge", OPTIONAL, False, f"{_short(exc)} (optional)")


def probe_renderers() -> dict[str, Any]:
    """Report which renderers are missing — absence is *information*, not failure."""
    found = [name for name in RENDERERS if shutil.which(name)]
    missing = [name for name in RENDERERS if name not in found]
    if missing and found:
        detail = f"found: {', '.join(found)}; missing: {', '.join(missing)}"
    elif missing:
        detail = f"missing: {', '.join(missing)} (paper dockets emit .tex + markdown)"
    else:
        detail = f"found: {', '.join(found)}"
    return leg("renderers", OPTIONAL, True, detail, found=found, missing=missing)


def probe_dashboard_port() -> dict[str, Any]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", DASHBOARD_PORT))
        return leg("dashboard port", OPTIONAL, True, f"127.0.0.1:{DASHBOARD_PORT} free", port=DASHBOARD_PORT)
    except OSError as exc:
        return leg(
            "dashboard port",
            OPTIONAL,
            False,
            f"127.0.0.1:{DASHBOARD_PORT} in use ({exc.strerror or exc})",
            port=DASHBOARD_PORT,
        )
    finally:
        sock.close()


# --------------------------------------------------------------------------- #
# Runner / formatting
# --------------------------------------------------------------------------- #


def default_probes() -> list[tuple[str, Callable[[], dict[str, Any]]]]:
    """``(leg_name, probe)`` pairs, resolved via module globals so tests can monkeypatch."""
    return [
        ("Occamy", probe_occamy),
        ("SearXNG", probe_searxng),
        ("crawl bridge", probe_crawl_bridge),
        ("graphify", probe_graphify),
        ("docling bridge", probe_docling),
        ("renderers", probe_renderers),
        ("dashboard port", probe_dashboard_port),
    ]


def _invoke(fn: Callable[..., dict[str, Any]], force: bool) -> dict[str, Any]:
    """Call a probe with ``force`` only when it declares that keyword.

    Keeps zero-argument probes (and test doubles) callable unchanged while
    letting a probe that owns a negative memory honour an explicit force.
    """
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):  # pragma: no cover - exotic callables
        params = {}
    if "force" in params:
        return fn(force=force)
    return fn()


def run_doctor(
    probes: Iterable[tuple[str, Callable[[], dict[str, Any]]] | Callable[[], dict[str, Any]]] | None = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Run every probe; never raises.  Returns the report with its exit code.

    ``probes`` accepts ``(leg_name, callable)`` pairs (the default, so a probe
    that raises can still be named) or bare callables.

    ``force=True`` bypasses the negative memory and probes every dependency
    afresh.  Otherwise a leg that reported DOWN less than ``negative_ttl_s()``
    seconds ago is re-reported from that memory instead of being re-probed: the
    verdict and every leg dict are identical to a fresh probe's would-be output,
    only the network attempt is skipped.

    **Slow is not down.**  ``core_down``/``optional_down`` list only legs whose
    ``state`` is ``DOWN`` (a leg dict without a ``state``, e.g. a test double, is
    classified by ``ok`` exactly as before).  A leg that timed out while the
    cheap liveness check still saw something accepting is reported with
    ``state="slow"`` and listed in ``core_slow``/``optional_slow`` instead.  It
    does **not** enter ``core_down`` and does **not** change the exit code: the
    exit contract (``0`` = no core leg DOWN, ``2`` = a core leg is DOWN) is
    unchanged, so a slow core leg leaves ``exit_code == 0`` and ``ok is True``
    while ``degraded`` becomes ``True`` and the leg is visible in ``core_slow``
    and in :func:`format_table`.  Reporting it DOWN would be the same class of
    defect as a bound manufacturing a failure.
    """
    specs = list(probes) if probes is not None else default_probes()
    legs: list[dict[str, Any]] = []
    for item in specs:
        if isinstance(item, tuple):
            name, fn = item[0], item[1]
        else:
            fn = item
            name = getattr(fn, "__name__", "probe")
        try:
            result = _invoke(fn, force)
        except Exception as exc:  # belt and braces: a probe must never fail the doctor
            result = leg(name, CORE, False, f"probe raised {_short(exc)}")
        legs.append(result)
    core_down = [l["leg"] for l in legs if l["class"] == CORE and _state_of(l) == DOWN]
    optional_down = [l["leg"] for l in legs if l["class"] == OPTIONAL and _state_of(l) == DOWN]
    core_slow = [l["leg"] for l in legs if l["class"] == CORE and _state_of(l) == SLOW]
    optional_slow = [l["leg"] for l in legs if l["class"] == OPTIONAL and _state_of(l) == SLOW]
    return {
        "ok": not core_down,
        "exit_code": 0 if not core_down else 2,
        "degraded": bool(core_slow or optional_slow),
        "checked_at": utcnow(),
        "legs": legs,
        "core_down": core_down,
        "core_slow": core_slow,
        "optional_down": optional_down,
        "optional_slow": optional_slow,
    }


LEG_WIDTH = 16
CLASS_WIDTH = 9
STATUS_WIDTH = 7


def _state_of(entry: dict[str, Any]) -> str:
    """Effective state of a leg dict: its ``state``, else UP/DOWN from ``ok``."""
    state = entry.get("state")
    if state in (UP, DOWN, SLOW):
        return str(state)
    return UP if entry.get("ok") else DOWN


def format_table(report: dict[str, Any]) -> str:
    lines = [
        f"{'LEG':<{LEG_WIDTH}} {'CLASS':<{CLASS_WIDTH}} {'STATUS':<{STATUS_WIDTH}} DETAIL",
        f"{'-' * LEG_WIDTH} {'-' * CLASS_WIDTH} {'-' * STATUS_WIDTH} {'-' * 40}",
    ]
    for entry in report["legs"]:
        state = _state_of(entry)
        status = "ok" if state == UP else ("slow" if state == SLOW else "DOWN")
        lines.append(
            f"{entry['leg']:<{LEG_WIDTH}} {entry['class']:<{CLASS_WIDTH}} "
            f"{status:<{STATUS_WIDTH}} {entry['detail']}"
        )
    core = [l for l in report["legs"] if l["class"] == CORE]
    optional = [l for l in report["legs"] if l["class"] == OPTIONAL]
    core_ok = sum(1 for l in core if _state_of(l) == UP)
    optional_ok = sum(1 for l in optional if _state_of(l) == UP)
    core_slow = list(report.get("core_slow") or [])
    slow_note = f"; slow: {', '.join(core_slow + list(report.get('optional_slow') or []))}" if (
        core_slow or report.get("optional_slow")
    ) else ""
    if report["ok"]:
        verdict = f"CORE SLOW: {', '.join(core_slow)}" if core_slow else "OK"
    else:
        verdict = f"CORE DOWN: {', '.join(report['core_down'])}"
    lines.append(
        f"core {core_ok}/{len(core)} green; optional {optional_ok}/{len(optional)} green "
        f"({', '.join(report['optional_down']) or 'none'} down{slow_note}) "
        f"-> doctor: {verdict} (exit {report['exit_code']})"
    )
    return "\n".join(lines)


def format_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True)
