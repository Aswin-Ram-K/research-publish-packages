#!/usr/bin/env python3
"""unstamped_audit.py - mechanical check on the failed-column census.

WHAT IT CHECKS (one pass, stdlib only, no network, no board writes)
  1. COVERAGE. The census covers exactly the card ids the board currently reports as
     `failed` (status=failed, not archived). A missing id fails and is named; a row for a
     card that is no longer failed also fails, because a stale census is a wrong census.
  2. NO DUPLICATES. One row per card id.
  3. verified_fail ROWS MEASURE. Every `verified_fail` row carries a non-null command and an
     exit code that is in the measuring set -- decided by `verdict_semantics.is_refusal`,
     never by a second copy of the table here.
  4. unstamped_refusal ROWS DO NOT. No `unstamped_refusal` row may claim a measuring exit.
  5. KNOWN CLASSES ONLY.

    python3 experiments/ptr-engine/tools/unstamped_audit.py --check
    # Board source resolution: --board PATH, then $UNSTAMPED_BOARD_LEDGER, then (only with
    #   UNSTAMPED_BOARD_LIVE=1) ~/.dsh/task-board/ledger-v2.json, else the census's own
    #   recorded card_ids. The default is the recorded scope on purpose: the live board
    #   changes as cards settle, so a live join is opt-in, not the default.
    # --board accepts either the Host ledger shape ({"tasks":[...]}) or {"card_ids":[...]}.

Exit 0 = clean, printed as `CENSUS OK ...`. Exit 1 = every offending card id named.
Exit 2 = the census file itself is missing/unparseable (nothing was audited).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import verdict_semantics  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, os.pardir))
DEFAULT_CENSUS = os.path.join(ROOT, "measure", "UNSTAMPED-CENSUS.json")
DEFAULT_LEDGER = os.path.expanduser("~/.dsh/task-board/ledger-v2.json")

CLASSES = {
    "verified_fail",
    "unstamped_refusal",
    "never_had_a_row",
    "blocked_by_another_card",
    "superseded_or_duplicate",
}


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def board_card_ids(path):
    """Card ids the board reports failed. Ledger shape or {card_ids:[...]}."""
    data = load_json(path)
    if isinstance(data, dict) and "card_ids" in data:
        return set(data["card_ids"])
    tasks = data.get("tasks") if isinstance(data, dict) else data
    if not isinstance(tasks, list):
        raise ValueError("unrecognised board file shape: %s" % path)
    return {
        t["id"]
        for t in tasks
        if t.get("status") == "failed" and not t.get("archivedAt")
    }


def resolve_board(args, census):
    if args.board:
        return board_card_ids(args.board), args.board
    env = os.environ.get("UNSTAMPED_BOARD_LEDGER")
    if env:
        return board_card_ids(env), env
    if os.path.exists(DEFAULT_LEDGER) and os.environ.get("UNSTAMPED_BOARD_LIVE") == "1":
        return board_card_ids(DEFAULT_LEDGER), DEFAULT_LEDGER
    return set(census.get("card_ids") or []), "census:card_ids (board revision %s)" % (
        (census.get("scope") or {}).get("board_revision", "recorded"))


def is_measuring(code):
    """True only for a code the partition says measures. Unknown -> False, never a guess."""
    if code is None:
        return False
    try:
        return not verdict_semantics.is_refusal(code)
    except verdict_semantics.UnclassifiedExitCode:
        return False


def check(census, board_ids):
    problems = []
    rows = census.get("rows")
    if not isinstance(rows, list):
        return ["census has no `rows` list"]
    seen = {}
    for row in rows:
        cid = row.get("card_id")
        if cid in seen:
            problems.append("%s: duplicate row" % cid)
        seen[cid] = row
        cls = row.get("classification")
        if cls not in CLASSES:
            problems.append("%s: unknown classification %r" % (cid, cls))
            continue
        code = row.get("exit_code")
        if cls == "verified_fail":
            if row.get("command") is None:
                problems.append("%s: verified_fail with a null command" % cid)
            if not is_measuring(code):
                problems.append(
                    "%s: verified_fail claims a non-measuring exit %r" % (cid, code)
                )
        elif cls == "unstamped_refusal":
            if is_measuring(code):
                problems.append(
                    "%s: unstamped_refusal claims a measuring exit %r" % (cid, code)
                )
        elif cls in ("never_had_a_row", "superseded_or_duplicate"):
            if cls == "never_had_a_row" and row.get("command") is not None:
                problems.append("%s: never_had_a_row but carries a command" % cid)
    missing = sorted(board_ids - set(seen))
    extra = sorted(set(seen) - board_ids)
    problems += ["%s: failed card missing from the census" % cid for cid in missing]
    problems += ["%s: census row for a card the board no longer reports failed" % cid for cid in extra]
    summary = dict(census.get("summary") or {})
    counts = summary.get("counts") or {}
    if counts and sum(int(v) for v in counts.values()) != len(rows):
        problems.append("summary counts sum to %d but there are %d rows"
                        % (sum(int(v) for v in counts.values()), len(rows)))
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="audit the failed-column census")
    ap.add_argument("--check", action="store_true", help="run the mechanical checks")
    ap.add_argument("--census", default=DEFAULT_CENSUS)
    ap.add_argument("--board", default=None, help="board ledger or {card_ids:[...]} snapshot")
    args = ap.parse_args(argv)
    if not args.check:
        ap.print_help()
        return 2
    try:
        census = load_json(args.census)
    except (OSError, ValueError) as exc:
        print("CENSUS UNREADABLE: %s: %s" % (args.census, exc))
        return 2
    board_ids, source = resolve_board(args, census)
    problems = check(census, board_ids)
    if problems:
        for p in problems:
            print("FAIL %s" % p)
        print("CENSUS FAIL: %d problem(s) against %s" % (len(problems), source))
        return 1
    rows = census["rows"]
    counts = census.get("summary", {}).get("counts", {})
    print("CENSUS OK %d rows against %s; %s" % (
        len(rows), source,
        ", ".join("%s=%s" % (k, counts[k]) for k in sorted(counts)) or "no counts"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
