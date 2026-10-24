# UPOSTCHK1 — record Preprints.org acceptance, re-check public posting

**Status:** done (bound exceeded: 14 calls vs 12 — 3 self-inflicted checker SyntaxError/KeyError runs)
**Purpose:** Record author-reported editorial acceptance of Preprints.org 239326 (E) and 239329 (G) in
`strategy/SUBMISSION_RECORD.md` rows 1 and 7; record 239328 (R) row 4 as not accepted / state unknown;
re-check whether anything posted. No paper, archive or PDF touched.

**Write paths used:** `strategy/SUBMISSION_RECORD.md`, `orchestration/units/UPOSTCHK1.md`,
`orchestration/handoffs/UPOSTCHK1.json`, `scratch/upostchk1/**`.

**Probes (2026-10-20, literal):**
- Crossref `api.crossref.org/prefixes/10.20944/works`, rows=20, select=DOI,title,created,prefix, by title
  (full titles, then short distinctive phrases with exact-title equality checked): HTTP 200 on all six
  requests; total-results 14 / 872 / 0 (full) and 337 / 872 / 72 (short); **exact-title matches = 0 for all three**.
- `https://www.preprints.org/manuscript/{239326,239328,239329}`: **HTTP 403 / 403 / 403** (no state inferred).

**Edits:** rows 1/4/7 status cells replaced (DOI cell still `pending`); filename/size/sha256 cells asserted
byte-identical post-edit (28,712 / 11,526 / 15,296 B); dated provenance note added under the table.

**Not verified:** whether anything actually posted (venue 403; Crossref lag 1–2 days); acceptance date beyond
the author's 2026-10-20 report; any DOI.
