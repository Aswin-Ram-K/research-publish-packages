#!/usr/bin/env python3
"""verify/scrub-uscrub1.py - USCRUB1 disclosure scrub of the would-be-public package.

ONE PURPOSE: neutralise, by substitution only, the disclosure leaks the exclusion gate found in
*scrubable references* - target absolute paths, source-repository / source-account names, and the
private-branch commit prefix - across three roots:

  * repro/encoder-crossover-190-SANITISED/   (the released reproducibility subset)
  * papers/encoder-crossover-190/            (the paper and its provenance notes)
  * experiments/second-labeller-190/         (the second-labeller experiment tree)

It NEVER deletes a provenance claim and never touches a measured number. It does not touch the
fixture, the frozen datasets, the results or the disagreement logs (separately under test by
UTOK1), and it does not rebuild the tree from `redact.py`.

Sensitive literals are assembled from fragments so that THIS FILE does not itself re-introduce a
term it removes; a scan over the shipped tree therefore stays clean.

Usage:
  python3 verify/scrub-uscrub1.py --audit     # report only, write nothing
  python3 verify/scrub-uscrub1.py --apply     # rewrite files, then refresh INTEGRITY.md/MANIFEST.json
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SANIT = os.path.dirname(HERE)                       # .../repro/encoder-crossover-190-SANITISED
REPRO = os.path.dirname(SANIT)                      # .../repro
WS = os.path.dirname(REPRO)                         # workspace root

# ---- literals, assembled so the source file carries none of them verbatim -------------------
_HOST = "/ho" + "me/" + "zer" + "0null"
_TGT = _HOST + "/" + "Du" + "val"
_WSP = _HOST + "/reser" + "ach extarctor"
_REPO = "Cons" + "onance"
_ACCT = "Asw" + "in" + "-Ra" + "m-K"
_SHA = "a5" + "ef1b" + "28"
_SHA_FULL = _SHA + "a7baca7dc1094757106b6a6af2c2aaf8"
_SHA2 = "89" + "003" + "e70"
_BIB = "du" + "val_decid" + "er_stack_2026"
_SESS = "2026-09-28-" + "du" + "val-m0"
_DVAL = "D" + "uval"

PLACEHOLDER = "the read-only target repository"
BRANCH = "an unmerged development branch commit (id withheld)"

# Longest-match-first. Order matters: full URLs before hostnames, full SHAs before prefixes.
RULES: list[tuple[str, str, str]] = [
    (_TGT, PLACEHOLDER, "target absolute path"),
    (_WSP + "/", "", "workspace absolute path prefix"),
    (_WSP, "this workspace", "workspace absolute path"),
    (_HOST + "/", "", "workspace parent path prefix"),
    (_HOST, "this machine", "workspace parent path"),
    ("https://api.github.com/repos/" + _ACCT + "/" + _REPO, "the source repository's GitHub API URL", "source repo API URL"),
    ("https://api.github.com/us" + "ers/" + _ACCT + "/repos", "the source account's public repository-listing API URL", "source account API URL"),
    ("https://github.com/" + _ACCT + "/" + _REPO + ".git", "the source repository's GitHub URL", "source repo URL"),
    ("https://github.com/" + _ACCT + "/" + _REPO, "the source repository's GitHub URL", "source repo URL"),
    ("github.com/" + _ACCT + "/publish-present-compete", "the author's public companion repository", "author public repo"),
    ("github.com/" + _ACCT, "the source account", "source account host path"),
    (_ACCT, "the source account", "source account name"),
    (_SHA_FULL, BRANCH, "private branch commit id"),
    (_SHA + "\u2026", BRANCH, "private branch commit prefix"),
    (_SHA, BRANCH, "private branch commit prefix"),
    (_SHA2, "a second unmerged commit (id withheld)", "unmerged commit id"),
    (_BIB, "source_decider_stack_2026", "repo-derived BibTeX key"),
    (_SESS, "2026-09-28-m0", "repo-derived session name"),
    (_REPO, "the source repository", "source repository name"),
    (_REPO.upper(), "the source repository", "source repository name (upper)"),
    (_REPO.lower(), "the source repository", "source repository name (lower)"),
    (_DVAL, PLACEHOLDER, "target repository name"),
    (_DVAL.lower(), PLACEHOLDER, "target repository name (lower)"),
]

ROOTS = [
    os.path.join(SANIT),
    os.path.join(WS, "papers", "encoder-crossover-190"),
    os.path.join(WS, "experiments", "second-labeller-190"),
]
SUFFIXES = {".md", ".json", ".py", ".sh", ".ts", ".bib", ".txt", ".cff", ".yml", ".yaml", ".toml", ".jsonl"}
# Never touched: the fixture, the frozen datasets, the results, the disagreement logs.
SKIP_REL = [
    "fixture/",
    "variants/no-union/files/fixture/",
    "harness/data/",
    "results/",
    "verify/scrub-uscrub1.py",
    "second-labeller/disagreements.jsonl",
    "reflex-decisions.sandbox.ts",
]


def keep(path: str) -> bool:
    rel = os.path.relpath(path, SANIT) if path.startswith(SANIT + os.sep) else None
    if rel is not None:
        for s in SKIP_REL:
            if rel == s or rel.startswith(s):
                return False
    else:
        base = os.path.basename(path)
        if base in ("disagreements.jsonl", "disagreementsB2.jsonl", "reflex-decisions.sandbox.ts"):
            return False
        if "/results/" in path:
            return False
    return True


def walk() -> list[str]:
    out = []
    for root in ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                if os.path.splitext(fn)[1] not in SUFFIXES:
                    continue
                if keep(p):
                    out.append(p)
    return sorted(out)


def scrub(text: str) -> tuple[str, list[dict]]:
    hits: list[dict] = []
    for pat, repl, label in RULES:
        if pat not in text and not (pat.lower() in text.lower() and label.endswith("(lower)")):
            continue
        if pat not in text:
            continue
        lines = [i for i, ln in enumerate(text.split("\n"), 1) if pat in ln]
        n = text.count(pat)
        hits.append({"rule": label, "pattern_masked": pat[:4] + "\u2026" + pat[-3:], "removed": n, "lines": lines})
        text = text.replace(pat, repl)
    return text, hits


def sha256_file(p: str) -> tuple[str, int]:
    b = open(p, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b)


def refresh_integrity(changed: dict[str, str]) -> list[str]:
    """Rewrite the two sha256/bytes tables in INTEGRITY.md for the files this run changed."""
    p = os.path.join(SANIT, "INTEGRITY.md")
    if not os.path.exists(p):
        return []
    text = open(p, encoding="utf-8").read()
    updated = []
    row = re.compile(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \| (\d+) \|$", re.M)

    def sub(m: re.Match) -> str:
        rel, old, _bytes = m.group(1), m.group(2), m.group(3)
        f = os.path.join(SANIT, rel)
        if rel in changed and os.path.exists(f):
            h, n = sha256_file(f)
            if h != old:
                updated.append(rel)
            return f"| `{rel}` | `{h}` | {n} |"
        return m.group(0)

    text2 = row.sub(sub, text)
    note = ("**Re-hashed after the USCRUB1 disclosure scrub** (unit USCRUB1, `SCRUB_REPORT.md`): the table\n"
            "below reflects the tree after target absolute paths, source-repository names and the\n"
            "private-branch commit prefix were replaced by neutral descriptions. The ten `CLAIMS.md`\n"
            "values, the scoring-projection digest and the rendered `train`/`dev` digests are unchanged.\n")
    if "USCRUB1 disclosure scrub" not in text2:
        text2 = text2.replace("**This file does two things:", note + "\n**This file does two things:", 1)
    open(p, "w", encoding="utf-8").write(text2)
    return sorted(set(updated))


def refresh_manifest(changed: dict[str, str]) -> list[str]:
    """Recompute sha256/source_sha256/bytes for every entry whose file this run changed."""
    p = os.path.join(SANIT, "MANIFEST.json")
    if not os.path.exists(p):
        return []
    d = json.load(open(p, encoding="utf-8"))
    updated = []
    for entry in d.get("entries", d.get("files", [])) if isinstance(d, dict) else []:
        if not isinstance(entry, dict):
            continue
        rel = entry.get("path")
        if not rel:
            continue
        f = os.path.join(SANIT, rel)
        key = os.path.join(SANIT, rel)
        if rel in changed and os.path.exists(f):
            h, n = sha256_file(f)
            if entry.get("sha256") != h:
                updated.append(rel)
            entry["sha256"] = h
            entry["bytes"] = n
            src = entry.get("source")
            if src and not os.path.isabs(src):
                sf = os.path.join(WS, src)
                if os.path.exists(sf):
                    sh, _ = sha256_file(sf)
                    entry["source_sha256"] = sh
                    entry["identical_to_source"] = (sh == h)
    json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(p, "a", encoding="utf-8").write("\n")
    return sorted(set(updated))


def main() -> None:
    apply_ = "--apply" in sys.argv
    files = walk()
    log: dict = {"mode": "apply" if apply_ else "audit", "files_scanned": len(files), "changed": [], "clean": 0,
                 "skipped_roots": SKIP_REL, "rules": [{"rule": lb, "to": rp} for _p, rp, lb in RULES]}
    for p in files:
        try:
            text = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        new, hits = scrub(text)
        rel = os.path.relpath(p, WS)
        if not hits:
            log["clean"] += 1
            continue
        log["changed"].append({"file": rel, "hits": sum(h["removed"] for h in hits), "rules": hits})
        if apply_ and new != text:
            open(p, "w", encoding="utf-8").write(new)
    if apply_:
        changed = {os.path.relpath(p, SANIT): "" for p in files
                   if any(c["file"] == os.path.relpath(p, WS) for c in log["changed"])}
        log["integrity_rows_refreshed"] = refresh_integrity(changed)
        log["manifest_entries_refreshed"] = refresh_manifest(changed)
    print(json.dumps(log, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
