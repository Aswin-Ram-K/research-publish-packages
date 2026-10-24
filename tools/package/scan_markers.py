#!/usr/bin/env python3
"""scan_markers.py -- search a shipped tree for marker families that must not appear.

Generalises the ad-hoc greps used for "does the project name / an internal unit ID / a withheld
filename appear in the shipped tree".  Every marker is a REGEX (so one engine covers case
sensitivity and shapes).  Default families:

  * the product/project name        ``encoder-crossover-190``
  * the internal product name       ``(?i)CONSONANCE``   (case-insensitive)
  * unit-ID shaped                  ``U[A-Z]+[0-9]+``

Exit 0 = no marker found; 1 = at least one marker found (printed with file:line); 2 = bad input.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pkg

DEFAULT_MARKERS = ["encoder-crossover-190", "(?i)CONSONANCE", r"U[A-Z]+[0-9]+"]


def load_markers(args):
    markers = list(DEFAULT_MARKERS) if not args.no_defaults else []
    if args.config:
        with open(args.config, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln and not ln.startswith("#"):
                    markers.append(ln)
    markers.extend(args.marker or [])
    return markers


def main():
    ap = argparse.ArgumentParser(description="marker-family scan over a package tree")
    _pkg.add_package_arg(ap)
    ap.add_argument("--marker", action="append", help="extra regex marker (repeatable)")
    ap.add_argument("--config", help="file of regex markers, one per line, # comments")
    ap.add_argument("--no-defaults", action="store_true", help="drop the built-in default families")
    a = ap.parse_args()
    tree = _pkg.resolve_package(a.package)
    markers = load_markers(a)
    if not markers:
        _pkg.die("no markers configured", 2)
    try:
        compiled = [(m, re.compile(m)) for m in markers]
    except re.error as exc:
        _pkg.die("bad marker regex: %s" % exc, 2)

    per_marker = {m: 0 for m in markers}
    hits = {m: [] for m in markers}
    for rel, full, sz in _pkg.iter_files(tree):
        try:
            txt = open(full, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(txt.splitlines(), 1):
            for m, rx in compiled:
                if rx.search(line):
                    per_marker[m] += 1
                    hits[m].append((rel, lineno, line.strip()[:120]))
    total = sum(per_marker.values())
    for m, rx in compiled:
        print("%-28s hits=%d" % (m, per_marker[m]))
        for rel, lineno, text in hits[m][:20]:
            print("  %s:%d: %s" % (rel, lineno, text))
        if len(hits[m]) > 20:
            print("  ... %d more" % (len(hits[m]) - 20))
    print("markers=%d total_hits=%d" % (len(markers), total))
    if total:
        print("MARKER SCAN: FAIL -- %d marker hit(s)" % total)
        return 1
    print("MARKER SCAN: PASS -- no configured marker appears")
    return 0


if __name__ == "__main__":
    sys.exit(main())
