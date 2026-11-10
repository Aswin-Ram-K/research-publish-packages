# U-SPCC-CLOSE — session close-out: journal, indexes, state and status for the SPCC batch

**Card:** U-SPCC-CLOSE · execution close-out (2026-11-10)
**Bound:** ≤35 tool calls, **0 inference requests**. OFFLINE: no live model call, no container or service
change, no git commit/push, no edit to `orchestration/VERDICTS.md`, no test/row/`serving/` edit.

## Why

The serving-context programme batch (`U-SPCC-0` … `U-SPCC-9C`, verifiers `V-SPCC-0` … `V-SPCC-5C`) landed
artefacts but its record is not closed: there is no `journal/2026-11-10.md`, `journal/INDEX.md` stops at
2026-11-06, `docs/STATE.md` still says `Last updated: 2026-11-06` and carries a git line that the
preservation commit invalidated, `orchestration/STATUS.md` has no batch section, and `doc_check` fails on
two orphan pages written by this batch.

## Objective

1. Write `journal/2026-11-10.md`: what was asked, every deliverable with its owning handoff, what was
   verified and by what, the corrections (masking 12/48 + 8/48 with all successes at d=2 ⇒ 0/36 beyond
   distance 2; `prefix_sha256` over L0+L1; the reverted `origin/main` merge; the compiler's unwired first
   incarnation), what is red and why, what is blocked and by which decision, and the exact next step.
2. Extend `journal/INDEX.md` (title range + one row).
3. Refresh `docs/STATE.md`: header, §0, new §1a current state (compiler, `spcc` arm, allowance,
   pre-registration), §5 git line, §6 the three genuine decisions, new §11 "what changed".
4. Append the batch section to `orchestration/STATUS.md` and extend its one-line state.
5. Add the two missing rows to `docs/INDEX.md`.

## TESTS

No new test. The documentation guard is the test: `python3 tools/doc_check.py` fails on an orphan doc, a
broken `](…md)` target or a journal day with no index row.

## CLOSING

- Acceptance command (see `verify:` below) run once as a frozen string; its real exit code is pasted in the
  handoff's `evidence.doc_check`.
- **The verdict row is owed, not written here.** This card may not edit `orchestration/VERDICTS.md`; the
  row is handed to the same backfill unit that owns the six unverdicted closures listed in
  `U-SPCC-9A.json` `remaining_failures` item 4.
- Handoff written last.

## verify
```
verify: python3 tools/doc_check.py
```

## WRITE PATHS — exactly (nothing else)
`journal/2026-11-10.md`
`journal/INDEX.md`
`docs/STATE.md`
`orchestration/STATUS.md`
`docs/INDEX.md`
`orchestration/units/U-SPCC-CLOSE.md`
`orchestration/handoffs/U-SPCC-CLOSE.json`

## HARD RULES
- Never edit the checker, a test, a row file, a frozen record or `VERDICTS.md` to make the gate green.
- Never print a number the handoffs do not carry; re-measure where the record moved (ledger).
- Do not claim the live billed-accounting proof passed: `U-SPCC-LIVE.json` does not exist.

## REPORT

Board end line: `doc_check` exit 0; `tests/test_agent_context.py tests/test_orchestration_handoffs.py`
**red on a pre-existing handoff-shape cluster** (49 post-freeze files, none `U-SPCC-*`); ledger re-measured
7,969 / 12,094 ⇒ 4,125 remaining (row count over 93 `rows-*.jsonl` files).

## CORRECTION — 2026-11-10T06:31 (billed proof)

This card's first draft said the live billed-accounting proof was **pending** because
`orchestration/handoffs/U-SPCC-LIVE.json` was absent when the directory was read. It was written at
**06:29**, two minutes later. Re-read, the proof is **DONE**:

- `--claim-mode plumbing`, arms `masking-no-fetch`, fixture `tasks-v7/TX-03.v1.json`;
  **100 turns / 100 requests, 0 failed, 0 truncated, `finish_reason{"stop":100}`**.
- prompt **174,047** · cached **159,744** · uncached **13,746** ⇒ cached/prompt **0.917821**; `null`
  `cached_tokens` on turns **[1, 5]** only (`coverage 0.98`); **557** prompt tokens accounted as neither;
  the block's `cached_fraction` `0.9207677` is cached/(cached+uncached), not cached/prompt.
- **It is a plumbing proof only:** the scorecard exits **1** with **40/50 checks failing on answer shape
  (`kind NONE != NUM`)**, so it says nothing about accuracy on that arm/fixture pairing.
- **Billing is now measured, not vacuous** (`U-SPCC-11` landed the stamping fix): `billed_tokens`
  **14,303** with `billed_source "derived"` (`prompt − cached`; `= prompt` when `cached` is null, because
  SGLang omits the counter when nothing was cached — never `uncached_tokens`, never `0`). The ambiguous
  `cached_fraction` was removed for two named fields: `cached_fraction_of_prompt` **0.917821048337518** and
  `cached_fraction_of_accounted` **0.920767767594674`. `reconcile_delta_total` **557** against tolerance
  **1,740** (1 % of prompt), **within tolerance true**. **14,303 is charged; 159,744 is the discount**; the
  557 residual is **reported, not asserted away**. The landed score file
  `experiments/ptr-engine/measure/score-spcc-billedproof-2026-11-10.json` still carries the stale
  `billed_tokens: 0` block and must not be cited until its landing unit refreshes it.

## CORRECTION 2 — 2026-11-10T06:32 (ledger figure)

The ledger line first read **7,953 spent / 4,141 remaining** from an intermediate `request_ledger.py`
snapshot. The **row store** is the count of record: **93 `rows-*.jsonl` files, 7,969 rows** ⇒
**7,969 spent / 4,125 remaining** of the 12,094 `PROJECT_QUOTA`
(`experiments/ptr-engine/longrun/cell.py:141`); `U-SPCC-LIVE.json` `store_after` records the same. Over the
tool's 4,320 default by **3,649**; the de-duplicated 7,939 is deliberately not deducted. The comparative
ratio is restated consistently as **7,560 / 4,125 = 1.833×**.

## CORRECTION 3 — 2026-11-10T06:32 (ancestry and a stale record)

**`origin/main` is an ancestor of HEAD** (`mergebase 5554d82 = origin/main`, `HEAD 17182ff`), so the
"shares no common ancestor / different project" justification once attached to the revert is **false**;
the revert (`1977d30`) stands as a fact, and `origin/main` was **never advanced** by either merge — plan
deliverable 0 is **half done**. Backup ref: `origin/backup/screened-dirty-progress-2026-11-10-1348`.
`docs/CURRENT-REPO-STATE.md` still asserts `HEAD: dfba6aa` and the no-common-ancestor sentence; it is
**outside this card's write paths**, so it is named here for its owner rather than edited.

The machine blockers (SGLang relaunch, remote root, 68 GB `MemAvailable` reserve) stand unchanged.
Docs updated in place: `docs/STATE.md` §0, §1a, §5, §6, §11; `orchestration/STATUS.md` one-line state and
batch section; `journal/2026-11-10.md` blockers, corrections and evidence table; `journal/INDEX.md`
headline. `FINDINGS-LEDGER.md` untouched.
