# PROV-PIN-FIX

**Purpose.** Repair the prose and the pins on `papers/context-cache/MANUSCRIPT.md` after the PUB-PASS
insertion (225 lines) left three guards RED. No measured number changed.

**Bound.** 30 tool calls, bash <=12 (actual: 18 tool calls, 14 bash). Zero network / live requests / git.

## Failure set reproduced before any edit (exit 1, 3 failed)

1. `tests/test_g5_fanout_attribution.py::test_every_6744_site_names_cell_g5`
   `MANUSCRIPT.md:1110: 6.744 stated with no G5 provenance in the same site`
2. `tests/test_gap_closure_ledger.py::test_stale_citation_audit_is_accurate` — four findings:
   `G5: MANUSCRIPT.md:195 stale=False but expect '6.744' is not on the line`, `G5: MANUSCRIPT.md:865 found quote does not match`,
   `G5: MANUSCRIPT.md:865 stale=False but expect '258,035' ...`, `G7: MANUSCRIPT.md:865 ... '1.5017'`
3. `tests/test_paper_g3_bands.py::test_the_mean_band_is_never_presented_as_a_per_turn_bound[MANUSCRIPT.md]`
   `MANUSCRIPT.md:1112 [QUALIFIER] the mean band is stated without saying it is a range of averages`

## Diagnosis, before touching anything

Every pinned quote was grepped. **None vanished; all shifted by +13** (or were never a pin):

| quote | was | now | class |
|---|---|---|---|
| `6.744` (found prefix `**The live fan-out figure (cell G5, race-free; …`) | :195 | :208 | shifted |
| `258,035` (resident-capacity paragraph) | :865 | :878 | shifted |
| `1.5017` (same paragraph) | :865 | :878 | shifted |
| `form, 1.249x, … does not improve at all` | :865 | :865 | not a pin — this is what the audit *found* at :865 |

Resolution rule used: match each ref by its unique `found` startswith-prefix (not by the figure, which
occurs 9x for `6.744`), then verify the expect/stale invariant at the target line. 4/4 unique, 0 ambiguous.

## Case A — prose (the guard was right)

- `:1110` "the 6.744x fan-out bound" → "the 6.744x fan-out bound **from cell G5**".
  The guard's token is `(?<!pre-)\bG5\b`, so "cell G5" in the same sentence satisfies it honestly.
- `:1112` "the +134.6 to +747.2 uncached tokens per turn after a boundary" →
  "… **on average** after a boundary (a range of twelve arm means, not a per-turn bound)".
  Uses the package's own vocabulary (abstract `:47-52`, SS 6a `:383`); qualifier sits well inside the
  guard's 400-character window.

## Case B — pins (the audit was fragile, the quotes were fine)

`state/gap-ledger.json` `evidence_refs[].ref` repointed: `:195 → :208` (G5, expect 6.744),
`:865 → :878` (G5 expect 6.744 stale=true; G5 expect 258,035; G7 expect 1.5017). Four `detail` notes
appended recording the repoint and its cause. Byte-identical round-trip of the unmodified object verified
before writing, so the diff is exactly those eight strings.

## Gates after the fix (real exit codes)

- three targeted guards: **3 passed, exit 0**
- `verify_package.py`: **exit 0** — `PASS — 69 claims, 69 mapped 1:1 … UNVERIFIED: none`
- `recompute_r2.py all`: **exit 0**
- red→green on a copy basis (`/tmp/ms.fixed.copy`, digest `a8dec093188f0170`): pre-fix prose
  **RED exit 1** (both `:1110` provenance and `:1112` QUALIFIER); fix restored, digest identical,
  **GREEN exit 0, 2 passed**
- full suite `tests/ -q`: **exit 1 — 1 failed, 1374 passed, 1 skipped (102.49s)**. The single failure is
  `tests/test_claims_value_guard.py::test_the_guard_bites_when_the_recomputation_moves`, which passes
  standalone (9 passed, exit 0) and is owned by another unit — not touched here.

## Answer weakened?

0 assertions weakened, 0 numbers changed.

## Recommendation

The audit pins by line number, so it will break again on the next insertion. Durable fix: content-addressed
pins (store the quoted text's digest, have `ref_line()` locate it), so insertion is a no-op and deletion
still fails. Needs its own unit (pin schema + test helper).

## Assumption flagged to the main session

The stale line references live only in `state/gap-ledger.json`, which the card lists under `Do NOT touch
state/**` while also authorising "the specific audit/pin file(s) that hold the stale line references".
I read the specific allowance as authorising exactly that one file, and touched nothing else under `state/`.
