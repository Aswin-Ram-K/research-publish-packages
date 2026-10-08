"""Dashboard HTTP surface: FastAPI app + loopback-only enforcement.

Safety contract
---------------
* The app binds loopback by default.  :func:`check_bind_host` refuses a
  non-loopback host unless ``allow_remote=True`` is passed explicitly.
* Read routes are open on loopback (this is a local read-only surface).  The
  *control* routes (``POST /api/control/*``) honour an optional one-time token.
* No directory traversal: a docket slug containing ``/`` or ``..`` is rejected
  by :func:`resextract.dashboard.api.safe_slug` and the route answers 404.
* A hard byte cap (``max_bytes``) bounds every read; the 3 MB graph is hashed
  by streaming and summarised by ``graph_stats`` (which itself streams).

``python -m resextract.dashboard`` starts uvicorn on ``127.0.0.1:8901``.
"""

from __future__ import annotations

import asyncio
import hmac
import ipaddress
import json
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from resextract import journal as journal_mod
from resextract.store import utcnow

from . import api

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8901
SSE_INTERVAL = 1.0


def is_loopback(host: str | None) -> bool:
    """True for ``localhost``, ``::1`` and any IPv4/IPv6 loopback address."""
    if not host:
        return False
    text = str(host).strip().strip("[]")
    if text.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(text).is_loopback
    except ValueError:
        return False


def check_bind_host(host: str | None, allow_remote: bool = False) -> str:
    """Return the host, or raise ``ValueError`` for a non-loopback bind.

    Reverting this guard lets ``create_app(host="0.0.0.0")`` succeed, which
    exposes the read surface to the network — the red state of
    ``test_non_loopback_host_is_refused``.
    """
    resolved = host or DEFAULT_HOST
    if is_loopback(resolved) or allow_remote:
        return resolved
    raise ValueError(
        f"refusing to bind non-loopback host {resolved!r}; "
        "pass allow_remote=True (or an explicit --host) to override"
    )


def _safe(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Call a data-layer function; an unexpected failure is data, not a 500."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - the API never 500s
        return {"error": f"{type(exc).__name__}: {exc}"}


def create_app(
    store_path: str | None = None,
    journal_dir: str | None = None,
    dockets_dir: str | None = None,
    *,
    graph_path: str | None = None,
    token: str | None = None,
    host: str | None = DEFAULT_HOST,
    allow_remote: bool = False,
    max_bytes: int = api.DEFAULT_MAX_BYTES,
) -> FastAPI:
    bound_host = check_bind_host(host, allow_remote)
    layer = api.DataLayer(
        store_path, journal_dir, dockets_dir, graph_path, max_bytes=max_bytes
    )

    app = FastAPI(title="resextract dashboard", docs_url=None, redoc_url=None)
    app.state.dashboard = {
        "layer": layer,
        "host": bound_host,
        "allow_remote": bool(allow_remote),
        "token_required": token is not None,
        "max_bytes": max_bytes,
        "store_path": str(layer.store_path),
        "journal_dir": str(layer.journal_dir),
        "dockets_dir": str(layer.dockets_dir),
        "graph_path": str(layer.graph_path),
    }

    def _authorized(request: Request) -> bool:
        if token is None:
            return True
        supplied = request.headers.get("x-dashboard-token") or ""
        auth = request.headers.get("authorization") or ""
        if not supplied and auth.lower().startswith("bearer "):
            supplied = auth[7:].strip()
        return bool(supplied) and hmac.compare_digest(supplied, token)

    # -- UI ---------------------------------------------------------------- #

    @app.get("/", response_class=HTMLResponse)
    def index() -> Any:
        page = STATIC_DIR / "index.html"
        if page.is_file():
            return FileResponse(page, media_type="text/html")
        return HTMLResponse(
            "<h1>resextract dashboard</h1><p>static/index.html is missing from the install.</p>",
            status_code=200,
        )

    # -- read routes (open on loopback) ------------------------------------ #

    @app.get("/api/status")
    def api_status() -> Any:
        return JSONResponse(_safe(layer.status))

    @app.get("/api/runs")
    def api_runs() -> Any:
        return JSONResponse(_safe(layer.runs_summary))

    @app.get("/api/reasoning")
    def api_reasoning(run_id: str | None = None, limit: int = api.DEFAULT_EVENT_LIMIT) -> Any:
        limit = max(1, min(int(limit or api.DEFAULT_EVENT_LIMIT), 5000))
        return JSONResponse(_safe(layer.reasoning_trace, run_id, limit))

    @app.get("/api/findings")
    def api_findings() -> Any:
        return JSONResponse(_safe(layer.findings))

    @app.get("/api/dockets")
    def api_dockets() -> Any:
        return JSONResponse(_safe(layer.dockets))

    @app.get("/api/dockets/{slug:path}")
    def api_docket_detail(slug: str) -> Any:
        if api.safe_slug(slug) is None:
            return JSONResponse({"error": f"invalid docket slug: {slug!r}", "slug": slug}, status_code=404)
        payload = _safe(layer.docket_detail, slug)
        if isinstance(payload, dict) and payload.get("error"):
            return JSONResponse(payload, status_code=404)
        return JSONResponse(payload)

    @app.get("/api/web-health")
    def api_web_health() -> Any:
        return JSONResponse(_safe(layer.web_research_health))

    @app.get("/api/graph")
    def api_graph() -> Any:
        return JSONResponse(_safe(layer.graph_summary))

    @app.get("/api/doctor")
    def api_doctor() -> Any:
        return JSONResponse(_safe(layer.doctor_status))

    @app.get("/api/refresh")
    def api_refresh() -> Any:
        return JSONResponse(_safe(layer.refresh_backlog))

    # -- control routes (token-gated when a token is configured) ----------- #

    @app.post("/api/control/rescan")
    def api_control_rescan(request: Request) -> Any:
        if not _authorized(request):
            return JSONResponse({"error": "control token required"}, status_code=401)
        report = _safe(layer.doctor_status, force=True)
        docket_report = _safe(layer.dockets)
        return JSONResponse(
            {
                "ok": True,
                "control": "rescan",
                "at": utcnow(),
                "doctor": {
                    "ok": report.get("ok") if isinstance(report, dict) else None,
                    "core_down": report.get("core_down") if isinstance(report, dict) else None,
                    "checked_at": report.get("checked_at") if isinstance(report, dict) else None,
                },
                "dockets": docket_report.get("count") if isinstance(docket_report, dict) else None,
            }
        )

    @app.post("/api/control/doctor")
    def api_control_doctor(request: Request) -> Any:
        if not _authorized(request):
            return JSONResponse({"error": "control token required"}, status_code=401)
        return JSONResponse(_safe(layer.doctor_status, force=True))

    # -- SSE --------------------------------------------------------------- #

    def _journal_state() -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        root = Path(layer.journal_dir)
        if not root.is_dir():
            return out
        for path in sorted(root.glob("*.jsonl")):
            try:
                stat = path.stat()
            except OSError:  # pragma: no cover
                continue
            seq = 0
            try:
                for entry in journal_mod.read(path.stem, root=root):
                    seq = int(entry.get("seq") or seq)
            except Exception:  # noqa: BLE001 - an unreadable journal is data
                seq = -1
            out[path.stem] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "last_seq": seq}
        return out

    def _docket_state() -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        root = Path(layer.dockets_dir)
        if not root.is_dir():
            return out
        for manifest in sorted(root.glob("*/MANIFEST.json")) + sorted(root.glob("*/*/MANIFEST.json")):
            try:
                stat = manifest.stat()
                slug = str(manifest.parent.relative_to(root)).replace("\\", "/")
            except (OSError, ValueError):  # pragma: no cover
                continue
            out[slug] = {"mtime_ns": stat.st_mtime_ns, "size": stat.st_size}
        return out

    async def event_stream(ticks: int | None) -> AsyncIterator[dict[str, Any]]:
        journals = _journal_state()
        dockets = _docket_state()
        doctor = layer.doctor_snapshot()
        yield {
            "event": "heartbeat",
            "data": json.dumps(
                {
                    "at": utcnow(),
                    "note": "stream open",
                    "journals": len(journals),
                    "dockets": len(dockets),
                    "doctor": doctor,
                }
            ),
        }
        count = 0
        while True:
            await asyncio.sleep(SSE_INTERVAL)
            count += 1
            current_journals = _journal_state()
            for run_id, state in current_journals.items():
                previous = journals.get(run_id)
                if previous is None:
                    yield {
                        "event": "journal",
                        "data": json.dumps(
                            {"run_id": run_id, "change": "appeared", "last_seq": state["last_seq"]}
                        ),
                    }
                elif state["size"] != previous["size"]:
                    yield {
                        "event": "journal",
                        "data": json.dumps(
                            {
                                "run_id": run_id,
                                "change": "appended",
                                "bytes_delta": state["size"] - previous["size"],
                                "last_seq": state["last_seq"],
                            }
                        ),
                    }
            for run_id in journals.keys() - current_journals.keys():
                yield {"event": "journal", "data": json.dumps({"run_id": run_id, "change": "removed"})}
            journals = current_journals

            current_dockets = _docket_state()
            for slug, state in current_dockets.items():
                if dockets.get(slug) != state:
                    yield {
                        "event": "docket",
                        "data": json.dumps(
                            {
                                "slug": slug,
                                "change": "appeared" if slug not in dockets else "changed",
                                "mtime_ns": state["mtime_ns"],
                            }
                        ),
                    }
            for slug in dockets.keys() - current_dockets.keys():
                yield {"event": "docket", "data": json.dumps({"slug": slug, "change": "removed"})}
            dockets = current_dockets

            current_doctor = layer.doctor_snapshot()
            if current_doctor != doctor:
                yield {"event": "doctor", "data": json.dumps(current_doctor)}
                doctor = current_doctor

            yield {
                "event": "heartbeat",
                "data": json.dumps(
                    {
                        "at": utcnow(),
                        "tick": count,
                        "journals": len(journals),
                        "dockets": len(dockets),
                        "doctor_checked_at": (doctor or {}).get("checked_at"),
                    }
                ),
            }
            if ticks is not None and count >= ticks:
                yield {"event": "end", "data": json.dumps({"ticks": count, "note": "tick budget reached"})}
                return

    @app.get("/api/events")
    async def api_events(ticks: int | None = None) -> Any:
        budget = None if ticks is None else max(1, min(int(ticks), 10000))
        return EventSourceResponse(
            event_stream(budget),
            ping=5,
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


__all__ = ["DEFAULT_HOST", "DEFAULT_PORT", "STATIC_DIR", "check_bind_host", "create_app", "is_loopback"]
