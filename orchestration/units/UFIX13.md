# UFIX13 — bounded correction pass on CPRIME_MEASUREMENT.md

**Unit:** UFIX13 (correction unit; did not author the report). **Date:** 2026-10-15.
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a.
**Purpose:** apply, verbatim in substance, the four corrections listed in
`strategy/VERIFICATION_REPORT_13.md` (unit UVER13, verdict `pass`, 29 tool calls, its §5), plus record the
not-reproduced 25-of-190 variant. Nothing UVER13 reproduced was re-derived or changed.
**Bound:** ≤12 tool calls. **Used: 6.**
**Write paths (only these):** `strategy/CPRIME_MEASUREMENT.md`, `orchestration/units/UFIX13.md`,
`orchestration/handoffs/UFIX13.json`.

## Result

- Target, before: 323 lines, 21,748 B, sha256 `13d0712ebecf77a086747115fcda7e21d989642aa8a001e5c17d7e015f338dcb` (matched).
- Target, after: **368 lines, 26,018 B, sha256 `184daf02ba6e81fb039ea52490284411a6cfd55aa8aa02d1380cdd51bfb6d42c`**.
- Method: one assertion-guarded Python patch — each edit's `before` text asserted to occur exactly once in its
  line range before slicing; ranges applied bottom-up; every before/after printed verbatim.

## Evidence checked before each edit

- **C1:** `scratch/uneutral3/census-tree-bij.txt` (11,663 B, mtime Oct 15 20:06) lines 3-4 read exactly
  `distinct identifiers hit: 99 of 184` / `TOTAL OCCURRENCES: 8213`; siblings `census-tree-pinned.txt` (TOTAL 26344),
  `census-tree-stripped.txt` (TOTAL 9247); `ls scratch/uneutral3/` shows no census scanner (only `strip.py`,
  `bij.py`, `run_diags.sh`, `gen-pinned.log`, `strip-report.json`); census file header line 1 is
  `tree: scratch/uneutral3/tree-bij`, so it is the superseded 20:06 build.
- **C2:** `sed -n '316p' repro/encoder-crossover-190-SANITISED/harness/train.py` →
  `    print(f"  fitting on {len(labels)} (situation, option) pairs", flush=True)`; `grep -n '\["situation"\]'`
  returns `train.py:311`, `train.py:322`, `tccommon.py:163` only.
- **C3:** `c78681d6…` is the live corpus digest that `tccommon.py:64 CORPUS_SHA256` pins; pinned=stripped
  `58b09a3c…`; red→green outcome is UVER13 §6 (exit 2 RED / exit 0 GREEN in both copies, full 2,205,127 / 484,922 B re-emit).
- **C4:** `grep -n 'metrics.json\|labelsB\|ALL CLAIM NUMBERS PRESERVED' repro/encoder-crossover-190-SANITISED/verify/recompute-claims.py`
  → `:113 jload("second-labeller","metrics.json")`, `:115-117` reads `closed_subset`/`roster_and_bespoke_subset`/`AB_mutual_agreement`,
  `:125 print("\n  ALL CLAIM NUMBERS PRESERVED:", ok)`; UVER13 §1/§5.5/§1a/§3 give 15,417/7,851/4,463, 9,531 and 21 files.

## Edits (verbatim before/after)

### C4a — :9-12 (reader's warning)

**Before:**
```
> `verify/recompute-claims.py` prints `ALL CLAIM NUMBERS PRESERVED: True` **even on a tree where route A has
> moved**. It reads neither JSONL and never recomputes route A. That `True` was reproduced by me on all three
> trees — including `tree-bij`, whose fixture-correctness digest is *not* the one UNEUTRAL3 claimed. **Do not
> cite that `True` as evidence that no number moved.**
```

**After:**
```
> `verify/recompute-claims.py` prints `ALL CLAIM NUMBERS PRESERVED: True` **even on a tree where route A has
> moved**. It reads no JSONL and never recomputes route A from the data — but it is **not vacuous**: it does
> read `second-labeller/metrics.json` (`:112-118`) and compares the stored second-labeller numbers against
> frozen constants, so moving a stored `labelsB` number makes it print `ALL CLAIM NUMBERS PRESERVED: False`
> and **exit 1**. It is a **consistency check between the claimed numbers and the stored metrics/labels**, not
> a recomputation. That `True` was reproduced by me on all three trees — including `tree-bij`, whose
> fixture-correctness digest is *not* the one UNEUTRAL3 claimed. **Do not cite that `True` as evidence that no
> number moved.**
```

### C4b — :135-138 (§4 mixed walk)

**Before:**
```
**Why the pinned raw-line count (26,344) differs from a decoded-value count (16,813).** My value-level walk
(`scratch/uneutral4/floor.py`, case-insensitive over JSON values) totals pinned **16,813**, stripped **9,247**,
bij **5,384** — the stripped and bij totals agree with `census2.py` *exactly*, which validates the walk (the
first version of my walk undercounted because it used `low.count(i)` without `i.lower()`; fixed). The pinned
```

**After:**
```
**Why the pinned raw-line count (26,344) differs from a decoded-value count (16,813).** `floor.py` is a **MIXED**
walk: decoded values+keys for the 19 JSON files, raw text for every non-JSON file. Under that mixed method it
totals pinned **16,813**, stripped **9,247**, bij **5,384**; a strict decoded-only walk gives pinned **15,417**,
stripped **7,851**, bij **4,463** (inside-stimulus 2,171 / 30 is unaffected). The stripped and bij totals agree
with `census2.py` *exactly* only because the mixed walk counts non-JSON files raw — that cross-check is partly
circular, not an independent validation (the first version of the walk undercounted because it used
`low.count(i)` without `i.lower()`; fixed). The pinned
```

### C4c — :110 (§3 stale build)

**Before:**
```
20:07:57; `diff -rq tree-bij rt/bij` shows ~20 differing data files. The on-disk `tree-bij`, my two fresh
```

**After:**
```
20:07:57; `diff -rq tree-bij rt/bij` shows 21 common files differing (plus 11 files only in `rt/bij`). The on-disk `tree-bij`, my two fresh
```

### C4d — :141 (§4 escape gap)

**Before:**
```
(3,180 + 3,179 + 3,178 = 9,537, ~the whole gap). Those characters do not exist in the decoded data, and they
```

**After:**
```
(3,177 + 3,177 + 3,177 = 9,531 — the raw identifier hits 3,180 / 3,179 / 3,178 include 6 genuine `.ts`/`.sh`
hits counted by both methods). Those characters do not exist in the decoded data, and they
```

### C4e — :235 (§7 kind-token count)

**Before:**
```
`(?<![A-Za-z0-9_.])k(?![A-Za-z0-9_])`; 25 of 190 by lowercase substring; 75 of 190 questions contain *some*
```

**After:**
```
`(?<![A-Za-z0-9_.])k(?![A-Za-z0-9_])`; UVER13's lowercase-substring alternation over the 7 live kinds also
gives **23/190** — the earlier "25 of 190 by lowercase substring" did **not** reproduce; 75 of 190 questions contain *some*
```

### C2 — :158 (§5 read-site table row)

**Before:**
```
| `situation` | `harness/train.py:311`, `:316`, `:322`; `harness/tccommon.py:163` |
```

**After:**
```
| `situation` | `harness/train.py:311`, `:322` (the `:316` hit is a print statement, not a field use); `harness/tccommon.py:163` |
```

### C3 — :197-198 (§6 prepare.py paragraph)

**Before:**
```
ever ran. Consequence: **the released tree cannot regenerate its own JSONL; the strip is one-way.** (`tree-bij`
differs because the bijection renamed data in `corpus.json` too.)
```

**After:**
```
ever ran. Consequence: **the released tree cannot regenerate its own JSONL under its pinned corpus — but the
strip is not one-way.** Red→green [UVER13]: restoring the live corpus (digest `c78681d6…`) makes
`harness/prepare.py` **exit 0 in both the pinned and the stripped copies**, and it re-emits the **FULL
unstripped** JSONL — 2,205,127 B train / 484,922 B dev. So the refusal is caused by the **corpus-digest pin**
alone, not by the strip; regeneration is blocked by that pin alone, and a reader who restored the pinned corpus
would regenerate the *pre-strip* artifact. (`tree-bij` differs because the bijection renamed data in
`corpus.json` too.)
```

### C1a — :291-293 (§9.2)

**Before:**
```
2. **The claimed bij census `8,213` / `99 of 184` has no on-disk source.** Reproduced: `tree-bij` → 5,384/95;
   my deterministic rebuild → 5,384/95; `rt/bij` (superseded) → 9,768/99. No scanner exists under
   `scratch/uneutral3/`, so the number cannot be regenerated by any command I could find.
```

**After:**
```
2. **The claimed bij census `8,213` / `99 of 184` has a printed on-disk source, but no scanner behind it.**
   `scratch/uneutral3/census-tree-bij.txt` (11,663 B, written 20:06) contains exactly `TOTAL OCCURRENCES: 8213`
   and `distinct identifiers hit: 99 of 184`, with siblings `census-tree-pinned.txt` (26,344) and
   `census-tree-stripped.txt` (9,247). What is missing is the **scanner**, not the number: no census script
   exists under `scratch/uneutral3/` (the scanner is `scratch/uneutral2/census2.py`), so the claim cannot be
   regenerated in place. The file is a **superseded 20:06 build** — the same build that yields the `rt/bij`
   diagnostics and the stale `30b75581…` digest. Re-measured on the on-disk tree: `tree-bij` → 5,384/95; my
   deterministic rebuild → 5,384/95; `rt/bij` (superseded) → 9,768/99.
```

### C1c — :323 (§10 index; row appended)

**Before:**
```
| `scratch/uneutral3/{strip.py,bij.py,run_diags.sh,gen-pinned.log,strip-report.json}` | the builders under test |
```

**After:**
```
| `scratch/uneutral3/{strip.py,bij.py,run_diags.sh,gen-pinned.log,strip-report.json}` | the builders under test |
| `scratch/uneutral3/census-tree-{pinned,stripped,bij}.txt` | the 20:06 census outputs (26,344 / 9,247 / 8,213); no scanner under `scratch/uneutral3/` writes them |
```

## Also recorded (not a correction)

UVER13's own count of fixture questions carrying a real kind token is **23/190**, and its lowercase-substring
alternation over the 7 live kinds also gives 23/190 — the report's "25 of 190 by lowercase substring" **did not
reproduce**. Applied at `:235`.

## Corrections note appended to the report

A closing `## Corrections applied` section (date 2026-10-15) names UVER13, its verdict, bound and §5, and lists the
four corrections plus the 23/190 record. It states that no number UVER13 reproduced was changed.

## Bounds respected

No writes outside the three declared paths; `strategy/VERIFICATION_REPORT_13.md`, `repro/`, `scratch/**`,
`papers/**` and `/home/zer0null/Duval` untouched; no build run; no git invoked.
