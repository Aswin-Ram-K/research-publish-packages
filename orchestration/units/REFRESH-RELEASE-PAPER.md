# UNIT REFRESH-RELEASE-PAPER — refresh the stale manuscript in the publication tree

**Run:** 2026-10-24 (autonomous) · **Status: `done`** — all 10 gates pass.

## Defect (as reported, and re-measured by this unit)
`release/v0.1/papers/context-cache/MANUSCRIPT.md` was 92,454 bytes / mtime 21:16, sha256
`deeb0b1300dc79b8d0840181a44a0cb9c6770f8361bf8776ca0b06722c84c72b` — copied *before* `CITE-VERIFY` and
before `CITE-PROSE-REPAIR`. Re-measured: it carried **3** `[CITATION NEEDED]` markers, **0** of the three
verified citations, and **1** occurrence of the mangled fragment `SGLang review of attention backends`.
`papers/context-cache/CITATIONS.md` was **absent** from the release tree entirely.

## Purpose
Refresh the two paper files from the live tree, re-apply the mandatory sanitisation to the copies,
regenerate the manifest, and record the refresh in `release/REPORT.md`.

## Bound
30 tool calls. Handoff written FIRST as `partial`, updated to `done` after the gates passed.
Stop-and-report rule: a gate failing 3 times on the same file → report `partial` naming file + line.
(Not triggered.)

## Write paths
`release/**`, `orchestration/units/REFRESH-RELEASE-PAPER.md`,
`orchestration/handoffs/REFRESH-RELEASE-PAPER.json`.

## What was done
1. Copied live `papers/context-cache/{MANUSCRIPT.md,CITATIONS.md}` → `release/v0.1/papers/context-cache/`
   (`papers/**` read-only: copied *from*, never written to).
2. Re-applied sanitisation with exact, order-fixed patterns:
   `192\.168\.2\.(168|187)(?::\d+)?` → `serving-host`;
   `/home/zer0null/reserach extarctor` → `<workspace>`; `/home/zer0null/Duval` → `<workspace>`.
   Counts: MANUSCRIPT **1** host / **0** path; CITATIONS **0** / **0**. The one hit is line 993
   (`http://192.168.2.168:8012` → `http://serving-host`), consuming the `:8012` port suffix per the
   existing A2 rule. `diff` live vs release = exactly line 993; line count unchanged at 1214.
3. Regenerated `MANIFEST.json` from disk: 942 → **943** entries, `total_bytes` 61,027,417 → **61,035,244**;
   exactly one digest changed (`MANUSCRIPT.md`), one added (`CITATIONS.md`), none removed. Run twice —
   the second run after appending to `release/REPORT.md` — with identical results.
4. Appended §10 to `release/REPORT.md` (dated 2026-10-24 21:50 CDT) with before/after sha256s, the
   replacement-count table, and the verbatim gate outputs.

## Gates (all 10 pass, final state)

| # | Command | Output |
|---|---|---|
| 1 | `grep -rE '192\.168\.' release/v0.1 \| wc -l` | `0` |
| 2 | `grep -rE '/home/zer0null' release/v0.1 \| wc -l` | `0` |
| 3 | `grep -c 'CITATION NEEDED' <release MANUSCRIPT>` | `0` |
| 4 | `grep -c 'SGLang review of attention backends' <release MANUSCRIPT>` | `0` |
| 5 | `grep -c` for 2309.06180 / 2312.07104 / 2605.23296 | `1` / `1` / `1` |
| 6 | `wc -l <release MANUSCRIPT>` | `1214` |
| 7 | `find release/v0.1 -size +25M` | *(empty)* |
| 8 | licence line + `diff` vs `sed -n '5p' /home/zer0null/Duval/LICENSE` | `1` + `IDENTICAL` |
| 9 | entries vs shipped-minus-manifest | `entries=943 on_disk=944 shipped_minus_manifest=943 equal=True` (mismatched=0, unlisted=0) |
| 10 | `du -sh release/v0.1`; file count | `62M release/v0.1`; `944` |

## Constraints observed
No writes under `papers/**` or `/home/zer0null/Duval`; Duval read only via `sed -n '5p'`. No server
restarted, no `/flush_cache`.

## Assumptions
- **A9** — per-refresh replacement counts recorded as an *added* key `sanitisation.refresh_2026_10_24`
  inside the existing `sanitisation` object; top-level shape preserved; tree-wide tallies
  (`files_redacted` 167, host 850, path 161) carried over unchanged from the original pass.
- **A10** — `generated` left at `2026-10-24` (same day; the dated refresh record lives in `REPORT.md` §10).
- **A11** — `CITATIONS.md` had no before-digest because it was absent; recorded as `null`/absent rather
  than fabricated.
