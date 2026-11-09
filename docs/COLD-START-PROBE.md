# COLD-START-PROBE — what a fresh session can reconstruct from the record alone

Unit `COLD-START-PROBE`, 2026-10-26. 0 requests, 0 spawns, no dispatch, no repair. `NOT IN THE RECORD` = silent.

## 1. Objective and its verdict word
Minimise **p95 TTFT** and **tokens-to-verified-success** over long runs at equal-or-better verified quality on
`occamy-1.0`/SGLang `:8012` — "not to confine the space but to use the space better".
`source:` `orchestration/STATUS.md:380-384`; board #437/#438.
**Verdict word for the thesis: none exists** — only a batch aggregate, 134 rows: PASS 15 · FAIL 11 · partial 34 ·
author-report 73 · pending 1. `source:` `orchestration/VERDICTS.md:4024-4028`.
**Not adjudicable:** H1 — per-cell shape is 48 turns → n=48 < 60 (G3, exit 12, `docs/GATE-CHAIN.md` §5), pooled
n=144/96 clears n but is refused by G2 (8,640/5,760 s vs 2,880 s); `source:`
`orchestration/handoffs/TRANCH1-DRYRUN.json`. H3 — below 8 decidable of 12 checkpoints; `source:`
`docs/PARM-1-ERRATA.md:154`.

## 2. The spend
**1,101 used of a 4,320 cap; 3,219 remaining.** `source:` `experiments/ptr-engine/measure/REQUEST-LEDGER.json` —
`requests_raw` 1101, `remaining_raw` 3219, `requests` 1101, `remaining` 3219; cap/spent/remaining also in its
`budget` object as cited by `docs/PRICE-REPLICATION.md:32-35`.
**De-duplicated figure exists and is NOT deducted:** `requests_deduplicated` 1071, `remaining_deduplicated` 3249,
`duplicate_excess` 30, `deduction_rule_sound` false, `deduction.applied` false (the rule hashes assistant content,
not the request). Retired pairings: `WI-001` (≈466), `WI-002` (1,071 / 3,249).

## 3. The three holds
**(a) 660-request tranche — a gate pincer.** G3 refuses H1 at n=48 for every 48-turn cell; the pooled shape passes
G3 and is refused by G2. `source:` `orchestration/handoffs/TRANCH1-DRYRUN.json` (`g3_refusal_verbatim`,
`pooled_probes`). Carrier card `RUN-A*` `ad214412-c39c-4a47-afb1-2be328e03b1e`; the launch decision is card-level;
**the clearing card's id is NOT IN THE RECORD.**
**(b) a live cell through the conductor — the spawn certificate.** `V-SPAWN-ATTACK-2` partial: "gate precondition …
NOT fully met on this tree" — the record is not tree-bound (**D5**) and `cell.py`'s refusal document drops
`instrumentation` (**D6**); D2/D3/D4 fixed by `SPAWN-RECORD-BIND`. `source:`
`orchestration/handoffs/V-SPAWN-ATTACK-2.json` (`gate_precondition`), `docs/GATE-CHAIN.md` §11. The clearing card is
described in `SPAWN-RECORD-BIND.next_unit_hint` but **does not exist — NOT IN THE RECORD.**
**(c) publication — the gate precondition, not prose.** `source:` `orchestration/STATUS.md:399-405`: link 1 not
discharged — `VERDICT-DISPUTE` found the closure PASS rested on 26 assertions, **6 encoding the bypass as their pass
condition**, card `overall` fail (`WI-008`); link 2 `V-STAMP-NEUTRAL` partial; link 3 v8 provenance; plus 3
`[CITATION NEEDED — verify]` markers needing a unit with network. Clearing cards unnamed — **NOT IN THE RECORD.**

## 4. Withdrawn numbers and how to check a figure
**15 entries, `WI-001`…`WI-015`** — withdrawn 9 (`001,004,005,006,009,010,011,012,013`), superseded 6
(`002,003,007,008,014,015`); `WI-004` has **no replacement**; `002/004/005` carry a recorded discrepancy. Examples:
`WI-001` "≈466 of 4,320 used"; `WI-002` "1,071 / 3,249"; `WI-006` "217k at turn 48"; `WI-008` "the gate chain has no
surviving hole"; `WI-013` "0.85x/turn, ~620k". `source:` `experiments/ptr-engine/measure/WITHDRAWN.json`; paste at
`orchestration/VERDICTS.md:4181-4205`.
**Check:** `python3 experiments/ptr-engine/tools/withdrawn_index.py --check <file>` — **exit 1** if a withdrawn claim
is quoted without its correction, **0** if clean; `--self-test` opens every `decided_by` path.
`source:` `WITHDRAWN.json.how_to_use`; `experiments/ptr-engine/tools/withdrawn_index.py:129`.

## 5. The next dispatchable card
**None is dispatchable.** Next in queue: `RUN-A*`, card **`ad214412-c39c-4a47-afb1-2be328e03b1e`**, priced at
"**4 arms, pair at 3 reps, context at 2 reps = 480 turns / 660 requests** (10 cells of 48 turns; 2,559 remain)"
(`docs/PRICE-REPLICATION.md:170`), while its own text encodes "4 arms × 48 turns × 3 reps = 12 cells / ~792
requests": quoted — "its title, description, hard cap (900) and `conditional-launch` tags all encode '4 arms × 48
turns × 3 reps = 12 cells / ~792 requests'" (`docs/PRICE-REPLICATION.md:219-221`). Preconditions: G1 allows
(1,101 + 48 + 5 = 1,154; marginal 53/cell), G2 allows at exactly 2,880 s, **G3 refuses, exit 12**.
`source:` `orchestration/handoffs/TRANCH1-DRYRUN.json`.

## 6. Frozen thresholds that may never be lowered
48 turns per arm (`N = 48`); reps ≥ 2; the four-arm clause (same grid, identical `fixture_sha256` and reasoning
policy); `TAIL_MIN = 3`; p95 minimum n = 60; H3 unadjudicable below 8 of 12; the 2/12 margin; McNemar `b+c ≥ 6` at
p<0.05; the 180 s live turn wall. The 100 ms gate is a *scheduling* predicate, never an adjudication threshold.
`source:` `docs/PREREG-ARM-RUN.md` (:37, :113, :137, :142, :150-152); `docs/PARM-1-ERRATA.md:223-230`
(`thresholds_unchanged`); `docs/GATE-CHAIN.md` §5; `docs/EXIT-CODES.md` code 12; `docs/PRICE-REPLICATION.md` §4, §8.

## 7. A path named in the record that does not exist
**`docs/BUDGET-SCHEDULE.md`** — cited at `docs/PRICE-REPLICATION.md:222`, in `price-replication.json` (:35, :39, :115, :119, :393) and in `handoffs/PRICE-REPLICATION.json:27`. **It does not exist**; the artefact is `experiments/ptr-engine/measure/BUDGET-SCHEDULE.md`. Reported, **not repaired**. (`docs/PARM-1-ERRATA.json` is also absent but is cited only as a snippet.)

## 8. What a verdict row is
A row of `{command, exitCode, sha}` recorded for one card via `orchestration_verdict`; it proves **one command exited
with the recorded status against a named commit — nothing more** (`orchestration/VERDICTS.md:4216-4219`).
**Why most closed cards lack one:** of 134 rows **1 is complete**, 11 lack `sha`, 64 lack `exit` and `sha`, 58 lack
all three (`VERDICTS.md:4166-4172`) — rows are machine-extracted from handoffs and most handoffs recorded a prose
outcome. **When missing:** the row is "a report, not a verdict — the gate never saw it" (`VERDICTS.md:4230-4233`);
`experiments/ptr-engine/longrun/tests/test_verdict_ritual.py` fails on any *new* closure settled with no verdict row
(`orchestration/handoffs/WIRE-TREE-FREEZE-INTO-VERDICTS.json` `known_gap_observed`); a settle with nothing recorded
derives `no-verdict`.

## Record age and one reading defect
`VERDICTS.md` and `STATUS.md` mtime **2026-10-26 12:34:22 -05:00** (one write); board **397 replies**, newest seq retrieved **#971**.
`orchestration_board read` with `limit`/`since` returns from the **beginning** of the thread and truncates, so "the newest 40 replies" cannot be read as instructed; answers 3 and 5 come from handoffs and docs.
