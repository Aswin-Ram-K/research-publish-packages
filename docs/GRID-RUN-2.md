# GRID-RUN-2 — the 16-cell era-B grid did not launch, and why

**Unit:** `GRID-RUN-2` · **Card:** `d2d00521` · **Written:** 2026-10-27T20:44Z
**Requests sent:** **0** · **Cells run:** **0 of 16** · **Spend delta:** **0** against `measure/LEDGER-GRID-BASELINE-3.json`
**Verdict:** **`not adjudicable`** — not because the grid ran and was inconclusive, but because no cell ran.

This page is the report the card asked for, in its own fixed terms. It records what was verified,
the one blocking measurement, and the single change that would unblock the same card.

---

## 1. The blocking finding (measured twice, from both sides)

`experiments/ptr-engine/tools/run_a_star.py` is the only thing that starts a grid cell. Its
`remaining_basis()` gate compares the live ledger to a frozen baseline **plus** the rows it can
attribute to files billed after the baseline's `as_of`. Both honest states of the ledger are refused:

| ledger state | RECONCILE line (launcher's own) | exit |
|---|---|---|
| the file as it stands (`REQUEST-LEDGER.json`, built 2026-10-26T22:33:00Z, 1,176 / 3,144) | `baseline=1176 attributed_delta=115 live=1176 explained=1291 gap=-115` | **1 — REFUSED** |
| the ledger's own recount (`tools/request_ledger.py`, 1,321 / 2,999) | `baseline=1176 attributed_delta=115 live=1321 explained=1291 gap=30` | **1 — REFUSED** |

Commands, verbatim:

```
python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --dry-run
RUN_A_STAR_LEDGER_LIVE=/tmp/ledger-fresh.json \
  python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --dry-run
```

The second run used the launcher's own documented read hook to point at a scratch rebuild
(`python3 experiments/ptr-engine/tools/request_ledger.py --write /tmp/ledger-fresh.json`); no
repository file was written, and the ledger's owner was not bypassed.

### The 30 rows, named

The gap is exactly the `kind="turn-initial"` row class, counted by the ledger's owner and silently
dropped by the launcher:

| rows file | `turn-initial` rows |
|---|---|
| `rows-cell-lease-reopen-20261027T004219Z.jsonl` | 2 |
| `rows-cell-lease-reopen-20261027T024223Z.jsonl` | 7 |
| `rows-cell-lease-reopen-20261027T084049Z.jsonl` | 13 |
| `rows-cell-pointer-stable-20261027T004027Z.jsonl` | 6 |
| `rows-cell-transcript-compact-20261027T004155Z.jsonl` | 1 |
| `rows-cell-transcript-grow-20261027T004129Z.jsonl` | 1 |
| **total** | **30** |

`run_a_star.py:_row_counts()` counts only `COUNTED_KINDS = ("turn", "tool-followup")` and returns
`False` for any other kind. `request_ledger.py`'s closed vocabulary counts an unrecognised kind
conservatively as `assumed_billed` and flags it. The launcher's own comment at
`run_a_star.py:221` claims it applies request_ledger's rule ("a row counts unless it declares it was
not billed"); it does not.

These are real wire requests, not mirrors. Example (`rows-cell-pointer-stable-20261027T004027Z.jsonl`,
turn 1): the `turn-initial` row carries `prompt_tokens 3987`, `completion_tokens 65`,
`ttft_ms 705.181`, `content_sha256 03388fbb…`; the paired `turn` row carries `prompt_tokens 4479`,
`completion_tokens 71`, `ttft_ms 190.913`, `content_sha256 2a029f29…`. Two distinct requests,
stamped with the same turn-end time.

### The tree's own suite says the same thing

`experiments/ptr-engine/tests/test_launcher_pin_and_cells.py` is **6 failed, 6 passed** on this tree.
Four of the failures are the launcher dry-run tests dying on the same
`REFUSED: 115 request(s) of ledger gap …` line; the other two are stale test expectations
(`3219`/`3192` where the record now says `3144`). The conductor is red for the same reason the grid
cannot start — this is not a condition this unit created.

**Verdict row (recorded before the handoff write):** `PASS f17663d1…`, execution
`c84f24cf-301d-43ce-b7a5-6fb95a76dd4e`. The frozen command re-runs both directions (stale ⇒ `gap=-115`,
rebuilt ⇒ `gap=30`, rebuild = `1321/2999`, `turn-initial` total = 30) and exits 0 only when all four
hold; it reproduces the block without sending a request.

### Why it is not repaired here

Closing the gap needs one of:

* a change to `run_a_star.py` — a **harness file**, forbidden to this card;
* a write to `REQUEST-LEDGER.json` or a baseline — both **forbidden**;
* a ledger figure that restates `baseline + 115` while contradicting the on-disk recount — that is
  the fabrication the whole ledger discipline exists to prevent.

The card's own rule governs: **a cell you cannot run is reported, never repaired.**

---

## 2. What was verified before the stop (quoted, not re-derived)

| # | precondition | result |
|---|---|---|
| 1 | pin = generation 6, `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3` (`measure/HARNESS-PIN.json`), expected by `run_a_star.py:72-73` | **HOLDS** |
| 1b | `cell.py` is not in the pin; standalone sha256 recorded `c494e212679f8e73c84226cf486566d0716559c0f2cd677f20845b24057baf86`, unchanged through the run | **HOLDS** (no later cell) |
| 2 | four arms cleared from rows: pointer-stable / transcript-grow / transcript-compact `shape_ok` in `measure/CANARY-ERA-B-4.json`; lease-reopen `lease_arm_usable_for_grid: true` in `measure/LEASE-REOPEN-23.json` (T23 `lease=2`, `prompt_sha256 14078d25…` vs `e76210e84393…` at T22, 3 verified answers, 0 cap-length) | **HOLDS** — no canary re-run |
| 3 | tool channel live: `TOOL-CHANNEL-WIRE` `dda84411` PASS; `V-TOOL-CHANNEL` verified `<tool_result … base="engine">` with real source lines, tools-off digest `f0499dd1…` unchanged, one billed round | **HOLDS** (verifier's own `overall` is `partial`, not `pass`) |
| 4 | ledger: file stale; delta-aware launcher check exists | **HOLDS AS DESCRIBED — and is the blocker (§1)** |
| 5 | `GRID-PARAMS.json` rev 3 says **16 cells, 6/6/2/2, price 1,056**, and the launcher enforces exactly that (`_grid_record`, `SHAPE_EXPECTATION`, `price_line`). The 10-cell / 1,016 figures survive only as preserved history under `price.supersedes` / `sixteen_cell_supersede` | **MATCHES THE CARD** — the `price-reconcile` tag's "still says 10 cells/1,016" is stale against rev 3 |
| 6 | stamping rule: `analyze_stats.py:749` `excluded = analyses is not None and len(analyses) == 0`, so an absent `usable_for` is **included** | **HOLDS** (unexercised — no rows written) |

`measure/GRID-SHAPE.json`'s `cells[0..9]` still carry the old 10-cell argv (`--budget 67`,
`--fetch-followup-allowance 24`); the live argv comes from `cell_argv()` (`--turns 48`, `--budget 108`,
`--fetch-followup-allowance 48`). The launcher derives its plan from `GRID-PARAMS.json shape.arms`,
not from `cells[]`.

---

## 3. The report, in the card's fixed terms

No cell wrote a rows file, so every interval below is absent by construction — not suppressed, and not
substituted.

**H1 (pooled R-all, n = 144 per pair arm via `quantile_ci`).** No measurement. 0 rows in both pair
arms, no interval printed, `n_eff` and the lag-1 `r` are not estimable (no rows to estimate them from).
The clearance figures quoted on the card (`r ≤ 0.655`; `n_eff = 62.73` at `r = 0.6423`) are properties
of the *planned* 288-turn pair arms, not of data that exists. **No H1 interval is printed for the
context arms (96 turns) either**, per the card's own binding rule; the binding arm is `none — no data`.
Verdict: **`not_adjudicable`**.

**H2 (both limbs).** `cache_inclusive` **UNDEFINED**; `uncached_ratio` **UNDEFINED**; sign **UNDEFINED**.

**H3 (`x/12` with NONE flagged, plus `x/9`, `answered_ratio`, `contract_adherence`).** 0 cells, 0 grade
files: `x/12` **N/A**, `x/9` **N/A**, `answered_ratio` — **UNDEFINED (placeholder string)**,
`contract_adherence` — **UNDEFINED (placeholder string)**. `grade_v5` has no such columns (0 hits for
either name across `experiments/ptr-engine/longrun/*.py`), so H3 here reports answer production and
accuracy only, and no substitute metric was computed.

**`tokens_to_verified_success`.** **UNDEFINED** (`docs/TVS.md`).

**Completion tokens and answer length per arm.** **UNDEFINED** — no rows exist, and no cost claim is
made anywhere on this page.

**Spend.** Delta **0** requests against `LEDGER-GRID-BASELINE-3` (`requests 1176`, `remaining 3144`,
`cap 4320`, `as_of 2026-10-26T22:33:00Z`). Recomputing from rows instead of reading the stale file:
**1,321 spent / 2,999 remaining** (ledger owner's own recount; conservative). The 30-row gap between
those two figures is §1. Era B rows are never pooled with era A's.

---

## 4. The one change that unblocks the same card

A card that may edit harness files must do both, in one pass:

1. `run_a_star.py:_row_counts()` counts `kind="turn-initial"` the way `request_ledger.py` does — or
   defers to the ledger's rule instead of carrying a second copy of it;
2. `measure/REQUEST-LEDGER.json` is **regenerated from rows** (never hand-edited) so the live figure is
   `1,321 / 2,999`, not `1,176 / 3,144`.

Then this same 16-cell card launches unchanged: generation-6 pin, price 1,056, recomputed remaining
2,999 against the 4,320 cap. No canary re-run is required — the four arms are already cleared.

## 5. Files

* `experiments/ptr-engine/measure/GRID-RUN-2.json` — the run record (machine-read).
* `orchestration/journals/GRID-RUN-2.jsonl` — `grid_start` / `grid_abort`, with the ledger figures.
* `orchestration/units/GRID-RUN-2.md` — the unit card.
* `orchestration/handoffs/GRID-RUN-2.json` — the handoff.

## Execution 2 — live era-B tools-on grid (2026-10-28T02:45Z–03:36Z)

Card `d2d00521-…`, execution `882e93a7-c048-48c7-a26a-08a5b3cecafe`, unit GRID-RUN-2. 16 cells × 48 turns, one launcher invocation per cell, sequential, no retries; tools `read_file` on; claim H2; era B.

### Preconditions quoted, not re-derived
1. Pin generation 6 `efefd885…9579b3` (`measure/HARNESS-PIN.json`); `run_a_star.py:72-73` expects it. `cell.py` is outside the pin: standalone sha256 `c494e212679f8e73c84226cf486566d0716559c0f2cd677f20845b24057baf86`, recorded at cell 1 and re-checked before **every** later cell — unchanged.
2. Canary cleared by `measure/CANARY-ERA-B-4.json` (3 arms shape_ok) + `measure/LEASE-REOPEN-23.json` (`lease=2` at T23, prefix change at T22, `lease_arm_usable_for_grid: true`). No canary re-run.
3. Tool channel live (`V-TOOL-CHANNEL`).
4. Ledger recomputed, never read: baseline `LEDGER-GRID-BASELINE-4.json` = 1,321 requests / 2,999 remaining / cap 4,320; live ledger rebuilt with `tools/request_ledger.py --write` (scratch) and passed via the launcher's documented `RUN_A_STAR_LEDGER_LIVE` hook because the repository `REQUEST-LEDGER.json` is stale by ≥115 rows and its regeneration is not in this card's write scope. Every RECONCILE line printed `gap=0`.
5. Command set verbatim from `measure/GRID-SHAPE.json`: `--max-turns 48 --tools read_file --budget 108 --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --thinking off --expect-harness efefd885…`. `GRID-PARAMS.json` rev 3 records 16 cells / price 1,056 and the launcher enforces exactly that — the card's "GRID-PARAMS still says 10 cells/1,016" tag is stale text in its `status` string only.
6. Per-cell stamping is done by the launcher (`analyze_stats.write_cell_manifest_usable_for`) into `measure/cell-<stamp>.json`.

### The 16 cells (one rows file each, never appended)

| # | arm | rep | rows file (stamp) | rows | turns | exit | usable_for |
|---|---|---|---|---|---|---|---|
| 1 | pointer-stable | 1 | 20261028T024509Z | 96 | 48 | 0 | h1,h2,h3 |
| 2 | pointer-stable | 2 | 20261028T024942Z | 93 | 48 | 0 | h1,h2,h3 |
| 3 | pointer-stable | 3 | 20261028T025312Z | 94 | 47 | **4** | — (no manifest) |
| 4 | pointer-stable | 4 | 20261028T025853Z | 93 | 46 | **4** | — (no manifest) |
| 5 | pointer-stable | 5 | 20261028T030232Z | 94 | 48 | 0 | h1,h2,h3 |
| 6 | pointer-stable | 6 | 20261028T030559Z | 89 | 48 | 0 | h1,h2,h3 |
| 7–12 | transcript-grow | 1–6 | …030925Z, 031218Z, 031401Z, 031606Z, 031753Z, 032058Z | 77,53,56,56,82,53 | 48 | 0 | **[]** zero-marker |
| 13–14 | transcript-compact | 1–2 | …032235Z, 032430Z | 66,81 | 48 | 0 | **[]** zero-marker |
| 15–16 | lease-reopen | 1–2 | …032823Z, 033139Z | 91,96 | 48 | 0 | h1,h2,h3 |

Spend: **2,591 spent / 1,729 remaining** of cap 4,320; delta vs baseline **+1,270**; unattributable gap **0** at all 15 re-checks. Price line was 1,056 (66/cell); actual 53–96/cell (+214 over price) because fetch follow-ups are billed per round, not by the price line.

### Findings
- **F1 (blocker for the report linkage).** `cell.py` writes the manifest with `rows_path` **nested under `run.rows_path`** and top-level `rows_path: null`; `analyze_stats.load_cell_manifests` requires a top-level `rows_path` (`analyze_stats.py:661-671`). Consequently `run_grid_report.py` cannot link any of the 16 rows files to its stamp and reports every cell `refused_usable_for_absent`. The stamp itself is present and correct at top level (`usable_for`). Reported, not repaired (harness files are forbidden to this card).
- **F2 (the arms' treatments never fire).** All 6 `transcript-grow` cells are stamped `[]` with "zero-marker: evicted_turns=0" and both `transcript-compact` cells `[]` with "zero-marker: digest_rows=0": prompt tokens peaked at 12,497, so neither the transcript wall nor a digest fired inside 48 turns, even though the projected preflight says "first wall at T21". The C/A pair is therefore **incomplete**, and every hypothesis that needs it is not adjudicable.
- **F3 (two cells refused mid-run).** Pointer-stable r3 and r4 were refused by the runner's own cap gate at T47/T48 (`run_longrun.py exited 4 … cap gate (G1) refused the send`), keeping 94/93 rows but writing **no manifest** — untampable, excluded by name, never pooled, not retried.
- **F4 (report census).** Because of F1 the only way to feed the tool its own stamps was a census derived **from the manifests** (`path ← run.rows_path`, `usable_for` verbatim; `[]` only for the two manifests-absent exit-4 cells). This is disclosed, and the census is scratch, not a repository artefact.

### Report (run_grid_report.py, 6 of 16 cells included: pointer-stable ×4, lease-reopen ×2)
- **H1** — no pooled R-all interval is printed for the context arms: `transcript-grow` and `transcript-compact` have **zero** usable cells, so there is no C/A pair and **the binding arm is `transcript-grow`**. What the tool can compute per included arm, with the grid's own lag-1 r and n_eff printed beside every interval:
  - pointer-stable: p50 **156.151 ms** [146.306, 291.926], n=48, **r = +0.2949, n_eff = 26.14** → below the effective-n floor of 60 ⇒ the grid's own H1 verdict is **`not_adjudicable_floor`**.
  - lease-reopen: p50 **198.395 ms** [130.843, 270.899], n=48, **r = −0.1188, n_eff = 60.95**.
  - p95 is **refused** for both (n=48 < the 60 required).
  - Named fallback: a 7th pair run (≈ +132 requests) would still not help while the grow arm is stamped unusable; the binding blocker is F2, not n.
- **H2** — both limbs computed for both included arms, both positive (cache credited): pointer-stable cached-inclusive **5,395.09** vs uncached **355.62** tokens/turn (sign **+1**, n=364); lease-reopen **1,497.85** vs **332.28** (sign **+1**, n=184). Comparison **not adjudicable**: C-vs-A pair incomplete.
- **H3** — **x/12 = 0**, **x/9 = 0**, **answered_ratio = 0.0**, **contract_adherence = "pre-check column; not folded into accuracy"** (verbatim placeholder — `grade_v5` has no contract-adherence column, so H3 reports answer production + accuracy only; no substitute was computed); NONE flagged: `cp.3.t14` pass, `cp.5.t20` undecidable, `cp.10.t42` pass; McNemar refused (0 discordant < floor 6). Verdict **not_adjudicable**. Caveat: the tool attributes H3 grades by **arm**, not by included cell, so its `transcript-grow` per-arm row (5/7) is drawn from excluded cells and is not a result.
- **TVS** — **UNDEFINED**: the graded checkpoint pass needs the C/A pair, which F2 removed from the grid.
- **Verbosity (before any cost claim)** — pointer-stable mean completion **72.65 tok**, answer **80.95 chars** (n=372 turns); lease-reopen **78.73 tok**, **54.48 chars** (n=187).

### Verdict
`not_adjudicable` across H1/H2/H3 and `UNDEFINED` for TVS — not because of sample size alone but because the two transcript arms are stamped unusable by the launcher's own marker rule (F2). The grid spent 1,270 requests and produced 6 usable cells (4 pointer-stable, 2 lease-reopen) plus 8 loud stamps and 2 named refusals.
