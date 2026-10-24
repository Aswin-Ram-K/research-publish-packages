# ULICENCE5 — licence placeholders filled + name/logo reservation removed

**Status: done.** Bound: ≤20 tool calls (used ~17). Written 2026-10-16.

## Purpose (one)
Make protection depend on a **real** licence text: fill every placeholder in
`strategy/licence-templates/**`, remove the name/logo reservation the author does not want, keep the
PolyForm Noncommercial 1.0.0 body byte-identical, and close the copyright-registration workstream.

## Author decisions implemented (settled 2026-10-16, not re-opened)
- No US copyright registration — protection is **licence-based alone**.
- The name/logo is **not** reserved (he does not mind it being shared).
- No personal email address, and none invented: `<CONTACT>` = the published repository's own issue
  tracker, `https://github.com/Aswin-Ram-K/research-publish-packages`.

## What changed
| File | Change |
|---|---|
| `PROPRIETARY-LICENSE.txt` | `<YEAR>`→2026, `<COPYRIGHT HOLDER>`→Aswin-Ram-K (4 occurrences, one split across a newline) |
| `RELEASED-PIECE/LICENSE` | Required Notice filled; name/logo paragraph removed; provenance note updated; body untouched |
| `RELEASED-PIECE/COMMERCIAL.md` | contact resolved to the issue tracker; gap note rewritten; `## Name and logo` removed |
| `RELEASED-PIECE/CONTRIBUTING.md` | `## Name and logo` (incl. limitation paragraph) removed |
| `PLACEMENT.md` | instructions rewritten; `§4` reservation section removed; `§5/§6` renumbered §4/§5; removal + registration-declined records added |
| `README-PARAGRAPHS.md` | placeholders filled in Case A, Case B and notices; reservation sentence removed; contact note resolved |
| `COPYRIGHT_REGISTRATION.md`, `COPYRIGHT_DEADLINES.md` | dated CLOSED note inserted at the top; existing analysis untouched |

## Verified properties
- **Zero placeholders remain** across `strategy/licence-templates/` (tree-wide angle-bracket scan empty).
- **Licence body byte-identical**: `lines 5–135`, **4563 bytes**, sha256
  `ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8` — re-fetched from the
  canonical URL on 2026-10-16 and equal. The old `lines 10–140` anchor is **superseded**.
- **Whole file now** 151 lines / 5851 B / `3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900`
  (was 150 / 5662 / `25aa637ba1689e87ad34c5acc25464a4eaaa2f5b2c84e3dc4d7ed84158277cfe`).
- **MIT census on the emitted package: exactly 7 hits**, all third-party model-licence attributions
  (DeBERTa-v3-base). No licence instrument and no README names MIT.
- **Closure notes are pure insertions** (diff shows 0 deletions).

## Follow-up (outside this unit's write paths)
`orchestration/units/UBUILD1.build.sh` now **fails closed**: its licence drift guard `:583–585` still
pins the old template digest, so the build aborts with
`FATAL: LICENSE template drift: sha256 is 3d364676... , expected 25aa637b...cfe`. Its `:586–587`
comment, its emitted-README placeholder line `:409–411`, and its git commit message `:988` are stale
too. A fresh unit must update them; ULICENCE5 may not write there.

## Recovery record
`strategy/` is untracked, so before/after is carried in `scratch/ulicence5/templates-orig/**`,
`scratch/ulicence5/edits.diff`, `scratch/ulicence5/edits.txt` and the verbatim removed sections in
`orchestration/handoffs/ULICENCE5.json`.
