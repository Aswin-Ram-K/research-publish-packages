# Unit UFIXCUT7 — byte-bookkeeping correction to the release-cut document

**Status:** in progress. Card persisted first, per workspace rules.
**Parent session:** `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`
**Workspace:** `/home/zer0null/reserach extarctor`

## Purpose (one, single-purpose unit)

Apply verifier unit **UVEREL7**'s corrections to `strategy/GATED_READ_RELEASE_CUT.md`:

1. **§2 byte bookkeeping** (contradicted by the filesystem). Correct cut1, cut2, cut4 totals and both
   deltas; `cut3` = 5 files / **28,233 B** is correct and must not change. Preserve each original value
   next to its correction and add one dated `Note 2026-10-16 (UFIXCUT7):` naming UVEREL7 as the measurer
   and the method it used (`find -printf '%s'` / `du -sb`).
2. **§8 universality sentence** ("every number in §1–§6 … from the run that produced the §4 md5s") — it
   fails for the three §2 totals; say so, do not delete the sentence.
3. **§5 / §6 absolutes** — no *substantive* private identifier survives; three harmless surface strings do
   (`ptok` at `verify_claims.py:244`, `n_files` as a substring of `payload_in_files`, `unparsed` at
   `METHOD.md:38`). Wording only; UVEREL7 found no substantive leak.

## Declared write paths (exactly these)

- `strategy/GATED_READ_RELEASE_CUT.md`
- `orchestration/units/UFIXCUT7.md`
- `orchestration/handoffs/UFIXCUT7.json`
- `scratch/ufixcut7/**`

## Inputs read

- `strategy/VERIFICATION_REPORT_REL7.md` — UVEREL7 verdict `partial`, **no blocker**, ship decision unchanged.
- `strategy/GATED_READ_RELEASE_CUT.md` — target; UVEREL7's appended dated note (lines 246–275) is
  **not to be touched**.

## Method / evidence

- Re-measure every cut before writing: `find scratch/urelease7/<cut> -type f -printf '%s\n'` summed, and
  `du -sb scratch/urelease7/<cut>/*` total. Assert cut1=1,572,249; cut2=1,148,742; cut3=28,233;
  cut4=27,200; abort if measurement disagrees with UVEREL7.
- Assert each before-string matches exactly once before writing; abort (no partial write) on any mismatch.
- Re-verify `ptok` is on `verify_claims.py:244` and `unparsed` on `METHOD.md:38` before quoting those
  line numbers.

## Hard bound

**8 tool calls.** STOP and report if a before-string does not match exactly once, or a measured byte count
differs from UVEREL7's.

## Untouched

- UVEREL7's appended dated note; every number/section outside the correction list.
- `/home/zer0null/Duval` (read-only); **no git command is run anywhere**.
