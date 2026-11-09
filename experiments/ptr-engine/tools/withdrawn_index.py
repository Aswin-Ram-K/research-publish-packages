#!/usr/bin/env python3
"""withdrawn_index.py - the guard for `measure/WITHDRAWN.json`.

The register lists every number this batch withdrew or superseded, with the artefact that
replaces it. This tool has two jobs:

  --check <file>   print the id of every withdrawn claim whose string occurs in <file> without
                   its correction attached; exit 1 if any such claim is found, 0 if clean.
                   Use it to screen a document BEFORE publishing it.
  --self-test      verify the register itself: required fields, enum values, unique ids, every
                   `decided_by` handoff path exists, every `superseded_by` artefact opens.
                   A `none — no replacement exists` row is legitimate and is not opened.

--strict changes the window, nothing else:
  default   a correction marker anywhere within 400 characters of the hit (either side)
  --strict  a correction marker in the SAME PARAGRAPH (blank-line delimited) as the hit, so a
            stale sentence cannot be excused by a marker in a neighbouring paragraph. The two
            published latency pages are screened this way.

Read-only, offline, zero requests. It never edits the register or the file it screens.

A finding means "this document quotes a withdrawn number and its correction is not within the
window". It is a prompt to attach the correction, not a claim that the sentence is false.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_REGISTER = os.path.join(HERE, "..", "measure", "WITHDRAWN.json")

KINDS = {"wrong_denominator", "wrong_unit", "unsound_rule", "retracted_finding", "overstated_mechanism"}
STATUSES = {"withdrawn", "superseded", "disputed"}
CITABLE = {"never", "only with the correction attached"}
REQUIRED = ("id", "claim", "claim_ref", "kind", "status", "superseded_by",
            "decided_by", "date", "still_citable", "quote", "markers")
NO_REPLACEMENT = "none — no replacement exists"
WINDOW = 400
# A blank line (or a line holding only whitespace) separates paragraphs.
PARAGRAPH_SEP = re.compile(r"\n[ \t]*\n")

def load_register(path: str | None = None) -> dict:
    p = path or DEFAULT_REGISTER
    with open(p, encoding="utf-8") as fh:
        reg = json.load(fh)
    if not isinstance(reg.get("entries"), list):
        raise SystemExit(f"{p}: no 'entries' list")
    return reg

def paragraph_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    """The blank-line-delimited paragraph that encloses text[start:end]."""
    begin = 0
    for m in PARAGRAPH_SEP.finditer(text, 0, start):
        begin = m.end()
    m = PARAGRAPH_SEP.search(text, end)
    stop = m.start() if m else len(text)
    return begin, stop

def corrected(text: str, start: int, end: int, markers, window: int = WINDOW,
              strict: bool = False) -> bool:
    """True when a correction marker appears near the occurrence, EXCLUDING the quote itself.

    The quote is excluded because a claim can contain its own marker word (entry WI-005's
    claim contains "era", one of its markers); counting that would make the guard never fire.

    strict=True searches only the enclosing paragraph (blank-line delimited). The default
    (strict=False) is the historical 400-character window, byte-identical to earlier versions.
    """
    if strict:
        begin, stop = paragraph_bounds(text, start, end)
        around = (text[begin:start] + " " + text[end:stop]).lower()
    else:
        left = text[max(0, start - window):start].lower()
        right = text[end:end + window].lower()
        around = left + " " + right
    return any(m.lower() in around for m in markers)

def check_file(path: str, reg: dict, window: int = WINDOW, strict: bool = False):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}")
    findings = []
    for e in reg["entries"]:
        quote = e.get("quote") or ""
        if not quote:
            continue
        start = 0
        while True:
            i = text.find(quote, start)
            if i < 0:
                break
            j = i + len(quote)
            if not corrected(text, i, j, e.get("markers") or [], window, strict=strict):
                line = text.count("\n", 0, i) + 1
                snippet = " ".join(text[i:j].split())[:110]
                findings.append((e["id"], line, snippet))
            start = j
    return findings

def short_quote_notes(reg: dict) -> list[str]:
    """Quotes under 5 characters are false-positive risks; reported, never fatal."""
    return [f"{e['id']}: quote {e.get('quote')!r} is shorter than 5 characters "
            f"(reported, not a failure)" for e in reg["entries"]
            if len(e.get("quote") or "") < 5]

def self_test(reg: dict, root: str = ROOT):
    problems, ids = [], set()
    for e in reg["entries"]:
        eid = e.get("id", "<no id>")
        for k in REQUIRED:
            if k not in e or e[k] in (None, "", []):
                problems.append(f"{eid}: missing required field {k!r}")
        if eid in ids:
            problems.append(f"{eid}: duplicate id")
        ids.add(eid)
        if e.get("kind") not in KINDS:
            problems.append(f"{eid}: kind {e.get('kind')!r} not in {sorted(KINDS)}")
        if e.get("status") not in STATUSES:
            problems.append(f"{eid}: status {e.get('status')!r} not in {sorted(STATUSES)}")
        if e.get("still_citable") not in CITABLE:
            problems.append(f"{eid}: still_citable {e.get('still_citable')!r} not in {sorted(CITABLE)}")
        dec = e.get("decided_by") or {}
        hp = dec.get("handoff")
        if not hp:
            problems.append(f"{eid}: decided_by.handoff missing")
        elif not os.path.isfile(os.path.join(root, hp)):
            problems.append(f"{eid}: decided_by handoff does not exist: {hp}")
        if not dec.get("card"):
            problems.append(f"{eid}: decided_by.card missing")
        sup = e.get("superseded_by") or {}
        sp = sup.get("path")
        if not sp:
            problems.append(f"{eid}: superseded_by.path missing")
        elif sp.startswith("none"):
            if NO_REPLACEMENT not in sp:
                problems.append(f"{eid}: a 'none' row must spell {NO_REPLACEMENT!r}")
            if not sup.get("number"):
                problems.append(f"{eid}: superseded_by.number missing beside a 'none' row")
        else:
            ap = sp if os.path.isabs(sp) else os.path.join(root, sp)
            try:
                with open(ap, "rb") as fh:
                    if not fh.read(1):
                        problems.append(f"{eid}: superseded_by artefact is empty: {sp}")
            except OSError as exc:
                problems.append(f"{eid}: superseded_by artefact does not open: {sp} ({exc.__class__.__name__})")
            if not sup.get("number"):
                problems.append(f"{eid}: superseded_by.number missing")
    return problems

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Screen a file for withdrawn claims, or self-test the register.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", metavar="FILE", help="exit 1 if FILE quotes a withdrawn claim without its correction")
    g.add_argument("--self-test", action="store_true", help="verify the register's paths and fields")
    ap.add_argument("--register", default=None, help="path to WITHDRAWN.json")
    ap.add_argument("--window", type=int, default=WINDOW, help="characters searched either side of a hit")
    ap.add_argument("--strict", action="store_true",
                    help="window = the enclosing paragraph (blank-line delimited), not %d chars" % WINDOW)
    a = ap.parse_args(argv)
    reg = load_register(a.register)
    if a.self_test:
        problems = self_test(reg)
        for p in problems:
            print("FAIL", p)
        for n in short_quote_notes(reg):
            print("NOTE", n)
        n = len(reg["entries"])
        print(f"self-test: {n - 0} entries, {len(problems)} problem(s)")
        return 1 if problems else 0
    findings = check_file(a.check, reg, window=a.window, strict=a.strict)
    mode = "strict-paragraph" if a.strict else f"window={a.window}"
    if not findings:
        print(f"CLEAN {a.check}: no withdrawn claim found without its correction "
              f"({len(reg['entries'])} entries screened, {mode})")
        return 0
    for eid, line, snip in findings:
        print(f"WITHDRAWN {eid} line {line}: {snip}")
    print(f"FOUND {len({f[0] for f in findings})} withdrawn claim(s) without a correction in {a.check} ({mode})")
    return 1

if __name__ == "__main__":
    sys.exit(main())
