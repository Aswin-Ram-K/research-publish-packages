"""``python -m resextract.dashboard`` — run uvicorn on loopback.

Refuses a non-loopback ``--host`` unless it was passed explicitly (the explicit
flag *is* the opt-in) and never starts anything without the caller asking.
"""

from __future__ import annotations

import argparse
import sys

from .app import DEFAULT_HOST, DEFAULT_PORT, check_bind_host, create_app, is_loopback


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resextract-dashboard", description=__doc__)
    parser.add_argument("--host", default=None, help=f"bind host (default {DEFAULT_HOST}; loopback only)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"bind port (default {DEFAULT_PORT})")
    parser.add_argument("--token", default=None, help="optional one-time token for POST /api/control/* routes")
    parser.add_argument("--store", default=None, help="path to state.sqlite")
    parser.add_argument("--journal-dir", default=None, help="path to the journal directory")
    parser.add_argument("--dockets-dir", default=None, help="path to the dockets directory")
    parser.add_argument("--graph", default=None, help="path to graph.json")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="explicitly permit a non-loopback bind (dangerous: exposes research material)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    explicit_host = args.host is not None
    host = args.host or DEFAULT_HOST
    allow_remote = args.allow_remote or (explicit_host and not is_loopback(host))
    try:
        bound = check_bind_host(host, allow_remote)
    except ValueError as exc:
        print(f"refusing to start: {exc}", file=sys.stderr)
        return 2
    if not is_loopback(bound):
        print(f"WARNING: binding non-loopback host {bound!r}; this exposes the dashboard", file=sys.stderr)

    app = create_app(
        args.store,
        args.journal_dir,
        args.dockets_dir,
        graph_path=args.graph,
        token=args.token,
        host=host,
        allow_remote=allow_remote,
    )

    import uvicorn

    uvicorn.run(app, host=bound, port=int(args.port), log_level="info", access_log=False)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
