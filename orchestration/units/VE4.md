# VE4 — verifier for E4 `boundary-n20`

**Verdict: pass (with two word-level corrections).** Offline only: 0 live requests, no `.occamy.lock`,
no POST, nothing written outside the three declared paths. Bound: 15 tool calls / 20.

## What was re-run

`e4_analyze.py` re-executed **in an isolated temp copy** of the pinned rows (sha256
`5f10b3160a8c7b394512b841a991e5f1cc5956d2c6c252aaa1645d0fae8a2560`, verified on the copy) so the pinned
`e4_report.json` was never overwritten. The rerun reproduced the pinned report **byte for byte**
(`f3a341c33f288b1d6f09fed233a1dfa19102d26bbc1e423e7a383b61f8ee387d`).

## Check 1 — per-cell counts (PASS)

| L | n | rep-1 full misses | rep-1 cached hist |
|---|---|---|---|
| 960 | 5 | 5/5 | {0: 5} |
| 1023 | 20 | 0/20 | {960: 20} |
| 1024 | 20 | 20/20 | {0: 20} |
| 1025 | 20 | 0/20 | {1024: 20} |
| 1088 | 20 | 20/20 | {0: 20} |

Pooled multiples **45/45 CP95 [0.9213, 1.0]**; non-multiples **0/40 CP95 [0.0, 0.0881]**;
Fisher two-sided **p = 3.4646074215706565e-25**. rep-1 `cached == 0` in **45/45** boundary rows
(**40/40** at 1024+1088, as the card states), never an intermediate value. The CP bounds are right
independently: `0.025**(1/45) = 0.9213`, `1 - 0.025**(1/40) = 0.0881`; per-cell 5/5 → 0.4782 and
20/20 → 0.8316 match the unit card's table.

## Check 2 — rep-2 lands only at `L-64` (PASS)

1024 → `cached = 960` x20; 1088 → `cached = 1024` x20. **40/40 at `L-64`**, **0/40 at `L`**, block tax
`prompt - cached == 64` in **40/40**. No rep-3 rows exist (0). 960 has no rep-2 rows, so the `(L-1)` form
cannot be checked against a multiple other than 1024/1088.

## Check 3 — red→green (PASS; both guards go red)

* **Boundary claim.** Relabelling the 20 control trials `1025 → 1024` (trial index +100 to avoid the
  analyzer's `(cell, trial)` merge) turns the 1024 cell into **20/40** misses with hist `{0: 20, 1024: 20}`,
  pooled multiples **45/65 CP95 [0.5655, 0.8009]**, Fisher **9.82e-09**, and `F_a` marks L=1024
  inconsistent. The "every multiple misses 20/20" claim fails, as required.
* **Fisher.** Swapping the boundary *label* of 1088 (multiple) and 1023 (control) gives 2x2
  `[[25,20],[20,20]]` → **p = 0.6666** (> 0.05: stops rejecting), against the observed `[[45,0],[0,40]]`
  → 3.46e-25. An independent exact implementation (Fractions, `math.comb`, different loop) returns the
  same 3.4646074215706565e-25, so the p-value is computed, not baked.

## Check 4 — word-by-word adjudication

**(a) Plain tax law `64*floor(L/64)` at multiples: falsified**, not merely "not observed". It is a point
prediction; its complement occurred 40/40 at two multiples on rep-1 (0 vs 1024/1088, CP95 upper 0.0881 for
attainment) and 40/40 on rep-2 (`L-64` vs `L`). Scope: falsified **as an equality** at 1024/1088 (960 also
0/5 but n=5 is a spot-check). As an upper bound it is not violated — `cached <= L` trivially — so the word
"falsified" belongs to the equality/attainment reading, which is the reading E4 uses.

**(b) `(L-1)` ceiling: correct as the steady-state ceiling, refuted as the miss rule — both directions
checked on the rows.** Miss rule: at 1025 (`(L-1)%64 == 0`) it predicts a miss and got **0/20**; at
1024/1088 (`(L-1)%64 == 63`) it predicts a hit and got **20/20** — 3 discriminating cells, 0 consistent.
As a value rule, `64*floor((L-1)/64) = L-64` matches rep-2 **40/40**, and `L` 0/40. **Correction of scope:**
it is the ceiling that binds *from the second repeat on*, not a ceiling on rep-1 — it predicts `L-64` at a
boundary and got 0. E4's own C2 paragraph says this, but check 4's headline ("the (L-1) form is the right
ceiling rule at the boundary") should carry "steady-state".

**(c) "Deterministic": licensed as description, not as inference.** Licensed for the 45 measured trials:
45/45 immediate repeats returned `cached == 0`, no intermediate value ever, TTFT bimodal (205/257 ms miss
vs 67/89 ms hit), gap 0.14–0.16 ms — no distribution was observed. **Not** licensed as a property of the
boundary: CP95 lower is only **0.9213**, so a race with escape probability up to ~7.9% is not excluded at
95%; there is no rep-3 and only two boundary lengths on one endpoint. The honest wording is "reproduced in
45/45 (CP95 lower 0.9213, no variance observed)", not "deterministic".

## Check 5 — A1 and containment (PASS, two notes)

Rows are **220 = 85 cold + 85 rep1 + 40 rep2 + 10 cal** — exactly the claimed 220 requests and exactly the
cap (`max_requests` 220, zero headroom). Cold rows `cached == 0` **85/85**; every cold `prompt_tokens`
equals its cell length **85/85**. 960 has 5 trials (n=5); 1023/1025 have cold+rep1 only (2 sends);
1024/1088 have cold+rep1+rep2 (3 sends). 1008, 1152, 2048, 4096 are absent from the rows, as A1 states.
Planned-vs-cap arithmetic is consistent: 960@7 + 4x20x(2/3) + 10 probes = 224 > 220, so 960 loses 2 trials.

Containment: every file touched after 15:40 lies under `experiments/context-cache/cells/E4/`,
`orchestration/units/E4.md` or `orchestration/handoffs/E4.json`. Shared modules are untouched —
`experiments/context-cache/client.py` and `analyze.py` mtime **2026-10-20 17:57:55**, `runner.py`
**2026-10-20 18:36:48**; no `render.py` exists under `experiments/`. The driver writes only
`cells/E4/e4_rows.jsonl`, `cells/E4/e4_run.json` and a harness progress JSONL under `$DSH_PROGRESS_DIR`.

**Notes (not blockers).** (1) A1 deviates from the card's drop order — the card drops 4096 → 2048 → 1152 →
960, E4 dropped 1008 and kept 960 at n=5; it is disclosed in `E4.md:26`, but the effect is that a real
control was traded for a 5-trial spot-check. (2) The driver *imports* `cells/U10/u10_corpus.py`
(`e4_cell.py:66`) read-only; no modification. (3) Lock coverage of all 220 sends cannot be proven offline:
rows carry no acquire/release timestamps, only `lock_wait_s = 5.501`, `elapsed_s = 54.2` and the code's
flock/unlock pair.

## Corrections to carry forward

1. `deterministic` → "reproduced in 45/45, CP95 lower 0.9213, no variance observed" (overstated as an
   inference; keep the descriptive use).
2. `(L-1)` "right ceiling" → "steady-state (rep-2) ceiling"; it is not a rep-1 ceiling.
3. "permanent 64-token shortfall on every later repeat" (`E4.md:48`) is an extrapolation: no rep-3 exists,
   and `E4.md:58` already admits a one-more-repeat lag is equally consistent. Drop "permanent" or mark it as
   a prediction.
