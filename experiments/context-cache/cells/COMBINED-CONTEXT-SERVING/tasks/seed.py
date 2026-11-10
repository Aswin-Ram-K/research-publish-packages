#!/usr/bin/env python3
"""Seed an isolated writable copy of the pinned Duval sources for one task.

Verifies every source digest before copying. A mismatch aborts with exit 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CELL = BASE.parent
DUVAL = Path("/home/zer0null/Duval")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_digest(value: str) -> str:
    value = str(value).strip()
    if value.lower().startswith("sha256:"):
        value = value[7:]
    return value.lower()


def load_fixture(task_id: str) -> dict:
    path = BASE / f"{task_id}.json"
    if not path.is_file():
        raise SystemExit(f"fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def seed_task(task_id: str) -> int:
    fixture = load_fixture(task_id)
    seed_root = CELL / "tasks" / "work" / task_id / "seed"
    if seed_root.exists():
        shutil.rmtree(seed_root)
    seed_root.mkdir(parents=True, exist_ok=True)
    manifest = []
    for src in fixture.get("sources", []):
        raw_path = Path(src["path"])
        path = raw_path if raw_path.is_absolute() else (Path("/home/zer0null") / raw_path)
        if not path.is_file():
            raise SystemExit(f"source not found: {path}")
        actual = sha256_file(path)
        expected = norm_digest(src["sha256"])
        if actual != expected:
            raise SystemExit(
                f"digest mismatch for {path}: expected {expected}, got {actual}"
            )
        if path.is_relative_to(DUVAL):
            rel = path.relative_to(DUVAL)
        else:
            rel = Path(path.name)
        dest = seed_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        manifest.append(
            {
                "source_path": str(path),
                "seeded_path": str(dest.relative_to(CELL)),
                "sha256": actual,
                "pointer": src.get("pointer"),
            }
        )
    (seed_root / "SEED_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"task": task_id, "seeded": len(manifest), "root": str(seed_root)}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", help="task id or 'all'")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--path", type=Path)
    ap.add_argument("--sha256")
    args = ap.parse_args()

    if args.verify_only:
        if args.path is None or args.sha256 is None:
            raise SystemExit("--verify-only requires --path and --sha256")
        actual = sha256_file(args.path)
        expected = norm_digest(args.sha256)
        if actual != expected:
            print(f"REFUSED: digest mismatch: expected {expected}, got {actual}")
            return 1
        print(f"OK: digest matches: {actual}")
        return 0

    if not args.task:
        raise SystemExit("--task required")
    if args.task == "all":
        for task_file in sorted(BASE.glob("T*.json")):
            seed_task(task_file.stem)
        return 0
    return seed_task(args.task)


if __name__ == "__main__":
    raise SystemExit(main())
