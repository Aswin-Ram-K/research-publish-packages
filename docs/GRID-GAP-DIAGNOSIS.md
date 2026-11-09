# GRID-GAP-DIAGNOSIS — the three gaps GRID-RUN-2 reported, classified by layer

**Unit:** `GRID-GAP-DIAG` · **Card:** `ee6448b3` · **Execution:** 4b67552c · **Written:** 2026-10-28
**Requests sent:** **0** · **Cells run:** **0** · **Network calls:** 0 · **Ledger touched:** no
**Grid state at diagnosis:** 2,591 spent / 1,729 remaining (cap 4,320)

> **Verdict in one line, first as the card demands: we are in the (B) world.**
> The transcript treatments never fired because the **fixture's wall was priced from its own
> declared answer padding**, not from the measured growth of real completions. Fixing that is a
> **fixture generation change (`v9`, generation 7)**, and era-B gen-6 cells cannot be pooled with
> gen-7 cells. Re-running all 16 cells at the measured ~162 requests/cell costs ≈ **2,592**, against
> **1,729** remaining → **the grid is unaffordable**, and the honest result is
> *budget-bound: H1 not adjudicable this cycle*.
> The `exit 4` cap gate is a second (B) defect (the runner's projection under-counts billed
> `turn-initial` requests). Only the `rows_path` join is (A), and it is repaired here.

---

## 1. Classification table

| # | GRID-RUN-2 finding | Layer | Code path that owns it | Fix touches | Gen bump |
|---|---|---|---|---|---|
| 1 | **8 transcript cells unusable**: `evicted_turns = 0`, `digest_rows = 0` across 48 turns although the fixture preflight predicts first grow/wall event at T21 | **(B) fixture** `longrun/tasks-v6/LR-01.v8.json` (`wall_tokens_by_arm`) | fixture text; runner correctly prices the wall it is given (`run_longrun.py:1153`, `:1224`, `:1241`) | new fixture generation `v9` | **YES → gen 7** |
| 2 | **2 cells refused `exit 4`** at T47/T48 (94 rows) | **(B) pinned runner** `longrun/run_longrun.py` | `projected_requests` `run_longrun.py:482-485`; `RequestCapGate.acquire` `:398-427`; one-row-per-send `:2716-2730` | `run_longrun.py` projection | **YES → gen 7** |
| 3 | **`rows_path` nested under `run`** so `analyze_stats.load_cell_manifests` cannot link rows to stamps | **(C) record layer, write side in (A)** `longrun/cell.py` | writer `cell.py:2277-2287` vs pinned reader `analyze_stats.py:655-687` (`man.get("rows_path")`) | `cell.py` only | **NO — none** |

`cell.py` is **not** in its own harness list (`cell.py:129-135`, `HARNESS_FILES`) and the pin's
`digest_recipe` says so verbatim: *"cell.py is NOT in its own list"*
(`measure/HARNESS-PIN.json`, gen 6, digest `efefd885…`). A `cell.py` edit therefore mints no
generation; a fixture or `run_longrun.py` edit does.

---

## 2. Why the treatments never fired — the wall is unreachable at 48 turns

### 2.1 What the fixture declares

`LR-01.v8.json`:

```json
"wall_tokens_by_arm": {"lease-reopen": 10616, "pointer-stable": 10616,
                       "transcript-compact": 10616, "transcript-grow": 10616},
"wall_tokens_basis": {"arithmetic": "wall_for_T = prompt_T1 + slope x (T - 1)",
  "per_arm_rule": "wall_tokens_by_arm[arm] = prompt_T1(this fixture) + ceil(mean declared
                   answer padding x 23). This fixture: prompt_T1 = 3848 tokens ...
                   mean padding = 14125/48 = 294.27 tok/turn, so 3848 + ceil(294.27 x 23)
                   = 3848 + 6769 = 10616. Both growth arms then fire at T21 ..."}
```

Two independent errors in that arithmetic:

1. **The base is understated.** The fixture's own prompt model says T1 = 3,848 tokens. The live
   cells measured **5,628–6,139** prompt tokens at T1 (tool channel on: the INDEX/`read_file`
   preamble is not in `working_set_block`). So the true gap to the wall is ~4,500–5,000 tokens,
   not 6,769.
2. **The slope is overstated by ~4–7×.** The wall was set from the **declared** answer padding
   (294 tok/turn average, 540 tok/turn at `answer_padding_tokens`), but real completions in these
   cells run 29–390 tokens. Measured live growth, robust `(T48 − T1)/47` over the 8 transcript
   rows files:

| cell (rows file) | T1 pt | T48 pt | growth tok/turn | turns to wall 10,616 |
|---|---|---|---|---|
| `rows-cell-transcript-compact-20261028T032235Z.jsonl` | 5,630 | 7,929 | 48.9 | **102** |
| `rows-cell-transcript-compact-20261028T032430Z.jsonl` | 5,901 | 10,489 | 97.6 | **48** |
| `rows-cell-transcript-grow-20261028T030925Z.jsonl` | 5,628 | 8,827 | 68.1 | **73** |
| `rows-cell-transcript-grow-20261028T031218Z.jsonl` | 5,628 | 7,819 | 46.6 | **107** |
| `rows-cell-transcript-grow-20261028T031401Z.jsonl` | 5,630 | 8,620 | 63.6 | **78** |
| `rows-cell-transcript-grow-20261028T031606Z.jsonl` | 5,630 | 8,067 | 51.9 | **96** |
| `rows-cell-transcript-grow-20261028T031753Z.jsonl` | 6,139 | 8,087 | 41.4 | **108** |
| `rows-cell-transcript-grow-20261028T032058Z.jsonl` | 5,630 | 7,708 | 44.2 | **113** |

Not one cell gets to the wall inside 48 turns; the fastest would need T48–T113. `evicted`/`digest`
never appearing is therefore **the correct behaviour of the runner given an unreachable wall**, not
a bug in the FIFO or compaction branch. This is the **fixture-design defect** the card anticipated:
the wall is unreachable *by construction* because it was derived from a padding model the model
does not honour.

### 2.2 The preflight is circular, which is why the cell was admitted

`run_longrun.py --dry-run` on the same fixture, same horizon, prints:

```
[transcript-grow]    first FIFO truncation at turn T21
[transcript-grow]    first wall at turn > 48 (NEVER inside the horizon)
[transcript-compact] first wall at turn T21
would_send_total=96
```

The "T21" is computed by simulating **declared** padding answers (`answer_padding=540 tok/turn`);
the same declared padding is what priced the wall. So the reachability guard validates the fixture
*against itself*: both the prediction and the limit move together, and a padding model the real
model ignores makes the guard agree with a wall no real cell can reach. The guard
(`EXIT_TREATMENTS_UNREACHABLE`, `run_longrun.py:328`) cannot catch this class of defect unless its
slope comes from measured rows rather than the fixture's declared padding.

### 2.3 What the fix is (and what it is not)

* **Is**: a new fixture generation with `wall_tokens_by_arm` priced from **measured** growth at the
  live base — e.g. `wall ≈ 5,630 + 75 × 20 ≈ 7,130` for a T21 fire — i.e. `v9`. That is a (B)
  change: new generation, new pin, provenance break.
* **Is not**: lowering the wall until something fires in the gen-6 fixture. Lowering the number
  silently changes the treatment (eviction/compaction intensity), and the card forbids it.

---

## 3. Why two cells were refused `exit 4` — the projection model under-counts

Reconstructed offline from the runner's own code and the recorded rows (no request sent):

* **Allocation** = `projected_requests(cfg, fixture, arm)`
  (`run_longrun.py:482-485`): `n_turns + expected_digests + fetch_rounds_per_arm`
  = **48 + 0 + 48 = 96** for `pointer-stable`. `TOOL_FETCH_ROUNDS_PER_ARM` is **48**
  (`run_longrun.py:282-296`), not the 24 named in `docs/FETCH-BUDGET-48.md` §1.
* **What the gate compares**: `RequestCapGate.acquire` (`run_longrun.py:398-427`) refuses when
  `would = used_in_run + 1 > allocation`, reserving the slot **before** the send; and separately
  against the global ledger (`spent + 1 > cap − reserve`). Here `cap = 4320`, `reserve = 0`,
  `spent_at_start = 2591` → the global cap never binds. The refusal was `run allocation`.
* **What a turn actually costs**: one row per send (`run_longrun.py:2716-2730`): a tools-on turn is
  `turn-initial` (the model's tool-call request — **billed**) + *k* `tool-followup` rows + the
  `turn` row. So **k+1 requests**, not 1.
* **The refused rows**: `rows-cell-pointer-stable-20261028T025312Z.jsonl` = 94 rows
  `{turn: 47, turn-initial: 24, tool-followup: 23}`; the second refused cell
  `…T025853Z` = 93 rows `{turn: 46, turn-initial: 22, tool-followup: 25}`. That is **2.0 requests
  per completed turn**, so a 48-turn cell needs ≈96 requests *before* its final turn's answer —
  the 97th trips `would > 96`.

**Verdict on the gate: the refusal is CORRECT enforcement of a defective projection.** The cell
genuinely needed more than 96; the gate did not overspend. The defect is that
`projected_requests` prices **one request per turn** and then adds a **fetch-round** pool, while
reality is *one request per turn **plus** one billed `turn-initial` request on every turn where the
model calls a tool, plus follow-ups*. The pool is nominally large enough to absorb them by
coincidence (48 rounds ≈ 48 invitations), which is why 14 of 16 cells completed at exactly
2.0 requests/turn and 2 did not. The finding is a **design finding about the allocation model**,
not a runner bug, and its fix is in a pinned file → **gen 7**.

---

## 4. `rows_path` nesting — the (A) repair, done

**Defect.** `stage_run` returns `rows_path` inside its detail (`cell.py:2145-2146`), the cell record
carries it as `"run": run` (`cell.py:2277-2287`), and the pinned reader
`analyze_stats.load_cell_manifests` accepts only a **top-level** `rows_path`
(`analyze_stats.py:664`, `:682`). Every cell.py record was silently dropped; GRID-RUN-2 rebuilt a
census by hand.

**Repair (layer A, no generation).**
`experiments/ptr-engine/longrun/cell.py`:

* `cell_rows_path(record)` — one accessor that reads **either** shape
  (`record["rows_path"]` first, then `record["run"]["rows_path"]`);
* `with_rows_path(record, rows_path=None)` — adds the flat join key in place, **keeps** the nested
  key (existing consumers), and adds nothing when the record describes no rows file;
* the record is passed through `with_rows_path()` once, immediately before `stage_record`
  (`cell.py:2341`).

The reader is **not** edited: it is pinned. Writing the flat key makes the pinned reader work
unchanged.

| | sha256 |
|---|---|
| `cell.py` **before** | `c494e212679f8e73c84226cf486566d0716559c0f2cd677f20845b24057baf86` |
| `cell.py` **after** | `c15f086c457d2dc465683d447fecb17ff5e6961b03ee163486d49d78e184687e` |

**Red→green harness**: `experiments/ptr-engine/tests/test_grid_gap_fix.py` — 4 tests.
Red (before the fix): `AttributeError: module 'cell' has no attribute 'with_rows_path'` (3 failed,
1 passed — the passing one is the defect pin below). Green (after): **4 passed**. The suite pins
the defect as well: a nested-only record is still dropped by the pinned reader, so the test fails
if someone "fixes" it by editing the reader instead of the writer.

**Known gap, stated not hidden.** The 16 records already written by GRID-RUN-2 remain nested-only;
they are measurement records and are not rewritten here. Linking *them* needs either the pinned
reader changed (forbidden) or a one-off census tool — owner: the report layer (C).

---

## 5. Repair list, with owners

| repair | file | owner | allowed here? |
|---|---|---|---|
| wall priced from measured growth; `prompt_T1` corrected to the live tool-on base; reachability priced from measured slope | new fixture generation `v9` | fixture-generation unit, **after a pin decision** | **NO** — (B), would mint gen 7 |
| `projected_requests` must count the billed `turn-initial` per inviting turn (or price invitations from the recorded invitation rate) | `longrun/run_longrun.py:482-485` | harness generation-7 unit | **NO** — pinned |
| reader accepts nested shape (not needed if writer emits flat) | `longrun/analyze_stats.py:655-687` | harness / analysis owner | **NO** — pinned |
| writer emits flat `rows_path`; accessor reads both | `longrun/cell.py` | this unit | **YES — done** |
| census over the 16 existing nested records | report layer (C) | report owner | reported only |

## 6. The arithmetic the card asked to be stated, not left implicit

* Measured cost per cell in GRID-RUN-2: **2,591 / 16 = 161.9 ≈ 162 requests/cell**.
* A gen-7 fixture fix makes every era-B gen-6 cell non-poolable (provenance refuses, correctly),
  so the grid must re-run **all 16**: `16 × 162 = 2,592` requests.
* Ledger: **2,591 spent / 1,729 remaining**.
* `2,592 > 1,729` ⇒ **unaffordable**.
* Even the cheaper-looking 8-cell repair (`8 × 162 = 1,296 ≤ 1,729`) is unavailable: it would
  leave 8 gen-6 cells and 8 gen-7 cells, and era-B cannot be mixed across generations.
* Therefore: **budget-bound — H1 not adjudicable this cycle.** The correct next spend is a
  pin/generation decision plus a ledger re-baseline, not another cell launch.

**Cost of this unit:** 0 inference requests, 0 network events, 0 cells run, 0 ledger writes.
Only `cell.py`, the new test file, this page, the unit card, the handoff and the journal were
written.
