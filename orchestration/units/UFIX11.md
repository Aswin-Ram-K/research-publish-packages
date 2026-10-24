# UFIX11 — apply UVER10's four corrections to `papers/gated-read-batching/`

**Status:** done · **Tool calls:** 14 of 30 · **Date:** 2026-10-15

## Purpose (one)
Apply the four factual corrections UVER10 returned against the #7 batching manuscript
(`strategy/VERIFICATION_REPORT_10.md`): no re-measurement, no claim withdrawn, no new sentences.

## Write paths
`papers/gated-read-batching/**`, `orchestration/units/UFIX11.md`, `orchestration/handoffs/UFIX11.json`.
Untouched: `repro/**` (UREDACT2), `strategy/**`, `/home/zer0null/Duval` (read-only target; not edited,
no `git` run there).

## Corrections applied — 4/4
1. **bs90 F1 truncation.** `0.210` → `0.211` at `MANUSCRIPT.md:9,135,137,158,174,215`;
   F1 spread `0.017` → `0.016` at `MANUSCRIPT.md:9,137,197`; the contribution bullet's budget-arithmetic
   F1 change `0.008` → `0.007` at `MANUSCRIPT.md:30` (forced by the same correction). `CLAIMS.md`
   rows C24 (`:58`), C25 (`:59`), C38 (`:77`) and `GAPS.md` G-08 (`:62`) updated to match.
2. **Reference 10's title.** Wrong title `…Taxonomy of 13 Coding-Agent Scaffolds` →
   `…Taxonomy of Coding Agent Architectures` at `MANUSCRIPT.md:234` and `REFS.md:50` (B9).
   The source still carries the wrong title at `GATED_READ_PROVENANCE.md:47` (it was carried, not invented) —
   **the source document was not edited** (outside write paths; it is a record).
   Note: the unit card said `GATED_READ_2026.md:47`; that is a slip — the wrong title occurs only at
   `GATED_READ_PROVENANCE.md:47`.
3. **Two wrong `CLAIMS.md` locators + the 73/73 claim.** `C48` numeral `p ≥ 0.219` is at
   `GATED_READ_2026.md:313`, not `:211-213`; `C65`'s second locator is at
   `GATED_READ_PROVENANCE.md:254-256`, not `:247-249`. Both replacements were **opened and confirmed
   by me** before editing (see `DISCLOSURE_CHANGES.md` §Correction 3). `CLAIMS.md:87` and `:109` repointed;
   the blanket "73/73 with a source locator" softened to "all 73 rows have a locator; **exact-line
   accuracy 71/73**" at `CLAIMS.md:131` and `MANUSCRIPT.md:127`.
4. **The "10×" prose.** `MANUSCRIPT.md:147` "ten times the completion tokens" → "8.9× …";
   `MANUSCRIPT.md:187` "the 10× completion-token blow-up" → "the 8.9× …"; `CLAIMS.md:68` (C34) claim
   column and `GAPS.md:16` updated. Arithmetic re-verified: 1,690,920 / 190,699 = 8.87× (= 8.9×);
   1,690,920 / 821,909 = 2.06× (= 2.1× at the source's own precision).

## Toolformer (ref 11) — resolved, no change
arXiv v1 abs (`https://arxiv.org/abs/2302.04761`) lists **8** authors (no Hambro); the NeurIPS 2023
proceedings page for the same paper lists **9**, including **Hambro**. The source's 9-author list
matches the published version ⇒ the citation is correct as written; left unchanged rather than
guessed at.

## Evidence
- `md5_before MANUSCRIPT.md f9118b2f9ada553d3c9df6e7b440e23f` → `md5_after 137d83c9c803c8d9a0aa99025927f063`
  (`CLAIMS.md` 374e5ce4…, `REFS.md` 7a3ac71b…, `GAPS.md` 0862ae00…).
- Word count `wc -w MANUSCRIPT.md` = **5213** (UVER10 measured 5193).
- Disclosure grep (`/home/zer0null`, `duval`, `Consonance`, `a5ef1b28`, `89003e70`, `publish-present-compete`,
  hex `[0-9a-f]{8,}`): **no new hit introduced** — hit counts identical before/after. `MANUSCRIPT.md` and
  `GAPS.md` are 0-hit. Pre-existing, unchanged: `CLAIMS.md:8` and `REFS.md:12` each name the read-only target
  root in their source-path preamble (present before this pass, not created by it) — flagged, not silently
  changed, since redaction is a packaging decision outside a correction pass.
- `papers/gated-read-batching/DISCLOSURE_CHANGES.md` carries every verbatim before/after line with file+line.

## Not done (deliberately)
No re-measurement, no re-derivation beyond the two arithmetic checks above, no restructuring, no claim
withdrawn, no change outside the four corrections (plus the two mechanically forced `0.008 → 0.007` and
C24/C25/C38/G-08 consistency updates).

## Pass 2 (UFIX11 follow-up) — package-wide disclosure sweep + neutralisation
Whole-directory sweep of `papers/gated-read-batching/`: **5 files scanned** — `CLAIMS.md`, `GAPS.md`,
`MANUSCRIPT.md`, `REFS.md`, `DISCLOSURE_CHANGES.md` (no `CHECKLIST.md`/`OPEN_QUESTIONS.md`/`REFERENCES.bib`/
`README*` exist in this package). Patterns: `/home/zer0null`, `/home/`, `/Users/`, `/mnt/`, `/opt/`,
`duval`/`consonance` (ci), `a5ef1b28`, `89003e70`, `publish-present-compete`, `Aswin-Ram-K`, `github.com/Aswin`,
`UVER`, `UPAPER`, `UFIX`, `StateClass`, `grantPolicy`, `expanded[`, `admit(`, hex `[0-9a-f]{8,}`.

Hits **60 → 52**, and all 52 remaining are inside `DISCLOSURE_CHANGES.md` (the audit log — left intact;
recommend excluding it from any shipped subset rather than scrubbing it, precedent
`repro/encoder-crossover-190-SANITISED/EXCLUDED.md`).

**4 sites fixed** (verbatim before/after in `DISCLOSURE_CHANGES.md` §Pass 2):
- `CLAIMS.md:8` — source-root path → "the root of the read-only source material (an external checkout; name and location withheld)"
- `REFS.md:12` — same convention: provenance fact kept, name withheld
- `REFS.md:17` — "by unit UPAPER7" → "for this manuscript" (internal unit id)
- `GAPS.md:16` — "the UFIX11 correction pass" → "a later correction pass"

**0 hits** remain outside the log for every pattern, including `Consonance`, `a5ef1b28`, `89003e70`,
`publish-present-compete`, `Aswin-Ram-K`, `github.com/Aswin`, `StateClass`, `grantPolicy`, `expanded[`, `admit(`,
`/Users/`, `/mnt/`, `/opt/`. `MANUSCRIPT.md` was and is 0-hit; no absolute path of any kind survives outside the log.

**Flagged, not guessed:** generic "unit"/"non-unit" process nouns (`CLAIMS.md:5`, `REFS.md:4`, `REFS.md:11`) and the
G/P/R/S source-document filenames, which are the citation targets themselves (removing them breaks every locator).

md5 after pass 2: `MANUSCRIPT.md` `137d83c9c803c8d9a0aa99025927f063` (unchanged), `CLAIMS.md`
`2392ccafd6f32a4c7039a373fdeb1a3b`, `REFS.md` `917a31f43f0e30e7d268cc94ca147916`, `GAPS.md`
`8e38d394a149685c0680215bd6079876`, `DISCLOSURE_CHANGES.md` `e36733146f54b07700c94e86b1bb4baf`.
`wc -w MANUSCRIPT.md` = **5213** (unchanged — pass 2 touched no manuscript prose). Target `/home/zer0null/Duval`
never written; no `git` run there.

## Pass 3 (UFIX11 follow-up) — internal process nouns removed
The three flagged (b) items — plus the same class wherever it appeared in the four shipped files: **12 sites**
(`CLAIMS.md:5,136`; `REFS.md:4,9,11,38,55,92`; `GAPS.md:135,175,179` ×2 — that row carried two). Every sentence
stays **true** after the change; none needed a unit name. Verbatim before/after per site is in
`DISCLOSURE_CHANGES.md` §Pass 3 / §3b / §3c (appended only — the log's own 52 hits and the G/P/R/S filenames were
left untouched by instruction).

- `CLAIMS.md:5` "recomputed by **this unit**" → "recomputed by **the authors of this manuscript**"; `CLAIMS.md:136` "…by this unit from the raw rows **R**" → "…by the authors from the raw rows **R**"
- `REFS.md:4` "re-verified by this unit in this session" → "re-verified by the authors of this manuscript during preparation"
- `REFS.md:9` "Verification date for this unit's own checks" → "…for the authors' own checks"
- `REFS.md:11` "**Source of all non-unit verification:**" → "**Source of the verification not performed by the authors:**" — the instruction's proposed "independent of the source material" would have **inverted** the line's meaning (it names where the verification the authors did *not* perform comes from), so the meaning-preserving wording was used
- `REFS.md:38,55` "This unit did not (independently) re-fetch them" → "The authors did not…"; `REFS.md:92` "Re-verified by this unit in this session (Tier A)" → "Re-verified for this manuscript…"
- `GAPS.md:135` "This unit did not perform that rename" → "The authors did not…"; `GAPS.md:175` "Gaps this unit hit in its own production process" → "Gaps the authors hit in producing this package"; `GAPS.md:179` "created by this unit" → "created by the authors" and "their framing is this unit's" → "…the authors'"

**20-pattern sweep: 0 hits** in all four shipped files. Residual bare word "unit": **5**, all legitimate or
ambiguous and deliberately left — `GAPS.md:11` ("the source is unit-sloppy": ambiguous, may name the source
project's producing unit), `GAPS.md:182` ("eight prose units"), `MANUSCRIPT.md:44` ("**unit of decision**"),
`MANUSCRIPT.md:50` ("*file-read* unit"), `MANUSCRIPT.md:201` ("the units are aligned").

md5 after pass 3: `CLAIMS.md` `83df6bfe1bfbc5f11330baff17e5ab4f`, `REFS.md`
`ba413fc3b97abed8421471cf655ae18a`, `GAPS.md` `71e4678472e30a120f0df5b1b5cf8cef`, `MANUSCRIPT.md`
`137d83c9c803c8d9a0aa99025927f063` (unchanged), `DISCLOSURE_CHANGES.md` `713e1a2abe0f7247bc4a190bea5466b2`.
`wc -w MANUSCRIPT.md` = **5213** (unchanged — pass 3 touched no manuscript prose).
