# `strategy/` — index, and the verification ledger

**Unit:** UCAP1 · **Date:** 2026-10-14 · **Purpose:** a map of this folder that says **what has been
independently verified and what has not.** It is not a summary; read the files themselves.

**What this folder is.** Eight documents produced from the read-only Duval/Consonance corpus
(`/home/zer0null/Duval`): which papers the corpus can support, where to publish them, and which
immigration routes those publications could serve. **Nothing here has been executed** — no paper
posted, no release tagged, no application filed.

---

## 1. The eight files

| File | What it is | Verified? |
|---|---|---|
| [`PAPER_CANDIDATES.md`](PAPER_CANDIDATES.md) | 14 ranked paper candidates from `docs/research/` | **`pass-with-corrections`** (UVER2, **independent** — [`VERIFICATION_REPORT_2.md`](VERIFICATION_REPORT_2.md), 2026-10-15). All ten protected statistics were re-derived from the corpus: **9 exact, 1 contradicted** — the imajev row count, **3,590 → 3,690**, corrected at `:305` by UCORR2. **One number is `not_reproduced`:** the pre-UCORR1 citation census cannot be re-queried (the superseded file is untracked, no backup) — see §6. |
| [`PAPER_CANDIDATES_SUPPLEMENT.md`](PAPER_CANDIDATES_SUPPLEMENT.md) | Material outside `docs/research/`: 7 corrections, 1 new candidate (NC1), novelty-risk verdict | **Not independently verified.** The V13 / arXiv 2608.03836 prior-art finding is sourced from the corpus's own `SOURCE_VERIFICATION.md` and was **not** re-confirmed by a second unit in this workspace. It remains **not independently verified** as of 2026-10-15: UFIX2's citation re-anchoring and UH3's attribution correction are citation hygiene, not verification. |
| [`PUBLICATION_STRATEGY.md`](PUBLICATION_STRATEGY.md) | Venue comparison, DOI mechanics, O-1 mapping, costed timeline | **`pass-with-corrections`** (UVER1, independent). Its one correction applied by UCAP1 at L185–187 (406 → 408 lines; nothing else changed). |
| [`VISA_US_ROUTES.md`](VISA_US_ROUTES.md) | Cap-exempt H-1B, O-1A, EB-1A/NIW, 7 AAO precedents | **`pass-with-corrections`** (UVER2, **independent** — [`VERIFICATION_REPORT_2.md`](VERIFICATION_REPORT_2.md), 2026-10-15). Every decision-changing claim confirmed verbatim (the `(h)(8)(iii)(F)(4)` cap-exempt paragraph, `INA 214(g)(5)`, the eight O-1A criteria, all seven precedent identifiers). **1 citation contradicted, corrected by UCORR2:** the software-repository example was attributed to 6 USCIS-PM F.2 — where the word "repositories" occurs **0×** — and is verbatim in **2 USCIS-PM M.4** (`:348`, `:362`, `:551`, `:609`). **The O-1A recommendation is unchanged; only the citation was wrong.** |
| [`VISA_INDIA_EUROPE.md`](VISA_INDIA_EUROPE.md) | 8 countries, 28 routes, 20 fellowships, precedents | **`pass`, zero contradicted** (UVER1, independent — 26 claims re-fetched 2026-10-15). |
| [`SOCIAL_PRESENCE.md`](SOCIAL_PRESENCE.md) | Platform plan, O-1 mapping, 30-day checklist | **Two claims author-verified at source** (arXiv 2026-01-21 endorsement change; Google Scholar institutional-email rule). **No independent re-check.** Its author marks 10 further items `UNVERIFIED`. |
| [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) | UVER1's independent re-check of the two files above | — (this *is* the verification). |
| [`VERIFICATION_REPORT_2.md`](VERIFICATION_REPORT_2.md) | UVER2's independent re-check of `PAPER_CANDIDATES.md` and `VISA_US_ROUTES.md` | — (this *is* the verification). |

**Read the asymmetry honestly.** Four of eight files have now been through an independent verifier —
`VISA_INDIA_EUROPE.md` and `PUBLICATION_STRATEGY.md` (UVER1, 2026-10-15; report `VERIFICATION_REPORT.md`),
then `VISA_US_ROUTES.md` and `PAPER_CANDIDATES.md` (UVER2, 2026-10-15; report `VERIFICATION_REPORT_2.md`).
Of the remaining four rows, `PAPER_CANDIDATES_SUPPLEMENT.md` and `SOCIAL_PRESENCE.md` rest on their
authors' own measurements, however carefully made, and have never had an independent re-check; the two
`VERIFICATION_REPORT*.md` files *are* the verifications, not independently verified deliverables.
"Author-verified" is not a lesser accusation — it is simply a different and weaker claim, and this index
will not launder it.

> **[corrected by UCONS1, 2026-10-15]** §1 formerly read "Seven documents" / "The seven files" and
> omitted `VERIFICATION_REPORT_2.md`. Measured: `strategy/` holds **nine** `.md` files — this index plus
> **eight** documents; the count and the missing row are now corrected. No verdict changed.

---

## 2. What was independently verified, and by whom

- **UVER1** (not the author of either document) re-fetched **every load-bearing claim** in
  `VISA_INDIA_EUROPE.md` and `PUBLICATION_STRATEGY.md` against live primary sources on 2026-10-15:
  **zero contradicted claims**, 6 `not_reproduced` (coverage limits, all non-load-bearing), and
  **exactly one** `overstated` — the JOSS date, now corrected.
- **Repo facts** in `PUBLICATION_STRATEGY.md` §1 were **re-measured read-only** by UVER1: 857 commits,
  earliest `2026-09-28 dae60e0`, head `24f339c`, one tag `m0-baseline`, fixture 2,220 lines / 191
  `id:` matches / 145,031 B, `CITATION.cff` with **no `doi:`** — all exact.
- **The `$0` venue premise** was tested adversarially by UVER1 (searched TMLR's four surfaces for
  `fee|APC|publication charge|article processing` and found none; JOSS and JAIR state `$0`). It holds.
- **The append-only norm.** This corpus corrects by dated errata headers, not silent rewrites — see
  the `ERRATA HEADER` at the top of `PAPER_CANDIDATES.md` (UCORR1) and the inline
  `[corrected by UCAP1 per UVER1]` marker at `PUBLICATION_STRATEGY.md:187`.

---

## 3. The three things to act on first

1. **Start the clock — today.** Tag a release → mint the **Zenodo DOI** → put it in `CITATION.cff`;
   and **start the arXiv submission for #3 now**, because the submission triggers the **endorsement
   request** and endorsement is the long pole (no institutional email, no prior arXiv authorship:
   `SOCIAL_PRESENCE.md` §arXiv). Everything downstream waits on this.
2. **Fix the 190-case fixture with a second labeller.** ~12.7 person-hours (380 judgements). It is the
   rate-limiting item and it **unblocks several candidates at once** (#3/#4/#5/#10) by supplying the
   external-validity evidence each of them currently lacks.
3. **For immigration, the mechanism most likely to fit is `8 CFR 214.2(h)(8)(iii)(F)(4)`** — a
   part-time research affiliation at a qualifying entity, documented as **≥50% of work time on duties
   furthering that entity's research mission**, where **telework counts** as work "at" the entity
   (`VISA_US_ROUTES.md:613`, `:668`). It converts an affiliation into cap-exempt H-1B without an
   employer lottery.

---

## 4. What is NOT done

- **No second labeller and no external benchmark exists anywhere in the corpus.** Every strong
  candidate therefore still **fails on external validity**: the measurements are the authors' own,
  on the authors' own fixture, judged by the authors' own labels. This is the single largest gap.
- **No named individual immigration precedent** was found for a **software/AI researcher without a
  PhD.** `VISA_US_ROUTES.md` carries 7 AAO decisions — **4 dismissed, 1 withdrawn/remanded** — and
  `VISA_INDIA_EUROPE.md` carries **9 rule-level precedents and 0 named individual cases**. The
  documents say so; do not cite a personal precedent from them.
- **The pipeline cannot produce evidence.** It holds **0 claims / 0 evidence / 0 verdicts**. The
  binding constraint is an internal **producer gate** (`run.py:2008–2012`, `:2067`) plus an
  **unimplemented `mine` stage** — not the model endpoint, which is reachable. Until that is fixed, no
  verdict can be anything but `UNVERIFIED`.
- **Not executed:** no arXiv post, no Zenodo DOI, no `CITATION.cff` edit, no JOSS/TMLR submission, no
  second labeller engaged, no application filed. The timelines are plans, not records.
- **Coverage limits, not defects:** `udi.no` and `migri.fi` returned HTTP 403 to every unit; the
  Norway/Finland cells are consequently thin. Several venue fee lines remain `UNVERIFIED`.

---

## 5. Not legal advice

`VISA_US_ROUTES.md` and `VISA_INDIA_EUROPE.md` are **research summaries, not legal advice.** They are
not a substitute for a licensed immigration attorney in the relevant jurisdiction, they are
date-stamped to rule changes in force in **2026**, and several thresholds are **`UNVERIFIED`**. Do not
file, or decide not to file, on the strength of these documents alone.

---

## 6. Defect ledger — what is closed, and what remains open

*Rewritten by UH3 (2026-10-15). This section formerly read "Known defects recorded, not fixed (for a
separate unit)" and listed the two residues below as **OPEN**. Both are now closed, so that wording was
stale; per the append-only-errata norm the superseded items are named here, not deleted.*

**Closed by UFIX2 (2026-10-15)** — evidence: `orchestration/handoffs/UFIX2.json`.

1. **JOSS date residue — CLOSED.** `PUBLICATION_STRATEGY.md` L24/L209/L292 no longer carry the
   unqualified "≈2027-03-28": each now states `2027-03-29` with L185's condition (*"only if the
   repository has been publicly available since 2026-09-28 — a premise that is itself `UNVERIFIED`
   (§11.10)"*) and the marker `[corrected by UFIX2 per UCAP1/UVER1]`. L185 is unaltered.
2. **Supplement citations — CLOSED.** `PAPER_CANDIDATES_SUPPLEMENT.md` §7 cited `PAPER_CANDIDATES.md`
   at pre-UCORR1 line numbers. UFIX2 re-resolved **16 citations** against the current 970-line file
   (each anchor read back at the line cited; no constant-offset shift) and added a dated errata header.
   The one anchor with no counterpart (`:295–336` → B6) is stated in place.

**Closed by UH3 (2026-10-15)** — citation hygiene only; no finding, number or verdict changed.

3. **Stale companion line count — CLOSED.** The supplement's companion line said *"(UP1, 710 lines)"*.
   It now records that **UP2 surveyed the pre-revision 710-line file**, and that UCORR1 revised that
   companion to **970 lines** — the surveyed-version distinction the errata header protects. Measured:
   `wc -l strategy/PAPER_CANDIDATES.md` → **970**. (The line is **L16**, not the L26 UFIX2's card
   recorded.)
4. **Mis-attributed candidate — CLOSED.** The supplement attributed the SM-pilot results citation to
   "candidate #6"; it now names **#8 (B8)**, citing `PAPER_CANDIDATES.md:576`. Verified by reading that
   line: it cites `docs/research/SM_PILOT_RESULTS.md`; B6 (`:394–432`) cites no SM file, as UCORR1's
   own note at `:598–599` records. UP2's finding is unchanged.

**Closed by UVER2 (2026-10-15)** — verdict for **both** documents: **`pass-with-corrections`**. Evidence:
`strategy/VERIFICATION_REPORT_2.md` (144 lines, 38 tool calls). Corrections applied by **UCORR2**, marked
`[corrected by UCORR2 per UVER2]`; handoff `orchestration/handoffs/UCORR2.json`.

5. **Independent verification of `PAPER_CANDIDATES.md` and `VISA_US_ROUTES.md` — CLOSED.** Both were
   "in progress" under UVER2; that report has landed. `PAPER_CANDIDATES.md`: ten protected statistics
   re-derived from the corpus, **9 exact / 1 contradicted** — imajev rows **3,590 → 3,690** at `:305`
   (a transposed digit inherited from `FINDINGS_REGISTER.md:47`). `VISA_US_ROUTES.md`: every
   decision-changing claim confirmed verbatim; **one citation contradicted** — the software-repository
   example was attributed to 6 USCIS-PM F.2, which contains **0** occurrences of "repositories"; it is
   verbatim in **2 USCIS-PM M.4** (O-1A). Corrected at `:348`, `:362`, `:551`, `:609`. Three minor
   `overstated` items repaired: the §13.12 quota flag was **narrowed to the implementing regulations**
   (the figures are correct — INA 214(g)(8)(B)(ii): 1,400 Chile + 5,400 Singapore = **6,800**; E-3
   **10,500**), §2.2's "(C) would not help them even if they had one" was loosened, and §1's O-1A row
   now carries its `UNVERIFIED` flag. **Upgrade:** §13.6's *Matter of Dhanasar* text flag was **closed**
   (UVER2 decoded the DOJ PDF). **The O-1A route recommendation is unchanged** — only the citation was
   wrong.

**Open items — verification gaps, not citation hygiene.**

6. **`PAPER_CANDIDATES_SUPPLEMENT.md` and `SOCIAL_PRESENCE.md` still have no independent verifier**
   (§1). No verifier unit has run on either; the UFIX2 and UH3 passes were citation hygiene and do not
   change that.
7. **An owed correction to the corpus of record (for the user — the target is read-only to this
   workspace).** **`/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47`** (F-EXP11-11) still
   states *"across all 4,090 decider rows and **3,590** imajev rows"*. The correct value is **3,690** —
   evidence: `docs/research/EXP#11-evidence/imajev-rows.jsonl` parses to **3,690** valid JSON rows (0
   invalid), and `imajev-progress.json`'s final `rowsOnDisk` = **3,690**; 3,590 was a mid-run snapshot.
   **UCORR2 verified this line but did not write it.** Any other document that copies F-EXP11-11
   inherits the stale figure.
8. **The pre-revision `PAPER_CANDIDATES.md` citation census is not independently re-derivable.** The
   pre-UCORR1 file was superseded **in place** and is untracked, so no backup exists
   (`git log -- strategy/PAPER_CANDIDATES.md` is empty). UVER2 classified this `not_reproduced`: the
   census **method** and its literal "0×" counts survive in `orchestration/handoffs/UP2.json`, and its
   measurable parts (38 root `docs/*.md`, the `FINDINGS.md` citation, the post-correction counts)
   re-measure correctly — but the pre-revision text itself cannot be re-queried. **Do not present those
   counts as independently verified.**
