#!/usr/bin/env python3
"""build_snapshot.py — freeze the trees an agentic episode is allowed to read.

WHY THIS EXISTS.  Stage 2 of the compaction A/B (docs/AGENTIC-COMPACTION-AB.md §3.2)
replaces the scripted replay with an episode in which the MODEL chooses what to read.
The moment a read is model-chosen, the root it resolves under stops being an
implementation detail and becomes part of the measurement: a read of the live tree is a
read of a repository that moves between runs, so two arms of the same episode would be
answering about different bytes and the cost difference between them would be
unattributable.  This tool produces the frozen root, and `run_longrun.py --root` +
`--snapshot-manifest` refuse to run against a root whose bytes have moved.

WHAT IS COPIED.  Exactly the four trees a task can legitimately be derived from and read:

    experiments/ptr-engine/ptr_engine
    experiments/ptr-engine/longrun
    experiments/ptr-engine/tools
    src/resextract

Two subtrees of `longrun/` are NOT copied, and the reason is not size:

  * `longrun/state/` — run artefacts (row files, logs, baselines).  A task's own
    evidence lives there; copying it would let the snapshot answer the question the
    snapshot is supposed to make the agent work for.
  * `longrun/manifests/` — pre-edit snapshots of the runner itself.  They are history,
    not source, and a second copy of `run_longrun.py` inside the root is a decoy that
    makes "which file did the agent read" ambiguous.

`__pycache__` and `*.pyc` are skipped for the same class of reason: they are derived
bytes that change without any source changing, so including them would make the root
digest move for a reason that is not a change.

THE DIGEST.  `root_sha256` is sha256 over `"<relpath>:<sha256>\\n"` for every copied
file, relpaths sorted — the same recipe `cell.py` uses for the harness pin, so a reader
who knows one knows the other.  The snapshot directory is NAMED by that digest, which
makes the freeze self-describing: `state/snapshots/<root_sha256>/` either holds the tree
that hashes to its own name or it is refused.

IDEMPOTENCE.  Re-running on an unchanged tree is a no-op: the directory already exists,
every file already matches, and `manifest.json` is not rewritten (same bytes, same
mtime).  A directory whose recorded `root_sha256` differs from the tree's is REFUSED,
never overwritten — a snapshot that silently becomes a different snapshot is worse than
no snapshot.

USAGE
    .venv/bin/python experiments/ptr-engine/longrun/tools/build_snapshot.py
    .venv/bin/python experiments/ptr-engine/longrun/tools/build_snapshot.py --json

Exit codes: 0 built or unchanged, 2 refused (missing tree, foreign directory).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(os.path.dirname(HERE))          # experiments/ptr-engine
ROOT = os.path.dirname(os.path.dirname(ENGINE))          # workspace root

#: The trees a task may be derived from and read.  Repo-root-relative, in copy order.
SNAPSHOT_TREES = (
    "experiments/ptr-engine/ptr_engine",
    "experiments/ptr-engine/longrun",
    "experiments/ptr-engine/tools",
    "src/resextract",
)

#: Subtrees that are artefacts or history, never source.  See the module docstring.
SNAPSHOT_SKIP_DIRS = ("__pycache__", "state", "manifests")
SNAPSHOT_SKIP_SUFFIXES = (".pyc", ".pyo")

MANIFEST_NAME = "manifest.json"
MANIFEST_SCHEMA = "snapshot-manifest/1"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(root: str) -> dict:
    """``{relpath: sha256}`` for every file the snapshot carries, sorted by relpath."""
    files: dict = {}
    for tree in SNAPSHOT_TREES:
        base = os.path.join(root, tree)
        if not os.path.isdir(base):
            raise SystemExit("snapshot tree is missing: %s" % tree)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SNAPSHOT_SKIP_DIRS)
            for name in sorted(filenames):
                if name.endswith(SNAPSHOT_SKIP_SUFFIXES):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                files[rel] = sha256_file(full)
    return dict(sorted(files.items()))


def root_digest(files: dict) -> str:
    """sha256 over ``"<relpath>:<sha256>\\n"`` for sorted relpaths — cell.py's recipe."""
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(("%s:%s\n" % (rel, files[rel])).encode("utf-8"))
    return h.hexdigest()


def manifest_bytes(files: dict, root_sha: str) -> bytes:
    """The manifest's exact bytes.  Deterministic, so an unchanged tree is a no-op."""
    doc = {"schema": MANIFEST_SCHEMA, "root_sha256": root_sha, "files": files}
    return (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8")


def read_manifest(path: str):
    """The manifest at `path`, or None when it is absent or unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    return doc if isinstance(doc, dict) else None


def _tree_matches(target: str, files: dict) -> bool:
    """Whether every manifest entry is present under `target` with the recorded bytes."""
    for rel, want in files.items():
        try:
            if sha256_file(os.path.join(target, rel)) != want:
                return False
        except OSError:
            return False
    return True


def build(root: str, dest_root: str) -> dict:
    """Freeze `root`'s snapshot trees under `dest_root/<root_sha256>/`.

    Returns ``{"root_sha256", "dir", "files", "state"}`` where state is ``created``,
    ``unchanged`` or ``repaired``.  Raises SystemExit(2) on a foreign directory.
    """
    files = collect(root)
    root_sha = root_digest(files)
    target = os.path.join(dest_root, root_sha)
    manifest_path = os.path.join(target, MANIFEST_NAME)

    if os.path.isdir(target):
        existing = read_manifest(manifest_path)
        if existing is None:
            raise SystemExit(
                "refusing to overwrite %s: it exists and carries no readable %s"
                % (target, MANIFEST_NAME))
        if existing.get("root_sha256") != root_sha:
            raise SystemExit(
                "refusing to overwrite %s: its manifest records root_sha256=%s but this "
                "tree hashes to %s" % (target, existing.get("root_sha256"), root_sha))
        if _tree_matches(target, files):
            return {"root_sha256": root_sha, "dir": target, "files": len(files),
                    "state": "unchanged"}
        state = "repaired"
    else:
        state = "created"

    for rel in files:
        dest = os.path.join(target, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(os.path.join(root, rel), dest)
    with open(manifest_path, "wb") as fh:
        fh.write(manifest_bytes(files, root_sha))
    return {"root_sha256": root_sha, "dir": target, "files": len(files), "state": state}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="freeze the trees an agentic episode may read, with a per-file manifest")
    ap.add_argument("--root", default=ROOT, metavar="DIR",
                    help="workspace root to snapshot (default: this repo)")
    ap.add_argument("--dest", default=None, metavar="DIR",
                    help="snapshot parent (default: <root>/state/snapshots)")
    ap.add_argument("--json", action="store_true",
                    help="print the result as one JSON object instead of a line")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    dest = args.dest or os.path.join(args.root, "state", "snapshots")
    result = build(args.root, dest)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("root_sha256=%s files=%d state=%s dir=%s"
              % (result["root_sha256"], result["files"], result["state"], result["dir"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
