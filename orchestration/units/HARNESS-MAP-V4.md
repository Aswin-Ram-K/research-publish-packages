# HARNESS-MAP-V4 — completion test, REFUSED at preflight: `not_yet`

**Unit** `HARNESS-MAP-V4` · execution `c9e43bf9` · HEAD `f17663d1fed0162a7dc3c5a0a58d372c710974c3` · 0 requests, offline.
**Verdict: `not_yet`** — the page this card exists to grade has not been written, and the grid has not produced a single completed cell.

## Preflight, measured

| # | Requirement | Met | Evidence (path) |
|---|---|---|---|
| 1 | `RUN-A*` (`ad214412-c39c-4a47-afb1-2be328e03b1e`) settled | **yes** | card `status=done`, execution `c456e8d4` `endedAt=1793039625939` `result=succeeded`; unit handoff `status=partial` — [`RUN-A-STAR.json`](../handoffs/RUN-A-STAR.json) |
| 2 | `orchestration/handoffs/OPERATOR-BRIEF-5.json` exists | **NO** | absent; `find` returns no `*BRIEF-5*`; highest page on disk is `OPERATOR-BRIEF-4.json` (`status=done`) — [`OPERATOR-BRIEF-4.json`](../handoffs/OPERATOR-BRIEF-4.json) |

Requirement 2 fails, so the card stops here. Writing a completion argument before the page exists would
be grading my own composition rather than the batch, and there is nothing to grade: `docs/HARNESS-MAP-V4.md`
is deliberately **not** created.

## What the grid state actually is (paths on disk)

- **0 cells completed, 1 attempted.** `RUN-A*` cell 1 (`pointer-stable` rep 1) exited **6** — runaway turns
  T3/T27 truncated at `--max-tokens 4096`; stop rule 7 fired. 27 rows billed, 3,192 of 3,219 remaining.
  Journal: [`orchestration/journals/RUN-A-STAR.jsonl`](../journals/RUN-A-STAR.jsonl).
- **Ledger baseline in force:** 1,128 spent / 3,192 remaining / cap 4,320, frozen `2026-10-26T19:04:18Z` —
  [`LEDGER-GRID-BASELINE-2.json`](../../experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json).
- **Board at refusal:** todo 24 · running 5 · done 372 · failed 105 · archived 345. Four cards besides this
  one are mid-flight (`HARNESS-PIN-GEN5`, `ERA-B-ANALYSIS-CONTRACT`, `VERDICT-SCOPE-STAMP`, `V-LEDGER-BASELINE`),
  and `RUN-A-STAR-2` has spent nothing.

## Why none of the six deliverables was produced

Every section the card asks for is defined **against live rounds and cells**: the stage map is priced per
experiment, the cost table wants one offline round and one live cell as median + range, the verdict-adoption
rate wants closures before and after `VERDICT-RITUAL`, and the one-paragraph answer wants three numbers.
With zero completed cells and no page, each would be a fabricated figure. The card's own HARD RULES forbid
that ("a figure you cannot re-derive is omitted, never estimated"), so the honest output is the refusal.

## What a successor needs (unchanged objective)

1. `RUN-A-STAR-2` (or its successor) finishes its cells and a graded analysis exists in `measure/`.
2. `orchestration/handoffs/OPERATOR-BRIEF-5.json` is written and settled.
3. `HARNESS-MAP-V4` is then re-carded verbatim — nothing about its objective has been satisfied by this run.

Machine record: [`experiments/ptr-engine/measure/HARNESS-MAP-V4.json`](../../experiments/ptr-engine/measure/HARNESS-MAP-V4.json).
