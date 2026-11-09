# HARNESS-PIN-GEN5

**Status:** partial — every task delivered; the launcher constant (`run_a_star.py:51`) is out of this card's write scope and is named in the handoff's blocker. · **Journal:** `orchestration/journals/HARNESS-PIN-GEN5.jsonl` · **Handoff:** `orchestration/handoffs/HARNESS-PIN-GEN5.json`
**Mode:** automated, OFFLINE — 0 requests, 0 live cells, `cell.py --dry-run` only.

## One purpose

Regenerate `measure/HARNESS-PIN.json` as **generation 5** after two `HARNESS_FILES` moved, bring the
cached copy in `measure/GRID-PARAMS.json` to the same generation, ship a guard that reddens when any
artefact embeds a digest that is neither the pin's current value nor a *recorded predecessor in that
file's own supersedes slot*, and repair the runbook prose that still describes generation 3 as current.

## Preconditions (verified on disk before any write)

1. `orchestration/handoffs/BUDGET-STAGE-MAX-TURNS.json` — status `partial`; it declares `cell.py` +
   a test as write paths and states in `evidence.harness_digest_note` that **cell.py is not in its own
   `HARNESS_FILES` list**, so its change cannot move the digest. Read, not assumed.
2. `orchestration/handoffs/GRADE-V5-T4-DECORATION.json` — status `done`; `grader_sha256_before
   056eb605…` → `after 3d70ed1d…`; its `harness_pin` evidence names `a3fa2ee0…` (grader-only bump).
3. Digest recomputed from `cell.py`'s own recipe (`cell.py:126-136` HARNESS_FILES + fixture,
   `cell.py:329-341` sorted `name:sha256\n`) — six per-file shas + combined recorded in the handoff
   **before** the write.
4. Attribution: `grade_v5.py` moved under `GRADE-V5-T4-DECORATION`; `run_longrun.py` moved under
   `RUN-DRY-TURN-SCOPE` (both settled `done`). No unexplained change ⇒ no STOP. `cell.py` also moved
   (`BUDGET-STAGE-MAX-TURNS`) but is not a digest input.
5. `GRID-PARAMS-DIGEST-SUPERSEDE`'s work preserved: `read_the_pin_at` still points at
   `measure/HARNESS-PIN.json`, the gen-3 block stays verbatim, nothing is deleted.

## Hard bound

≤ 60 tool calls. STOP and report `partial` if the digest cannot be reproduced twice identically, if any
changed `HARNESS_FILES` entry has no settled card behind it, or if the guard cannot be shown red→green.

## Write paths (exactly)

`experiments/ptr-engine/measure/HARNESS-PIN.json` · `experiments/ptr-engine/measure/GRID-PARAMS.json` ·
`experiments/ptr-engine/tests/test_embedded_digests_match_pin.py` · `docs/GRID-PARAMS.md` ·
`docs/GRID-RUNBOOK.md` (digest lines + the `:82-95` passage) · this card ·
`orchestration/handoffs/HARNESS-PIN-GEN5.json` · `orchestration/journals/HARNESS-PIN-GEN5.jsonl`.

## Not touched

`cell.py`, `run_longrun.py`, `analyze_stats.py`, `grade_v5.py`, `run_a_star.py`, any fixture, any
threshold, `PARM-1*`, any published measurement page, the launch price (1,016), the ledger
(1,128 / 3,192), the canary wall (900).

## Known crossing (reported, not papered over)

`experiments/ptr-engine/tools/run_a_star.py:51` hard-codes `HARNESS_PIN = "fa6fd8cc…"` (generation 4)
and `run_a_star.py:64` refuses any pin record whose `generation` is not 4. After generation 5 is
recorded, `pinned_digest()` exits with `HARNESS-PIN record disagrees with the launcher`. This card may
not edit `run_a_star.py`; the advance is named in the handoff's `blocker`/`next_unit_hint`.
