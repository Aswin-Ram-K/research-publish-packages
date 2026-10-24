# UCONS2 — consolidate the six job sweeps into one master shortlist

**Status:** done (artifacts on disk) · **Card reconstructed by UFINAL2 on 2026-10-15.**

> **⚠️ This card was NOT written by UCONS2.** UCONS2 produced both artifacts, then died while
> self-verifying its numbers — its last recorded line was *"Now verifying every number and claim asserted in
> the report against the JSONL."* No card and no handoff were ever written. This file and
> `orchestration/handoffs/UCONS2.json` were reconstructed by unit **UFINAL2** from the artifacts on disk and
> from a full re-derivation against the seven source `JOBS.jsonl` files. Nothing here is UCONS2's own
> self-report; every figure was computed by UFINAL2. UCONS2's prose in `jobs/MASTER_SHORTLIST.md` is
> unchanged; corrections live in the dated `VERIFICATION` note at the top of that file.

## Purpose

Merge the six completed job sweeps into a single ranked, de-duplicated answer file — one row per opening —
carrying every source field verbatim plus consolidation fields (`source_units`, `dedupe_key`, `rank`,
`rank_reason`, `route_class`, `blockers`, `action`, `no_phd*`, `merge_note`) — and write an operator-facing
report over it. No searching, no invention: merge existing verified data only.

## Declared write paths

- `jobs/MASTER_SHORTLIST.md`
- `jobs/MASTER_SHORTLIST.jsonl`

## What UCONS2 actually produced

| file | size |
|---|---|
| `jobs/MASTER_SHORTLIST.md` | 312 lines (report, sections 1–10) |
| `jobs/MASTER_SHORTLIST.jsonl` | 284 rows, one per opening |

Inputs read: 295 rows from the six declared sweeps (`agent-runtime-global` 49, `evals-safety-foundations` 53,
`india-ai` 27, `scandinavia-europe` 10, `us-national-labs` 75, `us-nonprofit-research` 81) plus 8 rows from
`jobs/coverage-repair/` = **303 rows read**.

## Result (re-derived by UFINAL2, not copied from the report)

| figure | re-derived |
|---|---|
| rows read in | **303** (295 six declared sweeps + 8 coverage-repair) |
| duplicates merged | **19** (Σ k−1 over the 16 `merge_note` rows; 303−19=284 and 295−19=276) |
| rows out | **284** — 276 from the six sweeps + 8 coverage-repair |
| `apply_now` / `apply_later` / `watch` / `exclude` | 10 / 62 / 117 / 95 |
| `route_class` | cap_exempt_us 168 (105 open) · o1_suitable 51 · eu_researcher_permit 21 · india 30 · cap_subject_fallback 14 |
| cap-exempt US, open | **105** |
| no-PhD required (all rows / open non-funding role rows) | **26 / 13** |
| individual funding an individual may apply for | **13** (of 30 funding rows; 8 from JOB4/`evals-safety-foundations`) |
| deadlines with an explicit year inside 60 days | **3** |

## Verification (UFINAL2, same day)

Counts, de-duplication, referential integrity, the §4 deadline table, both §6 integrity catches and the §9
coverage-repair rows were all re-derived. Verbatim records and the corrections are in the **VERIFICATION**
note at the top of `jobs/MASTER_SHORTLIST.md`. Headlines:

- All headline counts match except the details listed below; all 10 Top-10 URLs and all 5 ranks-11–15 URLs
  exist in the JSONL; `rank` is a unique 1…284; every `url` is well-formed http(s); no row's `action`
  disagrees with its `status` without a recorded blocker.
- **One bad merge (rank 216):** three genuinely different UK AISI grant programmes sharing one URL — The
  Challenge Fund (£200k), The Alignment Project (£1m) and Systemic AI Safety Grants — were collapsed into a
  single Challenge-Fund row. §8 of the report claims these were *deliberately not merged*; they were. The other
  17 merges are genuine duplicates (verified same org + same normalised role + same normalised URL).
- **Section count errors:** `no_relevant_role` is **13**, not 14; the §8 merge-composition table
  (12/2/4/1) should read **7/2/8/2 = 19**; ANRF holds **6** rows on two URLs, not 5 on one; the six
  coverage-repair NREL rows sit at ranks **23, 24, 32, 64, 65, 83**, not all "between 20 and 30".
- The brief's own template figures `rows_in=295` / `duplicates_merged=11` do not both hold: 295 is right only
  for the six declared sweeps, and the merge count is 19 on either accounting.

## §9 coverage-repair — carried out as UCONS2 described (confirmed)

UCONS2's decision was to include the 8 undeclared `coverage-repair` rows but report the count both ways and
never present them as coming from a unit that reported success. Confirmed on disk: 8 rows, all tagged
`source_unit:"coverage-repair"`, all well-formed, 7 open NREL/NLR openings via the correct Workday slug
`nrel.wd5` + 1 honest `unreachable` INL row; rank 6 of the Top 10 is one of them; the report states 284 total /
276 from the six declared sweeps and names the disagreement in §9 and §7.

## Hard bound and outcome

UCONS2 stopped at the verification step — no bound exhaustion is visible in the artifacts. The deliverables
are complete and consistent with the source data apart from the errata above; the missing record (this card
and the handoff) is the only part UFINAL2 supplied.
