# UAGNOSTIC1 — code-agnostic release policy: identifier census, total substitution, placeholder harness, totality check

**Status:** done · **Bound:** 60 tool calls (used ~42) · **Parent:** `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`

## Purpose
Serve the author's release policy — **code-agnostic release, the way the large labs do it**: minimal for
validity, no identifier of the system under study survives in any form, random neutral tags, placeholder
harness architecture. This **supersedes** the "ship the sanitised subset and manage the residue" approach:
the residue question is replaced by a **totality check**.

## Deliverable
`strategy/CODE_AGNOSTIC_RELEASE_POLICY.md` (88,337 chars) with sections A–F:
- **A** identifier census (172 distinct identifiers, 53,395 occurrences, 49/58 files, per-category tables with counts + `path:line` + load-bearing class, 100 mechanism option labels, the five carriers, rationale measurement)
- **B** substitution map (`NEUTRAL-TAG/v1`: `K01/F01/S01/C01/R01/D01` + `TAG_NN`; three strata; the tokenisation-safety rules; the F-A/F-B fork)
- **C** placeholder harness architecture (`instrument/`, `host/`, `baselines/`, `runs/`, `verify/`, `paper/` + entry points)
- **D** runnable totality check (differential totality T1–T5, variant sweep, clean-room replay, red→green) and why the 24-pattern HARD list cannot do the job
- **E** paper consequences (`MANUSCRIPT.md:793/:258`, `:835–840`, typed-channel vs sealed-fixture)
- **F** UNVERIFIED (8 items)

## Headline counts
| measure | value |
|---|---|
| distinct project-specific identifiers | **172** |
| occurrences | **53,395** |
| files carrying ≥1 | **49** of 58 |
| rename-sensitive (in scored stimulus) | **33** |
| rename-safe (metadata only) | **90** |
| incidental (filenames/paths/pointers/denylist) | **49** |
| identifiers only inside `gate.sh` | **17** |
| denylist coverage | 31/172 → **81% invisible to the gate** |
| option labels | 215 distinct / **100 mechanism-naming** |

## Method
`scratch/uagnostic1/census1.py` (fixture extraction) → `census2.py` (676-token vocabulary sweep) →
`census3.py` (184-seed census over `.ucurate1/pre/research-publish-packages`, 172 present, writes
`census.tsv`) → `census4.py` (scored-stimulus vs metadata; option-label classification) → `census5.py`
(buckets) → `gen_report.py` (emits the document).

## Critical findings
1. **`gate.sh` ships the denylist and excludes itself from its own scan.** 17 identifiers occur only there; it
   names nine internal process documents, four mechanism symbols, `src/**` paths and target-repo identifiers.
2. **The leak is not the 62 lines of `REGEN_ASSESSMENT.md` §2.** It is 53,395 occurrences across 172
   identifiers, dominated by the metadata field class (~32,000 occurrences) that no pattern list names.
3. **`MANUSCRIPT.md:793`/`:258` cite a digest the package does not ship** (`076164ac…` = as-audited; shipped =
   `751dc007…`).
4. **F-A vs F-B is the decisive fork**: the option labels are simultaneously the model input and plain-English
   mechanism descriptions, so "no identifier…or prose" cannot coexist with preserving the numbers.
5. The shipped fixture's header (`reflex-decisions.ts:1–27`) is a live prose-pointer leak with seven
   `REDACTION_REPORT.md` references — the cheapest single win.

## Constraints honoured
No writes outside the four declared write paths. `/home/zer0null/Duval` untouched; no `git` run in the target;
`/home/zer0null/research-publish-packages` never written.
