# UNIT `TVS-ROWS-IDENTITY`

**Status:** done · **Date:** 2026-10-26 · **Bound:** 18 tool calls (used 18)

## Objective

Make every `tokens_to_verified_success` figure carry the sha256 of the rows file it was computed
from, and refuse to emit a figure it cannot bind. Offline, zero inference requests, no network.

## The gap as found

| Where | What it carried before |
|---|---|
| `experiments/ptr-engine/tools/tokens_to_verified.py:57-68` (`load_rows`) | opened the rows file, parsed lines, **hashed nothing**. No rows identity existed anywhere in the tool. |
| `experiments/ptr-engine/tools/tokens_to_verified.py:30-35` (`INSTRUMENT`) | the grader sha was a **hardcoded literal** `6893d5…3077`. |
| `experiments/ptr-engine/tools/tokens_to_verified.py:187-197` (cell record) | keys `grid, arm, declared_space, pass_turns, tvs, reason, duplicate_records_skipped, rows_in_file, requests_distinct, whole_run_total, code_state` — no path, no digest, no size. |
| `experiments/ptr-engine/measure/TVS.json` (cells 19/20/22) | identical key set; `"rows_sha256"` appears **nowhere** in the file (verified by scan). |
| `docs/TVS.md:5-7` | claims only that the metric is produced by `grade_v5` "sha256 `6893d5…3077`" — **no rows-file identity is claimed at all**, and the pinned grader sha no longer matches the grader file on disk (`056eb6…6772`). |

So a reader could recover neither *which* rows file a number came from nor *which bytes* of it.

## What changed

1. **`load_rows` reads once, hashes those bytes, parses those same bytes.** `read_rows_bytes`
   returns `(bytes, sha256)`; `load_rows` decodes and parses that buffer — never a second read.
2. **Five stamp fields on every emitted tvs record** (and echoed at record level):
   `rows_file, rows_sha256, rows_size, computed_at, grader_sha256`.
3. **`grader_sha256` is resolved through `tools/grader_identity.py`**, never a pin: a stamped grade
   document supplies its own `grader_sha256`; an unstamped one (every historical `grade_v5` file)
   resolves to `null` with `grader_sha_source: "unstamped_grade_document"` and the full
   `grader_identity` block, plus `grader_pin_check` recording that the declared pin does **not**
   match the grader bytes on disk. `grader_file_sha256_now` is a fact, not a claim.
4. **Refusal instead of a guess.** `RowsRefusal` exits **2** with `rows_missing`, `rows_unreadable`
   or `rows_sha_mismatch` (naming both shas) and emits `tvs: null`, `refused: true`,
   `refusal.number_emitted: false` — **no figure at all**. `--expect-rows-sha256` /
   `--expect-rows-size` let a caller pin what it expects.
5. **Additive restamp of `measure/TVS.json`**: 26 records (23 cells + 3 secondary) gained the five
   fields, each record also `grader_sha_source` / `grade_file` / `grade_sha256` / `grader_pin_check`
   / `identity_origin`; the three `tvs` sub-blocks gained the same five. Top level gained
   `restamped_at` (2026-10-26T18:58:30Z) and `restamp_method` (with `reproductions` and
   `grader_pin_check`). Nothing was deleted; no historical number was rewritten (verified: 0 numeric
   drift over all original leaves, 0 original keys lost).

## Evidence

Green — the three figures reproduce from their stamped bytes:

| grid | stored | recomputed | rows_sha256 | rows_size |
|---|---|---|---|---|
| `rows-longrun-v4-2026-10-26` | 48,347 | 48,347 | `999f298dac8b8356…` | 299,143 |
| `rows-longrun-v4-tools-2026-10-26` | 50,847 | 50,847 | `f11391aa2989949f…` | 169,988 |
| `rows-longrun-v6-tools` | 111,994 | 111,994 | `1e78d75f259afbe0…` | 225,648 |

Red — tampered byte:
`REFUSED rows_sha_mismatch: /tmp/tvs-rows-tampered.jsonl (expected sha256 1e78d75f…8b3e531e, actual
sha256 67ff2a1c…e6d06e56)` → exit 2, `tvs: null`, no number.
Red — deleted file: `REFUSED rows_missing: /tmp/tvs-rows-gone.jsonl (no such file)` → exit 2.

Tests: `PYTHONPATH=src python3 -m pytest tests/test_tokens_to_verified.py -q` → **9 passed**.
Verdict row recorded: PASS, exit 0, sha `f17663d1fed0162a7dc3c5a0a58d372c710974c3`.

## Not touched

`cell.py`, `run_longrun.py`, `analyze_stats.py`, `grade_v5.py`, any `rows-*.jsonl`, any published
`docs/` page, `PARM-1*`, `GRID-*.json`.

## Residual (recorded, not hidden)

`grader_sha256` is **null** for all three figures: their grade_v5 documents carry no stamp, and
re-grading is another unit's job. Those three numbers are now byte-traced to their rows but not
grader-traced. Fixing that means stamping/regrading, not restamping `TVS.json`.
