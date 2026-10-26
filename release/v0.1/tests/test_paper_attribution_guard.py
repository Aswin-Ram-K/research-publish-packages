"""Red->green guard: the context-cache package may not re-attribute 1.700x to break cost.

Why this file exists
--------------------
The context-cache synthesis package makes one load-bearing causal claim: append-a-note
beats summarise-in-place by ``1.700x`` on total uncached tokens, and that gap is a
**post-compaction window-truncation** effect (92.2 % of R's excess), *not* a break-event
effect.  The refuted reading -- "avoiding the break saves the prefix", i.e. the win is
bought by not creating the break -- was the original causal reading of C21.  G1 re-measured
the per-break cost at ``E/F = 1.038`` (within measurement noise; 2 of 6 break events within
10 %) and U15's own decomposition puts only 7.8 % of the excess on the break, so the
refuted reading is now the wrong one.

``papers/context-cache/recompute.py``'s C44 guard flips to FAIL if
``u15_1_700x_survives_decomposition`` is expected True -- but that is a CODE-side guard: it
checks a number, not a sentence.  ``tests/test_claims_decompose.py`` is also out of scope: it
tests the ``resextract`` claims store, not ``papers/context-cache/``.  So before this file
existed, the manuscript could drift back to the refuted causal sentence and every check in
the repo would still pass (V-PAPER, verdict ``partial``, ``not_reproduced``).

What is in scope
----------------
ONLY prose that makes a *causal claim* about the 1.700x.  This guard therefore asserts three
things and nothing more:

  (A) the G1 attribution is PRESENT -- near each place the 1.700x figure is stated, the
      document says the gap is a post-compaction window-truncation effect;
  (B) no DENIED assertion is present -- the specific refuted readings (the 1.700x *is* a
      break-cost win; append/not-creating-the-break/forking *saves* the prefix; the win
      *comes from* avoiding the break);
  (C) no break-cost noun sits in a win-attributing frame near the 1.700x figure.

Deliberately NOT a table of known-good phrasings.  A whitelist would force every legitimate
rewrite to fight the test; instead the deny side is a short list of refuted *assertions*
and the assert side is the presence of the attribution, so a re-wording that keeps the
G1 reading passes and a re-wording that flips the cause fails.

Historical quotes are out of scope, by a marker the documents already use: a denied phrase
inside a double-quoted span (``"avoiding the break saves the prefix"``) is a quotation of a
superseded phrasing, and ``CLAIMS.md`` § "Corrections to the source cards" and
§ "Supersessions by G1" record exactly those in that form.  Inline code spans are skipped
for the same reason -- they name cards, files and claim ids, not prose.  No new syntax is
invented; a legitimate causal statement is never written inside quotation marks, and
``test_a_quotation_cannot_smuggle_the_claim_back`` proves an *unquoted* statement of the
refuted reading is still caught.

Red->green (PROVEN; transcript is the ``red_green`` field of
``orchestration/handoffs/GUARD-ATTR.json``)
-------------------------------------------------------------------------
Measured 2026-10-22, ``PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
tests/test_paper_attribution_guard.py -q``.

  RED-1 (manuscript).  The abstract's G1 sentence (the one ending "...not a fork/append
  cost (u15_1_700x_survives_decomposition = False; C44)") replaced by ``Avoiding the break
  is what buys the 1.700x: an arm that never creates the break keeps the prefix and saves
  the tokens, which is why appending beats compacting here.``: ``2 failed, 7 passed`` --
  ``MANUSCRIPT.md:28 [ATTR]`` and ``MANUSCRIPT.md:21 [ATTR]`` (the paragraph's other two
  figures lost their attribution with it).  ``tests/test_claims_decompose.py`` stayed
  ``13 passed`` and ``recompute.py all`` stayed ``42 claims checked, all match``: nothing
  else in the repo noticed.

  RED-2 (claims table).  The C44 row's ``the 1.700x is post-compaction window truncation,
  not break-event cost`` replaced by ``the 1.700x is a break-cost win``: ``1 failed,
  8 passed`` -- ``CLAIMS.md:127 [DENY-1]`` plus ``CLAIMS.md:94`` / ``:97 [ATTR]`` (C21/C24
  lost their re-attribution).

  GREEN.  Both files restored from byte-identical pre-edit copies; sha256 back to
  MANUSCRIPT.md ``c22656c8c55f8f198ffd63305b00b018be94b836bdacf95bf8b907ac40c203e5`` and
  CLAIMS.md ``dd3c2d8c7635008c80e788b0d4d657951829dbddca2efce9f824a566e1e64b7d``;
  ``9 passed``.

GUARD-INDEP (added 2026-10-23): the same failure mode, a second claim
--------------------------------------------------------------------
FIX-MAN2 repaired the abstract's renderer sentence from "two independently implemented
prompt renderers emitted byte-identical prompts" to a statement that both render modes are
``RenderPolicy`` variants of one library -- and measured that reverting it left this file at
``11 passed``.  Nothing pinned the sentence.  The block at the bottom of this file (see
"GUARD-INDEP" below) pins it, with the red->green transcript in the ``red_green`` field of
``orchestration/handoffs/GUARD-INDEP.json``:

  RED-1 (abstract, the FIX-MAN2 revert verbatim): ``1 failed, 17 passed`` --
  ``MANUSCRIPT.md:9 [INDEP-DENY]``.

  RED-2 (SS 2, abstract restored): the mechanism clause ("a property of one library, not of
  two independent implementations: both render modes are the RenderPolicy variants ...")
  deleted: ``2 failed, 16 passed`` -- ``MANUSCRIPT.md:96 [INDEP]`` (the SS 2 statement at
  ``:96`` loses its mechanism, and the abstract's copy of the figure at ``:10`` loses it too,
  since the abstract never carried it; measured in isolation on the 2026-10-23 tree).

  GREEN: manuscript restored byte-identically, sha256 back to
  ``342cd4dd3067cd35c36cc1b396bd95b236d387111014b8bb4e92f88393240e34`` (the digest FIX-MAN2
  recorded for the repaired file); ``18 passed``.

Offline: reads two Markdown files off disk; no network, no cache lock, no rows.  Neither
paragraph of this docstring may outlive its measurement: the GREEN digest above is the whole
reason the red->green claim can be re-checked later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "papers" / "context-cache"
MANUSCRIPT = PACKAGE / "MANUSCRIPT.md"
CLAIMS = PACKAGE / "CLAIMS.md"

#: The two figures the claim is stated with. ``1.7002x`` (C21's own value) and ``1.70x``
#: (the rounded restatement in SS 10 rule 2) are the same claim, so all three forms are the
#: anchor; a document that states the claim must state it with one of them.
FIGURE = re.compile(r"1\.700\d*x|1\.70x", re.IGNORECASE)

#: How far around a figure to look for its attribution.  Measured on the current tree, the
#: attribution is not always adjacent: the abstract states the figure and its G1 attribution
#: in one 1,077-character paragraph (figure at the head, attribution at the tail), and in
#: CLAIMS.md the figure sits in the C21/C24 rows while its re-attribution is the C44 row
#: 5,034-5,171 characters later -- the ROWS ARE ALIGNED, so C21's own row is padded to a
#: column width and the distance is table padding, not prose.  A window that cannot reach
#: C44 is exactly the hole to close (a revert that keeps an honest C44 row but flips the
#: prose around the figure in the same table would pass a narrower guard).  The measured
#: span is 5,171 characters, so the window is 6,000: wider than the table's own padding and
#: narrower than one h1 section of the manuscript (the abstract to SS 1 is ~2.3 kB, SS 6 to
#: SS 7 ~5.7 kB, and the nearest *unrelated* figure-to-attribution distance is larger still).
WINDOW = 6000

#: How far around a figure to look for a causal reading.  The deny patterns are self-
#: contained assertions ("the 1.700x is ... break"), so they need the figure only adjacent;
#: a wide window here would let C44's own corrective sentence ("... truncation, not
#: break-event cost") read as a denial.
CAUSAL_WINDOW = 200

#: The G1 attribution, as a conjunction of markers that must all appear in one window.
#: The package names the effect "post-compaction window truncation" (abstract, SS 6, C44),
#: "compaction-window cost" (SS 6, SS 10 rule 2) and "steady-state truncation" (SS 10); any
#: one of those, together with a negation of break/fork/append cost, is the attribution.
#: Kept as alternatives, not as a sentence, so the wording may change.  "window cost" alone
#: is NOT accepted: C21/C24's own rows say R's *window cost* is unbounded (C25), a different
#: statement, and accepting it would make the attribute side tap out on a table row that
#: never mentions truncation.
ATTRIBUTION_EFFECT = re.compile(
    r"window[- ]truncat|truncat\w* window|window[- ]policy|window-polic"
    r"|steady[- ]state truncat|truncation[- ]plus|truncation \*plus\*",
    re.IGNORECASE,
)
ATTRIBUTION_NEGATION = re.compile(
    r"\bnot\b[^.]{0,80}\b(?:break|fork|append)\w*[^.]{0,40}cost"
    r"|\b(?:break|fork|append)\w*[- ]cost\b[^.]{0,60}\bnot\b"
    r"|\bnot (?:an? )?(?:break|fork|append)\w*[- ]?(?:cost|effect|win)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Denial:
    """One refuted assertion, as a pattern plus the reading it encodes."""

    code: str
    why: str
    pattern: re.Pattern[str]


#: The refuted causal assertions.  Each is an ASSERTION about the 1.700x / the prefix, not a
#: word list: "break" appears everywhere in this package legitimately (SS 6's table column is
#: "Net break cost"), so a bare noun is never a finding.
DENIALS: tuple[Denial, ...] = (
    Denial(
        "DENY-1",
        "the 1.700x (or the win / the gain) *is* a break-cost win",
        re.compile(
            r"(?:1\.700\d*x|1\.70x|the (?:win|gain|advantage|speedup|saving)s?)"
            r"[^.]{0,120}?"
            r"\b(?:is|was|comes from|derives from|stems from|is due to|is driven by|"
            r"is attributable to|is bought by|is a result of)\b"
            r"[^.]{0,60}?\bbreak\b",
            re.IGNORECASE,
        ),
    ),
    Denial(
        "DENY-2",
        "avoiding / not creating / skipping the break saves the prefix (or the tokens)",
        re.compile(
            r"\b(?:avoid|avoiding|avoids|avoided|dodge|dodging|sidestep\w*|skip\w*|"
            r"prevent\w*|elide|eliding|bypass\w*|never (?:creating|incurring|paying)|"
            r"without (?:ever )?(?:creating|incurring))"
            r"\b[^.]{0,40}?\b(?:the )?(?:break|breaks|compaction break|break event)\b"
            r"[^.]{0,120}?\b(?:save\w*|saves|buys?|wins?|earns?|protects?|preserves?|"
            r"keeps?|retains?|recovers?)\b"
            r"[^.]{0,120}?\b(?:prefix|tokens?|cache|window)\b",
            re.IGNORECASE,
        ),
    ),
    Denial(
        "DENY-3",
        "forking instead of compacting is what buys the prefix / the tokens",
        re.compile(
            r"\bfork\w*\b[^.]{0,60}?\binstead of\b[^.]{0,60}?\b(?:compact|summaris|summariz)\w*"
            r"[^.]{0,80}?\b(?:buys?|saves?|wins?|earns?|keeps?|preserves?|protects?)\b"
            r"[^.]{0,60}?\b(?:prefix|tokens?|cache)\b",
            re.IGNORECASE,
        ),
    ),
    Denial(
        "DENY-4",
        "not compacting is what buys the 1.700x (append's win is attributed to the absence "
        "of compaction rather than to the retained window)",
        re.compile(
            r"\b(?:not compacting|never compacting|no compaction|avoid\w* compaction|"
            r"skipping compaction|compaction[- ]free)\b"
            r"[^.]{0,80}?\b(?:is|was|buys?|saves?|wins?|earns?|delivers?|gives?)\b"
            r"[^.]{0,80}?\b(?:1\.700\d*x|1\.70x|the win|the gain)\b",
            re.IGNORECASE,
        ),
    ),
    Denial(
        "DENY-5",
        "compact *earlier* / *less* to save prefix tokens (the steady-state reading forbids "
        "this: the truncation cost is what compaction buys, not what it saves)",
        re.compile(
            r"\b(?:compact|compacting|compaction)\b[^.]{0,40}?\b(?:earlier|sooner|less often|"
            r"less aggressively)\b"
            r"[^.]{0,60}?\b(?:saves?|saving|buys?|reduces?|cuts?)\b"
            r"[^.]{0,40}?\b(?:prefix|tokens?)\b",
            re.IGNORECASE,
        ),
    ),
)

#: A causal reading assembled across clauses without any of the DENIALS verb forms: a
#: break-cost noun in a win-attributing frame near the figure.  This is the "implies" half of
#: the brief -- e.g. "the 1.700x is what not breaking is worth".
COUNTERFACTUAL_WIN = re.compile(
    r"(?:1\.700\d*x|1\.70x)"
    r"[^.]{0,120}?"
    r"\b(?:would not hold|would vanish|disappears?|is what|is (?:the )?worth|"
    r"is bought|is paid for|rests on)\b"
    r"[^.]{0,80}?"
    r"\b(?:break|breaks|breaking)\b",
    re.IGNORECASE,
)

#: The span of a DENY match counts as a denial only if it is not negated: G1's own
#: corrective sentence "-- the 1.700x is a post-compaction window-truncation cost, not a
#: fork/append cost --" overlaps DENY-1's shape ("... is ... fork") while asserting the
#: opposite.  A negated copula in front of the attributed noun ("is not a break-cost
#: effect") is the attribution, not the claim.
NEGATED_HEAD = re.compile(
    r"\b(?:is|was|are|were)\s+not\b"
    r"|\bnot\s+(?:an?|the)\s+\w"
    r"|\bnot\b[^.]{0,20}\bcost\b",
    re.IGNORECASE,
)


def denial_spans(text: str) -> list[tuple[Denial, re.Match[str]]]:
    """Every DENY match whose own sentence does not negate it."""
    hits: list[tuple[Denial, re.Match[str]]] = []
    for denial in DENIALS:
        for match in denial.pattern.finditer(text):
            sentence_end = text.find(". ", match.end())
            tail = text[match.start() : len(text) if sentence_end < 0 else sentence_end]
            if NEGATED_HEAD.search(tail):
                continue
            hits.append((denial, match))
    return hits


# --------------------------------------------------------------------------- #
# Reading the prose: strip what is not a causal assertion.
# --------------------------------------------------------------------------- #

_FENCE = re.compile(r"^(```|~~~).*?^\1", re.DOTALL | re.MULTILINE)
_QUOTED = re.compile(r'"[^"\n]{3,200}"')
_INLINE_CODE = re.compile(r"`[^`\n]*`")


def assertion_text(text: str) -> str:
    """Return the text with non-assertion spans blanked out, preserving offsets.

    Fenced blocks are prose in this package (the CPython block in ``CLAIMS.md``'s header),
    double-quoted spans are historical quotations, and inline-code spans name cards and
    files.  Each is replaced by spaces of the same length so that character offsets, line
    numbers and the +/- WINDOW neighbourhoods stay valid.
    """

    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    for pattern in (_FENCE, _QUOTED, _INLINE_CODE):
        text = pattern.sub(blank, text)
    return text


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def excerpt(text: str, offset: int) -> str:
    """The sentence-ish fragment around an offset, for a readable failure message."""
    start = max(0, text.rfind(". ", 0, offset) + 2 if text.rfind(". ", 0, offset) >= 0 else 0)
    end = text.find(". ", offset)
    end = len(text) if end < 0 else end + 1
    return " ".join(text[start:end].split())[:400]


@dataclass
class Document:
    path: Path
    raw: str
    prose: str

    @property
    def name(self) -> str:
        return self.path.name

    def findings(self) -> list[str]:
        found: list[str] = []

        # (A) every statement of the figure carries the G1 attribution beside it.
        for match in FIGURE.finditer(self.prose):
            lo, hi = max(0, match.start() - WINDOW), min(len(self.prose), match.end() + WINDOW)
            window = self.prose[lo:hi]
            if not (ATTRIBUTION_EFFECT.search(window) and ATTRIBUTION_NEGATION.search(window)):
                found.append(
                    f"{self.name}:{line_of(self.prose, match.start())} [ATTR] "
                    f"'{match.group(0)}' is stated with no nearby G1 attribution "
                    f"(expected a window-truncation / compaction-window reading and a "
                    f"negation of break/fork/append cost). Text: {excerpt(self.prose, match.start())}"
                )

        # (B) no refuted causal assertion.
        for denial, match in denial_spans(self.prose):
            found.append(
                f"{self.name}:{line_of(self.prose, match.start())} [{denial.code}] "
                f"refuted causal reading present ({denial.why}). Text: "
                f"{excerpt(self.prose, match.start())}"
            )

        # (C) the assembled counterfactual framing, near a figure.
        for match in COUNTERFACTUAL_WIN.finditer(self.prose):
            near = any(
                abs(match.start() - fig.start()) <= CAUSAL_WINDOW
                for fig in FIGURE.finditer(self.prose)
            )
            if not near:
                continue
            found.append(
                f"{self.name}:{line_of(self.prose, match.start())} [DENY-6] "
                f"the figure is framed as resting on the break. Text: "
                f"{excerpt(self.prose, match.start())}"
            )
        return found


def load(path: Path) -> Document:
    assert path.is_file(), f"{path} is missing -- the guard has nothing to read"
    raw = path.read_text(encoding="utf-8")
    return Document(path=path, raw=raw, prose=assertion_text(raw))


@pytest.fixture(scope="module")
def manuscript() -> Document:
    return load(MANUSCRIPT)


@pytest.fixture(scope="module")
def claims() -> Document:
    return load(CLAIMS)


# --------------------------------------------------------------------------- #
# The guard.
# --------------------------------------------------------------------------- #


def test_the_package_documents_exist() -> None:
    assert MANUSCRIPT.is_file() and CLAIMS.is_file(), (
        f"{MANUSCRIPT} and {CLAIMS} are the documents this guard reads; both must be present"
    )


def test_no_document_re_attributes_the_1_700x_to_break_cost(manuscript: Document, claims: Document) -> None:
    """The whole guard: attribution present, refuted readings absent, in both documents."""
    findings = manuscript.findings() + claims.findings()
    assert not findings, (
        "the context-cache package says (or implies) that avoiding the break / not "
        "compacting / forking instead of compacting saves prefix tokens. G1 re-attributes "
        "the 1.700x to post-compaction window truncation (E/F = 1.038; C44). Keep the "
        "historical quotation in double quotes, or re-word. Findings:\n  - "
        + "\n  - ".join(findings)
    )


def test_the_figure_is_actually_stated(manuscript: Document, claims: Document) -> None:
    """A guard on a document that stopped stating the claim would pass vacuously."""
    assert FIGURE.search(manuscript.prose) or FIGURE.search(
        claims.prose
    ), "no 1.700x / 1.70x figure found in MANUSCRIPT.md or CLAIMS.md -- the guard is vacuous"


def test_the_attribution_is_stated_in_the_abstract_and_in_section_6(manuscript: Document) -> None:
    """The two places a reader meets the claim: the abstract and SS 6.

    Pins the G1 attribution where it matters rather than only somewhere, so a rewrite that
    keeps one stray attribution and reverts the headline sentence still fails (A above).
    """
    prose = manuscript.prose
    abstract_end = prose.find("## 1.")
    section6 = prose.find("## 6.")
    section7 = prose.find("## 7.")
    assert 0 < abstract_end and 0 < section6 < section7, (
        "MANUSCRIPT.md no longer has the section structure this guard addresses "
        "(abstract before '## 1.', '## 6.' before '## 7.')"
    )
    for label, lo, hi in (
        ("abstract", 0, abstract_end),
        ("section 6", section6, section7),
    ):
        block = prose[lo:hi]
        assert ATTRIBUTION_EFFECT.search(block), (
            f"the {label} no longer states a window-truncation / compaction-window "
            f"attribution for the 1.700x (C44)"
        )
        assert ATTRIBUTION_NEGATION.search(block), (
            f"the {label} no longer negates break/fork/append cost for the 1.700x (C44)"
        )


def test_c44_guard_in_recompute_is_not_weakened() -> None:
    """The code-side half stands: C44's expected value keeps survives_decomposition False.

    This file guards the prose; it must not become the reason the numeric guard was
    loosened. If someone edits ``recompute.py`` to expect True so the prose guard is the
    only thing objecting, this fails first.
    """
    source = (PACKAGE / "recompute.py").read_text(encoding="utf-8")
    assert re.search(
        r'"u15_1_700x_survives_decomposition"\s*:\s*False', source
    ), "recompute.py's C44 expected value no longer has u15_1_700x_survives_decomposition=False"


# --------------------------------------------------------------------------- #
# The marker's own limits: a quotation is exempt, a statement is not.
# --------------------------------------------------------------------------- #


def test_a_quotation_is_exempt() -> None:
    """The marker the docs already use: a denied phrase inside double quotes is history."""
    quoted = 'The card said "avoiding the break saves the prefix" and G1 re-attributed it.'
    prose = assertion_text(quoted)
    assert '"' not in prose and "avoiding" not in prose, "the quoted span was not blanked"
    assert prose.startswith("The card said") and prose.rstrip().endswith("G1 re-attributed it.")
    assert " ".join(prose.split()) == "The card said and G1 re-attributed it."
    assert len(prose) == len(quoted), "blanking must preserve offsets for line numbers"


def test_a_quotation_cannot_smuggle_the_claim_back() -> None:
    """A reverted sentence is never quoted -- only the *rejected* phrasing is.

    The revert this guard exists for (the abstract's U15 reading) states the claim in
    prose; blanking the quotation spans the docs actually use does not touch it, so the
    exemption cannot be widened without failing here.
    """
    reverted = "Avoiding the break is what buys the prefix and the 1.700x follows."
    prose = assertion_text(reverted)
    assert any(d.pattern.search(prose) for d in DENIALS), (
        "an unquoted statement of the refuted reading slipped past every DENY pattern"
    )


def test_every_denial_pattern_matches_its_own_refuted_sentence() -> None:
    """Each DENY pattern is exercised by the sentence it is meant to catch (no dead guard)."""
    probes = {
        "DENY-1": "The 1.700x win is a break-cost effect.",
        "DENY-2": "Avoiding the break saves the prefix on every later turn.",
        "DENY-3": "Fork instead of compacting preserves the prefix across the run.",
        "DENY-4": "Not compacting is what buys the 1.700x.",
        "DENY-5": "Compacting less often saves prefix tokens.",
    }
    by_code = {d.code: d for d in DENIALS}
    for code, sentence in probes.items():
        assert by_code[code].pattern.search(sentence), (
            f"{code} no longer matches its own refuted sentence: {sentence!r}"
        )


def test_a_negated_sentence_is_not_a_denial() -> None:
    """G1's own corrective wording must never read as the claim it corrects."""
    correctives = (
        "The 1.700x is post-compaction window truncation, not break-event cost.",
        "The 1.700x is not a break-cost effect.",
        "so the 1.700x is a compaction-window cost, not a fork/append cost",
    )
    for sentence in correctives:
        assert not denial_spans(sentence), f"false positive on a corrective: {sentence!r}"
    assert denial_spans("The 1.700x win is a break-cost effect."), (
        "the negated-head exemption must not swallow the real claim"
    )


# --------------------------------------------------------------------------- #
# GUARD-INDEP: "one library, not two" cannot be silently reverted.
#
# The guard above protects the 1.700x attribution and the G5/M4 cells.  This block
# protects a *different* correction, made after that guard was written: the
# renderer-identity result (760/760 byte-identical, C01) compares
# ``RenderPolicy.POINTER`` against ``RenderPolicy.NAIVE_APPEND`` -- two mode flags of
# ONE appender in ``resextract.context``, reached through ONE
# ``build_cell(..., policy=...)`` call (``experiments/context-cache/cells/CX-V2/
# u5_recon.py:47-48``).  It is not two independent implementations, and reading it as
# one infers convergence the build could not have produced.
#
# The defect this fixes was measured, not imagined (FIX-MAN2, ``unverified[0]``):
# reverting the abstract to "two independently implemented prompt renderers emitted
# byte-identical prompts" left this file at ``11 passed`` -- nothing pinned the
# sentence.  The red tests below are exactly that revert.
#
# Same deny/assert shape as the rest of this file, so a legitimate re-wording passes:
#   (A) whichever sentence states the renderer identity must name the shared-library
#       mechanism (one library / same appender / both render modes / RenderPolicy);
#   (B) no sentence may assert that the renderers were separate implementations
#       (independent / separate implementations / two teams / second implementation);
# and ``test_the_independence_mechanism_still_holds_in_code`` re-derives (A)'s premise
# from the source, so the guard cannot outlive the fact it protects.
# --------------------------------------------------------------------------- #

#: The renderer-identity result, as the documents state it: a sentence that pairs a
#: renderer noun with byte-identity.  ``byte-identical`` alone is NOT the anchor -- measured
#: on the 2026-10-23 tree it occurs seven times for unrelated facts (the 64-token grid of
#: byte-identical repeats at :425/:443, the fork marker at :249, the arms at :196, and the
#: CLAIMS rows), and anchoring on it forced the mechanism into sentences that make no
#: renderer claim at all.  The pairing is what matters, because the pairing is the
#: sentence that can carry the wrong inference.
#: ``prompt`` is deliberately NOT a noun here: MANUSCRIPT.md:248 reads "the fork \n prompt is
#: 7,966 characters ... and the material after the marker is byte-identical to the bare
#: summary" -- marker placement, not renderers -- and forcing a mechanism into that sentence
#: is a false positive (measured).  Statements written with "prompt" as the subject are
#: covered by ``RENDERER_IDENTITY``'s explicit ``byte-identical prompts`` shape.
RENDERER_NOUN = r"(?:renderer|renderers|render(?:ing)?|appender)"
#: Only the renderer-as-subject shape is anchored: a renderer noun within 600 characters
#: BEFORE the identity word, in the same sentence, which is how every statement of the
#: result is written (abstract :9 "... tree appender emitted byte-identical prompts ...";
#: SS 2 :100 "compares the pointer renderer against ...: 760/760 cells byte-identical").
#: The mirror shape (identity word, then a renderer noun) was tried and rejected on
#: measurement: it matched MANUSCRIPT.md:248, where the byte-identity is between "the
#: material after the marker" and "the bare summary" -- a claim about marker placement,
#: not about renderers -- and forced a mechanism into an unrelated sentence.
RENDERER_IDENTITY = re.compile(
    RENDERER_NOUN + r"\b[^.]{0,600}?\bbyte-identical"
    # ``graphic`` means "prompt" alone is ambiguous: MANUSCRIPT.md:248 reads "the fork \n
    # prompt is 7,966 characters ... and the material after the marker is byte-identical to
    # the bare summary" -- a claim about marker placement, not renderers -- and "prompt"
    # inside it made the sentence look like a renderer-identity statement.  The shapes that
    # DO state the result are therefore pinned explicitly (both are in the abstract).
    r"|\bbyte-identical prompts?\b",
    re.IGNORECASE,
)

#: The reverted sentence's shape, even when the sentence names no renderer verbatim:
#: a claim of *separate authorship* of the compared renderers.  This is the deny side and
#: needs no renderer noun, because "two teams converged" is the inference, not the fact.
IMPLEMENTATION_NOUN = r"(?:implementations?|implemented|renderers?|appenders?|librar\w+|prompts?)"

#: The mechanism that makes the identity trivial.  Any ONE of these names it: the shared
#: library (``one library``), the shared appender (``same appender`` / ``same renderer``),
#: the shared call (``build_cell``), the two mode flags (``both ... render modes``), or the
#: policy enum itself (``RenderPolicy``).  Kept as alternatives so the prose may be
#: rewritten; what may not change is that the sentence says *why* the bytes matched.
INDEPENDENCE_MECHANISM = re.compile(
    r"\bone librar(?:y|ies)\b|\bsame (?:appender|renderer)\b|\bbuild_cell\b"
    r"|\bboth (?:of )?(?:its )?render\s+modes\b|\bRenderPolicy\b"
    r"|\bone appender(?:\s+honouring\s+two\s+mode\s+flags)?\b"
    r"|\bsame (?:policy|pol icy)(?:\s+enum)?\b",
    re.IGNORECASE,
)

#: What the sentence must NOT claim.  ``independently implemented`` is the exact wording of
#: the reverted abstract; the rest are the shapes a rewrite reaches for when it wants the
#: same inference without the original words.  Plain ``independently`` is deliberately NOT
#: denied: ``MANUSCRIPT.md:32`` says G1 "re-derives the break cost independently", which is
#: true and unrelated -- the denial is on independence of the *implementations*.
INDEPENDENCE_DENIAL = re.compile(
    r"\bindependent(?:ly)?\s+(?:implemented|implementations?|renderers?|appenders?|\w+\s+librar\w+)\b"
    r"|\bindependently\s+\w+\s+" + IMPLEMENTATION_NOUN + r"\b"
    r"|\b(?:two|2)\s+(?:independently\s+implemented\s+)?(?:separate\s+|distinct\s+)?"
    r"(?:implementations?|renderers?|appenders?|librar\w+)\b"
    r"|\bseparately\s+implemented\b|\bsecond\s+implementation\b"
    r"|\b(?:two|both)\s+(?:different\s+)?(?:teams|codebases|code\s+bases)\b"
    r"|\bmutually independent implementation",
    re.IGNORECASE,
)


def _renderer_findings(doc: Document) -> tuple[list[str], list[str]]:
    """(assert-side gaps, deny-side hits) for the renderer-identity sentences."""
    gaps: list[str] = []
    denials: list[str] = []

    for match in RENDERER_IDENTITY.finditer(doc.prose):
        # (A) applies to sentences that MAKE the comparison, not to sentences that cite it.
        # Four measured sites are references and carry no mechanism by design: "whose
        # prompts were byte-identical, as Section 2 shows" (:196 -- the pointer is the
        # citation), the fork marker's "material after the marker is byte-identical to the
        # bare summary" (:248 -- a different claim), and the CLAIMS.md table rows
        # (C01/C37/C38 -- the table states the claim in a cell and the mechanism in §2).
        # A referring sentence is recognised by a section/cell pointer; a stating sentence
        # is not, and must name the mechanism in its own neighbourhood.
        # The pointer follows the figure at :196 ("..., as\nSection 2 shows") and sits in
        # the same sentence, so the look-ahead has to reach the sentence end, not the match.
        context = doc.prose[max(0, match.start() - 160): match.end() + 120]
        # Normalise whitespace first: the pointer at :196 is broken across lines ("as\nSection
        # 2 shows"), so a raw search misses it (measured).
        flat = " ".join(context.split())
        table_row = "|" in doc.prose[
            doc.prose.rfind("\n", 0, match.start()) + 1: match.end()
        ]
        if table_row or re.search(
            r"\bas (?:Section|SS|§) ?\d|\bsee (?:Section|SS|§) ?\d|§ ?\d",
            flat,
            re.IGNORECASE,
        ):
            continue
        sentences = _sentences(doc.prose)
        idx = next(
            (i for i, (start, sent) in enumerate(sentences)
             if start <= match.start() < start + len(sent)),
            None,
        )
        # +-2 fragments, not +-1: ``_sentences`` splits on ``". "``, and the abstract's
        # mechanism sits in the em-dash clause AFTER the figure, i.e. one fragment past a
        # +-1 window (measured: the window came out "Four results ... byte-identical
        # prompts ... in all 760 cells —" with the mechanism just outside).  +-2 reaches
        # the "so every between-arm difference ..." clause that names it, and is still too
        # narrow to borrow a mechanism from an unrelated neighbouring paragraph.
        window = " ".join(s for _, s in sentences[max(0, (idx or 0) - 2): (idx or 0) + 3])
        if not INDEPENDENCE_MECHANISM.search(window):
            gaps.append(
                f"{doc.name}:{line_of(doc.prose, match.start())} [INDEP] a sentence "
                f"states the renderer identity ('byte-identical') without naming the "
                f"mechanism that makes it trivial (one library / same appender / both "
                f"render modes / RenderPolicy / build_cell). Text: "
                f"{excerpt(doc.prose, match.start())}"
            )

    for match in INDEPENDENCE_DENIAL.finditer(doc.prose):
        # The corrective sentence names the refuted reading only to deny it ("a property of
        # one library, not of two independent implementations: both render modes are the
        # RenderPolicy variants ...").  A negation in the clause before the noun is the same
        # exemption ``denial_spans`` gives the G1 corrective -- without it the honest sentence
        # is the only thing this guard would flag.
        # The negation must govern the noun, so it is looked for in the clause that ends at
        # the match: back to the nearest clause boundary (``:`` ``,`` ``--`` or sentence
        # start).  A 90-character head was tried and was WRONG: the reverted abstract reads
        # "the renderer is not the lever: two independently implemented ... renderers", and
        # that unrelated "not" (renderer is not the *lever*) sat 60 characters away and
        # swallowed the denial -- measured as ``test_the_reverted_abstract_is_caught``
        # passing the revert.  The corrective sentence this exemption exists for puts "not"
        # in the same clause ("a property of one library, not of two independent
        # implementations").
        head = doc.prose[max(0, match.start() - 90): match.start()]
        clause = re.split(r"[:;]|\s--\s|,\s", head)[-1]
        if re.search(r"\bnot\b|\brather than\b|\binstead of\b", clause, re.IGNORECASE):
            continue
        denials.append(
            f"{doc.name}:{line_of(doc.prose, match.start())} [INDEP-DENY] the document "
            f"claims the renderers were separate implementations ({match.group(0)!r}); "
            f"they are two RenderPolicy modes of one appender in resextract.context. "
            f"Text: {excerpt(doc.prose, match.start())}"
        )
    return gaps, denials


def test_the_renderer_identity_is_state_and_attributed(manuscript: Document, claims: Document) -> None:
    """The whole GUARD-INDEP guard: attributed where stated, and never re-independised."""
    gaps: list[str] = []
    denials: list[str] = []
    for doc in (manuscript, claims):
        g, d = _renderer_findings(doc)
        gaps += g
        denials += d
    assert not denials, (
        "the context-cache package asserts that the prompt renderers were separately "
        "implemented. They were not: u5_recon.py compares RenderPolicy.POINTER with "
        "RenderPolicy.NAIVE_APPEND inside one library, through one build_cell(...) call. "
        "Keep the superseded wording (if quoted) in double quotes. Findings:\n  - "
        + "\n  - ".join(denials)
    )
    assert not gaps, (
        "a renderer-identity sentence lost the mechanism that explains it; a reader can "
        "infer two converging implementations. Findings:\n  - " + "\n  - ".join(gaps)
    )


def test_the_renderer_identity_is_actually_stated(manuscript: Document) -> None:
    """A guard on a document that stopped stating the result would pass vacuously."""
    assert RENDERER_IDENTITY.search(manuscript.prose), (
        "MANUSCRIPT.md no longer states the 760/760 byte-identical renderer result; the "
        "guard would be vacuous"
    )
    assert "one library" in manuscript.prose, (
        "MANUSCRIPT.md no longer states the 'one library, not two independent "
        "implementations' reading of the 760/760 result"
    )


def test_the_independence_mechanism_still_holds_in_code() -> None:
    """The guard's premise is re-derived from source, not assumed.

    If someone ever *does* add a genuinely independent appender and re-runs the comparison
    against it, the manuscript may say 'independent' again -- and this test (not the prose
    guard) is where that has to be noticed and re-argued.
    """
    cells = ROOT / "experiments" / "context-cache" / "cells" / "U5" / "u5_cells.py"
    source = cells.read_text(encoding="utf-8")
    assert re.search(r"from resextract\.context import \(", source), (
        "U5 cells no longer import from resextract.context; the 'one library' reading may "
        "no longer be the right one -- re-argue it before relaxing this guard"
    )
    imported = source[source.find("from resextract.context import ("):]
    imported = imported[: imported.find(")")]
    assert "RenderPolicy" in imported, (
        "u5_cells.py no longer imports RenderPolicy; the two compared renderers are no "
        "longer modes of one library"
    )
    recon = ROOT / "experiments" / "context-cache" / "cells" / "CX-V2" / "u5_recon.py"
    text = recon.read_text(encoding="utf-8")
    assert "u5.RenderPolicy.POINTER" in text and "u5.RenderPolicy.NAIVE_APPEND" in text, (
        "u5_recon.py no longer compares RenderPolicy.POINTER against "
        "RenderPolicy.NAIVE_APPEND; the 760/760 result is no longer the same measurement"
    )
    pointe = text.count("u5.build_cell(")
    assert pointe >= 2, (
        "u5_recon.py no longer reaches both render modes through build_cell(...); the "
        "'one appender honouring two mode flags' reading has to be re-checked"
    )


def test_the_reverted_abstract_is_caught() -> None:
    """RED, as a unit: the exact sentence FIX-MAN2 repaired must fail this guard."""
    reverted = (
        "First, the renderer is not the lever: two independently implemented prompt "
        "renderers emitted byte-identical prompts in all 760 cells of the compaction "
        "experiment."
    )
    doc = Document(path=MANUSCRIPT, raw=reverted, prose=assertion_text(reverted))
    gaps, denials = _renderer_findings(doc)
    assert denials, "the reverted abstract's 'independently implemented' claim was not caught"
    assert gaps, "the reverted abstract states byte-identical with no mechanism"


def test_a_quoted_supersession_is_exempt() -> None:
    """The docs' marker still applies: a quoted old phrasing is history, not a claim."""
    quoted = 'The card read "two independently implemented prompt renderers" until FIX-MAN2.'
    doc = Document(path=MANUSCRIPT, raw=quoted, prose=assertion_text(quoted))
    gaps, denials = _renderer_findings(doc)
    assert not denials and not gaps, f"a quotation was treated as a claim: {denials + gaps}"


def test_a_legitimate_rewording_passes() -> None:
    """Re-wording that keeps the mechanism must not fight the guard."""
    good = (
        "the tree appender emitted byte-identical prompts under both of its render modes "
        "in all 760 cells, because both modes are RenderPolicy variants of resextract."
        "context reached through one build_cell call."
    )
    doc = Document(path=MANUSCRIPT, raw=good, prose=assertion_text(good))
    gaps, denials = _renderer_findings(doc)
    assert not denials and not gaps, f"a legitimate rewording was rejected: {gaps + denials}"


def test_the_independence_allowlist_is_not_vacuous() -> None:
    """The unrelated 're-derives ... independently' sentence must stay legal."""
    fine = "G1 re-derives the break cost independently (per-break E/F = 1.038)."
    doc = Document(path=MANUSCRIPT, raw=fine, prose=assertion_text(fine))
    _, denials = _renderer_findings(doc)
    assert not denials, f"the allowlist denied unrelated independence: {denials}"


# --------------------------------------------------------------------------- #
# X-CITE2: the two late cells must keep their attribution in the paper.
#
# The guard above protects one causal reading of the 1.700x.  These two findings
# were measured after that guard was written, and the failure mode is the same:
# a number can survive in a table while the sentence that says WHAT IT MEASURED
# is deleted.  Each test therefore anchors the figure together with the cell id,
# the mechanism, and the numeric conditions in one window, and separately pins
# the one-command provenance in CLAIMS.md.  Removing either prose paragraph, or
# its C53/C54 row, makes the corresponding test fail.
#
# Tightened after V-PAPER3 (check 5, ``unverified[0]``): the window alone did NOT
# make the G5 half bite.  The required token ``"G5"`` was satisfied by the string
# ``pre-G5`` in the trailing supersession note, so deleting ``cell G5`` from the
# fan-out sentence left ``11 passed`` on both of the verifier's reverts while the
# docstring claimed the cell was pinned.  The cell and the measurement condition
# are now required on the sentence that carries 6.744, and every failure message
# names the specific token(s) that are missing.
# --------------------------------------------------------------------------- #

G5_FIGURE = re.compile(r"6\.744")
M4_FIGURE = re.compile(r"0\.1592")

#: The two tokens anchored on the *sentence that carries 6.744*, not on a window around it.
#: ``"cell G5"`` is the literal attribution the manuscript uses (``MANUSCRIPT.md:119``:
#: ``Fan-out (cell G5, race-free; 8 fan-outs x 8 branches, 192 rows).``); the bare ``"G5"``
#: subsumes it and was satisfied by ``pre-G5`` in the supersession note, which is a
#: different assertion.  ``G5_CONDITION`` is the figure's measurement condition, taken
#: verbatim from the manuscript -- ``8 fan-outs x 8 branches`` (ASCII lower-case ``x``, no
#: multiplication sign) -- so a condition rewrite fails here and must update this tuple.
G5_SENTENCE_REQUIRED = ("cell G5", "8 fan-outs x 8 branches")

#: The figure-carrying sentence itself, anchored where the paper states the result -- NOT
#: "any sentence that mentions 6.744".  Two reasons, both measured on the 2026-10-23 tree:
#:
#:  * The figure is stated in eight places (abstract at ``MANUSCRIPT.md:15``, SS 3 at
#:    ``:94``/``:126``/``:132``, the arm table, SS 3's tail, SS 11's limitation at ``:443``).
#:    A "some sentence satisfies it" check is satisfied by whichever of those survives, so
#:    deleting the cell from the SS 3 result sentence left the abstract's copy standing and
#:    the guard green -- measured: ``11 passed`` on exactly the revert this test exists for.
#:  * A window is a neighbourhood and reaches the supersession note (``supersedes the pre-G5
#:    band 3.31 measured / 5.39 projected``), where a bare ``"G5"`` stands in for the cell
#:    (V-PAPER3 check 5, ``unverified[0]``).
#:
#: So: the sentence must state 6.744, live inside ``## 3.``, and live in the paragraph whose
#: bold lead-in names the live fan-out figure.  Rewriting that paragraph is expected; the
#: requirement is that the rewritten sentence keeps the cell and the condition.
_SENTENCE_BREAK = re.compile(r"(?<=\.)\s+")
G5_ANCHOR_SECTION = "## 3."
G5_ANCHOR_PARAGRAPH = "The live fan-out figure"


def _sentences(text: str) -> list[tuple[int, str]]:
    """``(offset, sentence)`` pairs; a decimal point is never a sentence boundary.

    The split is on ``". "`` only, so ``6.744 [4.045, 9.443]`` stays inside its sentence
    while the supersession note that follows the fan-out paragraph starts a new one --
    which is the whole point: it cannot count as attribution.
    """
    out: list[tuple[int, str]] = []
    offset = 0
    for chunk in _SENTENCE_BREAK.split(text):
        out.append((offset, chunk))
        offset += len(chunk)
        # The offsets must be exact: the whitespace the split consumed belongs to the
        # *following* chunk, not to this one.  (Before this loop advanced past the
        # whitespace only -- measured 2026-10-23 -- every offset after the first " ". "
        # was short by the run length, so ``start <= offset < start+len`` selected the
        # previous fragment and the neighbourhood was shifted by one.  The shipped X-CITE2
        # assertions compare substrings, so they never depended on it; the renderer guard
        # does, because it locates the figure's own sentence.)
        while offset < len(text) and text[offset] in " \t\r\n":
            offset += 1
    return out


def _paragraphs(text: str) -> list[tuple[int, str]]:
    """``(offset, paragraph)`` pairs, split on blank lines, offsets preserved."""
    out: list[tuple[int, str]] = []
    offset = 0
    for chunk in re.split(r"(?:\r?\n[ \t]*){2,}", text):
        out.append((offset, chunk))
        offset += len(chunk)
        while offset < len(text) and text[offset] in "\r\n":
            offset += 1
    return out


def _figure_windows(text: str, figure: re.Pattern[str], before: int, after: int):
    for match in figure.finditer(text):
        yield text[max(0, match.start() - before): min(len(text), match.end() + after)]


def test_g5_fanout_attribution_is_present(manuscript: Document, claims: Document) -> None:
    """G5's 6.744 B/A ratio must travel with its cell, layout and mechanism."""
    # (1) the SS 3 result sentence names the cell and the measurement condition.
    #     Anchored on ONE sentence -- the one in the "live fan-out figure" paragraph of
    #     SS 3 -- because "any sentence mentioning 6.744" is satisfied by the abstract's
    #     copy of the figure, which is how the first attempt at this tightening stayed
    #     green on the exact revert it exists for.  Failure names every missing token.
    prose = manuscript.prose
    section = prose.find(G5_ANCHOR_SECTION)
    section_end = prose.find("\n## ", section + len(G5_ANCHOR_SECTION)) if section >= 0 else -1
    assert section >= 0 and section_end > section, (
        f"MANUSCRIPT.md no longer has the '{G5_ANCHOR_SECTION}' section that states the G5 "
        f"fan-out result; the guard has no anchor for the cell attribution"
    )
    block = prose[section:section_end]
    paragraphs = [
        (section + start, para) for start, para in _paragraphs(block)
        if G5_ANCHOR_PARAGRAPH in para
    ]
    assert paragraphs, (
        f"the '{G5_ANCHOR_SECTION}' section no longer has a paragraph whose lead-in names "
        f"'{G5_ANCHOR_PARAGRAPH}'; the G5 result paragraph has been renamed or deleted"
    )
    para_start, para = paragraphs[0]
    figure_sentences = [
        (para_start + start, sentence)
        for start, sentence in _sentences(para)
        if G5_FIGURE.search(sentence)
    ]
    assert figure_sentences, (
        f"the '{G5_ANCHOR_PARAGRAPH}' paragraph of {G5_ANCHOR_SECTION} no longer states "
        f"the G5 figure 6.744; the paragraph and its figure have come apart. Paragraph: "
        + " ".join(para.split())[:400]
    )
    missing_by_sentence = []
    for start, sentence in figure_sentences:
        missing = tuple(t for t in G5_SENTENCE_REQUIRED if t not in sentence)
        if not missing:
            break
        missing_by_sentence.append((start, sentence, missing))
    else:
        missing = min((m for _, _, m in missing_by_sentence), key=len)
        raise AssertionError(
            "the sentence in MANUSCRIPT.md that states the G5 figure 6.744 no longer "
            "carries the required token(s) "
            + ", ".join(repr(t) for t in missing)
            + ". Requirement: "
            + " AND ".join(repr(t) for t in G5_SENTENCE_REQUIRED)
            + " must all appear in the SAME sentence as 6.744, inside the "
            + f"'{G5_ANCHOR_PARAGRAPH}' paragraph of {G5_ANCHOR_SECTION}. A neighbouring "
            "sentence does not count (the supersession note mentioning 'pre-G5' is a "
            "different assertion from naming the cell), and neither does the abstract's "
            "own statement of the same figure. Sentences carrying 6.744 there:\n  - "
            + "\n  - ".join(
                f"MANUSCRIPT.md:{line_of(manuscript.prose, start)} "
                f"[missing {', '.join(repr(t) for t in m)}]: "
                + " ".join(sentence.split())[:500]
                for start, sentence, m in missing_by_sentence
            )
        )

    # (2) the wider attribution: layout figures, mechanism, replaced band.
    windows = list(_figure_windows(manuscript.prose, G5_FIGURE, 900, 2_200))
    required = ("G5", "102,912", "20,328", "0 of 123,256", "never share a prefix",
                "structurally 0", "3.31", "5.39")
    missing = tuple(t for t in required if not any(t in w for w in windows))
    assert not missing, (
        "the G5 fan-out paragraph no longer carries its attribution (cell G5, A's "
        "123,240/102,912/20,328 split, B's structural zero hit, and the replaced "
        "3.31/5.39 band). Missing token(s) within +/-900/2,200 characters of 6.744: "
        + ", ".join(repr(t) for t in missing)
        + ". Windows seen: "
        + " | ".join(" ".join(w.split())[:240] for w in windows)
    )
    raw = claims.raw
    assert "C53" in raw and "6.744" in raw and "G5-rows" in raw, (
        "CLAIMS.md no longer has the C53 row that maps 6.744 to G5-rows"
    )
    assert "recompute.py C53" in raw, (
        "CLAIMS.md's C53 row no longer names the single recompute invocation"
    )


def test_m4_resident_capacity_attribution_is_present(manuscript: Document, claims: Document) -> None:
    """M4-EVICT's 0.1592 capacity ratio must travel with its pressure and verdict."""
    windows = list(_figure_windows(manuscript.prose, M4_FIGURE, 700, 2_000))
    assert windows, (
        "MANUSCRIPT.md no longer states the M4-EVICT resident-capacity ratio 0.1592; "
        "the measured capacity bound has lost its figure"
    )
    required = ("M4-EVICT", "1.5017", "30-31", "258,035", "266,636",
                "1,620,892", "max_mamba_cache_size 64", "consistent_with_lru",
                "token-pool LRU")
    assert any(all(token in window for token in required) for window in windows), (
        "the M4-EVICT resident-capacity paragraph no longer carries its attribution "
        "(cell M4-EVICT, 1.5017x pressure, 30-31 documents / 258,035-266,636 tokens "
        "of 1,620,892, state-cache binding constraint, consistent_with_lru, token-pool "
        "LRU excluded). Windows seen: "
        + " | ".join(" ".join(w.split())[:240] for w in windows)
    )
    raw = claims.raw
    assert "C54" in raw and "0.1592" in raw and "M4-rows" in raw, (
        "CLAIMS.md no longer has the C54 row that maps 0.1592 to M4-rows"
    )
    assert "recompute.py C54" in raw, (
        "CLAIMS.md's C54 row no longer names the single recompute invocation"
    )
