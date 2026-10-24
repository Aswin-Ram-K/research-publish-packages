"""Shared helpers for the tools/package/ pipeline.

Every command takes ``--package <slug>``: a slug naming a directory under ``papers/``, or an
explicit path to a package directory (that is what lets ``--package scratch/uneutral10/package``
reproduce the shipped known-good numbers).
"""
import hashlib
import os
import sys

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
PROSE_KEYS = {"question", "options", "situation"}
CENSUS_TSV = os.path.join(WORKSPACE, "scratch", "uagnostic1", "census.tsv")


def add_package_arg(parser):
    parser.add_argument("--package", required=True,
                        help="slug under papers/ OR a path to a package directory")


def resolve_package(arg):
    cands = [arg] if os.path.isabs(arg) else []
    cands.append(os.path.join(WORKSPACE, arg))
    cands.append(os.path.join(WORKSPACE, "papers", arg))
    for c in cands:
        if os.path.isdir(c):
            return os.path.abspath(c)
    sys.stderr.write("FATAL: --package %r is not an existing directory and papers/%s is absent\n"
                     % (arg, arg))
    sys.exit(3)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root, skip_dirs=True):
    """(rel, full, size) for every regular file, sorted by rel."""
    out = []
    for dp, dn, fns in os.walk(root):
        if skip_dirs:
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
        dn.sort()
        for f in sorted(fns):
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            out.append((rel, full, os.path.getsize(full)))
    return out


def census_ids():
    """The 184 census identifiers (scratch/uagnostic1/census.tsv column 2)."""
    ids = []
    with open(CENSUS_TSV, encoding="utf-8") as fh:
        next(fh, None)
        for ln in fh:
            parts = ln.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[1]:
                ids.append(parts[1])
    return sorted(set(ids))


def die(msg, code=2):
    sys.stderr.write("FATAL: %s\n" % msg)
    sys.exit(code)
