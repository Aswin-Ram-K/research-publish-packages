# HANDOFF-RECOVERY — recover what the disk can prove, and only that

**Status:** done · **Bound:** ≤34 tool calls, zero inference requests · **Used:** see handoff `tool_calls`
**Write paths:** `orchestration/handoffs/recovered/*.json`, `experiments/ptr-engine/measure/HANDOFF-RECOVERY.json`,
`docs/HANDOFF-RECOVERY.md`, `orchestration/units/HANDOFF-RECOVERY.md`,
`orchestration/handoffs/HANDOFF-RECOVERY.json`, `orchestration/journals/HANDOFF-RECOVERY.jsonl`

## Purpose
`HANDOFF-LINT` found 16 `E_STUB` handoffs. A stub is not necessarily lost work: `PROBE-CP3-V6`
stayed a 1,175-byte stub while its cell had finished and written 72 rows. This unit enumerates the
stubs from the linter's own output, decides each from disk evidence alone, and writes an **additive**
recovered record where the disk can prove the unit ran.

## Method
1. Re-ran `handoff_lint.py orchestration/handoffs --summary` into
   `experiments/ptr-engine/measure/HANDOFF-LINT-rerun.json` (the `/tmp` write is outside the sandbox;
   the measure dir is a write path). 948 files scanned, 0 skipped mid-write, **16 `E_STUB`**, 75
   `E_ARTIFACT_ABSENT`, 40 `done`/`pass` claims with incomplete artifacts.
2. Enumerated all 16 (under the 20 cap → no truncation). Journalled the list **before** touching anything.
3. For each stub: unit card, declared write paths, `state/verify/<UNIT>/`, `state/logs/<UNIT>*`,
   `state/debris/<UNIT>/`, a mtime-window sweep, and a repo-wide grep for the unit name.
4. Classified into exactly one of recoverable / unrecoverable / not-a-stub.
5. Wrote `orchestration/handoffs/recovered/<UNIT>.json` only where artifacts were attributable;
   stubs left byte-for-byte intact.
6. Dogfooded the linter on every written file.

## Log
- Linter re-run: 16 stubs (8 unit-shaped, 6 verifier-shaped below 1 KB, 2 large bodies).
- Recoverable **8**, unrecoverable **7**, not-a-stub **1**.
- **Linter gap found:** no `recovered` status in `handoff_lint.py:167-194` — a `status:"recovered"`
  file is never held to `E_DONE_NO_EVIDENCE`/`E_DONE_NO_ARTIFACTS`. Reported, linter not edited.

## Bound / stop condition
If a stub's artifacts could not be attributed, it was classified rather than reconstructed. No number
in any recovered record comes from prose: sizes, mtimes and quoted lines were read from disk at write time.
