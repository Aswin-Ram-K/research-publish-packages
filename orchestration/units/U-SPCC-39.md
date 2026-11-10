# U-SPCC-39 — G3's `n` is turns×reps, not requests; E1 is unsatisfiable inside its own ceiling

## 0. The question

PREREG-SPCC budgets E1 at **200–500 requests** over 48 checkpoints, with three arms
(`spcc`, `masking-no-fetch`, `bounded-context-fetch`). The G3 gate wired in by U-SPCC-37
computes an `n` and compares it to that ceiling. Does that `n` count requests, or
turns × reps?

## 1. Answer: turns × reps, per arm. It is not the request count.

- `experiments/ptr-engine/longrun/cell.py:1259` — `facts["n"] = int(t["value"]) * int(r["value"])`.
  Two operands: `--turns` and `--reps`. No arm term.
- `experiments/ptr-engine/longrun/cell.py:1296` — `if ok and not (lo <= facts["n"] <= hi)`
  compares that `n` to `spcc["request_ceiling"]` (`min`/`max` from
  `research-seed-concepts/PREREG-SPCC.json`).
- `experiments/ptr-engine/longrun/cell.py:1130` — G1, by contrast, does count arms:
  `turns_total = facts["turns"] * facts["arms"] * facts["reps"]`. G1 and G3 disagree
  about what a cell costs.
- `experiments/ptr-engine/longrun/run_longrun.py:3105` — the runner prices each arm as
  `cell_total = turns + extra` where `turns = n_turns * reps`.
- `experiments/ptr-engine/longrun/run_longrun.py:3113` — `would_send_total` is the sum of
  `cell_total` over every arm in the cell.

So the gate's `n` is the **per-arm** turn allocation, while the ceiling it is compared
against is denominated in **requests for the whole experiment** (`PREREG-SPCC.json` E1
`unit_of_account: "requests"`, `arms: [spcc, masking-no-fetch, bounded-context-fetch]`).

## 2. The four shapes

Measured offline, no request sent. `validate_g3("E1", 100, reps, 48, {"E1": e1}, spcc=e1)`
and `run_longrun.py --dry-run --arms spcc,masking-no-fetch,bounded-context-fetch --reps R`
on `longrun/tasks-v7/TX-03.v1.json` (N=100, 48 checkpoints, `digest_requests=0`):

| Shape | gate `n` | gate verdict | true requests | violates |
|---|---|---|---|---|
| 3 arms × 1 rep × 100 turns | 100 | **refused** (below 200) | 300 | gate floor |
| 3 arms × 2 reps × 100 turns | 200 | **admitted** | 600 | 500 request ceiling |
| 2 arms × 2 reps × 100 turns | 200 | admitted | 400 | E1 design (needs 3 arms) |
| 1 arm × 2 reps × 100 turns | 200 | admitted | 200 | E1 design (needs 3 arms) |

`would_send_total` from the runner's own dry-run: **300** at `--reps 1`, **600** at
`--reps 2`, for the three-arm cell.

## 3. The defect, stated plainly

The gate admits a three-arm, two-rep cell at `n = 200` while that cell sends **600**
requests — 100 above PREREG-SPCC's own 500 ceiling. The gate cannot see the other two
arms because `cell.py` takes a single `--arm` (`cell.py:2222`) and `validate_g3` never
receives an arm count. A cell that spends 20 % over its preregistered ceiling is
admitted as if it were at the floor.

The converse also holds: the only three-arm shape the gate admits is the one that
overspends, and the only three-arm shape that fits the ceiling (`reps=1`, 300 requests)
is refused for being under the floor.

## 4. Consequence: E1 as preregistered cannot be run

No three-arm shape satisfies all three constraints simultaneously:

- gate `n` ∈ [200, 500]
- true requests ≤ 500
- true requests ≤ 4,013 headroom

`reps=1` fails the gate floor; `reps=2` fails the request ceiling. Shortening
`--max-turns` is not available either: the fixture's 48 checkpoints span turns 3–100
(12 at turn < 24, 36 at turn ≥ 24), so any shortened cell loses checkpoints and is not
E1. Substituting a fixture is likewise not E1.

**No E1 request was spent.** The honest outcome is that the preregistration's own budget
and the gate's own arithmetic are mutually inconsistent, and that is a finding about the
preregistration, not a licence to run a smaller cell and label it E1.

## 5. What would fix it

Either the gate must take the arm count into `n` (making `n` the request count the
ceiling is denominated in, matching G1's `turns_total` at `cell.py:1130`), or
PREREG-SPCC's E1 ceiling must be restated per arm. Until one of those happens, an
admissible E1 cannot be constructed at any shape.

## 6. Record

`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` — one row appended
(7-column table, 15 → 16 rows; the 10-column and 3-column counts unchanged).
