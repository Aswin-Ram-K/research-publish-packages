# UH3 — clear the three residues UFIX2 recorded

**Unit:** UH3 · **Date:** 2026-10-15 · **Workspace:** `/home/zer0null/reserach extarctor`
**Target:** `/home/zer0null/Duval` — **never opened** (no read, no write, no git).

## Purpose (one)

Make `strategy/` internally consistent by closing the three residues UFIX2 recorded but did not fix.
Citation/ledger hygiene only.

## Hard bound

**30 tool calls maximum.** Used **25**. No process started; no `git` run.

## Declared write paths

`strategy/PAPER_CANDIDATES_SUPPLEMENT.md`, `strategy/README.md`,
`orchestration/units/UH3.md`, `orchestration/handoffs/UH3.json`.

## Task 1 — stale provenance line (supplement) — DONE

The line was **L16**, not the L26 UFIX2's card and handoff recorded (measured:
`grep -n "710" strategy/PAPER_CANDIDATES_SUPPLEMENT.md` → L4, L16). The sentence formerly read
*"**Companion:** `PAPER_CANDIDATES.md` (UP1, 710 lines)"*. It now states which version was **surveyed**
— *"UP2 surveyed the **pre-revision 710-line** version (UP1's); unit UCORR1 revised that companion to
**970 lines** on 2026-10-14 and UFIX2 re-anchored this supplement's citations against the 970-line
version on 2026-10-15"* — with the marker `(count corrected by UH3, 2026-10-15; the sentence formerly
read "(UP1, 710 lines)")`. Measured current count: `wc -l strategy/PAPER_CANDIDATES.md` → **970**. The
surveys-version/current-version distinction UFIX2's errata header protects is preserved.

## Task 2 — mis-attributed candidate (supplement L227) — DONE

**Target verified before writing.** `sed -n '576p' strategy/PAPER_CANDIDATES.md` is
`[docs/research/SM_PILOT_RESULTS.md]` inside B8's *Evidence base* — the SM-pilot citation.
`sed -n '394,432p' strategy/PAPER_CANDIDATES.md | grep -n "SM\|PILOT"` → **no match**: B6 cites no SM
file. UCORR1's own note at `:598–599` records the same. L227's *"*results* candidate #6 cites"* is now
*"*results* candidate **#8 (B8)** cites — `docs/research/SM_PILOT_RESULTS.md`, cited in
`PAPER_CANDIDATES.md` at **`:576`**"*, with marker `(attribution corrected by UH3, 2026-10-15: … The
finding itself is unchanged — only the candidate carrying it.)`. UP2's substance, numbers and
quotations in that row are untouched; the unrelated `candidate #6` at L112 (D-085…D-090 substrate) was
**not** changed.

## Task 3 — README §6 under-reported closure — DONE

§6 was retitled *"Defect ledger — what is closed, and what remains open"* and rewritten:

- **Closed by UFIX2 (2026-10-15),** each traced to `orchestration/handoffs/UFIX2.json`: (1) the JOSS date
  residue at `PUBLICATION_STRATEGY.md` L24/L209/L292; (2) the supplement's pre-UCORR1 anchors (16
  re-anchored, one stated in place).
- **Closed by UH3 (2026-10-15):** (3) the stale companion line count; (4) the mis-attributed candidate.
- **Still open:** (5) `PAPER_CANDIDATES_SUPPLEMENT.md` remains **not independently verified** — §1 row 2
  now says so explicitly and that UFIX2/UH3 are citation hygiene, not verification;
  (6) `PAPER_CANDIDATES.md` and `VISA_US_ROUTES.md` are **under independent verification by UVER2**
  (report to land at `strategy/VERIFICATION_REPORT_2.md`), **status unchanged until it lands —
  author-checked / author-verified only**.

The superseded heading (*"Known defects recorded, not fixed (for a separate unit)"*) and the two OPEN
items are named in the new text, not silently deleted (append-only norm). §1's *Verified?* cells for
`PAPER_CANDIDATES.md` and `VISA_US_ROUTES.md` carry the UVER2-in-progress note; no status was upgraded.

**UVER2 check (before writing):** `find . -name "*VERIFICATION_REPORT_2*"` → nothing;
`grep -rn "UVER2" .` → **no hits anywhere**; `orchestration/units/` has no UVER2 card and
`orchestration/handoffs/` has no UVER2 handoff (latest: UFIX2). The README therefore says
**in progress** and records that no UVER2 artifact was on disk at this check — it does not cite a
report that does not exist.

## New inconsistency found (recorded, not silently absorbed)

UFIX2's card (L59) and handoff (`other_inconsistencies` item 1) both place the stale companion line at
**L26**; it is at **L16** — L26 is §0.1's heading. The line is fixed; the offset is recorded here so the
next unit does not re-derive it.

## Evidence commands

```
wc -l strategy/PAPER_CANDIDATES.md strategy/PAPER_CANDIDATES_SUPPLEMENT.md strategy/README.md
        # 970, 316, 131 (supplement unchanged at 316 — in-line edits; README 102 -> 131)
grep -n "710" strategy/PAPER_CANDIDATES_SUPPLEMENT.md      # L4 (errata header), L16 (companion, fixed)
sed -n '227p' strategy/PAPER_CANDIDATES_SUPPLEMENT.md      # "#8 (B8)" + ":576" + UH3 marker
sed -n '576p' strategy/PAPER_CANDIDATES.md                 # SM_PILOT_RESULTS.md in B8 — verified
sed -n '394,432p' strategy/PAPER_CANDIDATES.md | grep -n "SM\|PILOT"   # no match — B6 cites no SM file
grep -n "Defect ledger\|in progress\|VERIFICATION_REPORT_2" strategy/README.md
find . -name "*VERIFICATION_REPORT_2*"                     # nothing — UVER2 in progress
grep -rn "UVER2" .                                          # no hits before this unit's edits
```

## Next

The real gap is unchanged: `PAPER_CANDIDATES_SUPPLEMENT.md` has still never had an independent
verifier, and `PAPER_CANDIDATES.md` / `VISA_US_ROUTES.md` are only *waiting* on UVER2. When
`strategy/VERIFICATION_REPORT_2.md` lands, a unit should update §1 and §6 item 6 from "in progress" to
its verdict.
