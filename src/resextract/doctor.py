"""Dependency prober: classify each leg as ``core`` or ``optional``.

Exit contract: **0** when every core leg is green (optional legs may be down),
**2** when any core leg is down.  No probe ever raises: a failure is data
(``ok=False`` + a human detail string), never an exception.

Timeouts: 5 s per leg, 30 s for the Occamy completion probe.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable

import httpx

CORE = "core"
OPTIONAL = "optional"

HTTP_TIMEOUT = 5.0
OCCAMY_COMPLETION_TIMEOUT = 30.0
DASHBOARD_PORT = 8901

DEFAULT_ENDPOINTS: dict[str, str] = {
    "occamy_base_url": "http://192.168.2.168:8012/v1",
    "occamy_model": "occamy-1.0",
    "searxng_base_url": "http://127.0.0.1:8080",
    "crawl_scrape_base_url": "http://127.0.0.1:8891",
    "docling_bridge_base_url": "http://127.0.0.1:8893",
}

RENDERERS = ("pdflatex", "pandoc", "tectonic")


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


def leg(leg_name: str, klass: str, ok: bool, detail: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"leg": leg_name, "class": klass, "ok": bool(ok), "detail": detail}
    out.update(extra)
    return out


def _short(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    return text[:300]


# --------------------------------------------------------------------------- #
# Probes (each returns a leg dict and never raises)
# --------------------------------------------------------------------------- #


def probe_occamy() -> dict[str, Any]:
    """GET /v1/models, then a max_tokens=8 completion with thinking disabled."""
    ep = endpoints()
    base = ep["occamy_base_url"].rstrip("/")
    wanted = ep.get("occamy_model")
    started = time.monotonic()
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            models = client.get(f"{base}/models")
        if models.status_code != 200:
            return leg("Occamy", CORE, False, f"GET /models -> HTTP {models.status_code}")
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
        return leg(
            "Occamy",
            CORE,
            ok,
            detail,
            model=model_id,
            models=ids,
            http_status=completion.status_code,
            latency_ms=ms,
        )
    except Exception as exc:
        return leg("Occamy", CORE, False, _short(exc))


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


def run_doctor(
    probes: Iterable[tuple[str, Callable[[], dict[str, Any]]] | Callable[[], dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Run every probe; never raises.  Returns the report with its exit code.

    ``probes`` accepts ``(leg_name, callable)`` pairs (the default, so a probe
    that raises can still be named) or bare callables.
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
            result = fn()
        except Exception as exc:  # belt and braces: a probe must never fail the doctor
            result = leg(name, CORE, False, f"probe raised {_short(exc)}")
        legs.append(result)
    core_down = [l["leg"] for l in legs if l["class"] == CORE and not l["ok"]]
    optional_down = [l["leg"] for l in legs if l["class"] == OPTIONAL and not l["ok"]]
    return {
        "ok": not core_down,
        "exit_code": 0 if not core_down else 2,
        "checked_at": utcnow(),
        "legs": legs,
        "core_down": core_down,
        "optional_down": optional_down,
    }


LEG_WIDTH = 16
CLASS_WIDTH = 9
STATUS_WIDTH = 7


def format_table(report: dict[str, Any]) -> str:
    lines = [
        f"{'LEG':<{LEG_WIDTH}} {'CLASS':<{CLASS_WIDTH}} {'STATUS':<{STATUS_WIDTH}} DETAIL",
        f"{'-' * LEG_WIDTH} {'-' * CLASS_WIDTH} {'-' * STATUS_WIDTH} {'-' * 40}",
    ]
    for entry in report["legs"]:
        lines.append(
            f"{entry['leg']:<{LEG_WIDTH}} {entry['class']:<{CLASS_WIDTH}} "
            f"{('ok' if entry['ok'] else 'DOWN'):<{STATUS_WIDTH}} {entry['detail']}"
        )
    core = [l for l in report["legs"] if l["class"] == CORE]
    optional = [l for l in report["legs"] if l["class"] == OPTIONAL]
    core_ok = sum(1 for l in core if l["ok"])
    optional_ok = sum(1 for l in optional if l["ok"])
    verdict = "OK" if report["ok"] else f"CORE DOWN: {', '.join(report['core_down'])}"
    lines.append(
        f"core {core_ok}/{len(core)} green; optional {optional_ok}/{len(optional)} green "
        f"({', '.join(report['optional_down']) or 'none'} down) -> doctor: {verdict} (exit {report['exit_code']})"
    )
    return "\n".join(lines)


def format_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True)
