#!/usr/bin/env python3
"""PATH-REFS — every path a document cites must be a path the tree has.

Why this exists. Four cards in one batch each cost a correction because a document
named a path that was not there: `verdict_with_freeze.py` (twice), `docs/GATE-SIMPLIFY.md`,
`docs/PRICE-REPLICATION.md`, and `docs/BUDGET-SCHEDULE.md` (the artefact is
`experiments/ptr-engine/measure/BUDGET-SCHEDULE.md`). The patch is cheap; the instrument is
the deliverable. This tool is the instrument: it parses every path-shaped reference out of
the corpus, resolves it, and fails on a reference the tree cannot satisfy unless a frozen
baseline already records it.

Classifications
---------------
  ok         the cited path resolves, byte for byte.
  wrong_dir  the cited path does not exist, but the same basename does exist in the tree.
             `resolved` names where it actually is. The BUDGET-SCHEDULE case is this class.
             Two locations are treated as *legal alternates* and named first when present:
             `experiments/ptr-engine/measure/<basename>` and `docs/<basename>` — the two
             directories this corpus actually moves artefacts between. A unique location
             anywhere else in the tree is still `wrong_dir`; the citation is still wrong.
  missing    no file with that basename exists anywhere in the tree — including the case
             below, where every same-basename hit is a copy. REPORTED, never repaired by
             creating the file: a deliberate future path is not a defect, and creating the
             file a citation names is how a phantom becomes a lie.

Candidate set (the copy rule, in one sentence): a candidate that is one of two or more
byte-identical files with the cited basename (same sha256) is a COPY in a duplicated tree,
not an addressable alternate, so copies are removed from the candidate set and the
citation reports `missing`; a basename whose candidates differ in content keeps every
candidate and stays `wrong_dir`, because that ambiguity is real.
  ignored    the citing line says it is talking about a path that is not there, or that the
             line is illustrative. The allowlist is the four phrases below and nothing else;
             every entry is justified in docs/PATH-REFS.md so a later reader can audit it.

Forward-only baseline
---------------------
`state/logs/path-refs-baseline.json` freezes the today census of `wrong_dir` + `missing`
reference keys (``<citing-file>::<cited-path>``). `--check` exits 1 only for a key NOT in the
baseline and exits 0 when only baselined keys remain. Nothing is ever silently excused: every
baselined key is in the file, with its classification and the resolved path it had when frozen.

Usage
-----
  python3 experiments/ptr-engine/tools/path_refs.py --report
  python3 experiments/ptr-engine/tools/path_refs.py --check           # exit 0 clean, 1 new
  python3 experiments/ptr-engine/tools/path_refs.py --write-baseline  # freeze the census
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
import time

ROOT_DEFAULT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
)

SCAN_GLOBS = [
    "docs/**/*.md",
    "experiments/ptr-engine/measure/*.md",
    "experiments/ptr-engine/measure/*.json",
    "orchestration/units/*.md",
    "orchestration/handoffs/*.json",
]

# A path-shaped reference: a top-level corpus root, then path characters, then a known suffix.
PATH_RE = re.compile(
    r"\b(docs|experiments|orchestration|papers|tests|state)/[\w./-]+\.(?:md|json|jsonl|py|sh|txt)\b"
)

# Allowlist: a citing line that carries one of these is DISCUSSING a path, not citing it.
# Each entry is justified in docs/PATH-REFS.md — audit them there, not here.
IGNORE_PATTERNS = [
    (re.compile(r"\bdoes not exist\b", re.I), "says-it-does-not-exist"),
    (re.compile(r"\bnot exist\b", re.I), "says-it-does-not-exist"),
    (re.compile(r"\bnonexistent\b", re.I), "says-it-does-not-exist"),
    (re.compile(r"\bphantom\b", re.I), "named-as-phantom"),
    (re.compile(r"\bWI-", re.I), "withdrawn-item"),
    (re.compile(r"\bfor example\b", re.I), "illustrative"),
    (re.compile(r"\bno such file\b", re.I), "says-it-does-not-exist"),
]

LEGAL_ALTERNATES = [
    "experiments/ptr-engine/measure/{base}",
    "docs/{base}",
]

BASELINE_DEFAULT = os.path.join("state", "logs", "path-refs-baseline.json")

# Ephemeral verifier copies (`.scratch/judge-*`, `.verify-scratch/`) are pruned: they are
# snapshots of this tree taken by other sessions, not the tree's own artefacts. Counting them
# made a basename "exist" in a copy one minute and vanish the next, flipping a citation between
# `wrong_dir` and `missing` between two runs of the same scan.
WALK_PRUNE = {".git", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache",
              ".venv", "venv", ".tox", ".ruff_cache", ".scratch", ".verify-scratch"}


def ignore_reason(line):
    """Return the allowlist reason for `line`, or None."""
    for rx, reason in IGNORE_PATTERNS:
        if rx.search(line):
            return reason
    return None


def iter_scan_files(root):
    """Yield scanned files as paths relative to `root`, in a stable order."""
    out = []
    for pattern in SCAN_GLOBS:
        base = pattern.split("*")[0].rstrip("/")
        start = os.path.join(root, base)
        if not os.path.isdir(start):
            continue
        if "**" in pattern:
            for dirpath, dirnames, filenames in os.walk(start):
                dirnames[:] = sorted(d for d in dirnames if d not in WALK_PRUNE)
                for name in sorted(filenames):
                    if fnmatch.fnmatch(name, "*.md"):
                        out.append(os.path.relpath(os.path.join(dirpath, name), root))
        else:
            stem = pattern.rsplit("/", 1)[-1]
            for name in sorted(os.listdir(start)):
                full = os.path.join(start, name)
                if os.path.isfile(full) and fnmatch.fnmatch(name, stem):
                    out.append(os.path.relpath(full, root))
    return sorted(set(out))


def basename_index(root):
    """basename -> sorted list of repo-relative paths, for the whole tree."""
    index = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in WALK_PRUNE)
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            index.setdefault(name, []).append(rel)
    for name in index:
        index[name].sort()
    return index


_SHA_CACHE = {}


def _sha256(root, rel):
    """Content digest of one repo file, cached for the process (None if unreadable)."""
    key = (root, rel)
    if key not in _SHA_CACHE:
        h = hashlib.sha256()
        try:
            with open(os.path.join(root, rel), "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            _SHA_CACHE[key] = h.hexdigest()
        except OSError:
            _SHA_CACHE[key] = None
    return _SHA_CACHE[key]


def all_identical_copies(root, paths):
    """True when `paths` is 2+ files sharing ONE content: a copied tree, not alternates."""
    if len(paths) < 2:
        return False
    shas = {_sha256(root, p) for p in paths}
    return len(shas) == 1 and None not in shas


def candidate_paths(root, cited, index):
    """The candidate set for one citation: same-basename files, minus copy artefacts.

    The single home of the copy rule. `classify` and `path_refs_resolve` both call this,
    so a resolver can never disagree with the guard about what counts as a candidate.
    """
    base = cited.rsplit("/", 1)[-1]
    hits = [p for p in index.get(base, []) if p != cited]
    if all_identical_copies(root, hits):
        return []
    return hits


def classify(root, path, index):
    """Return (classification, resolved) for one cited path."""
    if not path or path.startswith("..") or os.path.isabs(path):
        return "ignored", "non-repo-path"
    if os.path.isfile(os.path.join(root, path)):
        return "ok", path
    base = path.rsplit("/", 1)[-1]
    alts = [a.format(base=base) for a in LEGAL_ALTERNATES]
    alts = [a for a in alts if a != path and os.path.isfile(os.path.join(root, a))]
    if alts:
        return "wrong_dir", " | ".join(alts)
    hits = candidate_paths(root, path, index)
    if hits:
        return "wrong_dir", " | ".join(hits[:3])
    return "missing", ""


def scan(root):
    """Full census: list of dicts {file, line, text, path, classification, resolved, reason}."""
    root = os.path.abspath(root)
    index = basename_index(root)
    findings = []
    for rel in iter_scan_files(root):
        full = os.path.join(root, rel)
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        fence = None            # info string of the open fenced block, or None
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                mark = stripped[:3]
                if fence is None:
                    fence = stripped[3:].strip().lower()
                elif stripped.startswith(mark):
                    fence = None
                continue
            if fence is not None and fence.startswith("diff") and stripped.startswith("-") \
                    and not stripped.startswith("---"):
                # A `-` line in a correction diff quotes the token that was REPLACED: the
                # citation no longer exists in the document, so it is not a live reference.
                continue
            for m in PATH_RE.finditer(line):
                cited = m.group(0).rstrip(".,;:)`'\"")
                reason = ignore_reason(line)
                if reason:
                    findings.append({"file": rel, "line": lineno, "path": cited,
                                     "classification": "ignored", "resolved": "",
                                     "reason": reason, "text": line.strip()[:200]})
                    continue
                cls, resolved = classify(root, cited, index)
                findings.append({"file": rel, "line": lineno, "path": cited,
                                 "classification": cls, "resolved": resolved,
                                 "reason": "", "text": line.strip()[:200]})
    return findings


def key_of(f):
    return "%s::%s" % (f["file"], f["path"])


def load_baseline(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {"anchors": {}}
    if not isinstance(data, dict) or not isinstance(data.get("anchors"), dict):
        return {"anchors": {}}
    return data


def write_baseline(path, findings, root):
    anchors = {}
    for f in findings:
        if f["classification"] in ("wrong_dir", "missing"):
            anchors[key_of(f)] = {
                "classification": f["classification"],
                "resolved": f["resolved"],
                "first_seen": "%s:%d" % (f["file"], f["line"]),
            }
    data = {
        "frozen_by": "PHANTOM-PATH-FIX",
        "frozen_at": time.time(),
        "frozen_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "purpose": (
            "Frozen record of every wrong_dir / missing path reference present when PATH-REFS "
            "was armed. These are RECORDED findings, not excused ones: no artefact was created "
            "to satisfy a citation, and no prose was rewritten. The guard fails only on a key "
            "NOT in this file; the BUDGET-SCHEDULE citations are absent because they were "
            "corrected in the same pass, not because they were excused."
        ),
        "rule": (
            "Forward-only. key = '<citing-file>::<cited-path>'. --check exits 1 for any "
            "wrong_dir/missing key not present here, 0 when only baselined keys remain. A "
            "corrected citation leaves the baseline untouched; fixing a key does not require "
            "rewriting this file."
        ),
        "root": os.path.abspath(root),
        "anchors": anchors,
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    # One anchor per line: a 1,000-key baseline stays greppable and diffable.
    head = {k: v for k, v in data.items() if k != "anchors"}
    lines = ["{"]
    for k in sorted(head):
        lines.append(" %s: %s," % (json.dumps(k), json.dumps(head[k], sort_keys=True)))
    lines.append(' "anchors": {')
    keys = sorted(anchors)
    for i, k in enumerate(keys):
        lines.append('  %s: %s%s' % (json.dumps(k), json.dumps(anchors[k], sort_keys=True),
                                     "," if i < len(keys) - 1 else ""))
    lines.append(" }")
    lines.append("}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return len(anchors)


def census(findings):
    counts = {"ok": 0, "wrong_dir": 0, "missing": 0, "ignored": 0}
    for f in findings:
        counts[f["classification"]] = counts.get(f["classification"], 0) + 1
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=ROOT_DEFAULT, help="repo root (default: this checkout)")
    ap.add_argument("--report", action="store_true", help="print the full census")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 on a wrong_dir/missing reference not in the frozen baseline")
    ap.add_argument("--write-baseline", action="store_true",
                    help="freeze the current wrong_dir/missing census")
    ap.add_argument("--baseline", default=None,
                    help="baseline path (default: <root>/state/logs/path-refs-baseline.json)")
    ap.add_argument("--json", action="store_true", help="machine-readable census on stdout")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    baseline_path = args.baseline or os.path.join(root, BASELINE_DEFAULT)
    findings = scan(root)
    counts = census(findings)
    bad = [f for f in findings if f["classification"] in ("wrong_dir", "missing")]

    if args.write_baseline:
        n = write_baseline(baseline_path, findings, root)
        print("baseline frozen: %d anchors -> %s" % (n, baseline_path))
    if args.json:
        print(json.dumps({"counts": counts, "findings": findings}, indent=1))
    else:
        if args.report or not (args.check or args.write_baseline):
            for f in findings:
                if f["classification"] == "ok" and not args.report:
                    continue
                extra = (" -> %s" % f["resolved"]) if f["resolved"] else ""
                why = (" [%s]" % f["reason"]) if f["reason"] else ""
                print("%s:%d  %-9s %s%s%s" % (f["file"], f["line"],
                                             f["classification"], f["path"], extra, why))
        print("census: ok=%d wrong_dir=%d missing=%d ignored=%d"
              % (counts["ok"], counts["wrong_dir"], counts["missing"], counts["ignored"]))

    if args.check:
        anchors = load_baseline(baseline_path).get("anchors", {})
        new = [f for f in bad if key_of(f) not in anchors]
        for f in new:
            extra = (" -> %s" % f["resolved"]) if f["resolved"] else ""
            print("NEW %s:%d %s %s%s" % (f["file"], f["line"], f["classification"],
                                         f["path"], extra))
        print("path-refs: %d known (baselined), %d new" % (len(bad) - len(new), len(new)))
        if new:
            print("FAIL: a document cites a path the tree does not have")
            return 1
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
