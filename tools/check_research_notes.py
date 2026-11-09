#!/usr/bin/env python3
"""Guard for docs/RESEARCH-PROTOCOL.md — checks a research note and the protocol's own structure.

Usage:
    python3 tools/check_research_notes.py \
        --protocol docs/RESEARCH-PROTOCOL.md \
        --template orchestration/units/TEMPLATE.md \
        --note measure/research/tool-channel-sglang.json \
        --doc docs/research/tool-channel-sglang.md

Exit 0 only when every check passes; exit 1 with one line per failure, so the command can be recorded as a
verdict and re-run by the sweeper. Deliberately strict about the parts the protocol calls load-bearing:
`sources[].url`, `sources[].retrieved_at`, `sources[].claim_taken`, `claims[].status` in
{verified, inferred, contradicted}, `open_questions`, and a named source for every `verified` claim.
"""
import argparse
import json
import sys

STATUSES = {"verified", "inferred", "contradicted"}
PROTOCOL_HEADINGS = [
    "## 1. When research is required",
    "## 2. Where research lands",
    "## 3. The citation rule",
    "## 4. The stopping rule",
    "## 5. The precedence rule",
    "## 6. Anti-patterns",
    "## 7. Checklist",
]


def check_note(path):
    errs = []
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - report, do not crash
        return ["%s: not valid JSON (%s)" % (path, exc)]
    sources = data.get("sources") or []
    if not sources:
        errs.append("%s: sources is empty" % path)
    ids = set()
    for s in sources:
        sid = s.get("id")
        ids.add(sid)
        for key in ("url", "retrieved_at", "claim_taken"):
            if not s.get(key):
                errs.append("%s: source %r missing %s" % (path, sid, key))
        if not str(s.get("retrieved_at", ""))[:4].isdigit():
            errs.append("%s: source %r retrieved_at is not a date" % (path, sid))
    claims = data.get("claims") or []
    if not claims:
        errs.append("%s: claims is empty (a note with sources and no claims is not research)" % path)
    for c in claims:
        cid, status = c.get("id"), c.get("status")
        if status not in STATUSES:
            errs.append("%s: claim %r status %r not in %s" % (path, cid, status, sorted(STATUSES)))
        if status == "verified" and c.get("source") not in ids:
            errs.append("%s: verified claim %r names no known source" % (path, cid))
        if not c.get("claim"):
            errs.append("%s: claim %r has no claim text" % (path, cid))
    if "open_questions" not in data or not isinstance(data.get("open_questions"), list):
        errs.append("%s: open_questions missing or not a list" % path)
    if "changes_plan" not in data or not isinstance(data.get("changes_plan"), list):
        errs.append("%s: changes_plan missing or not a list" % path)
    return errs


def check_protocol(path):
    text = open(path, encoding="utf-8").read()
    errs = ["%s: missing heading %r" % (path, h) for h in PROTOCOL_HEADINGS if h not in text]
    for key in ("research_note", "claims_status"):
        if key not in text:
            errs.append("%s: checklist does not name %r" % (path, key))
    return errs


def check_template(path):
    text = open(path, encoding="utf-8").read()
    errs = []
    if "## Research" not in text:
        errs.append("%s: missing '## Research' section" % path)
    for key in ("research_note", "claims_status"):
        if key not in text:
            errs.append("%s: Research section does not require %r" % (path, key))
    return errs


def check_doc(path):
    text = open(path, encoding="utf-8").read()
    errs = []
    for needle in ("**Question:**", "## Verified", "## Inferred", "## Contradicted"):
        if needle not in text:
            errs.append("%s: missing %r" % (path, needle))
    return errs


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol", action="append", default=[])
    p.add_argument("--template", action="append", default=[])
    p.add_argument("--note", action="append", default=[])
    p.add_argument("--doc", action="append", default=[])
    args = p.parse_args(argv)
    errs = []
    for path in args.protocol:
        errs += check_protocol(path)
    for path in args.template:
        errs += check_template(path)
    for path in args.note:
        errs += check_note(path)
    for path in args.doc:
        errs += check_doc(path)
    if not (args.protocol or args.template or args.note or args.doc):
        errs.append("nothing to check: pass --protocol/--template/--note/--doc")
    for e in errs:
        print(e)
    print("%s: %d check(s), %d failure(s)" % ("FAIL" if errs else "OK", 0 if errs else 1, len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
