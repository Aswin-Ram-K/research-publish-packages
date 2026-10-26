# VERIFICATION_REPORT — independent re-check of UH2 and UV1

**Unit:** UVER1 (independent verifier; not the author of either document)
**Date:** 2026-10-15 · **All URLs re-fetched:** 2026-10-15 · **Tool calls used:** 23 of 55
**Documents verified:**
- [`strategy/VISA_INDIA_EUROPE.md`](VISA_INDIA_EUROPE.md) (322 lines, unit UH2)
- [`strategy/PUBLICATION_STRATEGY.md`](PUBLICATION_STRATEGY.md) (406 lines, unit UV1)

---

## 0. Contradicted claims — called out at the top

**NONE. Zero contradicted claims were found in either document.**

Every load-bearing claim I was asked to falsify reproduced against a live primary source, with the
verbatim wording the documents quote. Two documents that both report an honest `UNVERIFIED` list and
whose load-bearing rows all survive independent re-fetch is the outcome; I did not manufacture a
correction to have one.

The one *overstated* claim (§2, PUB-7 below) is a presentation/caveat-completeness issue with a
concrete replacement wording. It changes no decision.

---

## 1. Verdicts

| Document | Verdict |
|---|---|
| `strategy/VISA_INDIA_EUROPE.md` | **pass** |
| `strategy/PUBLICATION_STRATEGY.md` | **pass-with-corrections** |

Both verdicts are supported by the measured tables below. Neither document asserts a load-bearing
value as fact without a source that I could open; where a source was unreachable (udi.no, migri.fi)
both the author's note and my own re-test agree, so those are **coverage limits, not defects**.

---

## 2. Claim-by-claim measurement table

Classification key: `confirmed` · `not_reproduced` (could not check — coverage limit) · `overstated`
(true but stated too strongly) · `unverified` · `contradicted` (wrong).

### 2.1 `strategy/VISA_INDIA_EUROPE.md`

| # | Claim | Doc + line | What I measured | Correct value + source (fetched 2026-10-15) | Class |
|---|---|---|---|---|---|
| V1 | Sweden researcher permit: doctorate **or** eligibility to start a doctoral programme | L49, L185 (P2) | Verbatim on the page | "You can be granted a residence permit as a researcher if you have a doctorate or are eligible to start a doctoral programme and are invited here by a research principal that has been approved by the Swedish Research Council." — [migrationsverket.se researchers](https://www.migrationsverket.se/en/you-want-to-apply/work/employee-or-self-employed/researchers.html) | **confirmed** |
| V2 | A **business** can be an approved research principal | L49, L184 (P1) | Verbatim | "A research principal can be a Swedish higher education institution, some other type of research institution, or a business." — same URL | **confirmed** |
| V3 | Maintenance SEK 9,700/month | L49, L251 | Verbatim | "...at least SEK 9,700 per month." — same URL | **confirmed** |
| V4 | Fee SEK 1,500 (employee); family SEK 1,500; child SEK 750 | L49 | Verbatim | "Employees: SEK 1,500. Adult family members: SEK 1,500 Children: SEK 750" — same URL | **confirmed** |
| V5 | Researcher processing 1 month (75% complete) / 2 months incomplete | L49, L189 (P6) | Verbatim table row | "Highly qualified workers (including ICT permits, EU Blue Cards and researchers) 1 2" — [migrationsverket.se waiting-times](https://www.migrationsverket.se/en/contact-us/waiting-times.html) | **confirmed** |
| V6 | Sweden Blue Card: five years' relevant professional experience **replaces** 180 credits | L50, L191 (P8) | Verbatim | "Your higher education must correspond to at least 180 higher education credits. Alternatively, you can have at least five years of relevant professional experience." — [migrationsverket.se eu-blue-cards](https://www.migrationsverket.se/en/you-want-to-apply/work/employee-or-self-employed/eu-blue-cards.html) | **confirmed** |
| V7 | Blue Card threshold **SEK 53,625/month since 15 July 2026** | L50, L80 | Verbatim | "Since 15 July 2026, the salary threshold is SEK 53,625 per month." + "1.25 times the average gross salary in Sweden published by the National Mediation Office" — same URL | **confirmed** |
| V8 | Blue Card fee SEK 2,000 | L50 | Verbatim | "Employees/self-employed people: SEK 2,000." — same URL | **confirmed** |
| V9 | Ordinary work-permit floor **SEK 34,470/month** (90% of median SEK 38,300, from 16 June 2026) | L51, L82–83, L254 | Verbatim | "As of 16 June, the median salary is SEK 38,300, which means that you must have a salary/wages of at least SEK 34,470 (90 per cent of the median salary) a month in order to be granted a work permit." — researchers page | **confirmed** |
| V10 | **Three-year** PR rule from 11 June 2026 for research/doctoral/Blue Card time, additive | L49, L50, L190 (P7), L253 | Verbatim, Swedish | "Efter 11 juni förkortas tiden ... du kan få permanent uppehållstillstånd efter **tre års sammanhängande tillstånd** med något av följande: uppehållstillstånd för forskning ... svenskt EU-blåkort. Om du har haft flera av dessa tillstånd kan tiden räknas ihop." — [news 2026-05-25](https://www.migrationsverket.se/nyheter/nyhetsarkiv/2026-05-25-nya-regler-for-dig-som-ar-forskare-eller-doktorand.html) | **confirmed** |
| V11 | 4-in-7 PR rule still available for work permits | L51 | Verbatim | "...fyra år under en sjuårsperiod" — same news URL | **confirmed** |
| V12 | Post-research work-seeking permit 12–18 months | L53, L192 (P9) | Verbatim | "minst tolv månader och högst 18 månader" — same news URL | **confirmed** |
| V13 | Row 5 processing "1 month complete / 3 incomplete" ("Look for work after completing research") | L53 | Table row found | "Look for work after completing research 1 3" — waiting-times URL | **confirmed** |
| V14 | Self-employed route URL works | L52 | HTTP 200 | [egen-foretagare.html](https://www.migrationsverket.se/du-vill-ansoka/arbeta/anstalld-eller-egen-foretagare/egen-foretagare.html) returns HTTP 200 | **confirmed** |
| V15 | **Denmark Pay Limit**: no specific educational background; **DKK 552,000**; fee DKK 6,810; 1 month / up to 3 | L55, L84, L186 (P3), L233–238 | Verbatim, nyidanmark.dk direct | "It is not required that you have a specific educational background or that your job is within a specific professional field." + "The minimum amount DKK 552,000 (2026 level). The minimum amount is regulated every year on 1 January." + "Processing fee DKK 6,810,-" + "1 month / up to 3 months" — [nyidanmark Pay Limit Scheme](https://www.nyidanmark.dk/en-GB/You-want-to-apply/Work/Pay-Limit-Scheme) | **confirmed** |
| V16 | Denmark researcher: fee DKK 6,810, 1 month / up to 2, employment at "a research institute **or company**", "particular research related reasons" | L54 | Verbatim | "You are a researcher and have been offered employment at a research institute or company in Denmark." + "particular research related reasons" + "Processing fee DKK 6,810,-" — [nyidanmark Researcher](https://www.nyidanmark.dk/en-GB/You-want-to-apply/Work/Researcher) | **confirmed** |
| V17 | Germany §18g(2): Blue Card **without** the academic qualification for ISCO-08 **133 or 25**, salary ≥45.3%, ≥3 years' experience in last 7 | L72, L187 (P4), L263–266 | Verbatim statute | "abweichend von § 18 Absatz 2 Nummer 4 ... in einem Beruf, der zu den Gruppen 133 oder 25 ... gehört, wenn 1. die Höhe des Gehalts mindestens 45,3 Prozent der jährlichen Beitragsbemessungsgrenze ... beträgt ... a) die auf einer in den letzten sieben Jahren erworbenen, mindestens dreijährigen Berufserfahrung ... beruhen ... b) deren Niveau mit einem Hochschulabschluss ... vergleichbar ist" — [§18g AufenthG](https://www.gesetze-im-internet.de/aufenthg_2004/__18g.html) | **confirmed** |
| V18 | Germany §18d: research permit decided within 60 days | L71 | Verbatim | "In den Fällen des Satzes 1 Nummer 1 Buchstabe a ist die Aufenthaltserlaubnis innerhalb von 60 Tagen nach Antragstellung zu erteilen." — [§18d AufenthG](https://www.gesetze-im-internet.de/aufenthg_2004/__18d.html) | **confirmed** |
| V19 | **MSCA PF requires a PhD** | L95, L278–280 | Verbatim | "The Postdoctoral Fellowships action targets researchers holding a PhD" + "should have a PhD degree at the time of the deadline for applications" — [MSCA Postdoctoral Fellowships](https://marie-sklodowska-curie-actions.ec.europa.eu/actions/postdoctoral-fellowships) | **confirmed** |
| V20 | MSCA PF host can be a business/SME; "the beneficiary … needs to recruit the researcher" | L95, L123 | Verbatim | "...together with a host organisation, which can be a university, research institution, business, SME or other organisation..." + "The beneficiary organisation recruiting the researcher also needs to be established in an EU Member State..." — same URL | **confirmed** |
| V21 | **ERC Starting Grant requires a PhD** (0–10 y post-PhD) | L98, L278–280 | Verbatim | "Researchers of any nationality with 0-10 years of experience since completion of PhD" — [ERC Starting Grant](https://erc.europa.eu/apply-grant/starting-grant) | **confirmed** |
| V22 | ERC StG up to €1.5M/5 y, +€1M, up to +€2M for relocation from non-associated third countries | L98 | Verbatim | "up to €1.5 million for a period of 5 years ... an additional €1 million ... the maximum additional funding may be up to €2 million" — same URL | **confirmed** |
| V23 | Norway skilled worker: degree **or** "special qualifications", expressly exceptional | L63, L188 (P5) | Verbatim | "skilled worker permits are only granted on the basis of special qualifications in exceptional circumstances and that extensive documentation is required" — [EURAXESS Norway](https://www.euraxess.no/norway/information-assistance/work-permit) | **confirmed** |
| V24 | Precedent table P1–P10 = **9 rule-level precedents, 0 named individual cases**; every row's URL opens | L182–193 | Read all 10 rows; opened every URL in P1–P9 | P1–P9 all resolve and their pages carry the quoted text (see V1–V2, V6, V10, V12, V15, V17, V23). P10 has no URL and is the explicit negative row ("**NOT ESTABLISHED — UNVERIFIED**"). No personal name appears anywhere in the document; §4 and §5.23 both state no named case is asserted and forbid citing one. | **confirmed** |
| V25 | udi.no and migri.fi blocked (author's stated coverage limit) | L62, L65, L202–203 | Re-tested myself | `udi.no/.../researchers/` → **HTTP 403**; `migri.fi/en/researcher` → **HTTP 403**. Author's block claim reproduced. | **confirmed** (coverage limit, not a defect) |
| V26 | ERC-2027-STG call dates: "opened 22 July 2026, deadline 14 October 2026" | L98 | Not present on the page I fetched (ERC StG page carries the eligibility/budget text, not a 2027 call calendar) | Claim withheld from the "correct value" column — not reproduced. Not load-bearing: the row is self-flagged *aspirational* and V21 independently establishes the PhD gate, so the decision does not turn on the date. | **not_reproduced** |
| V27 | `make-it-in-germany.com` "bot-blocked" (Radware) | L206 | Returned **HTTP 200** to my curl with a browser UA | Author's experience not reproducible from my client; this is client/UA-dependent, **not** a falsification. No value in the document depends on it (German law text was used instead, correctly). | **not_reproduced** |
| V28 | Row 1 evidence "page carries news items dated 2026-10-01"; row 26 IND "Last update: 11 September 2026" | L49, L74 | Not re-checked | Cosmetic metadata, not load-bearing. | **unverified** |
| V29 | Everything in §5 (the 23-item UNVERIFIED list) | L197–224 | Spot-checked: items 1–2 (udi.no, migri.fi) reproduced by direct HTTP 403; item 4 (`local_web_search` broken) matches the verifier brief exactly | The list is **honest and complete for every load-bearing row**: rows 9–13 (DK), 14–19 (NO/FI), 20–22 (IS/EE), all India rows, all funder amounts, and every non-Swedish PR cell are marked UNVERIFIED inline *and* collected. Nothing load-bearing is asserted as fact without an openable source. | **confirmed** |

### 2.2 `strategy/PUBLICATION_STRATEGY.md`

| # | Claim | Doc + line | What I measured | Correct value + source (fetched 2026-10-15) | Class |
|---|---|---|---|---|---|
| P1 | arXiv assigns a free DataCite DOI to every submission, "at no cost to the authors"; prefix `10.48550` | L30–31, L90–97, S12 | Verbatim | "All articles submitted to arXiv are automatically assigned DOIs that correspond to their arXiv ID, and the associated article metadata is submitted to DataCite **at no cost to the authors**." + "What is arXiv's DOI prefix with DataCite? 10.48550" — [info.arxiv.org/help/doi.html](https://info.arxiv.org/help/doi.html) | **confirmed** |
| P2 | JOSS: "**no fees** for submitting or publishing" | L63, L189, S16 | Verbatim | "There are no fees for submitting or publishing in JOSS." — [joss.readthedocs.io submitting](https://joss.readthedocs.io/en/latest/submitting.html) | **confirmed** |
| P3 | JAIR: "no publication fees are charged to authors"; ~three months to review | L64, S18 | Verbatim | "...no publication fees are charged to authors." + "JAIR reviews papers within approximately three months of submission" — [jair.org about](https://www.jair.org/index.php/jair/about) | **confirmed** |
| P4 | **TMLR: no fee** (verifiable negative on Home / FAQ / Submissions / Author guidelines) | L62, L342–343, S15 | Re-read all four pages; regex for `fee\|APC\|publication charge\|article processing` returned only incidental substrings ("feedback", "e-mail") — **no fee, APC or payment mechanism anywhere** | No fee is stated. The memo's `UNVERIFIED`-in-the-affirmative marking (L342–343) is the honest form. **The "minimum cost" premise survives: no missed fee at any of the three recommended venues.** | **confirmed** |
| P5 | TMLR: "approximately 9 weeks after submission"; not open to surveys since 2026-09-01; arXiv preprints accepted | L62, L299, L366–367, S13 | Verbatim | "...the rolling review process aims to deliver a final decision approximately 9 weeks after submission" + "As of September 1, 2026, TMLR no longer considers survey papers for review" + "You can still submit, even if a preprint of your work already is available online" — [jmlr.org/tmlr/faq.html](https://jmlr.org/tmlr/faq.html) | **confirmed** |
| P6 | TMLR emphasis + ISSN 2835-8856 | L62, S14 | Verbatim | "TMLR emphasizes technical correctness over subjective significance" + "ISSN 2835-8856" — [jmlr.org/tmlr/](https://jmlr.org/tmlr/) | **confirmed** |
| P7 | **JOSS blocked until ≈2027-03-28** from earliest commit 2026-09-28 under the ">6 months public" rule | L24, L42, L174–187, L207, L210 | Rule verbatim; arithmetic re-derived | Rule: "The repository must have been public for **more than six months** prior to submission, with active development spanning that period." + "There must be evidence that the software is being used for research" + "Your paper must not focus on new research results" — [joss submitting](https://joss.readthedocs.io/en/latest/submitting.html). 2026-09-28 + 6 months = 2027-03-28 ⇒ earliest compliant submission 2027-03-29. §5 states the date flatly from commit history while **§11.10 itself concedes the repo's *public* status is `UNVERIFIED`** (JOSS's clock runs from public availability, not the first commit). The date is sound as a *lower bound* in all cases, so the claim is not wrong — but the §11.10 caveat is not carried into §5's conclusion, and the "≈" hides a one-day optimism. | **overstated** (mild; presentation) |
| P8 | ICLR 2027 workshop: contributions ≈1 Feb 2027 → verdict 26 Feb 2027; accepted papers must be public on OpenReview | L23, L65, L206, S19 | Verbatim | "Suggested Submission Deadline for Workshop Contributions: **1 Feb 2027**" + "Mandatory Accepted Paper Notification Date*: **26 February 2027**, 11.59pm AoE" + "make all accepted papers publicly available on OpenReview" — [iclr.cc CallForWorkshops 2027](https://iclr.cc/Conferences/2027/CallForWorkshops) | **confirmed** |
| P9 | NeurIPS 2026 workshops closed: proposal 2026-06-06, contributions 2026-08-29, notification 2026-09-29 | L66, S20 | Verbatim | "Workshop Application Deadline: June 06, 2026" + "Suggested Submission Date for Workshop Contributions: August 29, 2026" + "Mandatory Accept/Reject Notification Date: September 29, 2026" — [neurips.cc CallForWorkshops 2026](https://neurips.cc/Conferences/2026/CallForWorkshops) | **confirmed** |
| P10 | Distill dead since 2021-03-04 | L70, L310, S23 | Verbatim, page-dated | "After five years, Distill will be taking a break." — editorial dated **March 4, 2021** — [distill.pub](https://distill.pub/) | **confirmed** |
| P11 | Zenodo invalidates its own DOI when a record already carries an external DOI | L101–103, S24 | Verbatim | "content found to already have an external DOI will have the Zenodo DOI invalidated and the record updated to indicate the original external DOI" — [about.zenodo.org/policies](https://about.zenodo.org/policies/) | **confirmed** |
| P12 | O-1: 8 CFR 214.2(o)(3) requires one major award **or at least three of eight**, then a separate final-merits determination | L123–131, S1–S2 | Verbatim | "(B) **At least three** of the following forms of documentation:" + "one of the small percentage who have arisen to the very top of the field of endeavor" — [eCFR 8 CFR 214.2](https://www.ecfr.gov/current/title-8/chapter-I/subchapter-B/part-214/section-214.2) | **confirmed** |
| P13 | The memo does **not** claim publication is itself a criterion; it says authorship is one of eight and 3 of 8 are needed | L26–28, L143–146, L161–164 | Read the argument end-to-end; cross-checked against eCFR | Memo: "**publication is not an O-1 criterion — authorship is, and authorship is only one of eight criteria of which three are needed**". eCFR (B)(5) = "Evidence of the alien's original scientific, scholarly, or business-related contributions of major significance in the field"; (B)(6) = "Evidence of the alien's authorship of scholarly articles in the field, in professional journals, or other major media". The memo's criterion numbering, the "at least three", and the separate final-merits step all match the regulation. | **confirmed** |
| P14 | USCIS reading: authorship "alone, regardless of caliber, would satisfy the criterion"; publishing does not by itself establish major significance | L136–141, L156–157, S3, S7 | Verbatim | "authorship of scholarly articles in the field in professional journals or other major media, alone, regardless of caliber, would satisfy the criterion at 8 CFR 214.2(o)(3)(iii)(B)(6)" + "Evidence that the beneficiary's work was funded, patented, or published, while potentially demonstrating the work's originality, will not necessarily establish, on its own, that the work is of major significance to the field." — [USCIS Policy Manual Vol. 2 Pt. M Ch. 4](https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4) | **confirmed** |
| P15 | Criterion (1) glossed as "a lesser nationally or internationally recognized prize or award" | L152, S8 | Verbatim | "USCIS determines whether the award is a lesser nationally or internationally recognized prize or award" — same USCIS URL | **confirmed** |
| P16 | Measured repo facts: **857** commits, earliest **2026-09-28**, head `24f339c`, one tag `m0-baseline`, fixture **2,220 lines / 191 `id:` matches / 145,031 B**, non-shallow, `CITATION.cff` with no `doi:` | L39–46, S28 | Re-measured read-only on `/home/zer0null/Duval` | `git rev-list --count HEAD` = **857**; earliest = `2026-09-28 dae60e0 "Initial commit: DUVAL M0 …"`; head = `24f339c0c3994f7af5c6f505bd8b65744612f853` (2026-10-14); `.git/shallow` absent; `git tag` = `m0-baseline`; `wc -l` = **2220**; `grep -c "id:"` = **191**; `wc -c` = **145031**; `CITATION.cff` `cff-version: 1.2.0`, `type: software`, `license: AGPL-3.0`, `version: "0.0.1"`, **no `doi:`**. Every value matches exactly. | **confirmed** |
| P17 | `PAPER_CANDIDATES.md` is 710 lines (the input the memo takes as given) | L4 | `wc -l` = **710** | Matches. | **confirmed** |
| P18 | MLSys 2027: submissions open 2026-10-19, deadline 2026-10-30 12:00 PDT | L67, S21 | Not reproduced in my fetch — the MLSys 2027 homepage now reads "The call for papers has been posted! Submissions to MLSys 2027 is through OpenReview." The Oct 19/30 '26 strings did not appear. | Not reproduced. The memo **already flags this itself** in §11.5 ("Whether those dates belong to MLSys 2027's main track or a co-located event is `UNVERIFIED`"), so the marking is honest; and the memo tells the reader to decide explicitly (L329–330) rather than plan against it. | **not_reproduced** |
| P19 | Software Heritage SWHID is ISO/IEC 18670, standardised 2025-04-23 | L76, S25 | FAQ page did not yield the string to my fetch | Not reproduced (page rendered/parsed differently for me). Not load-bearing — it is the *third* citation handle, after the arXiv and Zenodo DOIs. | **not_reproduced** |
| P20 | Preprints.org footer: "free preprint server supported by MDPI" | L73, S26 | String not present in my fetch | Not reproduced (footer is client-rendered). Venue is listed only as an arXiv fallback. | **not_reproduced** |
| P21 | §11 UNVERIFIED list (13 items: Zenodo price, TMLR price, registration, cs.\* endorsement domains, MLSys track, AAAI-27, ICLR Blogposts, OSF/HAL/TechRxiv/SSRN, labeller price, repo public visibility, best-paper awards, arXiv licences) | L338–367 | Spot-checked items 1–3, 5, 10, 13 against sources | **Honest and complete.** Item 2 (TMLR price) is correctly marked UNVERIFIED-in-the-affirmative and P4 above independently confirms the negative. Item 10 correctly isolates the one premise JOSS's date depends on. Item 13's positive claim (TMLR surveys) is marked *verified*, and I confirm it (P5). | **confirmed** |

---

## 3. The required lists, explicitly separated

### 3.1 `contradicted` (wrong claim, replacement value required)
**Empty.** No claim in either document was falsified.

### 3.2 `not_reproduced` (I could not check it — coverage limit, **not** an author failure)
1. **ERC-2027-STG call dates** "opened 22 July 2026, deadline 14 October 2026" — `VISA` L98. The ERC
   Starting Grant page carries eligibility and budget text but no 2027 call calendar in the fetch;
   the dates live on ERC's Work Programme / call-calendar surface. Not load-bearing (the row is
   self-flagged aspirational and the PhD gate is independently confirmed at V21).
2. **MLSys 2027 dates** — `PUB` L67 / S21. Homepage now advertises a posted CFP via OpenReview; the
   `Oct 19 '26` / `Oct 30 '26` strings did not reproduce. Already self-flagged in `PUB` §11.5.
3. **Software Heritage ISO/IEC 18670, 2025-04-23** — `PUB` L76 / S25. Not reproduced in my fetch.
4. **Preprints.org footer wording** — `PUB` L73 / S26. Not reproduced (client-rendered footer).
5. **`make-it-in-germany.com` bot-block** — `VISA` L206. Returned HTTP 200 to my client, so the
   author's Radware interception is client-dependent. This is a *reproducibility* gap, not a
   falsification, and no value in the document rests on it.
6. **Cosmetic metadata**: `VISA` L49 ("news items dated 2026-10-01") and L74 (IND "Last update: 11
   September 2026"). Not re-checked; not load-bearing.

### 3.3 `overstated` (true, but stated more strongly than its own evidence supports)
1. **`PUBLICATION_STRATEGY.md` §5, L185 (JOSS unblock date)** — "The six-month gate therefore cannot
   clear before **≈2027-03-28**" is derived from commit history alone, while the document's own
   **§11.10 (L360–362)** says the repository's *public* visibility — the thing JOSS actually measures
   from — is `UNVERIFIED`. As a lower bound the inference is sound; the defect is that the §11.10
   caveat is not carried inline, and "more than six months" puts the earliest compliant date one day
   later than the stated one.
   **Suggested replacement value:** *"The six-month gate cannot clear before **2027-03-29**, and only
   if the repository has been publicly available since 2026-09-28 — a premise that is itself
   `UNVERIFIED` (§11.10). If public availability began later, the gate clears later."*
   **Impact:** timeline shift of at most a day for a step the memo already places in Jul 2027 (L210).
   No decision changes.

### 3.4 `unverified` (the claim I could not check; author did **not** assert it as fact)
Item 3.2.6 above (the two cosmetic metadata stamps). Note the important asymmetry: every *load-bearing*
item I could not reproduce was either already marked `UNVERIFIED` by the author (`PUB` §11.5) or is
non-decisional. **No load-bearing claim in either document is asserted as fact without a source I
could open.**

---

## 4. Minor observations (no verdict impact — recorded for completeness)

- **`VISA` L51 citation label.** The evidence cell labels its second link "news 2026-06-16" but the
  URL is the EU Blue Cards page. The `SEK 34,470` figure is confirmed independently on that page and
  on the researchers page (V9), so this is a cosmetic label/URL mismatch, not a content mismatch.
- **`VISA` §4 framing.** P10 is a table row that establishes a *negative* (no named individual case),
  so "9 rule-level precedents and 0 named individual cases" is the correct reading of a 10-row table.
  The framing is honest and the document twice forbids citing a personal precedent from it (L193,
  L224).
- **`VISA` L52 fee comment** "(self-employed, same fee class as employees)" is corroborated by the
  Blue Card page wording "Employees/self-employed people: SEK 2,000."
- **Containment check.** My operations on `/home/zer0null/Duval` were read-only: `git rev-list`,
  `git log`, `git tag`, `ls`, `wc`, `grep`, `cat`. No write, no `git` state change, no hook installed.
  (`git status --porcelain` showed pre-existing modifications from other units — I made none.)

---

## 5. What would change my verdict

- **VISA → fail** if any of V1–V17 (the rank-1 Denmark Pay Limit row, the Sweden researcher/Blue
  Card rows, or §18g(2)) were shown to be misread rather than quoted — in particular if nyidanmark's
  Pay Limit page dropped the "not required that you have a specific educational background" sentence,
  since the memo's rank-1 ranking rests entirely on it. I re-read that page directly and it is there.
- **VISA → pass-with-corrections** if a *precedent-table* URL (P1–P9) were found dead or whose page did
  not carry the quoted text. All nine opened and matched.
- **PUB → pass** if the JOSS date were restated as the conditional in §3.3, or if §11.10's caveat were
  moved inline at §5. That single wording change is the only correction I am carrying.
- **PUB → fail** if any of the three recommended venues carried a submission or publication fee that
  the memo missed. I searched TMLR Home/FAQ/Submissions/Author-guide for `fee|APC|publication
  charge|article processing` and found none; JOSS and JAIR state "$0" affirmatively. **The `$0`
  premise holds.**
- **Either → fail** if a named individual precedent, invented statistic, or invented URL were found.
  None was. I also confirmed the two `UNVERIFIED` block claims (udi.no, migri.fi) are real — HTTP 403
  on my own client — so those coverage limits are truthfully reported rather than convenient.
