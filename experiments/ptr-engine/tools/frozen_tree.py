#!/usr/bin/env python3
"""frozen_tree.py — verify a snapshot, not a moving tree.

A verifier that reads the live tree holds every author whose write path touches one
of the files it reads: one verifier serialises a whole batch of cards. This tool
removes that contention by making the verifier's jurisdiction a *frozen copy* with a
recorded identity:

* ``snapshot(paths, dest)`` copies named files (and directories, recursively) into
  ``dest`` preserving relative paths and writes ``dest/SNAPSHOT.json`` with
  ``relpath`` / ``sha256`` / ``bytes`` / ``mtime_ns`` per file, plus a
  ``snapshot_sha256`` that names exactly the bytes the snapshot is.
* ``verify(snapshot_dir, command)`` re-digests every listed file **before** the
  run, runs the command with ``cwd`` inside the snapshot, and re-digests **after**.
  ``inputs_unchanged: false`` is fatal: a verification whose inputs moved is not a
  verdict (exit 2).

``snapshot_sha256`` is the sha256 of the canonical JSON of the per-file digests
(``relpath`` + ``sha256``, sorted, no whitespace). It is deliberately independent of
copy time and of ``mtime_ns``/``bytes``: the same bytes snapshotted at different
times keep one identity, and a single changed byte changes it.

Exit codes (CLI): 0 ok · 1 command failed · 2 snapshot mutated or invalid ·
3 usage / refused snapshot.

Constraints honoured: stdlib only, no network, no ``git`` invocation anywhere. The
filesystem is copied directly; ``.git`` is never entered or read. A refused snapshot
never leaves a partial ``dest``: everything is written to a sibling temp directory
and made visible with a single ``os.rename`` (temp-dir + rename; removed on failure).

Usage::

  python3 experiments/ptr-engine/tools/frozen_tree.py snapshot --dest DIR PATH...
  python3 experiments/ptr-engine/tools/frozen_tree.py verify --snapshot DIR -- CMD...
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TOOL_VERSION = 1
MANIFEST_NAME = "SNAPSHOT.json"

EXIT_OK = 0
EXIT_CMD_FAILED = 1
EXIT_SNAPSHOT_BAD = 2
EXIT_USAGE = 3

TAIL_CHARS = 4000
SKIP_DIRS = frozenset({".git"})


class SnapshotRefused(Exception):
    """A snapshot input was refused; the message always names the offending path."""


# --------------------------------------------------------------------- helpers

def _root(root: str | os.PathLike | None) -> Path:
    return Path(root).resolve() if root is not None else Path.cwd().resolve()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_digests(files) -> str:
    """Canonical JSON of the per-file digests; the only thing snapshot_sha256 hashes."""
    pairs = [{"relpath": f["relpath"], "sha256": f["sha256"]} for f in files]
    pairs.sort(key=lambda p: p["relpath"])
    return json.dumps(pairs, sort_keys=True, separators=(",", ":"))


def snapshot_sha256(files) -> str:
    return hashlib.sha256(canonical_digests(files).encode("utf-8")).hexdigest()


def _inside(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def _relpath(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


# ------------------------------------------------------------------- collection

def _collect_one(root: Path, arg: str | os.PathLike) -> list[tuple[Path, str]]:
    """Resolve one CLI path argument into (source_file, relpath) pairs."""
    raw = Path(arg)
    src = (root / raw) if not raw.is_absolute() else raw
    shown = str(arg)

    if not os.path.lexists(src):
        raise SnapshotRefused(f"missing path: {shown} (no such file or directory under {root})")

    resolved = src.resolve()
    if src.is_symlink() and not _inside(root, resolved):
        raise SnapshotRefused(
            f"symlink escapes workspace root: {shown} -> {resolved} (root {root})"
        )
    if not _inside(root, resolved):
        raise SnapshotRefused(f"path outside workspace root: {shown} -> {resolved} (root {root})")
    if not resolved.exists():
        raise SnapshotRefused(f"missing path: {shown} (dangling symlink to {resolved})")

    out: list[tuple[Path, str]] = []
    if resolved.is_dir():
        for dirpath, dirnames, filenames in os.walk(resolved, followlinks=False):
            here = Path(dirpath)
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                f = here / name
                if f.is_symlink():
                    target = f.resolve()
                    if not _inside(root, target):
                        raise SnapshotRefused(
                            f"symlink escapes workspace root: {_safe(f, root)} -> {target}"
                        )
                    if not target.is_file():
                        raise SnapshotRefused(f"unsupported symlink (not a regular file): {_safe(f, root)}")
                if not f.is_file():
                    continue
                out.append((f, _safe(f, root)))
    elif resolved.is_file():
        out.append((resolved, _relpath(root, resolved)))
    else:
        raise SnapshotRefused(f"unsupported path type (not file/dir): {shown}")

    if not out:
        raise SnapshotRefused(f"path contains no files: {shown}")
    return out


def _safe(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _import_closure(root: Path, files: list[tuple[Path, str]]) -> list[tuple[Path, str]]:
    """Best-effort: add same-root python modules imported by the given .py files.

    Only top-level (absolute, non-dotted-runtime) imports are followed, resolving
    ``mod`` to ``<root>/mod.py`` / ``<root>/mod/__init__.py`` and the same next to the
    importing file. STDlib and unfindable modules are ignored — this is a convenience,
    not an environment resolver.
    """
    seen = {rel for _p, rel in files}
    queue = [p for p, _rel in files if p.suffix == ".py"]
    extra: list[tuple[Path, str]] = []
    while queue:
        cur = queue.pop()
        try:
            tree = ast.parse(cur.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            for name in names:
                parts = name.split(".")
                for base in (root, cur.parent):
                    cand = base.joinpath(*parts[:-1], parts[-1] + ".py") if len(parts) > 1 else base / (parts[0] + ".py")
                    init = base.joinpath(*parts, "__init__.py")
                    for c in (cand, init):
                        if c.is_file() and _inside(root, c.resolve()):
                            rel = _safe(c, root)
                            if rel not in seen:
                                seen.add(rel)
                                extra.append((c.resolve(), rel))
                                if c.suffix == ".py":
                                    queue.append(c.resolve())
    return extra


# --------------------------------------------------------------------- snapshot

def snapshot(paths, dest, include_imports: bool = False, root=None) -> dict:
    """Copy ``paths`` into ``dest`` at recorded sha256s; write ``dest/SNAPSHOT.json``.

    Refuses (``SnapshotRefused``, naming the path) on a missing path, a path outside
    the workspace root, or a symlink escaping it. Nothing is left at ``dest`` when the
    snapshot is refused: the tree is built in a sibling temp dir and renamed in.
    """
    if not paths:
        raise SnapshotRefused("no paths given")
    root_p = _root(root)
    dest_p = Path(dest)

    if dest_p.exists():
        raise SnapshotRefused(f"dest already exists: {dest_p}")
    dest_p.parent.mkdir(parents=True, exist_ok=True)

    files: list[tuple[Path, str]] = []
    for arg in paths:
        files.extend(_collect_one(root_p, arg))
    if include_imports:
        files.extend(_import_closure(root_p, files))

    # de-duplicate by relpath, first occurrence wins (stable, deterministic)
    dedup: dict[str, Path] = {}
    for src, rel in files:
        dedup.setdefault(rel, src)

    tmp = Path(tempfile.mkdtemp(prefix=".frozen_tree.", dir=str(dest_p.parent)))
    try:
        entries = []
        for rel in sorted(dedup):
            src = dedup[rel]
            out = tmp / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, out)
            st = src.stat()
            os.utime(out, ns=(st.st_atime_ns, st.st_mtime_ns))
            digest = _sha256_file(out)
            if digest != _sha256_file(src):
                raise SnapshotRefused(f"copy is not byte-identical: {rel}")
            entries.append(
                {
                    "relpath": rel,
                    "sha256": digest,
                    "bytes": int(st.st_size),
                    "mtime_ns": int(st.st_mtime_ns),
                }
            )

        manifest = {
            "tool": "frozen_tree",
            "version": TOOL_VERSION,
            "root": str(root_p),
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "files": entries,
            "snapshot_sha256": snapshot_sha256(entries),
        }
        (tmp / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.rename(tmp, dest_p)  # atomic publish; dest never exists partially
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return manifest


# ----------------------------------------------------------------------- verify

def _digest_inputs(snap: Path, manifest: dict) -> tuple[dict[str, str], list[str]]:
    """Return {relpath: current sha256 or "" if gone} and the changed relpaths."""
    current: dict[str, str] = {}
    changed: list[str] = []
    for f in manifest.get("files", []):
        rel = f["relpath"]
        target = snap / rel
        if not target.is_file():
            current[rel] = ""
            changed.append(rel)
            continue
        digest = _sha256_file(target)
        current[rel] = digest
        if digest != f["sha256"]:
            changed.append(rel)
    return current, sorted(changed)


def verify(snapshot_dir, command, cwd=None, timeout=None) -> dict:
    """Run ``command`` inside a frozen snapshot and report whether its inputs held."""
    snap = Path(snapshot_dir).resolve()
    manifest_path = snap / MANIFEST_NAME
    result = {
        "command": list(command),
        "exit_code": None,
        "duration_ms": 0,
        "inputs_unchanged": False,
        "changed": [],
        "snapshot_sha256": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = manifest["files"]
        result["snapshot_sha256"] = manifest["snapshot_sha256"]
        if snapshot_sha256(files) != manifest["snapshot_sha256"]:
            raise ValueError("manifest snapshot_sha256 does not match its own per-file digests")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result["stderr_tail"] = f"INVALID SNAPSHOT: {exc}"
        return result

    _cur, changed_before = _digest_inputs(snap, manifest)
    if changed_before:
        result["changed"] = changed_before
        result["stderr_tail"] = (
            "SNAPSHOT ALREADY MUTATED before the run: " + ", ".join(changed_before)
        )
        return result

    workdir = snap if cwd is None else (snap / cwd if not Path(cwd).is_absolute() else Path(cwd))
    if not workdir.is_dir():
        result["stderr_tail"] = f"INVALID SNAPSHOT: cwd is not a directory inside the snapshot: {workdir}"
        return result

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    started = time.monotonic()
    try:
        proc = subprocess.run(
            list(command),
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        out, err, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        err = (exc.stderr or "") if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        err += f"\nTIMEOUT after {timeout}s"
        code = 124
    except FileNotFoundError as exc:
        out, err, code = "", f"command not found: {exc}", 127
    duration_ms = int((time.monotonic() - started) * 1000)

    _cur2, changed_after = _digest_inputs(snap, manifest)
    result.update(
        exit_code=code,
        duration_ms=duration_ms,
        inputs_unchanged=not changed_after,
        changed=changed_after,
        stdout_tail=out[-TAIL_CHARS:],
        stderr_tail=err[-TAIL_CHARS:],
    )
    return result


def verdict_exit_code(result: dict) -> int:
    """0 ok · 1 command failed · 2 snapshot mutated/invalid (fatal, beats the command)."""
    if result.get("exit_code") is None or not result.get("inputs_unchanged"):
        return EXIT_SNAPSHOT_BAD
    return EXIT_OK if result.get("exit_code") == 0 else EXIT_CMD_FAILED


# -------------------------------------------------------------------------- CLI

def _human_snapshot(manifest: dict, dest) -> str:
    lines = [
        f"snapshot {dest}",
        f"  snapshot_sha256 {manifest['snapshot_sha256']}",
        f"  files {len(manifest['files'])}",
    ]
    lines += [f"  {f['relpath']}  {f['sha256'][:16]}…  {f['bytes']}B" for f in manifest["files"]]
    return "\n".join(lines)


def _human_verify(result: dict) -> str:
    verdict = "OK" if verdict_exit_code(result) == EXIT_OK else (
        "MUTATED" if not result.get("inputs_unchanged") else "FAILED"
    )
    lines = [
        f"{verdict}: exit {result['exit_code']} in {result['duration_ms']}ms",
        f"  snapshot_sha256 {result['snapshot_sha256']}",
        f"  inputs_unchanged {str(result['inputs_unchanged']).lower()}",
    ]
    if result["changed"]:
        lines.append("  changed " + ", ".join(result["changed"]))
    if result["stdout_tail"].strip():
        lines.append("  stdout_tail " + result["stdout_tail"].strip().splitlines()[-1][:200])
    if result["stderr_tail"].strip():
        lines.append("  stderr_tail " + result["stderr_tail"].strip().splitlines()[-1][:200])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return EXIT_OK if argv else EXIT_USAGE

    mode, rest = argv[0], argv[1:]

    if mode == "snapshot":
        ap = argparse.ArgumentParser(prog="frozen_tree.py snapshot")
        ap.add_argument("--dest", required=True)
        ap.add_argument("--root", default=None)
        ap.add_argument("--include-imports", action="store_true")
        ap.add_argument("--json", action="store_true")
        ap.add_argument("paths", nargs="+")
        try:
            ns = ap.parse_args(rest)
        except SystemExit:
            return EXIT_USAGE
        try:
            manifest = snapshot(
                ns.paths, ns.dest, include_imports=ns.include_imports, root=ns.root
            )
        except SnapshotRefused as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return EXIT_USAGE
        if ns.json:
            print(json.dumps(manifest, sort_keys=True))
        else:
            print(_human_snapshot(manifest, ns.dest))
        return EXIT_OK

    if mode == "verify":
        if "--" in rest:
            i = rest.index("--")
            opts, command = rest[:i], rest[i + 1:]
        else:
            opts, command = rest, []
        ap = argparse.ArgumentParser(prog="frozen_tree.py verify")
        ap.add_argument("--snapshot", required=True)
        ap.add_argument("--cwd", default=None)
        ap.add_argument("--timeout", type=float, default=None)
        ap.add_argument("--json", action="store_true")
        try:
            ns = ap.parse_args(opts)
        except SystemExit:
            return EXIT_USAGE
        if not command:
            print("usage: frozen_tree.py verify --snapshot DIR -- CMD...", file=sys.stderr)
            return EXIT_USAGE
        try:
            result = verify(ns.snapshot, command, cwd=ns.cwd, timeout=ns.timeout)
        except OSError as exc:
            print(f"INVALID SNAPSHOT: {exc}", file=sys.stderr)
            return EXIT_SNAPSHOT_BAD
        code = verdict_exit_code(result)
        if ns.json:
            print(json.dumps(result, sort_keys=True))
        else:
            print(_human_verify(result))
        return code

    print(f"unknown mode: {mode} (expected snapshot|verify)", file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
