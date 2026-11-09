# CELL-STAMP-WIRING — what a fresh, unstamped grid cell does

**Question.** A fresh era-B cell's manifest carries **no `usable_for` key at all**.
Is its data silently included, silently skipped, or loudly refused — and what must
the grid run after each cell?

**Answer, one line:** **silently included.** It enters every statistic with one
stdout line saying so, exit 0. It is never certified and never refused.

Everything below is offline: no network, no live cell, zero requests.

---

## 1. The consumer's absent-stamp branch, quoted

All in `experiments/ptr-engine/longrun/analyze_stats.py`.

Resolution only matches a document that **has the key**:

```
analyze_stats.py:714   def usable_for_for_path(rows_path, manifests=None, sanity=None):
analyze_stats.py:722       if _norm_path(man.get("rows_path")) == target and USABLE_FOR_FIELD in man:
analyze_stats.py:728       if _norm_path(cell.get("path")) == target and USABLE_FOR_FIELD in cell:
analyze_stats.py:733   return {"usable_for": None, "reason": "", "source": USABLE_FOR_UNSTAMPED,
analyze_stats.py:734           "manifest_path": None}
```

`USABLE_FOR_FIELD in man` is the whole gate: no key ⇒ the `for` loop cannot match ⇒
the fall-through at `:733` returns `usable_for: None`, source `"unstamped"`
(`USABLE_FOR_UNSTAMPED = "unstamped"`, `analyze_stats.py:630`).

Exclusion is decided by **empty list**, not by absence:

```
analyze_stats.py:749           excluded = analyses is not None and len(analyses) == 0
analyze_stats.py:754           if not excluded:
analyze_stats.py:755               kept.append((path, count, rows))
```

`None` (absent) is not `[]` (stamped empty), so the cell is **kept**.

The CLI then reports it and exits **0**:

```
analyze_stats.py:1753           print("  usable_for unstamped  %s  (included: no usability stamp on "
analyze_stats.py:1754                 "disk -- not a certification)" % rec["name"])
```

Refusal happens only when *every* input cell was excluded:

```
analyze_stats.py:1760       print("  usable_for EXCLUDED every cell: no usable cells (%s)" % names)
analyze_stats.py:1761       raise SystemExit("no usable cells: every input cell is stamped "
analyze_stats.py:1762                        "usable_for: [] -- refusing rather than printing an "
analyze_stats.py:1763                        "empty table as success (%s)" % names)
```

Design intent is stated in the comment block at `analyze_stats.py:626`:
*"A cell with no stamp at all is INCLUDED and REPORTED `usable_for: unstamped`
-- it is not silently certified either."*

---

## 2. The three cases, built offline

Fixture: `experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl` — a **real
48-turn era-B-shaped** corpus (48 `kind="turn"` rows + 24 `tool-followup` rows = 72
rows), copied into `/tmp/stampwiring/rows.jsonl`. Manifests differ only in the stamp.
Command form (each case):

```bash
python3 analyze_stats.py --rows /tmp/stampwiring/rows.jsonl \
  --manifest /tmp/stampwiring/man-<case>.json --no-census --resamples 200
```

| case | manifest stamp | exit | analyser says | outcome |
|---|---|---|---|---|
| **(a)** key **absent** | — | **0** | `usable_for unstamped  rows.jsonl  (included: no usability stamp on disk -- not a certification)` | **interval printed**: `ttft_p50 n=48  144.81ms [143.58, 147.68]` |
| **(b)** `usable_for: ["h1","h2","h3"]` | list of str | **0** | `usable_for ['h1', 'h2', 'h3']  rows.jsonl  source=manifest` | **identical interval**: `ttft_p50 n=48  144.81ms [143.58, 147.68]` |
| **(c)** `usable_for: []` | empty list | **1** | `usable_for EXCLUDED  rows.jsonl  72 row(s) NOT analysed  source=manifest  usable_for=[]  reason=era A / partial` then `usable_for EXCLUDED every cell: no usable cells (rows.jsonl)` | **refusal**: `no usable cells: every input cell is stamped usable_for: [] -- refusing rather than printing an empty table as success` |

(a) and (b) are byte-identical in their statistics: **the absent stamp neither
excludes the cell nor marks it.** The only difference between the two runs is one
reporting line. (c) is the only state that refuses.

Note the fallback paths also exist but only fire when a *document* carries the key:
`measure/GRID-CELL-SANITY.json` (`analyze_stats.py:728`) and an explicit
`--manifest PATH` (`:722`). A census entry **with** `usable_for: []` for the same
`rows_path` will exclude an otherwise-unstamped cell; `--no-census` disables that.
An unstamped cell that the census does **not** know about is included, full stop.

---

## 3. The exact stamping command

`cell.py` is frozen, so the writer lives beside the consumer:
`write_cell_manifest_usable_for()` (`analyze_stats.py:777`) → `stamp_usable_for()`
(`analyze_stats.py:759`), exposed on the CLI by `--stamp-rows` (`analyze_stats.py:1647`).

Run from `experiments/ptr-engine/longrun`:

```bash
python3 analyze_stats.py --stamp-rows <CELL_ROWS_PATH> \
  --manifest-out <CELL_MANIFEST_JSON> \
  --usable-for "h1,h2,h3" \
  --usable-for-reason "<one line: what the scan proved>"
```

* `--usable-for ""` (empty string) stamps `usable_for: []` → the cell is **excluded by name**.
* `--manifest-out` may be omitted; the writer then resolves the manifest whose
  `rows_path` matches (`analyze_stats.py:784-792`) and **raises `FileNotFoundError`**
  when none does — the one loud failure mode in this path.
* `--dry-run` prints the would-be stamp and writes nothing.
* Shape written: `usable_for` is always a **list of strings**, `usable_for_reason` a
  string, `sort_keys=True, indent=1`, atomic `os.replace` (`analyze_stats.py:765-775`).

Proven on case (a):

```
BEFORE  usable_for present: False
        keys: ['N', 'arm', 'dry_run', 'rep', 'rows_path', 'run_id', 'schema']
$ python3 analyze_stats.py --stamp-rows /tmp/stampwiring/rows.jsonl \
    --manifest-out /tmp/stampwiring/man-a.json --usable-for "h1,h2,h3" \
    --usable-for-reason "era-B 48-turn scan: pointer-stable, zero truncation"
stamped usable_for=['h1', 'h2', 'h3'] into man-a.json          EXIT=0
AFTER   usable_for present: True  ['h1', 'h2', 'h3']
        "usable_for": [ "h1", "h2", "h3" ]   (man-a.json:9)
        "usable_for_reason": "era-B 48-turn scan: ..."   (man-a.json:14)
```

Re-run of the analyser after stamping:

```
before:  usable_for unstamped  rows.jsonl  (included: ... not a certification)
         ttft_p50 n=48  144.81ms [143.58, 147.68]
after:   usable_for ['h1', 'h2', 'h3']  rows.jsonl  source=manifest
         ttft_p50 n=48  144.81ms [143.58, 147.68]
```

**The numbers do not change.** Stamping a good cell changes nothing in the
statistics — it changes *what the record claims*, and it arms the exclusion path for
the cell that later turns out to be unusable. That is the entire value, and it is why
an unstamped cell is a compliance gap rather than a numeric one.

Stamping to empty on the same manifest flips it to a refusal:

```
$ python3 analyze_stats.py --stamp-rows ... --manifest-out man-a-empty.json --usable-for ""
stamped usable_for=[] into man-a-empty.json   →  next analyse run: no usable cells, exit 1
```

---

## 4. What RUN-A-STAR-2 must run after **each** cell

Run this **after every finished cell**, not only after the last one — the stamp is the
only thing that can exclude a bad cell, and a cell that finishes before the batch ends
is otherwise unexcludable for the whole remainder of the run (a crash or a kill before
the final stamp leaves every completed cell certified-by-omission).

Copy-paste, from `experiments/ptr-engine/longrun` (one line; `UF` is what the cell's
sanity scan proved — `h1,h2,h3` when clean, empty when not):

```bash
UF="h1,h2,h3"  # or UF="" for a cell the scan rejected
python3 analyze_stats.py --stamp-rows "$CELL_ROWS" --manifest-out "$CELL_MANIFEST" \
  --usable-for "$UF" --usable-for-reason "$CELL_REASON" \
&& grep -q '"usable_for"' "$CELL_MANIFEST" && echo "STAMP OK $CELL_MANIFEST"
```

**What to check that the stamp took** — all four, because the first is vacuous on its own:

1. **Exit 0** of the stamp command (a missing manifest raises `FileNotFoundError`, exit 1).
2. **The key exists in the file**, not just in stdout:
   `grep -q '"usable_for"' "$CELL_MANIFEST"` — the writer rewrites atomically, so a
   post-write read is the real evidence.
3. **The value is what was intended**, and empty is distinguished from absent:
   `python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));assert "usable_for" in d;print(d["usable_for"])' "$CELL_MANIFEST"`
   ⇒ `[]` means "excluded, on purpose"; *key error* means the stamp never landed.
4. **The analyser agrees**, cheaply: `--no-census` is not needed here, but the
   reporting line must read `source=manifest` (not `unstamped`). Run
   `python3 analyze_stats.py --rows "$CELL_ROWS" --manifest "$CELL_MANIFEST" | grep usable_for`
   and require `source=manifest`.

Do not skip the stamp for a "partial/in-progress" cell and expect a later pass to catch
it: a partial cell without a stamp is included, and `GRID-RESUME-TOOL` already reports
the two existing cells as `usable_for=[]` precisely because someone did stamp them.
The unwritten third state — no key — is the one that leaks.

**If stamping after each cell were unnecessary**, the code that would make it
unnecessary is absent: there is no default-deny. `analyze_stats.py:749` defaults to
*include* (`analyses is not None and len(analyses) == 0` is `False` for `None`), and
`analyze_stats.py:733` deliberately returns `None` rather than `[]` so the analyser
cannot invent a permission. Until that default flips to deny-by-absence, per-cell
stamping is the only mechanism.

---

## 5. The guard: `tests/test_stamp_wiring.py`

9 tests, green on the current code, all offline (`PYTHONPATH=src python3 -m pytest
tests/test_stamp_wiring.py -q`). They pin:

* `usable_for_for_path` → `{"usable_for": None, "source": "unstamped"}` for a manifest
  with **no** key (§1 branch), and `_usable_list(None) is None`;
* `select_usable_cells` keeps that cell with `excluded is False, analyses is None`;
* `[]` excludes while absent includes — the two records stay distinguishable;
* CLI: absent ⇒ exit 0 + `usable_for unstamped`; stamped ⇒ exit 0 + the list +
  `source=manifest`; empty ⇒ exit 1 + `no usable cells` + the refusal sentence;
* the writer stamps `["h1","h3"]` into a manifest that had no key, round-trips, and
  raises `FileNotFoundError` for a rows path with no manifest.

**Red→green.** `test_guard_bites_when_absent_is_treated_as_usable` rewrites a *copy* of
`analyze_stats.py` with the absent-key branch replaced by `treat absent as usable`
and asserts the invariants break. The branch in the real file is **not** changed.
Same mutation run standalone proves the pin:

```
REAL   (green)  usable_for=None                 source='unstamped'  invariant holds: True
MUTANT (red)    usable_for=['h1', 'h2', 'h3']   source='manifest'   invariant holds: False
```

The guard also fails loudly if that branch ever moves or changes shape
(`assert src.count(ABSENT_BRANCH) == 1`), so it cannot quietly stop testing anything.

---

## 6. Not changed

`analyze_stats.py` thresholds, `analyze.py`, `cell.py`, `run_longrun.py`, rows,
grades, `PARM-1` and every published page are untouched. No `measure/cell-*.json`
was written; all manifests in this work lived under `/tmp`. The absent-key branch is
**reported only**.
