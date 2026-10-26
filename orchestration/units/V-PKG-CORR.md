# V-PKG-CORR — verify the package after the ground-truth restore and the MTP sign flip

**Verdict: FAIL** (one mandated check fails; the other five reproduce). Verifier unit, independent of
the authors of the restore and the MTP correction. Offline: zero live requests, no GX10, no docker,
`.occamy.lock` untouched. 17 tool calls of a 20 bound.

## Contract source

The board-delivered prompt was a generic verifier stub with no subject. The authoritative contract is
task card `be6d5796-127e-41bc-97e4-b4535d3683d9` ("V-PKG-CORR — verify the package still holds after
the ground-truth restore and the MTP sign flip"); its `description` carries the six checks. Read with
`task_board_list`.

## Purpose

Try to break the package after two changes: (1) `experiments/context-cache/cells/PROMPT-O1/rows.jsonl`
restored from `rows.pre-correction.jsonl` after a bad "repair" was falsified (repaired file quarantined
as `rows.repaired-DO-NOT-USE.jsonl`); (2) the MTP correction flipped the published C63 signs
(`engine_effect` 1225.18 -> 549.33; `model_effect` +275.83 -> -400.02).

## Write paths

- `orchestration/handoffs/V-PKG-CORR.json`
- `orchestration/units/V-PKG-CORR.md`

Nothing under `papers/`, `state/`, `experiments/` or `dockets/` was written; the red->green experiment
ran on a `/tmp/vpkg_rg` copy with symlinked `experiments/` and `state/`.

## Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | `python3 papers/context-cache/verify_package.py` | PASS | `EXIT=0`; "verify_package: PASS — 63 claims in CLAIMS.md, 63 mapped 1:1, 2 script-backed + 61 recompute.py-backed functions all present, ... UNVERIFIED: none" |
| 2 | `.venv/bin/python papers/context-cache/recompute.py all` | PASS | `EXIT=0`; "60 claims checked, all match"; 4 `COVERAGE GUARD ok`; "COVERAGE GUARD PASS 63 claims documented, 61 runnable here + 2 script-backed". Printed count is **60**, not 63: `recompute.py:1234 SPECIAL = {"C61": lambda: grid_guard()}` and `:2333-2334 claims = list(FUNCS)` exclude the C61 special runner from `all`. |
| 3 | `.venv/bin/python papers/context-cache/grid_guard_selftest.py` | PASS | `EXIT=0`; GREEN "GRID GUARD PASS 31 file(s), 9121 sglang cached_tokens, every one a multiple of 64"; its own planted RED (row 3 `cached_tokens=1409`) -> "GRID GUARD FAIL ... 1 off-grid"; removal -> PASS again. |
| 4 | `pytest tests/test_paper_attribution_guard.py tests/test_claims_decompose.py tests/test_serving_brief.py -q` | PASS | `EXIT=0`; "34 passed in 5.59s". Extra (not on the card): `test_cached_dedupe.py` + `test_c63_ratio_raw_operands.py` -> "13 passed in 0.85s". |
| 5 | falsified-number sweep over `papers/` | **FAIL** | `3.3133` (11 occurrences / 10 lines) and `1.700` (40 / 10 files) are everywhere disclosed as superseded/withdrawn. `137.8`, `390.80`, `-53.85` have **zero** hits. But **`papers/context-cache/PACKAGE.md:70-76` presents the pre-MTP numbers as live**: "+1,225.18 ... 2.6738x ... 91.2 % of the grand mean, while the model main effect is +275.83 ... +548.06 under vLLM ... interaction of +272.23", with no supersession marker. `CLAIMS.md:219-220` marks every one of those SUPERSEDED and replaced. |
| 6 | C63 published values + red->green | PASS | `CLAIMS.md:219-220` carries `+549.33 [462.4, 631.9]`, `-400.02 [-474.2, -326.5]` and the disclosure "the Round-1 vLLM dense cell ran with `--speculative-config mtp`; removing it re-measured that cell 2,230.7782 -> 879.0669". `recompute.py C63` -> "PASS 43/43 values match". Red->green in `/tmp`: baseline PASS 43/43; revert `recompute.py:2176 '"engine_effect": 549.33'` -> 1225.18 => "FAIL engine_effect recomputed=549.33 paper=1225.18 / FAIL 42/43"; restore => PASS 43/43. Patching the CLAIMS row instead changes nothing (still PASS) — expected values live in `recompute.py`, not `CLAIMS.md`. |

## Restore integrity

`rows.jsonl` and `rows.pre-correction.jsonl` are byte-identical, 355 lines, 238,087 B, sha256
`dc0774d8…01eff`; the quarantine `rows.repaired-DO-NOT-USE.jsonl` is 355 lines, 240,711 B, sha256
`58c95fae…269c` — both match the card's stated digests.

## Defect to repair (blocker)

`papers/context-cache/PACKAGE.md:67-76` (§3 item 6) states the superseded C63 values as the finding.
Its own superseded markers sit at `PACKAGE.md:112`, `:201`, `:223` — none covers item 6.

## Corrections / notes

- `CLAIMS.md:219` reads "MTP CORRECTION (**2024**-10-24)"; today is 2026-10-24 — a year typo, cosmetic.
- The card's check-6 mechanism ("run the C63 recompute against the /tmp copy if the harness supports a
  path argument") is false: `recompute.py` has no path argument (`main()`, `:2325-2357`, takes claim
  ids; `CLAIMS_MD_PATH` fixed at `:2362`). The card's fallback guard line in
  `tests/test_paper_attribution_guard.py` does not exist (0 hits for `C63`/`549.33`/`400.02`/`1225.18`);
  the real number guard is `recompute.py:2176`, exercised red->green above.
