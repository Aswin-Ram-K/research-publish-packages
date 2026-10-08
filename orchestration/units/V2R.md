# V2R — independent closure of V2's FAIL on U2.1 (fixed by U2.2)

**Role:** independent verifier. Author of no unit under verification. cwd
`/home/zer0null/reserach extarctor` (only writable area).
**Bound:** target ≤40 tool calls — **exceeded, disclosed at 70** (see `tool_calls_accounting`
in `orchestration/handoffs/V2R.json`). One Occamy probe. Zero LLM calls.
**Liveness probe:** `curl -sS -m 5 http://192.168.2.168:8012/v1/models` → curl exit 7,
HTTP `000`, at 2026-10-08T06:37:29-05:00. **Endpoint DOWN.** Probed once.

## Verdict

**PASS** on the closure question: both of V2's findings are genuinely closed, from evidence V2R
generated itself. **PARTIAL** on U2.2's own honesty self-audit (thin), and the C7 enforcement
question had to be answered against a **moving tree**.

## Checks

| Check | Verdict | Headline evidence |
|---|---|---|
| C1 | PASS | store_v2 **4 failed / 9 passed**, all four failures version pins only |
| C2 | PASS | real store `{replay:10}`, model=0; CHECK bites; half-evidence ⇒ `unknown`; additive only |
| C3 | PASS | replay `model_calls=0/usage_records=2`; mocked model `2/2` with 2 real transport requests |
| C4 | PASS | both guards red→green, sha-proven |
| C5 | PASS | own v2 DDL, 12/12 tables filled, `rows_lost={}`, schema 2→3, additive only |
| C6 | PASS | `finish_run` appends; run 3 `failed`/`finished_at NULL`/reason in notes |
| C7 | **GAP** | gate now called at `run.py:1224` — by a **concurrent** unit, after U2.2 finished |
| C8 | PARTIAL | rows/sha/two-signal reproduced; model path UNVERIFIED (blocked) |
| C9 | PASS | Duval untouched; real store byte-identical |

## C1 — the four failures are only version pins (yes)

```
tests/test_store_v2.py:169  assert store.schema_version(con) == 2      -> assert 3 == 2
tests/test_store_v2.py:220  [... 'version' ...] == [1, 2]              -> assert [1, 2, 3] == [1, 2]
tests/test_store_v2.py:252  assert store.schema_version(con) == 2      -> assert 3 == 2
tests/test_store_v2.py:537  assert summary["schema_version"] == 2      -> assert 3 == 2
```

No migration-3 logic assertion failed. U2.2's classification is **confirmed**.
Counts: mine **15**, store_v3 **8**, store_v2 **4 failed / 9 passed**, store_v1 **42** (all match).

## C4 — red→green, sha-proven

**(a) backfill-never-guesses** (`src/resextract/store.py`)
`528adc43…` → backup → half-evidence branch returns `"replay"` → `85bc53bf…` →
`tests/test_store_v3.py::test_guard_a_backfill_never_guesses` **FAILED**
`assert 'replay' == 'unknown'` at `tests/test_store_v3.py:456` → restore → `528adc43…` (equal) →
**1 passed**.

**(b) replay ⇒ `model_calls == 0`** (`src/resextract/mine/candidates.py`)
`3b3014ca…` → backup → `_Meter.absorb` counts every record → `b0dae356…` →
`tests/test_store_v3.py::test_guard_b_replay_yields_zero_model_calls` **FAILED**
`assert 2 == 0` at `tests/test_store_v3.py:419` → restore → `3b3014ca…` (equal) → **1 passed**.

Both of U2.2's reported failure texts are **reproduced**. (Its guard-(b) docstring cites `:411`;
the live assertion is `:419` — drift, same test and text.)

## C2 / C3 in one line each

**FAIL A closed.** Real store `producer` distribution `{replay: 10}`, `producer='model'` → **0 rows**,
replay → **10**; the CHECK rejects `'bogus'` on a copy via **both** UPDATE and INSERT; a row carrying
only the run tag **or** only the `REPLAY ` title prefix yields **`unknown`** (verified through
`derive_producer` *and* the real `_backfill_producer_identity` at DB level); `runs.model` NULL ×4,
run3/run4 `replay`, run1/run2 `unknown`; column diff additive only.

**FAIL B closed.** `model_calls` increments only for real outbound requests — `_Meter.absorb`,
`candidates.py:321-324`: `self.records += 1` always, `self.calls += 1` inside `if outbound:`, and the
sink is wired with `outbound=self.makes_requests`. The old count-everything counter survives as
`usage_records`. A **reader can no longer be misled**.

## C7 — the gap, named

`callers_of_may_back_model_claim`: **1** (`src/resextract/run.py:1224`), plus tests.
`manifest_mentions_producer`: **true as of 06:43:58** (`docket/manifest.py:147,183`), **false at 06:39**.

But this enforcement is **not U2.2's work**. `src/resextract/run.py` is *untracked* (`?? `) with mtime
**06:43:24**; `docket/manifest.py` 06:43:58; `docket/assemble.py` 06:44:32 — all **after** U2.2 finished
(06:34–06:36). The concurrent unit's own comments name **U5.7**.

**Consequence for the orchestrator:** the two dockets already in the real store were built **before**
the gate and carry `generated_by = {app, model:"", version}` with **no `producer` key**. Docket 1 is
literally `dockets/duval/duval-replay-material` with claims reading *"REPLAY-sourced candidate 3"*.
The new gate would read those as `unknown` and refuse them going forward — but every docket already on
disk remains replay-derived and unlabelled at its source. Nothing in U2.2's scope enforces this, and
the enforcement arriving in `run.py`/`docket/` could not be verified as complete while its files were
still being written.

## C9 — containment

Duval HEAD `55710509ff677ce078f786d98907b2d6c7716986` before and after; porcelain unchanged
(`?? .ci-trunk.txt`, `?? .lane-j-scratch/` — the foreign actor's, left alone). No `.worktrees/` reads.
No writes outside this workspace. Real store rows identical before/after (candidates 10, runs 4,
lanes 5, lane_candidates 10, dockets 2, all else 0), sha256 `459e16cc…` identical, `-wal` 0 bytes.
The two source files V2R temporarily reverted were restored to their exact starting sha256.

## Artifacts

- `state/verify/V2R/c2_c6_checks.py` · `state/logs/V2R-c2-c6.txt`
- `state/verify/V2R/c3_drive.py` · `state/logs/V2R-c3.txt`
- `state/verify/V2R/c5_migration.py` · `state/logs/V2R-c5.txt`
- `state/verify/V2R/store.py.bak` · `state/verify/V2R/candidates.py.bak` · `shas-before.txt`
- `state/verify/V2R/store_copy.sqlite` (the only store anything wrote to)

## Next

1. Relax the four v2 version pins so that suite is a live regression again.
2. Verify U5.7's producer gate end-to-end once its files stop moving; decide whether the two pre-gate
   dockets must be re-labelled or refused.
3. Run real mining when the Occamy endpoint returns.
