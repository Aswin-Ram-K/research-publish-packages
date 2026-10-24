# V2-R — independent verification of the batch-1 numbers

**Status:** `partial` — completed and reported; nothing left running.
**Bound:** max 60 tool calls, 0 live model requests. **Used:** 30 tool calls, 0 requests.
**Independence:** this unit did not author any of U2, U4b, U5, U9, U10 and did not modify any of their files.
**Write paths (mine alone):** `state/verify/V2/**`, `orchestration/handoffs/V2-R.json`, `orchestration/units/V2-R.md`.

## Objective

Re-derive from the raw rows every number the batch-1 units published; flag anything that does not
reproduce; separately confirm the instrument-gate assertions hold *in the rows* (cold → cached null/0,
warm → cached non-null, repeat determinism).

## Deliverable

`orchestration/handoffs/V2-R.json` in the verifier shape (`unit`, `overall`, `checks`, `not_reproduced`,
`overstated`, `unverified`, `blocker`, `next_unit_hint`, `write_paths`, plus `red_green`, `assumptions`,
`tool_calls`, `bound`).

Every check carries the command that produces it: `python3 state/verify/V2/recompute.py`.

## Method

One stdlib-only script, `state/verify/V2/recompute.py`, reads the five rows files and recomputes
104 values against what the handoffs published. No network, no scipy — Fisher exact, McNemar/sign exact
and Clopper-Pearson were reimplemented and CP was validated against U10's four published bounds, all of
which it reproduces to 4 dp.

- `--mutate` runs the red→green check (see below).
- `--json` dumps the machine-readable results.
- Exit 0 = every check pass; exit 1 = at least one fail (the last run exits 1, by design, because
  eight checks fail — that is the finding, not a broken script).

Sources: `cells/U2/u2_rows.jsonl` + `u2_cache_rows.jsonl` + `u2_report.json`; `cells/U9/u9_trials.jsonl`;
`cells/U10/u10_rows.jsonl` + `u10_rows_p23.jsonl` + `u10_report.json`; `cells/U4b/rows.jsonl`;
`cells/U5/u5_raw.jsonl`.

## Result: 94 pass / 8 fail / 2 unverifiable (104 checks)

### Holds

- **Instrument gate.** Cold requests report `prompt_tokens_details: null` (U2 G0) and coerce to 0; all 55
  U10 cold rows, all 44 U2 cache_rows cold rows and every U9/U10/U4b/U5 warm row carry an explicit
  integer `cached_tokens`. Repeat determinism: U2 G0 `prompt [841,841,841]` / `cached [832,832,832]`,
  44/44 U2 warm cases single-valued, U10 rep2 10/10 at exactly `64*((L-1)//64)`.
- **U2 tax law.** `cached == 64*floor(L/64)` with residual 0 on 44/44 lengths, reproduced independently
  from both `u2_rows.jsonl` and `u2_cache_rows.jsonl`; stored `residual`/`resid_mod64` fields and the warm
  `raw_usage_warm` block all agree with fresh computation.
- **U10.** Every published count reproduces: 5/5 misses at L=1024 and L=1088, 0/5 at 1008/1023/1025,
  pooled `[[10,0],[0,15]]`, Fisher p=3.059e-07, 20/20 delay misses, 5/5 insert misses, 25/25 hits at the
  tax-law value.
- **U5.** All arm accuracies (137/134/132/126 of 190), confusion cells, exact agreement, McNemar p-values,
  retention counts, kill-condition margin 2.632 pts and 760/760 HTTP 200 reproduce to the digit.
- **U4b arithmetic.** `cached_by_branch`, totals, `B/A = 15400/4648 = 3.3133`, `C/A = 1.0000` reproduce
  exactly.

### Does not reproduce

1. **U9 per-length medians, five of six lengths.** Recomputed 348.1 / 692.9 / 1421.9 / 3054.9 / 7529.0 ms
   against published 349.2 / 674.6 / 1431.6 / 3039.5 / 7541.9. The cause is structural: the trial rows
   switch the uncached-fill role from `miss` to `prime` at seq61, and no single grouping outside the one
   the publisher used lands on these numbers.
2. **U9 p=0.0078 is arithmetically impossible** for the test described: the minimum two-sided exact p at
   n=7 is 2/2⁷ = **0.0156**. The published value is exactly half of it.
3. **U9 exponents** 1.052 / 0.268 / −0.784 and OLS 0.2407 / 0.00466 reproduce only to two decimals
   (1.039 / 0.264 / 0.775); the sign of the ratio exponent is reported as −0.784 and recomputes positive
   because the fit is on the miss/hit ratio.
4. **U4b cached=1792 contradicts the tax law.** L=1925, so both published forms predict 1920; all 12 hit
   rows say 1792 (7×256), a 128-token/6.7% shortfall. `B/A=3.31` is right as arithmetic but sits on cache
   accounting the other cells do not support.
5. **U4b `len_P_chars`** 8754 appears nowhere in its own rows (A/B 9068, C 9069).
6. **U2's "CONFIRMED" cannot reach multiples of 64.** No U2 length is a multiple of 64 and the 15,787-token
   probe is `%64 = 43`, so `floor(L/64)` and `(L-1)//64` are indistinguishable there.

### Unverifiable from rows

- `G0.short_boundary` (42-token prompt, cached [0,0]) exists only as a report field; there is no sub-64
  row in either U2 rows file.
- U5's `shallow summarise == fork 190/190` — `u5_raw.jsonl` has one shallow condition (`shared`), so the
  claim is true by construction and can neither be confirmed nor falsified.

## Red → green

`python3 state/verify/V2/recompute.py --mutate` → **5/5 mutations behaved as required → PASS**.
Real U2 rows satisfy the tax law (green); the same rows with one `cached` value inflated by 64 fail it (red);
`B/A=3.3133` passes against the published value (green) and fails against a mutated 3.5000 (red); a flipped
recomputed expectation goes red. Log: `state/verify/V2/redgreen.log`.

## Assumptions recorded (no human available; conservative defaults taken)

- The card names `cells/U2/rows.jsonl`; that path does not exist. Used `cells/U2/u2_rows.jsonl`
  (44 rows) plus `u2_cache_rows.jsonl` (88 rows) — recorded as a card typo, not a missing artifact.
- U9's handoff labels its lengths by *observed* prompt length (1024…31415) while its rows key them by
  `length_target` (1024…32768); joins are on `length_target`, and the card's labels are quoted as-is.
- Fisher / McNemar / Clopper-Pearson reimplemented stdlib-only; CP validated against U10's four
  published bounds to 4 dp, so the implementation is not the source of any divergence.

## Artifacts

- `state/verify/V2/recompute.py` — the recomputation (104 checks, `--mutate`, `--json`)
- `state/verify/V2/run.log` — full check table, final run
- `state/verify/V2/results.json` — machine-readable results
- `state/verify/V2/redgreen.log` — red→green transcript
- `orchestration/handoffs/V2-R.json` — the handoff
