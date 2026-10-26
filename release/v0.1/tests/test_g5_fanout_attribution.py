"""GUARD-G5B -- every statement of the 6.744 fan-out figure carries its G5 provenance.

Background (V-PAPER3, GUARD-G5B card): the attribution guard pinned only the section-3
sentence.  Deleting the `cell G5` provenance from the abstract's 6.744 statement left
the suite green, because the required token `G5` was satisfied by the string `pre-G5`
in the trailing supersession sentence.  FIX-GUARD tightened that one site; this module
closes the class.

Rule: for EVERY occurrence of `6.744` in papers/context-cache/*.md, the site that
states it -- the sentence containing it, or for a markdown-table cell the table row
plus that table's column-header row -- must contain a G5 provenance token that
`pre-G5` CANNOT satisfy.  Sites that cannot be same-sentence attributed without
rewriting prose (this unit may not edit manuscripts) are named exemptions with
written reasons; an exemption that no longer matches a live occurrence fails the
suite, so the list cannot rot silently.
"""

import re
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1] / "papers" / "context-cache"
FIGURE_RE = re.compile(r"6\.744")

# Anchored so `pre-G5` can never satisfy it: the negative lookbehind rejects the
# hyphenated supersession form, while the word boundaries still match every real
# reference form in the package: "cell G5", "G5's", "(G5,", "G5 fan-out",
# "B/A (live, G5)".
PROVENANCE_RE = re.compile(r"(?<!pre-)\bG5\b")

# (filename, anchor text inside the site region, reason).  An exemption is live only
# while an unattributed occurrence's region contains the anchor; once the prose is
# fixed the stale exemption FAILS the suite and must be deleted.
EXEMPT = [
    (
        "MANUSCRIPT.md",
        "B/A = **6.744** [4.045, 9.443]",
        "section-3 live-figure sentence: the bold lead-in sentence immediately before it "
        "in the same paragraph names 'cell G5, race-free; 8 fan-outs x 8 branches, 192 "
        "rows, C53', and both are pinned together by tests/test_paper_attribution_guard."
        "py::test_g5_fanout_attribution_is_present (FIX-GUARD), which this unit does not "
        "weaken.",
    ),
    (
        "MANUSCRIPT.md",
        "only 1.5x below the 6.744",
        "descriptive comparison inside the U4b floor-retraction paragraph: the sentence "
        "names the G5 condition ('an 8x8 race-free measurement') and the next sentence "
        "names the cell ('6.744 ... from cell G5').  Prose is frozen for this card.",
    ),
    (
        "MANUSCRIPT.md",
        "6.744 is 1.25x above the 5.39",
        "the pre-G5 supersession statement itself: it contrasts the pre-G5 band against "
        "the post-G5 figure, and the cell is named two sentences earlier in the same "
        "paragraph ('6.744 ... from cell G5').  Prose is frozen for this card.",
    ),
    (
        "GAPS.md",
        "replacing the 3.31-5.39 band",
        "inside the '## G5. Fan-out ratio -- STATUS: CLOSED by G5 (C53)' section of "
        "GAPS.md, between two sentences that both state 'cell G5' for the same figure.  "
        "Prose is frozen for this card.",
    ),
]


def _is_real_period(text, i):
    """A '.' that ends a sentence, not one inside a number such as 4.045."""
    before = text[i - 1] if i else ""
    after = text[i + 1] if i + 1 < len(text) else ""
    return not (before.isdigit() and after.isdigit())


def _line_bounds(text, pos):
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return start, (len(text) if end == -1 else end)


def _table_header_line(text, line_start):
    """Column-header line of the markdown table containing line_start, else None.

    Walks up through every contiguous `|`-prefixed line (a data row's immediate
    predecessor is another data row, not the separator), locates the separator,
    and returns the line directly above it.
    """
    above = []
    end = line_start - 1  # newline that terminates the previous line
    while end > 0:
        start = text.rfind("\n", 0, end) + 1
        above.append(text[start:end])
        end = start - 1
    for i, ln in enumerate(above):
        stripped = ln.strip()
        if (
            stripped.startswith("|")
            and "-" in stripped
            and re.fullmatch(r"[\s:|-]*", stripped.strip("|"))
        ):
            if i + 1 < len(above):
                header = above[i + 1].strip()
                return header if header.startswith("|") else None
            return None
    return None


def site_region(text, match):
    """The region that must carry provenance for this occurrence."""
    line_start, line_end = _line_bounds(text, match.start())
    line = text[line_start:line_end]
    if line.lstrip().startswith("|"):
        header = _table_header_line(text, line_start)
        region = f"{header or ''}\n{line}"
    else:
        s = match.start()
        while True:
            s = text.rfind(".", 0, s)
            if s == -1 or _is_real_period(text, s):
                break
        start = 0 if s == -1 else s + 1
        e = match.end() - 1
        while True:
            e = text.find(".", e + 1)
            if e == -1 or _is_real_period(text, e):
                break
        end = len(text) if e == -1 else e + 1
        region = text[start:end]
    return " ".join(region.split())


def _occurrences():
    out = []
    for path in sorted(PKG_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for m in FIGURE_RE.finditer(text):
            lineno = text.count("\n", 0, m.start()) + 1
            out.append((path, text, m, lineno))
    return out


def test_provenance_token_cannot_be_satisfied_by_pre_g5():
    for form in (
        "cell G5",
        "G5's race-free 6.744",
        "(G5, 8 fan-outs x 8 branches",
        "G5 fan-out (race-free)",
        "B/A (live, G5)",
    ):
        assert PROVENANCE_RE.search(form), f"token must match {form!r}"
    for trap in ("pre-G5", "supersedes the pre-G5 band 3.31 measured / 5.39 projected"):
        assert not PROVENANCE_RE.search(trap), f"pre-G5 must NOT satisfy the guard: {trap!r}"


def test_every_6744_site_names_cell_g5():
    offenders = []
    for path, text, m, lineno in _occurrences():
        region = site_region(text, m)
        if PROVENANCE_RE.search(region):
            continue
        if any(f == path.name and a in region for f, a, _ in EXEMPT):
            continue
        offenders.append(
            f"{path.name}:{lineno}: 6.744 stated with no G5 provenance in the same "
            f"site -> {region[:180]}"
        )
    assert not offenders, "unattributed 6.744 sites:\n" + "\n".join(offenders)


def test_exempt_sites_are_live():
    """An exemption that no longer matches an unattributed site must be deleted."""
    unattributed = []
    for path, text, m, _lineno in _occurrences():
        region = site_region(text, m)
        if not PROVENANCE_RE.search(region):
            unattributed.append((path.name, region))
    stale = [
        f"{fname}: exemption anchor {anchor!r} matches no unattributed site -- delete it"
        for fname, anchor, _reason in EXEMPT
        if not any(f == fname and anchor in region for f, region in unattributed)
    ]
    assert not stale, "\n".join(stale)


def test_exemptions_all_carry_written_reasons():
    for fname, anchor, reason in EXEMPT:
        assert reason.strip(), f"exemption {fname}:{anchor!r} has no reason"
        assert len(reason) > 40, f"exemption {fname}:{anchor!r} reason too thin"
