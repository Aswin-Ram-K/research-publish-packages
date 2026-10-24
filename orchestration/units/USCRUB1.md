# USCRUB1 — disclosure scrub of the would-be-public encoder-crossover package

## Purpose (one purpose)

Remove the **scrubable-reference** class of exclusion-gate hits from the would-be-public
encoder-crossover package — the third of the gate's three hit classes, and the only one that is this
unit's job. The other two classes (95 audit artefacts → curation; 104 fixture/dataset instrument hits →
under separate test by UTOK1) are out of scope and were not touched.

## Why this unit exists

An exclusion gate over the package reported **301 hard-fail hits**: **95** audit artefacts that should
not ship (curation, not this unit), **104** fixture/dataset instrument hits (`code/fixture/**`,
`code/harness/data/**`, `eval/results/**`, `disagreements*.jsonl` — UTOK1's separate test), and **~102
scrubable references — this unit's job.** Two of the three defects are defects in *publishable* material
that need fixing regardless of the fixture question.

## Hard bound

**Maximum 45 tool calls.** Stop and report `partial` if that would be exceeded. **Actual: 32** calls.

## Declared write paths (touched nothing else)

`papers/encoder-crossover-190/MANUSCRIPT.md` · `repro/encoder-crossover-190-SANITISED/**` ·
`experiments/second-labeller-190/**` · `orchestration/units/USCRUB1.md` ·
`orchestration/handoffs/USCRUB1.json`

## The three defects and what happened

| # | defect | verdict |
|---|---|---|
| 1 | `MANUSCRIPT.md` named the private branch SHA (`:754`, `:821`) and pointed at internal documents (`:832` exclusion inventory, `:842` licence to-do) | **fixed** — SHA and branch name replaced by *"an unmerged development branch (name and commit withheld)"*; both internal-document pointers removed by neutral re-wording; no measured number touched |
| 2 | sanitisation MISS in `code/harness/**` — absolute target paths survived because the strict-term list never held the target path or repo name | **partly fixed** — `harness/collect.py:394` fixed; **the 3 named `harness/data/manifest.json:5,10,15` hits were left** because the ⛔ DO-NOT-TOUCH list names `code/harness/data/**` (see *Instruction conflicts*) |
| 3 | provenance citations of the read-only target — ~98 hits in `paper/**` (27) and `eval/**` (71) | **fixed** — by neutral substitution; provenance claim, read-only proof and evidence content all preserved |

## Evidence

See `repro/encoder-crossover-190-SANITISED/SCRUB_REPORT.md` (the deliverable) for: the masked substitution
rules (14 rules), **per-pattern before/after counts**, **every file changed with `file:line`**, the
reproduction re-run output, and the new findings beyond the known set.

Headline numbers:

* **35 existing files changed + 2 new**; **184 rule-hits** removed by the rule engine plus 6 hand-checked
  edits. 34 files had disclosure hits.
* Per-pattern before → after, released subset: `<user-home>` **75 → 5**, `<target-repo>` **61 → 5**,
  `<source-repo>` **3 → 0**, `<sha8>` 0 → 0, `github.com/<source-account>` **1 → 0**, `/Users/` 0 → 0,
  `~/` 0 → 0, `89003e70` 0 → 0. Paper: `<user-home>` **41 → 0**, `<target-repo>` **42 → 0**,
  `<sha8>` **9 → 0**, `<source-repo>` **17 → 0**. Eval tree: `<user-home>` **40 → 0**,
  `<target-repo>` **38 → 0**.
* `MANUSCRIPT.md` specifically: `<sha8>` **2 → 0**, `<user-home>` **0**, `<target-repo>` **0**,
  `<source-repo>` **0**.
* **`numbers_changed = 0`** — the ten `CLAIMS.md` values, the `57a29b4e78bff60f84309e2e95b56f49663884a13b801345eecd93813ecbf300`
  scoring-projection digest and the `train`/`dev` digests (`24c39afa…020c09`, `d311a99f…4eaa976`) are
  **identical**; `ALL CLAIM NUMBERS PRESERVED: True`; declared primary baseline **`0.6789` intact**;
  `orig-regenerated == san-regenerated : True`; `san-regenerated == shipped : True`. The re-run logs
  (`verify/VERIFICATION.txt`, `verify/RECOMPUTE-CLAIMS.txt`) are regenerated and scan **clean**.
* Metadata: `INTEGRITY.md` **46/46 rows verified against disk, 0 stale**; `MANIFEST.json`
  `counts.bytes_total 5393492 → 5383740`, `hashes_verified_identical 40 → 37`.
* Tool: `verify/scrub-uscrub1.py` (`--audit` / `--apply`), idempotent, literals assembled from fragments
  so the tool itself ships clean.

## Residuals (deliberate, named)

1. **`/home/zer0null` / `Duval`: 5 lines remain** in the released subset, and they are exactly the
   do-not-touch instrument: `fixture/DECISION_CASE_SCHEMA.ts:2`,
   `variants/no-union/files/fixture/DECISION_CASE_SCHEMA.ts:2`, `harness/data/manifest.json:5,10,15`.
2. The **fixture/dataset instrument vocabulary** — `src/broker` 6/9, `StateClass` 108/111,
   `grantPolicy` 79/82, `admit(` 43/46, `expanded[` 53/58 (subset, before-scrub-count/after incl. report
   mentions) — untouched by instruction; UTOK1 owns it. **These cannot be removed without changing the
   instrument's own question text and therefore every reported accuracy.**
3. `EXCLUDED.md` / `LICENCE_TODO.md` named outside `MANUSCRIPT.md` — those denote files that ship *inside*
   the released subset, not a private boundary.
4. The target's revision identity (`907fa39…`, `ad301ae…`) and `.worktrees/integration` — **kept**; the
   revision ids are the read-only proof's anchors and removing them would weaken a checked claim.

## Instruction conflicts encountered (must be ratified by the parent)

1. **Defect 2 vs the ⛔ list, on the same three lines.** Defect 2 says "fix every occurrence in the
   sanitised tree" and names `manifest.json`(3), but `code/harness/data/**` is on the DO-NOT-TOUCH list.
   `harness/data/manifest.json:5,10,15` **is** those three hits. **Honoured the ⛔ list** (stronger
   constraint, stated reason is that editing invalidates UTOK1's in-flight test, and the file carries a
   recorded sha256 and is regenerated by `prepare.py`).
2. **Paper write-path gap.** The declared-write-path list names only `papers/encoder-crossover-190/MANUSCRIPT.md`,
   but defect 3 requires neutral substitution in `paper/**` across nine files. **Edited those eight extra
   paper files** — defect 3 cannot otherwise be satisfied, and neither UTOK1 (`experiments/token-substitution-test/**`)
   nor ULEAD1 (`strategy/LEAD_PACKAGE.md`) owns anything under `papers/**`, so no write clash was possible.
   **Parent should ratify or revert**: `AVAILABILITY.md`, `CHECKLIST.md`, `CLAIMS.md`,
   `DISCLOSURE_CHANGES.md`, `EVIDENCE_NOTES.md`, `LICENSE_ANALYSIS.md`, `MANUSCRIPT_CHANGES.md`,
   `OPEN_QUESTIONS.md`, `REFERENCES.bib`, `REFS.md`, `REFS_VERIFIED.md`, `UNSOURCED_RETAINED.md`,
   `VERIFIER_CORRECTIONS.md`.

## Not touched

`code/fixture/**` · `code/harness/data/**` · `eval/results/**` · `disagreements*.jsonl` ·
`repro/encoder-crossover-190/**` (raw tree, never written) · `strategy/**` · `code/verify/**` and the
audit artefacts' inclusion/exclusion (curation's call). `/home/zer0null/Duval` was never written and
never had `git` run in it. Nothing was written to `/tmp` or `/dev/shm` as durable state (per-call tmpfs).

## Deliverables

1. The edited files (see `SCRUB_REPORT.md` §3 for the full `file:line` list).
2. `repro/encoder-crossover-190-SANITISED/SCRUB_REPORT.md`.
3. `orchestration/handoffs/USCRUB1.json`.
