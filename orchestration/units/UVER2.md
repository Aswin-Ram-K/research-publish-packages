# UVER2 — independent verifier

**Purpose (one).** Independently verify the two deliverables that UCAP1's audit of
`strategy/README.md`'s verification table found had **never** had an independent verifier:

- `strategy/VISA_US_ROUTES.md` (author UH1) — the 8 CFR 214.2 `(h)(8)(iii)(F)(4)` claim and the seven
  AAO precedents are decision-changing and had been checked by nobody but their author.
- `strategy/PAPER_CANDIDATES.md` (author UP1, revised by UCORR1) — its statistics had only been re-checked
  by UCORR1, the author of that file's revisions.

**Not in scope** (owned by concurrently running units, editing possibly in progress):
`strategy/PAPER_CANDIDATES_SUPPLEMENT.md`, `strategy/PUBLICATION_STRATEGY.md`.

**Hard bound.** Maximum 60 tool calls. **Used: 38.** Stop-and-report-`partial` condition not reached.

**Write paths (declared).**
`strategy/VERIFICATION_REPORT_2.md`, `orchestration/units/UVER2.md`, `orchestration/handoffs/UVER2.json`.
Nothing else was written; scratch fetches were made under `.uver2/` and **deleted** before close, so no
path outside the three declared ones is left modified. `/home/zer0null/Duval` was read only (no writes, no
state-changing git).

**Method.** Every load-bearing claim was taken to its primary source and read verbatim, never to a
secondary summary:

1. `8 CFR 214.2` and `8 CFR 204.5` fetched from the Cornell LII e-CFR mirror, HTML-stripped, and the
   quoted paragraphs extracted by pattern match ([8 CFR 214.2](https://www.law.cornell.edu/cfr/text/8/214.2)).
2. `8 U.S.C. 1184` fetched from govinfo ([2022 ed.](https://www.govinfo.gov/content/pkg/USCODE-2022-title8/html/USCODE-2022-title8-chap12-subchapII-partII-sec1184.htm)) for INA 214(g)(5) and 214(g)(8).
3. All four USCIS Policy Manual chapters cited (2-PM M.3, M.4; 6-PM F.2, F.5) fetched and text-extracted.
4. **All five AAO decision PDFs downloaded and decoded with `pdftotext`**, each identifier read from the
   document itself, each quoted holding located in the text. The `Matter of Dhanasar` DOI PDF was decoded
   too — which the author's fetcher could not do.
5. `PAPER_CANDIDATES.md`'s protected statistics **re-derived from the corpus by parsing**, not by
   transcribing the inventory: JSON row counts, `FINDINGS_REGISTER.md` entries, and `imajev-progress.json`
   time series.
6. The §D census re-measured (`ls docs/*.md | wc -l`) and the pre-revision 0× counts corroborated against
   UP2's recorded command in `orchestration/handoffs/UP2.json`.
7. **Red→green reproduced** on the one machine-enforced guard in scope: `evals/prevention.ts` check F. The
   real file yields GREEN (sentence 19/12/3/4 == parsed table 19/12/3/4); the same table against a mutated
   sentence ("20 classes — 13 automated") yields RED.

**Verdicts.**

| Document | Verdict |
|---|---|
| `strategy/VISA_US_ROUTES.md` | `pass-with-corrections` |
| `strategy/PAPER_CANDIDATES.md` | `pass-with-corrections` |

**Contradicted (2).**

1. `VISA_US_ROUTES.md` §4.1 :351–352, :356–361 and §6.1 :550 attribute the
   *"Contributions to repositories of software, data, designs, protocols, or other technical resources"*
   example and the *"interested government agency"* clause to **6 USCIS-PM F.2(B) criterion 5** (EB-1A).
   Measured 2026-10-15: **0 occurrences of `repositories` in 6 USCIS-PM F.2** (HTML or text); the passage
   is verbatim in **2 USCIS-PM M.4** (O-1A). Replacement: cite 2 USCIS-PM M.4. The doc's own §3.4 already
   names the 8 Jan 2025 alert as affecting *M.3, M.4, M.9*.
2. `PAPER_CANDIDATES.md` :305 states *"**3,590** imajev rows"*. Re-derived: `imajev-rows.jsonl` holds
   **3,690** valid JSON rows and `imajev-progress.json`'s final `rowsOnDisk` is **3,690** (3,590 is a
   mid-run snapshot). **The same correction is owed to `docs/research/FINDINGS_REGISTER.md:47`**, the
   source of the figure.

**Overstated (3, minor, all in `VISA_US_ROUTES.md`).** §1 quota figures stated as fact while §13.12 marks
"quota figures" `UNVERIFIED` (values are correct: 1,400 Chile + 5,400 Singapore = 6,800; E-3 10,500);
§2.2's *"(C) would not help them even if they had one"* (it does open a separate 20,000 pool); §1's flat
"No cap, no lottery" for O-1A (flagged in §9 but not in the table).

**Not reproduced (1).** The literal pre-revision 0× census counts: the pre-revision
`PAPER_CANDIDATES.md` is superseded in place with no backup and is untracked in the workspace repo. The
census's method and result are recorded in `UP2.json`, the 38-file count and the FINDINGS.md citation
re-measure correctly, and the current file's post-correction counts are exactly the claimed increments —
so the census is corroborated, but not independently re-derivable. (The 2,060,775 B figure now reads
2,061,249 B: drift from the concurrent unrelated session writing root `docs/*.md`, not a defect.)

**Unverified.** Every author-flagged §13 item was checked for the item-8 consistency rule and left
standing; my own coverage limits are the 8 Jan 2025 policy-alert PDF, the AAO index page, and the
E-3/H-1B1 implementing regulations. One author flag is now **closable**: `Matter of Dhanasar`'s own text
decodes fine and its three prongs are confirmed in the opinion.

**Blocker.** None. No claim in scope was unreachable in the sense of the standard.

**Next unit hint.** Verify the *other two* files UCAP1 flagged as never-independent
(`strategy/PAPER_CANDIDATES_SUPPLEMENT.md`, `strategy/PUBLICATION_STRATEGY.md`) once their current
editing settles — and re-run the `3,590` check across `docs/research/FINDINGS_REGISTER.md` and any
downstream document that inherited it. The `(h)(8)(iii)(F)(4)` route memo's advice is unchanged by C1, so
no route-sequencing work needs redoing.
