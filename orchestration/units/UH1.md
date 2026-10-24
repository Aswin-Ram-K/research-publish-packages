# UH1 — US visa routes independent of student status (+ real precedents)

**Status:** done · **Date:** 2026-10-14 · **Bound:** max 60 tool calls · **Used:** 35

## One purpose
Map the **US** routes that do not depend on student status for an independent AI/agent-runtime researcher
whose school has stopped issuing OPT/CPT, and find **real, verifiable precedents** matching that profile.

## Write paths (touched nothing else)
- `strategy/VISA_US_ROUTES.md` (deliverable)
- `orchestration/units/UH1.md` (this card)
- `orchestration/handoffs/UH1.json`

## Inputs read
- `AGENTS.md` (workspace contract, handoff shapes)
- `strategy/PAPER_CANDIDATES.md` (what the research record actually contains, incl. §E's O-1 leverage
  analysis and the recommended #3 → #1 → #4 sequencing)

## Method
Primary sources only where reachable: eCFR (Title 8, served but truncated at §214.2(f)) → Cornell LII
e-CFR mirror for the §(h) and §(o) text; GovInfo US Code for INA 214 and 212; USCIS Policy Manual
(2 M.3/M.4, 6 F.2/F.5, 2 H index); USCIS premium-processing and I-140 pages; the AAO non-precedent
decisions index, from which five 2026 EB-1A decision PDFs were downloaded and text-extracted with
`pdftotext`. Failed/unreachable and marked as such: `web_search` (no API key), `local_web_search`
(SearXNG returned no results), travel.state.gov Visa Bulletin (HTTP 403).

## Findings that matter
1. **The unit card's own citation was wrong.** 8 CFR 214.2(h)(8)(ii)(B) is about *unused petition numbers*.
   The cap-exemption provision is **8 CFR 214.2(h)(8)(iii)(F)** (definitions at **(h)(19)(iii)(C)**).
2. **INA 214(g)(5)(C)** — the US-master's exemption — is **not** an employer cap exemption; it is capped at
   20,000 and still runs through the lottery. The employer exemptions are (g)(5)(A) and (B) only.
3. **8 CFR 214.2(h)(8)(iii)(F)(4)** is the concurrent/off-site unlock: ≥50% of work time on duties
   furthering a qualifying entity's research mission, where **telework/remote work counts as work "at" the
   institution** and "USCIS will focus on the job duties to be performed, rather than where the duties are
   physically performed". **(F)(5)** is the trap: if cap-exempt employment ceases and the person was never
   counted, they become cap-subject.
4. **The nonprofit-research test is "a fundamental activity"**, not "primary purpose" — the regulation says
   an organisation "may perform or promote more than one fundamental activity", and applied research
   expressly "may have specific commercial objectives".
5. **Degree equivalency is real and quantified**: 8 CFR 214.2(h)(4)(iii)(D)(5) — three years of specialised
   training/work experience per missing year of college; master's equivalence needs a bachelor's + 5 years;
   a doctorate only if the specialty requires it.
6. **O-1A has no degree requirement** — the words "degree"/"baccalaureate" appear nowhere in the eight
   criteria at 8 CFR 214.2(o)(3)(iii).
7. **O-1 self-petition is barred** ("O beneficiaries may not petition for themselves"), but a **US agent**
   may petition for the traditionally self-employed, and an **owned corporation/LLC** may file — 2 USCIS-PM
   M.3(A), quoted verbatim.
8. **6 USCIS-PM F.2 criterion 5 and 2 USCIS-PM M.4 criterion 5** expressly list *"Contributions to
   repositories of software, data, designs, protocols, or other technical resources with evidence of
   significant scientific, scholarly, or business-related impact"* — the most on-point verified text for an
   open-source agent-runtime record (added by the 8 Jan 2025 O-1 policy alert).
9. **EB-1A self-petition is express**: 8 CFR 204.5(h)(3)(5) "No offer of employment required"; 6 USCIS-PM
   F.2(A) "anyone can file the petition… including the alien who may file as a self-petitioner".
10. **NIW's catch and its escape hatch**: EB-2 eligibility is a statutory prerequisite (advanced degree or
    exceptional ability); 6 USCIS-PM F.5(D)(1) expressly contemplates "a person who has computer science
    education or experience that does not equate to the definition of an advanced degree" qualifying via
    **exceptional ability**.
11. **Precedents verified (6):** five real AAO non-precedent EB-1A decisions dated 24–31 Aug 2026
    (In Re 41750160, 43913762, 43912394, 43728055, 43193587), each downloaded and read; **Kazarian v. USCIS,
    596 F.3d 1115 (9th Cir. 2010)** verified as quoted inside AUG272026_03B2203 — *"(upholding agency's
    decision to deny EB-1 classification to Ph.D.-holding theoretical physicist working with researchers at
    Caltech)"*. Four of the five confirm in practice that meeting three criteria is not enough.
12. **A required negative finding:** **no** real AAO or precedent decision involving a software/AI
    researcher or engineer without a PhD was found in the window examined. **No case number was invented.**
    This is recorded in the deliverable's `UNVERIFIED` list (§13 item 5) with the search method for counsel.

## Honesty controls applied
- Regulation text and practice commentary are in separately labelled sections; §9 tabulates which claims are
  "the regulation says" vs "in practice".
- A 16-item `UNVERIFIED` list is a required part of the deliverable; nothing on it is relied on elsewhere.
- The Visa Bulletin's HTTP 403 is reported rather than papered over: **no priority date is quoted**, and the
  "EB-1A is less backlogged for Indians" premise is marked unverified even though it is plausible.
- No fee number is printed (could not extract any; one verified figure — the $600 Asylum Program Fee — is
  quoted with its URL).
- "Not legal advice" is stated in the document header, in the closing line, and in the memo's §1/§12.

## Bound accounting
35 tool calls used of a 60 bound. Two research surfaces were unavailable (no search API key; local SearXNG
empty; travel.state.gov 403) and are reported as gaps rather than blockers.

## Remainder (not attempted, deliberately)
- O-1-specific AAO decisions: the non-precedent index page's visible window held the EB-1A (B2) and one
  other category; the O-1 (I-129) category directory was not located within the call budget.
- Practitioner case studies of independent/open-source researchers obtaining O-1A/EB-1A: secondary, none
  verified, none cited.
