"""STRAY-REF guard: the stale scratch tree is never the package record (unit STRAY-REF, 2026-10-23).

WHY THIS EXISTS
Two independent units were misled by ``scratch/uneutral10``: VERIFY-CENSUS cited
the tree ``scratch/uneutral10`` as proof a package defect was fixed — specifically via that tree's
``package/second-labeller/RUN.json`` — and FIX-RUN-R2's ``next_unit_hint`` called that path "the
package chain".  Measured 2026-10-23: that RUN.json is a **2026-10-16 22:25 record of a different
experiment** — ``_experiment: "G46"``,
``_unit: "G33"``, ``_target_head: "907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b"``,
``_fixture_path_in_target: "P05"`` — an old copy of a *different target repo's* run record that
happens to sit inside the released payload tree.  It is not this package's record, and no citation
may treat it as one.

THE RULE
Scan ``papers/``, ``tests/``, ``tools/`` for citations of the stale tree:

1. RECORD-SOURCE (the poisoned form): a line citing the tree **together with** a run-record
   artefact name (``RUN.json`` / ``run.json`` / ``EVIDENCE.md`` / ``rows.jsonl``) fails unless that
   file is in ``RECORD_SOURCE_EXEMPTIONS``.  That table is **empty by measurement** (2026-10-23):
   zero legitimate sites exist — verified by the sweep that produced this guard.  An empty table is
   the point: the form has no sanctioned use.
2. Any *other* citation of the tree must be classified in ``CITATION_EXEMPTIONS`` with a one-line
   reason (fixture pins, tool docs, historical build-input rows).  Unclassified = fail.

KNOWN LIMIT (deliberate, same-anchor design as tests/test_g5_fanout_attribution.py): detection is
line-scoped.  A path on one line and its record token two lines later is not caught; splitting them
that far would also break honest prose.  ``__pycache__``/``.pyc`` are excluded by the suffix filter
(bytecode, not text — no text content is skipped).

HARD RULES (unit contract): this file may not modify anything it scans; the red→green plant is a
temporary NEW file removed afterwards, never an edit to a shared file (concurrent units run pytest).
"""

from __future__ import annotations

from pathlib import Path

import pytest

WS = Path(__file__).resolve().parent.parent

SCAN_ROOTS = ("papers", "tests", "tools")
SCAN_SUFFIXES = {".py", ".md", ".json", ".sh", ".txt", ".toml", ".cfg", ".yml", ".yaml", ".bib"}

# Assembled from two halves so this guard's own description text cannot trip its scanner; every
# real citation below is the literal on one line, and SELF is allowlisted with a reason anyway.
SCRATCH_TOKEN = "scratch/" + "uneutral10"

# A "record" artefact: exactly what the two misled units cited as the package chain.
RECORD_TOKENS = ("RUN.json", "run.json", "EVIDENCE.md", "rows.jsonl")

SELF = "tests/test_no_stray_package_refs.py"

# ---------------------------------------------------------------------------
# Table 1 — non-record citations, each classified with a one-line reason.
# Measured sweep 2026-10-23 (unit STRAY-REF): 5 text files, 17 lines cite the tree in
# papers/ tests/ tools/.  All are payload-fixture pins, tool docs, or historical rows.
# ---------------------------------------------------------------------------
CITATION_EXEMPTIONS: dict[str, str] = {
    "papers/encoder-crossover-190/released/SUPERSEDED-UNPACKED-TREE.md":
        "HISTORICAL: build-inputs row records what the superseded archive was built from; a quote of past work, not the current record",
    "tests/test_package_tools.py":
        "fixture pin: the frozen 29-file payload tree is the package-tools known-good input; never read as a run record",
    "tests/test_build_wiring.py":
        "wiring pin: asserts build.sh's PROMOTED_SAN_SRC default names the same proven payload tree",
    "tools/package/regen_manifest.py":
        "tool docs: documents the self-exemption convention it implements (generator behaviour)",
    "tools/package/classify.py":
        "tool docs: notes where MATERIALISE is implemented; behaviour note, not a record claim",
    "tools/package/_pkg.py":
        "tool docs: documents the --package flag's example value",
    "tools/package/README.md":
        "tool docs: known-good numbers measured on the payload tree; the README itself warns payload-volatile cites must be re-measured",
    SELF:
        "the guard's own detection pattern, plant string and exemption tables must name what they forbid",
}

# ---------------------------------------------------------------------------
# Table 2 — citations presenting the tree's RUN RECORD as authoritative.
# EMPTY by measurement (2026-10-23): the poisoned form has zero legitimate sites.
# Adding an entry here is a claim that some specific file legitimately needs it;
# the justification belongs in the unit handoff, not only here.
# ---------------------------------------------------------------------------
RECORD_SOURCE_EXEMPTIONS: dict[str, str] = {}


def _violations_for_line(
    text: str,
    relpath: str,
    *,
    citation_exempt: bool,
    record_exempt: bool,
) -> list[str]:
    """Classify one scanned line.  Pure function so the red→green proof cannot depend on disk state."""
    if SCRATCH_TOKEN not in text:
        return []
    is_record = any(tok in text for tok in RECORD_TOKENS)
    if is_record:
        if record_exempt:
            return []
        return [
            f"{relpath}: treats the stale scratch tree's RUN RECORD as the package record "
            f"({SCRATCH_TOKEN} + record artefact) — that tree's RUN.json is experiment G46/unit G33 "
            f"of 2026-10-16, not this package's record"
        ]
    if citation_exempt:
        return []
    return [
        f"{relpath}: unclassified citation of the stale tree ({SCRATCH_TOKEN}) — classify it in "
        f"CITATION_EXEMPTIONS with a one-line reason, or remove it"
    ]


def _iter_scanned_files():
    for root in SCAN_ROOTS:
        base = WS / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in SCAN_SUFFIXES:
                yield path


def _rel(path: Path) -> str:
    return path.relative_to(WS).as_posix()


def test_every_stale_tree_citation_is_classified() -> None:
    """Every citation in papers/ tests/ tools/ is either a classified non-record cite or fails."""
    violations: list[str] = []
    for path in _iter_scanned_files():
        rel = _rel(path)
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
        ):
            hits = _violations_for_line(
                line,
                f"{rel}:{lineno}",
                citation_exempt=rel in CITATION_EXEMPTIONS,
                record_exempt=rel in RECORD_SOURCE_EXEMPTIONS,
            )
            violations.extend(f"{hit} | line: {line.strip()[:110]}" for hit in hits)
    assert not violations, "stale scratch tree cited as the package record:\n" + "\n".join(violations)


def test_classifier_bites_on_the_measured_defect() -> None:
    """RED→GREEN core: the exact cited line fails for a normal file and passes only with a named exemption."""
    planted = f"| package record | `{SCRATCH_TOKEN}/package/second-" + "labeller/RUN.json` | the chain |"
    hit = _violations_for_line(planted, "planted.md:1", citation_exempt=False, record_exempt=False)
    assert len(hit) == 1 and "planted.md:1" in hit[0] and "RUN RECORD" in hit[0]
    # Same line in an allowlisted file still fails: the record form is governed by its own table.
    assert _violations_for_line(planted, "p.md:1", citation_exempt=True, record_exempt=False)
    # Only a named record-exemption silences it.
    assert _violations_for_line(planted, "p.md:1", citation_exempt=True, record_exempt=True) == []
    # A non-record citation of the same tree is a different, classifiable case.
    other = "fixture tree: scratch/uneutral10/package (29 files)"
    assert _violations_for_line(other, "p.md:1", citation_exempt=False, record_exempt=False)
    assert _violations_for_line(other, "p.md:1", citation_exempt=True, record_exempt=False) == []
    # Lines that do not name the tree are untouched.
    assert _violations_for_line("experiments/second-labeller-190/RUN.json", "p.md:1",
                                citation_exempt=False, record_exempt=False) == []


def test_exemption_tables_have_no_stale_entries() -> None:
    """Allowlist rot fails loudly: every exempted file exists and still cites the tree it exempts."""
    stale: list[str] = []
    for table_name, table in (
        ("CITATION_EXEMPTIONS", CITATION_EXEMPTIONS),
        ("RECORD_SOURCE_EXEMPTIONS", RECORD_SOURCE_EXEMPTIONS),
    ):
        for rel, reason in table.items():
            path = WS / rel
            if not path.is_file():
                stale.append(f"{table_name}[{rel}]: file does not exist — prune the entry")
                continue
            body = path.read_text(encoding="utf-8", errors="replace")
            if SCRATCH_TOKEN not in body:
                stale.append(f"{table_name}[{rel}]: no longer cites the tree — prune the entry")
            if not reason.strip():
                stale.append(f"{table_name}[{rel}]: empty reason — every exemption carries one")
    assert not stale, "\n".join(stale)
