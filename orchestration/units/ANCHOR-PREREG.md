# UNIT ANCHOR-PREREG — design-only (frozen rule R2, zero requests)

**Status:** done (self-reported). **Bound:** ≤25 tool calls, zero network requests,
no grading run. **Actual:** 20 tool calls, 0 requests, 0 re-grades.

## Objective

The §4 anchor rule (`grade_v3.py:178-191`: *the `^ANSWER:` marker must contain
**every** anchor derived from `expected`*) rejects substantively correct answers on
English connectives. Measured twice, independently:

- `measure/rows-longrun-v6-tools.grade-v3.json`, `arms.pointer-stable.checks[2]`
  (`cp.2.t46`): `reason=refused_while_knowable`, `detail="marker dropped anchors;
  missing raising"` — the arm's answer named the right call, right kwargs, right
  module; it omitted the prose word `raising` from "before re-raising".
- `measure/rows-longrun-c-2026-10-26.jsonl:142` / `...grade-v3.json`:
  `missing_anchor:raising`, `"missing 1/9 anchors: raising"`.

This unit freezes a repair **without applying it**: no fixture, grader, row or
grade file was touched, and no arm is re-scored.

## What was produced

| artefact | role |
|---|---|
| `experiments/ptr-engine/longrun/ANCHOR-PREREG.md` | frozen normative R2 text, non-goals, Task-1 census table, Task-3 probe record, Task-4 counts, sha256 provenance |
| `experiments/ptr-engine/tools/anchor_prereg_check.py` | offline checker: recomputes the census, compares it to the recorded table, re-runs both probes, recounts Task 4 |
| `orchestration/handoffs/ANCHOR-PREREG.json` | unit handoff |

## R2 (frozen 2026-10-26T13:29:21Z)

> A checkpoint's `^ANSWER:` marker must contain every anchor token classified
> **CODE-SYMBOL** or **NUMBER**; tokens classified **PROSE-CONNECTOR** are
> informational and not required. `required_anchors` is derived from the fixture's
> `expected` string plus the cited source file — never hand-written.

Classes are operational, recomputed by the checker with `tokenize`:
CODE-SYMBOL = token occurs in the cited file outside any string/comment;
NUMBER = numeric expected value, with the establishing `file:line`;
PROSE-CONNECTOR = no code occurrence (only inside a docstring/comment, or absent).

**Amendment recorded (the card's premise was wrong):** `raising` *does* occur in the
cited source — `resolve.py:67`, inside the docstring `"""Record the refusal before
re-raising. …"""` — so "does not appear in the cited source" cannot be the test.
The context test is strictly narrower than absence, so it cannot smuggle a code
symbol out of the required set.

## Census (Task 1)

11 cells over the v4 fixture; `LR-01.v4.json` and `LR-01.v4.tools2.json` carry
**identical** `checkpoints` arrays (tools2 adds only `tools_channel`):

- 2 NUMBER — `cp.0.t12` = 64 (`resolve.py:39`), `cp.1.t24` = 31 (`errors.py:15-247`,
  31 `^class Ptr` definitions);
- 8 CODE-SYMBOL on `cp.2.t46` — ledger, record, refusal, scope, serialized, text,
  code, error;
- **1 PROSE-CONNECTOR** — `raising` on `cp.2.t46` (`resolve.py:67`, docstring only).

## Two-sided proof (Task 3) — recorded, exit 0

| probe | R1 | R2 |
|---|---|---|
| A: real V6 cp.2.t46 answer (content sha short `ecdb3fc9d9f0`) | REJECT `missing_anchor:raising` | **ACCEPT** `ok` |
| B: same sentence, `record_refusal` → `write_audit` | REJECT | **REJECT** `missing_anchor:record` |
| C: `scope=` → `grant=` | REJECT | **REJECT** `missing_anchor:scope` |

## Task 4 — would-flip counts (no re-grade, no accuracy number)

**≤3 of 39** checkpoint arm-checks, all on the one checkpoint `cp.2.t46`, all on the
one prose anchor `raising`:

- `measure/rows-longrun-c-2026-10-26.grade-v3.json` — ≤2 of 12 (`pointer-stable`,
  `transcript-grow`; both `cp.2.t46` `missing_anchor:raising`, "missing 1/9")
- `measure/rows-longrun-v6-tools.grade-v3.json` — ≤1 of 3 (`pointer-stable`
  `cp.2.t46` `refused_while_knowable`, "missing raising")
- v3 / v3-final / v4 / v4-tools / v5-tools grids — ≤0 (their cp.2 failures miss 6 or
  9 code anchors, or fail as `marker_missing`; R2 cannot rescue those)

## Kill conditions honoured

- No edit to any fixture, `check`/`checkpoint`/`marker`/`expected` field,
  `grade_v3.py`, `grade_v2.py`, `score_longrun.py`, `analyze_longrun.py`, or any
  row/grade file (write paths above are the only files created).
- No re-grade, no accuracy percentage, no live request, no endpoint probe.
- R2 is derivable from source files alone; probe B/C prove it is not a blanket pass.

## Next unit hint

Implement R2 in a **new** grader version (e.g. `grade_v4.py`) under its own
pre-registration, then re-grade the 39 arm-checks and report the delta against
`ANCHOR-PREREG.md` §6 — do not edit `grade_v3.py` in place, or the v6 record stops
being reproducible.
