#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for tools/package/md2tex.py -- the single Markdown->LaTeX converter.

Run either way:

    python3 tests/test_md2tex.py
    python3 -m pytest tests/test_md2tex.py --noconftest -q

--noconftest is required in this workspace: tests/conftest.py:19 imports a
module that is absent, so the wider suite cannot be collected here.

What is covered
---------------
  test_idempotent            two runs of the tool produce byte-identical output
  test_byte_identity         regenerated files == the files shipped on disk
  test_citation_guard        red->green on a deliberately uncited bibliography entry
  test_shipped_artifacts_are_clean   the shipped main.tex itself passes the
                             bidirectional cite/bibitem guard (read from disk)
  test_replay_bibliography_guard     paper #2's eight-entry bibliography:
                             red->green in BOTH directions; the shipped artefact
                             carries 8 \\bibitem, 8 distinct cited keys, 0 uncited,
                             0 unresolved (expected_bib_count=8, expect_zero_bib=False)
  test_no_control_word_absorbs_a_letter
                             regression added by the concurrent converter-fix unit:
                             no generated main.tex may contain a bare TeX control
                             word immediately followed by a letter
  test_ships_author_slot_and_bibliography
                             all three papers ship the SAME byline (exact line,
                             exactly once) and their declared bibliography passes
                             the bidirectional guard.

History (retained, not deleted). These two tests were named
`test_zero_bibliography_guard` and
`test_ships_author_slot_placeholder_and_no_citation_apparatus`. They asserted that
paper #2 (`replay-record-not-decision`) cited nothing -- `bib_source == "none"`,
`expected_bib_count == 0` -- and that its shipped `main.tex` carried no `\\cite`,
no `\\bibitem` and no `thebibliography`. The author reversed that decision: the
paper now ships eight verified references. Those assertions no longer described the
paper, so they were replaced -- at the new size -- by the bidirectional cite/bibitem
invariant they existed to protect. Nothing was disabled: the replacement is strictly
stronger (it also asserts 8/8/0/0 against the registry and the artefact).

Expectations are never typed in as digests. Every expected byte comes from the
file on disk (test_byte_identity, test_shipped_artifacts_are_clean) or from the
tool's own config table (test_citation_guard, test_replay_bibliography_guard), so a
change to a paper shows up as a failure rather than as two literals agreeing with
each other.
"""
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TESTS_DIR)
TOOL = os.environ.get("MD2TEX_TOOL", os.path.join(ROOT, "tools", "package", "md2tex.py"))
# MD2TEX_TOOL exists so the red run below can be reproduced against a kept copy of the pre-fix
# converter (scratch/ufixtex1/md2tex_prefix.py) without reverting the fix on disk.  Default is the
# real tool, so an ordinary run is unaffected.  The override path is 3 levels deep, like
# tools/package/md2tex.py, so the copy computes the same REPO_ROOT.
SCRATCH = os.path.join(ROOT, "scratch", "umdtex1")


def _load_tool():
    spec = importlib.util.spec_from_file_location("md2tex_tool", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


md2tex = _load_tool()
PACKAGES = md2tex.PACKAGES


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def expected_outputs(cfg):
    names = ["main.tex"]
    if cfg["emit_abstract_files"]:
        names += ["ABSTRACT.txt", "ABSTRACT_METADATA.txt"]
    return names


def run_tool(package, outdir, paper_root=None):
    cmd = [sys.executable, TOOL, "--package", package, "--outdir", outdir, "--quiet"]
    if paper_root:
        cmd += ["--paper-root", paper_root]
    return subprocess.run(cmd, capture_output=True, text=True)


def _tmpdir():
    os.makedirs(SCRATCH, exist_ok=True)
    return tempfile.mkdtemp(prefix="t-", dir=SCRATCH)


def test_idempotent():
    """Two independent runs must be byte-identical, for every package."""
    for slug, cfg in PACKAGES.items():
        a, b = _tmpdir(), _tmpdir()
        r1, r2 = run_tool(slug, a), run_tool(slug, b)
        assert r1.returncode == 0, "run 1 failed for %s: %s" % (slug, r1.stderr)
        assert r2.returncode == 0, "run 2 failed for %s: %s" % (slug, r2.stderr)
        for name in expected_outputs(cfg):
            da = sha256(os.path.join(a, name))
            db = sha256(os.path.join(b, name))
            assert da == db, "%s/%s: two runs differ (%s != %s)" % (slug, name, da, db)
            print("  idempotent %-22s %-22s %s" % (slug, name, da))
        shutil.rmtree(a); shutil.rmtree(b)


def test_byte_identity():
    """The regenerated bytes must equal the bytes shipped on disk. The
    expectation is read from the shipped file, never written down here."""
    for slug, cfg in PACKAGES.items():
        shipped_dir = os.path.join(ROOT, cfg["root"], cfg["outdir"])
        out = _tmpdir()
        r = run_tool(slug, out)
        assert r.returncode == 0, "%s failed: %s" % (slug, r.stderr)
        for name in expected_outputs(cfg):
            shipped = os.path.join(shipped_dir, name)
            assert os.path.exists(shipped), "no shipped %s for %s" % (name, slug)
            want, got = sha256(shipped), sha256(os.path.join(out, name))
            print("  %-22s %-22s shipped=%s regenerated=%s %s"
                  % (slug, name, want, got, "MATCH" if want == got else "MISMATCH"))
            assert got == want, "%s/%s: %s != %s" % (slug, name, got, want)
        shutil.rmtree(out)


def test_citation_guard():
    """Red->green, end to end, on paper #3 (whose bibliography is a .bib file).

    RED:   a copy of the paper's REFERENCES.bib gets one extra, genuinely
           uncited entry appended. The tool must exit non-zero and name it as
           uncited -- a bibliography entry nothing cites is exactly the trap
           this project has hit twice.
    GREEN: the same copy with the probe entry removed must exit 0 and reproduce
           the shipped main.tex byte for byte.

    Why this is non-vacuous: the probe entry is well-formed and parses; nothing
    else about the run changes. If the citation guard were deleted, the red run
    would exit 0 and write a main.tex carrying a \\bibitem that no \\cite
    refers to -- so 'returncode != 0' is a real detection of an absent guard,
    not an incidental syntax error. The key is asserted by name in the message.
    """
    slug = "encoder-crossover-190"
    cfg = PACKAGES[slug]
    probe_key = "uncited_probe_2099"
    probe = ("\n@misc{%s,\n  author = {Probe Author},\n  title = {An entry nothing cites},\n"
             "  year = {2099},\n}\n" % probe_key)

    src = os.path.join(ROOT, cfg["root"])
    work = _tmpdir()
    paper = os.path.join(work, "paper")
    shutil.copytree(src, paper, ignore=shutil.ignore_patterns("submission"))
    bib = os.path.join(paper, cfg["bib_file"])
    original_bib = open(bib, encoding="utf-8").read()

    # --- RED ------------------------------------------------------------------
    red_out = os.path.join(work, "out-red")
    with open(bib, "w", encoding="utf-8") as fh:
        fh.write(original_bib + probe)
    red = run_tool(slug, red_out, paper_root=paper)
    msg = red.stdout + red.stderr
    print("  RED  exit=%d  message=%r" % (red.returncode, msg.strip().splitlines()[-1] if msg.strip() else ""))
    assert red.returncode != 0, "guard did not fire on an uncited entry: %r" % msg
    assert probe_key in msg, "failure did not name the uncited key %s: %r" % (probe_key, msg)
    assert "uncited" in msg, "failure was not the citation guard: %r" % msg

    # --- GREEN ----------------------------------------------------------------
    with open(bib, "w", encoding="utf-8") as fh:
        fh.write(original_bib)
    green_out = os.path.join(work, "out-green")
    green = run_tool(slug, green_out, paper_root=paper)
    print("  GREEN exit=%d" % green.returncode)
    assert green.returncode == 0, "guard stayed red after the entry was removed: %s" % green.stderr
    shipped = os.path.join(src, cfg["outdir"], "main.tex")
    got, want = sha256(os.path.join(green_out, "main.tex")), sha256(shipped)
    print("  GREEN main.tex regenerated=%s shipped=%s %s"
          % (got, want, "MATCH" if got == want else "MISMATCH"))
    assert got == want, "green run did not reproduce the shipped bytes"
    shutil.rmtree(work)


def test_shipped_artifacts_are_clean():
    """The guard also has to hold for the artefact already on disk: read each
    shipped main.tex and require every \\bibitem to be cited and every \\cite to
    have a \\bibitem. This checks the shipped paper, not the tool."""
    for slug, cfg in PACKAGES.items():
        shipped = os.path.join(ROOT, cfg["root"], cfg["outdir"], "main.tex")
        doc = open(shipped, encoding="utf-8").read()
        cited, missing, unknown, bibitems = md2tex.guard_citations(doc, _bib_keys(doc, cfg), cfg)
        print("  %-22s bibitems=%d distinct cite keys=%d uncited=%s unknown=%s"
              % (slug, bibitems, len(cited), missing or "none", unknown or "none"))
        assert not missing and not unknown
        if cfg["expected_bib_count"] is not None:
            assert bibitems == cfg["expected_bib_count"], (
                "%s: %d \\bibitem, registry says %d" % (slug, bibitems, cfg["expected_bib_count"]))


def _bib_keys(doc, cfg):
    """Derive the shipped bibliography's keys from the document itself: every
    \\bibitem{...} is a key, in order."""
    import re
    return re.findall(r"\\bibitem\{([^}]*)\}", doc)


def _first_cite_marker(text):
    """The first [[CITE:<key>]] key in the manuscript, or None."""
    m = re.search(r"\[\[CITE:([A-Za-z0-9_\\]+?)\]\]", text)
    return m.group(1) if m else None


def test_replay_bibliography_guard():
    """Red->green on paper #2, whose bibliography now carries eight cited entries.

    Registry assertions come first: `bib_source` is a BibTeX file, the count is 8,
    and `expect_zero_bib` is False. Then BOTH directions of the load-bearing invariant
    are red-proven on a copy of the paper (never on the shipped tree):

      RED-1  a \\cite with no matching \\bibitem -- a `[[CITE:ghost]]` marker appended
             to the manuscript. The tool must exit non-zero, name `ghost`, and report
             it as an unresolved (unknown) cite key.
      RED-2  a \\bibitem that nothing cites -- one existing `[[CITE:<key>]]` marker
             removed from the manuscript. The tool must exit non-zero, name that key,
             and report it as uncited. The .bib is untouched, so the entry count is
             still 8 and the count check cannot be what fired.
      GREEN  the untouched manuscript must exit 0 and reproduce the shipped main.tex
             byte for byte.

    Why this is non-vacuous: in RED-1 the injected marker parses and REFERENCES.bib is
    untouched, so the run fails ONLY because the guard rejects an unresolved \\cite; in
    RED-2 the .bib is untouched and the entry count is unchanged, so the run fails ONLY
    because the guard rejects an uncited entry. Delete the guard and both red runs would
    exit 0 and ship exactly the defect it exists to prevent. The keys are asserted by
    name in the message, and the green run is byte-checked against the shipped artefact.
    """
    slug = "replay-record-not-decision"
    cfg = PACKAGES[slug]
    assert cfg["bib_source"] == "bibtex_file", cfg["bib_source"]
    assert cfg["expect_zero_bib"] is False, cfg["expect_zero_bib"]
    assert cfg["expected_bib_count"] == 8, cfg["expected_bib_count"]

    src = os.path.join(ROOT, cfg["root"])
    work = _tmpdir()
    paper = os.path.join(work, "paper")
    shutil.copytree(src, paper, ignore=shutil.ignore_patterns("submission"))
    md = os.path.join(paper, cfg["md"])
    original = open(md, encoding="utf-8").read()
    cited_key = _first_cite_marker(original)
    assert cited_key, "the manuscript must carry at least one [[CITE:<key>]] marker"

    # --- RED-1: a \cite with no matching \bibitem -----------------------------
    with open(md, "w", encoding="utf-8") as fh:
        fh.write(original + "\nA stray citation marker [[CITE:ghost]] rides here.\n")
    red1 = run_tool(slug, os.path.join(work, "out-red1"), paper_root=paper)
    msg1 = red1.stdout + red1.stderr
    print("  RED-1 exit=%d  last line=%r"
          % (red1.returncode, msg1.strip().splitlines()[-1] if msg1.strip() else ""))
    assert red1.returncode != 0, "guard did not fire on a \\cite with no \\bibitem: %r" % msg1
    assert "ghost" in msg1, "failure did not name the unresolved key: %r" % msg1
    assert ("unknown=['ghost']") in msg1, "failure was not the cite/bibitem guard: %r" % msg1

    # --- RED-2: a \bibitem that nothing cites ---------------------------------
    with open(md, "w", encoding="utf-8") as fh:
        fh.write(original.replace("[[CITE:%s]]" % cited_key, "", 1))
    red2 = run_tool(slug, os.path.join(work, "out-red2"), paper_root=paper)
    msg2 = red2.stdout + red2.stderr
    print("  RED-2 exit=%d  last line=%r"
          % (red2.returncode, msg2.strip().splitlines()[-1] if msg2.strip() else ""))
    assert red2.returncode != 0, "guard did not fire on an uncited entry: %r" % msg2
    assert cited_key in msg2, "failure did not name the uncited key %s: %r" % (cited_key, msg2)
    assert ("uncited=['%s']" % cited_key) in msg2, "failure was not the uncited-entry guard: %r" % msg2

    # --- GREEN ----------------------------------------------------------------
    with open(md, "w", encoding="utf-8") as fh:
        fh.write(original)
    green_out = os.path.join(work, "out-green")
    green = run_tool(slug, green_out, paper_root=paper)
    print("  GREEN exit=%d" % green.returncode)
    assert green.returncode == 0, "guard stayed red after the probes were removed: %s" % green.stderr
    shipped = os.path.join(src, cfg["outdir"], "main.tex")
    got, want = sha256(os.path.join(green_out, "main.tex")), sha256(shipped)
    print("  GREEN main.tex regenerated=%s shipped=%s %s"
          % (got, want, "MATCH" if got == want else "MISMATCH"))
    assert got == want, "green run did not reproduce the shipped bytes"
    shutil.rmtree(work)


AUTHOR_SLOT = "\\author{Aswin Ram Kalugasala Moorthy}"
# The byline is per-package data (PACKAGES[slug]["author_line"]).  The author has decided
# (UPREPRINT2, 2026-10-19) that ALL THREE papers carry the SAME three-line byline: the name,
# the affiliation and the corresponding-author contact paper #3 already carried.  The two
# tokens below are the author-supplied affiliation/contact; each package's registry entry must
# BE the expected three-line byline, so an entry that drops the email (or the affiliation) is
# RED on its own -- proved in the report against a kept copy
# (scratch/upreprint2/md2tex_noemail.py).
AFFILIATION_TOKEN = "Independent researcher"
CONTACT_TOKEN = "aswinram.k.1603@gmail.com"
EXPECTED_AUTHOR_LINE = ("\\author{Aswin Ram Kalugasala Moorthy\\\\ Independent researcher\\\\ "
                        "\\texttt{%s}}" % CONTACT_TOKEN)
BYLINE_PAPERS = ("encoder-crossover-190", "gated-read-batching",
                 "replay-record-not-decision")


def assert_author_slot(slug, shipped):
    """The byline must be EXACTLY the registry's shared three-line byline for `slug`.

    Asserts the literal expected line, not merely that some \\author exists: this FAILS on a
    DIFFERENT name, on a missing byline, on a SECOND \\author line, on a missing affiliation
    and on a missing corresponding-author contact -- for EVERY package (the author has decided
    that #2 and #7 carry the same three lines as #3, so no package is name-only any more).  It
    also pins each registry entry to the shared expected line, so dropping the email or the
    affiliation from ONE PACKAGES entry is RED on its own.
    """
    cfg = PACKAGES[slug]
    expected = cfg["author_line"]
    assert expected == EXPECTED_AUTHOR_LINE, (
        "%s: registry byline is not the shared three-line byline (affiliation+contact "
        "required for every package): %r" % (slug, expected))
    for tok in (AFFILIATION_TOKEN, CONTACT_TOKEN):
        assert tok in expected, "%s: registry byline lacks %r: %r" % (slug, tok, expected)
    doc = open(shipped, encoding="utf-8").read()
    lines = [ln.strip() for ln in doc.splitlines()]
    hits = [ln for ln in lines if ln == expected]
    others = [ln for ln in lines if ln.startswith("\\author") and ln != expected]
    assert len(hits) == 1 and not others, (
        "%s must carry exactly one byline line %r (found %d); other \\author lines: %r"
        % (shipped, expected, len(hits), others))
    for tok in (AFFILIATION_TOKEN, CONTACT_TOKEN):
        n = doc.count(tok)
        assert n == 1, ("%s: %r must appear exactly once, on the byline (found %d)"
                        % (shipped, tok, n))


def assert_no_citation_apparatus(shipped):
    """SUPERSEDED 2026-10-16 -- retained as history; no longer called.

    This asserted that paper #2 cited nothing, so no citation apparatus could appear in
    its shipped main.tex. The author has since added an eight-entry bibliography, so no
    package is zero-citation and this function describes none of them. It is kept (not
    deleted) so the retired guard stays auditable. The live guard is
    `assert_bibliography`, which is strictly stronger.
    """
    doc = open(shipped, encoding="utf-8").read()
    for tok in ("\\cite{", "\\bibitem{", "thebibliography"):
        print("  replay main.tex contains %-18r %s" % (tok, tok in doc))
        assert tok not in doc, "unexpected %r in %s" % (tok, shipped)


def assert_bibliography(shipped, cfg):
    """Every \\cite resolves to a \\bibitem and every entry is cited, at the size the
    registry declares. Read from disk: checks the artefact, not the tool."""
    doc = open(shipped, encoding="utf-8").read()
    keys = _bib_keys(doc, cfg)
    cited, missing, unknown, bibitems = md2tex.guard_citations(doc, keys, cfg)
    expected = cfg["expected_bib_count"]
    print("  %-22s bibitems=%d bibkeys=%d distinct cite keys=%d uncited=%s unresolved=%s"
          % (cfg["slug"], bibitems, len(keys), len(cited), missing or "none",
             unknown or "none"))
    assert bibitems == len(keys), "%s: %d \\bibitem for %d keys" % (cfg["slug"], bibitems, len(keys))
    if expected is not None:
        assert bibitems == expected, "%s: %d \\bibitem, registry says %d" % (cfg["slug"], bibitems, expected)
        assert len(keys) == expected, "%s: %d bib keys, registry says %d" % (cfg["slug"], len(keys), expected)
        assert len(cited) == expected, "%s: %d distinct cite keys, registry says %d" % (cfg["slug"], len(cited), expected)
    assert not missing and not unknown, "%s: uncited=%s unresolved=%s" % (cfg["slug"], missing, unknown)


def test_ships_author_slot_and_bibliography():
    """Author decision applied: ALL THREE papers now carry the same three-line byline.

    The author has decided (UPREPRINT2, 2026-10-19) that papers #2 and #7 carry the same name,
    affiliation and corresponding-author contact as paper #3, so every package's byline is the
    shared three-line block and no package is name-only any more.  The shipped LaTeX must carry
    that exact \\author line exactly once and no other \\author line.  The citation half: every
    paper ships its declared cited bibliography, so this asserts the bidirectional invariant at
    the declared size (8 \\bibitem for #2; 13 for #3 and #7; 0 uncited, 0 unresolved).  Read from
    disk: checks the artefact, not the tool."""
    for slug in BYLINE_PAPERS:
        shipped = os.path.join(ROOT, "papers", slug, "submission", "main.tex")
        assert_author_slot(slug, shipped)
        print("  %s author slot present" % slug)
        assert_bibliography(shipped, PACKAGES[slug])


def _bare_control_word_escapes():
    """Every escape value the converter's OWN tables can emit that is a bare control word
    (a backslash followed by letters and nothing else).  Derived from SPECIALS plus every
    package's unicode map, so this grows with the tables instead of naming today's one instance.

    A value such as ``\\textasciitilde{}`` (already terminated), ``$\\kappa$`` (math) or ``\\`i``
    (a control SYMBOL) cannot absorb a following letter, so only a value that fullmatches a
    control word is in scope.  Derived, not hardcoded: on the current tables this is exactly
    ``['\\\\S']``."""
    import re
    vals = set(md2tex.SPECIALS.values())
    for cfg in PACKAGES.values():
        vals.update(cfg["unicode"].values())
    return sorted(v for v in vals if re.fullmatch(r"\\[A-Za-z]+", v))


def test_no_control_word_absorbs_a_letter():
    """Regression: no generated main.tex may contain a control word immediately followed by a letter.

    TeX keeps reading letters into a control word, so an escape that ends in one absorbs the next
    character.  The section sign mapped to \\S turned "§B3" into "\\SB3" -- a macro that does not
    exist -- and the shipped PDF silently lost the "§B" (measured: four sites, all in
    papers/encoder-crossover-190: lines 62, 335 x2, 339).  The check iterates the converter's own
    escape tables rather than a hardcoded "\\S", so any future bare-control-word mapping is covered.

    RED on the pre-fix converter (scratch/ufixtex1/md2tex_prefix.py): 4 offending sites.
    GREEN on the fixed converter, which terminates the word as \\S{}.
    """
    import re
    macros = _bare_control_word_escapes()
    assert macros, "no bare-control-word escape values derived -- this check would be vacuous"
    print("  bare control-word escape values derived from the tool's tables: %r" % (macros,))
    for slug, cfg in PACKAGES.items():
        out = _tmpdir()
        r = run_tool(slug, out)
        assert r.returncode == 0, "%s failed: %s" % (slug, r.stderr)
        for name in expected_outputs(cfg):
            doc = open(os.path.join(out, name), encoding="utf-8").read()
            hits = []
            for mac in macros:
                for m in re.finditer(re.escape(mac) + r"(?=[A-Za-z])", doc):
                    hits.append((doc[:m.start()].count("\n") + 1, doc[m.start():m.start() + 12]))
            print("  %-22s %-22s %s" % (slug, name, "clean" if not hits else "DEFECT %r" % (hits,)))
            assert not hits, (
                "%s/%s: a control word is immediately followed by a letter, so TeX will look up "
                "the wrong macro and silently drop text: %r" % (slug, name, hits))
        shutil.rmtree(out)


# The author-approved keyword sets (UPREPRINT3, 2026-10-19), pinned LITERALLY and IN ORDER.
# The author supplied these exact words in this exact order for all three papers, so the
# registry value and the shipped main.tex must carry them character for character.  A set
# comparison would be too weak: it cannot see a reorder, and reordering is exactly the edit
# this test exists to catch.
EXPECTED_KEYWORDS = {
    "encoder-crossover-190":
        "text classification benchmark, encoder classifiers, fine-tuned decision model, "
        "sealed evaluation, majority-class control, McNemar exact test, reproducibility, "
        "withheld evaluation harness",
    "gated-read-batching":
        "tool-call gating, batched decisions, read-gate classification, binary gate decisions, "
        "token exposure, low-effort prompting",
    "replay-record-not-decision":
        "replay determinism, LLM decision replication, binding divergence, record versus "
        "decision, option-index encoding, agent trace reproducibility",
}
KEYWORD_PAPERS = tuple(sorted(EXPECTED_KEYWORDS))


def test_keywords_pinned_per_package():
    """Every package's keyword set is pinned EXACTLY, in order, in the registry and the artefact.

    RED on a reordered set or a dropped keyword: the comparison is against the literal
    author-approved string, not a set, so moving `option-index encoding` after
    `record versus decision` fails even though the same words are present.  Also asserts the
    emission site: the keyword line occurs exactly once, after \\maketitle and before
    \\begin{abstract}, which is what places it on page 1 (the Preprints.org first-page
    requirement).  Paper #3 already carried its set; #2 and #7 gained theirs in UPREPRINT3.
    """
    for slug in KEYWORD_PAPERS:
        cfg = PACKAGES[slug]
        expected = EXPECTED_KEYWORDS[slug]
        assert cfg.get("keywords") == expected, (
            "%s: registry keywords are not the author-approved set, in order: %r != %r"
            % (slug, cfg.get("keywords"), expected))
        shipped = os.path.join(ROOT, "papers", slug, "submission", "main.tex")
        doc = open(shipped, encoding="utf-8").read()
        line = "\\noindent\\textbf{Keywords:} " + expected
        hits = [ln for ln in doc.splitlines() if ln.startswith("\\noindent\\textbf{Keywords:}")]
        assert hits == [line], (
            "%s: expected exactly one keyword line %r in %s, found %r"
            % (slug, line, shipped, hits))
        i_mk = doc.index("\\maketitle")
        i_kw = doc.index(line)
        i_abs = doc.index("\\begin{abstract}")
        assert i_mk < i_kw < i_abs, (
            "%s: keyword line is not between \\maketitle and \\begin{abstract} "
            "(%d/%d/%d) -- it would not be on page 1" % (slug, i_mk, i_kw, i_abs))
        print("  %-22s keywords pinned exactly, in order (%d chars), between \\maketitle and "
              "\\begin{abstract}" % (slug, len(expected)))


def main():
    tests = [test_byte_identity, test_idempotent, test_citation_guard,
             test_shipped_artifacts_are_clean,
             test_replay_bibliography_guard,
             test_no_control_word_absorbs_a_letter,
             test_ships_author_slot_and_bibliography,
             test_keywords_pinned_per_package]
    for t in tests:
        print("== %s" % t.__name__)
        t()
    print("\nALL %d TESTS PASSED" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
