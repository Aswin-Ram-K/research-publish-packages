# URECORD1 — SUBMISSION_RECORD provenance record

Purpose: build `strategy/SUBMISSION_RECORD.md` — nine venue rows (3 papers x 3 venues), per-deposit versions
table from the live Zenodo API, linkage section, mandatory disclosure history, usage note.

Bound: 20 tool calls. Write paths: `strategy/SUBMISSION_RECORD.md`, `orchestration/units/URECORD1.md`,
`orchestration/handoffs/URECORD1.json`, `scratch/urecord1/**`.

Inputs given by the author: Preprints.org manuscripts 239326 / 239328 / 239329 (encoder corrected from 23932);
TMLR forum ids L9GcDGb2fr / U2WjJMH0EK / q72ZB9ZMqy. Zenodo concept DOIs and version ids verified live, not
taken from the card.

Work done:
1. Skeleton card + handoff written before any research (call 2).
2. Measured 9 artefacts (size, mtime, sha256) and md5 of the 3 `released/*.tar.gz` with stat/sha256sum/md5sum.
3. Queried `https://zenodo.org/api/records/<concept>/versions/latest` — needed `-L` (301 → HTTP 200). Recorded
   id, doi, conceptdoi, publication_date, created, language, resource_type.type, license.id, file key/size/md5.
   Local md5 matched the API md5 for all three archives.
4. Listed versions via `/api/records/<version>/versions` (the `/records/<concept>/versions` path 404s). E has 3
   versions (23463945 / 23464507 / 23482311 current), R 2 (23482512 / 23483304), G 2 (23483315 / 23485733).
5. Verified TMLR anonymisation: `\author{Anonymous authors}` at `papers/<slug>/tmlr/main.tex:18` in all three.
6. Verified "no paper text in the deposit": `tar -tzf` → 37/13/16 entries, 0 matching `*.tex|*.pdf|*.bib`.
7. Read authoritative disclosure wording: `strategy/WITHHELD.md:300–359` (§8.2–8.4, `:313–316`),
   `strategy/GATED_READ_DISCLOSURE.md:15–59` (withhold item 10, AD-1 at `:170`, AD-6 at `:175`).
8. Wrote `strategy/SUBMISSION_RECORD.md` (§1 nine rows, §2 versions, §3 linkage, §4 disclosure + standing rule, §5 usage).

Not verified (recorded, not invented): Preprints.org submission timestamps and DOIs (not minted); TMLR
submission timestamps (OpenReview API returned HTTP 403 from this host). Rows carry `pending` for those cells.

Status: done.
