#!/usr/bin/env python3
"""unit_journal.py — append-only per-unit work journal.

A journal is a JSONL file at ``orchestration/journals/<UNIT>.jsonl``. One record is
appended per step, as the work happens, and nothing is ever rewritten: a kill can
destroy at most the single line being written, never the trail before it.

Usage (stdlib only, no third-party dependency):

  python3 tools/unit_journal.py init   --unit U --card C --bound N --paths a b c
  python3 tools/unit_journal.py log    --unit U --kind artifact --path docs/X.md --bytes 4021 --note "s3"
  python3 tools/unit_journal.py log    --unit U --kind evidence --command "pytest" --exit 0 --out "12 passed"
  python3 tools/unit_journal.py log    --unit U --kind next --text "run corpus audit, then handoff"
  python3 tools/unit_journal.py status --unit U
  python3 tools/unit_journal.py resume --unit U

``status`` and ``resume`` are strictly read-only. ``status`` exits 1 if and only if a
logged artifact is missing (torn/garbage lines are tolerated, never fatal).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

KINDS = ("artifact", "evidence", "next", "assumption", "blocker")
EXIT_MISSING_ARTIFACT = 1
EXIT_USAGE = 2


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def journal_path(root: str, unit: str) -> str:
    return os.path.join(root, "orchestration", "journals", unit + ".jsonl")


def _read_records(path: str) -> tuple[list[dict], int]:
    """Return (parseable records, torn/unparseable line count).

    A torn final line is EXPECTED after a kill, so it is counted, not raised.
    """
    records: list[dict] = []
    torn = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    torn += 1
                    continue
                if isinstance(obj, dict):
                    records.append(obj)
                else:
                    torn += 1
    except FileNotFoundError:
        raise SystemExit("no journal: %s" % path)
    return records, torn


def _append(path: str, record: dict) -> None:
    """The ONLY write path in this tool: one line, appended, fsynced."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=False) + "\n"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


def _last_step(records: list[dict]) -> int:
    steps = [r.get("step") for r in records if isinstance(r.get("step"), int)]
    return max(steps) if steps else -1


def cmd_init(args) -> int:
    path = journal_path(args.root, args.unit)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        sys.stderr.write("journal already exists (append-only, refusing to rewrite): %s\n" % path)
        return EXIT_USAGE
    _append(path, {
        "t": now(), "step": 0, "kind": "header",
        "unit": args.unit, "card": args.card, "bound": args.bound,
        "paths": args.paths or [],
    })
    print("init %s -> %s" % (args.unit, path))
    return 0


def cmd_log(args) -> int:
    path = journal_path(args.root, args.unit)
    records, _ = _read_records(path)
    record = {"t": now(), "step": _last_step(records) + 1, "kind": args.kind}
    if args.kind == "artifact":
        if not args.path:
            sys.stderr.write("artifact record needs --path\n")
            return EXIT_USAGE
        full = args.path if os.path.isabs(args.path) else os.path.join(args.root, args.path)
        record["path"] = args.path
        record["bytes"] = args.bytes if args.bytes is not None else (
            os.path.getsize(full) if os.path.exists(full) else 0)
        if args.note:
            record["note"] = args.note
    elif args.kind == "evidence":
        if not args.command:
            sys.stderr.write("evidence record needs --command\n")
            return EXIT_USAGE
        record["command"] = args.command
        record["exit"] = args.exit
        record["out"] = args.out or ""
    else:  # next | assumption | blocker
        if not args.text:
            sys.stderr.write("%s record needs --text\n" % args.kind)
            return EXIT_USAGE
        record["text"] = args.text
        if args.note:
            record["note"] = args.note
    _append(path, record)
    print("logged step %d %s" % (record["step"], args.kind))
    return 0


def _artifact_state(records: list[dict], root: str) -> tuple[list, list]:
    existing, missing = [], []
    seen = set()
    for r in records:
        if r.get("kind") != "artifact":
            continue
        p = r.get("path")
        if not p or p in seen:
            continue
        seen.add(p)
        full = p if os.path.isabs(p) else os.path.join(root, p)
        if os.path.exists(full):
            existing.append((p, os.path.getsize(full)))
        else:
            missing.append(p)
    return existing, missing


def _last_note(records: list[dict], kind: str):
    for r in reversed(records):
        if r.get("kind") == kind:
            return r
    return None


def cmd_status(args) -> int:
    path = journal_path(args.root, args.unit)
    records, torn = _read_records(path)
    existing, missing = _artifact_state(records, args.root)
    print("journal: %s" % path)
    print("records: %d  last_step: %s  torn_lines: %d" % (len(records), _last_step(records), torn))
    print("artifacts exist  (%d):" % len(existing))
    for p, size in existing:
        print("  OK      %s  %d bytes" % (p, size))
    print("artifacts MISSING (%d):" % len(missing))
    for p in missing:
        print("  MISSING %s" % p)
    nxt = _last_note(records, "next")
    print("last next: %s" % (nxt.get("text") if nxt else "(none)"))
    blk = _last_note(records, "blocker")
    if blk:
        print("last blocker: %s" % blk.get("text"))
    if missing:
        print("MISSING-ARTIFACT: " + ", ".join(missing))
        return EXIT_MISSING_ARTIFACT
    return 0


def cmd_resume(args) -> int:
    path = journal_path(args.root, args.unit)
    records, torn = _read_records(path)
    header = records[0] if records and records[0].get("kind") == "header" else {}
    existing, missing = _artifact_state(records, args.root)
    ev = _last_note(records, "evidence")
    nxt = _last_note(records, "next")
    blk = _last_note(records, "blocker")
    unit = header.get("unit", args.unit)

    parts = ["RESUME %s (card %s, bound %s): %d journal records, last step %s."
             % (unit, header.get("card", "?"), header.get("bound", "?"),
                len(records), _last_step(records))]
    if existing:
        parts.append("Artifacts already on disk (%d): %s."
                     % (len(existing),
                        "; ".join("%s (%d bytes)" % (p, s) for p, s in existing)))
    else:
        parts.append("No logged artifact is on disk yet.")
    if missing:
        parts.append("Logged but NOT on disk (%d) — re-create or record a blocker: %s."
                     % (len(missing), ", ".join(missing)))
    if ev:
        parts.append("Last evidence: `%s` -> exit %s: %s"
                     % (ev.get("command", "?"), ev.get("exit", "?"),
                        (ev.get("out") or "")[:300]))
    if blk:
        parts.append("Open blocker: %s" % blk.get("text"))
    if nxt:
        parts.append("Last stated next action: %s" % nxt.get("text"))
    else:
        parts.append("No next action was logged.")
    parts.append("Do not rewrite this journal; append to it. Torn lines (%d) are ignored."
                 % torn)
    print(" ".join(parts))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="append-only unit work journal")
    p.add_argument("--root", default=os.getcwd(),
                   help="workspace root containing orchestration/ (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init")
    i.add_argument("--unit", required=True)
    i.add_argument("--card", default="")
    i.add_argument("--bound", default="")
    i.add_argument("--paths", nargs="*", default=[])
    i.set_defaults(func=cmd_init)

    l = sub.add_parser("log")
    l.add_argument("--unit", required=True)
    l.add_argument("--kind", required=True, choices=KINDS)
    l.add_argument("--path")
    l.add_argument("--bytes", type=int)
    l.add_argument("--command")
    l.add_argument("--exit", type=int, default=None)
    l.add_argument("--out")
    l.add_argument("--text")
    l.add_argument("--note")
    l.set_defaults(func=cmd_log)

    s = sub.add_parser("status")
    s.add_argument("--unit", required=True)
    s.set_defaults(func=cmd_status)

    r = sub.add_parser("resume")
    r.add_argument("--unit", required=True)
    r.set_defaults(func=cmd_resume)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
