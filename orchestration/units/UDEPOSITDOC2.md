# UDEPOSITDOC2 — close remaining deposit-documentation unknowns; make one file authoritative

**Status:** in progress
**Hard bound:** 25 tool calls. If Preprints.org taxonomy cannot be fetched from a primary source, STOP that sub-job and report unresolved — do not invent a category.
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a

## Purpose
1. Resolve four UNKNOWNs from primary sources (verbatim quote + URL each; NOT VERIFIED if unreachable):
   - Preprints.org subject-area taxonomy + this paper's category
   - Zenodo resource types — exact list, and whether >1 type may be carried
   - Identifier shapes: Zenodo DOI (`10.5281/zenodo.<id>`) and Preprints.org DOI
   - Preprints.org requirements: accepted file formats, LaTeX source alongside PDF, screening/turnaround, licence options (author wants CC BY 4.0)
2. Make one file authoritative — resolve the six divergences between `strategy/ZENODO_DEPOSIT.md` and `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` (which file is the deposit; resource type Dataset vs Software; version v1 vs blank; two keyword lists; two descriptions). Superseded wording marked superseded with a date, not deleted.
3. Confirm ordering hazard: DOI pasted into identified `main.tex` after anonymous variant built → runbook must say anonymous TMLR variant is rebuilt from final identified source after DOI paste and must NOT contain the DOI. Do NOT rebuild the variant.
4. Update `strategy/DEPOSIT_METADATA.md` to carry the single agreed set + authority statement at top.

## Search tooling
Local endpoint `http://127.0.0.1:8080/search?q=<query>&format=json`; `local_web_crawl` for full pages. (built-in web_search unavailable — API key unset)

## Write paths (nothing else)
`strategy/DEPOSIT_METADATA.md`, `strategy/SUBMISSION_RUNBOOK.md`, `strategy/ZENODO_DEPOSIT.md`, `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt`, `scratch/udepositdoc2/**`, `orchestration/units/UDEPOSITDOC2.md`, `orchestration/handoffs/UDEPOSITDOC2.json`

## Do NOT
Upload/submit/register/create account/contact anyone. No credentials/tokens/ORCID in any file. Do not modify `papers/**` or `scratch/uneutral10/package/**`.
