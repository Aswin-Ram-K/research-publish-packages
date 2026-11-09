# Treatments: making the four long-run arms reachable at the frozen 48-turn horizon

Owner: unit `FIXTURE-TREATMENTS`. Evidence: `experiments/ptr-engine/measure/FIXTURE-TREATMENTS.json`.
Fixture: `experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json` (v7 is frozen and byte-identical,
sha256 `42b4df007352d9397778d9e2b50b1b64ef451190e54ea2c6d1992f9f77bd8392`).

## The measurement that forced this

Across the settled grid corpus (576 turn rows, 4 controlled grids) **no row ever took a treatment
path**: `evicted > 0` on **0** rows, `lease > 1` on **0** rows, digest rows **0**. At the frozen
`wall_tokens: 65536` the measured first-fire turns were G4 grow **T94**, G4 compact **T847**,
stage1 grow **T1654**, stage1 compact **T571**, v3 grow **T1046**, v4 grow **T1010** — every growth
arm spends all 48 turns on its control path. `lease-reopen` was unreachable at *any* N because
`lease_reopen_turns` was absent from all 12 runtime fixtures.

Three things changed. The horizon (PARM-1 line 137, N=48) did not.

## 1. Fixture `LR-01.v8.json`

| field | v7 | v8 | why |
|---|---|---|---|
| `wall_tokens` | 65536 | **3838** | the value the unit card names: `2114 + 75.021 x 23 = 3839.5`, the published `wall_for_T24` of the G4 transcript-compact cell |
| `wall_tokens_by_arm` | — | **10616** (all four) | `prompt_T1(3848) + ceil(294.27 x 23)`; see "Per-arm wall" |
| `lease_reopen_turns` | absent | **[23, 40]** | the reopen predicate reads this list and nothing else |
| `expected_digests` | runner literal `2` | **derived string** | a third digest aborted a legal cell at exit 4 |
| `treatments` | — | block | declares the contract the launch precondition is armed by |

**The 3838 is 10 tokens below this fixture's own first prompt** (working set 3818 tokens +
question = 3848). On v8 it fires at T2 and compacts a transcript that never fit — a fixture-size
effect, not a treatment effect. It is kept on the top-level field because that is the number the
card names, and it is *documented rather than silently raised*: the growth arms run at
`wall_tokens_by_arm`.

### Per-arm wall, not per-grid

Answer verbosity differed **~9x** between arms inside one grid (G4: grow answers far longer than
compact's), so one `wall_tokens` copied across arms measures verbosity as much as treatment.
The wall is therefore a **fixture field per arm** (`wall_tokens_by_arm`), never a CLI default:

    wall_tokens_by_arm[arm] = prompt_T1(fixture) + ceil(mean declared answer padding x 23)
                            = 3848 + ceil(294.27 x 23) = 10616

where `294.27 = sum(answer_padding_by_turn)/48` and each turn's padding is
`answer_budget.words_per_turn_kind x tokens_per_word_assumed` (150 words → 203 tokens on work,
plant and repair turns; 400 words → 540 on checkpoint and verify turns).

## 2. Turn-row marker for compaction

`build()` already computed `info["digest_request"]`; it was **never written to a row**, so a reader
filtering turn rows could not see compaction at all. Rows now carry **`digest_at`** (the turn a
digest was requested on, `null` otherwise), written beside `evicted`. `kind == "digest"` rows are
unchanged and still emitted — this adds, never replaces.

## 3. Launch precondition (refuses, never logs)

`check_treatments(fixture, arm, horizon)` in `run_longrun.py` returns
`(EXIT_TREATMENTS_UNREACHABLE, lines)` — exit **3**, "the run did not start", already in
`exit_codes.RUNNER_CODES`. It is applied in `--dry-run` **before any preview body is rendered** and
at the top of `run_cell` **before the manifest is frozen**, and is exported so `cell.py` (owned by
another card) can call the same assertion. The dry run prints, per arm:

    first FIFO truncation at turn T21
    first wall at turn T21
    first lease step at turn T23
    first prefix change at turn T2        (pointer-stable's own treatment)

Computed offline by driving the **real** `Planner` with the fixture's own maximum legal answer per
turn (no inference), so the estimate is a lower bound on the fire turn. Score at v8:

| arm | marker | first fire |
|---|---|---|
| transcript-grow | `evicted > 0` | **T21** |
| transcript-compact | `digest_at` set | **T21** (second digest near T48) |
| lease-reopen | `lease = 2` | **T23** |
| pointer-stable | `prefix_sha256` moves | **T2** |

Refusal cases (all quoted from the test run):

* `first FIFO truncation > 48 turns at wall_tokens=65536 (grow never evicts …)` — the red case,
  `wall_tokens` set back to 65536;
* `missing fixture field 'lease_reopen_turns' — the lease can never step, so the reopen arm is the
  pointer arm with a different label`;
* the frozen v7 inputs, once the contract is declared over them, refuse for all three arms.

The gate is **armed by the fixture's `treatments` block**. Frozen v5/v6/v7 fixtures are evidence,
not cells to relabel, so they are not retro-armed.

## 4. `expected_digests` is derived

    expected_digests(fixture) = digest requests produced by dry-simulating transcript-compact over
                                `turns` at this arm's wall, with a legal ceiling answer per turn
                                plus a 700-token digest (the COMPRESS instruction's own ceiling)

At v8 that is **2** per cell (reserve 50 requests, not the old literal 50+2). At 65536 it is **0**,
so a fixture that never reaches its wall reserves nothing — the projection cannot disagree with the
cell, and a third digest can no longer abort a legal cell at exit 4.

## 5. What this costs

A grid is `576 turn requests x 1.374532 = 792` (the published A*). With compaction firing twice per
rep: `(576 + 2 x 3) x 1.374532 = 800` per grid. Four firing grids = **3,200** against the ledger's
remaining **3,219** — **19 requests of slack**, i.e. four grids still fit, but with no room for a
fifth. The reserve is a ceiling; the ledger counts spend.

## 6. Is H3 measurable now?

H3's quality pass-rate is now **measurable per arm** — each of the three treatment predicates fires
inside the frozen horizon and leaves a row marker — but the *magnitude* of the transcript arms'
cost/quality difference is still confounded by answer verbosity, because the answer budget is
declared and recorded, not enforced; until answers are budget-normalised, a longer grow-cell answer
inflates its own wall.
