# CHECKPOINT-COVERAGE — 12 decidable checkpoints, their cost, and the ranking they buy

Unit `CHECKPOINT-COVERAGE`. Offline: zero inference requests. Every truth value below is
**recomputed by `experiments/ptr-engine/tools/fixture_coverage.py` from the AST** of the pinned
sources — none is copied from a card, a chat message, or the fixture's own `expected` string
(the gate compares the two and fails on divergence).

Fixture: [`LR-01.v6.json`](../experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json).
`LR-01.v5.json` is **unmodified** (a live cell's rows reference it); v6 is a new file.

## 1. Why this exists

`EVAL-PRACTICE-SURVEY` (handoff `orchestration/handoffs/EVAL-PRACTICE-SURVEY.json`) measured that
the v5 fixture carries **3** decidable checkpoints. At `b+c = 3` the exact McNemar minimum
two-sided p is **0.25**, so a 3-checkpoint fixture cannot rank two arms *at any number of repeats* —
repeats shrink variance in the wrong quantity; they do not buy discordant pairs. The survey's
recommendation was a 3 → 12 checkpoint expansion as the cheapest way to restore discriminating
power.

## 2. The 12 items

Twelve checkpoints, **one per checkpoint turn** (see §5 for why not four per turn).

| # | id | turn | kind | question | truth (AST-derived) | pinned source |
|---|---|---|---|---|---|---|
| 1 | `cp.3.t06` | T6 | CALL | what does `resolve()` call when it records a successful resolution, and with which keywords? | `ledger.record_resolution(scope=scope.name, serialized_ref=presented, bytes_appended=..., block_size=scope.block(), entry_text=...)` | resolve.py#L159 |
| 2 | `cp.4.t08` | T8 | CALL | which scope method does `resolve()` call for the ledger's block size? | `scope.block()` | resolve.py#L163 |
| 3 | `cp.0.t12` | T12 | NUM | default per-turn resolve budget in refs | `64` (`DEFAULT_MAX_REFS`) | resolve.py#L39 |
| 4 | `cp.5.t14` | T14 | NONE | does `resolve()` itself call `ledger.record_refusal()`? | `NONE` (it delegates to `_refuse`) | resolve.py#L74-L166 |
| 5 | `cp.6.t18` | T18 | NUM | how many `PtrLedger*` error classes? | `6` | errors.py#L15-L250 |
| 6 | `cp.7.t20` | T20 | NONE | does `_refuse()` call `ledger.resolved_count()`? | `NONE` | resolve.py#L66-L71 |
| 7 | `cp.1.t24` | T24 | NUM | how many `Ptr*` error classes does errors.py define? | `31` | errors.py#L15-L250 |
| 8 | `cp.8.t26` | T26 | NUM | how many `PtrLaw*` (hit-ledger law) classes? | `5` | errors.py#L15-L250 |
| 9 | `cp.9.t32` | T32 | NUM | how many `PtrUnknown*` classes? | `2` | errors.py#L15-L250 |
| 10 | `cp.10.t36` | T36 | CALL | which ledger method counts refs already resolved (first of three sites)? | `ledger.resolved_count()` | resolve.py#L141 |
| 11 | `cp.11.t42` | T42 | NONE | does `_refuse()` call `scope.block()`? | `NONE` | resolve.py#L66-L71 |
| 12 | `cp.2.t46` | T46 | CALL | what does `_refuse` call, and what does it pass? | `ledger.record_refusal(scope=..., serialized_ref=text, code=error.code)` | resolve.py#L66-L71 |

Kinds: **NUM 5 · CALL 4 · NONE 3**. No `TEXT` item (grade_v5 refuses TEXT). Longest expected answer:
**33 cl100k tokens** (`cp.3.t06`), under the 40-token cap.

**The three v5 items, retained verbatim in value and turn** (so the v5 and v6 numbers are comparable
per item): `cp.0.t12` = 64, `cp.1.t24` = 31, `cp.2.t46` = the `record_refusal` call. They keep their
v5 ids; the nine new ids were chosen not to collide with them.

**Slice repair (v6).** The `resolve.py` pin widens from `#L36-L110` to `#L36-L166`. Reason: three CALL
truths sit at L141/159/163, which the v5 pin truncated at L110 — asking for `scope.block()` from a range
that ends before L163 is exactly the defect that cost this project three rounds (`DEFAULT_MAX_REFS` at
L39 with `resolve.py` pinned L66-110). The precedent is the v4→v5 widening, recorded in v5's
`adaptation.slice_repair`.

## 3. Request cost: 4 arms × 3 repeats

A checkpoint is one request per arm per repeat; work/verify turns are unchanged.

```
v5:  3 checkpoints x 4 arms x 3 reps =  36 checkpoint requests
v6: 12 checkpoints x 4 arms x 3 reps = 144 checkpoint requests
                                       ---
delta:  9 extra x 4 arms x 3 reps    = +108 checkpoint requests
```

Per arm per repeat the delta is **9 requests** (12 − 3); across the full 4 × 3 grid it is
**108**. This is the 108 the survey predicted, and it is the whole cost: no new turns, no new
bodies, no extra verify requests.

## 4. Discordant-pair budget and the ranking it buys

A checkpoint pair can be *discordant* only when the two arms disagree on it, so with `c` decidable
items the encounter count `b+c` is capped at `c`. Exact McNemar, two-sided, `p = 2·Σ_{i≤k} C(n,i)/2^n`
with `n = b+c` and `k = min(b,c)`:

| decidable items | max b+c | best split | exact two-sided p |
|---|---|---|---|
| 3 (v5) | 3 | 3–0 | **0.25** |
| 6 | 6 | 6–0 | **0.03125** |
| 6 | 6 | 5–1 | 0.21875 |
| 12 (v6) | 12 | 12–0 | **0.000488** |
| 12 (v6) | 12 | 11–1 | 0.006348 |
| 12 (v6) | 12 | 10–2 | 0.038574 |

Ranking power, stated plainly: **v5 could not clear 0.25 at any n of repeats, while v6 clears
p < 0.05 whenever an arm wins at least 10 of 12 items and clears p < 0.01 at 11–1
(2·13/2¹² = 0.006348), reaching 2/2¹² = 0.000488 on a 12–0 sweep** — i.e. a real 8-point effect is
now detectable where a 3-item fixture could only ever report "no evidence".

## 5. Two deviations from the card, both measured

1. **One item per checkpoint turn, twelve turns — not four items on T12/T24/T46.**
   `grade_v5.parse_answer_contract` accepts exactly **one** `ANSWER:` line per answer; a second one
   sets `answer_parse_error = multiple_answer_lines` and the checkpoint grades `fail`. Four items on
   one turn therefore could not be graded by the contract the fixture itself pins, and 12 items on 3
   requests would also contradict the card's own ±9-request-per-arm arithmetic (which assumes 12
   checkpoint requests). Twelve turns deliver 12 independently decidable items at exactly the
   predicted cost.
2. **`TEXT` is removed from `answer_contract.forms`** in v6 (it remains parseable and still never
   passes, but the fixture no longer offers it), because a TEXT form invites the prose grading this
   contract replaced.

## 6. Known gap: 4 of the 12 items need a `grade_v5` branch (measured, not assumed)

`grade_v5.derive_truth` (longrun/grade_v5.py:247-306) dispatches **only** `constant_value` and
`count_classes` for NUM (from `resolve.py` / `errors.py` hardcoded at :249-252) and
`call_inside_function` for CALL. Measured on v6:

```
NONE items (cp.5.t14, cp.7.t20, cp.11.t42)
  SystemExit: fixture_truth_mismatch: <id> has no usable answer_spec
call_at_line item (cp.10.t36)
  KeyError: 'function'
```

So **12 of 12 items are gradeable by `grade_v5` today** (derived via `grade_v5.py:661-734`); the earlier "8 of 12" claim is stale.
additions in a file this unit does not own (`grade_v5.py` is another card's write path): a NONE
branch that confirms absence via `no_attr_call_inside_function`, and a `call_at_line` branch for a
callee with repeated identical sites. The gate in §7 implements both rules, so the fixture can be
verified now and graded once that branch lands.

The prose-judge attenuation measured by the survey (**1 − FN − FP = 0.237** for grade_v3, **0.231**
for grade_v4) does not apply to v5/v6 at all: both compare a typed value against AST truth, so a
checkpoint's per-item error rate is a contract-parse rate, not a token-anchor rate.

## 7. The gate

```
python3 experiments/ptr-engine/tools/fixture_coverage.py \
    --fixture experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json
```

One row per checkpoint: `id · turn · kind · answerable_from_pinned_range · truth (AST-derived) ·
expected token count · collision · sites`. Exit **0** only when every checkpoint is answerable from
its declared pinned range, none collides, all are ≤ 40 tokens, no `TEXT` item exists, and no two
items decide the same fact.

Observed on v6:

```
PASS: 12/12 checkpoints decidable, none colliding, all <= 40 tokens
```

Observed red on the three mutants (`experiments/ptr-engine/longrun/tests/test_fixture_coverage.py`,
8 passed):

```
(a) truth moved outside its pinned range
  - cp.4.t08: truth at [163] falls outside the declared pinned range #L36-L110
(b) colliding truth value
  - cp.1.t24: duplicate truth of cp.6.t18
  - cp.6.t18: duplicate truth of cp.1.t24
(c) a TEXT item
  - cp.9.t32: kind TEXT is refused by grade_v5
```

Each exits non-zero; each is a fixture that does not go near the board.
