# UREVER2 — Re-verification of Candidate #2/A2: "Replay reproduces the record, not the decision"

**Kind:** RE-VERIFICATION (independent of the proposing/reconnaissance unit).
**Hard bound:** 25 tool calls. Increments appended to `strategy/PAPER2_REVERIFICATION.md` as measured.
**Workspace:** `/home/zer0null/reserach extarctor` (sole write scope).
**Read-only:** `/home/zer0null/Duval` — reading only, **no git command of any kind**.

## Purpose
Establish from raw records whether the proposed headline finding is real:
1. Locate the 3,040-output corpus and `l1-head-to-head.jsonl`; report path, size, count, sha256.
2. Establish schema: quote one verbatim record from each; identify recorded-output field vs decision field; state divergence definition.
3. Re-derive divergence rate independently (numerator, denominator, rate), broken down by four variants if records allow.
4. Compare against inventoried **41.8%**. Do not tune the computation to match.
5. Judge draftability: (a) draftable now, (b) draftable after new measurement, (c) not supported.
6. State limits: what a reader cannot check, releasability, minimal repro subset.

## Declared write paths
- `strategy/PAPER2_REVERIFICATION.md`
- `orchestration/units/UREVER2.md`
- `orchestration/handoffs/UREVER2.json`
- `scratch/urever2/**`

## First-path-to-check (from UPICK1 recon, unconfirmed)
`state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/`

## Rules observed
- No paper prose. Feasibility measurement only.
- Do not trust prior summaries; verify paths, variant names, and 41.8% against raw files.
- Report under explicit `Measured` / `Inferred` / `Could not determine` headings.
- Secrets/PII: counts and field names only, no values copied.

## Status log
- (start) card persisted; beginning path confirmation.
- STEP 1 done: UPICK1 path EXISTS and is readable. `decision-variants.jsonl` 1,197,797 B / 3,040 lines / sha256 `c5ec44a7…`; `l1-head-to-head.jsonl` 63,238 B / 380 lines / sha256 `6af0e0d8…`. 15 byte-identical mirrors of each under `state/`.
- STEP 2 done: schema captured verbatim; **`correct` is the option INDEX (0–4) in BOTH files, not a flag**; decision = `picked_index`, outcome = `picked_index==correct`.
- STEP 3–4 done: all inventoried figures reproduced exactly from raw records — 41.8 % = 476/1140 (binding, V0), 32.2 % = 245/760 (prompt), 0 % = 244/244 (control), 31.6 % = 60/190 (stable), 51.6 % = 98/190 (l1). Per-variant binding: V0 41.75 / V1 47.11 / V2 40.00 / V3 43.33 %.
- STEP 5–6 done: verdict **(a) draftable now**; limits and the `l1` non-independence finding written to `strategy/PAPER2_REVERIFICATION.md`.
- END: handoff written. 18 tool calls used of 25. Confirmed `/home/zer0null/Duval` never touched and no `git` command run anywhere.
