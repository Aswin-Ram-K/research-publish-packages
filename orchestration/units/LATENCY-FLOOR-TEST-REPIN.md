# UNIT `LATENCY-FLOOR-TEST-REPIN`

**Purpose.** Re-pin `experiments/ptr-engine/longrun/tests/test_latency_floor_policy.py` to the
current published artefact without weakening the policy it tests. Offline, one test file.

## 1. The failure, verbatim

`experiments/ptr-engine/longrun/tests/test_latency_floor_policy.py:148`

```
assert p["n"] == NEW_N[gid] == c["ttft_used"], (gid, p, c.get("ttft_used"))
AssertionError: ('G8', {'n': 47, 'refused': 'refusing p95 at n=47: the 95% order-statistic span is ranks 42-47 (p89.4-p100.0) and n*(1-q)=2.4 < 3; minimum n for p95 is 60', 'stats': {}}, 47)
```

(handoff `TURN-CENSUS-60` quoted the earlier `n=45` form: `('G8', {'n': 45, 'refused': 'refusing p95 at n=45 ...'})`.)

Current `experiments/ptr-engine/measure/LATENCY-REPORT.json`:

| cell | n_raw | n_dedup | n_turn | n_turn_dedup | ttft_used | p95 |
|---|---|---|---|---|---|---|
| G8/pointer-stable | 72 | 70 | 48 | 48 | 47 | `{"n": 47, "refused": "refusing p95 at n=47: ... minimum n for p95 is 60", "stats": {}}` |
| G9/pointer-stable | 72 | 61 | 48 | 48 | 48 | `{"n": 48, "refused": "refusing p95 at n=48: ... minimum n for p95 is 60", "stats": {}}` |

`p95_inventory.cells_with_p95 = 0`, `arms_with_a_p95 = []`; 24 of 24 cells refuse.

## 2. Why the numbers moved

A **de-duplication change**, not truncation: `orchestration/handoffs/LATENCY-DEDUPE-FIX.json`
records the field move verbatim — `"report_numbers": "G8 n_turn_dedup 46->48, ttft_used 45->47 ...
G9 37->48, 37->48"` — so the statistic population followed the turn de-dup, while `n_dedup`
stayed `70/61/51`. (`LATENCY-REDERIVE-TRUNCATED` had earlier moved it to 30/45/37 and added
`truncated-turns/1`; the test's `NEW_N = {"G8": 45, "G9": 37}` was literally true of that artefact
and stale one card later.)

## 3. What the test now asserts

- **Floor, both directions, artefact-derived** (`check_p95_pinned`): for every cell, `p95.n` must
  equal the artefact's own `ttft_used`; a **point** is allowed only if that count `>= 60` (and
  `lo`/`hi` present and the both-count gate publishes); otherwise a **refusal** is required whose
  text names `minimum n for p95 is 60`; a refusal at `n >= 60` is raised as a **CONTRADICTION**.
- **Synthetic fixture** (`case_g_synthetic_floor`): `quantile_ci` produces a p95 point at n=65 with
  `lo <= point <= hi`, and raises at n=59, 45 and 21 naming the floor — the floor is tested on data
  independent of the artefact, not merely observed.
- `case_e`/`case_f` re-pinned to the artefact's own arithmetic (`total == bitexact + moved`,
  inventory counts re-derived from `report["cells"]`), so no per-turn literal remains in the file.

## 4. Mutation proofs

(a) analyser copy in `/tmp` with the `n*(1-q) < TAIL_MIN` clause removed:

```
AssertionError: the analyser produced a p95 at n=59, below the floor 60
```

(b) report copy in `/tmp` with G8 `p95.n = ttft_used = 65` while still carrying a refusal:

```
AssertionError: G8: CONTRADICTION - n=65 clears the floor 60 but the cell carries a refusal instead of a p95: {'n': 65, 'refused': 'refusing p95 at n=47: ...', 'stats': {}}
```

## 5. Suite counts

- `python3 experiments/ptr-engine/longrun/tests/test_latency_floor_policy.py` — **7 cases PASS,
  exit 0** (a,b,c,d,e,f,g).
- Regression: `PYTHONPATH=src:. pytest -q tests/test_turn_dedup.py tests/test_grid_cell_sanity.py
  experiments/ptr-engine/measure/test_accuracy_recomputed.py` → **16 passed, 1 failed** —
  `test_accuracy_recomputed.py:30 test_recomputed_record_regenerates_byte_identically`, a
  byte-identity check on an accuracy record, untouched by this card (one test file changed).

## Write paths touched

`experiments/ptr-engine/longrun/tests/test_latency_floor_policy.py` (only).
