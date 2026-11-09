# REGRADE — one command that re-derives a published grade

**Tool:** `experiments/ptr-engine/tools/regrade.py` · **Tests:** `experiments/ptr-engine/longrun/tests/test_regrade.py` (8 passed) ·
**Report table:** `experiments/ptr-engine/measure/REGRADE.json` · **Offline:** zero inference requests, zero network.

`regrade.py` takes a rows file (one, many, or `--all`), the fixture, and a grader module plus
its `sha256`; it runs the **grader that produced the published grade** and writes a *fresh*
grade to `experiments/ptr-engine/measure/regrade/<rows-stem>.grade-v5.json`. It never edits or
overwrites an existing grade file, a rows file, `TVS.json`, `LATENCY-REPORT.json`,
`REQUEST-LEDGER.json` or anything under `longrun/tasks*/`.

Every output records the grader's `sha256` (`grader_sha256`), the grader path and the pinned
`generated_at`, so **a grade carries its own provenance**. The same sha is printed on stdout.

---

## 1. The command per paper-figure class

All examples run from the workspace root (`/home/zer0null/research extractor`).

### Quality figure — `checkpoint_accuracy` over a rows file / a set of rows files

```bash
python3 experiments/ptr-engine/tools/regrade.py \
  --rows experiments/ptr-engine/measure/rows-longrun-c-2026-10-26.jsonl \
  --as-of 2026-10-26T16:00:00+00:00
```

Read `arms.<arm>.checkpoint_accuracy` and its **decidable denominator**:
`arms.<arm>.decidable` (`pass + fail`; `undecidable` and `missing` are printed beside it and
never enter the denominator). To cover every grid at once use `--all --report` (§3).

### tvs figure — tokens to verified success, 23 declared run/arm pairs

tvs is defined by `docs/TVS.md`: the first `grade_v5` `pass`, summed over distinct requests
through that turn. Re-derive the instrument output first, then hand it to the metric's tool:

```bash
python3 experiments/ptr-engine/tools/regrade.py \
  --rows experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.jsonl \
  --as-of 2026-10-26T16:00:00+00:00
python3 experiments/ptr-engine/tools/tokens_to_verified.py \
  --rows experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.jsonl \
  --grade experiments/ptr-engine/measure/regrade/rows-longrun-v4-tools-2026-10-26.grade-v5.json \
  --arm pointer-stable
```

`null` is a real result: the command prints `reason: "no_verified_success"` and never `0`.

### Per-cell checkpoint list — every checkpoint, its verdict and its derivation

```bash
python3 experiments/ptr-engine/tools/regrade.py \
  --rows experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl \
  --as-of 2026-10-26T16:00:00+00:00
python3 - <<'EOF'
import json
d = json.load(open("experiments/ptr-engine/measure/regrade/"
                   "rows-longrun-v6-tools.grade-v5.json"))
for c in d["cells"]:
    print(c["arm"], c["id"], c["turn"], c["verdict"], c["reason"],
          c["asserted"], c["expected"], c["derivation"].get("text"))
EOF
```

Each cell carries `verdict`, `reason`, `asserted`, `expected`, the raw contract line and the
AST `derivation` (`file:line`, node kind, symbol), which is what a paper figure cites.

---

## 2. Auditing a published number — the `--check` idiom

```bash
# one rows/grade pair
python3 experiments/ptr-engine/tools/regrade.py \
  --rows experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.jsonl --check

# every rows file under measure/, against the grade file already on disk
python3 experiments/ptr-engine/tools/regrade.py --all --report
```

`--check` regrades **in memory** (nothing is written) and compares against the existing grade
dict-wise, ignoring only `generated_at`. It prints:

- `IDENTICAL <rows file> (grader_sha256=…)` and exits **0**; or
- `DIFFERS …` with one `DIFF <path>: grade=<old> regrade=<new>` line per differing path, exit **1**.

Two provenance subtleties, both stated rather than hidden:

1. Legacy v5 grade files predate `grader_sha256`/`grader_path`. When the old document does not
   carry those keys they are printed as `provenance-only` and not counted as differences. When
   the old document **does** carry a recorded sha, it is compared — a wrong recorded sha is a
   difference (this is the red→green test).
2. The old document's `rows_file`/`fixture_file` label is adopted for the comparison when it
   names the same file (labels are written relative in some grades and absolute in others).

This is precisely the mode `V6-COMPLETE` performed by hand, and the reason a published number
can now be audited without trusting the grade file that sits beside its rows file.

---

## 3. The report table

`--report` prints one line per `rows*.jsonl` under `--measure` and writes
`experiments/ptr-engine/measure/REGRADE.json`:

| column | meaning |
|---|---|
| `rows_file` | the rows file |
| `pairs` | distinct arms in that file = declared (rows file, arm) pairs |
| `graded` | cells with a decidable verdict (`pass` or `fail`) |
| `ungraded` | cells `undecidable` or `turn_missing` |
| `grader_sha256` | first 16 hex of the grader that regraded it (full value in the JSON) |
| `grade_file` | the existing grade found for this rows file, or `-` |
| `check` | `identical` \| `differs` \| `absent` (+ the first differing path) |

A grade is matched to a rows file by **file identity**, not by basename: `.cell-demo/rows.jsonl`
and `measure/rows.jsonl` share a basename, and matching them would audit the wrong document.

Exit codes: **0** ok · **1** a `--check` mismatch · **2** unreadable input / no existing grade ·
**3** grader import or sha failure · **4** refused overwrite.

---

## 4. Determinism — the deliverable

Two runs of the same inputs with `--as-of` pinned are **byte-identical**; without `--as-of` they
differ only in `generated_at`. Measured on all 9 declared long-run grids (`rows-longrun-*.jsonl`),
run into three independent directories:

| rows stem | sha256 of output (first 16) |
|---|---|
| `rows-longrun-2026-10-26-fix` | `923008f50c310390` |
| `rows-longrun-2026-10-26` | `8095afb7d387b4bf` |
| `rows-longrun-2026-10-26-policy` | `10361ae8d9f4f934` |
| `rows-longrun-c-2026-10-26` | `9187b46fb8e85289` |
| `rows-longrun-v3-2026-10-26` | `07d702f247ab4ebb` |
| `rows-longrun-v4-2026-10-26` | `566fb1c2a4d760f2` |
| `rows-longrun-v4-tools-2026-10-26` | `50f22d4a6c19bcb1` |
| `rows-longrun-v5-tools` | `f3e0786091a7ef28` |
| `rows-longrun-v6-tools` | `74af4aff6e188e77` |

All three copies of all nine files compare equal byte-for-byte (`cmp`), with
`--as-of 2026-10-26T16:00:00+00:00`.

**The two published grids, re-derived:**

- **Quality grid (grade_v5 checkpoint cells over the 23 declared run/arm pairs):** regraded to
  **3 pass / 25 decidable** (12.0 %), `checkpoint_accuracy` per arm as in
  `measure/regrade/*.grade-v5.json`. *The published 5/43 = 11.6 % is not this grid* — see §5.
- **TVS grid (23 declared run/arm pairs, `docs/TVS.md`):** 3 produced, 20 `null /
  no_verified_success`, 0 `not_produced`. The three values regenerate **exactly** from the
  regraded grade files: **48 347** (`rows-longrun-v4-2026-10-26` / pointer-stable, turn 12),
  **50 847** (`rows-longrun-v4-tools-2026-10-26`), **111 994** (`rows-longrun-v6-tools`).

Eight of the nine existing grade-v5 files regrade **`identical`**. The ninth,
`measure/cell-pointer-stable-20261026T145722Z.grade-v5.json` (the `rows-longrun-v6-tools` grid),
**`differs`** in 22 paths — see §5.

---

## 5. Archaeology — what cannot be re-derived without re-grading

Scope: `experiments/ptr-engine/measure/` (15 `rows*.jsonl`, 29 grade files).

| question | answer |
|---|---|
| rows files with **no grade file at all** | **6**: `rows-baseline-2026-10-26`, `rows-cell-pointer-stable-20261026T145758Z`, `rows-equalinfo-2026-10-26`, `rows-live-2026-10-26`, `rows-pilot-thinking-2026-10-26`, `rows.jsonl`. None is a declared long-run grid; `regrade.py` produces a grade for each on demand, but none existed to check against. |
| grade files produced by a grader **other than** `6893d559…` | **19** are certainly not that sha: all 18 `grade-v2`/`grade-v3`/`grade-v4` files (2 + 7 + 9), plus `cell-pointer-stable-20261026T145722Z.grade-v5.json`, whose output is **not reproducible by the current grader** (below). 2 more (`cell-transcript-grow-*`, rows in `/tmp` and `.cell-demo`, now absent) cannot be verified at all. |
| grade-v5 files that **do** reproduce under `6893d559…` | **8** — the eight `cell-longrun-*` files from `TVS-REGRADE`, all `IDENTICAL`. They did not *record* a sha, so identity with the current grader is established by output, not provenance. |

**The one `differs` grade-v5 file is a real grader change, not a path/label artefact.**
`measure/cell-pointer-stable-20261026T145722Z.grade-v5.json` was produced before the
`GRADE-V5-REPAIR` `T3` change (an absent answer becoming `undecidable`, not `fail`). Regrading
`rows-longrun-v6-tools.jsonl` under `6893d559…` gives `1/1` where the file says `1/3`; 22 paths
differ, including:

```
DIFF arms.pointer-stable.checkpoint_accuracy: grade='1/3' regrade='1/1'
DIFF arms.pointer-stable.cells: grade='missing-in-grade' regrade=3
DIFF cells[1].verdict: grade='fail' regrade='undecidable'
```

`cp.0.t12` still passes, so the **tvs value 111 994 is unaffected** — but the v6 accuracy
`1/3` published in `measure/V6-RESULT.md` is *not* the current grader's output. It can only be
re-derived by pinning that earlier grader (whose sha was never recorded), not by this command.

**Published numbers that this command cannot re-derive, and why:**

1. **Quality `5/43 = 11.6 %`** (`docs/OPERATOR-BRIEF.md`, `measure/MATRIX-HONESTY.json`) — its
   instrument is `tools/det_verify.py` (sha `12ccc74e…`), not `grade_v5`; it grades 92 declared
   cells (3 fixture checkpoints **plus `repair.t30`**) with a different decidability rule. A
   single-grader reproducer cannot reproduce a second instrument's grid. Re-running the det
   instrument is a different command (`matrix_audit.py`).
2. **V6 accuracy `1/3`** — produced by an earlier, unrecorded `grade_v5` sha (§above). The tvs
   value beside it does regenerate.
3. **Every figure sourced from `grade-v2/v3/v4`** — those graders are not the instrument of
   record; `regrade.py` reproduces `grade_v5` only (secondary-instrument passes are labelled
   `certified: false` in `TVS.json`).

---

## 6. Named limitation

**Regrade reproduces the grader's output; it does not validate it.** If the grader has a
defect — a weak matching rule, an over-broad citation rule, a checkpoint the AST cannot
decide — `regrade.py` reproduces that defect faithfully and prints `IDENTICAL`. Identity is
evidence about *reproducibility*, never about *correctness*. Attacking the grader (showing that
a wrong answer passes or a right one fails) is a different card's job, with a different
instrument; nothing in this tool substitutes for it.

---

## 7. Tests

`experiments/ptr-engine/longrun/tests/test_regrade.py` — **8 passed**. Covers the contracted
cases: (a) a grader sha is recorded in the output; (b) an in-sync pair prints `IDENTICAL` and
exits 0; (c) one mutated field exits 1 and names the path; (d) `--as-of` makes two runs
byte-identical (and without it they differ only in `generated_at`); (e) a refused overwrite
exits 4; (f) red→green on the recorded `grader_sha256` (mutate → exit 1 naming the key,
restore → exit 0); plus a wrong `--sha256` exit 3 and an unreadable rows file exit 2.
