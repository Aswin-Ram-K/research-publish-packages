# P95-POWER-DIGEST-FIX

**Status:** done · **bound:** ≤26 tool calls, 0 inference requests · **cost:** 0 requests.

## Objective
Make the power verifier pass or fail on the numbers `P95-POWER.json` is supposed to check, not on a
`method.analyze_stats_sha256_atimport` digest it cannot recompute. Fix the digest mechanism; never move
a computed number, threshold, bootstrap parameter, `min_n_for(0.95)=60` floor, or seed.

## Start state (measured)
- `bash experiments/ptr-engine/measure/p95-power-verify.sh` -> **exit 1**, twice (stable).
- Fresh generator run vs committed JSON differs in exactly one line:
  `"analyze_stats_sha256_atimport": "0a9a7861…"` (regenerated) vs `"2c9756f3…"` (committed).
- `git ls-files --error-unmatch experiments/ptr-engine/longrun/analyze_stats.py` -> exit 1: the module is
  **untracked**, so "the digest of the file at HEAD" was never a reproducible quantity.
- Generator hashed a path literal, `sha(ANALYZE_STATS)` at `p95_power_gen.py:272`, and recorded
  `analyze_stats_imported: False` — nothing was imported, so "atimport" was a misnomer.

## Provenance verdict
(a) **stale for an earlier content revision** of the same path — the JSON was written at 11:41, the file
was edited at 11:45 — *and* (c) **genuinely unreproducible because untracked**. Not (b): same path.
`2c9756f3…` is withdrawn.

## Fix (files)
- `experiments/ptr-engine/measure/p95_power_gen.py` — imports `analyze_stats` via `importlib` and digests
  `os.path.realpath(module.__file__)`; `method.analyze_stats` now records `imported`, `path`, `realpath`,
  `sha256_atimport`, `tracked` (from `git ls-files --error-unmatch`), `dirty` (untracked or modified).
  Legacy flat key `analyze_stats_sha256_atimport` kept, same value.
- `experiments/ptr-engine/measure/p95-power-verify.sh` — temp file moved in-repo (was `/tmp`).
- `experiments/ptr-engine/measure/P95-POWER.json` — regenerated; only the `method` block changed.
- `docs/P95-POWER.md` — provenance note, §8 "what the verifier certifies, and what it cannot".
- `experiments/ptr-engine/tools/p95_power_probe.py` — independent re-derivation of every closed-form number.

## Hard rules honoured
No threshold, bootstrap parameter, seed, floor or computed statistic was changed; no rows file, fixture,
`analyze_stats.py`, `cell.py`, `run_longrun.py`, `client.py` or `grade_v5.py` was edited; zero inference.
