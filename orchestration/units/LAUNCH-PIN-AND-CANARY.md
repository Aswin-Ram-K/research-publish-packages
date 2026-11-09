# UNIT LAUNCH-PIN-AND-CANARY

**Purpose.** Make the launcher pinned by construction and the canary cover all four arms.
Offline unit: zero requests, no sockets, no live cell, `--dry-run` only.

**Write paths.** `experiments/ptr-engine/measure/HARNESS-PIN.json` (gen 4 added, 1-3 kept) ·
`experiments/ptr-engine/tools/run_a_star.py` · `tests/test_run_a_star_pin.py` (new) ·
`orchestration/units/LAUNCH-PIN-AND-CANARY.md` · `orchestration/handoffs/LAUNCH-PIN-AND-CANARY.json` ·
`orchestration/journals/LAUNCH-PIN-AND-CANARY.jsonl`. NOT edited: `cell.py`, `run_longrun.py`,
`analyze_stats.py`, fixtures, rows/grades, thresholds, `PARM-1*`, published pages.

## A · pin, by construction
1. Recomputed from `cell.py:334-349` over the current six inputs -> `fa6fd8cc519f5a2794b54fe5f215c808f781b136de657bdece7f5eb4bf37e8ac`.
   Six per-file digests quoted in the handoff and in gen 4 of `HARNESS-PIN.json`.
   Gen 4 frozen additively; gen 3 preserved byte-for-byte under `supersedes_pin_generation_3`
   (its nested gen 2, and gen 2's `c4541802` gen-1 record, remain).
   **cause**: `analyze_stats.py` 800c8f6c.. (82694 B, 18:55:52Z) -> 30b07d4d.. (84560 B) at
   19:14:14Z, five minutes after gen 3 froze at 19:09:18Z; card `LATENCY-DEDUPE-FIX`.
2. Wiring: `cell_argv` now appends `--expect-harness`, driven by `HARNESS_PIN` and checked
   against gen 4 by `pinned_digest()` (record/launcher disagreement is fatal).
3. Three states, real `cell.py --dry-run`:
   - stale gen 3 -> `rc 2`, "harness changed mid-cell ... REFUSED(2)", stage 2/7;
   - current gen 4 -> `rc 0`, G1 allow 1,142/4,320, G2 WOULD-REFUSE 720 s of 600 s, G3 allow n=12;
   - no digest -> `rc 0` (allowed). That path is no longer reachable from the launcher:
     `cell_argv` is the single argv builder for grid and canary, and always passes the flag.

## B · canary per arm
4. Before: `a.cell = a.cell or 1  # a canary is ONE arm, 12 turns` + the single-cell filter
   `if not a.cell or n == a.cell` -> 1 arm, 12 requests.
5. After: canary cells = first rep of each arm (1,4,7,9) -> 4 arms, `4 x 12 = 48` requests,
   declared on `DRY END ... canary_arms=4 canary_requests=48` and in the journal.
   `--cell` no longer narrows the canary (printed note). `cell.py` was not edited.
   Claim: `claim_mode_of("smoke")` = `{mode: smoke, claim: none, comparison_eligible: false}`
   for every arm; the analyser refuses each arm by name (`incomparable_claim <arm>: ...`).
6. One-arm consequence: with only pointer-stable gated, transcript-grow, transcript-compact and
   lease-reopen would reach the grid ungated; a degeneration of any of them at turn 3 (e.g.
   completion-ceiling blowup, evicted-transcript storm, or lease thrash) would have been paid for
   across 48-turn cells and only visible after the 1,016-request grid was spent.

**Known drift (not in write paths, reported)**: `tests/test_run_a_star_claim.py` pins the old
literal argv at `GRID_ARGV` (no `--expect-harness`), so 2 of its 8 cases now fail — expected,
because the wiring must change the argv. It needs a one-line follow-up card to add the flag
to `GRID_ARGV`; the card forbade editing it here.

**Verdict command.** `PYTHONPATH=src python3 -m pytest tests/test_run_a_star_pin.py -q` -> 8 passed.
