# Code-Licensing Strategy — source-available, free for personal use, paid for commercial

**Unit:** UCODE1 · **Verification date:** 2026-10-15 (all URLs fetched on this date, UTC)
**Target repo:** `/home/zer0null/Duval` — read-only; nothing in the target was modified.
**Scope:** the code/project licensing decision only. **Not legal advice** (see §8).

---

## ERRATA — unit UMEMO1, 2026-10-15

> **ERRATA — unit UMEMO1, 2026-10-15.** The author clarified his IP position after this memo was
> written: *"i wanna keep the core pieces trade secrets … i only wanna even make public some pieces of
> the core consonance engine itself and not the whole thing as a whole piece **so no licence on the
> main consonance folder that's proprietary**"* (2026-10-15). **§5.1 and §6 Stage 0 are therefore
> superseded for the main Consonance repository.** The original text is **not deleted**: the two
> superseded passages are marked in place (§5.1, §6), and this header says what replaces them, so a
> reader can see the correction.

**The two-tier structure now in force:**

| | **Main Consonance repository** | **Each released piece** |
|---|---|---|
| **Status** | proprietary, private, trade secret | source-available, public |
| **Licence** | **proprietary notice — all rights reserved** (no public licence) | **PolyForm Noncommercial 1.0.0** |
| **Files carried** | `LICENSE` (proprietary notice), `TRADE-SECRET-NOTICE.md`, proprietary README paragraph | `LICENSE` (PolyForm NC + Required Notice), `COMMERCIAL.md`, `CONTRIBUTING.md`, source-available README paragraph |

The main repository is **never published under PolyForm NC**. It is not "unlicensed" in the sense of
having no terms: §5.4's rule — *replace the AGPL file, do not amend it* — still holds, but the file
that replaces it in the main repo is the **proprietary notice**, not PolyForm NC. This is the structure
ULIC2 implemented in `strategy/licence-templates/` and recorded (unresolved) in `PLACEMENT.md` §5
item 4; **this errata resolves it.** The corrected file-by-file table is at **§5.1**.

**Other statements in this memo that assumed the main repository would be PolyForm-licensed** —
corrected where clearly stale, recorded where ambiguous:

*Clearly stale — corrected in the two-tier table at §5.1:* (1) §5.1 "Paid commercial licence … a short
**root-level** `COMMERCIAL.md`"; (2) §5.1 "Contribution policy — a short `CONTRIBUTING.md`"; (3) §5.1
"README language — one plain paragraph" (the main-repo README carries the **proprietary** paragraph;
the source-available paragraph belongs to each released piece); (4) §6 Stage 0; (5) §6 Stage 2
("`consonance` public core"), which implies publishing the core whole — only **extracted pieces** are
released; (6) §6 rule 3 ("before the repo goes public" — it is each **released piece's** repository
that goes public, per `PLACEMENT.md` §3 step 3).

*Ambiguous — recorded, not decided here:* (7) §3.3's note (`:186`) that "§5.1 states the boundary in
plain language in the project's own README"; (8) §4 (`:358`) "say so loudly in the README"; (9) §6
rule 6 ("name it in the README") — these now attach to a **released piece's** README, since the
academic carve-out is a PolyForm NC term and the main repo carries no such licence; (10) §8 (`:583`)
recommending review of "the wording of `COMMERCIAL.md`" — `COMMERCIAL.md` belongs to each released
piece, not to the main repository root. None of (7)–(10) contradicts the final position; they are left
as written because placing the replacement text is ULIC2's task, not this memo's.

**Trade-secret dimension (cross-reference).** §4 states the O-1 cost of a non-commercial licence;
secrecy for the core is an **additional, separate** author decision. A trade-secret posture is not just
a licensing choice — it imposes **ongoing hygiene obligations** (marking, access control, and
non-disclosure across papers, releases and fixtures, with a record of what was withheld and when). The
legal basis and the item-by-item hygiene audit are the subject of
**`strategy/TRADE_SECRET_AUDIT.md`** — unit UTS1, **507 lines / 48,851 bytes, written 2026-10-15
15:31:34**. That file **is on disk in this workspace**; its findings are **not** summarised, imported,
guessed or pre-empted here. The proprietary-main-repo notice and `TRADE-SECRET-NOTICE.md` drafted by
ULIC2 are the implementing documents.

> **CORRECTION — unit UFIX5, 2026-10-15 (append-only errata norm: the paragraph above is corrected in
> place and the withdrawn wording is kept visible below, not silently deleted).** What this errata
> originally said here was: *"being produced by another unit. **That file is not on disk in this
> workspace at the time of this errata** (`PLACEMENT.md` §5 item 3 records the same gap). Its findings
> are **in progress**…"* — **true when written** (UMEMO1 checked before the audit landed; its card was
> written 15:33 against that earlier read) and **false now**: the audit exists at
> `strategy/TRADE_SECRET_AUDIT.md`. Corrected so no reader is told a present file is missing.
> `PLACEMENT.md` §5 item 3 is corrected the same day. **Nothing from the audit's findings has been
> imported into this memo** — only the reference changed.

---

## 0. The final model, and the contradiction it resolves

### 0.1 What the author wants (his words, 2026-10-15)

> *"i want it to be **source available only** — where if they arent making money off of it then its
> cool ..."*
>
> *"**no try before you buy** — if its for commercial purpose they gotta pay — but if its just somebody
> running it at home for themselves as tool then its cool."*
>
> *"for the community merging i meant we let people **publish their modifications** and we integrate
> some of those in house rather than take their code."*

**`source-available` is the author's own term and it is the correct one.** Four requirements:

| # | Requirement |
|---|---|
| 1 | **Source-available only** — never described as open source |
| 2 | **Free for personal / at-home / hobby / research use** |
| 3 | **Commercial purpose → paid. No free commercial evaluation.** Deliberately foreclosed |
| 4 | **Community modifications are welcome and may be published**; the project integrates **ideas, not code** (§5.3) |

### 0.2 The contradiction, stated first and plainly

**AGPL-3.0 and "commercial use is paid" are two different strategies, and the repo currently declares
the wrong one.**

`/home/zer0null/Duval/LICENSE` is **AGPL-3.0**, verbatim:

> "GNU AFFERO GENERAL PUBLIC LICENSE / Version 3, 19 November 2007"
> — `/home/zer0null/Duval/LICENSE`, lines 1–2 (read directly; **not modified**)

AGPL-3.0 **explicitly permits free commercial use.** Its preamble is designed to make sure you have the
freedom to *"distribute copies of free software (and charge for them if you wish)"*; §4 says *"You may
charge any price or no price for each copy that you convey."* What AGPL actually does is **copyleft** —
it controls **source disclosure**, not **who may use the code**. AGPL §13 requires that a modified
version offered over a network *"must prominently offer all users interacting with it remotely ... an
opportunity to receive the Corresponding Source."*

| | AGPL-3.0 (what the repo says) | What the author wants |
|---|---|---|
| Commercial use | **Free and permitted** (§4, preamble) | **Paid** |
| Mechanism | source-disclosure obligation | paid permission / field-of-use limit |
| OSI open source? | **Yes** | **No** (OSD §6 — see §3.2) |
| Fits the four requirements? | **No** — fails requirement 3 outright | — |

So the file in the tree is not merely suboptimal; it grants the exact opposite of requirement 3. **It
must be replaced before publication** (§5.4). This is not a problem, because of §1.

---

## 1. The private-repo relief — nothing is irrevocable yet

Verified 2026-10-15:

```
$ curl -sS -o /dev/null -w "%{http_code}" -L https://github.com/Aswin-Ram-K/Consonance
404
```

An unauthenticated fetch returns **404**, and the author confirms the repo has been kept private.
(A supplementary `api.github.com` call returned HTTP 403 `"API rate limit exceeded"` — a rate limit,
*not* evidence either way. A private repo returns 404 to unauthenticated users by GitHub's design.)

**Consequence: no licence has been granted to anyone.** A licence in a private repository binds nobody,
because no one has received a copy. The AGPL text in the working tree is an **intention, not a grant**,
and the author — as sole copyright holder — may replace it freely. **The choice is entirely open.**

This also removes the usual obstacle: because no contributor code exists, there is no third-party
copyright to negotiate around. **Keep it that way** (§5.3).

---

## 2. Comparison table

`Fits this policy?` is judged against the four requirements in §0.1. "Corporate-adoption risk" = the
likelihood that a company's or foundation's licence policy blocks or slows internal use.

| # | Option | Commercial use? | OSI open source? | Source disclosed? | Corporate-adoption risk | O-1 impact evidence | Reversibility | **Fits this policy?** |
|---|---|---|---|---|---|---|---|---|
| 1 | **AGPL-3.0** (what the repo currently declares) | **Free and permitted** (§4) | **Yes** | Yes, incl. network-served derivatives (§13) | **HIGH** — Google bans it outright | High in research/OSS; suppressed in big tech | None per version (§2) | **NO** — permits free commercial use; fails req 3 |
| 2 | **AGPL-3.0 + paid commercial licence** (dual licensing) | Free *if* you accept AGPL; paid to escape copyleft | **Yes** | Yes for AGPL-compliant users | Medium (AGPL half still banned) | **Highest** of the restricted options | None per version | **NO** — still lets commercial users in free; needs a CLA. Viable only if req 3 changes |
| 3 | **GPL-3.0 + paid commercial licence** | Same as #2, no network clause | **Yes** | On distribution only | Lower than AGPL, still copyleft | High | None per version | **NO** — same reason as #2 |
| 4 | **BUSL 1.1** + Additional Use Grant + Change Date | Paid for production beyond the grant | **No** — it says so itself | Yes; *use* is limited, not disclosure | **HIGH** — ASF Category X | Moderate; forked away (Terraform→OpenTofu) | Governed by Change Date | **PARTLY** — paid commercial ✓, but it *grants* free non-production/eval (unwanted) and *becomes open source* (unrequested). Excluded as needless complexity |
| 5 | **SSPL v1** | **Free**, but must publish the whole service stack to compete | **No** | Yes, radically | **HIGH** — ASF Category X | Low–moderate; drove OpenSearch fork | None per version | **NO** — permits free commercial use |
| 6 | **Elastic License 2.0** | **Free** except hosted/managed service | **No** | Not required | **HIGH** | Moderate | None per version | **NO** — permits free commercial use |
| 7 | **PolyForm Noncommercial 1.0.0** | **No — paid required** | **No** (fails OSD §6) | Yes, source public | **HIGH** — corporate NC bans | **Low — the deliberate cost** (§4) | None per version | **YES — the fit** (§5) |
| 8 | **CC BY-NC 4.0** | **No** | **No** | Yes | **HIGH** | Low | None per version | **NO** — CC itself advises against it for software (§3.4) |
| 9 | **MIT / Apache-2.0** | **Free** | **Yes** | No obligation | **Lowest** | **Highest raw adoption** | None per version | **NO** — gives away the commercial rights req 3 reserves |
| 10 | **Public repo, no licence** | Nobody has rights | **No** | Visible, not licensed | HIGH — unusable by anyone careful | **Zero** — cannot be adopted, so cannot be cited | Fully reversible, generates nothing | **NO** — fails req 2 and 4 at once |

**Options compared: 10.** One fits.

---

## 3. Evidence base

Every claim below traces to a page fetched on **2026-10-15**. Verbatim excerpts are quoted.

### 3.1 AGPL-3.0 permits commercial use
`https://www.gnu.org/licenses/agpl-3.0.en.html` (fetched 2026-10-15, HTTP 200)

> "Our General Public Licenses are designed to make sure that you have the freedom to distribute copies
> of free software (and charge for them if you wish) ..." (Preamble)

> "You may charge any price or no price for each copy that you convey, and you may offer support or
> warranty protection for a fee." (§4)

> "All rights granted under this License are granted for the term of copyright on the Program, and are
> irrevocable provided the stated conditions are met." (§2)

> "if you modify the Program, your modified version must prominently offer all users interacting with it
> remotely through a computer network ... an opportunity to receive the Corresponding Source of your
> version" (§13)

> "You may not impose any further restrictions on the exercise of the rights granted or affirmed under
> this License." (§10) — and §7: *"All other non-permissive additional terms are considered 'further
> restrictions' within the meaning of section 10."*

**§2 gives the one-way-door rule for the whole plan**: once a version is published under a licence, that
grant is **irrevocable**. §7+§10 give the reason the AGPL file cannot simply be annotated with a
non-commercial rider (§5.4).

### 3.2 A non-commercial licence is NOT open source
`https://opensource.org/osd` (fetched 2026-10-15, HTTP 200) — the Open Source Definition:

> "**6. No Discrimination Against Fields of Endeavor**
> The license must not restrict anyone from making use of the program in a specific field of endeavor.
> For example, it may not restrict the program from being used in a business, or from being used for
> genetic research."

`https://opensource.org/licenses` (fetched 2026-10-15) — searched for `polyform`, `business source`,
`BUSL`, `SSPL`, `server side`, `elastic license`, `noncommercial`, `commons clause`: **zero matches.**

**Consequence: the project is "source-available", NOT "open source".** The author already uses the
correct term. Keep using it — calling it open source would be inaccurate, and in an immigration petition
that inaccuracy is cheap to avoid and expensive to be caught in.

### 3.3 PolyForm Noncommercial 1.0.0 — the fit
`https://polyformproject.org/licenses/noncommercial/1.0.0` (fetched 2026-10-15, HTTP 200)

> "**Noncommercial Purposes.** Any noncommercial purpose is a permitted purpose."

> "**Personal Uses.** Personal use for research, experiment, and testing for the benefit of public
> knowledge, personal study, private entertainment, **hobby projects, amateur pursuits**, or religious
> observance, **without any anticipated commercial application**, is use for a permitted purpose."

> "**Noncommercial Organizations.** Use by any charitable organization, educational institution, public
> research organization, public safety or health organization, environmental protection organization, or
> government institution is use for a permitted purpose **regardless of the source of funding** or
> obligations resulting from the funding."

> "**Changes and New Works License.** The licensor grants you an additional copyright license to make
> changes and new works based on the software for any permitted purpose."

> "**Distribution License.** The licensor grants you an additional copyright license to distribute
> copies of the software."

**Two points confirmed against the author's requirements:**

1. **Requirement 2 is satisfied — prong (a) covers "running it at home for themselves as a tool".**
   The quoted list is explicit: *personal study*, *private entertainment*, ***hobby projects***,
   ***amateur pursuits*** — all *"without any anticipated commercial application."* An individual using
   it at home for their own purposes is squarely inside it.
2. **The "without any anticipated commercial application" qualifier is now a property, not a defect.**
   It is exactly the "no free commercial evaluation" behaviour of requirement 3. Under the earlier
   "try before you pay" framing this clause looked like a trap; under the final model it is the feature.
   **No companion evaluation grant is needed or wanted.**
3. **Requirement 4 is satisfied at law** — the Changes and New Works License expressly permits making
   changes and new works, and the Distribution License permits distributing them. A third party may
   therefore fork and publish their own modified version, **for noncommercial purposes**, without
   asking permission. This is the legal basis for the "we let people publish their modifications"
   half of requirement 4.

Note also what the licence does **not** define. Its Definitions section defines *licensor*, *software*,
*you*, *your company*, *control*, *your licenses*, and *use* — **it does not define "noncommercial".**
The only elaboration is the Personal Uses clause quoted above. This is normal for NC licences and it is
why §5.1 states the boundary in plain language in the project's own README rather than leaving a reader
to infer it.

### 3.4 CC BY-NC 4.0 — rejected, on Creative Commons' own advice
`https://creativecommons.org/licenses/by-nc/4.0/` (fetched 2026-10-15, HTTP 200)

> "**NonCommercial** — You may not use the material for commercial purposes."
> "The licensor cannot revoke these freedoms as long as you follow the license terms."

`https://creativecommons.org/faq/` (fetched 2026-10-15):

> "We recommend against using Creative Commons licenses for software."

CC BY-NC also has **no** evaluation carve-out and is not OSI-approved. It is a
documentation/content licence, and CC says so. **Removed from consideration for code.**

### 3.5 BUSL 1.1 — excluded as an instrument for a requirement that no longer exists
`https://mariadb.com/bsl11/` (fetched 2026-10-15) — the canonical Business Source License 1.1 text:

> "The Business Source License (this document, or the "License") **is not an Open Source license**."

> "The Licensor hereby grants you the right to copy, modify, create derivative works, redistribute, and
> make **non-production use** of the Licensed Work."

> "The Licensor may make an Additional Use Grant, above, permitting limited production use."

> "Change Date may vary for each version of the Licensed Work released by Licensor." ... "... Change
> License the GPL Version 2."

BUSL is a **parameterised template** (Licensor, Licensed Work, Additional Use Grant, Change Date, Change
License). It is a good instrument — but it is the wrong one *here*: its free **non-production use** grant
is precisely the free commercial evaluation requirement 3 forbids, and its **Change Date** turns the
project into an open-source project later, which the author did not ask for. It also adds an ASF
Category X problem (§3.9) for no benefit. **Not recommended.**

### 3.6 SSPL v1 — does not do what the author wants either
`https://www.mongodb.com/legal/licensing/server-side-public-license` (fetched 2026-10-15):

> "... Program or a modified version available to third parties as a service, you must make the Service
> Source Code available via network download to everyone at no charge, under the terms of this License."

SSPL **does not forbid commercial use and does not charge for it.** It forces anyone offering the
software *as a service* to publish the source of the entire necessary stack. Not OSI-approved, Category
X at Apache. **Fails requirement 3.**

### 3.7 Elastic License 2.0 — same problem
`https://www.elastic.co/licensing/elastic-license` (fetched 2026-10-15):

> "**Limitations**
> You may not provide the software to third parties as a hosted or managed service, where the service
> provides users with access to any substantial set of the features or functionality of the software."

> "The licensor grants you a non-exclusive, royalty-free, worldwide, non-sublicensable, non-transferable
> license to use, copy, distribute, make available, and prepare derivative works of the software ..."

ELv2 permits ordinary commercial use **for free** and requires no source disclosure. It restricts exactly
one competitive behaviour. **Fails requirement 3.**

### 3.8 Dual licensing / open-core — the established pattern, kept for the record
`https://www.mysql.com/about/legal/licensing/oem/` (fetched 2026-10-15):

> "Oracle provides its MySQL database server and MySQL Client Libraries under a **dual license model**
> designed to meet the development and distribution needs of both commercial distributors (such as OEMs,
> ISVs and VARs) and open source projects."

> "... commercially licensed software under ... the GNU General Public License (the "GPL") must enter
> into a commercial license agreement with Oracle."

This is the established mechanism for pairing a copyleft licence with a paid one. It is **not** the right
instrument here, because it succeeds by *letting commercial users in for free* provided they accept the
copyleft — the opposite of requirement 3. Recorded as the alternative if the requirements ever change
(§5.6).

### 3.9 Adoption cost — documented, institutional, and it applies to the status quo too
`https://opensource.google/documentation/reference/using/agpl-policy` (fetched 2026-10-15) — **relevant
to the licence currently in the tree:**

> "... the consequences of an engineer accidentally depending on AGPL for one of these services are so
> great that we maintain an **aggressively-broad ban on all AGPL software** to doubly-ensure that AGPL
> could never be incorporated in these services in any manner."

> "Do not attempt to check AGPL-licensed code into google3 or use it in a [Google service]. Do not
> install AGPL-licensed programs on your workstation ..."

`https://www.apache.org/legal/resolved.html` (fetched 2026-10-15):

> "Category X: Licenses in Category X may NOT be included in Apache Software Foundation products."
> "You may NOT include the following licenses within Apache products:"
> "... Redis Source Available License (RSAL) ... Confluent Community License Version 1.0 ...
> **Business Source License 1.1** ... Any license including the Commons Clause License Condition v1.0 ...
> **Server Side Public License (SSPL) version 1**"

> "Apache projects may not distribute Category X licensed components, in source or binary form"

So the adoption penalty is **real and institutional**, and it hits **every** option in the table except
MIT/Apache-2.0 — including the AGPL currently declared, and including PolyForm NC (via the general
corporate hostility to NC licences, §7 item 8).

### 3.10 Fork post-mortem — what a licence change costs
`https://opentofu.org/blog/opentofu-announces-fork-of-terraform/` (fetched 2026-10-15, dated
2023-08-25):

> "Two weeks ago, HashiCorp announced they are changing the license to all their core products,
> including Terraform, to the Business Source License (BSL)."
> "... we're proud to announce that we have created a fork of Terraform called OpenTofu."
> "... we've been working on this fork for several days already, with **over 10 engineers across
> multiple companies** working on it."

`https://opentofu.org/` (fetched 2026-10-15):

> "... in response to HashiCorp's switch from an open-source license to the **BUSL**."
> "... the BUSL license has no restrictions for non-commercial use cases."

The lesson is **double-edged and directly relevant to the O-1 goal**: a restrictive licence can cost you
the community (ten engineers forked within two weeks), *but* ten engineers only fork a project that
mattered. **A project nobody uses gets no fork, no manifesto, and no O-1 evidence.** The fork is a
symptom of prior adoption, not a substitute for it.

### 3.11 PolyForm Noncommercial has real (if modest) adopters
`https://polyformproject.org/adopters` (fetched 2026-10-15) lists projects using "PolyForm
Noncommercial License 1.0" and "PolyForm Noncommercial for its vscode-extension library", among others.
The option is real and in use — but note the scale: extensions and niche tools, not
widely-depended-on infrastructure. **That is itself the adoption-cost signal (§4).**

---

## 4. The O-1 trade-off — stated, not argued

USCIS Policy Manual, Vol. 2, Part M, Chapter 4 (fetched 2026-10-15,
`https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4`), criterion 5 for O-1A:

> "**Criterion 5:** Evidence of the beneficiary's original scientific, scholarly, or business-related
> contributions of major significance in the field."

and among the listed examples of relevant evidence:

> "**Contributions to repositories of software, data, designs, protocols, or other technical resources
> with evidence of significant scientific, scholarly, or business-related impact in the field**;"

and, immediately adjacent in the same list, an item that bears directly on this decision:

> "**Evidence of commercial use of the beneficiary's work**, such as commercialization of a research
> innovation;"

The chapter sets the overall bar as a totality determination: for O-1A, the beneficiary must show he is
"one of the small percentage who have arisen to the very top of his or her field."

**The consequence, plainly.** This policy deliberately forecloses commercial evaluation, and commercial
use requires payment. Both choices suppress adoption — the first by removing the frictionless trial that
lets a tool spread inside a company, the second by pricing it out of informal use. **Suppressed adoption
suppresses the third-party impact evidence that criterion 5 rewards**, by two verified mechanisms:

1. **Institutional bans.** Corporate and foundation policies block these licences outright (§3.9), so
   the code never reaches the environments where large, documentable impact happens.
2. **No usage to document.** If companies cannot use it, there is no adoption to cite, and the
   criterion-5 bullet *"Evidence of commercial use of the beneficiary's work"* becomes unavailable as an
   exhibit. Under the previous dual-licensing draft, commercial users existed lawfully and some paid —
   which was *better* evidence. **Under this policy the strongest potential exhibit is legally
   foreclosed.**

**This is a real cost the author has accepted. It is stated here, not argued against.**

**The one lever that softens it, and it is a real one:** PolyForm NC's *Noncommercial Organizations*
clause permits use by *"any charitable organization, educational institution, public research
organization, public safety or health organization, environmental protection organization, or government
institution ... **regardless of the source of funding**"* (§3.3). **Academia, public research
organisations and government labs may use the code for free, including in funded research.** Those are
exactly the users who **cite**, **publish**, **review**, and **build on** work — so a substantial share
of the citable, third-party, scholarly impact evidence survives this policy intact. For an O-1A petition
focused on *scientific and scholarly* impact rather than *business* impact, this materially reduces the
cost.

**Make the most of that lever:** the licence already grants it; say so loudly in the README and the
paper's artifact section, and invite academic users by name. The author's policy buys a smaller
community than Apache-2.0 would — but it can be a *well-cited* one.

---

## 5. Recommendation

### 5.1 The recommended structure (implementable)

> **SUPERSEDED FOR THE MAIN REPOSITORY — unit UMEMO1, 2026-10-15 (see the ERRATA at the top of this
> memo).** The table below describes **one** repository with PolyForm NC at its root. That is no longer
> the structure. The main Consonance repository is **proprietary and stays unlicensed** (proprietary
> notice), and **PolyForm Noncommercial 1.0.0 attaches to each extracted piece that is released
> publicly**, each carrying its **own** `LICENSE`, `COMMERCIAL.md` and `CONTRIBUTING.md`. The original
> table is retained below, unaltered, for the record. **It is replaced by:**

| Tier | File | What it is |
|---|---|---|
| **Main Consonance repo** (proprietary, private, trade secret) | `LICENSE` | **Proprietary notice — all rights reserved** (`PROPRIETARY-LICENSE.txt`), replacing AGPL-3.0. **Not PolyForm NC.** |
| Main Consonance repo | `TRADE-SECRET-NOTICE.md` (root) | Interior trade-secret notice; referenced by the README paragraph and by `LICENSE`. |
| Main Consonance repo | `README` paragraph (Case A) | States that the repository is proprietary and a trade secret. |
| **Each released piece** (source-available, public) | `LICENSE` | **PolyForm Noncommercial 1.0.0** verbatim, with the *"Required Notice: Copyright \<year\> \<author\>"* line. |
| Each released piece | `COMMERCIAL.md` (root of the piece) | Any commercial purpose requires a paid licence; PolyForm NC does not cover it (§5.2). |
| Each released piece | `CONTRIBUTING.md` (root of the piece) | Forks and published modifications welcome under PolyForm NC; **only ideas are integrated, code contributions are not accepted** (§5.3). |
| Each released piece | `README` paragraph (Case B) | "This is **source-available**, not open source. Free to use for personal, hobby, and research purposes. Commercial use requires a paid licence." |
| Both tiers | **Old licence file** | `LICENSE` (AGPL-3.0) **must be replaced, not amended** (§5.4) — in the main repo by the proprietary notice, in each released piece by PolyForm NC. |
| Both tiers | **Evaluation grant** | **None. Explicitly none** (§5.2) — unchanged. |
| Both tiers | **Paid commercial licence** | Offered **directly by the author** as a separate written agreement, priced per use, arranged by contact (§8) — unchanged. |

*Destinations as implemented by ULIC2 in `strategy/licence-templates/PLACEMENT.md` §1. Reason the
licence choice is unchanged for released pieces: the "Why PolyForm Noncommercial and nothing else"
paragraph below still governs **released pieces**, not the main repository.*

**The original §5.1 table (superseded for the main repository, retained for the record):**

| Piece | What it is | Why |
|---|---|---|
| **Licence text** | **PolyForm Noncommercial 1.0.0**, verbatim, as `LICENSE`, with the required notice line — *"Required Notice: Copyright <year> <author>"* | Free for personal/hobby/research use ✓; commercial requires paid permission ✓; source public ✓; modification and redistribution expressly permitted for permitted purposes ✓ (req 1, 2, 3, 4) |
| **Evaluation grant** | **None. Explicitly none.** | No free commercial evaluation (req 3, §5.2) |
| **Paid commercial licence** | Offered **directly by the author**, as a separate written agreement, priced per use, arranged by contact. A short root-level **`COMMERCIAL.md`** states that any commercial purpose requires a paid licence and that the Noncommercial licence does not cover it | Req 3, req 5. No third-party licensor, no marketplace, nothing to operate |
| **Contribution policy** | A short **`CONTRIBUTING.md`** stating: forks and published modifications are welcome under the Noncommercial licence; **only ideas are considered for integration; code contributions and patches are not accepted or merged** | Req 4, and the hygiene rule that keeps the paid tier legally clean (§5.3) |
| **README language** | One plain paragraph: "This is **source-available**, not open source. Free to use for personal, hobby, and research purposes. Commercial use requires a paid licence." | Req 1. Prevents the mislabelling that §3.2 warns about |
| **Old licence file** | **`LICENSE` (AGPL-3.0) must be replaced, not amended** | §5.4 |

**Why PolyForm Noncommercial and nothing else:** it is the only well-established, professionally drafted
template in the comparison table that makes commercial use **paid** while keeping the source **public**
and permitting **modification and redistribution** for permitted purposes. Requirement 3 is the
discriminator: AGPL, SSPL, ELv2, MIT/Apache-2.0 and BUSL all permit free commercial use in some
material form; CC BY-NC is the wrong instrument for code (§3.4); dual licensing lets commercial users in
free (§3.8). **PolyForm NC is the fit.**

### 5.2 The "no anticipated commercial application" clause is the feature, not a bug

PolyForm NC's Personal Uses clause grants free use *"without any anticipated commercial application"*
(§3.3). Under an earlier "try before you pay" framing this looked like it might accidentally exclude a
company evaluating the tool. **Under the final model it is precisely what the author asked for:** a
business evaluating in order to decide whether to buy has an anticipated commercial application, and is
therefore **not** licensed to evaluate for free — it must buy first. **No companion evaluation grant is
needed, and none should be added.** PolyForm Free Trial 1.0.0 exists and would grant a 32-day trial
(fetched 2026-10-15: use *"for less than 32 consecutive calendar days, on behalf of you or your
company, is use for a permitted purpose"*) — **do not use it.** It solves a problem the author does not
have and would directly contradict requirement 3. Likewise BUSL's non-production allowance is excluded
for the same reason (§3.5).

Confirmed for the record, on the author's own example: prong (a) **does** cover *"somebody running it at
home for themselves as tool"* — *personal study*, *private entertainment*, ***hobby projects*** and
***amateur pursuits*** are named, and running it at home as a tool falls inside them.

### 5.3 Contributions: ideas in, code not — the one real risk

The mechanism the author described: others **fork and publish their own modifications** (lawful — §3.3
point 3), the author **reviews them and integrates selected changes in-house by implementing them
himself**, and **no contributor code enters the project**. **No CLA and no DCO are required, because no
third-party code is ever received.**

**The one caveat that does remain, stated plainly:**

> **If the author copies contributed code verbatim into the project, that code arrives carrying the
> contributor's Noncommercial licence — and it then cannot lawfully be included in a paid commercial
> licence.** The commercial tier would silently stop covering part of the codebase.

Copying **ideas, approaches, algorithms and techniques** and writing an **independent implementation** is
fine: **copyright protects expression, not ideas.** That is the whole basis of the mechanism.

**The hygiene rule (this is the operative rule; write it down):**

1. **Integrate by re-implementation. Never by copy-paste. Never merge contributor patches or
   pull requests.** If a fork's change is wanted, read it, understand it, then write the code yourself.
2. **Never accept a patch into the tree.** Not even a one-line fix, and not even with attribution — the
   licence travels with the expression.
3. **Make the boundary provable if it is ever challenged.** Keep a stated policy (`CONTRIBUTING.md`),
   keep merges closed (branch protection / a policy of not accepting PRs), keep a record of where an
   idea came from and that the implementation was independent, and keep the commit history clean of
   contributor authorship on the changed lines.
4. **Say which model is in force.** The policy must state explicitly that *only ideas are integrated and
   code contributions are not accepted*. **If the author ever wants to accept code, the CLA question
   returns** — dual licensing a project that contains third-party code requires a contributor agreement
   granting the right to relicense. Deciding "ideas only" now, in writing, is what avoids that.

### 5.4 The AGPL-3.0 file must be replaced, not amended

`LICENSE` currently contains **AGPL-3.0** (§0.2). Two reasons it must be **replaced** for any public
release:

1. **It grants the opposite of requirement 3** — free commercial use, irreversibly, for any version
   published under it.
2. **A non-commercial rider cannot lawfully be bolted onto AGPL.** AGPL §7 provides that *"All other
   non-permissive additional terms are considered 'further restrictions' within the meaning of section
   10"*, and §10 provides *"You may not impose any further restrictions on the exercise of the rights
   granted or affirmed under this License."* "AGPL + no commercial use" is therefore internally
   contradictory, not merely unusual.

**This is clean to fix**, because of §1: the repo is private, no licence has been granted to anyone, and
the author owns the copyright. **Replace the file before the repository is made public.** Leaving AGPL in
a public repo while intending a non-commercial model would grant rights the author does not intend to
give, and that grant could not be withdrawn for that version (AGPL §2).

*The target's `LICENSE` was read and deliberately left untouched by this unit — the replacement is the
author's action to take.*

### 5.5 Consequences accepted (for the record)

- **Corporate adoption will be sharply limited.** No free commercial evaluation, plus institutional
  hostility to non-commercial licences (§3.9). Expect few or no corporate users, and expect some
  companies to decline even to look.
- **O-1A criterion 5 impact evidence is reduced** — §4 states the mechanism. The mitigation is the
  academic/research/government carve-out, which is real and worth exploiting deliberately.
- **The choice is permanent per version.** AGPL §2 (*"irrevocable"*) and CC (*"cannot revoke these
  freedoms"*) both establish that once a version is published under a licence, that grant stands.
  **Piece-by-piece release is fine; every released piece is permanent** (§6).
- **Revenue is uncertain.** A solo researcher's commercial-licence income may be small or zero. **This
  strategy's primary payoff is control and optionality, not revenue.** Stated honestly.

### 5.6 Alternative, if the requirements ever change

**AGPL-3.0 + a paid commercial licence (dual licensing)** — the established pattern (§3.8). Choose it if
the O-1 impact goal later outweighs the "commercial must pay" goal, or if revenue matters more than
exclusivity. It is genuinely OSI open source, maximises citable adoption, and still sells something.
**Cost of switching later:** it requires a CLA before any code contribution is accepted, and it cannot
retroactively apply to versions already published under PolyForm NC. **The decision is cheaper now than
later.**

### 5.7 Explicitly not recommended

- **CC BY-NC 4.0 for code** — Creative Commons itself says *"We recommend against using Creative Commons
  licenses for software"* (§3.4).
- **PolyForm Free Trial 1.0.0** — grants the free commercial evaluation requirement 3 forbids (§5.2).
- **BUSL 1.1** — grants free non-production (evaluation) use and later becomes open source; neither was
  asked for, and it adds an ASF Category X problem (§3.5, §3.9).
- **SSPL, Elastic License 2.0** — they permit free commercial use, so they do not do the job (§3.6, §3.7).
- **Publishing with no licence** — visible code with no grant is unusable by anyone careful: zero
  adoption, zero O-1 evidence, and it fails requirements 2 and 4 at once (table option 10).
- **A bespoke "Noncommercial but not quite PolyForm" licence** — the worst of all worlds: not a
  recognised template, not reviewable by a corporate legal team in an afternoon, and a magnet for
  ambiguity. **Never invent licence terms.**

---

## 6. Gradual-disclosure plan

The author's intent — *"slowly disclose pieces rather than just the whole thing"* — is fully compatible
with §5.1. The governing constraint:

> **Once a piece is published under a licence, that grant cannot be revoked for that version.**
> AGPL §2: *"irrevocable provided the stated conditions are met."* CC: *"The licensor cannot revoke these
> freedoms."* **Piece-by-piece release is fine; each piece is permanent.**

| Stage | Repo | Licence | What it buys |
|---|---|---|---|
| 0 (now, private) | `Duval` (private) | **Replace AGPL with PolyForm NC; add `COMMERCIAL.md`, `CONTRIBUTING.md`; state the policy** | Preserves every option; nothing granted yet (§1) |
| 1 | **`consonance-eval`** — public eval harness, datasets, benchmark scripts | **PolyForm NC 1.0.0** (or Apache-2.0 if maximum citation reach is preferred over consistency) | A public artifact for the paper; research users can reproduce results for free |
| 2 | `consonance` public core | **PolyForm NC 1.0.0 + `COMMERCIAL.md`** | Source-available core; free personal/research use; paid commercial use |
| 3 | Kernel / training pipeline | stays private | No grant made, no obligation incurred; optionality retained |
| 4 | Staged releases of kernel pieces | PolyForm NC, piece by piece | Each released piece is irrevocably NC — release only what you are content to bind |
| 5 | Optional, later | Revisit §5.6 | If O-1 impact or revenue goals change, a *new* version can use a new licence |

> **SUPERSEDED — unit UMEMO1, 2026-10-15 (see the ERRATA at the top of this memo).** In the table
> above, **Stage 0** ("Replace AGPL with PolyForm NC; add `COMMERCIAL.md`, `CONTRIBUTING.md`; state the
> policy") is superseded: the main repository is **proprietary and stays unlicensed** — it receives the
> **proprietary notice**, `TRADE-SECRET-NOTICE.md` and a proprietary README paragraph, **not PolyForm
> NC**, and it is **not published at all** (the author: *"no licence on the main consonance folder
> that's proprietary"*). **Stage 2** is likewise read as **extracted pieces**, each released in its
> **own** repository under PolyForm NC + `COMMERCIAL.md` + `CONTRIBUTING.md`; the core engine is **not**
> published whole. Stages 1 and 4 (piece-by-piece release of separate artifacts) and Stage 3 (kernel
> stays private) stand unchanged. Rule 3 ("before the repo goes public") therefore binds **each
> released piece's repository**, per `PLACEMENT.md` §3 step 3.

**Rules that make this safe:**

1. **Separate repositories, not one repo with mixed licences.** Per-directory licence files work but are
   a compliance minefield; separate repos make the boundary unambiguous.
2. **Never release a piece you might want to license differently later.** The grant is irrevocable per
   version, so the private/public line is a one-way door. Keep the kernel private until the model has
   settled; publish the eval harness now because it is the piece you want cited.
3. **Put `COMMERCIAL.md` and `CONTRIBUTING.md` in place *before* the repo goes public**, so the paid
   tier and the ideas-not-code policy exist from day one, with no window of ambiguity.
4. **Replace `LICENSE` before publishing** (§5.4). Never publish with AGPL still in the tree.
5. **Do not describe the release as "open source."** Use **"source-available."** Verified: BUSL says of
   itself *"is not an Open Source license"*, and NC licences fail OSD §6 (§3.2).
6. **Lean on the academic carve-out deliberately** — name it in the README and the artifact section, and
   invite research users. It is the O-1 mitigation (§4).
7. **Date every release and keep the licence text of each version.** The audit trail is itself evidence
   of a deliberate programme — useful for O-1 and for anyone evaluating the commercial licence.

---

## 7. UNVERIFIED

Items a reader should not treat as established by this memo:

1. **The repository's private status is inferred from an unauthenticated 404** on
   `https://github.com/Aswin-Ram-K/Consonance` (2026-10-15). A 404 is also what a *non-existent* repo
   returns, and GitHub returns 404 to unauthenticated users for private repos. The author's own
   confirmation of privacy is the corroborating evidence. **Not verified via an authenticated session.**
2. **The GitHub API check failed** with HTTP 403 `"API rate limit exceeded"` (2026-10-15). Not evidence
   either way; recorded so the 404 is not over-read.
3. **BUSL 1.1's full `Change Date` / `Change License` definition text was not cleanly extracted.** The
   canonical page (`https://mariadb.com/bsl11/`) rendered as a large navigational page; only fragments
   were recovered verbatim. BUSL is excluded from the recommendation, so this gap does not affect the
   recommendation — but do not rely on this memo as a BUSL reference.
4. **`https://www.hashicorp.com/en/license-faq` returned HTTP 429** (bot/rate limiting). HashiCorp's own
   rationale is therefore **not** cited from source; the OpenTofu fork evidence (§3.10) is used instead.
5. **The Elastic License 2.0 text was taken from the rendered page**
   (`https://www.elastic.co/licensing/elastic-license`). Raw fetches of
   `raw.githubusercontent.com/elastic/elasticsearch/.../ELASTIC-LICENSE-2.0.txt` returned empty for both
   `main` and `7.10` (possibly a moved path). Treated as authoritative here; the raw file is not.
6. **No OSI page states in so many words "non-commercial licences are not open source."** §3.2 is
   **derived** from two verified facts: OSD criterion 6 as quoted, and the absence of
   PolyForm/BUSL/SSPL/Elastic/Commons Clause from `https://opensource.org/licenses`. The derivation is
   sound; it is a derivation.
7. **Revenue is an estimate, not a fetched fact.** "Commercial-licence income may be small or zero"
   (§5.5) is judgement. No source supports it and none should be assumed.
8. **No company policy page banning PolyForm Noncommercial by name was located.** The "corporate NC
   ban" claim rests on the OSI/OSD position and on the ASF and Google precedents for adjacent licences
   (§3.9), **not** on a fetched corporate page naming non-commercial licences. Treat that rating as
   reasoned, not cited.
9. **The O-1 citations are to the USCIS Policy Manual**, which is policy guidance — not the regulation
   (8 CFR 214.2(o)) and not a precedent decision. Adjudication is a totality determination; the
   criterion list is evidence-marshalling, not a scorecard.
10. **The copyright principle in §5.3 (expression vs. ideas) is stated as general principle, not quoted
   from a fetched source.** No statute or case was fetched for this memo to support it. It is
   well-established and it is the basis of the recommended hygiene rule, but it is **not** cited here,
   and the provability measures in §5.3 are what actually protect the author in practice.
11. **The `What to do if you ever accept code` point assumes a CLA would be sufficient.** The specific
    relicensing grant such an agreement must contain was **not** verified from a primary source: the
    Apache ICLA text now redirects to a PDF (`https://www.apache.org/licenses/icla.txt` → *"has moved to
    https://apache.org/licenses/icla.pdf"*), and text extraction from that PDF returned nothing. If the
    author ever moves to accepting code, **this must be researched properly before doing so.**

---

## 8. This is not legal advice

This memo is a research synthesis of publicly available licence texts and policy pages, produced by a
non-lawyer, to frame a decision. It is **not legal advice**, no attorney-client relationship arises from
it, and nothing here should be relied on as a substitute for advice from a qualified attorney licensed
in the relevant jurisdiction.

The model in §5 is deliberately simple, which removes most of the complexity a lawyer would otherwise
have to untangle — there is no dual-licensing mechanism, no contributor agreement, and no relicensing
chain to audit. **But one review is still worth buying: a short (roughly 20-minute) review of the
commercial licence terms** — the wording of `COMMERCIAL.md` and the standard paid agreement offered to
commercial users. That is the document that will actually be tested if a company uses the software
commercially without paying, and it is the one piece of this plan that is drafted rather than adopted
off the shelf.

Two further questions are worth raising in the same conversation, because they are cheap to ask and
expensive to get wrong: (a) whether any **employment, institutional affiliation, or funding** encumbers
the copyright in this code — an employer or funder with rights in the work would break the commercial
tier outright; and (b) whether the intended **commercial licence terms** are consistent with the
author's immigration posture, given that the software's commercial use is itself a factor the O-1
analysis may consider (§4).

---

*End of memo. Prepared by unit UCODE1, 2026-10-15. Target repo `/home/zer0null/Duval` was read, never
modified; no git state in the target was changed. `LICENSE` was deliberately left untouched.*
