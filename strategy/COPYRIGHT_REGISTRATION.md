# Copyright registration — what to register in this corpus, what it costs, and by when

> **⛔ CLOSED — REGISTRATION DECLINED BY THE AUTHOR, 2026-10-16. DO NOT RE-OPEN.**
>
> The author declined US copyright registration on **2026-10-16** and chose **licence-based
> protection alone**: the PolyForm Noncommercial 1.0.0 instrument for each released piece, carrying
> the `Required Notice: Copyright 2026 Aswin-Ram-K` line, plus the proprietary notice for the main
> repository. This file is retained **as analysis, not as a task list**; nothing below is a pending
> action.
>
> **Consequence, stated honestly:** without registration, **statutory damages and attorney's fees
> under 17 U.S.C. § 504 are unavailable** for these unpublished works, and registration remains
> the precondition under § 411(a) for a US infringement suit on them. What remains is **actual
> damages, the infringer's profits, and the licence's own terms** — including termination of the
> licence for violation under PolyForm's *Violations* clause. The analysis below is unaltered.


**Unit:** UCOPY1 · **Written / all URLs accessed:** **2026-10-16** (UTC) · **Author's registrations to date: none.**
**Purpose (one):** the decision document the author executes to register copyright in the parts of his research
output worth protecting, in his own name, before publishing.

> **This is information, not legal advice.** I am not a lawyer and this is not a legal opinion. It reports what
> the statutes, regulations and the Copyright Office's own pages say as of the access date above. It does not
> tell the author whether to sue, how to enforce, or how to draft anything. Anything I could not read live is
> marked `UNVERIFIED`.

---

## 1. What registration actually adds

Copyright **subsists automatically on fixation**; registration is a separate, optional act. 17 U.S.C. § 102(a)
grants protection to "original works of authorship fixed in any tangible medium of expression". No registration,
no notice and no publication is needed for the right to exist. What registration adds is procedural and
remedial, and it is not small:

**(a) It is the key to the courthouse for US works.** 17 U.S.C. § 411(a), read live 2026-10-16 at
<https://www.law.cornell.edu/uscode/text/17/411>:

> "Except for an action brought for a violation of the rights of the author under section 106A(a), and subject
> to the provisions of subsection (b), **no civil action for infringement of the copyright in any United States
> work shall be instituted until preregistration or registration of the copyright claim has been made** in
> accordance with this title."

**(b) It unlocks statutory damages and attorney's fees — but only if the § 412 timing bar is beaten.** Statutory
damages and fees are the practical remedies in cases where actual damages are hard to prove, which is the normal
case for copied text or code. 17 U.S.C. § 412 and § 504–505 govern; see § 2 below.

**(c) It is prima facie evidence of validity** for registrations made before or within five years of first
publication. 17 U.S.C. § 410(c), read live 2026-10-16 at <https://www.law.cornell.edu/uscode/text/17/410>:

> "In any judicial proceedings the certificate of a registration made before or within five years after first
> publication of the work shall constitute **prima facie evidence of the validity of the copyright and of the
> facts stated in the certificate.** The evidentiary weight to be accorded the certificate of a registration
> made thereafter shall be within the discretion of the court."

**(d) It is the prerequisite to customs recordation.** 19 CFR § 133.31(a), read live 2026-10-16 at
<https://www.law.cornell.edu/cfr/text/19/133.31>:

> "(a) *Eligible works.* Claims to copyright which have been **registered** in accordance with the Copyright Act
> of July 30, 1947, as amended, or the Copyright Act of 1976, as amended, **may be recorded with Customs for
> import protection.**"

That is a border-enforcement measure. It is not a reason for this author to register unless infringing copies
have been imported.

**Statutory-damage amounts.** § 504(c) sets the ranges and § 505 the fee award. I did **not** read § 504(c) live
in this session, so I do not state the current dollar figures: **UNVERIFIED** (the only figures I read live were
in the 1976 House Report reprinted alongside § 504, which quotes the *pre-1999* ranges "$250 and $10,000" /
"$50,000" / "$100" and are obsolete). Read <https://www.law.cornell.edu/uscode/text/17/504> before relying on a
number.

---

## 2. The § 412 timing rule, isolated and emphasised

**This is the deadline that matters, and it is the only one.** 17 U.S.C. § 412, read live 2026-10-16 at
<https://www.law.cornell.edu/uscode/text/17/412>, verbatim:

> "In any action under this title, other than an action brought for a violation of the rights of the author
> under section 106A(a), an action for infringement of the copyright of a work that has been preregistered under
> section 408(f) before the commencement of the infringement and that has an effective date of registration not
> later than the earlier of 3 months after the first publication of the work or 1 month after the copyright owner
> has learned of the infringement, or an action instituted under section 411(c), **no award of statutory damages
> or of attorney's fees, as provided by sections 504 and 505, shall be made for—**
>
> (1) any infringement of copyright in an **unpublished work** commenced before the effective date of its
> registration; or
>
> (2) any infringement of copyright commenced after first publication of the work and before the effective date
> of its registration, **unless such registration is made within three months after the first publication of the
> work.**"

In one sentence: **register within three months of first publication, or forgo statutory damages and attorney's
fees against anyone who started infringing before you registered.** For unpublished works (clause (1)) there is
no grace period at all — the bar is the effective date of registration, full stop; an unpublished work
registered *before* any infringement is fully covered prospectively.

**What this means for this author, given some work is already public.** The audit record in this workspace says
the author's public surface went live around **2026-10-09/10**:

| Already public | Where recorded | Consequence under § 412 |
|---|---|---|
| 13 mechanisms, **MIT**, public repo, `findings/PAPER-DERIVATION.md` byte-identical `sha256 d98c4359…`, ≤ 2026-10-10 | `strategy/PUBLICATION_STRATEGY.md` header note (marked by UWITH1 per UVER6 5.1); `strategy/DISCLOSURE_INVENTORY.md` P1–P9 | § 412(2) grace runs **three months from first publication**. If first publication is 2026-10-10, the last day to register with remedies intact is on or about **2027-01-10**. |
| Consonance implementation, **AGPL-3.0**, public for ~27.5 h (2026-10-09 04:11 → 2026-10-10 07:51), since withdrawn from the anonymous channel but still served by SHA | `strategy/DISCLOSURE_INVENTORY.md:19`, `:161`, `:265`; `strategy/ARCHIVE_WINDOW_CHECK.md` | Same clock, from the same publication window. Because the object remains reachable by SHA, infringement "commenced" during or after that window is a live § 412 question. |

**The actionable finding: the window is still open, and it is short.** On the dates in this workspace, the
three-month deadline for the *already-public* material is approximately **2027-01-10** — a clock that has been
running since October. It closes the remedy that makes an infringement suit economically possible.

Caveats, so the date is not treated as firmer than it is: first publication is dated from the material's own
publication event, not from this document; the exact date of *each* work's first publication (paper vs. repo
contents vs. the 27.5-hour code window) must be fixed from the repository's own records before a date is relied
on. **UNVERIFIED:** the precise first-publication date of any single work — the audit gives a window
(2026-10-08/09/10), not a per-work first-publication line.

**Consequence of missing it.** The copyright is not lost, and an injunction plus actual damages and the
infringer's profits remain available. But statutory damages and attorney's fees are gone for pre-registration
infringement — and for copied prose or copied source code, actual damages are often nominal and the fee award is
what makes a claim worth bringing.

---

## 3. Fees and the application route — verified live 2026-10-16

Source: **Fees, U.S. Copyright Office, <https://www.copyright.gov/about/fees.html>**, read **2026-10-16**.
Verbatim entries from that page:

| Service (as labelled on the page) | Fee |
|---|---|
| Electronic filing — "**Single author, same claimant, one work, not for hire**" (Single Application) | **$45** |
| Electronic filing — **Standard Application** | **$65** |
| Paper Filing (Forms PA, SR, TX, VA, SE) | $125 |
| Registration of a claim in a **group of unpublished works** | **$85** |
| Registration of a claim in a **group of short online literary works** | **$65** |
| Registration of a claim in a **group of contributions to periodicals** | **$85** |
| Registration of a claim in a group of published / unpublished photographs | $55 |
| Supplementary registration (correction/amplification), electronic | $100 |
| Special handling of a claim | $800 |
| Additional certificate of registration | $55 |
| Handling fee for each additional non-special-handling claim using the same deposit | $50 |
| Full-term retention of a published electronic deposit | $220 |
| Full-term retention of a published physical deposit | $540 |

**Single Application vs. Standard Application, and group registration.** The Single Application is the $45
route and its eligibility is stated on the fee page itself: *single author, same claimant, one work, not made
for hire*. It therefore **cannot** cover a group, and it cannot cover a work with more than one author.
**UNVERIFIED:** the full eligibility confirmation screens (I read the fee label and the Registration Portal's
"Single Application" listing at <https://www.copyright.gov/registration/other-digital-content/>, but not the
step-by-step eligibility rules page). Group options are separate application types with their own forms and
their own conditions (§ 5).

**Change note.** Nothing on the fee page read on 2026-10-16 indicates a recent change; no "recently changed"
banner is present. The $45/$65/$85/$65 figures above are the page's current values as read today. **UNVERIFIED:**
whether any of these changed within the last year — I checked the current page only.

---

## 4. Deposit requirements for a computer program

Governing regulation: **37 CFR § 202.20(c)(2)(vii)**, read live 2026-10-16 at
<https://www.law.cornell.edu/cfr/text/37/202.20>. Verbatim:

**(A)** "For published or unpublished computer programs, one copy of *identifying portions* of the program,
reproduced in a form visually perceptible without the aid of a machine or device, either on paper or in
microform. For these purposes 'identifying portions' shall mean one of the following:"

> **(1)** "The first and last 25 pages or equivalent units of the source code if reproduced on paper, or at least
> the first and last 25 pages or equivalent units of the source code if reproduced in microform, together with
> the page or equivalent unit containing the copyright notice, if any. **If the program is 50 pages or less, the
> required deposit will be the entire source code.** In the case of revised versions of computer programs, if the
> revisions occur throughout the entire program, the deposit of the page containing the copyright notice and the
> first and last 25 pages of source code will suffice; if the revisions do not occur in the first and last 25
> pages, the deposit should consist of the page containing the copyright notice and any 50 pages of source code
> representative of the revised material; or"

> **(2)** "**Where the program contains trade secret material**, the page or equivalent unit containing the
> copyright notice, if any, plus one of the following: the first and last 25 pages or equivalent units of source
> code **with portions of the source code containing trade secrets blocked-out**, provided that the blocked-out
> portions are proportionately less than the material remaining, and **the deposit reveals an appreciable amount
> of original computer code**; or the first and last 10 pages or equivalent units of source code alone with no
> blocked-out portions; or the first and last 25 pages of object code, together with any 10 or more consecutive
> pages of source code with no blocked-out portions; or for programs consisting of, or less than, 50 pages or
> equivalent units, the entire source code with the trade secret portions blocked-out, provided that the
> blocked-out portions are proportionately less than the material remaining, and the remaining portion reveals an
> appreciable amount of original computer code. If the copyright claim is in a revision not contained in the
> first and last 25 pages, the deposit shall consist of either 20 pages of source code representative of the
> revised material with no blocked-out portions, or any 50 pages of source code representative of the revised
> material with portions of the source code containing trade secrets blocked-out, provided that the blocked-out
> portions are proportionately less than the material remaining and the deposit reveals an appreciable amount of
> original computer code. **Whatever method is used to block out trade secret material, at least an appreciable
> amount of original computer code must remain visible.**"

**(C)** screen displays, if claimed: in addition to (A), the deposit must include related screen displays — this
matters only if the author claims the screens as authorship.

**What the redaction provision allows and forbids.**

- **Allowed:** blocking out trade-secret portions of the first and last 25 pages, *provided* the blocked-out
  material is proportionately **less** than what remains, and the deposit still reveals an **appreciable amount
  of original code**. Alternative routes avoid redaction entirely: first-and-last **10** pages in full; or 25
  pages of object code plus 10+ consecutive pages of unobscured source.
- **Forbidden:** a deposit that is mostly blacked out; redacting so much that no appreciable original code
  remains; and — since the rule speaks of "pages" — simply declaring the deposit "too secret to show".
- **The ≤50-page rule:** if the program is 50 pages or less, the deposit is the **entire source code**; the
  trade-secret variant for a ≤50-page program still requires the whole code with the secret portions blocked
  out, subject to the same "proportionately less" and "appreciable amount" limits.
- **Alternative identifying-material route:** § 202.20(c)(2)(vii)(A)(2) itself offers three non-redacting
  alternatives (10 pages full; object code + 10 consecutive source pages). Beyond that, the general
  identifying-material and **special-relief** provisions of § 202.20 (subsection (c)(2)(ii)/(iii) and (d)) are
  the escape hatch when the standard deposit cannot be made. **UNVERIFIED:** I read subsection (c)(2)(vii) in
  full but did not read (c)(2)(ii)–(iii) or (d) live in this session, so the special-relief route is cited from
  memory and must be read at the same URL before use.

**Practical translation for this workspace.** The sanitised trees are 6,184 lines across 15 `.py`/`.ts`/`.js`
files (`.ucurate1/pre/research-publish-packages/`, 154 files total) — comfortably over 50 printed pages, so the
**first and last 25 pages of source code** is the deposit. Because these trees are *already sanitised* (the
private implementation is excluded by construction — see the package README, "What is deliberately NOT here"),
redaction should be unnecessary for them. Redaction is the tool for the **as-audited private tree**, not for the
published package.

---

## 5. Group registration options relevant here

### 5.1 Short online literary works (GRTX)

Source: **37 CFR § 202.4(j)**, read live 2026-10-16 at <https://www.law.cornell.edu/cfr/text/37/202.4>.
Verbatim from the paragraph:

> "(j) *Group registration of short online literary works.* Pursuant to the authority granted by 17 U.S.C.
> 408(c)(2), the Register of Copyrights has determined that a group of literary works may be registered in Class
> TX with one application, the required deposit, and the filing fee required by § 201.3(c) if the following
> conditions are met:"

> "(1) The group may include **up to 50 short online literary works**, and the application must specify the total
> number … a short online literary work is a work **consisting of text that contains at least 50 words and no
> more than 17,500 words**, such as a poem, short story, article, essay, column, blog entry, or social media
> post. **The work must be published as part of a website or online platform**, including online newspapers,
> social media websites, and social networking platforms. **The group may not include computer programs,
> audiobooks, podcasts, or emails.** Claims in any form of authorship other than 'text' or claims in the
> selection, coordination, or arrangement of the group as a whole will not be permitted on the application."

> "(6) The applicant must complete and submit the online application designated for a group of short online
> literary works. The application may be submitted by any of the parties listed in § 202.3(c)(1)."

**Does GRTX apply to research papers?** The word-count test is satisfied — `papers/encoder-crossover-190/
MANUSCRIPT.md` is **9,678 words** and `papers/gated-read-batching/MANUSCRIPT.md` is **5,213 words**, both inside
the 50–17,500 band, and both are "text". Two limits decide it:

- **It requires *online publication as part of a website or online platform*.** An unpublished manuscript does
  **not** qualify for GRTX, because GRTX registers *published* works. Once posted on the author's site, a
  preprint server, or a journal site, it does.
- **The group exists to make a large set cheap.** With only two candidate papers, the $65 group fee is not
  obviously better than the alternatives in § 6, and a group of two is an odd fit for a mechanism designed for
  dozens of short posts.
- If a paper is instead first published **in a journal/periodical**, the closer option is the **group of
  contributions to periodicals** ($85) — a different group option with its own conditions (same author; works
  first published as contributions to periodicals). **UNVERIFIED:** the full conditions of § 202.4(g)
  (contributions to periodicals) were not read verbatim in this session; the fee is verified on the fees page,
  the conditions are not.
- **UNVERIFIED — GRTX's author/claimant condition.** Group options generally require that all works share the
  same author, or the same joint authors, and identical claimant information. I saw that condition text in the
  § 202.4 fetch but could not pin it to paragraph (j) specifically, so I do not quote it as a GRTX requirement.

### 5.2 Group registration of unpublished works

Listed on the verified fee page at **$85** ("Registration of a claim in a group of unpublished works"), and it is
the group option that actually fits this workspace **today**, because the two manuscripts are unpublished. Its
conditions — including the same-author / same-claimant requirement — are in 37 CFR § 202.4 and were not read
verbatim here: **UNVERIFIED** as to the exact paragraph; the **fee is verified**.

### 5.3 Can a work already published under CC BY 4.0 still be registered?

**Yes, on the statute — and no Copyright Office rule was found that says otherwise.** Reasoning, with the
statutes it rests on rather than a remembered blog claim:

- Copyright ownership is not lost by granting a licence. A **non-exclusive** licence is expressly *not* a
  "transfer of copyright ownership": 17 U.S.C. § 101 defines a transfer as "an assignment, mortgage, exclusive
  license, or any other conveyance … **but not including a nonexclusive license**". CC BY 4.0 is a
  non-exclusive public licence, so it conveys rights to the public without moving ownership out of the author.
- A transfer of ownership requires a writing signed by the owner (17 U.S.C. § 204(a)); a public licence
  published alongside the work is not such an instrument. **UNVERIFIED:** I did not read § 101's definition or
  § 204(a) live in this session; both are quoted from memory and should be read at
  <https://www.law.cornell.edu/uscode/text/17/101> and `…/17/204` before being relied on.
- Registration is of a **claim** in a work; the *claimant* is the owner. Nothing in the registration
  regulations read live (§ 202.3, § 202.4, § 202.20, fee page) makes an open licence a bar. **This is a negative
  finding — "no bar found on the pages read", not a positive Copyright Office statement that CC-licensed works
  are registrable. Marked UNVERIFIED as to a positive statement.**
- **Practical consequence:** registering the *claim* does not un-CC the work. The CC BY 4.0 grant already made
  is irrevocable as to material already released under it; registration adds remedies against infringers who
  never took the licence (e.g. a defendant who strips attribution/exceeds the licence and therefore falls
  outside it). Registration does not let the author sue a party who complied with the licence.

---

## 6. The shortlist — what in THIS workspace is worth registering

Artifacts actually examined (all paths relative to the workspace root; contents read in this session):

| # | Artifact (path) | What it is | Registrable? | Published? | Deposit | Redaction needed? | Worth the fee? |
|---|---|---|---|---|---|---|---|
| A | `papers/encoder-crossover-190/MANUSCRIPT.md` (9,678 words) | Paper #3 manuscript — fine-tuned small-encoder head vs. fine-tuned 4B decider, sealed 190-case fixture | **Yes** — literary work (text) | **Unpublished** (`strategy/PAPER_CANDIDATES.md:1023` ranks it "**publish**"; `strategy/O1_EVIDENCE_ASSESSMENT.md:215` states "**Paper #3 unpublished**") | Complete copy of the manuscript (text deposit) | **No** | **YES** — the flagship scholarly claim; $45 Single Application is the cheapest defensible registration in the corpus |
| B | `papers/gated-read-batching/MANUSCRIPT.md` (5,213 words) | Second manuscript (text) | **Yes** — literary work | **Unpublished** (no publication record found; `UNVERIFIED` — no per-paper publication line was found for this one) | Complete copy of the manuscript | **No** | **YES** — $45; a second, independent textual work for one application fee |
| C | `.ucurate1/pre/research-publish-packages/` (154 files; 15 code files, **6,184 LOC**; `packages/exp12-encoder-crossover/{paper,code/{fixture,harness,verify},eval/{preregistration,results,second-labeller}}`) | The author's **public-facing package**: manuscript + sanitised code + evaluation evidence, fresh git history | **Yes** — computer program (source code) and, as a compilation/collective work, the package as a whole | **Unpublished** — README: "**Status: private for now.** Nothing here is announced or published yet" | First and last 25 pages of source code (program > 50 pages) | **No** — sanitised by construction; the README's "What is deliberately NOT here" excludes the private implementation, branches and absolute paths | **YES** — $65; this is the artifact that will actually be public, so this is where enforcement will be needed |
| D | `repro/encoder-crossover-190-SANITISED/` (`fixture/`, `harness/` incl. `train.py`, `evaluate.py`, `collect.py`, `prepare.py`, `analyze.py`, `defect-probe.py`, `lint.ts`, `export-fixture.ts`, `tccommon.py`, `tcmodel.py`; plus `REDACTION_REPORT.md`, `REDACT3_REPORT.md`, `SCRUB_REPORT.md`, `EXCLUDED.md`, `RESIDUALS.md`, `LICENCE_TODO.md`) | The sanitised reproducibility tree and its redaction record | **Yes** — computer program; the 190-case fixture is arguably a compilation | **Unpublished** | First and last 25 pages of source code | Not for the code; the accompanying redaction/scrub reports are process documents, not the work | **NO, not separately** — near-identical expression to C; one registration should cover the shipped expression rather than paying twice for two copies of the same program |
| E | `repro/encoder-crossover-190/` (the **as-audited** tree; private, contains what C and D exclude) | The residual trade secret — private implementation, corpora, weights | **Yes** — computer program | Never published (per `strategy/DISCLOSURE_INVENTORY.md`; while the 27.5 h AGPL window exposed the Consonance implementation, this as-audited tree is the private record) | First and last 25 pages **with trade-secret portions blocked out**; or the 10-page-full / object-code alternatives in § 202.20(c)(2)(vii)(A)(2) | **Yes** — this is precisely the deposit the redaction provision exists for | **OPTIONAL** — $65 only if the author anticipates enforcement. Secrecy, not registration, is what protects this material day to day, and registration does not publish the deposit |
| F | Instrument / fixture — `repro/encoder-crossover-190-SANITISED/fixture/` (`DECISION_CASE_SCHEMA.ts`, `reflex-decisions.ts`), 190 sealed cases | The measuring instrument and its sealed case set | **Thin** — the schema and code are expression; the *cases* are data/compilation, and the *method of measurement* is an unprotectable method (§ 102(b)) | Unpublished | Covered by the program deposit, or as identifying portions of a compilation | No | **NO** — registering it separately buys little: the valuable part (the method) is not protectable, and the expression is inside C |
| G | Harness — `.ucurate1/pre/research-publish-packages/packages/exp12-encoder-crossover/code/harness/` | Collection, preparation, training, evaluation, analysis, linting | **Yes** — computer program | Unpublished | Included in the C deposit | No | **NO, not separately** — it is a directory of C |

### Recommended shortlist and cost

| Order | What | Route | Fee |
|---|---|---|---|
| 1 | A + B — the two unpublished manuscripts | **Group registration of unpublished works** (one application, both works) | **$85** |
| 1-alt | A + B individually, if the group's same-author/claimant conditions do not fit | 2 × Single Application ($45) | $90 |
| 2 | C — the sanitised publish package as a computer program | Standard Application | **$65** |
| 3 | E — the as-audited private tree, redacted deposit | Standard Application | **$65 (optional)** |

**Total recommended: $150** (shortlist 1+2). With the optional private-tree registration: **$215**.
Cheapest acceptable variant (two Single Applications, no group): **$155**.

**Why not more.** D, F and G are expression already inside C; paying a separate fee for each would register the
same program two or three times. The manuscripts are cheap enough to register individually if the group route
turns out not to fit, so nothing here depends on the group conditions being read correctly the first time.

---

## 7. What registration does NOT do

1. **It is not a licence and it does not regulate licensees.** A work released under MIT, AGPL-3.0, PolyForm
   Noncommercial, or CC BY 4.0 remains governed by that licence. Registration gives remedies against those who
   infringe *outside* the licence; it cannot be used against a licensee who complied.
2. **It protects expression only.** 17 U.S.C. § 102(b), read live 2026-10-16 at
   <https://www.law.cornell.edu/uscode/text/17/102>, verbatim:

   > "In no case does copyright protection for an original work of authorship extend to any idea, procedure,
   > process, system, method of operation, concept, principle, or discovery, regardless of the form in which it
   > is described, explained, illustrated, or embodied in such work."

   So the *measurement*, the *architecture*, the algorithm, the experimental method and the decision procedure
   are not protected by copyright — only the particular words and code that express them. The reported numbers
   and facts are likewise not protected.
3. **It does not conflict with the author's trade-secret posture.** Registration and secrecy are compatible: the
   deposit is **not published** as part of the registration record, and § 202.20(c)(2)(vii)(A)(2) exists
   precisely so that a secret program can be registered with the secret portions blocked out. Two caveats, so
   this is not overstated: (i) the Office's registration records — including identifying material from deposits —
   are subject to inspection and copying under its regulations; **UNVERIFIED:** I did not read 37 CFR § 201.2
   live, so read it before assuming total confidentiality. (ii) Registering a work does not excuse a secret
   programme's publication elsewhere; the confidentiality of the *source* is preserved by practice, not by the
   registration.
4. **It is not world copyright.** Protection abroad is treaty-based, not automatic from a US certificate.
   Berne Convention works enjoy protection in member states without formalities (17 U.S.C. § 104 and the § 101
   definition of "Berne Convention work" supply the US side); the certificate's evidentiary weight, statutory
   damages and attorney's-fees remedies are **US** remedies. **UNVERIFIED:** §§ 104 and 101 were not read live
   in this session.
5. **It does not create the copyright.** The copyright existed on fixation (§ 102(a)). Registration changes what
   the author can *recover*, not whether he owns something.

---

## 8. Ordered checklist

1. **Fix first-publication dates per work.** Before anything else, write down, for each work, the date and place
   it was first published (public repo commit + push time; the 27.5-hour code window; each manuscript's posting
   date). This sets the § 412 clock.
2. **Register the already-public works first** — anything first published around **2026-10-09/10** must be
   registered on or before approximately **2027-01-10** to keep statutory damages and fees (§ 412).
3. **Register the two unpublished manuscripts** as a group of unpublished works ($85), or individually
   (2 × $45 = $90) if the group conditions do not fit.
4. **Register the sanitised publish package** as a computer program ($65), depositing the first and last 25 pages
   of source code from `.ucurate1/pre/research-publish-packages/packages/exp12-encoder-crossover/code/`.
5. **Decide on the private as-audited tree** (`repro/encoder-crossover-190/`) — register only if enforcement is
   anticipated, with the trade-secret portions blocked out per § 202.20(c)(2)(vii)(A)(2), keeping at least an
   appreciable amount of original code visible.
6. **Use the online (eCO) route** at the Registration Portal; keep the Single Application ($45) only for a
   genuinely single-author, single-claimant, non-work-for-hire, one-work claim.
7. **Record the deposit copies and the receipt.** Keep the exact deposit bytes, so a later supplementary
   registration or an infringement claim can be tied to what was filed.
8. **Re-check the fees page and the GRTX/unpublished-group conditions** at copyright.gov on the day of filing —
   this document's fees are current as of **2026-10-16** only.

---

## Appendix — evidence log

**URLs fetched live, with access date 2026-10-16:**

| URL | What it supplied |
|---|---|
| <https://www.law.cornell.edu/uscode/text/17/412> | Verbatim § 412 (quoted in full, § 2) |
| <https://www.law.cornell.edu/uscode/text/17/411> | Verbatim § 411(a) first sentence (quoted, § 1a) |
| <https://www.law.cornell.edu/uscode/text/17/410> | Verbatim § 410(c) (quoted, § 1c) |
| <https://www.law.cornell.edu/uscode/text/17/102> | Verbatim § 102(b) (quoted, § 7.2) |
| <https://www.law.cornell.edu/cfr/text/37/202.20> | Verbatim 37 CFR 202.20(c)(2)(vii)(A)(1), (A)(2), (C) (quoted, § 4) |
| <https://www.law.cornell.edu/cfr/text/37/202.4> | Verbatim 37 CFR 202.4(j)(1), (j)(6) (quoted, § 5.1) |
| <https://www.copyright.gov/about/fees.html> | All fee figures in § 3, verbatim from the page |
| <https://www.copyright.gov/registration/other-digital-content/> | Computer Programs listed among registrable digital content; links to Single Application, group options (unpublished works, short online literary works), and the GRTX group |
| <https://www.law.cornell.edu/cfr/text/19/133.31> | Verbatim 19 CFR 133.31(a) (quoted, § 1d) |

**Workspace artifacts examined by path:** `papers/encoder-crossover-190/MANUSCRIPT.md` (9,678 words),
`papers/gated-read-batching/MANUSCRIPT.md` (5,213 words), `.ucurate1/pre/research-publish-packages/README.md`,
`.ucurate1/pre/research-publish-packages/LICENSE` ("MIT License / Copyright (c) <YEAR> <COPYRIGHT HOLDER>"),
`.ucurate1/pre/research-publish-packages/packages/exp12-encoder-crossover/` tree,
`repro/encoder-crossover-190-SANITISED/` tree (incl. `harness/`, `fixture/`, `REDACTION_REPORT.md`,
`REDACT3_REPORT.md`, `SCRUB_REPORT.md`), `repro/encoder-crossover-190/`, `strategy/PAPER_CANDIDATES.md:1023`,
`strategy/O1_EVIDENCE_ASSESSMENT.md:215`, `strategy/DISCLOSURE_INVENTORY.md:19,161,203,265,308`,
`strategy/PUBLICATION_STRATEGY.md:1–25`, `strategy/PUBLISH_PACKAGE_MANIFEST.md:70,469`,
`strategy/TRADE_SECRET_AUDIT.md:440,474`.

**UNVERIFIED — everything I could not confirm live, listed explicitly:**

1. **§ 504(c)/§ 505 statutory-damage dollar ranges** — not read live; the only figures seen were obsolete ones
   in the 1976 House Report.
2. **§ 101 definition of "transfer of copyright ownership"** and **§ 204(a)** — quoted from memory in § 5.3.
3. **Positive Copyright Office statement on CC-licensed works** — searched, found none; § 5.3 is a negative
   finding plus statutory reasoning.
4. **37 CFR § 202.20(c)(2)(ii)–(iii) and (d)** (identifying material / special relief) — cited from memory in § 4.
5. **37 CFR § 202.4(g)** (contributions to periodicals) conditions — fee verified, conditions not.
6. **37 CFR § 202.4 GRTX author/claimant condition paragraph** — the same-author/claimant requirement was seen
   in the § 202.4 fetch but not pinned to paragraph (j).
7. **37 CFR § 201.2** (inspection/copying of deposits) — not read; § 7.3(i) is a caveat, not a verified rule.
8. **17 U.S.C. §§ 104 and 101 ("Berne Convention work")** — not read live; § 7.4's treaty point.
9. **The exact first-publication date of any individual work** — the workspace records a window
   (2026-10-08/09/10), not a per-work date; the ~2027-01-10 deadline is computed from that window.
10. **Per-paper publication status of `papers/gated-read-batching/MANUSCRIPT.md`** — no publication record found
    for it; treated as unpublished on the strength of the corpus-wide statements.
11. **Whether any fee changed in the last year** — current page read only; no change banner present.
12. **Single Application full eligibility screens** — only the fee-page label and the portal listing were read.
13. **Whether duplicate registrations of the sanitised package and the repro tree would in fact be merged** —
    § 6's "not separately" is a cost judgement, not a Copyright Office rule.

*Nothing in this document is legal advice. It is a record of what the cited primary sources said on 2026-10-16.*
