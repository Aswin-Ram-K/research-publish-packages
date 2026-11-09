# V-CAPGATE-DEDUP — attack the deduplicated-spend seam in the cap gate

**Unit class:** verifier (attacker). **Bound:** 24 tool calls (used 20). **Offline:** 0 inference requests, 0 sockets.
**Verdict:** `partial` — the gate refuses every overrun as shipped, but `delta<0` only warns, and the claimed deduction is not live.

## The claim being tested

`orchestration/handoffs/REQUEST-LEDGER-2.json` `assumptions[1]`: budget.spent is the de-duplicated 1,071 and the cap gate therefore spends against 1,071; a future duplicate mirror should surface as `delta<0` `CAP GATE UNRECORDED` instead of inflating the budget.

## What the code actually does (P1, read-only)

- `request_ledger.DEDUCTION_RULE_SOUND = False` (tools/request_ledger.py:155) and `deduction_permitted()` refuses to subtract without a `request_identity_hash` evidence key, so `build_report().requests = requests_raw = 1101`; the 1,071 lives under `diagnostic` with `deducted: false`.
- `RequestCapGate.__init__` (longrun/run_longrun.py:340) sets `headroom = cap - reserve`, `spent_at_start = build_report(...)['budget']['spent']`.
- `acquire()` (longrun/run_longrun.py:370) reserves before the send: `projected = spent_at_start + used_in_run + 1`, refuses when `projected > headroom` with exit 4.
- `_gate_finish()` (longrun/run_longrun.py:480): `delta>0` → `CAP GATE RECONCILE DIVERGENCE`, exit 9; `delta==0` → reconciled; `delta<0` → `CAP GATE UNRECORDED`, **rc stays 0**.

## Five probes, with observed strings and exit codes

| # | Probe | Observed | Exit |
|---|---|---|---|
| 1 | source arithmetic | `budget.spent` = 1101 raw vs `headroom`; `DEDUCTION_RULE_SOUND=False` | n/a (read) |
| 2a | +1 unseen duplicate, as shipped | `cap-gate: reconciled — the run's count 1 equals the rows gained 1 (delta 0)` | 0 |
| 2b | +2 unseen duplicates, as shipped | `CAP GATE RECONCILE DIVERGENCE (delta=+1): ... A divergence is a bug, not a rounding error.` | 9 |
| 2c | +1 unseen duplicate, deduction ON (claimed world) | `CAP GATE UNRECORDED (delta=-1): 1 request(s) reached the wire but their rows were not written before the run stopped (used_in_run=1 rows_gained=0); the next run's disk read under-counts by that many — reported, never silent` | **0** (warns) |
| 3a | `spent + planned == cap` (cap 1103, planned 2) | `cap-gate: reconciled — the run's count 2 equals the rows gained 2 (delta 0)`; no refusal | 0 |
| 3b | one over (planned 3, cap 1103) | `CAP REFUSED at T3 (turn) — over the global cap: spent=1103 would_spend=3 cap=1103 reserve=0 headroom=1103 allocation=3 used_in_run=2 turn=3 kind=turn projected=1104 over_by=1 — nothing sent` | 4 |
| 3c | which count (cap 1101) | raw: `CAP REFUSED at T1 (turn) — over the global cap: spent=1101 ... projected=1102 over_by=1`; dedup shim: `believed_unspent=30`, 30/30 acquired | 4 / launch |
| 4 | unsafe: rows 1101, ledger 1071, cap 1101 | as shipped: `believed_unspent=0`, 0/30 acquired, refused; claimed world: `believed_unspent=30`, **30/30 launched**, exit reconciliation `delta=0 rc=0` | 4 / 0 |
| 4b | `--dry-run` against `--budget-cap 1` on 1101 spent | `would_send_total=1` | **0** — the dry run never constructs the gate |
| 5 | ledger vs gate today | `REQUEST-LEDGER.json` spent=1101, spent_raw=1101, remaining=3219; gate prints `spent_at_start=1101 ... delta=0` | 0 |

## Findings

1. **The claim is false as stated.** The gate spends against the RAW 1,101, not the de-duplicated 1,071. The ledger reversed the deduction (`V-DUPLICATE-RULE overall fail`: `content_sha256` hashes the assistant's content, so tuple identity is not request identity). Being wrong in this direction is *safe* — the gate over-counts by 30.
2. **`delta<0` is a warning, not a brake.** `CAP GATE UNRECORDED` prints and returns exit 0. A run whose rows under-count its own requests still exits success, and the manifest's `reconcile` block records the negative delta while the process reports 0. Nothing downstream fails.
3. **The unsafe direction is latent, not live.** With deduction enabled the gate would launch 30 requests on zero true headroom, and the exit reconciliation would then print `delta=0` because the deduction hides the mirror. It is behind `DEDUCTION_RULE_SOUND` plus a `request_identity_hash` that does not exist today, so it cannot be reached on this commit — but the seam is one evidence key away.
4. **A dry run cannot preview the brake.** `build_cap_gate()` is only called from `run_cell()` (longrun/run_longrun.py:2155); `--dry-run` exits 0 with `--budget-cap 1` against 1,101 already spent.

## Answer to the gate question

As shipped, the cap gate can be trusted as the brake behind `RUN-A*`: it spends against the raw, conservative 1,101 and refuses at `projected > cap` (exit 4), verified at the exact boundary and one request over. The two defects — `delta<0` warn-only, and a dry run that never touches the gate — are gaps, not ways to buy unearned headroom on this commit.

## Reproduce

```
python3 experiments/ptr-engine/tools/capgate_dedup_attack.py
```

Exit 0 always; every probe prints its own observed exit code. Mirrors live under `/tmp/capgate-dedup-mirror`; the repository's gate, ledger, rows and artefact are only read.
