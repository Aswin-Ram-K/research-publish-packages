"""Red->green guard: the G3 boundary band must be stated as the measurement it is.

Why this file exists
--------------------
Cell G3-LIMIT-V2 is the only cell in the package that crosses a context limit, and its
result is stated in seven reader-facing places: the abstract (``MANUSCRIPT.md:46``), SS 6a
(``:326``), SS 10 rule 5 (``:559``), ``CLAIMS.md``'s C62 row (``:190``), ``PACKAGE.md:58``,
``EVIDENCE.md:205`` and ``GAPS.md:65``.  All seven said the same thing:

    the compacting arms pay **+134.6 to +747.2 uncached tokens per turn**

That sentence is an overstatement of what the rows support, and it is the package's own
recompute (C62) that shows it.  ``134.6`` and ``747.2`` are not turns: they are the smallest
and the largest of **twelve per-arm MEANS**, each averaged over 27-89 post-boundary turns
(``recompute.py``'s ``post_delta_min`` / ``post_delta_max``).  Per turn the same segment
runs **-927 to +5,473**, and **all twelve arms** contain at least one turn below their
baseline, so neither end of the mean range is a per-turn bound in either direction:

  * the floor is 7x too high (a turn of the pointer fork at 64k comes in 856 tokens *cheaper*
    than its baseline; the 32k pointer fork's worst turn is -57);
  * the ceiling is 3x too low (arm F-ptr reaches +2,203 at 32k, arm S 5,473 at 64k).

Averaging also hides the one arm whose significance moves: excluding the turns that follow
one of the baseline's own window drops leaves eleven means where they were but takes the 32k
pointer fork from +134.6 to **+112.5**, whose interval [-33.7, 264.3] crosses zero.

The prose half of the fix is not enough on its own, which is why this guard pins the numbers
as well as the sentences: ``recompute.py`` compares ``EXPECTED["C62"]`` with a tolerance, and
a rewrite that re-pinned ``post_turn_delta_min``/``max`` to a different pair of arm means
would still pass there.  This file fails if the paper stops saying, anywhere a reader meets
the band, that the 134.6-747.2 range is a range of averages and what the per-turn range is.

What is in scope
----------------
  (A) every document that states the mean band also states the per-turn band in the same
      document (not necessarily the same sentence -- the abstract and SS 6a each carry both);
  (B) no document presents the mean band as a per-turn range without the qualifier;
      the qualifier is a word the package uses ("average", "arm mean", "arm means", "mean");
  (C) the cell and the condition travel with the figure that states it (the X-CITE2 lesson:
      a number can survive in a table while the sentence that says what it measured is
      deleted);
  (D) ``recompute.py`` still pins the per-turn band and the arm count -- the code-side half,
      so that deleting the sentence without changing the data cannot pass either;
  (E) the steady-turn result is still stated where it is load-bearing (SS 6a).

Red->green (measured 2026-10-23, ``PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
tests/test_paper_g3_bands.py -q``)
-------------------------------------------------------------------------
RED.  The abstract reverted to the pre-fix sentence -- "six compacting arms pay **+134.6 to
+747.2 uncached tokens per turn** against the compaction-free baseline" -- with the per-turn
sentence deleted: ``2 failed, 11 passed`` --
  ``[QUALIFIER]`` ``MANUSCRIPT.md:46`` ("the mean band is stated without saying it is a range
  of averages") and ``[PER-TURN]`` on ``test_the_manuscript_carries_the_cell_and_the_condition``
  ("the abstract no longer states the per-turn band (-927 to +5,473)").
Nothing else in the repo noticed: ``recompute.py C62`` printed ``PASS 23/23`` (the rows never
changed -- this is a prose regression over unchanged data) and
``tests/test_paper_attribution_guard.py`` stayed ``11 passed`` (it guards the 1.700x, not
this band).  That is the hole this file closes.
GREEN.  The correction restored; ``13 passed``.

Offline: reads five Markdown files and two Python files off disk; no network, no rows.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "papers" / "context-cache"

MANUSCRIPT = PACKAGE / "MANUSCRIPT.md"
CLAIMS = PACKAGE / "CLAIMS.md"
PACKAGE_MD = PACKAGE / "PACKAGE.md"
EVIDENCE = PACKAGE / "EVIDENCE.md"
GAPS = PACKAGE / "GAPS.md"
RECOMPUTE = PACKAGE / "recompute.py"

#: The mean band, as every document states it.  Both decimal separators are accepted because
#: EVIDENCE/GAPS write the same figures as ``+134.6 to +747.2`` and CLAIMS as
#: ``134.6-747.2``; the test only needs to find where the mean band is being discussed.
MEAN_BAND = re.compile(r"134\.6\W{0,4}(?:to|…|-|–)\W{0,4}\+?747\.2")

#: The per-turn band, in the forms the corrected documents use: ``-927 to +5,473``,
#: ``−927 to +5,473`` (typographic minus), ``−927…+5,473``.  A document that states the mean
#: band MUST state one of these, because the mean band alone understates both ends.
PER_TURN_BAND = re.compile(r"[-\u2212]927\W{0,4}(?:to|…|-|–)\W{0,4}\+?5,?473")

#: How a document is allowed to keep the mean band: it must say the range is of averages.
#: The package's own vocabulary -- "on average", "arm means", "twelve arm means", "as an arm
#: mean", "mean band".  Kept as alternatives so a rewrite does not have to reuse a sentence.
QUALIFIER = re.compile(
    r"on average|arm mean|arm means|twelve (?:arm )?means|as an arm mean|mean band"
    r"|averaged over|an? average over",
    re.IGNORECASE,
)

#: How far from the mean band its qualifier and its per-turn companion may sit.  Measured on
#: the corrected tree: the abstract states both bands in one 600-character paragraph, SS 6a
#: in one 1,400-character paragraph, CLAIMS.md in one table row (the two figures ~200
#: characters apart), PACKAGE.md in two consecutive lines.  400 characters covers the table
#: row and every paragraph; a window is used rather than a sentence because SS 6a's
#: qualifier ("twelve *arm means*") and its band sit in the same sentence but CLAIMS.md's
#: qualifier opens the row.
WINDOW = 400

#: Documents a reader can meet the band in.  ``MANUSCRIPT.md`` is read by everyone;
#: ``PACKAGE.md``/``EVIDENCE.md``/``GAPS.md``/``CLAIMS.md`` are the package's own reading
#: order (READER-MAP.md sends a reader to them in that sequence).
DOCUMENTS = (MANUSCRIPT, CLAIMS, PACKAGE_MD, EVIDENCE, GAPS)


def _prose(text: str) -> str:
    """Blank fenced blocks and inline code, preserving offsets for line numbers."""
    text = re.sub(r"^(```|~~~).*?^\1", lambda m: re.sub(r"[^\n]", " ", m.group(0)),
                  text, flags=re.DOTALL | re.MULTILINE)
    return re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), text)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _excerpt(text: str, offset: int, span: int = 320) -> str:
    start = max(0, offset - span // 2)
    return " ".join(text[start: offset + span // 2].split())[:span]


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: p.name)
def test_a_document_that_states_the_mean_band_states_the_per_turn_band(path: Path) -> None:
    """(A) the understated figure cannot stand alone in any document that carries it."""
    assert path.is_file(), f"{path} is missing -- the guard has nothing to read"
    prose = _prose(path.read_text(encoding="utf-8"))
    hits = list(MEAN_BAND.finditer(prose))
    if not hits:
        pytest.skip(f"{path.name} does not state the G3 mean band; nothing to qualify")
    assert PER_TURN_BAND.search(prose), (
        f"{path.name} states the mean band "
        f"(line {line_of(prose, hits[0].start())}) and never states the per-turn band. "
        "134.6-747.2 are twelve per-arm MEANS over 27-89 turns, not turns; the same segment "
        "runs -927 to +5,473 per turn and all twelve arms have a turn below baseline. "
        "Recompute: .venv/bin/python papers/context-cache/recompute.py C62"
    )


@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: p.name)
def test_the_mean_band_is_never_presented_as_a_per_turn_bound(path: Path) -> None:
    """(B) each statement of the mean band keeps its qualifier within WINDOW characters."""
    prose = _prose(path.read_text(encoding="utf-8"))
    missing = []
    for hit in MEAN_BAND.finditer(prose):
        lo = max(0, hit.start() - WINDOW)
        hi = min(len(prose), hit.end() + WINDOW)
        if not QUALIFIER.search(prose[lo:hi]):
            missing.append(
                f"{path.name}:{line_of(prose, hit.start())} [QUALIFIER] the mean band is "
                f"stated without saying it is a range of averages: "
                f"{_excerpt(prose, hit.start())}"
            )
    assert not missing, (
        "the G3 boundary band is an average per arm, not a cost per turn. Each statement of "
        "134.6-747.2 must say so (PUBLISHED FAILURE MODE: the abstract, SS 6a, SS 10 rule 5, "
        "CLAIMS C62, PACKAGE, EVIDENCE and GAPS all read as if the range were a per-turn "
        "bound). Findings:\n  - " + "\n  - ".join(missing)
    )


def test_the_manuscript_carries_the_cell_and_the_condition_with_the_figure() -> None:
    """(C) the figures travel with the cell, the budgets and the arm count (X-CITE2 lesson).

    Pinned on the abstract, where a reader meets the result first: deleting ``G3-LIMIT-V2``
    or the arm count from it would leave the numbers standing and unowned.
    """
    prose = _prose(MANUSCRIPT.read_text(encoding="utf-8"))
    abstract_end = prose.find("## 1.")
    assert abstract_end > 0, "MANUSCRIPT.md no longer has an abstract before '## 1.'"
    abstract = prose[:abstract_end]
    assert PER_TURN_BAND.search(abstract), (
        "the abstract no longer states the per-turn band (-927 to +5,473); the band that a "
        "reader takes away is the one the summary sentence carries"
    )
    for token in ("G3-LIMIT-V2", "2,780", "18 compactions", "32k", "64k", "twelve arms"):
        assert token in abstract, (
            f"the abstract no longer carries {token!r} next to the boundary band; the figure "
            "must keep the cell, its request count, its budgets and its arm count"
        )


def test_recompute_still_pins_the_per_turn_band_and_the_arm_count() -> None:
    """(D) the code-side half: the pinned expectation, not only the prose."""
    source = RECOMPUTE.read_text(encoding="utf-8")
    for key, value in (
        ('"post_turn_delta_min"', "-927.0"),
        ('"post_turn_delta_max"', "5473.0"),
        ('"post_turns_below_zero"', "12"),
    ):
        assert re.search(re.escape(key) + r"\s*:\s*" + re.escape(value), source), (
            f"recompute.py's C62 expected value no longer pins {key}: {value}. The per-turn "
            "band is what the prose is allowed to claim, so it must stay pinned in the "
            "recompute, not only in a test."
        )
    assert '"post_turn_band"' in source and '"post_steady"' in source, (
        "recompute.py no longer pins the per-arm band tables (post_turn_band / post_steady); "
        "a global band alone passes on whichever arm happens to carry its ends"
    )


def test_the_steady_turn_result_is_stated_where_it_is_load_bearing() -> None:
    """(E) SS 6a keeps the result that moves 32k F-ptr from +134.6 to +112.5."""
    prose = _prose(MANUSCRIPT.read_text(encoding="utf-8"))
    section = prose.find("## 6a.")
    section_end = prose.find("\n## 7.", section) if section >= 0 else -1
    assert section >= 0 and section_end > section, (
        "MANUSCRIPT.md no longer has the '## 6a.' section that states the boundary result"
    )
    # The manuscript types the lower bound with a typographic minus (\u2212), so both
    # spellings are accepted: the requirement is the figure, not the glyph.
    block = prose[section:section_end].replace("\u2212", "-")
    for token in ("+112.5", "-33.7, 264.3"):
        assert token in block, (
            f"SS 6a no longer carries {token!r}: the resting-turn means are where this cell "
            "loses a significance, and deleting it would restore the claim that 11 of 12 "
            "intervals survive any reasonable re-weighting of the segment"
        )
