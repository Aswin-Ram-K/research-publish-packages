# PUBLISH_WITHOUT_ENDORSEMENT.md — can paper #3 be public, dated and citable without an arXiv endorsement?

Unit **UARXIV1**, 2026-10-15. Scope: paper #3 (`papers/encoder-crossover-190/`, the 190-case encoder-crossover
selection result), its author as an **unaffiliated independent researcher** (no institutional email, no academic
position). Every claim below traces to a page fetched during this unit on **2026-10-15 (UTC)** unless explicitly
marked `UNVERIFIED`. This file **does not edit** `PUBLICATION_STRATEGY.md`; corrections to it are recorded in §6
with the line named.

---

## 1. Direct answer

**Conditional `yes`.**

Paper #3 can be made **public, dated, citable and DOI-bearing without any arXiv endorsement** — the routes exist,
are free (or no fee is documented) and admit unaffiliated authors. What endorsement blocks is **arXiv
specifically**, and with it the ML field's default preprint address and Google-Scholar/`cs.LG` visibility.

The condition is on the word *paper*:

- A **DOI-bearing preprint** on an endorsement-free platform is **not peer-reviewed** and must never be described
  as such (arXiv says of its own process: "the arXiv moderation process is not a peer-review process", and
  Preprints.org says of its content: "Content on Preprints.org is not peer-reviewed").
- The **peer-reviewed** path does not need arXiv either. **TMLR does not require an arXiv preprint** — verified
  from TMLR's own author guidance (§3.2, §4). TMLR submission is direct on OpenReview, and the CC BY 4.0
  requirement is confirmed verbatim (§4).
- So the endorsement is **not** the plan's blocking prerequisite. It is an obstacle to *one* channel (arXiv),
  and a real obstacle to *discoverability*, but not to a dated public record.

**Do not conflate the two outcomes.** A preprint gets the author a **date-stamped, DOI-bearing citation handle**;
only a venue gets him a **peer-reviewed publication**. For the O-1 file those are different criteria (§5).

---

## 2. arXiv: endorsement and rate limits, from primary sources

### 2.1 Endorsement — what the current policy actually says

- "arXiv requires that users be endorsed before submitting their first paper to arXiv or a new category."
  — <https://info.arxiv.org/help/endorsement.html>, fetched 2026-10-15.
- Two paths, and **institutional email alone is not one of them**:
  "Your account may receive endorsement if: you have **claimed ownership** of a paper submitted by a co-author
  *and* your email address meets the institutional email criteria." — same page.
- "If you are the submitting author or have claimed papers but do not have an institutional email: you will need
  to update your email address to an institutional email." — same page.
- The policy change is explicit: "As of January 21, 2026, arXiv will no longer accept institutional email
  addresses (i.e., an email address associated with an academic or research institution) as the sole qualifier of
  endorsement for new authors." and "The first path requires **both** 1) an institutional email address from an
  academic/research institution **and** 2) previous authorship on an existing paper which has been accepted to the
  arXiv *'endorsement domain'* they wish to submit to."
  — <https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/>, dated **January 21st 2026**.
- **Every category, not some:** "Endorsement for new submitters in **all categories** will now follow two paths."
  — same blog post.
- **Personal endorsement is the only remaining door for an unaffiliated first-timer:**
  "Alternatively you can seek personal endorsement from an established arXiv author. … At least one positive
  endorsement is required per endorsement category to be considered endorsed for that category."
  — endorsement page. Who may endorse: "Endorsers must have authored a certain number of papers within the
  *endorsement domain* of a subject area. … we only count papers that have been submitted between three months
  and five years ago." — same page. And the endorser's own duty: "You should know the person that you endorse
  **or** you should see the paper that the person intends to submit." — same page.
- **What happens if nobody endorses: the submission cannot proceed, and arXiv will not fix it.**
  "arXiv staff cannot waive endorsement requirements or provide a personal endorsement for authors."
  — the 2026-01-21 blog post.
- **It is not review, and the request code is mechanical:** "The endorsement process is not peer review."
  (endorsement page). The code is a **six-character alphanumeric** string: "If an author asks you for
  endorsement, they will send you a six-character alphanumeric *endorsement code*. After you enter this code on
  the endorsement form, you can tell us that you **do** or **do not** wish to endorse a person." — same page.
  The requester obtains it by starting a new submission: "Start a new submission and select the category you
  wish to submit to. … Check your **email for an endorsement request email**. This will include a link you can
  provide to prospective endorsers." — same page.
- **Anti-spam rule that constrains the approach:** "it is inappropriate to email large numbers of potential
  endorsers at once, or to repeatedly email the same endorser with a request for endorsement." — same page.

**Honest read for this author: difficult, but not impossible.** The first path is closed to him *by construction*:
it requires an institutional email **and** a prior accepted arXiv paper in the same domain. The second path
requires a real human who either knows him or will read the paper — and the endorsement page's own advice ("A good
choice for graduate students would be your thesis advisor…") is written for people who have one. He does not. The
realistic version is cold-approaching one or two authors of papers #3 already cites, with the manuscript attached
(the endorser is permitted to rely on seeing the paper). That is a weeks-to-months, low-probability, non-blocking
side quest — see §7.

### 2.2 Rate limits — confirmed, and rejections count

- "Each author may submit up to **two new submissions per calendar month** with a limit of **three active
  submissions**. For replacements, there is a one per week rate limit after version 5."
  — <https://info.arxiv.org/help/moderation/index.html>, fetched 2026-10-15.
- Rejections count, verbatim FAQ:
  "**If my paper is rejected, does it count towards my monthly total?** — Yes – this rate limit is for
  submissions, not announced papers, because it is submissions that consume moderator time. If you submit two
  papers in a month, whether they are accepted or rejected, you will have to wait until the next month to submit
  to arXiv again."
  — <https://blog.arxiv.org/2026/10/01/updated-rate-limit-policy/>, dated **October 1st 2026**. Same page:
  "arXiv now limits submitters to up to two submissions per calendar month, with a limit of three total active
  submissions at any given time." and "This rate limit applies to all submissions, across all categories."
- A deleted-before-announcement submission does **not** count, and holdings from a previous month do not consume
  the next month's allowance (same FAQ page).

**Consequence for #3:** the earlier corpus figure *2/month, 3 active, rejections count* is **correct as written**,
and the practical reading is that a single failed arXiv attempt costs a full month's allowance. This is an
argument for not burning the attempt until an endorser has actually agreed.

---

## 3. TMLR — the peer-reviewed route, and it does not need arXiv

### 3.1 Does a TMLR submission require an arXiv preprint? **No.**

TMLR's own pages describe submission as direct and say nothing that makes arXiv a prerequisite:

- "We are using the reviewing and publication system of OpenReview for openness and transparency:
  https://openreview.net/group?id=TMLR … proceed to the OpenReview TMLR site to begin the submission process."
  — <https://jmlr.org/tmlr/submissions.html>, fetched 2026-10-15.
- arXiv is *permitted*, not required: "Authors are also allowed to upload their submissions to arXiv or other
  preprint servers at any time, either anonymously or including their identity, though double blind of the TMLR
  submission itself must be maintained by not linking to another version that includes the authors' names."
  — <https://jmlr.org/tmlr/author-guide.html>, fetched 2026-10-15.
- And a preprint does not disqualify: "You can still submit, even if a preprint of your work already is available
  online somewhere (as long as it's not in official proceedings for some other publishing venue)."
  — <https://jmlr.org/tmlr/faq.html>, fetched 2026-10-15.

### 3.2 Affiliation and OpenReview

- "All authors must have complete and active OpenReview profiles, including information such as affiliations,
  conflicts of interest, and publication history." — author guide. **Affiliation is a profile field; the TMLR
  pages do not require an institutional affiliation to submit.** Whether OpenReview's own profile moderation
  admits an unaffiliated author without friction was **not** verifiable from the page I fetched — see §8.4.
- No fee is stated anywhere on Home, Submissions, Author Guidelines or FAQ (checked 2026-10-15) — a verifiable
  negative, exactly as the corpus already records.
- CC BY 4.0 **from time of submission** — confirmed verbatim: "All TMLR submissions, from the time of submission
  to final publication, are licensed under [CC BY 4.0]. At all times, copyright is retained by the authors."
  — author guide. Paper #3 is already released under CC BY 4.0 (`papers/encoder-crossover-190/AVAILABILITY.md`),
  so there is no licence conflict.
- Scope/format constraints that touch #3: submissions must use the mandatory TMLR LaTeX stylefile; survey papers
  are no longer considered ("As of September 1, 2026, TMLR no longer considers survey papers for review." — FAQ);
  "the rolling review process aims to deliver a final decision approximately **9 weeks** after submission" — FAQ.
- **Double-blind interaction to plan for:** because the TMLR submission must stay anonymised and must not link to
  an identified preprint version, posting #3 publicly under the author's name **before** TMLR submission is
  allowed but slightly raises de-anonymisation risk. The FAQ anticipates it: "We follow the same approach as
  double blind conferences, asking that reviewers don't actively search online to figure out who the authors are."

---

## 4. Per-route table (endorsement-free and DOI-bearing options, assessed)

`free?` = stated positively by the venue, or "no fee documented" where only a verifiable negative exists.
"respected in ML?" is an **assessment**, flagged as such; every other cell is a fetched quote.

| Route | DOI? | Free? | Endorsement needed? | Affiliation needed? | Peer-reviewed? | Respected in ML? | URL · fetched | Verbatim quote |
|---|---|---|---|---|---|---|---|---|
| **arXiv** (cs.LG) | **Yes** — `10.48550/arXiv.<id>`, automatic | Yes — "submission to arXiv is free for authors" (`help/submit/index.html`) | **Yes** — first submission, every category | No, but the *automatic* path needs an institutional email **plus** claimed authorship | **No** — "the arXiv moderation process is not a peer-review process" | Yes — the default ML preprint address | <https://info.arxiv.org/help/endorsement.html> · 2026-10-15 | "arXiv requires that users be endorsed before submitting their first paper to arXiv or a new category." |
| **TMLR** (journal, ISSN 2835-8856) | **`UNVERIFIED`** — no DOI statement found on Home / Submissions / Author Guidelines / FAQ | No fee stated on those four pages (verifiable negative) | **No** — no arXiv posting required | No institutional affiliation required on the pages read | **Yes** — double-blind, ≥3 reviewers, rolling | Yes — "emphasizes technical correctness over subjective significance" | <https://jmlr.org/tmlr/author-guide.html> · 2026-10-15 | "Authors are also allowed to upload their submissions to arXiv or other preprint servers at any time" (= arXiv optional); "All TMLR submissions, from the time of submission to final publication, are licensed under CC BY 4.0." |
| **Preprints.org** | **Yes** — Crossref | **Yes** | **No** (none mentioned) | **No** (none mentioned) | **No** | Weak-moderate in ML; disciplinary fit exists ("Computer Science & Mathematics") | <https://www.preprints.org/about> · 2026-10-15 | "Preprints.org are posted online free of charge."; "Each preprint will be registered with a unique digital object identifier issued by Crossref."; "Content on Preprints.org is not peer-reviewed" |
| **Research Square** | **Yes** | **Yes** — "Free to post" | **No** (none mentioned) | **No** (none mentioned) | **No** | Weak in ML (life-sciences-heavy, multidisciplinary) | <https://www.researchsquare.com/researchers/preprints> · 2026-10-15 | "Our preprints are: Free to post … Issued a DOI … Indexed in Google Scholar, Meta, Researcher, Europe PMC, PubMed (Covid-related research), and Scite" |
| **Zenodo** | **Yes** — DataCite, per record/version | No fee documented on About / Principles / Policies → `UNVERIFIED` affirmatively | **No** | **No** — "Anyone may register as user of Zenodo." | **No** (repository, not a venue) | The standard DOI layer for artefacts; **not** an ML paper venue | <https://about.zenodo.org/principles/> · 2026-10-15 | "A DOI is issued to every published record on Zenodo."; <https://help.zenodo.org/docs/get-started/quickstart/>: "Once you publish, we will automatically assign a Digital Object Identifier (DOI) to your record." |
| **OSF Preprints** | **Yes**, on acceptance | No fee stated on the page read → `UNVERIFIED` affirmatively | **No** | **No** | **No** | Poor fit for ML — OSF hosts discipline servers (PsyArXiv, SocArXiv, …); no ML server on the list | <https://help.osf.io/article/376-preprints-home-page> · 2026-10-15 | "If accepted, preprints receive a DOI and a persistent URL to allow your preprint to be cited" |
| **SSRN** | `UNVERIFIED` — not established from any fetched page | `UNVERIFIED` | No | No | No | **Not** a respected ML venue (law/economics/social science) | only search-engine snippets reached; **not fetched** | — (no verbatim quote; deliberately not asserted) |
| **OpenReview (as a venue host)** | No | Yes to post | n/a | n/a | Venue-dependent | It is the *substrate* for TMLR and workshops, not a preprint server | <https://docs.openreview.net/…/signing-up-for-openreview> · 2026-10-15 — body did not render | No quote obtained; whether an unaffiliated individual can create a venue is `UNVERIFIED` (§8.5) |

**Count: 8 routes assessed; 4 of them (Preprints.org, Research Square, Zenodo, OSF Preprints) carry a DOI, need
no endorsement and need no affiliation.** SSRN's DOI behaviour is unresolved and is therefore **not** counted.

### 4.1 What is *not* a route
- **Non-archival workshop papers** are peer-reviewed at workshop level and are posted publicly on OpenReview, but
  they carry **no DOI** by themselves and so do not satisfy the "citable with a DOI" requirement on their own.
  ICLR 2027's workshop page returned **HTTP 404** on 2026-10-15 (`https://iclr.cc/Conferences/2027/Workshops`), so
  **no 2027 workshop deadline is asserted here**; the strategy's §2 line 65 entry remains uncorroborated by this unit.
- **arXiv alternatives that are not ML venues** (HAL, TechRxiv) were not re-fetched; TechRxiv returned HTTP 403 to
  earlier work. `UNVERIFIED`.
- The **Foresight RFP 2026-10-31** and **SINTEF 2026-11-04** deadlines are funding/proposal dates, **not
  publication venues**, and are ignored here by instruction.

---

## 5. What actually counts as citable, and what it is worth

For **credibility**, three distinct things are in play and must not be blurred:

1. **A DOI-bearing preprint** — dated, permanent, resolvable, quotable. It establishes *priority, authorship and
   a public record*. It is **not** peer-reviewed, and any document that says otherwise is false. Preprints.org
   states the status of its own content ("not peer-reviewed"); arXiv states its moderation is "not a peer-review
   process".
2. **A peer-reviewed venue paper** (TMLR, JOSS, a conference) — carries independent expert evaluation. TMLR adds
   an ISSN-bearing journal record, double-blind review by ≥3 reviewers, and a public review thread.
3. **A workshop paper** — peer-reviewed at workshop level, published publicly, but usually non-archival and
   without a DOI unless separately deposited.

For the **O-1 evidence file**, USCIS's own text draws the line the corpus already records, and I re-read it at
source on 2026-10-15 (<https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4>):

- Criterion 6 (authorship of scholarly articles): "In the academic arena, a scholarly article reports on original
  research, experimentation, or philosophical discourse. … **The article is normally peer-reviewed.**" and
  "A petitioner need not provide evidence that the beneficiary's published work has been cited to meet this
  criterion."
- Criterion 5 (original contributions of major significance) is where citation weight lives:
  "Documentation that the beneficiary's original work was cited at a level indicative of major significance in
  the field".

**Honest consequence for this author:** a preprint satisfies "authored a scholarly article" in substance, but the
"normally peer-reviewed" sentence means **peer review is the materially stronger reading**, and criterion 5 needs
*third-party citations*, which a preprint does not create by itself. So: the preprint is the **floor and the
date-stamp**, and TMLR is the **load-bearing** item. The preposition "peer-reviewed" must never be attached to the
preprint in any O-1 exhibit, cover letter or CV line.

---

## 6. Corrections to `PUBLICATION_STRATEGY.md` (recorded here, not edited there)

- **C1 — §8, line 321 is wrong as of 2026-01-21.** The line instructs: *"Use an institutional email if you have
  one — it can remove the endorser requirement entirely."* Since the 2026-01-21 policy the institutional email
  **cannot** do that alone: the first path requires **both** an institutional email **and** prior authorship on a
  paper already accepted to the same endorsement domain ("requires **both** 1) an institutional email address…
  and 2) previous authorship on an existing paper which has been accepted to the arXiv *'endorsement domain'*
  they wish to submit to"). For an unaffiliated author with no arXiv co-authorship this path is **unavailable
  regardless of email**, so line 321's advice is not merely incomplete — it points at a door that is bolted for
  this author.
- **C2 — §10 item 1 (line 321 again, same sentence) carries the same error** and needs the same fix.
- **C3 — §2, line 61 is wrong in one clause.** It says arXiv is *"the prerequisite for TMLR/Google-Scholar
  visibility."* **TMLR is not gated on arXiv**: its author guidance permits arXiv uploads but never requires one,
  and its FAQ accepts submissions whose preprint is already online. arXiv is a *discoverability* advantage, not a
  TMLR prerequisite. (Google-Scholar visibility may well track arXiv; that half is not contradicted.)
- **C4 — §9, line 288 asserts TMLR gets a "journal DOI".** I could not corroborate a DOI statement on TMLR's
  Home, Submissions, Author Guidelines or FAQ (fetched 2026-10-15). The claim is now marked `UNVERIFIED` in §4
  above rather than repeated.
- **C5 — §11 item 4 (line 348) is partially resolved.** The 2026-01-21 blog post says endorsement for new
  submitters applies "in **all categories**", which answers "every category or only some" (answer: every
  category, for a first submission to it). Whether *cs.AI / cs.LG / cs.SE / cs.PL* form **one or several
  endorsement domains** remains `UNVERIFIED` — neither page enumerates the cs domains.
- **§8's core finding stands:** a first submission needs endorsement, "The endorsement process is not peer
  review", and the 2/month + 3-active limits with rejections counted are all confirmed verbatim (§2.2).

---

## 7. Recommended sequence for paper #3 (cheapest and most certain first)

The ordering principle: **never let the arXiv door gate the public record**, and never spend the one monthly arXiv
attempt before an endorser has consented.

1. **Tag the reproducibility release and mint a Zenodo DOI (today, $0, no endorsement, no affiliation).**
   Paper #3 already ships a sealed fixture and harness (`repro/encoder-crossover-190/`, CC BY 4.0 for the paper;
   the **code licence is still undecided** — `LICENCE_TODO.md` — so settle it before depositing). Zenodo states
   "Anyone may register as user of Zenodo" and issues a DOI per published record. This does not make the paper a
   publication; it makes the **artefact** citable and it is needed anyway for criterion 5.
2. **Post the paper itself for a dated, DOI-bearing public record. Primary: Preprints.org. Fallback: Research
   Square.** Both state "free", "DOI" and no endorsement/affiliation requirement, and both accept CC BY 4.0.
   Paper #3's licence already matches. Expect Preprints.org's short screen ("usually takes less than 24 hours").
   **Do not write "peer-reviewed" anywhere near it.**
3. **Submit #3 to TMLR in parallel — the peer-reviewed, endorsement-free path.** Use the mandatory TMLR stylefile,
   anonymise the manuscript, and **do not link the identified Preprints.org version** in the submission. Free
   (no fee stated), ~9 weeks to decision, CC BY 4.0 from submission. This is the item that satisfies the
   "normally peer-reviewed" reading of criterion 6 and can begin generating real citations.
4. **Only then, attempt arXiv endorsement — as a side quest, not a gate.** See §8 below. If it succeeds later,
   the arXiv version is a *replacement/addition* to a record that already exists, not the record itself.
5. **Workshops, when a live CFP is actually verifiable.** Non-archival and non-DOI on their own; they add a
   peer-reviewed *presentation* (criterion 6's own evidence list names "Published conference presentations") and
   a shot at a best-paper award. No 2027 workshop deadline is asserted here (ICLR 2027 workshops page 404,
   2026-10-15).

### The trade-off, stated plainly
- **Fast preprint first** (steps 1–2): public and citable in **hours to days**, zero cost, no gatekeeper, no
  affiliation. Buys the author a date-stamped public address and a citation handle **now**, while the review
  clock has not started. Buys **nothing** in peer review and, on its own, does not create citations.
- **Slow peer-reviewed path** (step 3, TMLR): **~9 weeks** to a decision, longer if revisions are demanded,
  public review thread, and a real chance of rejection — but on acceptance it is a genuine journal publication
  with an ISSN and the strongest single item for criterion 6. Running both in parallel is not merely allowed, it
  is the point: the preprint fixes priority and the date; TMLR fixes credibility. The only interaction to manage
  is TMLR's double-blind rule about not linking an identified version.

---

## 8. What to do about arXiv endorsement anyway

**Is it worth attempting? Yes — once, cheaply, and without letting it gate anything.** The expected value is a
`cs.LG` posting that TMLR, Google Scholar and every ML reader treats as the canonical address for #3. The cost is
one email and, if it fails, one month of arXiv submission allowance that #3 was not otherwise using.

**How one would realistically obtain it, given no affiliation and no co-author network:**

1. Start the arXiv submission for #3 in the intended primary category (cs.LG per §8's own assignment) and collect
   the **endorsement request email** with its six-character code and shareable link — this is the documented
   self-check, and it is free (endorsement page).
2. Take the papers #3 already cites (the corpus names Huang et al. ICLR 2024, Stechly et al., CriticGPT,
   Valmeekam, CriticBench, Xiong et al.), find them on arXiv, and use the abstract page's "**Which authors of this
   paper are endorsers?**" link to identify **one** eligible endorser. Eligibility is real: "Endorsers must have
   authored a certain number of papers within the *endorsement domain*", counting papers submitted **3 months to
   5 years ago** (endorsement page).
3. Email **one** such person — not a batch. The page is explicit that mass emailing is "inappropriate". Attach the
   manuscript, because the endorser's duty is satisfied either by knowing the author "**or** … see[ing] the paper
   that the person intends to submit".
4. If nobody replies, **stop and move on**. The 2026-01-21 blog post removes the hope of escalation: "arXiv staff
   cannot waive endorsement requirements or provide a personal endorsement for authors."

**Honest assessment: difficult for an unaffiliated researcher.** Both automatic paths are closed (no institutional
email at all; and even with one he has no prior accepted arXiv paper in the domain), so the entire burden falls on
a stranger's goodwill, mediated by an anti-mass-mailing rule and a submission allowance that a rejection consumes.
This is not a reason to delay the public record by a single day — steps 1–3 of §7 are independent of it.

---

## 9. `UNVERIFIED` list (asserted nowhere above as fact)

1. **Zenodo's "$0" in the affirmative.** No fee is documented on About, Principles or Policies (fetched
   2026-10-15) — a verifiable negative only.
2. **OSF Preprints' "$0" in the affirmative.** No fee statement found on the help page read; the "free preprint
   service" phrases on it describe individual community servers (PsyArXiv etc.), not OSF preprints generally.
3. **SSRN's DOI behaviour and fee.** No SSRN page was fetched (search-engine snippets only), so nothing is
   asserted. Deliberately unresolved rather than filled from memory.
4. **TMLR's DOI.** No DOI statement found on TMLR Home, Submissions, Author Guidelines or FAQ (2026-10-15);
   `PUBLICATION_STRATEGY.md` §9 line 288's "journal DOI" is not corroborated by this unit.
5. **OpenReview profile moderation for an unaffiliated author**, and whether an individual can create an
   OpenReview venue outside a conference/workshop. The docs page body did not render on fetch; unanswered.
6. **Whether cs.AI / cs.LG / cs.SE / cs.PL are one endorsement domain or several.** Neither the endorsement page
   nor the blog post enumerates the cs domains ("most high-level subject areas … are currently endorsement
   domains", with physics as the exception).
7. **ICLR 2027 workshop deadlines and their treatment of independent researchers.** `https://iclr.cc/Conferences/2027/Workshops`
   returned **HTTP 404** on 2026-10-15; no 2027 workshop date is asserted.
8. **Preprints.org's indexing/visibility list.** The page text was truncated at "Visibility for Preprints"; the
   indexing claim is not quoted.
9. **Research Square's acceptance criteria for an ML paper.** The page lists screening for "complete author
   information, appropriate declaration statements, and potential risks to human health" — nothing about
   disciplinary fit for ML.
10. **HAL and TechRxiv** (pricing, DOI, DOI mechanics). Not re-fetched this unit; TechRxiv returned HTTP 403 to
    earlier work. They remain untested fallbacks.

---

## 10. Sources fetched this unit (URL · date)

| # | URL | Fetched | Used for |
|---|---|---|---|
| S1 | <https://info.arxiv.org/help/endorsement.html> | 2026-10-15 | endorsement mechanics, code, endorser eligibility, "not peer review" |
| S2 | <https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/> | 2026-10-15 (post dated 2026-01-21) | institutional email insufficient; both-path requirement; all categories; staff cannot waive |
| S3 | <https://info.arxiv.org/help/moderation/index.html> | 2026-10-15 | 2/month, 3 active; moderation ≠ peer review |
| S4 | <https://blog.arxiv.org/2026/10/01/updated-rate-limit-policy/> | 2026-10-15 (post dated 2026-10-01) | rejections count; across all categories; deleted submissions do not count |
| S5 | <https://jmlr.org/tmlr/submissions.html> | 2026-10-15 | direct OpenReview submission; no arXiv step |
| S6 | <https://jmlr.org/tmlr/author-guide.html> | 2026-10-15 | arXiv optional; CC BY 4.0 from submission; OpenReview profiles |
| S7 | <https://jmlr.org/tmlr/faq.html> | 2026-10-15 | preprints accepted; ~9 weeks; surveys excluded; arXiv not required |
| S8 | <https://www.preprints.org/about> | 2026-10-15 | free of charge; Crossref DOI; not peer-reviewed |
| S9 | <https://www.researchsquare.com/researchers/preprints> | 2026-10-15 | free to post; DOI; ISSN |
| S10 | <https://about.zenodo.org/principles/> + <https://about.zenodo.org/policies/> + <https://help.zenodo.org/docs/get-started/quickstart/> | 2026-10-15 | DOI per record; anyone may deposit; no fee documented |
| S11 | <https://help.osf.io/article/376-preprints-home-page> | 2026-10-15 | DOI on acceptance; community servers listed |
| S12 | <https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4> | 2026-10-15 | criterion 6 "normally peer-reviewed"; criterion 5 citation weight |
| S13 | <https://info.arxiv.org/help/submit/index.html> | 2026-10-15 | "submission to arXiv is free for authors"; new users "may be required to find endorsements" |
| S14 | <https://iclr.cc/Conferences/2027/Workshops> | 2026-10-15 | **HTTP 404** — recorded as a failed fetch, not a negative finding |
