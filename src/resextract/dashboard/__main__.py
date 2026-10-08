"""``python -m resextract.dashboard`` — run uvicorn on loopback.

Refuses a non-loopback ``--host`` unless ``--allow-remote`` was given: an
explicit ``--host`` is *not* an opt-in.  U6.9 removed the inference that made
``--host 0.0.0.0`` here bind every interface (open read routes) while
``resextract serve`` refused the very same flag; the one decision is
``app.check_bind_host``.

``--token auto`` (U6.15) has exactly one meaning, the same one
``resextract serve`` gives it: on loopback it *generates* a strong random
token and prints it; on a non-loopback bind it is refused (exit 2, nothing
bound) because the token there gates every route, reads included, and must be
operator-chosen.  The literal string ``auto`` is never used as a secret.
"""

from __future__ import annotations

import argparse
import secrets
import sys

from .app import DEFAULT_HOST, DEFAULT_PORT, check_bind_host, create_app, is_loopback


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resextract-dashboard", description=__doc__)
    parser.add_argument("--host", default=None, help=f"bind host (default {DEFAULT_HOST}; loopback only)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"bind port (default {DEFAULT_PORT})")
    parser.add_argument(
        "--token",
        default=None,
        metavar="TOKEN|auto",
        help=(
            "token for every route on a non-loopback bind and for "
            "POST /api/control/* on loopback; 'auto' generates a strong token "
            "and prints it on loopback, and is REJECTED on a non-loopback bind. "
            "REQUIRED with --allow-remote"
        ),
    )
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


def _resolve_token(raw_token: str | None) -> str | None:
    """One meaning for ``auto``, mirroring ``cli._resolve_serve`` (U6.15).

    * ``auto``          -> a fresh ``secrets.token_urlsafe(32)`` secret, and the
      caller prints it; the literal string ``auto`` is never the secret
    * anything else      -> the operator's literal token, unchanged
    * ``None``/blank     -> no token (loopback only; refused off-loopback)
    """
    raw = "" if raw_token is None else str(raw_token).strip()
    if raw.lower() == "auto":
        return secrets.token_urlsafe(32)
    return raw or None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # U6.9: an explicit --host is NOT an opt-in.  `is_loopback(host)` used to be
    # folded into `allow_remote` here, which bound 0.0.0.0 (exposing the open
    # read routes) while `resextract serve` refused the same flag.  The one bind
    # decision lives in app.check_bind_host and is consulted below with the
    # user's own --allow-remote only; this entry point must never grant remote
    # binding by itself.
    host = args.host or DEFAULT_HOST
    allow_remote = bool(args.allow_remote)
    try:
        bound = check_bind_host(host, allow_remote)
    except ValueError as exc:
        print(f"refusing to start: {exc}", file=sys.stderr)
        return 2

    # U6.15: `auto` is NEVER a literal secret, and absence is not the only
    # refusal case any more.  A non-loopback bind refuses `auto` exactly as
    # `resextract serve` does (U6.12 rule (b)) because the token there gates
    # every route, reads included, and must be operator-chosen.  `""`/absent is
    # the same "remote with no secret at all" case.  Nothing is bound before
    # this returns 2.
    raw_token = "" if args.token is None else str(args.token).strip()
    if not is_loopback(bound) and raw_token.lower() in ("", "auto"):
        print(
            "refusing to start: a non-loopback bind requires an explicit --token "
            "(the token gates every route, reads included); 'auto' is not an "
            "operator-chosen secret -- pass --token <secret>",
            file=sys.stderr,
        )
        return 2
    token = _resolve_token(args.token)
    if not is_loopback(bound):
        print(
            f"WARNING: binding non-loopback host {bound!r}; every route now requires the token",
            file=sys.stderr,
        )
    elif token is not None and len(token) < 16:
        # Non-fatal on purpose: a short operator-chosen token on loopback is a
        # deliberate (if unwise) local choice, not a reason to refuse to serve.
        print(
            f"WARNING: --token {token!r} is only {len(token)} characters; a longer "
            "operator-chosen secret is safer (continuing)",
            file=sys.stderr,
        )

    app = create_app(
        args.store,
        args.journal_dir,
        args.dockets_dir,
        graph_path=args.graph,
        token=token,
        host=host,
        allow_remote=allow_remote,
    )

    if raw_token.lower() == "auto":
        # V6G asked for this: print the generated secret so `auto` is usable,
        # matching `resextract serve: control token: <token>`.
        print(f"resextract dashboard: control token: {token}", flush=True)

    import uvicorn

    uvicorn.run(app, host=bound, port=int(args.port), log_level="info", access_log=False)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
