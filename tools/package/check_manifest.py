#!/usr/bin/env python3
"""check_manifest.py -- independent re-hash of every file listed in a package MANIFEST.json.

Reads no stored digest as truth: it re-hashes and re-stats every listed path and walks the tree
for files the manifest omitted.  Prints EXACTLY FIVE zero-counts and exits non-zero if any is
non-zero:

    missing  hash_mismatch  size_mismatch  unlisted  listed_but_absent

Sources: scratch/utool1/check_manifest6.py (list/sort/dup checks) and scratch/uver24/
(check_manifest_uver24.py -- the five-count shape).  The manifest's own manifest_self digest is
reported as information only; the exit status is driven by the five counts alone.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pkg

SELF = "MANIFEST.json"


def main():
    ap = argparse.ArgumentParser(description="independent manifest checker")
    _pkg.add_package_arg(ap)
    a = ap.parse_args()
    tree = _pkg.resolve_package(a.package)
    mp = os.path.join(tree, SELF)
    if not os.path.isfile(mp):
        _pkg.die("no %s in %s" % (SELF, tree), 2)
    raw = open(mp, "rb").read()
    m = json.loads(raw)
    entries = m["files"]
    listed = [e["path"] for e in entries]
    listedset = set(listed)

    missing, hash_bad, size_bad = [], [], []
    for e in entries:
        p = os.path.join(tree, e["path"])
        if not os.path.isfile(p):
            missing.append(e["path"])
            continue
        if os.path.getsize(p) != e["bytes"]:
            size_bad.append(e["path"])
        if _pkg.sha256_file(p) != e["sha256"]:
            hash_bad.append(e["path"])

    present = {rel for rel, full, sz in _pkg.iter_files(tree)}
    unlisted = sorted(present - listedset - {SELF})
    listed_absent = sorted(listedset - present)

    print(f"missing={len(missing)} hash_mismatch={len(hash_bad)} size_mismatch={len(size_bad)} "
          f"unlisted={len(unlisted)} listed_but_absent={len(listed_absent)}")
    for name, lst in (("MISSING", missing), ("HASH", hash_bad), ("SIZE", size_bad),
                      ("UNLISTED", unlisted), ("LISTED_ABSENT", listed_absent)):
        for x in lst:
            print(f"  {name}: {x}")

    # manifest_self is information, not a gate: recompute it the documented way.
    body = {k: v for k, v in m.items() if k != "manifest_self"}
    utc = body.get("generated_utc", "")
    canon = json.dumps(body, indent=2, sort_keys=True).replace(utc, "")
    self_ok = hashlib.sha256(canon.encode()).hexdigest() == m.get("manifest_self")
    print(f"manifest_self_recomputes={self_ok} (blank generated_utc; drop manifest_self; "
          f"sort_keys indent=2)")

    bad = bool(missing or hash_bad or size_bad or unlisted or listed_absent)
    print("VERDICT", "FAIL" if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
