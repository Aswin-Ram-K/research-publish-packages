"""Red->green guard: U4's null result may never be printed as a positive claim.

Why this file exists
--------------------
U4 compared three rewriting policies and reported that ``summarise_in_place`` and ``fork``
had **identical break cost** (21 pairs, median delta 0, 18/21 exactly 0, p = 1.0, C11), and
its card concluded the edit-vs-fork hypothesis was **REFUTED**.  It was not refuted: the cell
driver rendered every arm through one appender (``RENDER = naive_append``; ``POINTER_FORK``
never imported, C13), so a fork chain and a summarise chain over the same nodes emitted the
same bytes and the "comparison" compared an arm with itself.  What the rows measure is
**renderer identity**, not policy.  The correct record is therefore:

    the fork hypothesis is UNTESTED at n>0 under the fixed library -- NOT REFUTED

That qualifier is the whole point of MANUSCRIPT SS 5 ("the one error this package exists to
prevent").  It is also invisible to every other check in the repo: ``recompute.py``'s C13
pins the *static source fact* that one renderer was used, and C11 pins the *degenerate pair
statistics* (p = 1.0), but nothing pins the sentence a reader takes away.  A rewrite that
kept C13/C11 intact and deleted the qualifier --

    "the edit-vs-fork hypothesis is refuted" / "fork and summarise cost the same"

-- would pass ``recompute.py``, ``tests/test_paper_attribution_guard.py`` (it guards the
1.700x attribution) and ``tests/test_paper_g3_bands.py`` (it guards the boundary band).  The
FIX/GUARD-INDEP handoff names exactly this as the natural next guard
(``orchestration/handoffs/GUARD-INDEP.json`` ``next_unit_hint``).  On the other side, the
package's equally-degenerate *positive* readings -- "fork equals summarise", "the policies
cost the same", "forking saves the prefix" -- must not be asserted either; they are the same
error pointing the other way.  A **dated** G1 measurement (C44) now supplies a real break-cost
comparison and is allowed to say so, because it is a different cell with rows that discriminate
(2 of 6 events within 10 %, E/F = 1.038): the deny list therefore only fires on a coincidence
claim made about **U4 / U5 / its 21 pairs**.

This guard exists because a prior unit claimed this guard and did not write it: the
``GUARD-U4`` and ``GUARD-U4-R1`` cards reported ``tests/test_context_cache_qualifier.py`` as an
artefact while the file was absent from the tree.  An artefact asserted in a handoff is not an
artefact; the file, its measurement and its digest are.

What is in scope
----------------
  (A) PRESENCE -- every document in the package's own reading order that names the U4
      comparison states, near it, that the hypothesis is untested / not refuted / remains
      open.  Absence of a refutation is never rendered as a finding.
  (B) DENY -- no document asserts the EXCLUDED middle: refuted, or measured-equal.  Both are
      statements about the policies that U4's rows cannot support, in either direction.
  (C) PROVENANCE -- the qualifier travels with the cell it belongs to, and the two facts that
      make it necessary (one renderer, C13; bodies separate only under the fixed library,
      C16) stay stated, so that a future editor cannot delete the reason and keep the
      conclusion.
  (D) CODE-SIDE -- ``recompute.py`` still pins the two claims the prose rests on (C13's single
      renderer, C11's degenerate pairs); a prose fix over unchanged rows is not enough, and a
      rows fix without a prose fix is not either.

Deliberately not a table of known-good phrasings: the presence side accepts the package's own
vocabulary ("untested", "not refuted", "remains open") so a legitimate rewrite is not forced
to reuse a sentence, and the deny side is a short list of *assertions* rather than words --
"refuted" appears legitimately in the abstract ("untested at n>0, not refuted") and in the
correction tables ("the ``REFUTED`` in U4's handoff is superseded"), so a bare word ban would
fail on the corrected tree.

Red->green (measured on the 2026-10-23 tree,
``PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_context_cache_qualifier.py -q``)
-------------------------------------------------------------------------
RED.  ``MANUSCRIPT.md`` SS 5's consequence paragraph reverted to the U4 card's reading --
"The hypothesis ... **was refuted by the comparison**" with the "untested at n>0, not
refuted" clause deleted -- and ``CLAIMS.md`` correction 3 and ``PACKAGE.md``'s bullet reverted
with it to "the hypothesis is refuted": the deny test (B) fails with ``[DENY]`` on all three
documents.  GREEN.  The qualifier restored: all tests pass.  The exact RED/GREEN counts and
the restored digests are recorded in ``orchestration/handoffs/GUARD-U4-R2.json``.

Offline: reads five Markdown files and one Python file off disk; no network, no lock, no rows.
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

#: How the package names the comparison U4 made.  Any document that mentions it is a
#: document in which a reader can learn what U4 concluded, so all of them are in scope.
COMPARISON = re.compile(
    r"edit[- ]vs[- ]fork"
    r"|fork (?:comparison|hypothesis|question)\b"
    r"|(?:summarise|summarize)[_ ]in[_ ]place\W{0,40}\bfork\b"
    r"|\bfork\b[\s\S]{0,40}(?:cost the same|same break cost|equals? summarise)",
    re.IGNORECASE,
)

#: The qualifier, in the vocabulary the corrected tree already uses.  Kept as alternatives so
#: a rewrite does not have to reuse a sentence; the requirement is the *claim*, not the words.
QUALIFIER = re.compile(
    r"untested|not refuted|\bnot\b[\s\S]{0,40}\brefut\w*|remains? open|has not been made"
    r"|has not been (?:run|measured|compared)|no information about|measured (?:renderer )?nothing"
    r"|cannot be salvaged|null experiment"
    # the hedge form: "must not be read the way the earlier cards read them", "is invalid"
    r"|must not be read|invalid comparison|is the (?:first|one) thing a reviewer should check",
    re.IGNORECASE,
)

#: The assertions U4's rows cannot support, in either direction.  Each is a *statement about
#: the policies*, not a mention of the word.  A dated G1 (C44) comparison may assert what it
#: measured, so every pattern here is required to sit where the coincident reading is being
#: claimed rather than merely reported as superseded -- hence the negation/quote screening in
#: ``_denied_assertions``.
DENIED = (
    # The refutation reading, as U4's card stated it.  Scoped to a claim *about the policies*
    # ("the hypothesis was refuted", "the comparison refuted it") -- a refuted premise or a
    # refuted *renderer question* is a different subject and is legitimately in the tree.
    (re.compile(
        r"(?:\b(?:the |this )?(?:edit[- ]vs[- ]fork |fork )?(?:hypothesis|comparison|question|"
        r"conclusion)\b[\s\S]{0,90}\b(?:was|is|has been|had been|been)\s+refuted\b"
        r"|\brefut(?:ed|es)\s+the\s+(?:edit[- ]vs[- ]fork |fork )?(?:hypothesis|comparison|"
        r"idea)\b"
        r"|\b(?:hypothesis|comparison)\b[\s\S]{0,30}\bis\s+(?:a\s+)?refutation\b)",
        re.IGNORECASE), "the hypothesis is stated as refuted"),
    # The measured-equal reading, which is the same null result dressed as a finding.  Scoped
    # to the *coincident-cost* frame: "fork ... costs the same as summarise".  A byte-level
    # "the fork digests equal the summarise digest" is C03, the very defect being qualified.
    (re.compile(
        r"(?:fork|edit)\b(?:\s+\w+){0,4}\s+(?:costs?|pays?|prices?|lands?)\b[\s\S]{0,40}"
        r"\b(?:the same|equally|identical)\b[\s\S]{0,30}(?:summarise|summarize)",
        re.IGNORECASE), "fork is stated as costing the same as summarise"),
    (re.compile(
        r"(?:summarise|summarize)\b(?:\s+\w+){0,4}\s+(?:costs?|pays?)\b[\s\S]{0,40}"
        r"\bthe same\b[\s\S]{0,20}fork",
        re.IGNORECASE), "summarise is stated as costing the same as fork"),
    (re.compile(
        r"\b(?:policies|arms|strategies)\b[\s\S]{0,40}\b(?:cost the same|have (?:the )?same "
        r"(?:break )?cost|produce (?:the )?same (?:break )?cost)\b",
        re.IGNORECASE), "the policies are stated as costing the same"),
    # the premise that would license the two readings above without naming them
    (re.compile(
        r"\bno (?:measurable )?difference (?:in break cost )?between (?:fork and summarise|"
        r"summarise and fork)",
        re.IGNORECASE), "a no-difference finding is stated for fork vs summarise"),
)

#: How far from the comparison noun its qualifier may sit.  Measured on the corrected tree the
#: qualifier is inside the same sentence everywhere (MANUSCRIPT SS 5 consequence, abstract,
#: PACKAGE bullet, CLAIMS correction 3, EVIDENCE correction row, GAPS G1); 500 characters
#: also covers a table row whose effect cell trails its cells.
WINDOW = 500

#: The package's reading order -- ``READER-MAP.md`` sends a reader to these in this sequence,
#: and a reader who stops after any one of them must not come away with the refutation.
DOCUMENTS = (MANUSCRIPT, CLAIMS, PACKAGE_MD, EVIDENCE, GAPS)


def _prose(text: str) -> str:
    """Blank fenced blocks and inline code, preserving offsets for line numbers."""
    text = re.sub(r"^(```|~~~).*?^\1", lambda m: re.sub(r"[\s\S]", " ", m.group(0)),
                  text, flags=re.DOTALL | re.MULTILINE)
    return re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), text)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _excerpt(text: str, offset: int, span: int = 260) -> str:
    start = max(0, offset - span // 2)
    return " ".join(text[start: offset + span // 2].split())[:span]


def _denied_assertions(prose: str) -> list[str]:
    """Assertions in the excluded middle, screened for the legitimate ones.

    Two legitimate contexts keep a denied pattern in the tree and must not fail the guard:

      * a **quotation** of the superseded phrasing -- the tree wraps U4's own words in double
        quotes ("``REFUTED``", "refuted by the comparison") and marks the correction table
        rows with the word *superseded* / *restated*;
      * a statement about **what U4's rows do not do** (``"U4's comparison measured nothing"``,
        ``"cannot be salvaged"``), which the presence side already requires.

    The screen is therefore: drop a hit whose sentence quotes the reading, and drop a hit whose
    clause carries an explicit supersession word.
    """
    found = []
    # the supersession screen must also see the clause that follows the assertion ("... was
    # refuted. That conclusion is void:") -- the corrective clause routinely opens the next
    # sentence, so the window runs on to the second sentence end.
    SUPERSESSION = re.compile(
        r"\bsupersed\w*|\brestated\b|\bnot\b[\s\S]{0,40}\brefut"
        r"|\bis void\b|\bvoid\b|\bwrong to do so\b|\bis wrong\b",
        re.IGNORECASE)
    for pattern, label in DENIED:
        for hit in pattern.finditer(prose):
            # sentence window around the hit, extended one sentence to the right
            lo = prose.rfind(". ", 0, hit.start())
            lo = 0 if lo < 0 else lo + 1
            hi = prose.find(". ", hit.end())
            hi = len(prose) if hi < 0 else hi + 1
            hi2 = prose.find(". ", hi + 1)
            hi2 = len(prose) if hi2 < 0 else hi2 + 1
            sentence = prose[lo:hi2]
            if SUPERSESSION.search(sentence):
                continue
            # a denied assertion wrapped in quotation marks is a quotation of the old reading
            before = prose[max(0, hit.start() - 1): hit.start()]
            if before in {'"', "\u201c", "`"}:
                continue
            found.append(f"{label}: {_excerpt(prose, hit.start())}")
    return found


# --------------------------------------------------------------------------- #
# (A) the qualifier is present wherever a reader meets the comparison
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: p.name)
def test_a_document_that_names_the_comparison_carries_the_qualifier(path: Path) -> None:
    assert path.is_file(), f"{path} is missing -- the guard has nothing to read"
    prose = _prose(path.read_text(encoding="utf-8"))
    hits = list(COMPARISON.finditer(prose))
    if not hits:
        pytest.skip(f"{path.name} does not name the U4 comparison; nothing to qualify")
    missing = []
    for hit in hits:
        lo = max(0, hit.start() - WINDOW)
        hi = min(len(prose), hit.end() + WINDOW)
        if not QUALIFIER.search(prose[lo:hi]):
            missing.append(
                f"{path.name}:{line_of(prose, hit.start())} [PRESENCE] the comparison is "
                f"named with no untested/not-refuted qualifier: {_excerpt(prose, hit.start())}"
            )
    assert not missing, (
        "U4's arms were rendered by one appender (C13), so its identical break cost is a "
        "measurement of renderer identity, not of policy. Every mention of the comparison "
        "must carry that reading -- 'untested at n>0', 'not refuted', 'remains open'. "
        "Findings:\n  - " + "\n  - ".join(missing)
    )


# --------------------------------------------------------------------------- #
# (B) the excluded middle is denied in every document
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("path", DOCUMENTS, ids=lambda p: p.name)
def test_no_document_asserts_the_refutation_or_the_equality(path: Path) -> None:
    prose = _prose(path.read_text(encoding="utf-8"))
    found = _denied_assertions(prose)
    assert not found, (
        "PUBLISHED FAILURE MODE: U4's card concluded the edit-vs-fork hypothesis was REFUTED "
        "and this package exists partly to undo that. Its rows cannot support either "
        "direction -- 'refuted' or 'fork and summarise cost the same' -- because both arms "
        "were the same bytes. Say 'untested at n>0, not refuted' and name C13/C16. "
        f"Findings in {path.name}:\n  - " + "\n  - ".join(found)
    )


def test_the_same_screen_would_catch_the_original_reading() -> None:
    """Self-check: the deny patterns bite on the U4 card's own sentence and on the
    measured-equal restatement, and do NOT bite on the corrected tree's quotations."""
    refutation = _denied_assertions(
        "On that basis the edit-vs-fork hypothesis was refuted and the card triggered."
    )
    assert refutation, "the deny screen does not catch 'the hypothesis was refuted'"
    equality = _denied_assertions(
        "Break cost was identical for summarise_in_place and fork, so fork costs the same as summarise."
    )
    assert equality, "the deny screen does not catch 'fork costs the same as summarise'"
    quoted = _denied_assertions(
        'U4 recorded the edit-vs-fork hypothesis as "REFUTED"; that reading is superseded.'
    )
    assert not quoted, (
        "the deny screen flags the corrected tree's own quotation of the superseded reading, "
        "which would make the guard unfixable: " + "; ".join(quoted)
    )


# --------------------------------------------------------------------------- #
# (C) the qualifier travels with its provenance
# --------------------------------------------------------------------------- #
def test_the_manuscript_states_the_two_facts_that_make_the_qualifier_necessary() -> None:
    """SS 5 must keep the *reason*: one renderer ran every arm, and only the fixed library
    separates the bodies. Deleting either leaves the conclusion unsupported and unexplained."""
    prose = _prose(MANUSCRIPT.read_text(encoding="utf-8"))
    section = prose.find("## 5.")
    assert section >= 0, "MANUSCRIPT.md no longer has a '## 5.' section"
    end = prose.find("\n## 6.", section)
    assert end > section, "MANUSCRIPT.md's SS 5 no longer ends before '## 6.'"
    block = prose[section:end].replace("\u2212", "-")
    for token, why in (
        ("C13", "the static fact that one renderer ran every arm"),
        ("C16", "the replay that separates the bodies from turn 12 under the fixed library"),
        ("11/44", "the under-the-fixed-library body equality count"),
        ("438", "U4's row count -- the rows cannot be salvaged"),
    ):
        assert token in block, (
            f"MANUSCRIPT SS 5 no longer carries {token} ({why}). The qualifier without its "
            "provenance is an assertion a future editor can delete the reason for and keep, "
            "which is how 'refuted' came back the first time."
        )
    assert QUALIFIER.search(block), (
        "MANUSCRIPT SS 5 no longer says the hypothesis is untested / not refuted"
    )


def test_the_abstract_keeps_the_qualifier_it_reports_as_a_negative_result() -> None:
    """The abstract is where most readers stop; it may not lose 'not refuted'."""
    prose = _prose(MANUSCRIPT.read_text(encoding="utf-8"))
    abstract_end = prose.find("## 1.")
    assert abstract_end > 0, "MANUSCRIPT.md no longer has an abstract before '## 1.'"
    abstract = prose[:abstract_end]
    assert COMPARISON.search(abstract), (
        "the abstract no longer reports the U4 comparison as a negative result; it is one of "
        "the two results the abstract says 'change how the record must be read'"
    )
    assert QUALIFIER.search(abstract), (
        "the abstract names the fork comparison without the 'untested at n>0, not refuted' "
        "qualifier -- the exact claim U4 got wrong"
    )


# --------------------------------------------------------------------------- #
# (D) the code-side facts the prose rests on
# --------------------------------------------------------------------------- #
def test_recompute_still_pins_the_single_renderer_and_the_degenerate_pairs() -> None:
    source = RECOMPUTE.read_text(encoding="utf-8")
    for key, value in (
        ('"RENDER"', '"naive_append"'),
        ('"POINTER_FORK_in_source"', "False"),
    ):
        assert re.search(re.escape(key) + r"\s*:\s*" + re.escape(value), source), (
            f"recompute.py's C13 expected value no longer pins {key}: {value}. C13 is the "
            "static fact (one renderer, never the pointer fork) that makes U4's identical "
            "break cost a measurement of the renderer; without it the qualifier has no cause."
        )
    for key, value in (
        ('"n_pairs"', "21"),
        ('"n_zero"', "18"),
        ('"permutation_p"', "1.0"),
    ):
        assert re.search(re.escape(key) + r"\s*:\s*" + re.escape(value), source), (
            f"recompute.py's C11 expected value no longer pins {key}: {value}. The degenerate "
            "pairs (21, 18 exactly zero, p = 1.0) are the evidence that the comparison carried "
            "no information; a prose fix over changed rows would be a claim about nothing."
        )
    assert '"C13"' in source and '"C11"' in source, (
        "recompute.py no longer registers C13/C11, the two claims this qualifier rests on"
    )
