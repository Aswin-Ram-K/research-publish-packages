#!/usr/bin/env python3
"""PATH-REFS-RESOLVE — decide the citations path_refs can only report.

`path_refs.py` classifies a citation as `wrong_dir` when the same *basename* exists in
2+ places: uniqueness does not decide it, so the guard reports and stops. This module
decides the in-scope remainder by EVIDENCE, never by substitution, and emits a decision
table that names the rule that fired.

Rules, in order, first one that fires wins (mirrors the unit card PATH-REFS-BATCH-FIX-2):

  content  exactly one candidate file CONTAINS the symbol the sentence is about.
           Two or more containing it => the rule does not fire.
  dir      exactly one candidate sits in a directory the citing line names (`longrun/`,
           `tools/`, `measure/` ...). Two or more => the rule does not fire.
  owner    a unit card (`orchestration/units/<U>.md`) citing an artefact whose path
           carries <U> — that artefact belongs to that unit's tree. Exactly one such
           candidate => fires.
  undecidable  otherwise. NO mtime, NO recency, NO fuzzy tiebreak: one candidate being
           newer is not evidence, it is a coin flip wearing a timestamp. A wrong
           correction is worse than a dead citation, because it launders a phantom into
           a plausible path.

Import the guard, never reimplement it: classification, scanning, and the basename index
all come from path_refs.

Usage
-----
  python3 experiments/ptr-engine/tools/path_refs_resolve.py --table          # decision table (JSON)
  python3 experiments/ptr-engine/tools/path_refs_resolve.py --apply --json   # apply decided docs rows
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import path_refs as pr  # noqa: E402  the guard: scan/classify/index live there

# Out of scope by instruction (PATH-REFS-BATCH-FIX-2): handoff records and machine-written
# measure artefacts. Nothing here may edit or rewrite them.
OUT_OF_SCOPE_PREFIXES = (
    "orchestration/handoffs/",
    "orchestration/journals/",
    "experiments/ptr-engine/measure/",
)

# Only these trees may be corrected by --apply (the unit card's declared write paths).
APPLY_PREFIXES = ("docs/",)

SYMBOL_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_.-]{3,60})`")
IDENT_RE = re.compile(r"\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b")


def in_scope(file_rel):
    return not file_rel.startswith(OUT_OF_SCOPE_PREFIXES)


def candidates_for(root, cited, index):
    """Every repo-relative CANDIDATE for the cited basename, in stable order.

    The copy rule (an artefact that is one of 2+ byte-identical same-basename files is
    not a candidate) lives in the guard: this resolves against that set, never its own.
    """
    return pr.candidate_paths(root, cited, index)


def line_context(root, file_rel, lineno):
    """The citation line plus the two either side: the sentence a symbol lives in."""
    full = os.path.join(root, file_rel)
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return ""
    lo = max(0, lineno - 3)
    hi = min(len(lines), lineno + 2)
    return "\n".join(lines[lo:hi])


def symbols_in(text, cited):
    """Symbols the sentence is about: backticked identifiers, else snake_case words.

    Path-shaped tokens and the citation itself are dropped — they are the subject, not
    evidence about it.
    """
    out = []
    for m in SYMBOL_RE.finditer(text):
        tok = m.group(1)
        if "/" in tok or tok in cited or tok.endswith((".py", ".md", ".json")):
            continue
        out.append(tok)
    if not out:
        for m in IDENT_RE.finditer(text):
            tok = m.group(1)
            if tok not in cited:
                out.append(tok)
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def file_contains(root, rel, symbol):
    try:
        with open(os.path.join(root, rel), "r", encoding="utf-8", errors="replace") as fh:
            return symbol in fh.read()
    except OSError:
        return False


def rule_content(root, cited, cands, ctx):
    syms = symbols_in(ctx, cited)
    if not syms or not cands:
        return None
    hits = [c for c in cands if any(file_contains(root, c, s) for s in syms)]
    if len(hits) == 1:
        return hits[0], "content"
    return None


def rule_dir(cited, cands, ctx):
    """Exactly one candidate lives in a directory the citing line names."""
    if not cands:
        return None
    hits = []
    for c in cands:
        parts = c.split("/")[:-1]
        named = any(("%s/" % seg) in ctx or ("/%s/" % seg) in ctx for seg in parts)
        if named:
            hits.append(c)
    if len(hits) == 1:
        return hits[0], "dir"
    return None


def unit_name(file_rel, ctx):
    """The unit a card belongs to, or None for a non-card document."""
    if not file_rel.startswith("orchestration/units/"):
        return None
    stem = file_rel.rsplit("/", 1)[-1][:-3]
    return stem


def rule_owner(file_rel, cands, ctx):
    """A unit card citing an artefact that carries its own unit name as a PATH SEGMENT.

    Segment, not substring: `V0` must not claim `release/v0.1/...` — that is a version
    number, not an ownership claim, and accepting it would launder a phantom into a
    plausible-looking path.
    """
    unit = unit_name(file_rel, ctx)
    if not unit:
        return None
    u = unit.lower()
    hits = []
    for c in cands:
        segs = [s.lower() for s in c.split("/")[:-1]]
        base = c.rsplit("/", 1)[-1].lower()
        if u in segs or base.startswith(u + ".") or base.startswith(u + "-") or base.startswith(u + "_"):
            hits.append(c)
    if len(hits) == 1:
        return hits[0], "owner"
    return None


def decide(root, finding, index):
    cited, file_rel = finding["path"], finding["file"]
    cands = candidates_for(root, cited, index)
    ctx = line_context(root, file_rel, finding["line"])
    row = {
        "token": cited,
        "file": file_rel,
        "line": finding["line"],
        "candidates": cands,
        "rule": "",
        "chosen": "",
        "confidence": "undecidable",
        "text": finding["text"],
    }
    for fn, name in ((lambda: rule_content(root, cited, cands, ctx), "content"),
                     (lambda: rule_dir(cited, cands, ctx), "dir"),
                     (lambda: rule_owner(file_rel, cands, ctx), "owner")):
        got = fn()
        if got:
            row["chosen"], row["rule"] = got[0], got[1]
            row["confidence"] = name
            return row
    row["rule"] = "none"
    return row


def build_table(root):
    root = os.path.abspath(root)
    index = pr.basename_index(root)
    findings = [f for f in pr.scan(root)
                if f["classification"] == "wrong_dir" and in_scope(f["file"])]
    rows = [decide(root, f, index) for f in findings]
    rows.sort(key=lambda r: (r["file"], r["line"], r["token"]))
    return rows


def normalise(text, tokens):
    """Replace every citation token with <P>: the load-bearing equivalence check."""
    for tok in sorted(tokens, key=len, reverse=True):
        text = text.replace(tok, "<P>")
    return text


def apply_rows(root, rows):
    """Token substitution only, per file, guarded by a normalised-byte proof.

    Returns (edited, skipped, failures): a file whose normalised bytes change is reverted
    in full and reported — a substitution that moved a non-citation byte is not a fix.
    """
    root = os.path.abspath(root)
    by_file = {}
    for r in rows:
        if r["confidence"] == "undecidable":
            continue
        if not r["file"].startswith(APPLY_PREFIXES):
            continue
        by_file.setdefault(r["file"], []).append(r)
    edited, skipped, failures = [], [], []
    for rel, rs in sorted(by_file.items()):
        full = os.path.join(root, rel)
        try:
            with open(full, "r", encoding="utf-8") as fh:
                before = fh.read()
        except OSError as exc:
            failures.append({"file": rel, "error": str(exc)})
            continue
        subs = {}
        for r in rs:
            old, new = r["token"], r["chosen"]
            want = old.rsplit("/", 1)[-1]
            if new.rsplit("/", 1)[-1] != want or not os.path.isfile(os.path.join(root, new)):
                skipped.append({"file": rel, "line": r["line"], "token": old,
                                "reason": "chosen basename/disk check failed"})
                continue
            subs[old] = new
        if not subs:
            continue
        after = before
        for old, new in subs.items():
            after = after.replace(old, new)
        toks = set(subs) | set(subs.values())
        if normalise(after, toks) != normalise(before, toks):
            failures.append({"file": rel, "error": "normalised diff changed a non-citation byte",
                             "tokens": sorted(subs)})
            continue
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(after)
        edited.append({"file": rel, "substitutions": {k: subs[k] for k in sorted(subs)}})
    return edited, skipped, failures


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=pr.ROOT_DEFAULT)
    ap.add_argument("--table", action="store_true", help="emit the decision table as JSON")
    ap.add_argument("--apply", action="store_true", help="apply decided docs rows (guarded)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    rows = build_table(root)
    if not (args.apply or args.table or args.json):
        for r in rows:
            print("%s:%d  %-11s %s -> %s" % (r["file"], r["line"], r["confidence"],
                                             r["token"], r["chosen"] or "UNDECIDABLE"))
    if args.apply:
        edited, skipped, failures = apply_rows(root, rows)
        print(json.dumps({"edited": edited, "skipped": skipped, "failures": failures}, indent=1))
        if failures:
            return 1
    if args.table or args.json:
        print(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
