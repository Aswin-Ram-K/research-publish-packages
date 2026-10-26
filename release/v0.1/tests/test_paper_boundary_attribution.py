"""Red->green guard: the paper may not sell the compaction-at-the-boundary cost as free.

Why this file exists
--------------------
The context-cache package's claim about compaction at a *context limit* was, until
G3-LIMIT-V2, a statement of absence: every earlier cell (G3's 888 rows, U15, G1, the
cross-stack window) scheduled compaction or never reached a limit, so
``scheduled_compaction`` was false on every row and the package said the limit question was
open.  G3-LIMIT-V2 measured it (C62): compaction-free baselines rendered in the same bytes,
six compacting arms per budget, 18 compactions, a flat control segment and a +134.6 to
+747.2 uncached-token-per-turn post-boundary delta.

The failure mode this guard exists for is the one the earlier G3 units actually hit: a
sentence (or a status line) that keeps saying the limit case is unmeasured, or a new
sentence that reports "compaction at the limit is free", while ``recompute.py C62`` stays
green because the *numbers* are still correct.  The numbers are pinned by C62; this file
pins the prose that says what they measured.

What is in scope
----------------
(1) ``GAPS.md`` G3's status line may not still call the gap NOT SETTLED / UNMEASURED /
    OPEN on the limit question, and the file must state the measured band.
(2) ``MANUSCRIPT.md`` must carry the boundary section, the figure, and the control side
    (the arms were indistinguishable before the boundary) together -- the control is half
    the result and is the half a rewrite drops first.
(3) ``CLAIMS.md`` must map C62 to the cell and to the single command.
(4) The sentence in ``MANUSCRIPT.md`` that states the post-boundary band must not present
    compaction as cost-free.

Red->green (proven 2026-10-23, ``PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
tests/test_paper_boundary_attribution.py -q``)
--------------------------------------------------------------------------
  RED-1 (GAPS status).  G3's heading restored to its pre-G3-LIMIT-V2 wording ("STATUS: NOT
  SETTLED by the cross-stack window ...") -> ``1 failed`` on
  ``test_g3_status_is_measured_on_the_limit_question``.
  RED-2 (manuscript).  The §6a result sentence's cheap end corrected to "+0.0" and the
  control sentence's band replaced by "0.0" -> ``2 failed``
  (``test_manuscript_states_the_boundary_band``, ``test_manuscript_states_the_control_segment``).
  A first attempt at this revert only rewrote the band and left the table rows intact; the
  section-wide token check stayed green at ``8 passed``, which is why the assertions are now
  anchored on the sentences that state the result.
  GREEN.  Both files restored; the numbers re-derived by ``recompute.py C62`` (17/17 values
  match) before the edits, and the same after.

Offline: reads three Markdown files off disk; no network, no rows, no cache lock.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "papers" / "context-cache"
MANUSCRIPT = PACKAGE / "MANUSCRIPT.md"
CLAIMS = PACKAGE / "CLAIMS.md"
GAPS = PACKAGE / "GAPS.md"

#: The post-boundary band, as C62 prints it.  Anchored on the SENTENCE that states the band,
#: not on the section: every per-arm row of §6a's table also carries a figure, so a
#: section-wide "is this token anywhere" check stays green while the sentence that states the
#: result is rewritten.  Measured on the 2026-10-23 tree -- dropping one arm row from the table
#: left a token-wide check at ``8 passed``.
BAND_SENTENCE = re.compile(r"post-boundary delta[^\n]{0,200}", re.IGNORECASE)
#: Both ends are required: quoting only the cheap end is the optimistic reading, only the dear
#: end the pessimistic one.
BAND_REQUIRED = ("+134.6", "+747.2")

#: The control segment, as C62 prints it, anchored the same way.
CONTROL_SENTENCE = re.compile(r"matched-turn contrast[^\n]{0,200}", re.IGNORECASE)
CONTROL_REQUIRED = ("-11.8", "+51.0")

#: Phrasings that would put the gap back where it was before G3-LIMIT-V2.
STILL_UNSETTLED = re.compile(
    r"(?:not settled|unsettled|unmeasured|never measured|no measurement|not measured)\b"
    r"[^.]{0,200}?\b(?:limit|boundary)\b"
    r"|\b(?:limit|boundary)\b[^.]{0,120}?\b(?:not settled|unsettled|unmeasured|"
    r"never measured|not measured)\b",
    re.IGNORECASE,
)

#: Assertions that compaction at a limit costs nothing.  The package may *quote* the old
#: reading; it may not assert it outside quotation marks.  A copula with a negation between it
#: and the noun ("compaction at the boundary is **not** free") is the corrective, not the claim,
#: so the deny side carries the same negated-head exemption the 1.700x guard uses.
FREE_READING = re.compile(
    r"\b(?:compaction|compacting)\b[^.]{0,80}?\b(?:is|was|stays|remains)\b(?!\s+not\b)"
    r"[^.]{0,40}?\b(?:free|cost[- ]free|free of charge|cheap|harmless)\b"
    r"|\b(?:free|cost[- ]free)\b[^.]{0,60}?\b(?:when|once|at)\b[^.]{0,40}?"
    r"\b(?:the )?(?:limit|boundary|window)\b",
    re.IGNORECASE,
)

#: The manuscript restates the rejected reading in one place without quotation marks: "A
#: reviewer who read only the accuracy table would conclude compaction is harmless. It is
#: not: the gold line ...".  A *counterfactual reader's conclusion* immediately corrected in
#: the next sentence is a quotation of a rejected reading, so it is exempted -- and only for
#: as long as the correction is there.  Deleting "It is not:" puts the sentence back in
#: front of the deny side, which is the failure this exemption must not hide.
REJECTED_READING = re.compile(
    r"\b(?:would conclude|a reader would|one could conclude|read as if|implies)\b[^.]{0,120}\."
    r"\s+It is not\b",
    re.IGNORECASE,
)

_QUOTED = re.compile(r'"[^"\n]{3,200}"')
_INLINE_CODE = re.compile(r"`[^`\n]*`")


def prose(text: str) -> str:
    """Blank quotations and inline code, preserving offsets (same marker as the other guard)."""
    def blank(m: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))

    for pattern in (_QUOTED, _INLINE_CODE):
        text = pattern.sub(blank, text)
    return text


def assertions(text: str) -> str:
    """``prose`` plus the one exemption the boundary claim needs.

    The manuscript restates the "a table would conclude compaction is harmless" reading in
    order to reject it (MANUSCRIPT.md §4).  That span is a quotation of a rejected reading, so
    it is blanked like any other quotation; every other quotation stays visible to the deny
    side, which keeps the exemption the size of one sentence and not a licence.
    """
    return REJECTED_READING.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), prose(text))


def g3_block(text: str) -> str:
    start = text.find("## G3.")
    assert start >= 0, "GAPS.md no longer has a '## G3.' entry"
    nxt = text.find("\n## G", start + 5)
    return text[start: nxt if nxt > start else len(text)]


def section(text: str, heading: str) -> str:
    start = text.find(heading)
    assert start >= 0, f"MANUSCRIPT.md no longer has the '{heading}' section"
    nxt = text.find("\n## ", start + len(heading))
    return text[start: nxt if nxt > start else len(text)]


def read(path: Path) -> str:
    assert path.is_file(), f"{path} is missing -- the guard has nothing to read"
    return path.read_text(encoding="utf-8")


def test_g3_status_is_measured_on_the_limit_question() -> None:
    """G3's status line must say the limit case was measured, not that it is still open."""
    block = g3_block(read(GAPS))
    head = block.splitlines()[0]
    assert re.search(r"STATUS:\s*MEASURED", head), (
        f"GAPS.md G3's status line no longer says the limit question was MEASURED: {head!r}"
    )
    for token in BAND_REQUIRED:
        assert token in block, f"GAPS.md G3 no longer states the measured band end {token!r}"
    # A status line that also re-asserts the old verdict makes the file contradict itself.
    head_prose = prose(head)
    assert not STILL_UNSETTLED.search(head_prose), (
        "GAPS.md G3's status line still says the limit question is not settled: " + head
    )


def test_manuscript_states_the_boundary_band() -> None:
    """The post-boundary band, both ends, in the sentence that states the result."""
    body = section(read(MANUSCRIPT), "## 6a.")
    sentences = BAND_SENTENCE.findall(body)
    assert sentences, (
        "MANUSCRIPT.md §6a no longer has a sentence stating the post-boundary delta; the "
        "measured cost of compaction at the boundary has lost its result sentence"
    )
    missing = [t for t in BAND_REQUIRED if not any(t in s for s in sentences)]
    assert not missing, (
        f"MANUSCRIPT.md §6a's post-boundary sentence no longer states {missing!r}. "
        "Sentences seen: " + " | ".join(" ".join(s.split())[:240] for s in sentences)
    )
    assert "C62" in body, "MANUSCRIPT.md §6a no longer names C62 as the source of the band"


def test_manuscript_states_the_control_segment() -> None:
    """Half the result is that the arms were indistinguishable BEFORE the boundary."""
    body = section(read(MANUSCRIPT), "## 6a.")
    sentences = CONTROL_SENTENCE.findall(body)
    assert sentences, (
        "MANUSCRIPT.md §6a no longer has a sentence stating the matched-turn contrast; the "
        "control half of the result has gone"
    )
    missing = [t for t in CONTROL_REQUIRED if not any(t in s for s in sentences)]
    assert not missing, (
        f"MANUSCRIPT.md §6a's control sentence no longer states {missing!r}; without both "
        "ends the band is an arm difference with no control. Sentences seen: "
        + " | ".join(" ".join(s.split())[:240] for s in sentences)
    )
    assert re.search(r"\b0 of 12\b", body), (
        "MANUSCRIPT.md §6a no longer states that 0 of 12 pre-boundary intervals exclude zero"
    )


def test_claims_maps_c62_to_its_cell_and_command() -> None:
    raw = read(CLAIMS)
    assert "C62" in raw and "G3-LIMIT-V2" in raw and "G3V2-rows" in raw, (
        "CLAIMS.md no longer maps C62 to the G3-LIMIT-V2 rows"
    )
    assert "recompute.py C62" in raw, (
        "CLAIMS.md's C62 row no longer names the single recompute invocation"
    )
    assert re.search(r"^\|\s*C62\s*\|", raw, re.MULTILINE), (
        "CLAIMS.md has no C62 table row"
    )


def test_no_document_sells_compaction_at_the_boundary_as_free() -> None:
    for path in (MANUSCRIPT, GAPS, CLAIMS):
        found = FREE_READING.search(assertions(read(path)))
        assert not found, (
            f"{path.name} asserts (or implies) that compaction at the boundary is free. "
            f"C62 measures +134.6 to +747.2 uncached tokens per turn after it. "
            f"Match: {found.group(0)!r}"
        )


def test_every_phrase_the_package_must_not_use_is_caught() -> None:
    """Each deny pattern is exercised by the sentence it exists for (no dead guard)."""
    assert STILL_UNSETTLED.search("the limit question is not settled by these rows")
    assert STILL_UNSETTLED.search("no measurement of the limit case exists")
    assert FREE_READING.search("Compaction once the window fills is free.")
    assert FREE_READING.search("compacting is cost-free at the limit")
    # The correctives must not be caught.
    assert not FREE_READING.search("compaction at the boundary is not free")
    assert FREE_READING.search("compaction at the boundary is free")
    # ...and the rejection exemption is one corrected sentence, not a licence.
    rejected = "A reviewer would conclude compaction is harmless. It is not: the row says so."
    assert not FREE_READING.search(assertions(rejected))
    assert FREE_READING.search(assertions(rejected.replace(" It is not:", "")))
    assert FREE_READING.search(assertions("A reviewer would conclude. Compaction is harmless."))
    assert not STILL_UNSETTLED.search("the limit case was measured at 32k and 64k")


def test_a_quotation_is_exempt_but_a_statement_is_not() -> None:
    quoted = 'The card said "compaction at the limit is unmeasured" before G3-LIMIT-V2 ran.'
    assert not STILL_UNSETTLED.search(prose(quoted))
    assert STILL_UNSETTLED.search(prose("Compaction at the limit is unmeasured."))


def test_c62_expected_rows_are_pinned_not_range_only() -> None:
    """The recompute-side pin: dropping one arm row from C62's table must fail the check."""
    source = (PACKAGE / "recompute.py").read_text(encoding="utf-8")
    for arm in ('"32k", "F-ptr"', '"32k", "S"', '"64k", "F-ptr"'):
        assert arm in source, f"recompute.py's C62 pinned rows no longer contain ({arm})"
    assert re.search(r'"C62":\s*c62', source), "recompute.py no longer registers C62"
