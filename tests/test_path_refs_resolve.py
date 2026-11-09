"""Tests for PATH-REFS-RESOLVE — the evidence rules and the substitution guard.

Three claims are load-bearing and each gets a test that fails without the code:
  * a substitution that moves a non-citation byte is REVERTED (red case),
  * a citation with two candidates stays UNDECIDABLE even when one is newer
    (recency is not evidence), and
  * the directory rule still fires when exactly one candidate sits where the prose points.
"""

import os
import sys

import pytest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "experiments", "ptr-engine", "tools")
sys.path.insert(0, TOOLS)

import path_refs as pr          # noqa: E402
import path_refs_resolve as R   # noqa: E402


def _touch(root, rel, text=""):
    full = os.path.join(root, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)
    return full


def _finding(file_rel, line, token):
    return {"file": file_rel, "line": line, "path": token,
            "classification": "wrong_dir", "resolved": "", "reason": "", "text": ""}


def test_red_substitution_that_moves_a_non_citation_byte_is_reverted(tmp_path):
    """The chosen path CONTAINS the cited token: replacing it rewrites bytes that are not
    the citation (`docs/docs/a/b/foo.py`). The guard must refuse and leave the file alone."""
    root = str(tmp_path)
    _touch(root, "docs/a/b/foo.py", "real\n")
    original = "cite docs/a/b/foo.py here\n"          # the longer citation carries the token
    cited_path = _touch(root, "docs/x.md", original)

    rows = [{"token": "a/b/foo.py", "file": "docs/x.md", "line": 1,
             "candidates": ["docs/a/b/foo.py"], "rule": "content",
             "chosen": "docs/a/b/foo.py", "confidence": "content"}]
    edited, skipped, failures = R.apply_rows(root, rows)

    assert edited == []
    assert failures and "normalised diff" in failures[0]["error"]
    with open(cited_path, "r", encoding="utf-8") as fh:
        assert fh.read() == original, "a refused substitution must leave the bytes untouched"


def test_green_substitution_is_pure_token_substitution(tmp_path):
    root = str(tmp_path)
    _touch(root, "docs/new/foo.py", "real\n")
    original = "see `docs/old/foo.py` and nothing else\n"
    cited_path = _touch(root, "docs/x.md", original)
    rows = [{"token": "docs/old/foo.py", "file": "docs/x.md", "line": 1,
             "candidates": ["docs/new/foo.py"], "rule": "content",
             "chosen": "docs/new/foo.py", "confidence": "content"}]
    edited, skipped, failures = R.apply_rows(root, rows)
    assert failures == [] and len(edited) == 1
    with open(cited_path, "r", encoding="utf-8") as fh:
        after = fh.read()
    toks = {"docs/old/foo.py", "docs/new/foo.py"}
    assert R.normalise(after, toks) == R.normalise(original, toks)


def test_newer_candidate_does_not_decide_an_ambiguous_citation(tmp_path):
    """Two candidates, no content or directory evidence, one of them freshly written.
    Recency is a coin flip wearing a timestamp: the citation must stay undecidable."""
    root = str(tmp_path)
    old = _touch(root, "docs/old/foo.py", "alpha\n")
    new = _touch(root, "docs/new/foo.py", "beta\n")
    os.utime(old, (1_000_000, 1_000_000))
    os.utime(new, None)                                # newest possible mtime
    assert os.path.getmtime(new) > os.path.getmtime(old)
    _touch(root, "docs/cite.md", "see docs/x/foo.py\n")

    index = pr.basename_index(root)
    row = R.decide(root, _finding("docs/cite.md", 1, "docs/x/foo.py"), index)

    assert row["confidence"] == "undecidable"
    assert row["chosen"] == ""
    assert len(row["candidates"]) == 2


def test_directory_rule_fires_when_the_prose_names_one_candidate_dir(tmp_path):
    root = str(tmp_path)
    # Different bytes on purpose: two real files, not copies of one (see the copy rule
    # in path_refs). Byte-identical same-basename files are artefacts and are not
    # candidates at all, so this fixture must not accidentally model a copied tree.
    _touch(root, "longrun/run_longrun.py", "def main(): pass\n")
    _touch(root, "tools/run_longrun.py", "def main(): return 1\n")
    _touch(root, "docs/cite.md", "run `longrun/run_longrun.py`\n")

    index = pr.basename_index(root)
    row = R.decide(root, _finding("docs/cite.md", 1, "run_longrun.py"), index)
    assert row["confidence"] == "dir"
    assert row["chosen"] == "longrun/run_longrun.py"


def test_owner_rule_does_not_claim_a_version_suffix(tmp_path):
    """`V0` must not own `release/v0.1/...`: segment match, not substring."""
    root = str(tmp_path)
    _touch(root, "release/v0.1/src/x/journal.py", "x\n")
    _touch(root, "research/journal.py", "y\n")
    _touch(root, "orchestration/units/V0.md", "artefact `journal.py`\n")
    index = pr.basename_index(root)
    row = R.decide(root, _finding("orchestration/units/V0.md", 1,
                                  "state/verify/V0/journal.py"), index)
    assert row["confidence"] == "undecidable", row
