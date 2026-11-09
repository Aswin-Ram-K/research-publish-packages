# LAUNCH-CONTRACT — scoped judging for `launch_contract_diff.py --check`

The contract diff compares every number a launch depends on (price, per-cell budget, ledger,
canary, grid) and exits **1** when two live occurrences disagree. That is the right default:
a caller who names nothing asked for the strict reading.

It is the wrong acceptance gate for a card whose row is *supposed* to be stale until the next
pin generation.

## The case that produced this page

`GRID-PARAMS-DIGEST-SUPERSEDE` (`a3fdaab5`) settled **FAIL exit-1 `f17663d1`**. Its work was
correct and its `--check` passed at the moment it ran:

| time | event |
|---|---|
| 19:27:25Z | generation 4 frozen: `harness_sha256 = fa6fd8cc…`, `grade_v5.py = 056eb605…` |
| 19:27 | the card recomputed the digest, matched pin gen 4, wrote the cached copy with a `supersedes` block, `--check` → **0** |
| ~19:30 | `GRADE-V5-T4-DECORATION` repaired `grade_v5.py` (`056eb605… → 3d70ed1d…`) |
| 19:33 | the harness digest moved to `a3fa2ee0…`; `--check` → **1**, naming a digest row that is *supposed* to be stale until the next pin generation |

Nothing about that card's work was wrong and nothing about the next tree was wrong. The check
simply had no notion of **which tree it judged**, so a neighbour's edit inside the judged inputs
read as this row's defect.

## The rule this page installs

> **A check whose acceptance depends on files other cards may edit must be run with an explicit
> scope; a check that cannot name its tree cannot distinguish a defect from a neighbour.**

A check with no scope cannot tell "the number is wrong" from "someone else changed the tree
between my write and my re-check" — both arrive as the same exit 1.

## Usage

```sh
python3 experiments/ptr-engine/tools/launch_contract_diff.py --check                       # strict, unchanged
python3 experiments/ptr-engine/tools/launch_contract_diff.py --check --pin-generation 4    # judge generation 4's tree
python3 experiments/ptr-engine/tools/launch_contract_diff.py --check --tree-sha <sha256>   # judge a named recorded tree
python3 experiments/ptr-engine/tools/launch_contract_diff.py --write --pin-generation 4    # record the artefact, scoped
```

`--pin-generation N` resolves the generation through `measure/HARNESS-PIN.json`'s **supersedes
chain** (generation 4 → `supersedes_pin_generation_3` → …), so older generations stay on the
record and are judged in their own terms. `--tree-sha` must be a digest the pin records —
an unrecorded tree names no recorded values to judge against, is refused with **exit 2**, and
must be recorded in the pin first. That refusal is deliberate: a scope that accepts any digest
would be a way to launder a disagreement.

## Statuses and exit codes

| exit | meaning |
|---|---|
| **0** | every number agrees — including, when scoped, *the tree on disk is the tree the scope named* |
| **1** | a genuine `DISAGREES`/`UNRESOLVED` row (default behaviour, unchanged) |
| **13** | **`MOVED`** — the tree on disk is not the named tree (`exit_codes.EXIT_TREE_MOVED`, imported from the project's one exit-code table, never re-typed) |
| **2** | usage refusal: unknown generation, unrecorded `--tree-sha` |

`MOVED` is a **distinct class from `DISAGREES`**: it names every pinned input whose bytes differ,
with *both* digests (recorded and current), and it is not a verdict on the row's correctness.
13 is the project's established tree-moved code — declared in `experiments/ptr-engine/longrun/
exit_codes.py` and raised by `tools/tree_freeze.py`, which also prefixes such a verdict row
`UNSTAMPED:`. No new code was invented, and `1` keeps its meaning: the work failed.

A scope is **not a bypass**. Every other row is still judged strictly, and the suite proves it:
a tree that is exactly the named generation but carries a real `108 → 67` disagreement exits
**1** under `--pin-generation 5` exactly as it does unscoped.

## What the report carries

Scoped runs add `judged_tree: {generation, harness_sha256, pinned_at}` to the document and to the
digest row, plus `live_harness_sha256` and `moved_inputs: [{path, name, recorded_sha256,
current_sha256}]`. Unscoped runs are byte-for-byte the old shape — no `judged_tree` key at all —
so an existing reader sees no change.

## The recorded artefact

`measure/LAUNCH-CONTRACT-DIFF.json` was written with `--write --pin-generation 4`, i.e. **under
pin generation 4**, at a moment when the tree had moved under it. It therefore records
`judged_tree.generation = 4` and `summary.check_exit = 13` with `moved: ["harness_pin_digest"]`,
naming `grade_v5.py` (`056eb605… → 3d70ed1d…`) and `run_longrun.py` (`b2003038… → 30dfa9e9…`)
as movers, and `live_harness_sha256 = 35ff41b7…`. `summary.unscoped_check_exit` records what the
strict reading would have said about the same bytes. That is the honest record: the row was not
re-judged against a tree it did not see, and no launch number was re-derived.

## Proof, three cases (`measure/LAUNCH-CONTRACT-DIFF.json`, `tests/test_launch_contract_diff.py`)

| case | command | result |
|---|---|---|
| (a) today's real tree, scoped to gen 4 | `--check --pin-generation 4` | `MOVED`, **exit 13**, mover + both digests |
| (b) a tree whose recorded gen 4 matches its bytes | `--check --pin-generation 4` (in a `/tmp` copy) | 22 numbers `AGREES=16, STALE-BY-DESIGN=6`, **exit 0** |
| (c) a tree with one genuine disagreement (help `108 → 67`) | default `--check` | `per_cell_budget` `DISAGREES` at `run_a_star.py:241` and `run_a_star.py:367`, **exit 1** |
| (c′) the same tree, scoped | `--check --pin-generation 5` | still **exit 1** — the scope did not hide the defect |

## Traps

- **Do not restore a tree by re-recording a generation inside the workspace.** A pin bump is a
  card of its own (`HARNESS-PIN.json` is not this tool's to write). Re-recording is fine inside a
  `/tmp` copy for a proof, and that is what case (b) does — with the caveat recorded there: the
  generation-4 bytes of `grade_v5.py` are unrecoverable (untracked by git, no backup), so the
  copy's *record* was made to match its bytes rather than the bytes restored to the record.
- **`--write` writes `experiments/ptr-engine/measure/`**, not `<root>/measure/`. The old join
  wrote outside the measure directory; it is fixed here.
- **A moving tree is normal during a batch.** Run the scoped check when the acceptance is a row
  that another card's edit can move; run the default check when you are auditing the tree itself.
