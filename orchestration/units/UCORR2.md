# UCORR2 — apply UVER2's corrections to two strategy documents

**Unit:** UCORR2 · **Date:** 2026-10-15 · **Bound:** 45 tool calls (used 44) · **Status:** done
**Work order:** `strategy/VERIFICATION_REPORT_2.md` (UVER2, independent verifier, 144 lines —
`pass-with-corrections` for both documents; 2 contradicted, 3 overstated, 1 not_reproduced, 1 upgrade).
**Target:** `/home/zer0null/Duval` — read-only; read only, never written.

**Write paths:** `strategy/VISA_US_ROUTES.md`, `strategy/PAPER_CANDIDATES.md`, `strategy/README.md`,
`orchestration/units/UCORR2.md`, `orchestration/handoffs/UCORR2.json`. Nothing else touched.

## What I re-confirmed myself before editing

- **C1 (chapter attribution).** Live-fetched both chapters 2026-10-15:
  `6 USCIS-PM F.2` → `repositories` **0×**, `interested government agency` **0×**;
  `2 USCIS-PM M.4` → `repositories` **1×**, `interested government agency` **3×**. Extracted M.4's
  criterion-5 list and read the passage verbatim: *"Contributions to repositories of software, data,
  designs, protocols, or other technical resources…; and A letter or other documentation from an
  interested government agency, including a quasi-governmental entity…"*. C1 is real.
- **C2 (transposed digit).** Re-derived by **parsing**, not `wc -l`:
  `docs/research/EXP#11-evidence/imajev-rows.jsonl` → **3,690** valid JSON rows, 0 invalid;
  `decider-rows.jsonl` → **4,090**; `imajev-progress.json` final `rowsOnDisk` = **3,690**. C2 is real.
- **Overstated 1.** INA 214(g)(8)(B)(ii) makes 1,400 Chile + 5,400 Singapore = 6,800; E-3 = 10,500.
  Values correct → narrowed the flag rather than deleting the claim.
- **A26.** INA 214(g)(5)(C) is a 20,000 numeric exemption with no per-country element → one-line fix.
- **Upgrade.** *Matter of Dhanasar* text is decodable (UVER2, `pdftotext`) → flag closed, not a repair.

## Changes applied (append-only; every change marked `[corrected/closed/narrowed by UCORR2 per UVER2]`)

### `strategy/VISA_US_ROUTES.md` (11 edits; **line count held at 785** so cross-file anchors do not drift)
- **C1** — `:348` attribution changed to **2 USCIS-PM M.4, criterion 5 (O-1A)** with the measurement and an
  explicit "the O-1A recommendation is unchanged — only the citation is corrected"; `:362` now states the
  example is **absent from F.2**; `:551` (§6.1 F.2 row) drops the misattributed quote; `:609` attributes the
  Manual's repository language to O-1A criterion (5), not EB-1A criterion 5.
- **Overstated 1** — §13.12 narrowed to the **implementing regulations** (`:768`); quota figures now
  **verified** as additive evidence. §5.3 (`:512`) and §5.5 (`:528`) narrowed to match.
- **Overstated 2** — §2.2 `:87`: "(C) would not help them even if they had one" loosened (separate 20,000
  pool acknowledged; the point kept).
- **Overstated 3** — §1 `:40` O-1A row now carries the `UNVERIFIED` flag (presentation only). H-1B1/E-3
  figures at `:45`/`:47` left as fact — they are correct.
- **A26** — §4.3 `:433–434`: "(C) has no per-country element".
- **Upgrade** — §13.6 `:752–755` and the §6.1 Dhanasar row `:549` closed, with UVER2's evidence.

### `strategy/PAPER_CANDIDATES.md` (2 edits; **line count held at 970**)
- **C2** — `:305`: **3,590 → 3,690**, marked, with the re-derivation recorded inline.
- Errata header `:33–35` — the "independently verified exact" claim is superseded **on that one number
  only**, in place (no new lines, to protect the supplement's and UVER2's `:NNN` anchors).
- Every other protected statistic is untouched: 4,090 / 0.6700 / 0.0156 / 244/244 / 4.167e−09 / 51.6 % /
  3,628 / 9,260.

### `strategy/README.md`
- §1 rows for both files: **`pass-with-corrections`**, citing `VERIFICATION_REPORT_2.md`.
- §1 asymmetry: **four of seven** files now independently verified; `PAPER_CANDIDATES_SUPPLEMENT.md` and
  `SOCIAL_PRESENCE.md` still have not.
- §6: the UVER2 "in progress" item **closed** with the new verdicts; three new open items added (below).

## MUST-DO — recorded, not fixed: an owed correction to the corpus of record

`/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47` (F-EXP11-11) still reads *"across all 4,090
decider rows and **3,590** imajev rows"*. I read the line and confirmed the stale figure is present
(mtime 2026-10-06 23:43:39 — **not modified**). Correct value **3,690** (evidence: `imajev-rows.jsonl`
parses to 3,690 valid rows; `imajev-progress.json` final `rowsOnDisk` = 3,690). **This is a finding for
the user; the target is strictly read-only to this workspace.** Recorded in README §6 item 7.

## Honest limitations recorded (README §6 items 7–8)
- The pre-revision `PAPER_CANDIDATES.md` citation census is **`not_reproduced`** — superseded in place,
  untracked, no backup. Not presented as verified.
- `PAPER_CANDIDATES_SUPPLEMENT.md` and `SOCIAL_PRESENCE.md` remain unverified by any independent unit.

## Containment
No writes outside the five declared paths. `/home/zer0null/Duval` read only (no `git`, no state change;
`FINDINGS_REGISTER.md` mtime unchanged). `VERIFICATION_REPORT_2.md`, `PAPER_CANDIDATES_SUPPLEMENT.md` and
`PUBLICATION_STRATEGY.md` untouched.
