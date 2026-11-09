# PARM-1 ERRATA — the denominators, made honest before the grid runs

**Unit:** `PARM-1-ERRATA`. **Dated (UTC):** `2026-10-26T15:56:40Z`. **Requests:** 0.
**Status:** additive errata. Nothing in this file edits, re-freezes, or supersedes `docs/PREREG-ARM-RUN.md`.

This is **not** a revision of the rule. The rule body still hashes to
`21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8`
(`docs/PREREG-ARM-RUN.md:276`), recomputed from the delimited body by the command at
`docs/PREREG-ARM-RUN.md:264-273`. Every threshold below is **byte-unchanged**. What changed is *what
those thresholds are applied to* — the census of items behind them — and that census was frozen in a
fixture that has since moved.

Two units landed after the freeze and neither is reflected in the frozen text:

| unit | what it did | artefact |
|---|---|---|
| `CHECKPOINT-ITEMS-V2` | replaced the fixture with `LR-01.v7.json`, where **12/12 checkpoint ids are decidable**, but **3 of the 12 are NONE-kind** (the arm must answer `ANSWER: NONE`) | `experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` (sha256 `42b4df007352d9397778d9e2b50b1b64ef451190e54ea2c6d1992f9f77bd8392`) |
| `TVS-DEFINE-AND-COMPUTE` | dropped `repair.t30` from the TVS declared space; TVS now has a **3-id denominator**, which is a *different claim* from H3's 12 | `docs/TVS.md:78-96`, `experiments/ptr-engine/measure/TVS.json` |

A reader of `RUN-A*` will see both `x/12` and a tvs in the same report. Without this errata they would
merge them. E1–E4 are the separations. E5 records what is still not settled.

---

## E1 — H3's 12 ids are **9 substantive + 3 NONE**, and both counts travel with every H3 number

**What the frozen text says** (`docs/PREREG-ARM-RUN.md:99`):

> **Margin (frozen): 2 checkpoints out of the 12 declared checkpoints = 16.7 percentage points.**

and (`docs/PREREG-ARM-RUN.md:103-104`):

> The margin is stated on the 12-item denominator, so "no worse than 2 checkpoints" and "no worse
> than 16.7 pp" are the same rule; a run that loses more than 2 checkpoints fails H3 even if the
> paired test is silent.

and (`docs/PREREG-ARM-RUN.md:113-114`):

> **Unadjudicable clause:** if either arm's `decidable` is below **8 of 12**, H3 returns **no
> verdict** and the run is `not adjudicable`; it must not be read as a pass.

**What is now measured.** The 12 declared ids and their kinds, re-read from the frozen fixture
`experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json`:

| # | id | turn | kind | substantive? |
|---|---|---|---|---|
| 1 | `cp.0.t06` | 6 | CALL | yes |
| 2 | `cp.1.t08` | 8 | CALL | yes |
| 3 | `cp.2.t12` | 12 | NUM | yes |
| 4 | `cp.3.t14` | 14 | **NONE** | **no** |
| 5 | `cp.4.t18` | 18 | NUM | yes |
| 6 | `cp.5.t20` | 20 | **NONE** | **no** |
| 7 | `cp.6.t24` | 24 | NUM | yes |
| 8 | `cp.7.t26` | 26 | NUM | yes |
| 9 | `cp.8.t32` | 32 | NUM | yes |
| 10 | `cp.9.t36` | 36 | CALL | yes |
| 11 | `cp.10.t42` | 42 | **NONE** | **no** |
| 12 | `cp.11.t46` | 46 | CALL | yes |

Census: **NUM 5 · CALL 4 · NONE 3**; **9 substantive + 3 NONE = 12**. The three NONE ids are
**T14/T20/T42** — fixture ids `cp.3.t14`, `cp.5.t20`, `cp.10.t42` (question/kind table:
`docs/CHECKPOINT-COVERAGE.md:20-37`).

A NONE item is gradeable and is a real checkpoint — it asserts that a call is **absent** inside a
function. But its answer is the constant `ANSWER: NONE`, so a degenerate policy that always answers
`ANSWER: NONE` passes all three for free. That is exactly the pre-existing caveat recorded by
`CHECKPOINT-ITEMS-V2` (`orchestration/handoffs/CHECKPOINT-ITEMS-V2.json`, `caveats[0]`):

> A constant ANSWER: NONE passes the three NONE items for free: 3 of 12 decidable items have a
> constant-answer floor. The denominator is honest, one quarter of it is cheap.

**What the run will therefore report.** Neither denominator replaces the other; **both travel with
any H3 number**:

1. **`x/12`** — the frozen denominator, with the 3 NONE items **flagged**: any `x/12` must say how
   many of the `x` are NONE items, and how many of the 12−`x` misses are NONE items. A degenerate
   arm's `x` must not be read as `x` semantic checkpoints.
2. **`x/9`** — the same pass counts over the **substantive** (NUM/CALL) items only, reported
   alongside, labelled as a decomposition of the `x/12` number and not as the H3 gate.

The **gate itself stays on `x/12`** and on the frozen "loses more than 2 checkpoints" rule: E4.

## E2 — TVS's denominator is **3 ids**, not 12, and TVS is a different claim from H3

**What the frozen text says.** H3's denominator is `docs/PREREG-ARM-RUN.md:99` (quoted in E1). TVS
is not mentioned in `docs/PREREG-ARM-RUN.md` at all; it is defined and settled in `docs/TVS.md`.

**What is now measured** (`docs/TVS.md:89-90`):

> | declared space per arm | 4 ids (`cp.0.t12`, `cp.1.t24`, `cp.2.t46`, `repair.t30`) | 3 ids (`cp.0.t12`, `cp.1.t24`, `cp.2.t46`) |
> | permanently undecidable items | 1 (`repair.t30`, 13/13 pairs) | 0 |

and `docs/TVS-RESULTS.md:18`:

> `repair.t30` | dropped from TVS's declared space: grade_v5 emits no verdict for it, so it can
> neither certify a success nor sit in the denominator

**What the run will therefore report.** TVS is a **cost-to-first-verified-checkpoint** metric: the
prompt+completion tokens summed from the first request through the first checkpoint turn whose cell
`grade_v5` graded `pass`. Its denominator is **3 declared ids per arm** — the three v5 truth
checkpoints, retained verbatim in value and turn (`docs/CHECKPOINT-COVERAGE.md:41-43`). Under the v7
renumbering those ids are `cp.2.t12`, `cp.6.t24`, `cp.11.t46`; the v6 id spellings above stay the
names of record because the historical grade files use them
(`experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` → `id_map`).

**TVS must never be written as a fraction of 12.** `x/12` is "how many of twelve checkpoints did the
arm answer correctly"; a TVS is "how many tokens did it cost to reach the *first* verified
success". They have different denominators, different units and different populations, and a tvs
value is not comparable across a fixture change. The only shared object between them is that TVS's
3 ids are a **subset of** H3's 12 — and, measured, a subset of the **substantive** 9 (NUM, NUM,
CALL; no NONE).

## E3 — `repair.t30` is outside the TVS space, undecidable under `grade_v5`, and **not one of H3's 12**

**What the frozen text says.** Nothing about `repair.t30`; H3's population is the 12 checkpoint ids
at `docs/PREREG-ARM-RUN.md:99`. `docs/LATENCY-REPORT.md:359-368` (quoted at `docs/TVS.md:19-21`)
had made "four declared checkpoints" = three fixture truth checkpoints **plus `repair.t30`** the
arm-level conjunction, and that is where the 13-item reading came from.

**What is now measured.** `repair.t30` is a fixture *repair* at turn 30
(`experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` → `repair.at_turn = 30`), **not** a
checkpoint id: the fixture's `checkpoints[]` turns are
`6,8,12,14,18,20,24,26,32,36,42,46` — turn 30 is absent. It has **no `grade_v5` cell in any pair**
(`docs/TVS.md:80-84`), and it is not in TVS's declared space (`docs/TVS.md:78-96`).

**Count arithmetic (shown, because the reviewer must see the number):**

| reading | denominator | margin of 2 checkpoints | status |
|---|---|---|---|
| frozen H3 (`PREREG-ARM-RUN.md:99`) | 12 ids | 2/12 = **16.7 pp** | **in force** |
| 13-item reading incl. `repair.t30` (`LATENCY-REPORT.md:359-368`) | 13 ids | 2/13 = 15.4 pp | **not in force**; `repair.t30` has no instrument |
| H3 without the 3 NONE items (E1 decomposition) | 9 substantive ids | 2/9 = 22.2 pp | reported **alongside**, not a gate |
| TVS declared space (E2) | 3 ids | n/a — TVS is a token sum, not an accuracy margin | in force for TVS |

**Answer to the question H3 must state:** **`repair.t30` is not scored.** It is not among the 12 and
not in the TVS space; the frozen 12-item denominator is therefore **unaffected** by its exclusion and
the 16.7 pp figure is arithmetically intact. What *would* have changed the denominator was counting
it as a 13th item, and the frozen text does not.

**What the run will therefore report.** Any statement about `repair.t30` is a statement about turn 30
behaviour, never an H3 item: no pass, no fail, no cell, no denominator.

## E4 — thresholds that are **NOT** changed (this errata loosens nothing)

Every entry below is byte-unchanged from the frozen rule body and is re-asserted by
`experiments/ptr-engine/tools/parm1_errata_check.py` against recorded digests. Listed so this errata
cannot be read as a loosening:

| # | threshold | frozen value | frozen at |
|---|---|---|---|
| 1 | H3 margin | **2 checkpoints** out of 12 | `docs/PREREG-ARM-RUN.md:99` |
| 2 | H3 margin as a percentage | **16.7 pp** (= 2/12) | `docs/PREREG-ARM-RUN.md:99` |
| 3 | H3 failure rule | more than 2 checkpoints lost ⇒ **fail**, whatever McNemar says | `docs/PREREG-ARM-RUN.md:104` |
| 4 | H3 unadjudicable gate | `decidable < 8 of 12` ⇒ **no verdict** | `docs/PREREG-ARM-RUN.md:113` |
| 5 | H2 materiality | C ≤ **0.95 ×** A on prompt tokens | `docs/PREREG-ARM-RUN.md:69` |
| 6 | H2 uncached field | C **< 1.00 ×** A | `docs/PREREG-ARM-RUN.md:70` |
| 7 | H1 admissibility | `MIN_N=20`, `TAIL_MIN=3` ⇒ **n ≥ 60** at q=0.95 | `docs/PREREG-ARM-RUN.md:35-36` |
| 8 | H1 level | `LEVEL=0.95` | `docs/PREREG-ARM-RUN.md:33` |
| 9 | H1 bootstrap | `resamples=10000`, `seed=20261020` | `docs/PREREG-ARM-RUN.md:32-33` |
| 10 | H1 ranking | disjoint intervals only | `docs/PREREG-ARM-RUN.md:38-39` |
| 11 | H3 secondary veto | McNemar licensed only at `b + c >= 6`, `p < 0.05` | `docs/PREREG-ARM-RUN.md:106-108` |

Consequences, stated to be unambiguous:

- The **gate is unchanged**: H3 still fails at a loss of more than 2 checkpoints **on the 12-item
  denominator**, and the `8 of 12` unadjudicable clause is unchanged. The `x/9` substantive view in
  E1 is a **reporting decomposition**, never a second gate; it cannot turn a 12-item failure into a
  pass, and it does not create an `8 of 9` adjudicability rule.
- **No threshold moves with the census.** If a settled grid's `decidable` is below 12 (a turn goes
  missing, a cell returns `verdict: text`), the number of checkpoints allowed to be lost is still
  **2**, and the percentage is recomputed as 2/`decidable` and printed next to the count — arithmetic,
  not a new rule. If `decidable < 8`, H3 is unadjudicable and the run says so.
- The TVS drop of `repair.t30` (E2/E3) changes a **different metric's** declared space; it does not
  touch H3.

## E5 — what this errata does **not** claim: decidable-on-paper is not decidable-in-a-run

`CHECKPOINT-ITEMS-V2` settled **`partial`**, not `done`
(`orchestration/handoffs/CHECKPOINT-ITEMS-V2.json`, `"status": "partial"`), and this errata does not
upgrade it. The exact position, measured offline today with
`experiments/ptr-engine/tools/fixture_coverage.py` over `LR-01.v7.json` (exit 0):

> `PASS: 12/12 checkpoints decidable, none colliding, all <= 40 tokens`

So **12 of 12 declared ids are decidable on the fixture** — 0 undecidable-on-paper, 0 missing. The
`partial` is about **quality, not coverage**: three of those twelve are NONE items with a
constant-answer floor (E1), which is why this errata separates `x/12` from `x/9` rather than
celebrating 12/12.

What is *not* claimed: that any **settled run** is decidable at 12/12. H3's population is `grade_v5`
cells (`analyze_stats.py:431-463`), and a run's `decidable = pass + fail` can be smaller — `text`
verdicts and `turn_missing` leave the denominator and are printed by name. `docs/TVS.md:95` records
the state of the settled corpus at its writing ("rows carry only 3 of the 12 declared ids"); no v6
`RUN-A*` grid exists yet (`docs/PREREG-ARM-RUN.md` §1, H2 note: "no v6 rows exist"), so the run-time
denominator is unknown **and must be reported, not assumed**. An errata that overstated decidability
would be worse than the frozen text; there is nothing here to overstate beyond 12/12 on paper.

---

## Machine-readable claims (parsed by `parm1_errata_check.py`)

<!-- parm1-errata-claims:begin -->
```json
{
  "unit": "PARM-1-ERRATA",
  "date_utc": "2026-10-26T15:56:40Z",
  "prereg": "docs/PREREG-ARM-RUN.md",
  "frozen_digest": "21cb85511b78dc4046f0f8f1449b68a7de2fd8bd8f659985efd63c9651398ec8",
  "threshold_digest": "069d28a4a023856b5b82273247568fba5b6a83a2f8ad81cee154e668ed6d64f6",
  "fixture": "experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json",
  "fixture_sha256": "42b4df007352d9397778d9e2b50b1b64ef451190e54ea2c6d1992f9f77bd8392",
  "ids_total": 12,
  "ids_substantive": 9,
  "ids_none": 3,
  "ids_by_kind": {"NUM": 5, "CALL": 4, "NONE": 3},
  "none_ids": ["cp.3.t14", "cp.5.t20", "cp.10.t42"],
  "substantive_ids": ["cp.0.t06", "cp.1.t08", "cp.2.t12", "cp.4.t18", "cp.6.t24", "cp.7.t26", "cp.8.t32", "cp.9.t36", "cp.11.t46"],
  "decidable_fixture": 12,
  "undecidable_fixture": 0,
  "h3_denominator": 12,
  "h3_margin_checkpoints": 2,
  "h3_margin_pp_on_12": 16.7,
  "h3_unadjudicable_below": "8 of 12",
  "tvs_denominator": 3,
  "tvs_ids": ["cp.0.t12", "cp.1.t24", "cp.2.t46"],
  "tvs_ids_v7": ["cp.2.t12", "cp.6.t24", "cp.11.t46"],
  "rep_t30_status": "excluded: not one of H3's 12 checkpoint ids and not in TVS's declared space; no grade_v5 cell exists for it",
  "rep_t30_in_h3_denominator": false,
  "rep_t30_scored": false,
  "thresholds_unchanged": ["h2_ratio", "h2_uncached", "h3_margin", "h3_margin_rule", "h3_unadjudicable", "level", "mcnemar_alpha", "mcnemar_discordant", "min_n", "p95_min_n", "resamples", "seed", "tail_min"]
}
```
<!-- parm1-errata-claims:end -->

## Provenance of every figure in this file

| figure | source |
|---|---|
| rule-body sha256 `21cb85…` | `docs/PREREG-ARM-RUN.md:276`; recomputed by the tool (exit 0) |
| 12 ids, turns, kinds NUM 5 / CALL 4 / NONE 3 | `experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` `checkpoints[]`, `answer_spec.kind`; `docs/CHECKPOINT-COVERAGE.md:20-37` |
| 12/12 decidable, none colliding, ≤ 40 tokens | `python3 experiments/ptr-engine/tools/fixture_coverage.py --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v7.json` → exit 0 |
| 9 substantive + 3 NONE | same fixture, `answer_spec.kind != "NONE"` |
| the NONE constant-answer caveat | `orchestration/handoffs/CHECKPOINT-ITEMS-V2.json` → `caveats[0]` |
| TVS 4 → 3 ids, `repair.t30` dropped | `docs/TVS.md:78-96`; `docs/TVS-RESULTS.md:18` |
| TVS's 3 ids are a subset of the substantive 9 | fixture `id_map` (v6→v7) + kind census above |
| 2/13 = 15.4 pp was never in force | `docs/TVS.md:95`; `docs/PREREG-ARM-RUN.md:99` states 12 |
| thresholds 1–11 | `docs/PREREG-ARM-RUN.md:32-33`, `:35-36`, `:38-39`, `:69-70`, `:99`, `:104`, `:106-108`, `:113` |
