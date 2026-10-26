# Q0-ANSWER-DEGENERACY — unit card (copy)

**Unit:** `Q0-ANSWER-DEGENERACY` · **Lane:** OFFLINE, ZERO LIVE REQUESTS · **Date:** 2026-10-26
**Status:** done · **Live requests spent:** 0 · **Tool calls used:** 20 of 40 bound

## Why this card exists

`RUN-C-V2` spent 192 live requests on the config-C grid (4 arms × 48 turns, N=48, occamy-1.0 at
`http://192.168.2.168:8012`). Every arm scored **0/3** checkpoints (`cp.t12`, `cp.t24`, `cp.t46`), so
`tokens_to_verified_success` is `null` and the pre-registered rule resolves **UNDECIDABLE**. Latency did
separate (p95 ms: transcript-grow 838.85, transcript-compact 224.08, pointer-stable 356.12,
lease-reopen 201.78).

Separately `PROBE-CP3-V5` (v4 fixture, tools on) scored 0/3 while its tools-off control scored **1/3** —
a checkpoint has been graded correct exactly once in this project, on v4, tools off. Since
`QUALITY-POSITIVE-CONTROL`/`V3-PILOT` established the fixture is answerable and the grader accepted, 0/3
is either an instrument defect, an instruction defect, or a real arm effect. **Nobody had separated
those three.** That was this card.

## Objective

Determine from the recorded rows alone *why* the checkpoints score zero, and whether 0/3 licenses any
statement about arm quality.

## Deliverables (five, in order)

1. Per arm × per checkpoint-turn classification of every row as NO ANSWER TEXT / ANSWERED WITHOUT THE
   MARKER / MALFORMED MARKER / MARKER PRESENT AND ACCEPTED, with ≥200-char quotes and `file:line`
   identity. → `ANSWER-DEGENERACY.md` §1
2. Whether the checkpoint turn ever asks for the marker, with the fixture's verbatim checkpoint
   instruction and the provenance of the grader's `^ANSWER:` rule. → §2
3. The control diff: passing CP1 row vs failing CP3 row, same arm, mechanically named. → §3
4. Ranked causes, each with cheapest falsifier, offline feasibility, and price in live requests. → §4
5. What 0/3 licenses, against `frozen_rule_outcome` clauses (i)/(ii)/(iii). → §5

## Acceptance

`experiments/ptr-engine/tools/answer_degeneracy_check.py` — stdlib, offline, idempotent, no
`requests`/`httpx`; recomputes the 12-cell table and exits 0 iff it equals
`orchestration/handoffs/Q0-ANSWER-DEGENERACY.json` `evidence.table`, else 1 with differing cells.

## Inputs read (never edited)

- `experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl` (192 rows) + `.analysis.txt` +
  `.grade-v3.json`
- `experiments/ptr-engine/measure/rows-longrun-v4-2026-10-26.jsonl` + `.grade-v3.json` + `.score.json`
- `experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.jsonl` + `.grade-v3.json`
- `experiments/ptr-engine/measure/rows-longrun-v5-tools.jsonl` + `.grade-v3.json`
- `experiments/ptr-engine/longrun/tasks-v2/runtime-v2/LR-01.v2.json` (sha256 `0a07db1b…`),
  `…/tasks-v4/runtime-v4/LR-01.v4.json` (sha256 `5a5f8c4b…`)
- `experiments/ptr-engine/longrun/grade_v3.py`, `GRADER-V3.md`, `run_longrun.py` (read-only)
- `experiments/ptr-engine/ptr_engine/{resolve.py,errors.py}` (read-only, ground truth)
- `orchestration/handoffs/RUN-C-V2.json` (`frozen_rule_outcome`)
- `experiments/ptr-engine/longrun/grade_v3.py`, `score_longrun.py`, `analyze_longrun.py`

## Hard bound

40 tool calls; **0 live requests**. Used 20. No network call of any kind was made.

## Forbidden (respected)

No edit to any fixture, checkpoint, marker rule, grader, `run_longrun.py`, or row file. The grid was not
re-scored as new evidence; verdicts are cited from the existing `.grade-v3.json`/`.score.json`.

## Write paths (exactly these four)

- `experiments/ptr-engine/measure/ANSWER-DEGENERACY.md`
- `experiments/ptr-engine/tools/answer_degeneracy_check.py`
- `orchestration/units/Q0-ANSWER-DEGENERACY.md` (this file)
- `orchestration/handoffs/Q0-ANSWER-DEGENERACY.json`

## Result in one line

0/3 is a **fixture/instruction artefact**: `LR-01.v2.json` pins `resolve.py#L66-L110` (line 39's
`DEFAULT_MAX_REFS = 64` outside) and `errors.py#L114-L126` (3 of 31 classes), so cp.t12 and cp.t24 had no
derivable answer, and the `ANSWER:` marker was never in play (`answer_marker` absent →
`marker_required = False` → `marker_lines = 0`); all 12 cells are `NO_MARKER`. Full reasoning and the
v2→v4 item diff that proves the repair: `ANSWER-DEGENERACY.md`.
