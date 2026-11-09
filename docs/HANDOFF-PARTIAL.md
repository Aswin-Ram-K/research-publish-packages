# HANDOFF-PARTIAL — making a partial handoff judgeable

Owner: `experiments/ptr-engine/tools/handoff_lint.py` (codes) · forward-only ledger:
`state/logs/handoff-partial-baseline.json`. Added by unit `HANDOFF-PARTIAL-SUBSTANCE`.

## The gap this closes

`HANDOFF-LINT` already guarded **done**-shaped handoffs (`E_STUB`, `E_DONE_NO_EVIDENCE`,
`E_DONE_NO_ARTIFACTS`). Partials were unguarded — and partial is the outcome the contract
encourages ("partial is a result"). Two settled records made that concrete:

- `V-STAMP-NEUTRAL` settled `overall: partial` with `evidence: null`; its two-line hint named a
  stale `DEFAULT_GRADER_SHA` pin and unstamped regrade output, and nothing in the handoff let a
  reader check either claim.
- `NEVER-ANSWERED-ROOT` settled `partial` after two tool calls with `blocker: "in progress"`, no
  table, no artefact — at read time indistinguishable from a delivered unit.

An empty partial and a delivered partial read identically. That is the defect these codes name.

## The three codes

| code | severity | fires when |
|---|---|---|
| `W_PARTIAL_NO_EVIDENCE` | warning | `status`/`overall` is `partial` and **no substance key** carries anything |
| `W_PARTIAL_NO_COMMAND` | warning | a partial **with** substance that carries no `commands`/`command` and no non-trivial `command_or_count` |
| `E_STATUS_WORD_CONTRADICTION` | error | `status`/`overall` says `done`/`pass` while **no substance key** is present |

Warnings because a partial is legitimate; the empty one is not. The error exists because
`done`+`pass` with nothing under it is how a false PASS enters the record.

## Substance is not one key name — this is the rule's spine

`evidence` is **not** the only place substance lives. The keys accepted are:

```
evidence, checks, measurements, findings, commands, command_or_count
```

A handoff passes when **any** of them is non-empty (`nonempty()` in the tool: non-blank strings,
non-empty lists/dicts-of-non-empty, true booleans, any number). A bare `counts` dict is
deliberately **not** substance: `{"counts": {"cells": 63}}` names a number without naming what
produced it.

Two measured counter-examples, which is why the rule is shaped this way:

- **`V-FIXTURE-V8`** (6,222 B, `status: done`, `overall: pass`) has **no `evidence` key at all**
  and is fully substantive — `checks` (12/12 truths re-derived, source pins, v7→v8 delta,
  NONE-by-construction proof), `measurements`, `findings`, `can_800_be_graded`,
  `not_reproduced`/`overstated`/`unverified`. A rule keyed on `evidence` would flag it. It is the
  negative control and must stay clean.
- A verifier verdict carries its substance under `checks` by shape (`VERIFIER_REQUIRED` mandates
  that key), so presence of the shape-mandated key alone proves nothing either — the *content*
  is what is tested.

**Do not re-narrow this to one key.** A lint code keyed on `evidence` alone produces false
positives on exactly the substantive handoffs the contract wants.

## Forward-only baseline

`state/logs/handoff-partial-baseline.json` freezes every hit measured at the moment the rule
landed. Exempt when the basename is a key in the file, when the handoff mtime is not newer than
`frozen_at`, or when it was written less than `grace_seconds` ago. Nothing was edited to satisfy
the rule and no evidence was filled in — the frozen entries are **recorded** hits, not excused
ones. `--partial-baseline-out` refuses to rewrite an existing baseline.

## Corpus at landing (1,050 handoffs)

| code | old | new | frozen |
|---|---|---|---|
| `W_PARTIAL_NO_EVIDENCE` | — | 15 | 15 |
| `W_PARTIAL_NO_COMMAND` | — | 103 | 103 |
| `E_STATUS_WORD_CONTRADICTION` | — | 3 (`R2-A3`, `R2-B2`, `R2-C`) | 3 |

Every pre-existing code counted identically before and after the change (`E_PARSE` 0, `E_SHAPE` 0,
`E_MISSING_KEY` 36, `E_ARTIFACT_ABSENT` 75, `E_DONE_NO_EVIDENCE` 4, `E_DONE_NO_ARTIFACTS` 3,
`E_STUB` 16, `E_JOURNAL_MISSING` 21, `W_JOURNAL_STALE` 7, `W_NO_COMMANDS` 187,
`W_VERSION_STALE` 21), proved by running the same tool with the new-code emission stubbed out at
the same instant and diffing per-file code sets.

## Red and green

Red (synthetic): `evidence: null` and nothing else → `W_PARTIAL_NO_EVIDENCE`;
`{"counts": {"cells": 63}}` → `W_PARTIAL_NO_COMMAND` (+ `W_PARTIAL_NO_EVIDENCE`);
`status: done` or `overall: pass` with nothing → `E_STATUS_WORD_CONTRADICTION`.

Green: `V-REASON-MIX` (partial, substantive, commands present) clean; `V-FIXTURE-V8`
(done+pass, no `evidence`, substance under `checks`/`measurements`) clean.

Suite: `experiments/ptr-engine/longrun/tests/test_handoff_partial.py` (12 tests, all passing).

## A finding the rule produced on the way in

Re-measured on disk at landing time, the two prompting cards no longer match their descriptions:

- `V-STAMP-NEUTRAL` has **no `evidence`** but **11 substantive `checks`** (sha256 pin, reverse
  diff, 20/20 regrade, mutation trials). It is *not* empty: it fails only `W_PARTIAL_NO_COMMAND`,
  because none of it can be re-run from the handoff.
- `NEVER-ANSWERED-ROOT` now carries `evidence.command_or_count` ("corpus located: 11 grade-v5
  docs, 8 primary, 7 rows-longrun-*.jsonl grids") plus two commands and a journal artifact, so
  it passes both new codes clean.

Flagging the second would mean ignoring its commands — the false positive this rule exists not to
produce. The measured result stands; the card's premise about it is stale.

## Usage

```
python3 experiments/ptr-engine/tools/handoff_lint.py orchestration/handoffs --summary
python3 experiments/ptr-engine/tools/handoff_lint.py orchestration/handoffs \
    --partial-baseline-out state/logs/handoff-partial-baseline.json   # once, refuses to overwrite
```
