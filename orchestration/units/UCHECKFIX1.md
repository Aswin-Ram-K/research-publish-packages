# UCHECKFIX1 — refresh a stale row in the publication checklist

**Status:** done — 7 of 8 tool calls used.

## Outcome
`strategy/PUBLICATION_CHECKLIST.md`: 12 same-class stale lines corrected in place, each carrying a dated
`Superseded 2026-10-19:` history note; old wording retained. `papers/**` untouched; the companion-DOI
sentence in row 245 was preserved because it is intentional and correct.

## Sweep verdicts
- stale → corrected: lines 12, 13, 245, 246, 247, 248, 257, 258, 259, 260, 275, 301.
- correct: line 233/234 (encoder DOI + back-fill), line 267 (historical use of "superseded").
- stale but OUT OF SCOPE (inventory digests/sizes, not the deposit class, not measured for hashes):
  line 236 `tmlr/main.pdf` 176,971 → disk 177,298 B; line 244 replay release 107,641 → 107,764 B;
  line 256 gated release 128,559 → 128,902 B; §2 sizes for replay/gated preprints zips
  (11,379 → 11,526 B; 14,094 → 15,296 B).
- No row claimed any of the six upload artifacts missing: all six verified present in `submission-kit/`.
- No cross-citation error: `23463944` is only ever attributed to the encoder / companion note.

## Purpose
One row of `strategy/PUBLICATION_CHECKLIST.md` is stale and would mislead the author. Bring it current
and record the true state. Additionally sweep the same file for the same class of staleness and for
claims that any of the six submission-kit upload artifacts are missing/unbuilt.

## Bound
**8 tool calls total.** Stop and report `partial` when the bound is reached.

## Write paths (nothing outside these)
- `strategy/PUBLICATION_CHECKLIST.md`
- `orchestration/units/UCHECKFIX1.md`
- `orchestration/handoffs/UCHECKFIX1.json`
- `scratch/ucheckfix1/**`

## Verified facts supplied by the orchestrator (re-verified on disk here)
- replay: concept DOI `10.5281/zenodo.23482511`, latest v2 = record `23483304`,
  `papers/replay-record-not-decision/released/replay-record-not-decision-released.tar.gz`
  107,764 B md5 `41afa2831ff2f43af91d9c4416d8f658` — PUBLISHED.
- gated: concept DOI `10.5281/zenodo.23483314`, latest v2 = `23485733`,
  archive 128,902 B md5 `a7e81bf7c8ebe49da83e869a002be1b2` — PUBLISHED.
- All six upload artifacts exist in `submission-kit/` (3 preprints zips + 3 TMLR PDFs).

## Do NOT change
- `papers/**` — read-only for this unit. In particular replay's deliberate citation of
  `10.5281/zenodo.23463944` (stimulus fixtures release with the companion/encoder note) is INTENTIONAL
  and CORRECT; it is not a cross-citation error and must not be flagged or "fixed".
- `/home/zer0null/Duval` — READ-ONLY target, untouched.

## Method
1. Read the row and its table header/column semantics.
2. Correct in place to true state; keep old wording visible as dated history using this file's own
   existing convention (e.g. `Superseded <date>:`); if none exists, a dated inline parenthetical.
3. Sweep same file for: rows claiming a deposit is missing; `10.5281/zenodo.23463944` cited as the
   deposit for replay/gated; claims that any of the six upload artifacts are missing/unbuilt.
4. Report every hit with verdict: stale / correct / historical.
