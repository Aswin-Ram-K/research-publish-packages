# HARNESS-MAP-PREGRID — the scoreboard on the corpus that exists

**pre_grid: true.** Unit `HARNESS-MAP-PREGRID`, 2026-10-26. Written **before** the grid so it cannot be
fitted to a result. Offline: **zero inference requests, zero sockets**, read-only over every artefact it
grades. It grades the harness and this session's conduct, not the arms. Nothing here is a cell result;
the two existing `rows-cell-*` files are cited **only** as evidence about launch mechanics and both carry
`usable_for: []` (`experiments/ptr-engine/measure/GRID-REPORT-2.json`, `measure/ANALYSIS-PATH.json`).

Bound: ≤30 tool calls (used 27). Every number carries its path; a figure that could not be re-derived is
**omitted**, never estimated.

---

## 1. Stage map at HEAD (`f17663d1fed0162a7dc3c5a0a58d372c710974c3`)

**13 stages, 0 `unlocated`.** "Refuses" is the exit code the stage itself raises; the table lives in
`experiments/ptr-engine/longrun/exit_codes.py` and `cell.py` refuses to keep a second copy
(`cell.py:39-41`).

| # | stage | `file:line` | reads | writes | refuses (exit) |
|---:|---|---|---|---|---|
| 1 | Preflight | `experiments/ptr-engine/longrun/cell.py:247 stage_preflight()` | fixture JSON: `system_prompt`, `checkpoints[].turn/question/truth/answer_spec`, arm list | nothing | **2** — no/empty `system_prompt` (`cell.py:255-260`), no checkpoints, arm not in runner's arms |
| 2 | Harness freeze | `cell.py:329 stage_harness()`, list at `cell.py:128 HARNESS_FILES` | 5 harness files + the fixture | digest into the record; compared to `--expect-harness` | **2** — harness file missing or digest moved (`cell.py:342-346`) |
| 3 | Budget / G1 ledger | `cell.py:354 stage_budget()`, `:1215 eval_gate_ledger()`, `tools/request_ledger.py:787 main()` | row files on disk, `--budget`, cap/reserve | ledger JSON via `--write` (`request_ledger.py:821`) | **4** `EXIT_OVER` (`request_ledger.py:131`), **5** rows unreadable (`:132`), **3** usage (`:130`) |
| 4 | G2 projection | `cell.py:813 stage_projection()`, `:683 eval_gate_projection()` | projection artefact (p90 per thinking mode), `--max-wall`, `--turn-wall-cap` | gate verdict in the cell record | **8** — projected wall > limit (`docs/CANARY-ERA-B.md:40-43` shows `REFUSED(8)`) |
| 5 | G3 prereg / hypothesis | `cell.py:1390 eval_gate_prereg()` | claim sidecar (`*claim.json`), fixture checkpoint count (≥8) | gate verdict | **12** — no declared hypothesis (`docs/GATE-CHAIN.md:95`) |
| 6 | Run | `cell.py:1571 stage_run()` → `run_longrun.py:2191 run_cell()` | frozen manifest, fixture, endpoint | rows jsonl (append-only), claim sidecar (`cell.py:1601`) | runner codes; **5** `EXIT_RUNNER_CRASH` remap (`cell.py:1639`), **9** `EXIT_CAP_DIVERGENCE` (`run_longrun.py:318`) |
| 7 | Row writing | `run_longrun.py:1781 make_row()`, `:1998 append_row()` | response payload, usage, manifest sha | one row **per request**, fsynced | — (a failed row blocks resume: `:2039`) |
| 8 | Grade | `cell.py:1648 stage_grade()` → `grade_v5.py:1081 main()` | rows + fixture truth, derived from the source tree (`grade_v5.py:553 derive_truth`) | `<rows>.grade-v5.json` (`grade_v5.py:1101`) | `SystemExit` on `fixture_truth_mismatch` (`:463`, `:582`) |
| 9 | Analyse | `cell.py:1671 stage_analyse()` → `analyze_stats.py:1620 main()` | rows, grade, manifests' `usable_for` (`analyze_stats.py:714`) | analysis JSON (`:1840`) | `SystemExit` `no usable cells` (`:1761`), `--rows` required (`:1675`) |
| 10 | Record | `cell.py:1775 stage_record()` | gate verdicts, grade, analysis | `measure/cell-<arm>-<stamp>.json` + `.md` (`:1785`, `:1835`) | propagates the refusing stage's code |
| 11 | Launcher | `experiments/ptr-engine/tools/run_a_star.py:467 main()` | `HARNESS-PIN` record, prior cell stamp (`:266`) | `run-a-star.json` (`:131`), journal (`:116`) | **4** `EXIT_UNSTAMPED_CELL` (`:68`) |
| 12 | Verdict binding | `tools/tree_freeze.py:413 wrap()`, `tools/verdict_scope.py:198 run()` | git HEAD / tracked path bytes | freeze record (`tree_freeze.py:505`), verdict payload (`verdict_scope.py:180`) | **13** tree moved, **2** usage, **1** command failed |
| 13 | Request ledger report | `tools/request_ledger.py:571 build_report()` | every row file matched | `--write` JSON only | **4** over cap (`:846`), **5** (`:811`) |

### Diff against `docs/HARNESS-MAP.md` (v1, 18 stages)

- **New (9):** preflight, harness freeze, G1 ledger, G2 projection, G3 prereg, launcher
  `run_a_star.py`, `tree_freeze.py`, `verdict_scope.py`, `request_ledger.py`. The v1 map's cells were
  launched by hand; the whole gate chain is now inside `cell.py`.
- **Replaced in the chain (1):** v1 stages 9/10 (`grade_v3`, `grade_v4`) are still on disk but the cell
  chain grades with `grade_v5` (`cell.py:1648`).
- **Gone:** none removed.
- **Moved — every `run_longrun.py` line reference in the v1 map is stale.** The file grew to 3008 lines
  (`wc -l`), so v1's `:859 build_manifest` is now `:1404`, `:938 write_manifest` → `:1498`,
  `:1191 make_row` → `:1781`, `:1296 append_row` → `:1998`, `:1344 run_dry` → `:2057`,
  `:1445 run_cell` → `:2191`, `:709 Planner` → `:1050`, `:1026 send_chat` → `:1541`. **8 of 8 checked refs
  do not resolve to the named function.** The map's *content* still reads correctly; its *citations* no
  longer re-derive, and this card does not edit it.

---

## 2. Cost — two tables, never averaged

### 2a. Offline (this batch, no requests)

Basis: all `orchestration/handoffs/*.json` whose mtime is 2026-10-26 — **282 settled cards**. Fields are
whatever each handoff recorded; 147 recorded `tool_calls`, 141 recorded `bound`.

| figure | value | basis |
|---|---|---|
| settled cards today | **282** | `orchestration/handoffs/*.json` mtime = 2026-10-26 |
| `tool_calls` per card | **median 21**, range 6–45, n=147 | `handoff.tool_calls` |
| `bound` per card | **median 26**, range 14–60, n=141 | `handoff.bound` |
| rounds that recorded **0** tool calls | **0 of 147** | same |
| rounds that spent **0 requests** (proxy) | **280 of 282** | only 2 row files exist today (`rows-cell-*` 10:17, 13:31); every other card wrote none. *Proxy only:* a card can spend requests without a row file, so this is an upper bound on zero-request rounds, not a count |
| status mix | done 221 · partial 47 · pass 7 · fail 5 · blocked 2 | `handoff.status`/`overall` |

### 2b. Live (per cell, requests)

| cell | rows = requests | turns | requests/turn | latency sum | ttft p50 | stop reasons | usable_for |
|---|---:|---:|---:|---:|---:|---|---|
| `measure/rows-cell-pointer-stable-20261026T145758Z.jsonl` | **6** | 1–6 | **1.00** | 1145.6 s | 299 ms | none recorded (6) | `[]` |
| `measure/rows-cell-pointer-stable-20261026T182535Z.jsonl` | **27** | 1–27 | **1.00** | 346.9 s | 141.6 ms | stop 25 · length 1 · runaway_turn 1 | `[]` |

Factor path: `run_longrun.py:1781 make_row()` writes one row per request and a tool fetch buys a second
row, so rows **are** requests; both cells ran with **0 tool calls** (`sum(len(tool_calls)) = 0`), hence
1.00 requests/turn. The 48-turn projection multiplies requests by the calibrated **60 s/turn**
(`docs/CANARY-ERA-B.md:52-53`).

**The one live launch attempt** (`LIVE-CANARY-4ARM`, exec `bd952f84`): **1 warm-up + 0 cell requests**,
stopped pre-request at `rc 8` because `stage_budget` priced the runner's dry run at the fixture's full
**48 × 60 = 2880 s > 900 s** (`docs/CANARY-ERA-B.md:40-43`). Wall-clock for that attempt is not recorded
in any artefact I can read → **omitted**.

---

## 3. The 14 v1 inefficiencies, re-adjudicated at HEAD

**closed 6 · narrowed 7 · open 1 · superseded 0.** A `closed` below names a refusal site or test path;
anything softer is `narrowed`.

| # | v1 item | state | proving path (checked this card) |
|---:|---|---|---|
| 1 | answer shape never constrained | **closed** | `cell.py:255-260` refuses a fixture with no `system_prompt` (exit 2); contract emitted/parsed by `run_longrun.py`; `longrun/tests/test_answer_contract.py` exists (6191 B) |
| 2 | fixture re-authoring, 4 generations | **open** | a 7th generation exists (`tasks-v6/LR-01.v7.json`) and v6 is still in service; no pool rule anywhere |
| 3 | answerless acceptance, 36/92 missing | **narrowed** | current fixture 12/12 decidable, but the historical 36/92 empty cells are untouched — absent ≠ fixed |
| 4 | tool channel refuses silently | **narrowed** | `run_longrun.py:999` writes `"error": "turn_call_cap"` into the row's census; still no hint injected into the `<tool_result>` the model reads |
| 5 | budgets in three currencies | **closed** | one ledger: `tools/request_ledger.py` (cap/reserve/`deduction_permitted:169`), read by `cell.py:1215`; dedup explicitly not deducted |
| 6 | mid-cell code-version mixing | **narrowed** (V3 said closed) | digest binds **5 files + fixture** (`cell.py:128-135`) and resume refuses on manifest-sha change (`run_longrun.py:2039`, `:2232`) — but **`cell.py` is not in its own list** (`measure/HARNESS-PIN.json: digest_recipe`: "cell.py is NOT in its own list"), so the conductor's bytes are unbound |
| 7 | no grader line-of-descent | **narrowed** | `grade_v5.py` has **0** occurrences of `fixture_sha256` (grep at HEAD) — the chain's grader still does not assert the row's fixture |
| 8 | handoff stubs strand on restart | **closed** | test path `tests/test_orchestration_handoffs.py`; measured today **1158 handoffs, 0 unparseable** (my parse) — not re-run as a test here to avoid writing caches |
| 9 | acceptance gate undecidable for 5/13 | **narrowed** | no artefact tier is written by the runner; `repair.t30` remains judge-undecidable (`regrade-det.json:limits[0]`) |
| 10 | verification guard red, not runnable | **narrowed** | `tests/test_orchestration_handoffs.py` exists but the recorded state is 1 failed / 21 passed (V3), naming 4 gap files; not re-run here |
| 11 | reasoning spend dominates, truncates | **closed** | mode-aware projection: `cell.py:683/813` with per-mode p90 from the artefact; wrong-mode override is a refusal (exit 8) |
| 12 | three graders disagree, none authoritative | **narrowed** | the chain has one grader (`cell.py:1648` → `grade_v5`), but nothing on disk proves `det_verify` retired; not re-derived here |
| 13 | cross-run regrade is prose | **closed** | `tools/regrade.py` exists (20 919 B, mtime 12:21) + `docs/REGRADE.md` |
| 14 | prereg prose re-authored | **closed** | G3 refuses a cell with no hypothesis (**exit 12**, `docs/GATE-CHAIN.md:95`; `cell.py:1390`) |

**Still open: #2** (fixture generations, no pool rule). **7 narrowed** are the live edge: #3, #4, #6, #7,
#9, #10, #12 — each has a repair and an unrepaired tail.

---

## 4. New waste this batch introduced (ranked; mine included)

| rank | waste | count / cost | evidence |
|---:|---|---|---|
| 1 | **This card duplicates `HARNESS-MAP-V3`.** V3 already re-adjudicated the same 14 items and priced the same batch (§3–§6); I re-derived a second scoreboard over the same corpus because `HARNESS-MAP-V4`'s completion test is post-grid. That is one full card (27 calls) spent on a second view of one corpus. | **1 card, 0 requests** | `docs/HARNESS-MAP-V3.md:62-136` |
| 2 | **A grid card gates 1,056 while the price artefact says 1,016.** `RUN-A-STAR-2` is titled "≈1,056 requests"; `measure/GRID-PARAMS.json :: price.total = 1016` (964 tranche + 48 canary + 4 warm-ups); the successor canary card calls the 1,016/10-cell figure "superseded". | **40-request disagreement on the number a launch is authorised against** | `measure/GRID-PARAMS.json`, `task_board_list` todo `d2d00521`, `e07e2764` |
| 3 | **A phantom tool is still cited.** `tools/verdict_with_freeze.py` does not exist; it is named in `docs/PATH-REFS.md:17` (twice, two cards), and **survives in `measure/COLD-START-SCORE.json:78`**. | **1 surviving citation** | `orchestration/units/PHANTOM-PATH-FIX.md:42`; `ls experiments/ptr-engine/tools/` |
| 4 | **The verification sha does not bind most harness bytes.** **8 of the 10** chain files are **untracked** (`client.py`, `grade_v5.py`, `analyze_stats.py`, `cell.py`, `run_a_star.py`, `tree_freeze.py`, `verdict_scope.py`, `request_ledger.py`); only `run_longrun.py` and `tools/det_verify.py` are tracked. A verdict row's `sha` therefore says nothing about the bytes that graded or launched. | **8 of 10 files** | `git ls-files --error-unmatch` |
| 5 | **`cell.py` is outside its own `HARNESS_FILES`** — deliberately, but it is the file that computes G1/G2/G3 and runs the budget stage; the pin's own recipe says so. | **1 conductor unbound** | `cell.py:128-135`; `measure/HARNESS-PIN.json:digest_recipe` |
| 6 | **A 12-turn canary was arithmetically impossible under a 48-turn projection.** Dry run priced 12 turns (720 s ≤ 900), live gate priced the fixture's N=48 (2880 s > 900) → exit 8, 0 cell requests, both defects carded after the spend of a warm-up. | **1 warm-up, 0 cell requests; 1 card** | `docs/CANARY-ERA-B.md:40-61` |
| 7 | **Proof-line drift is silent.** V3's proofs for #5/#6 cite `cell.py:223` (handle-harness) and `run_longrun.py:938`/`:1465`; at HEAD `cell.py:223` is `n += 1` inside `_count_rows`, `run_longrun.py:938` is an `engine_root` existence check, `:1465` is a provenance comment. A verifier that checks *line exists* passes; one that checks *the code the line is said to do* fails. | **3 of 3 checked proofs stale** | `cell.py:217-225`, `run_longrun.py:930-945`, `:1459-1472` |
| 8 | **Three instruments are blind to exactly what they protected**: `grade_v5` binds no fixture sha (#7 above); the harness pin excludes `cell.py` (#5); the verdict `sha` is a git commit that cannot contain the untracked files (#4). | **3 instruments, 3 blind spots** | as cited |
| 9 | **`todo` is inflated by cards that are not this batch's work**: measured `todo = 25` on the board, spanning **3 workspaces** (`78cead56` project, `30b03b80` lead, `6b0e96bc` fleet) with `executionCount: 0` on every never-run card read. The often-quoted "11 foreign cards" is **not re-derivable from the summary read here → omitted**; the measured foreign minimum is 2. | **≥2 foreign, 25 local todo** | `task_board_list` summary + todo rows |

---

## 5. Verdict-rate table

Denominator: **closures**, from `~/.dsh/storages/orchestration/closure.jsonl` (event-sourced `put`
records, 1058 closures). Numerator: a task with ≥1 row in `verdict.jsonl` (182 rows, **177 distinct
tasks**).

| window | closures | with a verdict row | rate |
|---|---:|---:|---:|
| all closures to date | 1058 | 184 | **17.4 %** |
| before the ritual (10:30–11:13 local) | 38 | 1 | **2.6 %** |
| **after the ritual landed (11:13:05 local →)** | **169** | **159** | **94.1 %** |

The ritual moved the behaviour: **94 %** of post-ritual closures carry a row, against **2.6 %** in the
window before it. Two caveats that stop this being a clean win:

- **Retroactive rows, reported separately:** **35** verdict rows were recorded **after** their own card's
  closure (`at` > the closure's `createdAt`). They count in the numerator but they are not evidence the
  card recorded a row *before* handoff — **they do not move a column** and no column above is adjusted for
  them.
- **The `sha` in a row binds a commit, not the harness.** HEAD is
  `f17663d1fed0162a7dc3c5a0a58d372c710974c3` and the most recent verdict row names exactly that sha — yet
  8 of the 10 chain files are untracked, so that sha is silent about the bytes that graded the run.
  `verdict_scope.py run --paths … -- <cmd>` (exit 13 = moved, never FAIL) is the instrument that would
  bind bytes; it is not what the recorded rows used.

---

## 6. Did building an experiment get cheaper?

### `not measurable yet`

**The missing instrument is one gated, completed cell.** A "cell" here means
`measure/cell-<arm>-<stamp>.json` + `cell-<arm>-<stamp>.gates.json` + a rows file + a grade, i.e. a run
that passed G1/G2/G3, sent requests, and was graded — and there are **zero** such artefacts: the only two
`rows-cell-*` files hold 6 and 27 rows and both carry `usable_for: []`
(`measure/GRID-REPORT-2.json`, `measure/ANALYSIS-PATH.json` declare them `included: false`,
`cell_state: in_progress`).

**Era-B absence is the reason, and it is exact:** no era-B cell exists — the only era-B evidence on disk
is a *stand-in* slice of era-A rows (`measure/ANALYSIS-PATH.json :: era_b_standin_rows` →
`rows-longrun-v6-tools.jsonl`, 72 rows), and the era-A cells on disk are 33 rows whose every published
use is refused. So the batch's live spend is **33 rows / 0 graded cells**, and the process cost beside it
is **282 settled cards, median 21 tool calls, median bound 26, 0 requests** — a card-to-cell ratio that
has no cell in its denominator.

Until one cell exists, "cheaper" would be a claim about documents, not about experiments.

---

## 7. What a pre-grid scoreboard cannot say

**It cannot say whether the grid will be cheaper, or which arm is better** — no cell in this repository
has been graded, both existing cells are `usable_for: []`, and every cost here is the price of *preparing*
to measure, not of measuring.
