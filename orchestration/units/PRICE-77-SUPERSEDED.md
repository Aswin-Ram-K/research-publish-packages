# UNIT `PRICE-77-SUPERSEDED`

**Status:** done · **Bound:** 16 tool calls (used 9) · **Offline:** zero requests.
**Write paths:** `docs/PRICE-REPLICATION.md` · `orchestration/units/PRICE-77-SUPERSEDED.md` ·
`orchestration/handoffs/PRICE-77-SUPERSEDED.json` · `orchestration/journals/PRICE-77-SUPERSEDED.jsonl`.

## Why
`COLD-START-SCORE` (`46b629dd`) marked probe item 5 **WRONG**: it recycled `PRICE-REPLICATION §7`'s
description of the `RUN-A*` card *before* the board edit, asserted the card still encodes 792 requests /
12 cells / cap 900, and called the price contradictory. The card encodes **660 requests / 10 cells**; 792
is the superseded figure. A later reader of §7 would reproduce the same error, so §7 is marked.

## What was done
Appended (never deleted, never re-derived) a dated supersession block directly after §7's item 1
(`docs/PRICE-REPLICATION.md:223-247`), quoting the card from `task_board_get` rather than recomputing any
price. No other number in the document was changed; §5's 660 figure and §7's blockquote are untouched.

## Evidence
- `sha256` before `3a2271c7721e78574594d447c8c985e64d543ec8683cc6b8438cd5e7949aeb17`, 17,661 bytes
- `sha256` after  `36965790d7299d67c4f5e477ab3c51a06aad46e69446effeb30ea8a43b140c52`, 19,857 bytes (+2,196)
- `python3 experiments/ptr-engine/tools/path_refs.py --check` → `path-refs: 1057 known (baselined), 0 new`, exit **0**
- `python3 experiments/ptr-engine/tools/withdrawn_index.py --check docs/PRICE-REPLICATION.md` → `CLEAN ... (15 entries screened, window=400)`, exit **0**
- `git diff` is empty for this file because it is untracked (`?? docs/PRICE-REPLICATION.md`); the diff is the block below, by line range.

## The appended block, verbatim
```
   **SUPERSEDED 2026-10-26 (board #960, restated #988).** The sentence above is this §7's description of
   the card's **pre-#960** text, and it must not be reproduced as current. What §7 described was **792
   requests / 12 cells / cap 900**: A\*'s price on the frozen 4-arm × 48-turn × 3-rep grid — still correctly
   priced as 576 turns / **792** requests / 2,427 remaining for *that shape* in
   `experiments/ptr-engine/measure/BUDGET-SCHEDULE.md` §2 — plus a hard brake of 900.

   What the card says **now**, quoted from `task_board_get ad214412-c39c-4a47-afb1-2be328e03b1e`:
   - **title** — "tranche 1 PAIR-3+CTX-2 (pair 3 reps, context arms 2 reps) = **10 cells / 480 turns /
     ≈660 requests**";
   - **description** — "ten cells, 480 turns, ≈660 requests"; booked at `--request-allocation ~67` per
     cell with the ledger cap left at its artefact value **4,320**, not 900 (the board's CAP CORRECTION,
     #975: "Hard brake: cap=900" was the card author's own error and is superseded);
   - **preconditions as currently posted** — (1) `WIRE-GATES` PASS, read `docs/GATE-CHAIN.md`;
     (2) gate-refusal semantics: PASS verdict rows from **both** `SPAWN-RECORD-BIND` and `SPAWN-TREE-BIND`
     (`D5`/`D6` now closed), a refusal record covering all of {2,3,4,8,12} and carrying `cell_sha256`,
     `spawn_record_sha256`, `argv` and `tree_sha`, the first two matching the files on disk at launch;
     (3) `WIRE-CAP-GATE`, the brake as prevention under the 4,320 cap; (4) the v8 fixture
     `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json`, whose four treatments must fire by T48
     (grow T21 · compact T21 · lease T23 · pointer T2) at `wall_tokens 10616`, never the top-level 3838;
     (5) 12 loadable checkpoint ids (`NUM 5 · CALL 4 · NONE 3`); (6) `EXIT-CODE-TABLE`; (7) the request
     ledger's `remaining ≥ 900` before cell 1 — with the six-handoff pre-launch tag alongside.

   The one sentence a reader needs:

   > A cap of 900 is the cumulative-spend brake, not the run's size: G1 compares cumulative `spent` (1,101 already spent + 48 turns + 5 allowance) against `cap − reserve`, so cap 900 would refuse before spending anything.
```

## Answer for the record
**No** — a reader of §7 can no longer conclude the card is 792 requests / 12 cells: the supersession line,
the quoted title/description and the cap sentence stand between the old sentence and that conclusion.
