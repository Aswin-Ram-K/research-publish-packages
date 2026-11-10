# U-SPCC-35 — E1: `spcc` beats masking and fetch on TX-03, but not at `d2`

## 0. Precondition

`resolve_claim("E1")` from `experiments/ptr-engine/longrun/claim_mode.py` returned
`mode=hypothesis claim=E1 comparison_eligible=True`. The first attempt, against the
committed resolver, raised `ClaimRefusal` (`claim_mode.py:222`, `CLAIM_IDS = ("H1",
"H2", "H3")` at `:95`); the claim-namespace unit landed `SPCC_CLAIM_IDS = ("E1", ...,
"E6")` at `claim_mode.py:102` while this unit was open, and the gate then passed. No
substitution (`smoke`/`plumbing`/`H1`/`H2`/`H3`) was used and the cap was not raised.

## 1. The cell

```
TMPDIR=/home/zer0null/tmp-pytest .venv/bin/python experiments/ptr-engine/longrun/run_longrun.py \
  --fixture experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json \
  --arms spcc --reps 1 --temperature 0 --seed 42 \
  --model occamy-1.0 --base-url http://192.168.2.168:8012/v1 \
  --claim-mode E1 --budget-cap 12094 \
  --run-id e1-spcc-2026-11-10 \
  --rows experiments/ptr-engine/measure/rows-e1-spcc-2026-11-10.jsonl
```

Exit 0, wall 30.55 s. `rows=100 requests=100 truncated=0 failed_turns=0`,
`finish_reason {"stop": 100}`, `answer_source {"content": 100}`,
`token_dist {"n": 100, "mean": 4.6, "p95": 7.0, "max": 7.0}`,
`tok_method=tiktoken:cl100k_base`. Cap gate: `allocation=100 cap=12094
spent_at_start=7981 used_in_run=100 spent_after=8081 delta=0`, reconciled
(`the run's count 100 equals the rows gained 100`). Manifest
`longrun/manifests/e1-spcc-2026-11-10-spcc-r1.json` sha256
`dbd5047c041ba2241a92e1bb7c56737aca23dddf2c350f46ffbfaf6357148e5c`.
Every row carries `claim=E1`, `comparison_eligible=True`, `model=occamy-1.0`,
`temperature=0.0`, `seed=42`, `fixture_sha256=f0a636fe…620c3`.

## 2. Three-arm table

Scored by `longrun/score_longrun.py:score_answer_contract_rows(fixture, rows)` — the
repo's own entry point, not a hand-rolled counter. All three files are the **same
endpoint and model** (`manifests/celltx03-*.json` → `endpoint
http://192.168.2.168:8012/v1`, `id occamy-1.0`), same fixture, seed 42, temperature 0.
**Same build is not proven**: `image_digest` and `exact_argv` are `UNSOURCEABLE` in all
three manifests, so no container image or `sglang` version is comparable.
`rows-tx03-8014-*` was not used.

Two accuracy columns, because they differ: **value-correct** (the number is right) and
**contract-correct** (the number is right *and* the answer form is `NUM`).

| arm | rows file | value-correct | contract-correct | answered_correctly | abstained_after_mask | answered_wrong | unparsed | ungradeable | graded | total |
|---|---|---|---|---|---|---|---|---|---|---|
| `spcc` | `rows-e1-spcc-2026-11-10.jsonl` | **20/48** | **19/48** | 20 | 0 | 0 | 0 | 0 | 48 | 48 |
| `masking-no-fetch` | `rows-tx03-masking-r1.jsonl` | 8/48 | 8/48 | 8 | 40 | 0 | 0 | 0 | 48 | 48 |
| `bounded-context-fetch` | `rows-tx03-fetch-r1.jsonl` | 12/48 (12/39 graded) | 12/48 (12/39 graded) | 12 | 16 | 1 | 10 | 19 | 39 | 48 |

`spcc`'s one value/contract gap is `cp.TX-03.f08.d2` (turn 70): it answered
`kind=TEXT` with the right value `3700` where the contract requires `NUM`.

**The fetch denominator.** `rows-tx03-fetch-r1.jsonl` has 53 rows carrying a non-null
`expected`, but that is a *row* count, not a checkpoint count: 14 of those rows are
interim (row-level split 12 value-correct + 14 interim + 16 `NONE` + 10 unparsed + 1
wrong = 53). The file carries exactly the fixture's 48 checkpoint identities, so
restricting all three arms to the shared 48 is a no-op — they already share one
checkpoint set. The real gap is that **9 of fetch's 48 checkpoints have no final
answer** (`f01.d5`, `f02.d5`, `f02.d8`, `f03.d6`, `f03.d20`, `f04.d6`, `f04.d20`,
`f07.d5`, `f08.d8`), so its graded denominator is 39 while `spcc`'s and masking's are
48. `12/48` counts those 9 as failures; `12/39` is the graded figure.

By distance (`contract`/`n`):

| arm | d2 | d5 | d6 | d8 | d20 | d32 |
|---|---|---|---|---|---|---|
| `spcc` | 6/8 | 3/8 | 5/8 | 3/8 | 2/8 | 0/8 |
| `masking-no-fetch` | 8/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| `bounded-context-fetch` | 6/8 | 1/8 | 2/8 | 1/8 | 1/8 | 1/8 |

## 3. Per-checkpoint breakdown for `spcc`

20 of 48 checkpoints are value-correct (19 contract-correct; the table below lists the
20 value-correct ones). `COMPACT_EVERY = 24`, so compactions fall at turns
24, 48, 72, 96. Fact delivery turns: `f01`@1, `f02`@8, `f03`@17, `f04`@24, `f05`@45,
`f06`@52, `f07`@61, `f08`@68.

| checkpoint | probe turn | intro turn | distance | epoch |
|---|---|---|---|---|
| `cp.TX-03.f01.d2` | 3 | 1 | 2 | pre-compaction |
| `cp.TX-03.f01.d5` | 6 | 1 | 5 | pre-compaction |
| `cp.TX-03.f01.d6` | 7 | 1 | 6 | pre-compaction |
| `cp.TX-03.f01.d8` | 9 | 1 | 8 | pre-compaction |
| `cp.TX-03.f02.d2` | 10 | 8 | 2 | pre-compaction |
| `cp.TX-03.f02.d5` | 13 | 8 | 5 | pre-compaction |
| `cp.TX-03.f02.d6` | 14 | 8 | 6 | pre-compaction |
| `cp.TX-03.f02.d8` | 16 | 8 | 8 | pre-compaction |
| `cp.TX-03.f03.d2` | 19 | 17 | 2 | pre-compaction |
| `cp.TX-03.f01.d20` | 21 | 1 | 20 | pre-compaction |
| `cp.TX-03.f03.d5` | 22 | 17 | 5 | pre-compaction |
| `cp.TX-03.f03.d6` | 23 | 17 | 6 | pre-compaction |
| `cp.TX-03.f05.d2` | 47 | 45 | 2 | post-24, fact delivered after it |
| `cp.TX-03.f06.d2` | 54 | 52 | 2 | post-48, fact delivered after it |
| `cp.TX-03.f06.d6` | 58 | 52 | 6 | post-48, fact delivered after it |
| `cp.TX-03.f07.d2` | 63 | 61 | 2 | post-48, fact delivered after it |
| `cp.TX-03.f07.d6` | 67 | 61 | 6 | post-48, fact delivered after it |
| `cp.TX-03.f07.d8` | 69 | 61 | 8 | post-48, fact delivered after it |
| `cp.TX-03.f08.d2` | 70 | 68 | 2 | post-48, fact delivered after it |
| `cp.TX-03.f06.d20` | 72 | 52 | 20 | post-48, probe on the compaction turn |

**12 passes are pre-compaction (turn < 24). 8 passes are post-compaction (turns
47–72), and every one of those is for a fact introduced after the most recent
compaction. Zero passes cross a compaction boundary** — checked as
`intro < c < probe` for `c ∈ {24, 48, 72, 96}`, 0 hits. `f04` (delivered at turn 24,
the compaction turn itself) never passes: `d2`@26, `d5`@29, `d6`@30, `d8`@32,
`d20`@44, `d32`@56 all fail. The journal is dropped, not summarised, and no fact
survives the fold.

## 4. Billing for the `spcc` cell

From `score_answer_contract_rows(...)["spcc__rep1"]["billing"]`:

| field | value |
|---|---|
| `prompt_tokens` | 47,594 |
| `cached_tokens` | 37,632 |
| `billed_tokens_known` | 9,962 |
| `billed_upper_bound_tokens` | 9,962 |
| `billed_unknown_rows` | 0 |
| `coverage` | 1.0 |

`billed_source=reported`, `cached_fraction_of_prompt=0.7907`,
`reconcile_delta_total=0` (tolerance 475), `reconcile_within_tolerance=true`.
Comparison arms: `masking-no-fetch` 12,489 billed (80,905 prompt / 68,416 cached);
`bounded-context-fetch` 23,624 billed (100,104 / 76,480). All three `coverage=1.0`,
`billed_unknown_rows=0`.

## 5. Verdict against E1

Quoted from `experiments/ptr-engine/research-seed-concepts/PREREG-SPCC.md` §E1:

> **Predicted outcome (written before running):** `spcc` scores ≥ fetch on single-fact
> and > masking everywhere; billed tokens ≤ masking.
>
> **Falsifier:** `spcc` below fetch on single-fact, or `spcc` not strictly above masking
> on any checkpoint class, or billed tokens above masking.

**The prediction FAILED. The falsifier did NOT fire.**

- `spcc` ≥ fetch on single-fact: **holds** — 20/48 vs 12/48 by value and 19/48 vs
  12/48 by contract overall, and 6/8 vs 6/8 at `d2`, 3/8 vs 1/8 at `d5`, 5/8 vs 2/8 at
  `d6`, 3/8 vs 1/8 at `d8`.
- `spcc` > masking **everywhere**: **fails.** At `d2` masking scores 8/8 and `spcc`
  6/8; at `d32` both score 0/8, which is not ">". `spcc` is strictly above masking on
  `d5` (3>0), `d6` (5>0), `d8` (3>0) and `d20` (2>0) only.
- billed tokens ≤ masking: **holds** — 9,962 ≤ 12,489.

Falsifier clauses, one by one: `spcc` is not below fetch on single-fact (20 > 12), so
clause 1 does not fire; `spcc` *is* strictly above masking on four checkpoint classes,
so clause 2 ("not strictly above masking on **any** class") does not fire; billed
tokens are below masking, so clause 3 does not fire. The prereg's own deviation note
predicted the falsifier "is expected to fire" on post-compaction probes — **it did
not**, because `spcc` does beat masking on `d5`/`d6`/`d8`/`d20`. That expectation was
wrong; the prediction's "everywhere" conjunct is what broke, and it broke at `d2`,
which is pre-compaction.

## 6. Limitations, stated plainly

- **The cell is below E1's own request floor.** `PREREG-SPCC.md:25` says "E1–E5 are
  each 200–500 requests"; this cell spent 100. `run_longrun.py` does not call
  `cell.eval_gate_prereg` (no reference to `eval_gate_prereg`, `validate_g3` or
  `GATE_PREREG` in the file), so nothing refused the shortfall. The result is a
  single-rep, under-ceiling observation, not a full E1 adjudication.
- **One rep per arm; same endpoint and model, not proven same build.** `image_digest`
  and `exact_argv` are `UNSOURCEABLE` in all three manifests. `spcc` has never been run
  on `:8014`; no cross-build claim is made (ledger rule 9).
- **The fetch arm's graded denominator is 39, not 48.** 9 of its 48 checkpoints carry
  no final answer, so `12/48` counts them as failures while `12/39` is the graded
  figure. `spcc` and masking are graded on all 48.
- **`d2` is the only class where masking is non-zero**, so "`spcc` > masking
  everywhere" was always going to be decided at `d2` alone. `spcc` loses there.

## 7. Ledger and gates

`experiments/ptr-engine/research-seed-concepts/FINDINGS-LEDGER.md` gained one row
(7 columns, matching the main table). Column-count check before: `15 10 / 7 3 / 14 7`;
after: `15 10 / 7 3 / 15 7` — the 7-column table went 14 → 15, nothing else moved.
`python3 tools/doc_check.py` → `OK docs clean under /home/zer0null/research extractor`,
exit 0.
