#!/usr/bin/env python3
"""Measure grid spend as a DELTA against a frozen, sha-pinned ledger baseline.

Added by unit LEDGER-GRID-BASELINE (2026-10-26) against v1
(`measure/LEDGER-GRID-BASELINE.json`, spent 1101).  Re-pinned by unit
LEDGER-BASELINE-REPIN (2026-10-26) to v2
(`measure/LEDGER-GRID-BASELINE-2.json`, requests 1128 / remaining 3192), which is
the DEFAULT baseline from now on: v2 was frozen after the rebuild so the 27
era-A abandoned-cell requests are pre-grid spend, not tranche spend.  v1 is not
edited and remains reachable by passing `--baseline` explicitly.

Offline by construction: it reads local JSON files and prints numbers; it opens
no socket.

Why this exists
---------------
The cumulative baseline for this batch has been ambiguous three times and each
time it moved a decision.  This tool makes the sentence "spend went from X to Y,
delta Z, against baseline file sha S" checkable in one command, and makes a
baseline that was EDITED (rather than frozen) fail loudly instead of silently
producing a plausible delta.

Arithmetic it enforces
----------------------
  delta                = spent_now - spent_before
  cross-check  (b)     = requests_raw_now - requests_raw_before   must equal delta
  remaining_now        = remaining_raw_before - delta             must equal the ledger's remaining_raw

Any break prints a `deficit:` line naming the pair that did not close and the
process exits 1.  Exit 0 means the arithmetic closes.

Rows-inventory guard
--------------------
Rows files are append-only.  Comparing the baseline's recorded rows inventory
(`per_file` or `rows_inventory`) against the current ledger's, it REFUSES when a
rows file's line count changed while its sha256 did not (a count that moved with
no sha change was never written by appending), and when a sha256 changed while
the line count did not (an in-place rewrite of a rows file).  A file that is new
since the baseline is reported, not refused: those are the tranche's own rows.

HARD RULE carried from the ledger artefact: the de-duplicated figure is
DIAGNOSTIC ONLY.  content_sha256 hashes assistant content, not request identity,
so subtracting it would understate spend.  This tool never subtracts it.

Usage
-----
  python3 experiments/ptr-engine/tools/ledger_delta.py            # v2 (default)
  python3 experiments/ptr-engine/tools/ledger_delta.py \\
      --baseline experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json   # v1, dated record
  # optional: --ledger <path> to point at a copy (used by the tests)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

DEFAULT_LEDGER = "experiments/ptr-engine/measure/REQUEST-LEDGER.json"
DEFAULT_BASELINE = "experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: str) -> dict:
    with open(path, "rb") as fh:
        return json.loads(fh.read())


def spent_of(doc: dict) -> int:
    """budget.spent, falling back to top-level requests_raw for hand-made fixtures."""
    budget = doc.get("budget") or {}
    if "spent" in budget:
        return int(budget["spent"])
    for key in ("spent", "requests_raw", "requests"):
        if key in doc:
            return int(doc[key])
    raise KeyError("no spend figure (budget.spent / requests_raw / requests) in document")


def requests_raw_of(doc: dict) -> int:
    # the frozen baseline carries the raw count under counting; a ledger carries it at top level
    counting = doc.get("counting") or {}
    for value in (counting.get("requests_raw"), doc.get("requests_raw"), (doc.get("budget") or {}).get("spent_raw")):
        if value is not None:
            return int(value)
    return spent_of(doc)


def remaining_raw_of(doc: dict) -> int:
    counting = doc.get("counting") or {}
    for value in (counting.get("remaining_raw"), doc.get("remaining_raw"), (doc.get("budget") or {}).get("remaining_raw")):
        if value is not None:
            return int(value)
    return 0


def rows_index(doc: dict) -> dict:
    """{file: (rows, sha256)} from either shape: baseline `rows_inventory` or ledger `per_file`."""
    entries = doc.get("rows_inventory") or doc.get("per_file") or []
    if isinstance(entries, dict):
        entries = entries.get("per_file") or []
    index = {}
    for entry in entries:
        name = entry.get("file")
        if not name:
            continue
        rows = entry.get("rows")
        if rows is None:
            rows = entry.get("disk_rows", entry.get("ledger_rows"))
        sha = entry.get("sha256") or entry.get("disk_sha256") or entry.get("ledger_sha256")
        index[name] = (None if rows is None else int(rows), sha)
    return index


def check_rows_inventory(base: dict, cur: dict) -> tuple[list, dict]:
    """Refuse a rows file whose line count moved without its sha moving, or vice versa."""
    before, now = rows_index(base), rows_index(cur)
    if not before or not now:
        return [], {"checked": 0, "skipped": True,
                    "why": "one side carries no rows inventory (fixture or pre-inventory artefact)"}
    problems = []
    for name, (rows_before, sha_before) in sorted(before.items()):
        if name not in now:
            problems.append(f"rows guard: {name} is in the baseline but absent from the current ledger")
            continue
        rows_now, sha_now = now[name]
        if rows_before is not None and rows_now is not None and rows_before != rows_now:
            if sha_before and sha_now and sha_before == sha_now:
                problems.append(
                    f"rows guard: {name} line count changed {rows_before} -> {rows_now} with NO sha change "
                    f"recorded ({str(sha_before)[:12]}); appending to a rows file must move its sha256"
                )
        elif rows_before is not None and rows_now is not None and rows_before == rows_now:
            if sha_before and sha_now and sha_before != sha_now:
                problems.append(
                    f"rows guard: {name} sha changed {str(sha_before)[:12]} -> {str(sha_now)[:12]} with an "
                    f"unchanged line count ({rows_before}); rows files are append-only"
                )
    new_files = sorted(set(now) - set(before))
    return problems, {"checked": len(before), "skipped": False, "new_files": new_files}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="delta of current request ledger against a frozen baseline")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE,
                    help=f"frozen baseline JSON (default: {DEFAULT_BASELINE}; pass "
                         f"experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json for the v1 dated record)")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"current ledger JSON (default: {DEFAULT_LEDGER})")
    args = ap.parse_args(argv)

    for path in (args.baseline, args.ledger):
        if not os.path.exists(path):
            print(f"error: missing file: {path}", file=sys.stderr)
            return 1
        if not os.path.isfile(path):
            print(f"error: not a file: {path}", file=sys.stderr)
            return 1

    try:
        base = load(args.baseline)
        cur = load(args.ledger)
    except json.JSONDecodeError as exc:
        print(f"error: unparseable JSON: {exc}", file=sys.stderr)
        return 1

    base_sha = sha256_file(args.baseline)
    cur_sha = sha256_file(args.ledger)

    spent_before = spent_of(base)
    spent_now = spent_of(cur)
    raw_before = requests_raw_of(base)
    raw_now = requests_raw_of(cur)
    remaining_before = remaining_raw_of(base)
    remaining_now = remaining_raw_of(cur)

    delta = spent_now - spent_before
    delta_raw = raw_now - raw_before
    remaining_expected = remaining_before - delta
    remaining_gap = remaining_expected - remaining_now

    print(f"baseline                {args.baseline}")
    print(f"baseline_sha256         {base_sha}")
    print(f"baseline_label          {base.get('label', '(unlabelled)')}")
    print(f"baseline_captured_utc   {base.get('captured_utc', base.get('frozen_at', '(unknown)'))}")
    print(f"ledger                  {args.ledger}")
    print(f"ledger_sha256           {cur_sha}")
    print(f"spent_before            {spent_before}")
    print(f"spent_now               {spent_now}")
    print(f"delta                   {delta}")
    print(f"remaining_now           {remaining_now}")
    print(f"remaining_before_minus_delta  {remaining_expected}")
    print(f"requests_raw_before     {raw_before}")
    print(f"requests_raw_now        {raw_now}")
    if base.get("diagnostic", {}).get("requests_deduplicated") is not None or base.get("requests_deduplicated") is not None:
        dedup = base.get("diagnostic", {}).get("requests_deduplicated", base.get("requests_deduplicated"))
        print(f"diagnostic_deduplicated {dedup}  (NOT subtracted; unsound request-identity rule)")

    problems = []
    if spent_now != raw_now:
        problems.append(
            f"spent_now ({spent_now}) != requests_raw_now ({raw_now}): the ledger's own spend and raw count disagree"
        )
    if spent_before != raw_before:
        problems.append(
            "baseline is internally inconsistent: budget.spent "
            f"({spent_before}) != requests_raw ({raw_before}) -- the baseline was edited, not frozen"
        )
    if delta != delta_raw:
        problems.append(
            f"delta ({delta}) != requests_raw delta ({delta_raw}): spend moved by {delta} while raw requests moved by {delta_raw}"
        )
    if remaining_now != remaining_expected:
        problems.append(
            f"remaining_raw_now ({remaining_now}) != remaining_raw_before - delta ({remaining_expected}); gap {remaining_gap}"
        )

    guard_problems, guard_info = check_rows_inventory(base, cur)
    if guard_info.get("skipped"):
        print(f"rows_guard              skipped ({guard_info.get('why')})")
    else:
        print(f"rows_guard              checked {guard_info['checked']} rows file(s); "
              f"new since baseline: {len(guard_info['new_files'])}")
        for name in guard_info["new_files"]:
            print(f"rows_guard_new          {name}")
    problems.extend(guard_problems)

    if problems:
        print(f"deficit                 {delta_raw - delta}")
        for p in problems:
            print(f"discrepancy             {p}")
        print("verdict                 FAIL (arithmetic does not close)")
        return 1

    print(f"deficit                 none")
    print("verdict                 OK (arithmetic closes: delta is a real measurement, not a re-read)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
