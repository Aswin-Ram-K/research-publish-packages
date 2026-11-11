#!/usr/bin/env python3
"""agentic_pin.py - the stage-2 instrument pin: which files produced an episode row.

The replay runner's pin (`measure/HARNESS-PIN.json`, generation 9) covers the replay
instrument.  Stage 2 is a different instrument -- an episode loop, not a scripted replay --
so it gets its own pin rather than a new generation of the replay one.  Mixing them would
mean a stage-2 row and a replay row could claim the same digest while running different
code, which is exactly the failure the replay pin exists to prevent.

The digest is sha256 over the sorted `name:sha256\\n` lines of every file in FILES, so a
one-byte change to any of them changes the digest.  Every stage-2 row carries it as
`harness_sha256`, and `--check` fails when the record and the tree disagree.

    python3 tools/agentic_pin.py --write     # record the current tree
    python3 tools/agentic_pin.py --check     # fail if the tree moved since the record
    python3 tools/agentic_pin.py --print     # the digest only, for a --expect-harness flag
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)          # experiments/ptr-engine
LONGRUN = os.path.join(ENGINE, "longrun")
REPO = os.path.dirname(os.path.dirname(ENGINE))

#: Every file whose bytes can change what an episode row means.  A new measurement input
#: is added here in the same commit that adds it, never afterwards.
FILES = (
    "longrun/agentic_cell.py",
    "longrun/agentic_contract.py",
    "longrun/client.py",
    "longrun/run_longrun.py",
    "longrun/tools/analyze_agentic.py",
    "longrun/tools/build_agentic_tasks.py",
)

RECORD = os.path.join(ENGINE, "measure", "AGENTIC-PIN.json")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_digests(engine: str = ENGINE) -> dict:
    out = {}
    for name in FILES:
        path = os.path.join(engine, name)
        if not os.path.exists(path):
            raise SystemExit("agentic_pin: missing instrument file %s" % (path,))
        out[name] = _sha256(path)
    return out


def digest_of(digests: dict) -> str:
    h = hashlib.sha256()
    for name in sorted(digests):
        h.update(("%s:%s\n" % (name, digests[name])).encode("utf-8"))
    return h.hexdigest()


def compute(engine: str = ENGINE) -> dict:
    digests = file_digests(engine)
    return {"harness_sha256": digest_of(digests), "files": digests,
            "file_count": len(digests)}


def write(engine: str = ENGINE, record: str = RECORD) -> dict:
    payload = compute(engine)
    payload["instrument"] = "agentic-episode-loop"
    payload["note"] = ("stage 2's own pin; the replay runner's HARNESS-PIN.json is a "
                       "different instrument and is not superseded by this record")
    with open(record, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return payload


def check(engine: str = ENGINE, record: str = RECORD) -> tuple:
    """``(code, message)``: 0 = agrees, 1 = the tree moved, 2 = no record.

    A missing record is a DISAGREEMENT, not a pass: a gate that cannot fail is not a gate.
    The three codes are distinct so a caller can tell "the instrument moved" (1) from
    "the instrument was never recorded" (2) — the same split ``cell.py`` uses for
    ``SPEC NOT RECORDED``.
    """
    if not os.path.exists(record):
        return 2, "no record at %s; run --write" % (record,)
    with open(record, encoding="utf-8") as fh:
        rec = json.load(fh)
    live = compute(engine)
    if rec.get("harness_sha256") == live["harness_sha256"]:
        return 0, "ok %s (%d files)" % (live["harness_sha256"], live["file_count"])
    moved = sorted(name for name in live["files"]
                   if rec.get("files", {}).get(name) != live["files"][name])
    return 1, ("record %s != tree %s; moved: %s"
               % (rec.get("harness_sha256"), live["harness_sha256"],
                  ", ".join(moved) or "(file set changed)"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="record the current tree")
    g.add_argument("--check", action="store_true", help="fail if the tree moved")
    g.add_argument("--print", dest="show", action="store_true", help="print the digest")
    args = ap.parse_args(argv)
    if args.write:
        payload = write()
        print("wrote %s harness_sha256=%s files=%d"
              % (RECORD, payload["harness_sha256"], payload["file_count"]))
        return 0
    if args.check:
        code, message = check(ENGINE, RECORD)
        print("agentic pin: " + message)
        return code
    print(compute()["harness_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
