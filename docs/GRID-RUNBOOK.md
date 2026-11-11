# GRID-RUNBOOK — read this before touching a running or interrupted grid

**Unit:** `GRID-RUNBOOK` · **Scope:** `RUN-A-STAR-2` (era B, tools-on, 10 cells, 1,056 requests)
**Written:** 2026-10-26 · **Offline:** 0 requests, 0 network events, 0 live cells.
**Status:** documentation only. No harness file, fixture, rows file, grade, threshold or published
page was edited by this unit.

This page exists because the grid's discipline lived **only inside the card's prompt**. The grid
session sees that prompt; the session that inherits the mess does not. Everything below is either
a command verified in this tree on 2026-10-26 or a stated fact with its `file:line`.

> **Rule of this page:** every command was run or its flag was read out of the source before it was
> written here. Nothing in this page is a remembered flag. Where a figure is *derived* rather than
> quoted, the derivation is shown.

---

## 0. The one-line status, and how to get it fresh

```bash
python3 experiments/ptr-engine/tools/grid_resume.py
```

Read-only, offline, 0 requests. It prints the whole grid state and the ledger delta. **This is the
first command of every session** — including this one. Do not start from a handoff's claim about the
grid; start from this output.

Measured 2026-10-26 (verbatim shape of the render):

```
GRID RESUME — RUN-A-STAR-2  (read-only, offline: 0 requests)
measure_dir              .../experiments/ptr-engine/measure
fixture LR-01.v8 sha256  0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641
era note                 era A and era B share this fixture sha; era is
                         decided by the rows' own tools_mode/stamps, not names

CELLS (declared order, 10):
  1 pointer-stable r1    state=partial        files=2
      rows-cell-pointer-stable-20261026T145758Z.jsonl      file_state=partial        turns=6/48 ...
      rows-cell-pointer-stable-20261026T182535Z.jsonl      file_state=era_a_excluded turns=27/48 ...
  2 pointer-stable r2    state=absent         files=0
  ...
next_cell   pointer-stable r1
CANARY ARMS (N=12, 4):
  pointer-stable       state=absent files=0
  ...
LEDGER (delta vs measure/LEDGER-GRID-BASELINE-2.json):
  spent_now      1128
  remaining_now  3192
  delta          0
  verdict        OK (arithmetic closes: delta is a real measurement, not a re-read)
  next cell price 108 requests; fits=True (remaining_now >= price)
```

**State as of this page (measured, not inherited):** **0 of 10 cells complete.** `pointer-stable r1`
carries two partial rows files — 6 turns (an earlier fixture sha `967cef03…`) and 27 turns
(`tools_mode=off` in 27/27 rows, `stop_reason=runaway_turn` at turn 27, `era_a_excluded`). Both are
`usable_for=[]`. Cells 2–10 and all four canary arms are `absent`.

---

## 1. Pre-flight checklist (run in this order; stop at the first failure)

Every line is a command, its expected output, and **the file that is wrong if it fails**.

| # | Check | Command | Expected | File that is wrong if it fails |
|---|---|---|---|---|
| 1 | **Pin — recompute** | see block below | `a668491a55a4e2714b6e58dc8168919ee163bd2b5e3bb733b54fd9e38263bf73` | the harness file that moved (pin names all seven); then `measure/HARNESS-PIN.json` is stale and must be **regenerated, never hand-edited** |
| 2 | **Pin — generation** | `python3 -c "import json;d=json.load(open('experiments/ptr-engine/measure/HARNESS-PIN.json'));print(d['generation'],d['harness_sha256'])"` | `11 a668491a…` | `measure/HARNESS-PIN.json` |
| 3 | **Pin — the flag you will pass** | `grep -n 'launch_must_pass' experiments/ptr-engine/measure/GRID-PARAMS.json` | `--expect-harness a668491a…` (⚠️ 1a: the copy is not the authority) | `measure/GRID-PARAMS.json` (`harness_pin.launch_must_pass`) |
| 4 | **Price** | `python3 -c "import json;p=json.load(open('experiments/ptr-engine/measure/GRID-PARAMS.json'))['price'];print(p['total'],p['components'],p['remaining_after'])"` | `1056 {'tranche': 964, 'canary': 48, 'warm_ups': 4} 8447` | `measure/GRID-PARAMS.json` (`price.*`) |
| 5 | **Price arithmetic** | same file, `price.arithmetic` | `964 tranche + 48 canary + 4 warm-ups = 1,016` | `measure/GRID-PARAMS.json` |
| 6 | **Ledger** | `python3 experiments/ptr-engine/tools/ledger_delta.py` | `spent_before 1128` / `spent_now 1128` / `delta 0` / `remaining_now 3192` / `verdict OK (arithmetic closes…)` | `measure/LEDGER-GRID-BASELINE-2.json` if the baseline sha moved; `measure/REQUEST-LEDGER.json` if the counter cannot read its row files |
| 7 | **Ledger baseline identity** | `sha256sum experiments/ptr-engine/measure/LEDGER-GRID-BASELINE-2.json` | `3b79f4766abc8479a7a963f9e04063837928d09d48d2435e91f488b3c6d3ae0d` | `measure/LEDGER-GRID-BASELINE-2.json` — **if this sha changes, every delta measured against it is void** |
| 8 | **Fixture** | `sha256sum experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` | `0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641` (57,242 bytes) | `longrun/tasks-v6/LR-01.v8.json` — and the pin's `fixture` entry with it |
| 9 | **Canary wall (G2)** | see ⚠️ below | projection must leave **≥720 s** inside `--max-wall` | `measure/PROJECTION.json` / the `--max-wall` you passed |
| 10 | **Canary claim** | after the canary cell, `python3 -c "import json,glob;f=sorted(glob.glob('.../rows-cell-*.jsonl.claim.json'))[-1];print(json.load(open(f))['claim'],json.load(open(f))['comparison_eligible'])"` | `none` / `False` — a `smoke` canary is **never pooled** | the claim sidecar written by `cell.py` `stage_run`; a claim other than `none` on a canary cell |
| 11 | **Per-cell stamp** | the cell invocation writes `--out-dir/cell-<arm>-<stamp>.json`, `.md`, `.gates.json` | all three exist, `.gates.json` names the gate record it ran under | `cell.py` `stage_record`; a missing `.json` is exit **7**, not exit 0 |

### ⚠️ 1a. The pin flag: read `HARNESS-PIN.json`, never this page's copy.

`GRID-PARAMS.json` carries a **cached copy** of the pin at `harness_pin.launch_must_pass`, and it has
been wrong before: **generation 3 quoted the old digest** there while the tree had moved on — the trap.

**The cached copy now quotes the pin's current generation** (generation 6) — pin and copy move in the
same pass — and the file says so itself at `harness_pin.read_the_pin_at`: "this block is a CACHED
COPY, not the authority". Passing a digest the tree no longer has still raises:

```
Abort(2, "2/7 harness", "harness changed mid-cell: --expect-harness ...")
```

**The authority is always `HARNESS-PIN.json`: read `harness_sha256` (with `generation`) at launch time
and pass that value — never this page's copy, never a value quoted in prose.** Measured for the
generation 4 → 5 move: `--expect-harness <generation 4's digest>` exits **2** at stage 2/7;
`--expect-harness <generation 5's digest>` exits **0** with `G1 allow`, `G2 allow`, `G3 allow` (both
quoted in `orchestration/handoffs/HARNESS-PIN-GEN5.json`).

```bash
# Pin recompute — the exact recipe cell.py:381-402 uses (HARNESS_FILES at cell.py:130-138
# + 'fixture'; cell.py is NOT in its own list). Run from the longrun dir.
cd experiments/ptr-engine/longrun && python3 - <<'PY'
import hashlib, os, json
HERE, ENGINE = os.getcwd(), os.path.dirname(os.getcwd())
F = [(os.path.join(HERE,'run_longrun.py'),'run_longrun.py'),
     (os.path.join(HERE,'client.py'),'client.py'),
     (os.path.join(HERE,'grade_v5.py'),'grade_v5.py'),
     (os.path.join(HERE,'analyze_stats.py'),'analyze_stats.py'),
     (os.path.join(ENGINE,'tools','det_verify.py'),'tools/det_verify.py'),
     (os.path.join(HERE,'arm_cd.py'),'arm_cd.py'),
     (os.path.join(ENGINE,'ptr_engine','layers.py'),'ptr_engine/layers.py'),
     (os.path.join(HERE,'tasks-v6','LR-01.v8.json'),'fixture')]
d = {n: hashlib.sha256(open(p,'rb').read()).hexdigest() for p, n in F}
c = hashlib.sha256()
for n in sorted(d): c.update(('%s:%s\n' % (n, d[n])).encode())
print(c.hexdigest())
PY
```

Measured 2026-11-11 (generation 10): prints
`a668491a55a4e2714b6e58dc8168919ee163bd2b5e3bb733b54fd9e38263bf73` — **the pin holds**.
Generation 9 printed `32463261…`, generation 6 `efefd885…`, generation 8 `64e69e49…`; all
three stay on the record under their own generation label and none launches any more.

### ⚠️ 1b. The canary wall: 12 × 60 = 720 s versus the 600 s G2 headroom

The canary is `N=12` turns per arm, 4 arms (`GRID-PARAMS.json` `canary.N`). G2
(`cell.py` `eval_gate_projection`, exit **8**) compares **projected requests × projected turn wall**
against `--max-wall`. The G2 finding is the arithmetic:

```
12 turns × 60 s = 720 s  >  600 s
```

so a canary launched under a 600 s wall is **refused at G2 before it sends anything** — the ratio is
the point, not the two constants. Pass an explicit `--max-wall` with ≥720 s of room, and never shrink
the projection to fit the wall (`cell.py` exit-8 action says exactly this).

*Note, to keep two different 720s apart:* `docs/TRANCHE-CANARY.md:181` also quotes **≈720**, but that
is the **tranche's request count**, not seconds. Do not cite it as the wall finding.

---

## 2. Resume procedure

### 2.1 The tool

```bash
python3 experiments/ptr-engine/tools/grid_resume.py [--json] [--no-ledger] \
        [--done-turns 48] [--canary-turns 12]
```

Verified `--help` text: *"read-only RUN-A-STAR-2 resumption report"*, options `--measure-dir`,
`--root`, `--json`, `--no-ledger`, `--done-turns`, `--canary-turns`. Verified output shape
(default render) is quoted in §0: a `CELLS (declared order, 10)` block where each cell shows
`state=`, `files=`, and per-file `file_state=`, `turns=n/48`, `usable_for=[...]`, plus
`next_cell`, a `CANARY ARMS (N=12, 4)` block with `canary_next`, and a `LEDGER` block reporting
`spent_now`, `remaining_now`, `delta`, `baseline_sha`, `verdict`, `next cell price … fits=`.
`--json` emits the same report as JSON (`cell.py`-style `sort_keys`).

### 2.2 Count the rows yourself — never trust a filename

`turns=n/48` in `grid_resume` comes from a line count. The cheap independent check is:

```bash
for f in experiments/ptr-engine/measure/rows-cell-*.jsonl; do
  printf '%s\t%s\n' "$(wc -l < "$f")" "$(basename "$f")"; done
```

Measured 2026-10-26:

```
6	rows-cell-pointer-stable-20261026T145758Z.jsonl
27	rows-cell-pointer-stable-20261026T182535Z.jsonl
```

* **complete** ⇒ exactly **48** lines for that arm/rep, and `grid_resume` says `file_state=`
  complete/usable. A file with 48 lines that the tool does **not** call usable is **not** done —
  the stamp/era evidence outranks the count.
* **partial** ⇒ any count **1–47**. It is a partial however promising it looks.

### 2.3 The per-cell decision table

| What is on disk | Decision | Why |
|---|---|---|
| **48 turns** on disk for that arm/rep | **done — never re-run** | re-running spends ~48–108 requests to overwrite a paid-for measurement |
| **partial** (1–47 turns) | **re-run as a fresh cell, never append** | the runner appends; a second invocation against the same rows path mixes two launches into one file with no boundary. Use a new `--out-dir`/stamp |
| **no file** (`state=absent`) | **next cell** | nothing was spent; just run it |
| **two rows files for one arm/rep** | **STOP and report** | a duplicate is how the ledger went stale by 27 |

**The duplicate case is live right now.** `pointer-stable r1` has two files. The stop rule says stop;
the *reason the rule can be satisfied without stopping* is that the files are **distinguishable by
evidence already on disk**, and `grid_resume` did it: the 27-turn file is `era_a_excluded`
(`tools_mode=off` in 27/27 turn rows, `stop_reason=runaway_turn` at turn 27), and the 6-turn file
carries a **different fixture sha** (`967cef03…`). Neither is `usable_for` anything.

* Two files ⇒ **STOP** unless a per-row field (`tools_mode`, fixture sha, stamp/era) **separates
  them**. If the only thing that separates them is the filename, stop.
* **Never resolve a duplicate by deleting a file.** The 27 era-A rows are the excluded evidence the
  ledger's 1,128 baseline is reconciled against — see §5.

### 2.4 The cell invocation

```bash
python3 experiments/ptr-engine/longrun/cell.py \
  --arm <arm> --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json \
  --turns 48 --reps 1 --budget 220 \
  --expect-harness a668491a55a4e2714b6e58dc8168919ee163bd2b5e3bb733b54fd9e38263bf73 \
  --out-dir <out>
```

Flag names verified in `cell.py`: `--arm`, `--fixture`, `--turns`, `--reps`, `--budget`,
`--expect-harness` (`cell.py:1862`), `--out-dir`, `--max-wall`, `--projected-from`,
`--hypothesis`, `--allow-inconsistent`, plus `--endpoint` and `--offline <rows>`.
(`cell.py`'s docstring example still shows a **`tasks-v5/runtime-v5/LR-01.v5.json`** path — that
example is stale; the pinned fixture is `tasks-v6/LR-01.v8.json`.)

---

## 3. Exit codes for a grid session

The table has **one copy**: `experiments/ptr-engine/longrun/exit_codes.py`. `cell.py` holds none.
Print it, never retype it:

```bash
python3 experiments/ptr-engine/longrun/exit_codes.py
```

Everything below is rendered from that module on 2026-10-26.

| Code | Name | Meaning | Action |
|---|---|---|---|
| `0` | ok | cell completed; verdicts and record written | read the cell record in `--out-dir`; nothing to repair |
| `1` | internal-error | an unclassified exception escaped a stage; traceback printed | a **harness defect**, not a measurement. Do not re-run hoping for a different result; file the traceback against the stage named in the last stage line |
| `2` | preflight / **pin** | fixture, harness freeze, or unreadable gate artefact; **also argparse usage errors** | fix the artefact or flag; no request was sent, nothing to re-measure |
| `3` | budget | runner dry-run + 10 % headroom exceeds `--budget` | raise `--budget`, or lower `--turns/--reps/--arm`; **do not edit the runner** |
| `4` | ledger-cap | G1 cap gate refused the send (`spent + would_spend + reserve > cap`, cap 4,320) | repair/extend the ledger artefact. **A refusal here is the budget being honest, not a cell failure** |
| `5` | **runner-crash** | `run_longrun.py` exited outside its own guard refusals | read the runner's stderr in the record; rows written before the crash are kept |
| `6` | `RUNAWAY` | one or more runaway turns ended the cell (runner rc 6, or the live turn-wall cap) | inspect rows to the last turn; a runaway is a client/harness problem — fix it before spending one more request |
| `7` | unwritable | a required artefact could not be written (rows, or stage 7's cell JSON/markdown) | fix path/permissions/space. **The measurement may exist but its evidence is not on disk** — this project has already paid for that |
| `8` | projection | G2: projected wall exceeds `--max-wall` | raise `--max-wall` or recalibrate `--projected-from`/`PROJECTION.json`; **never shrink the projection to fit** |
| `9` | inconsistent | grader decidable > 0 ⇎ analyser `graded_n` > 0, and no `--allow-inconsistent` | find out why the two populations differ before believing either; the override records, it does not resolve |
| `10` | grade | `grade_v5.py` itself refused | re-run the **grading**, not the cell |
| `11` | analyse | `analyze_stats.py` itself refused | re-run the **analyser**; the grade document stands, no request needed |
| `12` | prereg / G3 | the cell's own `n` cannot support the hypothesis (or none declared) | name it with `--hypothesis` or raise `--turns/--reps`; **never lower the minimum to fit the cell** |
| `13` | tree-moved | the bytes an audit froze are no longer on disk — raised by **`tools/tree_freeze.py`**, not by `cell.py` | re-run against the settled tree. **Not a failure: it is unstamped, so it is never FAIL** |

### 3.1 The `5` / `6` asymmetry — believe the code, not the label

`RUNNER_CODES = {2, 3, 4, 5, 6, 7}` are propagated **unmodified** into the cell's exit. Everything
else collapses to `5` (`cell.py:1616`):

```python
code = rc if rc in _RUNNER_CODES else exit_codes.EXIT_RUNNER_CRASH
```

So:

* **`6` is a first-class refusal**, and it means **runaway**. It survives the runner boundary intact,
  which is deliberate: *"collapsing them into one number is how a runaway abort became
  indistinguishable from a crash"* (`cell.py:1613-1615`).
* **`5` is the HARD STOP** — a **catch-all**. A runner `rc=1` (bare `SystemExit(str)`, e.g. RESUME
  REFUSED, or a runner traceback) becomes `5`. A runner **`rc=9` — `EXIT_CAP_DIVERGENCE`, a real
  bug — also becomes `5`** (`exit_codes.RUNNER_MAPPED_TO_CRASH`). The cell cannot tell you which,
  because **`9` is the *cell's* grader/analyser-inconsistency code** and this is a declared numbering
  collision in `run_longrun.py`, reported and deliberately *not* renumbered. **Always read the
  runner's stderr in the cell record; the number alone is under-determined by design.**
* **Ambiguous by design:** `2` covers both a pin/fixture preflight failure and an argparse usage
  error (argparse's own convention). `9` can only be the *cell's* inconsistency — a runner cap
  divergence never reaches you as `9`.

> Note on this card's brief: it described `6` as *"abandon and continue (three abandons stop the
> grid)"*. The authoritative table says **6 = runaway**; no `Abort(6, …)` site in `cell.py` raises
> "abandon", and `grep -n abandon` over `cell.py` / `run_a_star.py` returns nothing. **Abandon is a
> session-level decision recorded in the journal, not an exit code.** Treat "three abandons" as
> operator discipline, not an enforced rule — nothing in this tree enforces or counts it.

---

## 4. Between-cell ritual — four lines, before the next cell starts

1. **Ledger delta.** `python3 experiments/ptr-engine/tools/ledger_delta.py` → expected
   `delta = spent_after − spent_before` (the tool prints `delta` = `spent_now − 1128`), plus
   `rows_guard … new since baseline: N` and `verdict OK (arithmetic closes…)`. The delta must equal
   the requests the cell actually priced; `rows_guard` naming a new rows file is the proof the spend
   is row-backed rather than a re-read.
2. **Three stamp checks.** (a) the cell exited **0**; (b) the intended key is **present** in the cell
   record / `.claim.json` (e.g. `claim`); (c) the value is the **intended** one (`none` for a smoke
   canary, `comparison_eligible=false`). A missing `.gates.json` or `.json` is exit **7**, not success.
3. **Journal line.** `python3 experiments/ptr-engine/tools/unit_journal.py log …` (subcommands
   verified: `init`, `log`, `status`, `resume`) — one line per cell, append-only.
4. **The one line that must be written before the next cell starts:**
   > `cell <n>/10 <arm> r<rep>: <48 turns | partial <k>/48 | absent> · rc=<code> · ledger delta=<N> · rows=<path> · <-next cell | STOP: reason>`

   Without that line, the next cell starts against an unrecorded baseline and a killed session
   cannot be reconstructed from disk.

---

## 5. Killed-session recovery

A successor's first five minutes are the risk. **Five things it must NOT do:**

1. **Re-run a 48-turn cell.** 48 turns on disk is a paid measurement. `wc -l` first (§2.2).
2. **Delete or rewrite the era-A 27 rows** (`rows-cell-pointer-stable-20261026T182535Z.jsonl`, 27
   turns, `tools_mode=off`). They are excluded from usable evidence — **not** from the ledger's
   accounting: the baseline's own note says *"the 27 are era-A abandoned-cell spend, pre-grid, not
   tranche spend"*. Deleting them makes the 1,128 unreconcilable.
3. **Pool eras.** Era A (tools-off) and era B (tools-on) **share the fixture sha** `0804b515…`; era is
   decided by the rows' own `tools_mode`/stamps, **not by filename**. Pooling them silently compares
   two different measurements.
4. **Edit a grade.** A grade document is evidence. `10`/`11` mean re-run the grader/analyser against
   the same rows — never hand-edit the output.
5. **Lower `min_n_for(0.95) = 60`.** Verified: `analyze_stats.TAIL_MIN = 3`, `MIN_N = 20`,
   `min_n_for(q) = max(MIN_N, ceil(TAIL_MIN/(1-q)))` → `ceil(3/0.05) = 60`. G3 (exit `12`) exists to
   refuse exactly the cell that would need this lowered. Raise `--turns/--reps` instead.

**Two commands that establish truth cheaply:**

```bash
for f in experiments/ptr-engine/measure/rows-cell-*.jsonl; do printf '%s\t%s\n' "$(wc -l < "$f")" "$(basename "$f")"; done
python3 experiments/ptr-engine/tools/grid_resume.py
```

Neither sends a request. Together they give row counts per file and the tool's era/usable
classification and the ledger delta.

---

## 6. Stop-report format

A stop is diagnosable without the session only if it carries five fields: **`gate`**, **`computed`**,
**`limit`**, **`rc`**, **rows path**. The eight stop classes this page defines, each mapped to a
verified code:

| # | Stop class | code | Quote |
|---|---|---|---|
| 1 | harness moved / pin mismatch | 2 | `gate=2/7 harness`, `computed=<current digest>`, `expected=<pin>`, `limit=HARNESS-PIN.json` gen N, `rc=2`, `rows=<none — nothing sent>` |
| 2 | fixture / gate artefact unreadable | 2 | `gate=preflight`, `computed=<which check failed>`, `limit=<fixture sha 0804b515…>`, `rc=2`, `rows=<none>` |
| 3 | budget | 3 | `gate=3/7 budget`, `computed=required_with_headroom`, `limit=--budget`, `rc=3`, `rows=<path>` |
| 4 | ledger cap | 4 | `gate=G1`, `computed=spent+would_spend+reserve`, `limit=cap 4320`, `rc=4`, `rows=<path>` |
| 5 | runner crash (incl. hidden rc 1/9) | 5 | `gate=4/7 run`, `computed=runner rc=<1 or 9>`, `limit=<none>`, `rc=5`, `rows=<path>`, **plus the runner stderr tail** |
| 6 | runaway | 6 | `gate=4/7 run`, `computed=runaway turns=<n>`, `limit=--runaway-turns`, `rc=6`, `rows=<path>` |
| 7 | projection | 8 | `gate=G2`, `computed=<projected requests × turn wall>`, `limit=--max-wall`, `rc=8`, `rows=<path>` |
| 8 | prereg / G3 | 12 | `gate=G3`, `computed=n=<turns×reps>`, `limit=min_n_for(0.95)=60`, `rc=12`, `rows=<path>` |

Also carry, when they fire: `7` unwritable (quote the **path** and the `OSError`), `9` inconsistent
(quote both populations: grader decidable vs analyser `graded_n`), `13` tree-moved (quote the
**moved file** and both shas; record it as **unstamped, never FAIL**).

A stop that omits `computed` is an assertion, not a diagnosis.

---

## 7. What this runbook cannot know

Named, so no successor mistakes silence for safety:

1. **Whether a cell's shape is degenerate.** That is the **canary's** job (`N=12`, 4 arms, verdict
   rule `answer_verified >= 1`, `stop_signal_source=finish_reason`). A green pre-flight says nothing
   about whether the cell measures anything.
2. **Whether quality is comparable across eras.** Era A vs era B is a real comparison question; the
   shared fixture sha does not make it one population. `docs/` owns it; this page only says do not pool.
3. **Who confirms a permission.** Not a runbook fact — a human act. This page cannot grant it.
4. **Whether the endpoint is up or what a turn will really cost.** Wall clock is an extrapolation
   from measured rows until the cells run.
5. **Whether the effective `--max-wall` default is 600 s.** The §1b arithmetic is the finding; the
   default itself must be re-read from `cell.py` (`grep -n 'max-wall' cell.py`) before quoting 600.
6. **Whether the ledger counts every rows file.** `ledger_delta` reports
   `rows_guard checked 15 rows file(s)`; a rows file outside that inventory is not priced.
7. **Whether 48 turns is the right shape for an arm.** The price (`964 = 480 + 480 + 4`) is pinned;
   the *appropriateness* of 48 is a prereg question, not a runbook one.
8. **Whether concurrent cards have moved the tree.** A pin freezes at a moment. `13` exists because
   the tree can move under an audit — re-verify the pin at launch, not once at planning.

---

*Verified in this tree on 2026-10-26. Commands printed here were run or their flags read from
source: `grid_resume.py --help` + default render, `ledger_delta.py --help` + run,
`exit_codes.py` run, `harness_baseline.py --help`, `unit_journal.py --help`, `cell.py`
(`:128-135`, `:334-346`, `:1613-1621`, `:1862`), `analyze_stats.min_n_for`, `GRID-PARAMS.json`,
`HARNESS-PIN.json`, `LEDGER-GRID-BASELINE-2.json`, `docs/TRANCHE-CANARY.md:181`. No file outside
this page's declared write paths was modified.*

**Dated 2026-10-26:** generation 5 was the canary's epoch: `35ff41b7…` covered its 36 rows, which stay labelled generation 5 and are **not comparable** to a generation-6 tools-on digest, because TOOL-CHANNEL-WIRE changed the request body and the tools-on `request_sha256` moved (measured 3c0ff847…); a tools-off `request_sha256` is unchanged at f0499dd1…. Generation 6 was `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3` (full value in `measure/HARNESS-PIN.json` generation 6 and in `measure/GRID-PARAMS.json` `harness_pin.supersedes_generation_6`) and on that date it was the only value `--expect-harness` could carry; generation 8 then printed `64e69e49…` and generation 9 `32463261…`. <!-- predecessor -->
