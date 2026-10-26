# O-1A Evidence Assessment — on the corrected disclosure facts

**Unit:** UO1C · **Date:** 2026-10-15 · **Status:** complete
**Purpose (one):** an updated, honest **evidence assessment** for an O-1A petition on the corrected
facts — (a) **13 of 13 kernel mechanisms are already public** (MIT) in
`github.com/Aswin-Ram-K/publish-present-compete`; (b) the **umbrella paper is withdrawn**, posture is
*publish the design, keep the implementation*.

**No web tool was used by this unit.** Every quote below was lifted from a file on disk and is
labelled with its provenance. "second-hand (via UCODE1)" means the text was fetched by unit UCODE1
on 2026-10-15 and preserved verbatim on disk; this unit did not fetch it.

**Correction to the unit card (recorded, not silently worked around).** The card states the
criterion-5 quotes live in `strategy/TRADE_SECRET_AUDIT.md` §4. They do **not** — §4 of that file is
*"Per-mechanism triage"* (§4.1–§4.3, trade-secret mechanism triage), and a grep of the whole file
for `major significance`, `criterion 5`, `commercial` returns no USCIS criterion text. The quotes
**are** on disk, at `strategy/CODE_LICENSING_STRATEGY.md:379–393` (fetched by **UCODE1**, 2026-10-15)
and corroborated verbatim at `strategy/VERIFICATION_REPORT_2.md:16` (fetched by **UVER2**, same URL,
same day). Those are the sources used below. Nothing was reconstructed from memory.

---

## 1. What changed, and what it invalidates

Two verified findings invert the factual base the O-1 analysis in `strategy/VISA_US_ROUTES.md` was
written against.

**Finding 1 — the design is public, and the mechanisms are already released.**
`strategy/DISCLOSURE_INVENTORY.md:15` settles the count: *"UDISC1 reported 9 of 13 disclosed … so the
count is **13 of 13**"*. `:29–38` records ten public artefacts in
`github.com/Aswin-Ram-K/publish-present-compete`, each under **MIT** with *"commercial reuse
**granted**"*, including `findings/PAPER-DERIVATION.md` — **46,636 B, byte-identical to the corpus's
withheld `docs/research/PAPER_DERIVATION.md`** (sha256
`d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802` per the card and the inventory).
The disclosure is therefore not partial: **every kernel mechanism is already in the public record.**

**Finding 2 — the implementation is still private, and that is now verified rather than inferred.**
`strategy/DISCLOSURE_INVENTORY.md:17`: *"the author had already force-rewritten the repository so
that **no reachable commit contains the source**"*; `consonance/src/journal.ts` and `src/journal.ts`
both **HTTP 404 at every historical ref tested**. The inventory also records the countervailing fact
at `:19`: between **2026-10-09 04:11** and **2026-10-10 07:51** the implementation *was* public under
**AGPL-3.0** (*"528 commits, 441 files, 16,704 LOC in `src/`"*), and *"A one-day public window that is
retrospectively erased is not the same thing as never published"*.

**Finding 3 — the umbrella paper is withdrawn**, so the posture is *publish the design, keep the
implementation*, and the authorship exhibit the O-1 plan leaned on is gone.

### Superseded statements in `strategy/VISA_US_ROUTES.md`

| # | Location | Statement as written | Why it no longer holds |
|---|---|---|---|
| S1 | `:265–267` (§3.3) | *"for an independent researcher with a **publication and citation record** but no PhD …"* | The premise is false on the corrected facts: **zero arXiv, zero DOI, zero peer-reviewed, zero citations** (§3.4 below). The comparison is being run for a researcher *without* the record it assumes. |
| S2 | `:604` (§7) | Assemble the *"**Publication record** — the working paper and the ~39 research records, with venues, dates, and identifiers"* | The working (umbrella) paper is **withdrawn**, and the ~39 records are internal: no venue, no identifier. The row cannot be assembled as written. |
| S3 | `:605` (§7) | Assemble *"**Independent citation counts** … snapshotted with the retrieval date"* | No citable published work exists, so no citation count exists. An unfillable row is a promise the petition cannot keep. |
| S4 | `:357–361` (§4) | *"That 'contributions to repositories of software' example is **directly on point for an open-source agent-runtime project**"* | **Half survives, half inverts.** The criterion text is still on point, and a public repo now *exists* — which is better than the private posture this passage assumed. But the passage was written for a project whose mechanisms were unpublished; 13/13 are now public, and the passage nowhere says so. |
| S5 | `:609` (§7) | Assemble *"**Open-source impact** — download/usage/adoption figures, dependent packages, downstream citations, third-party integrations, and **written statements from independent adopters**"* | Still the right target, but the corrected record contains **only a public repo and a licence** — no adopters, no usage figures, no downstream packages, no statements. The row is aspirational, not evidential. |
| S6 | implicit posture (references in `TRADE_SECRET_AUDIT.md` §3, *"The consequence of withholding the blanket paper (O-1)…"*) | The O-1 plan treated the withheld umbrella paper as a forthcoming authorship exhibit | The paper is **withdrawn**, not merely withheld: the cost TSA §3 priced as *conditional* has been **paid**. |

**Not superseded — still good law from `VISA_US_ROUTES.md`:** the eight criteria (`:215–241`), the
no-degree-requirement reading (`:251–256`), the agent-as-petitioner rule and the self-petition bar
(`:287`, quoted from 2 USCIS-PM M.3(A)), the advisory-opinion requirement (`:298–304`), and the
corrected criterion-5 attribution to **2 USCIS-PM M.4** rather than 6 USCIS-PM F.2 (`:348`). None of
those turned on the privacy of the work.

---

## 2. The criterion text being argued against

All three quotes below are **second-hand (via UCODE1/UVER2)** — fetched from
`https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4` on **2026-10-15** by UCODE1 and
preserved at `strategy/CODE_LICENSING_STRATEGY.md:382–393`, corroborated at
`strategy/VERIFICATION_REPORT_2.md:16`. This unit did not fetch them.

**Criterion 5, the criterion itself** (`CODE_LICENSING_STRATEGY.md:382–383`):

> "**Criterion 5:** Evidence of the beneficiary's original scientific, scholarly, or business-related
> contributions of major significance in the field."

**The software bullet — the single most useful sentence for this profile**
(`CODE_LICENSING_STRATEGY.md:387–388`):

> "**Contributions to repositories of software, data, designs, protocols, or other technical resources
> with evidence of significant scientific, scholarly, or business-related impact in the field**;"

**The commercial-use bullet, immediately adjacent in the same list**
(`CODE_LICENSING_STRATEGY.md:392–393`):

> "**Evidence of commercial use of the beneficiary's work**, such as commercialization of a research
> innovation;"

**The totality bar** (`CODE_LICENSING_STRATEGY.md:395–396`): the beneficiary must be *"one of the small
percentage who have arisen to the very top of his or her field."*

**Criterion 6 — where the no-citation rule was found.** The card asked for the statement that a
petitioner *"need not provide evidence that the beneficiary's published work has been cited"*, "in
`strategy/VISA_US_ROUTES.md` or a `VERIFICATION_REPORT`". **It is not in either.** It is on disk at
**`orchestration/units/ULIC.md:63`**, quoted verbatim from the same 2026-10-15 fetch of
`volume-2-part-m-chapter-4`:

> *"A petitioner need not provide evidence that the beneficiary's published work has been cited."*

(The same fetch is recorded in `orchestration/handoffs/ULIC.json`, which attributes it to criterion 6.)

---

## 3. Asset-by-asset assessment

Weight is stated as **what a USCIS officer could verify from documents**, not what is true of the work.

### 3.1 The public design repo — `github.com/Aswin-Ram-K/publish-present-compete`

- **What it evidences:** a dated, public, citable body of original work: `WHITEPAPER.md`
  (self-dated *October 2026*), `findings/PAPER-DERIVATION.md` (46,636 B, byte-identical to the
  corpus paper), `decisions/DECISION_LOG.md` (**99 decisions**, each with rejected alternatives),
  `experiments/` (15 pre-registrations + results), 15 `findings/` files — all **MIT**, *"public ≤
  2026-10-10"* (`DISCLOSURE_INVENTORY.md:29–38`). It reaches criterion 5's *"contributions to
  repositories … of designs, protocols, or other technical resources"* **literally**.
- **Current weight:** **low-to-moderate, and evidentially thin.** It proves *authorship and
  originality*; it does not prove *major significance*. Three specific defects: (i) **GitHub is not
  peer-reviewed** and confers no editorial filter an officer can point to; (ii) **no DOI**, so there
  is no persistent identifier, no version of record, and no third-party archive; (iii) **self-dated**
  — the only date evidence is the author's own file content, and the repository's commit history was
  **force-rewritten**, which weakens even GitHub's own timestamps as evidence.
- **What would raise it:** a **DOI through a citable archive** (Zenodo/Software Heritage give an
  identifier and an independent timestamp without peer review), plus **≥1 independent adopter** and
  **written third-party statements** interpreting the impact. A tag/release with a version number.
- **Cost/effort:** DOI minting is **near-zero cost, same-day**. Independent adoption is **slow and
  not fully controllable** — it cannot be manufactured. This is the cheap half of the fix.

### 3.2 The private implementation

- **What it evidences:** the real engineering; under criterion 5, potentially the *"major
  significance"* half, since the design's claims are verified by code an examiner cannot see.
- **The tension, stated plainly:** evidence that cannot be produced is not evidence. The
  implementation is **not citable without disclosure** (`consonance/src/journal.ts` and
  `src/journal.ts` 404 at every historical ref — `DISCLOSURE_INVENTORY.md:17`), and disclosing it
  would destroy the asset. Worse, the **one-day AGPL window** (`:19`) means the implementation
  *was* public and could have been cloned: the author cannot truthfully swear it was never
  published, and the petition's account of the work must not claim otherwise.
- **What would raise it:** a **non-disclosing** bridge — a *published* architectural specification
  and a **redacted reproduction** (fixtures, schema, evaluation harness, pre-registered commands)
  that lets a third party re-run some claims **without the kernel source**. That is the only route
  that turns private work into independently checkable impact without giving up the implementation.
- **Cost/effort:** **high** — it is new engineering and carries its own disclosure risk. Note that
  `TRADE_SECRET_AUDIT.md` §4.3 and §5.2 already identify the fixture and schema as *already released*,
  so a minimal reproduction subset is partially built.

### 3.3 The MIT-published mechanisms — a loss **and** a usable lever

- **The loss:** 13/13 mechanisms public removes the secrecy that the earlier plan treated as the
  work's commercial advantage. The design is no longer proprietary. That is a real cost and it is
  not reversible.
- **The lever, and it is the important one:** **criterion 5 wants third-party use.** Its two example
  bullets are *"contributions to repositories … with evidence of significant … impact"* and
  *"Evidence of commercial use of the beneficiary's work"* — both are about **what other people did
  with the work**, not about what the author kept. A **permissive MIT licence is the enabling
  condition for exactly that evidence**, and — critically — it avoids the failure
  `CODE_LICENSING_STRATEGY.md:398–409` documents for the noncommercial alternative: *"Suppressed
  adoption suppresses the third-party impact evidence that criterion 5 rewards … Under this policy
  the strongest potential exhibit is legally foreclosed."* **MIT does not foreclose it.**
- **Current weight:** **zero as evidence today** (no adopters, no usage), but **positive as
  infrastructure** — it is the only licence posture under which the criterion-5 evidence can still be
  created. This is the corrected assessment's central inversion: the disclosure is simultaneously the
  biggest evidentiary loss and the only remaining path to criterion 5.
- **What would raise it:** documented third-party use under the MIT terms — a named dependent
  project, an integration, a citation in someone else's paper or repo, a commercial deployment — each
  captured as a dated artifact.
- **Cost/effort:** **low to accept, unknowable to obtain.** Adoption cannot be forced; it can only be
  made frictionless and then evidenced.

### 3.4 Papers

- **What it evidences:** authorship. **Zero arXiv, zero DOI, zero peer-reviewed publications, zero
  citations.** The corpus is a private working paper and ~39 internal research records.
- **Current weight:** **zero for criterion 5**, thin for criterion 6 (authorship of scholarly
  articles *"in professional journals, or other major media"* — internal records are not a
  professional journal or major medium).
- **Paper #3 is near-ready** (the encoder-crossover manuscript; `TRADE_SECRET_AUDIT.md` §4.3 treats it
  as a hypothesis-tested manuscript). It is the **only near-term path to a peer-reviewed or at least
  DOI'd, citable artifact**.
- **What would raise it:** publish #3 to a venue with a DOI and, ideally, peer review; then wait for
  independent citations (uncontrollable, slow).
- **Cost/effort:** **moderate effort, high value** — one manuscript, already substantially written;
  the binding constraint is time-to-publication, not authoring.

### 3.5 Criterion 6 — what the no-citation rule does *and does not* relieve

- **What it relieves:** for **criterion 6 (authorship)**, citations are **not required** —
  `orchestration/units/ULIC.md:63`: *"A petitioner need not provide evidence that the beneficiary's
  published work has been cited."* So the absence of a citation *record* does not, by itself, defeat
  criterion 6. (Caveat, recorded honestly: this unit did not fetch the source; it is second-hand via
  ULIC.)
- **What it does NOT relieve:**
  1. **It does not apply to criterion 5.** Criterion 5's own example list still includes
     *"Documentation that the beneficiary's original work was **cited at a level indicative of major
     significance** in the field"* (`VISA_US_ROUTES.md:350–351`) — and criterion 5 is the criterion
     this profile must win.
  2. **It does not create publications.** It removes a requirement *on* publications; it does not
     supply the *"scholarly articles in the field, in professional journals, or other major media"*
     that criterion 6 is about. Zero publications is still zero publications.
  3. **It does not touch the final-merits step.** Even three satisfied criteria can lose at totality
     — the structure confirmed in `VISA_US_ROUTES.md:545–547`.

---

## 4. Gap ranking and highest-leverage next action

Ranked by **reachability** (what can actually be done, soonest, by this author):

| Rank | Gap | Reachability | Fix |
|---|---|---|---|
| **1** | **No persistent identifier / no citation anchor for the public repo.** Self-dated GitHub content, history force-rewritten. | **High — days, near-zero cost** | Mint a **DOI** (Zenodo release / Software Heritage SWHID). Converts the repo into a dated, independently timestamped, citable artifact. |
| **2** | **No third-party use of the MIT mechanisms.** Criterion 5's actual target. | **Medium — months, not fully controllable** | Make adoption frictionless (done: MIT), then **solicit and document** use — a named external adopter, an integration, a downstream dependency. |
| **3** | **No independent expert letters.** | **Medium — weeks, cost = the author's network** | ≥2 letters from practitioners who state **"the basis of the writer's knowledge and expertise"** and describe the specific contribution against the field's baseline (`VISA_US_ROUTES.md:610`). Higher value than any self-authored document. |
| **4** | **Paper #3 unpublished; zero peer-reviewed papers.** | **Medium — one submission cycle** | Submit #3; obtain a DOI and, if possible, peer review. |
| **5** | **No reproduction path that does not disclose the kernel.** | **Low-to-medium — real engineering** | Publish a redacted reproduction subset (fixture + schema + harness + pre-registered commands) — partially built already (`TRADE_SECRET_AUDIT.md` §5.2). |
| **6** | **Statements S1–S6 remain in `VISA_US_ROUTES.md` and would mislead a brief writer.** | **High — documentation edit, minutes** | A future unit should annotate S1–S6 in place (this unit does not edit existing files). |

**Single highest-leverage next action:** **mint a DOI for the public design repository and, in the
same release, document the MIT grant as the standing invitation for third-party use** — because it is
the only step that (a) is fully within the author's control, (b) is cheap and fast, and (c) converts
the already-public design from *self-dated GitHub content* into a **dated, citable, independently
timestamped artifact whose permissive licence makes objective third-party impact evidence possible**.
Rank 2 (actual adoption) is what criterion 5 ultimately requires, but it is not fully controllable and
will not arrive faster than the citable artifact that invites it. Rank 3 (expert letters) is the
natural second move, since the letters must *interpret* the artifact.

---

## 5. The honest ceiling

This assessment does not soften the following.

1. **No verified precedent.** `VISA_US_ROUTES.md:773` records, of the targeted searches for a case
   matching *"a software/AI researcher without a PhD"*: **"None was verified, and none is cited."**
   There is **no on-disk precedent** for this exact profile succeeding on O-1A or EB-1A.
2. **The nearest analogue is a denial, and of a better-credentialled person.**
   **Kazarian v. USCIS, 596 F.3d 1115 (9th Cir. 2010)** is recorded at `VISA_US_ROUTES.md:547–548`
   as *"Ninth Circuit upheld denial of EB-1A to a **Ph.D.-holding theoretical physicist**"*, with the
   parenthetical *"(upholding agency's decision to deny EB-1 classification to Ph.D.-holding
   theoretical physicist working with researchers at Caltech)"*. The same row flags it as
   **`UNVERIFIED` directly** — *"I did not open the opinion"*; it is verified *through* the AAO
   decision (In Re: 43728055) that cites it. **A PhD physicist with Caltech collaborators was denied.**
   The corrected facts do not improve this profile's position relative to his: the author has **no
   PhD, no peer-reviewed papers, no citations, no DOI**, and — unlike the physicist — must also
   explain a **force-rewritten repository history** and a **one-day public window** of the
   implementation.
3. **Disclosure is not a free upgrade.** It gives the author a **published contribution** *and*
   removes **secrecy** — both are true and neither cancels the other. The published design is
   evidence of *originality*; it is not yet evidence of *major significance*, which is the criterion
   that must be won.
4. **A facts-and-circumstances discretionary call.** O-1A risks a discretionary denial
   (`VISA_US_ROUTES.md:268–270`), and the two-step structure means criteria satisfied can still fail
   at totality (`:545`). The realistic near-term ceiling on the current record is **one or two
   criteria — not three** — and the gap to three is closed by *evidence created after today*, not by
   re-reading what exists.

---

## 6. Provenance

| Quote used | Where it lives on disk | Provenance |
|---|---|---|
| Criterion 5 wording; software-repositories bullet; commercial-use bullet | `strategy/CODE_LICENSING_STRATEGY.md:382–393`; corroborated `strategy/VERIFICATION_REPORT_2.md:16` | **second-hand (via UCODE1, corroborated by UVER2)** — fetched 2026-10-15 from `volume-2-part-m-chapter-4`; this unit did not fetch it |
| Criterion 6 no-citation sentence | `orchestration/units/ULIC.md:63` | **second-hand (via ULIC)** — card said `VISA_US_ROUTES.md` or a `VERIFICATION_REPORT`; found in neither |
| 13/13 disclosure; byte-identical digest; 404s; one-day AGPL window | `strategy/DISCLOSURE_INVENTORY.md:15,17,19,29–38` | on-disk, primary to UDISC1/fetched by that unit |
| Kazarian denial; no-verified-precedent; two-step risk | `strategy/VISA_US_ROUTES.md:545–548,773,268–270` | on-disk (Kazarian `UNVERIFIED` directly, verified through the AAO decision) |
| O-1 regulation, agent rule, advisory opinion | `strategy/VISA_US_ROUTES.md:215–241,277–304` | on-disk, primary-by-UCORR2/UVER2 |

**No legal standard, statistic or precedent in this document was invented.** Everything is either
quoted from disk with a location or labelled as this unit's own assessment. No web tool was used.
