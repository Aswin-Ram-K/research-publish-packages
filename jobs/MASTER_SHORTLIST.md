# MASTER SHORTLIST — the one list to act on

## VERIFICATION — 2026-10-15, unit UFINAL2 (append-only errata; UCONS2's prose below is unchanged)

UCONS2 died while self-verifying and never wrote its card or handoff. This note records an independent
re-derivation of every number in this report from `MASTER_SHORTLIST.jsonl` (284 rows) and the seven source
`JOBS.jsonl` files (295 rows across the six declared sweeps + 8 in `jobs/coverage-repair/` = 303).

**Matched exactly.** 284 rows out, of which **276** from the six declared sweeps and **8** tagged
`source_unit:"coverage-repair"` (both-ways reporting carried out as §9 describes). `action`: apply_now 10,
apply_later 62, watch 117, exclude 95. `route_class`: cap_exempt_us 168, of which **105 open**; o1_suitable 51;
eu_researcher_permit 21; india 30; cap_subject_fallback 14. **19 duplicates merged** (Σ k−1 over the 16
`merge_note` rows = 19; 303−19=284 and 295−19=276 both hold). No-PhD: **26** rows, **13** of them open
non-funding role rows. Individual-funding rows **13** of 30 funding rows, **8** of the 13 from JOB4
(`evals-safety-foundations`), matching its FINDINGS Shortlist B. Deadlines with an explicit year inside 60 days
of the 2026-10-15 build: **3** (2026-10-31, 2026-11-04, 2026-11-08). §4 dates all trace to source: Foresight
**2026-10-31 23:59 PDT** verbatim in `evals-safety-foundations/JOBS.jsonl` `deadline` (labelled as verified);
SINTEF **04/11/2026** and KU Copenhagen **08-11-2026** in `scandinavia-europe/FINDINGS.md`; ANRF Ramanujan
**31.12.2026 17:00** in `india-ai/JOBS.jsonl` `deadline`. All 10 Top-10 URLs and all 5 ranks-11–15 URLs are
present in the JSONL; `rank` is a unique 1…284; all 284 `url` values are well-formed http(s); Wadhwani AI is
`status:"none_found"` (0 open rows); all 4 Anthropic rows come from `job-boards.greenhouse.io/anthropic/…` and
no row carries the aggregator-only title or any aggregator URL; `unreachable` = 58 rows / 64 raw across the six
units.

**ERRATUM 1 — one merge is wrong (the only bad merge found).** Row `rank 216` merged **three genuinely
different** UK AISI grant programmes that merely share one URL — *The Challenge Fund* (up to £200,000/project),
*The Alignment Project* (up to £1,000,000/project) and *Systemic AI Safety Grants Programme* (amount not stated)
(`evals-safety-foundations/JOBS.jsonl` [22],[23],[24]). The surviving row is titled and valued as the Challenge
Fund; `merge_note` unions nothing; the Alignment Project and Systemic rows and their amounts are **absent from
the JSONL** (§5's prose text is the only place they survive here). §8's claim that these three "were
**deliberately NOT merged**" is therefore the opposite of what happened. Cause: the merge key collapsed rows
whose `role` is null on org+URL, then persisted the winner's `title` in `dedupe_key`, hiding the collision —
the same rule did **not** fire on the six ANRF rows (4 of them also share one URL), so it was applied
inconsistently. **No other merge is wrong**: the other 17 are the same opening twice — METR/Apollo across
units, Redwood *MTS* vs *MTS (AI control research)*, Coefficient Giving under two org spellings, EleutherAI,
MITRE, and the six `us-national-labs` self-duplicates (SLAC, INL, NREL, ANL, Aerospace, Battelle) — each verified
as same organisation + same normalised role + same normalised URL.

**ERRATUM 2 — §6/§7 `no_relevant_role` count.** The table says **14**; the true count is **13** (13 blocker
carriers, 13 `status:"no_relevant_roles"` rows). With 13 the §6 breakdown sums to the correct 95 `exclude` rows
(58+15+13+7+1+1); §7's non-live total of 87 is separately correct as 58 unreachable + 15 `none_found` +
13 `no_relevant_roles` + 1 `closed`.

**ERRATUM 3 — §8 merge-composition table.** The rules-as-listed (12 / 2 / 4 / 1) do not describe the 19 actual
merges. Measured: exact org+title+URL **7** (METR Embedded 2, METR Evaluation Execution 2, Apollo Evaluations 1,
METR Offensive Security 1, METR Platform Engineer 1); title-annotation **2** (Redwood, Coefficient Giving);
both-non-open coverage **8** (EleutherAI, MITRE + the six national-lab self-duplicates); mis-merge **2**
(Erratum 1). The total 19 is right; only the breakdown is wrong.

**ERRATUM 4 — two smaller numeric claims.** §2: "6 more NREL openings sit between ranks 20 and 30" — the six
other coverage-repair NREL rows are at ranks **23, 24, 32, 64, 65, 83** (two in 20–30, four in 32–83). §8: "5
distinct ANRF schemes … share `awards_fellowship`" — the master holds **6** ANRF rows on **two** URLs; **4**
share `page/english/awards_fellowship` (Ramanujan, N-PDF, J.C. Bose, TARE) and 2 share `page/english/research_grants`
(PM ECRG, PAIR). The substantive claim (none merged) holds. §6 item 1 also attributes a `source_unreachable`
blocker to the Wadhwani rows; both carry `no_live_posting` (one also `student_status_likely`).

**Status/action agreement.** 87 rows carry a non-open `status`, all `exclude`; the other 8 `exclude` rows are
`status:"open"` and are *explained*, not silent — 7 JPL `clearance` + 1 LLNL `citizenship_required`. No row
disagrees with its `action` without a recorded blocker.

**ERRATA — UCONS3, 2026-10-15 (append-only; supersedes the counts in the UFINAL2 note above where they differ).**
A re-split pass, made in a **new unit rather than by editing the bad merge in place**, restores the two programmes
the rank-216 mis-merge lost and corrects §8's claim that they were deliberately left apart.

- **ERRATA A — rank 216 re-split (the fix).** §8's "Deliberately NOT merged … **3 distinct UK AISI grant
  programmes** share `aisi.gov.uk/grants`" was **false when written**: all three had been collapsed into one
  row. Three rows now exist, from `evals-safety-foundations/JOBS.jsonl` [22],[23],[24] and all sharing that URL:
  rank **216** *The Challenge Fund (AI safety research grants)* — up to £200,000/project; rank **216.1** *The
  Alignment Project (grants programme)* — up to £1 million/project (**new row**); rank **216.2** *Systemic AI
  Safety Grants Programme* — amount not stated; first 20 projects selected (**new row**). All three carry the
  source's own `status:"closed"`, `individuals_may_apply:"no"`, `phd_or_affiliation_required:"yes"` and their
  source amounts, deadlines and eligibility text; all three are `action:"exclude"` with blockers
  `posting_closed` + `phd_required`. **No field was invented** — every value on 216.1/216.2 is copied verbatim
  from its source row, and the closed/institution-gated status was preserved (not upgraded). The surviving 216
  row's `merge_note`, which claimed a 3-row merge, was cleared because it is no longer a merged row; nothing
  else on it changed except its `rank_reason`.
- **Rank technique — decimal siblings.** No row was re-ranked or reordered. The two restored rows take decimal
  ranks `216.1` and `216.2` adjacent to their sibling — the same slot-preserving technique UCORR1 used for `NC1`
  at rank `6½`. Every pre-existing integer rank stays valid, list order is unchanged, and only the two new rows
  are added.
- **ERRATA B — counts, before → after (current figures in bold).** rows out **284 → 286** (current **286**);
  six-declared-sweep rows **276 → 278** (current **278**); coverage-repair **8** (unchanged); duplicates merged
  **19 → 17** (current **17**), because the bad merge had removed 2 rows (k−1 = 2) that this re-split restores;
  funding rows **30 → 32** (both AISI rows are funding rows), so §5's "13 of 30" now reads "13 of **32**".
  Arithmetic closes both ways: 303−17=286 and 295−17=278. §8's merge-composition breakdown therefore becomes
  **7/2/8/0 = 17** (Erratum 3's 7/2/8/2 = 19, minus the 2 that were the mis-merge). The eight coverage-repair
  rows and the dual reporting are untouched; the six-sweep-only filter instruction remains
  `source_units != ["coverage-repair"]` and now yields **278** rows. In the UFINAL2 note above, `284`/`276`/`19`
  are the **pre-fix** figures and remain as that unit wrote them.
- **ERRATA C — sweep for further instances (card step 3).** Every source `JOBS.jsonl` was re-grouped by
  normalised URL (and by org+URL) and every group holding more than one source row was re-judged. **No second
  collapse of genuinely different programmes was found.** The other multi-row groups are true duplicates or
  same-gap coverage records: METR/Apollo across units, Redwood *MTS* vs *MTS (AI control research)*, Coefficient
  Giving under two org spellings, MITRE and EleutherAI (one gap recorded by two units), and the six
  `us-national-labs` self-duplicates. The six ANRF rows on two URLs (4 on `awards_fellowship`, 2 on
  `research_grants`) were **not** collapsed — but they were also not collapsed by the rule that should have
  collapsed them, which is the inconsistency UFINAL2 named. The two `title`-schema units
  (`evals-safety-foundations`, `india-ai`) are the only units with no `role` field, and the mis-merge fired on
  exactly one of their shared-URL groups. So the defect is **not systemic in effect** (one bad merge), though
  the rule that produced it remains inconsistently applied. §4's "Already closed" list already names all three
  AISI programmes, so it needed no change.

**Read paths.** `jobs/MASTER_SHORTLIST.jsonl`, `jobs/{agent-runtime-global,evals-safety-foundations,india-ai,scandinavia-europe,us-national-labs,us-nonprofit-research}/JOBS.jsonl`, `jobs/coverage-repair/JOBS.jsonl`, `jobs/scandinavia-europe/FINDINGS.md`.

---

**Unit:** UCONS2 · **Built:** 2026-10-15 · **Corpus observed:** 2026-10-15 (all source sweeps)
**Answer file:** [`MASTER_SHORTLIST.jsonl`](MASTER_SHORTLIST.jsonl) — **286** rows, one per opening (was 284 before the UCONS3 re-split; see ERRATA B).
**Question answered:** *of the ~300 openings the six sweeps found, which do I actually apply to, and in what order?*

This file **merges existing verified data only**. Nothing here was searched for, and no opening, deadline,
salary, URL or eligibility claim was invented. Where a source row had no value for a field, the field is
absent here too.

| corpus | count |
|---|---|
| rows read in | **303** (295 from the six declared sweeps + 8 from `jobs/coverage-repair/` — see §9) |
| duplicates merged | **17** *(was 19 before the UCONS3 rank-216 re-split — see ERRATA B)* |
| rows out (one per opening) | **286** *(was 284; 278 from the six declared sweeps + 8 coverage-repair — see ERRATA B)* |
| — `apply_now` | 10 |
| — `apply_later` | 62 |
| — `watch` | 117 |
| — `exclude` | 95 |
| cap-exempt US (open) | **105** |
| no-PhD required (all rows / open role rows) | 26 / **13** |
| individual funding an individual may apply for | **13** (8 of them from JOB4, matching its FINDINGS) |
| deadlines with an explicit year inside 60 days | **3** |

---

## 1. Top 10 to act on

Ranked by **your stated route priority** (cap-exempt H-1B ≈ O-1A → Scandinavian/European → India →
cap-subject fallback), then by the blockers, then by the recording unit's subject-matter fit. Prestige
was not a ranking input.

| # | Action | Organisation · role | Route | Why it ranks | Single next action |
|---|---|---|---|---|---|
| 1 | `apply_now` | **METR** · Member of Technical Staff, **Embedded Assessments**<br>`https://jobs.lever.co/metr/69792e29-e72c-44a2-8305-82cb40ab17c5` | cap_exempt_us | Cap-exempt 501(c)(3) research nonprofit; **no doctorate required** (posting states no degree requirement); fit 5/5 — empirical LLM capability assessment is the closest paid analogue of your agent-harness evaluation work. Salary is on the posting: **$402K–$687K**, on-site Berkeley. | Apply on Lever now — it is **rolling** (the posting itself warns responses may be slow, so no deadline to wait for). On-site Berkeley. |
| 2 | `apply_now` | **METR** · Member of Technical Staff, **Evaluation Execution**<br>`https://jobs.lever.co/metr/93baec4d-1e47-40f7-9990-6d7fef12da00` | cap_exempt_us | Same employer, same basis; **no doctorate required**; runs and improves frontier-model evaluation pipelines *on agent scaffolds* — the literal job description of your work. **$328K–$578K**. | Apply on Lever now — **rolling**. Berkeley on-site. |
| 3 | `apply_now` | **CZ Biohub (Chan Zuckerberg Initiative)** · Staff Research Scientist, **AI Safety** — Redwood City<br>`https://job-boards.greenhouse.io/biohub/jobs/7997533` | cap_exempt_us | Cap-exempt 501(c)(3) nonprofit research org; fit 5/5; AI-safety staff role whose posting covers **agentic systems, eval frameworks and RL post-training**. Doctorate not stated as required. | Apply on Greenhouse. **Hybrid Redwood City — you need a Bay Area presence.** |
| 4 | `apply_now` | **CZ Biohub** · Staff Research Scientist, **AI Safety** — New York<br>`https://job-boards.greenhouse.io/biohub/jobs/8127000` | cap_exempt_us | Identical role, second location — a genuinely separate opening (different URL), not a duplicate. The CZ Biohub posting states **relocation support**. | Apply on Greenhouse. **Hybrid New York — you need an NYC presence.** |
| 5 | `apply_now` | **Apollo Research** · Research Scientist/Engineer **(Evaluations)**<br>`https://jobs.lever.co/apolloresearch/4a65c6e1-785a-4f88-8998-a97574afb7ee` | cap_exempt_us | Nonprofit AI-safety research org (recorded by two sweeps as cap-exempt-likely); fit 5/5 — Inspect-based evaluation pipelines for frontier models. Doctorate not stated as required. **Caveat: the cap-exempt basis was *not* verified on the page** — verify before any petition. | Apply on Lever, then ask the recruiter to confirm the sponsoring entity is the nonprofit. **London & San Francisco — pick one and be there.** |
| 6 | `watch` | **NREL → National Laboratory of the Rockies (NLR)** · Graduate **Intern** — LLM Reliability and Uncertainty for AI Science Assistants<br>`https://nrel.wd5.myworkdayjobs.com/job/Golden-CO/Graduate-Intern---LLM-Reliability-and-Uncertainty-for-AI-Science-Assistants_R14416` | cap_exempt_us | Cap-exempt FFRDC (nonprofit/DOE operator), fit 5/5, subject matter is exactly agent-harness evaluation. **But it is an intern lane**: intern/graduate lanes normally require current enrolment, and continuing student status is your binding constraint. | **Do not spend time now.** Ask NLR whether the intern lane is open to a non-enrolled applicant; otherwise watch for a matching *staff* NLR opening. |
| 7 | `apply_later` | **CMU Software Engineering Institute** (FFRDC) · Senior ML Research Scientist — **Frontier Lab**<br>`https://cmu.wd115.myworkdayjobs.com/SEI/job/Pittsburgh-PA/Senior-Machine-Learning-Research-Scientist---Frontier-Lab_2024076-1` | cap_exempt_us | Cap-exempt FFRDC (university affiliate + nonprofit, DoD-sponsored), fit 5/5, frontier-AI research lab. **Decision-changing gate: the posting was not fetched, and SEI DoD-FFRDC roles commonly require US citizenship.** | **Verify citizenship eligibility before applying** — email the SEI recruiter one question: *"does this role require US citizenship?"* |
| 8 | `apply_later` | **CMU SEI** · Senior ML Research Scientist — **Secure AI Lab (SAIL)**<br>`https://cmu.wd115.myworkdayjobs.com/SEI/job/Pittsburgh-PA/Senior-Machine-Learning-Research-Scientist---SAIL_2024055-1` | cap_exempt_us | As above. | As above — same citizenship check. |
| 9 | `apply_later` | **CMU SEI** · **Senior AI Red Team Engineer**<br>`https://cmu.wd115.myworkdayjobs.com/SEI/job/Pittsburgh-PA/Senior-AI-Red-Team-Engineer_2025001-1` | cap_exempt_us | Red-teaming/evaluating LLM systems is the closest industry analogue to harness evaluation. | As above — same citizenship check. |
| 10 | `apply_later` | **CMU SEI** · **AI Red Team Engineer**<br>`https://cmu.wd115.myworkdayjobs.com/SEI/job/Pittsburgh-PA/AI-Red-Team-Engineer_2025000-1` | cap_exempt_us | As rank 9, one level below Senior — the more likely entry point if the Senior band is out of reach. | As above — same citizenship check. |

**Ranks 11–15** (all `apply_now` unless noted): Apollo Research *Science of Scheming*
([`…/271eb45a`](https://jobs.lever.co/apolloresearch/271eb45a-3aa9-42bb-8686-9cd1fc5e377e)) and *Research
Scientist (Control)* ([`…/24d016aa`](https://jobs.lever.co/apolloresearch/24d016aa-5a19-4976-8936-af2fbf748000));
then AI2 *Predoctoral Young Investigator, Open Ecosystem*
([`…/8054878`](https://job-boards.greenhouse.io/thealleninstitute/jobs/8054878)), *Senior Software Engineer,
Agent Frameworks* ([`…/7872683`](https://job-boards.greenhouse.io/thealleninstitute/jobs/7872683)) and *Senior
Research Scientist, Open Ecosystem* ([`…/8159367`](https://job-boards.greenhouse.io/thealleninstitute/jobs/8159367)).

> **The honest caveat on ranks 5, 11–15:** they are cap-exempt *on the strength of the employer's own
> description of itself*, which the sweep could **not** verify against a registration record. The rows carry
> the blocker `cap_exempt_basis_unverified`. Ranks 1–4 (METR, CZ Biohub) are the ones whose cap-exempt basis
> the corpus records as stated on the page.

---

## 2. The cap-exempt subset — the visa-critical list

**105 open openings** sit at a cap-exempt US employer (168 rows in the corpus across all statuses). This is
the list that does not depend on the H-1B lottery and does not depend on your school. Employers represented,
with the basis the source sweep recorded:

| Employer family | Recorded cap-exempt basis |
|---|---|
| **METR** | 501(c)(3) nonprofit research org (stated) |
| **CZ Biohub (CZI)** | 501(c)(3) nonprofit research org / Chan Zuckerberg network |
| **Arc Institute, Redwood Research, Santa Fe Institute, CAIS, MLCommons** | nonprofit research org — stated or strongly implied on the org's own page |
| **AI2 (Allen Institute for AI)** | 501(c)(3) nonprofit research org *(basis not verified on page)* |
| **FAR.AI, MIRI, Apollo Research, Palisade, LAION, Renaissance Philanthropy, Schmidt Sciences, Astera, Longview, Cooperative AI Foundation** | publicly nonprofit; **basis not verified on page → verify before petition** |
| **National labs / FFRDCs** — ORNL, LLNL, JPL (Caltech/NASA), NREL→NLR, CMU SEI, RAND, MITRE, Fermilab | governmental research org / FFRDC operated by a university or nonprofit (8 CFR 214.2(h)(8)(iii)(F)) |
| **NIST / CAISSI (US AISI successor)** | governmental research org — *all six CAISSI teams state "not hiring at this time"* |

**Do not read "cap-exempt" as "work-authorised."** Cap-exempt status removes the lottery, not the
citizenship gate. The national-lab share of this subset is heavily gated — see §6.

---

## 3. The no-PhD subset — where the posting says a doctorate is not required

26 rows in the corpus record no doctorate requirement; **13 are open role rows**. The distinction between
*stated* and *absent* is deliberate and is carried in the JSONL as `no_phd_kind`.

### Stated in the posting (`no_phd_kind:"explicit"`)

| Organisation · role | The posting's own words (verbatim, as quoted by the sweeping unit) | Route |
|---|---|---|
| **Simula Research Laboratory / SimulaMet** · Research Engineer — AI Safety (revision and red teaming, 2-yr) | *"Mastergrad i informatikk, maskinlæring … eller tilsvarende erfaring. **Doktorgrad er velkommen, men ikke et krav.**"* — "A master's degree in informatics, machine learning … or equivalent experience. A doctorate is welcome, but is not a requirement." | `eu_researcher_permit` |
| **SINTEF Digital** · Analytics and AI — Junior Researcher (**MSc** lane) and Researcher (PhD lane) | The advert states an **MSc lane** (Junior Researcher) alongside the PhD lane (Researcher). Recording unit's own note: *"Advert states MSc applies for junior-research-scientist lane; agentic AI + industrial ML; deadline 04/11/2026."* Verbatim requirement line: *"MSc (junior research scientist) OR PhD (research scientist) in CS/stats/optimisation etc."* | `eu_researcher_permit` |
| **TNO** · Research Software Engineer Geoscience, Utrecht (#1430) | *"**An MSc or PhD** in Earth Sciences…"* — MSc sufficient; posted degree level "Master". | `eu_researcher_permit` |
| **METR** · MTS Embedded Assessments, MTS Evaluation Execution, MTS Offensive Security Research, Platform Engineer Application Security, General Expression of Interest | Recorded PhD/affiliation requirement for these rows is literally **`no`** ("no degree requirement stated"). | `cap_exempt_us` |
| **Redwood Research** · Member of Technical Staff | Recorded PhD/affiliation requirement **`no`** (not stated). Pay band is on the page: **$350,000–$850,000/yr**. | `cap_exempt_us` |
| **Foresight RFP, EA Funds/LTFF, Emergent Ventures, MATS, Algoverse, Constellation ×2, Foresight Fellowship, NumFOCUS** | Recorded PhD/affiliation requirement **`no`** — see §5. | `o1_suitable` (funding) |

### Requirement absent from the posting (`no_phd_kind:"absent"` — weaker evidence, stated as such)

| Organisation · role | Basis |
|---|---|
| **KTH Royal Institute of Technology** · Research Engineer in Robotics, Perception and Learning | *"No doctoral-degree requirement anywhere in the ad (sibling KTH ads do state PhD explicitly; this one does not)."* Recorded as `phd_required: not_mentioned` — **absence of a requirement, not a statement that one is waived.** KTH's two Postdoc ads in the same sweep *do* say PhD. |

**Student-gated lanes inside this subset** (flag `student_status_likely`, action `watch` — unusable while you
cannot obtain student status): **TNO** *Internship — Cross-lingual transfer for Dutch LLM pretraining*;
**TNO** *Internship — Data-driven corpus mixtures*; **NREL→NLR** *Graduate Intern — LLM Reliability*;
**IndiaAI Fellowships** (open to UG/PG/PhD students).

---

## 4. Time-boxed items — soonest first

Deadlines as recorded. Everything below was read off the named page by the sweeping unit on 2026-10-15;
nothing was extrapolated from a search snippet.

| Deadline | Organisation · item | Route | Notes / eligibility | Source of the date |
|---|---|---|---|---|
| **2026-10-31 23:59 PDT** | **Foresight Institute** · AI for Science & Safety Grants RFP (CISAI) | `o1_suitable` (grant) | **Individuals**, teams and organisations may apply; no PhD or affiliation mentioned; **work product must be open-sourced** — the only item in the whole corpus whose stated terms match an AGPL-3.0 codebase. **$30,000–$100,000** typical. | `deadline` field, `evals-safety-foundations/JOBS.jsonl` |
| **2026-11-04** | **SINTEF Digital** · Analytics and AI — Junior Researcher (MSc) | `eu_researcher_permit` | The MSc lane; agentic AI + industrial ML. SINTEF also flags possible **Security Act clearance**, which can disadvantage non-EU candidates. | `scandinavia-europe/FINDINGS.md` §1 |
| **2026-11-08** | **University of Copenhagen / Novo Nordisk Foundation Center for Protein Design** · Computational and Data Staff Scientist | `eu_researcher_permit` | **PhD-gated**: *"A PhD in bioinformatics, data science or a related domain"* is essential. Listed for completeness — the deadline is real, the degree gate is the blocker. | `scandinavia-europe/FINDINGS.md` |
| **2026-12-31 17:00** | **ANRF (India)** · **Ramanujan Fellowship** | `india` | Individual applies with a host institution in India; Indian/Indian-origin scientists abroad, aged <40; PhD / MTech / MD + track record. **Rs 1,35,000/month incl. HRA + Rs 7 lakh/yr research grant + Rs 60,000/yr overhead, 5 years.** Results twice a year. | `deadline` field, `india-ai/JOBS.jsonl` |
| *Oct 17 cycle — year not stated on the page* | **NumFOCUS** · Small Development Grants | `o1_suitable` (grant) | **Institutions only — "individuals may NOT apply directly"**; route is to become a fiscally sponsored project first. Do not plan around this date. | `deadline` field |
| *"November 1 cohort" — year not stated on the page* | **Algoverse AI Research** · AI Safety Fellowship | `o1_suitable` (fellowship) | Open to university students **and industry professionals** worldwide; at least undergraduate-level education. 60 seats/cohort. | `deadline` field |

**Already closed, recorded so they are not re-chased:** UK AISI *Challenge Fund* (up to £200,000/project),
*Alignment Project* (up to £1,000,000/project) and *Systemic AI Safety Grants* — all "Applications are now
closed" on aisi.gov.uk/grants, and all institution-gated anyway.

---

## 5. The individual-funding track

**13 corpus rows** are grants/fellowships an individual can apply for (of **32** funding rows total — was 30 before the UCONS3 re-split; see ERRATA B). **8 of the
13 come from JOB4** and match its FINDINGS Shortlist B rows 1–8 exactly. The **individual-vs-institution
distinction is the decisive column** — most of the money in this corpus cannot be applied for by a person.

### You apply as an individual (no affiliation, no PhD stated)

| Org · programme | Amount (as stated) | Deadline | Eligibility / terms |
|---|---|---|---|
| **Foresight Institute** — AI for Science & Safety Grants RFP (CISAI) | $30,000–$100,000 typical | **2026-10-31 23:59 PDT** | "We accept applications from **individuals**, teams, and organizations"; no PhD/affiliation mentioned; **open-source mandate** |
| **EA Funds / Long-Term Future Fund** (LTFF) | varies per fund (not stated) | rolling | "EA Funds can make grants to **individuals** … **We accept applications from any country**" |
| **Emergent Ventures** (Mercatus) | per proposal (not stated) | rolling | "Applicants must be **at least 13 years old**" — nothing else. **AI-written applications rejected on sight** (AI ok for proofreading only) |
| **MATS Residency** — Winter & Summer 2027 cohorts open | **$1,250/week stipend + housing (Berkeley/London) + visa support + up to $25,000 relocation** | cohorts open; exact date not stated | "researchers of **varying backgrounds** … if you are unsure whether you fit, we would rather you apply"; no PhD requirement stated. ***The only item here that explicitly mentions visa support.*** |
| **Algoverse AI Research** — AI Safety Fellowship | stipend not stated; 60 seats/cohort | "Early deadline for the **November 1** cohort" (year not stated) | "open to **university students and industry professionals worldwide**"; prior research experience ideal, not required |
| **Constellation** — Astra Fellowship | funding + ops support (amount not stated) | not stated | "**Prior AI safety experience is not required**" |
| **Constellation** — Generator Residency | "**fully-funded**, three-month residency" | not extracted | generalists "pitch, build, and ship projects" for the AI-safety ecosystem |
| **Foresight Institute** — Foresight Fellowship, 2028 cohort | year-long; amount not stated | "Apply for the 2028 cohort" live | early-career scientists/engineers/innovators; apply or nomination; no PhD mentioned |

### You apply as an individual, but the money is gated by institution or degree

| Org · programme | Amount | Gate |
|---|---|---|
| **ANRF Ramanujan Fellowship** (India) | Rs 1,35,000/mo + Rs 7 lakh/yr + overhead, 5 yrs | Individual applies **with a host institution in India**; Indian/Indian-origin, <40; PhD/MTech/MD preferred. Deadline 2026-12-31 17:00 |
| **ANRF PM Early Career Research Grant** (India) | up to **Rs 60 lakh / 3 years** | Individual (age ≤42, relaxations); PhD not mentioned; **call-based, no date stated** |
| **ANRF TARE** (India) | Rs 60,000/yr fellowship + Rs 5 lakh/yr grant to host | Researcher **with own salary**, applies with parent + host institutions; call-based |
| **IndiaAI Fellowships** (MeitY) | not stated in the govt release | **Students (UG/PG/PhD)** — student-gated, so unusable under your binding constraint |
| **ANRF N-PDF / IISc Postdoctoral Fellowship / Google India Post-Doctoral Researcher** | Rs 80,000/mo (Rs 50,000 until degree awarded) / not stated / not stated | **PhD required** |
| **NumFOCUS Small Development Grants** | amount not stated | **"individuals may NOT apply directly"** — only fiscally sponsored or affiliated projects; route = sponsor your project first |
| **UK AISI Challenge Fund / Alignment Project** | up to £200,000 / up to £1,000,000 per project | **Closed**, and eligibility is "researchers based at eligible UK and international academic institutions and non-profit organisations" |

**Verified *not* open to individuals** (recorded on official pages, so not shortlisted anywhere above):
ANRF **J.C. Bose** (nominations only by Heads of Institutions — Rs 25 lakh/annum observed), ANRF **PAIR**
(only a Hub institution may submit), ANRF **PM Professorship** (superannuated faculty only).

**Watchlist — fetched, but no fundable open cycle verifiable from static content:** Schmidt Sciences
("do not accept unsolicited proposals"), AI2050, Manifund (JS-rendered rounds), Coefficient Giving GCR
opportunities directory (JS-filtered grant cards).

---

## 6. Excluded, and why

**95 rows are `exclude`.** A row is excluded only on a *recorded, decision-changing* fact — never on
judgement about the role's quality.

| Reason (blocker) | Rows | What it means |
|---|---|---|
| `source_unreachable` | 58 | The sweep could not fetch the page. **Status is preserved as `unreachable`; it never becomes `open` here.** Many of the 58 are whole-organisation coverage rows (LBNL, PNNL, SLAC, BNL, Sandia, LANL, INL, Battelle, Aerospace, AFRL, IARPA, ARL, NSF, DARPA, NOAA, USGS, USAJOBS itself) — they are gaps, not jobs. |
| `no_live_posting` (`status:"none_found"`) | 15 | The org was reached and no live relevant posting was found. |
| `no_relevant_role` | 14 | Reached, live listings, nothing matching the subject matter. |
| `clearance` | 7 | The posting requires a security clearance (JPL TS/SCI variants). |
| `posting_closed` | 1 | Explicitly closed on the page. |
| `citizenship_required` | 1 | LLNL *Senior Cyber AI Engineer* — *"REQUIRES DOE Q-level clearance -> U.S. citizenship required (decision-changing)"*, quoted from the posting itself. |

**Not excluded but gated — these stay in the list with the gate visible:** `citizenship_unverified` on the
9 CMU SEI rows (`apply_later`), `ndaa_3112_country_bar` on 2 LLNL postdocs (NDAA-2025 §3112 bars PRC/Russia/
Iran/DPRK citizens on assignments >179 days — only relevant if that is your nationality, which this unit does
not determine), and `phd_required` on 17 rows (`watch`, not `exclude`, because several sit at cap-exempt
employers that may open a non-doctoral lane).

### The two integrity catches, preserved

1. **Wadhwani AI's LLM-scientist posting was corrected to `none_found`.** The careers index listed ML
   Scientist (LLM), Associate ML Scientist, ML Intern and an Impact Analytics Fellow; **all three ATS postings
   tested returned "no longer available"** on 2026-10-15. The rows are in the corpus with
   `status:"none_found"` and `source_unreachable`/`no_live_posting` blockers — **the posting was not claimed
   to exist, and its URL still points at the ATS that refused it.**
2. **An Anthropic listing found only via an aggregator was not recorded.** *"Staff Engineer – Agent Runtime &
   Productivity"* was seen on jobleads.com but **is not on Anthropic's live Greenhouse board**. It is absent
   from the corpus. Verified: **0 rows** in `MASTER_SHORTLIST.jsonl` match that title, and **all 4** Anthropic
   rows that are present come from `job-boards.greenhouse.io/anthropic/…` — the live board. The same rule
   excluded Trase Systems (aggregator-only) and a Glean "Agents Runtime" title that the official board
   carries under a different name.

Both catches are *evidence the corpus was screened*, not omissions.

---

## 7. Coverage honesty — this corpus is not exhaustive

- **58 of 286 rows carry `status:"unreachable"`** (was 284 before the UCONS3 re-split; see ERRATA B) (64 raw across the six units; six collapsed into other
  coverage rows by de-duplication). Add 15 `none_found` + 14 `no_relevant_roles`, and **87 rows are not live
  openings at all** — they are the record of a failed or empty fetch, kept deliberately.
- The figure of **~103 unreachable URLs** quoted in this unit's brief counts *individual failed URL attempts*
  across all six FINDINGS tables, including paths that were retried and then resolved (e.g. intelligence.org
  403→200, mlcommons.org 403→200, alignmentresearch.org apex 000→200). It is a larger number than 58 because
  it counts attempts, not rows. **Both numbers are true; they measure different things.**
- **JOB7b, the coverage-repair unit, failed twice and delivered nothing.** That is the card's statement and it
  is what the handoff record shows — *but the disk contradicts it.* See §9.
- Whole-horizon gaps the sweeps themselves name: **all USAJOBS-only agencies produced zero openings** (NIST
  vacancies, NIH/CIT/NLM, NSF, NOAA, USGS, ARL, AFRL civilian, DOE Office of Science) because USAJOBS is a
  JS-only shell; **RISE (SE) and Tartu (EE) are WAF/403-blocked** from the network used; MITRE, PNNL, LBNL,
  SLAC, BNL, Riverside, SRI, Lincoln Lab, DTU, Aalto, INRIA, ETH and DFKI render listings only client-side.
- **Nothing here was searched for by this unit.** If an org is missing, it is missing because a sweep failed
  or never tried it — not because it has no openings.

---

## 8. How to read the JSONL

Every source field is preserved verbatim. Added fields:

| field | meaning |
|---|---|
| `source_unit` / `source_units` | which sweep(s) produced the row; `"a+b"` means the row was built by merging rows that a and b both recorded |
| `dedupe_key` | `org \| normalised-role \| normalised-URL`, lowercased, percent-decoded, query-stripped, `www.`-stripped |
| `rank` | 1 = act first. Sort order: eligibility bucket → route class (cap_exempt_us, o1_suitable, eu_researcher_permit, india, cap_subject_fallback) → `phd_required` last → subject-matter fit → soft caveats → deadline → source richness |
| `rank_reason` | the actual basis for this row's rank, incl. every blocker and any merge |
| `route_class` | `cap_exempt_us` \| `o1_suitable` \| `eu_researcher_permit` \| `india` \| `cap_subject_fallback`. **`eu_researcher_permit` covers UK roles too** (reached via UK Skilled Worker / Global Talent, not an EU Blue Card) — the enum has no separate UK value. **Funding rows** are classed `o1_suitable` because they have no employer, so no H-1B route is needed and the award itself is O-1A evidence. |
| `blockers` | `citizenship_required`, `clearance`, `citizenship_unverified`, `phd_required`, `phd_preferred`, `student_status_likely`, `cap_exempt_basis_unverified`, `ndaa_3112_country_bar`, `source_unreachable`, `no_live_posting`, `posting_closed`, `no_relevant_role` |
| `action` | `apply_now` (top-ranked, no person-level gate) \| `apply_later` (actable, but verify a caveat or lower rank) \| `watch` (doctorate required, student lane, or fit ≤2) \| `exclude` (recorded dead end) |
| `no_phd`, `no_phd_kind`, `no_phd_basis` | `kind` is `explicit` (the posting says so) or `absent` (no requirement appears anywhere); `basis` quotes the posting or names the FINDINGS table |
| `merge_note` | present only on merged rows; names the units and the fields unioned from the losing row |

**A row's `status` is never rewritten.** An `unreachable` row stays `unreachable` and its `action` is
`exclude`.

### De-duplication — what was merged, and what deliberately was not

**17 duplicates merged** across 303 rows → 286 (was 19 → 284; the rank-216 mis-merge was undone by the UCONS3 re-split, restoring 2 rows — see ERRATA B). Key: organisation + normalised role title + normalised URL.

| Collision rule | Merged |
|---|---|
| exact `org+title+URL` | 12 |
| same `org+URL`, one title annotates the other (Redwood Research *MTS* vs *MTS (AI control research)*; Coefficient Giving *Expression of Interest* recorded twice under two org spellings) | 2 |
| same `org+URL`, both non-open coverage records (CAISSI, MITRE, EleutherAI and one more — same gap recorded by two units) | 4 |
| same `org+URL`, same leading title words + same `entry_type` | 1 |

> **UCONS3 correction (2026-10-15).** The rule counts above are UCONS2's as-written and no longer describe the
> data. Erratum 3 already measured them as **7/2/8/2 = 19**; after the rank-216 re-split (§ ERRATA A) the
> mis-merge category drops to 0 and the operative composition is **7/2/8/0 = 17**. See ERRATA B.

The 12 exact merges include the collisions the brief predicted: **METR and Apollo roles that appear in both
JOB1 and JOB6/JOB4** (METR Evaluation Execution, METR Embedded Assessments and METR Offensive Security each
appear in 2–3 sweeps; Apollo Evaluations in 2), **plus 5 rows the us-national-labs sweep duplicated against
itself** (ANL, INL, NREL, Aerospace, Battelle coverage gaps). Where rows collided the **richer** row won
(more populated fields, then more characters) and **missing fields were unioned in from the losing row** —
which is why a merged METR row carries both the nonprofit sweep's `cap_exempt_basis` and the evals sweep's
`phd_or_affiliation_required`. Both units are recorded in `source_units`.

**Deliberately NOT merged** — different openings that share one posting URL, proving the merge rule did not
over-reach: **5 distinct ANRF schemes** (Ramanujan, N-PDF, J.C. Bose, TARE) share
`anrf.gov.in/page/english/awards_fellowship`; **3 distinct UK AISI grant programmes** share
`aisi.gov.uk/grants`; **2 Microsoft Research hub records** share the MSR careers URL; **3 TNO roles** share
the TNO vacancy path. CZ Biohub's two *Staff Research Scientist, AI Safety* rows are **New York and Redwood
City — two locations, two URLs, two openings**, and were kept apart.

> **UCONS3 correction (2026-10-15) — the AISI clause above was false when written.** *"3 distinct UK AISI grant
> programmes share `aisi.gov.uk/grants`"* was **not** true of the JSONL at the time: all three had been
> collapsed into the single rank-216 row. They are genuinely distinct programmes
> (`evals-safety-foundations/JOBS.jsonl` [22],[23],[24]) and are now restored as three rows at ranks **216**,
> **216.1** and **216.2** — see ERRATA A. The rest of the sentence (ANRF 6 rows on two URLs, 2 MSR hub records,
> 3 TNO roles) is unaffected: those genuinely were kept apart. The claim was right about the *rule's intent* and
> wrong about the *merge's outcome*; the outcome is now corrected rather than the claim quietly deleted.

---

## 9. ⚠️ One thing you must know before trusting the counts

This unit's brief states: *"JOB7b (the coverage-repair unit) failed twice and delivered nothing."*

**The handoff record agrees — there is no `JOB7b` handoff on disk. But the disk does not agree.** At
`jobs/coverage-repair/JOBS.jsonl` there is a **valid 8-row file written 2026-10-15 14:59**, with raw fetch
artifacts under `jobs/coverage-repair/tmp/` timestamped 14:53–14:58. Seven rows are **open NREL → National
Laboratory of the Rockies openings harvested through the correct Workday slug (`nrel.wd5`)**, which the
us-national-labs sweep had recorded as unreachable (`nrel.wd1` returned 406/422) — i.e. a coverage gap
actually repaired; the eighth row is an honest `unreachable` record for INL ("enumeration not completed").

I could not resolve the disagreement from inside this unit, so I did the honest thing on both sides: **the
rows are included**, tagged `source_unit:"coverage-repair"`, and **the count is reported both ways** — **286**
total (was 284), of which **278 come from the six declared sweeps** (was 276) — see ERRATA B. Nothing about them is presented as coming from a
unit that reported success, because none did.

Practical effect: **rank 6 of the Top 10 is one of these undeclared rows**, and 6 more NREL openings sit
between ranks 20 and 30. If you decide this file should not influence the ranking, filter
`source_units != ["coverage-repair"]` and the list re-orders correctly — the `rank` values were computed with
them included, so a filtered view keeps the relative order. **(After the UCONS3 re-split this filter yields
278 rows; the 8 coverage-repair rows and every pre-existing rank are unchanged — see ERRATA B.)**

---

## 10. What would change this list

1. **Proof of cap-exempt registration for APOLLO, FAR.AI, AI2, MIRI, MLCommons** — 5 of the top 15 carry
   `cap_exempt_basis_unverified`. If any turns out cap-subject, its whole family drops below the European
   no-PhD roles.
2. **The CMU SEI citizenship answer** — one email unblocks or eliminates ranks 7–10.
3. **Whether the NLR intern lane is open to a non-enrolled applicant** — decides rank 6, and whether a
   *staff* NLR opening is the thing to wait for.
4. **Your nationality** — it decides the two `ndaa_3112_country_bar` rows, the ANRF Ramanujan and IndiaAI
   eligibility lines, and whether the India tier is real for you at all. This unit deliberately did not
   determine it.
5. **A re-verification of the 58 `unreachable` rows from a network that is not WAF-blocked** — that is the
   JOB7b job, and it is still owed.
