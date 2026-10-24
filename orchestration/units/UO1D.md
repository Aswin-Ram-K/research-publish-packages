# UO1D — annotate the superseded premises in `strategy/VISA_US_ROUTES.md`

**Unit:** UO1D · **Date:** 2026-10-15 · **Status:** done
**Hard bound:** 30 tool calls (used 21, including one failed `edit` retried after re-reading and one invalid
handoff draft rewritten as valid JSON via `json.dump`). **Write paths:** `strategy/VISA_US_ROUTES.md`,
`orchestration/units/UO1D.md`, `orchestration/handoffs/UO1D.json`. No web tool used. Target repo untouched.

## Purpose (one)

Annotate `strategy/VISA_US_ROUTES.md` **append-only** so that the six statements superseded by the
disclosure findings are marked in place and the **false-statement trap** is impossible to walk into.

## Why this unit exists

Unit **UO1C** (`strategy/O1_EVIDENCE_ASSESSMENT.md`) found six superseded statements in
`strategy/VISA_US_ROUTES.md` and recorded that they "would mislead a brief writer" (its §4 rank 6), but
in-place annotation was outside its write paths. An **O-1 petition is a sworn filing to a US government
agency**: if the memo's premises led the author to assert something untrue about his own publication
history, the consequence would be far worse than a weak petition. The specific trap UO1C named: the
implementation sat in a **public AGPL-licensed window for ~27 hours**, so **any claim that the
implementation was "never published" would be false.**

## Work done

1. **Top block appended after the front matter** (`:34` onward): a dated
   `SUPERSEDED — unit UO1D, 2026-10-15 (append-only annotation)` block with an S1–S6 summary table, the
   false-statement-trap section, the corrected quote locations, the honest ceiling, the highest-leverage
   action, and the "still holds" list. Nothing deleted, nothing silently rewritten; the front matter's own
   `:6` wording ("a working paper") is retained and corrected by reference.
2. **Six statements marked in place** (each: a visible dated marker, the withdrawn wording quoted, the
   original text left standing):
   - **S1** — after §3.3's paragraph (premise: "a publication and citation record but no PhD"); corrected
     facts: zero arXiv / DOI / peer-reviewed / citations.
   - **S4** — after the criterion-5 "contributions to repositories of software" passage in §4.1; half
     survives, half inverts (13/13 mechanisms now public under MIT). The **quote-location correction** is
     carried in the same marker.
   - **S2, S3, S5, S6** — after the §7 assembly table; S2/S3 unfillable; S5 aspirational not evidential;
     S6 the withheld-paper posture, now **withdrawn**, cost paid.
3. **False-statement trap stated prominently** (own `### ⛔` section, plus a trap reminder in the §7
   marker): public AGPL-3.0 window `ccdab112` **2026-10-09 04:11** → removed by `b81b35e`
   **2026-10-10 07:51**, 528 commits / 441 files / 16,704 LOC, per `strategy/DISCLOSURE_INVENTORY.md:19`
   (recorded there as public artefact P10); 13 of 13 mechanisms public under MIT in
   `github.com/Aswin-Ram-K/publish-present-compete` (`:15,29–38`); therefore **no filing may assert that
   the work, or any part of it, was never published.**
4. **Quote locations re-verified from disk by this unit** (not taken on trust) and cited correctly:
   - `strategy/CODE_LICENSING_STRATEGY.md:382–383` = criterion-5 wording; `:387–388` = software-repositories
     bullet; `:392–393` = commercial-use bullet (i.e. **382–393** as UO1C recorded);
   - `strategy/VERIFICATION_REPORT_2.md:16` = same text verbatim;
   - `orchestration/units/ULIC.md:63` = criterion-6 no-citation sentence;
   - and the negative half of the correction: `strategy/TRADE_SECRET_AUDIT.md` §4 is a per-mechanism
     triage and does **not** contain the criterion-5 text. Any pointer to it for that text is wrong.
5. **Honest ceiling recorded unsoftened**: **one or two of the eight O-1A criteria — not three**; **no
   verified precedent** for a software/AI researcher without a PhD (memo's own §13 item 14: "None was
   verified, and none is cited."); *Kazarian v. USCIS*, 596 F.3d 1115 (9th Cir. 2010) as the **cautionary**
   analogue — a PhD physicist was **denied** — flagged `UNVERIFIED` directly in the memo and verified only
   through AAO **In Re: 43728055**.
6. **Highest-leverage action added**: **mint a DOI** (Zenodo / Software Heritage) for the public design repo
   and **document the MIT grant as a standing invitation for third-party use** — because criterion 5 rewards
   third-party use, and MIT *enables* it where the noncommercial alternative was documented as foreclosing
   it (`CODE_LICENSING_STRATEGY.md:398–409`). The reversal is stated explicitly: **the permissive licence is
   an O-1 asset, not only a loss.**
7. **"Still holds" list added** and nothing disturbed: eight criteria, no-degree reading, agent-petitioner /
   self-petition bar, advisory-opinion requirement, corrected **2 USCIS-PM M.4** attribution.

## Verification performed

- Retained-original check: the three original strings for S1/S2/S4 still occur exactly once each —
  `for an independent researcher with a publication and citation` (1×),
  `**Publication record** — the working paper and the ~39 research records` (1×),
  `That "contributions to repositories of software" example is directly on point` (1×).
- Marker count: `SUPERSEDED (S1)` 1×, `SUPERSEDED (S4)` 1×, `SUPERSEDED (S2, S3, S5, S6)` 1×, top block 1×.
- File grew 785 → 946 lines; every edit was a pure insertion at an anchor asserted to match exactly once.
- The three quoted source locations were read from disk with `sed` in this unit before being cited.

## Provenance / no invention

Every addition traces to `strategy/O1_EVIDENCE_ASSESSMENT.md`, `strategy/DISCLOSURE_INVENTORY.md`, or a file
this unit read (`strategy/CODE_LICENSING_STRATEGY.md`, `strategy/VERIFICATION_REPORT_2.md`,
`orchestration/units/ULIC.md`). No legal standard, precedent or statistic was invented; the memo's own
pre-existing `UNVERIFIED` flags on Kazarian and on the fee figures were preserved rather than cleared.
