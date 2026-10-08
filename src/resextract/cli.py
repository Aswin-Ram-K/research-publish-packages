"""``resextract`` command line entry point.

Real subcommands: ``doctor`` (dependency prober), ``status`` (store summary,
human or ``--json``), ``materialize`` (lane → copied material → assembled,
verified docket, plus its ``dockets`` row), ``serve`` (the dashboard, on
loopback) and ``run`` (the whole pipeline in one bounded, honest command:
blocked stages are reported as ``blocked`` with their reason, never skipped
silently, and the exit code follows resextract.run's contract).  Every
*remaining* pipeline subcommand is a declared placeholder that names its
owning batch and exits 3, so the dispatcher surface stays complete and honest.

``serve`` is a thin dispatcher over ``resextract.dashboard.app.create_app``:
it reuses that module's ``DEFAULT_HOST``/``DEFAULT_PORT``, its
``check_bind_host`` loopback guard and its ``token`` semantics rather than
inventing a second set of behaviours.  An explicit non-loopback ``--host`` is
not itself an opt-in: ``--allow-remote`` is required.  U6.9 made that the *only*
rule -- ``resextract.dashboard.__main__`` used to infer ``allow_remote`` from an
explicit ``--host`` and bind ``0.0.0.0`` (open read routes) while this command
refused, so every entry point (this one, ``python -m resextract.cli``,
``python -m resextract``, ``python -m resextract.dashboard`` and the console
script) now reaches the single decision in ``check_bind_host``.

Exit-code vocabulary (shared with ``doctor``):

* ``0`` success;
* ``2`` a hard dependency is unavailable (target missing, store unreadable, or
  the target is not quiescent so no honest snapshot can be taken);
* ``3`` the request is not implementable as asked — lane not found, or a lane
  that refuses to materialize because nothing it cites can be verified.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path
from typing import Sequence

from . import __version__, doctor, store

EXIT_OK = 0
EXIT_DEGRADED = 1
EXIT_CORE_DOWN = 2
EXIT_NOT_IMPLEMENTED = 3

# Subcommand -> owning *batch* (orchestration/STATUS.md, plan §10).  Owners are
# named by batch, never by a live unit id: a unit id names one agent that will
# finish and be superseded, so it cannot tell a reader what is still pending.
# This dict is the single source of truth: both the placeholder message and
# tests/test_cli.py read it.  ``materialize`` was the 11th placeholder (U5.3
# implemented it), ``serve`` was the 10th (U6.2 implemented it) and ``run`` was
# the 9th (U8.3 implemented it), so the placeholder set is now the 8 entries
# below.
PLACEHOLDERS: dict[str, str] = {
    "target": "batch 1 (KG knowledge graph)",
    "mine": "batch 2 (mining)",
    "assess": "batch 4 (assessment)",
    "lanes": "batch 4 (lanes/classifier)",
    "open": "batch 5 (docket)",
    "export": "batch 5 (docket)",
    "refresh": "batch 7 (continuity)",
    "watch": "batch 7 (continuity)",
}

#: Subcommands that actually run (as opposed to the placeholders above).
#: tests/test_cli.py pins both this set and the placeholder set, so a stage
#: cannot silently regress to a placeholder (or the reverse).
IMPLEMENTED: frozenset[str] = frozenset({"doctor", "status", "materialize", "serve", "run"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resextract",
        description="Bounded research extractor over graphify graphs.",
    )
    parser.add_argument("--version", action="version", version=f"resextract {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_doctor = sub.add_parser("doctor", help="probe every dependency and classify core/optional")
    p_doctor.add_argument("--json", action="store_true", help="emit the report as JSON")

    p_status = sub.add_parser("status", help="show store summary (lanes, dockets, last run)")
    p_status.add_argument("--json", action="store_true", help="emit the summary as JSON")

    p_mat = sub.add_parser(
        "materialize",
        help="copy a lane's cited material and assemble + verify its docket",
    )
    p_mat.add_argument(
        "--target",
        required=True,
        metavar="SLUG",
        help="target slug (targets table, else config/targets.toml)",
    )
    lane_source = p_mat.add_mutually_exclusive_group()
    lane_source.add_argument("--lane", metavar="SLUG", help="lane slug from the `lanes` table")
    lane_source.add_argument(
        "--lane-file", metavar="PATH", help="LaneSpec JSON (curated/escape-hatch lane)"
    )
    p_mat.add_argument(
        "--docket-root", default="dockets", metavar="DIR", help="docket root (default: dockets)"
    )
    p_mat.add_argument(
        "--source",
        dest="source_mode",
        choices=("commit", "working-tree"),
        default="commit",
        metavar="MODE",
        help=(
            "commit (default): pin every material file to the recorded commit and "
            "record its blob sha; working-tree: explicit opt-out that records "
            "itself as unpinned"
        ),
    )
    p_mat.add_argument(
        "--window",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="quiescence window observed before copying (default: 5)",
    )
    p_mat.add_argument(
        "--allow-active",
        action="store_true",
        help="measure a target that is moving on purpose (records the writer signal)",
    )
    p_mat.add_argument("--dry-run", action="store_true", help="plan only — write nothing")
    p_mat.add_argument("--json", action="store_true", help="emit the result as JSON")

    # Defaults and semantics mirror resextract.dashboard.__main__ (which in turn
    # passes them to create_app); only the non-loopback opt-in is stricter.
    p_serve = sub.add_parser(
        "serve",
        help="run the web dashboard (loopback only unless --allow-remote)",
    )
    p_serve.add_argument(
        "--host",
        default=None,
        metavar="HOST",
        help="bind host (default: dashboard 127.0.0.1; loopback unless --allow-remote)",
    )
    p_serve.add_argument(
        "--port",
        type=int,
        default=None,
        metavar="PORT",
        help="bind port (default: dashboard 8901)",
    )
    p_serve.add_argument(
        "--token",
        default="auto",
        metavar="TOKEN|auto",
        help=(
            "token for every route on a non-loopback bind and for "
            "POST /api/control/* on loopback; 'auto' (default) generates one and "
            "prints it.  A non-loopback bind REJECTS 'auto': pass an explicit "
            "secret the operator chose"
        ),
    )
    p_serve.add_argument(
        "--no-browser",
        action="store_true",
        help="accepted for compatibility — the dashboard never opens a browser itself",
    )
    p_serve.add_argument(
        "--allow-remote",
        action="store_true",
        help="explicitly permit a non-loopback bind (dangerous: exposes research material)",
    )
    p_serve.add_argument(
        "--docket-root",
        default=None,
        metavar="PATH",
        help=(
            "directory to serve dockets from (default: dockets); a relative path "
            "is resolved against the current working directory and the resolved "
            "absolute path is printed at startup.  Docket containment stays "
            "relative to this root, so the flag never widens what can be read."
        ),
    )

    p_run = sub.add_parser(
        "run",
        help="chain the pipeline into one bounded, honest run (blocked stages are reported)",
    )
    p_run.add_argument(
        "--target",
        required=True,
        metavar="SLUG",
        help="target slug (targets table, else config/targets.toml)",
    )
    p_run.add_argument(
        "--stages",
        default=None,
        metavar="A,B",
        help=(
            "comma-separated subset of the stages to run "
            "(default: graph,staging,mine,claims,assess,lanes,materialize,refresh)"
        ),
    )
    p_run.add_argument(
        "--window",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="quiescence window observed for the sealed window (default: 5)",
    )
    p_run.add_argument(
        "--allow-active",
        action="store_true",
        help="measure a target that is moving on purpose (the seal is still re-checked)",
    )
    p_run.add_argument(
        "--allow-replay",
        action="store_true",
        help=(
            "materialize lanes whose candidates are NOT model-produced; the reason "
            "then says the docket is replay-derived (a degradation, not a success)"
        ),
    )
    p_run.add_argument("--dry-run", action="store_true", help="preflight + plan only — write nothing")
    p_run.add_argument("--json", action="store_true", help="emit the run report as JSON")

    for name, owner in PLACEHOLDERS.items():
        p = sub.add_parser(name, help=f"not implemented yet — planned for {owner}")
        p.add_argument("rest", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)

    return parser


def _cmd_doctor(args: argparse.Namespace) -> int:
    report = doctor.run_doctor()
    if args.json:
        print(doctor.format_json(report))
    else:
        print(doctor.format_table(report))
    return int(report["exit_code"])


def _cmd_status(args: argparse.Namespace) -> int:
    db = store.default_db_path()
    if not db.exists():
        store.init_db(db)
    con = store.connect(db)
    try:
        summary = store.status_json(con)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True, default=str))
        else:
            print(store.status_text(con))
    finally:
        con.close()
    return EXIT_OK


def _cmd_placeholder(name: str) -> int:
    owner = PLACEHOLDERS.get(name, "unassigned")
    print(f"resextract {name}: not implemented yet — planned for {owner}")
    return EXIT_NOT_IMPLEMENTED


def _fmt_plan(result, as_json: bool) -> str:
    if as_json:
        return json.dumps(result.to_dict(), indent=2, sort_keys=True, default=str)
    lines = [
        f"resextract materialize: {'DRY RUN — nothing written' if result.dry_run else 'done'}",
        f"  docket     : {result.docket_dir}",
        f"  target HEAD: {result.head_sha or '(unknown)'} ({result.head_sha_source or 'n/a'})",
    ]
    if result.head_sha_end and result.head_sha_end != result.head_sha:
        lines.append(f"  HEAD end   : {result.head_sha_end}")
    lines.append(
        f"  source     : {result.source_mode}"
        f"{' (commit-pinned)' if result.pinned else ' (NOT pinned)'}"
    )
    if result.writer_signal is not None:
        lines.append(
            f"  writer     : {result.writer_signal.verdict} "
            f"(HEAD {str(result.writer_signal.head_before or '?')[:8]} -> "
            f"{str(result.writer_signal.head_after or '?')[:8]}, "
            f"{result.writer_signal.files_touched_in_window} tracked file(s) touched)"
        )
    if result.window_sealed is not None:
        lines.append(
            f"  window     : {'sealed' if result.window_sealed else 'NOT SEALED — needs_rework'}"
        )
    if result.plan is not None:
        lines.append(
            f"  plan       : {len(result.plan.to_copy)} to copy, "
            f"{len(result.plan.to_link)} to link, {len(result.plan.refused)} refused, "
            f"{len(result.plan.missing)} missing, {result.plan.total_bytes} bytes"
        )
    counts = result.counts()
    lines.append(
        "  copies     : "
        + ", ".join(f"{k}={v}" for k, v in counts.items())
    )
    if result.unpinned_material:
        lines.append(f"  UNPINNED   : {len(result.unpinned_material)} file(s)")
        for entry in result.unpinned_material:
            lines.append(
                f"    - {entry.get('dest')} ({entry.get('reason')}, "
                f"sha256 {str(entry.get('sha256') or '')[:8]}, "
                f"mtime {entry.get('mtime') or 'unknown'})"
            )
    if result.unresolved_refs:
        lines.append(f"  unresolved : {len(result.unresolved_refs)}")
        for item in result.unresolved_refs:
            lines.append(f"    - {item}")
    if result.verification is not None:
        lines.append(f"  verify     : {'ok' if result.verification.ok else 'FAILED'}")
    if not result.dry_run:
        lines.append(f"  files      : {len(result.files_written)}")
        lines.append(f"  dockets row: {result.dockets_row_id}")
    for note in result.notes:
        lines.append(f"  note       : {note}")
    return "\n".join(lines)


def _cmd_materialize(args: argparse.Namespace) -> int:
    # Imported lazily so a broken optional dependency cannot break `doctor`.
    from .docket import materialize as mat

    db = store.default_db_path()
    if not db.exists():
        store.init_db(db)
    try:
        con = store.connect(db)
    except Exception as exc:  # noqa: BLE001 - the store is a hard dependency
        print(f"resextract materialize: store unreadable at {db}: {exc}")
        return EXIT_CORE_DOWN

    try:
        target_root = mat.resolve_target_root(args.target, con=con)
        if not target_root:
            print(
                f"resextract materialize: target {args.target!r} not found "
                "(no targets row, no config/targets.toml entry, not a directory)"
            )
            return EXIT_CORE_DOWN

        if args.lane_file:
            try:
                lane = mat.LaneSpec.from_json(args.lane_file)
            except Exception as exc:  # noqa: BLE001 - a bad spec is not materializable
                print(f"resextract materialize: cannot load lane spec {args.lane_file!r}: {exc}")
                return EXIT_NOT_IMPLEMENTED
            if not lane.target_slug:
                lane.target_slug = args.target
        elif args.lane:
            lane_row = store.get_lane_by_slug(con, args.target, args.lane)
            if lane_row is None:
                print(f"resextract materialize: lane {args.lane!r} not found for target {args.target!r}")
                return EXIT_NOT_IMPLEMENTED
            # Absent a lane↔candidate join table, the mined candidates are the
            # members; U4.2's lane builder will narrow this when it lands.
            candidate_rows = [
                dict(row)
                for row in con.execute(
                    "SELECT * FROM candidates WHERE state='mined' ORDER BY id"
                ).fetchall()
            ]
            lane = mat.LaneSpec.from_store(lane_row, candidate_rows)
            if not lane.target_slug:
                lane.target_slug = args.target
        else:
            print("resextract materialize: one of --lane or --lane-file is required")
            return EXIT_NOT_IMPLEMENTED

        try:
            result = mat.materialize_lane(
                lane,
                target_root=target_root,
                docket_root=args.docket_root,
                dry_run=bool(args.dry_run),
                db_path=db,
                source_mode=str(getattr(args, "source_mode", "commit")),
                window_s=float(getattr(args, "window", 5.0)),
                allow_active=bool(getattr(args, "allow_active", False)),
            )
        except mat.TargetBusyError as exc:
            # A moving target cannot be measured honestly; say so and stop.
            print(f"resextract materialize: target is not quiescent — {exc}")
            print("  (re-run when the target is quiet, or pass --allow-active to record a moving target)")
            return EXIT_CORE_DOWN
        except mat.MaterializeRefused as exc:
            print(f"resextract materialize: refused — {len(exc.reasons)} reason(s)")
            for reason in exc.reasons:
                print(f"  - {reason}")
            return EXIT_NOT_IMPLEMENTED
        except mat.MaterializeError as exc:
            print(f"resextract materialize: {exc}")
            return EXIT_CORE_DOWN
        except FileNotFoundError as exc:
            print(f"resextract materialize: target dependency missing: {exc}")
            return EXIT_CORE_DOWN
    finally:
        con.close()

    print(_fmt_plan(result, bool(args.json)))
    return EXIT_OK


def _resolve_serve(args: argparse.Namespace) -> tuple[str, int, str | None]:
    """Resolve ``serve``'s bind host/port/token using the dashboard's rules.

    Raises ``ValueError`` for a non-loopback bind without ``--allow-remote``,
    exactly as ``dashboard.app.check_bind_host`` does when called with
    ``allow_remote=False``.
    """
    # Imported lazily so a missing optional web dependency cannot break
    # `doctor`, `status` or `materialize`.
    from .dashboard.app import DEFAULT_HOST, DEFAULT_PORT, check_bind_host, is_loopback

    host = args.host if args.host else DEFAULT_HOST
    allow_remote = bool(getattr(args, "allow_remote", False))
    bound = check_bind_host(host, allow_remote)
    port = int(args.port) if args.port else int(DEFAULT_PORT)
    token = getattr(args, "token", "auto")
    raw = "" if token is None else str(token).strip()
    # U6.12 rule (b): `--token auto` is *usable* (the generated secret is printed
    # to the operator's terminal) but it is not an operator CHOICE, and a remote
    # bind must exist because the operator decided a secret should gate it.  So a
    # non-loopback bind requires an explicit --token; `auto` (and a missing
    # token) is refused here, before anything binds.
    if not is_loopback(bound) and raw.lower() in ("", "auto"):
        raise ValueError(
            f"a non-loopback bind ({bound!r}) requires an explicit --token; "
            "'--token auto' is not an operator-chosen secret -- pass --token <secret>"
        )
    token = secrets.token_urlsafe(32) if raw.lower() == "auto" else token
    return bound, port, token


def _resolve_docket_root(raw: str | None) -> Path | None:
    """Resolve ``serve --docket-root`` to an absolute directory path.

    ``None`` (the flag was not given) returns ``None`` so the dashboard's own
    default root is used unchanged.  A relative path resolves against the
    current working directory.  A path that does not exist, or that is not a
    directory, raises ``ValueError`` — a bad root is a hard configuration
    failure (exit 2), never a silently empty dashboard.
    """
    if raw is None:
        return None
    candidate = Path(raw).expanduser()
    try:
        resolved = candidate.resolve()
    except OSError as exc:  # pragma: no cover - defensive
        raise ValueError(f"cannot resolve docket root {raw!r}: {exc}") from exc
    if not resolved.exists():
        raise ValueError(f"docket root does not exist: {resolved}")
    if not resolved.is_dir():
        raise ValueError(f"docket root is not a directory: {resolved}")
    return resolved


def _cmd_serve(args: argparse.Namespace) -> int:
    try:
        bound, port, token = _resolve_serve(args)
        docket_root = _resolve_docket_root(getattr(args, "docket_root", None))
    except ValueError as exc:
        # A refused bind or an unusable docket root is a hard configuration
        # failure, not a placeholder.
        print(f"resextract serve: refusing to start: {exc}")
        return EXIT_CORE_DOWN

    from .dashboard.app import create_app, is_loopback

    if not is_loopback(bound):
        print(
            f"resextract serve: WARNING binding non-loopback host {bound!r}; "
            "this exposes the dashboard",
            file=sys.stderr,
        )
    app = create_app(
        dockets_dir=str(docket_root) if docket_root is not None else None,
        token=token,
        host=bound,
        allow_remote=bool(getattr(args, "allow_remote", False)),
    )

    url = f"http://{bound}:{port}"
    effective_root = docket_root if docket_root is not None else Path("dockets").resolve()
    print(f"resextract serve: {url}")
    print(f"resextract serve: docket root: {effective_root}")
    print("resextract serve: read routes are open on loopback; POST /api/control/* needs the token")
    if token is not None:
        print(f"resextract serve: control token: {token}")
    print("resextract serve: press Ctrl-C to stop", flush=True)

    import uvicorn

    try:
        uvicorn.run(app, host=bound, port=port, log_level="info", access_log=False)
    except OSError as exc:
        print(f"resextract serve: cannot bind {bound}:{port}: {exc}")
        return EXIT_CORE_DOWN
    except SystemExit as exc:  # uvicorn sys.exit(1)s on a failed bind
        code = exc.code if isinstance(exc.code, int) else 1
        if code:
            print(f"resextract serve: server exited with code {code} (is port {port} already in use?)")
            return EXIT_CORE_DOWN
    return EXIT_OK


def _cmd_run(args: argparse.Namespace) -> int:
    # Imported lazily so a broken optional dependency cannot break `doctor`.
    from .run import STAGE_ORDER, format_report, run_pipeline

    stages = None
    raw = getattr(args, "stages", None)
    if raw:
        stages = [part.strip() for part in str(raw).split(",") if part.strip()]
        unknown = [s for s in stages if s not in STAGE_ORDER]
        if unknown:
            print(
                f"resextract run: unknown stage(s) {', '.join(unknown)}; "
                f"known stages: {', '.join(STAGE_ORDER)}"
            )
            return EXIT_NOT_IMPLEMENTED
    try:
        report = run_pipeline(
            args.target,
            stages=stages,
            dry_run=bool(args.dry_run),
            allow_active=bool(args.allow_active),
            allow_replay=bool(args.allow_replay),
            window_s=float(getattr(args, "window", 5.0)),
        )
    except ValueError as exc:
        print(f"resextract run: {exc}")
        return EXIT_NOT_IMPLEMENTED

    print(format_report(report, bool(args.json)))
    if report.exit_code == EXIT_DEGRADED:
        print(
            "resextract run: completed WITH DEGRADATIONS — the stage table above says "
            "what was blocked, skipped or replay-derived",
            file=sys.stderr,
        )
    return int(report.exit_code)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = getattr(args, "command", None)
    if command is None:
        parser.print_help()
        return EXIT_OK
    if command == "doctor":
        return _cmd_doctor(args)
    if command == "status":
        return _cmd_status(args)
    if command == "materialize":
        return _cmd_materialize(args)
    if command == "serve":
        return _cmd_serve(args)
    if command == "run":
        return _cmd_run(args)
    if command in PLACEHOLDERS:
        return _cmd_placeholder(command)
    parser.error(f"unknown command: {command}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    sys.exit(main())
