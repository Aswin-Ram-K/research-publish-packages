"""Forward-only guard: every ``fixture_sha256`` a row pins must have a file on disk.

1,368 rows across 13 ``rows-*.jsonl`` files pin a digest that no on-disk document carries. Those losses
are recorded, not repaired, and frozen in ``state/logs/lost-fixture-baseline.json`` as a **dated freeze**
(``frozen_at`` 2026-11-10, audit ``U-SPCC-30``). This test passes on exactly those and fails on any
*new* miss. ``state/`` is gitignored, so the baseline is force-added (``git add -f``); a re-freeze must be
force-added again or the guard ships without its baseline.

A new miss means a fixture was destroyed after 2026-11-10.

The assertion is set equality on ``(file, line)``, not a count: a new miss fails, and so does swapping
one frozen lost row for another. See ``experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md``
§Corpus-wide fixture provenance.

Run: python3 -m pytest experiments/ptr-engine/longrun/tests/test_lost_fixture.py -q
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASELINE = ROOT / "state" / "logs" / "lost-fixture-baseline.json"
FIXTURE_SCHEMAS = frozenset({
    "consonance.longrun-fixture/1",
    "consonance.longrun-fixture/2",
})
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
        if isinstance(doc, dict) and doc.get("schema") in FIXTURE_SCHEMAS:
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


def load_baseline() -> tuple[set[str], dict[str, dict], str]:
    """(frozen ``file:line`` keys, recorded lost digests, freeze date)."""
    doc = json.loads(BASELINE.read_text(encoding="utf-8"))
    frozen = {f"{r['file']}:{r['line']}" for r in doc["rows"]}
    return frozen, doc["digests"], doc["frozen_at"]


def misses(on_disk: set[str] | None = None) -> list[tuple[str, int, str]]:
    """Pins with no matching on-disk fixture. ``on_disk`` is hoisted: hashing the tree per pin is O(n) walks."""
    if on_disk is None:
        on_disk = fixture_digests()
    return [pin for pin in row_pins() if pin[2] not in on_disk]


def test_no_new_row_pins_a_missing_fixture() -> None:
    frozen, lost_digests, frozen_at = load_baseline()
    on_disk = fixture_digests()
    reported_pins = misses(on_disk)
    reported = {f"{path}:{line}" for path, line, _ in reported_pins}

    new = sorted(reported - frozen)
    assert not new, (
        f"NEW row(s) pin a fixture_sha256 with no file on disk: {', '.join(new)}. "
        f"A new miss means a fixture was destroyed after {frozen_at} (the dated freeze in "
        f"{BASELINE.relative_to(ROOT)}). Restore the fixture, or re-freeze deliberately with a new "
        f"dated note naming the audit — never widen the baseline silently."
    )

    vanished = sorted(frozen - reported)
    assert not vanished, (
        f"frozen lost row(s) no longer miss: {', '.join(vanished)}. A fixture came back or a rows file "
        f"changed; re-freeze deliberately with a new dated note rather than leaving a stale baseline."
    )

    # Every frozen row must still pin a digest the baseline records as lost, and that digest must still
    # be absent from disk — otherwise the freeze is describing a fixture that exists.
    for path, line, digest in reported_pins:
        assert digest in lost_digests, (
            f"{path}:{line} pins {digest}, which is not a recorded lost digest"
        )
        assert digest not in on_disk, f"{path}:{line} pins {digest}, which is on disk"
