#!/usr/bin/env python3
"""Keep byte baselines of the measurement harness so a later edit is attributable.

Why this exists: ``cell.py`` is untracked by git.  It was edited at 18:54:16Z on
2026-10-26 (sha e24e867b -> c29a9fb3) and no settled card claims the hunk, and
no prior copy of e24e867b survived anywhere in the tree -- so that change is
permanently unattributable.  An unversioned file edited by concurrent cards
cannot be attributed after the fact; it has to be attributable *before* the
edit, by having a byte copy of the pre-edit state.

Two subcommands, offline and read-only with respect to every source file:

    harness_baseline.py snapshot [--root DIR] [--label TS] [--out DIR]
        Copy every harness file into ``<out>/<label>/<repo-relative path>``,
        re-hash each copy and refuse (exit 1) if a copied byte differs from its
        source, then write ``MANIFEST.json`` with path/sha256/size/mtime_ns per
        file plus ``taken_at`` and ``harness_sha256_of_HARNESS_FILES`` (the
        cell.py recipe over the five HARNESS_FILES; fixture excluded because it
        is added per invocation, cell.py:128-135).

    harness_baseline.py verify <baseline-dir> [--root DIR]
        Recompute the sha256 of every file named in the manifest and print one
        line per file: ``same`` / ``moved`` / ``deleted`` / ``added`` (added =
        a harness file present now but absent from the manifest).  Exit 1 if
        anything differs, printing the baseline sha and the current sha.

Sources are never written.  Nothing here touches git, the network, or a row file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# cell.py:128-135 -- name used by the digest, repo-relative path.
HARNESS_FILES = (
    ("run_longrun.py", "experiments/ptr-engine/longrun/run_longrun.py"),
    ("client.py", "experiments/ptr-engine/longrun/client.py"),
    ("grade_v5.py", "experiments/ptr-engine/longrun/grade_v5.py"),
    ("analyze_stats.py", "experiments/ptr-engine/longrun/analyze_stats.py"),
    ("tools/det_verify.py", "experiments/ptr-engine/tools/det_verify.py"),
)

# Every other file in the harness lineage that a concurrent card can edit and
# git cannot recover: cell.py itself, the launcher, the grader entry points and
# the freeze helpers.
EXTRA_FILES = (
    "experiments/ptr-engine/longrun/cell.py",
    "experiments/ptr-engine/tools/run_a_star.py",
    "experiments/ptr-engine/longrun/spawn_record.py",
    "experiments/ptr-engine/longrun/exit_codes.py",
    "experiments/ptr-engine/tools/tree_freeze.py",
)

SNAPSHOT_PATHS = tuple(p for _, p in HARNESS_FILES) + EXTRA_FILES


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def harness_digest(root: str) -> str:
    """cell.py:332-346 recipe over the five HARNESS_FILES (fixture excluded)."""
    shas = {}
    for name, rel in HARNESS_FILES:
        shas[name] = sha256_file(os.path.join(root, rel))
    combined = hashlib.sha256()
    for name in sorted(shas):
        combined.update(("%s:%s\n" % (name, shas[name])).encode("utf-8"))
    return combined.hexdigest()


def cmd_snapshot(args) -> int:
    root = os.path.abspath(args.root)
    label = args.label or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dest = os.path.join(os.path.abspath(args.out), label)
    if os.path.isdir(dest) and os.listdir(dest) and not args.force:
        print("refusing: baseline already exists: %s (use --force)" % dest, file=sys.stderr)
        return 2

    taken_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entries = []
    for rel in SNAPSHOT_PATHS:
        src = os.path.join(root, rel)
        if not os.path.isfile(src):
            print("missing harness file: %s" % rel, file=sys.stderr)
            return 1
        st = os.stat(src)
        src_sha = sha256_file(src)
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        dst_sha = sha256_file(dst)
        if dst_sha != src_sha:
            print("COPY CORRUPTED: %s %s != %s" % (rel, dst_sha, src_sha), file=sys.stderr)
            return 1
        entries.append({
            "path": rel,
            "sha256": src_sha,
            "size": st.st_size,
            "mtime_ns": st.st_mtime_ns,
        })
        print("%s  %d  %s" % (src_sha[:8], st.st_size, rel))

    manifest = {
        "label": label,
        "taken_at": taken_at,
        "root": root,
        "harness_sha256_of_HARNESS_FILES": harness_digest(root),
        "harness_files_digest_recipe": "cell.py:332-346 over the five HARNESS_FILES; fixture excluded (per-invocation input)",
        "files": entries,
    }
    mpath = os.path.join(dest, "MANIFEST.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("baseline: %s" % dest)
    print("manifest_sha256: %s" % sha256_file(mpath))
    print("harness_sha256_of_HARNESS_FILES: %s" % manifest["harness_sha256_of_HARNESS_FILES"])
    return 0


def cmd_verify(args) -> int:
    bdir = os.path.abspath(args.baseline)
    with open(os.path.join(bdir, "MANIFEST.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    root = os.path.abspath(args.root or manifest.get("root") or REPO_ROOT)

    recorded = {e["path"]: e for e in manifest["files"]}
    differences = 0
    for rel in SNAPSHOT_PATHS:
        live = os.path.join(root, rel)
        base = recorded.get(rel)
        if base is None:
            print("added    %s  (present now, absent from baseline)" % rel)
            differences += 1
            continue
        if not os.path.isfile(live):
            print("deleted  %s  baseline %s -> MISSING" % (rel, base["sha256"][:8]))
            differences += 1
            continue
        cur = sha256_file(live)
        if cur == base["sha256"]:
            print("same     %s  %s" % (rel, cur[:8]))
        else:
            print("moved    %s  baseline %s -> now %s" % (rel, base["sha256"], cur))
            differences += 1

    print("---")
    print("%d differing file(s) against %s (root %s)" % (differences, bdir, root))
    return 1 if differences else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("snapshot", help="copy every harness file and write MANIFEST.json")
    s.add_argument("--root", default=REPO_ROOT)
    s.add_argument("--label", default=None, help="baseline directory name; default UTC timestamp")
    s.add_argument("--out", default=os.path.join(REPO_ROOT, "state", "harness-baselines"))
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_snapshot)

    v = sub.add_parser("verify", help="recompute shas and report same/moved/deleted/added")
    v.add_argument("baseline")
    v.add_argument("--root", default=None)
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
