# UNIT PROJECTION-CALIBRATION — a worst case is not a forecast

**Status:** done. **Zero inference requests** (offline; every wall figure re-derived from
row files on disk).

## Problem

`cell.py`'s preflight projection (from `HARNESS-GUARDS`) multiplied every request by
`--turn-wall-cap` (180 s) and refused with **exit 8** past `--max-wall` (3600 s). A 48-turn
cell "projected" 8,640 s and the operator's 60-turn comparison 10,800 s, so the guard
refused the experiments it exists to protect. The multiplier was the **live abort
threshold**, i.e. the worst case, not a forecast.

## What changed

`experiments/ptr-engine/longrun/cell.py`:

- `--projected-turn-wall` (seconds, default **60**) — the expected per-turn wall used by
  the projection.
- `--projected-from <rows-*.jsonl>` — use a prior row file's **p90 turn wall** instead;
  the preflight line names the file (`source=p90 file=…`). Missing/empty file → exit 2.
- Preflight prints both numbers, labelled:
  `projected_wall~=2880s (cap-per-turn 180s -> worst case 8640s) cap=3600s
  projected-turn-wall=60.0s source=default`.
- New `_p90`, `turn_walls_from_rows` (`wall_ms`/1000 else `latency_s`; `error` rows
  dropped), `projected_turn_wall`.
- `--max-wall` and **exit 8** unchanged. `--turn-wall-cap` unchanged: `stage_run` still
  hands it to `run_longrun.py`, which still aborts a live turn that reaches it. Exit 9
  untouched.

## Measured per-turn wall (paths named)

| group | n | p50 | p90 | mean | Σwall/Σcompletion_tokens |
|---|---|---|---|---|---|
| `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T145758Z.jsonl`, thinking auto | 6 | 129.1 s | 427.7 s | 190.9 s | 0.0288 s/token |
| pooled thinking on/auto | 9 | 218.2 s | 682.7 s | 286.5 s | 0.0349 s/token |
| pooled thinking off/absent (9 files, see docs) | 960 | 2.9 s | 38.1 s | 27.5 s | 0.0338 s/token |

The six live rows are **one arm on one day** — quoted as anecdotes, not a distribution; a
p90 over six points has no tail. Wall per completion token is stable at ~0.03 s in every
regime, which is why a 4096-token bound is ~123 s and 180 s was never an expectation.

## Arithmetic (`--max-wall 3600`)

| turns | ×60 (projected) | ×180 (worst) | verdict at 60 |
|---|---|---|---|
| 12 | 720 | 2,160 | admitted |
| 48 | 2,880 | 8,640 | admitted |
| 60 | 3,600 | 10,800 | admitted (equal, not past) |

At the measured p90 for thinking off (38.1 s): 457 / 1,829 / 2,286 — all admitted. At the
six-row p90 (427.7 s): 5,132 / 20,530 / 25,662 — all refused, which is the honest warning
that the thinking-on regime really is that long. 12-turn smoke = 720 s; operator
4-arm × 60-turn × 3-rep = 720 serial requests = 43,200 s (per cell 180 requests = 10,800 s,
so it needs `--max-wall ≥ 10800`, not a disabled guard).

## Tests

- `experiments/ptr-engine/longrun/tests/test_projection_calibration.py` — **4/4 passed**:
  (a) 48×60=2880 admitted, (b) 48×180=8640 exit 8, (c) p90 from file + file named,
  (d) live turn still aborted by `--turn-wall-cap` (0.4 s and 1.2 s, row records
  `turn_wall_cap`/`truncated`).
- `experiments/ptr-engine/longrun/tests/test_guards.py` — **6/6 GREEN** after re-run.
- Red→green: (a) refused with exit 8 and `projected_wall=8640s` before; (b) is the standing
  red-side control (the pre-fix arithmetic); (c) the flag did not exist; (d) is the
  invariant that passes before and after.

## Deviation, disclosed

`experiments/ptr-engine/longrun/tests/test_guards.py` check (d) was pinned to `--projected-turn-wall 180` and its assertion
changed to `projected_wall~=8640s`, because its old expectation — a 48-turn cell refused at
the default — is precisely the defect this unit removes. Without that test-only change the
suite would be red for the intended change. No guard behaviour was altered: exit 8 still
fires and still precedes the runner.

## Files

`experiments/ptr-engine/longrun/cell.py` · `experiments/ptr-engine/longrun/tests/test_projection_calibration.py`
· `docs/PROJECTION-CALIBRATION.md` · `experiments/ptr-engine/measure/PROJECTION.json` ·
`orchestration/units/PROJECTION-CALIBRATION.md` · `orchestration/handoffs/PROJECTION-CALIBRATION.json`
· `orchestration/journals/PROJECTION-CALIBRATION.jsonl`
