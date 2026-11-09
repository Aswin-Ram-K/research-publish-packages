# LAUNCH-PACKAGE-RECONCILE

**Status:** done · **Recorded:** 2026-10-26T19:10:02Z · **Bound:** 28 tool calls (used 18)

## Purpose
Make the launch package ONE consistent object, then prove it by re-running
`LAUNCH-PACKAGE-AUDIT`'s own eight checks. Offline: zero requests, no network, no live cell.

## What changed, and why
1. **Re-pinned to generation 3.** `measure/HARNESS-PIN.json` generation 3 records
   `harness_sha256 = 2b4d4808cf906582a378c47c340113022588284fc2b58640e83a95fc6bc23871` over the five `HARNESS_FILES` + fixture
   (cell.py:334-346 recipe). Generation 2 is preserved **byte-for-byte** under
   `supersedes_pin_generation_2` — nothing in it was edited.
   Baseline snapshot: `state/harness-baselines/2026-10-26T141100Z/` (manifest
   `01b1012f…`). The manifest's own `harness_sha256_of_HARNESS_FILES` is `bae1d87c…` because
   that tool excludes the fixture by its own recipe; the PIN recipe includes it.
   **Named delta:** `run_longrun.py` `0d581d1f…` → `b2003038…` (154,535 → 156,550 bytes), caused by
   `RUNNER-ROUNDS-48`: `TOOL_FETCH_ROUNDS_PER_ARM = 48` at `run_longrun.py:230` plus the real
   override `--fetch-rounds-per-arm` at `run_longrun.py:2857` (resolver `run_longrun.py:277`).
   Confirmed independently: `cell.py` stage 2/7 printed `harness_sha256=2b4d4808…` in this unit's probe.
2. **Budget settled by measurement.** Which stage reads `--budget`: **stage 3/7 budget**
   (`cell.py:353-395`), reached only on the live path — `cell.py --dry-run` returns at
   `cell.py:2009` *before* it, so a `--dry-run` can never exercise `--budget`. The stage runs the
   runner's own `--dry-run` and parses `would_send_total=`, then compares
   `ceil(would_send_total × 1.10)` to `--budget`.
   Measured, with a shim on `CELL_RUNNER_PATH` that delegates `--dry-run` to the real runner and
   refuses every live launch (exit 9), so nothing could be sent:
   - `--budget 67` → **exit 5 at stage 4/7 run**; stage 3/7 **ALLOWED**: `cell: 3/7 budget ok would_send_total=48 +10%=53 <= budget=67 (quota_remaining=3192 best-effort)`
   - `--budget 108` → **exit 5 at stage 4/7 run**; stage 3/7 **ALLOWED**: `cell: 3/7 budget ok would_send_total=48 +10%=53 <= budget=108 (quota_remaining=3192 best-effort)`
   `would_send_total` is **48, not 96** — the 48 fetch rounds are *not* priced into the runner's
   dry-run projection. `required = 53`, so **both** budgets pass.
   **One-sentence correction of `BUDGET-48-WIRE`'s claim:** the "refuses at exit 3 before any
   request" figure is **false today** — `--budget 67` is *allowed* at stage 3/7
   (`required 53 ≤ 67`) and the cell proceeds to stage 4/7, so the 48-turn tools-on cell is not
   refused by that gate at either 67 or 108.
   `docs/FETCH-BUDGET-48.md`'s historical text is untouched; a dated correction naming this card
   sits beneath it.
3. **The 1,016 price now has an artefact.** `measure/GRID-PARAMS.json` revision 2 (`schema
   consonance.grid-params/2`, `supersedes` naming this card, revision 1 preserved verbatim) states
   `964 tranche + 48 canary + 4 warm-ups = 1,016`, against remaining **3,192**, leaving **2,176**.
   The budget figure is recorded as **measured** (above), not assumed.
4. **Canary docs fixed to N=12** at `docs/TRANCHE-CANARY.md:23` and
   `docs/FETCH-BUDGET-48.md:166`; each keeps its original wording visible in a dated correction
   citing `CANARY-ERA-B-FIX`'s `era_b_gateable: true` (0 of 3 tools-on rows definitive at N=5,
   3 of 3 from N=12) and the gate `N=12, shape_ok, answer_verified ≥ 1, stop_signal_source=finish_reason`.
5. **GRID-SHAPE superseded by pointer only.** `measure/GRID-SHAPE.json` is **byte-unchanged**;
   `GRID-PARAMS` revision 2 `grid_shape_superseded_by_pointer` names **7** superseded fields and
   their replacement values. The 10 literal `--budget 67` and 10 literal
   `--fetch-followup-allowance 24` tokens therefore still read stale in that file *by design*.

## The eight checks (fresh run, 2026-10-26T19:10:02Z)
| gate | value | verdict |
|---|---|---|
| G1 pool | 48 (`run_longrun.py:230`, override `:2857`) | agree |
| G2 budget | 108 (command + `run_a_star.py:181`/`:280`); measured permissive | agree |
| G3 price | 1,016 = 964 + 48 + 4 | agree |
| G4 remaining | 3,192 → 2,176 | agree |
| G5 canary | N=12 in both docs; `canary_can_gate_era_b=true` | agree |
| G6 pin | gen 3 `2b4d4808…` == recomputed | agree |
| G7 baseline | `LEDGER-GRID-BASELINE-2` 3,192 | agree |
| G8 command | budget 108 / allowance 48 / `--expect-harness 2b4d4808…` | agree |

**ready_to_launch: true.** Contradiction table: **empty** — the eight fields that disagreed in
`LAUNCH-PACKAGE-AUDIT` (pin, price, remaining, budget, allowance, canary, runner constant, command)
now each resolve to one value in one authoritative artefact.

## Not touched
`cell.py`, `run_longrun.py`, `analyze_stats.py`, `run_a_star.py`, `GRID-SHAPE.json`, every row and
grade file, every threshold, every published analysis page.

## Side effect, disclosed
The stage-3 probe wrote four byproduct files into `measure/` (2 `*.gates.json`, `*.refusal.json`,
`*.claim.json`). They were this unit's own probe output, not evidence, and were **deleted**; the
follow-up runs were directed to `--out-dir state/harness-baselines/2026-10-26T141100Z/.probe/out`.
The probe shim lives at `state/harness-baselines/2026-10-26T141100Z/.probe/runner_shim.py`, inside a
declared write path.
