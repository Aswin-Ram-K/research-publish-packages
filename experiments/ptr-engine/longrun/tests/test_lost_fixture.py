"""Forward-only guard: every ``fixture_sha256`` a row pins must have a file on disk.

The lost digest ``72c3832d95f9c7966b4358eda10fa2882775a416ee8a663d57b1c871ed19c44d`` is pinned by 259
rows and by no file. That loss is recorded, not repaired, so the 259 known misses are frozen in
``state/logs/lost-fixture-baseline.json``. This test passes on those and fails on any *new* miss.

Run: python3 -m pytest experiments/ptr-engine/longrun/tests/test_lost_fixture.py -q
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = ROOT / "state" / "logs" / "lost-fixture-baseline.json"
FIXTURE_SCHEMA = "consonance.longrun-fixture/1"
CORPUS_DIRS = (
    ROOT / "experiments" / "ptr-engine" / "measure",
    ROOT / "experiments" / "ptr-engine" / "longrun",
)
SKIP_PARTS = {"__pycache__", ".venv", "node_modules"}


def _iter_files(root: Path, suffix: str):
    for path in root.rglob(f"*{suffix}"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        yield path


def fixture_digests() -> set[str]:
    """sha256 of every on-disk document carrying the longrun fixture schema."""
    digests: set[str] = set()
    for path in _iter_files(ROOT / "experiments" / "ptr-engine" / "longrun", ".json"):
        try:
            if path.stat().st_size > 2 * 1024 * 1024:
                continue
            doc = json.loads(path.read_bytes())
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict) and doc.get("schema") == FIXTURE_SCHEMA:
            digests.add(hashlib.sha256(path.read_bytes()).hexdigest())
    return digests


def row_pins() -> list[tuple[str, int, str]]:
    """(repo-relative path, 1-based line, fixture_sha256) for every row that pins one."""
    pins: list[tuple[str, int, str]] = []
    for directory in CORPUS_DIRS:
        for path in _iter_files(directory, ".jsonl"):
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, 1):
                if "fixture_sha256" not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                digest = row.get("fixture_sha256")
                if isinstance(digest, str) and len(digest) == 64:
                    pins.append((str(path.relative_to(ROOT)), lineno, digest))
    return pins


def load_baseline() -> tuple[str, set[str]]:
    doc = json.loads(BASELINE.read_text(encoding="utf-8"))
    frozen = {f"{r['file']}:{r['line']}" for r in doc["rows"]}
    return doc["lost_digest"], frozen


def misses() -> list[tuple[str, int, str]]:
    return [pin for pin in row_pins() if pin[2] not in fixture_digests()]


def test_no_new_row_pins_a_missing_fixture() -> None:
    lost_digest, frozen = load_baseline()
    known = {(pin[0], pin[1]) for pin in misses() if pin[2] == lost_digest}
    reported = {f"{path}:{line}" for path, line, _ in misses()}

    assert len(frozen) == 259, f"baseline should freeze 259 rows, has {len(frozen)}"
    assert reported == frozen, (
        "new row(s) pin a fixture_sha256 with no file on disk: "
        + ", ".join(sorted(reported - frozen))
    )
    assert known == {(p, int(l)) for p, l in (s.rsplit(":", 1) for s in frozen)}
