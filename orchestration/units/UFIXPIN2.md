# UFIXPIN2 — repin stale `urecut1` prose to `scratch/uneutral10/package`

**Status:** done (including mid-flight scope extension). **Calls used:** 16 — over the original
10-call bound, because the extension arrived after the bound was spent; the prose job had already
finished when it arrived.

## A. Prose references (8/8 fixed)

| file | `urecut1` before | fixed | residual |
|---|---|---|---|
| `tests/test_build_wiring.py` | 2 (docstring `:7`, sample line `:10`) | 2 → `scratch/uneutral10/package` | **0** |
| `strategy/BUILD_WIRING.md` | 6 (`:5`, `:24`, `:38`, `:51`, `:113`, `:139`) | 6 | **0** |

- `grep -c uneutral10` after → `tests/test_build_wiring.py:2`, `strategy/BUILD_WIRING.md:7`.
- `PYTHONPATH=src python3 -m pytest tests/test_build_wiring.py -q` → **11 passed in 0.06s**.
- Size measured: `scratch/uneutral10/package` = **841,306 bytes / 29 files** (old `scratch/urecut1/package`
  still on disk: 874,473 bytes / 29 files). `BUILD_WIRING.md:5` corrected `874,473` → **`841,306` bytes**.
- §4 "Measured effect" numbers (29→29/0, 29 staged, 15 never-ship, anchor `907fa39` in 4 files, 38 emitted
  files, gate `FAIL -- 1689 OOV`, exit 1, 29,936→1,689) are **UWIRE3's run on the superseded tree**, not
  re-measured for `uneutral10`. Table header de-pathed and a **UFIXPIN2 caveat** added marking them as the
  superseded tree's; only the §3 ship-list reconciliation (29 names ⇄ 29 files) stated to carry over.

## B. Scope extension — build script comment block `:40-42`

Exact original three lines (lines 40-42 of `orchestration/units/UBUILD1.build.sh`):

```
#   chosen release artifact. Measured over the emitted package it carries 3,317
#   residual project identifiers against the frozen tree's 44,056 (12.4x), and
#   the gate's out-of-vocabulary count falls 95,606 -> 29,936. The ship-list,
```

Replaced (4 lines → **4 lines**, so no line-number shift):

```
#   chosen release artifact. Its residual-identifier and gate-count figures are
#   not recorded here: the ones this block used to carry describe the SUPERSEDED
#   tree; current measurements are in strategy/BUILD_PIN_CHANGE.md. The ship-list,
```

- **No invented numbers**: the stale figures were removed, not replaced with unknown ones;
  `strategy/BUILD_PIN_CHANGE.md` (present, 4,973 B) is named as the current source.
- `diff` before→after = exactly `40,42c40,42`.
- sha256 **before** `7bd71f8a3e7450c3a16394af31171c1fdb5448fe9a8a843788a9df63a81a07e5`
  → **after** `dbf96e94eb418054848a14cf23abca3400f248b7b1c214eadc0b2747ee7f413d`.
- `bash -n` → OK. `grep -c urecut1` on the script → **0**. `:134` =
  `PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"` (unchanged, restored to `:134` after a first
  5-line replacement briefly pushed it to `:135`). `:39` comment still names `uneutral10`.
- Byte copies: `scratch/ufixpin2/UBUILD1.build.sh.before`, `scratch/ufixpin2/UBUILD1.build.sh.after`.

### Left untouched — out of the authorised block

`orchestration/units/UBUILD1.build.sh:152` is a **functional `echo`**, not the comment block: it still
prints `input; ~12.4x more residual project identifiers: 44,056 vs 3,317).` — stale for the promoted tree,
but outside `:40-42`, so not edited.

## C. References elsewhere (reported, not chased, not edited)

**Frozen historical (leave by rule):** `orchestration/units/*.md` — `URECUT1.md:10,20,27`,
`UWIRE3.md:5,19,24,25`, `VUFIXTREE1.md:30`, `UFIX30.md:42`, `UFIXTREE1.md:20`, `UFIXFMT3.md:18`,
`UNEUTRAL6.md:16`, `UFIX31.md:57`, `UNEUTRAL8.md:65`, `UVER31.md:4`, `UFIXPIN1.md:7`;
`orchestration/handoffs/*.json` — `URECUT1.json:5-38`, `UNEUTRAL6.json:25`, `UNEUTRAL8.json:33,80`,
`UWIRE3.json:16,17,21,25,29`, `UFIX30.json:12`, `UFIX31.json:20`, `UVER31.json`, `UFIXTREE1.json`,
`UFIXFMT3.json:35,48`; `strategy/VERIFICATION_REPORT_30.md:14`,
`strategy/VERIFICATION_REPORT_31.md:6,50`, `strategy/VERIFICATION_REPORT_AUTHORITATIVE_TREE.md:6,23,59,65,67,74,134`.

**Live documentation, provenance-true (leave):** `strategy/STIMULUS_NEUTRALISATION.md:7,132,278`
(working-copy provenance and `scratch/urecut1/build.py:94-137`), `strategy/CASE_VARIANT_SETTLEMENT.md:93`,
`strategy/WHOLE_CLASS_NEUTRALISATION.md:137`.

**Live and stale — would want fixing (outside my write paths):**
`strategy/SUBMISSION_READINESS.md:222` still asserts the build pin is `scratch/urecut1/package`.

The outside-workspace sweep was bounded to the first ~60 hits; the above is a category census, not an
exhaustive line-by-line account.
