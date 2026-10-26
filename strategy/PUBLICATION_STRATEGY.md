# PUBLICATION_STRATEGY — getting the Duval / Consonance corpus publicly viewable, peer-reviewable and citable, at minimum cost and friction, for an O-1 petition

**Unit:** UV1 · **Written:** 2026-10-14 · **Target repo:** `/home/zer0null/Duval` (read-only; verified read-only, see §10)
**Grounding:** [`strategy/PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) (710 lines, 2026-10-11) — its ranking and its recommended sequencing (**#3 first, #1 second, #4 third**) are taken as the input and are not re-argued here. **[marked 2026-10-15 by UWITH1 per UVER6 5.1: §13.1 voids the #1 step, and #1 is in any case already public — `findings/PAPER-DERIVATION.md`, MIT, ≤ 2026-10-10, byte-identical sha256 `d98c4359…`. See §13.6.]**
**Purpose (one):** how to get this research publicly viewable, peer-reviewable and citable at minimum cost and friction, as a costed ordered plan.

**Honesty rules applied.** Every load-bearing claim below carries **URL + page date + a short verbatim excerpt**, mirroring the corpus's own
[`EXTERNAL_EVIDENCE`](../../Duval/docs/research/EXTERNAL_EVIDENCE_2026-10-07.md) format. Anything I could not verify from a primary source is
marked `UNVERIFIED` inline and collected in §9. **No fee, deadline or policy below is guessed.** Where a page does not state a fee, I say
"no fee is stated on the pages checked" — a verifiable negative — rather than "it is free".

---

## 0. Bottom line (the recommended cheapest credible route)

**Do not choose between arXiv, a workshop and TMLR. Do all three in a fixed order, because they cost $0 in fees and satisfy different things.**

| Step | Action | Cash cost | Wall time | What it buys |
|---|---|---|---|---|
| **0** | Tag a release of the repo, mint a **Zenodo DOI**, put the DOI in `CITATION.cff`, post **#3 to arXiv** | **$0** | ~1 week | A citable artifact with a DOI, a date, and an author line. **Authorship criterion (B)(6) is met on its own terms from this moment.** |
| **1** | Submit **#3 to TMLR** | **$0** (no fee stated) | ~9 weeks to decision | A real peer-reviewed journal record, ISSN 2835-8856, reviews public on OpenReview. |
| **2** | Post **#1 to arXiv**, then submit **#1 to TMLR** | **$0** | ~1 week + ~9 weeks | The umbrella paper that makes the corpus one citable body of work. |
| **3** | Submit **#4 to an ICLR 2027 workshop** (contribution deadline ≈ **1 Feb 2027**; verdict **26 Feb 2027**) | **$0** to submit; **registration `UNVERIFIED`** if attending | ~2–4 weeks review | Peer-reviewed, **public on OpenReview whether or not you attend**, in exactly the self-refinement audience the O-1 claim needs. |
| **4** | Offer **JOSS** the *software* artifact — **earliest 2027-03-29**, and only if the repository has been publicly available since 2026-09-28 — a premise that is itself `UNVERIFIED` (§11.10) `[corrected by UFIX2 per UCAP1/UVER1]` | **$0** | months | A peer-reviewed software paper + Crossref DOI for Consonance itself. Blocked today (see §5). |

**The single most important correction to a common assumption: publication is not an O-1 criterion — authorship is, and authorship is only
one of eight criteria of which three are needed, and satisfying any criterion does not by itself establish extraordinary ability.** §4 does
this precisely, with the regulation and the USCIS Policy Manual quoted.

**The cheapest decisive move is Step 0, and it costs nothing.** arXiv assigns a DOI to every submission automatically at no cost
(§3.1), so "publicly viewable + citable" is achievable this week; peer review is a separate, equally-free, slower layer.

---

## 1. Where the corpus stands, factually (measured locally, read-only, 2026-10-14)

| Fact | Measured value | Command / source |
|---|---|---|
| Repo commits | **857**, not a shallow clone | `git -C /home/zer0null/Duval rev-list --count HEAD` = `857`; `.git/shallow` absent |
| Earliest commit | **2026-09-28** (`dae60e0` "Initial commit: DUVAL M0 …") | `git log --reverse --format='%ad %h %s' --date=short \| head -3` |
| Head commit | 2026-10-14 (`24f339c`) | `git log -1 --format='%H %ad %s' --date=short` |
| **Public development history** | **≈2.5 weeks** | derived from the two rows above — **this is the binding constraint on JOSS** (§5) |
| Tags | one: `m0-baseline` | `git tag` |
| `CITATION.cff` | present, 973 B, `cff-version: 1.2.0`, `type: software`, `license: AGPL-3.0`, `version: "0.0.1"`, `repository-code: "https://github.com/Aswin-Ram-K/Consonance"`, **no `doi:` field** | `cat /home/zer0null/Duval/CITATION.cff` |
| `LICENSE` | **AGPL-3.0** (OSI-approved) | `head -3 /home/zer0null/Duval/LICENSE` |
| Shared fixture | `evals/fixtures/reflex-decisions.ts` — **145,031 B, 2,220 lines, 191 `id:` matches** (190 case ids + the `DecisionCase` interface field declaration `id: string;` at line 63 — the one `id:` match that is not a case id, and the first by line order; there is no container id), consistent with the "190-case fixture" of `PAPER_CANDIDATES.md` | `wc -l`; `grep -c "id:"`; line-order check, UFIX4, 2026-10-15 **[corrected by UFIX4 per UVER3]** |
| Published artifacts | **No DOI, no arXiv id, no proceedings entry anywhere in the corpus.** **Publicly disclosed: yes** — `github.com/Aswin-Ram-K/publish-present-compete` (**public**, **MIT**, last commit **2026-10-10**) carries the whitepaper, the decision log, 15 pre-registrations and `findings/PAPER-DERIVATION.md` **byte-identical** (46,636 B; sha256 `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`) to `docs/research/PAPER_DERIVATION.md`; the public profile README states the thesis (public ≤ 2026-10-08). `[corrected by UWITH1 per UVER6 C3, 2026-10-15 — the row was true as to arXiv/DOI only, and is the row every later unit quoted; see §13.6]` | `PAPER_CANDIDATES.md` §F.6 stands only as to arXiv/DOI/proceedings. Disclosure: [`PRIOR_DISCLOSURE_AUDIT.md`](PRIOR_DISCLOSURE_AUDIT.md) §1–§2; [`WITHHELD.md`](WITHHELD.md) §8.1 |

**Read-out:** the corpus's *friction* problem is not quality, it is that **nothing has a date-stamped public address.** One arXiv posting and
one Zenodo DOI convert the whole thing from "private research" to "citable record". Both are free.

---

## 2. Venue comparison table

Cost column convention: **stated fee** = quoted from the venue's own page; **no fee stated** = I read the venue's home/FAQ/author/submission
pages on 2026-10-14 and no fee is mentioned anywhere (a verifiable negative, not a promise); `UNVERIFIED` = I could not confirm.

| Venue | Peer-reviewed? | Cost | Review model | Typical time to decision | Prestige / fit for this corpus |
|---|---|---|---|---|---|
| **arXiv** (cs.AI / cs.SE / cs.PL / cs.LG) | **No** — explicitly not | **$0** (DOI minted free) | Moderated for scope/quality, not refereed | QA **1–4 days**, then next announcement slot | Not prestigious by itself, but **universally citable** and the prerequisite for TMLR/Google-Scholar visibility. Best for #3, #1, #4 all at once. |
| **TMLR** (Transactions on ML Research) | **Yes** — journal, ISSN 2835-8856 | **no fee stated** on Home / FAQ / Submissions / Author guidelines (checked 2026-10-14) | Double-blind, ≥3 reviewers, one open discussion phase (2–4 weeks), rolling | **"approximately 9 weeks after submission"** | **Best value in ML.** "emphasizes technical correctness over subjective significance … topics that may not yet be accepted in mainstream venues". Exactly the framing #1 and #3 need. **Not open to surveys** since 2026-09-01. |
| **JOSS** (J. Open Source Software) | **Yes** — journal, ISSN 2475-9066 | **$0** — "no fees for submitting or publishing" | Editor + ≥2 reviewers, conversational, public GitHub review thread | weeks–months; author-sla 2 weeks to respond, 4–6 weeks to revise | For the **software**, not the papers: "Your paper must not focus on new research results accomplished with the software." **Blocked today** by the 6-month history gate (§5). |
| **JAIR** | **Yes** — journal | **$0** — "no publication fees are charged to authors" | Refereed; survey articles get their own track | **"approximately three months of submission"** | Second-best free journal; slower than TMLR and a higher bar on broad significance. A credible *fallback* if TMLR rejects #1. |
| **ICLR 2027 workshops** | **Yes at the workshop level** (organiser-run review) | **$0 to submit and to be published on OpenReview**; conference **registration `UNVERIFIED`** | Workshop-specific, usually 2–3 reviewers | Contributions ≈1 Feb 2027 → verdict 26 Feb 2027 | The realistic **2027** workshop target. Accepted papers must be **made public on OpenReview**. Right audience for #4. |
| **NeurIPS 2026 workshops** | Yes | $0 to submit | as above | **Already closed**: proposal deadline 2026-06-06, contribution date 2026-08-29, notification 2026-09-29 | Not available. Note for the record only. |
| **MLSys 2027** | Yes — conference (PMLR proceedings) | proceedings free; **registration `UNVERIFIED`** | Full conference review, ≥3 reviewers | submissions open 2026-10-19, **deadline 2026-10-30 12:00 PDT** | **Imminent but a full conference**: #1 as a *systems* paper is the corpus's own stated stretch (§6.4 "one kernel, one project, no external system"). Do not spend the window on a blanket paper. **[marked 2026-10-15 by UWITH1 per UVER6 5.1: *"unless #1 is already assembled"* is moot — #1 is already public (`findings/PAPER-DERIVATION.md`, MIT, ≤ 2026-10-10, §13.6) and §13.1 removes it from the plan; read this row as about an extracted-project paper, per §13.4's own note.]** |
| **AAAI-27 workshops** | Yes at workshop level | `UNVERIFIED` | workshop-specific | AAAI-27 is 2027-02-16→23; camera-ready for main track 2026-12-14 | Viable alternative to ICLR workshops; I could not load a primary workshops CFP (`aaai-27-workshops/` returned HTTP 404) → **`UNVERIFIED`**, do not plan against it without checking. |
| **ICLR Blogposts 2027** | **No** — editorial, non-archival | $0 | Editor-selected | n/a | The ICLR 2027 page currently says "**This document is not yet available for 2027/**". Treat as unavailable until the CFP appears. |
| **Distill** | was peer-reviewed | — | — | — | **Dead venue.** "After five years, Distill will be taking a break." (2021-03-04). Do not plan against it. |
| **OpenReview (non-archival workshop hosting)** | venue-dependent | **$0** to post; organised by hosts | public reviews/comments | n/a | The *substrate* by which TMLR and ICLR workshops become public and citable. Not itself a venue. |
| **SSRN** | No | no fee stated | screening, not refereed | days | Elsevier-run; not a scholarly-article venue under the USCIS test's "normally peer-reviewed" language. Skip. |
| **Preprints.org** | No | **"free preprint server supported by MDPI"** | screening | days | Redundant with arXiv. Use only if arXiv endorsement is delayed. |
| **HAL / TechRxiv / OSF Preprints** | No | no fee stated (`UNVERIFIED` for each; TechRxiv returned HTTP 403 to my fetch) | screening | days | All three are **fallbacks if arXiv endorsement fails**. OSF and HAL each mint a DOI; TechRxiv's DOI is `UNVERIFIED`. |
| **Zenodo** | No (repository, not a venue) | **no fee stated** on Get-started / Principles / Policies / About (checked 2026-10-14) → `UNVERIFIED` for "$0", but **no fee is documented** | none (scope/violation policy only) | minutes | **The DOI layer.** Mints a DOI per record/version; DOI revoked only on policy violation. Standard route: GitHub release → Zenodo → DOI into `CITATION.cff`. |
| **Software Heritage** | No | no fee stated | none | minutes–days | Permanent, content-addressed **SWHID**; the identifier is **ISO/IEC 18670** (standardised 2025-04-23). Use as the *third* citation handle on a software release, alongside the Zenodo DOI. |

### 2.1 Does a workshop paper count as peer-reviewed?
This is the question an O-1 officer or attorney will actually ask, and USCIS has answered it in text — see §4, quotation **C6-c** (footnote 33):
presentations that are peer reviewed *and published* may qualify as scholarly articles; presentations that never result in publication are not
automatically disqualified either, because the criterion's own evidence list includes "Published conference presentations at nationally or
internationally recognized conferences". **The operative distinction is `published`, not `workshop vs journal`** — which is exactly why the
ICLR 2027 rule that accepted papers *must* be posted to OpenReview matters.

---

## 3. DOI and archival mechanics (so the work is citable regardless of venue)

### 3.1 arXiv gives a DOI for free — this is the load-bearing fact
> "All articles submitted to arXiv are automatically assigned DOIs that correspond to their arXiv ID, and the associated article metadata
> is submitted to DataCite **at no cost to the authors**."
> — <https://info.arxiv.org/help/doi.html>, fetched 2026-10-14

> "An author can determine their article's DOI by using the DOI prefix `https://doi.org/10.48550/` followed by the arXiv ID (replacing the
> colon with a period)." — same page

**Consequence:** a preprint posted on arXiv is *already* DOI-bearing, DataCite-registered and citable by `https://doi.org/10.48550/arXiv.NNNN.NNNNN`.
There is no reason for this corpus to be uncitable for even one more week.

### 3.2 The ordering that avoids duplicate-DOI confusion
Zenodo will invalidate its own DOI if a record already carries an external DOI:
> "content found to already have an external DOI will have the Zenodo DOI invalidated and the record updated to indicate the original external DOI"
> — <https://about.zenodo.org/policies/>, fetched 2026-10-14

So: **Zenodo first for the software/data record** (which has no other DOI), and let **arXiv own the paper DOI**. Do not mint a Zenodo DOI for
a PDF that is already on arXiv.

### 3.3 `CITATION.cff` gap, measured
`/home/zer0null/Duval/CITATION.cff` is `cff-version: 1.2.0`, `type: software`, `version: "0.0.1"`, `license: AGPL-3.0` and **has no `doi:`
and no `preferred-citation:`**. Two edits fix every paper/software citation path: add `doi:` once Zenodo issues one, and add a
`preferred-citation` for the umbrella paper (#1) once it has an arXiv id.

### 3.4 GitHub release mechanics
Tag a release (`git tag -a`) → Zenodo's GitHub integration archives it and mints a DOI → paste the DOI into `CITATION.cff` and the README's
cite block → the repo becomes citable at a fixed version. `AGPL-3.0` is OSI-approved, so it satisfies JOSS's licence gate (§5) and does not
block preprint posting. Note the trade-off honestly: AGPL-3.0 discourages some corporate reuse, which *may* slow the "external adopters"
signal JOSS asks for — worth one deliberate thought before the first release, and worth stating to any attorney.

---

## 4. The O-1 criterion mapping (precise, honest, verbatim)

**The test.** 8 CFR 214.2(o)(3) requires either one major internationally recognized award, **or at least three of eight** forms of documentation,
**and then** a separate final determination that the person has sustained national or international acclaim at the very top of the field.

> "(A) Receipt of a major, internationally recognized award, such as the Nobel Prize; or (B) **At least three** of the following forms of documentation:"
> — 8 CFR 214.2(o)(3)(iii)(A)–(B), eCFR title 8 **up to date as of 10/13/2026**, fetched 2026-10-14, <https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/section-214.2>

> "Extraordinary ability in the field of science, education, business, or athletics means a level of expertise indicating that the person is
> **one of the small percentage who have arisen to the very top of the field of endeavor**."
> — 8 CFR 214.2(o)(2), same page, same date

**The correction the plan depends on.** USCIS Policy Manual, Vol. 2, Part M, Ch. 4, fetched 2026-10-14,
<https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4>:

> **C6-a** "authorship of scholarly articles in the field in professional journals or other major media, **alone, regardless of caliber, would
> satisfy the criterion** at 8 CFR 214.2(o)(3)(iii)(B)(6). **Analysis of whether those publications are consistent with a finding that the
> beneficiary has sustained acclaim and is among the small [percentage]…**"

> **C5-a** "**Evidence that the beneficiary's work was funded, patented, or published, while potentially demonstrating the work's originality,
> will not necessarily establish** [major significance]…"

**So, stated plainly and in the plan's own voice:** *publication is not a criterion; authorship is one criterion of eight; and winning the
paper lottery does not, by itself, prove "original contributions of major significance".* What converts a paper into O-1 evidence is
**independent citations, third-party expert attestation, and adoption** — which is why §7 (the second labeller) is a publication strategy
input, not a side quest, and why every artifact must be maximally *discoverable and quotable* rather than merely *accepted*.

### 4.1 All eight criteria, mapped to this corpus

| # | Criterion (8 CFR 214.2(o)(3)(iii)(B)) | Reachable from this corpus? | Exactly how, and what is missing |
|---|---|---|---|
| **(1)** | Receipt of nationally or internationally recognized prizes or awards for excellence in the field of endeavor | **Plausible — target it deliberately** | USCIS glosses it as "a **lesser** nationally or internationally recognized prize or award" and lists "**Certain awards recognizing presentations at nationally or internationally recognized conferences**" as acceptable evidence (C1-a). **Actionable:** submit #3/#4 to venues that give **best-paper / outstanding-paper awards**, and keep the award certificate + the awarding body's public announcement. `UNVERIFIED` whether any specific 2026–27 workshop offers such an award — check each CFP. |
| **(2)** | Membership in associations requiring outstanding achievements of members, judged by recognized experts | **No** — nothing in the corpus | Not reachable from publication. Needs a society fellowship route (USCIS explicitly cites IEEE Fellow and AAAI Fellow programmes). Multi-year. Do not count on it. |
| **(3)** | Published material in professional/major trade publications or major media **about the alien** | **No** | Requires press coverage *about* the person. USCIS: "published material that includes only a brief citation or passing reference … is not 'about' the beneficiary." Not produced by publishing papers. |
| **(4)** | Participation as a judge of the work of others | **Reachable, slowly** | "Peer reviewer for scholarly publications" counts, but USCIS requires evidence the review was **actually completed**, not merely invited. Realistic path: become a TMLR reviewer or a workshop programme-committee member *after* the first acceptance. 12–18 month horizon. Timestamp every completed review. |
| **(5)** | **Original scientific, scholarly, or business-related contributions of major significance in the field** | **This is the flagship claim — and it needs citations, not a PDF** | USCIS's own examples include "Documentation that the beneficiary's original work was **cited at a level indicative of major significance**" and "Contributions to repositories of software, data, designs, protocols … with evidence of significant scientific … impact" (C5-a). #4 is the corpus's designated flagship for this (PAPER_CANDIDATES §E). **Missing:** independent citations and ≥2 expert letters describing the specific contribution and the basis of the writer's expertise. **Explicitly not satisfied by the act of publishing (C5-a).** |
| **(6)** | **Authorship of scholarly articles in the field, in professional journals, or other major media** | **Yes — met by Step 0 alone, on USCIS's own words** | Evidence list: "Publications in professionally-relevant journals; and **Published conference presentations at nationally or internationally recognized conferences**" (C6-b). Consideration: "the articles must be scholarly … **The article is normally peer-reviewed**" (C6-c). **Honest reading:** an arXiv preprint satisfies "authored a scholarly article" and satisfies the *criterion* (C6-a), but the "normally peer-reviewed" sentence means a **TMLR acceptance is materially stronger**; and no citation evidence is required *for the criterion* (C6-a), only for the final merits. |
| **(7)** | Employment in a critical or essential capacity for distinguished organizations | **No** — nothing in the corpus | Not reachable from publishing. |
| **(8)** | High salary / remuneration | **No** — nothing in the corpus | Not reachable from publishing. USCIS requires comparative wage data for the locality. |

**Count of criteria realistically reachable from this publication programme: 3** — **(B)(6) authorship** (immediate, free), **(B)(5) original
contributions** (the #4 flagship, once cited), and **(B)(1) prizes/awards** (if a best-paper award is deliberately hunted). That is exactly the
**"at least three"** the regulation requires — *and no more*. The plan must therefore protect all three rather than assume a fourth will
materialise. **(B)(4)** judging is the fourth if the timeline stretches to 18 months.

**What must NOT be claimed.** That a preprint is peer review; that a workshop acceptance is a "major award"; that the number of papers
substitutes for citations. The petition's strength is honesty plus a control-stratum result the literature lacks
(PAPER_CANDIDATES §E: two "no external match found" results) — which is a **(B)(5)** argument carried by **(B)(6)** evidence.

---

## 5. JOSS — why it is blocked today, and the exact unblock date

JOSS is free and legitimate, and it is the right home for the *Consonance* software. It is **not** available this quarter:

> "The repository must have been public for **more than six months** prior to submission, with active development spanning that period. A
> repository made public immediately before submission, or one showing development concentrated into a few days or weeks, will not be accepted."
> — <https://joss.readthedocs.io/en/latest/submitting.html>, fetched 2026-10-14

> "There **must be evidence that the software is being used for research** — at minimum by the developers themselves, and ideally by others …
> **Aspirational statements about future use are not sufficient**." — same page

> "Your paper **must not focus on new research results** accomplished with the software." — same page

Measured history is **2026-09-28 → 2026-10-14** (§1). The six-month gate therefore cannot clear before **2027-03-29**, and only if the
repository has been publicly available since 2026-09-28 — a premise that is itself `UNVERIFIED` (§11.10); if public availability began later,
the gate clears later. `[corrected by UCAP1 per UVER1]` And even then the research-use gate must be met by **references in the corpus's own
published papers** — which is a *second* reason to post #3/#1/#4 first, since
each arXiv posting/acceptance is itself admissible "reference in a published paper/preprint" evidence for JOSS.

> "There are **no fees** for submitting or publishing in JOSS." — same page
> "Upon acceptance into JOSS, a **Crossref DOI** is minted" — <https://joss.theoj.org/about>, fetched 2026-10-14

---

## 6. Costed, month-by-month timeline (#3 → #1 → #4), 2026-10 → 2027-07

Assumed author-side costs are **zero** except where marked. Reviewer/registration fees are marked `UNVERIFIED` rather than guessed.
Today = **2026-10-14**.

| Month | #3 (encoder head vs fine-tuned 4B) | #1 (derivation umbrella) | #4 (self-refinement degradation) | Cash |
|---|---|---|---|---|
| **Oct 2026 (wk 1)** | Finish the paper; **post to arXiv** (needs endorsement, §8); fix the primary-baseline declaration (PAPER_CANDIDATES A3 gap 4) | Start assembly: §6.4 scoping paragraph front-and-centre; Method-first framing | Draft the paired-MDE correction as §1, not a footnote | **$0** |
| **Oct 2026 (wk 2)** | Release tag + **Zenodo DOI** → into `CITATION.cff`; submit **TMLR** | Post #1 to arXiv (second arXiv submission = no new endorsement needed in the same category) | Identify an ICLR 2027 workshop whose CFP matches; read its own deadline | **$0** |
| **Nov 2026** | Respond to TMLR reviewers within 2 weeks of the 3rd review (TMLR asks exactly that) | Submit #1 to TMLR | Commission the **second independent labeller** (§7) — this is the rate-limiting item | $0 + labeller cost §7 |
| **Dec 2026** | TMLR discussion phase (2–4 weeks) | TMLR discussion | Apply the second-labeller results to the fixture; re-run #4's affected arms | — |
| **Jan 2027** | TMLR decision due ≈9 weeks after submission | TMLR decision | **Submit #4 to the ICLR 2027 workshop** (suggested contribution deadline **1 Feb 2027**) | **$0** |
| **Feb 2027** | Camera-ready or resubmit per TMLR | same | Workshop verdict **26 Feb 2027**; accepted papers posted on OpenReview | **$0** (`registration UNVERIFIED` if attending) |
| **Mar 2027** | — | — | **Workshop paper is now publicly citable** → arXiv version with the workshop reference | **$0**; **JOSS gate clears 2027-03-29 at the earliest**, and only if the repository has been publicly available since 2026-09-28 — a premise that is itself `UNVERIFIED` (§11.10) `[corrected by UFIX2 per UCAP1/UVER1]` |
| **Apr 2027** | — | — | Extend #4 → **TMLR** (non-archival workshop version is not "previous publication": TMLR accepts papers with arXiv preprints) | **$0** |
| **May–Jun 2027** | #3 written up as an artifact for the O-1 dossier | #1 becomes the `preferred-citation` in `CITATION.cff` | #4 TMLR decision ≈Jun 2027 | **$0** |
| **Jul 2027** | — | — | **Submit the software to JOSS** (6-month gate cleared, research-use gate met by #3/#1/#4) | **$0** |

**Total cash to reach "publicly viewable + DOI + submitted + reviewed" for all three papers: $0 in venue fees**, plus the §7 labeller line and
any optional workshop registration. **The cheapest credible route is therefore not a compromise — it is the free route, executed in the right
order.**

---

## 7. The second-labeller fix — what it costs and what it unblocks

`PAPER_CANDIDATES.md` §F.3: "Several candidates share one fixture (`evals/fixtures/reflex-decisions.ts`, 190 cases) … **Fixing it is the single
highest return-on-effort action in the corpus.**" The measured size is **190 cases** (§1), so the work is boundable rather than open-ended.

**Quantity (deterministic, no guessing):** 190 cases × 2 independent passes (original + second labeller) = **380 judgements**. At a
conservative **2 minutes per case per pass**, that is **≈12.7 person-hours**. The *quantity* is a fact derived from the measured fixture; the
*price* is not.

**Three ways to buy it, cheapest first:**

| Route | Cash cost | Notes |
|---|---|---|
| **A. An independent expert/co-author labels for free** | **$0** | Strongest for O-1 as well: an independent labeller is also a potential **expert attestation** source under criterion (B)(5). Cost is ~13 h of someone else's time — **budget that as the real cost**, and pay it back with co-authorship or a formal acknowledgement. |
| **B. A second, different LLM family labels the same 190 cases** | token cost only — **`UNVERIFIED`**, because I did not verify a current published per-token price and will not guess one | Mechanically cheap and fast; evidentially **weakest** — USCIS weighs whether attestations come from recognized experts, and a second model is not a third party with standing. Use as a *sensitivity check*, not as *the* fix. |
| **C. A paid annotator (crowd or contractor)** | **= 12.7 h × rate**, where **rate is `UNVERIFIED`** — I could not load a primary recommended-pay page (Prolific's rate article returned HTTP 404 on 2026-10-14) | Needed only if A and B both fail. Get the rate from the platform's live page before committing; do not carry a number into a budget that no primary source supports. |

**What it unblocks (from PAPER_CANDIDATES §A/§B):** #3 (encoder head — "one 190-case fixture, authored by one worker" is its named gap 1),
#4 (self-refinement — "two 4B models, one project's fixture", gap 3), #5 (small decision models) and #10 (a read is not a gate) — **four
candidates**, i.e. every strong candidate's shared weakness. It upgrades #3's and #4's *external validity*, which is the attack a reviewer
actually makes; it does **not** fix #4's statistical power problem (that needs a **third model family, more rounds, and a pre-registered paired
MDE** — PAPER_CANDIDATES §E, "roughly one to two months of compute on the existing estate").

**Cheapest credible sequencing:** run **A** first (it doubles as an O-1 attestation), run **B** in parallel as a free sensitivity arm, and keep
**C** as the fallback. Do it in **Nov 2026** so the results land before the Feb 2027 workshop deadline.

---

## 8. arXiv endorsement — the one real prerequisite, and how to clear it

> "arXiv **requires that users be endorsed** before submitting their first paper to arXiv or a new category."
> — <https://info.arxiv.org/help/endorsement.html>, fetched 2026-10-14 (policy update blog post cited on that page is dated **2026-01-21**)

Two paths, both free:

> "Your account may receive endorsement if: you have **claimed ownership** of a paper submitted by a co-author *and* your email address meets
> the **institutional email criteria**." — same page

> "Alternatively you can seek **personal endorsement** from an established arXiv author … At least **one positive endorsement is required per
> endorsement category**." — same page

**Operational facts that matter:**
- **You can self-check before writing anything else:** start a submission, pick the category, and arXiv emails you an endorsement-request code;
  the abstract page of any related paper has a "**Which authors of this paper are endorsers?**" link. Do this in week 1 — if an endorser is
  needed, that is the plan's long pole, not the writing.
- **What endorsement is not:** "**The endorsement process is not peer review.**" (same page). Nor is moderation: "the arXiv moderation process
  is **not a peer-review process**. arXiv staff and moderators cannot give feedback on the submission."
  (<https://info.arxiv.org/help/moderation/index.html>, fetched 2026-10-14)
- **Turnaround:** "Quality assurance checks can take between **one to four days** to resolve, sometimes longer," and posting happens at the
  fixed announcement slots (submissions Sun–Thu, "no announcements Friday or Saturday").
  (<https://info.arxiv.org/help/availability.html>, fetched 2026-10-14)
- **A real risk to be aware of:** "Submitters who have had works previously delayed or declined by arXiv should anticipate closer scrutiny …
  In some cases, authors may be required to establish a conventional publication record and limit their submissions to works that are published
  in conventional venues." (moderation page) — an argument for arXiv *first*, cleanly, before volume.
- **Category choice:** the corpus spans a systems/methods claim (#1), an empirical ML-selection result (#3) and an LLM-behaviour result (#4).
  Sensible primaries are **cs.AI** (#4), **cs.LG** (#3), and **cs.SE** or **cs.PL** (#1, durable-execution/journaling angle). **[marked 2026-10-15 by UWITH1 per UVER6 5.1: §13.4 leaves §8 standing, but §13.1 removes #1 from the plan — assign this primary to an extracted-project paper, not to #1; see §13.6.]** Whether
  cs.AI / cs.SE / cs.PL / cs.LG are **separate endorsement domains** is **`UNVERIFIED`** — the endorsement page states domains are "most
  high-level subject areas … with the notable exception of physics" but does not enumerate the cs domains. **Treat each intended primary
  category as potentially requiring its own endorsement** and find out at submission time; do not assume one endorsement covers all three.
  Cross-listing is free but **requires the primary category first**, and should be used sparingly.

---

## 9. Explicit comparison: (a) arXiv+DOI now, (b) workshop, (c) TMLR/JOSS

| | **(a) arXiv preprint + DOI now** | **(b) Workshop submission** | **(c) TMLR** | **(c′) JOSS** |
|---|---|---|---|---|
| Publicly viewable | **Yes, within ~1–4 days + the next announcement slot** | Yes, at the mandated OpenReview posting (26 Feb 2027 for ICLR 2027) | Reviews public immediately on OpenReview; paper on acceptance | On acceptance |
| Citable with a DOI | **Yes — `10.48550/arXiv.<id>`, free, automatic** | OpenReview id; **arXiv/DOI needs a separate posting** | journal DOI | **Crossref DOI, free** |
| Peer-reviewed | **No** (and arXiv says so) | **Yes** | **Yes** | **Yes** |
| Cash cost | **$0** | **$0** to submit/publish; registration `UNVERIFIED` | **$0** (no fee stated) | **$0** |
| Time to a decision | days | ~2–4 weeks after the Feb 2027 deadline | **~9 weeks** | weeks–months |
| Best for | **#3, #4, and the other extracted-project papers, immediately — #1 is not a target** (§13.1; #1 is already public, §13.6) | **#4** (the audience that cites self-refinement work; and the best-paper-award hunt for criterion (B)(1)) | **#3 and the other extracted-project papers** (correctness over subjective significance) | the **software**, from 2027-03-29 at the earliest, and only if the repository has been publicly available since 2026-09-28 — a premise that is itself `UNVERIFIED` (§11.10) `[corrected by UFIX2 per UCAP1/UVER1]` |
| Strength for O-1 | Meets **(B)(6)** authorship on USCIS's own reading, and gives a **date-stamped public address** for every other claim | Adds a **published, peer-reviewed presentation** (C6-b) and a shot at **(B)(1)** via a best-paper award; **fast** | The strongest evidence for **(B)(6)** ("normally peer-reviewed") and the citation record **(B)(5)** needs | Evidence of a **contributions to repositories … with significant impact** (C5-a) |

### Recommendation
**Execute in the order 0 → 1 → 2 → 3 → 4 of §0, i.e. (a) *this week*, then (c) TMLR for #3 and the other extracted-project papers, then (b) an ICLR 2027 workshop for #4, then
(c′) JOSS for the software.** `[corrected 2026-10-15 by UWITH1 per UVER6 5.1: this execute-list carried #1 as a live TMLR target; §13.1 removes #1 from the plan, and it is already public in any case — see §13.6.]` Reasons, in order of force:

1. **(a) is free, immediate and irreversible-in-the-good-direction.** It converts 710 lines of ranked strategy into a DOI-bearing public
   record while the endorsement question is still open; nothing else in this plan can be *blocked by* it (TMLR explicitly accepts arXiv
   preprints: "You can still submit, even if a preprint of your work already is available online", TMLR FAQ, fetched 2026-10-14).
2. **(c) TMLR is the highest-expected-value peer review for this corpus:** free, ~9 weeks, and its stated remit — "technical correctness over
   subjective significance … topics that may not yet be accepted in mainstream venues" — is a precise match for pre-registered, control-heavy,
   single-fixture results. It also directly strengthens the "normally peer-reviewed" sentence in criterion (B)(6).
3. **(b) the workshop is not a substitute for (c); it is a *second* criterion.** It is where #4's citations will come from, it is free, it
   publishes publicly, and it is the only realistic shot at **(B)(1)** if a best-paper award exists. Its Feb 2027 deadline also imposes a
   healthy date on the second-labeller work.
4. **(c′) JOSS is deliberately last** because it is *gated* (6 months' history + demonstrated research use), and because its own scope rule —
   "must not focus on new research results" — means it complements the papers rather than competing with them.

**Explicitly rejected:** waiting for a main-conference acceptance before posting anything (PAPER_CANDIDATES §A1/§A4 both say a main venue needs
new experiments — waiting risks publishing nothing); NeurIPS 2026 workshops (closed); Distill (dead since 2021-03-04); a paid APC venue (none
is needed to satisfy the criteria).

---

## 10. "Do this next week" checklist (2026-10-14 → 2026-10-21)

1. **Start an arXiv submission for #3** in the intended primary category. This does two things at once: it triggers the endorsement request if
   one is needed (§8, the long pole), and it forces the primary-baseline declaration that PAPER_CANDIDATES §A3 gap 4 says must be settled.
   Use an institutional email if you have one — it can remove the endorser requirement entirely.
2. **If an endorser is needed:** open `SELF_REFINEMENT_DEGRADATION_2026.md` §2–§7, take the papers already cited there (Huang et al. ICLR 2024,
   Stechly et al., CriticGPT, Valmeekam, CriticBench, Xiong et al.), find them on arXiv, and use "Which authors of this paper are endorsers?"
   to identify **one** qualified endorser you can approach honestly, with the paper attached. Do not mass-email.
3. **Cut the first GitHub release and mint the Zenodo DOI**; add `doi:` to `CITATION.cff`. Remove the `UNVERIFIED` on the "$0" by reading the
   Zenodo upload page's own summary at the moment of deposit.
4. **Recruit the second independent labeller** (§7 route A, or B in parallel). 190 cases, ~13 person-hours of work. This is the corpus's own
   highest-return fix and it is cheaper than any APC.
5. **Fix #3's declared primary baseline** to the same-run 0.6789 (PAPER_CANDIDATES §A3 gap 4) and put the paired McNemar result
   (b=27, c=90, Δ=−0.3316, exact p=4.167e−09, paired MDE 0.1595) and **both** controls in the abstract.
6. **Check MLSys 2027 and the ICLR 2027 workshop list before writing anything longer** — the MLSys window (open 2026-10-19, close 2026-10-30)
   is the only imminent deadline; decide explicitly whether #1 is assembled enough to justify it, and record the decision either way.
7. **Read each chosen venue's registration page and record the number** rather than leaving it `UNVERIFIED` — it is the only un-costed line
   in §6.
8. **Write down the O-1 evidence chain now** (§4): for each of (B)(1), (B)(5), (B)(6), name the artifact, its DOI/URL, the date, and the
   *independent* corroboration (citation, expert letter, award announcement). A missing corroboration is a task, not an oversight.

---

## 11. `UNVERIFIED` list (asserted nowhere above as fact)

1. **Zenodo's price.** No fee is stated on Get-started, Principles, Policies or About (checked 2026-10-14); I did **not** find an explicit
   "free of charge" sentence, so "$0" is **`UNVERIFIED`** even though no fee is documented.
2. **TMLR's price.** No fee appears on Home, FAQ, Submissions or Author Guidelines (checked 2026-10-14) — a verifiable negative. I did not find
   an affirmative "no APC" sentence either, so it is **`UNVERIFIED`** in the affirmative direction.
3. **Workshop / conference registration costs** for ICLR 2027, MLSys 2027 and AAAI-27. Not loaded from any primary page →
   **`UNVERIFIED`**, and the only un-costed line in the §6 timeline.
4. **arXiv endorsement domains for cs.\*.** The endorsement page does not enumerate them; whether cs.AI / cs.SE / cs.PL / cs.LG are one domain
   or four is **`UNVERIFIED`**. Assume four until checked at submission time.
5. **MLSys 2027 deadlines** were read from the mlsys.org homepage ("Paper Submissions Open Oct 19 '26 … Paper Submission Deadline Oct 30 '26
   12:00 PM PDT", fetched 2026-10-14). Whether those dates belong to MLSys 2027's main track or a co-located event is **`UNVERIFIED`** — the
   same page also says only that "Planning for MLSys 2027 is underway."
6. **AAAI-27 workshops.** `aaai.org/conference/aaai/aaai-27/aaai-27-workshops/` returned **HTTP 404** on 2026-10-14, so no AAAI workshop
   deadline is asserted. **`UNVERIFIED`**.
7. **ICLR 2027 Blogposts.** The official page states "This document is not yet available for 2027/" → no 2027 policy or dates.
   **`UNVERIFIED`**.
8. **OSF Preprints, HAL, TechRxiv, SSRN pricing and DOI behaviour.** The help/FAQ pages I could load did not state fees or DOI mechanics;
   TechRxiv returned **HTTP 403**. All **`UNVERIFIED`**. Treat them as fallbacks only if arXiv endorsement fails, and confirm at use.
9. **Second-labeller price.** The quantity (380 judgements ≈ **12.7 person-hours**) is derived from the measured 190-case fixture and is solid;
   the **hourly rate is `UNVERIFIED`** (the Prolific recommended-pay article 404'd on 2026-10-14). Do not budget a currency figure from this
   document.
10. **Whether the `/home/zer0null/Duval` repository is publicly visible right now.** `CITATION.cff` names
    `https://github.com/Aswin-Ram-K/Consonance`; I did **not** fetch it, so its public status is **`UNVERIFIED`** — and JOSS's six-month clock
    runs from *public* availability, not from the first commit.
11. **Whether any specific 2026–27 venue offers a best-paper award** usable under criterion (B)(1). **`UNVERIFIED`** — check each CFP; this is
    the one path to a third criterion that does not depend on citations accumulating.
12. **arXiv's licence options and their effect on TMLR/JOSS reuse.** Licence choice was not researched in this unit; **`UNVERIFIED`**.
13. **`PAPER_CANDIDATES.md`'s new-in-2026 claim that TMLR "no longer considers survey papers"** *is* verified ("As of September 1, 2026, TMLR
    no longer considers survey papers for review", TMLR FAQ, fetched 2026-10-14) — recorded here because it rules out #13/#14 as TMLR targets.

---

## 12. Source ledger (URL · page date · verbatim excerpt)

| # | Source | Page date | Verbatim excerpt used |
|---|---|---|---|
| S1 | <https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/section-214.2> | title 8 "up to date as of **10/13/2026**" | "(B) At least three of the following forms of documentation: … (5) Evidence of the alien's original scientific, scholarly, or business-related contributions of major significance in the field; (6) Evidence of the alien's authorship of scholarly articles in the field, in professional journals, or other major media" |
| S2 | same | same | "Extraordinary ability in the field of science, education, business, or athletics means a level of expertise indicating that the person is **one of the small percentage who have arisen to the very top of the field of endeavor**." |
| S3 | <https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4> | fetched **2026-10-14** (page shows no "last reviewed" stamp in the fetched HTML → **`UNVERIFIED`** date) | "authorship of scholarly articles in the field in professional journals or other major media, **alone, regardless of caliber, would satisfy the criterion** at 8 CFR 214.2(o)(3)(iii)(B)(6)" |
| S4 | same | same | "Examples of relevant evidence may include … Publications in professionally-relevant journals; and **Published conference presentations at nationally or internationally recognized conferences**." |
| S5 | same | same | "the articles must be scholarly … **The article is normally peer-reviewed.**" |
| S6 | same | same | "**While many articles accepted for presentation at conferences do not result in publication, there are conferences that peer review and publish accepted presentations in professional journals (sometimes called proceedings), such that they may qualify as scholarly articles under this criterion.**" (footnote to criterion 6) |
| S7 | same | same | "**Evidence that the beneficiary's work was funded, patented, or published, while potentially demonstrating the work's originality, will not necessarily establish** [major significance]" |
| S8 | same | same | criterion 1: "USCIS determines whether the award is a **lesser** nationally or internationally recognized prize or award … **Certain awards recognizing presentations at nationally or internationally recognized conferences**" |
| S9 | <https://info.arxiv.org/help/endorsement.html> | fetched 2026-10-14; page cites a policy-update post dated **2026-01-21** | "arXiv requires that users be endorsed before submitting their first paper to arXiv or a new category."; "**The endorsement process is not peer review.**"; "At least one positive endorsement is required per endorsement category." |
| S10 | <https://info.arxiv.org/help/moderation/index.html> | fetched 2026-10-14 | "the arXiv moderation process is **not a peer-review process**. arXiv staff and moderators cannot give feedback on the submission." |
| S11 | <https://info.arxiv.org/help/availability.html> | fetched 2026-10-14 | "Quality assurance checks can take between **one to four days** to resolve, sometimes longer."; "no announcements Friday or Saturday" |
| S12 | <https://info.arxiv.org/help/doi.html> | fetched 2026-10-14 | "All articles submitted to arXiv are automatically assigned DOIs … submitted to DataCite **at no cost to the authors**."; prefix `https://doi.org/10.48550/` |
| S13 | <https://jmlr.org/tmlr/faq.html> | fetched 2026-10-14 | "the rolling review process aims to deliver a final decision **approximately 9 weeks after submission**"; "As of **September 1, 2026**, TMLR no longer considers survey papers for review."; "You can still submit, even if a preprint of your work already is available online" |
| S14 | <https://jmlr.org/tmlr/> | fetched 2026-10-14 | "TMLR emphasizes **technical correctness over subjective significance** … topics that may not yet be accepted in mainstream venues"; ISSN 2835-8856 |
| S15 | <https://jmlr.org/tmlr/submissions.html>, <https://jmlr.org/tmlr/author-guide.html> | fetched 2026-10-14 | no fee/APC mentioned on either page (**negative** evidence) |
| S16 | <https://joss.readthedocs.io/en/latest/submitting.html> | fetched 2026-10-14 | "**There are no fees** for submitting or publishing in JOSS."; "public for **more than six months** prior to submission"; "There **must be evidence that the software is being used for research**"; "must not focus on new research results" |
| S17 | <https://joss.theoj.org/about> | fetched 2026-10-14 | "a **Crossref DOI** is minted"; "pre-trained machine learning models and notebooks are **not in-scope**" |
| S18 | <https://www.jair.org/index.php/jair/about> | fetched 2026-10-14 | "**no publication fees are charged to authors**"; "JAIR reviews papers within **approximately three months** of submission" |
| S19 | <https://iclr.cc/Conferences/2027/CallForWorkshops> | fetched 2026-10-14 | "Workshop Application Deadline: **9 October 2026**"; "**Suggested Submission Deadline for Workshop Contributions: 1 Feb 2027**"; "**Mandatory Accepted Paper Notification Date: 26 February 2027**"; "make all accepted papers publicly available on OpenReview" |
| S20 | <https://neurips.cc/Conferences/2026/CallForWorkshops> | fetched 2026-10-14 | "Workshop Application Deadline: **June 06, 2026**"; "Suggested Submission Date for Workshop Contributions: **August 29, 2026**" |
| S21 | <https://mlsys.org/> | fetched 2026-10-14 | "Paper Submissions Open **Oct 19 '26** 12:00 PM PDT"; "Paper Submission Deadline **Oct 30 '26** 12:00 PM PDT" |
| S22 | <https://iclr.cc/Conferences/2027/CallForBlogPosts> | fetched 2026-10-14 | "**This document is not yet available for 2027/**" |
| S23 | <https://distill.pub/> | editorial dated **2021-03-04** | "After five years, **Distill will be taking a break**." |
| S24 | <https://about.zenodo.org/policies/> | fetched 2026-10-14 | "content found to already have an external DOI will have the Zenodo DOI invalidated and the record updated to indicate the original external DOI" |
| S25 | <https://www.softwareheritage.org/faq/> | fetched 2026-10-14 | "It became **ISO/IEC international standard 18670 on April 23, 2025**." |
| S26 | <https://www.preprints.org/> footer | fetched 2026-10-14 | "Preprints.org is a **free preprint server supported by MDPI** in Basel, Switzerland." |
| S27 | <https://openreview.net/about> | fetched 2026-10-14 | "OpenReview is a long-term project to advance science through improved peer review with **legal nonprofit status**." |
| S28 | local, read-only: `/home/zer0null/Duval` | measured 2026-10-14 | 857 commits, earliest **2026-09-28**, non-shallow; `CITATION.cff` `cff-version: 1.2.0`, `license: AGPL-3.0`, no `doi:`; `evals/fixtures/reflex-decisions.ts` 145,031 B / 2,220 lines / 191 `id:` matches; one tag `m0-baseline` |

**Target-repo containment:** only read operations were performed on `/home/zer0null/Duval` (`ls`, `cat`, `head`, `wc`, `grep`, `git log`,
`git rev-list`, `git tag`, `ls .git/shallow`). No write, no `git` state change, no hook installed. All writes from this unit are confined to
`strategy/PUBLICATION_STRATEGY.md`, `orchestration/units/UV1.md` and `orchestration/handoffs/UV1.json`.

---

## 13. ERRATA — the publication rule changed, and §0's sequence is void — unit UCAND1, 2026-10-15

**This is an appended errata section, not a rewrite.** §0 stands as written and dated 2026-10-14; where §13
and §0 disagree, **§13 governs**. The author's rule was given on **2026-10-15**, after §0 was written.

> *"dont publish any blanket papers, only small extracted projects that go public and the papers associated
> with it."*

Together with, same session: **no patents; the core Consonance engine is a trade secret; the main repository
stays proprietary; only selected extracted pieces are released (under PolyForm Noncommercial); every
released piece carries its own paper.** The register of what is deliberately withheld is
[`WITHHELD.md`](WITHHELD.md); the candidate-by-candidate re-triage is
[`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G.

### 13.1 §0's sequence is corrected: #3 first, then the other extracted-project papers — and #1 is gone

- **§0 Step 2 is VOID in both of its actions.** *"Post **#1** to arXiv, then submit **#1** to TMLR"* does not
  happen, at any time, in any rewording. Candidate **#1 is `docs/research/PAPER_DERIVATION.md` — a blanket
  paper** (it describes the kernel as a whole and fails the standalone test **[corrected 2026-10-15 by
  UWITH1 per UVER6 O1: *"by its own §6.4 admission"* is dropped — §6.4 is a scope-limitation section, not a
  releasability admission, and its dropped middle sentence cuts the other way. The withhold follows instead
  from contribution 2 at `PAPER_DERIVATION.md:72–76` and the private M13 `tools/**` inventory. See
  §13.6.]**), and
  blanket papers are withheld outright: **not edited, not abstracted, not "fixed".**
- **The sequence is now: #3 first, then the other extracted-project papers.** The re-triage
  ([`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G.1) marks **#2, #3, #4, #5, NC1, #9, #10, #11 and #12** as
  `publish` — nine extracted-project papers, each standing alone. **#6, #7, #8, #13 and #14 are
  `needs-author-decision`** at the author's discretion; **#1 is the sole `withhold`.**
- **#1 is removed from the plan entirely.** It is not deferred, not a later step, and not a hidden fallback:
  no row of §0's table, §6's timeline or §9's comparison may carry it.
- **§0's row 0 is unchanged and still first:** tag a release → Zenodo DOI → `CITATION.cff`
  → **post #3 to arXiv**. §0's row 1 (submit #3 to TMLR) is unchanged. §§0.3–0.4, 1, 2, 5, 7, 8 and 9 are
  unaffected except that every occurrence of "#1" as a target is replaced by the next extracted-project paper.
- **§6's timeline, corrected in place by this errata:** the **Oct-2026-wk2 row** *"Post #1 to arXiv (second
  arXiv submission …)"* is void; the **#1 column** becomes an embedded extracted-project column (a candidate
  from the §G.1 `publish` set, chosen by the author); the **May–Jun 2027 row** *"#1 becomes the
  `preferred-citation` in `CITATION.cff`"* is void.
- **§3.3's `CITATION.cff` gap, corrected:** `preferred-citation` points at **the first released paper (#3)**,
  or at the software's Zenodo record — **never at the umbrella paper**, which has no DOI to point at.

### 13.2 The "one citable body of work" argument is void — and what replaces it

§0's stated purpose for #1 was that it *"makes the corpus one citable body of work"* (echoed in §E of the
inventory and in §9's "Best for" column). **That argument is void**, because the document that would have
carried it is withheld and the argument cannot survive the document.

**What replaces it: each paper stands alone, and citations accrue per paper.** Every released piece has its
own paper, its own artifact (a minimal reproducibility subset — fixture schema, fixture, harness, exact
commands, pre-registered protocols; kernel/runtime and weights withheld — the norm implemented for #3 in
`repro/encoder-crossover-190/`), its own DOI, and its own citation path. **No claim in any released paper
may depend on a corpus-level framing**, because nothing in the citable record supplies one. The practical
consequences for this plan:

- **Venue mapping is per paper, not per corpus.** §9's "(c) TMLR" column named *"#3 and #1"*; it is now
  **#3 and the other extracted-project papers**, each judged on its own correctness-and-significance profile.
- **The JOSS research-use gate (§5) is met by references to the released papers**, exactly as before — the
  gate never depended on the umbrella, only on *"evidence that the software is being used for research"*
  (S16) via *"references in the corpus's own published papers"*. With more standalone papers, that gate is if
  anything easier to meet, not harder.
- **The second-labeller fix (§7) is unchanged** — and its priority rises slightly, because nine standalone
  single-fixture papers carry the same shared-fixture weakness that four did.

### 13.3 The O-1 consequence, stated plainly (not argued)

> **[CORRECTED 2026-10-15 by UWITH1 per UVER6 C2 — the premise sentence below is FALSE. The
> architectural/system claim **is** published, dated ≤ 2026-10-10, authored and citable; the public
> repository is its address. This section's cost framing is void, and the consequence inverts in the
> author's favour. See §13.6(b) and [`WITHHELD.md`](WITHHELD.md) §8.7. The original text stands as the
> record of what was issued; its (B)(6)/(B)(1)/(B)(4) sub-bullets and the per-paper evidence rule survive.]**

**Withholding the blanket paper means the architectural/system claim is never published and cannot be
claimed as a published contribution.** Concretely, the sentence *"we built the loop that couples stream,
derived state, commit, composition and projection under one source of truth"* — and §4.6's *"the moat
survives"*, and §5.5's five-layer rule — disappear from the citable record
([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §3). **What survives is the empirical findings from each
extracted project.** A reader will be able to cite the measurements, not the architecture.

**This is a deliberate cost the author accepted.** It is recorded here as a cost, not as an error and not as
a trade to be re-litigated. Its effect on §4 is narrow but must be honoured in the evidence chain (§10.8):

- **(B)(6) authorship** — unaffected, and now met paper by paper. The first submission is still #3, so the
  arXiv endorsement check (§8) still happens on #3's category and schedule.
- **(B)(5) original contributions** — the flagship is still **#4** (self-refinement degradation; §E), but the
  *basis of the claim* is now unambiguously the **measured finding**, never a systems contribution. No
  expert letter and no petition line may describe the architecture as a published contribution, because it
  is not one — it is a trade secret and is registered as such.
- **(B)(1) prizes / (B)(4) judging** — unaffected; both are paper-level outcomes.
- **The practical rule:** for each of the nine `publish` rows in
  [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G.1, the evidence chain names the **paper**, its **DOI**, its
  **artifact**, and its **independent corroboration** — and cross-checks that the claim the letter-writer
  attests to is a measured finding, not a design.

### 13.4 Explicitly unaffected (verified — kept whole)

| Unaffected item | Where | Why the rule does not touch it |
|---|---|---|
| The venue comparison table (arXiv, TMLR, JOSS, JAIR, ICLR 2027 workshops, MLSys, the dead/fallback venues) | §2 | Venue facts are properties of the venues, not of which paper is submitted; the same table serves #3 and every other extracted-project paper. |
| The $0 route and the free-DOI mechanics | §0 Step 0, §3 | Both are unchanged: arXiv mints the DOI, Zenodo mints the software DOI, and **Zenodo must not be minted for anything arXiv already owns** (§3.2). |
| The JOSS block and its exact unblock date | §5 | The six-month history gate and the research-use gate are untouched; the research-use gate is still met by references, now to the released papers. |
| arXiv endorsement mechanics | §8 | The rule changes *which* paper is first, not *that* a first submission needs endorsement. **#3 is still the first submission**, so §8's "do this in week 1" instruction stands as written. |
| The (a)/(b)/(c)/(c′) comparison and the TMLR conclusion | §9 | TMLR remains the highest-expected-value free peer review ("technical correctness over subjective significance", ~9 weeks). The **only** edit is which papers target it (13.2). |
| The **paper licence** conclusion — papers **CC BY 4.0** | `papers/encoder-crossover-190/AVAILABILITY.md`; `repro/encoder-crossover-190/README.md` | The paper licence is a per-paper decision (author, 2026-10-15) and is unaffected; the *code/artifact* licence is a separate instrument (PolyForm Noncommercial 1.0.0) and the split is deliberate ([`CODE_LICENSING_STRATEGY.md`](CODE_LICENSING_STRATEGY.md) §3.4, §5.1). **CC BY 4.0 for papers does not license the withheld kernel** — W5/W6 stay out. |
| §10's checklist items 2, 3, 4, 5, 7, 8 | §10 | Still valid verbatim; item 4 (the second labeller) is now the shared fix for nine papers rather than four. |

**Also noted, because it changes §10:** checklist item 1 must read *"start an arXiv submission for **#3**"*
(it already does — §10.1 names #3), and checklist item 6's decision about **MLSys 2027** is now made about
an *extracted-project* paper, not about #1. The MLSys window is not a reason to assemble a blanket paper.

### 13.5 What this errata does not do

It does **not** delete or renumber anything. It does **not** rewrite §0, §6 or §9 — it marks them corrected
by §13, per this corpus's append-only-errata norm (`docs/DECISION_LOG.md:3–4`: *"Append-only. … Amendments
are new entries, never edits"*). It does **not** decide the five `needs-author-decision` candidates; those
questions are stated in [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) §G.3.

### 13.6 Errata 2 — the prior-disclosure fact and the O-1 inversion (unit UWITH1, 2026-10-15)

**Appended, not a rewrite.** This section corrects §13.3's premise, carries the corrected §1 `:47` row, and
marks the five residual live `#1` references that §13.1's four named corrections did not cover. Where §13.6
and §§0/13.3 disagree, **§13.6 governs**.

**(a) The fact — the corpus is publicly disclosed, not merely "not yet on arXiv".**
`github.com/Aswin-Ram-K/publish-present-compete` is **public** and **MIT**-licensed (38 commits, last commit
**2026-10-10**); its `findings/PAPER-DERIVATION.md` is **byte-identical** (46,636 B; sha256
`d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`) to
`/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md`; the public profile README (public ≤ 2026-10-08)
states the thesis; `WHITEPAPER.md` and a 339,879 B `decisions/DECISION_LOG.md` are public in the same repo.
Found by UDISC1, re-verified **with a hash on both sides** by UVER6, and re-hashed locally by UWITH1
(2026-10-15). **§1's `:47` row is corrected in place.** Consequently **12 of the 13 mechanisms in
[`WITHHELD.md`](WITHHELD.md) §2 are already public** — M1–M10, M12, M13; M11 is `undetermined` — and the
register is re-issued at its §8.

**(b) §13.3's premise is VOID — the O-1 consequence inverts in the author's favour.** §13.3 opens
*"Withholding the blanket paper means the architectural/system claim is never published and cannot be claimed
as a published contribution."* **That is false.** The claim **is** published, dated (≤ 2026-10-10), authored
and citable — the public repository is its address. So:

- **(B)(5) original contributions** — the flagship is still **#4**, but the argument may now be made **with a
  prior-disclosure date attached**, which is *better* for the petition than the §13.3 text assumed.
  **No expert letter should describe the *code* as published** — the implementation is not — but nothing
  forbids citing the published design.
- **(B)(6) authorship** — unaffected; the paper remains the unit.
- **(B)(1) prizes and (B)(4) judging** — unaffected.
- **What is actually withheld is the implementation**: `src/**`, concrete types, the code-level state-class
  catalogue, private corpora, `tools/**`, unpublished prose ([`WITHHELD.md`](WITHHELD.md) §8.3). §13.3's
  "deliberate cost the author accepted" framing is corrected: it was neither a cost nor deliberate-as-priced.

**(c) The five residual live `#1` references, now marked in place.**

| Line | Marking applied |
|---|---|
| `:4` | Grounding sequence marked superseded — §13.1 voids the #1 step, and #1 is already public. |
| `:67` | MLSys row — *"unless #1 is already assembled"* marked moot; the row is about an extracted-project paper. |
| `:274–275` | §8's cs.SE/cs.PL primary, assigned to #1 — marked for reassignment to an extracted-project paper. |
| `:292` | §9's arXiv "Best for" cell — #1 removed as a target (the TMLR column was already corrected by §13.2). |
| `:296` | §11's execute-list — TMLR for #3 *and the other extracted-project papers*, not #1. |

**The irony, recorded:** #1 is the one candidate this plan withholds — and it is the one document already
public under MIT. The suppression protects nothing, and the public copy is citable today.

**(d) What does not change.** §13.4's explicitly-unaffected set (the venue table, the $0 route, the JOSS
block, arXiv endorsement, the TMLR conclusion, papers CC BY 4.0) is **undisturbed and not edited here**;
UVER6 re-verified it against UVER1/ULIC. The candidate split (**9 `publish` / 1 `withhold` / 5
`needs-author-decision`**) is re-derived and correct and is **not** re-triaged. The code/artifact licence
split (PolyForm Noncommercial 1.0.0 for code, CC BY 4.0 for papers) stands; what the public repo's **MIT**
licence already granted over the **public** material cannot be undone for those versions
([`WITHHELD.md`](WITHHELD.md) §8.6; `UNVERIFIED` as to prose, which needs counsel).
