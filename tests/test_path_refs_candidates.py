"""Tests for the CANDIDATE-SET rule in path_refs: a copy is not a candidate.

Three claims are load-bearing, each with a test that fails without the rule:
  * a citation whose every same-basename hit is a byte-identical COPY (a tree snapshot)
    has no addressable alternate: it is honestly `missing`, not `wrong_dir`;
  * a genuine duplicate -- two real files with the same basename and DIFFERENT bytes --
    stays `wrong_dir`, and so does a mixed set (copies plus one distinct file), so real
    ambiguity never disappears;
  * a citation that resolves today is untouched, because the rule never runs on an `ok`.
"""

import os
import sys

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


def _finding(root, doc_rel, token):
    for f in pr.scan(root):
        if f["file"] == doc_rel and f["path"] == token:
            return f
    raise AssertionError("%s does not cite %s" % (doc_rel, token))


def test_artefact_copies_are_not_candidates_and_the_citation_is_missing(tmp_path):
    """Two byte-identical copies under foreign roots: neither is where the prose points."""
    root = str(tmp_path)
    _touch(root, "docs/cite.md", "see `docs/plan/OUT.md` for the plan\n")
    _touch(root, "mirrorA/docs/plan/OUT.md", "same bytes\n")
    _touch(root, "mirrorB/docs/plan/OUT.md", "same bytes\n")

    f = _finding(root, "docs/cite.md", "docs/plan/OUT.md")
    assert f["classification"] == "missing", f
    assert f["resolved"] == ""
    assert R.candidates_for(root, "docs/plan/OUT.md",
                            pr.basename_index(root)) == []


def test_genuine_duplicate_stays_ambiguous(tmp_path):
    """Two real files, same basename, different bytes: the ambiguity is REAL, keep it."""
    root = str(tmp_path)
    _touch(root, "docs/cite.md", "see `tests/run/check.py` for the harness\n")
    _touch(root, "src/a/check.py", "alpha\n")
    _touch(root, "src/b/check.py", "beta\n")

    f = _finding(root, "docs/cite.md", "tests/run/check.py")
    assert f["classification"] == "wrong_dir", f
    assert len(R.candidates_for(root, "tests/run/check.py",
                                pr.basename_index(root))) == 2

    # Mixed set: identical copies PLUS one distinct file. Still ambiguous -- one real
    # alternate is enough, so the copies must not drag the citation to `missing`.
    _touch(root, "docs/cite2.md", "see `papers/note.json` for the note\n")
    _touch(root, "mirrorA/papers/note.json", "copy\n")
    _touch(root, "mirrorB/papers/note.json", "copy\n")
    _touch(root, "papers/rec/note.json", "the real one\n")
    g = _finding(root, "docs/cite2.md", "papers/note.json")
    assert g["classification"] == "wrong_dir", g


def test_resolving_citation_stays_ok(tmp_path):
    """Regression: a citation the tree satisfies is never re-classified by the rule."""
    root = str(tmp_path)
    _touch(root, "docs/real.md", "fine\n")
    _touch(root, "mirrorA/docs/real.md", "other bytes\n")
    _touch(root, "docs/cite.md", "see `docs/real.md`\n")

    f = _finding(root, "docs/cite.md", "docs/real.md")
    assert f["classification"] == "ok", f
    assert f["resolved"] == "docs/real.md"
