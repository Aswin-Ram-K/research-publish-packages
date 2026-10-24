# Unit UFIXAD7 — date-token chronology fix + §4 supersession pointer

**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Workspace:** `/home/zer0null/reserach extarctor` (target `/home/zer0null/Duval` strictly read-only; no git run against it)
**Hard bound:** 12 tool calls; stop-and-report if any before-string does not match exactly once.

## Why
`strategy/VERIFICATION_REPORT_AD6.md` (handoff `orchestration/handoffs/UVERAD6.json`) judged UFIXAD6's
corrections faithful (all nine anchors hold, class set exact, protective conclusion survives, red→green
non-vacuous) but found two blemishes:
1. **Chronology defect** — the host date is `2026-10-16` (`date '+%Y-%m-%d %H:%M:%S %z'` → `2026-10-16
   16:37:35 -0500`) and both edited files have mtime `2026-10-16 16:35:15`, yet every UFIXAD6 dated note
   says `2026-10-15`. A correction dated a day before the files it corrects sorts wrong.
   Report `:51` and `:136` list the stale markers at **9 notes / 8 lines** in
   `strategy/GATED_READ_DISCLOSURE.md` (`:27, :28, :37, :139, :140, :175, :182, :218` — `:140` carries two,
   `(window version; 2026-10-15, UFIXAD6)` and `Dated class change (2026-10-15, unit UFIXAD6)`) plus the
   single note at `strategy/WITHHELD.md:450`.
2. **Legibility risk** — `strategy/WITHHELD.md:152` is a bold flat declarative ("the architectural/system
   claim is never published…"), but `:396`/`:398` («§4 is superseded») corrects the O-1 inversion and
   records the claim **is** published, dated ≤ 2026-10-10. A reader at `:152` alone cannot tell; "never
   published" is the exact assertion `strategy/GATED_READ_DISCLOSURE.md` §6 item 10 forbids.

## Declared write paths
`strategy/WITHHELD.md`, `strategy/GATED_READ_DISCLOSURE.md`, `orchestration/units/UFIXAD7.md`,
`orchestration/handoffs/UFIXAD7.json`, `scratch/ufixad7/**`.

## Scope decision (documented deviation from the brief's enumeration)
The brief enumerated `GATED_READ_DISCLOSURE.md` lines `:37, :175, :182, :218`. The verification report
measures **all 9 notes on 8 lines** as `contradicted` — every one is unit **UFIXAD6** work done on
2026-10-16, so every one is the same defect. Fixing only four would leave five notes still sorting a day
before the files they correct. UFIXAD7 therefore re-stamps **all UFIXAD6-dated notes** in the two in-scope
files: `WITHHELD.md:450` and the 9 notes in `GATED_READ_DISCLOSURE.md`. No other file is touched; the
~1100 stale-token docs elsewhere are a separate job.

## Planned edits
- `strategy/WITHHELD.md:450` — `Dated correction (2026-10-15, unit UFIXAD6)` → `2026-10-16`; append one
  inline parenthetical recording drift (whole-workspace `*.md` count, measured).
- `strategy/WITHHELD.md:152` — keep the sentence verbatim; append a one-sentence forward pointer naming
  §8.7 / `:398` as the supersession.
- `strategy/GATED_READ_DISCLOSURE.md` — re-stamp all 9 UFIXAD6 notes `2026-10-15` → `2026-10-16`.
- All writes assert the target line/string occurs exactly once and that no non-target line changed.

## Measurement
- `date '+%Y-%m-%d %H:%M:%S %z'` → `2026-10-16 16:37:35 -0500`
- `grep -rl --include="*.md" "2026-10-15" .` → 1108 files; `... "2026-10-16" .` → 189 files
  (brief's "≈136 vs 71" did not reproduce under this command; tracked-only `git ls-files '*.md'` gives
  3 vs 1 — reported as measured, not copied from the brief).

## Anchor files (read-only, not edited)
`strategy/ARCHIVE_WINDOW_CHECK.md`, `strategy/DISCLOSURE_INVENTORY.md`, `strategy/PRIOR_DISCLOSURE_AUDIT.md`,
`strategy/VERIFICATION_REPORT_AD6.md`, `papers/**`.
