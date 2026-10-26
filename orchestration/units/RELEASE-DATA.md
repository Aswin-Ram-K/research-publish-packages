# RELEASE-DATA — make the shipped release tree self-sufficient

**Status:** done (with one named limitation, L1) · **Date:** 2026-10-24 23:22 CDT
**Write paths:** `release/**`, `orchestration/units/RELEASE-DATA.md`, `orchestration/handoffs/RELEASE-DATA.json`
**Bound:** 40 tool calls (used 27).

## Why

`V2-CURRENT` found the release was not self-sufficient: from `cd release/v0.1`,
`papers/context-cache/recompute.py all` and `recompute_r2.py all` exited 1 with
`FileNotFoundError: .../release/v0.1/state/config/rows.jsonl`, leaving C65, C66, C67, C68 and SYSOPT
unreachable (the verifier counted 6 of 69 claims as not re-derivable: C62, C63, C65, C66, C67, C68).
`tests/test_gap_closure_ledger.py` failed 8/8 on `FileNotFoundError: .../state/gap-ledger.json`.

## What was done

1. **Shipped `state/config/rows.jsonl`** (82,565 bytes) — the single file both runners need. It resolves
   through the *release* root: `recompute.py:1640` `C63_R2_CELLS = {"R2-VLLM-CELL": ROOT / "state" / "config" / "rows.jsonl"}`
   and `recompute_r2.py:557` `C65_R2_PATH = [ROOT / "state" / "config" / "rows.jsonl"]`, with
   `ROOT = Path(__file__).resolve().parents[2]`. Nothing else from `state/` (1.6 GB) was copied.
2. **Shipped `state/gap-ledger.json`** (25,834 bytes) — the file `tests/test_gap_closure_ledger.py:24` reads
   (`LEDGER = ROOT / "state" / "gap-ledger.json"`). Without it the guard crashes 8/8 on a missing file, which
   *hides* the real limitation; with it the guard reports its true state (2 passed, 6 failed on content refs).
   This is the minimal set that makes the claims re-derivable **and** makes the remaining red honest.
3. **Sanitisation:** both files measured before copying — `192.168.` occurrences **0**, `/home/zer0null`
   occurrences **0** — so **0 replacements** were needed and the shipped bytes are the live bytes.
   `rows.jsonl` re-validated as JSONL: 284 non-blank lines, each a valid object.
4. **`MANIFEST.json` recomputed from disk** (not appended to): 943 → **945** entries,
   61,035,244 → **61,143,643** bytes; on disk **946** files, so entries == files − 1; manifest never lists
   itself; all 945 `{path, bytes, sha256}` triples re-verified against disk with **0 mismatches**. A new
   `state_files_added_2026_10_24` key records the additions, the sanitisation result and what is still absent.
   One `.pytest_cache/` created by an early unfiltered pytest run was deleted before the recompute, so no test
   residue is listed or shipped (subsequent pytest runs use `-p no:cacheprovider`).
5. **`release/REPRO.md` rewritten** with the measured verdict and exit codes; every command uses
   `papers/context-cache/…` from `cd release/v0.1`. The stated path defect did not reproduce (see D7 below);
   what was wrong — the stale `NO as shipped` verdict, the 943-file header, and a `$OLDPWD/.venv/bin/python`
   line pointing at a nonexistent interpreter — is corrected.
6. **`release/REPORT.md` § 11 appended** with the defect, the fix, the file-count change and limitation L1.

## Evidence (all from `cd release/v0.1`, `PYTHONDONTWRITEBYTECODE=1`)

Interpreter: `/home/zer0null/reserach extarctor/.venv/bin/python` (3.14.4) = `../../.venv/bin/python`.
`release/.venv` and `release/v0.1/.venv` do **not** exist; the card's `../.venv/bin/python` is wrong.

| Command | Exit | Decisive output |
|---|---|---|
| `papers/context-cache/verify_package.py` | **0** | `verify_package: PASS — 69 claims in CLAIMS.md, 69 mapped 1:1, 8 script-backed + 61 recompute.py-backed functions all present, every referenced cell has rows, UNVERIFIED: none` |
| `papers/context-cache/recompute.py all` | **0** | `COVERAGE GUARD PASS  69 claims documented, 67 runnable here + 2 script-backed` (+ `GRID GUARD PASS  7/7 configs`, `64 claims checked, all match`) |
| `papers/context-cache/recompute_r2.py all` | **0** | 7 × `PASS n/n values match`: 61/61, 38/38, 48/48, 75/75, 85/85, 70/70, 50/50 |
| `-m pytest tests/test_gap_closure_ledger.py -q` | **1** | `6 failed, 2 passed in 0.07s` — `AssertionError: unresolvable evidence refs:` → `G11: orchestration/VERDICTS.md:12 (file_line) does not resolve` |
| `-m pytest tests/test_g5_fanout_attribution.py -q` | **0** | `4 passed in 0.01s` |
| `-m pytest tests/test_paper_g3_bands.py -q` | **0** | `13 passed in 0.02s` |
| `grep -rE '192\.168\.' release/v0.1 \| wc -l` | — | `0` |
| `grep -rE '/home/zer0null' release/v0.1 \| wc -l` | — | `0` |
| manifest check | — | entries 945, files on disk 946, entries == files−1 → True, sha256 mismatches 0 |

## Limitation L1 — recorded, not faked green

The gap-closure ledger guard fails on **9 unresolvable content refs** that a publication cannot contain:
`orchestration/VERDICTS.md:12` (G11); five `scratch/cache-audit/docs/pin_*` pinned upstream sources (G16); the
handoffs `CACHE-AUDIT` (G16) and `PAPER-FINAL` (G17); plus `state/config/live-server-config.json` (G16,
61,336 bytes, a serving-host config carrying two internal addresses — excluded by the same policy as the other
167 redacted files) and `state/sys-opt-verdict.json` (G17, a workspace verdict document, not a numeric source).
The four status-recomputation tests fail as a consequence of the same cause.

`orchestration/` and `scratch/` were **not** shipped: they are workspace provenance, they are in no manifest,
and publishing them would not make a single claim more re-derivable. The guard is a working-tree invariant —
`8 passed` live, red in any faithful artefact — so its red state here is a property of the package boundary, not
a numerics finding. It is not evidence about the 69 claims, which re-derive in full shipped-tree-only.

## Assumptions

- **A1** — "the minimum that makes the claims re-derivable" = `state/config/rows.jsonl` alone. Confirmed: with
  it, both runners exit 0 and print the full COVERAGE GUARD PASS line; the other four `state/` files are not
  reachable from the claim paths.
- **A2** — shipping `state/gap-ledger.json` as well is within scope: it is one small data file under a declared
  write path, it is required by the guard the card asked me to run, and without it the guard's failure mode is a
  missing file rather than the limitation the card asked me to document.
- **A3** — `state/config/live-server-config.json` and `state/sys-opt-verdict.json` were **not** shipped:
  the first carries internal serving-host addresses (sanitisation policy), the second is a verdict document that
  is not a numeric source. Trade-off recorded in L1 rather than resolved by widening the package.
- **A4** — the card's claim that `REPRO.md` documented root-level commands did not reproduce
  (`grep -rnE 'python +verify_package\.py|…' release/` → nothing). I fixed what was actually wrong there and
  recorded the non-reproduction as REPRO deviation D7 instead of manufacturing a change to match the brief.
- **A5** — pytest runs use `-p no:cacheprovider` so the guard check leaves no `.pytest_cache/` in the artefact;
  this changes no test behaviour.
