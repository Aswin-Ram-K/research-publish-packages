# Unit E4R — `rep3-probe`: one-repeat lag or persistent ceiling?

## Corrections (VE4R, applied by E4RC)

`VE4R` verdict **pass** (2026-10-21): every number re-derived, no count moved. Four record defects — all
wording, one label set — repaired here additively; every original is preserved in `superseded_text` of
`orchestration/handoffs/E4R.json` beside its `verifier_corrections` entry. **0 live requests, no lock, no
re-measurement.**

| # | where | as written | corrected to |
|---|---|---|---|
| 1 | `E4R.md:53` vs `E4R.md:37` + `E4R.json one_repeat_lag_persists` | "One-repeat lag is refuted" (`:53`) against the `:37` row and the JSON prediction, both CONFIRMED — the same label carried opposite verdicts | **"the one-repeat (transient) lag is refuted; the persistence reading is confirmed"** — the `:37` row is now labelled *persistence (was labelled "one-repeat lag")*, and the JSON says which reading is confirmed |
| 2 | `E4R.json` `rep3_licensed_sentence` | "a permanent one-block tax on every later repeat measured (repeats 1-3 ...)" reads as a 64-tax on repeats 1–3 | **persistent through repeat 3 — repeats 2–3 of 3 measured**; rep-1's tax is `L` (a full prefill, `cached 0` 20/20), the 64-tax is repeats 2–3; `(repeats 1–3)` is the measured **window**, not the tax's range. `E4R.md:57-58` already said this; the JSON now matches the card |
| 3 | `E4R.json` `ttft_ms_medians`, `E4R.md:61-62` | `1024_miss` / `1088_miss` = 231.4 / 278.9 ms — the **rep-1** medians (`cached == 0`), not cold | keys renamed **`1024_rep1` / `1088_rep1`**; cold added as `1024_cold` 232.5 / `1088_cold` 279.3; rep-2 116.9 / 117.6 and rep-3 116.7 / 117.3 recorded |
| 4 | `E4R.md:52` CP95 | — | confirmed **Clopper–Pearson** `0.025^(1/40)` = 0.9119, **not** Wilson (0.9124); the card's `CP` label was already correct — now named explicitly in the JSON |

Numbers unchanged: 180/180 requests, cold `cached == 0` 46/46, rep-3 **40/40** at `L-64`, **0/40** at `L`,
block tax 64 40/40, `rep3 == rep2` 40/40; `e4r_rows.jsonl` sha256 `05a59f28…e09a7` untouched.

**Status:** done (2026-10-21). **Purpose (one only):** settle the question E4 could not — is the
multiple-of-64 64-token shortfall a **one-repeat lag** (recovers at repeat 3) or a **persistent
ceiling** (`cached == L-64` on every later repeat)? E4 measured repeat-1 (`cached == 0`, 45/45) and
repeat-2 (`cached == L-64`, 40/40) and **never repeat-3**; VE4 and VE24 both scoped "deterministic" to
description only and both flagged rep-3 as the missing discriminator. Wording of record is
`orchestration/handoffs/E4C.json` (cite E4C, not E4's original headline).

**Hard bound:** ≤180 live requests, ≤20 min, ≤15 work tool calls, 3 consecutive failures → `partial`.
**Actual:** 180 requests (cap exactly, zero headroom), 42.2 s, 0 failures, 12 work tool calls.

## Inputs (read-only)
`orchestration/handoffs/{E4,E4C,VE4}.json`; `orchestration/units/E4.md`;
`experiments/context-cache/cells/E4/{e4_cell.py,e4_analyze.py,e4_report.json}` — protocol, salting and
definitions reused verbatim, so rows are directly comparable to E4's.

## Design (pre-registered before the first live request)
- Cells, in spend order: **1024** and **1088** at n=20 with 4 sends per trial (cold + repeats 1, 2, 3);
  **1008** and **1152** at n=5 with 2 sends, only if the 180 cap still had room. Rep-3 depth paid first;
  the neighbours are last by construction.
- Per trial: fresh salt → **cold** (verified `cached == 0`, warm cold row = probe, trial redrawn) →
  repeats 1, 2, 3 of the **byte-identical** text (sha256 recorded). Never `/flush_cache`.
- Every row records `prompt_tokens`, `prompt_tokens_mod_64`, `cached_tokens`, `block_tax`,
  `expected_u10 = 64*floor((L-1)/64)`, `expected_plain = 64*floor(L/64)`, `implied_ceiling`,
  `cached_eq_L`, `cached_eq_L_minus_64`, `cached_eq_ceiling_u10`, `ttft_ms`, `gap_ms`, and a
  `send_index`/`repeat_index` pair (the E4R card counts "rep-2/rep-3" as sends; E4 counts them as
  repeats — role names stay `cold, rep1, rep2, rep3` so rows line up with E4).
- One request in flight, strictly serial. Lock: `fcntl.flock(LOCK_EX)` on
  `experiments/context-cache/.occamy.lock`, acquired before the first live request, held to the last,
  released in `finally`; 1800 s deadline → timeout means `partial` / blocker `"lock timeout"`.
  `lock_wait_s = 0.0`.

## Predictions under test
| hypothesis | rep-2 | rep-3 |
|---|---|---|
| persistence (was labelled "one-repeat lag") | `L-64` | `L-64` (shortfall persists — the 64-token block lag is a property of the block, not of one request) |
| transient lag | `L-64` | `L` (recovers) |
| worse | `L-64` | further degraded (0 or `L-128`) |

Also tested: does rep-3's `cached` equal `64*floor((L-1)/64)` in **every** trial (the steady-state
ceiling VE4 licensed)?

## Result
| L | L%64 | n | rep1 `cached` | rep2 `cached` | rep3 `cached` | rep3 `== L-64` | rep3 `== L` |
|---|---|---|---|---|---|---|---|
| 1024 | 0 | 20 | 0 (20/20) | 960 (20/20) | 960 (20/20) | 20/20 | 0/20 |
| 1088 | 0 | 20 | 0 (20/20) | 1024 (20/20) | 1024 (20/20) | 20/20 | 0/20 |
| 1008 | 48 | 5 | 960 (5/5) | — | — | — | — |
| 1152 | 0 | 1 | 0 (1/1) | — | — | — | — |

- **Pooled rep-3: 40/40 at `L-64`** (CP95 [0.9119, 1.0]), **0/40 at `L`**, block tax exactly 64 in
  40/40, and per-trial `rep3 == rep2` in **40/40**. **The one-repeat (transient) lag is refuted; the persistence reading is
  confirmed** (the transient-recovery reading — `L` at rep-3 — is refuted at 0/40). The rows license: *the 64-token shortfall is a persistent steady-state ceiling from
  repeat 1 onward — `cached == 64*floor((L-1)/64) = L-64` on repeat 3 in 40/40 boundary trials, never
  `L` — so a multiple of 64 pays one full extra prefill at the first repeat and then a
  **persistent** 64-token (one block) tax on every later repeat measured.* **Scope (VE4R):**
  persistent **through repeat 3** — repeats 2–3 of 3 measured, which is where the 64-tax applies;
  rep-1's tax is `L` (`cached 0` 20/20). `(repeats 1–3)` is the measured **window**, not the tax's range. "Persistent" is licensed for
  repeats 2–3 of 3 measured; rep-4 was **not** reachable inside 180 requests (5 sends/trial x 40 trials =
  200 > 180).
- Rep-2 re-confirmed on the same trials: 40/40 at `L-64`, 0/40 at `L` — E4's rep-2 row reproduced at a
  new time, from a fresh server-side cache state, with 4-send trials.
- `TTFT` medians (ms): 1024 **rep1** 231.4 / rep2 116.9 / rep3 116.7 (**cold** 232.5); 1088 **rep1**
  278.9 / rep2 117.6 / rep3 117.3 (**cold** 279.3). Earlier wording said `miss`, which is the **rep-1**
  median, not the cold row: both sit in the `cached == 0` regime, but only cold starts from an idle
  server-side cache. Rep-3 latency matches rep-2, not the first-repeat miss — a persistent hit, not a
  re-prefill.
- New lengths: **1008** (mod 48) is a non-multiple control at a length E4 dropped — 5/5 `cached = 960
  = 64*floor(1007/64)`, block tax 48, no first-repeat miss. **1152** (multiple) shows the rep-1 miss
  1/1 — a spot check only, n=1, no rep-2/3.

## What this settles and what it does not
- Settles (at 1 endpoint / 1 model / 1 SGLang build, repeats 1–3, n=20 per length): the boundary
  shortfall **does not decay after one repeat**. VE4's licensed "steady-state ceiling" is correct at
  rep-3 and is now a finding, not a prediction. E4C's scoped "permanent" is restored as **"persistent through
  repeat 3"** — repeats 2–3 of 3 measured, the range on which the 64-tax holds (rep-1's tax is `L`).
- Does **not** settle the mechanism: `cached_tokens` is the server's own accounting (G13); no
  server-side trace of chunk insertion exists. It does not settle generality beyond this
  endpoint/model/build, nor rep-4-and-later, nor 1008/1152 at full n.

## Deviations and assumptions
- **A1 (budget):** 4 sends/trial at 1024+1088 = 160 requests, plus 8 calibration probes = 168; 1008
  took 10 and 1152 reached only 1 trial before the 180 cap. Neighbours landed at n=5/n=1, not the
  card's n=10: the card gave rep-3 depth priority and this is where the cap fell. 1152's n=1 is a
  spot check, never pooled.
- **A2 (rep-4):** not run. 5 sends/trial at both lengths would be 200 > 180 alone; the card made rep-4
  conditional on budget, so the three measured repeats carry the claim.
- **A3 (calibration order):** each cell is calibrated immediately before its trials (E4 calibrated all
  cells up front). Same `calibrate()` code; one probe per cell hit the exact length
  (1024 chars=4291 tail=26; 1088 4567/29; 1008 4221/26; 1152 4843/28), so no drift rows were spent.
- **A4 (rep naming):** role names follow E4 (`cold, rep1, rep2, rep3`) with `send_index`/`repeat_index`
  added; the card's "rep-3" is `repeat_index == 3` (`send_index == 4`).
- **A5 (cached_tokens):** accepted as the server reports it, as in E4/U10.

## Evidence
`python3 e4r_cell.py` → `requests=180 probes=8 rows=180 failures=0 aborted='' lock_wait_s=0.0
elapsed_s=42.2`; `e4r_rows.jsonl` sha256 `05a59f28d169947fd959842ef482e07ec95fb2a96ac8405151e4aaf1920e09a7`;
rows by role: cal 8, cold 46, rep1 46, rep2 40, rep3 40. Cold isolation 46/46 `cached == 0`; exact
length 46/46 trials (n=1 on 1152 included).

## Artifacts
`cells/E4R/e4r_cell.py` (protocol + analysis + report writer), `e4r_rows.jsonl`, `e4r_run.json`,
`e4r_report.json`, `e4r_rows_dryrun.jsonl`, `e4r_report_dryrun.json`.
