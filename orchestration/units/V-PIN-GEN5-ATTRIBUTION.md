# V-PIN-GEN5-ATTRIBUTION — unit card (reader)

**Purpose.** Independently certify harness pin generation 5 *before* 48 live requests are
spent against it, because this batch has twice accepted a self-issued pass
(`V-GATE-CHAIN-3` passed 6 assertions that asserted the surviving bypasses;
`V-SPAWN-DECLARE`'s `validate_refusal()` returned `ok=True` for a record with no `spawns`
key).

**Role.** Reader only. No edits to `measure/HARNESS-PIN.json`, `cell.py`,
`run_longrun.py`, `analyze_stats.py`, `grade_v5.py`, `tools/run_a_star.py`, any fixture,
threshold or published page. No re-pin, no canary re-run, no `ask_user_question`,
zero network, `--dry-run` only.

**Bound.** ≤20 tool calls; handoff within 8 calls of the verdict.

**Steps performed (in order).**

1. Recomputed the digest from `cell.py:334-349`'s stated recipe in own code — not by
   importing `cell.py`. `recomputed = 35ff41b7…`, `pinned = 35ff41b7…`,
   `files_counted = 6`, `match = true`.
2. Attribution against `supersedes_pin_generation_4`: two moves — `grade_v5.py`
   `056eb605… → 3d70ed1d…` owned by `GRADE-V5-T4-DECORATION` (done, exec succeeded),
   `run_longrun.py` `b2003038… → 30dfa9e9…` owned by `RUN-DRY-TURN-SCOPE` (done, exec
   succeeded). Zero unattributed rows. Four inputs byte-identical to gen 4.
3. Enforcement exercised twice on `--dry-run`: stale gen-4 `--expect-harness` → exit
   **2** at stage 2/7 naming the flag and the current digest (before any spawn); current
   digest → exit **0**. Launcher side probed: `pinned_digest()` raises `SystemExit`
   because it still checks `generation != 4` — fail-closed, no launcher cell can spawn.
4. `cell.py` sha256 `cf512f5f3bd075c46a2c7c508ce9b803a32d9ba1ceb44edf3c729ded6ce3ce18`,
   114 184 bytes, quoted beside the pin. The pin certifies the six files around the
   conductor, **not** `cell.py`.
5. Residuals named with owners; none repaired.

**Verdict:** `pin_attributable`.

**Write paths.** `experiments/ptr-engine/measure/V-PIN-GEN5.json`, `docs/V-PIN-GEN5.md`,
`orchestration/units/V-PIN-GEN5-ATTRIBUTION.md`,
`orchestration/handoffs/V-PIN-GEN5-ATTRIBUTION.json`,
`orchestration/journals/V-PIN-GEN5-ATTRIBUTION.jsonl`.
