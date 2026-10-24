# UFINAL2 — verify UCONS2's consolidated shortlist and close its missing record

**Status:** done · **Date:** 2026-10-15 · **Hard bound:** 35 tool calls (used 17).

## One purpose

Verify UCONS2's shipped artifacts against their source data, and complete the record UCONS2 never wrote. This
unit did **not** re-consolidate, re-rank, re-merge or restructure the shortlist.

## Situation inherited

UCONS2 consolidated six job sweeps into `jobs/MASTER_SHORTLIST.md` (312 lines) and
`jobs/MASTER_SHORTLIST.jsonl` (284 rows), then **died while self-verifying its numbers, before writing its card
and handoff**. Its last recorded line: *"Now verifying every number and claim asserted in the report against
the JSONL."* That verification had never been done.

## Declared write paths

`jobs/MASTER_SHORTLIST.md` (dated VERIFICATION note only — append-only errata, UCONS2's prose untouched),
`orchestration/units/UCONS2.md`, `orchestration/handoffs/UCONS2.json`, `orchestration/units/UFINAL2.md`,
`orchestration/handoffs/UFINAL2.json`.

## What was checked, and how

Every figure was recomputed from `jobs/MASTER_SHORTLIST.jsonl` and the seven source `JOBS.jsonl` files
(295 rows in the six declared sweeps + 8 in `coverage-repair` = 303) with a Python re-derivation — no number
was copied from the report.

1. **Counts** — total, per `source_unit`/`source_units`, `route_class`, `action`, status, blockers; the
   284/276/8 split.
2. **De-duplication** — the 16 `merge_note` rows (Σ k−1 = 19), each merge group reconstructed by normalised URL
   against the source files and judged on organisation + normalised role + URL.
3. **Referential integrity** — Top-10 and ranks-11–15 URLs, `rank` uniqueness, URL well-formedness,
   `status` vs `action`.
4. **§4 deadline table** — each date traced to a source `deadline` field or a FINDINGS table.
5. **§6 integrity catches** — Wadhwani AI `none_found`; aggregator-only Anthropic listing absent.
6. **§9 coverage-repair rows** — presence, tagging, well-formedness, 7 open NREL/NLR + 1 INL `unreachable`.

## Results

**Verified as stated:** 284 rows out (276 six-sweep + 8 coverage-repair, reported both ways);
apply_now 10 / apply_later 62 / watch 117 / exclude 95; cap_exempt_us 105 open of 168; no-PhD 26 all / 13 open
role rows; 19 merges; individual funding 13 of 30 (8 from JOB4); 3 deadlines with an explicit year inside 60
days; all §4 dates traceable; 15/15 headline URLs present; 284/284 URLs well-formed; Wadhwani `none_found`
(0 open); all 4 Anthropic rows on the live Greenhouse board with the aggregator-only title absent;
`unreachable` 58 rows / 64 raw; coverage-repair handled exactly as §9 describes.

**Corrections recorded in the VERIFICATION note (no prose rewritten):**

- **One bad merge — the substantive find.** `rank 216` collapsed three genuinely different UK AISI grant
  programmes sharing one URL: *The Challenge Fund* (£200k), *The Alignment Project* (£1m) and *Systemic AI
  Safety Grants*. Report §8 claims these were deliberately not merged; they were. The two losing rows and
  their amounts are absent from the JSONL. All other 17 merges are genuine duplicates.
- `no_relevant_role` is **13**, not 14 (§6 and §7), which makes §6's breakdown sum to the correct 95 excludes.
- §8's merge-composition table (12/2/4/1) should read **7/2/8/2 = 19**.
- The six coverage-repair NREL rows sit at ranks **23, 24, 32, 64, 65, 83**, not "between 20 and 30".
- ANRF holds **6** rows on two URLs, not 5 on one (the "not merged" claim itself holds).
- The brief's own template figures `rows_in=295` / `duplicates_merged=11` do not both hold: 295 is the
  six-sweep-only count (303 in total) and the merge count is 19 on either accounting.

## Outcome

UCONS2's artifacts stand; its record is now closed. Its one decision-changing defect is a single over-reach in
the merge step, named above with its exact source rows. No file outside the five declared write paths was
touched.
