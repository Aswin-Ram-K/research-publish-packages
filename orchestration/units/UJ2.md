# UJ2 — daily journal notes for 2026-10-06 … 2026-10-13

**Purpose (one):** consolidate the late, heavily-dated Duval research corpus into small daily journal
notes, one per day that actually had work, for **2026-10-06 through 2026-10-13 inclusive**.

**Target:** `/home/zer0null/Duval` — read-only throughout. No write, no `git` state change; only
`git log` (read-only) and file reads/greps were issued against it.

**Hard bound:** maximum **50 tool calls**. Used: **46** (43 before finalisation). Status: **done** — all
eight days carried real evidence, so no day was skipped.

**Declared write paths (only these were touched):**
- `journal/2026-10-06.md`, `journal/2026-10-07.md`, `journal/2026-10-08.md`, `journal/2026-10-09.md`
- `journal/2026-10-10.md`, `journal/2026-10-11.md`, `journal/2026-10-12.md`, `journal/2026-10-13.md`
- `orchestration/units/UJ2.md`, `orchestration/handoffs/UJ2.json`

`journal/INDEX.md` was **not** written (another unit owns it). Pre-existing notes for 2026-09-28 …
2026-10-05 (another unit's range) were not read for content and not modified.

**Method.**
1. `git -C /home/zer0null/Duval log --since=... --until=... --format='%h|%ad|%s' --date=short` for the
   whole 2026-10-01 … 2026-10-14 range, then a per-day commit count (`| sort | uniq -c`) to establish
   which days had work. All eight in-range days did (3, 31, 45, 28, 46, 28, 126, 79 commits).
2. A per-day `--name-only` pass for 2026-10-06 … 2026-10-09, and the commit list for the rest.
3. Only the sources produced by each day were then read: the four `TIER2_*` notes, `SEARCH_CHANNEL`,
   `KERNEL_RUN_FIRST_CYCLE`, `EXTERNAL_EVIDENCE_2026-10-07.md`, `TIER2_9B_SEARCH`,
   `experiments/EXP#16`, `EXP#18`, `EXP#22`, `FINDINGS_REGISTER.md`, `docs/DECISION_LOG.md`
   (headings D-090 … D-127) and `docs/COMPACTION_LOG.md`.

**Findings that shaped the notes.**
- `FINDINGS_REGISTER.md` was **not modified** in this window (verified by a per-path `git log`), and it
  carries no `F-*` ids for these days beyond `F-EXP11-*` / `F-IDENT-*`. So `Learned` cites `F-*` only
  where the register actually has them, and otherwise uses the corpus's own `D-1xx` decision ids and
  verbatim sentences. `SEARCH_CHANNEL` states explicitly that its findings are **instrument** findings
  and "must not be cited as if they were" `F-<scope>-<nn>` entries.
- `LONG_HORIZON_EVALS_2026.md`, `SELF_REFINEMENT_DEGRADATION_2026.md`,
  `STAGED_EXTRACTION_PROVENANCE.md` and `FINDINGS_REGISTER.md` were all **last touched before
  2026-10-06** (2026-10-01, 2026-10-04, 2026-09-29, 2026-10-04 respectively) — they are background
  corpus for this window, not work produced in it, so they are not claimed as any day's output.
- `/home/zer0null/Duval` was already dirty before this unit ran (`AGENTS.md`,
  `docs/COMPACTION_LOG.md`, `guidance/codex/COMPACTION_LOG.md` modified — consistent with the
  10-11 STOPPED_CLOSEOUT record of ~28 dirty paths). Nothing in this unit wrote to it.

**Known limitation (recorded, not fixed).** Word count per note was measured with `wc -w`, which counts
markdown emphasis tokens; notes 10-10 … 10-13 were trimmed once and the exact figures are in the
handoff. Any note still above the 400-word bound is left as-is per the parent's instruction that a
separate unit owns corrections.
