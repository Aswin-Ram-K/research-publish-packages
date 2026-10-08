"""resextract dashboard: a local, loopback-only read surface.

* :mod:`resextract.dashboard.api` — read-only data layer over the store,
  journal, dockets, graph and doctor.
* :mod:`resextract.dashboard.app` — FastAPI app, loopback enforcement, token
  gate for control routes, and the SSE event stream.
* ``python -m resextract.dashboard --port 8901`` starts it on 127.0.0.1.

Nothing here writes to the store, the journal or the docket tree; the surface
renders exactly what is on disk and labels absent data as absent.
"""

from __future__ import annotations

from .api import DataLayer
from .app import DEFAULT_HOST, DEFAULT_PORT, check_bind_host, create_app, is_loopback

__all__ = [
    "DataLayer",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "check_bind_host",
    "create_app",
    "is_loopback",
]
