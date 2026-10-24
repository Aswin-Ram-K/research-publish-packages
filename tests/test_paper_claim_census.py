"""Red->green guard: the claim census must keep working past C62, on any row shape.

Why this file exists
--------------------
Three places count claim ids with the same regex — ``recompute.py:coverage_ids``,
``recompute.py:surface_defects`` and ``verify_package.py:CLAIM_RE`` — and a fourth
(``recompute.py:script_backed``) reads the command out of column 5. The card this unit
serves asked whether the census is "blind past C62". Measured (four probes, each row
planted then restored, ``CLAIMS.md`` sha256 ``abcae72076…`` unchanged after every one):

  * The **id pattern is not blind**: ``C\\d{2}`` already matches C63–C99. Probe A — a
    ``| C63 |`` row inserted *before* C62, no runner — was caught by
    ``verify_package.py``: ``missing claim ids in READER-MAP: C63``, exit 1.
  * What *was* blind is ``script_backed()``: it ran ``re.search(r"(\\S+\\.py)", cell5).group(1)``
    and raised ``AttributeError: 'NoneType' object has no attribute 'group'`` on the first
    claim row whose command names no ``.py`` — the shape every new claim is written in.
    The row was caught (exit 1) but as a **traceback**, so the guard never said why.
  * No count could see a row lost *above* the maximum id: 62 lost C40 leaves 61 ids that
    still agree with 61 runners, and every check in ``coverage_guard`` stays green.

So the census's own regression is: (1) the pattern reaches C63, (2) the four regexes agree,
(3) a new claim row's non-script command is a declared FAIL, not a crash, (4) a gap below the
maximum is a declared FAIL, (5) no document re-states a hard-coded claim total.

Red->green (proven 2026-10-23, ``.venv/bin/python -m pytest tests/test_paper_claim_census.py -q``)
--------------------------------------------------------------------------------------------
  RED-1 (the crash, ``test_a_new_claim_row_without_a_script_is_a_fail_not_a_crash``).
  ``script_backed()`` restored to its ``.group(1)`` form and the ``UNRUNNABLE`` FAIL block
  removed -> the planted tail row ``| C63 | ... | none |`` raises ``AttributeError`` from
  ``coverage_guard()``; ``1 failed``.  GREEN -> ``COVERAGE GUARD FAIL  1 claim row(s) whose
  command names no .py script``, exit 1, and the test passes.
  RED-2 (the gap, ``test_a_deleted_claim_row_is_a_fail_below_the_maximum``).
  The contiguity check removed -> a ``CLAIMS.md`` copy with C40 deleted passes every existing
  count (61 ids, 61 runners) and ``coverage_guard()`` returns 0; ``1 failed``.  GREEN ->
  ``COVERAGE GUARD FAIL  claim-id gap(s) below the maximum C62: C40``, non-zero; the test
  passes.

Offline: reads four files off disk and imports ``recompute.py``; no network, no rows, no
endpoint, no cache lock.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "papers" / "context-cache"
RECOMPUTE = PACKAGE / "recompute.py"
VERIFY = PACKAGE / "verify_package.py"
CLAIMS = PACKAGE / "CLAIMS.md"
PACKAGE_MD = PACKAGE / "PACKAGE.md"
READER_MAP = PACKAGE / "READER-MAP.md"

#: Every file that decides what a claim id is.  A regex fixed in one and left in another is
#: a census that reports two different totals for the same ledger.
CENSUS_SOURCES = (RECOMPUTE, VERIFY)


def _load_recompute(claims_path: Path | None = None):
    """Import ``recompute.py`` as a module, optionally pointed at another CLAIMS.md."""
    spec = importlib.util.spec_from_file_location("_census_recompute_under_test", RECOMPUTE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if claims_path is not None:
        module.CLAIMS_MD_PATH = claims_path
    return module


def _documented_ids() -> list[str]:
    return re.findall(r"^\|\s*(C\d{2})\s*\|", CLAIMS.read_text(encoding="utf-8"), re.MULTILINE)


def test_the_census_reaches_claim_ids_past_c62() -> None:
    """The premise: C63..C99 are claim ids the census must be able to see.

    This is the fact that makes ``C62`` a *maximum*, not a *ceiling*.  If the pattern ever
    narrows (``C\\d`` to ``C[0-6]\\d``, or an enumerated list of ids), the very next claim id
    ships unbacked -- which is what the card that produced this file feared.
    """
    pattern = re.compile(r"^\|\s*(C\d{2})\s*\|", re.MULTILINE)
    for n in (62, 63, 64, 70, 99):
        assert pattern.search(f"| C{n:02d} | anything | x | y | z |\n"), (
            f"the claim-id pattern no longer matches C{n:02d}; a claim id past C62 would be "
            "invisible to every census count"
        )


@pytest.mark.parametrize("path", CENSUS_SOURCES, ids=lambda p: p.name)
def test_the_census_regex_is_the_same_in_every_source(path: Path) -> None:
    """One definition of "claim row" per source, and it is still ``C\\d{2}``."""
    source = path.read_text(encoding="utf-8")
    patterns = set(re.findall(r'r"\^\\\|\\s\*\(([^)]*)\)\\s\*\\\|"', source))
    assert patterns, f"{path.name} no longer declares a claim-id pattern at all"
    assert patterns == {r"C\d{2}"}, (
        f"{path.name} declares claim-id pattern(s) {sorted(patterns)}, expected exactly "
        r"{'C\\d{2}'} -- a narrowed or enumerated pattern stops matching new claim ids"
    )


def test_a_new_claim_row_without_a_script_is_a_fail_not_a_crash(tmp_path: Path) -> None:
    """The row shape every new claim is written in must produce a verdict, not a traceback.

    ``| C63 | ... | none |`` is a five-cell claim row whose command cell names no ``.py``.
    Before the fix, ``script_backed()`` raised ``AttributeError: 'NoneType' object has no
    attribute 'group'`` out of ``coverage_guard()``; the row was caught, but the guard never
    said which row or why.
    """
    planted = tmp_path / "CLAIMS.md"
    planted.write_text(
        CLAIMS.read_text(encoding="utf-8")
        + "| C63 | PLANTED by tests/test_paper_claim_census.py: a new claim, no runner | x | y | none |\n",
        encoding="utf-8",
    )
    module = _load_recompute(planted)
    assert module.coverage_ids()[-1] == "C63", "the planted row is not counted at all"

    status = module.coverage_guard()

    assert module.UNRUNNABLE and module.UNRUNNABLE[0].startswith("C63"), (
        "the row whose command names no .py script was not recorded; it is either invisible "
        "to script_backed() or it crashed the guard"
    )
    assert status != 0, "a claim row with no runner must fail the census, not pass it"


def test_a_deleted_claim_row_is_a_fail_below_the_maximum(tmp_path: Path) -> None:
    """A gap below C62 is invisible to every other count, so it needs its own check.

    Deleting C40 leaves ``coverage_ids`` with 61 ids (C01..C62 minus C40); the runner set
    still agrees with it one-for-one, no duplicate exists and nothing is invisible — the
    ledger is short by one row and passes.  Contiguity is the only symptom.

    C40 is the planted gap because it is a **stored-value** claim (a ``FUNCS`` entry), not
    one of the two external scripts or the guard: ``script_backed`` only reads rows whose
    command names an external ``.py``, and removing one of those would be caught by its own
    "missing script" check rather than by contiguity, which is the check under test.
    """
    text = CLAIMS.read_text(encoding="utf-8")
    without_c40 = "\n".join(
        line for line in text.splitlines() if not re.match(r"^\|\s*C40\s*\|", line)
    ) + "\n"
    assert without_c40 != text, "CLAIMS.md no longer has a '| C40 |' row to delete"

    holed = tmp_path / "CLAIMS.md"
    holed.write_text(without_c40, encoding="utf-8")
    module = _load_recompute(holed)

    assert "C40" not in module.coverage_ids()
    assert module.surface_defects() == [], (
        "the row's absence is not a surface defect -- as measured, this is what makes the "
        "gap invisible to every existing check"
    )
    assert module.coverage_guard() != 0, (
        "a claim id missing below the maximum passed the whole census: 61 ids still agree "
        "with 61 runners, so nothing else notices the lost row"
    )


def test_the_live_ledger_is_contiguous_and_fully_runnable() -> None:
    """The real ledger, not a fixture: every row a runner, no gap below the maximum.

    Contiguity is about the **set** of ids, not their order: ``CLAIMS.md`` is grouped by
    section ("A. Rendering", "B. Fan-out placement", …), so ``C13`` legitimately sits at row 4
    beside C01–C03 and the ids are not in numeric order in the file.  Comparing
    ``coverage_ids()`` (document order) against a numeric range test the wrong thing and was
    red on a correct ledger -- measured 2026-10-23, ids ``[C01, C02, C03, C13, C04, …]``.
    """
    module = _load_recompute()
    documented = module.coverage_ids()
    numbered = sorted(int(c[1:]) for c in documented)
    assert numbered == list(range(1, len(numbered) + 1)), (
        "CLAIMS.md claim ids are not contiguous from C01; a row was lost or renumbered above "
        "the maximum, which no other census count can see. "
        f"Duplicates: {sorted({c for c in documented if documented.count(c) > 1})}; "
        f"gaps below C{max(numbered):02d}: "
        f"{[f'C{n:02d}' for n in range(1, max(numbered) + 1) if n not in numbered]}"
    )
    assert module.surface_defects() == [], (
        f"a CLAIMS.md table row is invisible to the census: {module.surface_defects()}"
    )
    assert module.coverage_guard() == 0, "the live census does not pass"


@pytest.mark.parametrize("path", (PACKAGE_MD, READER_MAP), ids=lambda p: p.name)
def test_no_document_re_states_a_hard_coded_claim_total(path: Path) -> None:
    """A typed total is a count that goes stale the moment a claim is added.

    PACKAGE.md's own SS 7 records this failure mode ("a stale count typed here passed every
    guard, which is how the '58' figure survived four new claims"), and yet the total was
    typed in five places.  Counts are left to the COVERAGE GUARD / verify_package lines; the
    documents link to them instead of restating them.
    """
    text = path.read_text(encoding="utf-8")
    # A fenced block is a pasted transcript of a command's output, not a claim the document
    # asserts.  Two kinds live there and both are legitimate: the program's OWN vocabulary
    # ("59 claims checked, all match", "COVERAGE GUARD PASS 62 claims documented") and an
    # iconically quoted token ("`59 claims checked` is the count of stored-value claims").
    # What goes stale is a count the prose ASSERTS, so blocks are stripped before counting.
    prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    prose = re.sub(r"`[^`\n]*`", "", prose)
    stale = re.findall(r"\b\d{2}\s+claims?\b", prose)
    assert not stale, (
        f"{path.name} re-states a claim total ({', '.join(sorted(set(stale)))}); a typed "
        "count is a number that can only go stale. Link to COVERAGE GUARD / verify_package "
        "instead of counting by hand."
    )
