#!/usr/bin/env python3
"""classify.py -- class the census/OOV identifiers of a package tree.

SOURCES, STATED BECAUSE TWO DIFFERENT ID LISTS EXIST AND QUOTING THE WRONG ONE IS A KNOWN ERROR
  * ``mechanism`` authority  = the 184 distinct ids in scratch/uagnostic1/census.tsv column 2
                               (cat values there are field/filename/kind/kind-dotted/path/pointer/
                               role/symbol/tool-cap; the file carries NO literal "c-mechanism"
                               string).  classify_oov.py labels these ``c-mechanism-*``.
  * ``33-token class``       = the NEUTRAL-TAG/v1 token list (10 roles + 20 enums + 2 fragments +
                               MATERIALISE in scratch/uneutral10/scan.py).  It is NOT the mechanism
                               authority and must not be quoted as the census.
  * released-schema / third-party / encoding-artefact / unclassified = scratch/ugate1/'s own rules
                               (classify_oov.py), carried here unchanged.

Canonical class names (default output): released-schema, third-party/incidental,
mechanism-stimulus, mechanism-outside, encoding-artefact, unclassified.
``--legacy-names`` reproduces scratch/ugate1/classify_oov.py's a-schema / b-thirdparty /
c-mechanism-stimulus / c-mechanism-outside / d-artifact byte-for-byte.

``unclassified`` is DECLARED but unreachable in classify_oov.py: its else-branch assigns
b-thirdparty.  This port preserves that reachability exactly rather than inventing a new bucket.
"""
import argparse
import collections
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pkg

DATA_EXT = (".json", ".jsonl")
CANON = {"a-schema": "released-schema",
         "b-thirdparty": "third-party/incidental",
         "c-mechanism-stimulus": "mechanism-stimulus",
         "c-mechanism-outside": "mechanism-outside",
         "d-artifact": "encoding-artefact"}
LEGACY = {v: k for k, v in CANON.items()}

# 30-token stimulus class used only to split c-mechanism into stimulus/outside
STIM30 = set("""editor reasoner model.call attached verifier fs.read fs.write test.run net.fetch
detached topology output-only code-inspector memory.write memory-curator policyHash MATERIALISE
expanded[ broker admit( researcher critic web.fetch code-review escalation expiresAtEpoch
ToolCallIR reasonerCalls canRequestEscalation MutationProposal""".split())
ID_RE = re.compile(r"^(?:fam[br]|ex11b|ex11a|N\d\d-\d+|K\d\d|N\d\d|B\d\d|S\d\d)\d*$")


def load_vocab(emit, name):
    path = os.path.join(emit, "vocabulary", name)
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        _pkg.die("cannot read vocabulary file: %s" % path, 2)
    out = set()
    with open(path, encoding="utf-8") as h:
        for line in h:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for w in line.split():
                out.add(w)
    return out


def mechanism_ids():
    return _pkg.census_ids()


def walk_json(obj, data_keys, data_string_values, keypath=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                data_keys[k] += 1
            walk_json(v, data_keys, data_string_values, keypath + "/" + str(k))
    elif isinstance(obj, list):
        for v in obj:
            walk_json(v, data_keys, data_string_values, keypath)
    elif isinstance(obj, str):
        data_string_values[obj] += 1


def main():
    ap = argparse.ArgumentParser(description="class census/OOV identifiers of a package tree")
    _pkg.add_package_arg(ap)
    ap.add_argument("--oov", required=True, help="OOV tsv (token/occurrences/why/file_classes)")
    ap.add_argument("--out", default=None, help="write the classified tsv here (default stdout only)")
    ap.add_argument("--legacy-names", action="store_true",
                    help="emit classify_oov.py's a-/b-/c-/d- class strings")
    a = ap.parse_args()
    emit = _pkg.resolve_package(a.package)

    declared = load_vocab(emit, "public.txt")
    declared_lower = {d.lower() for d in declared}
    words = load_vocab(emit, "english.txt") | load_vocab(emit, "code.txt")
    census = set(mechanism_ids())
    census_norm = {c.rstrip("([") for c in census}
    census_lower = {c.lower() for c in census}

    data_keys = collections.Counter()
    data_string_values = collections.Counter()
    for dirpath, dirnames, filenames in os.walk(emit):
        dirnames[:] = [d for d in dirnames if d not in _pkg.SKIP_DIRS]
        for name in sorted(filenames):
            rel = os.path.relpath(os.path.join(dirpath, name), emit)
            if not rel.endswith(DATA_EXT):
                continue
            try:
                txt = open(os.path.join(dirpath, name), encoding="utf-8").read()
            except (OSError, ValueError):
                continue
            try:
                if rel.endswith(".jsonl"):
                    for line in txt.splitlines():
                        if line.strip():
                            walk_json(json.loads(line), data_keys, data_string_values)
                else:
                    walk_json(json.loads(txt), data_keys, data_string_values)
            except (ValueError, TypeError):
                pass

    def has_census_token(tok):
        if tok in census or tok.lower() in census_lower:
            return True
        for chunk in re.split(r"[^A-Za-z0-9]+", tok):
            if chunk and chunk in census_norm:
                return True
        parts = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+", tok)
        if parts and "".join(parts) in census_norm:
            return True
        return False

    def has_stimulus(tok):
        parts = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+", tok)
        for c in STIM30:
            cc = c.rstrip("([")
            if cc == tok or cc == tok.lower():
                return True
        for p in parts:
            for c in STIM30:
                cc = c.rstrip("([")
                if p == cc or p.lower() == cc.lower():
                    return True
        joined = "".join(parts)
        return any(joined == c.rstrip("([") for c in STIM30)

    rows = list(csv.DictReader(open(a.oov, encoding="utf-8"), delimiter="\t"))
    out = []
    for r in rows:
        tok = r["token"]
        classes = {part.rsplit("=", 1)[0] for part in r["file_classes"].split(",")}
        if has_census_token(tok):
            cls = "c-mechanism-stimulus" if has_stimulus(tok) else "c-mechanism-outside"
        elif tok in data_keys or ID_RE.match(tok) or (tok in declared or tok.lower() in declared_lower):
            cls = "a-schema"
        elif tok.strip("-_.").isdigit() or re.match(r"^[0-9a-f]{6,}$", tok):
            cls = "d-artifact"
        else:
            cls = "b-thirdparty"
        r["class"] = cls
        r["data_key"] = "yes" if tok in data_keys else "no"
        r["file_classes_set"] = sorted(classes)
        out.append(r)

    name_of = (lambda c: c) if a.legacy_names else (lambda c: CANON.get(c, c))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("token\toccurrences\tclass\twhy\tdata_key\tfile_classes\n")
            for r in out:
                fh.write("%s\t%d\t%s\t%s\t%s\t%s\n" % (r["token"], int(r["occurrences"]),
                                                       name_of(r["class"]), r["why"], r["data_key"],
                                                       ",".join(r["file_classes_set"])))

    agg = collections.defaultdict(lambda: [0, 0])
    for r in out:
        agg[r["class"]][0] += 1
        agg[r["class"]][1] += int(r["occurrences"])
    print("distinct tokens:", len(out))
    for k in sorted(agg):
        print("%-24s distinct=%-5d occurrences=%d" % (name_of(k), agg[k][0], agg[k][1]))
    print()
    print("data_json_keys_distinct:", len(data_keys))
    print("data_string_values_distinct:", len(data_string_values))
    print("declared public.txt:", len(declared))
    print()
    print("=== class c tokens (mechanism) that the current gate flags ===")
    for r in sorted([r for r in out if r["class"].startswith("c-")],
                    key=lambda x: -int(x["occurrences"])):
        print("%-28s %5d  %-22s %s" % (r["token"], int(r["occurrences"]), name_of(r["class"]),
                                       ",".join(r["file_classes_set"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
