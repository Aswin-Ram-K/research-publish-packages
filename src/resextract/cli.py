"""``resextract`` command line entry point.

Real subcommands in this unit: ``doctor`` (dependency prober) and ``status``
(store summary, human or ``--json``).  Every pipeline subcommand is a declared
placeholder that names its owning batch and exits 3, so the dispatcher surface
is complete and honest before the stages land.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from . import __version__, doctor, store

EXIT_OK = 0
EXIT_CORE_DOWN = 2
EXIT_NOT_IMPLEMENTED = 3

# Subcommand -> owning batch/unit (plan §10).  Placeholders until those land.
PLACEHOLDERS: dict[str, str] = {
    "target": "batch 1 (U1.1)",
    "run": "batch 2 (U2.1)",
    "mine": "batch 2 (U2.1)",
    "assess": "batch 4 (U4.1)",
    "lanes": "batch 4 (U4.2)",
    "materialize": "batch 5 (U5.2)",
    "refresh": "batch 7 (U7.1)",
    "open": "batch 5 (U5.2)",
    "export": "batch 5 (U5.2)",
    "serve": "batch 6 (U6.1)",
    "watch": "batch 7 (U7.1)",
}


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

    for name, owner in PLACEHOLDERS.items():
        p = sub.add_parser(name, help=f"not implemented yet (owner: {owner})")
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
    print(f"resextract {name}: not implemented in this unit (owner: {owner})")
    return EXIT_NOT_IMPLEMENTED


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
    if command in PLACEHOLDERS:
        return _cmd_placeholder(command)
    parser.error(f"unknown command: {command}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    sys.exit(main())
