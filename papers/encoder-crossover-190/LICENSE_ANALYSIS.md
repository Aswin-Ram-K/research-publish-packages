# LICENSE_ANALYSIS.md — the licence decision, the conflict behind it, and the disclosure scope it implies

Unit **ULIC**. Paper #3: [`MANUSCRIPT.md`](MANUSCRIPT.md) (encoder crossover, 190-case fixture).

**Status: the licence choice is MADE — CC BY 4.0 (author decision relayed 2026-10-15).** This file does not
make a choice; it documents the facts the choice rests on, the conflict that made the choice consequential,
and the **one decision that is still open** — the *content* disclosure scope (§8).

Every claim below carries a URL + date + verbatim excerpt. Two rules were held to:

- **Nothing is asserted about a licence that was not read off a page.** Where the page was silent, the claim
  is `UNVERIFIED` and the list at §9 says so.
- **The licence governs *reuse*, not *visibility*.** No licence on the menu hides the paper (§4).

---

## 1. Measured facts

### 1.1 arXiv's licence menu — 6 options (confirmed)

Source: <https://info.arxiv.org/help/license/index.html> — fetched **2026-10-15** (HTTP 200).

Verbatim, the six options and their descriptions:

> **CC BY 4.0**: Creative Commons Attribution
> "This license allows reusers to distribute, remix, adapt, and build upon the material in any medium or
> format, so long as attribution is given to the creator. The license allows for commercial use."

> **CC BY-SA 4.0**: Creative Commons Attribution-ShareAlike
> "…allows for commercial use. If you remix, adapt, or build upon the material, you must license the
> modified material under identical terms."

> **CC BY-NC-SA 4.0**: Creative Commons Attribution-Noncommercial-ShareAlike
> "…for noncommercial purposes only… If you remix, adapt, or build upon the material, you must license the
> modified material under identical terms."

> **CC BY-NC-ND 4.0**: Creative Commons Attribution-Noncommercial-NoDerivatives
> "This license allows reusers to copy and distribute the material in any medium or format **in unadapted
> form only**, for noncommercial purposes only, and only so long as attribution is given to the creator."

> **arXiv.org perpetual, non-exclusive license 1.0**
> "This license gives limited rights to arXiv to distribute the article, and also **limits re-use of any type
> from other entities or individuals**."

> **CC Zero** — "a public dedication tool, which allows creators to give up their copyright and put their
> works into the worldwide public domain." With the warning: *"If you choose this license, you will no longer
> control the article's copyright. A work distributed with CC Zero would not allow for copyright transfer, and
> this conflicts with many publishers' requirements."*

**Two properties, verbatim and unmodified:**

> "For all licenses here, with the exception of CC Zero, the original copyright holder retains ownership after
> posting on arXiv."

> "The license chosen is irrevocable and cannot be changed."

…and, in the same page's "How to choose a license" list (the mitigating sentence, also verbatim):

> "Please note that different versions of the work can have different licenses."

…and the **escape hatch** for an unlisted licence:

> "Some authors require a license that is not listed here. As long as the desired license does not restrict
> arXiv's license, authors can select the arXiv license and then indicate the desired license in the first
> page of the article. This is a requirement of some funders and governments."

The non-exclusive licence's own page — <https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html>
(fetched **2026-10-15**, HTTP 200) — records exactly what the submitter grants, and nothing more:

> "I grant arXiv.org a perpetual, non-exclusive license to distribute this article."
> "I certify that I have the right to grant this license."
> "I understand that submissions cannot be completely removed once accepted."

**Reading.** The non-exclusive option is the *most restrictive* thing on the menu, and it is not a
publication licence at all: it transfers nothing to third parties and grants no reuse. It is an
*anti-reuse* setting, not a *confidentiality* setting — see §4.

### 1.2 arXiv content is public regardless of licence — the load-bearing fact

Same page, second paragraph, verbatim:

> **"All articles on arXiv.org can be viewed and downloaded freely by anyone."**

This is the single most important measured fact in this file. **The licence governs reuse, not visibility.**
Posting under CC BY-NC-ND or under the non-exclusive licence does not withhold one word of the manuscript:
anyone may read and download it. The only thing a restrictive licence removes is other people's ability to
*reuse* the work — which is the opposite of what an author seeking recognition wants (§7).

**A restrictive licence does not hide content. Only redacting the content hides content.**

### 1.3 What frontier labs actually do — measured, not assumed (5 papers, 4 with a licence icon read)

Each row was fetched on **2026-10-15**; the licence is identified by the `Abs-license` block's icon and
`href` on the abstract page.

| paper | lab | arXiv id | licence **observed** | evidence on the abstract page |
|---|---|---|---|---|
| Constitutional AI: Harmlessness from AI Feedback | Anthropic | 2212.08073 | **CC BY 4.0** | icon `https://arxiv.org/icons/licenses/by-4.0.png`, link `http://creativecommons.org/licenses/by/4.0/` |
| Constitutional Classifiers (universal jailbreaks) | Anthropic | 2501.18837 | **CC BY 4.0** | icon `…/by-4.0.png`, link `http://creativecommons.org/licenses/by/4.0/` |
| Sleeper Agents | Anthropic | 2401.05566 | **arXiv perpetual, non-exclusive 1.0** | `[view license](http://arxiv.org/licenses/nonexclusive-distrib/1.0/)` — **no CC icon** |
| GPT-4 Technical Report | OpenAI | 2303.08774 | **arXiv perpetual, non-exclusive 1.0** | `[view license](http://arxiv.org/licenses/nonexclusive-distrib/1.0/)` — **no CC icon** |
| Weak-to-Strong Generalization | OpenAI | 2312.09390 | **arXiv perpetual, non-exclusive 1.0** | `[view license](http://arxiv.org/licenses/nonexclusive-distrib/1.0/)` — **no CC icon** |

**Measured distribution: 2 open / 3 restrictive.** The premise "the frontier labs publish under open licences"
is **half true and, as stated, wrong**: OpenAI's GPT-4 Technical Report — the flagship example of a
proprietary-lab paper — carries arXiv's *most restrictive* option, and two Anthropic/OpenAI papers do the same.

**But the substantive reading survives, and it is the important one.** Both readings are visible in the same
fetches:

- GPT-4's abstract, verbatim: "GPT-4 is a **Transformer-based model** pre-trained to predict the next token in
  a document." That is the entire architecture disclosure in an abstract for the report — the model card's
  openness is about *findings*, and the implementation is withheld **in the content**.
- Constitutional AI is CC BY 4.0 and still withholds its implementation: the paper is a method paper about a
  training procedure; no weights, no training data, no serving stack accompany it.

So the **proprietary-lab posture is achieved by selective disclosure of content**, and it is *orthogonal* to
the licence: the same posture appears under CC BY 4.0 (2212.08073, 2501.18837) and under the non-exclusive
licence (2303.08774, 2401.05566, 2312.09390). **A restrictive licence is neither necessary nor sufficient for
it.** The two Anthropic CC BY 4.0 papers are the closest measured match to the author's chosen posture
(open findings, withheld implementation) — and that posture is the decision recorded in §2.

### 1.4 THE CONFLICT — TMLR requires CC BY 4.0 from the moment of submission (CONFIRMED)

Source: <https://jmlr.org/tmlr/author-guide.html> — fetched **2026-10-15** (HTTP 200). Under
"**Copyright and Licensing**", verbatim:

> "All TMLR submissions, from the time of submission to final publication, are licensed under CC BY 4.0. At
> all times, copyright is retained by the authors."

The search snippet that raised this is therefore **confirmed verbatim**, not refuted. The same section adds a
mitigating sentence, also verbatim:

> "Authors are also allowed to upload their submissions to arXiv or other preprint servers at any time, either
> anonymously or including their identity, though double blind of the TMLR submission itself must be
> maintained by not linking to another version that includes the authors' names."

**The conflict, stated plainly.** TMLR requires CC BY 4.0 **from the time of submission**. arXiv's licence for
*a posted version* is **"irrevocable and cannot be changed"**. Therefore a paper first posted to arXiv under
CC BY-NC-ND (or under the non-exclusive licence) has a *permanently* restrictively-licensed public version,
and that version cannot be made CC BY 4.0 after the fact. Anyone planning to submit to TMLR must not post the
paper restrictively first: **for a TMLR-bound paper the licence choice is made at first posting and cannot be
revisited.**

**The limits of the consequence — stated so no reader over-reads it.**

- The irrevocability attaches to **the version posted**, and arXiv says verbatim that *"different versions of
  the work can have different licenses"* — a later version can carry CC BY 4.0.
- arXiv also says the copyright holder **retains ownership** for every licence except CC0, so the author
  remains able to grant CC BY 4.0 to TMLR for the same work.
- **`UNVERIFIED`:** whether TMLR would *reject or query* a submission whose earlier arXiv version is licensed
  restrictively. No TMLR statement addressing arXiv licence interplay was found on the author guide (fetched
  2026-10-15); the two sentences above are all the guide says on the point.

So the conflict is **real as a hard constraint on sequencing** ("the licence is chosen at first posting and is
irrevocable"), and its *enforcement* against an already-restrictive arXiv version is `UNVERIFIED`.

### 1.5 The workshop / OpenReview route — no CC BY requirement found at the venue level

- **ICLR 2025 Call for Papers** — <https://iclr.cc/Conferences/2025/CallForPapers> (fetched **2026-10-15**,
  HTTP 200) — states **no licence requirement for submissions at all**. What it does state, verbatim, is
  visibility: *"All submitted papers (accepted or rejected) will be deanonymized after the notification. The
  submissions and reviews will be released to the public."* And workshops are explicitly out of scope:
  *"As in past years, workshops will have their own organization and call for contributions."*
- **OpenReview Terms of Use** — <https://openreview.net/legal/terms> ("Last updated: September 24, 2024";
  fetched **2026-10-15**, read at 22,000 chars) — the venue imposes **no licence on Articles**:
  > "OpenReview does not ask that copyright for submitted Articles or Article Edits be transferred to
  > OpenReview. However, we require sufficient rights to allow us to distribute the Work in perpetuity."
  > "OpenReview asks that Venues and/or Authors indicate an Article's copyright license in the Article's
  > 'license' Database field… When no 'license' field is present in an Article, the way to find out the license
  > is to contact the associated Venue or Authors to ask for license information."
  > "If the authors wish to later submit the same Article to another Venue, journal, conference, or other
  > publisher, it is the responsibility of the Submitter to ensure that the license associated with the
  > OpenReview-submitted Article is compatible with the requirements of the later publisher."

  (Only **Comments and Configuration Records** are CC BY 4.0 by the Terms — not Articles.)

**Conclusion for the workshop route:** a restrictive arXiv licence is **not**, on this evidence, a bar to
ICLR-workshop submission — the venue sets the licence per venue and ICLR 2025 asserted none. **`UNVERIFIED`:**
the licence terms of any *specific* workshop (e.g. a NeurIPS or ICLR workshop CFP) — each has "their own
organization and call for contributions", and none was fetched by this unit.

### 1.6 The AGPL / repository question — resolved, and the earlier concern is WITHDRAWN

Measured on the read-only target `the read-only target repository` and against GitHub (all **2026-10-15**):

| fact | evidence |
|---|---|
| the code is **AGPL-3.0** | `the read-only target repository/LICENSE` line 1–2, verbatim: `GNU AFFERO GENERAL PUBLIC LICENSE` / `Version 3, 19 November 2007` |
| declared SPDX id | `the read-only target repository/package.json:122` — `"license": "AGPL-3.0-only"` |
| declared repository | `the read-only target repository/package.json:123–125` — `"url": "the source repository's GitHub URL"` |
| git remote in the clone | `git remote -v` → `origin the source repository's GitHub URL` (fetch and push) |
| citation metadata | `the read-only target repository/CITATION.cff` — `license: AGPL-3.0`, `repository-code: "the source repository's GitHub URL"` |
| **is that repository public?** | **No.** `the source repository's GitHub URL` → **HTTP 404**; `the source repository's GitHub API URL` → **HTTP 404**, body `{"message":"Not Found", …, "status":"404"}` |
| public repo list of that account | `the source account's public repository-listing API URL?per_page=100` (HTTP 200) — **no `the source repository` entry** in the returned public listing |

**The earlier concern is withdrawn.** A draft of this analysis (before the author's confirmation) treated
"the code is already public under AGPL-3.0" as a possible larger exposure. **It is moot, and this file
records the withdrawal so nobody later "discovers" a leak that did not happen:**

- The repository is **not publicly accessible** (404 unauthenticated). The author confirms it has been **kept
  private to date**.
- **AGPL-3.0 has therefore triggered no obligation to the public.** AGPL's source-offer duty (the §13 network
  clause) runs to users who *interact with the software over a network*; there are none. Its ordinary
  distribution duties run to those to whom the software is conveyed; the author states there are none.
- **Keeping the code private is fully consistent with the decision in §2.** Nothing about the code licence
  obstructs "do not release the code" — the lever is *whether the repository is published*, not which licence
  it carries.
- **`UNVERIFIED`:** the API 404 for an unauthenticated request cannot distinguish *private* from *renamed*
  from *never pushed*. The author's confirmation ("kept private to date") is the authority here; this unit
  verified only that it is **not public**.
- **The one AGPL point that survives:** if the author ever *does* run this kernel as a network service, AGPL
  §13 becomes the operative publication mechanism for the implementation — not the paper licence. That is a
  fact about the code licence, and it belongs to a different decision than the one in §2.

---

## 2. The decision (MADE — recorded here, not taken here)

| | |
|---|---|
| **Licence** | **CC BY 4.0** |
| **Decided by** | the author, relayed **2026-10-15** |
| **Posture** | **open paper, withheld implementation** — open publication of the *findings*; code, model weights and data **not released** |
| **Why this is the only TMLR-compatible option** | TMLR requires CC BY 4.0 "from the time of submission to final publication" (§1.4). Every other option on arXiv's menu is either non-commercial, no-derivatives, no-reuse-at-all, or copyright-ceding — none of which satisfies that sentence |
| **Why it matches the measured lab practice** | Anthropic's 2212.08073 and 2501.18837 use exactly CC BY 4.0 while withholding implementation (§1.3) |
| **What it costs** | nothing in visibility (arXiv is public under every option, §1.2) and nothing in reuse-restriction, because the *implementation* was never going to be in the paper |

**The premise that motivated a restrictive licence has been measured and inverted.** The belief under test was
"a restrictive licence is how a lab keeps its secrets, and that is how Anthropic/OpenAI publish." The
measured answer: the labs' secrecy is in **what the paper does not contain**; their licences range from CC BY
4.0 to the most restrictive item on arXiv's menu, and the licences do not track the secrecy at all (§1.3).

---

## 2.1 Author policy — **GENERAL: this applies to every paper, not only paper #3**

**Author policy, 2026-10-15**, relayed as standing policy. Restated verbatim as four clauses:

1. **Papers are public.** Licence **CC BY 4.0** — the industry standard, and what Anthropic uses in practice.
2. **Every paper ships a minimal reproducibility subset** — the "middle ground": the fixture schema and the
   fixture itself, the evaluation harness and exact commands, and the pre-registered protocols — while the
   **agent-state kernel / runtime implementation and any weights are withheld**.
3. **Code licensing is a SEPARATE decision from paper licensing.** Whether the code is open-sourced is its own
   matter; the intent is to **disclose code pieces gradually** rather than releasing the whole thing at once.
4. **Target: industry-standard presentation** (frontier-lab norms).

**Scope of this document under that policy.** The CC BY 4.0 decision in §2 is **one application of clause 1**
— the instance for paper #3, chosen by the author on 2026-10-15. §8.2's minimal reproducibility subset is
**clause 2's default for every paper**, instantiated here for paper #3. Nothing in this file is a
paper-#3-only rule.

**What this file does NOT decide, by clause 3.** The **code licence** is not part of the paper decision and is
**not decided here**. §1.6 measures the code's current declared licence; §5 (whose phrase "the *chosen*
pairing" is **amended by this policy**) treats the paper/code licence relationship as a relationship to be
managed, not a licence to be settled. Cross-reference: the code-licence question belongs to whatever unit owns
the repository decision; this file's only claim about it is the measured one — the repository is **private**,
so nothing has been given away yet (§2.2).

**The in/out lists for clause 2, for paper #3** (full detail, sentence by sentence, in §8):

- **INSIDE the subset (to be released):** the 190-case fixture and its schema; the evaluation harness and the
  exact commands that produce the reported numbers; the pre-registered protocol and the second-labeller
  pre-registration.
- **OUTSIDE the subset (withheld):** the agent-state kernel / runtime implementation (`src/`, `kernel/`), any
  model weights, the training pipeline internals, and the served decider stack.

## 2.2 The false constraint removed — the code licence is still open from scratch

Stated by the author **2026-10-15** and corroborated by the measurement in §1.6:

- The the source repository repository has been **private to date** (`the source repository's GitHub API URL`
  → **HTTP 404**, 2026-10-15; absent from the account's public repo listing). **No licence has been granted to
  anyone**, so **whatever `the read-only target repository/LICENSE` currently says, nothing has been irrevocably given
  away.** The author is **free to choose the code licence from scratch** when and if code pieces are disclosed.
- **Consequence for this file:** there is no "AGPL-3.0 commitment" constraining the paper decision, and no
  constraint flowing the other way either. The paper is CC BY 4.0 (§2); the code's licence is clause 3's
  separate matter. Neither decision binds the other.
- **The one honest residual:** this is recorded as the **author's statement**, and the question *"has a copy of
  the source ever been conveyed to anyone — a collaborator, a reviewer, a fork?"* is not observable from this
  workspace. It stays `UNVERIFIED` (§9 #6). If a copy ever was conveyed, AGPL-3.0 terms attached to **that
  copy** and cannot be revoked for that recipient — which is a fact about that recipient, not a constraint on
  choosing the licence for a future public release.

---

## 3. Option comparison

| option | reuse granted | commercial use | derivatives | TMLR-compatible? | O-1 impact |
|---|---|---|---|---|---|
| **CC BY 4.0** *(chosen)* | full — "distribute, remix, adapt, and build upon … in any medium or format", attribution required | **yes** | **yes** | **YES** — "licensed under CC BY 4.0" (§1.4) | best available: maximum legitimate reuse, quotation, translation, and derivative work → maximum surface for the recognition criteria (§7) |
| CC BY-SA 4.0 | full, **share-alike** on adaptations | yes | yes, under identical terms | No (TMLR names CC BY 4.0) | near-best; share-alike can deter incorporation into differently-licensed collections |
| CC BY-NC-SA 4.0 | non-commercial only, share-alike | **no** | yes, non-commercially | No | reduced: excludes every industry reader's reuse; a large share of the field's engagement is commercial |
| CC BY-NC-ND 4.0 | copy/distribute **unadapted** only, non-commercial | **no** | **no** | No | worst of the CC options: no derivatives means no figure reuse, no translation, no adaptation of the method into another's pipeline — the very activities that produce citations |
| arXiv perpetual, non-exclusive 1.0 | **none** — "limits re-use of any type from other entities or individuals" | no | no | No | worst overall: paper is fully readable (§1.2) and *nothing else is permitted*; every reuse becomes a permission request, which suppresses engagement without withholding anything |
| CC Zero | full, **no attribution required** | yes | yes | No (TMLR names CC BY 4.0; and this "conflicts with many publishers' requirements" per arXiv) | doubles-edged: maximum reuse but **loses the attribution that the recognition criteria are built on**; also cedes copyright |
| unlisted licence via the escape hatch | whatever the author names on page 1 | n/a | n/a | No | structurally identical to the row chosen: arXiv's licence plus a page-1 notice; still no reuse grant to third parties, still public content |

**The table's one-line summary:** on a menu where every option leaves the paper publicly readable, the
restrictive options remove *other people's* ability to use the work and add nothing to the author's.

---

## 4. Visibility vs reuse — stated plainly

- **Visibility.** Verbatim from arXiv (§1.2): *"All articles on arXiv.org can be viewed and downloaded freely
  by anyone."* This is true on every one of the six options. A restrictive licence **does not hide the
  manuscript, the method, the numbers, or the fixture description**. It hides nothing at all.
- **Reuse.** The licence is the *reuse* switch: whether a reader may redistribute, translate, adapt, quote at
  length, or build on the work, and whether they may do so commercially.
- **Therefore:** "I want a proprietary posture" and "I will choose a restrictive licence" are **different
  decisions with different levers**. Restricting the licence restricts *others' use of an already-public
  document*. Restricting the *content* restricts what is public in the first place.
- **The one-line form, for the record:** *a licence cannot un-publish a paper; only redaction can.*
- Corollary: if the goal is that the implementation not be public, the licence is **not the lever** — the
  implementation simply must not be in the paper, and must not be reachable from it (§5, §6, §8).

---

## 5. The AGPL point, and why it is not the exposure it first appeared to be

- The supporting code is **AGPL-3.0** (§1.6). AGPL is a strong copyleft whose network clause obliges source
  disclosure **to users who interact with the software over a network**.
- **If the concern is protecting the implementation, the paper licence is not where the exposure is** — and
  neither is the AGPL, *on the facts measured*: the repository is **not public**, no network service is
  described, so no source-offer duty to the public has been triggered. The concern raised in the first draft
  of this analysis ("already public under AGPL") **does not hold** and is withdrawn (§1.6).
- The residual risk is procedural, not legal: **the decision to keep the repository private is now load-
  bearing**, and it must be maintained deliberately. Publishing the repository later would simultaneously
  (a) release the implementation and (b) attach AGPL obligations to everyone who receives it.
- **A mismatch to state rather than resolve:** the paper may be CC BY 4.0 while its supporting code is
  AGPL-3.0-only. That is coherent (AGPL covers code, CC BY covers prose) and is now the *chosen* pairing —
  but the paper must not imply that an AGPL-licensed, private artifact is available for inspection.

---

## 6. The new constraint: a private repository forfeits criterion 5 on the software

Source: **2 USCIS-PM M.4, criterion 5** — <https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4>
(fetched **2026-10-15**, HTTP 200). Verbatim from the criterion's "Examples of relevant evidence":

> "Contributions to repositories of software, data, designs, protocols, or other technical resources **with
> evidence of significant scientific, scholarly, or business-related impact in the field**"

and, from the same criterion's considerations:

> "Evidence that the beneficiary's work was funded, patented, or published, while potentially demonstrating the
> work's originality, will not necessarily establish, on its own, that the work is of major significance to
> the field."

The corpus had already reached the same reading independently
([`../../strategy/VISA_US_ROUTES.md`](../../strategy/VISA_US_ROUTES.md), [`../../strategy/SOCIAL_PRESENCE.md`](../../strategy/SOCIAL_PRESENCE.md)),
including the correction that this language sits in the **O-1A** chapter (2 USCIS-PM M.4), not in the EB-1A
chapter.

**The tension, stated plainly.** The criterion names **impact**, not existence. A repository that is private
has, by construction, **zero observable impact evidence**: no adopters, no dependent packages, no download or
usage figures, no independent letters describing what the software changed for them. So:

> **"Withhold the code" protects the implementation and forfeits the repository as O-1A criterion-5
> evidence.** These two goals cannot both be maximised. The decision in §2 chooses withholding; §8 proposes
> the middle path that recovers part of what it costs.

**What the decision does *not* cost.** Criterion 6 (authorship of scholarly articles) is unaffected. Its own
text is explicit, verbatim from the same page:

> "In order to meet this criterion, the beneficiary must be a listed author of the submitted article or
> articles but need not be the sole or first author. **A petitioner need not provide evidence that the
> beneficiary's published work has been cited to meet this criterion.**"

So the **arXiv DOI alone** can support the authorship criterion on its own terms. The citable artifact becomes
the paper; nothing is lost *there*.

**The Zenodo code-DOI route is off the table as previously scoped.** Zenodo's docs —
<https://help.zenodo.org/docs/github/> and <https://help.zenodo.org/docs/github/enable-repository/> (both
fetched **2026-10-15**, HTTP 200) — describe the GitHub integration as toggling a repository from the
GitHub-linked list so that "new releases from the repository will be automatically ingested and archived".
Honest alternatives, per the same docs' index: **"Upload software manually"** — which **publishes the code**
and therefore contradicts the decision — or **no code DOI at all**. `UNVERIFIED`: the fetched docs do not
contain a verbatim sentence restricting the GitHub integration to *public* repositories; the mechanism
(releases are ingested from GitHub) is what makes it unusable for a private repo. Treat "public only" as
**not verbatim-verified**.

**And one flag for the paper.** `the read-only target repository/CITATION.cff` sets
`repository-code: "the source repository's GitHub URL"` — a URL that **404s for any reader**
(§1.6). The paper must not send reviewers to it, and the Data/code availability statement must not imply that
it resolves.

---

## 7. O-1 impact of the licence choice, criterion by criterion

*This section is reasoning over the fetched criterion text, not legal advice. The one quantification it
refuses to give is "how much impact is enough" — see `UNVERIFIED` §9.*

- **Criterion 6 — authorship.** **Citations are not required** (verbatim, §6). A CC BY 4.0 arXiv paper with a
  DOI satisfies the criterion's evidentiary shape on its own. **A restrictive licence neither helps nor
  hurts here.**
- **Criterion 5 — original contributions of major significance.** Turns on **impact** evidenced by others:
  "published materials about the significance", "cited at a level indicative of major significance",
  "widespread commentary on its importance from others working in the field". **Every one of those is other
  people's use of the work.** CC BY 4.0 permits reuse with attribution — the widest possible surface for that
  use. NC/ND and the non-exclusive licence restrict precisely the activities that generate it: NC excludes
  industry engagement, ND excludes adaptation and reuse in another's pipeline. **The restrictive options are
  negative for this criterion; the open one is not.**
- **The direction of the author's goals.** The corpus's own strategy files rank the licence question by what
  *recognition* it buys. For a body of work whose O-1A file turns on recognition, **the licence that maximises
  reuse maximises the evidence**; the restrictive options foreclose engagement while withholding nothing
  (§4).
- **What the withheld implementation costs the same criterion.** The code *is* the most verifiable artifact
  the corpus has — but only if it is public (§6). Withholding it removes the sub-clause the 2025 update added
  for software; the paper must then carry criterion 5 on citations and letters alone. **This is the real
  exposure created by the decision, and it is a disclosure-scope problem, not a licence problem.**
- **Bonus, measured:** CC0 would maximise reuse and **drop the attribution requirement** — the recognition
  loop that the criteria are built on runs on attribution. This is why CC BY 4.0, not CC0, is the coherent
  open choice.

---

## 8. THE OPEN DECISION — the disclosure scope (the real lever)

The licence question is closed (§2). **The open question is what the paper is allowed to say it contains**,
because "code, weights and data withheld" and the current manuscript's own statements are in tension.

### 8.1 What the manuscript currently discloses that conflicts with "implementation withheld"

Read out of [`MANUSCRIPT.md`](MANUSCRIPT.md) (read-only; **not edited** by this unit). Line numbers are that
file's.

| # | MANUSCRIPT.md | what it says (verbatim or close paraphrase) | conflicts because |
|---|---|---|---|
| 1 | §7 `:562–563` | "Everything in this paper is **re-derivable from the target repository `the read-only target repository`** (read-only) plus this workspace." | promises re-derivability from an artifact the reader cannot reach — the single strongest conflict |
| 2 | §7 `:565–576` | the "eight load-bearing sources" table: exact in-repo paths (`docs/research/EXP#12-evidence/…`, `docs/research/EXP#11-evidence/decider-rows.jsonl`, `experiments/second-labeller-190/{RUN.json,metrics.json,EVIDENCE.md}`) **plus commit `ad301ae1a5472fa7bd27807fdc7bb15d35f81988`** | a commit hash and a full file manifest is a *reproduction kit pointing into the private repository*; the commit hash is useless to any reader |
| 3 | Data and code availability `:604–605` | "The decision fixture (`evals/fixtures/reflex-decisions.ts`), the experiment record and the **26-file evidence tree** live in the target repository `the read-only target repository`." | states the artifact exists and names its path, with no access path |
| 4 | Data and code availability `:605–608` | "That repository is licensed **AGPL-3.0** … **⚠ The paper's own licence is a separate, deliberate choice that a human must still make**" | **stale after §2** (the licence is chosen) — and inviting a reader to look for an AGPL artifact that is not public |
| 5 | §7 `:590–593` | "**Instrument integrity checks a replicator should re-run**" — fixture sha256, "byte-identical sandbox copy", F4 firing counts, row identity `39+27+90+34=190` | frames a reader as a replicator with access to the tree |
| 6 | §7 `:584–586` | names `docs/research/EXP#11-evidence/decider-rows.jsonl` as the thing that re-scores to 0.6789 | the audit path is inside the private repo |
| 7 | §3.2 `:202–225` | arm parameter counts (149,015,041 / 183,832,321 / 109,489,537), DeBERTa train loss `1.1288 → 1.1235`, dev `0.50 → 0.495` vs `0.475`, "three identical training runs … 0.5150 and 0.5900 … 0.3421 and 0.3474" | **results of the training pipeline** — fine as reported results, but each is an invitation to "how did you train it", which is the withheld part |
| 8 | §3.1 `:177–183` | the fixture's full construction: 190 cases, 721 options, 74 labels (51 once), `K` distribution 33/27/76/54, sha256 `076164ac…4796` | **dataset construction** — this is the boundary case: it is arguably the *method*, and it is also a description precise enough to rebuild the instrument |
| 9 | §3.1 `:187–193`, `:194–195` | chance-floor derivation, option-0 rate 0.3789, leaky-majority 0.1474; "authored by one worker and carries known flagged weak points" | instrument-level disclosure (method); no implementation leak |
| 10 | Abstract `:32–35` | the n-gram leak criterion's operationalisation ("≥ 2 distinct shared 8-grams within one row pair", 0/152,000, seeded 13/44/57) | method detail; publishable, but it is an *implementation of a check* |
| 11 | §2.2 `:160–164` | internal corpus figures (`laya-typed-decisions` 0.374, `imajev-4b` 0.645 / fixture 0.6368) | quotes **third-party/internal corpus numbers** from the private repository — a consent question, not only a licence one |

**Factual negatives — checked, and worth recording because they shrink the problem:**

- The strings **`github` and `zenodo` do not occur anywhere in `MANUSCRIPT.md`** (grep, 2026-10-15). There is
  **no public repository URL and no code DOI in the manuscript to redact.** The only pointer is the local
  path `the read-only target repository`.
- There is **no hyperparameter table**: the strings `hyperparameter`, `learning rate` and `batch size` do not
  occur (same grep). The manuscript is already light on implementation detail — what it discloses is
  *pointers into a private artifact*, not the artifact.

**So the required edit is smaller than it looks:** the manuscript needs its *availability and reproduction
claims* reframed (§8.2), not its method stripped. Items 1–6 are the conflicts; items 7–11 are method.

### 8.2 The recommended middle path — a minimal reproducibility subset

This is what the frontier labs actually do (§1.3: publish the eval harness and the findings, withhold the
model), and it is the **only route that restores any criterion-5 surface** while honouring "implementation
withheld":

**Release, as a separate public artifact (not by opening the source repository):**

1. **The 190-case fixture** — the schema *and* the sealed decisions. *Caveat:* `CHECKLIST.md` §4 records that
   the fixture and evidence tree are **another project's recorded work**; publishing it needs that owner's
   consent. `UNVERIFIED` — not obtained by this unit.
2. **The evaluation harness and the exact commands** that produce the reported numbers — the command list
   currently in [`EVIDENCE_NOTES.md`](EVIDENCE_NOTES.md), which lives **in this workspace, not in the private
   repository**.
3. **The pre-registered protocol and the second-labeller pre-registration** — the falsifier, the MDE protocol,
   the κ procedure.

**Withhold:** the agent-state kernel / runtime implementation (`src/`, `kernel/` in the target), any model
weights, the training pipeline internals, and the served decider stack.

**Mechanically:** create a **new, small, public reproduction repository** (e.g. `encoder-crossover-repro`)
containing items 1–3 and nothing imported from the private tree. Its licence is a fresh, deliberate choice —
the author, as copyright holder, may license their own work as they wish; if any third-party contributions
exist in the pieces reused, their consent is needed (`UNVERIFIED`). **the source repository stays private and untouched.**

**What the subset licenses and what it restores:**

| | |
|---|---|
| what it publishes | the instrument, the harness, the protocol — *not* the implementation |
| what it licenses | whatever licence the new repro repo carries (recommend the same CC BY 4.0 posture for the fixture/protocol, so the reuse that generates citations is permitted; code in it can carry the author's choice) |
| what it restores for criterion 5 | a **public** repository with an observable existence, which is the precondition for every form of impact evidence the criterion names — adopters, reuse, independent letters. **A private repo can never accrue this; a public harness can** |
| what it does not do | it does not release the kernel, the weights, or the training pipeline; the "secrets" posture is intact |
| what the paper then says | the availability statement points at **that** artifact, never at `the read-only target repository`, and never at the 404ing `CITATION.cff` URL |

### 8.3 What can be disclosed without any code at all (peer review, reproducibility)

- **Disclosure that costs nothing:** the pre-registered protocol, the falsifier and its threshold, the MDE
  calculation, the fixture **schema** (field names and types) without the 190 rows, the arm definitions
  (families, parameter counts — already in §3.2), the exact evaluation **commands**, the chance-floor
  derivation, the κ procedure and its numbers, and the five owed corrections.
- **Disclosure that genuinely requires the artifact:** the 190 sealed decisions themselves, the per-case
  decider rows (`decider-rows.jsonl`) that make 0.6789 auditable, and the leak-lint re-runs.
- **The honest reviewer-facing sentence** the paper needs: reproduction of this specific paper requires *the
  fixture and the harness*; it does **not** require the the source repository kernel, the weights, or the training
  pipeline. That sentence is what makes "implementation withheld" a defensible choice instead of a
  reproducibility gap — and it is only true once items 1–3 are actually released.

**The practical tension, stated so it is not discovered at review time:** a paper that withholds its
implementation weakens its own reproducibility claim, and TMLR / workshop reviewers may simply ask for the
artifact (TMLR: *"We encourage authors to, whenever possible, upload materials that improve reproducibility.
Specifically, it is suggested that authors submit supplementary material including data or code towards this
end"* — <https://jmlr.org/tmlr/author-guide.html>, fetched 2026-10-15). Note the wording: **encouraged and
suggested, not required** — and the minimal subset in §8.2 is exactly what satisfies that encouragement
without opening the kernel.

---

## 9. `UNVERIFIED` list — what this unit could not confirm

| # | claim | why unverified |
|---|---|---|
| 1 | TMLR would reject / query a submission whose *earlier arXiv version* is licensed restrictively | the TMLR author guide (fetched 2026-10-15) says only the two sentences in §1.4; nothing addresses arXiv licence interplay |
| 2 | specific ICLR / NeurIPS **workshop** licence requirements | ICLR 2025 CFP asserts none for the conference and says "workshops will have their own organization and call for contributions"; no individual workshop CFP was fetched |
| 3 | Zenodo's GitHub integration is *public-repositories-only* | <https://help.zenodo.org/docs/github/enable-repository/> describes toggling from the linked list; **no verbatim "public only" sentence found** |
| 4 | the criterion-5 impact *threshold* ("how much impact is enough") | the criterion text names impact as the requirement and gives no quantity; the totality determination is discretionary |
| 5 | whether the the source repository repo is private vs renamed vs never pushed | GitHub returns 404 unauthenticated; the author's confirmation is the source of "private" |
| 6 | whether anyone outside the author has ever received the AGPL-3.0 source | not observable from this workspace; the author states the repo has been kept private |
| 7 | the fixture owner's consent to publish the 190-case fixture | `CHECKLIST.md` §4 records the fixture/evidence tree as another project's recorded work; consent not obtained or verified by this unit |
| 8 | `cs.LG` primary category and its endorsement domain | open item, carried unchanged from `OPEN_QUESTIONS.md` Q6; not this unit's purpose |
| 9 | whether the author's specific petition would be granted on this record | not a verifiable claim by an agent; the O-1 section (§7) reasons over the criteria's text only |

---

## 10. Decisions

| | decision | state |
|---|---|---|
| **D1** | **Licence = CC BY 4.0** — open paper, withheld implementation (§2) | ✅ **MADE** by the author, 2026-10-15. The TMLR conflict (§1.4) made this the only option compatible with a TMLR submission, and it is the posture Anthropic's two CC BY 4.0 papers actually use (§1.3) |
| **D2** | **What content is disclosed** — i.e. exactly what the paper may say it contains, and whether the §8.2 minimal reproducibility subset is published | ⚠️ **OPEN — and now the load-bearing decision.** The manuscript still promises "re-derivable from the target repository" (§8.1 items 1–6), which the withholding decision contradicts. Either the manuscript's availability/reproduction statements are reframed, or the subset in §8.2 is released — or both |

**Pointers to the rest of the paper's documents.** §8.1's conflict list belongs in
[`CHECKLIST.md`](CHECKLIST.md) §4 and [`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) Q2 (both updated by this unit);
the stale sentence at `MANUSCRIPT.md:606–608` ("the paper's own licence is a separate, deliberate choice that
a human must still make") is now *factually wrong* and must be corrected by whichever unit owns that file —
this unit did not edit `MANUSCRIPT.md`.
