# Ledger baselines — v1 (dated record) and v2 (current)

Two frozen request-ledger baselines exist. **v2 is the baseline every card quotes from now on.**
v1 is not deleted and not edited; it is superseded *by pointer*.

| | v1 | v2 |
|---|---|---|
| file | `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json` | `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json` |
| frozen | 2026-10-26T18:24:48Z (`captured_utc`) | 2026-10-26T19:04:18Z (`frozen_at`) |
| requests | 1101 | **1128** |
| remaining | 3219 | **3192** |
| cap / reserve | 4320 / 0 | 4320 / 0 |
| de-duplicated (diagnostic only, never subtracted) | 1071 | 1098 |
| source ledger sha256 | `2f60b831…6c4e1e5` | `6da0c1f19b7cd37203c9d99de5e5d8a9db879e002f389a2b525a776624c27806` |
| baseline file sha256 | `6b6dff4473e5e1b9a20ab73b58dfb4a884d50dff019751058ebbd0188b307470` | `3b79f4766abc8479a7a963f9e04063837928d09d48d2435e91f488b3c6d3ae0d` |

## Why a second baseline exists

`REQUEST-LEDGER.json` was **rebuilt** after v1 was frozen: requests 1101 → 1128, remaining 3219 → 3192,
artefact sha `6da0c1f1…` (v1 pinned `2f60b831…`). The 27-request difference is the **era-A abandoned
cell** — the 27 rows in `rows-cell-pointer-stable-20261026T182535Z.jsonl`, lines 1–27.

Those 27 are **pre-grid spend, not tranche spend**. `RUN-A-STAR-2` bills cell work against a baseline;
measured against v1 it would inherit the 27 as part of its own delta. Measured against v2 it inherits
nothing: on a bare invocation the tool reports `delta 0`.

**The 27's owner:** era A — the abandoned pointer-stable cell that produced
`rows-cell-pointer-stable-20261026T182535Z.jsonl`. It is recorded history, already spent, already
inside v2's 1128.

## How a future card quotes spend

```
delta = REQUEST-LEDGER.json :: budget.spent  -  1128          # = requests_raw - 1128
python3 experiments/ptr-engine/tools/ledger_delta.py          # defaults to v2
```

The tool enforces three identities and exits 1 if any breaks (`deficit:`/`discrepancy:` lines):

1. `delta == requests_raw_now - 1128`
2. `remaining_raw_now == 3192 - delta`
3. `spent_now == requests_raw_now`

**Never** subtract `requests_deduplicated` / `remaining_deduplicated`: `content_sha256` hashes assistant
*content*, not request identity, so the de-duplicated figure would understate spend. It stays visible as
`diagnostic_deduplicated` and is never subtracted.

## The standing rule: a stale baseline is not a baseline

A baseline is a *frozen* reading, not a re-derivation. It is only valid for the artefact whose sha256 it
names. Therefore:

- If `LEDGER-GRID-BASELINE-2.json`'s own sha256 changes, every delta measured against it is **void** —
  it was edited, not frozen. Quote the file sha alongside the delta; an unquoted delta cannot be audited.
- If `REQUEST-LEDGER.json` is regenerated **wholesale** (not appended to), the delta must be measured
  against a rows-file inventory diff, not only against `budget.spent`.
- A baseline that has stopped describing the ledger it pins (source sha mismatch, rows inventory
  disagreement) is stale. A stale baseline is **not** a baseline: freeze a new numbered file, point the
  old one at it via `supersedes`, and leave the old bytes untouched. That is exactly what v2 did to v1.
- v1 must never be repaired in place to match today's numbers. Ask for it explicitly if you want it:
  `ledger_delta.py --baseline experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json` reports
  `delta 27` against today's ledger — a true statement about a dated record, and the reason it is not
  the default.

## Rows-inventory guard (what it refuses)

Rows files are append-only, so `ledger_delta.py` compares the baseline's recorded inventory
(`rows_inventory.per_file`: file, rows, sha256) against the current ledger's `per_file` and refuses when:

- a rows file's **line count changed while its sha256 did not** — a count that moved with no sha change
  was never written by appending; or
- a **sha256 changed while the line count did not** — an in-place rewrite of an append-only file; or
- a rows file named in the baseline is **absent** from the current ledger.

A rows file that is *new* since the baseline is reported (`rows_guard_new …`), not refused: those are
the tranche's own rows. Implemented as `check_rows_inventory(base, cur)` in
`experiments/ptr-engine/tools/ledger_delta.py`, with red/green cases in `tests/test_ledger_delta.py`.
