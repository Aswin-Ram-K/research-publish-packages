# SUBMISSION_RUNBOOK.md — the ordered steps the author performs himself

Unit **UDEPOSITDOC1**. This is a **runbook for a human**: every step says *what to do*, *where*, *what
to paste*, and *what to expect*. Field values live in `strategy/DEPOSIT_METADATA.md` — this file says
*when* to use them and never restates them. Nothing here is done by an agent.

**Order: (1) Zenodo data deposit → (2) the preprint → (3) TMLR later.**

Legend — **[AUTHOR-ONLY]** = an account action, a click, or a fact only the author holds; no agent can
do it. **[AUTHOR-ONLY]** steps are: signing in, clicking *Publish*, clicking *Submit*, supplying the
minted DOI back, supplying contact/funding/AI-use facts, and OpenReview profiles.

**Nothing in this runbook uploads, submits, registers or contacts anyone. No network write is made by
the agent that wrote it.**

---

## Step 0 — Pre-flight (do this once, before Step 1)

1. Re-measure the deposit file (§0 of `DEPOSIT_METADATA.md`) and confirm the digest is still
   `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7` with md5
   `4066c3428c1e4836d200909c6a2db6b0` (159,014 B; superseded `bcdbf75eff70eec77fc1f4a181947c86dd9c12862871315e1dfeec8578fbb6a2` / 158,956 B, 2026-10-18 UFIXDEP4, rebuilt the same day by UREADMEFIX1) for the
   tarball. The zip `8e2f603efdf7990b4decb1d73bf14002c53d1da47ab48c482a4217a3b5183610` (169,869 B) is
   **not a deposit candidate** — it is recorded only so a stray copy can be recognised and left out.
   **If either digest has moved, stop and rebuild** — `strategy/DEPOSIT_ARCHIVE.md:48-49` invariant 2
   says any change under `scratch/uneutral10/package/` invalidates every recorded row.
2. **Decide the three author questions** in `DEPOSIT_METADATA.md` §3 and §4: the creator name split,
   which file to upload, and whether to set a version. Write the answers down; they are used in
   Step 1.3.
3. Build/confirm the identified PDF: `papers/encoder-crossover-190/rendered/encoder-crossover-190.pdf`
   — 188,364 B, 25 pages, sha256
   `752747f87423f1fa87cf365179ed1c93915ad65a1aed00e8d8929979964699a1` (re-measured by UDOCREFRESH2 2026-10-18; superseded 184,933 B / `58c22c906d0220fb707eed538bf13bf33304a4b2751b033e0d4a0c71bce7fd44`, preserved at `rendered/_superseded/encoder-crossover-190-tectonic-prior-main-58c22c90.pdf`, 2026-10-18 URENDER4). It
   is only needed at Step 2.
4. Do **not** paste the Zenodo DOI into the paper yet — that is Step 1.5, and Step 3 depends on the
   order (see the Step 3.1 warning).

---

## Step 1 — Zenodo: the data deposit, and its DOI

### 1.1 [AUTHOR-ONLY] Create or sign in to the Zenodo account
- **Where:** <https://zenodo.org/> → *Log in* (or sign up).
- **Expect:** the *New upload* page. Zenodo mints the DOI at publish; nothing costs anything.

### 1.2 Upload the one file
- **Where:** the *New upload* page → *Drag and drop files* / *Choose files*.
- **What:** `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` — **one file
  only**. Do not also upload the zip, the `uauclean1` zip, or the `778818b2…` archive.
- **Expect:** the file listed with its size, **159,014 bytes**; Zenodo may display a checksum — the
  sha256 must read `478941c0…c51e89d7` and the md5 `4066c3428c1e4836d200909c6a2db6b0`
  (superseded: `bcdbf75e…fbb6a2`, then `956d6363…`, then `7389bd87…`).

### 1.3 Fill the metadata form
- **Where:** the *Basic information* panel of the same page.
- **What to paste:** every value from `strategy/DEPOSIT_METADATA.md` §1 — the paste block, then §1.1
  (description, verbatim), §1.2 (upload type) and §1.3 (related identifiers / version).
- **Expect:** the licence picker finds *PolyForm Noncommercial License 1.0.0*; if it does not, follow
  `ZENODO_UPLOAD.txt:58-61` (select *Other* and paste the stated text). Leave creators' affiliation and
  ORCID empty. Leave *Related identifiers* empty.

### 1.4 [AUTHOR-ONLY] Click *Publish*
- **Where:** the green *Publish* button.
- **Expect:** **this is the irreversible click** — Zenodo mints the DOI and the record becomes public
  immediately. **Paste the DOI back:** copy the DOI (and the *Concept DOI*, which survives future
  versions) out of the page before closing it. If the created date is wrong, that is the moment to fix
  it, not later.

### 1.5 [AUTHOR-ONLY] Paste the minted Zenodo DOI back into the manuscript
- **Where:** `papers/encoder-crossover-190/submission/main.tex`, the `\section*{Data and code
  availability}` block (recorded at `:405`; the slot is a `DOI:` marker awaiting a value) and, if
  desired, `CITATION.cff`.
- **What to paste:** the DOI exactly as Zenodo shows it. **Copy it; do not reconstruct it** — the
  `10.5281/zenodo.NNNNNNN` shape is a convention this workspace never verified.
- **Expect:** the data-availability statement now cites a persistent identifier.
  **This edit changes `main.tex`, which is load-bearing for Step 3 — note the new sha256.**

### 1.6 Optional, after the preprint exists — add the related identifier
- **Where:** the published Zenodo record → *Edit* → *Related works*.
- **What:** relation **`is supplement to`**, identifier = the Preprints.org DOI from Step 2.4.
- **Expect:** the two records cross-reference. Do this only after Step 2; the paper's DOI does not exist
  before then (`DEPOSIT_METADATA.md` §1.3). The GitHub repo may be added as `is supplemented by` **only
  once the author confirms it is public**.

---

## Step 2 — Preprints.org: the preprint

### 2.1 Confirm the first-page requirements
- **Where:** `strategy/SUBMISSION_READINESS.md:87` and `strategy/FORMATTING_REQUIREMENTS.md:634`
  (R30) — the **current status is FAIL**.
- **What:** the rendered first page must carry title, author list, abstract, **keywords**,
  corresponding-author contact and affiliations.
- **Expect:** you must add keywords and a corresponding-author contact yourself; the keywords to use are
  in `DEPOSIT_METADATA.md` §2, the contact is **yours alone** to supply. If the name-only byline leaves
  no affiliation, state it explicitly rather than inventing one.

### 2.2 [AUTHOR-ONLY] Create the Preprints.org account and start a submission
- **Where:** <https://www.preprints.org/> → *Submit*.
- **Expect:** no endorsement is required (that is the whole point of this route —
  `strategy/ARXIV_SUBMISSION_PREP.md:104`), and it is free (`strategy/PUBLICATION_STRATEGY.md:73`).

### 2.3 Paste the metadata and upload the file
- **Where:** the submission form.
- **What to paste:** every value from `strategy/DEPOSIT_METADATA.md` §2 — including §2.1 (abstract,
  verbatim), and **§2.2, where the subject area must be picked by you from the live dropdown** (this
  workspace never recorded Preprints.org's taxonomy; the sheet's mapping is a recommendation only).
- **File:** the **LaTeX source**, zipped with every file needed to rebuild the PDF:
  `papers/encoder-crossover-190/submission/main.tex` (84,695 B,
  `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`; superseded 2026-10-17
  UDEPOSITDOC2: 84,223 B / `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`).
  Preprints.org accepts
  "Microsoft Word or LaTeX format" and requires any `.bib` in the archive; **a PDF alone is not a listed
  accepted source format** (`DEPOSIT_METADATA.md` §2.3,
  <https://www.preprints.org/instructions-for-authors>). The PDF from Step 0.3 is for the final/TMLR
  record, not this upload.
- **Licence:** `CC BY 4.0`. **DOI field:** leave empty — Step 2.4 mints it.
- **Article type:** `Preprint article` (`strategy/SUBMISSION_READINESS.md:87`, R31).
- **Expect:** the DOI field stays greyed/empty; screening applies.

### 2.4 [AUTHOR-ONLY] Submit, then read the minted DOI back off the posted preprint
- **Where:** the *Submit* button; then the posted preprint page.
- **Expect:** screening in **days** (`strategy/PUBLICATION_STRATEGY.md:73`); Preprints.org mints and
  displays the preprint's own DOI. **Copy that DOI** — it is the value for Step 1.6.
- **Paste it back:** only into the Zenodo record (Step 1.6). **Never into the TMLR PDF** — see Step 3.

> **Now the preprint is public and author-identified. From this moment Step 3's hard constraint is live.**

---

## Step 3 — TMLR, later

### 3.1 THE HARD CONSTRAINT, before anything else

> **The TMLR PDF must not link the preprint, the Zenodo DOI, or the GitHub repository — not in the
> body, not in the references, not in an appendix, not in the supplementary materials.**

Source: `strategy/TMLR_POLICY.md` Q2 — TMLR's Author Guidelines require "double blind of the TMLR
submission itself must be maintained by **not linking to another version that includes the authors'
names**"; TMLR is named-and-known for the preprint link, and `strategy/TMLR_POLICY.md` §Q2 states the
cautious reading that a named data DOI and a named GitHub URL are the same kind of link. **The
constraint is not "don't post the preprint" — it is "don't point at it from the TMLR PDF."**
Supplementary material must be anonymized too (`TMLR_POLICY.md` Q4).

**The stated order is CONFIRMED CORRECT** (checked 2026-10-17). Step 1.5 pastes the Zenodo DOI into the
identified `main.tex`; the anonymous variant at `scratch/utmlr1/anonymous/main.tex` was built **before**
that paste, so it does not carry the DOI today. But any variant built from the post-Step-1.5 `main.tex`
**would** inherit it and break this rule.

**REQUIRED ORDER — do not deviate:**
1. publish the Zenodo deposit and **paste the DOI into the identified `main.tex`** (Step 1.5);
2. **rebuild the anonymous TMLR variant from that final identified source** — the rebuild must start from
   the post-DOI `main.tex`, not from the pre-DOI one;
3. **strip the Zenodo DOI** — and every other named link: the preprint DOI and the GitHub URL — from the
   rebuilt variant; **the anonymous TMLR variant must NOT contain that DOI**;
4. re-run `scratch/vtmlr1/rg/anoncheck.py` on the rebuilt variant and require PASS.

Copying the DOI across from the identified source into the anonymous one is the failure this order exists
to prevent. A variant containing the DOI is not submittable. **Do not rebuild the variant now** — the DOI
does not exist yet, and the rebuild belongs to the unit that holds it.

### 3.2 Re-use the compliance work; do not redo it
- **Rule statement:** `strategy/TMLR_POLICY.md` (§Q2 for the no-link rule, Q4 anonymity, Q5 AI
  footnote, Q6 the mandatory `tmlr.sty`, Q7 timeline, Q9 parallel submission).
- **The anonymised artefact already built:** `strategy/TMLR_SUBMISSION.md` — `scratch/utmlr1/anonymous/main.tex`
  (84,206 B, `370472969027759c15d3efd980a2b6246c76aecdd130176f37c98ab9733bbcc9`) and
  `scratch/utmlr1/out/main.pdf` (184,983 B, 25 pages,
  `89d62e1d6d4c1932048f31c0bc3f39b532a48ded18fc94c68c061c931c23ccfa`). It strips the byline at
  `main.tex:12` and the name at `:435` — **those were the only two lines needing change at the time it
  was built**, before the DOI existed.
- **The independent verification already done:** `strategy/TMLR_VERIFICATION.md` (VTMLR1, overall
  **pass**), whose **C3** check already tests for "own preprint-or-DOI link" and records the residual
  "Zenodo DOI pending" text at `:375`/`:407` with **no DOI value present**. Its red→green guard is
  `scratch/vtmlr1/rg/anoncheck.py` — PASS on the anonymous artefact, FAIL when a name is re-inserted.
  **Re-run exactly that guard after 3.1's regeneration.**

### 3.3 Post the anonymised PDF
- **Where:** the TMLR submission portal (OpenReview).
- **What:** the PDF built from the regenerated anonymous `main.tex`, produced with the **mandatory**
  `tmlr.sty` template (Q6) — the current source is a stock `article` class
  (`strategy/SUBMISSION_READINESS.md:87`), so this rebuild is still outstanding.
- **Expect:** a format violation can mean rejection without review; the portal takes a PDF plus up to
  100 MB of PDF/ZIP supplementary material.
- **AUTHOR-ONLY extras:** the **AI-use footnote on page 1** (Q5 — mandatory, and it must not name the
  author); complete OpenReview profiles for every author (Q3); the authorship set is frozen at
  submission (Q9).

### 3.4 [AUTHOR-ONLY] Submit, then wait
- **Where:** *Submit*.
- **Expect:** about **9 weeks** to a final decision (Q7); an action editor within a week; three public
  reviews; ~2–4 weeks of discussion. Possible outcomes: *accept as is*, *accept with minor revision*,
  *reject* — there is no "major revision".

### 3.5 After acceptance — camera-ready swaps the links back in
- **Where:** the camera-ready PDF, verified by the action editor.
- **What:** the public GitHub repository and the Zenodo DOI **may now be cited normally**
  (`strategy/TMLR_POLICY.md` §Q4). Swap the anonymized mirror out.
- **Expect:** identity is disclosed once a decision is made; **on a reject, revealing identity is
  optional** and precludes a revised resubmission to TMLR (Q4).

---

## Author-only checklist (the steps no agent can perform)

| step | author-only action |
|---|---|
| 0.2 | decide the name split, the upload file, the version |
| 1.1, 1.4 | Zenodo account, and clicking **Publish** (irreversible) |
| 1.5, 2.4 | copying the minted DOIs back out of the services |
| 1.6 | editing the published Zenodo record |
| 2.1, 2.3 | supplying corresponding-author contact; picking the subject area |
| 2.2, 2.4 | Preprints.org account and clicking **Submit** |
| 3.3, 3.4 | OpenReview profiles, the AI-use facts, the TMLR rebuild, clicking **Submit** |

**Blockers that stay open at the end of this runbook:** the paper's DOI does not exist until Step 2.4;
Preprints.org's **first-level** subject area is fixed as *Computer Science and Mathematics* but its
**second-level** entry is unpicked (`DEPOSIT_METADATA.md` §2.2); the creator name split is unconfirmed;
TMLR's `tmlr.sty` rebuild and the post-DOI re-anonymisation are outstanding — per the reinforced order in
**3.1**, the anonymous variant must be **rebuilt from the final identified source after the DOI is pasted**
and **must not contain that DOI**.
