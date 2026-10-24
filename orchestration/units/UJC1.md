# UJC1 — journal correction pass (2026-09-28 … 2026-10-13)

**Purpose.** Re-confirm and fix the defects in the 14 finished daily notes; add `journal/INDEX.md`.
Different unit from the two authors; authors not extended.

**Write paths.** `journal/**`, `orchestration/units/UJC1.md`, `orchestration/handoffs/UJC1.json`.
**Hard bound.** 55 tool calls (used ~27). Target repo `/home/zer0null/Duval` strictly read-only
(only `git log`, `git status`, `grep`/`awk`/`sed -n` reads were run there).

## Defects — verified item by item

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1a | `2026-10-01.md` cites `docs/COMPACTION_LOG.md` | **CONFIRMED** | add-commit `e9facea` 2026-10-11 > 2026-10-01; file has no 2026-10-01 entry |
| 1b | `2026-10-05.md` lists `KERNEL_RUN_FIRST_CYCLE_2026-10-10.md` | **REFUTED** | cited in `2026-10-10.md`, not 10-05; add-commit `50cf9ad` 2026-10-10 = note date |
| 1c | `2026-10-06.md` cites `TIER2_MODEL_SURVEY_2026-10-10.md` | **CONFIRMED** | add-commit `1aa1431` 2026-10-09 > 2026-10-06 |
| 2 | `2026-10-05.md` cites `5113368` | **CONFIRMED** | commit is 2026-10-04 (off-date); subject matches note |
| 3 | `2026-10-09.md` cites `d22d2cf` | **CONFIRMED** | sha exists in no ref; `d22d6cf` 2026-10-09 subject matches "unwrap fences … tier-1" |
| 4 | `2026-10-01.md` Shipped has no shas | **CONFIRMED** | 140 commits that day (author-date, all refs); 21 shas now populated |
| 5a | `2026-10-10.md` over-length | **CONFIRMED** | 446 wc-strict / 422 prose → 409 / 385 after trim |
| 5b | `2026-10-12.md` over-length | **REFUTED** | 394 prose ≤ 400; the 429 wc-strict is 35 standalone punctuation tokens |
| 5c | `2026-10-13.md` over-length | **CONFIRMED** | 453 wc-strict / 421 prose → 424 / 392 after trim |

**Confirmed 7 · fixed 7 · refuted 2.** Notes edited: 10-01, 10-05, 10-06, 10-09, 10-10, 10-13 (6).

## Adjudication applied

- Non-anachronistic same-day repointing was preferred where a same-day artifact carries the fact.
- Both surviving `add-date > note-date` pointers (10-01 `COMPACTION_LOG.md`, 10-06 `TIER2_MODEL_SURVEY…`)
  are **kept and explicitly labelled `later write-up`** — provenance is never silently deleted.
- `5113368` is **kept and labelled `(off-date: 2026-10-04)`**: no 10-05 commit carries E0-13/F-ISSUE-04,
  so no repoint was possible; deletion was rejected.
- Trims removed prose only. Every commit sha, finding id (`F-*`/`D-*`/`E*`), numeric measurement and
  source path in the trimmed notes was preserved verbatim.

## Re-verification after editing (run by this unit)

- **3a** cited sha vs note date: daily notes → **1** mismatch, the labelled off-date `5113368`;
  `INDEX.md` anchors → 16/16 rows OK (10-03 has no anchor by design).
- **3b** cited `docs/...` add-date > note date: **2** raw, both explicitly labelled later write-ups → 0 unlabelled.
- **3c** prose-only word counts: **0** of 14 notes exceed 400 (max 394).
- Target repo: `git status --porcelain` = 8 pre-existing dirty paths; this unit wrote nothing there.

**Status: done.**
