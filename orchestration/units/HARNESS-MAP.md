# UNIT `HARNESS-MAP` — map the experiment harness before anyone changes it

Persisted by the unit itself (`AGENTS.md` unit contract rule 4). Card `500a9255-cd7c-400f-b591-f6a41c188c60`,
execution `964cfc68-aa8f-4809-bc19-ea78685fd6ff`, 2026-10-26. Tagged `automated`: no human answerer,
zero live requests, zero subagents.

## Purpose

Produce the factual map of how a cell is built, run, graded, verified and recorded, so that the next
change to the quality instrument is argued against measurements instead of against impressions. The
operator directive (message m00358) is the reason: stop patching the judge in isolation, learn the
harness the tests actually run on, then optimise the process of building tests and experiments as
part of the work.

## Deliverables (declared write paths, exactly)

| path | what it is |
|---|---|
| `docs/HARNESS-MAP.md` | the map: 18-row stage table with failure modes, the measured cell lifecycle, 14 ranked inefficiencies, the answer-contract specification with the diff a later card would make, the target pipeline, and the honest gap list |
| `orchestration/units/HARNESS-MAP.md` | this card |
| `orchestration/handoffs/HARNESS-MAP.json` | the machine-readable handoff (written `partial` first, updated as sections landed) |

## Bound and method

- **≤45 tool calls.** Used: **34** (all measurement commands, both artefact writes, and both board
  posts included).
- **Read-only over the whole repository.** Nothing but the three declared paths was written.
  Two commands were run that *would* write into the repo — `adapt_v4.py` and the runner's
  `--dry-run` — and both were redirected (`--manifest-dir /tmp/hm-manifests`, and `adapt_v4.py`
  refused its argumentless form so nothing was written at all). `det_verify.py --out /tmp/…`
  likewise.
- **No live request.** `grep` over every command run: no command touches `192.168.2.168:8012` or any
  HTTP endpoint. The runner was invoked with `--dry-run` only, which prints bodies and sends nothing
  (its own output: `0/3 differ`, `offline: zero requests`).
- **No subagents.** Every measurement is a local command.

## What was measured versus quoted

Measured by this unit (30 commands, wall-clocks in `docs/HARNESS-MAP.md` §Appendix):

- file counts (931 handoffs, 855 unit cards, 13 row files, 1095 rows);
- wall-clock for `--dry-run` (0.06 s), `grade_v3` (0.05 s), `grade_v4` (0.07 s), `det_verify`
  (0.05 s), the handoff guard test (3.08 s, 12 passed / 1 failed);
- per-request wall-clock derived from `latency_s` on 9 row files (v6: 367.3 s / 72 rows, mean 5.1 s,
  p95 11.4 s);
- the `ANSWER:` marker census per row file (v3 79/96 → v6 13/72);
- 9 of 13 declared checks emitted by `grade_v3`, 5 with a boolean decision;
- the negative result that no grader reads `fixture_sha256` (grep, then a live demonstration that
  grading config-C rows under the v4 fixture returns a clean `0/3` instead of a lineage error).

Quoted from existing handoffs rather than re-run: request counts already recorded
(`PROBE-CP3-V6` 72, `PROBE-CP3-V5` 72, `RUN-C-V2` 192, `RUN-STAGE1-LR01` 192, `RUN-V4-GRID` 96,
`V3-PILOT` 96, `PROBE-CP3-FETCH` 68+48, `RUN-INSTRUMENT-FIX` 42, `RUN-REASONING-POLICY` 26),
and the grader-fitness FN/FP rates from `measure/GRADER-FITNESS.md`.

## Headline result

**Baseline from a question to a trustworthy graded cell: 40 card rounds and 863 live requests**, in
which **31 of the 40 rounds spent zero requests** on process around **9 measurement rounds** — and the
last verifier is still `partial`, so no round has yet produced a cell that is both graded and
independently verified.

The three highest-cost inefficiencies:

1. **The answer shape is never constrained** (13 rounds, 386 requests rendered unreadable; the base
   fixture `LR-01.json` has no `system_prompt` at all, and marker compliance collapses from 82 % to
   18 % once the tool channel is on).
2. **Fixture re-authoring across four generations** (10 rounds, 16 runtime files, each generation
   invalidating the rows before it).
3. **36 of 92 checkpoint cells are answerless** (4 rounds, and it makes the 863 requests spent
   elsewhere un-interpretable: `checkpoint_accuracy` is computed over 3 of 12 declared checks).

**The single change to make first:** put a machine-checkable answer contract into the fixture and
the prompt, and parse it instead of prose — specified in `docs/HARNESS-MAP.md` §4, not implemented.

## Status

`partial` — not because a section is missing (all six are written) but because §6 lists nine things
this card could not determine (true card-round lower bound, current endpoint wall-clock, which checks
`V-DET-2` still holds open, and three un-timed stages). A restart should pick up at §6 item 3
(read `orchestration/handoffs/V-DET-2.json` body) and item 1 (a one-cell live timing), not at the
beginning.
