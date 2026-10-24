# UCONS3 — re-split the rank-216 mis-merge and sweep for the same defect

**Status:** done · **Date:** 2026-10-15 · **Hard bound:** 40 tool calls (used 33).

## One purpose

Restore, **in a new pass and not by editing the bad merge in place**, the two UK AISI programmes that
`jobs/MASTER_SHORTLIST.jsonl` rank 216 lost; correct §8's false "deliberately NOT merged" claim with append-only
errata; sweep for further shared-URL collapses; and make the report's totals consistent.

## Declared write paths (nothing else was touched)

`jobs/MASTER_SHORTLIST.jsonl`, `jobs/MASTER_SHORTLIST.md`, `orchestration/units/UCONS3.md`,
`orchestration/handoffs/UCONS3.json`.

## Inherited evidence

UFINAL2's report (`orchestration/handoffs/UFINAL2.json`, `orchestration/units/UFINAL2.md`) and the VERIFICATION
note at the top of `jobs/MASTER_SHORTLIST.md`: one bad merge, rank 216, three distinct AISI programmes sharing
`https://www.aisi.gov.uk/grants`.

## Step 1 — re-verified from the source (independently, not from the report)

Read `jobs/evals-safety-foundations/JOBS.jsonl` (53 rows). Indices **[22]**, **[23]**, **[24]** are three
genuinely distinct programmes with one shared URL, exactly as claimed:

| idx | title | `amount_or_duration` | `status` | `individuals_may_apply` | `phd_or_affiliation_required` |
|---|---|---|---|---|---|
| 22 | The Challenge Fund (AI safety research grants) | up to £200,000 per project | closed | no | yes |
| 23 | The Alignment Project (grants programme) | up to £1 million per project | closed | no | yes |
| 24 | Systemic AI Safety Grants Programme | amount not stated; first 20 projects selected | closed | no | yes |

The loser rows exist in the source and are **closed and institution-gated**; that status was carried across
verbatim, not upgraded.

## Step 2 — re-split rank 216 into three rows

`jobs/MASTER_SHORTLIST.jsonl` is now **286 rows**. Ranks `216`, `216.1`, `216.2`, in that file order. Rows
216.1/216.2 are copies of the 216 row with every field overwritten from their own source row: `role`/`title`,
`status`, `entry_type`, `observed`, `amount_or_duration`, `phd_or_affiliation_required`, `individuals_may_apply`,
`deadline`, `requirements`, `fit_1_5`, `why`, `http_status`, `source_unit`/`source_units`, `route_class`
(`o1_suitable`, as for all funding rows), `blockers` (`posting_closed`, `phd_required`), `no_phd*` (false/empty),
`action` (`exclude`), plus a `dedupe_key` and a new `rank_reason` naming the source index. **Nothing was
invented** — a field-by-field diff against the source row is asserted in the fix script. The surviving 216 row's
`merge_note` (which claimed "merged 3 rows") was cleared, since it is no longer a merged row; only its
`rank_reason` changed otherwise.

## Step 3 — sweep for the same defect elsewhere (the valuable half)

Every source `JOBS.jsonl` was re-grouped twice — by normalised **URL** alone and by **normalised org + URL** —
and every group with more than one source row was re-judged against its master rows.

**Result: 0 further collapses of genuinely different programmes.** The multi-row groups are:

| group | source rows | master rows | verdict |
|---|---|---|---|
| AISI `aisi.gov.uk/grants` | 3 distinct titles | 1 → **3** | **the defect — fixed** |
| ANRF `awards_fellowship` | 4 distinct programmes | 4 | not collapsed (correct) |
| ANRF `research_grants` | 2 distinct programmes | 2 | not collapsed (correct) |
| METR (4 URLs) / Apollo | 2–3 each, same title | 1 each | true duplicates across units |
| Redwood; Coefficient Giving | 2 | 1 each | true duplicates (title annotation / org spelling) |
| MITRE; EleutherAI | 2 | 1 each | one gap recorded by two units |
| us-national-labs (ANL, INL, NREL, Aerospace, Battelle) | 2 each | 1 each | self-duplicates |

**Why the rule fired once.** `evals-safety-foundations` and `india-ai` are the only two sweeps whose rows carry
`title` and **no `role` field**; the merge key (`org | normalised-role | normalised-URL`) therefore saw an empty
role for them. But it did **not** collapse the four ANRF rows on one URL in the very same title-schema unit, so
the rule was applied inconsistently rather than uniformly — the inconsistency UFINAL2 named. Net: **the defect
is not systemic in effect** (one bad merge), though the rule that produced it is unreliable. No second lost
programme was found.

## Step 4 — §8 corrected by append-only errata

A dated `ERRATA — UCONS3` block was inserted into the VERIFICATION area at the top of
`jobs/MASTER_SHORTLIST.md` (ERRATA A fix + rank technique, ERRATA B counts before→after, ERRATA C sweep), and a
`UCONS3 correction` note was placed directly under §8's "Deliberately NOT merged" paragraph stating that the
AISI clause **was false when written** and that the rows are now restored — the sentence is marked, not quietly
deleted. A further marker sits under the §8 rule-count table. UCONS2's and UFINAL2's prose is otherwise intact.

## Step 5 — counts (before → after; current in bold)

| figure | before | after (current) |
|---|---|---|
| rows out | 284 | **286** |
| six-declared-sweep rows | 276 | **278** |
| coverage-repair rows | 8 | **8** (unchanged, filter intact) |
| duplicates merged | 19 | **17** (303−17=286, 295−17=278) |
| funding rows (§5) | 30 | **32** |
| §8 merge composition | 7/2/8/2=19 | **7/2/8/0=17** |

Updated inline: the operative header table, the "Answer file" line, §5's funding-row denominator, §7's
"58 of …", §8's merge total + rule table, and §9's dual count and filter yield. The `284`/`276`/`19` figures
inside UFINAL2's own note are left as written and explicitly labelled pre-fix in ERRATA B.

## Step 6 — rank semantics preserved

No row was re-ranked, reordered or re-merged. The two restored rows take **decimal sibling ranks `216.1` and
`216.2`** — the slot-preserving technique UCORR1 used for `NC1` at rank `6½`. `rank` remains unique and sorted
(JSON numbers), every pre-existing integer rank 1…284 is still valid, and cross-references in the report do not
break.

## Step 7 — coverage-repair rows intact

The 8 rows tagged `source_unit:"coverage-repair"` are unchanged; the dual reporting is now **286 total / 278
six-sweep-only**, and the filter instruction `source_units != ["coverage-repair"]` still yields the six-sweep
view (278).

## Verification commands (all re-run at the end)

- Parse all 286 lines; `rank` unique and sorted; count 286 / 278 / 8.
- Field-by-field diff of ranks 216.1/216.2 against `evals-safety-foundations/JOBS.jsonl` [23],[24] — all shared
  fields equal.
- URL-level and org+URL-level regroup over all seven source `JOBS.jsonl` files — one bad collapse, fixed.
- Report grep for stale operative figures (remaining `284`/`276`/`19` are inside the pre-fix UFINAL2 note).

## Outcome

The two lost programmes are restored with their source fields and their closed, institution-gated status; the
false §8 claim is corrected in place with errata; the sweep found no second instance. No file outside the four
declared write paths was touched.
