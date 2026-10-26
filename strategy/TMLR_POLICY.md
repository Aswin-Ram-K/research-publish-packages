# TMLR policy vs. the author's planned publication order

**Unit:** UTMLRPOL1 · **Scope:** TMLR's own published rules only (jmlr.org/tmlr/*, the
`JmlrOrg/tmlr-style-file` repo). No blogs, no secondary summaries.
**Snapshot:** fetched this session. Footer reads "© TMLR 2026"; news current to 2026.01.01; the FAQ
contains an item dated "As of September 1, 2026". Policies can change — re-fetch before relying on this.

## Verdict on the planned order

**The order is compatible with TMLR, with one hard constraint and two practical ones.**

Planned order: Zenodo data deposit → public Preprints.org preprint under the author's real name → later
TMLR submission, with a public GitHub repo and a Zenodo DOI for the artifacts.

| # | Element of the plan | Status under TMLR's rules |
|---|---|---|
| 1 | Public **identified preprint** on Preprints.org before submitting | **Allowed.** Preprint servers are named as acceptable prior disclosure; posting under a real name is explicitly permitted. |
| 2 | Citing/linking that preprint or its **DOI** in the TMLR submission | **Forbidden in the TMLR PDF.** Anonymity "must be maintained by not linking to another version that includes the authors' names". |
| 3 | **No arXiv** version | **No problem.** arXiv is never required. |
| 4 | Public **GitHub repo** / **Zenodo DOI** cited in the submission | **Hazard.** A named repo or minted DOI is a de-anonymizing link. Must be anonymized or withheld until camera-ready. |
| 5 | Same work **not** under review at another venue | **Required.** Parallel submission to another *archival, peer-reviewed* venue is prohibited. |

The constraint is **not** "don't post the preprint". It is **"don't point at it from the TMLR PDF"**.

---

## Q1. May a submission whose content is already a public, identified preprint be submitted?

**Yes — explicitly.** The controlling text is the "Dual Submissions and Originality" section of
[Submission Guidelines and Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html), quoted in
full because the second sentence is what narrows it:

> "Unlike many other journals, TMLR only accepts original contributions that don't reuse the authors' own
> prior work. In particular, we do not accept submissions that are expanded versions of conference papers.
> There should not be any reuse of written text, figures or results between the submitted paper and any
> paper which has been published, accepted for publication, or submitted in parallel at another archival,
> peer-reviewed venue. It is acceptable for a submission to overlap with the author's previous work if it
> was shared at venues or tracks that are publicly declared, in writing, to be non-archival, such as
> workshops, or on preprint servers such as arXiv and bioRxiv."

The [FAQ](https://jmlr.org/tmlr/faq.html) states the operative test even more plainly:

> "**Q: How does the double blind policy work? Would papers already on arXiv be allowed? How about papers
> that are visible on authors' websites, etc.?**
> A: You can still submit, even if a preprint of your work already is available online somewhere (as long
> as it's not in official proceedings for some other publishing venue). We follow the same approach as
> double blind conferences, asking that reviewers don't actively search online to figure out who the
> authors are."

And the [Author Guidelines](https://jmlr.org/tmlr/author-guide.html) make identity in the preprint
irrelevant:

> "Authors are also allowed to upload their submissions to arXiv or other preprint servers at any time,
> either anonymously or including their identity, though double blind of the TMLR submission itself must
> be maintained by not linking to another version that includes the authors' names."

**Conditions the author must satisfy:**
- Preprints.org must not be "official proceedings for some other publishing venue" — a preprint server is
  not proceedings, so a plain Preprints.org posting qualifies. Do **not** let the same manuscript also
  appear in a peer-reviewed proceedings.
- The work must not be an "expanded version of conference papers", and there must be no reuse of text,
  figures or results from anything published/accepted/parallel-submitted at an *archival, peer-reviewed*
  venue.
- Note the two lists are introduced with "**such as**" / "**or other preprint servers**" — non-exhaustive.
  Preprints.org is a preprint server, so it falls inside the named category, but TMLR names arXiv and
  bioRxiv and never names Preprints.org. Treat this as **category-level coverage, not an explicit
  endorsement** — no primary source names Preprints.org.

**Separate hazard worth checking:** the TMLR home page says "TMLR does not accept submissions that have
any overlap with previously published work" (<https://jmlr.org/tmlr/>). That sentence, read alone, appears
to forbid the plan. It does not: "previously published work" is given its operative meaning by the Dual
Submissions section above, which expressly carves out preprint servers. Quote the section, not the
home-page line, if this is ever challenged.

---

## Q2. Must the submission avoid citing or linking the preprint / its DOI?

**Yes.** This is the sharpest, most directly applicable rule in the whole corpus — one clause in the
[Author Guidelines](https://jmlr.org/tmlr/author-guide.html):

> "Authors are also allowed to upload their submissions to arXiv or other preprint servers at any time,
> either anonymously or including their identity, **though double blind of the TMLR submission itself must
> be maintained by not linking to another version that includes the authors' names.**"

Consequences for the author:
- **Do not** cite the Preprints.org DOI, and do not hyperlink the preprint, anywhere in the submission PDF
  (body, references, or Appendix).
- **Do not** cite the Zenodo DOI or the public GitHub URL in the submission PDF either. Both are
  author-identifying (Zenodo records carry creator names; a GitHub org/repo does), and the rule is phrased
  as "not linking to another version that includes the authors' names" — a DOI that resolves to the
  named preprint is exactly that link. *This is an inference from the rule's purpose, not a separately
  quoted sentence; the quoted sentence covers "another version", and a data DOI is a different artifact,
  so an AE could read it more leniently. Treat the cautious reading as binding.*
- If the code/data must be referenced at submission time, reference an **anonymized mirror** (e.g. an
  anonymized repository) with no author names, and swap in the real GitHub/Zenodo links at camera-ready.
- The only permitted pointer to prior work is the **previous TMLR submission URL on a resubmission**,
  which the FAQ carves out: "Only the action editor (not the reviewers) will see the previous submission
  URL, so including it will not violate our guidelines." That carve-out is for TMLR resubmissions only —
  it does **not** license linking a Preprints.org DOI.

---

## Q3. Is an arXiv preprint required?

**No. arXiv is never required, and there is no arXiv-endorsement requirement anywhere.** TMLR's stated
submission prerequisites contain no arXiv step — the only profile requirement is on OpenReview:

> "All authors must have complete and active OpenReview profiles, including information such as
> affiliations, conflicts of interest, and publication history."
> — [Author Guidelines](https://jmlr.org/tmlr/author-guide.html)

arXiv appears only as *permission* ("allowed to upload ... at any time") and as a *convenience
suggestion*, in the FAQ's answer about indexing:

> "Fortunately, it is possible to edit or add entries to your own Google Scholar profile, and it is
> usually able to pick up papers posted to arXiv, so consider posting your paper to arXiv, waiting for it
> to be indexed, and then edit the details to reflect your paper's publication in TMLR."
> — [FAQ](https://jmlr.org/tmlr/faq.html)

"consider" — not "must". The author's non-use of arXiv has **no** bearing on TMLR eligibility.

---

## Q4. Anonymity at submission, and after acceptance

**At submission — double blind, full anonymization of the PDF *and* the supplementary material:**

> "TMLR uses a double blind review process and submissions must be anonymized."
> — [Author Guidelines](https://jmlr.org/tmlr/author-guide.html)

> "Authors may submit up to 100MB of supplementary material, such data, source code or illustrative videos;
> all supplementary materials must be in PDF or ZIP format. Supplementary material should be material
> created by the authors that directly supports the submission content. **Like submissions, supplementary
> material must be anonymized.**"
> — [Author Guidelines](https://jmlr.org/tmlr/author-guide.html)

> "TMLR uses an open-reviewing, double-blind process. ... we follow a double blind model where the
> identities of authors and invited reviewers are withheld. Reviewers are expected not to take any actions
> that would violate this double blind state, e.g. searching for related presentations or arXiv preprints."
> — [Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html)

Who sees what, during review:

> "Only the action editor assigned to that paper and the editors-in-chief can see the author's [names]."
> — [FAQ](https://jmlr.org/tmlr/faq.html) *(sic — "author's" appears in the original)*

Also note: the metadata (affiliations, conflicts, funding, IRB) is collected but withheld —
"Such information will not be disclosed to the reviewers, but will be once a decision on the manuscript
has been made" ([Author Guidelines](https://jmlr.org/tmlr/author-guide.html)).

**During review the paper is public but anonymous:** "the action editor will assign at least three
qualified reviewers and the paper will become public" ([Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html)).
Reviews and discussion are public too.

**After acceptance — anonymity ends.** Identity is disclosed once a decision is made (quote above), and
the camera-ready is the identified version:

> "Authors of accepted papers must provide a 'camera ready' version, verified by the action editor, which
> would include a link to the review page for the paper."
> — [Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html)

So the public GitHub repo and Zenodo DOI can be cited normally **at camera-ready**, after acceptance.

On a **reject**, anonymity is optional rather than imposed: "The submission remains publicly available on
OpenReview and the authors are given the opportunity to reveal their identity. Doing so will preclude them
from submitting a revised version of the manuscript to TMLR." (same page)

---

## Q5. AI-use disclosure — **the previous unit's "TMLR is silent" finding is WRONG**

TMLR has an explicit, mandatory disclosure. The previous unit appears to have read only the editorial
policies page, which states the *liability* rule and stops short of a footnote requirement; the
requirement is stated in the **FAQ**, under Authors:

> "**Q: Can I use ChatGPT or other large language model systems to assist in writing my TMLR submission?**
> A: Yes, but TMLR also considers that it is the authors' responsibility to avoid any unforeseen
> consequences that might come about from using such tools, such as the later discovery that a significant
> part of the submission's content has been plagiarized (in which case we'd have to reject the paper).
> Similarly, our expectation is that the ideas, claims and results found in submissions are human-sourced,
> not produced by such tools.
> **Additionally, transparency is always good, so we also require that authors mention explicitly in their
> submission that they have used this tool, as a footnote on the first page.**"
> — [FAQ](https://jmlr.org/tmlr/faq.html)

**Concrete obligation: a footnote on page 1 of the submission stating that an LLM tool was used.** This
applies to the TMLR PDF, and it must sit on the title page without naming the author.

Corroborating policy paragraph ([Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html)):

> "LLMs may be used as general-purpose assistive tools. Whichever tools are used, authors are fully
> responsible for content on which they are listed as (co-) authors. This includes, but is not limited to,
> content generated by LLMs that could be construed as plagiarism or scientific misconduct (e.g.,
> fabrication of facts). Low-quality contributions (be they submissions or reviews) that appear to be
> largely LLM-generated will be closely examined for evidence of the issues mentioned previously, such as
> scientific misconduct. LLMs are not eligible for authorship. We will periodically revise this policy as
> new information about the use of LLMs in the scientific process becomes available."

---

## Q6. LaTeX style file — mandatory, and only the PDF is submitted

**Yes, `tmlr.sty` and its template are mandatory**, and violating the format can cost the paper the review
entirely:

> "The Author Guidelines page contains a LaTeX stylefile and template; these are mandatory. Any changes to
> the stylefile or template that alters the formatting, font, or layout of the manuscript may result in
> rejection without review."
> — [Submission Instructions](https://jmlr.org/tmlr/submissions.html)

> "Submissions must be PDF files generated using the [TMLR LaTeX stylefile and template]."
> — [Author Guidelines](https://jmlr.org/tmlr/author-guide.html)

**Where to get it:** <https://github.com/JmlrOrg/tmlr-style-file> — direct zip:
<https://github.com/JmlrOrg/tmlr-style-file/archive/refs/heads/main.zip> (linked from the Author
Guidelines). The repo contains `tmlr.sty`, `tmlr.bst`, `main.tex`, `main.bib`, `math_commands.tex`,
`fancyhdr.sty`, plus `main.pdf` and `main-accepted.pdf`; Apache-2.0; last commit "Removed duplicated line
in tmlr.sty", Jun 30 2023.

**What the portal accepts:** **a PDF** for the manuscript (no LaTeX source is required — the text says
"must be PDF files generated using" the stylefile, i.e. the PDF is the artifact), plus **at most 100MB of
supplementary material in PDF or ZIP**. Appendices go in the main PDF: "Appendices can be included in the
main pdf. The supplementary zip file should contain additional material such as videos or code."
([FAQ](https://jmlr.org/tmlr/faq.html))

**If the author later does use the template for a preprint,** the FAQ adds: "We don't have a policy
proscribing the use of our template on arXiv. However, make sure to use the 'preprint' option of the
stylefile if you do." — a snippet the author may want for the Preprints.org build, though the
`[preprint]` option is documented for arXiv.

---

## Q7. Timeline and decision options

**Target: ~9 weeks to a final decision.**

> "TMLR does not make any guarantees, and manuscripts whose main body exceeds 12 pages are subject to
> longer timescales, but in general the rolling review process aims to deliver a final decision
> approximately 9 weeks after submission."
> — [FAQ](https://jmlr.org/tmlr/faq.html)

Stage timings from [Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html) and
[FAQ](https://jmlr.org/tmlr/faq.html):

| Stage | Stated duration / trigger |
|---|---|
| Action editor assigned | "within a week" — may desk-reject for scope, expertise, quality, or format violations |
| Reviews due | 2 weeks for ≤12 pages; 4 weeks for >12 pages (main content, before references) |
| Discussion phase | "at least 2 weeks and up to 4 weeks long" |
| Final recommendations | once "at least two weeks have elapsed after all 3 reviews became public" |
| Response to reviews | "no later than 2 weeks after the submission of the 3rd review" (strongly recommended) |

**Decision options — three, quoted verbatim:**

> "The discussion period ends when the action editor enters a decision for the paper, which is one of the
> following:
> - **Accept as is**: the author is notified, and, once the camera ready version is submitted and verified,
>   the manuscript is published.
> - **Accept with minor revision**: the author is notified of the required revisions, and, once the revised
>   camera ready version is submitted and verified, the manuscript is published.
> - **Reject**: the author is notified of the rejection, and the action editor indicates whether they would
>   be willing to consider a significantly revised version of the manuscript."
> — [Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html)

**There is no "major revision" option.** The only revision state is "minor", delivered as the camera-ready.
A reject may be resubmitted: "it will need to be entered as a new submission and a link provided to the
previously rejected submission as well as a description of the changes made since" (same page). Authors may
also **withdraw** before a decision, or **retract** after acceptance.

---

## Q8. Must code and data be available?

**No — availability is encouraged, not required.** Three quotes, all permissive:

> "We encourage authors to, whenever possible, upload materials that improve reproducibility. Specifically,
> it is suggested that authors submit supplementary material including data or code towards this end."
> — [Author Guidelines](https://jmlr.org/tmlr/author-guide.html)

> "The author is encouraged to submit additional materials that can help to support their paper, such as a
> video presentation or code."
> — [Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html)

> "Code and videos may be uploaded and associated with camera ready papers. This may expand over time."
> — [FAQ](https://jmlr.org/tmlr/faq.html)

"encourage" / "is suggested" / "may" throughout; no clause makes code or data a condition of acceptance.
The one binding constraint is again **anonymity**: any code/data supplied at submission time "must be
anonymized" (Q4). This is precisely where the author's public GitHub + minted Zenodo DOI collide with
double blind — see Q2.

---

## Q9. Under review elsewhere at the same time?

**Prohibited if the other venue is archival and peer-reviewed.** Same Dual Submissions paragraph:

> "There should not be any reuse of written text, figures or results between the submitted paper and any
> paper which has been published, accepted for publication, or **submitted in parallel at another archival,
> peer-reviewed venue**."
> — [Editorial Policies](https://jmlr.org/tmlr/editorial-policies.html)

Read together with the following sentence — "It is acceptable for a submission to overlap with the
author's previous work if it was shared at venues or tracks that are publicly declared, in writing, to be
non-archival, such as workshops, or on preprint servers" — the test is **archival vs. non-archival**, not
"is anyone else looking at it". A Preprints.org posting is not "under review"; it is public disclosure, and
it is the permitted kind.

**Not verified:** whether OpenReview's submission form contains a *declaration* field ("is this under
review elsewhere?") that must be answered. The OpenReview TMLR group page
(<https://openreview.net/group?id=TMLR>) is JavaScript-rendered and returned no instructions text to a
crawler — see the gap list below.

---

## Other rules that touch this plan

- **No survey papers.** "As of September 1, 2026, TMLR no longer considers survey papers for review."
  ([FAQ](https://jmlr.org/tmlr/faq.html)). If the manuscript reads as a survey/landscape piece rather than
  a reproduction-with-new-insight, it is out of scope. TMLR does *want* "reproducibility studies of
  previously published results or claims" (scope list) and the FAQ confirms "Are replications of previous
  research welcome? A: Yes." — but the Reproducibility Certification requires added value: "Beyond simple
  verification, the paper must contribute significant added value through additional baselines, analysis,
  ablations, or insights."
- **Author quotas.** Submissions consume an annual budget under the Generalized Harmonic Quota Rule with
  N_1 = 2, N_9 = 9 (doubled for reviewers/AEs). All co-authors need budget. Desk-rejected submissions
  still spend budget. Quota-circumvention via duplicate accounts risks a lifetime ban.
- **Broader Impact Statement** is required only "If their work carries a significant risk of harm"
  ([Author Guidelines](https://jmlr.org/tmlr/author-guide.html)) — optional otherwise, but the Ethics
  Guidelines do expect a harms discussion "when applicable".
- **No author changes.** "The exact set of authors must be listed on OpenReview ... at the time of
  submission and throughout the review process. No authors may be added or removed after submission. There
  are no exceptions to this policy."
- **Licence.** "All TMLR submissions, from the time of submission to final publication, are licensed under
  CC BY 4.0. At all times, copyright is retained by the authors." Compatible with a Zenodo deposit; check
  the Zenodo record's licence matches CC BY 4.0 or is compatible.
- **Holiday pause.** TMLR paused new submissions 2025-12-02 → 2026-01-05; expect a similar pause each
  December. The 2026 pause has not been announced in the fetched snapshot.

---

## Gaps — NOT VERIFIED

1. **OpenReview submission form fields.** <https://openreview.net/group?id=TMLR> is JS-rendered; the
   crawler returned only "Loading". So I cannot confirm: exact form fields, whether an "under review
   elsewhere" declaration is required, whether a preprint declaration is required, or the upload widget's
   accepted file types. Everything above about formats comes from jmlr.org text, not the form.
2. **Preprints.org is never named by TMLR.** The rules name arXiv and bioRxiv as examples ("such as",
   "or other preprint servers"). Coverage of Preprints.org is by category, not by explicit mention.
3. **Whether a data DOI (Zenodo) counts as "a version that includes the authors' names"** for the Q2
   rule — the rule speaks of "another version"; a dataset DOI is a different artifact. I take the cautious
   reading. An AE could read it more leniently.
4. **Whether TMLR checks preprint servers for de-anonymization.** Reviewer guidelines say reviewers "should
   not" search; nothing states authors are screened against Preprints.org. The author-guide does say
   submissions are evaluated to check they are "anonymous".
5. **Date of this snapshot.** The site footer says 2026 and the FAQ contains a 2026-09-01 item, but I did
   not capture a fetch timestamp from a source that proves the current date. Re-verify before submission.

## Sources fetched

| URL | Used for |
|---|---|
| <https://jmlr.org/tmlr/> | home page; "does not accept submissions that have any overlap with previously published work"; double blind; rolling process |
| <https://jmlr.org/tmlr/author-guide.html> | anonymity, preprint permission + no-linking rule, format, supplementary material, licence, decisions |
| <https://jmlr.org/tmlr/editorial-policies.html> | Dual Submissions and Originality, review phases, decision options, LLM policy, quotas, authorship |
| <https://jmlr.org/tmlr/faq.html> | preprint FAQ, LLM footnote requirement, 9-week timeline, openreview visibility, code/videos, surveys |
| <https://jmlr.org/tmlr/submissions.html> | stylefile mandatory, rejection-without-review for format violations |
| <https://jmlr.org/tmlr/ethics.html> | broader impact expectations, data ethics |
| <https://github.com/JmlrOrg/tmlr-style-file> | confirms `tmlr.sty`, `tmlr.bst`, template files |
| <https://openreview.net/group?id=TMLR> | **failed** — JS-rendered, no content |

---

**Dated note 2026-10-18 (UTMLR6):** the Q2 hazard materialised — the identified source gained the
minted Zenodo DOIs `10.5281/zenodo.23463945` (3 sites) and `10.5281/zenodo.23463944` (1 site). Both are
**removed** from the TMLR variant: the compiled PDF's own text and metadata contain **0** occurrences of
either, and `0` of `Zenodo`/`5281` (see `strategy/TMLR_SUBMISSION.md`, UTMLR6 section). The cautious
reading in Q2 is the one applied.
