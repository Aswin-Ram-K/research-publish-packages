#!/usr/bin/env python3
"""Check that the false-pass register still matches the flagged handoffs.

The register (experiments/ptr-engine/measure/FALSE-PASS.json) is ADDITIVE: it
classifies handoffs that say done/pass while carrying no substance under any of
the six contracted keys. It never edits a handoff, a ledger, or a verdict row.

`--check` exits 0 when, and only when:
  * every handoff the linter currently flags with E_STATUS_WORD_CONTRADICTION is
    registered, and
  * every registered handoff still has the sha256 recorded at registration, and
  * no registered handoff has been un-flagged since (that too means the handoff
    was edited after registration, which the register must not paper over).

Exit 1 names each offending record and why. The classification decision itself
is a human/unit judgement recorded in the register; this tool only measures
coverage and drift.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import handoff_lint as lint  # noqa: E402

DEFAULT_HANDOFFS = os.path.join("orchestration", "handoffs")
DEFAULT_REGISTER = os.path.join("experiments", "ptr-engine", "measure", "FALSE-PASS.json")
CODE = "E_STATUS_WORD_CONTRADICTION"


def sha256_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def flagged_records(handoffs_dir):
    """basename -> path for every handoff the linter flags with CODE."""
    out = {}
    if not os.path.isdir(handoffs_dir):
        return out
    for name in sorted(os.listdir(handoffs_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(handoffs_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except Exception:
            continue  # unparseable/mid-write: E_PARSE is handoff_lint's job
        if not isinstance(doc, dict):
            continue
        if any(f.get("code") == CODE for f in lint.partial_findings(doc)):
            out[name] = path
    return out


def load_register(path):
    with open(path, encoding="utf-8") as fh:
        reg = json.load(fh)
    if not isinstance(reg, dict) or not isinstance(reg.get("entries"), list):
        raise ValueError("register has no 'entries' list")
    entries = {}
    for e in reg["entries"]:
        if not isinstance(e, dict) or not e.get("path"):
            raise ValueError("register entry without a 'path'")
        entries[os.path.basename(e["path"])] = e
    return reg, entries


def check(handoffs_dir=DEFAULT_HANDOFFS, register_path=DEFAULT_REGISTER):
    """Return (ok, problems, summary)."""
    reg, entries = load_register(register_path)
    flagged = flagged_records(handoffs_dir)
    problems = []

    for name, path in flagged.items():
        entry = entries.get(name)
        if entry is None:
            problems.append("%s: flagged %s but not in the register" % (name, CODE))
            continue
        recorded = entry.get("sha256")
        actual = sha256_of(path)
        if recorded != actual:
            problems.append(
                "%s: handoff edited after registration (register sha256=%s, on disk=%s)"
                % (name, recorded, actual))

    for name, entry in entries.items():
        if name not in flagged:
            problems.append(
                "%s: registered as %s but no longer flagged %s (handoff drifted)"
                % (name, entry.get("classification"), CODE))

    summary = {
        "flagged": len(flagged),
        "registered": len(entries),
        "classes": {},
        "register": register_path,
        "handoffs": handoffs_dir,
    }
    for e in entries.values():
        c = e.get("classification")
        summary["classes"][c] = summary["classes"].get(c, 0) + 1
    return (not problems), problems, summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="verify coverage and sha256 freshness (default action)")
    ap.add_argument("--handoffs", default=DEFAULT_HANDOFFS, help="handoff directory to scan")
    ap.add_argument("--register", default=DEFAULT_REGISTER, help="register JSON path")
    ap.add_argument("--quiet", action="store_true", help="print only the verdict line")
    args = ap.parse_args(argv)

    try:
        ok, problems, summary = check(args.handoffs, args.register)
    except Exception as exc:  # a broken register is a failure, never a pass
        print("FAIL register unreadable: %s: %s" % (type(exc).__name__, exc))
        return 1

    if not args.quiet:
        print("flagged %s : %d" % (CODE, summary["flagged"]))
        print("registered            : %d %s" % (summary["registered"], summary["classes"]))
    for p in problems:
        print("FAIL " + p)
    if ok:
        print("OK register covers every flagged record and every sha256 matches")
        return 0
    print("FAIL %d problem(s)" % len(problems))
    return 1


if __name__ == "__main__":
    sys.exit(main())
