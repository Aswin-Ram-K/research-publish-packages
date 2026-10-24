#!/usr/bin/env python3
"""census.py -- count census-identifier occurrences over a package tree.

Behaviour carried from scratch/ubij1/census_one.py (decoded JSON walk; inside / outside /
JSON-keys split; by-class and by-identifier tables) and scratch/uneutral1/scan.py (raw-text
totality scan, exposed as ``--mode raw``).

In-stimulus is DEFINED as the values of the fixture's ``question`` / ``options`` / ``situation``
fields; every other string value of a decoded JSON/JSONL file is "outside", and object KEYS are
counted separately.
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pkg

PROSE = {"question", "options", "situation"}


def classify(rel):
    low = rel.lower()
    if rel in ("harness/data/train.jsonl", "harness/data/dev.jsonl"):
        return "data-jsonl"
    if low.endswith(".jsonl"):
        return "data-jsonl-other"
    if low.endswith(".json"):
        return "json"
    if low.endswith(".md"):
        return "prose-md"
    if low.endswith((".py", ".sh", ".bash")):
        return "tooling"
    if low.endswith(".ts"):
        return "ts"
    return "other"


def decoded(tree, ids):
    inside = collections.Counter()
    outside = collections.Counter()
    keys = collections.Counter()
    cls_inside = collections.Counter()
    cls_outside = collections.Counter()
    cls_keys = collections.Counter()
    cls_ids = collections.defaultdict(collections.Counter)
    nfiles = 0

    for dp, dn, fns in os.walk(tree):
        dn[:] = [d for d in dn if d not in _pkg.SKIP_DIRS]
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, tree)
            ext = os.path.splitext(fn)[1].lower()
            cls = classify(rel)
            try:
                txt = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            nfiles += 1
            if ext in (".json", ".jsonl"):
                def cl(s, k):
                    tgt = inside if k in PROSE else outside
                    low = s.lower()
                    for i in ids:
                        c = low.count(i.lower())
                        if c:
                            tgt[i] += c
                            (cls_inside if k in PROSE else cls_outside)[cls] += c
                            cls_ids[cls][i] += c

                def walk(o):
                    if isinstance(o, dict):
                        for k, v in o.items():
                            if isinstance(k, str):
                                low = k.lower()
                                for i in ids:
                                    c = low.count(i.lower())
                                    if c:
                                        keys[i] += c
                                        cls_keys[cls] += c
                                        cls_ids[cls][i] += c
                            if isinstance(v, str):
                                cl(v, k)
                            elif isinstance(v, list):
                                for x in v:
                                    if isinstance(x, str):
                                        cl(x, k)
                                    else:
                                        walk(x)
                            else:
                                walk(v)
                    elif isinstance(o, list):
                        for x in o:
                            walk(x)

                if ext == ".jsonl":
                    for ln in txt.splitlines():
                        if ln.strip():
                            try:
                                walk(json.loads(ln))
                            except Exception:
                                pass
                else:
                    try:
                        walk(json.loads(txt))
                    except Exception:
                        pass
            else:
                low = txt.lower()
                for i in ids:
                    c = low.count(i.lower())
                    if c:
                        outside[i] += c
                        cls_outside[cls] += c
                        cls_ids[cls][i] += c

    ti, to, tk = sum(inside.values()), sum(outside.values()), sum(keys.values())
    print(f"tree: {tree}")
    print(f"files scanned: {nfiles}")
    print(f"distinct identifiers hit: {len(set(inside) | set(outside) | set(keys))} of {len(ids)}")
    print(f"TOTAL OCCURRENCES (decoded walk): {ti + to + tk}")
    print(f"  inside stimulus (question/options/situation values): {ti}  distinct={len(inside)}")
    print(f"  outside stimulus (all other values + non-JSON text): {to}")
    print(f"  JSON object keys: {tk}")
    print("\n-- by class (inside / outside / keys / class-total) --")
    for c in sorted(set(cls_inside) | set(cls_outside) | set(cls_keys)):
        a, b, d = cls_inside[c], cls_outside[c], cls_keys[c]
        print(f"  {c:18s} inside={a:6d} outside={b:6d} keys={d:6d} total={a + b + d:6d}")
    print("\n-- by identifier (inside | outside | keys | class) --")
    for i in sorted(set(inside) | set(outside) | set(keys),
                    key=lambda x: (-(inside[x] + outside[x] + keys[x]), x)):
        if inside[i] or outside[i] or keys[i]:
            cs = ",".join(f"{c}:{n}" for c, n in cls_ids.items() if cls_ids[c][i]) or "-"
            print(f"{i}\tinside={inside[i]}\toutside={outside[i]}\tkeys={keys[i]}\t{cs}")
    return 0


def raw(tree, ids):
    pats = [(i, re.compile(re.escape(i), re.I)) for i in ids]
    total = collections.Counter()
    files = collections.Counter()
    nfiles = 0
    for root, dirs, fs in os.walk(tree):
        dirs[:] = [d for d in dirs if d not in _pkg.SKIP_DIRS]
        for f in fs:
            p = os.path.join(root, f)
            try:
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
            except (UnicodeDecodeError, IsADirectoryError):
                continue
            nfiles += 1
            for ident, rx in pats:
                n = len(rx.findall(text))
                if n:
                    total[ident] += n
                    files[ident] += 1
    hit = sorted(total)
    print(f"tree: {tree}")
    print(f"files scanned: {nfiles}")
    print(f"distinct identifiers hit: {len(hit)} of {len(ids)}")
    print(f"total occurrences: {sum(total.values())}")
    for i in hit:
        print(f"  {total[i]:7d}  {files[i]:3d}f  {i}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="identifier census over a package tree")
    _pkg.add_package_arg(ap)
    ap.add_argument("--mode", choices=("decoded", "raw"), default="decoded",
                    help="decoded = census_one.py walk (default); raw = scan.py raw-text scan")
    a = ap.parse_args()
    tree = _pkg.resolve_package(a.package)
    ids = _pkg.census_ids()
    return decoded(tree, ids) if a.mode == "decoded" else raw(tree, ids)


if __name__ == "__main__":
    sys.exit(main())
