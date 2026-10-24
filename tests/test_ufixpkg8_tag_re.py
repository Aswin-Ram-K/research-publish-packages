"""UFIXPKG8 - regression test for the redaction tag grammar (red->green).

The build script emits the positive-vocabulary gate (`gate.sh`) from a heredoc
(`orchestration/units/UBUILD1.build.sh:818`), and that gate compiles the tag grammar

    TAG_RE = re.compile("^(?:K|F|S|C|R|D|N)[" + DIGITS + "][" + DIGITS + "]$"
                        "|^TAG_[" + DIGITS + "][" + DIGITS + "]$")

Before UFIXPKG8 the character class was `K|F|S|C|R|D|N`: the neutral `P` family this
project actually mints and ships (`P01`-`P05`, `orchestration/units/UDTAG1.md:22-23`)
was rejected, so the validator could not validate the material it exists for.

These tests read the LIVE build script off disk and execute its own `TAG_RE` statement,
so they fail (red) on the old grammar and pass (green) on the fixed one.  The gate exists
in two on-disk copies: the build script is the source of truth (it writes `gate.sh` from
the heredoc); the checked-in emitted copy is `tools/package/gate.sh:110`.
"""
import re
import string
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "orchestration" / "units" / "UBUILD1.build.sh"
EMITTED_GATE = ROOT / "tools" / "package" / "gate.sh"


def load_tag_re(path):
    """Execute the file's own TAG_RE statement and return the compiled pattern."""
    text = path.read_text(encoding="utf-8")
    marker = "TAG_RE = re.compile"
    start = text.index(marker)
    depth = 0
    stmt = None
    for k in range(start + len(marker), len(text)):
        ch = text[k]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                stmt = text[start:k + 1]
                break
    assert stmt is not None, "unterminated TAG_RE statement in %s" % path
    namespace = {"re": re, "string": string, "DIGITS": string.digits}
    exec(stmt, namespace)  # noqa: S102 - statement read from this repository
    return namespace["TAG_RE"]


@pytest.fixture(scope="module", params=[BUILD_SCRIPT, EMITTED_GATE],
                ids=["build-script", "emitted-gate"])
def tag_re(request):
    """UFIXPKG9: read the grammar out of BOTH live on-disk copies.

    They had diverged -- the build script's heredoc carried ``N|P`` while the
    checked-in emitted ``tools/package/gate.sh`` still carried ``K|F|S|C|R|D|N``
    and rejected ``P01``-``P05``.  Parametrising the fixture runs every case
    against each copy, so the two can no longer disagree silently.
    """
    return load_tag_re(request.param)


P_FAMILY = ["P01", "P02", "P03", "P04", "P05"]
ALREADY_ACCEPTED = ["K01", "F56", "S02", "C01", "R10", "D43", "N01", "TAG_01"]
# Must stay unrecognised: arbitrary words, wrong arity, lowercase, hyphenated ids.
NEGATIVES = [
    "hello", "word", "P", "P1", "P001", "p01", "P01x", "P0a",
    "X01", "Q01", "D-067", "TAG_1", "TAG_100", "",
    "the withheld rationale note",
]


@pytest.mark.parametrize("token", P_FAMILY)
def test_live_gate_accepts_the_minted_p_family(tag_re, token):
    assert tag_re.match(token) is not None, (
        "%r is a NEUTRAL-TAG/v1 token this project mints, but the live gate "
        "grammar %r rejects it" % (token, tag_re.pattern)
    )


@pytest.mark.parametrize("token", ALREADY_ACCEPTED)
def test_live_gate_still_accepts_every_other_accepted_family(tag_re, token):
    assert tag_re.match(token) is not None


@pytest.mark.parametrize("token", NEGATIVES)
def test_live_gate_still_rejects_words_and_near_misses(tag_re, token):
    assert tag_re.match(token) is None, (
        "%r must not be treated as a redaction tag" % (token,)
    )
