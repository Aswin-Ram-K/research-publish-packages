# FIX-G16-LEDGER — the gap ledger predates G16, so test_gap_ids_match_ledger fails on a real entry

**Status:** done. **Bound:** 25 tool calls (24 used).
**Writes:** `state/gap-ledger.json`, `state/gap-triage.json`, `papers/context-cache/GAPS.md` (G16 heading
status + one dated note), `tests/test_gap_triage.py`, `state/logs/FIX-G16-LEDGER-redgreen.txt`, this card,
the handoff JSON.

## Objective

CACHE-AUDIT added `G16` to `papers/context-cache/GAPS.md` (stated limitation: the cache-option search was
narrow; two rejections cite a source that does not say what they claim) but deliberately did not regenerate
`state/gap-ledger.json`, so `tests/test_gap_closure_ledger.py::test_gap_ids_match_ledger` failed on a real gap.
The ledger had to learn G16 **truthfully** — a live entry whose evidence is re-checked, not a silencing edit.

## Method

1. Read the failing test, GAPS.md G16, the ledger (16 entries) and the triage record (10 decisions).
2. Re-checked G16's citations against disk by **content**, not existence: the five pinned docs under
   `scratch/cache-audit/docs/` match their recorded sizes and digests; `kv_offloading_size` is at
   `pin_vllm_cache.py:191`, `--kv-offloading-size` at `pin_vllm_argutils.py:1246`; the radix policy page lists
   all five policies and `protected_threshold` default 2 (line 63); the session page names
   `UnifiedRadixCache`; the S3 failure is `S3-startup-failure.log:42` — one line, `unrecognized arguments`.
3. Added the G16 entry (13 refs; no `role=closure` ref, so it derives `open`, matching its own status) and a
   `regenerated_by` block; appended the G16 triage decision under the same stated-limitation rule.
4. Put G16's classification on its heading (the triage guard requires one) and dated the header note.
5. Updated the triage guard's hardcoded ten-gap expectations to eleven, named as `EXPECTED_OPEN`/`EXPECTED_COUNTS`
   so the next gap is a one-line change rather than a treasure hunt.
6. The guard then surfaced a second, independent staleness: G5 and G7 cite `MANUSCRIPT.md:643` with
   `expect` figures that no longer sit there; repointed to `:645` and recorded `found`.

## Result

- `tests/test_gap_closure_ledger.py` + `tests/test_gap_triage.py` → **17 passed**.
- Ledger: 17 entries — **2 closed, 3 narrowed, 11 open, 1 unverifiable**. GAPS.md's 2026-10-23 tally
  (2/3/10/1) predates G16 and is cross-referenced by a dated note, not rewritten.
- `verify_package.py` → PASS, 63 claims, UNVERIFIED: none.
- Red→green (`state/logs/FIX-G16-LEDGER-redgreen.txt`): dropping G16 reproduces
  `gaps in GAPS.md missing from the ledger: ['G16']`; restoring `:643` reproduces
  `G5: MANUSCRIPT.md:643 ... expect '258,035' is not on the line`; restore → 17 passed.

## Findings left to the prose owner (not edited here)

- `PACKAGE.md:94-96` "Chunked-prefix cannot start": S3 died at **flag parsing** (`unrecognized arguments:
  --enable-chunked-prefix-cache`), i.e. the flag changed name in this SGLang build; it is not a feature result.
  GAPS.md's "the live default is already the enabled path" also reads a stale top-level field — the live
  effective value is `disable_chunked_prefix_cache: true` (`state/config/live-server-config.json:34`,
  `runtime_effective`).
- V-MATRIX-FOLD's `151.8172` → `152.0` understatement still stands; `serving_brief.py --check` FAILs on it.
