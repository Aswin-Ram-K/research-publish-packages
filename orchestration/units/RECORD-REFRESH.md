# RECORD-REFRESH — the two first-read files describe this batch then

**Unit card, persisted by the unit itself.** Executed 2026-10-26, automated, offline (**0 inference requests**).

## Purpose

`orchestration/VERDICTS.md` had not been written since **2026-10-25 02:39** (measured: 424,582 B / 4,010 lines /
`sha256 d01359d2…`). Through the whole ptr-engine longrun batch — every PASS and every FAIL it earned — the file a
session following `AGENTS.md` reads first was two days stale. `orchestration/STATUS.md` was fresher (2026-10-26 10:35,
41,302 B / 376 lines) but organised around the earlier docket/context-cache programme. A fresh session therefore read a
stale verdict ledger and a status page about different work.

## Hard bound

≤22 tool calls, 0 requests. **Used 18 calls, 0 requests.**

## Write paths (exactly)

`orchestration/VERDICTS.md`, `orchestration/STATUS.md`, `experiments/ptr-engine/measure/RECORD-REFRESH.json`,
`orchestration/units/RECORD-REFRESH.md`, `orchestration/handoffs/RECORD-REFRESH.json`,
`orchestration/journals/RECORD-REFRESH.jsonl`.

## Method

1. **Probe before trusting the card.** Re-measured both files (`sha256sum`, `wc -l`) — the card's table reproduced
   exactly, so its numbers are cited, not re-invented.
2. **Recover verdicts mechanically, never from prose.** Membership rule: a card is in the batch if its handoff carries
   a verifier `overall` dated `>= 2026-10-23`, **or** it has a journal in `orchestration/journals/` (93 files). Each
   row's verdict, command, exit and sha were extracted from `orchestration/handoffs/*.json` (`overall`, `evidence.command`,
   `evidence.commands`, `verdict_row`) and `orchestration/journals/*.jsonl` (`verdict`, `exitCode`, `exit`, `sha`,
   `executionId`, `taskId`). Nothing was inferred; where a field was absent it is printed `—` and the row is counted
   unrecoverable.
3. **Append, prove, then guard.** Old bytes are an exact prefix of new bytes (`sha256(head -c <old_size>)` == the
   pre-edit sha), which is insertions-only by construction. The register's guard ran on both files before and after.
4. **One paste, one register.** The 15 withdrawn entries were pasted from
   `experiments/ptr-engine/measure/WITHDRAWN.json` into `VERDICTS.md`; `STATUS.md` names the register, its guard and
   the 15 ids and re-derives nothing.

## Result

- `VERDICTS.md` += `## Batch: ptr-engine longrun (2026-10-26)` — 134 rows, split **PASS 15 · FAIL 11 · partial 34 ·
  cancelled 0**, plus 73 `author-report` and 1 `pending`; an `### Unrecoverable` accounting (133 of 134 rows cannot
  carry command+exit+sha); `### Withdrawn numbers — do not cite` (15 entries); `### What a verdict row can and cannot
  prove` built on `VERDICT-DISPUTE`; `### needs_correction`.
- `STATUS.md` += `## 8. Current programme` — objective in five lines, three pillars, the four-link blocker chain
  (gate precondition → claim stamp → v8 provenance → 800-request grid), live spend **1,101 / 4,320** used, **3,219**
  remaining (dedup 1,071 visible, **not deducted**), board thread `ws:78cead56-384a-4d9c-b974-02b454c6d3d5`, and a
  withdrawn-register pointer.

## needs_correction — recorded, not edited

| ref | defect |
|---|---|
| `orchestration/STATUS.md:221` | section 8 already held (`## 8. R2-VLLM instrument repair batch`); the append is also `## 8. Current programme`, so STATUS.md now carries two §8 headings. The card named the heading; a numbering pass is owed. |
| `orchestration/STATUS.md:320` | `## 9. SYS-OPT …` repeats the number of `## 9. Next structural steps` at `:286` — pre-existing. |
| `orchestration/VERDICTS.md:1-4010` | the ledger held no entry for this batch before the append; the cause (no unit was ever bound to journal its verdict there) is recorded, not fixed. |

## Verdict

**PASS** on the unit's own terms (additive-only proven, guard clean before and after, 0 requests), with one recorded
residual: 133 of 134 verdict rows remain unrecoverable as evidence and are listed as such rather than papered over.
