# UFIX2 — clear the two residues UCAP1 recorded (JOSS date; supplement citations)

**Unit:** UFIX2 · **Date:** 2026-10-15 · **Workspace:** `/home/zer0null/reserach extarctor`
**Target:** `/home/zer0null/Duval` — **never opened** (no read, no write, no git).

## Purpose (one)

Make `strategy/` internally consistent: carry L185's JOSS qualification to the three residues, and
re-resolve the supplement's pre-UCORR1 citations. Citation hygiene only.

## Hard bound

**35 tool calls maximum.** Used **25**. No process started; no `git` run.

## Declared write paths

`strategy/PUBLICATION_STRATEGY.md`, `strategy/PAPER_CANDIDATES_SUPPLEMENT.md`,
`orchestration/units/UFIX2.md`, `orchestration/handoffs/UFIX2.json`.

## Task 1 — JOSS date residue (3/3)

L185 (UCAP1) reads `2027-03-29` + *"only if the repository has been publicly available since
2026-09-28 — a premise that is itself `UNVERIFIED` (§11.10)"*. The unqualified `≈2027-03-28` at
**L24, L209, L292** is replaced with the same qualification and the marker
`[corrected by UFIX2 per UCAP1/UVER1]`, per the append-only-errata norm. Each sentence's surrounding
point is intact; L185 is unaltered. `grep -rn '2027-03-28' strategy/` now returns **only**
`VERIFICATION_REPORT.md` (UVER1's historical finding) and `README.md` §6 (the defect record) — no
occurrence in `PUBLICATION_STRATEGY.md`. File stayed **408 lines**.

## Task 2 — supplement citations + errata header

UCORR1 grew `PAPER_CANDIDATES.md` **710 → 970 lines**. Every `PAPER_CANDIDATES.md:<line>` citation in
the supplement was re-resolved against the current file; each new anchor was **read at the line
cited** before being written, and no number was shifted by a constant offset.

| Where | Was | Now (verified) |
|---|---|---|
| §0.3 / §7 row 7 method paragraph | `:9–11` | `:43–45` |
| §1.1 A1 gap 2 | `:88–90` | `:153–155` |
| §1.3 framing advice | `:104–106` | `:194` |
| §2.3 / §7 row 1 A1 thesis | `:62–64` | `:110–114` (+ superseded wording at `:115–120`) |
| §3.2 §D M1–M14 note | `~614–618` | `:834–842` (+ superseding UCORR1 correction at `:844–856`) |
| §3.3 LEARNINGS citation | `:73` | `:129` (`M1–M7`) and `:835–836` (`M1–M14`) |
| §7 row 2 A1 evidence base | `:66–80` | `:123–146` |
| §7 row 3 A2 | `:107–147` | `:198–243` |
| §7 row 4 §D | `:583–620` | `:793–856` (quoted sentence `:796–797`) |
| §7 row 5 A1 | `:59–106` | `:105–194` |
| §7 row 5 #6 | `:295–336` | **no counterpart** — B6 (`:394–432`) cites no SM file; said in place |
| §7 row 5 results file | `:393` | `:576` (B8), with UCORR1's note at `:590–599` |
| §7 row 6 #9 | `:429–476` | `:622–683` |

16 citations re-anchored; 1 genuinely unresolvable and stated in place rather than deleted. A dated
append-only **ERRATA HEADER** (UFIX2, 2026-10-15) now sits at the top of the supplement, matching
UCORR1's style at `PAPER_CANDIDATES.md:3–8`, and records that UP2's findings, numbers, verdicts and
quotations were **not** altered. File 305 → **316 lines**.

## Other inconsistencies found (recorded, NOT fixed — outside declaration)

1. Supplement (now L26): *"Companion: `PAPER_CANDIDATES.md` (UP1, 710 lines)"* — stale line count.
   The errata header carries the 710 → 970 change; the sentence itself is left as UP2 wrote it.
2. Supplement (now L227): *"the SM pilot whose results candidate #6 cites"* — rank-6 **B6** cites no
   SM file; `SM_PILOT_RESULTS.md` is cited in **B8** (`:576`). A mapping error UP2 made, not a
   notation shift; not silently rewritten.
3. `strategy/README.md:96` still lists the L24/L209/L292 residue **and** the supplement's stale
   anchors as open defects. Both are now closed, so README §6 is stale — but README is not in this
   unit's write paths, so it is recorded here, not edited.

## Evidence commands

```
grep -rn '2027-03-28' strategy/          # PUBLICATION_STRATEGY.md: none (was L24/L209/L292)
grep -n '2027-03-29' strategy/PUBLICATION_STRATEGY.md   # L24, L185, L209, L292
sed -n '1,14p' strategy/PAPER_CANDIDATES_SUPPLEMENT.md  # new ERRATA HEADER
sed -n '297,303p' strategy/PAPER_CANDIDATES_SUPPLEMENT.md  # re-anchored §7 table
wc -l strategy/PUBLICATION_STRATEGY.md strategy/PAPER_CANDIDATES_SUPPLEMENT.md  # 408, 316
```

## Next

The real gap is unchanged: `VISA_US_ROUTES.md`, `PAPER_CANDIDATES.md` and
`PAPER_CANDIDATES_SUPPLEMENT.md` have never had an **independent** verifier. Also refresh
`strategy/README.md` §6 once the two residues above are acknowledged.
