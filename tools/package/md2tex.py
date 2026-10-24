#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2tex.py -- ONE Markdown->LaTeX converter for every paper package here.

Why this file exists
--------------------
Paper #3 (papers/encoder-crossover-190) and paper #7 (papers/gated-read-batching)
each had a private copy of this converter:

    scratch/uprep1/md2tex.py    368 lines, sha256 e4594f1727cf40e1de7388a2b892b16acc0e3fa4b134c9656e82f79afa107f50
    scratch/uprep7/md2tex.py    429 lines, sha256 ccad301dfd1b6dc1ac320dfdb34267ec03e5ab77c70b70a9653051ac404ceb2e

A third paper (papers/replay-record-not-decision) needs a third. This is the
single converter: the per-paper *values* live in ONE table, PACKAGES, selected
with `--package <slug>`. Three copies of the logic become one; the two copies of
the values become one table.

Byte-identity (load-bearing)
----------------------------
For both existing packages this tool reproduces the shipped main.tex byte for
byte. Digests and cmp evidence: tools/package/README.md. tests/test_md2tex.py
re-checks both against the files on disk, and it never restates a digest as a
literal -- it derives the expectation from the file on disk.

The two papers genuinely diverged, and the config carries the divergence rather
than paper-specific branches in the logic:
  * bibliography source -- paper #3 parses REFERENCES.bib; paper #7 parses the
    numbered reference list inside its own MANUSCRIPT.md `## References` section;
  * paper #7 has a submission-hygiene stage (unit-id removal, markdown-link
    flattening, footnote-asterisk sentinel) that paper #3 does not run. This is
    NOT made generic: paper #3's manuscript contains a live unit id (UEXP2,
    measured), so applying S2 to it would change its output bytes;
  * paper #7 emits ABSTRACT.txt and ABSTRACT_METADATA.txt; paper #3 emits
    main.tex only;
  * the two unicode maps differ by exactly two entries (i-grave and
    element-of), the anchor tables differ (13 vs 14), and the guard sets differ.

Config: why not a TOML under orchestration/packages/
----------------------------------------------------
The unit card asked for a small TOML under orchestration/packages/, matching the
existing per-package manifests. That path is OUTSIDE this unit's declared write
paths, and orchestration/packages/<slug>.toml are UBUILD1 *build* manifests
(schema = 1) consumed by tools/package/check_manifest.py -- putting md2tex keys
there would be both an undeclared write and a change to another tool's schema.
So the config is the PACKAGES registry below: pure data, keyed by slug, the
single source of truth for every per-paper value. Migration path: if a unit with
the orchestration/packages/** write path is opened, lift PACKAGES verbatim into
orchestration/packages/<slug>/md2tex.toml and load it with tomllib -- no logic
changes, because every value is already data.

Writes nothing outside --outdir (default <paper>/<outdir>).
"""
import argparse
import collections
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- config literals, extracted verbatim from the two originals by
#     scratch/umdtex1/literals.py (AST), so nothing here was retyped. ---
U_ENC = {'§': '\\S', '±': '$\\pm$', '²': '$^{2}$', '×': '$\\times$', '–': '--', '—': '---', '‘': '`', '’': "'", '“': '``', '”': "''", '…': '\\ldots{}', '₁': '1', '₂': '2', '₃': '3', '→': '$\\to$', '↔': '$\\leftrightarrow$', '≈': '$\\approx$', '≤': '$\\le$', '≥': '$\\ge$', '−': '$-$', 'Δ': '$\\Delta$', 'κ': '$\\kappa$', 'ψ': '$\\psi$', 'χ': '$\\chi$', '⚠': '!', '✅': '$\\checkmark$'}
U_GRB = {'§': '\\S', '±': '$\\pm$', '²': '$^{2}$', '×': '$\\times$', 'ì': '\\`i', '–': '--', '—': '---', '‘': '`', '’': "'", '“': '``', '”': "''", '…': '\\ldots{}', '₁': '1', '₂': '2', '₃': '3', '→': '$\\to$', '↔': '$\\leftrightarrow$', '∈': '$\\in$', '≈': '$\\approx$', '≤': '$\\le$', '≥': '$\\ge$', '−': '$-$', 'Δ': '$\\Delta$', 'κ': '$\\kappa$', 'ψ': '$\\psi$', 'χ': '$\\chi$', '⚠': '!', '✅': '$\\checkmark$'}
ANCHORS_ENC = [('arxiv2602_06370', 'arXiv `2602\\.06370`'), ('arxiv2512_12677', 'arXiv `2512\\.12677`'), ('pride2309_03882', 'arXiv `2309\\.03882`'), ('gcd2305_13971', 'arXiv `2305\\.13971`'), ('source_decider_stack_2026', '`docs/DECIDER_STACK_DECISION\\.md` \\u00a711\\.6'), ('simmering2025modernbert', '`simmering2025modernbert`'), ('zaratiana2024gliner', '`zaratiana2024gliner`'), ('zaratiana2025gliner2', '`zaratiana2025gliner2`'), ('stepanov2025gliclass', '`stepanov2025gliclass`'), ('kostina2025llmtextclassification', '`kostina2025llmtextclassification`'), ('li2025smalllanguagemodels', '`li2025smalllanguagemodels`'), ('weller2025seqvsseq', '`weller2025seqvsseq`'), ('benayas2024comparative', '`benayas2024comparative`')]
ANCHORS_GRB = [('ref3,ref6', '\\(Cheng et al\\., 2023; Lin et al\\., 2023\\)'), ('ref11', '\\*\\*Toolformer\\*\\* \\(Schick et al\\., 2023\\)'), ('ref9', '\\*\\*TALM\\*\\* \\(Parisi et al\\., 2022\\)'), ('ref1', '\\*\\*Self-RAG\\*\\* \\(Asai et al\\., 2023\\)'), ('ref7', '\\*\\*Mallen et al\\.\\*\\* \\(2022\\)'), ('ref5', '\\*\\*FLARE\\*\\* \\(Jiang et al\\., 2023\\)'), ('ref4', '\\*\\*Adaptive-RAG\\*\\* \\(Jeong et al\\., 2024\\)'), ('ref8', '\\*\\*RouteLLM\\*\\* \\(Ong et al\\., 2024\\)'), ('ref2', '\\*\\*FrugalGPT\\*\\* \\(Chen et al\\., 2023\\)'), ('ref12', '\\*\\*GuardAgent\\*\\* \\(Xiang et al\\., 2024\\)'), ('ref3', '\\(Cheng, Kasai & Yu, 2023, EMNLP 2023 Industry Track\\)'), ('ref6', '\\*\\*BatchPrompt\\*\\* \\(Lin et al\\., 2023\\)'), ('ref13', '\\*Efficient but Vulnerable\\* \\(Yue & Yao, 2025\\)'), ('ref10', '\\(Rombaut, 2026\\)')]
STAR = '\x00STAR\x00'
ENC_DATE = '\\date{}   % deliberately empty: arXiv advises against \\today; author must set the date'
GRB_DATE = '\\date{}   % deliberately empty: arXiv advises against \\today'
GRB_RENEW = '\\renewcommand{\\refname}{}   % heading already printed by \\section*{References}'
ABS_META = 'We measure a binary file-read gate: a small decision model answers {"relevant": true|false} for a proposed read of file f for task t with stated purpose p, conditioned only on the question, the purpose, the file path, a short header and a structure outline -- never on the file body. On 1,800 (task, file) pairs drawn from a 90-file corpus and 20 tasks, we test whether those per-read decisions can be batched. Batching 16 or 90 decisions into a single request at reasoning_effort=none reduces decision calls from 1,800 to 120 and 20 (15x and 90x) and prompt tokens from 631 K to 270 K and 261 K (2.3x and 2.4x) while F1 moves from 0.218 to 0.227 and 0.211 -- a spread of 0.016, within +/-0.01 of the single-decision baseline. On this task, corpus and decision model, batching binary gate decisions at effort=none did not measurably degrade decision quality. This is a narrower claim than "batching is free": published batch-prompting losses on QA and NLI are large (-4 to -18 points; e.g. BoolQ 90.6% to 72.8%, -17.8, at batch size >= 64 without repair), and the present result is a measured exception on one task shape, not a refutation. The same run yields a negative result about the gate itself. Across five configurations the best F1 is 0.320, and the most precise configuration reaches precision 0.418 at recall 0.233 -- the most precise gate tested silently drops three of every four gold files. Raising reasoning_effort from none to minimal doubles recall (0.175 to 0.367) for roughly 30% more tokens, which is consistent with effort selecting a different classifier rather than a cheaper one. The gate is measurable and purpose-conditioned by design, but on header and structure alone it is not yet an accurate classifier, and we report it as a negative finding rather than hiding it behind the batching result. No formal non-inferiority test was run on the batching delta.'


ABS_REPLAY = (
    "We measure whether replaying a recorded decision trace reproduces the decision it encodes. On a corpus of 190 decision cases answered by four model configurations under four recorded variants (3,040 rows), we measure how often two configurations reason over the same record, at the same variant, and pick a different option. At the reference variant V0 that happens on 476 of 1,140 model-pair-by-case comparisons (41.7544%). The instrument has a real zero: the corpus's own replication arm re-issues the same request and returns an identical decision on 244 of 244 non-decomposable comparisons, across both replication pairs, with zero divergent. Against that control the divergence is a property of the binding, not of noise. The four variants give 41.75%, 47.11%, 40.00% and 43.33%, so the headline is one arm, not a four-variant average. Relabelling the options alone moves 245 of 760 decisions (32.2368%), but that pool hides the shape: one configuration moves 119 of 190 (62.63%) while the other three move 15.8-26.8%. A second record file is not an independent corpus: it covers the same 190 cases and the same two models, and reproduces the same picked_index on 190 of 190 rows per model; its 51.5789% divergence is the same 98 disagreements already counted in the binding table. The stimuli -- the questions and the options -- are withheld: the record files carry indices and latencies, not text. A reader can recompute every arithmetic figure here; the reader cannot check that the cases mean what the labels say they mean. No model was run, re-trained, or re-evaluated for this note."
)


SPECIALS = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
            "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}", "\\": r"\textbackslash{}"}

CODE_RE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
LINK_MARK_RE = re.compile(r"\[\[LINK:(.*?)\|(.*?)\]\]")
FIELD = re.compile(r"(\w+)\s*=\s*", re.S)

# ---------------------------------------------------------------- the one config table
PACKAGES = {
    "encoder-crossover-190": dict(
        slug="encoder-crossover-190",
        root="papers/encoder-crossover-190",
        md="MANUSCRIPT.md",
        outdir="submission",
        unicode=U_ENC,
        cite_anchors=ANCHORS_ENC,
        cite_mark_re=r"\[\[CITE:([A-Za-z0-9_\\]+?)\]\]",
        cite_extract_re=r"\\cite\{([A-Za-z0-9_]+)\}",
        cite_split=None,
        link_markers=False,
        footnote_star=False,
        sanitise_rules=(),
        drop_status_banners=False,
        bib_from_manuscript_references=False,
        bib_source="bibtex_file",
        bib_file="REFERENCES.bib",
        bib_preamble=(),
        date_line=ENC_DATE,
        fail_on_unmapped_nonascii=False,
        fail_on_residual_nonascii=False,
        expected_bib_count=None,
        require_balanced_braces=False,
        residual_markdown_bold=False,
        require_author_slot=True,
        # author_line -- CHANGED 2026-10-17 (UAUTHOR1).  Drafting-time value was the
        # name only, "\\author{Aswin Ram Kalugasala Moorthy}" (UBYLINE3).  Preprints.org
        # requires the first page to carry the author list, the AFFILIATION and a
        # CORRESPONDING-AUTHOR CONTACT, and the author has now supplied both for THIS
        # package: affiliation "Independent researcher", contact
        # "aswinram.k.1603@gmail.com" (deliberately public -- it is the corresponding
        # author's contact address, not a secret).  The value below is ONE \\author line
        # with `\\\\` row breaks, so guard()'s exactly-one-slot check still pins the whole
        # block character for character and still fails on a different name OR a
        # different affiliation.  Papers #2 and #7 are untouched: their registry entries
        # keep the name-only line (no affiliation, no contact), and the test asserts the
        # affiliation/contact appear in THIS package's main.tex only.
        author_line="\\author{Aswin Ram Kalugasala Moorthy\\\\ Independent researcher\\\\ \\texttt{aswinram.k.1603@gmail.com}}",
        expect_zero_bib=False,
        forbidden=(("stale string", "Draft status"),
                   ("stale string", "submission-candidate"),
                   ("stale string", "AFFILIATION TO BE SUPPLIED")),
        emit_abstract_files=False,
        abstract_metadata=None,
        keywords="text classification benchmark, encoder classifiers, fine-tuned decision model, sealed evaluation, majority-class control, McNemar exact test, reproducibility, withheld evaluation harness",
        guard_label="R18 FAILED",
    ),
    "gated-read-batching": dict(
        slug="gated-read-batching",
        root="papers/gated-read-batching",
        md="MANUSCRIPT.md",
        outdir="submission",
        unicode=U_GRB,
        cite_anchors=ANCHORS_GRB,
        cite_mark_re=r"\[\[CITE:([A-Za-z0-9_,]+?)\]\]",
        cite_extract_re=r"\\cite\{([^}]*)\}",
        cite_split=",",
        link_markers=True,
        footnote_star=True,
        sanitise_rules=("unit_ids", "flatten_links", "footnote_star"),
        drop_status_banners=True,
        bib_from_manuscript_references=True,
        bib_source="manuscript_references",
        bib_file=None,
        bib_preamble=(GRB_RENEW,),
        date_line=GRB_DATE,
        fail_on_unmapped_nonascii=True,
        fail_on_residual_nonascii=True,
        expected_bib_count=13,
        require_balanced_braces=True,
        residual_markdown_bold=True,
        require_author_slot=True,
        author_line="\\author{Aswin Ram Kalugasala Moorthy\\\\ Independent researcher\\\\ \\texttt{aswinram.k.1603@gmail.com}}",
        expect_zero_bib=False,
        forbidden=(("internal unit id", r"\bU[A-Z]{2,}[0-9]+[a-z]?\b"),
                   ("scratch dir", r"scratch"),
                   ("draft banner", r"(?i)draft (manuscript|status)"),
                   ("status banner", r"(?m)^\s*Status:"),
                   ("local path", r"(/home/|papers/|/tmp|submission/)")),
        emit_abstract_files=True,
        abstract_metadata=ABS_META,
        # keywords -- ADDED 2026-10-19 (UPREPRINT3).  The author approved this exact set, in this
        # exact order, for paper #7 ("gated-read-batching").  Emitted immediately after
        # \maketitle (see the emission site in convert()) so the keyword line is on page 1 by
        # construction.  The set contains no numeric literal, so it cannot move a measurement.
        keywords="tool-call gating, batched decisions, read-gate classification, binary gate decisions, token exposure, low-effort prompting",
        guard_label="CITE/BIBITEM GUARD FAILED",
    ),
    # ---- third package: a paper with ZERO external citations.  Every value below is
    # derived from papers/replay-record-not-decision/{MANUSCRIPT,AVAILABILITY}.md:
    #   * cite_anchors MUST be empty -- the manuscript contains no [[CITE:]] marker and no
    #     \cite (measured); a non-empty table would inject a \cite with no \bibitem.
    #   * bib_source="none" -- no REFERENCES.bib, no `## References` section, so no
    #     bibliography environment is emitted (an empty thebibliography would BE the
    #     "shipped bibliography nothing cites" defect the guard exists to prevent).
    #   * expected_bib_count=0 + expect_zero_bib=True -- the guard is NOT disabled; it
    #     asserts the output carries no citation apparatus at all (red-proven in tests).
    #   * author_line -- CHANGED 2026-10-16 (UFIXBYLINE2).  Drafting-time value was
    #     None, on MANUSCRIPT.md 7 ("carries no authorship statement by design") and
    #     AVAILABILITY.md ("deliberate and is not an omission to be corrected by a
    #     reader").  The author has since decided solo authorship (name only, no
    #     affiliation) and the other two packages of this route already ship exactly
    #     this placeholder; a paper with no author line cannot be submitted.  The
    #     placeholder below is the same expression as the other two entries and
    #     require_author_slot=True applies the identical exactly-one-slot guard.
    #     No name was invented.
    #   * author_line -- CHANGED 2026-10-16 (UBYLINE3).  The author has now supplied
    #     the name verbatim -- "Aswin Ram Kalugasala Moorthy" -- and the standing
    #     decision is name only, no affiliation.  All THREE packages carry that
    #     identical value, so the registry stays the single source of truth.  The
    #     placeholder wording above is retained as history.
    #   * date_line=GRB_DATE -- no publication date is stated anywhere in the documents.
    "replay-record-not-decision": dict(
        slug="replay-record-not-decision",
        root="papers/replay-record-not-decision",
        md="MANUSCRIPT.md",
        outdir="submission",
        unicode=U_ENC,
        cite_anchors=(),
        cite_mark_re=r"\[\[CITE:([A-Za-z0-9_\\]+?)\]\]",
        cite_extract_re=r"\\cite\{([^}]*)\}",
        cite_split=None,
        link_markers=False,
        footnote_star=False,
        sanitise_rules=(),
        drop_status_banners=False,
        # Targeted prose de-naming (14 rules).  Each string is copied from
        # papers/replay-record-not-decision/MANUSCRIPT.md; the released DATA files
        # (decision-variants.jsonl, l1-head-to-head.jsonl) are deliberately NOT rules --
        # AVAILABILITY.md ships them, so they are public material, not internal records.
        dename_rules=(
            ("`EXP#7-replay-divergence.md:16-17`", "the pre-registration record, \u00a71"),
            ("`EXP#7-replay-divergence.md:48-55`", "the pre-registration record, \u00a73"),
            ("`EXP#7-replay-divergence.md:139-154`", "the pre-registration record, analysis log"),
            ("`EXP#7-replay-divergence.md:148-150`", "the pre-registration record, analysis log"),
            ("`scratch/urever2/verify_divergence.py`", "the analysis script released with this note"),
            ("`strategy/PAPER2_REVERIFICATION.md:149`", "the re-verification record"),
            ("`strategy/PAPER2_REVERIFICATION.md:152`", "the re-verification record"),
            # UPDATED 2026-10-19 (UDENAME2): the replacement for this rule previously read
            # "the withheld stimulus fixture" and this became FALSE once the note began
            # releasing the stimulus fixture with the companion note (MANUSCRIPT.md §6/§7:
            # "since 2026-10-19 that fixture is **not withheld**"), so the shipped sentence
            # read "lived only in the withheld stimulus fixture ... this fixture is not
            # withheld".  The word is dropped, not the rule: the rule still hides the internal
            # source-tree path, and the stale-rule guard at the dename loop still fails if the
            # manuscript stops carrying this literal.  Superseded replacement retained as
            # history: "the withheld stimulus fixture".
            ("the fixture `evals/fixtures/reflex-decisions.ts`", "the stimulus fixture"),
            (" (`evals/fixtures/reflex-decisions.ts`)", ""),
            ("`tools/replay/exp7.ts` exists", "The pre-registration's analysis script exists"),
            ("and the analysis script `tools/replay/exp7.ts`, which was",
             "and the pre-registration's analysis script, which was"),
            ("`exp7.ts`", "that script"),
            ("on the L1 side", "on the second record's side"),
            ("`CLAIMS.md`", "this note's internal claim trace"),
            ("`GAPS.md`", "this note's internal gap log"),
            ("`AVAILABILITY.md`", "this note's internal availability record"),
        ),
        # UPDATED 2026-10-16 (UBIB2): the paper now carries a verified bibliography
        # (papers/replay-record-not-decision/REFS.md + REFERENCES.bib), so bib_source is a
        # BibTeX file and expected_bib_count/expect_zero_bib assert the citation guard instead
        # of asserting the absence of apparatus. Prior zero-bibliography values stay above as history.
        bib_from_manuscript_references=False,
        bib_source="bibtex_file",
        bib_file="REFERENCES.bib",
        bib_preamble=(),
        date_line=GRB_DATE,
        fail_on_unmapped_nonascii=True,
        fail_on_residual_nonascii=True,
        expected_bib_count=8,
        require_balanced_braces=True,
        residual_markdown_bold=True,
        require_author_slot=True,
        author_line="\\author{Aswin Ram Kalugasala Moorthy\\\\ Independent researcher\\\\ \\texttt{aswinram.k.1603@gmail.com}}",
        forbidden=(("internal record pointer", r"EXP#"),
                   ("scratch dir", r"scratch/"),
                   ("internal working record", r"\b(?:CLAIMS|GAPS|AVAILABILITY|PAPER2_REVERIFICATION)\.md\b"),
                   ("source-tree path", r"(?<![\w/])(?:evals|tools|strategy|docs)/"),
                   ("local path", r"(/home/|papers/|/tmp|submission/)"),
                   ("internal unit id", r"\bU[A-Z]{2,}[0-9]+[a-z]?\b"),
                   ("draft banner", r"(?i)draft (manuscript|status)"),
                   ("status banner", r"(?m)^\s*Status:")),
        emit_abstract_files=True,
        abstract_metadata=ABS_REPLAY,
        expect_zero_bib=False,
        # keywords -- ADDED 2026-10-19 (UPREPRINT3).  The author approved this exact set, in this
        # exact order, for paper #2 ("replay-record-not-decision").  Emitted immediately after
        # \maketitle (see the emission site in convert()) so the keyword line is on page 1 by
        # construction.  The set contains no numeric literal, so it cannot move a measurement.
        keywords="replay determinism, LLM decision replication, binding divergence, record versus decision, option-index encoding, agent trace reproducibility",
        guard_label="CITE/BIBITEM GUARD FAILED",
    ),
}


# ---------------------------------------------------------------- hygiene stage
def sanitise(doc, rules):
    """Paper #7's submission-hygiene stage; `rules` is a subset of
    {"unit_ids", "flatten_links", "footnote_star"}. An empty tuple is the
    identity transform, which is what paper #3 needs. Returns (doc, log)."""
    log = []
    if "unit_ids" in rules:
        ids = sorted(set(re.findall(r"\bU[A-Z]{2,}[0-9]+[a-z]?\b", doc)))
        if ids:
            doc = re.sub(r"\bU[A-Z]{2,}[0-9]+[a-z]?\b", "", doc)
            doc = re.sub(r",\s*,", ",", doc)
            doc = re.sub(r",\s*:", ":", doc)
            doc = re.sub(r"[ \t]{2,}", " ", doc)
            log.append("removed internal unit ids: %s" % ids)
    if "flatten_links" in rules:
        def link(m):
            label, url = m.group(1), m.group(2).strip()
            if url.startswith("http"):
                return "[[LINK:%s|%s]]" % (label, url)
            log.append("flattened local markdown link [%s](%s) to its label" % (label, url))
            return label
        doc = LINK.sub(link, doc)
    if "footnote_star" in rules:
        # a leading "\*" is the source's footnote-asterisk marker
        doc = re.sub(r"(?m)^\\\*", STAR, doc)
    return doc, log


# ---------------------------------------------------------------- bibliography: .bib strategy
def parse_bib(path):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"(?m)^%.*$", "", raw)             # strip comments
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,]+),", raw):
        kind, key = m.group(1), m.group(2).strip()
        j, depth, end = m.end(), 1, None
        while j < len(raw) and depth:
            if raw[j] == "{": depth += 1
            elif raw[j] == "}": depth -= 1
            j += 1
        end = j - 1
        body = raw[m.end():end]
        fields, k = {}, 0
        while True:
            fm = FIELD.search(body, k)
            if not fm: break
            name = fm.group(1).lower(); k = fm.end()
            while k < len(body) and body[k] in " \t\n": k += 1
            if k < len(body) and body[k] == "{":
                d, st = 1, k + 1
                while k + 1 < len(body) and d:
                    k += 1
                    if body[k] == "{": d += 1
                    elif body[k] == "}": d -= 1
                fields[name] = re.sub(r"\s+", " ", body[st:k]).strip(); k += 1
            else:
                q = body.find(",", k); q = len(body) if q < 0 else q
                fields[name] = re.sub(r"\s+", " ", body[k:q]).strip().rstrip(","); k = q + 1
        entries.append((kind, key, fields))
    return entries


def bibitem(key, f):
    """Render one entry. Values are already LaTeX as written in the .bib, so pass them raw."""
    def g(name):
        v = f.get(name)
        return re.sub(r"\s+", " ", v).strip() if v else ""
    def auth(v):
        parts = [x.strip() for x in v.split(" and ")]
        return (", ".join(parts[:-1]) + " and " + parts[-1]) if len(parts) > 1 else v
    bits = []
    if g("author"):    bits.append(auth(g("author")))
    if g("title"):     bits.append(r"\emph{" + g("title") + "}")
    # Honest authorless representation: declared via `authornote`, never the placeholder.
    if g("authornote"): bits.append(g("authornote"))
    if g("booktitle"): bits.append(g("booktitle"))
    if g("journal"):   bits.append(g("journal"))
    if g("volume"):    bits.append("vol.~" + g("volume"))
    if g("number"):    bits.append("no.~" + g("number"))
    if g("pages"):     bits.append("pp.~" + g("pages"))
    if g("publisher"): bits.append(g("publisher"))
    if g("address"):   bits.append(g("address"))
    if g("year"):      bits.append(g("year"))
    if g("doi"):       bits.append("DOI: " + g("doi"))
    if g("eprint"):    bits.append("arXiv:" + g("eprint"))
    if g("howpublished"): bits.append(g("howpublished"))
    if g("url"):       bits.append(r"\url{" + g("url") + "}")
    missing = [x for x in ("author", "title") if not g(x)]
    tail = (r" \emph{[Author and/or title not recorded in the corpus --- to be completed"
            r" before submission.]}") if (missing and not g("authornote")) else ""
    return "\\bibitem{" + key + "} " + ", ".join(bits) + "." + tail


# ---------------------------------------------------------------- inline conversion
class Converter:
    def __init__(self, cfg):
        self.cfg = cfg
        self.U = dict(U_ENC)
        self.U.update(cfg["unicode"])
        self.cite_re = re.compile(cfg["cite_mark_re"])
        self.link_markers = cfg["link_markers"]
        self.footnote_star = cfg["footnote_star"]

    # A LaTeX control WORD is a backslash followed by one or more letters, and TeX keeps
    # absorbing letters into the name until a non-letter appears.  So an escape that IS a bare
    # control word silently eats the next character when that character is a letter: the section
    # sign maps to \S, so "§B3" became "\SB3", and TeX then looked up a macro named \SB that does
    # not exist ("Undefined control sequence"), dropping the "§B" from the shipped PDF.  Terminating
    # the control word with an empty group is byte-minimal and semantics-preserving: both "\S{}B3"
    # and "\S B3" print "§B3".
    #
    # The decision has to be made per substituted character, while the source boundary is still
    # known.  A regex over the FINISHED string cannot be used: a greedy control-word regex matches
    # only a PREFIX of a longer macro, so inside "\documentclass" it matches "\documen", inside
    # "$\kappa$" it matches "\kapp", and it fires on legitimate escapes (measured: 2080 false hits
    # across the three papers).  So: this character's replacement must be exactly ONE control word,
    # and the NEXT character's replacement must start with a letter.
    CONTROL_WORD_ONLY = re.compile(r"\\[A-Za-z]+\Z")

    def esc(self, text):
        out = []
        for i, c in enumerate(text):
            rep = self.U.get(c, SPECIALS.get(c, c))
            if i + 1 < len(text):
                nxt = self.U.get(text[i + 1], SPECIALS.get(text[i + 1], text[i + 1]))
                if nxt[:1].isalpha() and self.CONTROL_WORD_ONLY.match(rep):
                    rep += "{}"
            out.append(rep)
        return "".join(out)

    def cite_mark(self, text):
        for key, pat in self.cfg["cite_anchors"]:
            m = re.search(pat, text)
            if m and ("[[CITE:%s]]" % key) not in text:
                text = text[:m.end()] + "[[CITE:%s]]" % key + text[m.end():]
        return text

    @staticmethod
    def _cite_emit(m):
        return "\\cite{" + m.group(1).replace("\\", "") + "}"

    @staticmethod
    def _link_emit(m):
        label, url = m.group(1), m.group(2)
        if url.startswith("http"):
            return label + " (\\url{" + url + "})"
        return label

    def inline(self, text):
        text = self.cite_mark(text)
        parts, pos = [], 0
        for m in CODE_RE.finditer(text):
            parts.append(self.esc(text[pos:m.start()]))
            parts.append(r"\texttt{" + self.esc(m.group(1)) + "}")
            pos = m.end()
        parts.append(self.esc(text[pos:]))
        s = "".join(parts)
        s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\\emph{\1}", s)
        if self.link_markers:
            s = LINK_MARK_RE.sub(self._link_emit, s)
        s = self.cite_re.sub(self._cite_emit, s)
        if self.footnote_star:
            s = s.replace(STAR, r"$^{*}$")
        return s


def quoteify(doc):
    """Pair straight double quotes across the body: " -> `` / ''."""
    out, open_q = [], True
    for ch in doc:
        if ch == '"':
            out.append("``" if open_q else "''"); open_q = not open_q
        else:
            out.append(ch)
    return "".join(out)


def extract_abstract(lines):
    ai = next(i for i, l in enumerate(lines) if l.strip() == "## Abstract")
    ae = ai + 1
    while ae < len(lines) and not lines[ae].startswith("## ") \
            and not re.fullmatch(r"-{3,}", lines[ae].strip()):
        ae += 1
    ab = lines[ai + 1:ae]
    while ab and ab[0].strip() == "":
        ab.pop(0)
    while ab and ab[-1].strip() == "":
        ab.pop()
    return "\n".join(ab) + "\n"


def compute_stats(lines):
    stats = dict(tables=0, code=0, blockquotes=0, bullets=0, numbered=0, footnotes=0,
                 images=0, html=0, math=0, hr=0)
    for ln in lines:
        stats["tables"] += 1 if ln.startswith("|") else 0
        stats["code"] += len(CODE_RE.findall(ln))
        stats["blockquotes"] += 1 if ln.startswith("> ") else 0
        stats["bullets"] += 1 if ln.startswith("- ") else 0
        stats["numbered"] += 1 if re.match(r"^\d+\. ", ln) else 0
        stats["footnotes"] += len(re.findall(r"\[\^", ln))
        stats["images"] += len(re.findall(r"!\[", ln))
        stats["html"] += len(re.findall(r"<(/?)(div|span|table|br|b|i|p|img)\b", ln))
        stats["math"] += len(re.findall(r"\$[^$]+\$", ln))
        stats["hr"] += 1 if re.fullmatch(r"-{3,}", ln.strip()) else 0
    return stats


# ---------------------------------------------------------------- block parser
def parse_blocks(lines, conv, cfg):
    body, headings, title = [], [], None
    bib_entries, banners = [], []
    refmode = False
    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.fullmatch(r"-{3,}", ln.strip()):
            i += 1; continue
        if ln.startswith("# ") and title is None:
            title = ln[2:].strip(); i += 1; continue
        m = re.match(r"^(#{2,3})\s+(.*)$", ln)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if txt.lower() == "abstract":
                body.append(("__ABSTRACT__", "raw")); headings.append((2, "Abstract")); i += 1; continue
            if txt.lower() == "references":
                body.append(("__BIBPROSE__", "raw")); headings.append((2, "References"))
                refmode = cfg["bib_from_manuscript_references"]; i += 1; continue
            num = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$", txt)
            numbered = bool(num)
            clean = num.group(2) if num else txt
            headings.append((lvl, clean))
            cmd = "section" if lvl == 2 else "subsection"
            body.append((("\\%s{%s}" % (cmd, conv.inline(clean))) if numbered
                         else ("\\%s*{%s}" % (cmd, conv.inline(clean))), "raw"))
            i += 1; continue
        if refmode and re.match(r"^\d+\.\s", ln):
            num = int(re.match(r"^(\d+)\.", ln).group(1))
            parts = [re.sub(r"^\d+\.\s*", "", ln).strip()]
            i += 1
            while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() \
                    and not re.match(r"^\d+\.\s", lines[i]):
                parts.append(lines[i].strip()); i += 1
            bib_entries.append((num, conv.inline(" ".join(parts))))
            continue
        if ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").lstrip()); i += 1
            body.append(("\\begin{quote}\n" + conv.inline(" ".join(buf)) + "\n\\end{quote}", "raw")); continue
        if ln.startswith("- "):
            items, cur = [], []
            while i < len(lines) and (lines[i].startswith("- ") or (lines[i].startswith("  ") and lines[i].strip())):
                if lines[i].startswith("- "):
                    if cur: items.append(" ".join(cur))
                    cur = [lines[i][2:].strip()]
                else:
                    cur.append(lines[i].strip())
                i += 1
            if cur: items.append(" ".join(cur))
            body.append(("\\begin{itemize}\n" + "\n".join("\\item " + conv.inline(x) for x in items)
                         + "\n\\end{itemize}", "raw")); continue
        if re.match(r"^\d+\.\s", ln):
            items, cur = [], []
            while i < len(lines) and (re.match(r"^\d+\.\s", lines[i]) or (lines[i].startswith("  ") and lines[i].strip())):
                if re.match(r"^\d+\.\s", lines[i]):
                    if cur: items.append(" ".join(cur))
                    cur = [re.sub(r"^\d+\.\s", "", lines[i]).strip()]
                else:
                    cur.append(lines[i].strip())
                i += 1
            if cur: items.append(" ".join(cur))
            body.append(("\\begin{enumerate}\n" + "\n".join("\\item " + conv.inline(x) for x in items)
                         + "\n\\end{enumerate}", "raw")); continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.fullmatch(r"[-:| ]+", lines[i].strip().strip("|")):
                    rows.append(cells)
                i += 1
            ncol = max(len(r) for r in rows)
            w = 0.96 / ncol
            spec = "@{}" + "".join(">{\\raggedright\\arraybackslash}p{%.3f\\textwidth}" % w for _ in range(ncol)) + "@{}"
            fs = "\\footnotesize\n" if ncol >= 5 else ""
            out = [fs, "\\begin{center}", "\\begin{tabular}{" + spec + "}", "\\hline"]
            for ridx, r in enumerate(rows):
                r = r + [""] * (ncol - len(r))
                cell = [conv.inline(c) for c in r]
                if ridx == 0: cell = [r"\textbf{" + c + "}" for c in cell]
                out.append(" & ".join(cell) + r" \\ \hline")
            out += ["\\end{tabular}", "\\end{center}"]
            body.append(("\n".join(out), "raw")); continue
        if not ln.strip():
            i += 1; continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,3}\s|>\s?|-\s|\d+\.\s|\|)", lines[i]) \
                and not re.fullmatch(r"-{3,}", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        body.append((conv.inline(" ".join(buf)), "para"))

    if cfg["drop_status_banners"]:
        clean = []
        for blk, kind in body:
            if kind == "para" and re.match(r"^(\\textbf\{Status:\}|Status:)", blk):
                banners.append(blk); continue
            clean.append((blk, kind))
        body = clean
    return title, body, headings, bib_entries, banners


# ---------------------------------------------------------------- the guard
def guard_citations(doc, bib_keys, cfg):
    """The trap this project has already hit twice: a \\bibitem that is never cited,
    or a \\cite with no \\bibitem, must fail loudly. Raises SystemExit.

    Zero-bibliography packages (bib_keys == [], expected_bib_count == 0): this check is
    NOT disabled and NOT vacuous in the failure direction -- `cited` and `bibitems` are
    asserted to be empty, so a stray \\cite is an unknown key and a stray \\bibitem breaks
    the count. What it CANNOT see is an empty thebibliography environment; that is why a
    zero-bibliography package emits none (bib_source="none") and why guard() adds the
    expect_zero_bib check. Both are red-proven in tests/test_md2tex.py."""
    raw_cites = re.findall(cfg["cite_extract_re"], doc)
    if cfg["cite_split"]:
        cited = sorted({k for c in raw_cites for k in c.split(cfg["cite_split"]) if k})
    else:
        cited = sorted(set(raw_cites))
    bibitems = len(re.findall(r"\\bibitem\{", doc))
    missing = [k for k in bib_keys if k not in cited]
    unknown = [k for k in cited if k not in bib_keys]
    if missing or unknown or bibitems != len(bib_keys):
        raise SystemExit("%s: uncited=%s unknown=%s bibitems=%d bibkeys=%d"
                         % (cfg["guard_label"], missing, unknown, bibitems, len(bib_keys)))
    return cited, missing, unknown, bibitems


def guard(cfg, doc, bib_keys):
    residual = collections.Counter(c for c in doc if ord(c) > 127)
    if cfg["fail_on_residual_nonascii"] and residual:
        raise SystemExit("NON-ASCII in main.tex: %r" % residual)
    if cfg["expected_bib_count"] is not None:
        if len(bib_keys) != len(set(bib_keys)) or len(bib_keys) != cfg["expected_bib_count"]:
            raise SystemExit("unexpected bibitem set: %r" % bib_keys)
    if cfg["expect_zero_bib"]:
        # The bidirectional check in guard_citations() is non-vacuous even with
        # zero bib keys, but it cannot see an EMPTY thebibliography environment or other
        # citation apparatus. This is the positive assertion for a paper that ships no
        # bibliography: the output must carry none of it.
        hits = [tok for tok in ("\\cite{", "\\bibitem{", "thebibliography") if tok in doc]
        if hits:
            raise SystemExit("%s: citation apparatus in a zero-bibliography paper: %s"
                             % (cfg["guard_label"], hits))
    cited, missing, unknown, bibitems = guard_citations(doc, bib_keys, cfg)
    if cfg["author_line"] is None and "\\author" in doc:
        raise SystemExit("NO-AUTHOR GUARD FAILED: package declares no author block "
                         "but \\author is present in main.tex")
    nb, ne = doc.count("\\begin{"), doc.count("\\end{")
    if nb != ne:
        raise SystemExit("unbalanced \\begin/\\end: %d/%d" % (nb, ne))
    if cfg["require_balanced_braces"]:
        ob, cb = doc.count("{"), doc.count("}")
        if ob != cb:
            raise SystemExit("unbalanced braces: %d/%d" % (ob, cb))
    for name, pat in cfg["forbidden"]:
        hit = re.search(pat, doc)
        if hit:
            raise SystemExit("DRAFTING ARTEFACT (%s): %r"
                             % (name, doc[max(0, hit.start() - 60):hit.end() + 60]))
    if cfg["residual_markdown_bold"] and "**" in doc:
        raise SystemExit("residual markdown bold in main.tex")
    if cfg["require_author_slot"]:
        # Exactly one \author line, and it must equal the configured byline.  The
        # expected value is read from the registry (author_line), so the data remains
        # the single source of truth; strictness is unchanged and this still fails on a
        # missing byline, a second \author line, or a different name.
        _author_lines = [ln.strip() for ln in doc.splitlines()
                         if ln.strip().startswith("\\author")]
        if _author_lines != [cfg["author_line"]]:
            raise SystemExit("author line missing, duplicated or different: %r"
                             % (_author_lines,))
    return dict(cited=cited, missing=missing, unknown=unknown, bibitems=bibitems,
                residual=residual, nb=nb, ne=ne)


# ---------------------------------------------------------------- the converter
def convert(cfg, repo_root=None, paper_root=None, outdir=None, quiet=False):
    root = paper_root or os.path.join(repo_root or REPO_ROOT, cfg["root"])
    md_path = os.path.join(root, cfg["md"])
    conv = Converter(cfg)
    raw = open(md_path, encoding="utf-8").read()
    nonascii = collections.Counter(c for c in raw if ord(c) > 127)
    unmapped = {c: n for c, n in nonascii.items() if c not in conv.U}
    if unmapped and cfg["fail_on_unmapped_nonascii"]:
        raise SystemExit("UNMAPPED non-ascii in source: %r" % unmapped)
    # Per-package PROSE de-naming: targeted literal replacements that describe an
    # internal working record instead of naming it in the shipped LaTeX.  Deliberately
    # NOT a blanket stripper -- each rule names one exact string; a rule that matches
    # nothing is a stale rule and is a hard failure, not a silent no-op.  Packages that
    # need no de-naming omit the key entirely (cfg.get default), so their output is
    # untouched.
    for _old, _new in cfg.get("dename_rules", ()):
        if raw.count(_old) < 1:
            raise SystemExit("dename_rules: rule matched nothing (stale rule): %r" % (_old,))
        raw = raw.replace(_old, _new)
    doc, sanlog = sanitise(raw, cfg["sanitise_rules"])
    lines = doc.split("\n")
    stats = compute_stats(lines)
    title, body, headings, bib_entries, banners = parse_blocks(lines, conv, cfg)

    tex = []
    # a4paper: the standard classes default to US letter. A4 is the safer default for preprint
    # servers, and this converter owns the document class and preamble, so the page size is set
    # here rather than left to a manuscript-level change.
    tex.append("\\documentclass[11pt,a4paper]{article}")
    # Tectonic is XeTeX, and the class option only sets the \paperwidth/\paperheight LENGTHS; the
    # PDF media box follows \pdfpagewidth/\pdfpageheight, which nothing sets unless a driver package
    # is loaded.  Measured: with only the a4paper option the compiled page stayed 612x792pt (US
    # letter).  These two primitives are the pdfTeX/XeTeX spelling of what a driver package does, so
    # the media box becomes 210x297mm while the class's own A4 text block is kept unchanged.
    tex.append("\\pdfpagewidth=\\paperwidth")
    tex.append("\\pdfpageheight=\\paperheight")
    tex.append("\\usepackage[utf8]{inputenc}")
    tex.append("\\usepackage[T1]{fontenc}")
    tex.append("\\usepackage{amsmath}")
    tex.append("\\usepackage{amssymb}")
    tex.append("\\usepackage{array}")
    tex.append("\\usepackage{url}")
    tex.append("\\sloppy")
    tex.append("\\title{" + conv.inline(title) + "}")
    if cfg["author_line"]:
        # None means this package ships no author block at all; the truth of that
        # claim is asserted in guard() ("NO-AUTHOR GUARD"), not assumed here.
        tex.append(cfg["author_line"])
    tex.append(cfg["date_line"])
    tex.append("\\begin{document}")
    tex.append("\\maketitle")
    if cfg.get("keywords"):
        # Keywords must be ON page 1 (Preprints.org: "The first page of your manuscript must
        # contain ... keywords").  Measured: paper #3's abstract alone fills page 1, so a
        # keyword line emitted after \end{abstract} lands on page 2; printing it immediately
        # after \maketitle keeps it on page 1 by construction and adds no numeric literal.
        tex.append("\\noindent\\textbf{Keywords:} " + cfg["keywords"])
        tex.append("")
    in_abs = False
    for blk, _ in body:
        if blk == "__ABSTRACT__":
            tex.append("\\begin{abstract}"); in_abs = True; continue
        if blk == "__BIBPROSE__":
            if in_abs: tex.append("\\end{abstract}"); in_abs = False
            tex.append("\\section*{References}")
            continue
        if in_abs and blk.startswith("\\section"):
            tex.append("\\end{abstract}"); in_abs = False
        tex.append(blk); tex.append("")
    if in_abs: tex.append("\\end{abstract}")

    if cfg["bib_source"] == "bibtex_file":
        entries = parse_bib(os.path.join(root, cfg["bib_file"]))
        bib_keys = [k for _, k, _ in entries]
    elif cfg["bib_source"] == "manuscript_references":
        entries = None
        bib_keys = ["ref%d" % n for n, _ in bib_entries]
    elif cfg["bib_source"] == "none":
        entries = None
        bib_keys = []
    else:
        raise SystemExit("unknown bib_source %r" % cfg["bib_source"])

    if cfg["bib_source"] != "none":
        for line in cfg["bib_preamble"]:
            tex.append(line)
        tex.append("\\begin{thebibliography}{99}")
        if entries is not None:
            for kind, key, f in entries:
                tex.append(bibitem(key, f))
        else:
            for num, txt in bib_entries:
                tex.append("\\bibitem{ref%d} %s" % (num, txt))
        tex.append("\\end{thebibliography}")
    tex.append("\\end{document}")

    main_doc = quoteify("\n".join(tex) + "\n")
    out = {"main.tex": main_doc}
    if cfg["emit_abstract_files"]:
        out["ABSTRACT.txt"] = extract_abstract(lines)
        meta = cfg["abstract_metadata"]
        if not meta.isascii():
            raise SystemExit("ABSTRACT_METADATA.txt is not ASCII")
        if "\n" in meta or "\r" in meta:
            raise SystemExit("ABSTRACT_METADATA.txt is not a single line")
        if not (0 < len(meta) <= 1920):
            raise SystemExit("ABSTRACT_METADATA.txt length %d outside 1..1920" % len(meta))
        out["ABSTRACT_METADATA.txt"] = meta + "\n"

    g = guard(cfg, main_doc, bib_keys)

    dest = outdir or os.path.join(root, cfg["outdir"])
    os.makedirs(dest, exist_ok=True)
    for name, text in out.items():
        with open(os.path.join(dest, name), "w", encoding="utf-8") as fh:
            fh.write(text)

    if not quiet:
        ncites = len(re.findall(r"\\cite\{", main_doc))
        print("[%s] wrote %s (%d bytes) | %d output file(s)"
              % (cfg["slug"], os.path.join(dest, "main.tex"), len(main_doc.encode()), len(out)))
        # Success line: state PASSED explicitly and name what guard_label means (the defect
        # this guard exists to prevent) so a passing run cannot be read as a failing one.
        print("  bibitems: %d | \\cite occurrences: %d | distinct cite keys: %d"
              " | guard: PASSED (the guard did not fire; label %r names the defect this guard"
              " exists to prevent — a shipped bibliography nothing cites, or a citation"
              " with no entry — and is NOT this run's outcome)"
              % (g["bibitems"], ncites, len(g["cited"]), cfg["guard_label"]))
        print("  uncited bib keys:", g["missing"] or "none",
              "| cite keys with no \\bibitem:", g["unknown"] or "none")
        print("  balanced \\begin/\\end:", g["nb"] == g["ne"], "(%d/%d)" % (g["nb"], g["ne"]))
        print("  residual non-ascii in output:", dict(g["residual"]) or "none")
        print("  sanitisation:", sanlog or "none", "| dropped drafting banners:", len(banners))
        print("  headings:", len(headings), "| bib entries:",
              len(entries) if entries is not None else len(bib_entries), "| constructs:", stats)
    return dict(root=root, dest=dest, outputs=out, bib_keys=bib_keys,
                nonascii=nonascii, unmapped=unmapped, sanlog=sanlog,
                banners=banners, stats=stats, headings=headings, guard=g)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Markdown -> LaTeX: one converter, one config table.")
    ap.add_argument("--package", required=True, choices=sorted(PACKAGES),
                    help="package slug (one key of PACKAGES)")
    ap.add_argument("--repo-root", default=REPO_ROOT)
    ap.add_argument("--paper-root", default=None,
                    help="override the paper directory (used to point at a copy, e.g. the guard test)")
    ap.add_argument("--outdir", default=None,
                    help="override the output directory (default: <paper>/<cfg.outdir>)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    convert(PACKAGES[args.package], repo_root=args.repo_root,
            paper_root=args.paper_root, outdir=args.outdir, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
