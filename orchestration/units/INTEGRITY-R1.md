# Unit INTEGRITY-R1 — prove the Round-1 record still re-derives before Round 2 numbers land on it

**Batch:** integrity gate ahead of the Round-2 (R2-*) measurement batch.
**Date:** 2026-10-23. **Unit type:** read-only verification (writes: its own card, its own handoff,
one verifier script, one guard test, one red→green capture). **No live requests, no lock, no GX10, no
writes to `papers/**` or `experiments/**`.**

## Objective

Before any Round-2 figure is placed on top of the Round-1 context-cache record, prove that the Round-1
record is still what its own pins say it is: every pinned row file, corpus, script and handoff
re-hashed; every claim re-derived; every guard still red→green. State plainly what is **not**
re-derived.

## Hard bound

`recompute.py all` ×2, `verify_package.py` ×3, `u5_recon.py` ×1, `u4_recon.py` ×1, attribution guard ×2,
pin guard ×4, verifier script ×5 — 18 runner invocations, one pass each, no retries. Stop condition:
if the verifier cannot be made green in 2 fix iterations, STOP and report `partial` naming the failing
check.

## Write paths (declared, no clash — no other unit running)

- `orchestration/units/INTEGRITY-R1.md`
- `orchestration/handoffs/INTEGRITY-R1.json`
- `tools/integrity/verify_round1_record.py`
- `tests/test_round1_record_pins.py`
- `state/logs/INTEGRITY-R1-redgreen.txt`

## What was done

1. Re-hashed every pin in `papers/context-cache/RUN.json` (units rows/events/analysis, `cell_digests`,
   `corpora`, the `pins` block, the verifier-handoff prefix and the `recompute.py` digest) and the 22
   source rows in `papers/context-cache/CLAIMS.md`.
2. Re-ran the three offline re-derivations: `recompute.py all`, `verify_package.py`, and the two
   script-backed claims `u5_recon.py` / `u4_recon.py`; plus the prose attribution guard.
3. Found the reuse hole that makes (2) insufficient, proved it, and closed it.
4. Captured red→green for both the new verifier and the new guard.

## Finding (the reason this unit was not a formality)

**A digest nobody recomputes is a pin in name only.** `verify_package.py` prints
`UNVERIFIED: none` and `recompute.py all` prints `60 claims checked, all match` on a tree whose
pinned row file has been truncated by one row, because:

- `verify_package.py` checks claim↔runner mapping and that "every referenced cell has rows" — it never
  compares bytes to a pinned digest;
- C63's expected values are aggregates over the **1,136** rows its filters select out of **2,780**
  across four files (`rows_per_cell` 284 = 4 arms × 71 turns), so the file's last line is invisible to it.

Closed by `tools/integrity/verify_round1_record.py` (85 checks, exit 0) and
`tests/test_round1_record_pins.py` (5 tests, the pin half of the record), both red→green proven on a
one-row truncation of `experiments/context-cache/cells/MOE-VLLM/rows.jsonl` and restored
byte-identical (`6658227689a35eee…`).

## Out of scope, stated so it is not implied

- Whether `recompute.py`'s **filters** select the right rows (only that the rows selected are those
  pinned). Flagged, not fixed: no recorded assertion ties `MOE-VLLM`'s `phase: probe`/`gate` rows to
  C63's admission rule.
- Whether the cells' prose agrees with their verifiers' rulings — `orchestration/STATUS.md` §8 item 3,
  still open, still needs its own unit.
- Anything requiring a live request.
