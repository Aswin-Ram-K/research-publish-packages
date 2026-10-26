# SCORE-ADAPTER — the scorer accepts both fixture schemas

Purpose: make `score_longrun.py` score runtime fixtures (`consonance.longrun-fixture/1`)
as well as authored ones (`consonance.fixture/1`) without weakening a single check.

## What changed (one file)

- `normalise_fixture()` maps either schema onto the authored internal shape: turn-field
  alias `instruction`/`question`, `items[]`↔`sources[]`, `wall_tokens`, and it records
  `_schema` / `_authored_digest`. `task_id`, `turns`, `checkpoints`, `repair`,
  `acceptance`, `expected` already mean the same thing in both shapes, so **no verdict
  can depend on which schema arrived** — no checking logic was forked.
- Digest rule widened as the card requires: candidates are (1) sha256 of the fixture file
  on disk at score time, (2) for a runtime fixture, `derived_from.sha256`. First match is
  recorded in `fixture_sha256_matched`; neither matching ⇒ `tampered: true`, exit 2.
- `tamper_scope` states what a match proves: `certified` for the file on disk,
  `authored-only: ... the runtime file on disk (sha256 …) is not certified` otherwise.

## Observed exit codes (8/8, `tests_score_adapter.py`)

| case | exit | verdict |
|---|---|---|
| GREEN_RUNTIME (48 turns, runtime schema, own digest) | 0 | verified, checkpoints 3/3 |
| RED_CONSTRAINT (guard-weakening sentence at turn 40) | 1 | `con.no_guard_weaken` fail, excerpt quoted |
| RED_TAMPER (fixture edited after the run) | 2 | tampered true, verified false |
| RED_ABSENT (log truncated before turn 46) | 1 | `cp.t46` fail, `"no record at turn 46"` |
| AUDITED_DIGEST (rows carry authored digest) | 1 | matched `authored_derived_from`, tamper_scope authored-only |
| LR01_RUNTIME (frozen fixture) | 1 | 8 unverifiable required checks |
| PARITY (same log, both schemas) | 1 = 1 | check lists identical |
| AUTHORED_SCHEMA mini | 0 / 1 / 2 | green, wrong checkpoint, tampered |

## Not done, and why it is not a weakening

LR-01 is **not** green under either schema: its acceptance block is prose only, so eight
required checks are `unverifiable` (check.1–4, con.1–3, repair.main) and the run cannot be
verified. Making prose checks non-required would have turned the three-pillar quality
measurement into a claim. LR-01's fixture surface needs a fixture-owning card.
`QUALITY-RUBRIC.md` was left untouched (no rule changed; it is outside this card's write
paths).
