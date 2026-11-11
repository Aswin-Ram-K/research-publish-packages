#!/usr/bin/env python3
"""repin_harness.py - write the replay harness pin from the tree, with history kept.

WHY THIS EXISTS.  `measure/HARNESS-PIN.json` had no writer: it was edited by hand, and it
went stale twice (generation 8 recorded `64e69e49…` while the disk hashed `d4b828dd…`, and
the launcher's documented constant still said generation 6's `efefd885…`).  A pin that is
maintained by hand is a pin that drifts, and a drifted pin certifies a run that did not
happen.  This tool computes the digest with `cell.py`'s own recipe over `cell.HARNESS_FILES`
plus the fixture, so the record and the launcher cannot disagree about how the number is
made.

The recipe is `cell.stage_harness`: sha256 over the sorted ``"<name>:<sha256>\\n"`` lines of
the seven `HARNESS_FILES` plus the fixture, which is the eighth measurement input.

    python3 tools/repin_harness.py --check          # fail if the record and the tree differ
    python3 tools/repin_harness.py --write --unit U-SPCC-80 --reason "..."
    python3 tools/repin_harness.py --print          # the digest only

A write SUPERSEDES: the previous generation's digest and file list are kept under
``superseded_generation_<N>``, and the record's ``generation`` is incremented.  Nothing is
deleted, because a row measured under an older generation must still be explainable.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)                       # experiments/ptr-engine
LONGRUN = os.path.join(ENGINE, "longrun")
REPO = os.path.dirname(os.path.dirname(ENGINE))      # the repository root
if LONGRUN not in sys.path:
    sys.path.insert(0, LONGRUN)

import cell  # noqa: E402  the ONE definition of HARNESS_FILES and the recipe

RECORD = os.path.join(ENGINE, "measure", "HARNESS-PIN.json")
#: The fixture the pin is recorded against.  A pin is per-fixture because the fixture is
#: the eighth input; `--fixture` overrides it for a cell that runs a different one.
#: `LR-01.v8.json` is the fixture generation 9 and 10 were recorded against.
DEFAULT_FIXTURE = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute(fixture: str = DEFAULT_FIXTURE) -> dict:
    """``{"harness_sha256", "files"}`` by `cell.stage_harness`'s recipe."""
    files = {}
    for path, name in cell.HARNESS_FILES:
        if not os.path.exists(path):
            raise SystemExit("repin_harness: missing harness file %s" % (path,))
        files[name] = _sha256_file(path)
    files["fixture"] = _sha256_file(fixture)
    combined = hashlib.sha256()
    for name in sorted(files):
        combined.update(("%s:%s\n" % (name, files[name])).encode("utf-8"))
    return {"harness_sha256": combined.hexdigest(), "files": files}


def _entries(files: dict, fixture: str = DEFAULT_FIXTURE) -> list:
    """The record's `files` list shape: name, path, sha256, size, mtime.

    STAGE-2-ROOT-GREP: this function published generation 11 with ``path: "experiments/"``
    on every entry and with the ``fixture`` entry missing, because the path was a literal
    and a name with no entry in ``cell.HARNESS_FILES`` was skipped.  A record whose file
    list disagrees with the digest it publishes is worse than no record: the digest is
    right and the list that is supposed to let a reader re-derive it is not.  So the path
    is the real repo-relative path, the fixture is an input like any other, and a name
    with no path is a hard error that names the member instead of being dropped.
    """
    by_name = {name: path for path, name in cell.HARNESS_FILES}
    by_name["fixture"] = fixture
    out = []
    for name in sorted(files):
        path = by_name.get(name)
        if path is None:
            raise SystemExit(
                "repin_harness: %r is in the digest but has no path; every input the "
                "recipe hashes must be named in cell.HARNESS_FILES or be the fixture"
                % (name,))
        st = os.stat(path)
        out.append({"name": name,
                    "path": os.path.relpath(path, REPO).replace(os.sep, "/"),
                    "sha256": files[name],
                    "size": st.st_size,
                    "mtime": datetime.datetime.fromtimestamp(
                        st.st_mtime, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    return out


def check(record: str = RECORD, fixture: str = DEFAULT_FIXTURE) -> tuple:
    if not os.path.exists(record):
        return False, "no record at %s" % (record,)
    with open(record, encoding="utf-8") as fh:
        rec = json.load(fh)
    live = compute(fixture)
    if rec.get("harness_sha256") == live["harness_sha256"]:
        return True, "ok generation %s %s" % (rec.get("generation"),
                                              live["harness_sha256"])
    recorded = {e["name"]: e["sha256"] for e in rec.get("files") or []}
    moved = sorted(n for n in live["files"] if recorded.get(n) != live["files"][n])
    return False, ("record generation %s %s != tree %s; moved: %s"
                   % (rec.get("generation"), rec.get("harness_sha256"),
                      live["harness_sha256"], ", ".join(moved) or "(file set changed)"))


def write(unit: str, reason: str, record: str = RECORD,
          fixture: str = DEFAULT_FIXTURE) -> dict:
    live = compute(fixture)
    old = {}
    if os.path.exists(record):
        with open(record, encoding="utf-8") as fh:
            old = json.load(fh)
    generation = int(old.get("generation") or 0) + 1
    doc = dict(old)
    if old:
        doc["superseded_generation_%s" % old.get("generation")] = {
            "harness_sha256": old.get("harness_sha256"),
            "files": old.get("files"),
            "recorded_at": old.get("recorded_at"),
        }
    doc.update({
        "schema": old.get("schema") or "harness-pin/1",
        "generation": generation,
        "harness_sha256": live["harness_sha256"],
        "files": _entries(live["files"], fixture),
        "unit": unit,
        "recorded_by": "tools/repin_harness.py",
        "recorded_at": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
    })
    with open(record, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return doc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    g.add_argument("--print", dest="show", action="store_true")
    ap.add_argument("--unit", default="", help="the unit that moved the harness")
    ap.add_argument("--reason", default="", help="why the harness moved")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    args = ap.parse_args(argv)
    if args.show:
        print(compute(args.fixture)["harness_sha256"])
        return 0
    if args.check:
        ok, message = check(fixture=args.fixture)
        print("harness pin: " + message)
        return 0 if ok else 1
    if not args.reason:
        print("refused: --write needs --reason (a pin without a reason is a silent "
              "instrument change)", file=sys.stderr)
        return 2
    doc = write(args.unit, args.reason, fixture=args.fixture)
    print("wrote %s generation=%s harness_sha256=%s files=%d"
          % (RECORD, doc["generation"], doc["harness_sha256"], len(doc["files"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
