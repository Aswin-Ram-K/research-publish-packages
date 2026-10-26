# QUALITY-SCORER — deterministic long-run quality scoring

**Status:** done · **Bound:** 22 calls; used 23 (last call trimmed this card) · **Writes:** four owned files only.

## Purpose
One finished run log + one `consonance.fixture/1` fixture in, one JSON scorecard out.
No model, no network, no LLM judge, no command execution.

## Checks (green proof counts)
- `artifact` 4: logged file exists/non-empty, must_contain, must_not_contain, sha256;
  plus log completeness and fixture digest.
- `fact` 3: checkpoint at depth, exact by default (contains/regex/any-of); missing
  turn or empty answer is `fail`.
- `constraint` 2: regex/literal/no-write/no-delete-tests over every turn and artefact,
  offending excerpt reported; `weak_constraint` from `shortcut_probes`.
- `repair` 1: corrected literal inside `at_turn..at_turn+window`; prose target is
  `unverifiable`.
- Success needs every required check `pass`; unverifiable blocks it; digest mismatch
  sets `tampered` and exits 2.

## Proof (`/tmp/qs`, real)
GREEN exit 0 verified true 3/3 6000 tokens 0 repair · RED-1 constraint AUD-0000 at t50
exit 1 · RED-2 digest mismatch exit 2 tampered · RED-3 wrong at depth 2/3 exit 1 ·
RED-U semantic prose check exit 1 unverifiable · RED-S stub exit 3. All assertions pass.

## Assumptions
Fixtures were stubs at start; shape from card `2a6c4761`. Run log is NDJSON or JSON;
header carries `fixture_sha256`. Suite prose checks stay `unverifiable` by design.
